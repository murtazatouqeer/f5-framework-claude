---
name: resilience-patterns
description: Patterns for building resilient distributed systems
category: architecture/distributed-systems
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Resilience Patterns

## Overview

Resilience patterns help systems handle failures gracefully, recover quickly,
and continue operating under adverse conditions. These patterns are essential
for distributed systems where partial failures are inevitable.

## Circuit Breaker

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
  private requestCount: number = 0;

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
    this.requestCount++;

    switch (this.state) {
      case CircuitState.CLOSED:
        return true;

      case CircuitState.OPEN:
        if (Date.now() - this.lastFailureTime >= this.config.timeout) {
          this.state = CircuitState.HALF_OPEN;
          this.successes = 0;
          return true;
        }
        return false;

      case CircuitState.HALF_OPEN:
        return true;
    }
  }

  private onSuccess(): void {
    this.failures = 0;

    if (this.state === CircuitState.HALF_OPEN) {
      this.successes++;
      if (this.successes >= this.config.successThreshold) {
        this.state = CircuitState.CLOSED;
      }
    }
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.state === CircuitState.HALF_OPEN) {
      this.state = CircuitState.OPEN;
    } else if (
      this.requestCount >= this.config.volumeThreshold &&
      this.failures >= this.config.failureThreshold
    ) {
      this.state = CircuitState.OPEN;
    }
  }

  getState(): CircuitState {
    return this.state;
  }

  getMetrics(): CircuitMetrics {
    return {
      state: this.state,
      failures: this.failures,
      successes: this.successes,
      requestCount: this.requestCount,
    };
  }
}

// Usage
const circuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  successThreshold: 3,
  timeout: 30000,
  volumeThreshold: 10,
});

async function callExternalService(): Promise<Response> {
  return circuitBreaker.execute(async () => {
    return await httpClient.get('https://api.example.com/data');
  });
}
```

## Retry with Backoff

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

        if (!this.shouldRetry(error, attempt)) {
          throw error;
        }

        const delay = this.calculateDelay(attempt);
        await this.sleep(delay);
      }
    }

    throw lastError!;
  }

  private shouldRetry(error: Error, attempt: number): boolean {
    if (attempt >= this.config.maxRetries) {
      return false;
    }

    if (this.config.retryableErrors) {
      return this.config.retryableErrors(error);
    }

    // Default: retry on network and server errors
    return this.isRetryableError(error);
  }

  private isRetryableError(error: any): boolean {
    const retryableCodes = [408, 429, 500, 502, 503, 504];
    return retryableCodes.includes(error.status || error.response?.status);
  }

  private calculateDelay(attempt: number): number {
    const delay = this.config.initialDelay * Math.pow(this.config.backoffMultiplier, attempt);
    const jitter = Math.random() * delay * 0.1; // 10% jitter
    return Math.min(delay + jitter, this.config.maxDelay);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Exponential backoff with jitter
const retryPolicy = new RetryPolicy({
  maxRetries: 3,
  initialDelay: 1000,
  maxDelay: 30000,
  backoffMultiplier: 2,
  retryableErrors: (error) => {
    return error.name === 'NetworkError' || error.status >= 500;
  },
});

// Usage
const result = await retryPolicy.execute(async () => {
  return await apiClient.fetchData();
});
```

## Bulkhead (Isolation)

```typescript
// Semaphore-based bulkhead
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

    return new Promise((resolve) => {
      this.waitQueue.push(resolve);
    });
  }

  private release(): void {
    if (this.waitQueue.length > 0) {
      const next = this.waitQueue.shift()!;
      next();
    } else {
      this.permits++;
    }
  }

  getMetrics(): BulkheadMetrics {
    return {
      availablePermits: this.permits,
      maxConcurrent: this.maxConcurrent,
      queueLength: this.waitQueue.length,
    };
  }
}

// Thread pool bulkhead
class ThreadPoolBulkhead {
  private pool: WorkerPool;
  private queue: Array<QueuedTask> = [];

  constructor(
    private coreSize: number,
    private maxSize: number,
    private queueCapacity: number
  ) {
    this.pool = new WorkerPool(coreSize, maxSize);
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.pool.hasAvailableWorker()) {
      return this.pool.submit(fn);
    }

    if (this.queue.length >= this.queueCapacity) {
      throw new BulkheadFullError('Bulkhead queue is full');
    }

    return new Promise((resolve, reject) => {
      this.queue.push({ fn, resolve, reject });
    });
  }
}

// Service with isolated bulkheads
class ResilientService {
  private bulkheads: Map<string, Bulkhead> = new Map();

  constructor() {
    // Separate bulkheads for different operations
    this.bulkheads.set('database', new Bulkhead(10));
    this.bulkheads.set('external-api', new Bulkhead(5));
    this.bulkheads.set('cache', new Bulkhead(20));
  }

  async queryDatabase<T>(query: () => Promise<T>): Promise<T> {
    return this.bulkheads.get('database')!.execute(query);
  }

  async callExternalApi<T>(request: () => Promise<T>): Promise<T> {
    return this.bulkheads.get('external-api')!.execute(request);
  }

  async accessCache<T>(operation: () => Promise<T>): Promise<T> {
    return this.bulkheads.get('cache')!.execute(operation);
  }
}
```

