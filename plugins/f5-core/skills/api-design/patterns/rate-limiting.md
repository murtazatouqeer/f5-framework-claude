---
name: rate-limiting
description: API rate limiting patterns and implementation
category: api-design/patterns
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Rate Limiting Patterns

## Overview

Rate limiting protects APIs from abuse, ensures fair usage, and maintains
service stability. This guide covers rate limiting strategies, algorithms,
and implementation patterns.

## Rate Limiting Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                Rate Limiting Strategies                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  By Identity                                                    │
│  ├── API Key / User ID                                          │
│  ├── IP Address                                                 │
│  ├── Organization / Tenant                                      │
│  └── Combination (user + IP)                                    │
│                                                                  │
│  By Resource                                                    │
│  ├── Global (all endpoints)                                     │
│  ├── Per Endpoint                                               │
│  ├── Per Operation Type (read vs write)                         │
│  └── Per Resource (specific user, document)                     │
│                                                                  │
│  By Time Window                                                 │
│  ├── Per Second (burst)                                         │
│  ├── Per Minute                                                 │
│  ├── Per Hour                                                   │
│  ├── Per Day                                                    │
│  └── Sliding Window                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Rate Limiting Algorithms

### Fixed Window

```typescript
/**
 * Fixed Window Counter
 * Simplest approach - count requests in fixed time windows
 */
class FixedWindowRateLimiter {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  async isAllowed(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number; reset: number }> {
    const now = Math.floor(Date.now() / 1000);
    const windowStart = Math.floor(now / windowSeconds) * windowSeconds;
    const windowKey = `ratelimit:${key}:${windowStart}`;

    const current = await this.redis.incr(windowKey);

    if (current === 1) {
      // First request in window, set expiry
      await this.redis.expire(windowKey, windowSeconds);
    }

    const reset = windowStart + windowSeconds;

    return {
      allowed: current <= limit,
      remaining: Math.max(0, limit - current),
      reset,
    };
  }
}

// Usage
const limiter = new FixedWindowRateLimiter(redis);
const result = await limiter.isAllowed(`user:${userId}`, 100, 60); // 100 per minute
```

### Sliding Window Log

```typescript
/**
 * Sliding Window Log
 * More accurate but uses more memory
 */
class SlidingWindowLogRateLimiter {
  private redis: Redis;

  async isAllowed(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number; reset: number }> {
    const now = Date.now();
    const windowStart = now - windowSeconds * 1000;
    const redisKey = `ratelimit:log:${key}`;

    // Remove old entries and add new one in transaction
    const multi = this.redis.multi();

    // Remove entries older than window
    multi.zremrangebyscore(redisKey, 0, windowStart);

    // Count current entries
    multi.zcard(redisKey);

    // Add current request
    multi.zadd(redisKey, now, `${now}:${Math.random()}`);

    // Set expiry
    multi.expire(redisKey, windowSeconds);

    const results = await multi.exec();
    const count = results[1][1] as number;

    const allowed = count < limit;
    if (!allowed) {
      // Remove the request we just added since it's not allowed
      await this.redis.zremrangebyscore(redisKey, now, now);
    }

    return {
      allowed,
      remaining: Math.max(0, limit - count - (allowed ? 1 : 0)),
      reset: Math.floor((now + windowSeconds * 1000) / 1000),
    };
  }
}
```

### Sliding Window Counter

```typescript
/**
 * Sliding Window Counter
 * Balanced approach - weighted average of current and previous window
 */
class SlidingWindowCounterRateLimiter {
  private redis: Redis;

  async isAllowed(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number; reset: number }> {
    const now = Math.floor(Date.now() / 1000);
    const currentWindow = Math.floor(now / windowSeconds) * windowSeconds;
    const previousWindow = currentWindow - windowSeconds;

    const currentKey = `ratelimit:${key}:${currentWindow}`;
    const previousKey = `ratelimit:${key}:${previousWindow}`;

    // Get counts from both windows
    const [currentCount, previousCount] = await this.redis.mget(currentKey, previousKey);

    // Calculate weighted count
    const elapsedInWindow = now - currentWindow;
    const previousWeight = 1 - elapsedInWindow / windowSeconds;
    const weightedCount =
      (parseInt(currentCount || '0', 10)) +
      (parseInt(previousCount || '0', 10)) * previousWeight;

    if (weightedCount >= limit) {
      return {
        allowed: false,
        remaining: 0,
        reset: currentWindow + windowSeconds,
      };
    }

    // Increment current window
    const multi = this.redis.multi();
    multi.incr(currentKey);
    multi.expire(currentKey, windowSeconds * 2);
    await multi.exec();

    return {
      allowed: true,
      remaining: Math.floor(limit - weightedCount - 1),
      reset: currentWindow + windowSeconds,
    };
  }
}
```

### Token Bucket

