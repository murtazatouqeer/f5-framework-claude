---
name: response-compression
description: HTTP response compression techniques
category: performance/api
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Response Compression

## Overview

Compression reduces the size of HTTP responses, improving transfer speed
and reducing bandwidth costs. Typical compression ratios are 60-90% for text-based content.

## Compression Algorithms

| Algorithm | Compression | Speed | Browser Support |
|-----------|-------------|-------|-----------------|
| gzip | Good | Fast | Universal |
| Brotli (br) | Better | Slower | Modern browsers |
| deflate | Good | Fast | Universal |
| zstd | Best | Fast | Limited |

## Express Compression

### Basic Setup

```typescript
import compression from 'compression';
import express from 'express';

const app = express();

// Enable compression for all responses
app.use(compression());
```

### Advanced Configuration

```typescript
import compression from 'compression';

app.use(compression({
  // Minimum size to compress (bytes)
  threshold: 1024, // Don't compress below 1KB

  // Compression level (1-9, higher = better compression, slower)
  level: 6, // Default, good balance

  // Memory level (1-9, higher = more memory, better compression)
  memLevel: 8,

  // Filter function - which responses to compress
  filter: (req, res) => {
    // Don't compress if client doesn't accept
    if (req.headers['x-no-compression']) {
      return false;
    }

    // Use default filter
    return compression.filter(req, res);
  },
}));
```

### Brotli Support

```typescript
import compression from 'compression';
import zlib from 'zlib';

app.use(compression({
  // Enable Brotli when supported
  brotli: {
    enabled: true,
    params: {
      [zlib.constants.BROTLI_PARAM_QUALITY]: 4, // 1-11, higher = better
    },
  },
}));

// Or use dedicated Brotli middleware
import shrinkRay from 'shrink-ray-current';

app.use(shrinkRay({
  brotli: { quality: 4 },
  zlib: { level: 6 },
  cache: () => true, // Cache compressed responses
  cacheSize: 128 * 1024 * 1024, // 128MB cache
}));
```

## NestJS Compression

```typescript
// main.ts
import { NestFactory } from '@nestjs/core';
import compression from 'compression';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.use(compression({
    threshold: 1024,
    level: 6,
  }));

  await app.listen(3000);
}
```

## Fastify Compression

```typescript
import Fastify from 'fastify';
import compress from '@fastify/compress';

const fastify = Fastify();

await fastify.register(compress, {
  global: true,
  threshold: 1024,
  encodings: ['gzip', 'br', 'deflate'],
  brotliOptions: { quality: 4 },
  zlibOptions: { level: 6 },
});
```

## Selective Compression

### By Content Type

```typescript
import compression from 'compression';

const compressibleTypes = [
  'text/html',
  'text/css',
  'text/javascript',
  'text/xml',
  'text/plain',
  'application/json',
  'application/javascript',
  'application/xml',
  'application/x-www-form-urlencoded',
];

app.use(compression({
  filter: (req, res) => {
    const contentType = res.getHeader('Content-Type');
    if (!contentType) return false;

    const type = contentType.toString().split(';')[0];
    return compressibleTypes.includes(type);
  },
}));
```

### By Route

```typescript
import compression from 'compression';

// Create compression middleware instance
const compress = compression({ threshold: 0 });

// Apply selectively
app.get('/api/large-data', compress, (req, res) => {
  res.json(largeData);
});

// Skip compression for small responses
app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' });
});

// Or use route-specific settings
app.use('/api', compression({ level: 9 })); // High compression for API
app.use('/static', compression({ level: 1 })); // Fast compression for static
```

### Exclude Already Compressed

```typescript
// Don't double-compress
app.use(compression({
  filter: (req, res) => {
    const contentType = res.getHeader('Content-Type')?.toString() || '';

    // Already compressed formats
    const skipTypes = [
      'image/jpeg',
      'image/png',
      'image/gif',
      'image/webp',
      'video/',
      'audio/',
      'application/zip',
      'application/gzip',
      'application/pdf',
    ];

    if (skipTypes.some(type => contentType.startsWith(type))) {
      return false;
    }

    return compression.filter(req, res);
  },
}));
```

## Pre-Compression

### Static File Pre-Compression

