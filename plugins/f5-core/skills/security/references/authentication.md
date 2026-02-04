# Authentication Patterns

JWT tokens, OAuth 2.0/OIDC, MFA, passwordless, and session management.

## Table of Contents

1. [JWT Token Security](#jwt-token-security)
2. [OAuth 2.0 & OpenID Connect](#oauth-20--openid-connect)
3. [Multi-Factor Authentication](#multi-factor-authentication)
4. [Passwordless Authentication](#passwordless-authentication)
5. [Session Management](#session-management)

---

## JWT Token Security

### Token Structure

```
Header.Payload.Signature

eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4iLCJpYXQiOjE1MTYyMzkwMjJ9.
SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### Token Service Implementation

```typescript
// services/token.service.ts
import jwt from 'jsonwebtoken';
import crypto from 'crypto';

interface TokenPayload {
  sub: string;
  email: string;
  roles: string[];
  type: 'access' | 'refresh';
}

export class TokenService {
  private readonly accessSecret: string;
  private readonly refreshSecret: string;
  private readonly accessExpiry = '15m';
  private readonly refreshExpiry = '7d';

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
        jwtid: crypto.randomUUID(),
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

    return { accessToken, refreshToken, expiresIn: 900 };
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
      throw new UnauthorizedError('Invalid token');
    }
  }
}
```

### Refresh Token Rotation

```typescript
export class AuthService {
  async refreshTokens(refreshToken: string): Promise<TokenPair> {
    const payload = this.tokenService.verifyRefreshToken(refreshToken);

    // Check if token exists in database (not revoked)
    const storedToken = await this.refreshTokenRepository.findByHash(
      this.hashToken(refreshToken)
    );

    if (!storedToken) {
      // Token reuse detected - revoke all user tokens
      await this.revokeAllUserTokens(payload.sub);
      throw new UnauthorizedError('Token reuse detected');
    }

    const user = await this.userRepository.findById(payload.sub);
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

  private hashToken(token: string): string {
    return crypto.createHash('sha256').update(token).digest('hex');
  }
}
```

### JWT Best Practices

| Practice | Description |
|----------|-------------|
| Short expiry | Access tokens: 15-30 minutes |
| Secure storage | HttpOnly cookies or secure storage |
| Rotate refresh | New refresh token on each use |
| Validate claims | Check iss, aud, exp, iat |
| Strong secrets | 256+ bit random keys |
| Token revocation | Implement blacklist/rotation |

### Algorithm Selection

| Algorithm | Type | Use Case |
|-----------|------|----------|
| HS256 | Symmetric | Simple apps, same secret |
| RS256 | Asymmetric | Microservices, distributed |
| ES256 | Asymmetric | High performance, smaller tokens |

---

## OAuth 2.0 & OpenID Connect

### OAuth 2.0 vs OIDC

| Aspect | OAuth 2.0 | OpenID Connect |
|--------|-----------|----------------|
| Purpose | Authorization | Authentication |
| Token | Access Token | ID Token + Access Token |
| Scope | Custom | openid, profile, email |
| User Info | Not standardized | /userinfo endpoint |

### Authorization Code Flow

```
User → Client: Click "Login with Google"
Client → Auth Server: Redirect with state, PKCE
User → Auth Server: Authenticate & consent
Auth Server → Client: Redirect with code
Client → Auth Server: Exchange code for tokens
Client → User: Create session
```

### OAuth Service Implementation

```typescript
export class OAuthService {
  private stateStore = new Map<string, { expiresAt: number; codeVerifier: string }>();

  generateAuthUrl(provider: 'google' | 'github'): { url: string; state: string } {
    const config = oauthConfig[provider];

    // Generate state for CSRF protection
    const state = crypto.randomBytes(32).toString('hex');

    // PKCE code verifier and challenge
    const codeVerifier = crypto.randomBytes(32).toString('base64url');
    const codeChallenge = crypto
      .createHash('sha256')
      .update(codeVerifier)
      .digest('base64url');

    this.stateStore.set(state, {
      expiresAt: Date.now() + 10 * 60 * 1000,
      codeVerifier,
    });

    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      response_type: 'code',
      scope: config.scopes.join(' '),
      state,
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
    });

    return { url: `${config.authorizationUrl}?${params}`, state };
  }

  async handleCallback(provider: string, code: string, state: string): Promise<OAuthTokens> {
    const storedState = this.stateStore.get(state);
    if (!storedState || storedState.expiresAt < Date.now()) {
      throw new Error('Invalid or expired state');
    }
    this.stateStore.delete(state);

    const response = await fetch(config.tokenUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        client_id: config.clientId,
        client_secret: config.clientSecret,
        code,
        grant_type: 'authorization_code',
        redirect_uri: config.redirectUri,
        code_verifier: storedState.codeVerifier,
      }),
    });

    return response.json();
  }
}
```

### ID Token Verification

```typescript
import jwksClient from 'jwks-rsa';

