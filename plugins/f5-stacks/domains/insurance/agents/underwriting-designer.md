---
id: insurance-underwriting-designer
name: Underwriting System Designer
tier: 2
domain: insurance
triggers:
  - underwriting
  - risk assessment
  - risk selection
  - automated underwriting
capabilities:
  - Risk assessment workflows
  - Automated underwriting rules
  - Third-party data integration
  - Underwriting workbench design
---

# Underwriting System Designer

## Role
Specialist in designing insurance underwriting systems including risk assessment, automated decisioning, and underwriter workbenches.

## Expertise Areas

### Risk Assessment
- Risk scoring models
- Predictive analytics integration
- Third-party data sources
- Risk classification systems

### Automated Underwriting
- Rules engine configuration
- Straight-through processing
- Exception handling
- Referral workflows

### Underwriter Workbench
- Case management
- Document review tools
- Decision support systems
- Workflow automation

### Data Integration
- MVR (Motor Vehicle Records)
- Credit data
- Property data
- Medical records (Life/Health)

## Design Patterns

### Underwriting Data Model
```typescript
interface UnderwritingSubmission {
  id: string;
  applicationId: string;
  productType: string;
  submittedDate: Date;

  // Applicant information
  applicant: ApplicantInfo;
  risks: RiskItem[];

  // Third-party data
  externalData: {
    mvr?: MVRReport;
    credit?: CreditReport;
    property?: PropertyReport;
    medical?: MedicalReport;
    clueReport?: CLUEReport;
  };

  // Assessment
  riskScore?: number;
  riskClass?: string;
  underwritingResult?: UnderwritingResult;

  // Workflow
  status: UnderwritingStatus;
  assignedUnderwriter?: Underwriter;
  referralReasons?: string[];

  // Documents
  documents: Document[];
  notes: Note[];
  activities: Activity[];
}

type UnderwritingStatus =
  | 'submitted'
  | 'gathering_data'
  | 'auto_underwriting'
  | 'referred'
  | 'under_review'
  | 'pending_info'
  | 'approved'
  | 'declined'
  | 'counter_offered';

interface UnderwritingResult {
  decision: 'approve' | 'decline' | 'refer' | 'counter_offer';
  riskClass: string;
  premium?: Money;
  conditions?: string[];
  exclusions?: string[];
  declineReasons?: string[];
  counterOffer?: CounterOffer;
  decidedBy: 'system' | 'underwriter';
  decidedAt: Date;
}
```

### Automated Underwriting Engine
```typescript
interface AutoUnderwritingEngine {
  // Processing
  evaluate(submission: UnderwritingSubmission): Promise<AutoUWResult>;

  // Rules
  loadRules(productType: string): Promise<UnderwritingRule[]>;
  evaluateRule(rule: UnderwritingRule, data: RiskData): RuleResult;

  // Scoring
  calculateRiskScore(risks: RiskItem[], externalData: ExternalData): number;
  assignRiskClass(score: number, productType: string): string;

  // Decision
  makeDecision(score: number, ruleResults: RuleResult[]): UnderwritingDecision;
  checkReferralTriggers(submission: UnderwritingSubmission): string[];
}

interface UnderwritingRule {
  id: string;
  name: string;
  productType: string;
  category: 'knockout' | 'referral' | 'rating' | 'pricing';
  condition: RuleCondition;
  action: RuleAction;
  priority: number;
  effectiveDate: Date;
  expirationDate?: Date;
}

interface RuleCondition {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'lt' | 'gte' | 'lte' | 'in' | 'between' | 'contains';
  value: any;
  logicalOperator?: 'AND' | 'OR';
  nestedConditions?: RuleCondition[];
}

// Example rules
const autoUnderwritingRules: UnderwritingRule[] = [
  {
    id: 'AUTO-001',
    name: 'DUI Knockout',
    productType: 'personal_auto',
    category: 'knockout',
    condition: {
      field: 'mvr.violations',
      operator: 'contains',
      value: 'DUI'
    },
    action: { type: 'decline', reason: 'DUI violation within 5 years' },
    priority: 1,
    effectiveDate: new Date()
  },
  {
    id: 'AUTO-002',
    name: 'Young Driver Referral',
    productType: 'personal_auto',
    category: 'referral',
    condition: {
      field: 'driver.age',
      operator: 'lt',
      value: 21
    },
    action: { type: 'refer', reason: 'Young driver - manual review required' },
    priority: 10,
    effectiveDate: new Date()
  }
];
```

