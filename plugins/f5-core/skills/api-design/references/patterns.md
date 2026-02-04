# API Patterns Reference

## Authentication

### API Keys

```typescript
// Generation
import crypto from 'crypto';

function generateApiKey(): { key: string; hash: string } {
  const key = `sk_live_${crypto.randomBytes(24).toString('base64url')}`;
  const hash = crypto.createHash('sha256').update(key).digest('hex');
  return { key, hash };
}

// Storage - hash only, never store raw key
interface ApiKeyRecord {
  id: string;
  key_hash: string;
  prefix: string;        // "sk_live_abc" for identification
  name: string;
  scopes: string[];
  created_at: Date;
  last_used_at: Date;
  expires_at: Date | null;
}

// Validation middleware
async function validateApiKey(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing API key' });
  }

  const key = authHeader.slice(7);
  const hash = crypto.createHash('sha256').update(key).digest('hex');

  const record = await db.apiKeys.findByHash(hash);
  if (!record || (record.expires_at && record.expires_at < new Date())) {
    return res.status(401).json({ error: 'Invalid API key' });
  }

  req.apiKey = record;
  next();
}
```

### JWT Authentication

```typescript
import jwt from 'jsonwebtoken';

interface TokenPayload {
  sub: string;      // Subject (user ID)
  iat: number;      // Issued at
  exp: number;      // Expiration
  jti: string;      // Token ID
  type: 'access' | 'refresh';
}

// Token generation
function generateTokens(userId: string) {
  const accessToken = jwt.sign(
    { sub: userId, type: 'access', jti: crypto.randomUUID() },
    process.env.JWT_SECRET!,
    { expiresIn: '15m' }
  );

  const refreshToken = jwt.sign(
    { sub: userId, type: 'refresh', jti: crypto.randomUUID() },
    process.env.JWT_REFRESH_SECRET!,
    { expiresIn: '7d' }
  );

  return { accessToken, refreshToken };
}

// Middleware
function authenticateToken(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;
  const token = authHeader?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: { code: 'MISSING_TOKEN' } });
  }

  try {
    const payload = jwt.verify(token, process.env.JWT_SECRET!) as TokenPayload;
    if (payload.type !== 'access') {
      return res.status(401).json({ error: { code: 'INVALID_TOKEN_TYPE' } });
    }
    req.user = { id: payload.sub };
    next();
  } catch (error) {
    if (error instanceof jwt.TokenExpiredError) {
      return res.status(401).json({ error: { code: 'TOKEN_EXPIRED' } });
    }
    return res.status(401).json({ error: { code: 'INVALID_TOKEN' } });
  }
}
```

### OAuth 2.0 with PKCE

```typescript
// PKCE flow for public clients
import crypto from 'crypto';

// Client-side: Generate challenge
function generatePKCE() {
  const verifier = crypto.randomBytes(32).toString('base64url');
  const challenge = crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');
  return { verifier, challenge };
}

// Authorization request
const authUrl = new URL('https://auth.example.com/authorize');
authUrl.searchParams.set('response_type', 'code');
authUrl.searchParams.set('client_id', CLIENT_ID);
authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
authUrl.searchParams.set('scope', 'read write');
authUrl.searchParams.set('state', crypto.randomUUID());
authUrl.searchParams.set('code_challenge', challenge);
authUrl.searchParams.set('code_challenge_method', 'S256');

// Token exchange
async function exchangeCode(code: string, verifier: string) {
  const response = await fetch('https://auth.example.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'authorization_code',
      code,
      redirect_uri: REDIRECT_URI,
      client_id: CLIENT_ID,
      code_verifier: verifier,
    }),
  });
  return response.json();
}
```

### Webhook Signatures

```typescript
function signWebhook(payload: string, secret: string): string {
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${payload}`)
    .digest('hex');
  return `t=${timestamp},v1=${signature}`;
}

function verifyWebhook(
  payload: string,
  signature: string,
  secret: string,
  tolerance: number = 300
): boolean {
  const parts = Object.fromEntries(
    signature.split(',').map(p => p.split('='))
  );

  const timestamp = parseInt(parts.t);
  if (Math.abs(Date.now() / 1000 - timestamp) > tolerance) {
    return false; // Replay attack prevention
  }

  const expected = crypto
    .createHmac('sha256', secret)
    .update(`${timestamp}.${payload}`)
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(parts.v1),
    Buffer.from(expected)
  );
}
```

## Error Handling

### Standard Error Response (RFC 7807)

```typescript
interface ProblemDetails {
  type: string;        // URI reference for error type
  title: string;       // Short, human-readable summary
  status: number;      // HTTP status code
  detail?: string;     // Human-readable explanation
  instance?: string;   // URI reference for specific occurrence
  errors?: FieldError[];
}

