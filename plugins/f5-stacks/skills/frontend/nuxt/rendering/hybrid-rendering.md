---
name: nuxt-hybrid-rendering
description: Per-route rendering modes in Nuxt 3
applies_to: nuxt
---

# Hybrid Rendering in Nuxt 3

## Overview

Hybrid rendering allows different rendering strategies per route, combining SSR, SSG, SPA, and ISR in one application.

## Route Rules Configuration

### nuxt.config.ts
```typescript
export default defineNuxtConfig({
  routeRules: {
    // Server-side rendered (default)
    '/': { ssr: true },

    // Static generation at build time
    '/about': { prerender: true },

    // Client-side only (SPA)
    '/admin/**': { ssr: false },

    // Incremental Static Regeneration
    '/blog/**': { isr: 3600 }, // Revalidate every hour

    // Stale-while-revalidate
    '/products/**': { swr: 60 }, // 60 seconds

    // Cache with max-age
    '/api/**': { cache: { maxAge: 60 * 60 } },

    // Static with headers
    '/docs/**': {
      prerender: true,
      headers: { 'Cache-Control': 'max-age=31536000' },
    },

    // Redirect
    '/old-path': { redirect: '/new-path' },

    // CORS headers for API
    '/api/**': {
      cors: true,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
      },
    },
  },
});
```

## Rendering Modes Explained

### 1. Server-Side Rendering (SSR)
```typescript
routeRules: {
  '/dashboard': { ssr: true },
}
```
- Renders on each request
- Fresh data every time
- Good for personalized/dynamic content

### 2. Static Site Generation (SSG)
```typescript
routeRules: {
  '/about': { prerender: true },
  '/docs/**': { prerender: true },
}
```
- Rendered at build time
- Fastest delivery
- Good for static content

### 3. Client-Side Only (SPA)
```typescript
routeRules: {
  '/admin/**': { ssr: false },
}
```
- No server rendering
- Full client-side app
- Good for admin panels, dashboards

### 4. Incremental Static Regeneration (ISR)
```typescript
routeRules: {
  '/blog/**': { isr: 3600 },
}
```
- Static with background revalidation
- Fresh after TTL expires
- Good for frequently updated content

### 5. Stale-While-Revalidate (SWR)
```typescript
routeRules: {
  '/products/**': { swr: 60 },
}
```
- Serves stale content immediately
- Revalidates in background
- Optimal for read-heavy pages

## Real-World Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Homepage - SSR for personalization
    '/': { ssr: true },

    // Marketing pages - Static
    '/about': { prerender: true },
    '/pricing': { prerender: true },
    '/contact': { prerender: true },

    // Documentation - Static with long cache
    '/docs/**': {
      prerender: true,
      headers: { 'Cache-Control': 'public, max-age=604800' },
    },

    // Blog - ISR (regenerate hourly)
    '/blog': { isr: 3600 },
    '/blog/**': { isr: 3600 },

    // Product catalog - SWR (fast, background refresh)
    '/products': { swr: 300 },
    '/products/**': { swr: 300 },

    // User dashboard - SPA (no SSR)
    '/dashboard/**': { ssr: false },

    // Admin panel - SPA, no indexing
    '/admin/**': {
      ssr: false,
      headers: { 'X-Robots-Tag': 'noindex' },
    },

    // API routes - Cache with CORS
    '/api/**': {
      cors: true,
      cache: { maxAge: 60 },
    },

    // User API - No cache
    '/api/users/**': {
      cors: true,
      cache: false,
    },
  },
});
```

## Per-Page Configuration

### Using definePageMeta
```vue
<!-- pages/admin/dashboard.vue -->
<script setup lang="ts">
definePageMeta({
  // Client-only rendering
  ssr: false,

  // Or specify in page
  layout: 'admin',
});
</script>
```

### Using nuxt.config.ts Override
```typescript
// Page-level takes precedence
definePageMeta({
  ssr: true, // This overrides routeRules
});
```

## Prerendering Specific Pages

### Generate at Build
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    '/products/**': { prerender: true },
  },

  nitro: {
    prerender: {
      // Crawl these routes
      crawlLinks: true,

      // Explicitly prerender these
      routes: ['/sitemap.xml', '/feed.rss'],

      // Ignore these
      ignore: ['/admin'],
    },
  },
});
```

### Dynamic Prerendering
```typescript
// server/routes/sitemap.xml.ts
export default defineEventHandler(async () => {
  const products = await prisma.product.findMany({
    select: { slug: true },
  });

  const urls = products.map((p) => ({
    loc: `/products/${p.slug}`,
    lastmod: new Date().toISOString(),
  }));

  return generateSitemap(urls);
});

// nuxt.config.ts
export default defineNuxtConfig({
  hooks: {
    async 'nitro:config'(nitroConfig) {
      // Fetch products and add to prerender routes
      const products = await fetch('/api/products').then((r) => r.json());

      nitroConfig.prerender?.routes?.push(
        ...products.map((p: { slug: string }) => `/products/${p.slug}`)
      );
    },
  },
});
```

## Edge Rendering

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Render at edge
    '/**': { edge: true },

    // Specific routes at origin
    '/api/private/**': { edge: false },
  },

  nitro: {
    preset: 'cloudflare-pages', // or 'vercel-edge'
  },
});
```

## Cache Headers

```typescript
routeRules: {
  // Public cache
  '/static/**': {
    headers: {
      'Cache-Control': 'public, max-age=31536000, immutable',
    },
  },

  // No cache for dynamic
  '/api/user/**': {
    headers: {
      'Cache-Control': 'private, no-cache, no-store',
    },
  },

  // Stale-while-revalidate headers
  '/products/**': {
    headers: {
      'Cache-Control': 'public, max-age=60, stale-while-revalidate=600',
    },
  },
}
```

## Best Practices

1. **Static for unchanging content** - prerender marketing pages
2. **ISR for semi-dynamic** - blog posts, product pages
3. **SSR for personalized** - dashboards, user content
4. **SPA for admin** - internal tools, no SEO needed
5. **Cache API routes** - reduce server load
6. **Use SWR wisely** - balance freshness vs performance
