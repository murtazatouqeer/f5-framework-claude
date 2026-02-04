---
name: nuxt-nitro
description: Nitro server engine in Nuxt 3
applies_to: nuxt
---

# Nitro Server Engine

## Overview

Nitro is Nuxt's server engine that enables universal deployment to any platform with zero configuration.

## Key Features

- **Universal deployment** - Node.js, Serverless, Edge, Static
- **Auto-imported utilities** - defineEventHandler, readBody, etc.
- **File-based routing** - API routes in server/api/
- **Hybrid rendering** - Mix SSR, SSG, SPA per route
- **Built-in caching** - defineCachedEventHandler
- **Storage abstraction** - useStorage for any backend

## Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    // Deployment preset
    preset: 'node-server', // or 'vercel', 'netlify', 'cloudflare', etc.

    // Prerender routes
    prerender: {
      routes: ['/sitemap.xml'],
      crawlLinks: true,
    },

    // Route rules
    routeRules: {
      '/api/**': { cors: true },
      '/blog/**': { isr: 3600 },
    },

    // Compression
    compressPublicAssets: true,

    // Storage
    storage: {
      cache: {
        driver: 'redis',
        url: process.env.REDIS_URL,
      },
    },

    // Development server
    devServer: {
      watch: ['./server'],
    },
  },
});
```

## Deployment Presets

### Node.js Server

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'node-server',
  },
});
```

```bash
npm run build
node .output/server/index.mjs
```

### Vercel

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'vercel',
  },
});
```

### Netlify

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'netlify',
  },
});
```

### Cloudflare Pages

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'cloudflare-pages',
  },
});
```

### AWS Lambda

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    preset: 'aws-lambda',
  },
});
```

### Docker

```dockerfile
# Dockerfile
FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

EXPOSE 3000
CMD ["node", ".output/server/index.mjs"]
```

## Server Routes

### API Routes

```typescript
// server/api/products/index.get.ts
export default defineEventHandler(async (event) => {
  const query = getQuery(event);
  const products = await prisma.product.findMany();
  return products;
});
```

### Custom Routes

```typescript
// server/routes/health.ts
export default defineEventHandler(() => {
  return { status: 'ok', timestamp: Date.now() };
});
```

### Middleware

```typescript
// server/middleware/auth.ts
export default defineEventHandler(async (event) => {
  const token = getHeader(event, 'authorization');
  if (!token && event.path.startsWith('/api/protected')) {
    throw createError({ statusCode: 401 });
  }
});
```

## Storage

### Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    storage: {
      // File system storage
      fs: {
        driver: 'fs',
        base: './data',
      },

      // Redis
      redis: {
        driver: 'redis',
        url: process.env.REDIS_URL,
      },

      // Cloudflare KV
      kv: {
        driver: 'cloudflare-kv-binding',
        binding: 'MY_KV',
      },
    },
  },
});
```

### Using Storage

```typescript
// server/api/cache/[key].ts
export default defineEventHandler(async (event) => {
  const key = getRouterParam(event, 'key');
  const storage = useStorage('redis');

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

## Caching

### Cached Event Handler

```typescript
// server/api/products/index.get.ts
export default defineCachedEventHandler(
  async (event) => {
    const products = await prisma.product.findMany();
    return products;
  },
  {
    maxAge: 60 * 10, // 10 minutes
    staleMaxAge: 60 * 60, // 1 hour stale
    swr: true,
    name: 'products',
    getKey: (event) => {
      const query = getQuery(event);
      return `products-${query.page}-${query.limit}`;
    },
  }
);
```

### Cached Function

```typescript
// server/utils/products.ts
export const getCachedProducts = defineCachedFunction(
  async (categoryId?: string) => {
    return await prisma.product.findMany({
      where: categoryId ? { categoryId } : undefined,
    });
  },
  {
    maxAge: 60 * 5, // 5 minutes
    name: 'products-by-category',
    getKey: (categoryId) => categoryId || 'all',
  }
);
```

## Plugins

### Server Plugin

```typescript
// server/plugins/database.ts
export default defineNitroPlugin(async (nitro) => {
  // Initialize database connection
  await connectDatabase();

  // Cleanup on shutdown
  nitro.hooks.hook('close', async () => {
    await disconnectDatabase();
  });
});
```

### Request Hooks

```typescript
// server/plugins/logger.ts
export default defineNitroPlugin((nitro) => {
  nitro.hooks.hook('request', (event) => {
    console.log(`[${new Date().toISOString()}] ${event.method} ${event.path}`);
  });

  nitro.hooks.hook('afterResponse', (event, response) => {
    console.log(`Response: ${response?.statusCode}`);
  });
});
```

## Environment Variables

```typescript
// Runtime config in API routes
export default defineEventHandler((event) => {
  const config = useRuntimeConfig(event);

  // Server-only secrets
  const apiSecret = config.apiSecret;

  // Public config
  const apiBase = config.public.apiBase;

  return { configured: true };
});
```

## Build Output

```bash
npm run build

# Output structure
.output/
├── server/
│   ├── index.mjs        # Entry point
│   ├── chunks/          # Server chunks
│   └── node_modules/    # Production deps
├── public/
│   ├── _nuxt/           # Client assets
│   └── ...
└── nitro.json           # Build metadata
```

## Best Practices

1. **Choose right preset** - Match deployment target
2. **Use caching** - defineCachedEventHandler for performance
3. **Storage abstraction** - useStorage for flexibility
4. **Environment variables** - runtimeConfig for secrets
5. **Plugins for setup** - Database, logging initialization
6. **Route rules** - Per-route rendering strategies
