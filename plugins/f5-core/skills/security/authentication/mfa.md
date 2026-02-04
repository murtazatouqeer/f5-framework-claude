---
name: mfa
description: Multi-factor authentication implementation
category: security/authentication
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Multi-Factor Authentication (MFA)

## Overview

MFA requires users to provide multiple verification factors,
significantly reducing unauthorized access risk.

## Authentication Factors

| Factor Type | Description | Examples |
|-------------|-------------|----------|
| **Something you know** | Knowledge | Password, PIN, security questions |
| **Something you have** | Possession | Phone, hardware token, smart card |
| **Something you are** | Inherence | Fingerprint, face, voice |

## TOTP Implementation

### Schema

```typescript
// models/mfa.model.ts
interface MfaSetup {
  userId: string;
  secret: string;          // Base32 encoded secret
  enabled: boolean;
  verifiedAt?: Date;
  backupCodes: string[];   // Hashed backup codes
  createdAt: Date;
}

// Prisma schema
model MfaSetup {
  id          String   @id @default(cuid())
  userId      String   @unique
  user        User     @relation(fields: [userId], references: [id])
  secret      String   // Encrypted
  enabled     Boolean  @default(false)
  verifiedAt  DateTime?
  backupCodes String[] // Hashed
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

### MFA Service

```typescript
// services/mfa.service.ts
import { authenticator } from 'otplib';
import crypto from 'crypto';
import qrcode from 'qrcode';

export class MfaService {
  private readonly BACKUP_CODE_COUNT = 10;
  private readonly BACKUP_CODE_LENGTH = 8;
  private readonly APP_NAME = 'MyApp';

  constructor(
    private mfaRepository: MfaRepository,
    private encryptionService: EncryptionService
  ) {}

  // Step 1: Generate MFA setup
  async initializeSetup(user: User): Promise<MfaSetupResponse> {
    // Generate secret
    const secret = authenticator.generateSecret();

    // Generate backup codes
    const backupCodes = this.generateBackupCodes();
    const hashedBackupCodes = backupCodes.map(code => this.hashCode(code));

    // Generate QR code
    const otpauth = authenticator.keyuri(
      user.email,
      this.APP_NAME,
      secret
    );
    const qrCodeUrl = await qrcode.toDataURL(otpauth);

    // Store setup (not enabled yet)
    await this.mfaRepository.upsert({
      userId: user.id,
      secret: this.encryptionService.encrypt(secret),
      enabled: false,
      backupCodes: hashedBackupCodes,
    });

    return {
      secret,        // Show once for manual entry
      qrCodeUrl,     // For QR code scanning
      backupCodes,   // Show once, user must save
    };
  }

  // Step 2: Verify and enable MFA
  async verifyAndEnable(userId: string, code: string): Promise<boolean> {
    const setup = await this.mfaRepository.findByUserId(userId);
    if (!setup) {
      throw new Error('MFA not initialized');
    }

    const secret = this.encryptionService.decrypt(setup.secret);
    const isValid = authenticator.verify({ token: code, secret });

    if (!isValid) {
      throw new Error('Invalid verification code');
    }

    // Enable MFA
    await this.mfaRepository.update(userId, {
      enabled: true,
      verifiedAt: new Date(),
    });

    return true;
  }

  // Verify MFA code during login
  async verify(userId: string, code: string): Promise<boolean> {
    const setup = await this.mfaRepository.findByUserId(userId);
    if (!setup || !setup.enabled) {
      return true; // MFA not enabled
    }

    // Try TOTP code first
    const secret = this.encryptionService.decrypt(setup.secret);
    if (authenticator.verify({ token: code, secret })) {
      return true;
    }

    // Try backup code
    return this.verifyBackupCode(userId, code, setup.backupCodes);
  }