## Timeout

```typescript
class TimeoutPolicy {
  constructor(private timeoutMs: number) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return Promise.race([
      fn(),
      this.createTimeout(),
    ]);
  }

  private createTimeout(): Promise<never> {
    return new Promise((_, reject) => {
      setTimeout(() => {
        reject(new TimeoutError(`Operation timed out after ${this.timeoutMs}ms`));
      }, this.timeoutMs);
    });
  }
}

// Timeout with cancellation
class CancellableTimeout {
  private controller: AbortController;

  constructor(private timeoutMs: number) {
    this.controller = new AbortController();
  }

  async execute<T>(fn: (signal: AbortSignal) => Promise<T>): Promise<T> {
    const timeout = setTimeout(() => {
      this.controller.abort();
    }, this.timeoutMs);

    try {
      return await fn(this.controller.signal);
    } finally {
      clearTimeout(timeout);
    }
  }
}

// Usage
const timeout = new CancellableTimeout(5000);

const result = await timeout.execute(async (signal) => {
  return await fetch('https://api.example.com/data', { signal });
});
```

## Fallback

```typescript
interface FallbackConfig<T> {
  primary: () => Promise<T>;
  fallback: () => Promise<T>;
  shouldFallback?: (error: Error) => boolean;
}

class FallbackPolicy<T> {
  constructor(private config: FallbackConfig<T>) {}

  async execute(): Promise<T> {
    try {
      return await this.config.primary();
    } catch (error) {
      if (this.config.shouldFallback && !this.config.shouldFallback(error)) {
        throw error;
      }
      return await this.config.fallback();
    }
  }
}

// Cache fallback
class CacheFallback<T> {
  constructor(
    private cache: Cache,
    private primary: () => Promise<T>,
    private cacheKey: string
  ) {}

  async execute(): Promise<T> {
    try {
      const result = await this.primary();
      await this.cache.set(this.cacheKey, result);
      return result;
    } catch (error) {
      const cached = await this.cache.get<T>(this.cacheKey);
      if (cached) {
        return cached;
      }
      throw error;
    }
  }
}

// Graceful degradation
class GracefulDegradation {
  async getProductRecommendations(userId: string): Promise<Recommendation[]> {
    try {
      // Primary: personalized recommendations
      return await this.mlService.getPersonalizedRecommendations(userId);
    } catch {
      try {
        // Fallback 1: popular items
        return await this.productService.getPopularItems();
      } catch {
        // Fallback 2: static defaults
        return this.getDefaultRecommendations();
      }
    }
  }
}
```

## Rate Limiting

