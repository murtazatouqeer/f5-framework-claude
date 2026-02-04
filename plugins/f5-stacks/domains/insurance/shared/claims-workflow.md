# Claims Workflow Template

## Complete Claims Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    FNOL     │────▶│Investigation│────▶│  Evaluation │────▶│  Settlement │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Report loss         Gather facts       Assess damages      Issue payment
  Verify coverage     Get statements     Determine liability Close claim
  Set reserves        Order reports      Coverage decision   Subrogation
```

## Claim States

```typescript
type ClaimStatus =
  | 'fnol_received'      // First notice received
  | 'coverage_verified'  // Coverage confirmed
  | 'assigned'           // Assigned to adjuster
  | 'investigation'      // Under investigation
  | 'pending_info'       // Waiting for information
  | 'evaluation'         // Evaluating damages
  | 'negotiation'        // Settlement negotiation
  | 'approved'           // Claim approved
  | 'partial_payment'    // Partial payment issued
  | 'settled'            // Fully settled
  | 'denied'             // Claim denied
  | 'closed'             // Administratively closed
  | 'reopened'           // Claim reopened
  | 'litigation'         // In legal proceedings
  | 'subrogation';       // In recovery process
```

## Claim Data Structure

```typescript
interface Claim {
  // Identification
  id: string;
  claimNumber: string;
  policyNumber: string;
  policyId: string;

  // Loss Information
  loss: {
    date: Date;
    time?: string;
    reportedDate: Date;
    reportedBy: Reporter;
    location: {
      address: Address;
      description: string;
    };
    description: string;
    causeOfLoss: CauseOfLoss;
    extent: 'total' | 'partial' | 'unknown';
  };

  // Coverage
  coverage: {
    verified: boolean;
    verifiedDate?: Date;
    coveragesApplied: AppliedCoverage[];
    deductible: Money;
    limits: CoverageLimits;
    reservations?: string[];
  };

  // Parties Involved
  parties: {
    claimant: Claimant;
    insured: Insured;
    witnesses: Witness[];
    thirdParties: ThirdParty[];
    attorneys?: Attorney[];
  };

  // Financial
  financials: {
    reserves: {
      indemnity: Money;
      expense: Money;
      subrogation: Money;
    };
    payments: Payment[];
    recoveries: Recovery[];
    incurred: Money; // Reserves + Payments - Recoveries
  };

  // Assignment
  assignment: {
    adjuster: Adjuster;
    supervisor?: Supervisor;
    specialUnit?: string;
    assignedDate: Date;
  };

  // Status
  status: ClaimStatus;
  priority: 'low' | 'medium' | 'high' | 'catastrophe';
  complexity: 'simple' | 'moderate' | 'complex';

  // SIU
  siu?: {
    referred: boolean;
    referralDate?: Date;
    referralReason?: string;
    investigator?: string;
    outcome?: string;
  };

  // Audit Trail
  activities: ClaimActivity[];
  notes: ClaimNote[];
  documents: ClaimDocument[];

  // Dates
  createdAt: Date;
  updatedAt: Date;
  closedAt?: Date;
}
```

## FNOL Processing

```typescript
interface FNOLWorkflow {
  // Step 1: Intake
  receiveFNOL(fnol: FNOLData): Promise<Claim>;

  // Step 2: Policy lookup
  findPolicy(searchCriteria: PolicySearchCriteria): Promise<Policy | null>;

  // Step 3: Coverage verification
  verifyCoverage(
    policy: Policy,
    lossDate: Date,
    causeOfLoss: CauseOfLoss
  ): Promise<CoverageVerification>;

  // Step 4: Initial assessment
  assessClaim(claim: Claim): Promise<InitialAssessment>;

  // Step 5: Triage & assignment
  triageAndAssign(claim: Claim, assessment: InitialAssessment): Promise<Assignment>;

  // Step 6: Set reserves
  setInitialReserves(claim: Claim, assessment: InitialAssessment): Promise<Reserves>;
}

interface FNOLData {
  // Reporter information
  reporter: {
    name: string;
    phone: string;
    email?: string;
    relationship: 'insured' | 'claimant' | 'agent' | 'witness' | 'other';
  };

  // Policy identification
  policy: {
    number?: string;
    insuredName?: string;
    insuredPhone?: string;
    insuredAddress?: Address;
  };

  // Loss details
  loss: {
    date: Date;
    time?: string;
    location: Address;
    description: string;
    causeOfLoss: string;
  };

  // Additional information
  injuries: boolean;
  injuryDetails?: string;
  policeReport: boolean;
  policeReportNumber?: string;
  thirdPartyInvolved: boolean;
  thirdPartyInfo?: ThirdPartyInfo;
  initialEstimate?: Money;
}

interface InitialAssessment {
  severity: 'minor' | 'moderate' | 'major' | 'catastrophic';
  complexity: 'simple' | 'moderate' | 'complex';
  handlerType: 'auto' | 'desk' | 'field' | 'complex' | 'siu';
  fraudIndicators: FraudIndicator[];
  suggestedReserves: {
    indemnity: Money;
    expense: Money;
  };
  priority: 'low' | 'medium' | 'high' | 'urgent';
}
```

## Investigation Workflow

```typescript
interface InvestigationService {
  // Create investigation plan
  createPlan(claimId: string): Promise<InvestigationPlan>;

  // Gather evidence
  recordStatement(claimId: string, statement: Statement): Promise<void>;
  requestDocuments(claimId: string, docRequests: DocumentRequest[]): Promise<void>;
  orderExpertReport(claimId: string, type: ExpertType): Promise<ExpertOrder>;

  // Scene investigation
  scheduleInspection(claimId: string, type: InspectionType): Promise<Inspection>;
  recordInspectionResults(inspectionId: string, results: InspectionResults): Promise<void>;

