# Compliance

GDPR, PCI-DSS, security audits, and regulatory compliance patterns.

## Table of Contents

1. [GDPR Compliance](#gdpr-compliance)
2. [PCI-DSS Compliance](#pci-dss-compliance)
3. [Security Auditing](#security-auditing)
4. [Compliance Automation](#compliance-automation)
5. [Documentation Requirements](#documentation-requirements)

---

## GDPR Compliance

### Data Subject Rights Implementation

```typescript
interface DataSubjectRequest {
  id: string;
  type: 'access' | 'rectification' | 'erasure' | 'portability' | 'restriction' | 'objection';
  subjectId: string;
  subjectEmail: string;
  requestedAt: Date;
  deadline: Date; // 30 days from request
  status: 'pending' | 'in_progress' | 'completed' | 'rejected';
  completedAt?: Date;
  notes?: string;
}

export class GDPRService {
  // Right to Access (Article 15)
  async handleAccessRequest(subjectId: string): Promise<{
    personalData: Record<string, any>;
    processingPurposes: string[];
    dataCategories: string[];
    recipients: string[];
    retentionPeriod: string;
    dataSource: string;
  }> {
    const user = await this.userRepository.findById(subjectId);
    const activities = await this.activityRepository.findByUserId(subjectId);
    const consents = await this.consentRepository.findByUserId(subjectId);

    return {
      personalData: {
        profile: this.sanitizeForExport(user),
        activities: activities.map(a => this.sanitizeForExport(a)),
        consents: consents,
      },
      processingPurposes: [
        'Service provision',
        'Communication',
        'Analytics',
      ],
      dataCategories: [
        'Identity data',
        'Contact data',
        'Usage data',
      ],
      recipients: [
        'Payment processors',
        'Email service providers',
      ],
      retentionPeriod: '3 years after last activity',
      dataSource: 'Directly from data subject',
    };
  }

  // Right to Erasure (Article 17)
  async handleErasureRequest(subjectId: string): Promise<{
    deleted: string[];
    retained: { category: string; reason: string }[];
  }> {
    const deleted: string[] = [];
    const retained: { category: string; reason: string }[] = [];

    // Delete non-essential data
    await this.activityRepository.deleteByUserId(subjectId);
    deleted.push('Activity logs');

    await this.preferencesRepository.deleteByUserId(subjectId);
    deleted.push('User preferences');

    // Anonymize instead of delete for legal requirements
    await this.orderRepository.anonymizeByUserId(subjectId);
    retained.push({
      category: 'Order records',
      reason: 'Legal requirement: Tax records retention (7 years)',
    });

    // Soft delete user account
    await this.userRepository.softDelete(subjectId);
    deleted.push('User account');

    return { deleted, retained };
  }

  // Right to Data Portability (Article 20)
  async handlePortabilityRequest(subjectId: string): Promise<Buffer> {
    const data = await this.handleAccessRequest(subjectId);

    // Return in machine-readable format (JSON)
    const exportData = {
      exportedAt: new Date().toISOString(),
      format: 'JSON',
      data: data.personalData,
    };

    return Buffer.from(JSON.stringify(exportData, null, 2));
  }

  // Right to Rectification (Article 16)
  async handleRectificationRequest(
    subjectId: string,
    corrections: Record<string, any>
  ): Promise<void> {
    const allowedFields = ['name', 'email', 'phone', 'address'];

    const validCorrections = Object.entries(corrections)
      .filter(([key]) => allowedFields.includes(key))
      .reduce((acc, [key, value]) => ({ ...acc, [key]: value }), {});

    await this.userRepository.update(subjectId, validCorrections);

    await this.auditService.log({
      action: 'gdpr_rectification',
      subjectId,
      changes: validCorrections,
    });
  }

  private sanitizeForExport(data: any): any {
    // Remove internal fields
    const { password, internalNotes, ...exportable } = data;
    return exportable;
  }
}
```

### Consent Management

```typescript
interface Consent {
  id: string;
  userId: string;
  purpose: string;
  description: string;
  granted: boolean;
  grantedAt?: Date;
  revokedAt?: Date;
  expiresAt?: Date;
  version: string;
  ipAddress: string;
  userAgent: string;
}

export class ConsentService {
  private readonly consentPurposes = {
    marketing: {
      name: 'Marketing Communications',
      description: 'Receive promotional emails and offers',
      required: false,
    },
    analytics: {
      name: 'Analytics',
      description: 'Help us improve our service through usage analysis',
      required: false,
    },
    essential: {
      name: 'Essential Cookies',
      description: 'Required for the website to function',
      required: true,
    },
  };

  async grantConsent(
    userId: string,
    purpose: string,
    context: { ip: string; userAgent: string }
  ): Promise<Consent> {
    const consent: Consent = {
      id: crypto.randomUUID(),
      userId,
      purpose,
      description: this.consentPurposes[purpose as keyof typeof this.consentPurposes]?.description,
      granted: true,
      grantedAt: new Date(),
      version: '1.0',
      ipAddress: context.ip,
      userAgent: context.userAgent,
    };

    await this.consentRepository.save(consent);

    return consent;
  }

  async revokeConsent(userId: string, purpose: string): Promise<void> {
    await this.consentRepository.update(
      { userId, purpose },
      { granted: false, revokedAt: new Date() }
    );
  }

  async hasConsent(userId: string, purpose: string): Promise<boolean> {
    const consent = await this.consentRepository.findOne({ userId, purpose });
    return consent?.granted === true && !consent.revokedAt;
  }

  async getConsentStatus(userId: string): Promise<Record<string, boolean>> {
    const consents = await this.consentRepository.findByUserId(userId);
    return consents.reduce(
      (acc, c) => ({ ...acc, [c.purpose]: c.granted && !c.revokedAt }),
      {}
    );
  }
}
```

### Privacy by Design

```typescript
// Data minimization - only collect necessary data
const registrationSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  // Only required fields, no optional collection
});

// Purpose limitation - track why data is collected
interface DataField {
  name: string;
  purpose: string;
  legalBasis: 'consent' | 'contract' | 'legal_obligation' | 'legitimate_interest';
  retentionDays: number;
}

const dataInventory: DataField[] = [
  {
    name: 'email',
    purpose: 'Account identification and communication',
    legalBasis: 'contract',
    retentionDays: 1095, // 3 years
  },
  {
    name: 'ip_address',
    purpose: 'Security and fraud prevention',
    legalBasis: 'legitimate_interest',
    retentionDays: 90,
  },
];

// Automatic data retention enforcement
async function enforceRetention(): Promise<void> {
  for (const field of dataInventory) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - field.retentionDays);

    await db.query(
      `UPDATE users SET ${field.name} = NULL
       WHERE last_activity < $1 AND ${field.name} IS NOT NULL`,
      [cutoffDate]
    );

    logger.info(`Retention enforced for ${field.name}`, { cutoffDate });
  }
}
```

---

## PCI-DSS Compliance

### Secure Card Data Handling

```typescript
// Never store full card numbers - use tokenization
export class PaymentService {
  constructor(private stripeClient: Stripe) {}

  async createPaymentMethod(
    cardDetails: { number: string; exp_month: number; exp_year: number; cvc: string }
  ): Promise<string> {
    // Card details go directly to Stripe, never touch our servers
    // Use Stripe.js or Elements on frontend instead

    throw new Error(
      'Do not pass card details to backend. Use Stripe.js on frontend.'
    );
  }

  async processPayment(
    customerId: string,
    paymentMethodId: string, // Token, not card number
    amount: number
  ): Promise<PaymentResult> {
    const paymentIntent = await this.stripeClient.paymentIntents.create({
      amount: Math.round(amount * 100),
      currency: 'usd',
      customer: customerId,
      payment_method: paymentMethodId,
      confirm: true,
    });

    // Log transaction without sensitive data
    await this.auditLog.record({
      action: 'payment_processed',
      customerId,
      amount,
      paymentIntentId: paymentIntent.id,
      status: paymentIntent.status,
      last4: paymentIntent.payment_method_details?.card?.last4,
    });

    return {
      success: paymentIntent.status === 'succeeded',
      transactionId: paymentIntent.id,
    };
  }
}

// Frontend: Use Stripe Elements
// <script src="https://js.stripe.com/v3/"></script>
// const stripe = Stripe('pk_live_xxx');
// const elements = stripe.elements();
// const cardElement = elements.create('card');
```

### PCI DSS Requirements Checklist

```typescript
interface PCIRequirement {
  requirement: string;
  controls: string[];
  implemented: boolean;
  evidence: string[];
}

const pciRequirements: PCIRequirement[] = [
  {
    requirement: '1. Install and maintain firewall',
    controls: [
      'Network segmentation',
      'Firewall rules documented',
      'Default deny policy',
    ],
    implemented: true,
    evidence: ['firewall-config.pdf', 'network-diagram.pdf'],
  },
  {
    requirement: '2. Change vendor defaults',
    controls: [
      'Default passwords changed',
      'Unnecessary services disabled',
      'Security parameters configured',
    ],
    implemented: true,
    evidence: ['hardening-checklist.pdf'],
  },
  {
    requirement: '3. Protect stored cardholder data',
    controls: [
      'No PAN storage (tokenization)',
      'Encryption at rest (if stored)',
      'Key management procedures',
    ],
    implemented: true,
    evidence: ['tokenization-architecture.pdf'],
  },
  {
    requirement: '4. Encrypt transmission',
    controls: [
      'TLS 1.2+ only',
      'Strong ciphers',
      'Certificate management',
    ],
    implemented: true,
    evidence: ['ssl-config.pdf', 'cert-inventory.xlsx'],
  },
  {
    requirement: '6. Develop secure systems',
    controls: [
      'Secure coding guidelines',
      'Code review process',
      'Vulnerability management',
    ],
    implemented: true,
    evidence: ['sdlc-policy.pdf', 'code-review-logs/'],
  },
  {
    requirement: '8. Identify and authenticate access',
    controls: [
      'Unique user IDs',
      'Strong authentication',
      'MFA for admin access',
    ],
    implemented: true,
    evidence: ['access-policy.pdf', 'mfa-config.pdf'],
  },
  {
    requirement: '10. Track and monitor access',
    controls: [
      'Audit logging enabled',
      'Log review procedures',
      'Alert mechanisms',
    ],
    implemented: true,
    evidence: ['logging-config.pdf', 'siem-dashboard.pdf'],
  },
];
```

### Network Segmentation

```typescript
// Cardholder Data Environment (CDE) isolation
// infrastructure/cde-network.tf (Terraform)

/*
resource "aws_vpc" "cde" {
  cidr_block = "10.1.0.0/16"

  tags = {
    Name = "PCI-CDE-VPC"
    PCI_Scope = "in-scope"
  }
}

resource "aws_security_group" "payment_api" {
  name        = "payment-api-sg"
  description = "Payment API security group"
  vpc_id      = aws_vpc.cde.id

  # Only allow from specific sources
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_subnet.app_subnet.cidr_block]
    description = "HTTPS from app tier only"
  }

  # No direct internet access
  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # To payment processor
    description = "HTTPS to payment processor"
  }
}
*/

// API validation for CDE endpoints
function validateCDERequest(req: Request, res: Response, next: NextFunction) {
  // Verify request comes from trusted source
  const allowedIPs = process.env.CDE_ALLOWED_IPS?.split(',') || [];

  if (!allowedIPs.includes(req.ip)) {
    logger.warn('Unauthorized CDE access attempt', { ip: req.ip });
    return res.status(403).json({ error: 'Access denied' });
  }

  // Verify authentication
  if (!req.headers.authorization) {
    return res.status(401).json({ error: 'Authentication required' });
  }

  next();
}
```

---

## Security Auditing

### Automated Security Scanning

```typescript
// Security scan configuration
interface SecurityScanConfig {
  sast: {
    enabled: boolean;
    tool: string;
    rules: string[];
  };
  dast: {
    enabled: boolean;
    tool: string;
    targetUrl: string;
  };
  dependency: {
    enabled: boolean;
    tool: string;
    failOnSeverity: string;
  };
  secrets: {
    enabled: boolean;
    tool: string;
  };
}

const scanConfig: SecurityScanConfig = {
  sast: {
    enabled: true,
    tool: 'semgrep',
    rules: ['p/security-audit', 'p/owasp-top-ten'],
  },
  dast: {
    enabled: true,
    tool: 'zap',
    targetUrl: process.env.DAST_TARGET_URL!,
  },
  dependency: {
    enabled: true,
    tool: 'npm-audit',
    failOnSeverity: 'high',
  },
  secrets: {
    enabled: true,
    tool: 'gitleaks',
  },
};

// CI/CD pipeline integration
/*
# .github/workflows/security.yml

name: Security Scan

on: [push, pull_request]

jobs:
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: p/security-audit p/owasp-top-ten

  dependency-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run npm audit
        run: npm audit --audit-level=high

  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2

  dast:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: ZAP Scan
        uses: zaproxy/action-full-scan@v0.4.0
        with:
          target: ${{ secrets.STAGING_URL }}
*/
```

### Vulnerability Management

```typescript
interface Vulnerability {
  id: string;
  source: 'sast' | 'dast' | 'dependency' | 'pentest' | 'bug_bounty';
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  title: string;
  description: string;
  affectedComponent: string;
  cve?: string;
  cwe?: string;
  discoveredAt: Date;
  status: 'open' | 'in_progress' | 'resolved' | 'accepted_risk' | 'false_positive';
  assignedTo?: string;
  resolvedAt?: Date;
  slaDeadline: Date;
}

class VulnerabilityService {
  private readonly slaDays = {
    critical: 1,
    high: 7,
    medium: 30,
    low: 90,
    info: 180,
  };

  async create(vuln: Omit<Vulnerability, 'id' | 'slaDeadline'>): Promise<Vulnerability> {
    const slaDeadline = new Date();
    slaDeadline.setDate(slaDeadline.getDate() + this.slaDays[vuln.severity]);

    const vulnerability: Vulnerability = {
      id: crypto.randomUUID(),
      slaDeadline,
      ...vuln,
    };

    await this.repository.save(vulnerability);

    // Alert based on severity
    if (vuln.severity === 'critical') {
      await this.alertService.sendCriticalVulnAlert(vulnerability);
    }

    return vulnerability;
  }

  async getOverdueSLA(): Promise<Vulnerability[]> {
    return this.repository.find({
      status: { $in: ['open', 'in_progress'] },
      slaDeadline: { $lt: new Date() },
    });
  }

  async generateReport(startDate: Date, endDate: Date): Promise<VulnerabilityReport> {
    const vulnerabilities = await this.repository.find({
      discoveredAt: { $gte: startDate, $lte: endDate },
    });

    return {
      period: { start: startDate, end: endDate },
      total: vulnerabilities.length,
      bySeverity: this.groupBy(vulnerabilities, 'severity'),
      byStatus: this.groupBy(vulnerabilities, 'status'),
      bySource: this.groupBy(vulnerabilities, 'source'),
      avgTimeToResolve: this.calculateAvgResolutionTime(vulnerabilities),
      slaCompliance: this.calculateSLACompliance(vulnerabilities),
    };
  }
}
```

### Penetration Testing

```typescript
interface PenTestReport {
  id: string;
  testType: 'external' | 'internal' | 'web_app' | 'mobile' | 'social_engineering';
  vendor: string;
  startDate: Date;
  endDate: Date;
  scope: string[];
  findings: PenTestFinding[];
  executiveSummary: string;
  recommendations: string[];
}

interface PenTestFinding {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  cvssScore?: number;
  description: string;
  impact: string;
  recommendation: string;
  evidence: string[];
  status: 'open' | 'remediated' | 'accepted_risk';
}

// Pentest finding tracking
class PenTestService {
  async importFindings(report: PenTestReport): Promise<void> {
    for (const finding of report.findings) {
      // Create vulnerability record
      await this.vulnerabilityService.create({
        source: 'pentest',
        severity: finding.severity,
        title: finding.title,
        description: finding.description,
        affectedComponent: finding.evidence.join(', '),
        discoveredAt: report.endDate,
        status: 'open',
      });
    }

    // Store full report
    await this.reportRepository.save({
      ...report,
      importedAt: new Date(),
    });
  }

  async scheduleRetesting(
    reportId: string,
    findingIds: string[]
  ): Promise<Date> {
    // Schedule retest 30 days after remediation
    const retestDate = new Date();
    retestDate.setDate(retestDate.getDate() + 30);

    await this.retestRepository.save({
      originalReportId: reportId,
      findingIds,
      scheduledDate: retestDate,
      status: 'scheduled',
    });

    return retestDate;
  }
}
```

---

## Compliance Automation

### Policy as Code

```typescript
// Define compliance policies in code
interface CompliancePolicy {
  id: string;
  name: string;
  description: string;
  framework: 'gdpr' | 'pci-dss' | 'hipaa' | 'soc2';
  checks: ComplianceCheck[];
}

interface ComplianceCheck {
  id: string;
  name: string;
  automated: boolean;
  checkFunction?: () => Promise<CheckResult>;
  manualEvidence?: string;
}

interface CheckResult {
  passed: boolean;
  details: string;
  evidence?: any;
}

const gdprPolicy: CompliancePolicy = {
  id: 'gdpr-v1',
  name: 'GDPR Compliance',
  description: 'General Data Protection Regulation requirements',
  framework: 'gdpr',
  checks: [
    {
      id: 'gdpr-consent-mechanism',
      name: 'Consent mechanism implemented',
      automated: true,
      checkFunction: async () => {
        const consentEndpoint = await fetch('/api/consent');
        return {
          passed: consentEndpoint.status === 200,
          details: 'Consent API endpoint accessible',
        };
      },
    },
    {
      id: 'gdpr-data-encryption',
      name: 'Personal data encrypted at rest',
      automated: true,
      checkFunction: async () => {
        const dbConfig = await getDatabaseConfig();
        return {
          passed: dbConfig.encryption === 'AES-256',
          details: `Encryption: ${dbConfig.encryption}`,
          evidence: { algorithm: dbConfig.encryption },
        };
      },
    },
    {
      id: 'gdpr-dpo-appointed',
      name: 'Data Protection Officer appointed',
      automated: false,
      manualEvidence: 'DPO appointment letter',
    },
  ],
};

// Run compliance checks
async function runComplianceAudit(policy: CompliancePolicy): Promise<AuditReport> {
  const results: CheckResult[] = [];

  for (const check of policy.checks) {
    if (check.automated && check.checkFunction) {
      const result = await check.checkFunction();
      results.push(result);
    }
  }

  const passedCount = results.filter(r => r.passed).length;
  const automatedCount = policy.checks.filter(c => c.automated).length;

  return {
    policyId: policy.id,
    runDate: new Date(),
    automatedPassed: passedCount,
    automatedTotal: automatedCount,
    complianceScore: (passedCount / automatedCount) * 100,
    results,
  };
}
```

### Continuous Compliance Monitoring

```typescript
import cron from 'node-cron';

class ComplianceMonitor {
  constructor(
    private policies: CompliancePolicy[],
    private alertService: AlertService
  ) {}

  start(): void {
    // Run daily compliance checks
    cron.schedule('0 2 * * *', async () => {
      await this.runAllChecks();
    });

    // Run critical checks hourly
    cron.schedule('0 * * * *', async () => {
      await this.runCriticalChecks();
    });
  }

  private async runAllChecks(): Promise<void> {
    for (const policy of this.policies) {
      const report = await runComplianceAudit(policy);

      // Alert on compliance issues
      if (report.complianceScore < 100) {
        await this.alertService.send({
          severity: report.complianceScore < 80 ? 'critical' : 'warning',
          title: `Compliance issue: ${policy.name}`,
          message: `Score: ${report.complianceScore}%`,
          metadata: report,
        });
      }

      // Store report
      await this.reportRepository.save(report);
    }
  }

  private async runCriticalChecks(): Promise<void> {
    const criticalChecks = [
      this.checkEncryptionEnabled,
      this.checkAccessLogsEnabled,
      this.checkMFAEnforced,
    ];

    for (const check of criticalChecks) {
      const result = await check();
      if (!result.passed) {
        await this.alertService.sendCritical({
          title: 'Critical compliance failure',
          details: result.details,
        });
      }
    }
  }
}
```

---

## Documentation Requirements

### Security Documentation

```typescript
interface SecurityDocumentation {
  policies: {
    informationSecurityPolicy: string;
    acceptableUsePolicy: string;
    accessControlPolicy: string;
    incidentResponsePlan: string;
    businessContinuityPlan: string;
    dataClassificationPolicy: string;
  };
  procedures: {
    changeManagement: string;
    vulnerabilityManagement: string;
    patchManagement: string;
    backupAndRecovery: string;
    userAccessReview: string;
  };
  records: {
    riskAssessments: string;
    auditReports: string;
    incidentReports: string;
    trainingRecords: string;
    thirdPartyAssessments: string;
  };
}

// Documentation template generator
function generateSecurityPolicy(template: string, variables: Record<string, string>): string {
  let content = template;
  for (const [key, value] of Object.entries(variables)) {
    content = content.replace(new RegExp(`{{${key}}}`, 'g'), value);
  }
  return content;
}

const accessControlPolicyTemplate = `
# Access Control Policy

**Version:** {{version}}
**Effective Date:** {{effectiveDate}}
**Owner:** {{owner}}

## 1. Purpose
This policy establishes access control requirements for {{companyName}} systems.

## 2. Scope
All employees, contractors, and third parties with access to {{companyName}} systems.

## 3. Policy

### 3.1 User Access Management
- All access requests require manager approval
- Access is granted based on least privilege principle
- Access reviews conducted quarterly

### 3.2 Authentication Requirements
- Minimum password length: {{minPasswordLength}} characters
- Password complexity: uppercase, lowercase, number, special character
- MFA required for: {{mfaRequiredFor}}
- Session timeout: {{sessionTimeout}} minutes

### 3.3 Privileged Access
- Admin access requires additional approval
- All admin actions are logged
- Admin accounts reviewed monthly

## 4. Compliance
Violations may result in disciplinary action up to termination.

## 5. Review
This policy is reviewed annually or upon significant changes.
`;
```

### Evidence Collection

```typescript
interface ComplianceEvidence {
  requirementId: string;
  evidenceType: 'screenshot' | 'config' | 'log' | 'document' | 'attestation';
  description: string;
  collectedAt: Date;
  collectedBy: string;
  content: Buffer | string;
  metadata: Record<string, any>;
}

class EvidenceCollector {
  async collectConfigEvidence(
    requirementId: string,
    configPath: string
  ): Promise<ComplianceEvidence> {
    const config = await fs.readFile(configPath, 'utf8');

    // Redact sensitive values
    const redacted = this.redactSensitiveData(config);

    return {
      requirementId,
      evidenceType: 'config',
      description: `Configuration file: ${configPath}`,
      collectedAt: new Date(),
      collectedBy: 'automated',
      content: redacted,
      metadata: { path: configPath },
    };
  }

  async collectLogEvidence(
    requirementId: string,
    query: string,
    timeRange: { start: Date; end: Date }
  ): Promise<ComplianceEvidence> {
    const logs = await this.logService.query(query, timeRange);

    return {
      requirementId,
      evidenceType: 'log',
      description: `Log query: ${query}`,
      collectedAt: new Date(),
      collectedBy: 'automated',
      content: JSON.stringify(logs, null, 2),
      metadata: { query, timeRange },
    };
  }

  async generateEvidencePackage(auditId: string): Promise<Buffer> {
    const evidence = await this.evidenceRepository.findByAuditId(auditId);

    // Create ZIP archive
    const archive = archiver('zip', { zlib: { level: 9 } });
    const output = new stream.PassThrough();

    archive.pipe(output);

    for (const item of evidence) {
      const filename = `${item.requirementId}_${item.evidenceType}.${this.getExtension(item)}`;
      archive.append(item.content, { name: filename });
    }

    // Add index
    const index = evidence.map(e => ({
      requirement: e.requirementId,
      type: e.evidenceType,
      description: e.description,
      collectedAt: e.collectedAt,
    }));
    archive.append(JSON.stringify(index, null, 2), { name: 'index.json' });

    await archive.finalize();

    return this.streamToBuffer(output);
  }
}
```

---

## Best Practices Summary

| Framework | Key Requirements | Implementation |
|-----------|------------------|----------------|
| GDPR | Data subject rights, consent, DPO | Rights API, consent service, retention |
| PCI-DSS | No card storage, network segmentation | Tokenization, VPC isolation |
| SOC 2 | Security controls, monitoring | Audit logging, access reviews |
| HIPAA | PHI protection, access controls | Encryption, audit trails |

## Compliance Checklist

```markdown
## Pre-Audit Checklist

### Documentation
- [ ] All security policies current and approved
- [ ] Procedures documented and followed
- [ ] Risk assessments up to date
- [ ] Incident reports complete

### Technical Controls
- [ ] Encryption at rest and in transit
- [ ] Access logs enabled and retained
- [ ] Vulnerability scans current
- [ ] Penetration test within 12 months

### Administrative Controls
- [ ] Security awareness training current
- [ ] Background checks completed
- [ ] Access reviews performed
- [ ] Third-party assessments current

### Physical Controls
- [ ] Data center certifications valid
- [ ] Access logs maintained
- [ ] Visitor procedures followed
```
