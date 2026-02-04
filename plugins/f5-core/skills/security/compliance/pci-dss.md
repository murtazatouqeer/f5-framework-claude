---
name: pci-dss
description: PCI-DSS compliance for payment card security
category: security/compliance
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# PCI-DSS Compliance

## Overview

Payment Card Industry Data Security Standard (PCI-DSS) protects cardholder
data. Compliance is required for any organization that stores, processes,
or transmits credit card information.

## PCI-DSS Requirements Overview

| Requirement | Description | Technical Controls |
|-------------|-------------|-------------------|
| 1 | Install and maintain firewall | Network segmentation |
| 2 | No vendor defaults | Configuration hardening |
| 3 | Protect stored data | Encryption, tokenization |
| 4 | Encrypt transmission | TLS 1.2+ |
| 5 | Protect against malware | Anti-virus, scanning |
| 6 | Secure systems | Patch management |
| 7 | Restrict access | Need-to-know basis |
| 8 | Identify and authenticate | Strong authentication |
| 9 | Restrict physical access | Physical security |
| 10 | Track and monitor | Logging, monitoring |
| 11 | Regular testing | Vulnerability scans |
| 12 | Security policies | Documentation |

## Cardholder Data Environment (CDE)

```
┌─────────────────────────────────────────────────────────────┐
│                     Network Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────┐                                             │
│  │   Internet  │                                             │
│  └──────┬──────┘                                             │
│         │                                                     │
│  ┌──────┴──────┐                                             │
│  │  Firewall   │  DMZ                                        │
│  └──────┬──────┘                                             │
│         │                                                     │
│  ╔══════╧══════╗                                             │
│  ║  Web Tier   ║  No cardholder data                         │
│  ╚══════╤══════╝                                             │
│         │                                                     │
│  ┌──────┴──────┐                                             │
│  │  Firewall   │  CDE Boundary                               │
│  └──────┬──────┘                                             │
│         │                                                     │
│  ╔══════╧══════════════════════════════════╗                 │
│  ║       Cardholder Data Environment       ║                 │
│  ║  ┌─────────────┐  ┌─────────────────┐   ║                 │
│  ║  │ Payment API │  │ Token Vault     │   ║                 │
│  ║  └─────────────┘  └─────────────────┘   ║                 │
│  ║  ┌─────────────┐  ┌─────────────────┐   ║                 │
│  ║  │ Card Store  │  │ Key Management  │   ║                 │
│  ║  │ (Encrypted) │  │ (HSM)           │   ║                 │
│  ║  └─────────────┘  └─────────────────┘   ║                 │
│  ╚═════════════════════════════════════════╝                 │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Tokenization Service

```typescript
// services/payment-tokenization.service.ts
import crypto from 'crypto';

interface CardToken {
  token: string;
  lastFour: string;
  expiryMonth: number;
  expiryYear: number;
  cardType: string;
  createdAt: Date;
}

interface CardData {
  cardNumber: string;
  expiryMonth: number;
  expiryYear: number;
  cvv: string;
  cardholderName: string;
}

export class PaymentTokenizationService {
  constructor(
    private tokenVault: TokenVault,
    private kmsService: KMSService,
    private auditLog: AuditLogService
  ) {}

  // Tokenize card data (Requirement 3)
  async tokenize(cardData: CardData): Promise<CardToken> {
    // Validate card data
    this.validateCardData(cardData);

    // Generate token
    const token = this.generateToken();

    // Encrypt card data
    const encryptionKey = await this.kmsService.getDataKey('card-encryption');
    const encryptedData = await this.encryptCardData(cardData, encryptionKey);

    // Store in vault
    await this.tokenVault.store({
      token,
      encryptedData,
      lastFour: cardData.cardNumber.slice(-4),
      expiryMonth: cardData.expiryMonth,
      expiryYear: cardData.expiryYear,
      cardType: this.detectCardType(cardData.cardNumber),
      createdAt: new Date(),
    });

    // Audit log (Requirement 10)
    await this.auditLog.log({
      action: 'card_tokenized',
      token,
      lastFour: cardData.cardNumber.slice(-4),
      timestamp: new Date(),
    });

    // Never store CVV (Requirement 3.2)
    // CVV is used only for the immediate transaction

    return {
      token,
      lastFour: cardData.cardNumber.slice(-4),
      expiryMonth: cardData.expiryMonth,
      expiryYear: cardData.expiryYear,
      cardType: this.detectCardType(cardData.cardNumber),
      createdAt: new Date(),
    };
  }

