---
name: gdpr
description: GDPR compliance implementation patterns
category: security/compliance
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GDPR Compliance

## Overview

The General Data Protection Regulation (GDPR) requires organizations to
protect EU citizens' personal data and privacy. This guide covers
technical implementations for GDPR compliance.

## Key Principles

| Principle | Description | Technical Implementation |
|-----------|-------------|-------------------------|
| Lawfulness | Legal basis for processing | Consent management system |
| Purpose limitation | Specific, explicit purposes | Data usage tracking |
| Data minimization | Only necessary data | Field-level restrictions |
| Accuracy | Keep data accurate | Update mechanisms |
| Storage limitation | Limited retention | Auto-deletion policies |
| Integrity | Security measures | Encryption, access control |
| Accountability | Demonstrate compliance | Audit logging |

## Consent Management

```typescript
// services/consent.service.ts
import { EventEmitter } from 'events';

interface ConsentRecord {
  userId: string;
  purpose: string;
  granted: boolean;
  timestamp: Date;
  source: 'explicit' | 'implicit';
  version: string;
  ipAddress?: string;
  userAgent?: string;
}

interface ConsentPurpose {
  id: string;
  name: string;
  description: string;
  required: boolean;
  defaultValue: boolean;
}

export class ConsentService extends EventEmitter {
  private purposes: ConsentPurpose[] = [
    {
      id: 'essential',
      name: 'Essential Cookies',
      description: 'Required for the website to function',
      required: true,
      defaultValue: true,
    },
    {
      id: 'analytics',
      name: 'Analytics',
      description: 'Help us understand how you use our site',
      required: false,
      defaultValue: false,
    },
    {
      id: 'marketing',
      name: 'Marketing',
      description: 'Personalized advertisements',
      required: false,
      defaultValue: false,
    },
    {
      id: 'functional',
      name: 'Functional',
      description: 'Enhanced features and personalization',
      required: false,
      defaultValue: false,
    },
  ];

  constructor(private consentStore: ConsentStore) {
    super();
  }

  // Record consent
  async recordConsent(
    userId: string,
    consents: Record<string, boolean>,
    metadata: { ipAddress?: string; userAgent?: string }
  ): Promise<void> {
    const version = await this.getCurrentPolicyVersion();

    for (const [purpose, granted] of Object.entries(consents)) {
      const record: ConsentRecord = {
        userId,
        purpose,
        granted,
        timestamp: new Date(),
        source: 'explicit',
        version,
        ...metadata,
      };

      await this.consentStore.save(record);

      this.emit('consent:recorded', record);
    }

    // Audit log
    await this.auditLog.log({
      action: 'consent_recorded',
      userId,
      details: consents,
    });
  }

  // Check if user has given consent for a purpose
  async hasConsent(userId: string, purpose: string): Promise<boolean> {
    const consent = await this.consentStore.getLatest(userId, purpose);

    if (!consent) {
      // Check if purpose is required
      const purposeConfig = this.purposes.find(p => p.id === purpose);
      return purposeConfig?.required ?? false;
    }

    return consent.granted;
  }

  // Withdraw consent
  async withdrawConsent(userId: string, purpose: string): Promise<void> {
    const purposeConfig = this.purposes.find(p => p.id === purpose);

    if (purposeConfig?.required) {
      throw new Error('Cannot withdraw consent for required purposes');
    }

    await this.recordConsent(
      userId,
      { [purpose]: false },
      { source: 'withdrawal' }
    );

    this.emit('consent:withdrawn', { userId, purpose });

    // Trigger data processing stop
    await this.stopProcessing(userId, purpose);
  }

  // Get consent status for all purposes
  async getConsentStatus(userId: string): Promise<Record<string, boolean>> {
    const status: Record<string, boolean> = {};

    for (const purpose of this.purposes) {
      status[purpose.id] = await this.hasConsent(userId, purpose.id);
    }

    return status;
  }

  // Export consent history
  async exportConsentHistory(userId: string): Promise<ConsentRecord[]> {
    return this.consentStore.getHistory(userId);
  }
}
```

## Right to Access (Article 15)