```typescript
// Token bucket algorithm
class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(
    private capacity: number,
    private refillRate: number // tokens per second
  ) {
    this.tokens = capacity;
    this.lastRefill = Date.now();
  }

  tryAcquire(tokens: number = 1): boolean {
    this.refill();

    if (this.tokens >= tokens) {
      this.tokens -= tokens;
      return true;
    }

    return false;
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    const tokensToAdd = elapsed * this.refillRate;

    this.tokens = Math.min(this.capacity, this.tokens + tokensToAdd);
    this.lastRefill = now;
  }
}

// Sliding window rate limiter
class SlidingWindowRateLimiter {
  private requests: Map<string, number[]> = new Map();

  constructor(
    private windowMs: number,
    private maxRequests: number
  ) {}

  isAllowed(key: string): boolean {
    const now = Date.now();
    const windowStart = now - this.windowMs;

    let timestamps = this.requests.get(key) || [];

    // Remove old timestamps
    timestamps = timestamps.filter(t => t > windowStart);

    if (timestamps.length >= this.maxRequests) {
      return false;
    }

    timestamps.push(now);
    this.requests.set(key, timestamps);

    return true;
  }

  getRemainingRequests(key: string): number {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    const timestamps = this.requests.get(key) || [];
    const validTimestamps = timestamps.filter(t => t > windowStart);

    return Math.max(0, this.maxRequests - validTimestamps.length);
  }
}

// Rate limiter middleware
class RateLimiterMiddleware {
  constructor(private limiter: SlidingWindowRateLimiter) {}

  handle(req: Request, res: Response, next: NextFunction): void {
    const key = req.ip || req.headers['x-forwarded-for'] as string;

    if (!this.limiter.isAllowed(key)) {
      res.status(429).json({
        error: 'Too many requests',
        retryAfter: this.getRetryAfter(key),
      });
      return;
    }

    res.setHeader('X-RateLimit-Remaining', this.limiter.getRemainingRequests(key));
    next();
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
    const results: Map<string, HealthStatus> = new Map();
    let overallStatus: 'healthy' | 'unhealthy' | 'degraded' = 'healthy';

    await Promise.all(this.checks.map(async (check) => {
      const start = Date.now();

      try {
        const status = await check.check();
        status.duration = Date.now() - start;
        results.set(check.name, status);

        if (status.status === 'unhealthy') {
          overallStatus = 'unhealthy';
        } else if (status.status === 'degraded' && overallStatus === 'healthy') {
          overallStatus = 'degraded';
        }
      } catch (error) {
        results.set(check.name, {
          status: 'unhealthy',
          details: { error: error.message },
          duration: Date.now() - start,
        });
        overallStatus = 'unhealthy';
      }
    }));

    return { status: overallStatus, checks: Object.fromEntries(results) };
  }
}

// Health check implementations
class DatabaseHealthCheck implements HealthCheck {
  name = 'database';

  constructor(private db: Database) {}

  async check(): Promise<HealthStatus> {
    try {
      await this.db.query('SELECT 1');
      return { status: 'healthy' };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: { error: error.message },
      };
    }
  }
}

class ExternalServiceHealthCheck implements HealthCheck {
  name = 'external-api';

  constructor(
    private serviceUrl: string,
    private timeoutMs: number = 5000
  ) {}

  async check(): Promise<HealthStatus> {
    try {
      const response = await fetch(`${this.serviceUrl}/health`, {
        signal: AbortSignal.timeout(this.timeoutMs),
      });

      if (response.ok) {
        return { status: 'healthy' };
      }

      return {
        status: 'degraded',
        details: { statusCode: response.status },
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        details: { error: error.message },
      };
    }
  }
}

// Liveness vs Readiness
class KubernetesHealthChecks {
  private registry: HealthCheckRegistry;

  // Liveness: Is the application running?
  async livenessCheck(): Promise<HealthStatus> {
    // Simple check - if we can respond, we're alive
    return { status: 'healthy' };
  }

  // Readiness: Can the application handle traffic?
  async readinessCheck(): Promise<SystemHealth> {
    // Check all dependencies
    return this.registry.checkAll();
  }
}
```

## Combined Resilience Policy

```typescript
// Policy builder for combining patterns
class ResiliencePolicy<T> {
  private policies: Array<(fn: () => Promise<T>) => Promise<T>> = [];

  withTimeout(ms: number): this {
    const timeout = new TimeoutPolicy(ms);
    this.policies.push((fn) => timeout.execute(fn));
    return this;
  }

  withRetry(config: RetryConfig): this {
    const retry = new RetryPolicy(config);
    this.policies.push((fn) => retry.execute(fn));
    return this;
  }

  withCircuitBreaker(config: CircuitBreakerConfig): this {
    const circuitBreaker = new CircuitBreaker(config);
    this.policies.push((fn) => circuitBreaker.execute(fn));
    return this;
  }

  withBulkhead(maxConcurrent: number): this {
    const bulkhead = new Bulkhead(maxConcurrent);
    this.policies.push((fn) => bulkhead.execute(fn));
    return this;
  }

  withFallback(fallbackFn: () => Promise<T>): this {
    this.policies.push(async (fn) => {
      try {
        return await fn();
      } catch {
        return await fallbackFn();
      }
    });
    return this;
  }

  async execute(fn: () => Promise<T>): Promise<T> {
    // Apply policies in order (innermost first)
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
  .withFallback(async () => ({ id: '', name: 'Guest', email: '' }));

const user = await policy.execute(async () => {
  return await userService.getUser(userId);
});
```

## Benefits

| Pattern | Protection Against | Trade-off |
|---------|-------------------|-----------|
| Circuit Breaker | Cascading failures | May reject valid requests |
| Retry | Transient failures | Increased latency |
| Bulkhead | Resource exhaustion | Limited throughput |
| Timeout | Hanging requests | May cut off valid operations |
| Fallback | Complete failure | Degraded functionality |
| Rate Limiting | Overload | Request rejection |

## When to Use

- **Circuit Breaker**: External service calls, database connections
- **Retry**: Network requests, distributed operations
- **Bulkhead**: Isolating critical from non-critical operations
- **Timeout**: Any I/O operation with uncertain latency
- **Fallback**: When degraded operation is acceptable
- **Rate Limiting**: Public APIs, shared resources
