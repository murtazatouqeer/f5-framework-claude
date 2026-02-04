---
name: security-audit
description: Security audit procedures and frameworks
category: security/compliance
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Security Audit

## Overview

Security audits systematically evaluate an organization's security
controls, policies, and practices to identify vulnerabilities and
ensure compliance with security standards.

## Audit Types

| Type | Scope | Frequency | Conducted By |
|------|-------|-----------|--------------|
| Internal | Controls, policies | Quarterly | Internal team |
| External | Compliance, vulnerabilities | Annually | Third party |
| Penetration Test | Technical security | Annually | Specialists |
| Code Review | Application security | Per release | Dev/Security team |
| Configuration | Infrastructure | Monthly | Operations |

## Audit Framework

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Audit Process                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Planning          2. Information       3. Assessment     │
│  ┌─────────────┐      ┌─────────────┐     ┌─────────────┐   │
│  │ Define Scope│  →   │ Collect Data│  →  │ Analyze     │   │
│  │ Set Goals   │      │ Interview   │     │ Findings    │   │
│  │ Resources   │      │ Document    │     │ Risk Score  │   │
│  └─────────────┘      └─────────────┘     └─────────────┘   │
│         │                    │                    │          │
│         ↓                    ↓                    ↓          │
│  4. Testing           5. Reporting        6. Remediation    │
│  ┌─────────────┐      ┌─────────────┐     ┌─────────────┐   │
│  │ Vuln Scan   │  →   │ Draft Report│  →  │ Fix Issues  │   │
│  │ Pen Test    │      │ Present     │     │ Verify      │   │
│  │ Code Review │      │ Prioritize  │     │ Re-test     │   │
│  └─────────────┘      └─────────────┘     └─────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Audit Planning

```typescript
// services/audit-planning.service.ts
interface AuditPlan {
  id: string;
  name: string;
  type: 'internal' | 'external' | 'pentest' | 'compliance';
  scope: AuditScope;
  schedule: AuditSchedule;
  team: AuditTeamMember[];
  objectives: string[];
  methodology: string;
  status: 'planning' | 'in_progress' | 'completed' | 'cancelled';
}

interface AuditScope {
  systems: string[];
  networks: string[];
  applications: string[];
  dataCategories: string[];
  exclusions: string[];
  compliance: string[]; // GDPR, PCI-DSS, SOC2, etc.
}

interface AuditSchedule {
  startDate: Date;
  endDate: Date;
  phases: AuditPhase[];
  milestones: Milestone[];
}

export class AuditPlanningService {
  // Create audit plan
  async createAuditPlan(input: CreateAuditPlanInput): Promise<AuditPlan> {
    const plan: AuditPlan = {
      id: this.generatePlanId(),
      name: input.name,
      type: input.type,
      scope: this.defineScope(input),
      schedule: this.createSchedule(input),
      team: await this.assignTeam(input),
      objectives: this.defineObjectives(input),
      methodology: this.selectMethodology(input.type),
      status: 'planning',
    };

    await this.planRepository.save(plan);

    // Notify stakeholders
    await this.notifyStakeholders(plan);

    return plan;
  }

  // Define audit scope
  private defineScope(input: CreateAuditPlanInput): AuditScope {
    return {
      systems: this.identifySystems(input.targetArea),
      networks: this.identifyNetworks(input.targetArea),
      applications: this.identifyApplications(input.targetArea),
      dataCategories: this.identifyDataCategories(input.compliance),
      exclusions: input.exclusions || [],
      compliance: input.compliance || [],
    };
  }

  // Select methodology based on audit type
  private selectMethodology(type: string): string {
    const methodologies: Record<string, string> = {
      internal: 'ISO 27001 Internal Audit',
      external: 'AICPA SOC 2 Type II',
      pentest: 'PTES (Penetration Testing Execution Standard)',
      compliance: 'NIST Cybersecurity Framework',
    };

    return methodologies[type] || 'Custom Framework';
  }

  // Risk-based audit prioritization
  async prioritizeAuditAreas(): Promise<AuditPriority[]> {
    const areas = await this.getAuditableAreas();

    return areas.map(area => ({
      area: area.name,
      riskScore: this.calculateRiskScore(area),
      lastAuditDate: area.lastAudit,
      daysSinceAudit: this.daysSince(area.lastAudit),
      priority: this.determinePriority(area),
      recommendedDate: this.recommendAuditDate(area),
    })).sort((a, b) => b.riskScore - a.riskScore);
  }
}
```