```typescript
/**
 * Token Bucket Algorithm
 * Allows bursts while maintaining average rate
 */
class TokenBucketRateLimiter {
  private redis: Redis;

  async isAllowed(
    key: string,
    bucketSize: number, // Max tokens (burst capacity)
    refillRate: number, // Tokens per second
    tokensRequired: number = 1
  ): Promise<{ allowed: boolean; remaining: number; reset: number }> {
    const now = Date.now() / 1000;
    const bucketKey = `bucket:${key}`;

    // Lua script for atomic token bucket
    const script = `
      local bucket_key = KEYS[1]
      local bucket_size = tonumber(ARGV[1])
      local refill_rate = tonumber(ARGV[2])
      local tokens_required = tonumber(ARGV[3])
      local now = tonumber(ARGV[4])

      -- Get current state
      local bucket = redis.call('HMGET', bucket_key, 'tokens', 'last_refill')
      local tokens = tonumber(bucket[1]) or bucket_size
      local last_refill = tonumber(bucket[2]) or now

      -- Calculate tokens to add
      local elapsed = now - last_refill
      local tokens_to_add = elapsed * refill_rate
      tokens = math.min(bucket_size, tokens + tokens_to_add)

      -- Check if request is allowed
      local allowed = tokens >= tokens_required
      if allowed then
        tokens = tokens - tokens_required
      end

      -- Save state
      redis.call('HMSET', bucket_key, 'tokens', tokens, 'last_refill', now)
      redis.call('EXPIRE', bucket_key, math.ceil(bucket_size / refill_rate) * 2)

      return {allowed and 1 or 0, math.floor(tokens)}
    `;

    const result = await this.redis.eval(
      script,
      1,
      bucketKey,
      bucketSize,
      refillRate,
      tokensRequired,
      now
    ) as [number, number];

    const [allowed, remaining] = result;
    const timeToRefill = (tokensRequired - remaining) / refillRate;

    return {
      allowed: allowed === 1,
      remaining,
      reset: Math.ceil(now + timeToRefill),
    };
  }
}
```

### Leaky Bucket

```typescript
/**
 * Leaky Bucket Algorithm
 * Smooths out bursts - requests processed at constant rate
 */
class LeakyBucketRateLimiter {
  private redis: Redis;

  async isAllowed(
    key: string,
    bucketSize: number, // Queue capacity
    leakRate: number // Requests processed per second
  ): Promise<{ allowed: boolean; remaining: number; waitTime: number }> {
    const now = Date.now() / 1000;
    const bucketKey = `leaky:${key}`;

    const script = `
      local bucket_key = KEYS[1]
      local bucket_size = tonumber(ARGV[1])
      local leak_rate = tonumber(ARGV[2])
      local now = tonumber(ARGV[3])

      -- Get current state
      local bucket = redis.call('HMGET', bucket_key, 'water', 'last_leak')
      local water = tonumber(bucket[1]) or 0
      local last_leak = tonumber(bucket[2]) or now

      -- Leak water (process requests)
      local elapsed = now - last_leak
      local leaked = elapsed * leak_rate
      water = math.max(0, water - leaked)

      -- Try to add water (new request)
      local allowed = water < bucket_size
      local wait_time = 0

      if allowed then
        water = water + 1
      else
        -- Calculate wait time until there's room
        wait_time = (water - bucket_size + 1) / leak_rate
      end

      -- Save state
      redis.call('HMSET', bucket_key, 'water', water, 'last_leak', now)
      redis.call('EXPIRE', bucket_key, math.ceil(bucket_size / leak_rate) * 2)

      return {allowed and 1 or 0, math.floor(bucket_size - water), wait_time}
    `;

    const result = await this.redis.eval(
      script,
      1,
      bucketKey,
      bucketSize,
      leakRate,
      now
    ) as [number, number, number];

    return {
      allowed: result[0] === 1,
      remaining: result[1],
      waitTime: result[2],
    };
  }
}
```

## Rate Limiting Middleware

```typescript
interface RateLimitConfig {
  // Requests per window
  limit: number;
  // Window in seconds
  window: number;
  // Key generator function
  keyGenerator?: (req: Request) => string;
  // Skip function
  skip?: (req: Request) => boolean;
  // Handler when rate limited
  handler?: (req: Request, res: Response) => void;
}

function rateLimit(config: RateLimitConfig) {
  const {
    limit,
    window,
    keyGenerator = defaultKeyGenerator,
    skip,
    handler = defaultHandler,
  } = config;

  const limiter = new SlidingWindowCounterRateLimiter(redis);

  return async (req: Request, res: Response, next: NextFunction) => {
    // Skip rate limiting for certain requests
    if (skip && skip(req)) {
      return next();
    }

    const key = keyGenerator(req);
    const result = await limiter.isAllowed(key, limit, window);

    // Set rate limit headers
    res.set({
      'X-RateLimit-Limit': limit.toString(),
      'X-RateLimit-Remaining': result.remaining.toString(),
      'X-RateLimit-Reset': result.reset.toString(),
    });

    if (!result.allowed) {
      res.set('Retry-After', (result.reset - Math.floor(Date.now() / 1000)).toString());
      return handler(req, res);
    }

    next();
  };
}

function defaultKeyGenerator(req: Request): string {
  // Prefer API key, fall back to IP
  if (req.apiKey) {
    return `apikey:${req.apiKey.id}`;
  }
  return `ip:${req.ip}`;
}

function defaultHandler(req: Request, res: Response): void {
  res.status(429).json({
    error: {
      code: 'RATE_LIMITED',
      message: 'Too many requests. Please try again later.',
      retry_after: parseInt(res.get('Retry-After') || '60', 10),
    },
  });
}

// Usage
app.use(
  '/api',
  rateLimit({
    limit: 100,
    window: 60, // 100 requests per minute
  })
);

// Different limits for different endpoints
app.post(
  '/api/orders',
  rateLimit({
    limit: 10,
    window: 60, // 10 orders per minute
  }),
  createOrder
);

app.get(
  '/api/search',
  rateLimit({
    limit: 30,
    window: 60, // 30 searches per minute
  }),
  search
);
```

