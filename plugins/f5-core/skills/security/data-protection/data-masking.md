---
name: data-masking
description: Data masking and anonymization techniques
category: security/data-protection
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Data Masking & Anonymization

## Overview

Data masking protects sensitive information by replacing it with
fictional but realistic data, while maintaining data utility.

## Masking Types

| Type | Description | Use Case |
|------|-------------|----------|
| Static | Permanent replacement | Test environments |
| Dynamic | On-the-fly masking | Production queries |
| Tokenization | Replace with tokens | Payment processing |
| Anonymization | Irreversible removal | Analytics, GDPR |

## Masking Functions

```typescript
// services/masking.service.ts
export class MaskingService {
  // Email: j***@example.com
  maskEmail(email: string): string {
    if (!email || !email.includes('@')) return '***@***.***';

    const [local, domain] = email.split('@');
    const maskedLocal = local[0] + '*'.repeat(Math.max(local.length - 1, 3));
    return `${maskedLocal}@${domain}`;
  }

  // Phone: ***-***-1234
  maskPhone(phone: string): string {
    const digits = phone.replace(/\D/g, '');
    if (digits.length < 4) return '***-***-****';

    const lastFour = digits.slice(-4);
    return `***-***-${lastFour}`;
  }

  // Credit card: **** **** **** 1234
  maskCreditCard(cardNumber: string): string {
    const digits = cardNumber.replace(/\D/g, '');
    if (digits.length < 4) return '**** **** **** ****';

    const lastFour = digits.slice(-4);
    return `**** **** **** ${lastFour}`;
  }

  // SSN: ***-**-1234
  maskSSN(ssn: string): string {
    const digits = ssn.replace(/\D/g, '');
    if (digits.length < 4) return '***-**-****';

    const lastFour = digits.slice(-4);
    return `***-**-${lastFour}`;
  }

  // Name: J*** D**
  maskName(name: string): string {
    if (!name) return '****';

    return name
      .split(' ')
      .map(part => {
        if (part.length <= 1) return '*';
        return part[0] + '*'.repeat(Math.min(part.length - 1, 3));
      })
      .join(' ');
  }

  // Address: 123 M*** S***
  maskAddress(address: string): string {
    if (!address) return '*** ***** *****';

    const parts = address.split(' ');
    return parts
      .map((part, i) => {
        // Keep numbers (street number)
        if (/^\d+$/.test(part)) return part;
        // Mask text
        if (part.length <= 1) return '*';
        return part[0] + '*'.repeat(Math.min(part.length - 1, 4));
      })
      .join(' ');
  }

  // IP Address: 192.168.***.***
  maskIP(ip: string): string {
    const parts = ip.split('.');
    if (parts.length !== 4) return '***.***.***.***';

    return `${parts[0]}.${parts[1]}.***.***`;
  }

  // Generic partial mask
  partialMask(
    value: string,
    visibleStart: number = 0,
    visibleEnd: number = 4,
    maskChar: string = '*'
  ): string {
    if (!value) return maskChar.repeat(8);

    const start = value.substring(0, visibleStart);
    const end = value.substring(value.length - visibleEnd);
    const maskLength = Math.max(value.length - visibleStart - visibleEnd, 3);

    return start + maskChar.repeat(maskLength) + end;
  }
}
```

## Response Masking Middleware

