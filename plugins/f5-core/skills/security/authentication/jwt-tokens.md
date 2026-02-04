---
name: jwt-tokens
description: JWT token implementation and best practices
category: security/authentication
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# JWT Token Security

## Overview

JSON Web Tokens (JWT) are compact, URL-safe tokens for authentication
and information exchange.

## JWT Structure

```
Header.Payload.Signature

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4iLCJpYXQiOjE1MTYyMzkwMjJ9.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### Header
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

### Payload (Claims)
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "iat": 1516239022,
  "exp": 1516242622
}
```

## Secure Implementation

### Token Service

```typescript
// services/token.service.ts
import jwt from 'jsonwebtoken';
import crypto from 'crypto';

interface TokenPayload {
  sub: string;        // Subject (user ID)
  email: string;
  roles: string[];
  type: 'access' | 'refresh';
}

interface TokenPair {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

export class TokenService {
  private readonly accessSecret: string;
  private readonly refreshSecret: string;
  private readonly accessExpiry = '15m';   // Short-lived
  private readonly refreshExpiry = '7d';   // Longer-lived

  constructor() {
    this.accessSecret = process.env.JWT_ACCESS_SECRET!;
    this.refreshSecret = process.env.JWT_REFRESH_SECRET!;

    if (!this.accessSecret || !this.refreshSecret) {
      throw new Error('JWT secrets must be configured');
    }
  }

  generateTokenPair(user: User): TokenPair {
    const payload: Omit<TokenPayload, 'type'> = {
      sub: user.id,
      email: user.email,
      roles: user.roles,
    };

    const accessToken = jwt.sign(
      { ...payload, type: 'access' },
      this.accessSecret,
      {
        expiresIn: this.accessExpiry,
        issuer: 'myapp',
        audience: 'myapp-api',
        jwtid: crypto.randomUUID(), // Unique token ID
      }
    );

    const refreshToken = jwt.sign(
      { ...payload, type: 'refresh' },
      this.refreshSecret,
      {
        expiresIn: this.refreshExpiry,
        issuer: 'myapp',
        audience: 'myapp-api',
        jwtid: crypto.randomUUID(),
      }
    );

    return {
      accessToken,
      refreshToken,
      expiresIn: 900, // 15 minutes in seconds
    };
  }

  verifyAccessToken(token: string): TokenPayload {
    try {
      const decoded = jwt.verify(token, this.accessSecret, {
        issuer: 'myapp',
        audience: 'myapp-api',
      }) as TokenPayload;

      if (decoded.type !== 'access') {
        throw new Error('Invalid token type');
      }

      return decoded;
    } catch (error) {
      if (error instanceof jwt.TokenExpiredError) {
        throw new UnauthorizedError('Token expired');
      }
      if (error instanceof jwt.JsonWebTokenError) {
        throw new UnauthorizedError('Invalid token');
      }
      throw error;
    }
  }

  verifyRefreshToken(token: string): TokenPayload {
    try {
      const decoded = jwt.verify(token, this.refreshSecret, {
        issuer: 'myapp',
        audience: 'myapp-api',
      }) as TokenPayload;

      if (decoded.type !== 'refresh') {
        throw new Error('Invalid token type');
      }

      return decoded;
    } catch (error) {
      throw new UnauthorizedError('Invalid refresh token');
    }
  }
}
```

### Refresh Token Rotation

```typescript
// services/auth.service.ts
export class AuthService {
  constructor(
    private tokenService: TokenService,
    private userRepository: UserRepository,
    private refreshTokenRepository: RefreshTokenRepository,
    private redis: Redis
  ) {}

  async login(email: string, password: string): Promise<TokenPair> {
    const user = await this.userRepository.findByEmail(email);
    if (!user || !await this.verifyPassword(password, user.passwordHash)) {
      throw new UnauthorizedError('Invalid credentials');
    }

    const tokens = this.tokenService.generateTokenPair(user);

    // Store refresh token hash for rotation/revocation
    await this.refreshTokenRepository.save({
      userId: user.id,
      tokenHash: this.hashToken(tokens.refreshToken),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
      userAgent: request.headers['user-agent'],
      ipAddress: request.ip,
    });

    return tokens;
  }

  async refreshTokens(refreshToken: string): Promise<TokenPair> {
    // Verify token
    const payload = this.tokenService.verifyRefreshToken(refreshToken);

    // Check if token is in database (not revoked)
    const storedToken = await this.refreshTokenRepository.findByHash(
      this.hashToken(refreshToken)
    );

    if (!storedToken) {
      // Token reuse detected! Revoke all user tokens
      await this.revokeAllUserTokens(payload.sub);
      throw new UnauthorizedError('Token reuse detected');
    }

    // Get fresh user data
    const user = await this.userRepository.findById(payload.sub);
    if (!user) {
      throw new UnauthorizedError('User not found');
    }

    // Generate new token pair
    const newTokens = this.tokenService.generateTokenPair(user);

    // Rotate: Delete old, save new
    await this.refreshTokenRepository.delete(storedToken.id);
    await this.refreshTokenRepository.save({
      userId: user.id,
      tokenHash: this.hashToken(newTokens.refreshToken),
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    });

    return newTokens;
  }

  async logout(refreshToken: string): Promise<void> {
    const tokenHash = this.hashToken(refreshToken);
    await this.refreshTokenRepository.deleteByHash(tokenHash);
  }

  async revokeAllUserTokens(userId: string): Promise<void> {
    await this.refreshTokenRepository.deleteAllByUserId(userId);

    // Also blacklist any existing access tokens
    await this.redis.set(
      `user:${userId}:tokens_revoked_at`,
      Date.now(),
      'EX',
      900 // 15 minutes (access token lifetime)
    );
  }

  private hashToken(token: string): string {
    return crypto.createHash('sha256').update(token).digest('hex');
  }
}
```

