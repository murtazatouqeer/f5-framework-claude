---
name: cdn-caching
description: CDN configuration and edge caching strategies
category: performance/caching
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CDN Caching

## Overview

Content Delivery Networks (CDNs) cache content at edge locations worldwide,
reducing latency by serving content from servers geographically close to users.

## CDN Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Requests                               │
└───────────────┬─────────────────┬─────────────────┬─────────────────┘
                │                 │                 │
                ▼                 ▼                 ▼
        ┌───────────┐     ┌───────────┐     ┌───────────┐
        │  Edge     │     │  Edge     │     │  Edge     │
        │  Tokyo    │     │  New York │     │  London   │
        └─────┬─────┘     └─────┬─────┘     └─────┬─────┘
              │                 │                 │
              │    Cache Miss   │    Cache Miss   │
              └────────────────►│◄────────────────┘
                                │
                                ▼
                        ┌───────────────┐
                        │    Origin     │
                        │    Server     │
                        └───────────────┘
```

## Cache Control for CDN

### Differentiating Browser vs CDN Cache

```typescript
// Use s-maxage for CDN-specific caching
function setCDNCacheHeaders(options: {
  browserMaxAge: number;
  cdnMaxAge: number;
  staleWhileRevalidate?: number;
}) {
  return (req: Request, res: Response, next: NextFunction) => {
    const directives = [
      'public',
      `max-age=${options.browserMaxAge}`,
      `s-maxage=${options.cdnMaxAge}`,
    ];

    if (options.staleWhileRevalidate) {
      directives.push(`stale-while-revalidate=${options.staleWhileRevalidate}`);
    }

    res.setHeader('Cache-Control', directives.join(', '));
    next();
  };
}

// Examples:
// Browser: 5 min, CDN: 1 hour
app.get('/api/products', setCDNCacheHeaders({
  browserMaxAge: 300,
  cdnMaxAge: 3600,
  staleWhileRevalidate: 86400,
}), getProducts);

// Browser: no cache, CDN: 5 min (for personalization at edge)
app.get('/api/feed', setCDNCacheHeaders({
  browserMaxAge: 0,
  cdnMaxAge: 300,
}), getFeed);
```

### Surrogate Control Header

```typescript
// CDN-specific caching (Fastly, Akamai)
function setSurrogateControl(maxAge: number, staleWhileRevalidate?: number) {
  return (req: Request, res: Response, next: NextFunction) => {
    let value = `max-age=${maxAge}`;
    if (staleWhileRevalidate) {
      value += `, stale-while-revalidate=${staleWhileRevalidate}`;
    }
    res.setHeader('Surrogate-Control', value);
    next();
  };
}
```

## CDN-Specific Configurations

### Cloudflare

```typescript
// Cloudflare-specific headers
function setCloudflareHeaders(options: {
  browserTTL?: number;
  edgeTTL?: number;
  bypassCache?: boolean;
}) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (options.bypassCache) {
      // Bypass Cloudflare cache
      res.setHeader('Cache-Control', 'no-store');
      res.setHeader('CF-Cache-Status', 'BYPASS');
    } else {
      // Set edge cache TTL
      if (options.edgeTTL) {
        res.setHeader('CDN-Cache-Control', `max-age=${options.edgeTTL}`);
      }

      // Set browser cache TTL
      if (options.browserTTL) {
        res.setHeader('Cache-Control', `public, max-age=${options.browserTTL}`);
      }
    }

    next();
  };
}

