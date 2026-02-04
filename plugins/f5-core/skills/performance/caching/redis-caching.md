---
name: redis-caching
description: Redis caching implementation and best practices
category: performance/caching
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Redis Caching

## Overview

Redis is an in-memory data structure store used as a cache, database, and message broker.
It provides sub-millisecond response times for caching.

## Connection Setup

### Basic Connection

```typescript
import Redis from 'ioredis';

// Single instance
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  db: parseInt(process.env.REDIS_DB || '0'),
  retryDelayOnFailover: 100,
  maxRetriesPerRequest: 3,
});

// Connection events
redis.on('connect', () => console.log('Redis connected'));
redis.on('error', (err) => console.error('Redis error:', err));
redis.on('close', () => console.log('Redis connection closed'));
```

### Cluster Connection

```typescript
// Redis Cluster
const cluster = new Redis.Cluster([
  { host: 'redis-1', port: 6379 },
  { host: 'redis-2', port: 6379 },
  { host: 'redis-3', port: 6379 },
], {
  redisOptions: {
    password: process.env.REDIS_PASSWORD,
  },
  scaleReads: 'slave', // Read from replicas
  maxRedirections: 16,
});
```

### Connection Pool

```typescript
// Pooled connections for high concurrency
import { createPool } from 'generic-pool';

const redisPool = createPool({
  create: async () => {
    return new Redis({
      host: process.env.REDIS_HOST,
      port: 6379,
      lazyConnect: true,
    });
  },
  destroy: async (client) => {
    await client.quit();
  },
}, {
  min: 5,
  max: 50,
});

// Usage
async function withRedis<T>(fn: (redis: Redis) => Promise<T>): Promise<T> {
  const client = await redisPool.acquire();
  try {
    return await fn(client);
  } finally {
    await redisPool.release(client);
  }
}
```

## Basic Operations

### String Operations

```typescript
// SET with options
await redis.set('key', 'value');
await redis.set('key', 'value', 'EX', 3600);     // Expire in 3600 seconds
await redis.set('key', 'value', 'PX', 3600000);  // Expire in 3600000 milliseconds
await redis.set('key', 'value', 'NX');           // Only set if not exists
await redis.set('key', 'value', 'XX');           // Only set if exists

// GET
const value = await redis.get('key');

// Multiple keys
await redis.mset('k1', 'v1', 'k2', 'v2', 'k3', 'v3');
const values = await redis.mget('k1', 'k2', 'k3');

// Increment/Decrement
await redis.incr('counter');
await redis.incrby('counter', 10);
await redis.decr('counter');

// Get and set
const oldValue = await redis.getset('key', 'newValue');
```

### JSON Operations

```typescript
// Store JSON
await redis.set('user:1', JSON.stringify({ id: 1, name: 'John' }));

// Retrieve JSON
const userJson = await redis.get('user:1');
const user = userJson ? JSON.parse(userJson) : null;

// Helper class
class RedisJson {
  constructor(private redis: Redis) {}

  async setJson<T>(key: string, value: T, ttl?: number): Promise<void> {
    const json = JSON.stringify(value);
    if (ttl) {
      await this.redis.set(key, json, 'EX', ttl);
    } else {
      await this.redis.set(key, json);
    }
  }

  async getJson<T>(key: string): Promise<T | null> {
    const value = await this.redis.get(key);
    return value ? JSON.parse(value) : null;
  }
}
```

### Hash Operations

```typescript
// Efficient for storing objects with many fields
await redis.hset('user:1', {
  name: 'John',
  email: 'john@example.com',
  age: '30',
});

// Get specific field
const name = await redis.hget('user:1', 'name');

// Get all fields
const user = await redis.hgetall('user:1');

// Increment hash field
await redis.hincrby('user:1', 'age', 1);

// Check field exists
const exists = await redis.hexists('user:1', 'name');

// Delete field
await redis.hdel('user:1', 'age');
```

### List Operations

```typescript
// Add to list
await redis.lpush('queue', 'item1', 'item2'); // Add to left
await redis.rpush('queue', 'item3', 'item4'); // Add to right

// Get from list
const item = await redis.lpop('queue'); // Remove from left
const items = await redis.lrange('queue', 0, -1); // Get all

// Blocking pop (for queues)
const result = await redis.blpop('queue', 5); // Wait up to 5 seconds

// Trim list (keep recent items)
await redis.ltrim('logs', 0, 99); // Keep only last 100 items
```

### Set Operations

