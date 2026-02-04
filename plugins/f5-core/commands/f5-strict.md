---
description: Strict Implementation Protocol (SIP)
argument-hint: <start|approve|mark|validate>
---

# /f5-strict - Strict Implementation Protocol Command

Enforce strict implementation of ONLY specified requirements with full traceability tracking.

## ARGUMENTS
The user's request is: $ARGUMENTS

## PURPOSE

Strict Implementation Protocol (SIP) ensures:
- Only specified requirements are implemented
- Full traceability from requirement to code
- No feature creep or scope expansion
- Coverage tracking and compliance reporting

## WORKFLOW OVERVIEW

```
STRICT IMPLEMENTATION PROTOCOL
════════════════════════════════════════════════════════════════

  1. START SESSION
     └── Load requirements file
     └── Parse requirements list
     └── Generate checklist
             ↓
  2. PREFLIGHT APPROVAL
     └── Review checklist
     └── Confirm: "Implement ONLY these items"
     └── Lock scope
             ↓
  3. IMPLEMENTATION
     └── Mark items: pending → in_progress → done
     └── Add traceability comments in code
     └── Track coverage
             ↓
  4. VALIDATION
     └── Scan code for traceability comments
     └── Match with requirements
     └── Report coverage %
             ↓
  5. END SESSION
     └── Final validation
     └── Generate compliance report
     └── Archive session

════════════════════════════════════════════════════════════════
```

## STEP 1: PARSE SUBCOMMAND

| Pattern | Action |
|---------|--------|
| `start <file>` | **START_SESSION** |
| `check` | **CHECK_STATUS** |
| `approve` | **APPROVE_PREFLIGHT** |
| `checklist` | **SHOW_CHECKLIST** |
| `mark <REQ-ID> <status>` | **MARK_STATUS** |
| `validate` | **VALIDATE_IMPL** |
| `report` | **GENERATE_REPORT** |
| `status` | **SHOW_SESSION** |
| `end` | **END_SESSION** |
| `pause` | **PAUSE_SESSION** |
| `resume` | **RESUME_SESSION** |
| (default) | **SHOW_HELP** |

---

## ACTION: START_SESSION

### `/f5-strict start <requirements.md>`

Start a strict implementation session.

```
WORKFLOW:

1. Load requirements file
2. Parse requirements (REQ-XXX, FR-XXX, NFR-XXX, UC-XXX, US-XXX, SPEC-XXX)
3. Categorize by priority
4. Generate preflight checklist
5. Create session file: .f5/strict-session.json
6. Wait for approval
```

### Output

```markdown
## Strict Implementation Protocol

**Loading:** {{REQUIREMENTS_FILE}}

### Requirements Found

| Priority | Count |
|----------|-------|
| Critical | {{CRITICAL_COUNT}} |
| High | {{HIGH_COUNT}} |
| Medium | {{MEDIUM_COUNT}} |
| Low | {{LOW_COUNT}} |
| **Total** | **{{TOTAL_COUNT}}** |

════════════════════════════════════════════════════════════════
                    PREFLIGHT CHECKLIST
════════════════════════════════════════════════════════════════

You are about to implement ONLY:

### [Critical]
{{#each CRITICAL}}
○ {{this.id}}: {{this.description}}
{{/each}}

### [High]
{{#each HIGH}}
○ {{this.id}}: {{this.description}}
{{/each}}

### [Medium]
{{#each MEDIUM}}
○ {{this.id}}: {{this.description}}
{{/each}}

### [Low]
{{#each LOW}}
○ {{this.id}}: {{this.description}}
{{/each}}

════════════════════════════════════════════════════════════════

### SCOPE LOCK WARNING

Any feature NOT in this list is OUT OF SCOPE.

If you discover new requirements during implementation:
1. Document them separately
2. Do NOT implement them in this session
3. Add to backlog for future planning

### Next Step

Run `/f5-strict approve` to confirm and lock scope.
```

---

## ACTION: CHECK_STATUS

### `/f5-strict check`

Quick check before implementation (used by CLAUDE.md).

```
WORKFLOW:

1. Check if .f5/strict-session.json exists
2. Return session status
3. Indicate if implementation is allowed
```

