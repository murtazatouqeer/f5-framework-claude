# Policy Lifecycle Template

## Complete Policy Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Quote    │────▶│ Application │────▶│    Bind     │────▶│   Active    │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Rate risks          Underwrite          Issue policy        Service policy
  Present options     Collect info        Generate docs       Endorsements
  Generate quote      Decision            Collect premium     Renewals
```

## Policy States

```typescript
type PolicyStatus =
  | 'quote'               // Initial quote created
  | 'application'         // Application submitted
  | 'underwriting'        // Under underwriting review
  | 'approved'            // Approved, pending bind
  | 'bound'               // Bound, policy in force
  | 'active'              // Active policy
  | 'pending_renewal'     // Renewal period
  | 'renewed'             // Successfully renewed
  | 'pending_cancel'      // Cancellation pending
  | 'cancelled'           // Cancelled
  | 'non_renewed'         // Not renewed
  | 'expired'             // Term expired
  | 'reinstated';         // Reinstated after lapse
```

## Policy Data Structure

```typescript
interface InsurancePolicy {
  // Identification
  id: string;
  policyNumber: string;
  quoteNumber?: string;
  applicationNumber?: string;

  // Product
  product: {
    id: string;
    name: string;
    lineOfBusiness: LineOfBusiness;
    edition: string;
    state: string;
  };

  // Policy Term
  term: {
    effectiveDate: Date;
    expirationDate: Date;
    termLength: number; // months
    termType: 'annual' | 'semi_annual' | 'quarterly' | 'monthly';
  };

  // Parties
  insured: {
    id: string;
    type: 'individual' | 'business';
    name: string;
    address: Address;
    phone: string;
    email: string;
    ssn?: string;
    ein?: string;
  };
  additionalInsureds?: AdditionalInsured[];
  agent?: {
    id: string;
    name: string;
    agency: string;
    commission: number;
  };

  // Coverages
  coverages: {
    id: string;
    code: string;
    name: string;
    limit: Money;
    deductible?: Money;
    premium: Money;
    isRequired: boolean;
  }[];

  // Risks
  risks: RiskItem[];

  // Premium
  premium: {
    written: Money;
    earned: Money;
    unearned: Money;
    fees: Fee[];
    taxes: Tax[];
    total: Money;
  };

  // Billing
  billing: {
    plan: BillingPlan;
    accountId: string;
    paymentMethod: PaymentMethod;
    nextDueDate?: Date;
    balance: Money;
  };

  // Status
  status: PolicyStatus;
  statusReason?: string;
  statusDate: Date;

  // Dates
  createdAt: Date;
  issuedAt?: Date;
  cancelledAt?: Date;
  renewedFrom?: string; // Previous policy number
}

type LineOfBusiness =
  | 'personal_auto'
  | 'homeowners'
  | 'renters'
  | 'umbrella'
  | 'life_term'
  | 'life_whole'
  | 'health_individual'
  | 'health_group'
  | 'commercial_property'
  | 'commercial_auto'
  | 'general_liability'
  | 'professional_liability'
  | 'workers_compensation'
  | 'cyber_liability';
```

## Quote to Bind Workflow

```typescript
interface QuoteService {
  // Quote creation
  createQuote(request: QuoteRequest): Promise<Quote>;
  rateQuote(quoteId: string): Promise<PremiumCalculation>;
  updateQuote(quoteId: string, changes: QuoteChanges): Promise<Quote>;

  // Quote options
  generateAlternatives(quoteId: string): Promise<QuoteAlternative[]>;
  compareQuotes(quoteIds: string[]): Promise<QuoteComparison>;

  // Conversion
  convertToApplication(quoteId: string): Promise<Application>;
}

interface ApplicationService {
  // Application management
  submitApplication(application: ApplicationData): Promise<Application>;
  updateApplication(appId: string, data: Partial<ApplicationData>): Promise<Application>;

  // Underwriting
  submitForUnderwriting(appId: string): Promise<UnderwritingSubmission>;
  getUnderwritingStatus(appId: string): Promise<UnderwritingStatus>;

  // Binding
  bindApplication(appId: string, bindRequest: BindRequest): Promise<Policy>;
}

