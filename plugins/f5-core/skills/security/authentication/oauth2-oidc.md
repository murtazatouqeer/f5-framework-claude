---
name: oauth2-oidc
description: OAuth 2.0 and OpenID Connect implementation
category: security/authentication
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# OAuth 2.0 & OpenID Connect

## Overview

OAuth 2.0 is an authorization framework. OpenID Connect (OIDC) adds
authentication layer on top of OAuth 2.0.

## OAuth 2.0 vs OIDC

| Aspect | OAuth 2.0 | OpenID Connect |
|--------|-----------|----------------|
| Purpose | Authorization | Authentication |
| Token | Access Token | ID Token + Access Token |
| Scope | Custom | openid, profile, email |
| User Info | Not standardized | /userinfo endpoint |

## OAuth 2.0 Flows

### Authorization Code Flow (Recommended)

```
┌──────────┐                              ┌──────────────┐
│   User   │                              │    Client    │
└────┬─────┘                              └──────┬───────┘
     │                                           │
     │ 1. Click "Login with Google"              │
     │ ─────────────────────────────────────────>│
     │                                           │
     │ 2. Redirect to Authorization Server       │
     │ <─────────────────────────────────────────│
     │                                           │
     │                     ┌─────────────────────┴──────────────────────┐
     │                     │           Authorization Server             │
     │                     └─────────────────────┬──────────────────────┘
     │                                           │
     │ 3. User authenticates & consents          │
     │ ─────────────────────────────────────────>│
     │                                           │
     │ 4. Redirect with authorization code       │
     │ <─────────────────────────────────────────│
     │                                           │
     │                     ┌─────────────────────┴──────────────────────┐
     │                     │                 Client                     │
     │                     └─────────────────────┬──────────────────────┘
     │                                           │
     │ 5. Exchange code for tokens (server-side) │
     │                                           │
     │ 6. Return user session                    │
     │ <─────────────────────────────────────────│
```

### Implementation

```typescript
// config/oauth.config.ts
export const oauthConfig = {
  google: {
    clientId: process.env.GOOGLE_CLIENT_ID!,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    authorizationUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
    tokenUrl: 'https://oauth2.googleapis.com/token',
    userInfoUrl: 'https://www.googleapis.com/oauth2/v3/userinfo',
    scopes: ['openid', 'email', 'profile'],
    redirectUri: 'http://localhost:3000/api/auth/callback/google',
  },
  github: {
    clientId: process.env.GITHUB_CLIENT_ID!,
    clientSecret: process.env.GITHUB_CLIENT_SECRET!,
    authorizationUrl: 'https://github.com/login/oauth/authorize',
    tokenUrl: 'https://github.com/login/oauth/access_token',
    userInfoUrl: 'https://api.github.com/user',
    scopes: ['read:user', 'user:email'],
    redirectUri: 'http://localhost:3000/api/auth/callback/github',
  },
};

// services/oauth.service.ts
import crypto from 'crypto';

export class OAuthService {
  private stateStore = new Map<string, { expiresAt: number; codeVerifier?: string }>();

  // Step 1: Generate authorization URL
  generateAuthUrl(provider: 'google' | 'github'): { url: string; state: string } {
    const config = oauthConfig[provider];

    // Generate state for CSRF protection
    const state = crypto.randomBytes(32).toString('hex');

    // Generate PKCE code verifier and challenge
    const codeVerifier = crypto.randomBytes(32).toString('base64url');
    const codeChallenge = crypto
      .createHash('sha256')
      .update(codeVerifier)
      .digest('base64url');

    // Store state and verifier
    this.stateStore.set(state, {
      expiresAt: Date.now() + 10 * 60 * 1000, // 10 minutes
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

    return {
      url: `${config.authorizationUrl}?${params}`,
      state,
    };
  }

  // Step 2: Handle callback and exchange code
  async handleCallback(
    provider: 'google' | 'github',
    code: string,
    state: string
  ): Promise<OAuthTokens> {
    const config = oauthConfig[provider];

    // Verify state
    const storedState = this.stateStore.get(state);
    if (!storedState || storedState.expiresAt < Date.now()) {
      throw new Error('Invalid or expired state');
    }
    this.stateStore.delete(state);

    // Exchange code for tokens
    const tokenResponse = await fetch(config.tokenUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        Accept: 'application/json',
      },
      body: new URLSearchParams({
        client_id: config.clientId,
        client_secret: config.clientSecret,
        code,
        grant_type: 'authorization_code',
        redirect_uri: config.redirectUri,
        code_verifier: storedState.codeVerifier!,
      }),
    });

    if (!tokenResponse.ok) {
      throw new Error('Token exchange failed');
    }

    return tokenResponse.json();
  }

  // Step 3: Get user info
  async getUserInfo(provider: 'google' | 'github', accessToken: string): Promise<OAuthUser> {
    const config = oauthConfig[provider];

    const response = await fetch(config.userInfoUrl, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to fetch user info');
    }

    const data = await response.json();

    // Normalize user data
    if (provider === 'google') {
      return {
        id: data.sub,
        email: data.email,
        emailVerified: data.email_verified,
        name: data.name,
        picture: data.picture,
        provider: 'google',
      };
    }

    // GitHub
    return {
      id: data.id.toString(),
      email: data.email,
      emailVerified: true, // GitHub emails are verified
      name: data.name || data.login,
      picture: data.avatar_url,
      provider: 'github',
    };
  }
}
```