  // Use backup code (one-time)
  private async verifyBackupCode(
    userId: string,
    code: string,
    hashedCodes: string[]
  ): Promise<boolean> {
    const normalizedCode = code.replace(/\s/g, '').toLowerCase();
    const hashedInput = this.hashCode(normalizedCode);

    const index = hashedCodes.findIndex(hashed => hashed === hashedInput);
    if (index === -1) {
      return false;
    }

    // Remove used backup code
    hashedCodes.splice(index, 1);
    await this.mfaRepository.update(userId, { backupCodes: hashedCodes });

    // Warn if running low
    if (hashedCodes.length <= 2) {
      // Send notification to regenerate backup codes
    }

    return true;
  }

  // Regenerate backup codes
  async regenerateBackupCodes(userId: string, code: string): Promise<string[]> {
    // Require MFA verification
    const isValid = await this.verify(userId, code);
    if (!isValid) {
      throw new Error('Invalid verification code');
    }

    const backupCodes = this.generateBackupCodes();
    const hashedBackupCodes = backupCodes.map(code => this.hashCode(code));

    await this.mfaRepository.update(userId, {
      backupCodes: hashedBackupCodes,
    });

    return backupCodes;
  }

  // Disable MFA
  async disable(userId: string, code: string): Promise<void> {
    const isValid = await this.verify(userId, code);
    if (!isValid) {
      throw new Error('Invalid verification code');
    }

    await this.mfaRepository.delete(userId);
  }

  private generateBackupCodes(): string[] {
    const codes: string[] = [];
    for (let i = 0; i < this.BACKUP_CODE_COUNT; i++) {
      const code = crypto
        .randomBytes(this.BACKUP_CODE_LENGTH / 2)
        .toString('hex');
      codes.push(code);
    }
    return codes;
  }

  private hashCode(code: string): string {
    return crypto
      .createHash('sha256')
      .update(code.toLowerCase())
      .digest('hex');
  }
}
```

### MFA Routes

```typescript
// routes/mfa.routes.ts
router.post('/mfa/setup', requireAuth, async (req, res) => {
  const setup = await mfaService.initializeSetup(req.user);
  res.json(setup);
});

router.post('/mfa/verify', requireAuth, async (req, res) => {
  const { code } = req.body;
  await mfaService.verifyAndEnable(req.user.id, code);
  res.json({ message: 'MFA enabled successfully' });
});

router.post('/mfa/disable', requireAuth, async (req, res) => {
  const { code } = req.body;
  await mfaService.disable(req.user.id, code);
  res.json({ message: 'MFA disabled' });
});

router.post('/mfa/backup-codes', requireAuth, async (req, res) => {
  const { code } = req.body;
  const backupCodes = await mfaService.regenerateBackupCodes(req.user.id, code);
  res.json({ backupCodes });
});
```

### Login Flow with MFA

```typescript
// services/auth.service.ts
async function login(email: string, password: string, mfaCode?: string) {
  // Step 1: Verify credentials
  const user = await userRepository.findByEmail(email);
  if (!user || !await verifyPassword(password, user.passwordHash)) {
    throw new UnauthorizedError('Invalid credentials');
  }

  // Step 2: Check if MFA is required
  const mfaSetup = await mfaRepository.findByUserId(user.id);
  if (mfaSetup?.enabled) {
    if (!mfaCode) {
      // Return partial response indicating MFA needed
      return {
        mfaRequired: true,
        tempToken: generateTempToken(user.id), // Short-lived token for MFA step
      };
    }

    // Verify MFA code
    const isValid = await mfaService.verify(user.id, mfaCode);
    if (!isValid) {
      throw new UnauthorizedError('Invalid MFA code');
    }
  }

  // Step 3: Create session
  const session = await sessionService.create(user.id, {
    roles: user.roles,
    mfaVerified: true,
  });

  return {
    user: sanitizeUser(user),
    sessionId: session.id,
  };
}
```

## WebAuthn / Passkeys

```typescript
// services/webauthn.service.ts
import {
  generateRegistrationOptions,
  verifyRegistrationResponse,
  generateAuthenticationOptions,
  verifyAuthenticationResponse,
} from '@simplewebauthn/server';

export class WebAuthnService {
  private readonly rpName = 'My Application';
  private readonly rpID = 'myapp.com';
  private readonly origin = 'https://myapp.com';