### Output

```markdown
## Strict Mode Check

{{#if NO_SESSION}}
### Status: NO_SESSION

No active strict implementation session.

To start a session:
```
/f5-strict start <requirements.md>
/f5-strict approve
```
{{/if}}

{{#if PENDING_APPROVAL}}
### Status: PENDING_APPROVAL

Session exists but not yet approved.

Run `/f5-strict approve` to confirm scope.
{{/if}}

{{#if PAUSED}}
### Status: PAUSED

Session is paused.

Run `/f5-strict resume` to continue.
{{/if}}

{{#if ACTIVE}}
### Status: ACTIVE

Session: {{SESSION_ID}}
Progress: {{DONE}}/{{TOTAL}} ({{PERCENTAGE}}%)

Ready to implement.

Quick Check:
```json
{
  "canImplement": true,
  "blockers": []
}
```
{{/if}}
```

---

## ACTION: APPROVE_PREFLIGHT

### `/f5-strict approve`

Approve the preflight checklist and lock scope.

```markdown
## Preflight Approval

### Confirming Scope Lock

You are agreeing to:
1. Implement ONLY the {{TOTAL_COUNT}} requirements listed
2. NOT add any features outside this list
3. Add traceability comments in code
4. Run validation before ending session

### Approved

Session ID: {{SESSION_ID}}
Status: ACTIVE
Scope: LOCKED

### Implementation Guidelines

1. **Mark progress** as you implement:
   ```
   /f5-strict mark REQ-001 in_progress
   /f5-strict mark REQ-001 done src/auth/service.ts:10-50
   ```

2. **Add traceability comments** in code:
   ```typescript
   // REQ-001: User authentication with JWT
   export class AuthService {
     // ...
   }
   ```

3. **Validate** periodically:
   ```
   /f5-strict validate
   ```

4. **End session** when done:
   ```
   /f5-strict end
   ```

### Ready to Implement
```

---

## ACTION: SHOW_CHECKLIST

### `/f5-strict checklist`

Display implementation checklist with progress.

### Options

| Option | Description |
|--------|-------------|
| `--pending` | Show only pending items |
| `--done` | Show only completed items |
| `--in-progress` | Show only in-progress items |
| `--blocked` | Show only blocked items |
| `--critical` | Show only critical priority |
| `--all` | Show all items (default) |

### Output

```markdown
## Implementation Checklist

**Session:** {{SESSION_ID}}
**Status:** {{STATUS}}

### Progress

[{{PROGRESS_BAR}}] {{PERCENTAGE}}%

| Status | Count |
|--------|-------|
| ✅ Done | {{DONE_COUNT}} |
| 🔄 In Progress | {{IN_PROGRESS_COUNT}} |
| ⬜ Pending | {{PENDING_COUNT}} |
| ❌ Blocked | {{BLOCKED_COUNT}} |

### Done ({{DONE_COUNT}})

{{#each DONE}}
✅ {{this.id}}: {{this.description}}
   → {{this.implementedIn}}
{{/each}}

### In Progress ({{IN_PROGRESS_COUNT}})

{{#each IN_PROGRESS}}
🔄 {{this.id}}: {{this.description}}
{{/each}}

### Pending ({{PENDING_COUNT}})

{{#each PENDING}}
⬜ {{this.id}}: {{this.description}}
{{/each}}

### Blocked ({{BLOCKED_COUNT}})

{{#each BLOCKED}}
❌ {{this.id}}: {{this.description}}
   Reason: {{this.blockedReason}}
{{/each}}
```

---

## ACTION: MARK_STATUS

### `/f5-strict mark <REQ-ID> <status> [location]`

Mark requirement implementation status.

### Status Values

| Status | Description | Requires |
|--------|-------------|----------|
| `pending` | Not started | - |
| `in_progress` | Currently working | - |
| `done` | Completed | Location in code |
| `blocked` | Cannot proceed | `--reason` flag |

### Usage Examples

```bash
# Mark as in progress
/f5-strict mark REQ-001 in_progress

# Mark as done with location
/f5-strict mark REQ-001 done src/auth/jwt.service.ts:15-45

# Mark as blocked
/f5-strict mark REQ-020 blocked --reason "Waiting for API credentials"

# Mark back to pending
/f5-strict mark REQ-005 pending
```

