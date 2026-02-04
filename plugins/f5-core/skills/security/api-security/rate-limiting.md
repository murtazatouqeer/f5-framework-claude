---
name: rate-limiting
description: Rate limiting and throttling implementations
category: security/api-security
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Rate Limiting

## Overview

Rate limiting protects APIs from abuse, DoS attacks, and ensures
fair usage across all clients.

## Rate Limiting Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| Fixed Window | Count requests in fixed time windows | Simple implementation |
| Sliding Window | Rolling window with partial counts | Smoother distribution |
| Token Bucket | Tokens replenish over time | Burst allowance |
| Leaky Bucket | Constant rate outflow | Strict rate enforcement |

## Implementation

### Fixed Window

```typescript
// services/rate-limiter/fixed-window.ts
export class FixedWindowRateLimiter {
  constructor(private redis: Redis) {}

  async isAllowed(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<RateLimitResult> {
    const windowStart = Math.floor(Date.now() / 1000 / windowSeconds) * windowSeconds;
    const redisKey = `rate:${key}:${windowStart}`;

    const current = await this.redis.incr(redisKey);

    if (current === 1) {
      await this.redis.expire(redisKey, windowSeconds);
    }

    const remaining = Math.max(0, limit - current);
    const resetAt = windowStart + windowSeconds;

    return {
      allowed: current <= limit,
      remaining,
      resetAt,
      limit,
    };
  }
}
```

### Sliding Window Log

```typescript
// services/rate-limiter/sliding-window.ts
export class SlidingWindowRateLimiter {
  constructor(private redis: Redis) {}

  async isAllowed(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<RateLimitResult> {
    const now = Date.now();
    const windowStart = now - windowSeconds * 1000;
    const redisKey = `rate:${key}`;

    // Use sorted set to store timestamps
    await this.redis
      .multi()
      .zremrangebyscore(redisKey, 0, windowStart)
      .zadd(redisKey, now, `${now}`)
      .zcard(redisKey)
      .expire(redisKey, windowSeconds)
      .exec();

    const count = await this.redis.zcard(redisKey);
    const remaining = Math.max(0, limit - count);

    return {
      allowed: count <= limit,
      remaining,
      resetAt: Math.ceil((windowStart + windowSeconds * 1000) / 1000),
      limit,
    };
  }
}
```

### Token Bucket

```typescript
// services/rate-limiter/token-bucket.ts
export class TokenBucketRateLimiter {
  constructor(private redis: Redis) {}

  async isAllowed(
    key: string,
    bucketSize: number,
    refillRate: number, // tokens per second
    tokensRequired: number = 1
  ): Promise<RateLimitResult> {
    const redisKey = `bucket:${key}`;
    const now = Date.now();

    // Lua script for atomic token bucket operation
    const script = `
      local key = KEYS[1]
      local bucket_size = tonumber(ARGV[1])
      local refill_rate = tonumber(ARGV[2])
      local now = tonumber(ARGV[3])
      local tokens_required = tonumber(ARGV[4])

      local bucket = redis.call('HMGET', key, 'tokens', 'last_update')
      local tokens = tonumber(bucket[1]) or bucket_size
      local last_update = tonumber(bucket[2]) or now

      -- Calculate tokens to add based on time elapsed
      local elapsed = (now - last_update) / 1000
      local tokens_to_add = elapsed * refill_rate
      tokens = math.min(bucket_size, tokens + tokens_to_add)

      local allowed = 0
      if tokens >= tokens_required then
        tokens = tokens - tokens_required
        allowed = 1
      end

      redis.call('HMSET', key, 'tokens', tokens, 'last_update', now)
      redis.call('EXPIRE', key, 3600)

      return {allowed, math.floor(tokens), bucket_size}
    `;

    const result = await this.redis.eval(
      script,
      1,
      redisKey,
      bucketSize,
      refillRate,
      now,
      tokensRequired
    ) as number[];

    return {
      allowed: result[0] === 1,
      remaining: result[1],
      limit: result[2],
      resetAt: Math.ceil(now / 1000) + Math.ceil((bucketSize - result[1]) / refillRate),
    };
  }
}
```

### Express Middleware

```typescript
// middleware/rate-limit.middleware.ts
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';

// Basic rate limiter
export const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  standardHeaders: true, // Return rate limit info in headers
  legacyHeaders: false,
  message: {
    error: 'Too many requests',
    retryAfter: 'See Retry-After header',
  },
  store: new RedisStore({
    client: redisClient,
    prefix: 'rl:api:',
  }),
  keyGenerator: (req) => {
    // Use user ID if authenticated, otherwise IP
    return req.user?.id || req.ip;
  },
});

// Strict limiter for sensitive endpoints
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // 5 attempts per window
  skipSuccessfulRequests: true,
  store: new RedisStore({
    client: redisClient,
    prefix: 'rl:auth:',
  }),
  handler: (req, res) => {
    res.status(429).json({
      error: 'Too many login attempts',
      retryAfter: Math.ceil(req.rateLimit.resetTime / 1000),
    });
  },
});

// Dynamic rate limiter based on user tier
export const tieredLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: (req) => {
    const tier = req.user?.subscriptionTier || 'free';
    const limits = {
      free: 10,
      basic: 50,
      premium: 200,
      enterprise: 1000,
    };
    return limits[tier] || 10;
  },
  standardHeaders: true,
  store: new RedisStore({
    client: redisClient,
    prefix: 'rl:tiered:',
  }),
});
```