```typescript
// middleware/masking.middleware.ts
interface MaskingRule {
  field: string;
  type: 'email' | 'phone' | 'creditCard' | 'ssn' | 'name' | 'address' | 'partial';
  options?: { visibleStart?: number; visibleEnd?: number };
}

const maskingRules: Record<string, MaskingRule[]> = {
  User: [
    { field: 'email', type: 'email' },
    { field: 'phone', type: 'phone' },
    { field: 'ssn', type: 'ssn' },
  ],
  PaymentMethod: [
    { field: 'cardNumber', type: 'creditCard' },
  ],
  Customer: [
    { field: 'name', type: 'name' },
    { field: 'email', type: 'email' },
    { field: 'address', type: 'address' },
  ],
};

export function createMaskingMiddleware(maskingService: MaskingService) {
  return (req: Request, res: Response, next: NextFunction) => {
    const originalJson = res.json.bind(res);

    res.json = (body: any) => {
      const masked = applyMasking(body, req.user?.role);
      return originalJson(masked);
    };

    next();
  };
}

function applyMasking(data: any, userRole?: string): any {
  // Skip masking for admins
  if (userRole === 'admin') return data;

  if (Array.isArray(data)) {
    return data.map(item => applyMasking(item, userRole));
  }

  if (data && typeof data === 'object') {
    const result = { ...data };

    // Determine entity type
    const entityType = data.__typename || data._type;
    const rules = maskingRules[entityType] || [];

    for (const rule of rules) {
      if (result[rule.field]) {
        result[rule.field] = applyMask(result[rule.field], rule);
      }
    }

    // Recursively mask nested objects
    for (const key of Object.keys(result)) {
      if (typeof result[key] === 'object') {
        result[key] = applyMasking(result[key], userRole);
      }
    }

    return result;
  }

  return data;
}

function applyMask(value: string, rule: MaskingRule): string {
  const maskingService = new MaskingService();

  switch (rule.type) {
    case 'email': return maskingService.maskEmail(value);
    case 'phone': return maskingService.maskPhone(value);
    case 'creditCard': return maskingService.maskCreditCard(value);
    case 'ssn': return maskingService.maskSSN(value);
    case 'name': return maskingService.maskName(value);
    case 'address': return maskingService.maskAddress(value);
    case 'partial':
      return maskingService.partialMask(
        value,
        rule.options?.visibleStart,
        rule.options?.visibleEnd
      );
    default: return value;
  }
}
```

## Data Anonymization

```typescript
// services/anonymization.service.ts
import crypto from 'crypto';
import { faker } from '@faker-js/faker';

export class AnonymizationService {
  private salt: string;

  constructor() {
    this.salt = process.env.ANONYMIZATION_SALT!;
  }

  // Consistent hash-based pseudonymization
  pseudonymize(value: string, domain: string): string {
    const hash = crypto
      .createHmac('sha256', this.salt)
      .update(`${domain}:${value}`)
      .digest('hex');

    return hash.substring(0, 16);
  }

  // Generate realistic fake data
  anonymizeUser(user: User): AnonymizedUser {
    // Seed faker with hash for consistent fake data per user
    const seed = parseInt(this.pseudonymize(user.id, 'user').substring(0, 8), 16);
    faker.seed(seed);

    return {
      id: this.pseudonymize(user.id, 'user'),
      email: faker.internet.email(),
      name: faker.person.fullName(),
      phone: faker.phone.number(),
      address: {
        street: faker.location.streetAddress(),
        city: faker.location.city(),
        state: faker.location.state(),
        zip: faker.location.zipCode(),
      },
      // Preserve non-PII fields
      createdAt: user.createdAt,
      accountType: user.accountType,
      isActive: user.isActive,
    };
  }

  // K-anonymity: generalize quasi-identifiers
  kAnonymize(records: Record[], k: number): Record[] {
    return records.map(record => ({
      ...record,
      // Generalize age to range
      ageRange: this.generalizeAge(record.age),
      // Generalize zip to first 3 digits
      zipPrefix: record.zip?.substring(0, 3) + '**',
      // Remove direct identifiers
      name: undefined,
      email: undefined,
      phone: undefined,
    }));
  }

  private generalizeAge(age: number): string {
    if (age < 20) return '0-19';
    if (age < 30) return '20-29';
    if (age < 40) return '30-39';
    if (age < 50) return '40-49';
    if (age < 60) return '50-59';
    return '60+';
  }

  // Differential privacy: add noise
  addNoise(value: number, epsilon: number = 1): number {
    // Laplace noise
    const u = Math.random() - 0.5;
    const noise = -Math.sign(u) * Math.log(1 - 2 * Math.abs(u)) / epsilon;
    return value + noise;
  }
}
```

## Database-Level Masking