## Security Control Assessment

```typescript
// services/control-assessment.service.ts
interface SecurityControl {
  id: string;
  name: string;
  category: string;
  description: string;
  framework: string; // NIST, ISO, CIS
  implementation: 'implemented' | 'partial' | 'planned' | 'not_applicable';
  effectiveness: 'effective' | 'partially_effective' | 'ineffective';
  evidence: Evidence[];
  gaps: Gap[];
}

interface ControlAssessment {
  controlId: string;
  assessedBy: string;
  assessedAt: Date;
  testingPerformed: string[];
  findingsSummary: string;
  rating: number; // 1-5
  recommendations: string[];
}

export class ControlAssessmentService {
  // NIST CSF control categories
  private readonly NIST_CATEGORIES = [
    'Identify',
    'Protect',
    'Detect',
    'Respond',
    'Recover',
  ];

  // Assess control implementation
  async assessControl(controlId: string): Promise<ControlAssessment> {
    const control = await this.controlRepository.findById(controlId);

    // Perform assessment activities
    const documentReview = await this.reviewDocumentation(control);
    const interviews = await this.conductInterviews(control);
    const technicalTesting = await this.performTechnicalTests(control);

    // Aggregate findings
    const assessment: ControlAssessment = {
      controlId,
      assessedBy: this.currentAuditor.id,
      assessedAt: new Date(),
      testingPerformed: [
        'Documentation review',
        'Personnel interviews',
        'Technical testing',
      ],
      findingsSummary: this.summarizeFindings(
        documentReview,
        interviews,
        technicalTesting
      ),
      rating: this.calculateRating(documentReview, interviews, technicalTesting),
      recommendations: this.generateRecommendations(control),
    };

    await this.assessmentRepository.save(assessment);

    return assessment;
  }

  // Assess all controls in a framework
  async assessFramework(framework: string): Promise<FrameworkAssessment> {
    const controls = await this.getControlsByFramework(framework);
    const assessments: ControlAssessment[] = [];

    for (const control of controls) {
      const assessment = await this.assessControl(control.id);
      assessments.push(assessment);
    }

    // Calculate overall maturity
    const maturityScore = this.calculateMaturityScore(assessments);

    return {
      framework,
      assessedAt: new Date(),
      totalControls: controls.length,
      implementedControls: assessments.filter(a => a.rating >= 4).length,
      partialControls: assessments.filter(a => a.rating >= 2 && a.rating < 4).length,
      gapControls: assessments.filter(a => a.rating < 2).length,
      maturityScore,
      assessments,
    };
  }

  // Generate control evidence
  async collectEvidence(controlId: string): Promise<Evidence[]> {
    const evidence: Evidence[] = [];

    // Automated evidence collection
    evidence.push(...await this.collectAutomatedEvidence(controlId));

    // Configuration snapshots
    evidence.push(...await this.captureConfigurations(controlId));

    // Log samples
    evidence.push(...await this.collectLogSamples(controlId));

    // Policy documents
    evidence.push(...await this.gatherPolicyDocs(controlId));

    return evidence;
  }
}
```

## Vulnerability Assessment

