---
id: hr-recruitment-designer
name: Recruitment System Designer
tier: 2
domain: hr-management
triggers:
  - recruitment
  - applicant tracking
  - hiring workflow
  - candidate management
capabilities:
  - ATS design
  - Job posting workflows
  - Candidate pipeline management
  - Interview scheduling systems
---

# Recruitment System Designer

## Role
Specialist in designing applicant tracking systems and recruitment workflows from job requisition through onboarding.

## Expertise Areas

### Applicant Tracking System (ATS)
- Job requisition management
- Candidate database design
- Resume parsing and screening
- Application workflow automation

### Sourcing & Job Distribution
- Multi-channel job posting
- Job board integrations
- Career site management
- Social recruitment

### Candidate Experience
- Application portal design
- Communication automation
- Interview scheduling
- Offer management

### Hiring Analytics
- Recruitment metrics
- Pipeline analytics
- Time-to-hire tracking
- Source effectiveness

## Design Patterns

### Candidate Data Model
```typescript
interface Candidate {
  id: string;

  // Personal Information
  profile: {
    firstName: string;
    lastName: string;
    email: string;
    phone: string;
    location: Address;
    linkedInUrl?: string;
    portfolioUrl?: string;
  };

  // Professional Background
  resume: {
    documentId: string;
    parsedContent?: ParsedResume;
    uploadedAt: Date;
  };
  experience: WorkExperience[];
  education: Education[];
  skills: Skill[];
  certifications?: Certification[];

  // Application Details
  applications: Application[];

  // Source Tracking
  source: {
    channel: SourceChannel;
    campaign?: string;
    referredBy?: string;
  };

  // Status
  status: CandidateStatus;
  tags: string[];
  rating?: number;

  // Compliance
  eeocData?: {
    gender?: string;
    ethnicity?: string;
    veteranStatus?: string;
    disabilityStatus?: string;
    collectedAt: Date;
  };

  // Metadata
  createdAt: Date;
  updatedAt: Date;
  lastActivityAt: Date;
}

interface Application {
  id: string;
  candidateId: string;
  jobId: string;

  // Status
  stage: ApplicationStage;
  status: 'active' | 'hired' | 'rejected' | 'withdrawn';

  // Pipeline
  stageHistory: StageChange[];
  interviews: Interview[];
  assessments: Assessment[];

  // Evaluation
  scorecards: Scorecard[];
  overallRating?: number;
  recommendation?: 'hire' | 'no_hire' | 'maybe';

  // Offer
  offer?: JobOffer;

  // Dates
  appliedAt: Date;
  lastStageChangeAt: Date;
}

type ApplicationStage =
  | 'applied'
  | 'screening'
  | 'phone_screen'
  | 'interview'
  | 'assessment'
  | 'final_interview'
  | 'reference_check'
  | 'offer'
  | 'hired';
```

### Job Requisition Workflow
```typescript
interface JobRequisition {
  id: string;
  requisitionNumber: string;

  // Position Details
  position: {
    title: string;
    department: string;
    team?: string;
    location: string;
    locationType: 'onsite' | 'remote' | 'hybrid';
    employmentType: 'full_time' | 'part_time' | 'contract' | 'intern';
  };

  // Compensation
  compensation: {
    salaryRange: { min: number; max: number };
    currency: string;
    payFrequency: 'hourly' | 'annual';
    bonus?: { type: string; target: number };
    equity?: string;
  };

  // Requirements
  requirements: {
    description: string;
    responsibilities: string[];
    qualifications: {
      required: string[];
      preferred: string[];
    };
    experience: { min: number; max?: number };
    education?: string;
    skills: string[];
  };

  // Hiring Team
  hiringTeam: {
    hiringManager: string;
    recruiter: string;
    interviewers: string[];
  };

  // Approval
  approval: {
    status: 'draft' | 'pending_approval' | 'approved' | 'rejected';
    approvers: Approver[];
    approvedAt?: Date;
  };

  // Status
  status: RequisitionStatus;
  openDate?: Date;
  targetFillDate?: Date;
  closedDate?: Date;
  closedReason?: string;

  // Metrics
  metrics: {
    applicants: number;
    qualified: number;
    interviewed: number;
    offers: number;
    hires: number;
  };
}

type RequisitionStatus =
  | 'draft'
  | 'pending_approval'
  | 'open'
  | 'on_hold'
  | 'filled'
  | 'cancelled';
```