// Cloudflare Page Rules (via API or dashboard)
const pageRules = {
  // Cache everything for static assets
  '*.example.com/static/*': {
    cache_level: 'cache_everything',
    edge_cache_ttl: 31536000, // 1 year
    browser_cache_ttl: 31536000,
  },

  // API caching with shorter TTL
  'api.example.com/*': {
    cache_level: 'cache_everything',
    edge_cache_ttl: 300, // 5 minutes
    browser_cache_ttl: 60,
  },

  // Bypass cache for dynamic content
  '*.example.com/api/user/*': {
    cache_level: 'bypass',
  },
};
```

### AWS CloudFront

```typescript
// CloudFront cache behavior configuration
const cloudFrontConfig = {
  Origins: [{
    DomainName: 'api.example.com',
    Id: 'apiOrigin',
    CustomOriginConfig: {
      HTTPPort: 80,
      HTTPSPort: 443,
      OriginProtocolPolicy: 'https-only',
    },
  }],

  DefaultCacheBehavior: {
    TargetOriginId: 'apiOrigin',
    ViewerProtocolPolicy: 'redirect-to-https',
    CachePolicyId: 'custom-cache-policy-id',
    OriginRequestPolicyId: 'custom-origin-policy-id',
    Compress: true,
  },

  CacheBehaviors: [
    // Static assets - long cache
    {
      PathPattern: '/static/*',
      TargetOriginId: 'apiOrigin',
      TTL: {
        DefaultTTL: 31536000,
        MaxTTL: 31536000,
        MinTTL: 31536000,
      },
      Compress: true,
    },
    // API responses - short cache
    {
      PathPattern: '/api/*',
      TargetOriginId: 'apiOrigin',
      TTL: {
        DefaultTTL: 300,
        MaxTTL: 3600,
        MinTTL: 0,
      },
      CacheQueryStrings: true,
      CacheHeaders: ['Authorization', 'Accept-Language'],
    },
  ],
};

// Lambda@Edge for dynamic caching
exports.handler = async (event) => {
  const request = event.Records[0].cf.request;
  const response = event.Records[0].cf.response;

  // Add cache headers based on content type
  const contentType = response.headers['content-type']?.[0]?.value || '';

  if (contentType.includes('application/json')) {
    response.headers['cache-control'] = [{
      key: 'Cache-Control',
      value: 'public, max-age=300, s-maxage=3600',
    }];
  }

  return response;
};
```

### Fastly VCL

```vcl
# Fastly VCL configuration

sub vcl_recv {
  # Remove cookies for static assets
  if (req.url ~ "^/static/") {
    unset req.http.Cookie;
  }

  # Hash by specific query params only
  if (req.url ~ "^/api/products") {
    set req.url = querystring.filter_except(req.url, "category,page,sort");
  }
}

sub vcl_fetch {
  # Set default TTL for API responses
  if (req.url ~ "^/api/") {
    set beresp.ttl = 5m;
    set beresp.grace = 1h;
  }

  # Long cache for static assets
  if (req.url ~ "^/static/") {
    set beresp.ttl = 365d;
  }

  # Strip Set-Cookie for cacheable responses
  if (beresp.ttl > 0s) {
    unset beresp.http.Set-Cookie;
  }
}

sub vcl_deliver {
  # Add debug headers in development
  if (req.http.X-Debug) {
    set resp.http.X-Cache-Status = if(obj.hits > 0, "HIT", "MISS");
    set resp.http.X-Cache-Hits = obj.hits;
    set resp.http.X-TTL = obj.ttl;
  }
}
```

## Cache Key Configuration

### Query String Handling

```typescript
// Different cache keys for different query params
function normalizeQueryString(url: string, relevantParams: string[]): string {
  const parsed = new URL(url, 'http://localhost');
  const newParams = new URLSearchParams();

  // Only include relevant params in cache key
  relevantParams.forEach(param => {
    if (parsed.searchParams.has(param)) {
      newParams.set(param, parsed.searchParams.get(param)!);
    }
  });

  // Sort params for consistent cache key
  newParams.sort();

  return `${parsed.pathname}?${newParams.toString()}`;
}

