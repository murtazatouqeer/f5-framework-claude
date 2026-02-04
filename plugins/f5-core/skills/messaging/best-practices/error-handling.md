---
name: error-handling
description: Handling failures in messaging systems
category: messaging/best-practices
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Error Handling in Messaging

## Overview

Error handling in messaging systems requires different strategies than synchronous systems. Messages can fail at production, delivery, or consumption, each requiring specific handling approaches.

## Error Categories

| Category | Examples | Handling |
|----------|----------|----------|
| **Transient** | Network timeout, service unavailable | Retry with backoff |
| **Permanent** | Invalid data, business rule violation | Dead letter queue |
| **Poison** | Malformed message, version mismatch | Isolate immediately |
| **System** | Out of memory, disk full | Alert and pause |

## Producer Error Handling

```typescript
class ResilientProducer {
  private readonly maxRetries = 3;
  private readonly retryDelay = 1000;

  async publish(event: DomainEvent): Promise<void> {
    let lastError: Error | undefined;

    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        await this.broker.send(event);
        return; // Success
      } catch (error) {
        lastError = error as Error;

        if (this.isRetryable(error)) {
          console.warn(`Publish attempt ${attempt} failed, retrying...`);
          await this.delay(this.retryDelay * attempt);
        } else {
          throw error; // Non-retryable, fail immediately
        }
      }
    }

    // All retries exhausted
    await this.handlePublishFailure(event, lastError!);
  }

  private isRetryable(error: any): boolean {
    // Network and timeout errors are retryable
    if (error.code === 'ECONNREFUSED') return true;
    if (error.code === 'ETIMEDOUT') return true;
    if (error.message?.includes('timeout')) return true;

    // Broker overloaded
    if (error.code === 'ERR_MSG_QUEUE_FULL') return true;

    return false;
  }

  private async handlePublishFailure(
    event: DomainEvent,
    error: Error
  ): Promise<void> {
    // Option 1: Store locally for retry
    await this.localQueue.enqueue(event);

    // Option 2: Store in database (outbox pattern)
    await this.outbox.save({
      event,
      error: error.message,
      failedAt: new Date(),
    });

    // Option 3: Alert for manual intervention
    await this.alertService.critical('Message publish failed', {
      eventId: event.eventId,
      error: error.message,
    });
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Consumer Error Handling

```typescript
interface ErrorContext {
  message: Message;
  error: Error;
  attemptNumber: number;
  firstFailedAt: Date;
}

class ResilientConsumer {
  private readonly maxRetries = 3;

  async processMessage(message: Message): Promise<void> {
    const retryCount = this.getRetryCount(message);

    try {
      await this.handler(message);
      await this.acknowledge(message);
    } catch (error) {
      await this.handleError({
        message,
        error: error as Error,
        attemptNumber: retryCount + 1,
        firstFailedAt: this.getFirstFailedAt(message) || new Date(),
      });
    }
  }

  private async handleError(context: ErrorContext): Promise<void> {
    const { message, error, attemptNumber } = context;

    // Classify error
    const errorType = this.classifyError(error);

    switch (errorType) {
      case 'transient':
        if (attemptNumber < this.maxRetries) {
          // Requeue with delay
          await this.requeueWithDelay(message, attemptNumber);
        } else {
          // Max retries exceeded
          await this.moveToDeadLetter(message, error);
        }
        break;

      case 'permanent':
        // No point retrying
        await this.moveToDeadLetter(message, error);
        break;

      case 'poison':
        // Isolate immediately
        await this.isolatePoisonMessage(message, error);
        break;
    }
  }

  private classifyError(error: Error): 'transient' | 'permanent' | 'poison' {
    // Parse errors are poison
    if (error instanceof SyntaxError) return 'poison';
    if (error.message.includes('JSON')) return 'poison';

    // Validation errors are permanent
    if (error instanceof ValidationError) return 'permanent';
    if (error.message.includes('required')) return 'permanent';

    // Network errors are transient
    if (error.message.includes('timeout')) return 'transient';
    if (error.message.includes('connection')) return 'transient';

    // Default to transient (will retry)
    return 'transient';
  }

  private async requeueWithDelay(
    message: Message,
    attemptNumber: number
  ): Promise<void> {
    const delay = Math.min(1000 * Math.pow(2, attemptNumber), 60000);

    await this.queue.send({
      ...message,
      headers: {
        ...message.headers,
        'x-retry-count': String(attemptNumber),
        'x-first-failed-at': message.headers?.['x-first-failed-at'] || new Date().toISOString(),
      },
    }, { delay });

    await this.acknowledge(message);
  }

  private async moveToDeadLetter(message: Message, error: Error): Promise<void> {
    await this.dlq.send({
      originalMessage: message,
      error: {
        message: error.message,
        stack: error.stack,
        type: error.constructor.name,
      },
      failedAt: new Date(),
      retryCount: this.getRetryCount(message),
    });

    await this.acknowledge(message);
    console.error(`Message ${message.id} moved to DLQ: ${error.message}`);
  }

