# Recruitment Patterns

## Overview
Design patterns for recruitment and applicant tracking systems.

## Key Patterns

### Pattern 1: Pipeline State Machine
**When to use:** Managing candidate progression through hiring stages
**Description:** State machine pattern for application pipeline
**Example:**
```typescript
interface PipelineStateMachine {
  stages: PipelineStage[];
  transitions: StageTransition[];
}

const recruitmentPipeline: PipelineStateMachine = {
  stages: [
    { id: 'new', name: 'New', order: 1, autoAdvance: false },
    { id: 'screening', name: 'Screening', order: 2, autoAdvance: true },
    { id: 'phone_screen', name: 'Phone Screen', order: 3, autoAdvance: false },
    { id: 'interview', name: 'Interview', order: 4, autoAdvance: false },
    { id: 'assessment', name: 'Assessment', order: 5, autoAdvance: false },
    { id: 'offer', name: 'Offer', order: 6, autoAdvance: false },
    { id: 'hired', name: 'Hired', order: 7, terminal: true },
    { id: 'rejected', name: 'Rejected', order: 8, terminal: true }
  ],
  transitions: [
    { from: 'new', to: 'screening', action: 'screen' },
    { from: 'new', to: 'rejected', action: 'reject' },
    { from: 'screening', to: 'phone_screen', action: 'advance' },
    { from: 'screening', to: 'rejected', action: 'reject' },
    { from: 'phone_screen', to: 'interview', action: 'advance' },
    { from: 'phone_screen', to: 'rejected', action: 'reject' },
    { from: 'interview', to: 'assessment', action: 'advance' },
    { from: 'interview', to: 'offer', action: 'skip_to_offer' },
    { from: 'interview', to: 'rejected', action: 'reject' },
    { from: 'assessment', to: 'offer', action: 'advance' },
    { from: 'assessment', to: 'rejected', action: 'reject' },
    { from: 'offer', to: 'hired', action: 'accept' },
    { from: 'offer', to: 'rejected', action: 'decline' }
  ]
};

class ApplicationPipelineService {
  private stateMachine: PipelineStateMachine;

  async transition(
    applicationId: string,
    action: string,
    metadata?: TransitionMetadata
  ): Promise<Application> {
    const application = await this.getApplication(applicationId);
    const currentStage = application.stage;

    const validTransition = this.stateMachine.transitions.find(
      t => t.from === currentStage && t.action === action
    );

    if (!validTransition) {
      throw new Error(`Invalid transition: ${currentStage} -> ${action}`);
    }

    // Execute transition
    const updatedApplication = await this.executeTransition(
      application,
      validTransition,
      metadata
    );

    // Record history
    await this.recordStageChange(application, validTransition, metadata);

    // Trigger automation
    await this.triggerAutomation(validTransition.to, updatedApplication);

    return updatedApplication;
  }

  private async triggerAutomation(
    newStage: string,
    application: Application
  ): Promise<void> {
    const stage = this.stateMachine.stages.find(s => s.id === newStage);

    if (stage?.autoAdvance) {
      // Auto-screen using AI/rules
      const screeningResult = await this.screeningService.screen(application);
      if (screeningResult.pass) {
        await this.transition(application.id, 'advance');
      }
    }

    // Send notifications
    await this.notificationService.sendStageChangeNotification(application);
  }
}
```