### Output

```markdown
## Status Updated

**Requirement:** {{REQ_ID}}
**Previous Status:** {{PREV_STATUS}}
**New Status:** {{NEW_STATUS}}

{{#if LOCATION}}
**Location:** {{LOCATION}}
{{/if}}

{{#if BLOCKED_REASON}}
**Blocked Reason:** {{BLOCKED_REASON}}
{{/if}}

### Progress Update

[{{PROGRESS_BAR}}] {{PERCENTAGE}}%

Done: {{DONE_COUNT}}/{{TOTAL_COUNT}}
```

---

## ACTION: VALIDATE_IMPL

### `/f5-strict validate`

Validate implementation against requirements.

```
WORKFLOW:

1. Scan code directories for traceability comments
   Patterns: // REQ-XXX, // FR-XXX, // NFR-XXX, etc.

2. Match found references with requirements
3. Detect missing traceability
4. Detect potential scope creep
5. Calculate coverage
6. Generate validation report
```

### Output

```markdown
## Validation Report

**Session:** {{SESSION_ID}}
**Scanned:** {{SCANNED_DIRS}}

### Scan Results

| Metric | Value |
|--------|-------|
| Files Scanned | {{FILES_SCANNED}} |
| Traceability Comments Found | {{COMMENTS_FOUND}} |
| Requirements Matched | {{MATCHED}} |

### Coverage

[{{COVERAGE_BAR}}] {{COVERAGE}}%

Implemented & Traced: {{TRACED_COUNT}}/{{TOTAL_COUNT}}

### Implemented & Traced ({{TRACED_COUNT}})

| Requirement | Location |
|-------------|----------|
{{#each TRACED}}
| {{this.id}} | {{this.location}} |
{{/each}}

### Missing Traceability ({{MISSING_COUNT}})

These requirements are marked done but no traceability comment found:

{{#each MISSING}}
- **{{this.id}}**: {{this.description}}
  - Marked location: {{this.markedLocation}}
  - Suggestion: Add `// {{this.id}}: {{this.description}}` in the file
{{/each}}

### Not Implemented ({{NOT_IMPL_COUNT}})