```typescript
// Generate .gz and .br files during build
import { gzip, brotliCompress } from 'zlib';
import { promisify } from 'util';
import fs from 'fs/promises';
import glob from 'glob';

const gzipAsync = promisify(gzip);
const brotliAsync = promisify(brotliCompress);

async function preCompress(pattern: string): Promise<void> {
  const files = glob.sync(pattern);

  for (const file of files) {
    const content = await fs.readFile(file);

    // Create gzip version
    const gzipped = await gzipAsync(content, { level: 9 });
    await fs.writeFile(`${file}.gz`, gzipped);

    // Create brotli version
    const brotli = await brotliAsync(content);
    await fs.writeFile(`${file}.br`, brotli);

    console.log(`Compressed: ${file}`);
  }
}

// Usage: preCompress('dist/**/*.{js,css,html,json}')
```

### Serve Pre-Compressed Files

```typescript
import express from 'express';
import expressStaticGzip from 'express-static-gzip';

app.use('/static', expressStaticGzip('dist', {
  enableBrotli: true,
  orderPreference: ['br', 'gzip'],
  serveStatic: {
    maxAge: '1y',
    immutable: true,
  },
}));

// Manual implementation
app.use('/static', (req, res, next) => {
  const acceptEncoding = req.get('Accept-Encoding') || '';

  if (acceptEncoding.includes('br')) {
    const brPath = `dist${req.path}.br`;
    if (fs.existsSync(brPath)) {
      res.set('Content-Encoding', 'br');
      return res.sendFile(brPath, { root: process.cwd() });
    }
  }

  if (acceptEncoding.includes('gzip')) {
    const gzPath = `dist${req.path}.gz`;
    if (fs.existsSync(gzPath)) {
      res.set('Content-Encoding', 'gzip');
      return res.sendFile(gzPath, { root: process.cwd() });
    }
  }

  next();
});
```

## Streaming Compression

```typescript
import { createGzip, createBrotliCompress } from 'zlib';

// Compress large responses as they stream
app.get('/api/export', async (req, res) => {
  const acceptEncoding = req.get('Accept-Encoding') || '';

  let compressor: NodeJS.ReadWriteStream | null = null;
  let encoding: string | null = null;

  if (acceptEncoding.includes('br')) {
    compressor = createBrotliCompress();
    encoding = 'br';
  } else if (acceptEncoding.includes('gzip')) {
    compressor = createGzip();
    encoding = 'gzip';
  }

  res.set('Content-Type', 'application/json');
  if (encoding) {
    res.set('Content-Encoding', encoding);
  }

  // Create data stream
  const dataStream = createLargeDataStream();

  if (compressor) {
    dataStream.pipe(compressor).pipe(res);
  } else {
    dataStream.pipe(res);
  }
});
```

## JSON-Specific Optimization

### Minify JSON

```typescript
// Remove whitespace from JSON
app.use('/api', (req, res, next) => {
  const originalJson = res.json.bind(res);

  res.json = function(data: any): Response {
    // JSON.stringify without pretty printing
    const json = JSON.stringify(data);
    res.set('Content-Type', 'application/json');
    return res.send(json);
  };

  next();
});
```

### Field Selection

```typescript
// Allow clients to request only needed fields
app.get('/api/users', async (req, res) => {
  const fields = (req.query.fields as string)?.split(',');

  const users = await prisma.user.findMany({
    select: fields ? Object.fromEntries(fields.map(f => [f, true])) : undefined,
  });

  res.json(users);
});

// Usage: GET /api/users?fields=id,name,email
// Returns: [{"id": "1", "name": "John", "email": "john@example.com"}]
// Instead of: [{"id": "1", "name": "John", "email": "...", "createdAt": "...", ...}]
```

## Monitoring Compression

```typescript
// Log compression stats
app.use((req, res, next) => {
  const originalSend = res.send.bind(res);
  let originalSize = 0;

  res.send = function(body: any): Response {
    originalSize = Buffer.byteLength(body);
    return originalSend(body);
  };

  res.on('finish', () => {
    const contentLength = parseInt(res.get('Content-Length') || '0', 10);
    const encoding = res.get('Content-Encoding');

    if (encoding && originalSize > 0) {
      const ratio = ((1 - contentLength / originalSize) * 100).toFixed(1);
      console.log(`Compression: ${encoding}, ${originalSize} → ${contentLength} (${ratio}% reduction)`);
    }
  });

  next();
});
```

## Best Practices

1. **Set appropriate threshold** - Don't compress tiny responses (< 1KB)
2. **Use Brotli when possible** - Better compression than gzip
3. **Pre-compress static files** - Avoid runtime compression overhead
4. **Skip already compressed** - Images, videos, archives
5. **Consider CPU vs bandwidth** - High compression uses more CPU
6. **Use streaming for large responses** - Don't buffer entire response
7. **Monitor compression ratios** - Ensure compression is effective
8. **Test with different content types** - Compression varies by content
