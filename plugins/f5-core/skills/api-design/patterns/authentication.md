---
name: authentication
description: API authentication patterns and security
category: api-design/patterns
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Authentication Patterns

## Overview

Authentication verifies the identity of API consumers. Choosing the right
authentication method depends on your use case, security requirements, and
client types.

## Authentication Methods Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                 Authentication Methods Comparison                │
├────────────────┬────────────────────────────────────────────────┤
│ Method         │ Use Case          │ Security │ Complexity      │
├────────────────┼───────────────────┼──────────┼─────────────────┤
│ API Keys       │ Server-to-server  │ Medium   │ Low             │
│ Basic Auth     │ Simple APIs       │ Low      │ Very Low        │
│ Bearer Tokens  │ User sessions     │ High     │ Medium          │
│ OAuth 2.0      │ Third-party apps  │ High     │ High            │
│ JWT            │ Stateless auth    │ High     │ Medium          │
│ mTLS           │ High-security     │ Very High│ High            │
│ HMAC           │ Webhook signing   │ High     │ Medium          │
└────────────────┴───────────────────┴──────────┴─────────────────┘
```

## API Keys

### Implementation

```typescript
// Generate API key
function generateApiKey(): { key: string; hash: string } {
  // Generate random key
  const prefix = 'sk_live_';
  const randomPart = crypto.randomBytes(24).toString('base64url');
  const key = `${prefix}${randomPart}`;

  // Store hash, not the key itself
  const hash = crypto.createHash('sha256').update(key).digest('hex');

  return { key, hash };
}

// Store in database
interface ApiKeyRecord {
  id: string;
  hash: string; // SHA-256 hash of the key
  name: string;
  user_id: string;
  scopes: string[];
  last_used_at: Date | null;
  expires_at: Date | null;
  created_at: Date;
}

// Validation middleware
async function validateApiKey(
  req: Request,
  res: Response,
  next: NextFunction
) {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({
      error: {
        code: 'MISSING_API_KEY',
        message: 'API key is required',
      },
    });
  }

  const apiKey = authHeader.slice(7);

  // Validate format
  if (!apiKey.startsWith('sk_live_') && !apiKey.startsWith('sk_test_')) {
    return res.status(401).json({
      error: {
        code: 'INVALID_API_KEY',
        message: 'Invalid API key format',
      },
    });
  }

  // Look up by hash
  const hash = crypto.createHash('sha256').update(apiKey).digest('hex');
  const keyRecord = await db.apiKeys.findByHash(hash);

  if (!keyRecord) {
    return res.status(401).json({
      error: {
        code: 'INVALID_API_KEY',
        message: 'API key not found or invalid',
      },
    });
  }

  // Check expiration
  if (keyRecord.expires_at && keyRecord.expires_at < new Date()) {
    return res.status(401).json({
      error: {
        code: 'EXPIRED_API_KEY',
        message: 'API key has expired',
      },
    });
  }

  // Update last used
  await db.apiKeys.updateLastUsed(keyRecord.id);

  // Attach to request
  req.apiKey = keyRecord;
  req.user = await db.users.findById(keyRecord.user_id);

  next();
}
```

### Scope-Based Authorization

```typescript
// Define scopes
const SCOPES = {
  'read:users': 'Read user data',
  'write:users': 'Create and update users',
  'delete:users': 'Delete users',
  'read:orders': 'Read order data',
  'write:orders': 'Create and update orders',
  admin: 'Full administrative access',
};

// Scope check middleware
function requireScopes(...requiredScopes: string[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    const keyScopes = req.apiKey?.scopes || [];

    // Admin has all permissions
    if (keyScopes.includes('admin')) {
      return next();
    }

    const hasAllScopes = requiredScopes.every((scope) =>
      keyScopes.includes(scope)
    );

    if (!hasAllScopes) {
      return res.status(403).json({
        error: {
          code: 'INSUFFICIENT_SCOPES',
          message: 'API key lacks required permissions',
          context: {
            required: requiredScopes,
            provided: keyScopes,
          },
        },
      });
    }

    next();
  };
}

// Usage
router.get('/users', requireScopes('read:users'), listUsers);
router.post('/users', requireScopes('write:users'), createUser);
router.delete('/users/:id', requireScopes('delete:users'), deleteUser);
```

## JWT Authentication

### Token Generation

```typescript
import jwt from 'jsonwebtoken';

interface TokenPayload {
  sub: string; // Subject (user ID)
  email: string;
  role: string;
  permissions: string[];
}

interface TokenPair {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: 'Bearer';
}

class AuthService {
  private readonly accessTokenSecret: string;
  private readonly refreshTokenSecret: string;
  private readonly accessTokenExpiry = '15m';
  private readonly refreshTokenExpiry = '7d';

