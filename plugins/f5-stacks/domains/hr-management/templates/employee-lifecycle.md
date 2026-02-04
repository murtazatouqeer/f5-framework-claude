# Employee Lifecycle Template

## Complete Employee Journey

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Hire       │────▶│  Onboard    │────▶│  Develop    │────▶│  Transition │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Offer accepted       First day          Performance         Promotion
  Background check     Training           Feedback            Transfer
  Pre-boarding         IT setup           Growth              Offboarding
```

## Employee States

```typescript
type EmployeeStatus =
  | 'pre_hire'           // Offer accepted, not started
  | 'onboarding'         // First days/weeks
  | 'active'             // Regular employee
  | 'on_leave'           // Various leave types
  | 'suspended'          // Administrative action
  | 'notice_period'      // Resignation/termination notice
  | 'offboarding'        // Final days
  | 'terminated'         // No longer employed
  | 'alumni';            // Former employee
```

## Employee Data Model

```typescript
interface Employee {
  id: string;
  employeeNumber: string;

  // Personal Information
  personal: {
    firstName: string;
    middleName?: string;
    lastName: string;
    preferredName?: string;
    dateOfBirth: Date;
    gender?: string;
    maritalStatus?: string;
    nationality?: string;
    ssn?: string; // Encrypted
  };

  // Contact
  contact: {
    email: string;
    personalEmail?: string;
    phone: string;
    address: Address;
    emergencyContacts: EmergencyContact[];
  };

  // Employment
  employment: {
    status: EmployeeStatus;
    type: 'full_time' | 'part_time' | 'contractor' | 'intern' | 'temp';
    hireDate: Date;
    originalHireDate?: Date; // For rehires
    terminationDate?: Date;
    terminationReason?: string;
    probationEndDate?: Date;
  };

  // Position
  position: {
    title: string;
    jobCode: string;
    department: string;
    division?: string;
    location: string;
    workLocation: 'onsite' | 'remote' | 'hybrid';
    reportsTo: string;
    directReports?: string[];
  };

  // Compensation
  compensation: {
    payType: 'salary' | 'hourly';
    payRate: Money;
    payFrequency: PayFrequency;
    flsaStatus: 'exempt' | 'non_exempt';
    compensationHistory: CompensationChange[];
  };

  // Benefits
  benefits: {
    eligibilityDate: Date;
    enrollments: BenefitEnrollment[];
    ptoBalance: PTOBalance;
  };

  // Documents
  documents: EmployeeDocument[];

  // System
  userId?: string;
  createdAt: Date;
  updatedAt: Date;
}
```

## Pre-Boarding Process

```typescript
interface PreBoardingWorkflow {
  employeeId: string;
  startDate: Date;
  status: PreBoardingStatus;

  // Tasks
  tasks: {
    // HR Tasks
    backgroundCheck: TaskStatus;
    i9Verification: TaskStatus;
    taxForms: TaskStatus;
    directDepositSetup: TaskStatus;
    benefitsEnrollment: TaskStatus;
    policyAcknowledgments: TaskStatus;

    // IT Tasks
    accountCreation: TaskStatus;
    equipmentOrder: TaskStatus;
    accessProvisioning: TaskStatus;

    // Manager Tasks
    workspaceSetup: TaskStatus;
    welcomeEmail: TaskStatus;
    firstDayAgenda: TaskStatus;
  };

  // Documents to Collect
  requiredDocuments: {
    type: string;
    received: boolean;
    receivedAt?: Date;
    verified: boolean;
  }[];

  // Communications
  communicationsSent: {
    type: string;
    sentAt: Date;
    template: string;
  }[];
}

type PreBoardingStatus =
  | 'pending_documents'
  | 'documents_received'
  | 'background_in_progress'
  | 'ready_for_start'
  | 'completed';
```

## Onboarding Workflow

```typescript
interface OnboardingPlan {
  employeeId: string;
  startDate: Date;
  buddyId?: string;
  managerId: string;

  // Timeline
  timeline: {
    day1: OnboardingTask[];
    week1: OnboardingTask[];
    month1: OnboardingTask[];
    month3?: OnboardingTask[];
  };

  // Milestones
  milestones: {
    day30Review: {
      scheduled: Date;
      completed?: Date;
      feedback?: string;
    };
    day60Review: {
      scheduled: Date;
      completed?: Date;
      feedback?: string;
    };
    day90Review: {
      scheduled: Date;
      completed?: Date;
      feedback?: string;
      probationDecision?: 'pass' | 'extend' | 'fail';
    };
  };

  // Progress
  progress: {
    tasksCompleted: number;
    totalTasks: number;
    percentComplete: number;
  };

  status: 'not_started' | 'in_progress' | 'completed';
}

interface OnboardingTask {
  id: string;
  title: string;
  description: string;
  category: OnboardingCategory;
  assignedTo: 'employee' | 'manager' | 'hr' | 'it' | 'buddy';
  dueDate: Date;
  status: 'pending' | 'in_progress' | 'completed' | 'skipped';
  completedAt?: Date;
  completedBy?: string;
  resources?: Resource[];
}

