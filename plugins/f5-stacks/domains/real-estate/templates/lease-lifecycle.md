# Lease Lifecycle Template

## Complete Lease Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Application │────▶│  Approved   │────▶│   Active    │────▶│   Renewal   │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Submit app         Sign lease          Collect rent        Offer terms
  Background         Collect deposit     Maintenance         Sign renewal
  Income verify      Move-in inspect     Communication       OR Move-out
```

## Lease States

```typescript
type LeaseStatus =
  | 'application_pending'
  | 'application_approved'
  | 'application_denied'
  | 'lease_pending_signature'
  | 'lease_signed'
  | 'move_in_scheduled'
  | 'active'
  | 'renewal_offered'
  | 'renewal_accepted'
  | 'notice_given'
  | 'move_out_scheduled'
  | 'move_out_complete'
  | 'deposit_reconciled'
  | 'closed'
  | 'eviction_process';
```

## Lease Data Model

```typescript
interface Lease {
  id: string;
  propertyId: string;
  unitId: string;

  // Parties
  landlord: {
    id: string;
    name: string;
    company?: string;
  };
  tenants: Tenant[];
  guarantors?: Guarantor[];

  // Terms
  terms: {
    leaseType: 'fixed_term' | 'month_to_month';
    startDate: Date;
    endDate?: Date;
    monthlyRent: Money;
    rentDueDay: number; // 1-28
    lateFeeGracePeriod: number; // days
    lateFeeAmount: Money;
    securityDeposit: Money;
    petDeposit?: Money;
    petRent?: Money;
  };

  // Move-in/out
  moveIn?: {
    date: Date;
    inspection: Inspection;
    keysIssued: string[];
  };
  moveOut?: {
    noticeDate?: Date;
    scheduledDate?: Date;
    actualDate?: Date;
    inspection?: Inspection;
    keysReturned?: string[];
  };

  // Documents
  documents: {
    leaseAgreement: SignedDocument;
    addendums: SignedDocument[];
    moveInChecklist?: Document;
    moveOutChecklist?: Document;
  };

  // Financial
  financial: {
    balance: Money;
    lastPaymentDate?: Date;
    nextPaymentDue: Date;
  };

  status: LeaseStatus;
  createdAt: Date;
  updatedAt: Date;
}

interface Tenant {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  dateOfBirth: Date;
  ssn?: string; // Encrypted
  driversLicense?: string;
  emergencyContact: Contact;
  isPrimary: boolean;
}
```

## Application Processing

```typescript
interface RentalApplication {
  id: string;
  propertyId: string;
  unitId: string;
  status: ApplicationStatus;

  // Applicants
  applicants: {
    personal: {
      firstName: string;
      lastName: string;
      email: string;
      phone: string;
      dateOfBirth: Date;
      ssn: string; // For background check
      driversLicense: string;
    };
    currentAddress: Address;
    desiredMoveInDate: Date;
  }[];

  // Employment
  employment: {
    employer: string;
    position: string;
    monthlyIncome: Money;
    startDate: Date;
    supervisorName: string;
    supervisorPhone: string;
    payStubs: Document[];
  }[];

  // Rental History
  rentalHistory: {
    address: Address;
    landlordName: string;
    landlordPhone: string;
    monthlyRent: Money;
    startDate: Date;
    endDate?: Date;
    reasonForLeaving?: string;
  }[];

  // Additional
  vehicles: Vehicle[];
  pets: Pet[];
  additionalOccupants: { name: string; relationship: string; age: number }[];

  // Screening Results
  screening?: {
    creditScore?: number;
    backgroundCheck?: BackgroundCheckResult;
    evictionHistory?: EvictionRecord[];
    incomeVerified?: boolean;
    referencesChecked?: boolean;
  };

  // Processing
  applicationFee: Money;
  feePaid: boolean;
  submittedAt: Date;
  processedAt?: Date;
  decision?: 'approved' | 'denied' | 'conditional';
  decisionReason?: string;
}

type ApplicationStatus =
  | 'draft'
  | 'submitted'
  | 'fee_pending'
  | 'screening'
  | 'under_review'
  | 'approved'
  | 'denied'
  | 'waitlisted'
  | 'expired';
```

## Rent Collection

```typescript
interface RentPayment {
  id: string;
  leaseId: string;
  tenantId: string;

  // Amount
  amount: Money;
  breakdown: {
    baseRent: Money;
    utilities?: Money;
    petRent?: Money;
    parking?: Money;
    lateFee?: Money;
    other?: { description: string; amount: Money }[];
  };

  // Payment Details
  method: 'ach' | 'credit_card' | 'debit_card' | 'check' | 'cash' | 'money_order';
  status: PaymentStatus;
  transactionId?: string;

  // Timing
  dueDate: Date;
  paidAt?: Date;
  period: {
    month: number;
    year: number;
  };

  // Metadata
  receiptNumber: string;
  notes?: string;
}

type PaymentStatus =
  | 'scheduled'
  | 'pending'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'refunded'
  | 'disputed';

interface RentCollectionService {
  // Billing
  generateInvoice(leaseId: string, period: { month: number; year: number }): Promise<Invoice>;
  calculateLateFee(leaseId: string): Promise<Money>;
  applyLateFee(leaseId: string): Promise<void>;

  // Payments
  processPayment(leaseId: string, payment: PaymentRequest): Promise<RentPayment>;
  scheduleRecurringPayment(leaseId: string, config: AutoPayConfig): Promise<void>;

  // Tracking
  getLedger(leaseId: string): Promise<LedgerEntry[]>;
  getBalance(leaseId: string): Promise<Money>;

  // Reminders
  sendRentReminder(leaseId: string): Promise<void>;
  sendLateNotice(leaseId: string): Promise<void>;
}
```

## Move-Out Process

```typescript
interface MoveOutProcess {
  leaseId: string;

  // Notice
  notice: {
    receivedDate: Date;
    effectiveDate: Date;
    reason?: string;
    forwardingAddress?: Address;
  };

  // Inspection
  inspection: {
    scheduledDate: Date;
    completedDate?: Date;
    inspector: string;
    condition: RoomCondition[];
    photos: Photo[];
    damages: Damage[];
  };

  // Deposit Reconciliation
  deposit: {
    originalAmount: Money;
    deductions: {
      description: string;
      amount: Money;
      photos?: Photo[];
    }[];
    refundAmount: Money;
    refundMethod: 'check' | 'ach';
    refundSentDate?: Date;
    itemizedStatement: Document;
  };

  // Keys
  keys: {
    issued: string[];
    returned: string[];
    unreturned: string[];
    replacementCharge?: Money;
  };

  // Final
  finalWalkthrough?: Date;
  unitTurnover?: {
    cleaningRequired: boolean;
    repairsRequired: Repair[];
    estimatedReadyDate: Date;
  };
}
```