  // Detokenize for processing (restricted access)
  async detokenize(token: string, purpose: string): Promise<CardData> {
    // Verify purpose is authorized
    if (!this.isAuthorizedPurpose(purpose)) {
      throw new Error('Unauthorized detokenization purpose');
    }

    // Retrieve from vault
    const storedData = await this.tokenVault.retrieve(token);
    if (!storedData) {
      throw new Error('Token not found');
    }

    // Decrypt card data
    const encryptionKey = await this.kmsService.getDataKey('card-encryption');
    const cardData = await this.decryptCardData(storedData.encryptedData, encryptionKey);

    // Audit log
    await this.auditLog.log({
      action: 'card_detokenized',
      token,
      purpose,
      timestamp: new Date(),
    });

    return cardData;
  }

  // Generate secure token
  private generateToken(): string {
    // Format: tok_card_[random]
    return `tok_card_${crypto.randomBytes(16).toString('hex')}`;
  }

  // Encrypt card data using AES-256-GCM
  private async encryptCardData(
    cardData: CardData,
    key: Buffer
  ): Promise<string> {
    const iv = crypto.randomBytes(12);
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);

    // Remove CVV before encryption - never store
    const dataToEncrypt = {
      cardNumber: cardData.cardNumber,
      expiryMonth: cardData.expiryMonth,
      expiryYear: cardData.expiryYear,
      cardholderName: cardData.cardholderName,
    };

    let encrypted = cipher.update(JSON.stringify(dataToEncrypt), 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return Buffer.concat([
      iv,
      authTag,
      Buffer.from(encrypted, 'hex'),
    ]).toString('base64');
  }

  // Validate card data format
  private validateCardData(cardData: CardData): void {
    // Luhn check
    if (!this.luhnCheck(cardData.cardNumber)) {
      throw new Error('Invalid card number');
    }

    // Expiry check
    const now = new Date();
    const expiry = new Date(cardData.expiryYear, cardData.expiryMonth - 1);
    if (expiry < now) {
      throw new Error('Card expired');
    }

    // CVV format
    if (!/^\d{3,4}$/.test(cardData.cvv)) {
      throw new Error('Invalid CVV');
    }
  }

  // Luhn algorithm for card validation
  private luhnCheck(cardNumber: string): boolean {
    const digits = cardNumber.replace(/\D/g, '');
    let sum = 0;
    let isEven = false;

    for (let i = digits.length - 1; i >= 0; i--) {
      let digit = parseInt(digits[i], 10);

      if (isEven) {
        digit *= 2;
        if (digit > 9) digit -= 9;
      }

      sum += digit;
      isEven = !isEven;
    }

    return sum % 10 === 0;
  }

  // Detect card type from number
  private detectCardType(cardNumber: string): string {
    const patterns: Record<string, RegExp> = {
      visa: /^4/,
      mastercard: /^5[1-5]/,
      amex: /^3[47]/,
      discover: /^6(?:011|5)/,
    };

    for (const [type, pattern] of Object.entries(patterns)) {
      if (pattern.test(cardNumber)) return type;
    }

    return 'unknown';
  }
}
```

## Encryption Key Management

```typescript
// services/pci-key-management.service.ts
interface KeyInfo {
  id: string;
  version: number;
  algorithm: string;
  createdAt: Date;
  expiresAt: Date;
  status: 'active' | 'rotating' | 'retired';
}

export class PCIKeyManagementService {
  private readonly KEY_ROTATION_DAYS = 365; // Rotate annually

  constructor(
    private hsm: HSMService, // Hardware Security Module
    private keyStore: KeyStore,
    private auditLog: AuditLogService
  ) {}

  // Generate new encryption key (Requirement 3.5/3.6)
  async generateKey(purpose: string): Promise<KeyInfo> {
    // Generate key in HSM
    const keyId = await this.hsm.generateKey({
      algorithm: 'AES-256',
      extractable: false,
      purpose,
    });

    const keyInfo: KeyInfo = {
      id: keyId,
      version: 1,
      algorithm: 'AES-256-GCM',
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + this.KEY_ROTATION_DAYS * 24 * 60 * 60 * 1000),
      status: 'active',
    };

    await this.keyStore.save(keyInfo);

    await this.auditLog.log({
      action: 'key_generated',
      keyId,
      purpose,
    });