  generateTokens(user: User): TokenPair {
    const payload: TokenPayload = {
      sub: user.id,
      email: user.email,
      role: user.role,
      permissions: user.permissions,
    };

    const accessToken = jwt.sign(payload, this.accessTokenSecret, {
      expiresIn: this.accessTokenExpiry,
      issuer: 'api.example.com',
      audience: 'example.com',
    });

    const refreshToken = jwt.sign(
      { sub: user.id, type: 'refresh' },
      this.refreshTokenSecret,
      {
        expiresIn: this.refreshTokenExpiry,
        issuer: 'api.example.com',
      }
    );

    return {
      access_token: accessToken,
      refresh_token: refreshToken,
      expires_in: 900, // 15 minutes in seconds
      token_type: 'Bearer',
    };
  }

  verifyAccessToken(token: string): TokenPayload {
    try {
      return jwt.verify(token, this.accessTokenSecret, {
        issuer: 'api.example.com',
        audience: 'example.com',
      }) as TokenPayload;
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new UnauthorizedError('Token has expired');
      }
      if (error instanceof jwt.JsonWebTokenError) {
        throw new UnauthorizedError('Invalid token');
      }
      throw error;
    }
  }

  async refreshTokens(refreshToken: string): Promise<TokenPair> {
    try {
      const payload = jwt.verify(refreshToken, this.refreshTokenSecret) as any;

      // Check if refresh token is blacklisted
      if (await this.isTokenBlacklisted(refreshToken)) {
        throw new UnauthorizedError('Token has been revoked');
      }

      // Get fresh user data
      const user = await db.users.findById(payload.sub);
      if (!user || user.status !== 'active') {
        throw new UnauthorizedError('User not found or inactive');
      }

      // Blacklist old refresh token (rotation)
      await this.blacklistToken(refreshToken);

      return this.generateTokens(user);
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new UnauthorizedError('Refresh token has expired');
      }
      throw error;
    }
  }

  private async blacklistToken(token: string): Promise<void> {
    const hash = crypto.createHash('sha256').update(token).digest('hex');
    await redis.set(`blacklist:${hash}`, '1', 'EX', 7 * 24 * 60 * 60);
  }

  private async isTokenBlacklisted(token: string): Promise<boolean> {
    const hash = crypto.createHash('sha256').update(token).digest('hex');
    return !!(await redis.get(`blacklist:${hash}`));
  }
}
```

### JWT Middleware

```typescript
// JWT validation middleware
async function jwtAuth(req: Request, res: Response, next: NextFunction) {
  const authHeader = req.headers.authorization;

  if (!authHeader?.startsWith('Bearer ')) {
    return res.status(401).json({
      error: {
        code: 'MISSING_TOKEN',
        message: 'Authorization token is required',
      },
    });
  }

  const token = authHeader.slice(7);

  try {
    const payload = authService.verifyAccessToken(token);

    // Check if user still exists and is active
    const user = await db.users.findById(payload.sub);
    if (!user || user.status !== 'active') {
      return res.status(401).json({
        error: {
          code: 'USER_INVALID',
          message: 'User not found or account suspended',
        },
      });
    }

    req.user = user;
    req.tokenPayload = payload;
    next();
  } catch (error) {
    if (error instanceof UnauthorizedError) {
      return res.status(401).json({
        error: {
          code: 'INVALID_TOKEN',
          message: error.message,
        },
      });
    }
    next(error);
  }
}
```

## OAuth 2.0

### Authorization Code Flow

```typescript
// OAuth configuration
interface OAuthConfig {
  clientId: string;
  clientSecret: string;
  redirectUri: string;
  authorizationUrl: string;
  tokenUrl: string;
  scopes: string[];
}

// Authorization endpoint
router.get('/oauth/authorize', (req, res) => {
  const { client_id, redirect_uri, response_type, scope, state } = req.query;

  // Validate client
  const client = await db.oauthClients.findById(client_id);
  if (!client) {
    return res.status(400).json({
      error: 'invalid_client',
      error_description: 'Unknown client',
    });
  }

  // Validate redirect URI
  if (!client.redirect_uris.includes(redirect_uri)) {
    return res.status(400).json({
      error: 'invalid_request',
      error_description: 'Invalid redirect URI',
    });
  }

  // Show consent page
  res.render('consent', {
    client,
    scopes: scope.split(' '),
    state,
    redirect_uri,
  });
});

// Handle consent
router.post('/oauth/authorize', jwtAuth, async (req, res) => {
  const { client_id, redirect_uri, scope, state, consent } = req.body;

  if (consent !== 'allow') {
    return res.redirect(
      `${redirect_uri}?error=access_denied&state=${state}`
    );
  }

  // Generate authorization code
  const code = crypto.randomBytes(32).toString('hex');

  // Store code with metadata (short-lived, 10 minutes)
  await redis.set(
    `oauth:code:${code}`,
    JSON.stringify({
      client_id,
      user_id: req.user.id,
      scope,
      redirect_uri,
    }),
    'EX',
    600
  );

  // Redirect with code
  res.redirect(`${redirect_uri}?code=${code}&state=${state}`);
});

