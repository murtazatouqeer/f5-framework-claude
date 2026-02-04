# Assessment Specification Template

## Assessment Overview

| Field | Value |
|-------|-------|
| Assessment Name | [Name] |
| Type | Quiz / Exam / Assignment |
| Duration | [X] minutes |
| Total Points | [X] |
| Passing Score | [X]% |
| Attempts Allowed | [X] |

## Question Types

### Multiple Choice (Single Answer)
```json
{
  "type": "multiple_choice_single",
  "question": "Question text here?",
  "options": [
    {"id": "a", "text": "Option A"},
    {"id": "b", "text": "Option B"},
    {"id": "c", "text": "Option C"},
    {"id": "d", "text": "Option D"}
  ],
  "correctAnswer": "b",
  "points": 1,
  "explanation": "Explanation for the correct answer"
}
```

### Multiple Choice (Multiple Answers)
```json
{
  "type": "multiple_choice_multiple",
  "question": "Select all that apply:",
  "options": [
    {"id": "a", "text": "Option A"},
    {"id": "b", "text": "Option B"},
    {"id": "c", "text": "Option C"}
  ],
  "correctAnswers": ["a", "c"],
  "points": 2,
  "partialCredit": true
}
```

### True/False
```json
{
  "type": "true_false",
  "question": "Statement to evaluate",
  "correctAnswer": true,
  "points": 1
}
```

### Fill in the Blank
```json
{
  "type": "fill_blank",
  "question": "The capital of France is ___.",
  "correctAnswers": ["Paris", "paris"],
  "caseSensitive": false,
  "points": 1
}
```

### Short Answer
```json
{
  "type": "short_answer",
  "question": "Explain the concept of...",
  "maxLength": 500,
  "rubric": [
    {"criteria": "Accuracy", "points": 3},
    {"criteria": "Clarity", "points": 2}
  ],
  "points": 5
}
```

## Assessment Settings

```typescript
interface AssessmentSettings {
  // Timing
  timeLimit: number | null; // minutes, null = unlimited
  showTimer: boolean;

  // Questions
  randomizeQuestions: boolean;
  randomizeOptions: boolean;
  questionsPerPage: number;

  // Attempts
  maxAttempts: number;
  attemptsInterval: number; // hours between attempts

  // Feedback
  showCorrectAnswers: 'immediately' | 'after_submission' | 'after_due_date' | 'never';
  showScore: 'immediately' | 'after_submission' | 'never';
  showExplanations: boolean;

  // Security
  requirePassword: boolean;
  password?: string;
  lockdownBrowser: boolean;
  preventCopyPaste: boolean;

  // Scheduling
  availableFrom: Date;
  availableUntil: Date;
  lateSubmission: boolean;
  latePenalty?: number; // percentage per day
}
```

## Grading Rubric Template

| Criteria | Excellent (4) | Good (3) | Satisfactory (2) | Needs Improvement (1) |
|----------|--------------|----------|------------------|----------------------|
| [Criteria 1] | Description | Description | Description | Description |
| [Criteria 2] | Description | Description | Description | Description |
| [Criteria 3] | Description | Description | Description | Description |
