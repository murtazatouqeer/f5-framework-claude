---
name: nestjs-caching
description: Caching strategies and patterns in NestJS
applies_to: nestjs
category: performance
---

# NestJS Caching

## Setup

```bash
npm install @nestjs/cache-manager cache-manager cache-manager-redis-yet redis
```

```typescript
// app.module.ts
import { CacheModule } from '@nestjs/cache-manager';
import { redisStore } from 'cache-manager-redis-yet';

@Module({
  imports: [
    CacheModule.registerAsync({
      isGlobal: true,
      useFactory: async () => ({
        store: await redisStore({
          socket: {
            host: process.env.REDIS_HOST || 'localhost',
            port: parseInt(process.env.REDIS_PORT, 10) || 6379,
          },
          password: process.env.REDIS_PASSWORD,
          ttl: 60 * 1000, // Default TTL: 60 seconds
        }),
      }),
    }),
  ],
})
export class AppModule {}
```

## Basic Caching

### Auto-Caching with Interceptor

```typescript
// modules/products/products.controller.ts
import { Controller, Get, UseInterceptors } from '@nestjs/common';
import { CacheInterceptor, CacheTTL, CacheKey } from '@nestjs/cache-manager';

@Controller('products')
@UseInterceptors(CacheInterceptor)
export class ProductsController {
  constructor(private productsService: ProductsService) {}

  @Get()
  @CacheTTL(300000) // 5 minutes
  findAll() {
    return this.productsService.findAll();
  }

  @Get(':id')
  @CacheKey('product')
  @CacheTTL(600000) // 10 minutes
  findOne(@Param('id') id: string) {
    return this.productsService.findOne(id);
  }
}
```

### Manual Cache Management

```typescript
// modules/products/products.service.ts
import { Injectable, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';

@Injectable()
export class ProductsService {
  constructor(
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private productsRepository: ProductsRepository,
  ) {}

  async findById(id: string): Promise<Product> {
    const cacheKey = `product:${id}`;

    // Try cache first
    const cached = await this.cacheManager.get<Product>(cacheKey);
    if (cached) {
      return cached;
    }

    // Fetch from database
    const product = await this.productsRepository.findOne(id);

    // Store in cache
    await this.cacheManager.set(cacheKey, product, 600000); // 10 minutes

    return product;
  }

  async update(id: string, data: UpdateProductDto): Promise<Product> {
    const product = await this.productsRepository.update(id, data);

    // Invalidate cache
    await this.cacheManager.del(`product:${id}`);
    await this.cacheManager.del('products:list');

    return product;
  }

  async invalidateProductCache(id: string): Promise<void> {
    const keys = [
      `product:${id}`,
      `product:${id}:details`,
      `product:${id}:reviews`,
      'products:list',
      'products:featured',
    ];

    await Promise.all(keys.map((key) => this.cacheManager.del(key)));
  }
}
```

## Cache Patterns

### Cache-Aside Pattern

```typescript
// common/cache/cache-aside.service.ts
import { Injectable, Inject } from '@nestjs/common';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';

@Injectable()
export class CacheAsideService {
  constructor(@Inject(CACHE_MANAGER) private cacheManager: Cache) {}

  async getOrSet<T>(
    key: string,
    fetcher: () => Promise<T>,
    ttl?: number,
  ): Promise<T> {
    // Check cache
    const cached = await this.cacheManager.get<T>(key);
    if (cached !== undefined && cached !== null) {
      return cached;
    }

    // Fetch data
    const data = await fetcher();

    // Store in cache
    if (data !== undefined && data !== null) {
      await this.cacheManager.set(key, data, ttl);
    }

    return data;
  }

  async invalidate(pattern: string): Promise<void> {
    // For Redis, use SCAN to find matching keys
    const store = this.cacheManager.store as any;
    if (store.keys) {
      const keys = await store.keys(`${pattern}*`);
      if (keys.length > 0) {
        await Promise.all(keys.map((key) => this.cacheManager.del(key)));
      }
    }
  }
}

// Usage in service
@Injectable()
export class ProductsService {
  constructor(private cacheAside: CacheAsideService) {}

  async findById(id: string): Promise<Product> {
    return this.cacheAside.getOrSet(
      `product:${id}`,
      () => this.repository.findOne(id),
      600000, // 10 minutes
    );
  }
}
```

### Write-Through Pattern

```typescript
// common/cache/write-through.service.ts
@Injectable()
export class WriteThroughCacheService<T> {
  constructor(@Inject(CACHE_MANAGER) private cacheManager: Cache) {}

  async write(
    key: string,
    data: T,
    writer: (data: T) => Promise<T>,
    ttl?: number,
  ): Promise<T> {
    // Write to database first
    const result = await writer(data);

    // Then update cache
    await this.cacheManager.set(key, result, ttl);

    return result;
  }

  async delete(
    key: string,
    deleter: () => Promise<void>,
  ): Promise<void> {
    // Delete from database
    await deleter();

    // Then invalidate cache
    await this.cacheManager.del(key);
  }
}
```