```typescript
// services/data-access.service.ts
export class DataAccessService {
  constructor(
    private userRepository: UserRepository,
    private dataRepositories: Map<string, DataRepository>
  ) {}

  // Generate complete data export
  async generateDataExport(userId: string): Promise<DataExport> {
    const user = await this.userRepository.findById(userId);

    if (!user) {
      throw new Error('User not found');
    }

    const export_data: DataExport = {
      exportDate: new Date(),
      userId,
      format: 'json',
      categories: {},
    };

    // Collect data from all sources
    for (const [category, repository] of this.dataRepositories) {
      export_data.categories[category] = await repository.findByUserId(userId);
    }

    // Include processing information
    export_data.processingInfo = {
      purposes: await this.getProcessingPurposes(userId),
      recipients: await this.getDataRecipients(userId),
      retentionPeriods: this.getRetentionPeriods(),
      rights: this.getDataSubjectRights(),
    };

    // Log the access request
    await this.auditLog.log({
      action: 'data_export_generated',
      userId,
      timestamp: new Date(),
    });

    return export_data;
  }

  // Generate human-readable report
  async generateReadableReport(userId: string): Promise<string> {
    const data = await this.generateDataExport(userId);

    return this.formatAsReadableDocument(data);
  }

  // Generate machine-readable format
  async generateMachineReadable(
    userId: string,
    format: 'json' | 'xml' | 'csv'
  ): Promise<Buffer> {
    const data = await this.generateDataExport(userId);

    switch (format) {
      case 'json':
        return Buffer.from(JSON.stringify(data, null, 2));
      case 'xml':
        return this.convertToXml(data);
      case 'csv':
        return this.convertToCsv(data);
    }
  }

  private getDataSubjectRights(): string[] {
    return [
      'Right to access your personal data',
      'Right to rectification of inaccurate data',
      'Right to erasure ("right to be forgotten")',
      'Right to restrict processing',
      'Right to data portability',
      'Right to object to processing',
      'Rights related to automated decision-making',
    ];
  }
}
```

## Right to Erasure (Article 17)

```typescript
// services/data-erasure.service.ts
interface ErasureRequest {
  userId: string;
  requestedAt: Date;
  reason: string;
  status: 'pending' | 'processing' | 'completed' | 'rejected';
  completedAt?: Date;
  retainedData?: RetainedDataRecord[];
}

interface RetainedDataRecord {
  category: string;
  reason: string;
  legalBasis: string;
  retentionPeriod: string;
}

export class DataErasureService {
  private readonly LEGAL_RETENTION_REASONS = [
    'legal_obligation',
    'public_interest',
    'legal_claims',
    'freedom_of_expression',
  ];

  constructor(
    private userRepository: UserRepository,
    private dataRepositories: Map<string, DataRepository>,
    private auditLog: AuditLogService
  ) {}

  // Process erasure request
  async processErasureRequest(userId: string, reason: string): Promise<ErasureRequest> {
    const request: ErasureRequest = {
      userId,
      requestedAt: new Date(),
      reason,
      status: 'pending',
      retainedData: [],
    };

    // Validate request
    const user = await this.userRepository.findById(userId);
    if (!user) {
      throw new Error('User not found');
    }

    request.status = 'processing';

    // Process each data category
    for (const [category, repository] of this.dataRepositories) {
      const canErase = await this.canEraseCategory(userId, category);

      if (canErase.allowed) {
        await this.eraseData(repository, userId);
      } else {
        request.retainedData!.push({
          category,
          reason: canErase.reason!,
          legalBasis: canErase.legalBasis!,
          retentionPeriod: canErase.retentionPeriod!,
        });
      }
    }

    // Anonymize user account
    await this.anonymizeUser(userId);

    // Complete request
    request.status = 'completed';
    request.completedAt = new Date();

    // Audit log
    await this.auditLog.log({
      action: 'erasure_completed',
      userId,
      retainedData: request.retainedData,
    });

    return request;
  }

  // Check if data category can be erased
  private async canEraseCategory(
    userId: string,
    category: string
  ): Promise<{
    allowed: boolean;
    reason?: string;
    legalBasis?: string;
    retentionPeriod?: string;
  }> {
    // Check legal retention requirements
    const retentionRules = this.getRetentionRules(category);

    if (retentionRules.legalRetention) {
      return {
        allowed: false,
        reason: 'Legal retention requirement',
        legalBasis: retentionRules.legalBasis,
        retentionPeriod: retentionRules.period,
      };
    }

    // Check for active legal proceedings
    const hasLegalHold = await this.checkLegalHold(userId, category);
    if (hasLegalHold) {
      return {
        allowed: false,
        reason: 'Active legal hold',
        legalBasis: 'Legal proceedings',
        retentionPeriod: 'Until case resolved',
      };
    }

    return { allowed: true };
  }

  // Anonymize user data
  private async anonymizeUser(userId: string): Promise<void> {
    await this.userRepository.update(userId, {
      email: `deleted_${userId}@anonymized.local`,
      name: '[DELETED]',
      phone: null,
      address: null,
      deletedAt: new Date(),
      isDeleted: true,
    });
  }

  // Erase data from repository
  private async eraseData(
    repository: DataRepository,
    userId: string
  ): Promise<void> {
    await repository.deleteByUserId(userId);
  }
}
```