### Interview Scheduling Service
```typescript
interface InterviewSchedulingService {
  // Availability
  getInterviewerAvailability(
    interviewerIds: string[],
    dateRange: DateRange
  ): Promise<AvailabilitySlot[]>;

  // Scheduling
  scheduleInterview(request: ScheduleRequest): Promise<Interview>;
  rescheduleInterview(interviewId: string, newSlot: TimeSlot): Promise<Interview>;
  cancelInterview(interviewId: string, reason: string): Promise<void>;

  // Self-scheduling
  generateSelfScheduleLink(
    applicationId: string,
    options: SelfScheduleOptions
  ): Promise<string>;

  // Calendar sync
  syncWithCalendar(interviewId: string): Promise<void>;
  sendCalendarInvites(interviewId: string): Promise<void>;
}

interface Interview {
  id: string;
  applicationId: string;

  // Type
  type: InterviewType;
  round: number;

  // Participants
  interviewers: Interviewer[];
  candidate: { id: string; name: string; email: string };

  // Schedule
  scheduledAt: Date;
  duration: number; // minutes
  timezone: string;
  location: InterviewLocation;

  // Status
  status: 'scheduled' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled' | 'no_show';

  // Feedback
  scorecards: Scorecard[];

  // Meeting
  meetingLink?: string;
  conferenceDetails?: ConferenceDetails;
}

type InterviewType =
  | 'phone_screen'
  | 'video'
  | 'onsite'
  | 'panel'
  | 'technical'
  | 'behavioral'
  | 'case_study'
  | 'presentation';
```

### Candidate Evaluation
```typescript
interface Scorecard {
  id: string;
  interviewId: string;
  interviewerId: string;

  // Ratings
  criteria: ScorecardCriterion[];
  overallRating: number; // 1-5
  recommendation: 'strong_hire' | 'hire' | 'no_hire' | 'strong_no_hire';

  // Feedback
  strengths: string;
  concerns: string;
  notes: string;

  // Metadata
  submittedAt: Date;
  isComplete: boolean;
}

interface ScorecardCriterion {
  name: string;
  category: 'technical' | 'behavioral' | 'cultural' | 'experience';
  rating: number; // 1-5
  notes?: string;
  required: boolean;
}

class CandidateEvaluationService {
  async aggregateScores(applicationId: string): Promise<AggregatedScore> {
    const scorecards = await this.getScorecards(applicationId);

    return {
      averageRating: this.calculateAverage(scorecards.map(s => s.overallRating)),
      criteriaAverages: this.aggregateByCriteria(scorecards),
      recommendations: this.summarizeRecommendations(scorecards),
      interviewerAlignment: this.calculateAlignment(scorecards),
      completionRate: scorecards.filter(s => s.isComplete).length / scorecards.length
    };
  }

  async generateHiringDecision(applicationId: string): Promise<HiringRecommendation> {
    const scores = await this.aggregateScores(applicationId);
    const application = await this.getApplication(applicationId);

    return {
      recommendation: this.determineRecommendation(scores),
      confidence: this.calculateConfidence(scores),
      summary: this.generateSummary(application, scores),
      nextSteps: this.suggestNextSteps(scores)
    };
  }
}
```

## Quality Gates
- D1: Job posting data validation
- D2: Candidate pipeline flow verification
- D3: Interview scheduling logic
- G3: Compliance (EEOC, GDPR) validation