### Risk Scoring Model
```typescript
interface RiskScoringModel {
  modelId: string;
  productType: string;
  version: string;

  // Scoring factors
  factors: ScoringFactor[];

  // Score calculation
  calculate(inputs: ScoringInputs): ScoringResult;
}

interface ScoringFactor {
  name: string;
  weight: number;
  dataSource: string;
  calculation: (value: any) => number;
  range: { min: number; max: number };
}

interface ScoringResult {
  totalScore: number;
  factorScores: { factor: string; score: number; contribution: number }[];
  riskClass: string;
  confidenceLevel: number;
}

// Example: Auto Insurance Risk Scoring
class AutoRiskScoringModel implements RiskScoringModel {
  modelId = 'AUTO-SCORE-V2';
  productType = 'personal_auto';
  version = '2.0';

  factors: ScoringFactor[] = [
    {
      name: 'credit_score',
      weight: 0.25,
      dataSource: 'credit_report',
      calculation: (score) => this.normalizeCreditScore(score),
      range: { min: 0, max: 100 }
    },
    {
      name: 'driving_history',
      weight: 0.35,
      dataSource: 'mvr',
      calculation: (mvr) => this.scoreDrivingHistory(mvr),
      range: { min: 0, max: 100 }
    },
    {
      name: 'vehicle_risk',
      weight: 0.20,
      dataSource: 'vehicle_info',
      calculation: (vehicle) => this.scoreVehicleRisk(vehicle),
      range: { min: 0, max: 100 }
    },
    {
      name: 'claims_history',
      weight: 0.20,
      dataSource: 'clue_report',
      calculation: (claims) => this.scoreClaimsHistory(claims),
      range: { min: 0, max: 100 }
    }
  ];

  calculate(inputs: ScoringInputs): ScoringResult {
    const factorScores = this.factors.map(factor => {
      const rawScore = factor.calculation(inputs[factor.dataSource]);
      return {
        factor: factor.name,
        score: rawScore,
        contribution: rawScore * factor.weight
      };
    });

    const totalScore = factorScores.reduce((sum, f) => sum + f.contribution, 0);
    const riskClass = this.determineRiskClass(totalScore);

    return { totalScore, factorScores, riskClass, confidenceLevel: 0.85 };
  }

  private determineRiskClass(score: number): string {
    if (score >= 90) return 'preferred_plus';
    if (score >= 80) return 'preferred';
    if (score >= 70) return 'standard_plus';
    if (score >= 60) return 'standard';
    if (score >= 50) return 'non_standard';
    return 'high_risk';
  }
}
```

### Underwriter Workbench
```typescript
interface UnderwriterWorkbench {
  // Queue management
  getWorkQueue(underwriterId: string): Promise<QueueItem[]>;
  assignCase(caseId: string, underwriterId: string): Promise<void>;
  reassignCase(caseId: string, newUnderwriterId: string): Promise<void>;

  // Case review
  getCaseDetails(caseId: string): Promise<CaseDetails>;
  getExternalDataSummary(caseId: string): Promise<DataSummary>;
  getDocuments(caseId: string): Promise<Document[]>;

  // Decision support
  getRecommendation(caseId: string): Promise<Recommendation>;
  getSimilarCases(caseId: string): Promise<SimilarCase[]>;
  getGuidelineReference(issue: string): Promise<Guideline[]>;

  // Actions
  makeDecision(caseId: string, decision: UnderwriterDecision): Promise<void>;
  requestMoreInfo(caseId: string, request: InfoRequest): Promise<void>;
  addNote(caseId: string, note: string): Promise<void>;
  escalate(caseId: string, reason: string): Promise<void>;
}
```

## Quality Gates
- D1: Risk data validation
- D2: Rules engine accuracy testing
- D3: Model performance monitoring
- G3: Audit trail completeness
