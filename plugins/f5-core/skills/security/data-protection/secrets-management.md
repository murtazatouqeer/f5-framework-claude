---
name: secrets-management
description: Managing secrets, credentials, and sensitive configuration
category: security/data-protection
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Secrets Management

## Overview

Secrets management involves securely storing, accessing, and rotating
sensitive credentials like API keys, passwords, and encryption keys.

## Secrets Types

| Type | Examples | Risk Level |
|------|----------|------------|
| Credentials | Database passwords, API keys | Critical |
| Encryption keys | AES keys, signing keys | Critical |
| Tokens | OAuth tokens, JWT secrets | High |
| Certificates | TLS certs, signing certs | High |
| Connection strings | Database URLs | High |

## Environment Variables

### Basic Setup

```typescript
// config/env.ts
import { z } from 'zod';
import dotenv from 'dotenv';

// Load .env file (development only)
if (process.env.NODE_ENV !== 'production') {
  dotenv.config();
}

// Define schema
const envSchema = z.object({
  NODE_ENV: z.enum(['development', 'test', 'staging', 'production']),

  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_SSL: z.string().transform(v => v === 'true').default('true'),

  // Auth
  JWT_SECRET: z.string().min(64),
  JWT_REFRESH_SECRET: z.string().min(64),
  SESSION_SECRET: z.string().min(32),

  // Encryption
  ENCRYPTION_KEY: z.string().length(64), // 32 bytes hex

  // External services
  STRIPE_SECRET_KEY: z.string().startsWith('sk_'),
  SENDGRID_API_KEY: z.string().startsWith('SG.'),

  // AWS
  AWS_ACCESS_KEY_ID: z.string().optional(),
  AWS_SECRET_ACCESS_KEY: z.string().optional(),
  AWS_REGION: z.string().default('us-east-1'),
});

// Validate and export
const parsed = envSchema.safeParse(process.env);

if (!parsed.success) {
  console.error('❌ Invalid environment variables:');
  console.error(parsed.error.format());
  process.exit(1);
}

export const env = parsed.data;

// Never log secrets
export function logConfig() {
  console.log('Configuration loaded:');
  console.log(`  NODE_ENV: ${env.NODE_ENV}`);
  console.log(`  DATABASE_URL: ${maskConnectionString(env.DATABASE_URL)}`);
  console.log(`  JWT_SECRET: ${maskSecret(env.JWT_SECRET)}`);
}

function maskSecret(secret: string): string {
  return secret.substring(0, 4) + '****' + secret.substring(secret.length - 4);
}

function maskConnectionString(url: string): string {
  return url.replace(/:\/\/[^@]+@/, '://****:****@');
}
```

### Secret Rotation Support

```typescript
// config/secrets.ts
export class SecretsConfig {
  // Support multiple secrets during rotation
  private jwtSecrets: string[];

  constructor() {
    // Current secret + previous secret for rotation
    const current = process.env.JWT_SECRET!;
    const previous = process.env.JWT_SECRET_PREVIOUS;

    this.jwtSecrets = previous ? [current, previous] : [current];
  }

  // Sign with current secret
  get currentJwtSecret(): string {
    return this.jwtSecrets[0];
  }

  // Verify with any valid secret
  get validJwtSecrets(): string[] {
    return this.jwtSecrets;
  }
}

// JWT verification with rotation support
function verifyToken(token: string, secrets: string[]): TokenPayload {
  for (const secret of secrets) {
    try {
      return jwt.verify(token, secret) as TokenPayload;
    } catch (error) {
      // Try next secret
    }
  }
  throw new Error('Invalid token');
}
```

## Cloud Secrets Managers

### AWS Secrets Manager

```typescript
// services/aws-secrets.service.ts
import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

export class AWSSecretsService {
  private client: SecretsManagerClient;
  private cache: Map<string, { value: any; expiresAt: number }> = new Map();
  private readonly cacheTTL = 5 * 60 * 1000; // 5 minutes

  constructor() {
    this.client = new SecretsManagerClient({
      region: process.env.AWS_REGION,
    });
  }

  async getSecret<T = string>(secretId: string): Promise<T> {
    // Check cache
    const cached = this.cache.get(secretId);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.value;
    }

    // Fetch from AWS
    const command = new GetSecretValueCommand({ SecretId: secretId });
    const response = await this.client.send(command);

    let value: T;
    if (response.SecretString) {
      try {
        value = JSON.parse(response.SecretString);
      } catch {
        value = response.SecretString as unknown as T;
      }
    } else if (response.SecretBinary) {
      value = Buffer.from(response.SecretBinary).toString() as unknown as T;
    } else {
      throw new Error('Secret has no value');
    }

    // Cache
    this.cache.set(secretId, {
      value,
      expiresAt: Date.now() + this.cacheTTL,
    });

    return value;
  }

  // Get database credentials
  async getDatabaseCredentials(): Promise<DatabaseCredentials> {
    return this.getSecret<DatabaseCredentials>('prod/database/credentials');
  }

  // Invalidate cache (for rotation)
  invalidateCache(secretId?: string) {
    if (secretId) {
      this.cache.delete(secretId);
    } else {
      this.cache.clear();
    }
  }
}
```

