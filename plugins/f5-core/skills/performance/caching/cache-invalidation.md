---
name: cache-invalidation
description: Cache invalidation strategies and patterns
category: performance/caching
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Cache Invalidation

## Overview

"There are only two hard things in Computer Science: cache invalidation and naming things."
— Phil Karlton

Cache invalidation is the process of removing or updating cached data when the source data changes.

## Invalidation Strategies

### 1. Time-Based (TTL)

Simplest approach - cache expires after a set time.

```typescript
// Set TTL on cache entry
await cache.set('user:123', userData, 'EX', 3600); // Expires in 1 hour

// Choosing TTL based on data characteristics
const TTL_CONFIG = {
  // Frequently changing data
  stockPrices: 10,        // 10 seconds
  userStatus: 60,         // 1 minute

  // Moderate change frequency
  userProfile: 3600,      // 1 hour
  productDetails: 21600,  // 6 hours

  // Rarely changing data
  categories: 86400,      // 24 hours
  countries: 604800,      // 7 days

  // Static data with versioning
  config: 2592000,        // 30 days (invalidate on deploy)
};
```

**Pros:**
- Simple to implement
- No additional infrastructure needed
- Automatic cleanup

**Cons:**
- Data can be stale until TTL expires
- TTL too short = poor hit rate
- TTL too long = stale data

### 2. Event-Based Invalidation

Invalidate when data changes.

```typescript
// Event-driven invalidation
class UserService {
  constructor(
    private cache: CacheService,
    private repository: UserRepository,
    private events: EventEmitter
  ) {
    // Listen for update events
    this.events.on('user.updated', this.handleUserUpdate.bind(this));
    this.events.on('user.deleted', this.handleUserDelete.bind(this));
  }

  async updateUser(id: string, data: UpdateUserDTO): Promise<User> {
    const user = await this.repository.update(id, data);

    // Emit event for invalidation
    this.events.emit('user.updated', { userId: id, user });

    return user;
  }

  private async handleUserUpdate({ userId, user }: { userId: string; user: User }) {
    // Invalidate all related caches
    await Promise.all([
      this.cache.del(`user:${userId}`),
      this.cache.del(`user:${userId}:profile`),
      this.cache.del(`user:${userId}:preferences`),
      // Invalidate list caches that might contain this user
      this.cache.invalidatePattern('users:list:*'),
    ]);

    // Optionally, refresh cache with new data
    await this.cache.set(`user:${userId}`, user, 3600);
  }

  private async handleUserDelete({ userId }: { userId: string }) {
    await this.cache.invalidatePattern(`user:${userId}*`);
  }
}
```

### 3. Write-Through Invalidation

Update cache when writing to database.

```typescript
class ProductService {
  async updateProduct(id: string, data: UpdateProductDTO): Promise<Product> {
    // Update database
    const product = await this.repository.update(id, data);

    // Update cache synchronously
    await this.cache.set(`product:${id}`, product, 3600);

    // Invalidate related caches
    await Promise.all([
      this.cache.del(`products:category:${product.categoryId}:*`),
      this.cache.del('products:featured'),
      this.cache.del('products:bestsellers'),
    ]);

    return product;
  }
}
```

### 4. Tag-Based Invalidation

Associate cache entries with tags for bulk invalidation.

```typescript
class TaggedCache {
  constructor(private redis: Redis) {}

  async setWithTags(
    key: string,
    data: any,
    tags: string[],
    ttl: number
  ): Promise<void> {
    const multi = this.redis.multi();

    // Store data
    multi.set(key, JSON.stringify(data), 'EX', ttl);

    // Add key to each tag set
    for (const tag of tags) {
      multi.sadd(`tag:${tag}`, key);
      multi.expire(`tag:${tag}`, ttl + 86400); // Tags expire after data
    }

    await multi.exec();
  }

  async invalidateByTag(tag: string): Promise<number> {
    // Get all keys with this tag
    const keys = await this.redis.smembers(`tag:${tag}`);

    if (keys.length === 0) {
      return 0;
    }

    // Delete all keys and the tag set
    const multi = this.redis.multi();
    multi.del(...keys);
    multi.del(`tag:${tag}`);
    await multi.exec();

    return keys.length;
  }

  async invalidateByTags(tags: string[]): Promise<number> {
    let total = 0;
    for (const tag of tags) {
      total += await this.invalidateByTag(tag);
    }
    return total;
  }
}

// Usage
const taggedCache = new TaggedCache(redis);

// Store product with multiple tags
await taggedCache.setWithTags(
  `product:${product.id}`,
  product,
  [
    'products',
    `category:${product.categoryId}`,
    `brand:${product.brandId}`,
    product.featured ? 'featured' : null,
  ].filter(Boolean) as string[],
  3600
);

// Invalidate all products in a category
await taggedCache.invalidateByTag(`category:${categoryId}`);

// Invalidate multiple tags
await taggedCache.invalidateByTags(['featured', 'bestsellers']);
```