```typescript
// services/vulnerability-assessment.service.ts
interface VulnerabilityAssessment {
  id: string;
  startedAt: Date;
  completedAt?: Date;
  scope: AssessmentScope;
  findings: Vulnerability[];
  summary: AssessmentSummary;
}

interface Vulnerability {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  cvss: number;
  cveId?: string;
  affectedAsset: string;
  description: string;
  impact: string;
  remediation: string;
  evidence: string;
  status: 'open' | 'in_remediation' | 'resolved' | 'accepted';
}

export class VulnerabilityAssessmentService {
  constructor(
    private scanner: VulnerabilityScanner,
    private assetInventory: AssetInventoryService,
    private reportGenerator: ReportGeneratorService
  ) {}

  // Run comprehensive vulnerability assessment
  async runAssessment(scope: AssessmentScope): Promise<VulnerabilityAssessment> {
    const assessment: VulnerabilityAssessment = {
      id: this.generateAssessmentId(),
      startedAt: new Date(),
      scope,
      findings: [],
      summary: {} as AssessmentSummary,
    };

    // Phase 1: Asset discovery
    const assets = await this.discoverAssets(scope);

    // Phase 2: Vulnerability scanning
    for (const asset of assets) {
      const vulnerabilities = await this.scanAsset(asset);
      assessment.findings.push(...vulnerabilities);
    }

    // Phase 3: Manual verification
    const verifiedFindings = await this.verifyFindings(assessment.findings);
    assessment.findings = verifiedFindings;

    // Phase 4: Risk scoring
    this.calculateRiskScores(assessment.findings);

    // Phase 5: Generate summary
    assessment.summary = this.generateSummary(assessment);
    assessment.completedAt = new Date();

    return assessment;
  }

  // Scan individual asset
  private async scanAsset(asset: Asset): Promise<Vulnerability[]> {
    const scanResults = await this.scanner.scan({
      target: asset.ipAddress || asset.hostname,
      scanType: this.determineScanType(asset),
      credentials: await this.getCredentials(asset),
    });

    return scanResults.vulnerabilities.map(v => ({
      id: this.generateVulnId(),
      title: v.name,
      severity: this.mapSeverity(v.cvss),
      cvss: v.cvss,
      cveId: v.cve,
      affectedAsset: asset.name,
      description: v.description,
      impact: v.impact,
      remediation: v.solution,
      evidence: v.output,
      status: 'open',
    }));
  }

  // Calculate risk scores
  private calculateRiskScores(vulnerabilities: Vulnerability[]): void {
    for (const vuln of vulnerabilities) {
      const assetCriticality = this.getAssetCriticality(vuln.affectedAsset);
      const exploitability = this.getExploitability(vuln.cveId);

      vuln.riskScore = (vuln.cvss * assetCriticality * exploitability) / 10;
    }
  }

  // Generate executive summary
  private generateSummary(assessment: VulnerabilityAssessment): AssessmentSummary {
    const findings = assessment.findings;

    return {
      totalVulnerabilities: findings.length,
      bySeverity: {
        critical: findings.filter(f => f.severity === 'critical').length,
        high: findings.filter(f => f.severity === 'high').length,
        medium: findings.filter(f => f.severity === 'medium').length,
        low: findings.filter(f => f.severity === 'low').length,
        info: findings.filter(f => f.severity === 'info').length,
      },
      topRisks: findings
        .sort((a, b) => (b.riskScore || 0) - (a.riskScore || 0))
        .slice(0, 10),
      assetsScanned: new Set(findings.map(f => f.affectedAsset)).size,
      overallRiskLevel: this.calculateOverallRisk(findings),
    };
  }
}
```

## Code Security Audit

```typescript
// services/code-audit.service.ts
interface CodeAuditResult {
  repositoryId: string;
  branch: string;
  commitHash: string;
  auditedAt: Date;
  staticAnalysis: StaticAnalysisResult;
  dependencyAudit: DependencyAuditResult;
  secretsAudit: SecretsAuditResult;
  manualReviewFindings: ManualFinding[];
}

interface StaticAnalysisResult {
  tool: string;
  findings: CodeFinding[];
  metrics: CodeMetrics;
}

export class CodeAuditService {
  constructor(
    private staticAnalyzer: StaticAnalyzer,
    private dependencyScanner: DependencyScanner,
    private secretsScanner: SecretsScanner
  ) {}

  // Run comprehensive code audit
  async auditRepository(repoPath: string, branch: string): Promise<CodeAuditResult> {
    const commitHash = await this.getCommitHash(repoPath, branch);

    // Static analysis (SAST)
    const staticAnalysis = await this.runStaticAnalysis(repoPath);

    // Dependency vulnerability scan
    const dependencyAudit = await this.auditDependencies(repoPath);

    // Secrets detection
    const secretsAudit = await this.scanForSecrets(repoPath);

    return {
      repositoryId: repoPath,
      branch,
      commitHash,
      auditedAt: new Date(),
      staticAnalysis,
      dependencyAudit,
      secretsAudit,
      manualReviewFindings: [],
    };
  }

  // Static analysis
  private async runStaticAnalysis(repoPath: string): Promise<StaticAnalysisResult> {
    const findings = await this.staticAnalyzer.analyze(repoPath, {
      rules: [
        // OWASP Top 10
        'sql-injection',
        'xss',
        'csrf',
        'insecure-deserialization',
        'xxe',
        'broken-access-control',
        // Cryptography
        'weak-crypto',
        'hardcoded-secrets',
        'insecure-random',
        // Input validation
        'path-traversal',
        'command-injection',
        'log-injection',
      ],
    });

    return {
      tool: 'semgrep',
      findings: findings.map(f => ({
        id: f.id,
        rule: f.rule,
        severity: f.severity,
        file: f.file,
        line: f.line,
        message: f.message,
        recommendation: f.fix,
      })),
      metrics: await this.collectMetrics(repoPath),
    };
  }

  // Dependency audit
  private async auditDependencies(repoPath: string): Promise<DependencyAuditResult> {
    const vulnerabilities = await this.dependencyScanner.scan(repoPath);

    return {
      totalDependencies: vulnerabilities.totalDependencies,
      vulnerableDependencies: vulnerabilities.vulnerable,
      findings: vulnerabilities.findings.map(v => ({
        package: v.package,
        version: v.version,
        vulnerability: v.cve,
        severity: v.severity,
        fixedIn: v.fixedVersion,
        recommendation: `Update to ${v.fixedVersion}`,
      })),
    };
  }

  // Secrets detection
  private async scanForSecrets(repoPath: string): Promise<SecretsAuditResult> {
    const secrets = await this.secretsScanner.scan(repoPath, {
      patterns: [
        'aws-access-key',
        'aws-secret-key',
        'github-token',
        'private-key',
        'api-key',
        'password',
        'connection-string',
      ],
      excludePaths: ['node_modules', '.git', 'test'],
    });

    return {
      secretsFound: secrets.length,
      findings: secrets.map(s => ({
        type: s.type,
        file: s.file,
        line: s.line,
        severity: 'critical',
        recommendation: 'Remove secret and rotate credentials',
      })),
    };
  }

  // Security metrics
  private async collectMetrics(repoPath: string): Promise<CodeMetrics> {
    return {
      linesOfCode: await this.countLines(repoPath),
      testCoverage: await this.getTestCoverage(repoPath),
      complexityCyclomatic: await this.measureComplexity(repoPath),
      technicalDebt: await this.calculateTechDebt(repoPath),
    };
  }
}
```