    return keyInfo;
  }

  // Rotate encryption key (Requirement 3.6.4)
  async rotateKey(keyId: string): Promise<KeyInfo> {
    const currentKey = await this.keyStore.get(keyId);
    if (!currentKey) {
      throw new Error('Key not found');
    }

    // Mark current key as rotating
    currentKey.status = 'rotating';
    await this.keyStore.save(currentKey);

    // Generate new key version
    const newKeyId = await this.hsm.generateKey({
      algorithm: 'AES-256',
      extractable: false,
      purpose: `rotation_of_${keyId}`,
    });

    const newKeyInfo: KeyInfo = {
      id: newKeyId,
      version: currentKey.version + 1,
      algorithm: 'AES-256-GCM',
      createdAt: new Date(),
      expiresAt: new Date(Date.now() + this.KEY_ROTATION_DAYS * 24 * 60 * 60 * 1000),
      status: 'active',
    };

    await this.keyStore.save(newKeyInfo);

    // Schedule re-encryption of existing data
    await this.scheduleReencryption(keyId, newKeyId);

    // Retire old key after re-encryption
    currentKey.status = 'retired';
    await this.keyStore.save(currentKey);

    await this.auditLog.log({
      action: 'key_rotated',
      oldKeyId: keyId,
      newKeyId,
    });

    return newKeyInfo;
  }

  // Split key management (Requirement 3.6.6)
  async splitKey(keyId: string, shares: number, threshold: number): Promise<string[]> {
    // Implement Shamir's Secret Sharing
    const keyMaterial = await this.hsm.exportKey(keyId, { wrapped: true });
    const shares_data = this.shamirSplit(keyMaterial, shares, threshold);

    await this.auditLog.log({
      action: 'key_split',
      keyId,
      shares,
      threshold,
    });

    return shares_data;
  }

  // Reconstruct key from shares
  async reconstructKey(shares: string[]): Promise<string> {
    const keyMaterial = this.shamirReconstruct(shares);
    const keyId = await this.hsm.importKey(keyMaterial, { wrapped: true });

    await this.auditLog.log({
      action: 'key_reconstructed',
      keyId,
      sharesUsed: shares.length,
    });

    return keyId;
  }
}
```

## Secure Transmission (Requirement 4)

```typescript
// config/tls.config.ts
import https from 'https';
import fs from 'fs';

export const pcidssHttpsOptions: https.ServerOptions = {
  key: fs.readFileSync('/path/to/private.key'),
  cert: fs.readFileSync('/path/to/certificate.crt'),
  ca: fs.readFileSync('/path/to/ca-bundle.crt'),

  // PCI-DSS requires TLS 1.2 or higher
  minVersion: 'TLSv1.2',
  maxVersion: 'TLSv1.3',

  // Strong cipher suites only
  ciphers: [
    'TLS_AES_256_GCM_SHA384',
    'TLS_AES_128_GCM_SHA256',
    'TLS_CHACHA20_POLY1305_SHA256',
    'ECDHE-ECDSA-AES256-GCM-SHA384',
    'ECDHE-RSA-AES256-GCM-SHA384',
    'ECDHE-ECDSA-AES128-GCM-SHA256',
    'ECDHE-RSA-AES128-GCM-SHA256',
  ].join(':'),

  honorCipherOrder: true,

  // Disable weak protocols
  secureOptions:
    crypto.constants.SSL_OP_NO_SSLv2 |
    crypto.constants.SSL_OP_NO_SSLv3 |
    crypto.constants.SSL_OP_NO_TLSv1 |
    crypto.constants.SSL_OP_NO_TLSv1_1,
};

// Middleware to enforce HTTPS
export function enforceHttps(req: Request, res: Response, next: NextFunction) {
  if (!req.secure && req.get('x-forwarded-proto') !== 'https') {
    // Redirect to HTTPS
    return res.redirect(301, `https://${req.get('host')}${req.url}`);
  }
  next();
}

// HSTS header
export function hstsHeader(req: Request, res: Response, next: NextFunction) {
  res.setHeader(
    'Strict-Transport-Security',
    'max-age=31536000; includeSubDomains; preload'
  );
  next();
}
```

## Access Control (Requirements 7 & 8)

```typescript
// services/pci-access-control.service.ts
interface PCIRole {
  id: string;
  name: string;
  permissions: string[];
  requiresMFA: boolean;
  sessionTimeout: number;
}