  async generateRegistration(user: User) {
    const userAuthenticators = await this.getAuthenticators(user.id);

    const options = generateRegistrationOptions({
      rpName: this.rpName,
      rpID: this.rpID,
      userID: user.id,
      userName: user.email,
      userDisplayName: user.name,
      attestationType: 'none',
      excludeCredentials: userAuthenticators.map(auth => ({
        id: auth.credentialID,
        type: 'public-key',
        transports: auth.transports,
      })),
      authenticatorSelection: {
        residentKey: 'preferred',
        userVerification: 'preferred',
      },
    });

    // Store challenge
    await this.storeChallenge(user.id, options.challenge);

    return options;
  }

  async verifyRegistration(user: User, response: RegistrationResponseJSON) {
    const expectedChallenge = await this.getChallenge(user.id);

    const verification = await verifyRegistrationResponse({
      response,
      expectedChallenge,
      expectedOrigin: this.origin,
      expectedRPID: this.rpID,
    });

    if (verification.verified && verification.registrationInfo) {
      // Store authenticator
      await this.saveAuthenticator(user.id, {
        credentialID: verification.registrationInfo.credentialID,
        credentialPublicKey: verification.registrationInfo.credentialPublicKey,
        counter: verification.registrationInfo.counter,
        transports: response.response.transports,
      });
    }

    return verification.verified;
  }

  async generateAuthentication(user: User) {
    const userAuthenticators = await this.getAuthenticators(user.id);

    const options = generateAuthenticationOptions({
      rpID: this.rpID,
      allowCredentials: userAuthenticators.map(auth => ({
        id: auth.credentialID,
        type: 'public-key',
        transports: auth.transports,
      })),
      userVerification: 'preferred',
    });

    await this.storeChallenge(user.id, options.challenge);

    return options;
  }

  async verifyAuthentication(user: User, response: AuthenticationResponseJSON) {
    const expectedChallenge = await this.getChallenge(user.id);
    const authenticator = await this.getAuthenticatorById(
      response.id
    );

    const verification = await verifyAuthenticationResponse({
      response,
      expectedChallenge,
      expectedOrigin: this.origin,
      expectedRPID: this.rpID,
      authenticator,
    });

    if (verification.verified) {
      // Update counter
      await this.updateCounter(
        response.id,
        verification.authenticationInfo.newCounter
      );
    }

    return verification.verified;
  }
}
```

## SMS/Email OTP

```typescript
// services/otp.service.ts
export class OTPService {
  private readonly OTP_LENGTH = 6;
  private readonly OTP_EXPIRY = 5 * 60; // 5 minutes

  constructor(
    private redis: Redis,
    private smsService: SMSService,
    private emailService: EmailService
  ) {}

  async sendSMS(userId: string, phoneNumber: string): Promise<void> {
    const otp = this.generateOTP();
    await this.storeOTP(userId, otp, 'sms');
    await this.smsService.send(phoneNumber, `Your verification code is: ${otp}`);
  }

  async sendEmail(userId: string, email: string): Promise<void> {
    const otp = this.generateOTP();
    await this.storeOTP(userId, otp, 'email');
    await this.emailService.send(email, 'Verification Code', {
      template: 'otp',
      data: { otp },
    });
  }

  async verify(userId: string, otp: string, method: 'sms' | 'email'): Promise<boolean> {
    const key = `otp:${method}:${userId}`;
    const storedOTP = await this.redis.get(key);

    if (!storedOTP || storedOTP !== otp) {
      return false;
    }

    // Delete used OTP
    await this.redis.del(key);
    return true;
  }

  private generateOTP(): string {
    return crypto.randomInt(100000, 999999).toString();
  }

  private async storeOTP(userId: string, otp: string, method: string): Promise<void> {
    const key = `otp:${method}:${userId}`;
    await this.redis.setex(key, this.OTP_EXPIRY, otp);
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Multiple methods | Offer TOTP, WebAuthn, backup codes |
| Backup codes | Always provide recovery option |
| Rate limiting | Prevent brute force on MFA |
| Secure storage | Encrypt MFA secrets at rest |
| User education | Explain MFA benefits clearly |
| Grace period | Allow temporary MFA bypass for recovery |
