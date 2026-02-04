---
name: cors
description: Cross-Origin Resource Sharing configuration
category: security/api-security
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CORS Configuration

## Overview

Cross-Origin Resource Sharing (CORS) is a security mechanism that
allows or restricts cross-origin requests from browsers.

## CORS Flow

```
┌─────────────────────────────────────────────────────────────┐
│                Simple Request                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Browser (https://app.com)     Server (https://api.com)     │
│           │                              │                  │
│           │ GET /data                    │                  │
│           │ Origin: https://app.com      │                  │
│           │ ─────────────────────────────>│                 │
│           │                              │                  │
│           │ Access-Control-Allow-Origin: https://app.com    │
│           │ <─────────────────────────────│                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                Preflight Request                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Browser (https://app.com)     Server (https://api.com)     │
│           │                              │                  │
│           │ OPTIONS /data                │                  │
│           │ Origin: https://app.com      │                  │
│           │ Access-Control-Request-Method: POST             │
│           │ Access-Control-Request-Headers: Content-Type    │
│           │ ─────────────────────────────>│                 │
│           │                              │                  │
│           │ Access-Control-Allow-Origin: https://app.com    │
│           │ Access-Control-Allow-Methods: POST              │
│           │ Access-Control-Allow-Headers: Content-Type      │
│           │ Access-Control-Max-Age: 86400                   │
│           │ <─────────────────────────────│                 │
│           │                              │                  │
│           │ POST /data (actual request)  │                  │
│           │ ─────────────────────────────>│                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Basic Configuration

```typescript
// middleware/cors.middleware.ts
import cors from 'cors';

// Simple configuration
app.use(cors({
  origin: 'https://myapp.com',
}));

// Multiple origins
app.use(cors({
  origin: ['https://myapp.com', 'https://admin.myapp.com'],
}));

// Dynamic origin validation
app.use(cors({
  origin: (origin, callback) => {
    const allowedOrigins = [
      'https://myapp.com',
      'https://admin.myapp.com',
      /\.myapp\.com$/,  // Regex for subdomains
    ];

    // Allow requests with no origin (mobile apps, curl)
    if (!origin) {
      return callback(null, true);
    }

    const isAllowed = allowedOrigins.some(allowed => {
      if (allowed instanceof RegExp) {
        return allowed.test(origin);
      }
      return allowed === origin;
    });

    if (isAllowed) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
}));
```

## Advanced Configuration

```typescript
// config/cors.config.ts
interface CorsConfig {
  origin: string | string[] | RegExp | boolean;
  methods: string[];
  allowedHeaders: string[];
  exposedHeaders: string[];
  credentials: boolean;
  maxAge: number;
  preflightContinue: boolean;
  optionsSuccessStatus: number;
}

const corsConfig: CorsConfig = {
  // Allowed origins
  origin: process.env.NODE_ENV === 'production'
    ? ['https://myapp.com', 'https://admin.myapp.com']
    : true, // Allow all in development

  // Allowed HTTP methods
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],

  // Allowed request headers
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'X-API-Key',
    'X-CSRF-Token',
  ],

  // Headers exposed to the browser
  exposedHeaders: [
    'X-Total-Count',
    'X-Page-Count',
    'X-RateLimit-Limit',
    'X-RateLimit-Remaining',
    'X-RateLimit-Reset',
  ],

  // Allow cookies/auth headers
  credentials: true,

  // Cache preflight response (seconds)
  maxAge: 86400, // 24 hours

  // Pass preflight response to next handler
  preflightContinue: false,

  // Status code for successful OPTIONS
  optionsSuccessStatus: 204,
};

export default corsConfig;
```

## Environment-Based CORS

```typescript
// middleware/cors.middleware.ts
function getCorsOrigins(): string[] | boolean {
  const env = process.env.NODE_ENV;

  switch (env) {
    case 'production':
      return [
        'https://myapp.com',
        'https://www.myapp.com',
        'https://admin.myapp.com',
      ];

    case 'staging':
      return [
        'https://staging.myapp.com',
        'https://staging-admin.myapp.com',
      ];

    case 'development':
      return [
        'http://localhost:3000',
        'http://localhost:3001',
        'http://127.0.0.1:3000',
      ];

    default:
      return false; // Deny all
  }
}

app.use(cors({
  origin: getCorsOrigins(),
  credentials: true,
}));
```

## Per-Route CORS

```typescript
// Different CORS for different routes
const publicCors = cors({
  origin: '*',
  methods: ['GET'],
  maxAge: 86400,
});