  // Third-party data
  orderPoliceReport(claimId: string): Promise<PoliceReport>;
  orderMedicalRecords(claimId: string, authorization: MedicalAuth): Promise<void>;
  orderSubrogationResearch(claimId: string): Promise<SubrogationResearch>;
}

interface InvestigationPlan {
  claimId: string;
  objectives: string[];
  tasks: InvestigationTask[];
  timeline: {
    targetCompletion: Date;
    milestones: Milestone[];
  };
  resources: {
    estimatedHours: number;
    vendorsNeeded: string[];
    expertReports: ExpertType[];
  };
}

interface InvestigationTask {
  id: string;
  type: TaskType;
  description: string;
  assignedTo: string;
  dueDate: Date;
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
  priority: number;
  dependencies: string[];
}

type TaskType =
  | 'contact_insured'
  | 'contact_claimant'
  | 'contact_witness'
  | 'scene_inspection'
  | 'vehicle_inspection'
  | 'property_inspection'
  | 'review_documents'
  | 'order_report'
  | 'medical_review'
  | 'coverage_analysis'
  | 'liability_analysis';
```

## Evaluation & Decision

```typescript
interface ClaimEvaluationService {
  // Liability assessment
  assessLiability(claimId: string): Promise<LiabilityAssessment>;

  // Damage evaluation
  evaluateDamages(claimId: string): Promise<DamageEvaluation>;

  // Coverage determination
  determineCoverage(claimId: string): Promise<CoverageDecision>;

  // Settlement calculation
  calculateSettlement(claimId: string): Promise<SettlementCalculation>;

  // Final decision
  makeDecision(claimId: string, decision: ClaimDecision): Promise<void>;
}

interface LiabilityAssessment {
  determination: 'insured_liable' | 'third_party_liable' | 'shared' | 'no_liability' | 'undetermined';
  insuredPercentage?: number;
  thirdPartyPercentage?: number;
  basis: string;
  supportingEvidence: string[];
}

interface DamageEvaluation {
  propertyDamage?: {
    items: DamageItem[];
    totalEstimate: Money;
    actualCashValue?: Money;
    replacementCost?: Money;
  };
  bodilyInjury?: {
    injuries: Injury[];
    medicalExpenses: Money;
    lostWages?: Money;
    painAndSuffering?: Money;
    futureExpenses?: Money;
  };
  additionalExpenses?: {
    description: string;
    amount: Money;
  }[];
  totalEvaluation: Money;
}

interface ClaimDecision {
  decision: 'approve' | 'partial_approve' | 'deny';
  approvedAmount?: Money;
  denialReason?: string;
  denialCode?: string;
  coverageApplied: string[];
  deductibleApplied: Money;
  conditions?: string[];
  appealRights?: string;
}
```

## Payment Processing

```typescript
interface ClaimPaymentService {
  // Reserve management
  setReserve(claimId: string, type: ReserveType, amount: Money): Promise<void>;
  adjustReserve(claimId: string, type: ReserveType, amount: Money, reason: string): Promise<void>;

  // Payment creation
  createPayment(claimId: string, payment: PaymentRequest): Promise<Payment>;

  // Approval workflow
  submitForApproval(paymentId: string): Promise<ApprovalRequest>;
  approvePayment(paymentId: string, approver: string): Promise<void>;
  rejectPayment(paymentId: string, reason: string): Promise<void>;

  // Payment issuance
  issuePayment(paymentId: string): Promise<PaymentConfirmation>;

  // Vendor payments
  createVendorPayment(claimId: string, vendor: Vendor, invoice: Invoice): Promise<Payment>;
}

interface PaymentRequest {
  claimId: string;
  paymentType: PaymentType;
  amount: Money;
  payee: Payee;
  description: string;
  coverageCode: string;
  documentSupport: string[];
}

type PaymentType =
  | 'indemnity'
  | 'medical'
  | 'repair'
  | 'replacement'
  | 'loss_of_use'
  | 'legal_expense'
  | 'adjuster_expense'
  | 'vendor'
  | 'settlement';

interface Payment {
  id: string;
  claimId: string;
  paymentNumber: string;
  type: PaymentType;
  amount: Money;
  payee: Payee;
  status: 'pending' | 'approved' | 'issued' | 'cleared' | 'voided' | 'stopped';
  checkNumber?: string;
  eftReference?: string;
  issuedDate?: Date;
  clearedDate?: Date;
  approvals: Approval[];
}
```

## Subrogation & Recovery

```typescript
interface SubrogationService {
  // Identify recovery potential
  evaluateRecoveryPotential(claimId: string): Promise<RecoveryPotential>;

  // Initiate subrogation
  initiateSubrogation(claimId: string, target: SubrogationTarget): Promise<Subrogation>;

  // Demand process
  sendDemand(subrogationId: string, demand: DemandLetter): Promise<void>;
  recordResponse(subrogationId: string, response: DemandResponse): Promise<void>;

  // Settlement
  negotiateSettlement(subrogationId: string, offer: SettlementOffer): Promise<void>;
  acceptSettlement(subrogationId: string): Promise<Recovery>;

  // Recovery recording
  recordRecovery(subrogationId: string, recovery: RecoveryData): Promise<void>;
}

interface Subrogation {
  id: string;
  claimId: string;
  status: SubrogationStatus;
  target: SubrogationTarget;
  demandAmount: Money;
  recoveredAmount: Money;
  deductibleReimbursed: Money;
  insuredShare: Money;
  companyShare: Money;
}

type SubrogationStatus =
  | 'identified'
  | 'demand_sent'
  | 'negotiating'
  | 'settled'
  | 'litigation'
  | 'collected'
  | 'closed_no_recovery';
```