  private async isolatePoisonMessage(message: Message, error: Error): Promise<void> {
    // Store in poison message store
    await this.poisonStore.save({
      message,
      error: error.message,
      isolatedAt: new Date(),
    });

    await this.acknowledge(message);

    // Alert immediately
    await this.alertService.critical('Poison message detected', {
      messageId: message.id,
      error: error.message,
    });
  }

  private getRetryCount(message: Message): number {
    return parseInt(message.headers?.['x-retry-count'] || '0', 10);
  }

  private getFirstFailedAt(message: Message): Date | null {
    const timestamp = message.headers?.['x-first-failed-at'];
    return timestamp ? new Date(timestamp) : null;
  }

  private async acknowledge(message: Message): Promise<void> {
    await this.queue.ack(message);
  }
}
```

## Error Recovery Patterns

### Compensation Pattern

```typescript
class CompensatingHandler {
  async handle(message: Message): Promise<void> {
    const completedSteps: string[] = [];

    try {
      // Step 1
      await this.reserveInventory(message.data);
      completedSteps.push('inventory');

      // Step 2
      await this.processPayment(message.data);
      completedSteps.push('payment');

      // Step 3
      await this.createShipment(message.data);
      completedSteps.push('shipment');

    } catch (error) {
      // Compensate completed steps in reverse
      await this.compensate(completedSteps, message.data);
      throw error;
    }
  }

  private async compensate(steps: string[], data: any): Promise<void> {
    for (const step of steps.reverse()) {
      try {
        switch (step) {
          case 'shipment':
            await this.cancelShipment(data);
            break;
          case 'payment':
            await this.refundPayment(data);
            break;
          case 'inventory':
            await this.releaseInventory(data);
            break;
        }
      } catch (compensationError) {
        // Log but continue compensating other steps
        console.error(`Compensation failed for ${step}:`, compensationError);
      }
    }
  }
}
```

### Circuit Breaker Pattern

```typescript
class CircuitBreaker {
  private failures = 0;
  private lastFailure?: Date;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private readonly threshold: number = 5,
    private readonly timeout: number = 30000
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (this.shouldReset()) {
        this.state = 'half-open';
      } else {
        throw new CircuitOpenError();
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailure = new Date();

    if (this.failures >= this.threshold) {
      this.state = 'open';
    }
  }

  private shouldReset(): boolean {
    if (!this.lastFailure) return false;
    return Date.now() - this.lastFailure.getTime() > this.timeout;
  }
}

// Usage in consumer
class ProtectedConsumer {
  private circuitBreaker = new CircuitBreaker(5, 30000);

  async process(message: Message): Promise<void> {
    try {
      await this.circuitBreaker.execute(() =>
        this.externalService.call(message.data)
      );
    } catch (error) {
      if (error instanceof CircuitOpenError) {
        // Circuit is open - defer processing
        await this.deferMessage(message);
      } else {
        throw error;
      }
    }
  }
}
```

## Logging and Monitoring

```typescript
class ErrorLogger {
  logError(context: ErrorContext): void {
    const logEntry = {
      level: 'error',
      timestamp: new Date().toISOString(),
      messageId: context.message.id,
      messageType: context.message.type,
      errorType: context.error.constructor.name,
      errorMessage: context.error.message,
      attemptNumber: context.attemptNumber,
      firstFailedAt: context.firstFailedAt.toISOString(),
      stack: context.error.stack,
      correlationId: context.message.correlationId,
    };

    console.error(JSON.stringify(logEntry));

    // Send to monitoring
    this.metrics.increment('message.errors', {
      messageType: context.message.type,
      errorType: context.error.constructor.name,
    });
  }
}

// Alerting thresholds
const alertRules = {
  errorRate: {
    threshold: 0.05, // 5%
    window: '5m',
    action: 'page',
  },
  dlqSize: {
    threshold: 100,
    action: 'alert',
  },
  poisonMessages: {
    threshold: 1,
    action: 'page', // Immediate attention
  },
};
```

## Error Response Patterns

```typescript
// Request-Reply error handling
interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details?: any;
    retryable: boolean;
  };
}

interface SuccessResponse<T> {
  success: true;
  data: T;
}

type Response<T> = SuccessResponse<T> | ErrorResponse;

class RequestReplyHandler {
  async handle(request: Message): Promise<Response<any>> {
    try {
      const result = await this.process(request);
      return { success: true, data: result };
    } catch (error) {
      return {
        success: false,
        error: {
          code: this.getErrorCode(error),
          message: (error as Error).message,
          retryable: this.isRetryable(error),
        },
      };
    }
  }

  private getErrorCode(error: any): string {
    if (error instanceof ValidationError) return 'VALIDATION_ERROR';
    if (error instanceof NotFoundError) return 'NOT_FOUND';
    if (error instanceof ConflictError) return 'CONFLICT';
    return 'INTERNAL_ERROR';
  }

  private isRetryable(error: any): boolean {
    return error instanceof TransientError;
  }
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Classify errors** | Transient vs permanent vs poison |
| **Retry with backoff** | Exponential delay for transient |
| **Use DLQ** | Capture failed messages |
| **Log context** | Include message ID, correlation ID |
| **Set limits** | Max retries, max delay |
| **Monitor rates** | Alert on error spikes |
| **Compensate** | Undo partial operations |
| **Test failures** | Chaos engineering |
