# Distributed Systems Reference

## Resilience Patterns

### Circuit Breaker

Prevents cascading failures by detecting failures and temporarily blocking requests.

```typescript
enum CircuitState {
  CLOSED = 'CLOSED',     // Normal operation
  OPEN = 'OPEN',         // Failing, reject requests
  HALF_OPEN = 'HALF_OPEN' // Testing recovery
}

interface CircuitBreakerConfig {
  failureThreshold: number;    // Failures before opening
  successThreshold: number;    // Successes to close from half-open
  timeout: number;             // Time in open state before half-open
  volumeThreshold: number;     // Min requests before evaluating
}

class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failures: number = 0;
  private successes: number = 0;
  private lastFailureTime: number = 0;

  constructor(private config: CircuitBreakerConfig) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (!this.canExecute()) {
      throw new CircuitOpenError('Circuit breaker is open');
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

  private canExecute(): boolean {
    switch (this.state) {
      case CircuitState.CLOSED:
        return true;
      case CircuitState.OPEN:
        if (Date.now() - this.lastFailureTime >= this.config.timeout) {
          this.state = CircuitState.HALF_OPEN;
          return true;
        }
        return false;
      case CircuitState.HALF_OPEN:
        return true;
    }
  }
}

// Usage
const circuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 3,
  timeout: 30000,
  volumeThreshold: 10,
});

const result = await circuitBreaker.execute(() => httpClient.get('/api/data'));
```

### Retry with Exponential Backoff

```typescript
interface RetryConfig {
  maxRetries: number;
  initialDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableErrors?: (error: Error) => boolean;
}

class RetryPolicy {
  constructor(private config: RetryConfig) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error;

    for (let attempt = 0; attempt <= this.config.maxRetries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        if (!this.shouldRetry(error, attempt)) throw error;
        await this.sleep(this.calculateDelay(attempt));
      }
    }
    throw lastError!;
  }

  private calculateDelay(attempt: number): number {
    const delay = this.config.initialDelay * Math.pow(this.config.backoffMultiplier, attempt);
    const jitter = Math.random() * delay * 0.1; // 10% jitter
    return Math.min(delay + jitter, this.config.maxDelay);
  }
}

// Usage
const retry = new RetryPolicy({
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
});

const data = await retry.execute(() => apiClient.fetchData());
```

### Bulkhead (Isolation)

```typescript
class Bulkhead {
  private permits: number;
  private waitQueue: Array<() => void> = [];

  constructor(private maxConcurrent: number) {
    this.permits = maxConcurrent;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }

  private acquire(): Promise<void> {
    if (this.permits > 0) {
      this.permits--;
      return Promise.resolve();
    }
    return new Promise((resolve) => this.waitQueue.push(resolve));
  }

  private release(): void {
    if (this.waitQueue.length > 0) {
      this.waitQueue.shift()!();
    } else {
      this.permits++;
    }
  }
}

// Isolate different operations
class ResilientService {
  private bulkheads = {
    database: new Bulkhead(10),
    externalApi: new Bulkhead(5),
    cache: new Bulkhead(20),
  };

  queryDatabase<T>(query: () => Promise<T>): Promise<T> {
    return this.bulkheads.database.execute(query);
  }

  callExternalApi<T>(request: () => Promise<T>): Promise<T> {
    return this.bulkheads.externalApi.execute(request);
  }
}
```

### Timeout

```typescript
class TimeoutPolicy {
  constructor(private timeoutMs: number) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return Promise.race([fn(), this.createTimeout()]);
  }

  private createTimeout(): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => reject(new TimeoutError(`Timed out after ${this.timeoutMs}ms`)), this.timeoutMs);
    });
  }
}

// With cancellation
class CancellableTimeout {
  async execute<T>(fn: (signal: AbortSignal) => Promise<T>, timeoutMs: number): Promise<T> {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fn(controller.signal);
    } finally {
      clearTimeout(timeout);
    }
  }
}
```

### Fallback