const PCI_ROLES: PCIRole[] = [
  {
    id: 'payment_admin',
    name: 'Payment Administrator',
    permissions: ['manage_tokens', 'view_logs', 'manage_keys'],
    requiresMFA: true,
    sessionTimeout: 15 * 60 * 1000, // 15 minutes
  },
  {
    id: 'payment_operator',
    name: 'Payment Operator',
    permissions: ['process_payments', 'view_transactions'],
    requiresMFA: true,
    sessionTimeout: 15 * 60 * 1000,
  },
  {
    id: 'auditor',
    name: 'Security Auditor',
    permissions: ['view_logs', 'generate_reports'],
    requiresMFA: true,
    sessionTimeout: 30 * 60 * 1000,
  },
];

export class PCIAccessControlService {
  constructor(
    private userRepository: UserRepository,
    private mfaService: MFAService,
    private auditLog: AuditLogService
  ) {}

  // Authenticate user with MFA (Requirement 8.3)
  async authenticateUser(
    username: string,
    password: string,
    mfaToken?: string
  ): Promise<AuthResult> {
    const user = await this.userRepository.findByUsername(username);

    if (!user) {
      await this.auditLog.log({
        action: 'login_failed',
        username,
        reason: 'user_not_found',
      });
      throw new Error('Invalid credentials');
    }

    // Check account lockout (Requirement 8.1.6)
    if (await this.isAccountLocked(user.id)) {
      throw new Error('Account locked');
    }

    // Verify password
    const passwordValid = await this.verifyPassword(password, user.passwordHash);
    if (!passwordValid) {
      await this.recordFailedAttempt(user.id);
      throw new Error('Invalid credentials');
    }

    // Check if MFA required
    const role = PCI_ROLES.find(r => r.id === user.roleId);
    if (role?.requiresMFA) {
      if (!mfaToken) {
        return { requiresMFA: true, userId: user.id };
      }

      const mfaValid = await this.mfaService.verify(user.id, mfaToken);
      if (!mfaValid) {
        await this.auditLog.log({
          action: 'mfa_failed',
          userId: user.id,
        });
        throw new Error('Invalid MFA token');
      }
    }

    // Successful login
    await this.auditLog.log({
      action: 'login_success',
      userId: user.id,
    });

    return {
      authenticated: true,
      userId: user.id,
      sessionTimeout: role?.sessionTimeout || 30 * 60 * 1000,
    };
  }

  // Check permission (Requirement 7)
  async checkPermission(userId: string, permission: string): Promise<boolean> {
    const user = await this.userRepository.findById(userId);
    const role = PCI_ROLES.find(r => r.id === user?.roleId);

    if (!role) return false;

    const hasPermission = role.permissions.includes(permission);

    await this.auditLog.log({
      action: 'permission_check',
      userId,
      permission,
      granted: hasPermission,
    });

    return hasPermission;
  }

  // Password requirements (Requirement 8.2)
  validatePassword(password: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];

    // Minimum 12 characters (PCI-DSS 4.0)
    if (password.length < 12) {
      errors.push('Password must be at least 12 characters');
    }

    // Complexity requirements
    if (!/[A-Z]/.test(password)) {
      errors.push('Password must contain uppercase letter');
    }
    if (!/[a-z]/.test(password)) {
      errors.push('Password must contain lowercase letter');
    }
    if (!/[0-9]/.test(password)) {
      errors.push('Password must contain number');
    }
    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      errors.push('Password must contain special character');
    }

    return { valid: errors.length === 0, errors };
  }

  // Account lockout after 6 failed attempts (Requirement 8.1.6)
  private async recordFailedAttempt(userId: string): Promise<void> {
    const attempts = await this.incrementFailedAttempts(userId);

    if (attempts >= 6) {
      await this.lockAccount(userId, 30 * 60 * 1000); // 30 minute lockout

      await this.auditLog.log({
        action: 'account_locked',
        userId,
        reason: 'exceeded_login_attempts',
      });
    }
  }
}
```

## Audit Logging (Requirement 10)

```typescript
// services/pci-audit-log.service.ts
interface PCIAuditEvent {
  timestamp: Date;
  eventType: string;
  userId?: string;
  sourceIP: string;
  action: string;
  outcome: 'success' | 'failure';
  details: Record<string, any>;
  componentId: string;
}

export class PCIAuditLogService {
  constructor(
    private logStore: SecureLogStore,
    private integrityService: LogIntegrityService
  ) {}

  // Log security event (Requirement 10.2)
  async log(event: Omit<PCIAuditEvent, 'timestamp'>): Promise<void> {
    const fullEvent: PCIAuditEvent = {
      ...event,
      timestamp: new Date(),
    };

    // Write to secure log store
    await this.logStore.write(fullEvent);

    // Add to integrity chain
    await this.integrityService.addToChain(fullEvent);
  }