interface FieldError {
  field: string;
  code: string;
  message: string;
}

// Example response
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "The request body contains invalid fields",
  "instance": "/users/123",
  "errors": [
    {
      "field": "email",
      "code": "INVALID_FORMAT",
      "message": "Must be a valid email address"
    }
  ]
}
```

### Error Classes

```typescript
abstract class ApiError extends Error {
  abstract readonly statusCode: number;
  abstract readonly code: string;
  readonly timestamp = new Date().toISOString();
  readonly requestId?: string;

  constructor(message: string, requestId?: string) {
    super(message);
    this.requestId = requestId;
  }

  toJSON(): ProblemDetails {
    return {
      type: `https://api.example.com/errors/${this.code.toLowerCase()}`,
      title: this.code.replace(/_/g, ' '),
      status: this.statusCode,
      detail: this.message,
    };
  }
}

class ValidationError extends ApiError {
  readonly statusCode = 422;
  readonly code = 'VALIDATION_ERROR';
  constructor(readonly errors: FieldError[]) {
    super('Validation failed');
  }
}

class NotFoundError extends ApiError {
  readonly statusCode = 404;
  readonly code = 'NOT_FOUND';
}

class UnauthorizedError extends ApiError {
  readonly statusCode = 401;
  readonly code = 'UNAUTHORIZED';
}

class ForbiddenError extends ApiError {
  readonly statusCode = 403;
  readonly code = 'FORBIDDEN';
}

class ConflictError extends ApiError {
  readonly statusCode = 409;
  readonly code = 'CONFLICT';
}

class RateLimitError extends ApiError {
  readonly statusCode = 429;
  readonly code = 'RATE_LIMIT_EXCEEDED';
  constructor(readonly retryAfter: number) {
    super(`Rate limit exceeded. Retry after ${retryAfter} seconds`);
  }
}
```

### Error Middleware

```typescript
function errorHandler(
  error: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  const requestId = req.headers['x-request-id'] as string;

  if (error instanceof ApiError) {
    return res.status(error.statusCode).json({
      ...error.toJSON(),
      instance: req.path,
      requestId,
    });
  }

  // Log unexpected errors
  console.error('Unexpected error:', {
    error: error.message,
    stack: error.stack,
    requestId,
    path: req.path,
    method: req.method,
  });

  // Don't expose internal details
  res.status(500).json({
    type: 'https://api.example.com/errors/internal',
    title: 'Internal Server Error',
    status: 500,
    detail: 'An unexpected error occurred',
    requestId,
  });
}
```

### Error Codes Taxonomy

```
AUTHENTICATION
├── AUTH_REQUIRED          401  Authentication needed
├── TOKEN_EXPIRED          401  Token has expired
├── TOKEN_INVALID          401  Token is malformed
└── TOKEN_REVOKED          401  Token has been revoked

AUTHORIZATION
├── FORBIDDEN              403  No permission for action
├── INSUFFICIENT_SCOPE     403  Token lacks required scope
└── RESOURCE_FORBIDDEN     403  No access to resource

VALIDATION
├── INVALID_REQUEST        400  Malformed request body
├── MISSING_FIELD          422  Required field missing
├── INVALID_FORMAT         422  Field format invalid
├── VALUE_OUT_OF_RANGE     422  Value exceeds limits
└── INVALID_REFERENCE      422  Referenced entity not found

RESOURCE
├── NOT_FOUND              404  Resource doesn't exist
├── ALREADY_EXISTS         409  Resource already exists
├── CONFLICT               409  State conflict
└── GONE                   410  Resource deleted

RATE_LIMITING
├── RATE_LIMIT_EXCEEDED    429  Too many requests
└── QUOTA_EXCEEDED         429  Usage quota exceeded

SERVER
├── INTERNAL_ERROR         500  Unexpected error
├── SERVICE_UNAVAILABLE    503  Temporary unavailability
└── GATEWAY_TIMEOUT        504  Upstream timeout
```

## Rate Limiting

### Algorithms Comparison

| Algorithm | Burst Handling | Memory | Accuracy | Complexity |
|-----------|---------------|--------|----------|------------|
| Fixed Window | Poor | Low | Low | Simple |
| Sliding Window Log | Good | High | High | Medium |
| Sliding Window Counter | Good | Medium | High | Medium |
| Token Bucket | Excellent | Medium | High | Medium |
| Leaky Bucket | Smoothed | Medium | High | Medium |

### Sliding Window Counter (Redis)

```typescript
class SlidingWindowRateLimiter {
  constructor(
    private redis: Redis,
    private windowMs: number,
    private maxRequests: number
  ) {}