### Pattern 2: Resume Parsing & Scoring
**When to use:** Automated resume screening
**Description:** Extract and score resume data against job requirements
**Example:**
```typescript
interface ResumeParser {
  parse(document: Document): Promise<ParsedResume>;
  score(resume: ParsedResume, job: JobRequirements): Promise<ResumeScore>;
}

interface ParsedResume {
  contact: {
    name: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedIn?: string;
  };
  summary?: string;
  experience: WorkExperience[];
  education: Education[];
  skills: Skill[];
  certifications?: Certification[];
  languages?: Language[];
  rawText: string;
  parseConfidence: number;
}

interface WorkExperience {
  company: string;
  title: string;
  location?: string;
  startDate?: Date;
  endDate?: Date;
  current: boolean;
  description: string;
  highlights: string[];
}

class ResumeScreeningService implements ResumeParser {
  async parse(document: Document): Promise<ParsedResume> {
    // Extract text
    const text = await this.extractText(document);

    // Use NLP/ML to parse sections
    const sections = await this.identifySections(text);

    // Extract structured data
    const contact = await this.extractContact(sections.contact || text);
    const experience = await this.extractExperience(sections.experience);
    const education = await this.extractEducation(sections.education);
    const skills = await this.extractSkills(text);

    return {
      contact,
      summary: sections.summary,
      experience,
      education,
      skills,
      rawText: text,
      parseConfidence: this.calculateConfidence(sections)
    };
  }

  async score(resume: ParsedResume, job: JobRequirements): Promise<ResumeScore> {
    const scores: ScoreComponent[] = [];

    // Experience match
    const experienceScore = this.scoreExperience(
      resume.experience,
      job.experienceRequirements
    );
    scores.push({ category: 'experience', score: experienceScore.score, weight: 0.35 });

    // Skills match
    const skillsScore = this.scoreSkills(
      resume.skills,
      job.requiredSkills,
      job.preferredSkills
    );
    scores.push({ category: 'skills', score: skillsScore.score, weight: 0.30 });

    // Education match
    const educationScore = this.scoreEducation(
      resume.education,
      job.educationRequirements
    );
    scores.push({ category: 'education', score: educationScore.score, weight: 0.20 });

    // Keywords match
    const keywordsScore = this.scoreKeywords(
      resume.rawText,
      job.keywords
    );
    scores.push({ category: 'keywords', score: keywordsScore.score, weight: 0.15 });

    const totalScore = scores.reduce(
      (sum, s) => sum + s.score * s.weight, 0
    );

    return {
      totalScore,
      components: scores,
      matchedRequirements: this.getMatchedRequirements(resume, job),
      missingRequirements: this.getMissingRequirements(resume, job),
      recommendation: this.getRecommendation(totalScore)
    };
  }

  private getRecommendation(score: number): string {
    if (score >= 0.8) return 'strong_match';
    if (score >= 0.6) return 'good_match';
    if (score >= 0.4) return 'potential_match';
    return 'weak_match';
  }
}
```

### Pattern 3: Interview Scheduling with Availability
**When to use:** Coordinating multi-party interview schedules
**Description:** Find optimal interview slots across multiple calendars
**Example:**
```typescript
interface SchedulingService {
  getAvailability(
    users: string[],
    dateRange: DateRange,
    duration: number
  ): Promise<AvailableSlot[]>;

  scheduleInterview(
    slot: TimeSlot,
    participants: Participant[]
  ): Promise<Interview>;

  generateSelfScheduleLink(
    application: Application,
    options: SelfScheduleOptions
  ): Promise<string>;
}

interface AvailableSlot {
  start: Date;
  end: Date;
  availableInterviewers: string[];
  score: number; // Preference score
}

class InterviewSchedulingService implements SchedulingService {
  async getAvailability(
    interviewerIds: string[],
    dateRange: DateRange,
    duration: number
  ): Promise<AvailableSlot[]> {
    // Fetch calendar data for all interviewers
    const calendars = await Promise.all(
      interviewerIds.map(id => this.calendarService.getEvents(id, dateRange))
    );

    // Build availability matrix
    const slots: AvailableSlot[] = [];
    const interval = 30; // minutes

    let current = dateRange.start;
    while (current < dateRange.end) {
      const slotEnd = addMinutes(current, duration);

      // Check each interviewer's availability
      const availableInterviewers = interviewerIds.filter((id, index) => {
        const events = calendars[index];
        return this.isSlotAvailable(current, slotEnd, events) &&
               this.isWithinWorkingHours(current, slotEnd, id);
      });

      if (availableInterviewers.length > 0) {
        slots.push({
          start: current,
          end: slotEnd,
          availableInterviewers,
          score: this.calculateSlotScore(current, availableInterviewers)
        });
      }

      current = addMinutes(current, interval);
    }

    return slots.sort((a, b) => b.score - a.score);
  }

  async generateSelfScheduleLink(
    application: Application,
    options: SelfScheduleOptions
  ): Promise<string> {
    // Get available slots
    const slots = await this.getAvailability(
      options.interviewerIds,
      options.dateRange,
      options.duration
    );

    // Filter by preferences
    const filteredSlots = slots.filter(slot =>
      slot.availableInterviewers.length >= options.minInterviewers
    );

    // Create scheduling token
    const token = await this.createSchedulingToken({
      applicationId: application.id,
      slots: filteredSlots.slice(0, options.maxSlots || 20),
      expiresAt: options.linkExpiration,
      interviewType: options.interviewType
    });

    return `${this.baseUrl}/schedule/${token}`;
  }

  private calculateSlotScore(time: Date, interviewers: string[]): number {
    let score = 0;

    // Prefer more interviewers available
    score += interviewers.length * 10;

    // Prefer mid-day slots
    const hour = time.getHours();
    if (hour >= 10 && hour <= 14) score += 5;

    // Prefer weekdays
    const day = time.getDay();
    if (day >= 1 && day <= 5) score += 5;

    return score;
  }
}
```

