---
name: passwordless
description: Passwordless authentication methods
category: security/authentication
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Passwordless Authentication

## Overview

Passwordless authentication eliminates passwords in favor of
more secure and user-friendly methods.

## Authentication Methods

| Method | Security | UX | Implementation |
|--------|----------|----|-----------------|
| Magic Links | High | Good | Easy |
| WebAuthn/Passkeys | Very High | Excellent | Medium |
| SMS OTP | Medium | Good | Easy |
| Email OTP | Medium | Good | Easy |
| Push Notification | High | Excellent | Complex |

## Magic Links

### Implementation

```typescript
// services/magic-link.service.ts
import crypto from 'crypto';

interface MagicLinkToken {
  token: string;
  email: string;
  expiresAt: number;
  used: boolean;
}

export class MagicLinkService {
  private readonly TOKEN_LENGTH = 32;
  private readonly TOKEN_EXPIRY = 15 * 60 * 1000; // 15 minutes
  private readonly BASE_URL = process.env.APP_URL;

  constructor(
    private redis: Redis,
    private emailService: EmailService
  ) {}

  async sendMagicLink(email: string): Promise<void> {
    // Generate secure token
    const token = crypto.randomBytes(this.TOKEN_LENGTH).toString('hex');
    const expiresAt = Date.now() + this.TOKEN_EXPIRY;

    // Store token
    await this.redis.setex(
      `magic_link:${token}`,
      this.TOKEN_EXPIRY / 1000,
      JSON.stringify({ email, expiresAt, used: false })
    );

    // Generate magic link
    const magicLink = `${this.BASE_URL}/auth/verify?token=${token}`;

    // Send email
    await this.emailService.send(email, 'Sign in to MyApp', {
      template: 'magic-link',
      data: {
        link: magicLink,
        expiresIn: '15 minutes',
      },
    });
  }

  async verifyToken(token: string): Promise<string> {
    const key = `magic_link:${token}`;
    const data = await this.redis.get(key);

    if (!data) {
      throw new Error('Invalid or expired token');
    }

    const tokenData = JSON.parse(data) as MagicLinkToken;

    // Check if already used
    if (tokenData.used) {
      throw new Error('Token already used');
    }

    // Check expiration
    if (tokenData.expiresAt < Date.now()) {
      await this.redis.del(key);
      throw new Error('Token expired');
    }

    // Mark as used (prevent replay)
    tokenData.used = true;
    await this.redis.setex(
      key,
      60, // Keep for 1 minute to prevent concurrent use
      JSON.stringify(tokenData)
    );

    return tokenData.email;
  }
}
```

### Routes

```typescript
// routes/auth.routes.ts
router.post('/auth/magic-link', async (req, res) => {
  const { email } = req.body;

  // Rate limit
  const rateLimitKey = `magic_link_rate:${email}`;
  const attempts = await redis.incr(rateLimitKey);
  if (attempts === 1) {
    await redis.expire(rateLimitKey, 3600); // 1 hour window
  }
  if (attempts > 5) {
    return res.status(429).json({ error: 'Too many requests' });
  }

  // Always return success (prevent enumeration)
  await magicLinkService.sendMagicLink(email);
  res.json({ message: 'If an account exists, a magic link has been sent' });
});

router.get('/auth/verify', async (req, res) => {
  try {
    const { token } = req.query;
    const email = await magicLinkService.verifyToken(token as string);

    // Find or create user
    let user = await userRepository.findByEmail(email);
    if (!user) {
      user = await userRepository.create({ email, emailVerified: true });
    }

    // Create session
    const session = await sessionService.create(user.id, {});
    res.cookie('sessionId', session.id, cookieConfig);

    res.redirect('/dashboard');
  } catch (error) {
    res.redirect('/login?error=invalid_token');
  }
});
```

## Passkeys (WebAuthn)

### Registration Flow

```typescript
// Frontend
async function registerPasskey() {
  // Get registration options from server
  const optionsResponse = await fetch('/api/webauthn/register/options');
  const options = await optionsResponse.json();

  // Create credential
  const credential = await navigator.credentials.create({
    publicKey: {
      ...options,
      challenge: base64ToBuffer(options.challenge),
      user: {
        ...options.user,
        id: base64ToBuffer(options.user.id),
      },
    },
  });

  // Send to server for verification
  await fetch('/api/webauthn/register/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: credential.id,
      rawId: bufferToBase64(credential.rawId),
      response: {
        clientDataJSON: bufferToBase64(credential.response.clientDataJSON),
        attestationObject: bufferToBase64(credential.response.attestationObject),
      },
      type: credential.type,
    }),
  });
}
```

### Authentication Flow

```typescript
// Frontend
async function authenticateWithPasskey() {
  // Get authentication options
  const optionsResponse = await fetch('/api/webauthn/authenticate/options');
  const options = await optionsResponse.json();

  // Get credential
  const credential = await navigator.credentials.get({
    publicKey: {
      ...options,
      challenge: base64ToBuffer(options.challenge),
      allowCredentials: options.allowCredentials?.map(cred => ({
        ...cred,
        id: base64ToBuffer(cred.id),
      })),
    },
  });

  // Verify with server
  const response = await fetch('/api/webauthn/authenticate/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      id: credential.id,
      rawId: bufferToBase64(credential.rawId),
      response: {
        clientDataJSON: bufferToBase64(credential.response.clientDataJSON),
        authenticatorData: bufferToBase64(credential.response.authenticatorData),
        signature: bufferToBase64(credential.response.signature),
        userHandle: credential.response.userHandle
          ? bufferToBase64(credential.response.userHandle)
          : null,
      },
      type: credential.type,
    }),
  });

  if (response.ok) {
    window.location.href = '/dashboard';
  }
}
```

