---
name: encryption
description: Data encryption at rest and in transit
category: security/data-protection
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Data Encryption

## Overview

Encryption protects data confidentiality by transforming readable data
into an unreadable format that can only be decoded with the correct key.

## Encryption Types

| Type | Use Case | Examples |
|------|----------|----------|
| Symmetric | Fast, bulk encryption | AES-256-GCM |
| Asymmetric | Key exchange, signatures | RSA, ECDSA |
| Hashing | One-way, integrity | SHA-256, bcrypt |

## Symmetric Encryption

### AES-256-GCM Implementation

```typescript
// services/encryption.service.ts
import crypto from 'crypto';

export class EncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyLength = 32; // 256 bits
  private readonly ivLength = 12;  // 96 bits for GCM
  private readonly tagLength = 16; // 128 bits

  constructor(private masterKey: Buffer) {
    if (masterKey.length !== this.keyLength) {
      throw new Error(`Master key must be ${this.keyLength} bytes`);
    }
  }

  encrypt(plaintext: string): EncryptedData {
    // Generate unique IV for each encryption
    const iv = crypto.randomBytes(this.ivLength);

    // Derive a unique key for this encryption (optional but recommended)
    const key = this.deriveKey(iv);

    const cipher = crypto.createCipheriv(this.algorithm, key, iv, {
      authTagLength: this.tagLength,
    });

    let ciphertext = cipher.update(plaintext, 'utf8', 'base64');
    ciphertext += cipher.final('base64');

    const authTag = cipher.getAuthTag();

    return {
      ciphertext,
      iv: iv.toString('base64'),
      authTag: authTag.toString('base64'),
      algorithm: this.algorithm,
    };
  }

  decrypt(encryptedData: EncryptedData): string {
    const iv = Buffer.from(encryptedData.iv, 'base64');
    const authTag = Buffer.from(encryptedData.authTag, 'base64');
    const key = this.deriveKey(iv);

    const decipher = crypto.createDecipheriv(this.algorithm, key, iv, {
      authTagLength: this.tagLength,
    });

    decipher.setAuthTag(authTag);

    let plaintext = decipher.update(encryptedData.ciphertext, 'base64', 'utf8');
    plaintext += decipher.final('utf8');

    return plaintext;
  }

  // Derive per-message key using HKDF
  private deriveKey(context: Buffer): Buffer {
    return crypto.hkdfSync(
      'sha256',
      this.masterKey,
      Buffer.alloc(0), // No salt (master key is already secure)
      context,
      this.keyLength
    );
  }

  // Convenience methods for string format
  encryptToString(plaintext: string): string {
    const encrypted = this.encrypt(plaintext);
    return `${encrypted.iv}:${encrypted.authTag}:${encrypted.ciphertext}`;
  }

  decryptFromString(encrypted: string): string {
    const [iv, authTag, ciphertext] = encrypted.split(':');
    return this.decrypt({
      iv,
      authTag,
      ciphertext,
      algorithm: this.algorithm,
    });
  }
}

// Usage
const masterKey = crypto.randomBytes(32);
const encryptionService = new EncryptionService(masterKey);

const encrypted = encryptionService.encryptToString('sensitive data');
const decrypted = encryptionService.decryptFromString(encrypted);
```

### Key Management