## Data Portability (Article 20)

```typescript
// services/data-portability.service.ts
export class DataPortabilityService {
  // Export data in portable format
  async exportPortableData(userId: string): Promise<Buffer> {
    const data = await this.collectUserData(userId);

    // Create structured, machine-readable format
    const portableData = {
      exportInfo: {
        exportDate: new Date().toISOString(),
        format: 'JSON-LD',
        schema: 'https://schema.org/Person',
        version: '1.0',
      },
      personalData: this.formatAsJsonLd(data.personal),
      activityData: data.activity,
      preferencesData: data.preferences,
      contentData: data.content,
    };

    return Buffer.from(JSON.stringify(portableData, null, 2));
  }

  // Transfer data to another controller
  async transferData(
    userId: string,
    targetController: string,
    targetEndpoint: string
  ): Promise<TransferResult> {
    // Verify target controller
    const isVerified = await this.verifyController(targetController);
    if (!isVerified) {
      throw new Error('Target controller not verified');
    }

    // Get portable data
    const data = await this.exportPortableData(userId);

    // Encrypt for transfer
    const encrypted = await this.encryptForTransfer(data, targetController);

    // Transfer data
    const result = await this.performTransfer(encrypted, targetEndpoint);

    // Audit log
    await this.auditLog.log({
      action: 'data_transferred',
      userId,
      targetController,
      timestamp: new Date(),
    });

    return result;
  }

  // Format data using JSON-LD schema
  private formatAsJsonLd(personal: PersonalData): object {
    return {
      '@context': 'https://schema.org',
      '@type': 'Person',
      name: personal.name,
      email: personal.email,
      telephone: personal.phone,
      address: personal.address
        ? {
            '@type': 'PostalAddress',
            streetAddress: personal.address.street,
            addressLocality: personal.address.city,
            postalCode: personal.address.zip,
            addressCountry: personal.address.country,
          }
        : undefined,
    };
  }
}
```

## Privacy by Design

```typescript
// decorators/privacy.decorator.ts
export function PersonalData(options: {
  purpose: string;
  retention: string;
  encrypted?: boolean;
}) {
  return function (target: any, propertyKey: string) {
    Reflect.defineMetadata('personalData', options, target, propertyKey);
  };
}

export function SensitiveData(category: string) {
  return function (target: any, propertyKey: string) {
    Reflect.defineMetadata('sensitiveData', category, target, propertyKey);
  };
}

// Usage in entity
class User {
  @PersonalData({
    purpose: 'account_management',
    retention: '3_years_after_deletion',
    encrypted: true,
  })
  email: string;

  @PersonalData({
    purpose: 'communication',
    retention: '1_year_after_last_contact',
  })
  phone: string;

  @SensitiveData('health')
  medicalInfo?: string;
}

// Privacy impact assessment
export class PrivacyImpactAssessment {
  async assessEntity(entityClass: any): Promise<PIAReport> {
    const fields = Object.keys(new entityClass());
    const report: PIAReport = {
      entityName: entityClass.name,
      personalDataFields: [],
      sensitiveDataFields: [],
      recommendations: [],
    };

    for (const field of fields) {
      const personalMeta = Reflect.getMetadata('personalData', entityClass.prototype, field);
      const sensitiveMeta = Reflect.getMetadata('sensitiveData', entityClass.prototype, field);

      if (personalMeta) {
        report.personalDataFields.push({
          field,
          ...personalMeta,
        });
      }

      if (sensitiveMeta) {
        report.sensitiveDataFields.push({
          field,
          category: sensitiveMeta,
        });
      }
    }

    // Generate recommendations
    report.recommendations = this.generateRecommendations(report);

    return report;
  }
}
```