export class OIDCService {
  private client = jwksClient({
    jwksUri: 'https://www.googleapis.com/oauth2/v3/certs',
    cache: true,
    rateLimit: true,
  });

  async verifyIdToken(idToken: string): Promise<IdTokenPayload> {
    const getKey = (header: jwt.JwtHeader, callback: jwt.SigningKeyCallback) => {
      this.client.getSigningKey(header.kid, (err, key) => {
        callback(err, key?.getPublicKey());
      });
    };

    return new Promise((resolve, reject) => {
      jwt.verify(idToken, getKey, {
        algorithms: ['RS256'],
        audience: process.env.GOOGLE_CLIENT_ID,
        issuer: ['https://accounts.google.com'],
      }, (err, decoded) => {
        if (err) reject(err);
        else resolve(decoded as IdTokenPayload);
      });
    });
  }
}
```

### OAuth Security Best Practices

| Practice | Description |
|----------|-------------|
| Use PKCE | Protect against code interception |
| Validate state | Prevent CSRF attacks |
| Verify ID tokens | Check signature, issuer, audience |
| Whitelist redirects | Only allow registered URIs |
| Short-lived tokens | Access tokens expire quickly |

---

## Multi-Factor Authentication

### TOTP Implementation

```typescript
import { authenticator } from 'otplib';
import QRCode from 'qrcode';

export class MFAService {
  // Generate secret for user
  async setupMFA(user: User): Promise<{ secret: string; qrCode: string }> {
    const secret = authenticator.generateSecret();

    const otpauth = authenticator.keyuri(
      user.email,
      'MyApp',
      secret
    );

    const qrCode = await QRCode.toDataURL(otpauth);

    // Store secret temporarily until verified
    await this.mfaRepository.savePending({
      userId: user.id,
      secret,
      expiresAt: new Date(Date.now() + 10 * 60 * 1000),
    });

    return { secret, qrCode };
  }

  // Verify and enable MFA
  async enableMFA(user: User, token: string): Promise<string[]> {
    const pending = await this.mfaRepository.findPending(user.id);
    if (!pending) {
      throw new Error('No pending MFA setup');
    }

    const isValid = authenticator.verify({ token, secret: pending.secret });
    if (!isValid) {
      throw new Error('Invalid verification code');
    }

    // Generate backup codes
    const backupCodes = this.generateBackupCodes();

    // Save MFA settings
    await this.mfaRepository.enable({
      userId: user.id,
      secret: this.encrypt(pending.secret),
      backupCodes: backupCodes.map(c => this.hashCode(c)),
    });

    return backupCodes;
  }

  // Verify TOTP code
  async verifyMFA(user: User, token: string): Promise<boolean> {
    const mfa = await this.mfaRepository.findByUserId(user.id);
    if (!mfa) return false;

    const secret = this.decrypt(mfa.secret);

    // Check TOTP with time window
    return authenticator.verify({
      token,
      secret,
      window: 1, // Allow 1 step before/after
    });
  }

