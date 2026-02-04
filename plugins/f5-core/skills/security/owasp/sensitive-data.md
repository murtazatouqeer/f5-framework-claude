---
name: sensitive-data
description: Protecting sensitive data exposure
category: security/owasp
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Sensitive Data Protection

## Overview

Sensitive data exposure occurs when applications don't adequately
protect sensitive information like credentials, financial data,
or personal information.

## Data Classification

| Classification | Examples | Protection Level |
|----------------|----------|------------------|
| **Critical** | Passwords, API keys, encryption keys | Maximum |
| **Confidential** | PII, financial data, health records | High |
| **Internal** | Business data, internal documents | Medium |
| **Public** | Marketing materials, public APIs | Basic |

## Encryption at Rest

### Database Encryption

```typescript
// services/encryption.service.ts
import crypto from 'crypto';

export class EncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyLength = 32;
  private readonly ivLength = 12;
  private readonly tagLength = 16;

  constructor(private masterKey: string) {
    if (!masterKey || masterKey.length < 32) {
      throw new Error('Master key must be at least 32 characters');
    }
  }

  encrypt(plaintext: string): string {
    const iv = crypto.randomBytes(this.ivLength);
    const key = this.deriveKey(this.masterKey);

    const cipher = crypto.createCipheriv(this.algorithm, key, iv);
    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const tag = cipher.getAuthTag();

    // Format: iv:tag:ciphertext
    return `${iv.toString('hex')}:${tag.toString('hex')}:${encrypted}`;
  }

  decrypt(ciphertext: string): string {
    const parts = ciphertext.split(':');
    if (parts.length !== 3) {
      throw new Error('Invalid ciphertext format');
    }

    const [ivHex, tagHex, encrypted] = parts;
    const iv = Buffer.from(ivHex, 'hex');
    const tag = Buffer.from(tagHex, 'hex');
    const key = this.deriveKey(this.masterKey);

    const decipher = crypto.createDecipheriv(this.algorithm, key, iv);
    decipher.setAuthTag(tag);

    let decrypted = decipher.update(encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }

  private deriveKey(password: string): Buffer {
    // Use PBKDF2 for key derivation
    return crypto.pbkdf2Sync(
      password,
      'encryption-salt', // Should be environment-specific
      100000,
      this.keyLength,
      'sha256'
    );
  }
}

// Usage with Prisma middleware
prisma.$use(async (params, next) => {
  const encryptedFields = {
    User: ['ssn', 'dateOfBirth'],
    PaymentMethod: ['cardNumber', 'cvv'],
  };

  const modelFields = encryptedFields[params.model];
  if (!modelFields) return next(params);

  // Encrypt before create/update
  if (['create', 'update'].includes(params.action)) {
    for (const field of modelFields) {
      if (params.args.data?.[field]) {
        params.args.data[field] = encryption.encrypt(params.args.data[field]);
      }
    }
  }

  const result = await next(params);

  // Decrypt after read
  if (['findUnique', 'findFirst', 'findMany'].includes(params.action)) {
    const decrypt = (obj: any) => {
      if (!obj) return obj;
      for (const field of modelFields) {
        if (obj[field]) {
          obj[field] = encryption.decrypt(obj[field]);
        }
      }
      return obj;
    };

    if (Array.isArray(result)) {
      return result.map(decrypt);
    }
    return decrypt(result);
  }

  return result;
});
```

### File Encryption

```typescript
// services/file-encryption.service.ts
import crypto from 'crypto';
import { pipeline } from 'stream/promises';
import { createReadStream, createWriteStream } from 'fs';

export class FileEncryptionService {
  private readonly algorithm = 'aes-256-cbc';
  private readonly key: Buffer;

  constructor(encryptionKey: string) {
    this.key = crypto.scryptSync(encryptionKey, 'salt', 32);
  }

  async encryptFile(inputPath: string, outputPath: string): Promise<string> {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);

    const input = createReadStream(inputPath);
    const output = createWriteStream(outputPath);

    // Write IV at the beginning of the file
    output.write(iv);

    await pipeline(input, cipher, output);

    return outputPath;
  }

  async decryptFile(inputPath: string, outputPath: string): Promise<string> {
    const input = createReadStream(inputPath);

    // Read IV from the beginning
    const iv = await new Promise<Buffer>((resolve, reject) => {
      const chunks: Buffer[] = [];
      input.on('data', chunk => {
        chunks.push(chunk);
        if (Buffer.concat(chunks).length >= 16) {
          input.pause();
          resolve(Buffer.concat(chunks).slice(0, 16));
        }
      });
      input.on('error', reject);
    });

    const decipher = crypto.createDecipheriv(this.algorithm, this.key, iv);
    const output = createWriteStream(outputPath);

    // Skip IV bytes and decrypt rest
    const encryptedInput = createReadStream(inputPath, { start: 16 });

    await pipeline(encryptedInput, decipher, output);

    return outputPath;
  }
}
```

