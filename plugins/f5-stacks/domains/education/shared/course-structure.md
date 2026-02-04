# Course Structure Template

## Course Hierarchy

```
Course
├── Overview
│   ├── Description
│   ├── Learning Objectives
│   ├── Prerequisites
│   └── Estimated Duration
│
├── Module 1: [Topic Name]
│   ├── Introduction
│   ├── Lesson 1.1: [Lesson Title]
│   │   ├── Video Content
│   │   ├── Reading Material
│   │   └── Practice Exercise
│   ├── Lesson 1.2: [Lesson Title]
│   └── Module Quiz
│
├── Module 2: [Topic Name]
│   └── ...
│
├── Final Assessment
│   ├── Comprehensive Exam
│   └── Project Submission
│
└── Certificate
```

## Course Entity

```typescript
interface Course {
  id: string;
  title: string;
  slug: string;
  description: string;
  shortDescription: string;

  // Categorization
  category: string;
  tags: string[];
  level: 'beginner' | 'intermediate' | 'advanced';

  // Media
  thumbnail: string;
  previewVideo?: string;

  // Structure
  modules: Module[];
  totalDuration: number; // minutes
  totalLessons: number;

  // Requirements
  prerequisites: string[];
  targetAudience: string[];
  learningObjectives: string[];

  // Instructors
  instructors: Instructor[];

  // Settings
  isPublished: boolean;
  isFree: boolean;
  price?: Money;
  enrollmentLimit?: number;

  // Completion
  passingScore: number; // percentage
  certificateEnabled: boolean;

  createdAt: Date;
  updatedAt: Date;
}

interface Module {
  id: string;
  courseId: string;
  title: string;
  description: string;
  position: number;

  // Content
  lessons: Lesson[];

  // Access
  dripDate?: Date;
  prerequisiteModules: string[];

  // Assessment
  quiz?: Quiz;
}

interface Lesson {
  id: string;
  moduleId: string;
  title: string;
  description: string;
  position: number;

  // Content
  contentType: 'video' | 'text' | 'quiz' | 'assignment' | 'live';
  content: LessonContent;
  duration: number; // minutes

  // Resources
  attachments: Attachment[];

  // Settings
  isFree: boolean;
  isPreviewable: boolean;
}
```

## Learning Objectives Template

```markdown
## Learning Objectives

By the end of this course, learners will be able to:

1. **Knowledge (Remember/Understand)**
   - Define [key concept]
   - Explain [fundamental principle]
   - Describe [process/workflow]

2. **Application (Apply)**
   - Apply [technique] to [situation]
   - Implement [solution] for [problem]
   - Use [tool] to accomplish [task]

3. **Analysis (Analyze)**
   - Compare [A] with [B]
   - Identify patterns in [domain]
   - Troubleshoot [common issues]

4. **Synthesis (Create)**
   - Design [artifact]
   - Develop [project/solution]
   - Create [deliverable]
```