## Audit Reporting

```typescript
// services/audit-report.service.ts
interface AuditReport {
  id: string;
  auditPlanId: string;
  generatedAt: Date;
  executiveSummary: ExecutiveSummary;
  scope: AuditScope;
  methodology: string;
  findings: AuditFinding[];
  recommendations: Recommendation[];
  appendices: Appendix[];
}

interface AuditFinding {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  category: string;
  description: string;
  impact: string;
  likelihood: 'certain' | 'likely' | 'possible' | 'unlikely' | 'rare';
  riskRating: number;
  affectedAssets: string[];
  evidence: string[];
  recommendation: string;
  managementResponse?: string;
  remediationDeadline?: Date;
}

export class AuditReportService {
  // Generate comprehensive audit report
  async generateReport(auditPlanId: string): Promise<AuditReport> {
    const auditPlan = await this.planRepository.findById(auditPlanId);
    const assessments = await this.assessmentRepository.findByAuditPlan(auditPlanId);
    const findings = await this.findingRepository.findByAuditPlan(auditPlanId);

    const report: AuditReport = {
      id: this.generateReportId(),
      auditPlanId,
      generatedAt: new Date(),
      executiveSummary: this.generateExecutiveSummary(findings),
      scope: auditPlan.scope,
      methodology: auditPlan.methodology,
      findings: this.formatFindings(findings),
      recommendations: this.generateRecommendations(findings),
      appendices: await this.generateAppendices(auditPlan),
    };

    return report;
  }

  // Executive summary
  private generateExecutiveSummary(findings: AuditFinding[]): ExecutiveSummary {
    const severityCounts = {
      critical: findings.filter(f => f.severity === 'critical').length,
      high: findings.filter(f => f.severity === 'high').length,
      medium: findings.filter(f => f.severity === 'medium').length,
      low: findings.filter(f => f.severity === 'low').length,
    };

    const overallRisk = this.calculateOverallRisk(severityCounts);

    return {
      auditObjective: 'Assess security controls and identify vulnerabilities',
      overallAssessment: overallRisk,
      keyFindings: findings
        .filter(f => f.severity === 'critical' || f.severity === 'high')
        .slice(0, 5)
        .map(f => f.title),
      positiveObservations: this.identifyPositives(findings),
      areasOfConcern: this.identifyConcerns(findings),
      criticalActions: this.identifyCriticalActions(findings),
    };
  }

  // Risk matrix visualization
  generateRiskMatrix(findings: AuditFinding[]): RiskMatrix {
    const matrix: RiskMatrix = {
      rows: ['Certain', 'Likely', 'Possible', 'Unlikely', 'Rare'],
      columns: ['Negligible', 'Minor', 'Moderate', 'Major', 'Catastrophic'],
      cells: [],
    };

    for (const finding of findings) {
      matrix.cells.push({
        likelihood: this.likelihoodToIndex(finding.likelihood),
        impact: this.severityToIndex(finding.severity),
        findingId: finding.id,
        title: finding.title,
      });
    }

    return matrix;
  }

  // Generate recommendations
  private generateRecommendations(findings: AuditFinding[]): Recommendation[] {
    const recommendations: Recommendation[] = [];

    // Group findings by category
    const byCategory = this.groupByCategory(findings);

    for (const [category, categoryFindings] of Object.entries(byCategory)) {
      recommendations.push({
        id: this.generateRecommendationId(),
        category,
        priority: this.determinePriority(categoryFindings),
        title: `Address ${category} vulnerabilities`,
        description: this.generateCategoryRecommendation(categoryFindings),
        relatedFindings: categoryFindings.map(f => f.id),
        estimatedEffort: this.estimateEffort(categoryFindings),
        expectedBenefit: this.calculateBenefit(categoryFindings),
      });
    }

    return recommendations.sort((a, b) =>
      this.priorityToNumber(b.priority) - this.priorityToNumber(a.priority)
    );
  }

  // Export report formats
  async exportReport(reportId: string, format: 'pdf' | 'docx' | 'html'): Promise<Buffer> {
    const report = await this.reportRepository.findById(reportId);

    switch (format) {
      case 'pdf':
        return this.generatePDF(report);
      case 'docx':
        return this.generateDocx(report);
      case 'html':
        return this.generateHTML(report);
    }
  }
}
```

