# API Security

Input validation, rate limiting, CORS, API keys, and secure API design patterns.

## Table of Contents

1. [Input Validation](#input-validation)
2. [Rate Limiting](#rate-limiting)
3. [CORS Configuration](#cors-configuration)
4. [API Authentication](#api-authentication)
5. [Request Security](#request-security)

---

## Input Validation

### Zod Schema Validation

```typescript
import { z } from 'zod';

// User registration schema
const createUserSchema = z.object({
  email: z.string()
    .email('Invalid email format')
    .max(255, 'Email too long')
    .toLowerCase()
    .trim(),

  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password too long')
    .regex(/[A-Z]/, 'Must contain uppercase letter')
    .regex(/[a-z]/, 'Must contain lowercase letter')
    .regex(/[0-9]/, 'Must contain number')
    .regex(/[^A-Za-z0-9]/, 'Must contain special character'),

  name: z.string()
    .min(1, 'Name is required')
    .max(100, 'Name too long')
    .trim(),

  age: z.number()
    .int('Age must be an integer')
    .min(13, 'Must be at least 13 years old')
    .max(120, 'Invalid age')
    .optional(),

  role: z.enum(['user', 'admin', 'moderator'])
    .default('user'),
});

type CreateUserInput = z.infer<typeof createUserSchema>;

// Validation middleware
function validate<T>(schema: z.Schema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.body = schema.parse(req.body);
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          error: 'Validation failed',
          details: error.errors.map(e => ({
            field: e.path.join('.'),
            message: e.message,
          })),
        });
      }
      next(error);
    }
  };
}

// Usage
app.post('/users', validate(createUserSchema), createUser);
```

### Query Parameter Validation

```typescript
const paginationSchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  limit: z.coerce.number().int().min(1).max(100).default(20),
  sortBy: z.enum(['createdAt', 'name', 'email']).default('createdAt'),
  sortOrder: z.enum(['asc', 'desc']).default('desc'),
});

const searchSchema = z.object({
  q: z.string().min(1).max(100).optional(),
  status: z.enum(['active', 'inactive', 'pending']).optional(),
  dateFrom: z.coerce.date().optional(),
  dateTo: z.coerce.date().optional(),
}).refine(
  data => !data.dateFrom || !data.dateTo || data.dateFrom <= data.dateTo,
  { message: 'dateFrom must be before dateTo' }
);

function validateQuery<T>(schema: z.Schema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      req.query = schema.parse(req.query) as any;
      next();
    } catch (error) {
      if (error instanceof z.ZodError) {
        return res.status(400).json({
          error: 'Invalid query parameters',
          details: error.errors,
        });
      }
      next(error);
    }
  };
}
```

### File Upload Validation

```typescript
import multer from 'multer';
import path from 'path';

const ALLOWED_MIME_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'application/pdf',
];

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: MAX_FILE_SIZE,
    files: 5,
  },
  fileFilter: (req, file, cb) => {
    // Check MIME type
    if (!ALLOWED_MIME_TYPES.includes(file.mimetype)) {
      return cb(new Error('Invalid file type'));
    }

    // Check extension
    const ext = path.extname(file.originalname).toLowerCase();
    const allowedExts = ['.jpg', '.jpeg', '.png', '.gif', '.pdf'];
    if (!allowedExts.includes(ext)) {
      return cb(new Error('Invalid file extension'));
    }

    cb(null, true);
  },
});

// Validate file content matches extension
import fileType from 'file-type';

async function validateFileContent(buffer: Buffer, filename: string): Promise<boolean> {
  const detected = await fileType.fromBuffer(buffer);
  const ext = path.extname(filename).toLowerCase().slice(1);

  if (!detected) {
    return false; // Can't detect type
  }

  // Verify detected type matches extension
  const mimeToExt: Record<string, string[]> = {
    'image/jpeg': ['jpg', 'jpeg'],
    'image/png': ['png'],
    'image/gif': ['gif'],
    'application/pdf': ['pdf'],
  };

  return mimeToExt[detected.mime]?.includes(ext) ?? false;
}
```

### Sanitization

```typescript
import sanitizeHtml from 'sanitize-html';
import validator from 'validator';

// HTML sanitization for rich text
function sanitizeRichText(html: string): string {
  return sanitizeHtml(html, {
    allowedTags: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li'],
    allowedAttributes: {
      a: ['href', 'title'],
    },
    allowedSchemes: ['http', 'https', 'mailto'],
  });
}

// String sanitization
function sanitizeString(input: string): string {
  return validator.escape(validator.trim(input));
}

// URL sanitization
function sanitizeUrl(url: string): string | null {
  if (!validator.isURL(url, {
    protocols: ['http', 'https'],
    require_protocol: true,
  })) {
    return null;
  }
  return url;
}

// Prevent NoSQL injection
function sanitizeMongoQuery(input: any): any {
  if (typeof input !== 'object' || input === null) {
    return input;
  }

  const sanitized: any = {};
  for (const [key, value] of Object.entries(input)) {
    // Block MongoDB operators
    if (key.startsWith('$')) {
      continue;
    }
    sanitized[key] = sanitizeMongoQuery(value);
  }
  return sanitized;
}
```

---

## Rate Limiting

### Token Bucket Algorithm

```typescript
import { RateLimiterRedis } from 'rate-limiter-flexible';
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

// Different limits for different endpoints
const rateLimiters = {
  // General API: 100 requests per minute
  api: new RateLimiterRedis({
    storeClient: redis,
    keyPrefix: 'rl:api',
    points: 100,
    duration: 60,
  }),

  // Auth endpoints: 5 attempts per 15 minutes
  auth: new RateLimiterRedis({
    storeClient: redis,
    keyPrefix: 'rl:auth',
    points: 5,
    duration: 15 * 60,
    blockDuration: 15 * 60, // Block for 15 minutes after exceeding
  }),

  // Expensive operations: 10 per hour
  expensive: new RateLimiterRedis({
    storeClient: redis,
    keyPrefix: 'rl:expensive',
    points: 10,
    duration: 60 * 60,
  }),
};

// Rate limiting middleware
function rateLimit(limiterName: keyof typeof rateLimiters) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const limiter = rateLimiters[limiterName];
    const key = req.user?.id || req.ip;

    try {
      const result = await limiter.consume(key);

      // Set rate limit headers
      res.set({
        'X-RateLimit-Limit': String(limiter.points),
        'X-RateLimit-Remaining': String(result.remainingPoints),
        'X-RateLimit-Reset': String(Math.ceil(result.msBeforeNext / 1000)),
      });

      next();
    } catch (error) {
      if (error instanceof Error && 'msBeforeNext' in error) {
        const retryAfter = Math.ceil((error as any).msBeforeNext / 1000);
        res.set({
          'Retry-After': String(retryAfter),
          'X-RateLimit-Limit': String(limiter.points),
          'X-RateLimit-Remaining': '0',
        });
        return res.status(429).json({
          error: 'Too many requests',
          retryAfter,
        });
      }
      next(error);
    }
  };
}

// Usage
app.post('/login', rateLimit('auth'), loginHandler);
app.get('/api/*', rateLimit('api'), apiHandler);
app.post('/reports/generate', rateLimit('expensive'), generateReport);
```

### Sliding Window Rate Limiting

```typescript
class SlidingWindowRateLimiter {
  constructor(
    private redis: Redis,
    private windowSize: number, // seconds
    private maxRequests: number
  ) {}

  async isAllowed(key: string): Promise<{
    allowed: boolean;
    remaining: number;
    resetAt: number;
  }> {
    const now = Date.now();
    const windowStart = now - this.windowSize * 1000;
    const redisKey = `ratelimit:${key}`;

    const multi = this.redis.multi();

    // Remove old entries
    multi.zremrangebyscore(redisKey, 0, windowStart);

    // Add current request
    multi.zadd(redisKey, now, `${now}-${Math.random()}`);

    // Count requests in window
    multi.zcard(redisKey);

    // Set expiry
    multi.expire(redisKey, this.windowSize);

    const results = await multi.exec();
    const count = results?.[2]?.[1] as number;

    return {
      allowed: count <= this.maxRequests,
      remaining: Math.max(0, this.maxRequests - count),
      resetAt: Math.ceil((now + this.windowSize * 1000) / 1000),
    };
  }
}
```

### User-Tier Rate Limiting

```typescript
interface RateLimitConfig {
  points: number;
  duration: number;
}

const tierLimits: Record<string, RateLimitConfig> = {
  free: { points: 100, duration: 60 * 60 },      // 100/hour
  basic: { points: 1000, duration: 60 * 60 },    // 1000/hour
  pro: { points: 10000, duration: 60 * 60 },     // 10000/hour
  enterprise: { points: 100000, duration: 60 * 60 }, // 100000/hour
};

async function tieredRateLimit(req: Request, res: Response, next: NextFunction) {
  const user = req.user;
  const tier = user?.tier || 'free';
  const config = tierLimits[tier];

  const limiter = new RateLimiterRedis({
    storeClient: redis,
    keyPrefix: `rl:tier:${tier}`,
    points: config.points,
    duration: config.duration,
  });

  try {
    await limiter.consume(user?.id || req.ip);
    next();
  } catch (error) {
    res.status(429).json({
      error: 'Rate limit exceeded',
      upgradeUrl: '/pricing',
    });
  }
}
```

---

## CORS Configuration

### Express CORS Setup

```typescript
import cors from 'cors';

// Development - permissive
const devCorsOptions: cors.CorsOptions = {
  origin: true, // Allow any origin
  credentials: true,
};

// Production - restrictive
const prodCorsOptions: cors.CorsOptions = {
  origin: (origin, callback) => {
    const allowedOrigins = [
      'https://myapp.com',
      'https://admin.myapp.com',
      'https://app.myapp.com',
    ];

    // Allow requests with no origin (mobile apps, Postman)
    if (!origin) {
      return callback(null, true);
    }

    if (allowedOrigins.includes(origin)) {
      return callback(null, true);
    }

    callback(new Error('Not allowed by CORS'));
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
  allowedHeaders: [
    'Content-Type',
    'Authorization',
    'X-Requested-With',
    'X-CSRF-Token',
  ],
  exposedHeaders: [
    'X-RateLimit-Limit',
    'X-RateLimit-Remaining',
    'X-RateLimit-Reset',
  ],
  maxAge: 86400, // 24 hours preflight cache
};

const corsOptions = process.env.NODE_ENV === 'production'
  ? prodCorsOptions
  : devCorsOptions;

app.use(cors(corsOptions));
```

### Dynamic CORS for Multi-Tenant

```typescript
interface Tenant {
  id: string;
  allowedOrigins: string[];
}

async function dynamicCors(
  req: Request,
  callback: (err: Error | null, options?: cors.CorsOptions) => void
) {
  const origin = req.header('Origin');

  if (!origin) {
    return callback(null, { origin: false });
  }

  try {
    // Get tenant from subdomain or header
    const tenantId = extractTenantId(req);
    const tenant = await getTenant(tenantId);

    if (tenant?.allowedOrigins.includes(origin)) {
      callback(null, {
        origin: true,
        credentials: true,
      });
    } else {
      callback(null, { origin: false });
    }
  } catch (error) {
    callback(error as Error);
  }
}

app.use(cors(dynamicCors));
```

### Preflight Handling

```typescript
// Handle OPTIONS preflight requests
app.options('*', cors(corsOptions));

// Custom preflight for specific routes
app.options('/api/upload', (req, res) => {
  res.set({
    'Access-Control-Allow-Origin': req.header('Origin'),
    'Access-Control-Allow-Methods': 'POST',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Max-Age': '86400',
  });
  res.status(204).send();
});
```

---

## API Authentication

### API Key Authentication

```typescript
import crypto from 'crypto';

// Generate API key
function generateApiKey(): { key: string; hash: string } {
  const key = `sk_live_${crypto.randomBytes(24).toString('base64url')}`;
  const hash = crypto.createHash('sha256').update(key).digest('hex');
  return { key, hash };
}

// Store only the hash in database
interface ApiKeyRecord {
  id: string;
  name: string;
  keyHash: string;
  userId: string;
  permissions: string[];
  rateLimit: number;
  lastUsedAt: Date | null;
  createdAt: Date;
  expiresAt: Date | null;
}

// API key middleware
async function apiKeyAuth(req: Request, res: Response, next: NextFunction) {
  const apiKey = req.header('X-API-Key') || req.query.api_key as string;

  if (!apiKey) {
    return res.status(401).json({ error: 'API key required' });
  }

  // Validate format
  if (!apiKey.startsWith('sk_live_') && !apiKey.startsWith('sk_test_')) {
    return res.status(401).json({ error: 'Invalid API key format' });
  }

  const keyHash = crypto.createHash('sha256').update(apiKey).digest('hex');
  const keyRecord = await apiKeyRepository.findByHash(keyHash);

  if (!keyRecord) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  if (keyRecord.expiresAt && keyRecord.expiresAt < new Date()) {
    return res.status(401).json({ error: 'API key expired' });
  }

  // Update last used
  await apiKeyRepository.updateLastUsed(keyRecord.id);

  req.apiKey = keyRecord;
  req.user = await userRepository.findById(keyRecord.userId);
  next();
}
```

### JWT + API Key Hybrid

```typescript
// Support both JWT (web) and API key (programmatic)
async function hybridAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.header('Authorization');
  const apiKey = req.header('X-API-Key');

  if (authHeader?.startsWith('Bearer ')) {
    // JWT authentication
    try {
      const token = authHeader.slice(7);
      const payload = tokenService.verifyAccessToken(token);
      req.user = await userRepository.findById(payload.sub);
      req.authMethod = 'jwt';
      return next();
    } catch (error) {
      return res.status(401).json({ error: 'Invalid token' });
    }
  }

  if (apiKey) {
    // API key authentication
    return apiKeyAuth(req, res, next);
  }

  res.status(401).json({ error: 'Authentication required' });
}
```

### OAuth2 Client Credentials

```typescript
// For service-to-service authentication
const clientCredentialsSchema = z.object({
  grant_type: z.literal('client_credentials'),
  client_id: z.string(),
  client_secret: z.string(),
  scope: z.string().optional(),
});

app.post('/oauth/token', async (req, res) => {
  try {
    const { client_id, client_secret, scope } = clientCredentialsSchema.parse(req.body);

    const client = await oauthClientRepository.findById(client_id);

    if (!client || !await bcrypt.compare(client_secret, client.secretHash)) {
      return res.status(401).json({
        error: 'invalid_client',
        error_description: 'Invalid client credentials',
      });
    }

    // Validate requested scopes
    const requestedScopes = scope?.split(' ') || [];
    const allowedScopes = requestedScopes.filter(s => client.allowedScopes.includes(s));

    const accessToken = jwt.sign(
      {
        sub: client.id,
        type: 'client',
        scopes: allowedScopes,
      },
      process.env.JWT_SECRET!,
      { expiresIn: '1h' }
    );

    res.json({
      access_token: accessToken,
      token_type: 'Bearer',
      expires_in: 3600,
      scope: allowedScopes.join(' '),
    });
  } catch (error) {
    res.status(400).json({
      error: 'invalid_request',
      error_description: 'Invalid request format',
    });
  }
});
```

---

## Request Security

### Request Size Limits

```typescript
import express from 'express';

// Global limits
app.use(express.json({ limit: '1mb' }));
app.use(express.urlencoded({ limit: '1mb', extended: true }));

// Route-specific limits
app.post('/upload',
  express.raw({ limit: '50mb', type: 'application/octet-stream' }),
  uploadHandler
);

// Custom size limit middleware
function limitRequestSize(maxSize: number) {
  return (req: Request, res: Response, next: NextFunction) => {
    let size = 0;

    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > maxSize) {
        req.destroy();
        res.status(413).json({ error: 'Request entity too large' });
      }
    });

    next();
  };
}
```

### Request Timeout

```typescript
import timeout from 'connect-timeout';

// Global timeout
app.use(timeout('30s'));

// Handle timeout
app.use((req, res, next) => {
  if (!req.timedout) next();
});

// Route-specific timeout
app.post('/long-operation',
  timeout('5m'),
  longOperationHandler,
  (req, res, next) => {
    if (!req.timedout) next();
  }
);

// Async operation with timeout
async function withTimeout<T>(
  promise: Promise<T>,
  ms: number,
  message = 'Operation timed out'
): Promise<T> {
  const timeout = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error(message)), ms);
  });

  return Promise.race([promise, timeout]);
}
```

### Request ID Tracking

```typescript
import { v4 as uuidv4 } from 'uuid';

// Add request ID
app.use((req, res, next) => {
  req.id = req.header('X-Request-ID') || uuidv4();
  res.set('X-Request-ID', req.id);
  next();
});

// Include in logs
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    logger.info({
      requestId: req.id,
      method: req.method,
      url: req.url,
      status: res.statusCode,
      duration: Date.now() - start,
      userAgent: req.header('User-Agent'),
      ip: req.ip,
    });
  });

  next();
});

// Propagate to downstream services
async function callService(endpoint: string, data: any, requestId: string) {
  return fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Request-ID': requestId,
    },
    body: JSON.stringify(data),
  });
}
```

### IP Filtering

```typescript
import ipRangeCheck from 'ip-range-check';

const allowedIPs = [
  '10.0.0.0/8',      // Private network
  '192.168.0.0/16',  // Private network
  '203.0.113.0/24',  // Specific allowed range
];

const blockedIPs = [
  '1.2.3.4',         // Known bad actor
  '5.6.7.0/24',      // Blocked range
];

function ipFilter(req: Request, res: Response, next: NextFunction) {
  const clientIP = req.ip || req.socket.remoteAddress;

  if (!clientIP) {
    return res.status(403).json({ error: 'Unable to determine client IP' });
  }

  // Check blocklist first
  if (ipRangeCheck(clientIP, blockedIPs)) {
    return res.status(403).json({ error: 'Access denied' });
  }

  // For admin routes, check allowlist
  if (req.path.startsWith('/admin')) {
    if (!ipRangeCheck(clientIP, allowedIPs)) {
      return res.status(403).json({ error: 'Access denied from this IP' });
    }
  }

  next();
}

app.use(ipFilter);
```

---

## Best Practices

| Category | Do | Don't |
|----------|-----|-------|
| Validation | Validate at API boundary | Trust client input |
| Rate Limiting | Per-user and per-IP limits | Single global limit |
| CORS | Whitelist specific origins | Allow all origins in prod |
| API Keys | Hash before storage | Store plain text |
| Timeouts | Set reasonable limits | Allow infinite execution |
| Logging | Include request IDs | Log sensitive data |