interface BindRequest {
  applicationId: string;
  effectiveDate: Date;
  paymentMethod: PaymentMethod;
  initialPayment: Money;
  billingPlan: BillingPlan;
  electronicDelivery: boolean;
  agreements: SignedAgreement[];
}
```

## Endorsement Processing

```typescript
interface EndorsementService {
  // Create endorsement
  createEndorsement(
    policyId: string,
    type: EndorsementType,
    changes: EndorsementChanges
  ): Promise<Endorsement>;

  // Rate endorsement
  rateEndorsement(endorsementId: string): Promise<PremiumChange>;

  // Process endorsement
  processEndorsement(endorsementId: string): Promise<Policy>;

  // Cancel endorsement
  cancelEndorsement(endorsementId: string): Promise<void>;
}

interface Endorsement {
  id: string;
  policyId: string;
  endorsementNumber: string;
  type: EndorsementType;
  effectiveDate: Date;
  description: string;
  changes: EndorsementChanges;
  premiumChange: Money;
  status: 'pending' | 'processed' | 'cancelled';
  processedAt?: Date;
}

type EndorsementType =
  | 'add_coverage'
  | 'remove_coverage'
  | 'change_limits'
  | 'change_deductible'
  | 'add_driver'
  | 'remove_driver'
  | 'add_vehicle'
  | 'remove_vehicle'
  | 'change_address'
  | 'add_mortgagee'
  | 'remove_mortgagee'
  | 'general_change';
```

## Renewal Processing

```typescript
interface RenewalService {
  // Identify renewals
  getUpcomingRenewals(daysAhead: number): Promise<Policy[]>;

  // Process renewal
  generateRenewal(policyId: string): Promise<RenewalOffer>;
  rateRenewal(renewalId: string): Promise<RenewalPricing>;
  issueRenewal(renewalId: string): Promise<Policy>;

  // Non-renewal
  nonRenew(policyId: string, reason: string): Promise<void>;

  // Notifications
  sendRenewalNotice(renewalId: string): Promise<void>;
}

interface RenewalOffer {
  id: string;
  expiringPolicyId: string;
  newPolicyNumber: string;
  effectiveDate: Date;
  expirationDate: Date;
  coverageChanges: CoverageChange[];
  premiumChange: {
    expiring: Money;
    renewal: Money;
    difference: Money;
    percentChange: number;
  };
  status: 'offered' | 'accepted' | 'declined' | 'expired';
  offerExpiresAt: Date;
}
```

## Cancellation Processing

```typescript
interface CancellationService {
  // Initiate cancellation
  requestCancellation(
    policyId: string,
    request: CancellationRequest
  ): Promise<Cancellation>;

  // Process cancellation
  processCancellation(cancellationId: string): Promise<Policy>;

  // Calculate refund
  calculateRefund(
    policyId: string,
    cancelDate: Date,
    method: RefundMethod
  ): Promise<RefundCalculation>;

  // Reinstatement
  requestReinstatement(policyId: string): Promise<ReinstatementRequest>;
  processReinstatement(requestId: string): Promise<Policy>;
}

interface CancellationRequest {
  policyId: string;
  requestedBy: 'insured' | 'company' | 'agent' | 'mortgagee';
  effectiveDate: Date;
  reason: CancellationReason;
  refundMethod: RefundMethod;
}

type CancellationReason =
  | 'insured_request'
  | 'non_payment'
  | 'underwriting'
  | 'material_misrepresentation'
  | 'risk_change'
  | 'rewritten'
  | 'sold_property'
  | 'deceased';

type RefundMethod = 'pro_rata' | 'short_rate' | 'flat' | 'none';
```

## Document Generation

```typescript
interface PolicyDocumentService {
  // Generate documents
  generateDecPage(policyId: string): Promise<Document>;
  generatePolicyForms(policyId: string): Promise<Document[]>;
  generateIdCards(policyId: string): Promise<Document[]>;
  generateBillingNotice(policyId: string): Promise<Document>;

  // Batch generation
  generatePolicyPacket(policyId: string): Promise<PolicyPacket>;

  // Delivery
  deliverDocuments(policyId: string, method: DeliveryMethod): Promise<void>;
}

interface PolicyPacket {
  declarationsPage: Document;
  policyForms: Document[];
  endorsements: Document[];
  idCards?: Document[];
  billingStatement: Document;
  welcomeLetter: Document;
}
```