type OnboardingCategory =
  | 'orientation'
  | 'training'
  | 'compliance'
  | 'tools_access'
  | 'team_intro'
  | 'goal_setting'
  | 'culture';
```

## Position Changes

```typescript
interface PositionChange {
  id: string;
  employeeId: string;
  type: PositionChangeType;
  effectiveDate: Date;

  // Previous
  previous: {
    title: string;
    department: string;
    location: string;
    manager: string;
    payRate: Money;
  };

  // New
  new: {
    title: string;
    department: string;
    location: string;
    manager: string;
    payRate: Money;
  };

  // Approval
  approvalStatus: 'pending' | 'approved' | 'rejected';
  approvedBy?: string;
  approvedAt?: Date;

  // Reason
  reason: string;
  justification?: string;

  createdAt: Date;
  createdBy: string;
}

type PositionChangeType =
  | 'promotion'
  | 'lateral_transfer'
  | 'demotion'
  | 'location_change'
  | 'department_change'
  | 'title_change'
  | 'compensation_adjustment';

interface PositionChangeService {
  // Create change request
  initiateChange(request: PositionChangeRequest): Promise<PositionChange>;

  // Approval workflow
  submitForApproval(changeId: string): Promise<void>;
  approve(changeId: string, approver: string): Promise<void>;
  reject(changeId: string, approver: string, reason: string): Promise<void>;

  // Process change
  processChange(changeId: string): Promise<void>;

  // History
  getChangeHistory(employeeId: string): Promise<PositionChange[]>;
}
```

## Leave Management

```typescript
interface LeaveRequest {
  id: string;
  employeeId: string;
  type: LeaveType;

  // Duration
  startDate: Date;
  endDate: Date;
  totalDays: number;
  halfDay?: 'first_half' | 'second_half';

  // Details
  reason?: string;
  attachments?: Document[];

  // Approval
  status: LeaveStatus;
  approverId: string;
  approvedAt?: Date;
  rejectionReason?: string;

  // Balance Impact
  balanceBefore: number;
  balanceAfter: number;

  createdAt: Date;
}

type LeaveType =
  | 'vacation'
  | 'sick'
  | 'personal'
  | 'bereavement'
  | 'jury_duty'
  | 'parental'
  | 'fmla'
  | 'military'
  | 'unpaid'
  | 'sabbatical';

type LeaveStatus =
  | 'draft'
  | 'pending'
  | 'approved'
  | 'rejected'
  | 'cancelled'
  | 'in_progress'
  | 'completed';

interface PTOBalance {
  employeeId: string;
  asOfDate: Date;

  balances: {
    leaveType: LeaveType;
    accrued: number;
    used: number;
    pending: number;
    available: number;
    carryover?: number;
    forfeitDate?: Date;
  }[];
}
```

## Offboarding Process

```typescript
interface OffboardingWorkflow {
  employeeId: string;
  terminationType: TerminationType;
  lastWorkingDay: Date;
  separationDate: Date;

  // Reason
  reason: TerminationReason;
  voluntaryReason?: string;
  involuntaryReason?: string;

  // Tasks
  tasks: {
    // HR Tasks
    exitInterview: TaskStatus;
    benefitsTermination: TaskStatus;
    finalPayCalculation: TaskStatus;
    cobraNotification: TaskStatus;
    w2Preparation: TaskStatus;
    recordsRetention: TaskStatus;

    // IT Tasks
    accountDeactivation: TaskStatus;
    equipmentReturn: TaskStatus;
    accessRevocation: TaskStatus;
    dataBackup: TaskStatus;

    // Manager Tasks
    knowledgeTransfer: TaskStatus;
    projectHandoff: TaskStatus;
    teamNotification: TaskStatus;

    // Employee Tasks
    equipmentReturn: TaskStatus;
    expenseSettlement: TaskStatus;
    propertyReturn: TaskStatus;
  };

  // Exit Interview
  exitInterview?: {
    scheduled: Date;
    completed?: Date;
    conductedBy: string;
    feedback?: ExitFeedback;
  };

  // Final Pay
  finalPay: {
    regularPay: Money;
    accruedPTO: Money;
    bonus?: Money;
    deductions: Money;
    netPay: Money;
    paymentDate: Date;
  };

  // Status
  status: OffboardingStatus;
}

type TerminationType = 'voluntary' | 'involuntary' | 'retirement' | 'death' | 'end_of_contract';

type TerminationReason =
  | 'resignation'
  | 'retirement'
  | 'performance'
  | 'conduct'
  | 'layoff'
  | 'restructuring'
  | 'position_elimination'
  | 'mutual_agreement'
  | 'contract_end'
  | 'other';

type OffboardingStatus =
  | 'initiated'
  | 'in_progress'
  | 'pending_final_pay'
  | 'completed';
```
