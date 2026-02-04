---
name: nuxt-edge
description: Edge deployment strategies for Nuxt 3
applies_to: nuxt
---

# Edge Deployment

## Overview

Edge deployment runs Nuxt closer to users at CDN edge locations, providing lower latency and faster responses.

## Edge Platforms

### Cloudflare Pages

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'cloudflare-pages',
  },
});
```

### Cloudflare Workers

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'cloudflare-worker',
  },
});
```

### Vercel Edge

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'vercel-edge',
  },
});
```

### Netlify Edge

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'netlify-edge',
  },
});
```

## Route-Level Edge

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Specific routes at edge
    '/api/fast/**': { edge: true },
    '/public/**': { edge: true },

    // Rest at origin
    '/api/heavy/**': { edge: false },
  },
});
```

## Edge API Routes

### Basic Edge Route

```typescript
// server/api/hello.ts
export default defineEventHandler((event) => {
  // Runs at edge
  return {
    message: 'Hello from the edge!',
    location: event.context.cf?.colo, // Cloudflare location
  };
});
```

### With Geo Data

```typescript
// server/api/location.ts
export default defineEventHandler((event) => {
  // Cloudflare geo data
  const cf = event.context.cf;

  return {
    country: cf?.country,
    city: cf?.city,
    timezone: cf?.timezone,
    latitude: cf?.latitude,
    longitude: cf?.longitude,
  };
});
```

## Edge KV Storage

### Cloudflare KV

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'cloudflare-pages',
    storage: {
      kv: {
        driver: 'cloudflare-kv-binding',
        binding: 'MY_KV_NAMESPACE',
      },
    },
  },
});
```

```typescript
// server/api/cache/[key].ts
export default defineEventHandler(async (event) => {
  const key = getRouterParam(event, 'key');
  const storage = useStorage('kv');

  if (event.method === 'GET') {
    return await storage.getItem(key);
  }

  if (event.method === 'POST') {
    const body = await readBody(event);
    await storage.setItem(key, body);
    return { success: true };
  }
});
```

### Vercel KV

```typescript
// server/utils/edge-cache.ts
import { kv } from '@vercel/kv';

export async function getCached<T>(key: string): Promise<T | null> {
  return await kv.get(key);
}

export async function setCached(key: string, value: any, ttl?: number) {
  if (ttl) {
    await kv.set(key, value, { ex: ttl });
  } else {
    await kv.set(key, value);
  }
}
```

## Edge Middleware

### Geo-based Routing

```typescript
// middleware/geo.ts
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) {
    const event = useRequestEvent();
    const country = event?.context?.cf?.country || 'US';

    // Redirect to localized version
    if (country === 'JP' && !to.path.startsWith('/ja')) {
      return navigateTo('/ja' + to.path);
    }

    if (country === 'DE' && !to.path.startsWith('/de')) {
      return navigateTo('/de' + to.path);
    }
  }
});
```

### A/B Testing

```typescript
// middleware/ab-test.ts
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) {
    const event = useRequestEvent();

    // Get or set experiment cookie
    let variant = getCookie(event!, 'ab-variant');

    if (!variant) {
      // Random assignment
      variant = Math.random() > 0.5 ? 'A' : 'B';
      setCookie(event!, 'ab-variant', variant, { maxAge: 60 * 60 * 24 * 30 });
    }

    // Inject into context
    event!.context.abVariant = variant;
  }
});
```

### Bot Detection

```typescript
// middleware/bot-protection.ts
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) {
    const event = useRequestEvent();
    const userAgent = getHeader(event!, 'user-agent') || '';

    // Simple bot detection
    const bots = ['bot', 'crawler', 'spider', 'scraper'];
    const isBot = bots.some((bot) => userAgent.toLowerCase().includes(bot));

    if (isBot && to.path.startsWith('/api')) {
      throw createError({ statusCode: 403, message: 'Forbidden' });
    }
  }
});
```

## Edge Caching

### Stale-While-Revalidate

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    '/api/products/**': {
      swr: 60, // 60 seconds
      edge: true,
    },
  },
});
```

### Custom Cache Headers

```typescript
// server/api/products.ts
export default defineEventHandler(async (event) => {
  const products = await getProducts();

  // Set cache headers
  setHeader(event, 'Cache-Control', 'public, s-maxage=60, stale-while-revalidate=600');

  return products;
});
```

## Edge Limitations

### What Works at Edge

- Simple computations
- KV storage operations
- HTTP requests (fetch)
- Cookie manipulation
- Header manipulation
- Geo routing

### What Doesn't Work

- Node.js APIs (fs, path, etc.)
- Traditional databases (use edge DBs)
- Long-running processes
- Large memory operations

## Hybrid Architecture

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Fast, cacheable at edge
    '/api/public/**': { edge: true, swr: 60 },
    '/static/**': { edge: true, prerender: true },

    // Complex, at origin
    '/api/admin/**': { edge: false },
    '/api/payments/**': { edge: false },

    // SSR at edge
    '/products/**': { edge: true, isr: 3600 },

    // SPA (no server)
    '/dashboard/**': { ssr: false },
  },
});
```

## Database at Edge

### Cloudflare D1

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'cloudflare-pages',
  },
});
```

```typescript
// server/api/users.ts
export default defineEventHandler(async (event) => {
  const db = event.context.cloudflare.env.DB;

  const { results } = await db.prepare('SELECT * FROM users').all();

  return results;
});
```

### PlanetScale / Turso

```typescript
// server/utils/db.ts
import { connect } from '@planetscale/database';

const conn = connect({
  url: process.env.DATABASE_URL,
});

export async function query(sql: string, args?: any[]) {
  const results = await conn.execute(sql, args);
  return results.rows;
}
```

## Best Practices

1. **Identify edge-suitable routes** - Fast, cacheable, low-compute
2. **Use KV for state** - Not traditional databases
3. **Cache aggressively** - SWR for dynamic content
4. **Fallback to origin** - Complex operations at origin
5. **Test edge locally** - Use Wrangler for Cloudflare
6. **Monitor cold starts** - Edge functions have startup costs
