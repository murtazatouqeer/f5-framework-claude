---
name: api-keys
description: API key management and security
category: security/api-security
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Key Management

## Overview

API keys provide a way to authenticate applications and track API usage.
Proper management is critical for security.

## Key Generation

```typescript
// services/api-key.service.ts
import crypto from 'crypto';

export class ApiKeyService {
  private readonly PREFIX = 'myapp';
  private readonly KEY_LENGTH = 32;
  private readonly HASH_ALGORITHM = 'sha256';

  constructor(
    private apiKeyRepository: ApiKeyRepository,
    private redis: Redis
  ) {}

  async generateKey(userId: string, options: CreateKeyOptions): Promise<GeneratedKey> {
    // Generate secure random key
    const keyValue = crypto.randomBytes(this.KEY_LENGTH).toString('hex');

    // Create prefixed key for easy identification
    // Format: myapp_live_abc123... or myapp_test_xyz789...
    const environment = options.isTest ? 'test' : 'live';
    const fullKey = `${this.PREFIX}_${environment}_${keyValue}`;

    // Hash for storage (never store plain key)
    const keyHash = this.hashKey(fullKey);

    // Generate key ID (first 8 chars of hash)
    const keyId = keyHash.substring(0, 8);

    // Store metadata with hash
    const apiKey = await this.apiKeyRepository.create({
      id: keyId,
      userId,
      keyHash,
      name: options.name,
      permissions: options.permissions || ['read'],
      rateLimit: options.rateLimit || 1000,
      expiresAt: options.expiresAt,
      allowedIps: options.allowedIps || [],
      allowedOrigins: options.allowedOrigins || [],
      isTest: options.isTest || false,
    });

    // Return full key only once (won't be stored)
    return {
      key: fullKey,
      keyId,
      prefix: `${this.PREFIX}_${environment}_${keyValue.substring(0, 8)}...`,
      createdAt: apiKey.createdAt,
    };
  }

  async validateKey(key: string): Promise<ApiKeyInfo | null> {
    // Check cache first
    const cached = await this.redis.get(`apikey:${key}`);
    if (cached === 'invalid') {
      return null;
    }
    if (cached) {
      return JSON.parse(cached);
    }

    // Hash and lookup
    const keyHash = this.hashKey(key);
    const apiKey = await this.apiKeyRepository.findByHash(keyHash);

    if (!apiKey) {
      // Cache negative result briefly
      await this.redis.setex(`apikey:${key}`, 60, 'invalid');
      return null;
    }

    // Check if expired
    if (apiKey.expiresAt && apiKey.expiresAt < new Date()) {
      await this.redis.setex(`apikey:${key}`, 60, 'invalid');
      return null;
    }

    // Check if revoked
    if (apiKey.revokedAt) {
      await this.redis.setex(`apikey:${key}`, 60, 'invalid');
      return null;
    }

    const keyInfo: ApiKeyInfo = {
      id: apiKey.id,
      userId: apiKey.userId,
      permissions: apiKey.permissions,
      rateLimit: apiKey.rateLimit,
      allowedIps: apiKey.allowedIps,
      allowedOrigins: apiKey.allowedOrigins,
      isTest: apiKey.isTest,
    };

    // Cache for 5 minutes
    await this.redis.setex(`apikey:${key}`, 300, JSON.stringify(keyInfo));

    return keyInfo;
  }

  async revokeKey(keyId: string, userId: string): Promise<void> {
    const apiKey = await this.apiKeyRepository.findById(keyId);

    if (!apiKey || apiKey.userId !== userId) {
      throw new NotFoundError('API key not found');
    }

    await this.apiKeyRepository.update(keyId, {
      revokedAt: new Date(),
    });

    // Invalidate cache
    await this.redis.del(`apikey:${apiKey.keyHash}`);
  }

  async rotateKey(keyId: string, userId: string): Promise<GeneratedKey> {
    const existingKey = await this.apiKeyRepository.findById(keyId);

    if (!existingKey || existingKey.userId !== userId) {
      throw new NotFoundError('API key not found');
    }

    // Generate new key with same settings
    const newKey = await this.generateKey(userId, {
      name: `${existingKey.name} (rotated)`,
      permissions: existingKey.permissions,
      rateLimit: existingKey.rateLimit,
      allowedIps: existingKey.allowedIps,
      allowedOrigins: existingKey.allowedOrigins,
      isTest: existingKey.isTest,
    });

    // Revoke old key after grace period
    setTimeout(async () => {
      await this.revokeKey(keyId, userId);
    }, 24 * 60 * 60 * 1000); // 24 hours

    return newKey;
  }

  private hashKey(key: string): string {
    return crypto
      .createHash(this.HASH_ALGORITHM)
      .update(key)
      .digest('hex');
  }
}
```