// Token endpoint
router.post('/oauth/token', async (req, res) => {
  const { grant_type, code, redirect_uri, client_id, client_secret, refresh_token } =
    req.body;

  // Validate client credentials
  const client = await db.oauthClients.findById(client_id);
  if (!client || client.secret !== client_secret) {
    return res.status(401).json({
      error: 'invalid_client',
      error_description: 'Invalid client credentials',
    });
  }

  if (grant_type === 'authorization_code') {
    // Exchange code for tokens
    const codeData = await redis.get(`oauth:code:${code}`);
    if (!codeData) {
      return res.status(400).json({
        error: 'invalid_grant',
        error_description: 'Invalid or expired authorization code',
      });
    }

    const { client_id: storedClientId, user_id, scope, redirect_uri: storedUri } =
      JSON.parse(codeData);

    // Validate code belongs to this client
    if (storedClientId !== client_id || storedUri !== redirect_uri) {
      return res.status(400).json({
        error: 'invalid_grant',
        error_description: 'Code does not match client',
      });
    }

    // Delete used code
    await redis.del(`oauth:code:${code}`);

    // Generate tokens
    const user = await db.users.findById(user_id);
    const tokens = authService.generateOAuthTokens(user, scope.split(' '));

    return res.json({
      access_token: tokens.access_token,
      token_type: 'Bearer',
      expires_in: 3600,
      refresh_token: tokens.refresh_token,
      scope,
    });
  }

  if (grant_type === 'refresh_token') {
    // Refresh tokens
    const tokens = await authService.refreshOAuthTokens(refresh_token, client_id);
    return res.json(tokens);
  }

  res.status(400).json({
    error: 'unsupported_grant_type',
    error_description: 'Grant type not supported',
  });
});
```

### PKCE (Proof Key for Code Exchange)

```typescript
// Client generates code verifier and challenge
function generatePKCE(): { verifier: string; challenge: string } {
  const verifier = crypto.randomBytes(32).toString('base64url');
  const challenge = crypto
    .createHash('sha256')
    .update(verifier)
    .digest('base64url');

  return { verifier, challenge };
}

// Authorization request with PKCE
const { verifier, challenge } = generatePKCE();

const authUrl = new URL('https://auth.example.com/oauth/authorize');
authUrl.searchParams.set('client_id', clientId);
authUrl.searchParams.set('redirect_uri', redirectUri);
authUrl.searchParams.set('response_type', 'code');
authUrl.searchParams.set('scope', 'read:users write:users');
authUrl.searchParams.set('code_challenge', challenge);
authUrl.searchParams.set('code_challenge_method', 'S256');
authUrl.searchParams.set('state', generateState());

// Store verifier for later
sessionStorage.setItem('pkce_verifier', verifier);

// Redirect to auth
window.location.href = authUrl.toString();

// Token exchange with verifier
const tokenResponse = await fetch('https://auth.example.com/oauth/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: authorizationCode,
    redirect_uri: redirectUri,
    client_id: clientId,
    code_verifier: sessionStorage.getItem('pkce_verifier'),
  }),
});
```

## Webhook Signature Verification

```typescript
// Generate webhook signature
function signWebhook(payload: string, secret: string, timestamp: number): string {
  const data = `${timestamp}.${payload}`;
  return crypto.createHmac('sha256', secret).update(data).digest('hex');
}

// Send webhook
async function sendWebhook(url: string, event: WebhookEvent, secret: string) {
  const payload = JSON.stringify(event);
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = signWebhook(payload, secret, timestamp);

  await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Webhook-Signature': `t=${timestamp},v1=${signature}`,
      'X-Webhook-ID': event.id,
    },
    body: payload,
  });
}

// Verify webhook (receiver side)
function verifyWebhook(
  payload: string,
  signatureHeader: string,
  secret: string,
  tolerance = 300 // 5 minutes
): boolean {
  // Parse signature header
  const parts = signatureHeader.split(',');
  const timestamp = parseInt(parts.find((p) => p.startsWith('t='))?.slice(2) || '0');
  const signature = parts.find((p) => p.startsWith('v1='))?.slice(3);

  if (!timestamp || !signature) {
    throw new Error('Invalid signature format');
  }

  // Check timestamp to prevent replay attacks
  const now = Math.floor(Date.now() / 1000);
  if (Math.abs(now - timestamp) > tolerance) {
    throw new Error('Timestamp too old');
  }

  // Verify signature
  const expected = signWebhook(payload, secret, timestamp);
  const valid = crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );

  if (!valid) {
    throw new Error('Invalid signature');
  }

  return true;
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Authentication Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use HTTPS Always                                            │
│     └── Never send credentials over HTTP                        │
│                                                                  │
│  2. Hash Stored Secrets                                         │
│     └── Store hashes of API keys, not keys themselves           │
│                                                                  │
│  3. Implement Token Rotation                                    │
│     └── Short-lived access tokens, refresh token rotation       │
│                                                                  │
│  4. Use Secure Random Generation                                │
│     └── crypto.randomBytes, not Math.random                     │
│                                                                  │
│  5. Implement Rate Limiting                                     │
│     └── Prevent brute force attacks                             │
│                                                                  │
│  6. Log Authentication Events                                   │
│     └── Track logins, failures, key usage                       │
│                                                                  │
│  7. Support Key Rotation                                        │
│     └── Allow users to revoke and regenerate keys               │
│                                                                  │
│  8. Use Constant-Time Comparison                                │
│     └── Prevent timing attacks                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