## Data Processing Records (Article 30)

```typescript
// services/processing-records.service.ts
interface ProcessingActivity {
  id: string;
  name: string;
  purposes: string[];
  legalBasis: string;
  dataCategories: string[];
  dataSubjects: string[];
  recipients: string[];
  thirdCountryTransfers?: {
    country: string;
    safeguards: string;
  }[];
  retentionPeriod: string;
  securityMeasures: string[];
  lastUpdated: Date;
}

export class ProcessingRecordsService {
  private activities: Map<string, ProcessingActivity> = new Map();

  // Register processing activity
  registerActivity(activity: ProcessingActivity): void {
    activity.lastUpdated = new Date();
    this.activities.set(activity.id, activity);
  }

  // Generate Article 30 report
  async generateReport(): Promise<Article30Report> {
    const report: Article30Report = {
      organizationName: process.env.ORGANIZATION_NAME!,
      dpoContact: process.env.DPO_EMAIL!,
      generatedAt: new Date(),
      activities: Array.from(this.activities.values()),
    };

    return report;
  }

  // Export for supervisory authority
  async exportForAuthority(): Promise<Buffer> {
    const report = await this.generateReport();
    return Buffer.from(JSON.stringify(report, null, 2));
  }
}

// Example registration
const processingRecords = new ProcessingRecordsService();

processingRecords.registerActivity({
  id: 'user-registration',
  name: 'User Account Registration',
  purposes: ['Account creation', 'Service delivery'],
  legalBasis: 'Contract performance (Art. 6(1)(b))',
  dataCategories: ['Name', 'Email', 'Password hash'],
  dataSubjects: ['Customers', 'Registered users'],
  recipients: ['Internal staff', 'Email service provider'],
  thirdCountryTransfers: [
    {
      country: 'USA',
      safeguards: 'Standard Contractual Clauses',
    },
  ],
  retentionPeriod: '3 years after account deletion',
  securityMeasures: ['Encryption at rest', 'Access controls', 'Audit logging'],
  lastUpdated: new Date(),
});
```

## Breach Notification (Article 33/34)

