---
name: broken-auth
description: Preventing broken authentication vulnerabilities
category: security/owasp
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Broken Authentication Prevention

## Overview

Broken authentication allows attackers to compromise passwords, keys,
or session tokens to assume other users' identities.

## Common Vulnerabilities

| Vulnerability | Risk | Prevention |
|---------------|------|------------|
| Weak passwords | High | Password policies |
| Credential stuffing | High | Rate limiting, breach detection |
| Session hijacking | High | Secure cookies, regeneration |
| Brute force | Medium | Account lockout, CAPTCHA |
| Insecure password recovery | High | Secure reset flow |
| Missing MFA | Medium | Implement MFA |

## Password Security

### Password Hashing

```typescript
// ✅ Use bcrypt or argon2
import bcrypt from 'bcrypt';
import argon2 from 'argon2';

const BCRYPT_ROUNDS = 12;

// Bcrypt (recommended)
async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, BCRYPT_ROUNDS);
}

async function verifyPassword(password: string, hash: string): Promise<boolean> {
  return bcrypt.compare(password, hash);
}

// Argon2 (more secure, newer)
async function hashPasswordArgon2(password: string): Promise<string> {
  return argon2.hash(password, {
    type: argon2.argon2id,
    memoryCost: 65536,    // 64 MB
    timeCost: 3,
    parallelism: 4,
  });
}

async function verifyPasswordArgon2(password: string, hash: string): Promise<boolean> {
  return argon2.verify(hash, password);
}

// ❌ NEVER do this
function badHash(password: string): string {
  // MD5 is broken
  return crypto.createHash('md5').update(password).digest('hex');
}
```

### Password Policies

```typescript
// validation/password.validation.ts
import { z } from 'zod';
import zxcvbn from 'zxcvbn';

export const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .max(128, 'Password must be less than 128 characters')
  .refine(
    (password) => /[a-z]/.test(password),
    'Password must contain a lowercase letter'
  )
  .refine(
    (password) => /[A-Z]/.test(password),
    'Password must contain an uppercase letter'
  )
  .refine(
    (password) => /\d/.test(password),
    'Password must contain a number'
  )
  .refine(
    (password) => /[!@#$%^&*(),.?":{}|<>]/.test(password),
    'Password must contain a special character'
  )
  .refine(
    (password) => {
      const result = zxcvbn(password);
      return result.score >= 3; // 0-4 scale
    },
    'Password is too weak'
  );

// Check against breached passwords
import { pwnedPassword } from 'hibp';

async function isPasswordBreached(password: string): Promise<boolean> {
  const count = await pwnedPassword(password);
  return count > 0;
}

// Full password validation
async function validatePassword(password: string): Promise<ValidationResult> {
  try {
    passwordSchema.parse(password);
  } catch (error) {
    return { valid: false, errors: error.errors };
  }

  if (await isPasswordBreached(password)) {
    return {
      valid: false,
      errors: ['This password has appeared in a data breach. Please choose a different password.'],
    };
  }

  return { valid: true, errors: [] };
}
```

## Brute Force Protection

### Rate Limiting

```typescript
// middleware/rate-limit.middleware.ts
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';

// General API rate limit
export const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  standardHeaders: true,
  legacyHeaders: false,
});

// Strict limit for authentication endpoints
export const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 5, // 5 attempts per window
  skipSuccessfulRequests: true, // Don't count successful logins
  store: new RedisStore({
    client: redisClient,
    prefix: 'rl:auth:',
  }),
  handler: (req, res) => {
    res.status(429).json({
      error: 'Too many login attempts. Please try again later.',
      retryAfter: Math.ceil(req.rateLimit.resetTime / 1000),
    });
  },
});

// Per-user rate limiting
export class UserRateLimiter {
  constructor(private redis: Redis) {}

  async checkLimit(userId: string, action: string): Promise<boolean> {
    const key = `rate:${action}:${userId}`;
    const limit = this.getLimitForAction(action);

    const current = await this.redis.incr(key);
    if (current === 1) {
      await this.redis.expire(key, limit.windowSeconds);
    }

    return current <= limit.maxRequests;
  }

  private getLimitForAction(action: string) {
    const limits: Record<string, { maxRequests: number; windowSeconds: number }> = {
      login: { maxRequests: 5, windowSeconds: 900 },
      passwordReset: { maxRequests: 3, windowSeconds: 3600 },
      mfaVerify: { maxRequests: 5, windowSeconds: 300 },
    };
    return limits[action] || { maxRequests: 100, windowSeconds: 60 };
  }
}
```

### Account Lockout

