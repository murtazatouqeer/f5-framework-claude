---
name: nuxt-caching
description: Data caching strategies in Nuxt 3
applies_to: nuxt
---

# Data Caching in Nuxt 3

## Overview

Nuxt 3 provides multiple caching strategies for optimal performance: client-side caching, server-side caching, and CDN caching.

## Client-Side Caching

### useFetch Caching

```typescript
// Default caching by URL
const { data } = await useFetch('/api/products');

// Custom cache key
const { data } = await useFetch('/api/products', {
  key: 'products-list',
});

// Unique key with params
const { data } = await useFetch(`/api/products/${id}`, {
  key: `product-${id}`,
});
```

### getCachedData

```typescript
const { data } = await useFetch('/api/products', {
  key: 'products',

  getCachedData: (key) => {
    const nuxtApp = useNuxtApp();

    // Check payload (SSR data)
    const cachedData = nuxtApp.payload.data[key];

    if (cachedData) {
      return cachedData;
    }

    // Or check static data
    return nuxtApp.static.data[key];
  },
});
```

### Time-Based Cache

```typescript
interface CachedData<T> {
  data: T;
  fetchedAt: number;
}

const { data } = await useFetch<Product[]>('/api/products', {
  key: 'products',

  getCachedData: (key) => {
    const nuxtApp = useNuxtApp();
    const cached = nuxtApp.payload.data[key] as CachedData<Product[]> | undefined;

    if (!cached) return null;

    // Cache for 5 minutes
    const maxAge = 5 * 60 * 1000;
    const isStale = Date.now() - cached.fetchedAt > maxAge;

    return isStale ? null : cached.data;
  },

  transform: (data) => ({
    data,
    fetchedAt: Date.now(),
  }),
});
```

### Dedupe Requests

```typescript
// Prevent duplicate concurrent requests
const { data, refresh } = await useFetch('/api/products');

// Multiple refreshes dedupe by default
await refresh({ dedupe: true }); // default
await refresh({ dedupe: false }); // Force new request
```

## Server-Side Caching

### Route Rules Cache

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Cache API responses
    '/api/products': {
      cache: {
        maxAge: 60, // 1 minute
        staleMaxAge: 600, // Serve stale for 10 min while revalidating
      },
    },

    // Different cache for different routes
    '/api/products/**': { cache: { maxAge: 300 } }, // 5 min
    '/api/categories': { cache: { maxAge: 3600 } }, // 1 hour
    '/api/user/**': { cache: false }, // No cache
  },
});
```

### SWR (Stale-While-Revalidate)

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Serve stale immediately, revalidate in background
    '/api/products/**': {
      swr: 60, // 60 seconds
    },

    // With custom stale time
    '/api/blog/**': {
      swr: true, // Use defaults
      cache: {
        maxAge: 60,
        staleMaxAge: 3600,
      },
    },
  },
});
```

### ISR (Incremental Static Regeneration)

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Regenerate every hour
    '/blog/**': {
      isr: 3600,
    },

    // With custom behavior
    '/products/**': {
      isr: 600, // 10 minutes
      prerender: true, // Also prerender at build
    },
  },
});
```

## API Route Caching

### defineCachedEventHandler

```typescript
// server/api/products/index.get.ts
export default defineCachedEventHandler(
  async () => {
    const products = await prisma.product.findMany();
    return products;
  },
  {
    maxAge: 60, // Cache for 60 seconds
    staleMaxAge: 600, // Serve stale for 10 min
    swr: true, // Enable SWR
    name: 'products', // Cache key name
    getKey: (event) => {
      // Custom cache key
      const query = getQuery(event);
      return `products-${query.page}-${query.limit}`;
    },
  }
);
```

### defineCachedFunction

```typescript
// server/utils/products.ts
export const getCachedProducts = defineCachedFunction(
  async (categoryId?: string) => {
    const where = categoryId ? { categoryId } : {};
    return await prisma.product.findMany({ where });
  },
  {
    maxAge: 300,
    name: 'products-by-category',
    getKey: (categoryId) => categoryId || 'all',
  }
);

// Usage in API route
export default defineEventHandler(async (event) => {
  const { categoryId } = getQuery(event);
  return await getCachedProducts(categoryId as string | undefined);
});
```

## Cache Invalidation

### Manual Invalidation

```typescript
// server/api/products/index.post.ts
export default defineEventHandler(async (event) => {
  const body = await readBody(event);

  // Create product
  const product = await prisma.product.create({ data: body });

  // Invalidate cache
  const storage = useStorage('cache');
  await storage.removeItem('nitro:handlers:products');

  return product;
});
```

### With Unstorage

```typescript
// server/utils/cache.ts
export async function invalidateProductCache() {
  const storage = useStorage('cache');

  // Remove specific keys
  await storage.removeItem('nitro:handlers:products');

  // Remove by pattern
  const keys = await storage.getKeys('nitro:handlers:products');
  await Promise.all(keys.map((key) => storage.removeItem(key)));
}

// Usage
export default defineEventHandler(async (event) => {
  await invalidateProductCache();
  // ...
});
```

## CDN/Edge Caching

### Cache-Control Headers

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Static assets - long cache
    '/_nuxt/**': {
      headers: {
        'Cache-Control': 'public, max-age=31536000, immutable',
      },
    },

    // API with CDN cache
    '/api/products': {
      headers: {
        'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=600',
      },
    },

    // No CDN cache, browser cache only
    '/api/user': {
      headers: {
        'Cache-Control': 'private, max-age=0, must-revalidate',
      },
    },
  },
});
```

### Vary Header

```typescript
// server/api/products.ts
export default defineEventHandler(async (event) => {
  // Cache varies by these headers
  setHeader(event, 'Vary', 'Accept-Language, Authorization');

  // ...
});
```

## State Caching

### useState with Caching

```typescript
// composables/useProducts.ts
export function useProducts() {
  // Cached in memory during session
  const products = useState<Product[]>('products', () => []);
  const lastFetch = useState<number>('products-fetch-time', () => 0);

  async function fetchProducts(force = false) {
    const now = Date.now();
    const cacheTime = 5 * 60 * 1000; // 5 minutes

    // Use cached if not stale
    if (!force && products.value.length && now - lastFetch.value < cacheTime) {
      return products.value;
    }

    const data = await $fetch<Product[]>('/api/products');
    products.value = data;
    lastFetch.value = now;

    return data;
  }

  return {
    products: readonly(products),
    fetchProducts,
  };
}
```

### Pinia with Persistence

```typescript
// stores/products.ts
export const useProductStore = defineStore('products', {
  state: () => ({
    products: [] as Product[],
    lastFetch: 0,
  }),

  actions: {
    async fetchProducts() {
      // Cache check
      if (this.products.length && Date.now() - this.lastFetch < 300000) {
        return;
      }

      this.products = await $fetch('/api/products');
      this.lastFetch = Date.now();
    },
  },

  persist: {
    storage: persistedState.localStorage,
    paths: ['products', 'lastFetch'],
  },
});
```

## Best Practices

1. **Layer caching** - Client → Server → CDN
2. **Appropriate TTLs** - Balance freshness vs performance
3. **Cache keys** - Include relevant parameters
4. **Invalidation** - Clear cache on mutations
5. **SWR for UX** - Show stale data while fetching fresh
6. **Private data** - Never cache user-specific data publicly