## Remediation Tracking

```typescript
// services/remediation-tracking.service.ts
interface RemediationPlan {
  findingId: string;
  status: 'pending' | 'in_progress' | 'completed' | 'verified' | 'accepted';
  owner: string;
  deadline: Date;
  actions: RemediationAction[];
  verification: VerificationResult[];
}

interface RemediationAction {
  id: string;
  description: string;
  assignee: string;
  dueDate: Date;
  status: 'pending' | 'in_progress' | 'completed';
  completedAt?: Date;
  evidence?: string;
}

export class RemediationTrackingService {
  // Create remediation plan
  async createPlan(findingId: string, input: CreatePlanInput): Promise<RemediationPlan> {
    const finding = await this.findingRepository.findById(findingId);

    const plan: RemediationPlan = {
      findingId,
      status: 'pending',
      owner: input.owner,
      deadline: this.calculateDeadline(finding.severity),
      actions: this.generateActions(finding, input),
      verification: [],
    };

    await this.planRepository.save(plan);

    // Schedule reminders
    await this.scheduleReminders(plan);

    return plan;
  }

  // Calculate SLA deadline based on severity
  private calculateDeadline(severity: string): Date {
    const slasDays: Record<string, number> = {
      critical: 7,
      high: 30,
      medium: 90,
      low: 180,
    };

    const days = slasDays[severity] || 30;
    return new Date(Date.now() + days * 24 * 60 * 60 * 1000);
  }

  // Update remediation status
  async updateStatus(
    findingId: string,
    status: string,
    notes?: string
  ): Promise<RemediationPlan> {
    const plan = await this.planRepository.findByFinding(findingId);

    plan.status = status;

    if (status === 'completed') {
      // Schedule verification
      await this.scheduleVerification(plan);
    }

    await this.planRepository.save(plan);

    // Audit log
    await this.auditLog.log({
      action: 'remediation_status_updated',
      findingId,
      status,
      notes,
    });

    return plan;
  }

  // Verify remediation
  async verifyRemediation(findingId: string): Promise<VerificationResult> {
    const plan = await this.planRepository.findByFinding(findingId);
    const finding = await this.findingRepository.findById(findingId);

    // Re-test the vulnerability
    const testResult = await this.retestVulnerability(finding);

    const verification: VerificationResult = {
      verifiedAt: new Date(),
      verifiedBy: this.currentUser.id,
      testPerformed: testResult.testDescription,
      result: testResult.vulnerable ? 'failed' : 'passed',
      evidence: testResult.evidence,
      notes: testResult.notes,
    };

    plan.verification.push(verification);

    if (verification.result === 'passed') {
      plan.status = 'verified';
    } else {
      plan.status = 'in_progress'; // Back to remediation
    }

    await this.planRepository.save(plan);

    return verification;
  }

  // Generate remediation dashboard
  async getDashboard(): Promise<RemediationDashboard> {
    const plans = await this.planRepository.findAll();

    return {
      totalFindings: plans.length,
      byStatus: {
        pending: plans.filter(p => p.status === 'pending').length,
        inProgress: plans.filter(p => p.status === 'in_progress').length,
        completed: plans.filter(p => p.status === 'completed').length,
        verified: plans.filter(p => p.status === 'verified').length,
      },
      overdue: plans.filter(p => new Date() > p.deadline && p.status !== 'verified').length,
      upcomingDeadlines: plans
        .filter(p => p.status !== 'verified')
        .sort((a, b) => a.deadline.getTime() - b.deadline.getTime())
        .slice(0, 10),
      averageTimeToRemediate: this.calculateAverageTime(plans),
    };
  }
}
```