```typescript
// services/account-security.service.ts
export class AccountSecurityService {
  private readonly MAX_FAILED_ATTEMPTS = 5;
  private readonly LOCKOUT_DURATION = 30 * 60 * 1000; // 30 minutes
  private readonly PROGRESSIVE_DELAYS = [0, 1000, 2000, 5000, 10000]; // ms

  constructor(
    private userRepository: UserRepository,
    private redis: Redis,
    private notificationService: NotificationService
  ) {}

  async recordFailedAttempt(userId: string, ipAddress: string): Promise<void> {
    const key = `failed_attempts:${userId}`;

    const attempts = await this.redis.incr(key);
    if (attempts === 1) {
      await this.redis.expire(key, 3600); // 1 hour window
    }

    // Log for security monitoring
    await this.logSecurityEvent({
      type: 'FAILED_LOGIN',
      userId,
      ipAddress,
      attempts,
    });

    // Lock account after max attempts
    if (attempts >= this.MAX_FAILED_ATTEMPTS) {
      await this.lockAccount(userId);
      await this.notificationService.sendAccountLockNotification(userId);
    }
  }

  async lockAccount(userId: string): Promise<void> {
    await this.userRepository.update(userId, {
      lockedUntil: new Date(Date.now() + this.LOCKOUT_DURATION),
      lockReason: 'Too many failed login attempts',
    });
  }

  async isAccountLocked(userId: string): Promise<boolean> {
    const user = await this.userRepository.findById(userId);
    if (!user.lockedUntil) return false;
    return user.lockedUntil > new Date();
  }

  async clearFailedAttempts(userId: string): Promise<void> {
    await this.redis.del(`failed_attempts:${userId}`);
  }

  async getProgressiveDelay(userId: string): Promise<number> {
    const attempts = await this.redis.get(`failed_attempts:${userId}`);
    const index = Math.min(parseInt(attempts || '0'), this.PROGRESSIVE_DELAYS.length - 1);
    return this.PROGRESSIVE_DELAYS[index];
  }
}
```

## Secure Password Reset

```typescript
// services/password-reset.service.ts
export class PasswordResetService {
  private readonly TOKEN_EXPIRY = 60 * 60 * 1000; // 1 hour

  constructor(
    private userRepository: UserRepository,
    private emailService: EmailService,
    private redis: Redis
  ) {}

  async initiateReset(email: string): Promise<void> {
    const user = await this.userRepository.findByEmail(email);

    // Always respond with success to prevent enumeration
    if (!user) {
      return;
    }

    // Generate secure token
    const token = crypto.randomBytes(32).toString('hex');
    const hashedToken = crypto
      .createHash('sha256')
      .update(token)
      .digest('hex');

    // Store hashed token
    await this.redis.setex(
      `password_reset:${hashedToken}`,
      3600, // 1 hour
      JSON.stringify({
        userId: user.id,
        createdAt: Date.now(),
      })
    );

    // Invalidate previous tokens for this user
    await this.invalidatePreviousTokens(user.id);

    // Send email with plain token
    const resetUrl = `${process.env.APP_URL}/reset-password?token=${token}`;
    await this.emailService.send(user.email, 'Password Reset Request', {
      template: 'password-reset',
      data: {
        name: user.name,
        resetUrl,
        expiresIn: '1 hour',
      },
    });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    // Hash the token to look up
    const hashedToken = crypto
      .createHash('sha256')
      .update(token)
      .digest('hex');

    const data = await this.redis.get(`password_reset:${hashedToken}`);
    if (!data) {
      throw new Error('Invalid or expired reset token');
    }

    const { userId, createdAt } = JSON.parse(data);

    // Check expiration
    if (Date.now() - createdAt > this.TOKEN_EXPIRY) {
      await this.redis.del(`password_reset:${hashedToken}`);
      throw new Error('Reset token has expired');
    }

    // Validate new password
    const validation = await validatePassword(newPassword);
    if (!validation.valid) {
      throw new Error(validation.errors.join(', '));
    }

    // Update password
    const hashedPassword = await hashPassword(newPassword);
    await this.userRepository.update(userId, {
      passwordHash: hashedPassword,
      passwordChangedAt: new Date(),
    });

    // Delete token
    await this.redis.del(`password_reset:${hashedToken}`);

    // Invalidate all sessions
    await this.sessionService.destroyAllUserSessions(userId);

    // Notify user
    const user = await this.userRepository.findById(userId);
    await this.emailService.send(user.email, 'Password Changed', {
      template: 'password-changed',
      data: { name: user.name },
    });
  }

  private async invalidatePreviousTokens(userId: string): Promise<void> {
    // Track user's reset tokens and delete them
    const pattern = 'password_reset:*';
    const keys = await this.redis.keys(pattern);

    for (const key of keys) {
      const data = await this.redis.get(key);
      if (data) {
        const { userId: tokenUserId } = JSON.parse(data);
        if (tokenUserId === userId) {
          await this.redis.del(key);
        }
      }
    }
  }
}
```