{{#each NOT_IMPLEMENTED}}
- {{this.id}}: {{this.description}}
{{/each}}

### Potential Scope Creep ({{SCOPE_CREEP_COUNT}})

Files with code but no requirement reference:

{{#each SCOPE_CREEP}}
- **{{this.file}}**
  - No requirement reference found
  - Review if this should be in scope
{{/each}}

### Validation Result

{{#if PASS}}
✅ **PASSED**
- All critical requirements: Done
- Coverage: {{COVERAGE}}% (target: 95%)
- No scope creep detected
{{else}}
⚠️ **NEEDS ATTENTION**
{{#each ISSUES}}
- {{this}}
{{/each}}
{{/if}}
```

---

## ACTION: GENERATE_REPORT

### `/f5-strict report`

Generate compliance report.

### Options

| Option | Description |
|--------|-------------|
| `--format <md\|json>` | Output format (default: md) |
| `--output <file>` | Save to file |

### Output (Markdown)

```markdown
# Implementation Compliance Report

## Session Information

| Field | Value |
|-------|-------|
| Session ID | {{SESSION_ID}} |
| Started | {{STARTED_AT}} |
| Requirements File | {{REQUIREMENTS_FILE}} |
| Status | {{STATUS}} |

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total Requirements | {{TOTAL}} |
| Implemented | {{IMPLEMENTED}} |
| Coverage | {{COVERAGE}}% |
| Blocked | {{BLOCKED}} |
| Pending | {{PENDING}} |

## Progress by Priority

| Priority | Total | Done | Coverage |
|----------|-------|------|----------|
| Critical | {{CRITICAL_TOTAL}} | {{CRITICAL_DONE}} | {{CRITICAL_PCT}}% |
| High | {{HIGH_TOTAL}} | {{HIGH_DONE}} | {{HIGH_PCT}}% |
| Medium | {{MEDIUM_TOTAL}} | {{MEDIUM_DONE}} | {{MEDIUM_PCT}}% |
| Low | {{LOW_TOTAL}} | {{LOW_DONE}} | {{LOW_PCT}}% |

## Traceability Matrix

| Requirement | Priority | Status | Location |
|-------------|----------|--------|----------|
{{#each REQUIREMENTS}}
| {{this.id}} | {{this.priority}} | {{this.status}} | {{this.location}} |
{{/each}}

## Issues

### Missing Traceability

{{#each MISSING_TRACE}}
- {{this.id}}: No code reference found
{{/each}}

### Potential Scope Creep

{{#each SCOPE_CREEP}}
- {{this.file}}: No requirement reference
{{/each}}

### Blocked Items

{{#each BLOCKED}}
- {{this.id}}: {{this.reason}}
{{/each}}

## Recommendations

{{#each RECOMMENDATIONS}}
{{@index}}. {{this}}
{{/each}}

## Compliance Status

**Result:** {{COMPLIANCE_STATUS}}

{{#if COMPLIANT}}
All requirements have been implemented with full traceability.
{{else}}
Action required before compliance can be achieved.
{{/if}}

---

*Generated: {{TIMESTAMP}}*
*F5 Framework - Strict Implementation Protocol*
```

---

## ACTION: SHOW_SESSION

### `/f5-strict status`

Show current session status.

```markdown
## Strict Mode Status

════════════════════════════════════════════════════════════════

**Session ID:** {{SESSION_ID}}
**Status:** {{STATUS}}
**Preflight:** {{PREFLIGHT_STATUS}}
**Started:** {{STARTED_AT}}
**Source:** {{REQUIREMENTS_FILE}}

### Progress

| Status | Count |
|--------|-------|
| Done | {{DONE}} |
| In Progress | {{IN_PROGRESS}} |
| Pending | {{PENDING}} |
| Blocked | {{BLOCKED}} |
| **Coverage** | **{{COVERAGE}}%** |

### Quick Check

```json
{
  "canImplement": {{CAN_IMPLEMENT}},
  "blockers": [{{BLOCKERS}}]
}
```

{{#if CAN_IMPLEMENT}}
✅ Ready to implement
{{else}}
❌ Cannot implement: {{BLOCKERS}}
{{/if}}

════════════════════════════════════════════════════════════════
```

---

## ACTION: END_SESSION

### `/f5-strict end`

End the strict implementation session.

```
WORKFLOW:

1. Run final validation
2. Generate compliance report
3. Save report to .f5/implementation-report-{session-id}.md
4. Archive session
5. Clear active session
```

### Output

```markdown
## Ending Strict Implementation Session

### Running Final Validation...

{{VALIDATION_RESULT}}

### Session Summary

════════════════════════════════════════════════════════════════

**Session:** {{SESSION_ID}}
**Duration:** {{DURATION}}

### Final Results

| Metric | Value |
|--------|-------|
| Implemented | {{IMPLEMENTED}}/{{TOTAL}} |
| Coverage | {{COVERAGE}}% |
| Blocked | {{BLOCKED}} |

### Compliance Status

{{#if COMPLIANT}}
✅ **COMPLIANT**
- All critical requirements: Done
- No scope creep detected
- Traceability: {{TRACEABILITY}}%
{{else}}
⚠️ **NEEDS ATTENTION**
{{#each ISSUES}}
- {{this}}
{{/each}}
{{/if}}

### Report Saved

📄 .f5/implementation-report-{{SESSION_ID}}.md

════════════════════════════════════════════════════════════════

### Session Ended

{{#if COMPLIANT}}
✅ Session ended successfully.

### Next Steps
1. Review compliance report
2. Commit changes with requirement references
3. Start new session for remaining items (if any)
{{else}}
⚠️ Session ended with issues.

### Recommended Actions
{{#each RECOMMENDATIONS}}
- {{this}}
{{/each}}
{{/if}}
```

---

## ACTION: PAUSE_SESSION

### `/f5-strict pause`

Pause the current session.

```markdown
## Session Paused

**Session:** {{SESSION_ID}}
**Status:** PAUSED

Progress saved:
- Done: {{DONE}}
- In Progress: {{IN_PROGRESS}}
- Pending: {{PENDING}}

To resume: `/f5-strict resume`
```

---

## ACTION: RESUME_SESSION

### `/f5-strict resume`

Resume a paused session.

```markdown
## Session Resumed

**Session:** {{SESSION_ID}}
**Status:** ACTIVE

### Current Progress

[{{PROGRESS_BAR}}] {{PERCENTAGE}}%

Done: {{DONE}}/{{TOTAL}}

### Pending Items

{{#each PENDING}}
- {{this.id}}: {{this.description}}
{{/each}}

Ready to continue implementation.
```

---

## TRACEABILITY COMMENT FORMAT

### Supported Formats

```typescript
// Single line
// REQ-001: User authentication with JWT
export class JwtService { }

// Multiple requirements
// REQ-002: Role-based access control
// REQ-003: Permission management
export class RbacGuard { }

// Block comment
/**
 * REQ-004: Session management
 * REQ-005: Token refresh
 */
export class SessionService { }

// Inline
const handler = () => { /* REQ-006: Error handling */ }
```

### Supported Prefixes

| Prefix | Type |
|--------|------|
| `REQ-XXX` | General requirement |
| `FR-XXX` | Functional requirement |
| `NFR-XXX` | Non-functional requirement |
| `UC-XXX` | Use case |
| `US-XXX` | User story |
| `SPEC-XXX` | Specification |

---

## SESSION FILE FORMAT

```json
// .f5/strict-session.json
{
  "id": "strict-2024-01-15-abc123",
  "status": "active",
  "preflightApproved": true,
  "startedAt": "2024-01-15T09:00:00Z",
  "requirementsPath": "docs/requirements.md",
  "config": {
    "validationThreshold": 95,
    "allowExtraFeatures": false,
    "requirePreflightApproval": true
  },
  "quickCheck": {
    "canImplement": true,
    "blockers": []
  },
  "requirements": [
    {
      "id": "REQ-001",
      "description": "User authentication with JWT",
      "priority": "Critical",
      "status": "done",
      "implementedIn": ["src/auth/jwt.service.ts:15-45"],
      "markedAt": "2024-01-15T10:30:00Z"
    },
    {
      "id": "REQ-002",
      "description": "Role-based access control",
      "priority": "Critical",
      "status": "in_progress",
      "implementedIn": [],
      "markedAt": null
    }
  ],
  "validation": {
    "lastRun": "2024-01-15T14:00:00Z",
    "coverage": 48,
    "issues": []
  }
}
```

---

## EXAMPLES

```bash
# Start strict session
/f5-strict start docs/requirements.md

# Approve preflight
/f5-strict approve

# Quick check before implementing
/f5-strict check

# View checklist
/f5-strict checklist

# View only pending items
/f5-strict checklist --pending

# View only critical items
/f5-strict checklist --critical

# Mark requirement as in progress
/f5-strict mark REQ-001 in_progress

# Mark requirement as done
/f5-strict mark REQ-001 done src/auth/jwt.service.ts:15-45

# Mark as blocked
/f5-strict mark REQ-020 blocked --reason "Waiting for API keys"

# Validate implementation
/f5-strict validate

# Check session status
/f5-strict status

# Generate report
/f5-strict report

# Save report to file
/f5-strict report --output compliance-report.md

# Pause session
/f5-strict pause

# Resume session
/f5-strict resume

# End session
/f5-strict end
```

---

## INTEGRATION

### Pre-Implementation Check (Required)

Before writing ANY code, Claude Code MUST:

```bash
# Step 1: Check strict status
/f5-strict check

# If NO session exists:
/f5-strict start <requirements.md>
/f5-strict approve

# If session exists but NOT approved:
/f5-strict approve
```

### Block Conditions

Do NOT implement if:
- No active SIP session
- Session not approved
- Session paused

### With BA Workflow

```
/f5-ba document --srs
    ↓
/f5-strict start ba-workflow/phase-4-documentation/documents/srs.md
    ↓
/f5-strict approve
    ↓
Implementation with traceability
    ↓
/f5-strict validate
    ↓
/f5-strict end
```

---

**Remember:** Strict mode ensures you implement ONLY what's specified. No feature creep!
