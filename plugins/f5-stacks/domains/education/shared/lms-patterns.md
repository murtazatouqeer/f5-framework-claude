# LMS Patterns

## Overview
Common patterns and best practices for Learning Management System development.

## Key Patterns

### Pattern 1: Progress Tracking Strategy
**When to use:** Tracking learner progress across courses
**Description:** Multi-level progress tracking with caching
**Example:**
```typescript
interface ProgressTracker {
  // Lesson level
  markLessonComplete(userId: string, lessonId: string): Promise<void>;

  // Module level (calculated)
  getModuleProgress(userId: string, moduleId: string): Promise<number>;

  // Course level (calculated)
  getCourseProgress(userId: string, courseId: string): Promise<number>;
}

// Progress stored per lesson, aggregated up
const progress = {
  lessonProgress: new Map<string, boolean>(),
  calculateModuleProgress: () => completedLessons / totalLessons * 100
};
```

### Pattern 2: Video Progress Tracking
**When to use:** Tracking video watch progress
**Description:** Capture video events and store progress
**Example:**
```typescript
const videoTracker = {
  events: ['play', 'pause', 'seek', 'ended'],
  progressInterval: 10, // seconds

  trackProgress: (currentTime: number, duration: number) => {
    const progress = (currentTime / duration) * 100;
    const completed = progress >= 90; // 90% = completed
    return { progress, completed };
  }
};
```

### Pattern 3: Drip Content Scheduling
**When to use:** Releasing content on schedule
**Description:** Schedule-based content access control
**Example:**
```typescript
const dripScheduler = {
  strategies: {
    'fixed_date': (module, enrollDate) => module.releaseDate,
    'days_after_enroll': (module, enrollDate) =>
      addDays(enrollDate, module.daysAfterEnroll),
    'after_completion': (module, enrollDate, completedModules) =>
      completedModules.includes(module.prerequisite)
  }
};
```

### Pattern 4: Adaptive Learning Path
**When to use:** Personalized learning experience
**Description:** Adjust content based on learner performance
**Example:**
```typescript
const adaptivePath = {
  assessPerformance: (quizScore: number) => {
    if (quizScore >= 90) return 'advanced';
    if (quizScore >= 70) return 'intermediate';
    return 'remedial';
  },

  getNextContent: (level: string) => {
    return contentMap[level];
  }
};
```

## Best Practices
- Cache progress calculations aggressively
- Use async processing for certificate generation
- Implement video CDN for global delivery
- Store xAPI statements for analytics
- Support offline access with sync

## Anti-Patterns to Avoid
- Recalculating progress on every request
- Storing video files in database
- Tight coupling of assessment and content services
- Not handling video playback errors