### Distributed Rate Limiting

```typescript
// services/distributed-rate-limiter.ts
export class DistributedRateLimiter {
  constructor(
    private redis: Redis,
    private config: RateLimitConfig
  ) {}

  async checkLimit(identifier: string): Promise<RateLimitResult> {
    const rules = this.getRulesForIdentifier(identifier);
    const results: RateLimitResult[] = [];

    // Check all applicable rules
    for (const rule of rules) {
      const result = await this.checkRule(identifier, rule);
      results.push(result);

      // If any rule denies, stop early
      if (!result.allowed) {
        return result;
      }
    }

    // Return the most restrictive result
    return results.reduce((most, current) => {
      if (current.remaining < most.remaining) return current;
      return most;
    });
  }

  private getRulesForIdentifier(identifier: string): RateLimitRule[] {
    // Could be user-specific, API key-specific, or default
    return this.config.rules.filter(rule => rule.matches(identifier));
  }

  private async checkRule(
    identifier: string,
    rule: RateLimitRule
  ): Promise<RateLimitResult> {
    const key = `rate:${rule.name}:${identifier}`;

    // Use sliding window counter with Redis
    const now = Date.now();
    const windowStart = now - rule.windowMs;

    const pipeline = this.redis.pipeline();
    pipeline.zremrangebyscore(key, 0, windowStart);
    pipeline.zadd(key, now, `${now}-${Math.random()}`);
    pipeline.zcard(key);
    pipeline.expire(key, Math.ceil(rule.windowMs / 1000));

    const results = await pipeline.exec();
    const count = results[2][1] as number;

    return {
      allowed: count <= rule.max,
      remaining: Math.max(0, rule.max - count),
      resetAt: Math.ceil((windowStart + rule.windowMs) / 1000),
      limit: rule.max,
      rule: rule.name,
    };
  }
}
```

## Response Headers

```typescript
// Add rate limit headers to responses
export function rateLimitHeaders(result: RateLimitResult) {
  return {
    'X-RateLimit-Limit': result.limit.toString(),
    'X-RateLimit-Remaining': result.remaining.toString(),
    'X-RateLimit-Reset': result.resetAt.toString(),
    'Retry-After': result.allowed ? undefined : (result.resetAt - Math.floor(Date.now() / 1000)).toString(),
  };
}

// Middleware to add headers
export function rateLimitHeadersMiddleware(limiter: RateLimiter) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const result = await limiter.checkLimit(req.user?.id || req.ip);

    // Add headers
    const headers = rateLimitHeaders(result);
    for (const [key, value] of Object.entries(headers)) {
      if (value) res.setHeader(key, value);
    }

    if (!result.allowed) {
      return res.status(429).json({
        error: 'Rate limit exceeded',
        retryAfter: headers['Retry-After'],
      });
    }

    next();
  };
}
```

## API Key Rate Limiting

```typescript
// Per-API-key rate limiting
export class ApiKeyRateLimiter {
  constructor(
    private redis: Redis,
    private apiKeyService: ApiKeyService
  ) {}

  async checkLimit(apiKey: string): Promise<RateLimitResult> {
    const keyInfo = await this.apiKeyService.getKeyInfo(apiKey);
    if (!keyInfo) {
      throw new Error('Invalid API key');
    }

    const limit = keyInfo.rateLimit || 1000; // Default 1000/hour
    const window = keyInfo.rateLimitWindow || 3600; // Default 1 hour

    return this.checkRateLimit(apiKey, limit, window);
  }

  async trackUsage(apiKey: string, endpoint: string): Promise<void> {
    const now = new Date();
    const hourKey = `usage:${apiKey}:${now.toISOString().slice(0, 13)}`;

    await this.redis.hincrby(hourKey, endpoint, 1);
    await this.redis.expire(hourKey, 86400 * 30); // Keep 30 days

    // Also track daily totals
    const dayKey = `usage:${apiKey}:${now.toISOString().slice(0, 10)}`;
    await this.redis.hincrby(dayKey, 'total', 1);
    await this.redis.expire(dayKey, 86400 * 90); // Keep 90 days
  }
}
```

## Cost-Based Rate Limiting

```typescript
// Different endpoints have different costs
export const endpointCosts: Record<string, number> = {
  'GET /api/users': 1,
  'POST /api/users': 5,
  'GET /api/reports': 10,
  'POST /api/ai/generate': 50,
};

export class CostBasedRateLimiter {
  constructor(private tokenBucket: TokenBucketRateLimiter) {}

  async checkLimit(
    identifier: string,
    endpoint: string
  ): Promise<RateLimitResult> {
    const cost = endpointCosts[endpoint] || 1;

    return this.tokenBucket.isAllowed(
      identifier,
      100,  // bucket size
      1,    // refill rate (tokens/second)
      cost  // tokens required
    );
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Use Redis | Centralized storage for distributed systems |
| Return headers | Always include rate limit headers |
| Graceful degradation | Queue vs reject when possible |
| Per-resource limits | Different limits for different endpoints |
| User-based limits | Higher limits for authenticated users |
| Burst allowance | Use token bucket for occasional spikes |
