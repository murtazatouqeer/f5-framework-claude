---
name: retry-strategies
description: Handling transient failures with retry mechanisms
category: messaging/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Retry Strategies

## Overview

Retry strategies handle transient failures in distributed systems. Proper retry implementation prevents cascade failures while ensuring eventual success for recoverable errors.

## Retry Types

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| **Immediate** | Retry instantly | Quick recovery |
| **Fixed Delay** | Wait constant time | Simple backoff |
| **Exponential** | Double delay each time | Prevent overload |
| **Jitter** | Add randomness | Avoid thundering herd |
| **Circuit Breaker** | Stop retries temporarily | Protect services |

## Basic Retry

```typescript
interface RetryOptions {
  maxAttempts: number;
  shouldRetry?: (error: Error) => boolean;
}

async function retry<T>(
  fn: () => Promise<T>,
  options: RetryOptions
): Promise<T> {
  const { maxAttempts, shouldRetry = () => true } = options;
  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxAttempts || !shouldRetry(lastError)) {
        throw lastError;
      }

      console.log(`Attempt ${attempt} failed, retrying...`);
    }
  }

  throw lastError;
}

// Usage
const result = await retry(
  () => fetchData(url),
  { maxAttempts: 3 }
);
```

## Exponential Backoff

```typescript
interface ExponentialBackoffOptions {
  maxAttempts: number;
  initialDelay: number;     // ms
  maxDelay: number;         // ms
  multiplier: number;       // Usually 2
  shouldRetry?: (error: Error) => boolean;
}

async function retryWithExponentialBackoff<T>(
  fn: () => Promise<T>,
  options: ExponentialBackoffOptions
): Promise<T> {
  const {
    maxAttempts,
    initialDelay,
    maxDelay,
    multiplier,
    shouldRetry = () => true,
  } = options;

  let lastError: Error | undefined;
  let delay = initialDelay;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxAttempts || !shouldRetry(lastError)) {
        throw lastError;
      }

      console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await sleep(delay);

      delay = Math.min(delay * multiplier, maxDelay);
    }
  }

  throw lastError;
}

function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Usage
const result = await retryWithExponentialBackoff(
  () => callExternalApi(),
  {
    maxAttempts: 5,
    initialDelay: 1000,  // 1 second
    maxDelay: 30000,     // 30 seconds
    multiplier: 2,       // 1s, 2s, 4s, 8s, 16s
  }
);
```

## Jittered Backoff

```typescript
type JitterStrategy = 'full' | 'equal' | 'decorrelated';

interface JitteredBackoffOptions extends ExponentialBackoffOptions {
  jitter: JitterStrategy;
}

function calculateJitteredDelay(
  baseDelay: number,
  jitter: JitterStrategy,
  attempt: number,
  multiplier: number
): number {
  const exponentialDelay = baseDelay * Math.pow(multiplier, attempt - 1);

  switch (jitter) {
    case 'full':
      // Random between 0 and exponential delay
      return Math.random() * exponentialDelay;

    case 'equal':
      // Half exponential + random half
      return exponentialDelay / 2 + Math.random() * (exponentialDelay / 2);

    case 'decorrelated':
      // Based on previous delay with randomness
      return Math.random() * (exponentialDelay * 3 - baseDelay) + baseDelay;

    default:
      return exponentialDelay;
  }
}

async function retryWithJitter<T>(
  fn: () => Promise<T>,
  options: JitteredBackoffOptions
): Promise<T> {
  const {
    maxAttempts,
    initialDelay,
    maxDelay,
    multiplier,
    jitter,
    shouldRetry = () => true,
  } = options;

  let lastError: Error | undefined;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;

      if (attempt === maxAttempts || !shouldRetry(lastError)) {
        throw lastError;
      }

      const delay = Math.min(
        calculateJitteredDelay(initialDelay, jitter, attempt, multiplier),
        maxDelay
      );

      console.log(`Attempt ${attempt} failed, retrying in ${Math.round(delay)}ms...`);
      await sleep(delay);
    }
  }

  throw lastError;
}
```

## Circuit Breaker

```typescript
type CircuitState = 'closed' | 'open' | 'half-open';

interface CircuitBreakerOptions {
  failureThreshold: number;   // Failures before opening
  successThreshold: number;   // Successes to close
  timeout: number;            // Time in open state (ms)
}

class CircuitBreaker {
  private state: CircuitState = 'closed';
  private failures = 0;
  private successes = 0;
  private lastFailureTime?: Date;

  constructor(private readonly options: CircuitBreakerOptions) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (this.shouldAttemptReset()) {
        this.state = 'half-open';
      } else {
        throw new CircuitOpenError('Circuit breaker is open');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailureTime) return false;

    const elapsed = Date.now() - this.lastFailureTime.getTime();
    return elapsed >= this.options.timeout;
  }

  private onSuccess(): void {
    if (this.state === 'half-open') {
      this.successes++;

      if (this.successes >= this.options.successThreshold) {
        this.state = 'closed';
        this.failures = 0;
        this.successes = 0;
      }
    } else {
      this.failures = 0;
    }
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = new Date();

    if (this.state === 'half-open') {
      this.state = 'open';
      this.successes = 0;
    } else if (this.failures >= this.options.failureThreshold) {
      this.state = 'open';
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}

class CircuitOpenError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'CircuitOpenError';
  }
}

// Usage
const circuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 2,
  timeout: 30000,
});

try {
  const result = await circuitBreaker.execute(() => callExternalService());
} catch (error) {
  if (error instanceof CircuitOpenError) {
    // Handle circuit open - use fallback
    return fallbackValue;
  }
  throw error;
}
```

