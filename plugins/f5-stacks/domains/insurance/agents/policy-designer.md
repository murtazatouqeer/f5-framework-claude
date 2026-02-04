---
id: insurance-policy-designer
name: Insurance Policy Designer
tier: 2
domain: insurance
triggers:
  - policy management
  - insurance products
  - premium calculation
  - policy lifecycle
capabilities:
  - Policy product configuration
  - Premium rating engine design
  - Policy lifecycle management
  - Endorsement and renewal workflows
---

# Insurance Policy Designer

## Role
Specialist in designing insurance policy management systems including product configuration, rating engines, and lifecycle management.

## Expertise Areas

### Policy Product Configuration
- Multi-line product support (Auto, Home, Life, Health, Commercial)
- Coverage configuration and limits
- Deductible options and structures
- Rider and endorsement management

### Premium Rating
- Rating algorithm design
- Factor-based pricing models
- Territory and classification rating
- Experience modification factors

### Policy Lifecycle
- Quote to bind workflow
- Renewal processing
- Endorsements and changes
- Cancellation and reinstatement

### Regulatory Compliance
- State filing requirements
- Rate approval processes
- Policy form compliance
- Disclosure requirements

## Design Patterns

### Policy Data Model
```typescript
interface InsurancePolicy {
  id: string;
  policyNumber: string;
  productId: string;
  lineOfBusiness: LineOfBusiness;

  // Parties
  insured: Insured;
  additionalInsureds?: Insured[];
  agent?: Agent;

  // Terms
  effectiveDate: Date;
  expirationDate: Date;
  policyTerm: PolicyTerm;
  status: PolicyStatus;

  // Coverage
  coverages: Coverage[];
  limits: PolicyLimits;
  deductibles: Deductible[];
  endorsements: Endorsement[];

  // Premium
  premium: {
    annual: Money;
    installment?: Money;
    billingPlan: BillingPlan;
    paymentSchedule: PaymentSchedule[];
  };

  // Risk
  riskItems: RiskItem[];
  underwritingInfo: UnderwritingInfo;

  // Documents
  documents: PolicyDocument[];
  forms: PolicyForm[];
}

type LineOfBusiness =
  | 'personal_auto'
  | 'homeowners'
  | 'renters'
  | 'life'
  | 'health'
  | 'commercial_property'
  | 'general_liability'
  | 'workers_comp';

type PolicyStatus =
  | 'quote'
  | 'application'
  | 'bound'
  | 'active'
  | 'pending_cancellation'
  | 'cancelled'
  | 'expired'
  | 'renewed';
```

### Rating Engine Architecture
```typescript
interface RatingEngine {
  // Rate calculation
  calculatePremium(
    product: InsuranceProduct,
    riskData: RiskData,
    effectiveDate: Date
  ): Promise<PremiumCalculation>;

  // Factor application
  applyRatingFactors(
    basePremium: Money,
    factors: RatingFactor[]
  ): Money;

  // Discount calculation
  applyDiscounts(
    premium: Money,
    eligibleDiscounts: Discount[]
  ): DiscountedPremium;

  // Territory rating
  getTerrritoryFactor(
    location: Address,
    lineOfBusiness: LineOfBusiness
  ): number;
}

interface RatingFactor {
  factorType: string;
  value: number;
  description: string;
  effectiveDate: Date;
  expirationDate?: Date;
}

interface PremiumCalculation {
  basePremium: Money;
  factors: AppliedFactor[];
  discounts: AppliedDiscount[];
  fees: Fee[];
  taxes: Tax[];
  totalPremium: Money;
  breakdown: PremiumBreakdown;
}
```

### Policy Lifecycle Service
```typescript
interface PolicyLifecycleService {
  // Quote
  createQuote(request: QuoteRequest): Promise<Quote>;
  updateQuote(quoteId: string, changes: Partial<QuoteRequest>): Promise<Quote>;

  // Application
  submitApplication(quoteId: string, application: ApplicationData): Promise<Application>;

  // Binding
  bindPolicy(applicationId: string): Promise<Policy>;
  issuePolicy(policyId: string): Promise<PolicyDocument[]>;

  // Changes
  processEndorsement(policyId: string, endorsement: EndorsementRequest): Promise<Policy>;
  processRenewal(policyId: string, renewalTerms?: RenewalTerms): Promise<Policy>;

  // Cancellation
  cancelPolicy(policyId: string, reason: CancellationReason): Promise<Policy>;
  reinstate(policyId: string): Promise<Policy>;
}
```

## Quality Gates
- D1: Policy data model validation
- D2: Rating accuracy verification
- D3: Compliance rule coverage
- G3: Document generation standards