const privateCors = cors({
  origin: ['https://myapp.com'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
});

const webhookCors = cors({
  origin: [
    'https://api.stripe.com',
    'https://api.github.com',
  ],
  methods: ['POST'],
});

// Apply per route
app.use('/api/public', publicCors);
app.use('/api/v1', privateCors);
app.use('/webhooks', webhookCors);

// Or per endpoint
router.get('/public/status', publicCors, getStatus);
router.post('/api/users', privateCors, createUser);
```

## Manual CORS Implementation

```typescript
// For more control, implement manually
export function corsMiddleware(options: CorsOptions) {
  return (req: Request, res: Response, next: NextFunction) => {
    const origin = req.headers.origin;

    // Check if origin is allowed
    const isAllowed = isOriginAllowed(origin, options.allowedOrigins);

    if (isAllowed) {
      res.setHeader('Access-Control-Allow-Origin', origin || '*');
    }

    // Always set Vary header for caching
    res.setHeader('Vary', 'Origin');

    if (options.credentials) {
      res.setHeader('Access-Control-Allow-Credentials', 'true');
    }

    if (options.exposedHeaders?.length) {
      res.setHeader(
        'Access-Control-Expose-Headers',
        options.exposedHeaders.join(', ')
      );
    }

    // Handle preflight
    if (req.method === 'OPTIONS') {
      res.setHeader(
        'Access-Control-Allow-Methods',
        options.methods?.join(', ') || 'GET, POST, PUT, DELETE'
      );

      res.setHeader(
        'Access-Control-Allow-Headers',
        options.allowedHeaders?.join(', ') || 'Content-Type, Authorization'
      );

      if (options.maxAge) {
        res.setHeader('Access-Control-Max-Age', options.maxAge.toString());
      }

      return res.status(204).end();
    }

    next();
  };
}

function isOriginAllowed(
  origin: string | undefined,
  allowedOrigins: (string | RegExp)[] | boolean
): boolean {
  if (allowedOrigins === true) return true;
  if (allowedOrigins === false) return false;
  if (!origin) return false;

  return allowedOrigins.some(allowed => {
    if (allowed instanceof RegExp) {
      return allowed.test(origin);
    }
    return allowed === origin;
  });
}
```

## Credentials and Cookies

```typescript
// When using credentials: true
// Origin CANNOT be '*', must be specific

const corsWithCredentials = cors({
  origin: (origin, callback) => {
    // Must validate and return specific origin
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, origin || true);
    } else {
      callback(new Error('Not allowed'));
    }
  },
  credentials: true,
});

// Client-side fetch with credentials
fetch('https://api.myapp.com/data', {
  credentials: 'include', // Send cookies
  headers: {
    'Content-Type': 'application/json',
  },
});
```

## Security Considerations

```typescript
// ❌ DANGEROUS: Allow all origins with credentials
app.use(cors({
  origin: '*',
  credentials: true, // This is blocked by browsers anyway
}));

// ❌ DANGEROUS: Reflect origin without validation
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', req.headers.origin);
  // Allows any origin!
});

// ✅ SAFE: Validate against whitelist
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || whitelist.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Blocked by CORS'));
    }
  },
}));

// ✅ SAFE: Strict production configuration
if (process.env.NODE_ENV === 'production') {
  app.use(cors({
    origin: ['https://myapp.com'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization'],
  }));
}
```

## CORS Error Handling

```typescript
// Handle CORS errors gracefully
app.use(cors({
  origin: (origin, callback) => {
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error(`Origin ${origin} not allowed by CORS`));
    }
  },
}));

// Error handler for CORS
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err.message.includes('CORS')) {
    return res.status(403).json({
      error: 'CORS Error',
      message: 'This origin is not allowed to access this resource',
    });
  }
  next(err);
});
```

## Testing CORS

```bash
# Test preflight request
curl -X OPTIONS https://api.myapp.com/data \
  -H "Origin: https://myapp.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Test actual request
curl -X GET https://api.myapp.com/data \
  -H "Origin: https://myapp.com" \
  -v
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Whitelist origins | Never use `*` with credentials |
| Validate origins | Don't reflect Origin header blindly |
| Limit methods | Only allow necessary HTTP methods |
| Set max-age | Cache preflight responses |
| Environment-specific | Different configs for dev/prod |
| Monitor violations | Log rejected CORS requests |