```typescript
// services/breach-notification.service.ts
interface DataBreach {
  id: string;
  detectedAt: Date;
  nature: string;
  categoriesAffected: string[];
  approximateSubjects: number;
  consequences: string[];
  measuresTaken: string[];
  dpoNotified: boolean;
  authorityNotified: boolean;
  subjectsNotified: boolean;
}

export class BreachNotificationService {
  private readonly AUTHORITY_NOTIFICATION_DEADLINE = 72 * 60 * 60 * 1000; // 72 hours

  constructor(
    private notificationService: NotificationService,
    private auditLog: AuditLogService
  ) {}

  // Report a data breach
  async reportBreach(breach: Omit<DataBreach, 'id'>): Promise<DataBreach> {
    const breachRecord: DataBreach = {
      ...breach,
      id: this.generateBreachId(),
      dpoNotified: false,
      authorityNotified: false,
      subjectsNotified: false,
    };

    // Immediate DPO notification
    await this.notifyDPO(breachRecord);
    breachRecord.dpoNotified = true;

    // Assess risk
    const riskLevel = this.assessRisk(breachRecord);

    // Notify authority if required (within 72 hours)
    if (riskLevel !== 'unlikely') {
      await this.scheduleAuthorityNotification(breachRecord);
    }

    // Notify affected individuals if high risk
    if (riskLevel === 'high') {
      await this.notifyAffectedSubjects(breachRecord);
      breachRecord.subjectsNotified = true;
    }

    // Log breach
    await this.auditLog.log({
      action: 'breach_reported',
      breachId: breachRecord.id,
      riskLevel,
      details: breachRecord,
    });

    return breachRecord;
  }

  // Assess breach risk level
  private assessRisk(breach: DataBreach): 'unlikely' | 'likely' | 'high' {
    // High risk if sensitive data involved
    const sensitiveCategories = [
      'health',
      'financial',
      'biometric',
      'children',
    ];
    const hasSensitive = breach.categoriesAffected.some(c =>
      sensitiveCategories.includes(c.toLowerCase())
    );

    if (hasSensitive || breach.approximateSubjects > 10000) {
      return 'high';
    }

    if (breach.approximateSubjects > 100) {
      return 'likely';
    }

    return 'unlikely';
  }

  // Notify supervisory authority
  async notifyAuthority(breach: DataBreach): Promise<void> {
    const notification = {
      organizationName: process.env.ORGANIZATION_NAME,
      dpoContact: process.env.DPO_EMAIL,
      breachDetails: {
        nature: breach.nature,
        categoriesAffected: breach.categoriesAffected,
        approximateSubjects: breach.approximateSubjects,
        consequences: breach.consequences,
        measuresTaken: breach.measuresTaken,
      },
      detectedAt: breach.detectedAt,
      reportedAt: new Date(),
    };

    // Submit to authority
    await this.submitToAuthority(notification);

    await this.auditLog.log({
      action: 'authority_notified',
      breachId: breach.id,
    });
  }

  // Notify affected individuals
  private async notifyAffectedSubjects(breach: DataBreach): Promise<void> {
    const affectedUsers = await this.getAffectedUsers(breach);

    for (const user of affectedUsers) {
      await this.notificationService.send({
        to: user.email,
        subject: 'Important: Data Security Incident',
        template: 'breach-notification',
        data: {
          userName: user.name,
          breachNature: breach.nature,
          consequences: breach.consequences,
          measuresTaken: breach.measuresTaken,
          dpoContact: process.env.DPO_EMAIL,
        },
      });
    }
  }
}
```

## Cookie Compliance

```typescript
// middleware/cookie-consent.middleware.ts
export function cookieConsentMiddleware(consentService: ConsentService) {
  return async (req: Request, res: Response, next: NextFunction) => {
    const consentCookie = req.cookies['cookie_consent'];

    if (!consentCookie) {
      // No consent given, only essential cookies
      res.locals.allowedCookies = ['essential'];
    } else {
      const consent = JSON.parse(consentCookie);
      res.locals.allowedCookies = Object.entries(consent)
        .filter(([, allowed]) => allowed)
        .map(([category]) => category);
    }

    // Provide consent banner status
    res.locals.showConsentBanner = !consentCookie;

    next();
  };
}

// Cookie configuration
export const cookieConfig = {
  essential: {
    sessionId: {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
      maxAge: 24 * 60 * 60 * 1000, // 24 hours
    },
    csrfToken: {
      httpOnly: true,
      secure: true,
      sameSite: 'strict',
    },
  },
  analytics: {
    _ga: {
      maxAge: 2 * 365 * 24 * 60 * 60 * 1000, // 2 years
      requires: 'analytics',
    },
  },
  marketing: {
    _fbp: {
      maxAge: 90 * 24 * 60 * 60 * 1000, // 90 days
      requires: 'marketing',
    },
  },
};
```

## Compliance Checklist

```yaml
# gdpr-compliance-checklist.yaml
lawful_basis:
  - consent_mechanism_implemented
  - legitimate_interest_assessment
  - contract_performance_documented

data_subject_rights:
  - right_to_access_implemented
  - right_to_rectification_implemented
  - right_to_erasure_implemented
  - right_to_portability_implemented
  - right_to_object_implemented

technical_measures:
  - encryption_at_rest
  - encryption_in_transit
  - access_controls
  - audit_logging
  - pseudonymization

organizational_measures:
  - privacy_policy_updated
  - dpo_appointed
  - staff_training
  - vendor_agreements
  - processing_records

breach_procedures:
  - detection_mechanisms
  - notification_process
  - documentation_templates
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Data minimization | Only collect necessary data |
| Purpose limitation | Use data only for stated purposes |
| Storage limitation | Implement retention policies |
| Privacy by design | Build privacy into systems |
| Regular audits | Assess compliance periodically |
| Staff training | Ensure awareness of obligations |
