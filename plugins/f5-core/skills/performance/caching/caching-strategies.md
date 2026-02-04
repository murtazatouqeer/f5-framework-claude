---
name: caching-strategies
description: Application caching patterns and strategies
category: performance/caching
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Caching Strategies

## Overview

Caching is the most effective way to improve application performance.
A well-designed caching strategy can reduce response times by 10-100x.

## Cache Patterns

### Cache-Aside (Lazy Loading)

Most common pattern - application manages cache directly.

```typescript
// Cache-aside implementation
class UserService {
  constructor(
    private cache: Redis,
    private userRepository: UserRepository
  ) {}

  async getUser(id: string): Promise<User | null> {
    const cacheKey = `user:${id}`;

    // 1. Try cache first
    const cached = await this.cache.get(cacheKey);
    if (cached) {
      return JSON.parse(cached);
    }

    // 2. Cache miss - fetch from database
    const user = await this.userRepository.findById(id);
    if (!user) {
      return null;
    }

    // 3. Store in cache for future requests
    await this.cache.set(
      cacheKey,
      JSON.stringify(user),
      'EX',
      3600 // 1 hour TTL
    );

    return user;
  }

  async updateUser(id: string, data: UpdateUserDTO): Promise<User> {
    const user = await this.userRepository.update(id, data);

    // Invalidate cache on update
    await this.cache.del(`user:${id}`);

    return user;
  }
}
```

**Pros:**
- Simple to implement
- Cache only what's needed
- Resilient to cache failures

**Cons:**
- First request always hits database
- Potential for stale data
- Cache stampede risk

### Write-Through

Write to cache and database simultaneously.

```typescript
// Write-through implementation
class ProductService {
  async createProduct(data: CreateProductDTO): Promise<Product> {
    // Write to database
    const product = await this.productRepository.create(data);

    // Write to cache immediately
    await this.cache.set(
      `product:${product.id}`,
      JSON.stringify(product),
      'EX',
      3600
    );

    return product;
  }

  async updateProduct(id: string, data: UpdateProductDTO): Promise<Product> {
    // Update database
    const product = await this.productRepository.update(id, data);

    // Update cache immediately
    await this.cache.set(
      `product:${id}`,
      JSON.stringify(product),
      'EX',
      3600
    );

    return product;
  }

  async getProduct(id: string): Promise<Product | null> {
    // Read from cache (guaranteed fresh due to write-through)
    const cached = await this.cache.get(`product:${id}`);
    if (cached) {
      return JSON.parse(cached);
    }

    // Fallback to database if cache miss
    return this.productRepository.findById(id);
  }
}
```

**Pros:**
- Cache always has latest data
- No stale data issues

**Cons:**
- Write latency increases
- Cache may have unused data

### Write-Behind (Write-Back)

Write to cache immediately, async write to database.

```typescript
// Write-behind implementation
class AnalyticsService {
  private writeQueue: Map<string, any> = new Map();
  private flushInterval = 5000; // 5 seconds

  constructor(
    private cache: Redis,
    private repository: AnalyticsRepository
  ) {
    // Periodically flush to database
    setInterval(() => this.flush(), this.flushInterval);
  }

  async trackEvent(event: AnalyticsEvent): Promise<void> {
    const key = `analytics:${event.type}:${Date.now()}`;

    // Write to cache immediately (fast)
    await this.cache.set(key, JSON.stringify(event), 'EX', 3600);

    // Queue for database write
    this.writeQueue.set(key, event);
  }

  private async flush(): Promise<void> {
    if (this.writeQueue.size === 0) return;

    const events = Array.from(this.writeQueue.values());
    this.writeQueue.clear();

    try {
      // Batch insert to database
      await this.repository.insertMany(events);
    } catch (error) {
      // Re-queue failed events
      events.forEach((event, index) => {
        this.writeQueue.set(`retry:${index}`, event);
      });
    }
  }
}
```

**Pros:**
- Very fast writes
- Reduces database load
- Batching improves efficiency

**Cons:**
- Risk of data loss if cache fails
- Complex consistency handling

### Read-Through

Cache handles fetching data automatically.