## Encryption in Transit

### HTTPS Configuration

```typescript
// server.ts
import https from 'https';
import fs from 'fs';
import express from 'express';

const app = express();

// Force HTTPS
app.use((req, res, next) => {
  if (!req.secure && process.env.NODE_ENV === 'production') {
    return res.redirect(301, `https://${req.headers.host}${req.url}`);
  }
  next();
});

// HSTS header
app.use((req, res, next) => {
  res.setHeader(
    'Strict-Transport-Security',
    'max-age=31536000; includeSubDomains; preload'
  );
  next();
});

// HTTPS server with strong TLS configuration
const httpsOptions = {
  key: fs.readFileSync('/path/to/private-key.pem'),
  cert: fs.readFileSync('/path/to/certificate.pem'),
  ca: fs.readFileSync('/path/to/ca-bundle.pem'),

  // TLS configuration
  minVersion: 'TLSv1.2',
  ciphers: [
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384',
  ].join(':'),
  honorCipherOrder: true,
};

https.createServer(httpsOptions, app).listen(443);
```

## Data Masking

```typescript
// services/data-masking.service.ts
export class DataMaskingService {
  // Mask email: j***@example.com
  maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    if (!domain) return '***';

    const maskedLocal = local[0] + '*'.repeat(Math.max(local.length - 1, 3));
    return `${maskedLocal}@${domain}`;
  }

  // Mask phone: ***-***-1234
  maskPhone(phone: string): string {
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 4) return '***';

    return '***-***-' + digits.slice(-4);
  }

  // Mask credit card: ****-****-****-1234
  maskCreditCard(cardNumber: string): string {
    const digits = cardNumber.replace(/\D/g, '');
    if (digits.length < 4) return '****';

    return '**** **** **** ' + digits.slice(-4);
  }

  // Mask SSN: ***-**-1234
  maskSSN(ssn: string): string {
    const digits = ssn.replace(/\D/g, '');
    if (digits.length < 4) return '***-**-****';

    return '***-**-' + digits.slice(-4);
  }

  // Mask name: J*** D**
  maskName(name: string): string {
    return name
      .split(' ')
      .map(part => part[0] + '*'.repeat(Math.max(part.length - 1, 2)))
      .join(' ');
  }

  // Generic field masking
  maskField(value: string, visibleChars: number = 4, position: 'start' | 'end' = 'end'): string {
    if (value.length <= visibleChars) {
      return '*'.repeat(value.length);
    }

    if (position === 'end') {
      return '*'.repeat(value.length - visibleChars) + value.slice(-visibleChars);
    } else {
      return value.slice(0, visibleChars) + '*'.repeat(value.length - visibleChars);
    }
  }
}