### Cache Decorator

```typescript
// common/decorators/cacheable.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const CACHEABLE_KEY = 'cacheable';

export interface CacheableOptions {
  key?: string;
  ttl?: number;
  keyGenerator?: (...args: any[]) => string;
}

export const Cacheable = (options: CacheableOptions = {}) =>
  SetMetadata(CACHEABLE_KEY, options);

// common/interceptors/cacheable.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Inject,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { CACHEABLE_KEY, CacheableOptions } from '../decorators/cacheable.decorator';

@Injectable()
export class CacheableInterceptor implements NestInterceptor {
  constructor(
    private reflector: Reflector,
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
  ) {}

  async intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Promise<Observable<any>> {
    const options = this.reflector.get<CacheableOptions>(
      CACHEABLE_KEY,
      context.getHandler(),
    );

    if (!options) {
      return next.handle();
    }

    const request = context.switchToHttp().getRequest();
    const cacheKey = this.generateKey(context, options, request);

    const cached = await this.cacheManager.get(cacheKey);
    if (cached !== undefined) {
      return of(cached);
    }

    return next.handle().pipe(
      tap(async (response) => {
        await this.cacheManager.set(cacheKey, response, options.ttl);
      }),
    );
  }

  private generateKey(
    context: ExecutionContext,
    options: CacheableOptions,
    request: any,
  ): string {
    if (options.keyGenerator) {
      return options.keyGenerator(request.params, request.query);
    }

    if (options.key) {
      return options.key;
    }

    const className = context.getClass().name;
    const methodName = context.getHandler().name;
    const params = JSON.stringify(request.params);
    const query = JSON.stringify(request.query);

    return `${className}:${methodName}:${params}:${query}`;
  }
}

// Usage
@Controller('products')
@UseInterceptors(CacheableInterceptor)
export class ProductsController {
  @Get(':id')
  @Cacheable({
    keyGenerator: (params) => `product:${params.id}`,
    ttl: 600000,
  })
  findOne(@Param('id') id: string) {
    return this.productsService.findOne(id);
  }
}
```

## Cache Invalidation

### Event-Based Invalidation

```typescript
// common/events/cache-invalidation.event.ts
export class CacheInvalidationEvent {
  constructor(
    public readonly pattern: string,
    public readonly keys?: string[],
  ) {}
}

// common/listeners/cache-invalidation.listener.ts
import { Injectable } from '@nestjs/common';
import { OnEvent } from '@nestjs/event-emitter';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Inject } from '@nestjs/common';
import { Cache } from 'cache-manager';

@Injectable()
export class CacheInvalidationListener {
  constructor(@Inject(CACHE_MANAGER) private cacheManager: Cache) {}

  @OnEvent('cache.invalidate')
  async handleCacheInvalidation(event: CacheInvalidationEvent) {
    if (event.keys) {
      await Promise.all(event.keys.map((key) => this.cacheManager.del(key)));
    }

    if (event.pattern) {
      await this.invalidatePattern(event.pattern);
    }
  }

  private async invalidatePattern(pattern: string): Promise<void> {
    const store = this.cacheManager.store as any;
    if (store.keys) {
      const keys = await store.keys(`${pattern}*`);
      if (keys.length > 0) {
        await Promise.all(keys.map((key) => this.cacheManager.del(key)));
      }
    }
  }
}

// Usage in service
@Injectable()
export class ProductsService {
  constructor(private eventEmitter: EventEmitter2) {}

  async update(id: string, data: UpdateProductDto): Promise<Product> {
    const product = await this.repository.update(id, data);

    this.eventEmitter.emit(
      'cache.invalidate',
      new CacheInvalidationEvent('product:', [`product:${id}`]),
    );

    return product;
  }
}
```

### Tag-Based Invalidation

```typescript
// common/cache/tagged-cache.service.ts
@Injectable()
export class TaggedCacheService {
  constructor(@Inject(CACHE_MANAGER) private cacheManager: Cache) {}

  async setWithTags<T>(
    key: string,
    value: T,
    tags: string[],
    ttl?: number,
  ): Promise<void> {
    // Store the value
    await this.cacheManager.set(key, value, ttl);

    // Store key in each tag set
    for (const tag of tags) {
      const tagKey = `tag:${tag}`;
      const taggedKeys = (await this.cacheManager.get<string[]>(tagKey)) || [];
      if (!taggedKeys.includes(key)) {
        taggedKeys.push(key);
        await this.cacheManager.set(tagKey, taggedKeys);
      }
    }
  }

  async invalidateByTag(tag: string): Promise<void> {
    const tagKey = `tag:${tag}`;
    const taggedKeys = (await this.cacheManager.get<string[]>(tagKey)) || [];

    // Delete all tagged keys
    await Promise.all(taggedKeys.map((key) => this.cacheManager.del(key)));

    // Delete the tag itself
    await this.cacheManager.del(tagKey);
  }
}

// Usage
await taggedCache.setWithTags(
  `product:${id}`,
  product,
  ['products', `category:${product.categoryId}`],
  600000,
);

// Invalidate all products in a category
await taggedCache.invalidateByTag(`category:${categoryId}`);
```

