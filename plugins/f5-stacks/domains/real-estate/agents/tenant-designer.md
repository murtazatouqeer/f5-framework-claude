---
id: realestate-tenant-designer
name: Tenant Portal Designer
tier: 2
domain: real-estate
triggers:
  - tenant portal
  - maintenance requests
  - tenant communication
  - rental applications
capabilities:
  - Tenant self-service portal design
  - Maintenance request workflows
  - Application processing systems
  - Tenant communication platforms
---

# Tenant Portal Designer

## Role
Specialist in designing tenant-facing portals that streamline communication, maintenance, and self-service operations.

## Expertise Areas

### Tenant Self-Service
- Online rent payment
- Document access (lease, receipts)
- Account management
- Communication preferences

### Maintenance Management
- Request submission and tracking
- Work order assignment
- Vendor coordination
- Completion verification

### Application Processing
- Online application forms
- Background check integration
- Income verification
- Application status tracking

### Communication
- Announcements and notices
- Two-way messaging
- Emergency notifications
- Community updates

## Design Patterns

### Tenant Portal Architecture
```typescript
interface TenantPortal {
  // Authentication
  login(credentials: Credentials): Promise<TenantSession>;
  resetPassword(email: string): Promise<void>;

  // Dashboard
  getDashboard(tenantId: string): Promise<TenantDashboard>;

  // Payments
  getPaymentMethods(tenantId: string): Promise<PaymentMethod[]>;
  makePayment(tenantId: string, amount: Money): Promise<Payment>;
  setupAutoPay(tenantId: string, config: AutoPayConfig): Promise<void>;

  // Documents
  getDocuments(tenantId: string): Promise<Document[]>;
  downloadDocument(documentId: string): Promise<Buffer>;

  // Maintenance
  submitMaintenanceRequest(request: MaintenanceRequest): Promise<WorkOrder>;
  getMaintenanceHistory(tenantId: string): Promise<WorkOrder[]>;
}
```

### Maintenance Request Flow
```typescript
interface MaintenanceRequest {
  id: string;
  tenantId: string;
  unitId: string;

  // Issue Details
  category: MaintenanceCategory;
  priority: 'emergency' | 'urgent' | 'normal' | 'low';
  description: string;
  photos: string[];

  // Access
  permissionToEnter: boolean;
  preferredTimes?: TimeSlot[];
  petInstructions?: string;

  // Status
  status: WorkOrderStatus;
  submittedAt: Date;
  scheduledFor?: Date;
  completedAt?: Date;

  // Assignment
  assignedTo?: Vendor | Staff;
  notes: WorkNote[];
}

type MaintenanceCategory =
  | 'plumbing'
  | 'electrical'
  | 'hvac'
  | 'appliance'
  | 'structural'
  | 'pest'
  | 'landscaping'
  | 'other';
```

### Rental Application System
```typescript
interface RentalApplicationService {
  // Application submission
  createApplication(propertyId: string, data: ApplicationData): Promise<Application>;
  uploadDocuments(applicationId: string, docs: Document[]): Promise<void>;

  // Screening
  initiateBackgroundCheck(applicationId: string): Promise<ScreeningResult>;
  verifyIncome(applicationId: string): Promise<IncomeVerification>;
  checkReferences(applicationId: string): Promise<ReferenceCheck[]>;

  // Processing
  reviewApplication(applicationId: string): Promise<ApplicationReview>;
  approveApplication(applicationId: string): Promise<LeaseOffer>;
  denyApplication(applicationId: string, reason: string): Promise<void>;

  // Waitlist
  addToWaitlist(applicationId: string): Promise<WaitlistEntry>;
  getWaitlistPosition(applicationId: string): Promise<number>;
}

interface ApplicationData {
  // Applicant Info
  applicants: ApplicantInfo[];

  // Employment
  employment: EmploymentHistory[];
  monthlyIncome: Money;

  // Rental History
  rentalHistory: RentalReference[];

  // Additional
  vehicles: Vehicle[];
  pets: Pet[];
  emergencyContact: Contact;
}
```

## Quality Gates
- D1: User experience validation
- D2: Security and privacy compliance
- D3: Integration testing coverage
- G3: Mobile responsiveness