### Route Handlers

```typescript
// routes/auth.routes.ts
import { Router } from 'express';

const router = Router();
const oauthService = new OAuthService();
const authService = new AuthService();

// Initiate OAuth flow
router.get('/login/:provider', (req, res) => {
  const provider = req.params.provider as 'google' | 'github';
  const { url, state } = oauthService.generateAuthUrl(provider);

  // Store state in session for verification
  req.session.oauthState = state;

  res.redirect(url);
});

// OAuth callback
router.get('/callback/:provider', async (req, res) => {
  try {
    const provider = req.params.provider as 'google' | 'github';
    const { code, state, error } = req.query;

    if (error) {
      return res.redirect('/login?error=oauth_denied');
    }

    // Verify state
    if (state !== req.session.oauthState) {
      return res.redirect('/login?error=invalid_state');
    }

    // Exchange code for tokens
    const tokens = await oauthService.handleCallback(
      provider,
      code as string,
      state as string
    );

    // Get user info
    const oauthUser = await oauthService.getUserInfo(
      provider,
      tokens.access_token
    );

    // Find or create user
    const user = await authService.findOrCreateOAuthUser(oauthUser);

    // Generate session
    const session = await authService.createSession(user);

    // Set session cookie
    res.cookie('sessionId', session.id, {
      httpOnly: true,
      secure: true,
      sameSite: 'lax',
    });

    res.redirect('/dashboard');
  } catch (error) {
    console.error('OAuth callback error:', error);
    res.redirect('/login?error=oauth_failed');
  }
});

export default router;
```

## OpenID Connect

### ID Token Verification

```typescript
// services/oidc.service.ts
import jwt from 'jsonwebtoken';
import jwksClient from 'jwks-rsa';

export class OIDCService {
  private jwksClients: Map<string, jwksClient.JwksClient> = new Map();

  constructor() {
    // Initialize JWKS clients for providers
    this.jwksClients.set(
      'google',
      jwksClient({
        jwksUri: 'https://www.googleapis.com/oauth2/v3/certs',
        cache: true,
        rateLimit: true,
      })
    );
  }

  async verifyIdToken(provider: string, idToken: string): Promise<IdTokenPayload> {
    const client = this.jwksClients.get(provider);
    if (!client) {
      throw new Error(`Unknown provider: ${provider}`);
    }

    // Get signing key
    const getKey = (header: jwt.JwtHeader, callback: jwt.SigningKeyCallback) => {
      client.getSigningKey(header.kid, (err, key) => {
        if (err) return callback(err);
        callback(null, key?.getPublicKey());
      });
    };

    return new Promise((resolve, reject) => {
      jwt.verify(
        idToken,
        getKey,
        {
          algorithms: ['RS256'],
          audience: oauthConfig.google.clientId,
          issuer: ['https://accounts.google.com', 'accounts.google.com'],
        },
        (err, decoded) => {
          if (err) reject(err);
          else resolve(decoded as IdTokenPayload);
        }
      );
    });
  }
}
```

## PKCE (Proof Key for Code Exchange)

```typescript
// Always use PKCE for public clients (SPAs, mobile apps)

function generatePKCE() {
  // Generate code verifier (43-128 characters)
  const codeVerifier = crypto.randomBytes(32).toString('base64url');

  // Generate code challenge
  const codeChallenge = crypto
    .createHash('sha256')
    .update(codeVerifier)
    .digest('base64url');

  return { codeVerifier, codeChallenge };
}

// Include in authorization request
const authUrl = new URL(authorizationUrl);
authUrl.searchParams.set('code_challenge', codeChallenge);
authUrl.searchParams.set('code_challenge_method', 'S256');

// Include verifier in token request
const tokenParams = new URLSearchParams({
  code_verifier: codeVerifier,
  // ... other params
});
```

## Security Best Practices

| Practice | Description |
|----------|-------------|
| Use PKCE | Protect against code interception |
| Validate state | Prevent CSRF attacks |
| Verify ID tokens | Check signature, issuer, audience |
| Short-lived tokens | Access tokens expire quickly |
| Secure storage | Never store tokens in localStorage |
| Validate redirect URIs | Whitelist allowed URIs |

## Common Vulnerabilities

```typescript
// ❌ WRONG: No state parameter (CSRF vulnerable)
const authUrl = `${authorizationUrl}?client_id=${clientId}&redirect_uri=${redirectUri}`;

// ✅ CORRECT: Include state
const state = crypto.randomBytes(32).toString('hex');
const authUrl = `${authorizationUrl}?client_id=${clientId}&redirect_uri=${redirectUri}&state=${state}`;

// ❌ WRONG: Open redirect
const redirectUri = req.query.redirect_uri; // User controlled!

// ✅ CORRECT: Whitelist redirect URIs
const allowedRedirects = ['http://localhost:3000/callback', 'https://myapp.com/callback'];
if (!allowedRedirects.includes(redirectUri)) {
  throw new Error('Invalid redirect URI');
}

// ❌ WRONG: Not verifying ID token
const idToken = tokens.id_token;
const user = jwt.decode(idToken); // Just decoding, not verifying!

// ✅ CORRECT: Verify ID token
const user = await oidcService.verifyIdToken('google', idToken);
```