### 5. Version-Based Invalidation

Use version numbers in cache keys.

```typescript
class VersionedCache {
  private versions: Map<string, number> = new Map();

  constructor(private redis: Redis) {}

  async get<T>(namespace: string, key: string): Promise<T | null> {
    const version = await this.getVersion(namespace);
    const fullKey = `${namespace}:v${version}:${key}`;
    const data = await this.redis.get(fullKey);
    return data ? JSON.parse(data) : null;
  }

  async set(namespace: string, key: string, data: any, ttl: number): Promise<void> {
    const version = await this.getVersion(namespace);
    const fullKey = `${namespace}:v${version}:${key}`;
    await this.redis.set(fullKey, JSON.stringify(data), 'EX', ttl);
  }

  async invalidateNamespace(namespace: string): Promise<void> {
    // Increment version - all old keys become invalid
    await this.redis.incr(`version:${namespace}`);
    this.versions.delete(namespace);
  }

  private async getVersion(namespace: string): Promise<number> {
    if (this.versions.has(namespace)) {
      return this.versions.get(namespace)!;
    }

    const version = await this.redis.get(`version:${namespace}`);
    const v = version ? parseInt(version, 10) : 1;
    this.versions.set(namespace, v);
    return v;
  }
}

// Usage
const versionedCache = new VersionedCache(redis);

// Store data
await versionedCache.set('products', 'featured', products, 3600);

// On catalog update, invalidate entire namespace
await versionedCache.invalidateNamespace('products');
// New version automatically used - old keys orphaned and expire
```

## Cascade Invalidation

Handle related cache dependencies.

```typescript
interface CacheDependency {
  key: string;
  dependsOn: string[];
}

class CascadeInvalidator {
  private dependencies: Map<string, Set<string>> = new Map();

  // Register that 'dependent' cache depends on 'source'
  registerDependency(dependent: string, source: string): void {
    if (!this.dependencies.has(source)) {
      this.dependencies.set(source, new Set());
    }
    this.dependencies.get(source)!.add(dependent);
  }

  // Get all keys that should be invalidated when 'key' changes
  getDependents(key: string): string[] {
    const result: string[] = [];
    const visited = new Set<string>();

    const traverse = (k: string) => {
      if (visited.has(k)) return;
      visited.add(k);

      const deps = this.dependencies.get(k);
      if (deps) {
        for (const dep of deps) {
          result.push(dep);
          traverse(dep); // Recursively get dependents
        }
      }
    };

    traverse(key);
    return result;
  }

  async invalidateWithCascade(cache: Redis, key: string): Promise<void> {
    const keysToInvalidate = [key, ...this.getDependents(key)];
    if (keysToInvalidate.length > 0) {
      await cache.del(...keysToInvalidate);
    }
  }
}

// Setup dependencies
const invalidator = new CascadeInvalidator();

// Product cache depends on category and brand
invalidator.registerDependency('products:featured', 'category:electronics');
invalidator.registerDependency('products:featured', 'brand:apple');
invalidator.registerDependency('homepage:widgets', 'products:featured');

// When category changes, cascade invalidation
await invalidator.invalidateWithCascade(redis, 'category:electronics');
// Invalidates: category:electronics, products:featured, homepage:widgets
```

## Distributed Invalidation

Invalidate across multiple servers/regions.

```typescript
// Pub/Sub based invalidation
class DistributedInvalidator {
  private publisher: Redis;
  private subscriber: Redis;
  private localCache: Map<string, any>;

  constructor(redisUrl: string, localCache: Map<string, any>) {
    this.publisher = new Redis(redisUrl);
    this.subscriber = new Redis(redisUrl);
    this.localCache = localCache;

    this.setupSubscription();
  }

  private setupSubscription(): void {
    this.subscriber.subscribe('cache:invalidate');

    this.subscriber.on('message', (channel, message) => {
      if (channel === 'cache:invalidate') {
        const { key, pattern, region } = JSON.parse(message);

        // Skip if from same region (already invalidated locally)
        if (region === process.env.REGION) return;

        if (key) {
          this.localCache.delete(key);
        } else if (pattern) {
          this.invalidateLocalPattern(pattern);
        }
      }
    });
  }

  async invalidate(key: string): Promise<void> {
    // Invalidate local
    this.localCache.delete(key);

    // Publish for other instances
    await this.publisher.publish('cache:invalidate', JSON.stringify({
      key,
      region: process.env.REGION,
    }));
  }

  async invalidatePattern(pattern: string): Promise<void> {
    // Invalidate local
    this.invalidateLocalPattern(pattern);

    // Publish for other instances
    await this.publisher.publish('cache:invalidate', JSON.stringify({
      pattern,
      region: process.env.REGION,
    }));
  }

  private invalidateLocalPattern(pattern: string): void {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    for (const [key] of this.localCache) {
      if (regex.test(key)) {
        this.localCache.delete(key);
      }
    }
  }
}
```