```typescript
// Add to set
await redis.sadd('tags', 'nodejs', 'redis', 'typescript');

// Check membership
const isMember = await redis.sismember('tags', 'nodejs');

// Get all members
const tags = await redis.smembers('tags');

// Set operations
await redis.sunion('tags1', 'tags2');       // Union
await redis.sinter('tags1', 'tags2');       // Intersection
await redis.sdiff('tags1', 'tags2');        // Difference

// Random member
const randomTag = await redis.srandmember('tags');
```

### Sorted Set Operations

```typescript
// Add with score (for rankings, time series)
await redis.zadd('leaderboard', 100, 'player1', 200, 'player2', 150, 'player3');

// Get by rank
const top10 = await redis.zrevrange('leaderboard', 0, 9, 'WITHSCORES');

// Get by score range
const mediumScores = await redis.zrangebyscore('leaderboard', 100, 200);

// Increment score
await redis.zincrby('leaderboard', 10, 'player1');

// Get rank
const rank = await redis.zrevrank('leaderboard', 'player1');

// Count in range
const count = await redis.zcount('leaderboard', 100, 200);
```

## Advanced Patterns

### Distributed Lock

```typescript
class RedisLock {
  constructor(private redis: Redis) {}

  async acquire(
    lockKey: string,
    ttlMs: number = 10000,
    retries: number = 3,
    retryDelay: number = 100
  ): Promise<string | null> {
    const lockValue = crypto.randomUUID();

    for (let i = 0; i < retries; i++) {
      const acquired = await this.redis.set(
        lockKey,
        lockValue,
        'PX',
        ttlMs,
        'NX'
      );

      if (acquired === 'OK') {
        return lockValue;
      }

      await this.sleep(retryDelay);
    }

    return null;
  }

  async release(lockKey: string, lockValue: string): Promise<boolean> {
    // Lua script ensures atomic check-and-delete
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
      else
        return 0
      end
    `;

    const result = await this.redis.eval(script, 1, lockKey, lockValue);
    return result === 1;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Usage
const lock = new RedisLock(redis);

const lockValue = await lock.acquire('resource:123');
if (lockValue) {
  try {
    // Critical section
    await processResource();
  } finally {
    await lock.release('resource:123', lockValue);
  }
} else {
  console.log('Could not acquire lock');
}
```

### Rate Limiting

```typescript
class RateLimiter {
  constructor(private redis: Redis) {}

  // Fixed window
  async checkFixedWindow(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number }> {
    const current = await this.redis.incr(key);

    if (current === 1) {
      await this.redis.expire(key, windowSeconds);
    }

    return {
      allowed: current <= limit,
      remaining: Math.max(0, limit - current),
    };
  }

  // Sliding window (more accurate)
  async checkSlidingWindow(
    key: string,
    limit: number,
    windowSeconds: number
  ): Promise<{ allowed: boolean; remaining: number }> {
    const now = Date.now();
    const windowStart = now - windowSeconds * 1000;

    // Use sorted set with timestamp as score
    const multi = this.redis.multi();
    multi.zremrangebyscore(key, '-inf', windowStart);
    multi.zadd(key, now, `${now}:${crypto.randomUUID()}`);
    multi.zcard(key);
    multi.expire(key, windowSeconds);

    const results = await multi.exec();
    const count = results?.[2]?.[1] as number;

    return {
      allowed: count <= limit,
      remaining: Math.max(0, limit - count),
    };
  }

  // Token bucket
  async checkTokenBucket(
    key: string,
    capacity: number,
    refillRate: number, // tokens per second
  ): Promise<{ allowed: boolean; tokens: number }> {
    const script = `
      local key = KEYS[1]
      local capacity = tonumber(ARGV[1])
      local refillRate = tonumber(ARGV[2])
      local now = tonumber(ARGV[3])

      local bucket = redis.call("hmget", key, "tokens", "lastRefill")
      local tokens = tonumber(bucket[1]) or capacity
      local lastRefill = tonumber(bucket[2]) or now

      -- Refill tokens
      local elapsed = now - lastRefill
      local refill = elapsed / 1000 * refillRate
      tokens = math.min(capacity, tokens + refill)

      -- Consume token
      local allowed = tokens >= 1
      if allowed then
        tokens = tokens - 1
      end

      redis.call("hmset", key, "tokens", tokens, "lastRefill", now)
      redis.call("expire", key, math.ceil(capacity / refillRate) + 1)

      return {allowed and 1 or 0, tokens}
    `;

    const [allowed, tokens] = await this.redis.eval(
      script,
      1,
      key,
      capacity,
      refillRate,
      Date.now()
    ) as [number, number];

    return { allowed: allowed === 1, tokens };
  }
}
```

### Pub/Sub for Cache Invalidation

```typescript
// Publisher (when data changes)
class CacheInvalidator {
  constructor(private redis: Redis) {}

