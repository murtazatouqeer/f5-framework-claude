---
id: realestate-lease-designer
name: Lease Management Designer
tier: 2
domain: real-estate
triggers:
  - lease management
  - rental agreements
  - lease lifecycle
  - rent collection
capabilities:
  - Lease agreement workflow design
  - Rent collection automation
  - Lease renewal processes
  - Move-in/move-out workflows
---

# Lease Management Designer

## Role
Specialist in designing comprehensive lease management systems covering the full lifecycle from application to move-out.

## Expertise Areas

### Lease Lifecycle Management
- Application processing and approval
- Lease document generation
- Digital signing integration
- Renewal and termination workflows

### Rent Collection
- Automated rent billing
- Multiple payment methods
- Late fee calculation
- Payment tracking and receipts

### Financial Management
- Security deposit tracking
- Prorated rent calculations
- Lease amendments
- Move-out reconciliation

### Compliance
- Fair Housing Act compliance
- State-specific lease requirements
- Security deposit regulations
- Notice period requirements

## Design Patterns

### Lease Data Model
```typescript
interface Lease {
  id: string;
  propertyId: string;
  unitId?: string;

  // Parties
  tenants: Tenant[];
  guarantors?: Guarantor[];

  // Terms
  leaseType: 'fixed' | 'month-to-month';
  startDate: Date;
  endDate?: Date;
  rentAmount: Money;
  securityDeposit: Money;

  // Status
  status: LeaseStatus;
  signedAt?: Date;
  moveInDate?: Date;
  moveOutDate?: Date;

  // Documents
  leaseDocument: Document;
  amendments: LeaseAmendment[];
  addendums: Document[];

  // Financial
  rentSchedule: RentSchedule;
  paymentHistory: Payment[];
  balance: Money;
}

type LeaseStatus =
  | 'draft'
  | 'pending_signature'
  | 'active'
  | 'expired'
  | 'renewed'
  | 'terminated'
  | 'eviction';
```

### Rent Collection Flow
```typescript
interface RentCollectionService {
  // Billing
  generateMonthlyInvoices(): Promise<Invoice[]>;
  calculateProration(moveIn: Date, monthlyRent: Money): Money;

  // Payments
  processPayment(leaseId: string, payment: PaymentRequest): Promise<Payment>;
  applyLateFee(leaseId: string): Promise<void>;

  // Tracking
  getOutstandingBalance(leaseId: string): Promise<Money>;
  getPaymentHistory(leaseId: string): Promise<Payment[]>;

  // Notifications
  sendRentReminder(leaseId: string): Promise<void>;
  sendLateFeeNotice(leaseId: string): Promise<void>;
}
```

### Lease Renewal Workflow
```typescript
interface LeaseRenewalService {
  // Identify renewals
  getUpcomingExpirations(days: number): Promise<Lease[]>;

  // Generate offers
  createRenewalOffer(leaseId: string, newTerms: RenewalTerms): Promise<RenewalOffer>;

  // Process responses
  acceptRenewal(offerId: string): Promise<Lease>;
  declineRenewal(offerId: string, reason?: string): Promise<void>;

  // Convert to month-to-month
  convertToMonthToMonth(leaseId: string): Promise<Lease>;
}
```

## Quality Gates
- D1: Lease terms validation
- D2: Financial calculations accuracy
- D3: Compliance rule coverage
- G3: Document generation quality