## Continuous Audit

```typescript
// services/continuous-audit.service.ts
export class ContinuousAuditService {
  constructor(
    private configMonitor: ConfigurationMonitor,
    private accessMonitor: AccessMonitor,
    private alertService: AlertService
  ) {}

  // Monitor configuration changes
  async monitorConfigurations(): Promise<void> {
    const changes = await this.configMonitor.getChanges();

    for (const change of changes) {
      // Check against baseline
      const compliance = await this.checkCompliance(change);

      if (!compliance.compliant) {
        await this.alertService.sendAlert({
          type: 'configuration_drift',
          severity: compliance.severity,
          message: `Configuration drift detected: ${change.resource}`,
          details: compliance.violations,
        });

        // Auto-remediate if possible
        if (compliance.autoRemediable) {
          await this.autoRemediate(change);
        }
      }
    }
  }

  // Monitor access patterns
  async monitorAccess(): Promise<void> {
    const anomalies = await this.accessMonitor.detectAnomalies();

    for (const anomaly of anomalies) {
      await this.alertService.sendAlert({
        type: 'access_anomaly',
        severity: anomaly.riskLevel,
        message: anomaly.description,
        userId: anomaly.userId,
        details: anomaly.details,
      });
    }
  }

  // Automated compliance checks
  async runComplianceChecks(): Promise<ComplianceCheckResult[]> {
    const checks: ComplianceCheckResult[] = [];

    // Password policy compliance
    checks.push(await this.checkPasswordPolicy());

    // MFA enforcement
    checks.push(await this.checkMFAEnforcement());

    // Encryption at rest
    checks.push(await this.checkEncryptionAtRest());

    // Network segmentation
    checks.push(await this.checkNetworkSegmentation());

    // Log retention
    checks.push(await this.checkLogRetention());

    return checks;
  }

  // Generate continuous audit report
  async generateContinuousReport(period: DateRange): Promise<ContinuousAuditReport> {
    return {
      period,
      configurationChanges: await this.getConfigChanges(period),
      accessAnomalies: await this.getAccessAnomalies(period),
      complianceChecks: await this.getComplianceHistory(period),
      alertsSummary: await this.getAlertsSummary(period),
      recommendations: await this.generateRecommendations(period),
    };
  }
}
```

## Audit Checklist Template

```yaml
# security-audit-checklist.yaml
access_control:
  - user_access_review_completed
  - privileged_accounts_documented
  - service_accounts_inventoried
  - mfa_enabled_for_sensitive_systems
  - password_policy_enforced
  - access_provisioning_process_documented
  - offboarding_process_verified

network_security:
  - firewall_rules_reviewed
  - network_segmentation_verified
  - intrusion_detection_active
  - vpn_configuration_secure
  - wireless_security_assessed

application_security:
  - input_validation_implemented
  - authentication_mechanisms_secure
  - session_management_secure
  - error_handling_appropriate
  - logging_sufficient
  - encryption_properly_implemented

data_protection:
  - data_classification_completed
  - encryption_at_rest_verified
  - encryption_in_transit_verified
  - backup_procedures_tested
  - data_retention_policy_followed

incident_response:
  - incident_response_plan_documented
  - incident_response_team_identified
  - communication_plan_established
  - incident_response_tested

compliance:
  - regulatory_requirements_identified
  - compliance_controls_mapped
  - compliance_evidence_collected
  - compliance_gaps_documented
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Risk-based approach | Prioritize by risk level |
| Evidence collection | Document everything |
| Independence | Maintain objectivity |
| Continuous monitoring | Don't wait for annual audits |
| Remediation tracking | Follow through on findings |
| Management engagement | Ensure executive support |