## Stampede Protection

Prevent thundering herd on invalidation.

```typescript
class StampedeProtectedCache {
  constructor(private redis: Redis) {}

  async getOrSet<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T> {
    // Try to get from cache
    const cached = await this.redis.get(key);
    if (cached) {
      return JSON.parse(cached);
    }

    // Use lock to prevent stampede
    const lockKey = `lock:${key}`;
    const lockValue = crypto.randomUUID();
    const acquired = await this.redis.set(lockKey, lockValue, 'PX', 5000, 'NX');

    if (acquired === 'OK') {
      try {
        // We have the lock - fetch data
        const data = await fetcher();
        await this.redis.set(key, JSON.stringify(data), 'EX', ttl);
        return data;
      } finally {
        // Release lock
        await this.releaseLock(lockKey, lockValue);
      }
    } else {
      // Someone else is fetching - wait and retry
      return this.waitForCache(key, fetcher, ttl);
    }
  }

  private async waitForCache<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number,
    maxWait: number = 5000
  ): Promise<T> {
    const start = Date.now();

    while (Date.now() - start < maxWait) {
      await this.sleep(100);

      const cached = await this.redis.get(key);
      if (cached) {
        return JSON.parse(cached);
      }
    }

    // Fallback: fetch ourselves
    const data = await fetcher();
    await this.redis.set(key, JSON.stringify(data), 'EX', ttl);
    return data;
  }

  private async releaseLock(key: string, value: string): Promise<void> {
    const script = `
      if redis.call("get", KEYS[1]) == ARGV[1] then
        return redis.call("del", KEYS[1])
      end
      return 0
    `;
    await this.redis.eval(script, 1, key, value);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## Soft Delete / Stale-While-Revalidate

Serve stale data while refreshing.

```typescript
class SWRCache {
  constructor(private redis: Redis) {}

  async get<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: { ttl: number; staleTTL: number }
  ): Promise<T> {
    const [data, meta] = await Promise.all([
      this.redis.get(key),
      this.redis.get(`${key}:meta`),
    ]);

    if (data) {
      const metadata = meta ? JSON.parse(meta) : null;
      const age = metadata ? Date.now() - metadata.fetchedAt : Infinity;

      // Check if stale
      if (age > options.ttl * 1000) {
        // Serve stale, refresh in background
        this.refreshInBackground(key, fetcher, options);
      }

      return JSON.parse(data);
    }

    // No data - fetch synchronously
    return this.refresh(key, fetcher, options);
  }

  private async refresh<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: { ttl: number; staleTTL: number }
  ): Promise<T> {
    const data = await fetcher();

    await Promise.all([
      this.redis.set(
        key,
        JSON.stringify(data),
        'EX',
        options.ttl + options.staleTTL
      ),
      this.redis.set(
        `${key}:meta`,
        JSON.stringify({ fetchedAt: Date.now() }),
        'EX',
        options.ttl + options.staleTTL
      ),
    ]);

    return data;
  }

  private async refreshInBackground<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: { ttl: number; staleTTL: number }
  ): Promise<void> {
    // Use lock to prevent multiple refreshes
    const lockKey = `refresh:${key}`;
    const acquired = await this.redis.set(lockKey, '1', 'PX', 5000, 'NX');

    if (acquired === 'OK') {
      this.refresh(key, fetcher, options).catch(console.error);
    }
  }
}

// Usage
const cache = new SWRCache(redis);

const data = await cache.get(
  'products:featured',
  () => fetchFeaturedProducts(),
  {
    ttl: 300,      // Fresh for 5 minutes
    staleTTL: 3600, // Serve stale for 1 hour while refreshing
  }
);
```

## Best Practices

1. **Choose the right strategy** - TTL for simple cases, events for critical data
2. **Use tags for bulk invalidation** - Better than pattern matching
3. **Protect against stampede** - Lock during regeneration
4. **Consider stale-while-revalidate** - Better UX with background refresh
5. **Track invalidation patterns** - Monitor for excessive invalidation
6. **Test invalidation** - Ensure all related caches are cleared
7. **Document dependencies** - Make cache relationships explicit