## Retry with Circuit Breaker

```typescript
interface RetryWithCircuitOptions {
  retry: ExponentialBackoffOptions;
  circuit: CircuitBreakerOptions;
}

class RetryWithCircuitBreaker {
  private circuitBreaker: CircuitBreaker;

  constructor(private readonly options: RetryWithCircuitOptions) {
    this.circuitBreaker = new CircuitBreaker(options.circuit);
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return this.circuitBreaker.execute(() =>
      retryWithExponentialBackoff(fn, this.options.retry)
    );
  }
}

// Usage
const resilientClient = new RetryWithCircuitBreaker({
  retry: {
    maxAttempts: 3,
    initialDelay: 1000,
    maxDelay: 10000,
    multiplier: 2,
  },
  circuit: {
    failureThreshold: 5,
    successThreshold: 2,
    timeout: 30000,
  },
});

const result = await resilientClient.execute(() => fetchData());
```

## Error Classification

```typescript
// Classify errors for retry decisions
class RetryableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'RetryableError';
  }
}

class NonRetryableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NonRetryableError';
  }
}

function isRetryable(error: Error): boolean {
  // Network errors
  if (error.message.includes('ECONNREFUSED')) return true;
  if (error.message.includes('ETIMEDOUT')) return true;
  if (error.message.includes('ENOTFOUND')) return true;

  // HTTP status codes
  if (error instanceof HttpError) {
    const retryableCodes = [408, 429, 500, 502, 503, 504];
    return retryableCodes.includes(error.statusCode);
  }

  // Explicit retry markers
  if (error instanceof RetryableError) return true;
  if (error instanceof NonRetryableError) return false;

  // Default to not retry for unknown errors
  return false;
}

// Usage with retry
await retryWithExponentialBackoff(fn, {
  ...options,
  shouldRetry: isRetryable,
});
```

## Rate Limiting with Retry

```typescript
class RateLimitedRetry {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private readonly tokensPerSecond: number,
    private readonly maxTokens: number
  ) {
    this.tokens = maxTokens;
    this.lastRefill = Date.now();
  }

  async execute<T>(fn: () => Promise<T>, retryOptions: ExponentialBackoffOptions): Promise<T> {
    await this.waitForToken();

    return retryWithExponentialBackoff(fn, {
      ...retryOptions,
      shouldRetry: (error) => {
        // Check for rate limit response
        if (error instanceof HttpError && error.statusCode === 429) {
          const retryAfter = error.headers?.['retry-after'];
          if (retryAfter) {
            // Respect server's retry-after header
            return true;
          }
        }
        return retryOptions.shouldRetry?.(error) ?? true;
      },
    });
  }

  private async waitForToken(): Promise<void> {
    this.refillTokens();

    if (this.tokens < 1) {
      const waitTime = (1 / this.tokensPerSecond) * 1000;
      await sleep(waitTime);
      this.refillTokens();
    }

    this.tokens--;
  }

  private refillTokens(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    const tokensToAdd = elapsed * this.tokensPerSecond;

    this.tokens = Math.min(this.tokens + tokensToAdd, this.maxTokens);
    this.lastRefill = now;
  }
}
```

## Message Queue Retry

```typescript
// BullMQ style retry configuration
interface QueueRetryOptions {
  attempts: number;
  backoff: {
    type: 'fixed' | 'exponential';
    delay: number;
  };
}

class MessageProcessor {
  async processWithRetry(
    message: Message,
    handler: (msg: Message) => Promise<void>,
    options: QueueRetryOptions
  ): Promise<void> {
    let attempt = 0;

    while (attempt < options.attempts) {
      attempt++;

      try {
        await handler(message);
        return;
      } catch (error) {
        if (attempt >= options.attempts) {
          // Move to dead letter queue
          await this.moveToDeadLetter(message, error);
          return;
        }

        const delay = this.calculateDelay(attempt, options.backoff);
        await this.scheduleRetry(message, delay);
        await sleep(delay);
      }
    }
  }

  private calculateDelay(
    attempt: number,
    backoff: QueueRetryOptions['backoff']
  ): number {
    if (backoff.type === 'exponential') {
      return backoff.delay * Math.pow(2, attempt - 1);
    }
    return backoff.delay;
  }

  private async moveToDeadLetter(message: Message, error: Error): Promise<void> {
    // Implementation
  }

  private async scheduleRetry(message: Message, delay: number): Promise<void> {
    // Implementation
  }
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use exponential backoff** | Prevent overwhelming failed services |
| **Add jitter** | Avoid thundering herd |
| **Set max attempts** | Prevent infinite retries |
| **Classify errors** | Only retry transient failures |
| **Use circuit breaker** | Fail fast when service is down |
| **Log retry attempts** | Enable debugging |
| **Monitor retry rates** | Detect systemic issues |

## Comparison

| Strategy | Pros | Cons |
|----------|------|------|
| Immediate | Fast recovery | Can overload |
| Fixed delay | Simple | Inefficient |
| Exponential | Prevents overload | Slower recovery |
| Jitter | Distributes load | More complex |
| Circuit breaker | Protects services | Needs tuning |
