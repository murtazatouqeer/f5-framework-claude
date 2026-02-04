# SCORM & xAPI Patterns

## Overview
Implementation patterns for e-learning standards compliance.

## SCORM (Sharable Content Object Reference Model)

### SCORM 1.2 API
```javascript
// Required API methods
const SCORM12API = {
  LMSInitialize: () => 'true',
  LMSGetValue: (element) => dataModel[element],
  LMSSetValue: (element, value) => { dataModel[element] = value; return 'true'; },
  LMSCommit: () => 'true',
  LMSFinish: () => 'true',
  LMSGetLastError: () => '0',
  LMSGetErrorString: (errorCode) => errorStrings[errorCode],
  LMSGetDiagnostic: (errorCode) => diagnostics[errorCode]
};

// Common data model elements
const dataModel = {
  'cmi.core.student_id': '',
  'cmi.core.student_name': '',
  'cmi.core.lesson_location': '',
  'cmi.core.lesson_status': 'not attempted', // passed, completed, failed, incomplete, browsed
  'cmi.core.score.raw': '',
  'cmi.core.score.max': '',
  'cmi.core.score.min': '',
  'cmi.core.session_time': '',
  'cmi.suspend_data': ''
};
```

### SCORM 2004 Enhancements
```javascript
// Additional data model elements
const scorm2004Data = {
  'cmi.completion_status': 'unknown', // completed, incomplete, not attempted, unknown
  'cmi.success_status': 'unknown', // passed, failed, unknown
  'cmi.progress_measure': 0, // 0 to 1
  'cmi.objectives._count': 0,
  'cmi.interactions._count': 0
};
```

## xAPI (Experience API / Tin Can)

### Statement Structure
```typescript
interface xAPIStatement {
  actor: {
    mbox: string; // mailto:learner@example.com
    name: string;
    objectType: 'Agent';
  };
  verb: {
    id: string; // http://adlnet.gov/expapi/verbs/completed
    display: { 'en-US': string };
  };
  object: {
    id: string; // URL of the activity
    objectType: 'Activity';
    definition: {
      name: { 'en-US': string };
      description: { 'en-US': string };
      type: string;
    };
  };
  result?: {
    score?: { scaled: number; raw: number; max: number; min: number };
    success?: boolean;
    completion?: boolean;
    duration?: string; // ISO 8601
  };
  context?: {
    registration: string; // UUID
    contextActivities?: {
      parent: Activity[];
      grouping: Activity[];
    };
  };
  timestamp: string; // ISO 8601
}
```

### Common Verbs
```typescript
const xAPIVerbs = {
  initialized: 'http://adlnet.gov/expapi/verbs/initialized',
  completed: 'http://adlnet.gov/expapi/verbs/completed',
  passed: 'http://adlnet.gov/expapi/verbs/passed',
  failed: 'http://adlnet.gov/expapi/verbs/failed',
  answered: 'http://adlnet.gov/expapi/verbs/answered',
  experienced: 'http://adlnet.gov/expapi/verbs/experienced',
  progressed: 'http://adlnet.gov/expapi/verbs/progressed'
};
```

### Sending Statements
```typescript
const sendStatement = async (statement: xAPIStatement) => {
  const response = await fetch(`${LRS_ENDPOINT}/statements`, {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${btoa(`${LRS_KEY}:${LRS_SECRET}`)}`,
      'Content-Type': 'application/json',
      'X-Experience-API-Version': '1.0.3'
    },
    body: JSON.stringify(statement)
  });
  return response.json();
};
```

## Best Practices
- Buffer xAPI statements and send in batches
- Implement retry logic for LRS failures
- Store statements locally for offline support
- Use consistent actor identifiers
- Include context for better analytics

## Anti-Patterns to Avoid
- Sending statements synchronously blocking UI
- Not validating statement structure
- Missing error handling for SCORM API calls
- Storing sensitive data in suspend_data