### Auth Middleware

```typescript
// middleware/auth.middleware.ts
export function authMiddleware(tokenService: TokenService, redis: Redis) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const authHeader = req.headers.authorization;
      if (!authHeader?.startsWith('Bearer ')) {
        throw new UnauthorizedError('No token provided');
      }

      const token = authHeader.substring(7);
      const payload = tokenService.verifyAccessToken(token);

      // Check if tokens were revoked after this token was issued
      const revokedAt = await redis.get(`user:${payload.sub}:tokens_revoked_at`);
      if (revokedAt) {
        const tokenIssuedAt = payload.iat! * 1000;
        if (tokenIssuedAt < parseInt(revokedAt)) {
          throw new UnauthorizedError('Token revoked');
        }
      }

      // Attach user to request
      req.user = {
        id: payload.sub,
        email: payload.email,
        roles: payload.roles,
      };

      next();
    } catch (error) {
      next(error);
    }
  };
}
```

## JWT Security Best Practices

| Practice | Description |
|----------|-------------|
| Short expiry | Access tokens: 15-30 minutes |
| Secure storage | HttpOnly cookies or secure storage |
| Rotate refresh | New refresh token on each use |
| Validate claims | Check iss, aud, exp, iat |
| Use strong secrets | 256+ bit random keys |
| Token binding | Tie to device/IP when possible |
| Revocation | Implement token blacklist/rotation |

## Common Mistakes

```typescript
// ❌ WRONG: Storing sensitive data in JWT
jwt.sign({
  userId: '123',
  password: 'secret',     // Never store passwords!
  creditCard: '4242...',  // Never store PII!
}, secret);

// ❌ WRONG: Long-lived access tokens
jwt.sign(payload, secret, { expiresIn: '30d' }); // Too long!

// ❌ WRONG: Weak secret
const secret = 'mysecret'; // Too weak!

// ✅ CORRECT: Strong random secret
const secret = crypto.randomBytes(64).toString('hex');

// ❌ WRONG: No token validation
const decoded = jwt.decode(token); // Doesn't verify signature!

// ✅ CORRECT: Always verify
const decoded = jwt.verify(token, secret, { algorithms: ['HS256'] });
```

## Token Storage Recommendations

### Web Applications

```typescript
// Option 1: HttpOnly Cookie (Recommended for web)
res.cookie('refreshToken', refreshToken, {
  httpOnly: true,      // Not accessible via JavaScript
  secure: true,        // HTTPS only
  sameSite: 'strict',  // CSRF protection
  maxAge: 7 * 24 * 60 * 60 * 1000, // 7 days
  path: '/api/auth',   // Only sent to auth endpoints
});

// Option 2: Memory + Secure Cookie combo
// Access token in memory, refresh in HttpOnly cookie
```

### Mobile Applications

```typescript
// Use secure storage
import * as SecureStore from 'expo-secure-store';

await SecureStore.setItemAsync('refreshToken', token);
const token = await SecureStore.getItemAsync('refreshToken');
```

## Algorithm Selection

| Algorithm | Type | Use Case |
|-----------|------|----------|
| HS256 | Symmetric | Simple apps, same secret both sides |
| RS256 | Asymmetric | Microservices, distributed systems |
| ES256 | Asymmetric | High performance, smaller tokens |

```typescript
// RS256 with key pair
const privateKey = fs.readFileSync('private.pem');
const publicKey = fs.readFileSync('public.pem');

// Sign with private key
const token = jwt.sign(payload, privateKey, { algorithm: 'RS256' });

// Verify with public key
const decoded = jwt.verify(token, publicKey, { algorithms: ['RS256'] });
```
