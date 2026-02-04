---
name: http-caching
description: HTTP caching headers and browser caching strategies
category: performance/caching
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# HTTP Caching

## Overview

HTTP caching uses headers to control how browsers and proxies cache responses.
Proper HTTP caching can eliminate network requests entirely for repeat visits.

## Cache Control Header

### Directives

```
Cache-Control: [directive1], [directive2], ...

Common directives:
- public        : Response can be cached by any cache
- private       : Response only for single user, not CDN
- no-cache      : Must revalidate before using cached copy
- no-store      : Don't cache at all (sensitive data)
- max-age=N     : Fresh for N seconds
- s-maxage=N    : Fresh for N seconds (shared caches only)
- must-revalidate : Must revalidate when stale
- immutable     : Never changes (can skip revalidation)
- stale-while-revalidate=N : Serve stale while fetching fresh
```

### Implementation

```typescript
// Express middleware for cache headers
import { Request, Response, NextFunction } from 'express';

interface CacheOptions {
  maxAge?: number;
  sMaxAge?: number;
  isPublic?: boolean;
  isPrivate?: boolean;
  noCache?: boolean;
  noStore?: boolean;
  mustRevalidate?: boolean;
  immutable?: boolean;
  staleWhileRevalidate?: number;
}

function setCacheHeaders(options: CacheOptions) {
  return (req: Request, res: Response, next: NextFunction) => {
    const directives: string[] = [];

    if (options.isPublic) directives.push('public');
    if (options.isPrivate) directives.push('private');
    if (options.noCache) directives.push('no-cache');
    if (options.noStore) directives.push('no-store');
    if (options.mustRevalidate) directives.push('must-revalidate');
    if (options.immutable) directives.push('immutable');

    if (options.maxAge !== undefined) {
      directives.push(`max-age=${options.maxAge}`);
    }
    if (options.sMaxAge !== undefined) {
      directives.push(`s-maxage=${options.sMaxAge}`);
    }
    if (options.staleWhileRevalidate !== undefined) {
      directives.push(`stale-while-revalidate=${options.staleWhileRevalidate}`);
    }

    if (directives.length > 0) {
      res.setHeader('Cache-Control', directives.join(', '));
    }

    next();
  };
}

// Usage examples
app.get('/api/products',
  setCacheHeaders({ isPublic: true, maxAge: 300, sMaxAge: 600 }),
  getProducts
);

app.get('/api/user/profile',
  setCacheHeaders({ isPrivate: true, maxAge: 60, noCache: true }),
  getUserProfile
);

app.get('/static/:file',
  setCacheHeaders({ isPublic: true, maxAge: 31536000, immutable: true }),
  serveStatic
);
```

## ETag and Conditional Requests

### ETag Generation

```typescript
import crypto from 'crypto';

// Generate ETag from content
function generateETag(content: string | Buffer): string {
  const hash = crypto
    .createHash('md5')
    .update(content)
    .digest('hex');
  return `"${hash}"`;
}

// Generate weak ETag (for semantic equivalence)
function generateWeakETag(content: string | Buffer): string {
  const hash = crypto
    .createHash('md5')
    .update(content)
    .digest('hex')
    .slice(0, 8);
  return `W/"${hash}"`;
}
```

### Conditional Request Middleware

```typescript
function conditionalGet() {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Store original send
    const originalSend = res.send.bind(res);

    res.send = function(body: any): Response {
      // Generate ETag
      const content = typeof body === 'string' ? body : JSON.stringify(body);
      const etag = generateETag(content);

      // Set ETag header
      res.setHeader('ETag', etag);

      // Check If-None-Match header
      const clientETag = req.header('If-None-Match');
      if (clientETag === etag) {
        res.status(304);
        return originalSend('');
      }

      return originalSend(body);
    };

    next();
  };
}

// Usage
app.get('/api/data', conditionalGet(), async (req, res) => {
  const data = await getData();
  res.json(data);
});
```

### Last-Modified Header

```typescript
function lastModified() {
  return async (req: Request, res: Response, next: NextFunction) => {
    const originalJson = res.json.bind(res);

    res.json = function(body: any): Response {
      // Check for lastModified in response data
      if (body.updatedAt) {
        const lastModified = new Date(body.updatedAt).toUTCString();
        res.setHeader('Last-Modified', lastModified);

        // Check If-Modified-Since header
        const clientDate = req.header('If-Modified-Since');
        if (clientDate) {
          const clientTime = new Date(clientDate).getTime();
          const serverTime = new Date(body.updatedAt).getTime();

          if (serverTime <= clientTime) {
            res.status(304);
            return res.send('');
          }
        }
      }

      return originalJson(body);
    };

    next();
  };
}
```

## Caching Strategies by Content Type

### Static Assets (Images, JS, CSS)