```typescript
// services/key-management.service.ts
import crypto from 'crypto';

export class KeyManagementService {
  private keys: Map<string, KeyInfo> = new Map();

  // Generate a new data encryption key (DEK)
  async generateDEK(): Promise<{ keyId: string; key: Buffer }> {
    const keyId = crypto.randomUUID();
    const key = crypto.randomBytes(32);

    // Encrypt DEK with Key Encryption Key (KEK)
    const encryptedKey = await this.encryptWithKEK(key);

    this.keys.set(keyId, {
      encryptedKey,
      createdAt: new Date(),
      version: 1,
    });

    return { keyId, key };
  }

  // Get DEK by ID
  async getDEK(keyId: string): Promise<Buffer> {
    const keyInfo = this.keys.get(keyId);
    if (!keyInfo) {
      throw new Error('Key not found');
    }

    return this.decryptWithKEK(keyInfo.encryptedKey);
  }

  // Rotate key
  async rotateKey(keyId: string): Promise<string> {
    const oldKey = await this.getDEK(keyId);
    const { keyId: newKeyId, key: newKey } = await this.generateDEK();

    // Re-encrypt data with new key (application-specific)
    // This should trigger re-encryption of all data using oldKey

    return newKeyId;
  }

  // Using AWS KMS or similar service
  private async encryptWithKEK(data: Buffer): Promise<Buffer> {
    // In production, use a KMS service
    // Example with AWS KMS:
    // const kms = new AWS.KMS();
    // const result = await kms.encrypt({
    //   KeyId: process.env.KMS_KEY_ID,
    //   Plaintext: data,
    // }).promise();
    // return result.CiphertextBlob;

    // For demo, use local encryption
    const kek = Buffer.from(process.env.KEK!, 'hex');
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', kek, iv);
    const encrypted = Buffer.concat([cipher.update(data), cipher.final()]);
    const tag = cipher.getAuthTag();
    return Buffer.concat([iv, tag, encrypted]);
  }

  private async decryptWithKEK(encrypted: Buffer): Promise<Buffer> {
    const kek = Buffer.from(process.env.KEK!, 'hex');
    const iv = encrypted.slice(0, 12);
    const tag = encrypted.slice(12, 28);
    const ciphertext = encrypted.slice(28);

    const decipher = crypto.createDecipheriv('aes-256-gcm', kek, iv);
    decipher.setAuthTag(tag);
    return Buffer.concat([decipher.update(ciphertext), decipher.final()]);
  }
}
```

## Asymmetric Encryption

```typescript
// services/asymmetric-encryption.service.ts
import crypto from 'crypto';

export class AsymmetricEncryptionService {
  // Generate key pair
  static generateKeyPair(): { publicKey: string; privateKey: string } {
    const { publicKey, privateKey } = crypto.generateKeyPairSync('rsa', {
      modulusLength: 4096,
      publicKeyEncoding: {
        type: 'spki',
        format: 'pem',
      },
      privateKeyEncoding: {
        type: 'pkcs8',
        format: 'pem',
      },
    });

    return { publicKey, privateKey };
  }

  // Encrypt with public key
  static encrypt(data: string, publicKey: string): string {
    const encrypted = crypto.publicEncrypt(
      {
        key: publicKey,
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
        oaepHash: 'sha256',
      },
      Buffer.from(data)
    );

    return encrypted.toString('base64');
  }

  // Decrypt with private key
  static decrypt(encryptedData: string, privateKey: string): string {
    const decrypted = crypto.privateDecrypt(
      {
        key: privateKey,
        padding: crypto.constants.RSA_PKCS1_OAEP_PADDING,
        oaepHash: 'sha256',
      },
      Buffer.from(encryptedData, 'base64')
    );

    return decrypted.toString('utf8');
  }

  // Sign data
  static sign(data: string, privateKey: string): string {
    const sign = crypto.createSign('SHA256');
    sign.update(data);
    return sign.sign(privateKey, 'base64');
  }

  // Verify signature
  static verify(data: string, signature: string, publicKey: string): boolean {
    const verify = crypto.createVerify('SHA256');
    verify.update(data);
    return verify.verify(publicKey, signature, 'base64');
  }
}
```

## Database Field Encryption

```typescript
// Prisma middleware for transparent encryption
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const encryption = new EncryptionService(masterKey);

// Define which fields to encrypt per model
const encryptedFields: Record<string, string[]> = {
  User: ['ssn', 'dateOfBirth'],
  PaymentMethod: ['cardNumber'],
  MedicalRecord: ['diagnosis', 'notes'],
};

// Middleware for encryption
prisma.$use(async (params, next) => {
  const modelFields = encryptedFields[params.model || ''];
  if (!modelFields) return next(params);

  // Encrypt before create/update
  if (['create', 'update', 'upsert'].includes(params.action)) {
    const data = params.args.data;
    for (const field of modelFields) {
      if (data?.[field]) {
        data[field] = encryption.encryptToString(data[field]);
      }
    }
  }

  const result = await next(params);

  // Decrypt after read
  if (['findUnique', 'findFirst', 'findMany'].includes(params.action)) {
    const decryptObj = (obj: any) => {
      if (!obj) return obj;
      for (const field of modelFields) {
        if (obj[field]) {
          try {
            obj[field] = encryption.decryptFromString(obj[field]);
          } catch (e) {
            // Field might not be encrypted (migration period)
            console.warn(`Failed to decrypt ${field}`);
          }
        }
      }
      return obj;
    };

    if (Array.isArray(result)) {
      return result.map(decryptObj);
    }
    return decryptObj(result);
  }

  return result;
});
```