  private generateBackupCodes(): string[] {
    return Array.from({ length: 10 }, () =>
      crypto.randomBytes(4).toString('hex').toUpperCase()
    );
  }
}
```

### MFA Methods Comparison

| Method | Security | UX | Implementation |
|--------|----------|----|--------------------|
| TOTP | High | Medium | Authenticator apps |
| SMS | Medium | High | Carrier-dependent |
| Email | Medium | High | Delivery delays |
| WebAuthn | Very High | High | Hardware keys |
| Push | High | Very High | Mobile app required |

---

## Passwordless Authentication

### Magic Link Implementation

```typescript
export class PasswordlessService {
  async sendMagicLink(email: string): Promise<void> {
    const token = crypto.randomBytes(32).toString('hex');
    const expiresAt = new Date(Date.now() + 15 * 60 * 1000);

    await this.magicLinkRepository.save({
      email,
      tokenHash: this.hash(token),
      expiresAt,
    });

    const link = `${process.env.APP_URL}/auth/verify?token=${token}`;
    await this.emailService.send({
      to: email,
      subject: 'Your login link',
      html: `<a href="${link}">Click to login</a>`,
    });
  }

  async verifyMagicLink(token: string): Promise<User> {
    const stored = await this.magicLinkRepository.findByHash(this.hash(token));

    if (!stored || stored.expiresAt < new Date()) {
      throw new Error('Invalid or expired link');
    }

    // Delete used token
    await this.magicLinkRepository.delete(stored.id);

    // Find or create user
    return this.userService.findOrCreateByEmail(stored.email);
  }
}
```

### WebAuthn (Passkeys)

```typescript
import { generateRegistrationOptions, verifyRegistrationResponse } from '@simplewebauthn/server';

export class WebAuthnService {
  async generateRegistrationOptions(user: User) {
    return generateRegistrationOptions({
      rpName: 'My App',
      rpID: 'myapp.com',
      userID: user.id,
      userName: user.email,
      attestationType: 'none',
      authenticatorSelection: {
        residentKey: 'preferred',
        userVerification: 'preferred',
      },
    });
  }

  async verifyRegistration(user: User, response: RegistrationResponse) {
    const verification = await verifyRegistrationResponse({
      response,
      expectedChallenge: user.currentChallenge,
      expectedOrigin: 'https://myapp.com',
      expectedRPID: 'myapp.com',
    });

    if (verification.verified) {
      await this.credentialRepository.save({
        userId: user.id,
        credentialId: verification.registrationInfo.credentialID,
        publicKey: verification.registrationInfo.credentialPublicKey,
        counter: verification.registrationInfo.counter,
      });
    }

    return verification.verified;
  }
}
```

---

## Session Management

### Secure Session Configuration

```typescript
import session from 'express-session';
import RedisStore from 'connect-redis';

app.use(session({
  store: new RedisStore({ client: redisClient }),
  name: '__Host-session', // Secure cookie prefix
  secret: process.env.SESSION_SECRET!,
  resave: false,
  saveUninitialized: false,
  cookie: {
    httpOnly: true,
    secure: true, // HTTPS only
    sameSite: 'strict',
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    path: '/',
  },
  rolling: true, // Reset expiry on activity
}));
```

### Session Security Best Practices

| Practice | Description |
|----------|-------------|
| Regenerate on auth | New session ID after login |
| Secure cookies | HttpOnly, Secure, SameSite |
| Server-side storage | Don't store sensitive data client-side |
| Idle timeout | Expire inactive sessions |
| Absolute timeout | Maximum session lifetime |
| Single session | Invalidate old sessions on new login |

### Session Regeneration

```typescript
// Regenerate session after login
app.post('/login', async (req, res) => {
  const user = await authenticate(req.body);

  // Regenerate to prevent session fixation
  req.session.regenerate((err) => {
    if (err) return next(err);

    req.session.userId = user.id;
    req.session.loginTime = Date.now();

    res.json({ success: true });
  });
});

// Destroy session on logout
app.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    res.clearCookie('__Host-session');
    res.json({ success: true });
  });
});
```

---

## Best Practices Summary

| Category | Do | Don't |
|----------|-----|-------|
| Tokens | Short expiry, rotate refresh | Long-lived access tokens |
| Passwords | bcrypt/Argon2, 12+ rounds | MD5, SHA1, plain text |
| OAuth | PKCE, state validation | Implicit flow for SPAs |
| MFA | TOTP/WebAuthn | SMS as only factor |
| Sessions | Server-side, regenerate | Client-side storage |
