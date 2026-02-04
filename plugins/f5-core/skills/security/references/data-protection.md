# Data Protection

Encryption, hashing, secrets management, and data privacy patterns.

## Table of Contents

1. [Encryption](#encryption)
2. [Hashing](#hashing)
3. [Secrets Management](#secrets-management)
4. [Key Management](#key-management)
5. [Data Masking](#data-masking)

---

## Encryption

### AES-256-GCM Encryption

```typescript
import crypto from 'crypto';

interface EncryptedData {
  ciphertext: string;
  iv: string;
  authTag: string;
}

export class EncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyLength = 32; // 256 bits
  private readonly ivLength = 12; // 96 bits for GCM

  constructor(private key: Buffer) {
    if (key.length !== this.keyLength) {
      throw new Error('Key must be 32 bytes (256 bits)');
    }
  }

  encrypt(plaintext: string): EncryptedData {
    const iv = crypto.randomBytes(this.ivLength);
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);

    let ciphertext = cipher.update(plaintext, 'utf8', 'base64');
    ciphertext += cipher.final('base64');

    return {
      ciphertext,
      iv: iv.toString('base64'),
      authTag: cipher.getAuthTag().toString('base64'),
    };
  }

  decrypt(encrypted: EncryptedData): string {
    const iv = Buffer.from(encrypted.iv, 'base64');
    const authTag = Buffer.from(encrypted.authTag, 'base64');
    const decipher = crypto.createDecipheriv(this.algorithm, this.key, iv);
    decipher.setAuthTag(authTag);

    let plaintext = decipher.update(encrypted.ciphertext, 'base64', 'utf8');
    plaintext += decipher.final('utf8');

    return plaintext;
  }
}

// Key generation
function generateEncryptionKey(): Buffer {
  return crypto.randomBytes(32);
}

// Key derivation from password
async function deriveKey(password: string, salt: Buffer): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    crypto.pbkdf2(password, salt, 100000, 32, 'sha256', (err, key) => {
      if (err) reject(err);
      else resolve(key);
    });
  });
}
```

### Field-Level Encryption

```typescript
import { EncryptionService } from './encryption';

interface EncryptedField {
  __encrypted: true;
  data: EncryptedData;
}

export class FieldEncryptor {
  constructor(private encryption: EncryptionService) {}

  encryptFields<T extends object>(
    data: T,
    fieldsToEncrypt: (keyof T)[]
  ): T {
    const result = { ...data };

    for (const field of fieldsToEncrypt) {
      if (result[field] !== undefined) {
        const value = String(result[field]);
        (result as any)[field] = {
          __encrypted: true,
          data: this.encryption.encrypt(value),
        } as EncryptedField;
      }
    }

    return result;
  }

  decryptFields<T extends object>(
    data: T,
    fieldsToDecrypt: (keyof T)[]
  ): T {
    const result = { ...data };

    for (const field of fieldsToDecrypt) {
      const value = result[field] as unknown as EncryptedField;
      if (value?.__encrypted) {
        (result as any)[field] = this.encryption.decrypt(value.data);
      }
    }

    return result;
  }
}

// Usage with Prisma middleware
prisma.$use(async (params, next) => {
  const sensitiveFields = ['ssn', 'creditCard', 'taxId'];

  if (params.action === 'create' || params.action === 'update') {
    params.args.data = fieldEncryptor.encryptFields(
      params.args.data,
      sensitiveFields
    );
  }

  const result = await next(params);

  if (result && (params.action === 'findUnique' || params.action === 'findFirst')) {
    return fieldEncryptor.decryptFields(result, sensitiveFields);
  }

  return result;
});
```

### Envelope Encryption

```typescript
// Encrypt data with data key, encrypt data key with master key
export class EnvelopeEncryption {
  constructor(private masterKey: Buffer) {}

  encrypt(plaintext: string): {
    encryptedData: EncryptedData;
    encryptedDataKey: EncryptedData;
  } {
    // Generate random data encryption key (DEK)
    const dataKey = crypto.randomBytes(32);

    // Encrypt data with DEK
    const dataEncryption = new EncryptionService(dataKey);
    const encryptedData = dataEncryption.encrypt(plaintext);

    // Encrypt DEK with master key (KEK)
    const keyEncryption = new EncryptionService(this.masterKey);
    const encryptedDataKey = keyEncryption.encrypt(dataKey.toString('base64'));

    return { encryptedData, encryptedDataKey };
  }

  decrypt(
    encryptedData: EncryptedData,
    encryptedDataKey: EncryptedData
  ): string {
    // Decrypt DEK with master key
    const keyEncryption = new EncryptionService(this.masterKey);
    const dataKeyBase64 = keyEncryption.decrypt(encryptedDataKey);
    const dataKey = Buffer.from(dataKeyBase64, 'base64');

    // Decrypt data with DEK
    const dataEncryption = new EncryptionService(dataKey);
    return dataEncryption.decrypt(encryptedData);
  }
}
```

---

## Hashing

### Password Hashing

```typescript
import bcrypt from 'bcrypt';
import argon2 from 'argon2';

// bcrypt - widely supported
export class BcryptHasher {
  private readonly saltRounds = 12;

  async hash(password: string): Promise<string> {
    return bcrypt.hash(password, this.saltRounds);
  }

  async verify(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }
}

// Argon2id - memory-hard, recommended for new projects
export class Argon2Hasher {
  async hash(password: string): Promise<string> {
    return argon2.hash(password, {
      type: argon2.argon2id,
      memoryCost: 65536, // 64 MB
      timeCost: 3,
      parallelism: 4,
    });
  }

  async verify(password: string, hash: string): Promise<boolean> {
    return argon2.verify(hash, password);
  }
}

// Password strength validation
import zxcvbn from 'zxcvbn';

function validatePasswordStrength(password: string): {
  valid: boolean;
  score: number;
  feedback: string[];
} {
  const result = zxcvbn(password);

  return {
    valid: result.score >= 3,
    score: result.score,
    feedback: [
      ...result.feedback.suggestions,
      result.feedback.warning,
    ].filter(Boolean),
  };
}
```

### Data Integrity Hashing

```typescript
import crypto from 'crypto';

// SHA-256 for data integrity
function hashData(data: string | Buffer): string {
  return crypto.createHash('sha256').update(data).digest('hex');
}

// HMAC for authenticated hashing
function hmacSign(data: string, secret: string): string {
  return crypto.createHmac('sha256', secret).update(data).digest('hex');
}

function hmacVerify(data: string, signature: string, secret: string): boolean {
  const expected = hmacSign(data, secret);
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(expected)
  );
}

// Checksum for file integrity
async function fileChecksum(filePath: string): Promise<string> {
  const hash = crypto.createHash('sha256');
  const stream = fs.createReadStream(filePath);

  return new Promise((resolve, reject) => {
    stream.on('data', (data) => hash.update(data));
    stream.on('end', () => resolve(hash.digest('hex')));
    stream.on('error', reject);
  });
}
```

### Token Generation

```typescript
import crypto from 'crypto';

// Secure random token
function generateSecureToken(length: number = 32): string {
  return crypto.randomBytes(length).toString('hex');
}

// URL-safe token
function generateUrlSafeToken(length: number = 32): string {
  return crypto.randomBytes(length).toString('base64url');
}

// Numeric OTP
function generateOTP(digits: number = 6): string {
  const max = Math.pow(10, digits);
  const randomInt = crypto.randomInt(0, max);
  return randomInt.toString().padStart(digits, '0');
}

// API key with prefix
function generateApiKey(prefix: string = 'sk'): string {
  const token = crypto.randomBytes(24).toString('base64url');
  return `${prefix}_${token}`;
}
```

---

## Secrets Management

### Environment Variables

```typescript
import { z } from 'zod';

// Validate required secrets at startup
const envSchema = z.object({
  JWT_ACCESS_SECRET: z.string().min(32),
  JWT_REFRESH_SECRET: z.string().min(32),
  DATABASE_URL: z.string().url(),
  ENCRYPTION_KEY: z.string().length(64), // 32 bytes hex
  REDIS_PASSWORD: z.string().optional(),
});

function validateEnv(): z.infer<typeof envSchema> {
  const result = envSchema.safeParse(process.env);

  if (!result.success) {
    console.error('Missing or invalid environment variables:');
    console.error(result.error.format());
    process.exit(1);
  }

  return result.data;
}

const env = validateEnv();

// Never log secrets
console.log('Config loaded:', {
  databaseHost: new URL(env.DATABASE_URL).hostname,
  jwtConfigured: !!env.JWT_ACCESS_SECRET,
  encryptionConfigured: !!env.ENCRYPTION_KEY,
});
```

### AWS Secrets Manager

```typescript
import {
  SecretsManagerClient,
  GetSecretValueCommand,
} from '@aws-sdk/client-secrets-manager';

export class SecretsManager {
  private client: SecretsManagerClient;
  private cache = new Map<string, { value: string; expiresAt: number }>();
  private cacheTTL = 5 * 60 * 1000; // 5 minutes

  constructor(region: string = 'us-east-1') {
    this.client = new SecretsManagerClient({ region });
  }

  async getSecret(secretId: string): Promise<string> {
    // Check cache
    const cached = this.cache.get(secretId);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.value;
    }

    // Fetch from AWS
    const command = new GetSecretValueCommand({ SecretId: secretId });
    const response = await this.client.send(command);

    if (!response.SecretString) {
      throw new Error(`Secret ${secretId} not found`);
    }

    // Cache result
    this.cache.set(secretId, {
      value: response.SecretString,
      expiresAt: Date.now() + this.cacheTTL,
    });

    return response.SecretString;
  }

  async getSecretJson<T>(secretId: string): Promise<T> {
    const secret = await this.getSecret(secretId);
    return JSON.parse(secret);
  }
}

// Usage
const secrets = new SecretsManager();
const dbCredentials = await secrets.getSecretJson<{
  username: string;
  password: string;
}>('prod/database/credentials');
```

### HashiCorp Vault

```typescript
import Vault from 'node-vault';

export class VaultClient {
  private vault: any;

  constructor(endpoint: string, token: string) {
    this.vault = Vault({
      apiVersion: 'v1',
      endpoint,
      token,
    });
  }

  async getSecret(path: string): Promise<Record<string, string>> {
    const result = await this.vault.read(path);
    return result.data.data;
  }

  async setSecret(path: string, data: Record<string, string>): Promise<void> {
    await this.vault.write(path, { data });
  }

  // Dynamic database credentials
  async getDatabaseCredentials(role: string): Promise<{
    username: string;
    password: string;
    ttl: number;
  }> {
    const result = await this.vault.read(`database/creds/${role}`);
    return {
      username: result.data.username,
      password: result.data.password,
      ttl: result.lease_duration,
    };
  }
}
```

---

## Key Management

### Key Rotation

```typescript
interface EncryptionKey {
  id: string;
  key: Buffer;
  createdAt: Date;
  expiresAt: Date;
  status: 'active' | 'rotating' | 'retired';
}

export class KeyManager {
  private keys: Map<string, EncryptionKey> = new Map();
  private activeKeyId: string | null = null;

  async rotateKey(): Promise<void> {
    // Generate new key
    const newKey: EncryptionKey = {
      id: crypto.randomUUID(),
      key: crypto.randomBytes(32),
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + 90 * 24 * 60 * 60 * 1000), // 90 days
      status: 'active',
    };

    // Mark old key as rotating
    if (this.activeKeyId) {
      const oldKey = this.keys.get(this.activeKeyId);
      if (oldKey) {
        oldKey.status = 'rotating';
      }
    }

    // Store and activate new key
    this.keys.set(newKey.id, newKey);
    this.activeKeyId = newKey.id;

    // Schedule re-encryption of data (background job)
    await this.scheduleReEncryption();
  }

  getActiveKey(): EncryptionKey {
    if (!this.activeKeyId) {
      throw new Error('No active key');
    }
    return this.keys.get(this.activeKeyId)!;
  }

  getKeyById(keyId: string): EncryptionKey | undefined {
    return this.keys.get(keyId);
  }

  private async scheduleReEncryption(): Promise<void> {
    // Queue background job to re-encrypt data with new key
    // Implementation depends on job queue (Bull, etc.)
  }
}

// Encrypted data includes key ID
interface EncryptedWithKeyId extends EncryptedData {
  keyId: string;
}

function encryptWithKeyId(
  plaintext: string,
  keyManager: KeyManager
): EncryptedWithKeyId {
  const activeKey = keyManager.getActiveKey();
  const encryption = new EncryptionService(activeKey.key);
  const encrypted = encryption.encrypt(plaintext);

  return {
    ...encrypted,
    keyId: activeKey.id,
  };
}
```

### Key Derivation

```typescript
import crypto from 'crypto';

// PBKDF2 for password-based key derivation
async function deriveKeyPBKDF2(
  password: string,
  salt: Buffer,
  iterations: number = 100000
): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    crypto.pbkdf2(password, salt, iterations, 32, 'sha256', (err, key) => {
      if (err) reject(err);
      else resolve(key);
    });
  });
}

// HKDF for key expansion
function deriveKeyHKDF(
  inputKey: Buffer,
  salt: Buffer,
  info: string,
  length: number = 32
): Buffer {
  return crypto.hkdfSync('sha256', inputKey, salt, info, length);
}

// Derive multiple keys from master
function deriveApplicationKeys(masterKey: Buffer): {
  encryptionKey: Buffer;
  authenticationKey: Buffer;
  signingKey: Buffer;
} {
  const salt = Buffer.alloc(32); // Empty salt for deterministic derivation

  return {
    encryptionKey: deriveKeyHKDF(masterKey, salt, 'encryption', 32),
    authenticationKey: deriveKeyHKDF(masterKey, salt, 'authentication', 32),
    signingKey: deriveKeyHKDF(masterKey, salt, 'signing', 32),
  };
}
```

---

## Data Masking

### PII Masking

```typescript
export class DataMasker {
  // Email: j***e@example.com
  maskEmail(email: string): string {
    const [local, domain] = email.split('@');
    if (local.length <= 2) {
      return `***@${domain}`;
    }
    return `${local[0]}***${local[local.length - 1]}@${domain}`;
  }

  // Phone: ***-***-1234
  maskPhone(phone: string): string {
    const digits = phone.replace(/\D/g, '');
    return '***-***-' + digits.slice(-4);
  }

  // Credit card: ****-****-****-1234
  maskCreditCard(number: string): string {
    const digits = number.replace(/\D/g, '');
    return '****-****-****-' + digits.slice(-4);
  }

  // SSN: ***-**-1234
  maskSSN(ssn: string): string {
    const digits = ssn.replace(/\D/g, '');
    return '***-**-' + digits.slice(-4);
  }

  // Name: J*** D***
  maskName(name: string): string {
    return name
      .split(' ')
      .map(part => part[0] + '***')
      .join(' ');
  }

  // Generic: mask all but last N characters
  maskGeneric(value: string, visibleChars: number = 4): string {
    if (value.length <= visibleChars) {
      return '*'.repeat(value.length);
    }
    const masked = '*'.repeat(value.length - visibleChars);
    return masked + value.slice(-visibleChars);
  }
}

// Auto-mask object fields
function maskSensitiveFields<T extends object>(
  obj: T,
  fieldMasks: Record<string, (value: string) => string>
): T {
  const result = { ...obj };
  const masker = new DataMasker();

  for (const [field, maskFn] of Object.entries(fieldMasks)) {
    if (field in result && typeof (result as any)[field] === 'string') {
      (result as any)[field] = maskFn((result as any)[field]);
    }
  }

  return result;
}

// Usage
const maskedUser = maskSensitiveFields(user, {
  email: (v) => masker.maskEmail(v),
  phone: (v) => masker.maskPhone(v),
  ssn: (v) => masker.maskSSN(v),
});
```

### Logging Sanitization

```typescript
const sensitivePatterns = [
  { pattern: /password["']?\s*[:=]\s*["']?[^"'\s,}]+/gi, replacement: 'password: [REDACTED]' },
  { pattern: /bearer\s+[a-zA-Z0-9._-]+/gi, replacement: 'Bearer [REDACTED]' },
  { pattern: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g, replacement: '[EMAIL]' },
  { pattern: /\b\d{3}-\d{2}-\d{4}\b/g, replacement: '[SSN]' },
  { pattern: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g, replacement: '[CARD]' },
];

export function sanitizeLogMessage(message: string): string {
  let sanitized = message;

  for (const { pattern, replacement } of sensitivePatterns) {
    sanitized = sanitized.replace(pattern, replacement);
  }

  return sanitized;
}

// Pino logger with sanitization
import pino from 'pino';

const logger = pino({
  hooks: {
    logMethod(inputArgs, method) {
      const [first, ...rest] = inputArgs;

      if (typeof first === 'string') {
        return method.apply(this, [sanitizeLogMessage(first), ...rest]);
      }

      if (typeof first === 'object') {
        return method.apply(this, [sanitizeObject(first), ...rest]);
      }

      return method.apply(this, inputArgs);
    },
  },
});

function sanitizeObject(obj: any): any {
  const sensitiveKeys = ['password', 'token', 'secret', 'apiKey', 'authorization'];

  if (typeof obj !== 'object' || obj === null) {
    return obj;
  }

  const result: any = Array.isArray(obj) ? [] : {};

  for (const [key, value] of Object.entries(obj)) {
    if (sensitiveKeys.some(k => key.toLowerCase().includes(k))) {
      result[key] = '[REDACTED]';
    } else if (typeof value === 'object') {
      result[key] = sanitizeObject(value);
    } else {
      result[key] = value;
    }
  }

  return result;
}
```

---

## Best Practices

| Category | Do | Don't |
|----------|-----|-------|
| Encryption | AES-256-GCM with random IV | ECB mode, fixed IV |
| Passwords | bcrypt/Argon2 with high cost | MD5, SHA1, plain text |
| Keys | Rotate regularly, use KMS | Hardcode in source |
| Secrets | Environment variables, Vault | Config files in repo |
| Logging | Sanitize sensitive data | Log passwords/tokens |
| Transmission | TLS 1.3, certificate pinning | HTTP, self-signed certs |
