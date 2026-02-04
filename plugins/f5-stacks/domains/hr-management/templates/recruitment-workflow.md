# Recruitment Workflow Template

## End-to-End Hiring Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Requisition │────▶│  Sourcing   │────▶│  Selection  │────▶│    Hire     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
      │                   │                   │                   │
      ▼                   ▼                   ▼                   ▼
  Create req          Post jobs          Screen               Offer
  Get approval        Source talent      Interview            Accept
  Define role         Build pipeline     Evaluate             Onboard
```

## Application Pipeline Stages

```typescript
type PipelineStage =
  | 'new'              // Just applied
  | 'screening'        // Resume review
  | 'phone_screen'     // Initial call
  | 'interview'        // In-person/video
  | 'assessment'       // Skills test
  | 'final_round'      // Final interviews
  | 'reference'        // Reference checks
  | 'offer'            // Offer stage
  | 'hired'            // Accepted
  | 'rejected'         // Not selected
  | 'withdrawn';       // Candidate withdrew
```

## Job Requisition

```typescript
interface JobRequisition {
  id: string;
  requisitionNumber: string;
  status: RequisitionStatus;

  // Position Details
  position: {
    title: string;
    jobCode: string;
    department: string;
    costCenter: string;
    location: string;
    locationType: LocationType;
    employmentType: EmploymentType;
    headcount: number;
  };

  // Job Description
  description: {
    summary: string;
    responsibilities: string[];
    requirements: {
      required: string[];
      preferred: string[];
    };
    qualifications: {
      education: string;
      experience: string;
      skills: string[];
      certifications?: string[];
    };
  };

  // Compensation
  compensation: {
    salaryRange: {
      min: number;
      max: number;
      currency: string;
    };
    payGrade?: string;
    bonus?: string;
    equity?: string;
    benefits: string[];
  };

  // Hiring Team
  hiringTeam: {
    hiringManager: HiringTeamMember;
    recruiter: HiringTeamMember;
    interviewers: HiringTeamMember[];
    approvers: Approver[];
  };

  // Timeline
  timeline: {
    targetStartDate: Date;
    targetFillDate: Date;
    postingDate?: Date;
    closeDate?: Date;
  };

  // Approval
  approval: {
    status: ApprovalStatus;
    history: ApprovalAction[];
  };

  // Metrics
  metrics: {
    views: number;
    applicants: number;
    qualified: number;
    interviewed: number;
    offers: number;
    hires: number;
    timeToFill?: number;
  };

  createdAt: Date;
  updatedAt: Date;
}

type RequisitionStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'open'
  | 'on_hold'
  | 'filled'
  | 'cancelled';

type LocationType = 'onsite' | 'remote' | 'hybrid';
type EmploymentType = 'full_time' | 'part_time' | 'contract' | 'intern' | 'temp';
```

## Job Posting

```typescript
interface JobPosting {
  id: string;
  requisitionId: string;
  status: PostingStatus;

  // Content
  content: {
    title: string;
    summary: string;
    description: string;
    requirements: string;
    benefits: string;
    applicationInstructions?: string;
  };

  // SEO
  seo: {
    keywords: string[];
    metaDescription: string;
  };

  // Distribution
  distribution: {
    careerSite: boolean;
    internalOnly: boolean;
    channels: PostingChannel[];
  };

  // Application Settings
  applicationSettings: {
    resumeRequired: boolean;
    coverLetterRequired: boolean;
    customQuestions: ScreeningQuestion[];
    eeoQuestions: boolean;
  };

  // Schedule
  schedule: {
    publishDate: Date;
    expirationDate?: Date;
  };

  // Tracking
  analytics: {
    views: number;
    clicks: number;
    applications: number;
    sourceBreakdown: Record<string, number>;
  };
}

interface PostingChannel {
  channel: string; // 'linkedin', 'indeed', 'glassdoor', etc.
  postingId?: string;
  status: 'pending' | 'active' | 'expired' | 'error';
  postedAt?: Date;
  expiresAt?: Date;
  cost?: Money;
}

interface ScreeningQuestion {
  id: string;
  question: string;
  type: 'text' | 'yes_no' | 'multiple_choice' | 'numeric';
  options?: string[];
  required: boolean;
  isKnockout: boolean;
  knockoutAnswer?: string;
}
```

## Application Process

```typescript
interface Application {
  id: string;
  candidateId: string;
  requisitionId: string;

  // Current State
  stage: PipelineStage;
  status: 'active' | 'hired' | 'rejected' | 'withdrawn';

  // Application Data
  applicationData: {
    resume: Document;
    coverLetter?: Document;
    screeningResponses: ScreeningResponse[];
    customResponses: CustomResponse[];
  };

  // Source
  source: {
    channel: string;
    campaign?: string;
    referrer?: string;
    utmParams?: Record<string, string>;
  };

  // Stage History
  stageHistory: StageTransition[];

  // Evaluation
  evaluation: {
    screeningScore?: number;
    interviewScores: InterviewScore[];
    assessmentScores: AssessmentScore[];
    overallRating?: number;
    recommendation?: Recommendation;
  };

  // Communication
  communications: Communication[];

  // Offer
  offer?: JobOffer;