// Example: /products?category=electronics&page=1&utm_source=google
// Cache key: /products?category=electronics&page=1
// (ignores utm_source for caching)
```

### Vary Header Configuration

```typescript
// Proper Vary header for CDN caching
app.get('/api/content', (req, res) => {
  // Only vary on headers that affect response
  res.setHeader('Vary', 'Accept-Language, Accept-Encoding');

  // DON'T include headers that change frequently
  // ❌ Vary: Cookie, Authorization
  // This would effectively disable CDN caching

  const lang = req.header('Accept-Language')?.split(',')[0] || 'en';
  res.json(getContent(lang));
});
```

## Cache Invalidation

### Purge API

```typescript
// Cloudflare purge
async function purgeCloudflareCache(urls: string[]): Promise<void> {
  await fetch(`https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${CF_API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ files: urls }),
  });
}

// Purge by prefix/tag
async function purgeByTag(tags: string[]): Promise<void> {
  await fetch(`https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/purge_cache`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${CF_API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ tags }),
  });
}

// AWS CloudFront invalidation
import { CloudFront } from 'aws-sdk';

const cloudfront = new CloudFront();

async function invalidateCloudFront(paths: string[]): Promise<void> {
  await cloudfront.createInvalidation({
    DistributionId: DISTRIBUTION_ID,
    InvalidationBatch: {
      CallerReference: Date.now().toString(),
      Paths: {
        Quantity: paths.length,
        Items: paths.map(p => p.startsWith('/') ? p : `/${p}`),
      },
    },
  }).promise();
}
```

### Cache Tags

```typescript
// Add cache tags for granular invalidation
function setCacheTags(tags: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    // Cloudflare
    res.setHeader('Cache-Tag', tags.join(','));

    // Fastly
    res.setHeader('Surrogate-Key', tags.join(' '));

    // Akamai
    res.setHeader('Edge-Cache-Tag', tags.join(','));

    next();
  };
}

// Usage
app.get('/api/products/:id', (req, res) => {
  const product = getProduct(req.params.id);

  // Set tags for targeted invalidation
  res.setHeader('Cache-Tag', [
    `product-${product.id}`,
    `category-${product.categoryId}`,
    'products',
  ].join(','));

  res.json(product);
});

// When product updates, invalidate by tag
async function onProductUpdate(productId: string, categoryId: string) {
  await purgeByTag([
    `product-${productId}`,
    `category-${categoryId}`,
  ]);
}
```

## Edge Computing

### Cloudflare Workers

```typescript
// Cloudflare Worker for edge caching with logic
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    // Check edge cache first
    const cacheKey = new Request(url.toString(), request);
    const cache = caches.default;
    let response = await cache.match(cacheKey);

    if (!response) {
      // Fetch from origin
      response = await fetch(request);

      // Clone for caching
      response = new Response(response.body, response);

      // Set cache headers
      response.headers.set('Cache-Control', 'public, max-age=300');

      // Store in edge cache
      if (response.ok) {
        await cache.put(cacheKey, response.clone());
      }
    }

    return response;
  },
};
```

### Vercel Edge Functions

```typescript
// vercel.json
{
  "headers": [
    {
      "source": "/api/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, s-maxage=300, stale-while-revalidate=600"
        }
      ]
    }
  ]
}

// Edge function with caching
export const config = { runtime: 'edge' };

export default async function handler(req: Request) {
  const data = await fetchData();

  return new Response(JSON.stringify(data), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, s-maxage=300, stale-while-revalidate=600',
    },
  });
}
```

## Monitoring and Debugging

```typescript
// Add debug headers for cache analysis
function addCacheDebugHeaders() {
  return (req: Request, res: Response, next: NextFunction) => {
    const start = Date.now();

    res.on('finish', () => {
      // Log cache-related headers
      console.log({
        url: req.url,
        cacheControl: res.getHeader('Cache-Control'),
        etag: res.getHeader('ETag'),
        lastModified: res.getHeader('Last-Modified'),
        vary: res.getHeader('Vary'),
        responseTime: Date.now() - start,
      });
    });

    next();
  };
}

// Check cache status from CDN headers
function parseCacheStatus(headers: Headers): {
  hit: boolean;
  age: number;
  ttl?: number;
} {
  return {
    hit: headers.get('CF-Cache-Status') === 'HIT' ||
         headers.get('X-Cache') === 'HIT',
    age: parseInt(headers.get('Age') || '0', 10),
    ttl: parseInt(headers.get('X-Cache-TTL') || '', 10) || undefined,
  };
}
```

## Best Practices

1. **Use s-maxage** - Separate browser and CDN cache durations
2. **Implement cache tags** - Enable granular invalidation
3. **Normalize query strings** - Consistent cache keys
4. **Be careful with Vary** - Too many headers = no caching
5. **Use stale-while-revalidate** - Better performance + freshness
6. **Monitor cache hit ratio** - Aim for >90% for static content
7. **Plan invalidation strategy** - How will you purge when content changes?