## Tiered Rate Limits

```typescript
interface TierConfig {
  name: string;
  limits: {
    global: { requests: number; window: number };
    perEndpoint?: Record<string, { requests: number; window: number }>;
  };
}

const TIERS: Record<string, TierConfig> = {
  free: {
    name: 'Free',
    limits: {
      global: { requests: 100, window: 3600 }, // 100/hour
      perEndpoint: {
        'POST /orders': { requests: 5, window: 3600 },
        'POST /exports': { requests: 2, window: 86400 },
      },
    },
  },
  starter: {
    name: 'Starter',
    limits: {
      global: { requests: 1000, window: 3600 }, // 1000/hour
      perEndpoint: {
        'POST /orders': { requests: 100, window: 3600 },
        'POST /exports': { requests: 10, window: 86400 },
      },
    },
  },
  pro: {
    name: 'Pro',
    limits: {
      global: { requests: 10000, window: 3600 }, // 10000/hour
    },
  },
  enterprise: {
    name: 'Enterprise',
    limits: {
      global: { requests: 100000, window: 3600 }, // 100000/hour
    },
  },
};

async function tieredRateLimit(req: Request, res: Response, next: NextFunction) {
  const user = req.user;
  const tier = TIERS[user?.tier || 'free'];
  const endpoint = `${req.method} ${req.route?.path || req.path}`;

  // Check endpoint-specific limit first
  if (tier.limits.perEndpoint?.[endpoint]) {
    const config = tier.limits.perEndpoint[endpoint];
    const result = await limiter.isAllowed(
      `${user.id}:${endpoint}`,
      config.requests,
      config.window
    );

    if (!result.allowed) {
      return res.status(429).json({
        error: {
          code: 'ENDPOINT_RATE_LIMITED',
          message: `Rate limit exceeded for ${endpoint}`,
        },
      });
    }
  }

  // Check global limit
  const globalResult = await limiter.isAllowed(
    `${user.id}:global`,
    tier.limits.global.requests,
    tier.limits.global.window
  );

  res.set({
    'X-RateLimit-Limit': tier.limits.global.requests.toString(),
    'X-RateLimit-Remaining': globalResult.remaining.toString(),
    'X-RateLimit-Reset': globalResult.reset.toString(),
  });

  if (!globalResult.allowed) {
    return res.status(429).json({
      error: {
        code: 'RATE_LIMITED',
        message: 'Global rate limit exceeded',
      },
    });
  }

  next();
}
```

## Distributed Rate Limiting

```typescript
/**
 * Distributed rate limiting with Redis Cluster
 * Uses consistent hashing for key distribution
 */
class DistributedRateLimiter {
  private cluster: Redis.Cluster;

  constructor(nodes: ClusterNode[]) {
    this.cluster = new Redis.Cluster(nodes);
  }

  async isAllowed(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number; reset: number }> {
    // Same algorithm but on cluster
    // Redis Cluster handles key distribution
    return this.slidingWindowCounter(key, limit, windowSeconds);
  }

  // For global limits across all instances
  async isAllowedGlobal(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number; reset: number }> {
    // Use {hash} tag to ensure same slot
    const taggedKey = `{ratelimit}:${key}`;
    return this.slidingWindowCounter(taggedKey, limit, windowSeconds);
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│               Rate Limiting Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Always Return Rate Limit Headers                            │
│     └── X-RateLimit-Limit, Remaining, Reset                     │
│                                                                  │
│  2. Include Retry-After on 429                                  │
│     └── Tell clients when to retry                              │
│                                                                  │
│  3. Use Appropriate Algorithm                                   │
│     ├── Token Bucket for bursts OK                              │
│     ├── Leaky Bucket for smooth rate                            │
│     └── Sliding Window for accuracy                             │
│                                                                  │
│  4. Rate Limit by Multiple Keys                                 │
│     └── User + IP prevents abuse with stolen keys               │
│                                                                  │
│  5. Different Limits per Endpoint                               │
│     └── Write operations need stricter limits                   │
│                                                                  │
│  6. Implement Graceful Degradation                              │
│     └── If Redis fails, allow or use local fallback             │
│                                                                  │
│  7. Document Rate Limits                                        │
│     └── Include in API documentation                            │
│                                                                  │
│  8. Monitor and Alert                                           │
│     └── Track rate limit hits for abuse detection               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