  async isAllowed(key: string): Promise<{ allowed: boolean; remaining: number }> {
    const now = Date.now();
    const windowStart = now - this.windowMs;
    const redisKey = `ratelimit:${key}`;

    const pipeline = this.redis.pipeline();
    // Remove old entries
    pipeline.zremrangebyscore(redisKey, 0, windowStart);
    // Add current request
    pipeline.zadd(redisKey, now, `${now}-${Math.random()}`);
    // Count requests in window
    pipeline.zcard(redisKey);
    // Set expiry
    pipeline.expire(redisKey, Math.ceil(this.windowMs / 1000));

    const results = await pipeline.exec();
    const count = results![2][1] as number;

    return {
      allowed: count <= this.maxRequests,
      remaining: Math.max(0, this.maxRequests - count),
    };
  }
}
```

### Token Bucket (Redis)

```typescript
class TokenBucketRateLimiter {
  constructor(
    private redis: Redis,
    private bucketSize: number,     // Max tokens
    private refillRate: number,     // Tokens per second
  ) {}

  async consume(key: string, tokens: number = 1): Promise<{
    allowed: boolean;
    remaining: number;
    retryAfter?: number;
  }> {
    const now = Date.now();
    const redisKey = `bucket:${key}`;

    const script = `
      local bucket_size = tonumber(ARGV[1])
      local refill_rate = tonumber(ARGV[2])
      local now = tonumber(ARGV[3])
      local requested = tonumber(ARGV[4])

      local data = redis.call('HMGET', KEYS[1], 'tokens', 'last_refill')
      local tokens = tonumber(data[1]) or bucket_size
      local last_refill = tonumber(data[2]) or now

      -- Refill tokens
      local elapsed = (now - last_refill) / 1000
      tokens = math.min(bucket_size, tokens + elapsed * refill_rate)

      if tokens >= requested then
        tokens = tokens - requested
        redis.call('HMSET', KEYS[1], 'tokens', tokens, 'last_refill', now)
        redis.call('EXPIRE', KEYS[1], 3600)
        return {1, tokens}
      else
        local wait_time = (requested - tokens) / refill_rate
        return {0, tokens, wait_time}
      end
    `;

    const result = await this.redis.eval(
      script, 1, redisKey,
      this.bucketSize, this.refillRate, now, tokens
    ) as number[];

    return {
      allowed: result[0] === 1,
      remaining: Math.floor(result[1]),
      retryAfter: result[2] ? Math.ceil(result[2]) : undefined,
    };
  }
}
```

### Rate Limit Middleware

```typescript
function rateLimitMiddleware(limiter: RateLimiter) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const key = req.user?.id || req.ip;
    const result = await limiter.isAllowed(key);

    res.setHeader('X-RateLimit-Limit', limiter.maxRequests);
    res.setHeader('X-RateLimit-Remaining', result.remaining);
    res.setHeader('X-RateLimit-Reset', Math.ceil(Date.now() / 1000) + 60);

    if (!result.allowed) {
      res.setHeader('Retry-After', result.retryAfter || 60);
      return res.status(429).json({
        type: 'https://api.example.com/errors/rate-limit',
        title: 'Rate Limit Exceeded',
        status: 429,
        detail: `Rate limit exceeded. Try again in ${result.retryAfter} seconds`,
      });
    }

    next();
  };
}
```

### Tiered Rate Limits

```typescript
const rateLimitTiers = {
  free: { requests: 100, window: 3600 },
  basic: { requests: 1000, window: 3600 },
  pro: { requests: 10000, window: 3600 },
  enterprise: { requests: 100000, window: 3600 },
};

function getTierLimiter(tier: keyof typeof rateLimitTiers) {
  const config = rateLimitTiers[tier];
  return new SlidingWindowRateLimiter(redis, config.window * 1000, config.requests);
}
```

## Idempotency

### Idempotency Key Pattern

```typescript
interface IdempotencyRecord {
  key: string;
  request_hash: string;
  response_status: number;
  response_body: string;
  created_at: Date;
  expires_at: Date;
}

class IdempotencyService {
  private lockTTL = 10; // 10 seconds
  private recordTTL = 24 * 60 * 60; // 24 hours