```sql
-- PostgreSQL: Row-level security with masking
CREATE OR REPLACE FUNCTION mask_email(email text)
RETURNS text AS $$
BEGIN
  RETURN substring(email, 1, 1) || '****@' || split_part(email, '@', 2);
END;
$$ LANGUAGE plpgsql;

-- Create a masking view
CREATE VIEW users_masked AS
SELECT
  id,
  mask_email(email) as email,
  '***-***-' || right(phone, 4) as phone,
  left(name, 1) || '****' as name,
  -- Non-PII fields unchanged
  created_at,
  account_type
FROM users;

-- Grant access to masked view only
GRANT SELECT ON users_masked TO reporting_user;
```

## Tokenization

```typescript
// services/tokenization.service.ts
export class TokenizationService {
  private tokens: Map<string, string> = new Map();

  constructor(
    private encryptionService: EncryptionService,
    private tokenStore: TokenStore
  ) {}

  // Tokenize sensitive data
  async tokenize(value: string, type: 'card' | 'ssn' | 'account'): Promise<string> {
    // Check if already tokenized
    const existingToken = await this.tokenStore.findByValue(
      this.encryptionService.hash(value),
      type
    );

    if (existingToken) {
      return existingToken.token;
    }

    // Generate new token
    const token = this.generateToken(type);

    // Store mapping (encrypted)
    await this.tokenStore.save({
      token,
      type,
      encryptedValue: this.encryptionService.encrypt(value),
      valueHash: this.encryptionService.hash(value),
      createdAt: new Date(),
    });

    return token;
  }

  // Detokenize (requires authorization)
  async detokenize(token: string): Promise<string> {
    const record = await this.tokenStore.findByToken(token);

    if (!record) {
      throw new Error('Invalid token');
    }

    return this.encryptionService.decrypt(record.encryptedValue);
  }

  private generateToken(type: string): string {
    const prefix = {
      card: 'tok_card_',
      ssn: 'tok_ssn_',
      account: 'tok_acct_',
    }[type] || 'tok_';

    return prefix + crypto.randomBytes(16).toString('hex');
  }
}

// Payment processing with tokenization
async function processPayment(cardNumber: string, amount: number) {
  const tokenService = new TokenizationService();

  // Tokenize card number
  const cardToken = await tokenService.tokenize(cardNumber, 'card');

  // Store only token in database
  await db.payment.create({
    cardToken, // Safe to store
    amount,
    status: 'pending',
  });

  // Detokenize only when needed for processing
  const actualCard = await tokenService.detokenize(cardToken);
  // Process payment...
}
```

## GDPR Anonymization

```typescript
// services/gdpr.service.ts
export class GDPRService {
  constructor(
    private userRepository: UserRepository,
    private anonymizationService: AnonymizationService
  ) {}

  // Right to erasure (Article 17)
  async eraseUserData(userId: string): Promise<void> {
    const user = await this.userRepository.findById(userId);

    // Option 1: Full deletion
    // await this.userRepository.delete(userId);

    // Option 2: Anonymization (preserves statistics)
    const anonymizedUser = {
      id: userId,
      email: `deleted_${userId}@deleted.local`,
      name: '[DELETED]',
      phone: null,
      address: null,
      deletedAt: new Date(),
      isDeleted: true,
    };

    await this.userRepository.update(userId, anonymizedUser);

    // Delete related data
    await this.deleteRelatedData(userId);

    // Audit log
    await this.logDeletion(userId);
  }

  // Export user data (Article 15)
  async exportUserData(userId: string): Promise<UserDataExport> {
    const user = await this.userRepository.findById(userId);
    const orders = await this.orderRepository.findByUserId(userId);
    const loginHistory = await this.loginHistoryRepository.findByUserId(userId);

    return {
      personalData: user,
      orders,
      loginHistory,
      exportedAt: new Date(),
    };
  }

  private async deleteRelatedData(userId: string): Promise<void> {
    await Promise.all([
      this.sessionRepository.deleteByUserId(userId),
      this.loginHistoryRepository.deleteByUserId(userId),
      this.auditLogRepository.anonymizeByUserId(userId),
    ]);
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Minimize data | Only collect what's needed |
| Mask by default | Show masked data unless necessary |
| Consistent masking | Same value always masks the same |
| Audit unmask | Log when data is unmasked |
| Test data | Use masked/fake data in non-prod |
| Document rules | Clear masking policies |