  // Dates
  appliedAt: Date;
  lastActivityAt: Date;
  hiredAt?: Date;
  rejectedAt?: Date;
}

interface StageTransition {
  fromStage: PipelineStage;
  toStage: PipelineStage;
  reason?: string;
  movedBy: string;
  movedAt: Date;
}
```

## Interview Process

```typescript
interface InterviewProcess {
  applicationId: string;
  rounds: InterviewRound[];
  status: 'scheduled' | 'in_progress' | 'completed';
}

interface InterviewRound {
  roundNumber: number;
  type: InterviewType;
  status: RoundStatus;

  // Schedule
  interviews: Interview[];

  // Evaluation
  scorecards: Scorecard[];
  roundDecision?: 'advance' | 'reject' | 'hold';
  decisionMadeBy?: string;
  decisionMadeAt?: Date;
}

type InterviewType =
  | 'phone_screen'
  | 'video'
  | 'onsite'
  | 'panel'
  | 'technical'
  | 'behavioral'
  | 'case_study'
  | 'presentation'
  | 'culture_fit';

interface Interview {
  id: string;
  roundId: string;
  type: InterviewType;

  // Participants
  candidate: {
    id: string;
    name: string;
    email: string;
  };
  interviewers: Interviewer[];

  // Schedule
  scheduledAt: Date;
  duration: number;
  timezone: string;

  // Location
  location: {
    type: 'in_person' | 'video' | 'phone';
    address?: string;
    room?: string;
    meetingLink?: string;
    dialIn?: string;
  };

  // Status
  status: InterviewStatus;
  confirmedAt?: Date;
  completedAt?: Date;

  // Feedback
  scorecardId?: string;
}

type InterviewStatus =
  | 'scheduling'
  | 'scheduled'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'no_show';

interface Scorecard {
  id: string;
  interviewId: string;
  interviewerId: string;

  // Criteria Ratings
  criteria: {
    name: string;
    category: string;
    rating: number;
    notes?: string;
  }[];

  // Overall Assessment
  overallRating: number;
  recommendation: 'strong_yes' | 'yes' | 'no' | 'strong_no';

  // Feedback
  strengths: string;
  concerns: string;
  additionalNotes?: string;

  // Metadata
  submittedAt: Date;
  timeSpent?: number;
}
```

## Offer Management

```typescript
interface JobOffer {
  id: string;
  applicationId: string;
  candidateId: string;
  requisitionId: string;

  // Offer Details
  details: {
    title: string;
    department: string;
    location: string;
    startDate: Date;
    employmentType: EmploymentType;
    reportsTo: string;
  };

  // Compensation
  compensation: {
    baseSalary: Money;
    bonus?: {
      type: 'signing' | 'annual' | 'quarterly';
      amount: Money;
    };
    equity?: {
      type: string;
      amount: number;
      vestingSchedule: string;
    };
    benefits: string[];
    otherCompensation?: string;
  };

  // Terms
  terms: {
    offerExpirationDate: Date;
    contingencies: string[];
    specialConditions?: string;
  };

  // Approval
  approval: {
    status: ApprovalStatus;
    approvers: Approver[];
    history: ApprovalAction[];
  };

  // Status
  status: OfferStatus;

  // Response
  response?: {
    decision: 'accepted' | 'declined' | 'negotiating';
    respondedAt: Date;
    declineReason?: string;
    counterOffer?: CounterOffer;
  };

  // Documents
  offerLetter?: Document;
  signedOffer?: Document;

  // Dates
  createdAt: Date;
  sentAt?: Date;
  acceptedAt?: Date;
}

type OfferStatus =
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'sent'
  | 'viewed'
  | 'accepted'
  | 'declined'
  | 'expired'
  | 'withdrawn'
  | 'negotiating';

interface CounterOffer {
  proposedSalary?: Money;
  proposedBonus?: Money;
  proposedStartDate?: Date;
  otherRequests?: string;
  submittedAt: Date;
}
```

## Hiring Workflow Service

```typescript
interface HiringWorkflowService {
  // Requisition
  createRequisition(req: CreateRequisitionRequest): Promise<JobRequisition>;
  submitForApproval(reqId: string): Promise<void>;
  approveRequisition(reqId: string, approver: string): Promise<void>;

  // Posting
  createPosting(reqId: string, posting: CreatePostingRequest): Promise<JobPosting>;
  publishPosting(postingId: string): Promise<void>;
  distributeToChannels(postingId: string, channels: string[]): Promise<void>;

  // Application
  processApplication(application: IncomingApplication): Promise<Application>;
  screenApplication(appId: string): Promise<ScreeningResult>;
  moveToStage(appId: string, stage: PipelineStage, reason?: string): Promise<void>;

  // Interview
  scheduleInterview(appId: string, config: InterviewConfig): Promise<Interview>;
  submitScorecard(interviewId: string, scorecard: ScorecardSubmission): Promise<void>;
  makeInterviewDecision(roundId: string, decision: string): Promise<void>;

  // Offer
  createOffer(appId: string, offer: CreateOfferRequest): Promise<JobOffer>;
  sendOffer(offerId: string): Promise<void>;
  processOfferResponse(offerId: string, response: OfferResponse): Promise<void>;

  // Hire
  convertToEmployee(appId: string): Promise<Employee>;
}
```