```typescript
class FallbackPolicy<T> {
  constructor(
    private primary: () => Promise<T>,
    private fallback: () => Promise<T>
  ) {}

  async execute(): Promise<T> {
    try {
      return await this.primary();
    } catch {
      return await this.fallback();
    }
  }
}

// Graceful degradation
class GracefulDegradation {
  async getRecommendations(userId: string): Promise<Recommendation[]> {
    try {
      return await this.mlService.getPersonalized(userId);
    } catch {
      try {
        return await this.productService.getPopular();
      } catch {
        return this.getStaticDefaults();
      }
    }
  }
}
```

### Combined Policy

```typescript
class ResiliencePolicy<T> {
  private policies: Array<(fn: () => Promise<T>) => Promise<T>> = [];

  withTimeout(ms: number): this {
    this.policies.push((fn) => new TimeoutPolicy(ms).execute(fn));
    return this;
  }

  withRetry(config: RetryConfig): this {
    this.policies.push((fn) => new RetryPolicy(config).execute(fn));
    return this;
  }

  withCircuitBreaker(config: CircuitBreakerConfig): this {
    const cb = new CircuitBreaker(config);
    this.policies.push((fn) => cb.execute(fn));
    return this;
  }

  withBulkhead(maxConcurrent: number): this {
    const bulkhead = new Bulkhead(maxConcurrent);
    this.policies.push((fn) => bulkhead.execute(fn));
    return this;
  }

  withFallback(fallbackFn: () => Promise<T>): this {
    this.policies.push(async (fn) => {
      try { return await fn(); }
      catch { return await fallbackFn(); }
    });
    return this;
  }

  async execute(fn: () => Promise<T>): Promise<T> {
    let wrapped = fn;
    for (const policy of [...this.policies].reverse()) {
      const current = wrapped;
      wrapped = () => policy(current);
    }
    return wrapped();
  }
}

// Usage
const policy = new ResiliencePolicy<User>()
  .withTimeout(5000)
  .withRetry({ maxRetries: 3, initialDelay: 1000, maxDelay: 10000, backoffMultiplier: 2 })
  .withCircuitBreaker({ failureThreshold: 5, successThreshold: 3, timeout: 30000, volumeThreshold: 10 })
  .withBulkhead(10)
  .withFallback(async () => ({ id: '', name: 'Guest' }));

const user = await policy.execute(() => userService.getUser(userId));
```

## Communication Patterns

### Synchronous (REST/gRPC)

```typescript
class ProductServiceClient {
  constructor(
    private http: HttpClient,
    private circuitBreaker: CircuitBreaker
  ) {}

  async getProduct(id: string): Promise<Product> {
    return this.circuitBreaker.execute(() =>
      this.http.get(`${PRODUCT_SERVICE_URL}/products/${id}`)
    );
  }
}
```

### Asynchronous (Events/Messages)

```typescript
class OrderEventPublisher {
  constructor(private messageBroker: MessageBroker) {}

  async publishOrderCreated(order: Order): Promise<void> {
    await this.messageBroker.publish('order.created', {
      orderId: order.id,
      customerId: order.customerId,
      items: order.items,
      total: order.total,
      timestamp: new Date().toISOString(),
    });
  }
}

class OrderEventsConsumer {
  constructor(private notificationService: NotificationService) {}

  @Subscribe('order.created')
  async onOrderCreated(event: OrderCreatedEvent): Promise<void> {
    await this.notificationService.sendOrderConfirmation(event);
  }
}
```

## Consistency Patterns

### Saga Pattern