  // Required event types (Requirement 10.2)
  private readonly REQUIRED_EVENTS = [
    'user_access_cardholder_data',
    'root_admin_action',
    'access_audit_trails',
    'invalid_access_attempt',
    'identification_mechanism_use',
    'initialization_of_audit_logs',
    'creation_deletion_system_objects',
  ];

  // Log cardholder data access
  async logCardholderAccess(
    userId: string,
    action: string,
    dataAccessed: string
  ): Promise<void> {
    await this.log({
      eventType: 'user_access_cardholder_data',
      userId,
      sourceIP: this.getSourceIP(),
      action,
      outcome: 'success',
      details: { dataAccessed },
      componentId: 'payment-system',
    });
  }

  // Log failed access attempt
  async logFailedAccess(
    sourceIP: string,
    attemptedAction: string,
    reason: string
  ): Promise<void> {
    await this.log({
      eventType: 'invalid_access_attempt',
      sourceIP,
      action: attemptedAction,
      outcome: 'failure',
      details: { reason },
      componentId: 'security-system',
    });
  }

  // Verify log integrity (Requirement 10.5.5)
  async verifyIntegrity(startDate: Date, endDate: Date): Promise<boolean> {
    return this.integrityService.verifyChain(startDate, endDate);
  }

  // Generate compliance report
  async generateComplianceReport(
    period: { start: Date; end: Date }
  ): Promise<ComplianceReport> {
    const events = await this.logStore.query(period);

    return {
      period,
      totalEvents: events.length,
      eventsByType: this.groupByType(events),
      failedAccessAttempts: events.filter(e => e.outcome === 'failure').length,
      uniqueUsers: new Set(events.map(e => e.userId).filter(Boolean)).size,
      integrityVerified: await this.verifyIntegrity(period.start, period.end),
    };
  }
}

// Log integrity with hash chain
export class LogIntegrityService {
  private previousHash: string = '';

  async addToChain(event: PCIAuditEvent): Promise<string> {
    const eventData = JSON.stringify(event);
    const currentHash = crypto
      .createHash('sha256')
      .update(this.previousHash + eventData)
      .digest('hex');

    this.previousHash = currentHash;

    await this.storeHash(event.timestamp, currentHash);

    return currentHash;
  }

  async verifyChain(start: Date, end: Date): Promise<boolean> {
    const entries = await this.getHashChain(start, end);
    let previousHash = '';

    for (const entry of entries) {
      const expectedHash = crypto
        .createHash('sha256')
        .update(previousHash + entry.eventData)
        .digest('hex');

      if (expectedHash !== entry.hash) {
        return false; // Integrity violation
      }

      previousHash = entry.hash;
    }

    return true;
  }
}
```

## Vulnerability Management (Requirement 6 & 11)

```typescript
// services/vulnerability-management.service.ts
interface VulnerabilityScan {
  id: string;
  type: 'internal' | 'external' | 'penetration';
  startedAt: Date;
  completedAt?: Date;
  findings: VulnerabilityFinding[];
  status: 'running' | 'completed' | 'failed';
}

interface VulnerabilityFinding {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  affectedComponent: string;
  remediation: string;
  status: 'open' | 'in_progress' | 'resolved' | 'accepted';
}

export class VulnerabilityManagementService {
  // Schedule quarterly external scans (Requirement 11.3.2)
  async scheduleExternalScan(): Promise<VulnerabilityScan> {
    const scan: VulnerabilityScan = {
      id: this.generateScanId(),
      type: 'external',
      startedAt: new Date(),
      findings: [],
      status: 'running',
    };

    // Trigger ASV (Approved Scanning Vendor) scan
    await this.triggerASVScan(scan.id);

    return scan;
  }

  // Internal vulnerability scans (Requirement 11.3.1)
  async runInternalScan(): Promise<VulnerabilityScan> {
    const scan: VulnerabilityScan = {
      id: this.generateScanId(),
      type: 'internal',
      startedAt: new Date(),
      findings: [],
      status: 'running',
    };

    // Run internal vulnerability scanner
    const findings = await this.internalScanner.scan({
      targets: await this.getCDETargets(),
      plugins: 'all',
    });

    scan.findings = findings;
    scan.completedAt = new Date();
    scan.status = 'completed';

    // Check for critical/high findings
    const criticalFindings = findings.filter(
      f => f.severity === 'critical' || f.severity === 'high'
    );

    if (criticalFindings.length > 0) {
      await this.alertSecurityTeam(criticalFindings);
    }

    return scan;
  }