### HashiCorp Vault

```typescript
// services/vault.service.ts
import vault from 'node-vault';

export class VaultService {
  private client: vault.client;
  private cache: Map<string, { value: any; expiresAt: number }> = new Map();

  constructor() {
    this.client = vault({
      apiVersion: 'v1',
      endpoint: process.env.VAULT_ADDR,
      token: process.env.VAULT_TOKEN,
    });
  }

  async getSecret(path: string): Promise<any> {
    // Check cache
    const cached = this.cache.get(path);
    if (cached && cached.expiresAt > Date.now()) {
      return cached.value;
    }

    // Read from Vault
    const result = await this.client.read(path);
    const value = result.data.data || result.data;

    // Cache based on lease duration
    const ttl = result.lease_duration
      ? result.lease_duration * 1000
      : 5 * 60 * 1000;

    this.cache.set(path, {
      value,
      expiresAt: Date.now() + ttl,
    });

    return value;
  }

  // Write secret
  async writeSecret(path: string, data: Record<string, any>): Promise<void> {
    await this.client.write(path, { data });
    this.cache.delete(path);
  }

  // Dynamic database credentials
  async getDatabaseCredentials(role: string): Promise<DatabaseCredentials> {
    const result = await this.client.read(`database/creds/${role}`);
    return {
      username: result.data.username,
      password: result.data.password,
      ttl: result.lease_duration,
    };
  }
}
```

## Docker Secrets

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    image: myapp
    secrets:
      - db_password
      - jwt_secret
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
      JWT_SECRET_FILE: /run/secrets/jwt_secret

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
```

```typescript
// Read Docker secrets
import fs from 'fs';

function readDockerSecret(name: string): string {
  const filePath = `/run/secrets/${name}`;

  if (fs.existsSync(filePath)) {
    return fs.readFileSync(filePath, 'utf8').trim();
  }

  // Fallback to environment variable
  return process.env[name.toUpperCase()] || '';
}

// Load secrets
const dbPassword = readDockerSecret('db_password');
const jwtSecret = readDockerSecret('jwt_secret');
```

## Secret Rotation

```typescript
// services/secret-rotation.service.ts
export class SecretRotationService {
  constructor(
    private secretsManager: AWSSecretsService,
    private notificationService: NotificationService
  ) {}

  async rotateSecret(secretId: string): Promise<void> {
    console.log(`Starting rotation for ${secretId}`);

    try {
      // 1. Generate new secret
      const newSecret = this.generateNewSecret(secretId);

      // 2. Update secret in secrets manager
      // AWS Secrets Manager handles this automatically with Lambda

      // 3. Test new secret
      await this.testSecret(secretId, newSecret);

      // 4. Update applications (via config reload)
      await this.notifyApplications(secretId);

      // 5. Invalidate cache
      this.secretsManager.invalidateCache(secretId);

      console.log(`Successfully rotated ${secretId}`);
    } catch (error) {
      console.error(`Failed to rotate ${secretId}:`, error);
      await this.notificationService.sendAlert({
        type: 'SECRET_ROTATION_FAILED',
        secretId,
        error: error.message,
      });
      throw error;
    }
  }

  private generateNewSecret(secretId: string): string {
    // Generate appropriate secret based on type
    if (secretId.includes('jwt')) {
      return crypto.randomBytes(64).toString('hex');
    }
    if (secretId.includes('api_key')) {
      return `sk_${crypto.randomBytes(32).toString('hex')}`;
    }
    return crypto.randomBytes(32).toString('hex');
  }

  private async testSecret(secretId: string, secret: string): Promise<void> {
    // Verify secret works before completing rotation
    // Implementation depends on secret type
  }

  private async notifyApplications(secretId: string): Promise<void> {
    // Send signal to reload configuration
    // Could use message queue, webhook, or config reload endpoint
  }
}
```

## Git Secrets Prevention

```bash
# .gitignore
.env
.env.*
!.env.example
*.pem
*.key
secrets/
credentials/

# pre-commit hook: .git/hooks/pre-commit
#!/bin/bash

# Check for secrets in staged files
PATTERNS=(
  'password\s*=\s*["\047][^"\047]+'
  'api[_-]?key\s*=\s*["\047][^"\047]+'
  'secret[_-]?key\s*=\s*["\047][^"\047]+'
  'AWS_ACCESS_KEY_ID'
  'AWS_SECRET_ACCESS_KEY'
  'sk_live_'
  'rk_live_'
)

for pattern in "${PATTERNS[@]}"; do
  if git diff --cached --diff-filter=ACM | grep -qiE "$pattern"; then
    echo "ERROR: Potential secret detected in commit"
    echo "Pattern matched: $pattern"
    exit 1
  fi
done
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Never commit secrets | Use .gitignore and pre-commit hooks |
| Use secrets manager | AWS SM, Vault, or GCP SM |
| Rotate regularly | Automated rotation schedules |
| Least privilege | Minimal access to secrets |
| Audit access | Log all secret retrievals |
| Encrypt at rest | Secrets manager handles this |