### Pattern 4: Duplicate Detection
**When to use:** Preventing duplicate candidate records
**Description:** Identify and merge duplicate candidates
**Example:**
```typescript
interface DuplicateDetector {
  findDuplicates(candidate: Candidate): Promise<DuplicateMatch[]>;
  merge(primaryId: string, duplicateIds: string[]): Promise<Candidate>;
}

interface DuplicateMatch {
  candidateId: string;
  confidence: number;
  matchedFields: string[];
  candidate: Candidate;
}

class CandidateDuplicateService implements DuplicateDetector {
  async findDuplicates(candidate: Candidate): Promise<DuplicateMatch[]> {
    const matches: DuplicateMatch[] = [];

    // Exact email match (highest confidence)
    if (candidate.email) {
      const emailMatches = await this.repository.findByEmail(candidate.email);
      for (const match of emailMatches) {
        if (match.id !== candidate.id) {
          matches.push({
            candidateId: match.id,
            confidence: 0.95,
            matchedFields: ['email'],
            candidate: match
          });
        }
      }
    }

    // Phone number match
    if (candidate.phone) {
      const phoneMatches = await this.repository.findByPhone(
        this.normalizePhone(candidate.phone)
      );
      for (const match of phoneMatches) {
        const existing = matches.find(m => m.candidateId === match.id);
        if (existing) {
          existing.confidence = Math.min(0.99, existing.confidence + 0.3);
          existing.matchedFields.push('phone');
        } else if (match.id !== candidate.id) {
          matches.push({
            candidateId: match.id,
            confidence: 0.7,
            matchedFields: ['phone'],
            candidate: match
          });
        }
      }
    }

    // Name + location fuzzy match
    const nameMatches = await this.fuzzyNameSearch(candidate);
    for (const match of nameMatches) {
      const existing = matches.find(m => m.candidateId === match.id);
      if (existing) {
        existing.confidence = Math.min(0.99, existing.confidence + 0.2);
        existing.matchedFields.push('name');
      } else if (match.id !== candidate.id && match.similarity > 0.8) {
        matches.push({
          candidateId: match.id,
          confidence: match.similarity * 0.6,
          matchedFields: ['name'],
          candidate: match.candidate
        });
      }
    }

    return matches
      .filter(m => m.confidence >= 0.5)
      .sort((a, b) => b.confidence - a.confidence);
  }

  async merge(primaryId: string, duplicateIds: string[]): Promise<Candidate> {
    const primary = await this.repository.findById(primaryId);
    const duplicates = await Promise.all(
      duplicateIds.map(id => this.repository.findById(id))
    );

    // Merge data (prefer primary, fill gaps from duplicates)
    const merged = this.mergeData(primary, duplicates);

    // Update primary record
    await this.repository.update(primaryId, merged);

    // Transfer applications
    for (const duplicate of duplicates) {
      await this.applicationService.transferApplications(duplicate.id, primaryId);
    }

    // Mark duplicates as merged
    for (const duplicateId of duplicateIds) {
      await this.repository.markAsMerged(duplicateId, primaryId);
    }

    // Log merge action
    await this.auditService.log('candidate_merge', {
      primaryId,
      duplicateIds,
      mergedFields: this.getMergedFields(primary, merged)
    });

    return merged;
  }
}
```

## Best Practices
- Implement robust duplicate detection early
- Use state machines for pipeline management
- Cache calendar availability data
- Provide self-scheduling for better candidate experience
- Track source attribution for analytics

## Anti-Patterns to Avoid
- Hard-coding pipeline stages
- Ignoring timezone handling in scheduling
- No audit trail for stage changes
- Manual duplicate management