```typescript
// Long cache with content hashing
app.use('/static', express.static('public', {
  maxAge: '1y',
  immutable: true,
  etag: false, // Not needed with content hashing
  lastModified: false,
  setHeaders: (res, path) => {
    // Fingerprinted files can be cached forever
    if (path.match(/\.[a-f0-9]{8}\./)) {
      res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
    }
  },
}));
```

### API Responses

```typescript
// Cache configuration by endpoint type
const cacheProfiles = {
  // Public, rarely changing data
  catalog: {
    isPublic: true,
    maxAge: 300,        // 5 minutes browser
    sMaxAge: 3600,      // 1 hour CDN
    staleWhileRevalidate: 86400,
  },

  // User-specific data
  userProfile: {
    isPrivate: true,
    maxAge: 60,
    noCache: true,      // Always revalidate
  },

  // Real-time data
  stockPrices: {
    noStore: true,      // Never cache
  },

  // Aggregated/computed data
  reports: {
    isPrivate: true,
    maxAge: 3600,
    mustRevalidate: true,
  },
};

// Apply to routes
app.get('/api/catalog', setCacheHeaders(cacheProfiles.catalog), getCatalog);
app.get('/api/user/profile', setCacheHeaders(cacheProfiles.userProfile), getProfile);
app.get('/api/stocks', setCacheHeaders(cacheProfiles.stockPrices), getStocks);
```

### HTML Pages

```typescript
// HTML pages - short cache with revalidation
app.get('/', (req, res) => {
  res.setHeader('Cache-Control', 'public, max-age=0, must-revalidate');

  // Generate ETag for content
  const html = renderPage();
  const etag = generateETag(html);
  res.setHeader('ETag', etag);

  // Conditional response
  if (req.header('If-None-Match') === etag) {
    return res.status(304).send();
  }

  res.send(html);
});
```

## Vary Header

```typescript
// Vary header tells caches which request headers affect the response
app.get('/api/data', (req, res) => {
  // Response varies by Accept-Language and Accept-Encoding
  res.setHeader('Vary', 'Accept-Language, Accept-Encoding');

  const lang = req.header('Accept-Language')?.split(',')[0] || 'en';
  const data = getDataByLanguage(lang);

  res.json(data);
});

// Common Vary values:
// - Accept-Encoding (for compression)
// - Accept-Language (for localization)
// - Authorization (for user-specific data)
// - Cookie (when response depends on cookies)
```

## Cache Busting

### Content Hashing

```typescript
// Webpack configuration for content hashing
module.exports = {
  output: {
    filename: '[name].[contenthash].js',
    chunkFilename: '[name].[contenthash].chunk.js',
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: '[name].[contenthash].css',
    }),
  ],
};
```

### Query String Versioning

```typescript
// Generate versioned URLs
function versionedUrl(path: string, version: string): string {
  return `${path}?v=${version}`;
}

// Or with file hash
import { createHash } from 'crypto';
import { readFileSync } from 'fs';

function hashedUrl(filePath: string): string {
  const content = readFileSync(filePath);
  const hash = createHash('md5').update(content).digest('hex').slice(0, 8);
  return `${filePath}?v=${hash}`;
}
```

## Service Worker Caching

```typescript
// service-worker.ts
const CACHE_NAME = 'app-v1';
const STATIC_ASSETS = [
  '/',
  '/app.js',
  '/styles.css',
  '/offline.html',
];

// Cache on install
self.addEventListener('install', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
});

// Serve from cache, fallback to network
self.addEventListener('fetch', (event: FetchEvent) => {
  event.respondWith(
    caches.match(event.request).then((cached) => {
      // Cache-first strategy for static assets
      if (cached && isStaticAsset(event.request.url)) {
        return cached;
      }

      // Network-first strategy for API
      if (event.request.url.includes('/api/')) {
        return fetch(event.request)
          .then((response) => {
            // Cache successful API responses
            if (response.ok) {
              const clone = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, clone);
              });
            }
            return response;
          })
          .catch(() => {
            // Return cached version if offline
            return cached || new Response('Offline', { status: 503 });
          });
      }

      // Default: network with cache fallback
      return fetch(event.request).catch(() => cached);
    })
  );
});

// Clean old caches
self.addEventListener('activate', (event: ExtendableEvent) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
});
```

## Best Practices

1. **Use long cache for versioned assets** - Static files with hash in filename
2. **Use short cache with revalidation for HTML** - Always fresh content
3. **Use no-store for sensitive data** - Auth tokens, personal data
4. **Set Vary header appropriately** - Prevents incorrect cached responses
5. **Use stale-while-revalidate** - Better UX with background refresh
6. **Implement ETag/Last-Modified** - Enable 304 responses
7. **Consider CDN caching** - Use s-maxage for edge caching
