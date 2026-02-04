---
name: hashing
description: Cryptographic hashing for passwords and data integrity
category: security/data-protection
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Cryptographic Hashing

## Overview

Hashing transforms data into a fixed-size output (digest) that cannot
be reversed. Used for passwords, integrity verification, and data
deduplication.

## Hash vs Encryption

| Feature | Hashing | Encryption |
|---------|---------|------------|
| Reversible | No | Yes |
| Key required | No (salt for passwords) | Yes |
| Output size | Fixed | Variable |
| Use case | Verification | Confidentiality |

## Password Hashing

### bcrypt

```typescript
// services/password.service.ts
import bcrypt from 'bcrypt';

export class PasswordService {
  private readonly SALT_ROUNDS = 12; // Adjust based on server capability

  async hash(password: string): Promise<string> {
    return bcrypt.hash(password, this.SALT_ROUNDS);
  }

  async verify(password: string, hash: string): Promise<boolean> {
    return bcrypt.compare(password, hash);
  }

  // Check if hash needs rehashing (after increasing rounds)
  needsRehash(hash: string): boolean {
    const rounds = bcrypt.getRounds(hash);
    return rounds < this.SALT_ROUNDS;
  }
}

// Usage
const passwordService = new PasswordService();

// Hashing
const hash = await passwordService.hash('userPassword123');
// Result: $2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYWfYVjHGKBm

// Verification
const isValid = await passwordService.verify('userPassword123', hash);
```

### Argon2 (Recommended)

```typescript
// services/password-argon2.service.ts
import argon2 from 'argon2';

export class Argon2PasswordService {
  private readonly options: argon2.Options = {
    type: argon2.argon2id,    // Hybrid variant (recommended)
    memoryCost: 65536,         // 64 MB
    timeCost: 3,               // 3 iterations
    parallelism: 4,            // 4 threads
    hashLength: 32,            // 256 bits
  };

  async hash(password: string): Promise<string> {
    return argon2.hash(password, this.options);
  }

  async verify(password: string, hash: string): Promise<boolean> {
    try {
      return await argon2.verify(hash, password);
    } catch {
      return false;
    }
  }

  // Check if hash needs update
  needsRehash(hash: string): boolean {
    return argon2.needsRehash(hash, this.options);
  }
}

// Usage
const passwordService = new Argon2PasswordService();

// Hashing
const hash = await passwordService.hash('userPassword123');
// Result: $argon2id$v=19$m=65536,t=3,p=4$c29tZXNhbHQ$...

// Verification with auto-rehash
async function verifyAndRehash(
  password: string,
  hash: string,
  userId: string
): Promise<boolean> {
  const isValid = await passwordService.verify(password, hash);

  if (isValid && passwordService.needsRehash(hash)) {
    const newHash = await passwordService.hash(password);
    await updateUserHash(userId, newHash);
  }

  return isValid;
}
```

## Data Integrity Hashing

### SHA-256/SHA-3

```typescript
// services/hash.service.ts
import crypto from 'crypto';

export class HashService {
  // SHA-256 - most common
  sha256(data: string | Buffer): string {
    return crypto.createHash('sha256').update(data).digest('hex');
  }

  // SHA-3-256 - newer, quantum-resistant considerations
  sha3_256(data: string | Buffer): string {
    return crypto.createHash('sha3-256').update(data).digest('hex');
  }

  // SHA-512 - larger output, slightly more secure
  sha512(data: string | Buffer): string {
    return crypto.createHash('sha512').update(data).digest('hex');
  }

  // File hash
  async hashFile(filePath: string): Promise<string> {
    const hash = crypto.createHash('sha256');
    const stream = createReadStream(filePath);

    return new Promise((resolve, reject) => {
      stream.on('data', chunk => hash.update(chunk));
      stream.on('end', () => resolve(hash.digest('hex')));
      stream.on('error', reject);
    });
  }

  // Streaming hash for large data
  createHashStream(): crypto.Hash {
    return crypto.createHash('sha256');
  }
}

// Usage examples
const hashService = new HashService();

// String hashing
const hash = hashService.sha256('Hello, World!');
// Result: dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f

// File integrity
const fileHash = await hashService.hashFile('/path/to/file');
```

### HMAC (Hash-based Message Authentication)

```typescript
// services/hmac.service.ts
import crypto from 'crypto';

export class HMACService {
  constructor(private secret: string) {}

  // Create HMAC
  sign(data: string): string {
    return crypto
      .createHmac('sha256', this.secret)
      .update(data)
      .digest('hex');
  }

  // Verify HMAC (timing-safe)
  verify(data: string, signature: string): boolean {
    const expected = this.sign(data);
    const actual = Buffer.from(signature, 'hex');
    const expectedBuf = Buffer.from(expected, 'hex');

    if (actual.length !== expectedBuf.length) {
      return false;
    }

    return crypto.timingSafeEqual(actual, expectedBuf);
  }
}

// Usage for webhook verification
const hmac = new HMACService(process.env.WEBHOOK_SECRET!);

// Sign outgoing webhook
const payload = JSON.stringify(data);
const signature = hmac.sign(payload);

// Verify incoming webhook
app.post('/webhook', (req, res) => {
  const signature = req.headers['x-signature'];
  const payload = JSON.stringify(req.body);

  if (!hmac.verify(payload, signature)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  // Process webhook...
});
```