  // Track remediation (Requirement 6.3.3)
  async trackRemediation(findingId: string): Promise<RemediationStatus> {
    const finding = await this.findingRepository.findById(findingId);

    return {
      findingId,
      severity: finding.severity,
      status: finding.status,
      daysOpen: this.calculateDaysOpen(finding),
      slaBreach: this.checkSLABreach(finding),
    };
  }

  // SLA requirements
  private readonly REMEDIATION_SLA = {
    critical: 1, // 1 day
    high: 7, // 7 days
    medium: 30, // 30 days
    low: 90, // 90 days
  };

  private checkSLABreach(finding: VulnerabilityFinding): boolean {
    const daysOpen = this.calculateDaysOpen(finding);
    const slaDays = this.REMEDIATION_SLA[finding.severity];
    return daysOpen > slaDays;
  }
}
```

## PCI-DSS Compliance Dashboard

```typescript
// services/pci-compliance-dashboard.service.ts
interface ComplianceStatus {
  requirement: string;
  description: string;
  status: 'compliant' | 'non_compliant' | 'partial' | 'not_applicable';
  lastAssessed: Date;
  evidence: string[];
  findings: string[];
}

export class PCIComplianceDashboard {
  async getComplianceStatus(): Promise<ComplianceStatus[]> {
    return [
      {
        requirement: '3',
        description: 'Protect stored cardholder data',
        status: await this.assessRequirement3(),
        lastAssessed: new Date(),
        evidence: [
          'Encryption keys rotated annually',
          'Card data tokenized',
          'CVV not stored',
        ],
        findings: [],
      },
      {
        requirement: '4',
        description: 'Encrypt transmission',
        status: await this.assessRequirement4(),
        lastAssessed: new Date(),
        evidence: [
          'TLS 1.2+ enforced',
          'Strong cipher suites',
          'HSTS enabled',
        ],
        findings: [],
      },
      {
        requirement: '8',
        description: 'Identify and authenticate',
        status: await this.assessRequirement8(),
        lastAssessed: new Date(),
        evidence: [
          'MFA enabled for CDE access',
          'Password policy enforced',
          'Account lockout configured',
        ],
        findings: [],
      },
      {
        requirement: '10',
        description: 'Track and monitor',
        status: await this.assessRequirement10(),
        lastAssessed: new Date(),
        evidence: [
          'Audit logs enabled',
          'Log integrity verified',
          'Centralized logging',
        ],
        findings: [],
      },
    ];
  }

  // Generate Self-Assessment Questionnaire
  async generateSAQ(type: 'A' | 'A-EP' | 'B' | 'C' | 'D'): Promise<SAQReport> {
    const questions = await this.getSAQQuestions(type);
    const answers = await this.collectAnswers(questions);

    return {
      type,
      generatedAt: new Date(),
      questions: questions.length,
      compliant: answers.filter(a => a.compliant).length,
      nonCompliant: answers.filter(a => !a.compliant).length,
      details: answers,
    };
  }
}
```

## Compliance Checklist

```yaml
# pci-dss-checklist.yaml
requirement_3:
  protect_stored_data:
    - no_full_pan_storage_unless_necessary
    - cvv_never_stored
    - encryption_at_rest_aes256
    - key_management_procedures
    - annual_key_rotation

requirement_4:
  encrypt_transmission:
    - tls_1_2_minimum
    - strong_cipher_suites
    - no_weak_protocols
    - certificate_management

requirement_7:
  restrict_access:
    - need_to_know_basis
    - role_based_access
    - access_reviews

requirement_8:
  authentication:
    - unique_user_ids
    - mfa_for_cde_access
    - password_policy
    - account_lockout
    - session_timeout

requirement_10:
  logging:
    - audit_all_access
    - log_integrity
    - centralized_logging
    - 1_year_retention
    - daily_log_review

requirement_11:
  testing:
    - quarterly_external_scans
    - quarterly_internal_scans
    - annual_penetration_test
    - wireless_detection
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Minimize CDE scope | Reduce systems handling card data |
| Use tokenization | Replace card data with tokens |
| Network segmentation | Isolate CDE from other networks |
| Strong encryption | AES-256 for data at rest |
| Key management | HSM for key storage |
| Regular testing | Quarterly scans, annual pen tests |