## File Encryption

```typescript
// services/file-encryption.service.ts
import crypto from 'crypto';
import { createReadStream, createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';

export class FileEncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyLength = 32;

  constructor(private key: Buffer) {}

  async encryptFile(inputPath: string, outputPath: string): Promise<void> {
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv(this.algorithm, this.key, iv);

    const input = createReadStream(inputPath);
    const output = createWriteStream(outputPath);

    // Write IV as header
    output.write(iv);

    await pipeline(input, cipher, output);

    // Append auth tag
    const tag = cipher.getAuthTag();
    await fs.promises.appendFile(outputPath, tag);
  }

  async decryptFile(inputPath: string, outputPath: string): Promise<void> {
    const stat = await fs.promises.stat(inputPath);
    const fileSize = stat.size;

    // Read IV from start
    const ivBuffer = Buffer.alloc(12);
    const fd = await fs.promises.open(inputPath, 'r');
    await fd.read(ivBuffer, 0, 12, 0);

    // Read auth tag from end
    const tagBuffer = Buffer.alloc(16);
    await fd.read(tagBuffer, 0, 16, fileSize - 16);
    await fd.close();

    const decipher = crypto.createDecipheriv(this.algorithm, this.key, ivBuffer);
    decipher.setAuthTag(tagBuffer);

    // Read encrypted content (skip IV, exclude tag)
    const input = createReadStream(inputPath, {
      start: 12,
      end: fileSize - 17,
    });
    const output = createWriteStream(outputPath);

    await pipeline(input, decipher, output);
  }
}
```

## Envelope Encryption

```typescript
// Envelope encryption: encrypt data with DEK, encrypt DEK with KEK
export class EnvelopeEncryption {
  constructor(
    private kmsService: KMSService,
    private encryptionService: EncryptionService
  ) {}

  async encrypt(data: string): Promise<EnvelopeEncryptedData> {
    // Generate random DEK
    const dek = crypto.randomBytes(32);

    // Encrypt data with DEK
    const encryptedData = this.encryptWithKey(data, dek);

    // Encrypt DEK with KMS (KEK)
    const encryptedDEK = await this.kmsService.encrypt(dek);

    return {
      encryptedData,
      encryptedDEK,
      keyId: this.kmsService.currentKeyId,
    };
  }

  async decrypt(envelope: EnvelopeEncryptedData): Promise<string> {
    // Decrypt DEK with KMS
    const dek = await this.kmsService.decrypt(envelope.encryptedDEK, envelope.keyId);

    // Decrypt data with DEK
    return this.decryptWithKey(envelope.encryptedData, dek);
  }

  private encryptWithKey(data: string, key: Buffer): string {
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    let encrypted = cipher.update(data, 'utf8', 'base64');
    encrypted += cipher.final('base64');
    const tag = cipher.getAuthTag();
    return `${iv.toString('base64')}:${tag.toString('base64')}:${encrypted}`;
  }

  private decryptWithKey(encrypted: string, key: Buffer): string {
    const [ivB64, tagB64, ciphertext] = encrypted.split(':');
    const iv = Buffer.from(ivB64, 'base64');
    const tag = Buffer.from(tagB64, 'base64');

    const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
    decipher.setAuthTag(tag);
    let decrypted = decipher.update(ciphertext, 'base64', 'utf8');
    decrypted += decipher.final('utf8');
    return decrypted;
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Use AES-256-GCM | Authenticated encryption |
| Unique IV | Never reuse IV with same key |
| Key rotation | Rotate keys periodically |
| Envelope encryption | Separate data and key encryption |
| KMS for KEK | Use cloud KMS for key encryption keys |
| Audit key access | Log all key operations |
