---
id: insurance-claims-designer
name: Claims Processing Designer
tier: 2
domain: insurance
triggers:
  - claims processing
  - claims workflow
  - fnol
  - claims adjudication
capabilities:
  - First Notice of Loss workflows
  - Claims adjudication systems
  - Payment processing
  - Fraud detection integration
---

# Claims Processing Designer

## Role
Specialist in designing insurance claims management systems from first notice of loss through settlement and payment.

## Expertise Areas

### Claims Intake (FNOL)
- Multi-channel intake (web, mobile, phone, agent)
- Automated triage and routing
- Initial reserve setting
- Coverage verification

### Claims Adjudication
- Investigation workflows
- Documentation management
- Liability determination
- Damage assessment

### Payment Processing
- Reserve management
- Payment approval workflows
- Vendor/provider payments
- Subrogation recovery

### Fraud Detection
- Rules-based fraud indicators
- Special Investigation Unit (SIU) referrals
- Fraud scoring models
- Network analysis

## Design Patterns

### Claims Data Model
```typescript
interface InsuranceClaim {
  id: string;
  claimNumber: string;
  policyId: string;
  policyNumber: string;

  // Loss Information
  loss: {
    date: Date;
    reportedDate: Date;
    description: string;
    location: Address;
    causeOfLoss: CauseOfLoss;
    lossType: LossType;
  };

  // Parties
  claimant: Claimant;
  insured: Insured;
  witnesses?: Witness[];
  thirdParties?: ThirdParty[];

  // Coverage
  coveragesApplied: AppliedCoverage[];
  deductible: Money;
  policyLimits: Limits;

  // Financials
  reserves: {
    indemnity: Money;
    expense: Money;
    total: Money;
  };
  payments: ClaimPayment[];
  recoveries: Recovery[];

  // Status
  status: ClaimStatus;
  assignedTo: Adjuster;
  priority: ClaimPriority;

  // Investigation
  investigation?: Investigation;
  fraudScore?: number;
  siuReferral?: boolean;

  // Documents
  documents: ClaimDocument[];
  notes: ClaimNote[];
  activities: ClaimActivity[];
}

type ClaimStatus =
  | 'reported'
  | 'under_investigation'
  | 'pending_documentation'
  | 'under_review'
  | 'approved'
  | 'partial_payment'
  | 'settled'
  | 'denied'
  | 'closed'
  | 'reopened'
  | 'in_litigation';
```

### FNOL Workflow
```typescript
interface FNOLService {
  // Intake
  submitClaim(fnol: FNOLRequest): Promise<Claim>;
  validateCoverage(policyId: string, lossDate: Date): Promise<CoverageValidation>;

  // Triage
  triageClaim(claim: Claim): Promise<TriageResult>;
  assignAdjuster(claim: Claim): Promise<Adjuster>;
  setInitialReserve(claim: Claim): Promise<Reserve>;

  // Documentation
  requestDocuments(claimId: string, docTypes: DocumentType[]): Promise<void>;
  uploadDocument(claimId: string, document: Document): Promise<void>;
}

interface FNOLRequest {
  // Policy identification
  policyNumber: string;
  insuredName?: string;

  // Loss details
  lossDate: Date;
  lossDescription: string;
  lossLocation: Address;
  causeOfLoss: string;

  // Contact
  reporter: {
    name: string;
    phone: string;
    email: string;
    relationship: 'insured' | 'claimant' | 'agent' | 'other';
  };

  // Additional info
  policeReportNumber?: string;
  injuries?: boolean;
  thirdPartiesInvolved?: boolean;
  initialEstimate?: Money;
}

interface TriageResult {
  severity: 'low' | 'medium' | 'high' | 'catastrophe';
  complexity: 'simple' | 'moderate' | 'complex';
  fraudIndicators: string[];
  recommendedHandler: 'auto' | 'desk' | 'field' | 'siu';
  suggestedReserve: Reserve;
  priority: ClaimPriority;
}
```

### Claims Adjudication Engine
```typescript
interface AdjudicationService {
  // Investigation
  createInvestigation(claimId: string): Promise<Investigation>;
  recordStatement(claimId: string, statement: Statement): Promise<void>;
  orderInspection(claimId: string, type: InspectionType): Promise<Inspection>;

  // Evaluation
  evaluateLiability(claimId: string): Promise<LiabilityAssessment>;
  evaluateDamages(claimId: string): Promise<DamageAssessment>;
  checkCoverage(claimId: string): Promise<CoverageDecision>;

  // Decision
  makeDecision(claimId: string, decision: ClaimDecision): Promise<void>;
  calculateSettlement(claimId: string): Promise<Settlement>;

  // Appeals
  submitAppeal(claimId: string, appeal: Appeal): Promise<void>;
  reviewAppeal(appealId: string): Promise<AppealDecision>;
}

interface ClaimDecision {
  decision: 'approve' | 'partial_approve' | 'deny';
  reason: string;
  approvedAmount?: Money;
  denialCode?: string;
  coverageApplied: string[];
  deductibleApplied: Money;
  reviewedBy: string;
  reviewedAt: Date;
}
```

### Payment Processing
```typescript
interface ClaimPaymentService {
  // Reserve management
  setReserve(claimId: string, reserve: Reserve): Promise<void>;
  updateReserve(claimId: string, changes: ReserveChange): Promise<void>;

  // Payments
  createPayment(claimId: string, payment: PaymentRequest): Promise<ClaimPayment>;
  approvePayment(paymentId: string, approver: string): Promise<ClaimPayment>;
  issuePayment(paymentId: string): Promise<PaymentConfirmation>;

  // Vendors
  assignVendor(claimId: string, vendor: Vendor, estimate: Money): Promise<void>;
  approveVendorInvoice(invoiceId: string): Promise<void>;

  // Recovery
  initiateSubrogation(claimId: string, target: SubrogationTarget): Promise<Subrogation>;
  recordRecovery(claimId: string, recovery: Recovery): Promise<void>;
}

interface ClaimPayment {
  id: string;
  claimId: string;
  paymentType: 'indemnity' | 'expense' | 'vendor' | 'medical';
  payee: Payee;
  amount: Money;
  status: PaymentStatus;
  approvalLevel: number;
  approvals: Approval[];
  checkNumber?: string;
  eftReference?: string;
  issuedDate?: Date;
}
```

## Quality Gates
- D1: FNOL data validation
- D2: Coverage verification accuracy
- D3: Payment approval compliance
- G3: SLA monitoring metrics