  async processRequest(
    key: string,
    requestBody: any,
    handler: () => Promise<{ status: number; body: any }>
  ): Promise<{ status: number; body: any; cached: boolean }> {
    // Validate key format (UUID or custom)
    if (!this.isValidKey(key)) {
      throw new ValidationError([{
        field: 'Idempotency-Key',
        code: 'INVALID_FORMAT',
        message: 'Must be a valid UUID',
      }]);
    }

    const requestHash = this.hashRequest(requestBody);
    const existing = await this.getRecord(key);

    if (existing) {
      if (existing.request_hash !== requestHash) {
        throw new ConflictError('Idempotency key used with different request body');
      }
      return {
        status: existing.response_status,
        body: JSON.parse(existing.response_body),
        cached: true,
      };
    }

    // Acquire lock for concurrent requests
    const lockKey = `idempotency:lock:${key}`;
    const locked = await this.redis.set(lockKey, '1', 'NX', 'EX', this.lockTTL);
    if (!locked) {
      throw new ConflictError('Request already being processed');
    }

    try {
      const result = await handler();
      await this.saveRecord({
        key,
        request_hash: requestHash,
        response_status: result.status,
        response_body: JSON.stringify(result.body),
        created_at: new Date(),
        expires_at: new Date(Date.now() + this.recordTTL * 1000),
      });
      return { ...result, cached: false };
    } finally {
      await this.redis.del(lockKey);
    }
  }

  private hashRequest(body: any): string {
    const normalized = JSON.stringify(body, Object.keys(body).sort());
    return crypto.createHash('sha256').update(normalized).digest('hex');
  }
}
```

### Idempotency Middleware

```typescript
function idempotencyMiddleware(options?: {
  headerName?: string;
  required?: boolean;
  methods?: string[];
}) {
  const {
    headerName = 'Idempotency-Key',
    required = false,
    methods = ['POST', 'PATCH'],
  } = options || {};

  return async (req: Request, res: Response, next: NextFunction) => {
    if (!methods.includes(req.method)) return next();

    const key = req.headers[headerName.toLowerCase()] as string;
    if (!key) {
      if (required) {
        return res.status(400).json({
          error: { code: 'MISSING_IDEMPOTENCY_KEY' }
        });
      }
      return next();
    }

    try {
      const result = await idempotencyService.processRequest(
        key,
        req.body,
        async () => {
          // Capture response
          return new Promise((resolve) => {
            const originalSend = res.send.bind(res);
            res.send = function(body: any) {
              resolve({ status: res.statusCode, body });
              return originalSend(body);
            };
            next();
          });
        }
      );

      if (result.cached) {
        res.set('Idempotency-Replayed', 'true');
        return res.status(result.status).json(result.body);
      }
    } catch (error) {
      if (error instanceof ConflictError) {
        return res.status(409).json({ error: { code: 'IDEMPOTENCY_CONFLICT' } });
      }
      throw error;
    }
  };
}
```

### Client Implementation

```typescript
async function idempotentRequest<T>(
  method: 'POST' | 'PATCH',
  path: string,
  body: any,
  options?: { idempotencyKey?: string; maxRetries?: number }
): Promise<T> {
  const {
    idempotencyKey = crypto.randomUUID(),
    maxRetries = 3,
  } = options || {};

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const response = await fetch(path, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        return response.json();
      }

      // Don't retry client errors (except rate limiting)
      if (response.status >= 400 && response.status < 500 && response.status !== 429) {
        throw new Error(await response.text());
      }

      // Retry with exponential backoff
      if (attempt < maxRetries) {
        await sleep(1000 * Math.pow(2, attempt - 1));
      }
    } catch (error) {
      if (attempt === maxRetries) throw error;
      await sleep(1000 * Math.pow(2, attempt - 1));
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Best Practices Summary

### Authentication
- [ ] Hash API keys before storing
- [ ] Use short-lived access tokens (15-30 min)
- [ ] Implement refresh token rotation
- [ ] Use PKCE for public clients
- [ ] Validate webhook signatures

### Error Handling
- [ ] Use consistent error format (RFC 7807)
- [ ] Include request ID in all errors
- [ ] Don't leak internal details
- [ ] Log errors with context
- [ ] Document all error codes

### Rate Limiting
- [ ] Use sliding window or token bucket
- [ ] Return rate limit headers
- [ ] Implement tiered limits
- [ ] Handle bursts gracefully
- [ ] Include Retry-After header

### Idempotency
- [ ] Require keys for mutations
- [ ] Hash request body for matching
- [ ] Set appropriate TTL (24h common)
- [ ] Handle concurrent requests
- [ ] Return Idempotency-Replayed header