## Authentication Middleware

```typescript
// middleware/api-key.middleware.ts
export function apiKeyAuth(apiKeyService: ApiKeyService) {
  return async (req: Request, res: Response, next: NextFunction) => {
    // Get key from header or query
    const apiKey =
      req.headers['x-api-key'] ||
      req.headers['authorization']?.replace('Bearer ', '') ||
      req.query.api_key;

    if (!apiKey || typeof apiKey !== 'string') {
      return res.status(401).json({ error: 'API key required' });
    }

    // Validate key
    const keyInfo = await apiKeyService.validateKey(apiKey);
    if (!keyInfo) {
      return res.status(401).json({ error: 'Invalid API key' });
    }

    // Check IP restriction
    if (keyInfo.allowedIps.length > 0) {
      const clientIp = req.ip;
      if (!keyInfo.allowedIps.includes(clientIp)) {
        return res.status(403).json({ error: 'IP not allowed' });
      }
    }

    // Check origin restriction
    if (keyInfo.allowedOrigins.length > 0) {
      const origin = req.headers.origin;
      if (origin && !keyInfo.allowedOrigins.includes(origin)) {
        return res.status(403).json({ error: 'Origin not allowed' });
      }
    }

    // Attach key info to request
    req.apiKey = keyInfo;
    req.userId = keyInfo.userId;

    next();
  };
}

// Permission check middleware
export function requirePermission(permission: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!req.apiKey?.permissions.includes(permission)) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        required: permission,
        current: req.apiKey?.permissions || [],
      });
    }
    next();
  };
}

// Usage
router.get('/api/data', apiKeyAuth(apiKeyService), getData);
router.post('/api/data', apiKeyAuth(apiKeyService), requirePermission('write'), createData);
router.delete('/api/data/:id', apiKeyAuth(apiKeyService), requirePermission('delete'), deleteData);
```

## Key Scopes and Permissions

```typescript
// types/api-key.types.ts
export const ApiKeyScopes = {
  // Read operations
  'read': 'Read access to resources',
  'read:users': 'Read user data',
  'read:orders': 'Read order data',
  'read:analytics': 'Read analytics data',

  // Write operations
  'write': 'Write access to resources',
  'write:users': 'Create/update users',
  'write:orders': 'Create/update orders',

  // Delete operations
  'delete': 'Delete resources',
  'delete:users': 'Delete users',
  'delete:orders': 'Delete orders',

  // Admin operations
  'admin': 'Full administrative access',
} as const;

export type ApiKeyScope = keyof typeof ApiKeyScopes;

// Scope hierarchy
export const scopeHierarchy: Record<string, string[]> = {
  'admin': Object.keys(ApiKeyScopes),
  'read': ['read:users', 'read:orders', 'read:analytics'],
  'write': ['write:users', 'write:orders'],
  'delete': ['delete:users', 'delete:orders'],
};

// Check if scopes include required permission
export function hasScope(
  userScopes: string[],
  requiredScope: string
): boolean {
  // Direct match
  if (userScopes.includes(requiredScope)) {
    return true;
  }

  // Check hierarchy
  for (const scope of userScopes) {
    const children = scopeHierarchy[scope];
    if (children?.includes(requiredScope)) {
      return true;
    }
  }

  return false;
}
```

## Key Management API