  async invalidate(key: string): Promise<void> {
    await this.redis.del(key);
    await this.redis.publish('cache:invalidate', JSON.stringify({ key }));
  }

  async invalidatePattern(pattern: string): Promise<void> {
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
    await this.redis.publish('cache:invalidate', JSON.stringify({ pattern }));
  }
}

// Subscriber (on other instances)
class CacheSubscriber {
  private subscriber: Redis;
  private localCache: Map<string, any>;

  constructor(redisUrl: string, localCache: Map<string, any>) {
    this.subscriber = new Redis(redisUrl);
    this.localCache = localCache;
    this.setupSubscription();
  }

  private setupSubscription(): void {
    this.subscriber.subscribe('cache:invalidate');

    this.subscriber.on('message', (channel, message) => {
      if (channel === 'cache:invalidate') {
        const { key, pattern } = JSON.parse(message);

        if (key) {
          this.localCache.delete(key);
        } else if (pattern) {
          const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
          for (const [k] of this.localCache) {
            if (regex.test(k)) {
              this.localCache.delete(k);
            }
          }
        }
      }
    });
  }
}
```

### Cache Aside with Stampede Protection

```typescript
class StampedeProtectedCache {
  constructor(private redis: Redis) {}

  async get<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T> {
    // Try to get from cache
    const cached = await this.redis.get(key);
    if (cached) {
      return JSON.parse(cached);
    }

    // Try to acquire lock for fetching
    const lockKey = `lock:${key}`;
    const lockValue = crypto.randomUUID();
    const acquired = await this.redis.set(lockKey, lockValue, 'PX', 5000, 'NX');

    if (acquired === 'OK') {
      try {
        // We have the lock, fetch data
        const data = await fetcher();
        await this.redis.set(key, JSON.stringify(data), 'EX', ttl);
        return data;
      } finally {
        // Release lock
        const script = `
          if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
          end
        `;
        await this.redis.eval(script, 1, lockKey, lockValue);
      }
    } else {
      // Another process is fetching, wait for it
      for (let i = 0; i < 50; i++) { // Max 5 seconds
        await this.sleep(100);
        const cached = await this.redis.get(key);
        if (cached) {
          return JSON.parse(cached);
        }
      }

      // Fallback: fetch ourselves
      return fetcher();
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Pipeline and Transactions

### Pipeline (Non-atomic batch)

```typescript
// Pipeline for batch operations
async function batchGet(keys: string[]): Promise<Map<string, any>> {
  const pipeline = redis.pipeline();

  for (const key of keys) {
    pipeline.get(key);
  }

  const results = await pipeline.exec();
  const map = new Map<string, any>();

  results?.forEach((result, index) => {
    if (result[1]) {
      map.set(keys[index], JSON.parse(result[1] as string));
    }
  });

  return map;
}
```

### Transaction (Atomic)

```typescript
// MULTI/EXEC for atomic operations
async function atomicTransfer(
  from: string,
  to: string,
  amount: number
): Promise<boolean> {
  const multi = redis.multi();

  multi.decrby(`balance:${from}`, amount);
  multi.incrby(`balance:${to}`, amount);

  try {
    await multi.exec();
    return true;
  } catch (error) {
    console.error('Transaction failed:', error);
    return false;
  }
}

// WATCH for optimistic locking
async function conditionalUpdate(key: string, update: (value: any) => any): Promise<boolean> {
  await redis.watch(key);

  const value = await redis.get(key);
  const newValue = update(value ? JSON.parse(value) : null);

  const multi = redis.multi();
  multi.set(key, JSON.stringify(newValue));

  try {
    const result = await multi.exec();
    return result !== null;
  } catch (error) {
    return false;
  }
}
```

## Best Practices

1. **Use appropriate data structures** - Hash for objects, Sorted Set for rankings
2. **Set TTL on all keys** - Prevent memory bloat
3. **Use pipeline for batch operations** - Reduce round trips
4. **Implement connection pooling** - Handle high concurrency
5. **Monitor memory usage** - Configure maxmemory and eviction policy
6. **Use Lua scripts for atomicity** - Complex operations in single call
7. **Handle reconnection gracefully** - Implement retry logic