// Response transformer
export function maskSensitiveData(data: any, fields: string[]): any {
  if (!data) return data;

  const masker = new DataMaskingService();
  const result = { ...data };

  for (const field of fields) {
    if (result[field]) {
      switch (field) {
        case 'email':
          result[field] = masker.maskEmail(result[field]);
          break;
        case 'phone':
        case 'phoneNumber':
          result[field] = masker.maskPhone(result[field]);
          break;
        case 'creditCard':
        case 'cardNumber':
          result[field] = masker.maskCreditCard(result[field]);
          break;
        case 'ssn':
        case 'socialSecurityNumber':
          result[field] = masker.maskSSN(result[field]);
          break;
        default:
          result[field] = masker.maskField(result[field]);
      }
    }
  }

  return result;
}
```

## Logging Security

```typescript
// services/secure-logger.service.ts
export class SecureLoggerService {
  private sensitivePatterns = [
    { pattern: /password["\s]*[:=]["\s]*["']?[\w\S]+["']?/gi, replacement: 'password=***' },
    { pattern: /bearer\s+[\w\-\.]+/gi, replacement: 'bearer ***' },
    { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, replacement: '[EMAIL]' },
    { pattern: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g, replacement: '[PHONE]' },
    { pattern: /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, replacement: '[CARD]' },
    { pattern: /\b\d{3}[-]?\d{2}[-]?\d{4}\b/g, replacement: '[SSN]' },
  ];

  sanitize(message: string | object): string {
    let text = typeof message === 'object' ? JSON.stringify(message) : message;

    for (const { pattern, replacement } of this.sensitivePatterns) {
      text = text.replace(pattern, replacement);
    }

    return text;
  }

  log(level: string, message: string | object, meta?: object) {
    const sanitizedMessage = this.sanitize(message);
    const sanitizedMeta = meta ? this.sanitize(meta) : undefined;

    // Use your logging library
    console.log(JSON.stringify({
      level,
      message: sanitizedMessage,
      meta: sanitizedMeta,
      timestamp: new Date().toISOString(),
    }));
  }
}

// Middleware to sanitize request logging
export function requestLoggingMiddleware(logger: SecureLoggerService) {
  return (req: Request, res: Response, next: NextFunction) => {
    // Sanitize request body for logging
    const sanitizedBody = { ...req.body };

    // Remove sensitive fields entirely
    const sensitiveFields = ['password', 'token', 'secret', 'apiKey', 'creditCard'];
    for (const field of sensitiveFields) {
      if (sanitizedBody[field]) {
        sanitizedBody[field] = '[REDACTED]';
      }
    }

    logger.log('info', 'Request received', {
      method: req.method,
      url: req.url,
      body: sanitizedBody,
      ip: req.ip,
    });

    next();
  };
}
```

## Response Filtering

```typescript
// decorators/sensitive.decorator.ts
import 'reflect-metadata';

const SENSITIVE_FIELDS_KEY = 'sensitive_fields';

// Decorator to mark sensitive fields
export function Sensitive(): PropertyDecorator {
  return (target, propertyKey) => {
    const existingFields = Reflect.getMetadata(SENSITIVE_FIELDS_KEY, target) || [];
    Reflect.defineMetadata(
      SENSITIVE_FIELDS_KEY,
      [...existingFields, propertyKey],
      target
    );
  };
}

// DTO with sensitive fields
class UserResponseDto {
  id: string;
  email: string;
  name: string;

  @Sensitive()
  passwordHash: string;

  @Sensitive()
  ssn: string;
}

// Response interceptor
export function sanitizeResponse<T>(data: T, dtoClass: new () => T): Partial<T> {
  const sensitiveFields = Reflect.getMetadata(SENSITIVE_FIELDS_KEY, dtoClass.prototype) || [];
  const result = { ...data };

  for (const field of sensitiveFields) {
    delete result[field];
  }

  return result;
}

// Or use class-transformer
import { Exclude, Expose } from 'class-transformer';

class UserResponse {
  @Expose()
  id: string;

  @Expose()
  email: string;

  @Expose()
  name: string;

  @Exclude()
  passwordHash: string;

  @Exclude()
  ssn: string;
}
```

## Secure Data Deletion

```typescript
// services/data-deletion.service.ts
export class DataDeletionService {
  async softDelete(userId: string): Promise<void> {
    await prisma.user.update({
      where: { id: userId },
      data: {
        deletedAt: new Date(),
        email: `deleted_${userId}@deleted.local`,
        name: '[DELETED]',
        // Anonymize but keep record for audit
      },
    });
  }

  async hardDelete(userId: string): Promise<void> {
    // Delete related data first
    await prisma.$transaction([
      prisma.session.deleteMany({ where: { userId } }),
      prisma.loginHistory.deleteMany({ where: { userId } }),
      prisma.order.deleteMany({ where: { userId } }),
      prisma.user.delete({ where: { id: userId } }),
    ]);

    // Audit log the deletion
    await this.auditService.log('USER_DELETED', { userId });
  }

  async anonymize(userId: string): Promise<void> {
    const anonymousId = crypto.randomUUID();

    await prisma.user.update({
      where: { id: userId },
      data: {
        email: `anon_${anonymousId}@anon.local`,
        name: 'Anonymous User',
        phone: null,
        address: null,
        dateOfBirth: null,
        ssn: null,
        isAnonymized: true,
        anonymizedAt: new Date(),
      },
    });
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Classify data | Identify and classify sensitive data |
| Encrypt at rest | Encrypt sensitive data in database |
| Encrypt in transit | Use TLS 1.2+ for all connections |
| Mask output | Mask sensitive data in responses |
| Secure logging | Never log sensitive data |
| Secure deletion | Properly delete/anonymize data |