## Credential Stuffing Protection

```typescript
// services/breach-detection.service.ts
export class BreachDetectionService {
  constructor(
    private userRepository: UserRepository,
    private notificationService: NotificationService
  ) {}

  async checkCredentials(email: string, password: string): Promise<void> {
    // Check if this credential pair appears in known breaches
    const isBreached = await this.checkAgainstBreachDatabase(email, password);

    if (isBreached) {
      const user = await this.userRepository.findByEmail(email);
      if (user) {
        // Force password change
        await this.userRepository.update(user.id, {
          requirePasswordChange: true,
        });

        // Notify user
        await this.notificationService.sendBreachNotification(user);
      }

      throw new Error(
        'These credentials may have been compromised. Please reset your password.'
      );
    }
  }

  // Check login attempts against known malicious IPs/patterns
  async checkSuspiciousActivity(
    userId: string,
    ipAddress: string,
    userAgent: string
  ): Promise<RiskAssessment> {
    const risk: RiskAssessment = {
      score: 0,
      factors: [],
    };

    // Check for impossible travel
    const lastLogin = await this.getLastLogin(userId);
    if (lastLogin && this.isImpossibleTravel(lastLogin, ipAddress)) {
      risk.score += 50;
      risk.factors.push('impossible_travel');
    }

    // Check for known bad IP
    if (await this.isKnownBadIP(ipAddress)) {
      risk.score += 30;
      risk.factors.push('bad_ip');
    }

    // Check for unusual device
    if (await this.isUnusualDevice(userId, userAgent)) {
      risk.score += 20;
      risk.factors.push('unusual_device');
    }

    return risk;
  }
}
```

## Secure Login Flow

```typescript
// services/auth.service.ts
export class AuthService {
  async login(
    email: string,
    password: string,
    mfaCode?: string,
    context?: LoginContext
  ): Promise<LoginResult> {
    // 1. Validate input
    if (!email || !password) {
      throw new UnauthorizedError('Invalid credentials');
    }

    // 2. Find user
    const user = await this.userRepository.findByEmail(email.toLowerCase());

    // 3. Timing-safe response (prevent enumeration)
    if (!user) {
      await this.simulatePasswordHash(); // Constant-time response
      throw new UnauthorizedError('Invalid credentials');
    }

    // 4. Check account status
    if (await this.accountSecurityService.isAccountLocked(user.id)) {
      throw new UnauthorizedError('Account is locked. Please try again later.');
    }

    // 5. Apply progressive delay
    const delay = await this.accountSecurityService.getProgressiveDelay(user.id);
    if (delay > 0) {
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    // 6. Verify password
    const isValid = await verifyPassword(password, user.passwordHash);
    if (!isValid) {
      await this.accountSecurityService.recordFailedAttempt(user.id, context?.ipAddress);
      throw new UnauthorizedError('Invalid credentials');
    }

    // 7. Check MFA
    if (user.mfaEnabled) {
      if (!mfaCode) {
        return { requiresMfa: true, tempToken: this.generateTempToken(user.id) };
      }
      if (!await this.mfaService.verify(user.id, mfaCode)) {
        throw new UnauthorizedError('Invalid MFA code');
      }
    }

    // 8. Risk assessment
    const risk = await this.breachDetectionService.checkSuspiciousActivity(
      user.id,
      context?.ipAddress,
      context?.userAgent
    );

    if (risk.score > 50) {
      // Require additional verification
      return { requiresVerification: true, riskFactors: risk.factors };
    }

    // 9. Clear failed attempts
    await this.accountSecurityService.clearFailedAttempts(user.id);

    // 10. Create session
    const session = await this.sessionService.create(user.id, {});

    // 11. Log successful login
    await this.auditService.log('LOGIN_SUCCESS', user.id, context);

    return { user: sanitizeUser(user), sessionId: session.id };
  }

  private async simulatePasswordHash(): Promise<void> {
    // Simulate the time it takes to hash a password
    // Prevents timing attacks for user enumeration
    await bcrypt.hash('dummy', 12);
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Strong hashing | Use bcrypt/argon2 with high cost |
| Rate limiting | Limit login attempts |
| Account lockout | Lock after failed attempts |
| MFA | Require for sensitive accounts |
| Session security | Regenerate, timeout, secure cookies |
| Audit logging | Log all auth events |