```typescript
// Read-through implementation
class CacheService {
  async get<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number = 3600
  ): Promise<T> {
    // Try cache
    const cached = await this.cache.get(key);
    if (cached) {
      return JSON.parse(cached);
    }

    // Cache miss - fetch and store
    const data = await fetcher();
    await this.cache.set(key, JSON.stringify(data), 'EX', ttl);
    return data;
  }

  async getWithSWR<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number = 3600,
    staleWhileRevalidate: number = 300
  ): Promise<T> {
    const cached = await this.cache.get(key);
    const metadata = await this.cache.get(`${key}:meta`);

    if (cached) {
      const meta = metadata ? JSON.parse(metadata) : null;
      const age = meta ? Date.now() - meta.createdAt : Infinity;

      // Return cached, but revalidate in background if stale
      if (age > ttl * 1000 && age < (ttl + staleWhileRevalidate) * 1000) {
        this.revalidate(key, fetcher, ttl).catch(console.error);
      }

      return JSON.parse(cached);
    }

    return this.revalidate(key, fetcher, ttl);
  }

  private async revalidate<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl: number
  ): Promise<T> {
    const data = await fetcher();

    await Promise.all([
      this.cache.set(key, JSON.stringify(data), 'EX', ttl + 300),
      this.cache.set(
        `${key}:meta`,
        JSON.stringify({ createdAt: Date.now() }),
        'EX',
        ttl + 300
      ),
    ]);

    return data;
  }
}

// Usage
const user = await cacheService.get(
  `user:${id}`,
  () => userRepository.findById(id),
  3600
);
```

## Cache Key Design

### Key Structure

```typescript
// Good key structure: namespace:entity:identifier[:variant]
const cacheKeys = {
  // Simple entity caching
  user: (id: string) => `user:${id}`,
  userProfile: (id: string) => `user:${id}:profile`,
  userPosts: (id: string, page: number) => `user:${id}:posts:page:${page}`,

  // Collection caching
  product: (id: string) => `product:${id}`,
  productsByCategory: (categoryId: string, page: number) =>
    `products:category:${categoryId}:page:${page}`,
  productsSearch: (query: string, filters: any) => {
    const hash = crypto
      .createHash('md5')
      .update(JSON.stringify({ query, filters }))
      .digest('hex')
      .slice(0, 8);
    return `products:search:${hash}`;
  },

  // Versioned keys for cache busting
  config: (version: string) => `config:v${version}`,

  // Session-specific
  session: (sessionId: string) => `session:${sessionId}`,
  cart: (userId: string) => `cart:${userId}`,
};
```

### Key Best Practices

```typescript
// Key builder with validation
class CacheKeyBuilder {
  private namespace: string;

  constructor(namespace: string) {
    this.namespace = namespace;
  }

  // Simple key
  forEntity(type: string, id: string): string {
    this.validateId(id);
    return `${this.namespace}:${type}:${id}`;
  }

  // Parameterized key
  forQuery(type: string, params: Record<string, any>): string {
    const sortedParams = Object.keys(params)
      .sort()
      .map(k => `${k}=${params[k]}`)
      .join(':');
    return `${this.namespace}:${type}:${sortedParams}`;
  }

  // Hashed key for complex queries
  forComplexQuery(type: string, query: any): string {
    const hash = crypto
      .createHash('sha256')
      .update(JSON.stringify(query))
      .digest('hex')
      .slice(0, 16);
    return `${this.namespace}:${type}:${hash}`;
  }

  private validateId(id: string): void {
    if (id.includes(':')) {
      throw new Error('ID cannot contain colon character');
    }
  }
}
```

## TTL Strategies

### TTL by Data Type

```typescript
const TTL = {
  // Short-lived - frequently changing
  SESSION: 30 * 60,              // 30 minutes
  RATE_LIMIT: 60,                // 1 minute
  OTP: 5 * 60,                   // 5 minutes

  // Medium - user-specific data
  USER_PROFILE: 60 * 60,         // 1 hour
  USER_PREFERENCES: 24 * 60 * 60, // 24 hours
  CART: 7 * 24 * 60 * 60,        // 7 days

  // Long-lived - rarely changing
  PRODUCT_CATALOG: 6 * 60 * 60,  // 6 hours
  CATEGORY_LIST: 24 * 60 * 60,   // 24 hours

  // Very long - reference data
  COUNTRY_LIST: 7 * 24 * 60 * 60,  // 7 days
  CURRENCY_RATES: 60 * 60,         // 1 hour (external API)
};
```

### Jitter to Prevent Thundering Herd

```typescript
// Add random jitter to prevent cache stampede
function withJitter(ttl: number, percentage: number = 0.1): number {
  const jitter = ttl * percentage * (Math.random() - 0.5) * 2;
  return Math.floor(ttl + jitter);
}

// Usage
await cache.set(key, value, 'EX', withJitter(TTL.USER_PROFILE)); // 3240-3960s instead of exactly 3600s
```

