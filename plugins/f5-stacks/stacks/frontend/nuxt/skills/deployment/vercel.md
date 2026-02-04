---
name: nuxt-vercel
description: Deploying Nuxt 3 to Vercel
applies_to: nuxt
---

# Deploying to Vercel

## Overview

Vercel provides zero-config deployment for Nuxt 3 with automatic edge functions, serverless API routes, and global CDN.

## Quick Start

### 1. Connect Repository

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

Or connect via Vercel Dashboard:
1. Import Git repository
2. Vercel auto-detects Nuxt
3. Deploy

### 2. Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  // Vercel preset is auto-detected
  // But can be explicit:
  nitro: {
    preset: 'vercel',
  },
});
```

## Environment Variables

### In Vercel Dashboard

1. Go to Project Settings > Environment Variables
2. Add variables for:
   - Production
   - Preview
   - Development

### In nuxt.config.ts

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  runtimeConfig: {
    // Server-only (use NUXT_ prefix in Vercel)
    databaseUrl: process.env.DATABASE_URL,
    apiSecret: process.env.API_SECRET,

    // Public (use NUXT_PUBLIC_ prefix)
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE,
    },
  },
});
```

### Variable Naming

```bash
# Vercel Environment Variables
DATABASE_URL=postgres://...
API_SECRET=secret123
NUXT_PUBLIC_API_BASE=https://api.example.com
```

## Route Rules

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Static pages
    '/': { prerender: true },
    '/about': { prerender: true },

    // ISR for blog
    '/blog/**': { isr: 3600 },

    // Edge rendering
    '/api/**': { edge: true },

    // SPA for admin
    '/admin/**': { ssr: false },
  },
});
```

## Edge Functions

### Edge API Routes

```typescript
// server/api/hello.ts
export default defineEventHandler((event) => {
  return { message: 'Hello from the edge!' };
});
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    '/api/**': {
      edge: true, // Run on Vercel Edge
    },
  },
});
```

### Edge Middleware

```typescript
// middleware/geo.ts
export default defineNuxtRouteMiddleware((to) => {
  const event = useRequestEvent();

  // Access Vercel geo data
  const geo = event?.context?.geo;

  if (geo?.country === 'JP') {
    // Redirect to Japanese site
    return navigateTo('/ja' + to.path);
  }
});
```

## Vercel KV

```bash
# Install SDK
npm install @vercel/kv
```

```typescript
// server/utils/kv.ts
import { kv } from '@vercel/kv';

export async function getFromCache(key: string) {
  return await kv.get(key);
}

export async function setInCache(key: string, value: any, ttl?: number) {
  if (ttl) {
    await kv.set(key, value, { ex: ttl });
  } else {
    await kv.set(key, value);
  }
}
```

## Vercel Postgres

```bash
npm install @vercel/postgres
```

```typescript
// server/utils/db.ts
import { sql } from '@vercel/postgres';

export async function getProducts() {
  const { rows } = await sql`SELECT * FROM products`;
  return rows;
}
```

## Vercel Blob Storage

```bash
npm install @vercel/blob
```

```typescript
// server/api/upload.post.ts
import { put } from '@vercel/blob';

export default defineEventHandler(async (event) => {
  const form = await readFormData(event);
  const file = form.get('file') as File;

  const blob = await put(file.name, file, {
    access: 'public',
  });

  return { url: blob.url };
});
```

## Analytics & Speed Insights

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: [
    '@nuxtjs/vercel-analytics',
  ],
});
```

```vue
<!-- app.vue -->
<template>
  <div>
    <NuxtPage />
    <VercelAnalytics />
  </div>
</template>
```

## Preview Deployments

Every PR gets a preview URL:

```yaml
# vercel.json
{
  "git": {
    "deploymentEnabled": {
      "main": true,
      "develop": true
    }
  }
}
```

## Custom Domain

1. Go to Project Settings > Domains
2. Add domain
3. Configure DNS:
   - A record: `76.76.21.21`
   - CNAME: `cname.vercel-dns.com`

## vercel.json

```json
{
  "framework": "nuxt",
  "buildCommand": "npm run build",
  "outputDirectory": ".output",
  "regions": ["iad1"],
  "functions": {
    "server/api/**": {
      "maxDuration": 30
    }
  },
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "X-Content-Type-Options",
          "value": "nosniff"
        }
      ]
    }
  ],
  "redirects": [
    {
      "source": "/old-path",
      "destination": "/new-path",
      "permanent": true
    }
  ]
}
```

## Monorepo Setup

```json
// vercel.json
{
  "framework": "nuxt",
  "installCommand": "npm install",
  "buildCommand": "npm run build",
  "outputDirectory": ".output",
  "rootDirectory": "apps/web"
}
```

## CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Vercel

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to Vercel
        uses: amondnet/vercel-action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
          vercel-args: '--prod'
```

## Best Practices

1. **Use ISR for content** - Faster builds, fresh content
2. **Edge for APIs** - Lower latency globally
3. **Environment per branch** - Different configs per environment
4. **Vercel integrations** - KV, Postgres, Blob for data
5. **Preview deployments** - Test before merging
6. **Monitor with Analytics** - Track performance