## Content-Addressable Storage

```typescript
// services/content-hash.service.ts
export class ContentHashService {
  private hashService = new HashService();

  // Generate content hash for deduplication
  getContentHash(content: Buffer): string {
    return this.hashService.sha256(content);
  }

  // Store file by content hash
  async storeByHash(content: Buffer): Promise<string> {
    const hash = this.getContentHash(content);
    const path = this.getPathForHash(hash);

    // Only write if doesn't exist (dedup)
    if (!await this.exists(path)) {
      await fs.promises.writeFile(path, content);
    }

    return hash;
  }

  // Retrieve by hash
  async retrieveByHash(hash: string): Promise<Buffer> {
    const path = this.getPathForHash(hash);
    return fs.promises.readFile(path);
  }

  // Convert hash to storage path (2 levels of directories)
  private getPathForHash(hash: string): string {
    // Example: abc123... -> /storage/ab/c1/abc123...
    return `/storage/${hash.slice(0, 2)}/${hash.slice(2, 4)}/${hash}`;
  }
}
```

## Token Generation

```typescript
// services/token.service.ts
import crypto from 'crypto';

export class SecureTokenService {
  // Generate secure random token
  generateToken(length: number = 32): string {
    return crypto.randomBytes(length).toString('hex');
  }

  // Generate URL-safe token
  generateUrlSafeToken(length: number = 32): string {
    return crypto.randomBytes(length).toString('base64url');
  }

  // Hash token for storage
  hashToken(token: string): string {
    return crypto.createHash('sha256').update(token).digest('hex');
  }

  // Generate and return both plain and hashed
  generateTokenPair(length: number = 32): { token: string; hashedToken: string } {
    const token = this.generateToken(length);
    const hashedToken = this.hashToken(token);
    return { token, hashedToken };
  }
}

// Usage for password reset
const tokenService = new SecureTokenService();

// Generate reset token
const { token, hashedToken } = tokenService.generateTokenPair();

// Store hashedToken in database
await db.passwordReset.create({
  userId,
  token: hashedToken,
  expiresAt: new Date(Date.now() + 3600000),
});

// Send plain token to user via email
sendEmail(userEmail, resetUrl + token);

// Verify reset token
const incomingHash = tokenService.hashToken(incomingToken);
const resetRecord = await db.passwordReset.findOne({
  token: incomingHash,
  expiresAt: { gt: new Date() },
});
```

## Fingerprinting

```typescript
// services/fingerprint.service.ts
export class FingerprintService {
  private hashService = new HashService();

  // Generate device fingerprint
  generateDeviceFingerprint(data: DeviceFingerprintData): string {
    const normalized = JSON.stringify({
      userAgent: data.userAgent,
      language: data.language,
      screenResolution: data.screenResolution,
      timezone: data.timezone,
      plugins: data.plugins?.sort(),
    });

    return this.hashService.sha256(normalized);
  }

  // Generate content fingerprint
  generateContentFingerprint(content: any): string {
    // Normalize and hash
    const normalized = this.normalizeContent(content);
    return this.hashService.sha256(normalized);
  }

  // Check for duplicate content
  async isDuplicate(content: any, existingHashes: string[]): Promise<boolean> {
    const hash = this.generateContentFingerprint(content);
    return existingHashes.includes(hash);
  }

  private normalizeContent(content: any): string {
    // Remove whitespace variations, normalize line endings
    if (typeof content === 'string') {
      return content.trim().replace(/\s+/g, ' ');
    }
    return JSON.stringify(content);
  }
}
```

## Hash Comparison

```typescript
// Always use timing-safe comparison for security
import crypto from 'crypto';

// ❌ WRONG: Vulnerable to timing attacks
function unsafeCompare(a: string, b: string): boolean {
  return a === b;
}

// ✅ CORRECT: Timing-safe comparison
function safeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }

  return crypto.timingSafeEqual(
    Buffer.from(a),
    Buffer.from(b)
  );
}

// For hex strings
function safeCompareHex(a: string, b: string): boolean {
  const bufA = Buffer.from(a, 'hex');
  const bufB = Buffer.from(b, 'hex');

  if (bufA.length !== bufB.length) {
    return false;
  }

  return crypto.timingSafeEqual(bufA, bufB);
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Use Argon2id | Best for password hashing |
| Salt passwords | Unique salt per password (automatic with bcrypt/argon2) |
| Timing-safe compare | Prevent timing attacks |
| Upgrade hashes | Re-hash on login if algorithm upgraded |
| Never MD5/SHA1 | Broken for security purposes |
| HMAC for MACs | Use HMAC, not plain hash for authentication |