```typescript
// routes/api-keys.routes.ts
router.get('/api-keys', requireAuth, async (req, res) => {
  const keys = await apiKeyRepository.findByUserId(req.user.id);

  // Return metadata only, never the actual key
  res.json({
    keys: keys.map(k => ({
      id: k.id,
      name: k.name,
      prefix: k.prefix,
      permissions: k.permissions,
      createdAt: k.createdAt,
      lastUsedAt: k.lastUsedAt,
      expiresAt: k.expiresAt,
      isTest: k.isTest,
    })),
  });
});

router.post('/api-keys', requireAuth, async (req, res) => {
  const { name, permissions, expiresAt, allowedIps, isTest } = req.body;

  // Validate permissions
  const validPermissions = permissions.filter(
    (p: string) => p in ApiKeyScopes
  );

  const generatedKey = await apiKeyService.generateKey(req.user.id, {
    name,
    permissions: validPermissions,
    expiresAt: expiresAt ? new Date(expiresAt) : undefined,
    allowedIps,
    isTest,
  });

  // This is the only time the full key is shown
  res.status(201).json({
    message: 'API key created. Save this key - it will not be shown again.',
    key: generatedKey.key,
    keyId: generatedKey.keyId,
  });
});

router.delete('/api-keys/:keyId', requireAuth, async (req, res) => {
  await apiKeyService.revokeKey(req.params.keyId, req.user.id);
  res.status(204).end();
});

router.post('/api-keys/:keyId/rotate', requireAuth, async (req, res) => {
  const newKey = await apiKeyService.rotateKey(req.params.keyId, req.user.id);

  res.json({
    message: 'New key generated. Old key will be revoked in 24 hours.',
    key: newKey.key,
    keyId: newKey.keyId,
  });
});
```

## Usage Tracking

```typescript
// services/api-usage.service.ts
export class ApiUsageService {
  constructor(private redis: Redis) {}

  async trackUsage(apiKeyId: string, endpoint: string, status: number): Promise<void> {
    const now = new Date();
    const hourKey = now.toISOString().slice(0, 13);
    const dayKey = now.toISOString().slice(0, 10);

    const pipeline = this.redis.pipeline();

    // Hourly stats
    pipeline.hincrby(`usage:${apiKeyId}:${hourKey}`, 'total', 1);
    pipeline.hincrby(`usage:${apiKeyId}:${hourKey}`, `status:${status}`, 1);
    pipeline.hincrby(`usage:${apiKeyId}:${hourKey}`, `endpoint:${endpoint}`, 1);
    pipeline.expire(`usage:${apiKeyId}:${hourKey}`, 86400 * 7);

    // Daily stats
    pipeline.hincrby(`usage:${apiKeyId}:daily:${dayKey}`, 'total', 1);
    pipeline.expire(`usage:${apiKeyId}:daily:${dayKey}`, 86400 * 90);

    // Update last used
    pipeline.hset(`apikey:meta:${apiKeyId}`, 'lastUsedAt', now.toISOString());

    await pipeline.exec();
  }

  async getUsageStats(apiKeyId: string, days: number = 7): Promise<UsageStats> {
    const stats: DailyStats[] = [];

    for (let i = 0; i < days; i++) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const dayKey = date.toISOString().slice(0, 10);

      const dayStats = await this.redis.hgetall(`usage:${apiKeyId}:daily:${dayKey}`);

      stats.push({
        date: dayKey,
        total: parseInt(dayStats.total || '0', 10),
      });
    }

    return { stats: stats.reverse() };
  }
}
```

## Security Considerations

```typescript
// Secure key display (obfuscate for logs)
function obfuscateKey(key: string): string {
  if (key.length < 20) return '***';
  return key.substring(0, 12) + '...' + key.substring(key.length - 4);
}

// Log usage without exposing key
function logApiKeyUsage(key: string, action: string) {
  console.log(`API Key ${obfuscateKey(key)}: ${action}`);
}

// Secure comparison to prevent timing attacks
function secureCompare(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  return crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b));
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Hash keys | Never store plain API keys |
| Prefix keys | Include environment (live/test) |
| Show once | Display key only on creation |
| Scope permissions | Principle of least privilege |
| Track usage | Monitor for anomalies |
| Rotate regularly | Support key rotation |
