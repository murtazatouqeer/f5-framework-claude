---
id: hr-performance-designer
name: Performance Management Designer
tier: 2
domain: hr-management
triggers:
  - performance management
  - performance reviews
  - goals
  - feedback
capabilities:
  - Goal management systems
  - Performance review workflows
  - 360 feedback design
  - Competency frameworks
---

# Performance Management Designer

## Role
Specialist in designing performance management systems including goal setting, reviews, feedback, and development planning.

## Expertise Areas

### Goal Management
- OKR and goal frameworks
- Goal cascading
- Progress tracking
- Alignment visualization

### Performance Reviews
- Review cycle management
- Multi-rater feedback
- Calibration sessions
- Rating systems

### Continuous Feedback
- Real-time feedback tools
- Recognition programs
- 1:1 meeting tracking
- Pulse surveys

### Development Planning
- Competency frameworks
- Development plans
- Career pathing
- Succession planning

## Design Patterns

### Goal Data Model
```typescript
interface Goal {
  id: string;
  employeeId: string;

  // Goal Details
  title: string;
  description: string;
  type: GoalType;
  category: GoalCategory;

  // Alignment
  alignment: {
    parentGoalId?: string;
    companyObjectiveId?: string;
    departmentGoalId?: string;
  };

  // Measurement
  measurement: {
    type: 'quantitative' | 'qualitative' | 'milestone';
    metric?: string;
    target?: number;
    current?: number;
    unit?: string;
    milestones?: Milestone[];
  };

  // Timeline
  startDate: Date;
  dueDate: Date;

  // Status
  status: GoalStatus;
  progress: number; // 0-100
  confidence: 'on_track' | 'at_risk' | 'off_track';

  // Weight
  weight: number; // For weighted scoring

  // Reviews
  checkIns: GoalCheckIn[];
  comments: Comment[];

  // Metadata
  createdAt: Date;
  updatedAt: Date;
  createdBy: string;
}

type GoalType = 'individual' | 'team' | 'department' | 'company';
type GoalCategory = 'performance' | 'development' | 'project' | 'behavioral';
type GoalStatus = 'draft' | 'active' | 'completed' | 'cancelled' | 'deferred';

interface Milestone {
  id: string;
  title: string;
  dueDate: Date;
  completed: boolean;
  completedAt?: Date;
}

interface GoalCheckIn {
  id: string;
  date: Date;
  progress: number;
  notes: string;
  blockers?: string;
  nextSteps?: string;
  submittedBy: string;
}
```

### Performance Review Cycle
```typescript
interface ReviewCycle {
  id: string;
  name: string;
  type: ReviewType;

  // Timeline
  timeline: {
    selfReviewStart: Date;
    selfReviewEnd: Date;
    managerReviewStart: Date;
    managerReviewEnd: Date;
    calibrationStart?: Date;
    calibrationEnd?: Date;
    releaseDate: Date;
  };

  // Scope
  scope: {
    departments?: string[];
    locations?: string[];
    employeeTypes?: string[];
    excludedEmployees?: string[];
  };

  // Configuration
  config: {
    includeGoals: boolean;
    includeCompetencies: boolean;
    include360: boolean;
    includeRatings: boolean;
    ratingScale: RatingScale;
    questionnaire: Question[];
  };

  // Status
  status: CycleStatus;
  statistics: {
    totalEmployees: number;
    selfReviewsCompleted: number;
    managerReviewsCompleted: number;
    calibrated: number;
    released: number;
  };
}

type ReviewType = 'annual' | 'mid_year' | 'quarterly' | 'project' | 'probation';
type CycleStatus = 'draft' | 'scheduled' | 'self_review' | 'manager_review' | 'calibration' | 'released' | 'closed';

interface RatingScale {
  type: 'numeric' | 'descriptive';
  levels: RatingLevel[];
}

interface RatingLevel {
  value: number;
  label: string;
  description: string;
  color?: string;
}
```