```typescript
interface SagaStep<C> {
  name: string;
  execute(ctx: C): Promise<void>;
  compensate(ctx: C): Promise<void>;
}

class CreateOrderSaga {
  private steps: SagaStep<OrderContext>[] = [
    {
      name: 'reserve_inventory',
      execute: async (ctx) => {
        ctx.reservationId = await this.inventory.reserve(ctx.items);
      },
      compensate: async (ctx) => {
        await this.inventory.cancelReservation(ctx.reservationId);
      },
    },
    {
      name: 'process_payment',
      execute: async (ctx) => {
        ctx.paymentId = await this.payment.charge(ctx.customerId, ctx.total);
      },
      compensate: async (ctx) => {
        await this.payment.refund(ctx.paymentId);
      },
    },
    {
      name: 'confirm_order',
      execute: async (ctx) => {
        await this.orderRepo.confirm(ctx.orderId);
      },
      compensate: async (ctx) => {
        await this.orderRepo.cancel(ctx.orderId);
      },
    },
  ];

  async execute(command: CreateOrderCommand): Promise<SagaResult> {
    const context = { ...command };
    const completedSteps: SagaStep<OrderContext>[] = [];

    try {
      for (const step of this.steps) {
        await step.execute(context);
        completedSteps.push(step);
      }
      return { success: true };
    } catch (error) {
      // Compensate in reverse order
      for (const step of completedSteps.reverse()) {
        await step.compensate(context).catch(console.error);
      }
      return { success: false, error: error.message };
    }
  }
}
```

### Outbox Pattern

```typescript
// Ensure message publishing with transaction
class OrderService {
  async createOrder(dto: CreateOrderDTO): Promise<Order> {
    return this.db.transaction(async (tx) => {
      // Create order
      const order = await tx.orders.create(dto);

      // Write to outbox table (same transaction)
      await tx.outbox.create({
        aggregateType: 'Order',
        aggregateId: order.id,
        eventType: 'OrderCreated',
        payload: JSON.stringify(order),
      });

      return order;
    });
  }
}

// Separate process publishes outbox messages
class OutboxProcessor {
  async processOutbox(): Promise<void> {
    const messages = await this.db.outbox.findUnpublished();

    for (const msg of messages) {
      await this.messageBroker.publish(msg.eventType, msg.payload);
      await this.db.outbox.markPublished(msg.id);
    }
  }
}
```

## Health Checks

```typescript
interface HealthCheck {
  name: string;
  check(): Promise<HealthStatus>;
}

interface HealthStatus {
  status: 'healthy' | 'unhealthy' | 'degraded';
  details?: Record<string, any>;
  duration?: number;
}

class HealthCheckRegistry {
  private checks: HealthCheck[] = [];

  register(check: HealthCheck): void {
    this.checks.push(check);
  }

  async checkAll(): Promise<SystemHealth> {
    const results = new Map<string, HealthStatus>();
    let overall: 'healthy' | 'unhealthy' | 'degraded' = 'healthy';

    await Promise.all(this.checks.map(async (check) => {
      const start = Date.now();
      try {
        const status = await check.check();
        status.duration = Date.now() - start;
        results.set(check.name, status);
        if (status.status === 'unhealthy') overall = 'unhealthy';
        else if (status.status === 'degraded' && overall === 'healthy') overall = 'degraded';
      } catch (error) {
        results.set(check.name, {
          status: 'unhealthy',
          details: { error: error.message },
          duration: Date.now() - start,
        });
        overall = 'unhealthy';
      }
    }));

    return { status: overall, checks: Object.fromEntries(results) };
  }
}

// Kubernetes liveness vs readiness
class KubernetesHealthChecks {
  async livenessCheck(): Promise<HealthStatus> {
    return { status: 'healthy' }; // Can we respond at all?
  }

  async readinessCheck(): Promise<SystemHealth> {
    return this.registry.checkAll(); // Can we handle traffic?
  }
}
```

## Pattern Selection

| Pattern | Protection Against | Trade-off |
|---------|-------------------|-----------|
| Circuit Breaker | Cascading failures | May reject valid requests |
| Retry + Backoff | Transient failures | Increased latency |
| Bulkhead | Resource exhaustion | Limited throughput |
| Timeout | Hanging requests | May cut valid operations |
| Fallback | Complete failure | Degraded functionality |

## When to Use

| Scenario | Recommended Pattern |
|----------|-------------------|
| External service calls | Circuit Breaker + Retry |
| Database connections | Connection pooling + Timeout |
| Critical vs non-critical ops | Bulkhead isolation |
| Uncertain latency operations | Timeout |
| Acceptable degradation | Fallback |
| Distributed transactions | Saga |
| Message reliability | Outbox |