## HTTP Caching

### Response Cache Headers

```typescript
// common/interceptors/http-cache.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable()
export class HttpCacheInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const response = context.switchToHttp().getResponse();

    return next.handle().pipe(
      tap(() => {
        // Set cache control headers
        response.setHeader('Cache-Control', 'public, max-age=300');
        response.setHeader('ETag', this.generateETag(response));
      }),
    );
  }

  private generateETag(response: any): string {
    // Generate ETag based on response body
    const body = JSON.stringify(response);
    return `"${Buffer.from(body).toString('base64').slice(0, 27)}"`;
  }
}

// ETag validation middleware
@Injectable()
export class ETagMiddleware implements NestMiddleware {
  use(req: Request, res: Response, next: NextFunction) {
    const ifNoneMatch = req.headers['if-none-match'];
    const etag = res.getHeader('ETag');

    if (ifNoneMatch && ifNoneMatch === etag) {
      res.status(304).end();
      return;
    }

    next();
  }
}
```

## Multi-Level Caching

```typescript
// common/cache/multi-level-cache.service.ts
@Injectable()
export class MultiLevelCacheService {
  private localCache = new Map<string, { value: any; expiry: number }>();

  constructor(@Inject(CACHE_MANAGER) private redisCache: Cache) {}

  async get<T>(key: string): Promise<T | undefined> {
    // Level 1: Local memory cache
    const local = this.localCache.get(key);
    if (local && local.expiry > Date.now()) {
      return local.value;
    }

    // Level 2: Redis cache
    const redis = await this.redisCache.get<T>(key);
    if (redis !== undefined) {
      // Populate local cache
      this.localCache.set(key, {
        value: redis,
        expiry: Date.now() + 60000, // 1 minute local TTL
      });
      return redis;
    }

    return undefined;
  }

  async set<T>(key: string, value: T, ttl: number): Promise<void> {
    // Set in both caches
    await this.redisCache.set(key, value, ttl);
    this.localCache.set(key, {
      value,
      expiry: Date.now() + Math.min(ttl, 60000),
    });
  }

  async del(key: string): Promise<void> {
    await this.redisCache.del(key);
    this.localCache.delete(key);
  }

  // Cleanup expired local cache entries
  @Cron('*/5 * * * *') // Every 5 minutes
  cleanupLocalCache() {
    const now = Date.now();
    for (const [key, entry] of this.localCache.entries()) {
      if (entry.expiry <= now) {
        this.localCache.delete(key);
      }
    }
  }
}
```

## Cache Monitoring

```typescript
// common/cache/cache-metrics.service.ts
@Injectable()
export class CacheMetricsService {
  private hits = 0;
  private misses = 0;

  recordHit(): void {
    this.hits++;
  }

  recordMiss(): void {
    this.misses++;
  }

  getStats(): CacheStats {
    const total = this.hits + this.misses;
    return {
      hits: this.hits,
      misses: this.misses,
      hitRate: total > 0 ? this.hits / total : 0,
      total,
    };
  }

  reset(): void {
    this.hits = 0;
    this.misses = 0;
  }
}

// Cache metrics endpoint
@Controller('admin/cache')
export class CacheAdminController {
  constructor(
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private metricsService: CacheMetricsService,
  ) {}

  @Get('stats')
  getStats() {
    return this.metricsService.getStats();
  }

  @Delete('flush')
  async flushCache() {
    await (this.cacheManager.store as any).reset?.();
    return { message: 'Cache flushed' };
  }
}
```

## Best Practices

1. **Choose TTL wisely**: Balance freshness vs performance
2. **Invalidate proactively**: Don't rely on TTL alone
3. **Use tags**: Group related cache entries
4. **Monitor hit rates**: Track cache effectiveness
5. **Handle failures gracefully**: Cache miss should fall back to source
6. **Avoid cache stampede**: Use locks for expensive operations

## Checklist

- [ ] Cache store configured (Redis recommended)
- [ ] TTL strategy defined
- [ ] Invalidation patterns implemented
- [ ] Cache-aside pattern for reads
- [ ] Event-based invalidation for writes
- [ ] HTTP cache headers for static content
- [ ] Cache metrics and monitoring
- [ ] Cache warm-up strategy (if needed)