### Performance Review Service
```typescript
interface PerformanceReviewService {
  // Cycle management
  createCycle(config: ReviewCycleConfig): Promise<ReviewCycle>;
  launchCycle(cycleId: string): Promise<void>;
  closeCycle(cycleId: string): Promise<void>;

  // Reviews
  createReview(cycleId: string, employeeId: string): Promise<PerformanceReview>;
  submitSelfReview(reviewId: string, responses: ReviewResponses): Promise<void>;
  submitManagerReview(reviewId: string, responses: ReviewResponses): Promise<void>;

  // 360 Feedback
  request360Feedback(reviewId: string, reviewers: string[]): Promise<void>;
  submit360Feedback(feedbackId: string, responses: FeedbackResponses): Promise<void>;

  // Calibration
  startCalibration(cycleId: string, groupId: string): Promise<CalibrationSession>;
  adjustRating(reviewId: string, newRating: number, justification: string): Promise<void>;

  // Release
  releaseReviews(cycleId: string): Promise<void>;
  acknowledgeReview(reviewId: string, employeeId: string): Promise<void>;
}

interface PerformanceReview {
  id: string;
  cycleId: string;
  employeeId: string;
  managerId: string;

  // Sections
  sections: {
    goals: GoalReviewSection;
    competencies?: CompetencyReviewSection;
    feedback360?: Feedback360Section;
    openEnded: OpenEndedSection;
  };

  // Ratings
  ratings: {
    selfRating?: number;
    managerRating?: number;
    finalRating?: number;
    calibratedRating?: number;
  };

  // Status
  status: ReviewStatus;
  selfReviewSubmittedAt?: Date;
  managerReviewSubmittedAt?: Date;
  calibratedAt?: Date;
  releasedAt?: Date;
  acknowledgedAt?: Date;

  // Comments
  managerComments?: string;
  employeeComments?: string;
  hrComments?: string;
}

type ReviewStatus =
  | 'not_started'
  | 'self_review_in_progress'
  | 'self_review_submitted'
  | 'manager_review_in_progress'
  | 'manager_review_submitted'
  | 'pending_calibration'
  | 'calibrated'
  | 'released'
  | 'acknowledged';
```

### Continuous Feedback System
```typescript
interface FeedbackService {
  // Giving feedback
  giveFeedback(feedback: FeedbackRequest): Promise<Feedback>;
  requestFeedback(request: FeedbackRequestConfig): Promise<void>;

  // Recognition
  giveRecognition(recognition: RecognitionRequest): Promise<Recognition>;
  endorseSkill(endorsement: SkillEndorsement): Promise<void>;

  // 1:1 Meetings
  schedule1on1(config: OneOnOneConfig): Promise<OneOnOne>;
  record1on1Notes(meetingId: string, notes: MeetingNotes): Promise<void>;

  // Analytics
  getFeedbackSummary(employeeId: string, period: DateRange): Promise<FeedbackSummary>;
}

interface Feedback {
  id: string;
  fromUserId: string;
  toUserId: string;
  type: FeedbackType;

  // Content
  content: string;
  competencies?: string[];
  values?: string[];

  // Visibility
  visibility: 'private' | 'manager' | 'public';
  isAnonymous: boolean;

  // Context
  context?: {
    projectId?: string;
    goalId?: string;
    meetingId?: string;
  };

  createdAt: Date;
}

type FeedbackType = 'praise' | 'constructive' | 'suggestion' | 'recognition';

interface Recognition {
  id: string;
  fromUserId: string;
  toUserIds: string[];

  // Recognition details
  title: string;
  message: string;
  badge?: Badge;
  values: string[];
  points?: number;

  // Visibility
  visibility: 'private' | 'team' | 'company';

  // Engagement
  reactions: Reaction[];
  comments: Comment[];

  createdAt: Date;
}

interface OneOnOne {
  id: string;
  managerId: string;
  employeeId: string;

  // Schedule
  scheduledAt: Date;
  duration: number;
  recurring: boolean;
  recurrence?: RecurrencePattern;

  // Content
  agenda: AgendaItem[];
  notes?: string;
  actionItems: ActionItem[];
  talkingPoints: TalkingPoint[];

  // Status
  status: 'scheduled' | 'completed' | 'cancelled' | 'rescheduled';
  completedAt?: Date;
}
```

### Competency Framework
```typescript
interface CompetencyFramework {
  id: string;
  name: string;
  description: string;

  // Competencies
  competencies: Competency[];

  // Mapping
  jobFamilyMappings: JobFamilyMapping[];
  levelMappings: LevelMapping[];
}

interface Competency {
  id: string;
  name: string;
  description: string;
  category: CompetencyCategory;

  // Levels
  levels: CompetencyLevel[];

  // Indicators
  behavioralIndicators: BehavioralIndicator[];
}

type CompetencyCategory = 'core' | 'leadership' | 'functional' | 'technical';

interface CompetencyLevel {
  level: number;
  name: string;
  description: string;
  expectedBehaviors: string[];
}

interface CompetencyAssessment {
  employeeId: string;
  assessorId: string;
  assessmentDate: Date;

  ratings: {
    competencyId: string;
    currentLevel: number;
    targetLevel: number;
    gap: number;
    evidence?: string;
  }[];

  overallAssessment: string;
  developmentRecommendations: string[];
}
```

## Quality Gates
- D1: Goal alignment validation
- D2: Review workflow completeness
- D3: Rating calibration logic
- G3: Analytics accuracy