### Backend

```typescript
// services/passkey.service.ts
import {
  generateRegistrationOptions,
  verifyRegistrationResponse,
  generateAuthenticationOptions,
  verifyAuthenticationResponse,
} from '@simplewebauthn/server';

export class PasskeyService {
  private readonly rpName = 'My Application';
  private readonly rpID = process.env.RP_ID!;
  private readonly origin = process.env.ORIGIN!;

  constructor(
    private credentialRepository: CredentialRepository,
    private redis: Redis
  ) {}

  async generateRegistrationOptions(user: User) {
    const existingCredentials = await this.credentialRepository.findByUserId(user.id);

    const options = await generateRegistrationOptions({
      rpName: this.rpName,
      rpID: this.rpID,
      userID: user.id,
      userName: user.email,
      attestationType: 'none',
      excludeCredentials: existingCredentials.map(cred => ({
        id: cred.credentialId,
        type: 'public-key',
        transports: cred.transports,
      })),
      authenticatorSelection: {
        residentKey: 'required',
        userVerification: 'required',
      },
    });

    // Store challenge
    await this.redis.setex(
      `webauthn_challenge:${user.id}`,
      300,
      options.challenge
    );

    return options;
  }

  async verifyRegistration(user: User, response: any) {
    const challenge = await this.redis.get(`webauthn_challenge:${user.id}`);
    if (!challenge) throw new Error('Challenge expired');

    const verification = await verifyRegistrationResponse({
      response,
      expectedChallenge: challenge,
      expectedOrigin: this.origin,
      expectedRPID: this.rpID,
    });

    if (verification.verified && verification.registrationInfo) {
      await this.credentialRepository.create({
        userId: user.id,
        credentialId: Buffer.from(verification.registrationInfo.credentialID),
        publicKey: Buffer.from(verification.registrationInfo.credentialPublicKey),
        counter: verification.registrationInfo.counter,
        transports: response.response.transports || [],
        deviceName: response.deviceName || 'Unknown Device',
      });
    }

    return verification.verified;
  }

  async generateAuthenticationOptions(email?: string) {
    let allowCredentials;

    if (email) {
      const user = await userRepository.findByEmail(email);
      if (user) {
        const credentials = await this.credentialRepository.findByUserId(user.id);
        allowCredentials = credentials.map(cred => ({
          id: cred.credentialId,
          type: 'public-key' as const,
          transports: cred.transports,
        }));
      }
    }

    const options = await generateAuthenticationOptions({
      rpID: this.rpID,
      allowCredentials,
      userVerification: 'required',
    });

    // Store challenge temporarily
    const challengeId = crypto.randomUUID();
    await this.redis.setex(`webauthn_auth_challenge:${challengeId}`, 300, options.challenge);

    return { ...options, challengeId };
  }

  async verifyAuthentication(challengeId: string, response: any) {
    const challenge = await this.redis.get(`webauthn_auth_challenge:${challengeId}`);
    if (!challenge) throw new Error('Challenge expired');

    const credential = await this.credentialRepository.findByCredentialId(
      Buffer.from(response.rawId, 'base64')
    );
    if (!credential) throw new Error('Credential not found');

    const verification = await verifyAuthenticationResponse({
      response,
      expectedChallenge: challenge,
      expectedOrigin: this.origin,
      expectedRPID: this.rpID,
      authenticator: {
        credentialID: credential.credentialId,
        credentialPublicKey: credential.publicKey,
        counter: credential.counter,
      },
    });

    if (verification.verified) {
      // Update counter
      await this.credentialRepository.updateCounter(
        credential.id,
        verification.authenticationInfo.newCounter
      );

      return credential.userId;
    }

    throw new Error('Authentication failed');
  }
}
```

## Push Notification Authentication

```typescript
// services/push-auth.service.ts
export class PushAuthService {
  constructor(
    private redis: Redis,
    private pushService: PushNotificationService,
    private deviceRepository: DeviceRepository
  ) {}

  async initiateAuth(userId: string): Promise<string> {
    const requestId = crypto.randomUUID();

    // Store pending request
    await this.redis.setex(
      `push_auth:${requestId}`,
      120, // 2 minutes
      JSON.stringify({
        userId,
        status: 'pending',
        createdAt: Date.now(),
      })
    );

    // Get user's devices
    const devices = await this.deviceRepository.findByUserId(userId);

    // Send push to all devices
    for (const device of devices) {
      await this.pushService.send(device.token, {
        title: 'Login Request',
        body: 'Approve this login request?',
        data: { type: 'auth_request', requestId },
      });
    }

    return requestId;
  }

  async respondToAuth(requestId: string, approved: boolean): Promise<void> {
    const key = `push_auth:${requestId}`;
    const data = await this.redis.get(key);

    if (!data) throw new Error('Request expired');

    const request = JSON.parse(data);
    request.status = approved ? 'approved' : 'denied';
    request.respondedAt = Date.now();

    await this.redis.setex(key, 60, JSON.stringify(request));
  }

  async checkAuthStatus(requestId: string): Promise<'pending' | 'approved' | 'denied' | 'expired'> {
    const data = await this.redis.get(`push_auth:${requestId}`);

    if (!data) return 'expired';

    const request = JSON.parse(data);
    return request.status;
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Token expiry | Short-lived tokens (15 min for magic links) |
| One-time use | Tokens can only be used once |
| Rate limiting | Prevent abuse of authentication endpoints |
| Fallback options | Provide backup authentication methods |
| Device management | Allow users to manage registered devices |
| Secure storage | Encrypt credentials at rest |