## Multi-Level Caching

```
┌─────────────────────────────────────────────────────┐
│                    Request Flow                      │
└─────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────┐     Hit
│  L1: Memory   │ ─────────► Response
│  (Process)    │
│  TTL: 1 min   │
└───────────────┘
        │ Miss
        ▼
┌───────────────┐     Hit
│  L2: Redis    │ ─────────► Response
│  (Shared)     │            (+ Update L1)
│  TTL: 1 hour  │
└───────────────┘
        │ Miss
        ▼
┌───────────────┐
│  L3: Database │ ─────────► Response
│  (Source)     │            (+ Update L1, L2)
└───────────────┘
```

```typescript
// Multi-level cache implementation
class MultiLevelCache {
  private l1: Map<string, { data: any; expires: number }> = new Map();
  private l1MaxSize = 1000;
  private l1TTL = 60000; // 1 minute

  constructor(private redis: Redis) {}

  async get<T>(key: string): Promise<T | null> {
    // L1: Check in-memory cache
    const l1Entry = this.l1.get(key);
    if (l1Entry && l1Entry.expires > Date.now()) {
      return l1Entry.data;
    }

    // L2: Check Redis
    const l2Data = await this.redis.get(key);
    if (l2Data) {
      const parsed = JSON.parse(l2Data);
      this.setL1(key, parsed); // Populate L1
      return parsed;
    }

    return null;
  }

  async set(key: string, data: any, ttlSeconds: number): Promise<void> {
    // Set in both levels
    this.setL1(key, data);
    await this.redis.set(key, JSON.stringify(data), 'EX', ttlSeconds);
  }

  private setL1(key: string, data: any): void {
    // Evict if full (simple LRU approximation)
    if (this.l1.size >= this.l1MaxSize) {
      const oldestKey = this.l1.keys().next().value;
      this.l1.delete(oldestKey);
    }

    this.l1.set(key, {
      data,
      expires: Date.now() + this.l1TTL,
    });
  }

  async invalidate(key: string): Promise<void> {
    this.l1.delete(key);
    await this.redis.del(key);
  }

  // Invalidate by pattern
  async invalidatePattern(pattern: string): Promise<void> {
    // Clear matching L1 entries
    for (const [key] of this.l1) {
      if (this.matchPattern(key, pattern)) {
        this.l1.delete(key);
      }
    }

    // Clear matching Redis entries
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }

  private matchPattern(key: string, pattern: string): boolean {
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*') + '$');
    return regex.test(key);
  }
}
```

## Cache Warming

```typescript
// Pre-populate cache on startup
class CacheWarmer {
  constructor(
    private cache: Redis,
    private productRepository: ProductRepository,
    private categoryRepository: CategoryRepository
  ) {}

  async warm(): Promise<void> {
    console.log('Warming cache...');

    await Promise.all([
      this.warmCategories(),
      this.warmTopProducts(),
      this.warmConfig(),
    ]);

    console.log('Cache warming complete');
  }

  private async warmCategories(): Promise<void> {
    const categories = await this.categoryRepository.findAll();

    await Promise.all(
      categories.map(cat =>
        this.cache.set(
          `category:${cat.id}`,
          JSON.stringify(cat),
          'EX',
          86400
        )
      )
    );

    // Cache the full list too
    await this.cache.set(
      'categories:all',
      JSON.stringify(categories),
      'EX',
      86400
    );
  }

  private async warmTopProducts(): Promise<void> {
    const topProducts = await this.productRepository.findTopSelling(100);

    await Promise.all(
      topProducts.map(product =>
        this.cache.set(
          `product:${product.id}`,
          JSON.stringify(product),
          'EX',
          21600
        )
      )
    );
  }

  private async warmConfig(): Promise<void> {
    const config = await this.loadConfig();
    await this.cache.set('app:config', JSON.stringify(config), 'EX', 86400);
  }
}

// Run on application startup
app.on('ready', async () => {
  const warmer = new CacheWarmer(cache, productRepo, categoryRepo);
  await warmer.warm();
});
```

## Best Practices

1. **Start simple** - Cache-aside is good for most cases
2. **Set appropriate TTLs** - Balance freshness vs performance
3. **Use jitter** - Prevent thundering herd
4. **Monitor hit rates** - Aim for >90% cache hits
5. **Plan for failures** - Graceful degradation when cache is down
6. **Invalidate carefully** - Too aggressive = low hit rate, too passive = stale data
