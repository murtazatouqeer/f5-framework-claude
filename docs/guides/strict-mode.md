# Strict Implementation Protocol (SIP) Guide

Complete guide for using F5 Strict Mode to ensure scope-locked, traceable implementations.

> **Version:** 1.3.6 | **Updated:** January 2025

---

## Overview

The Strict Implementation Protocol (SIP) enforces disciplined development by:
- Implementing ONLY specified requirements
- Maintaining full code traceability
- Preventing feature creep and scope expansion
- Generating compliance reports

**These rules are MANDATORY when `/f5-strict start` has been invoked.**

---

## Quick Start

```bash
# 1. Start session with requirements
/f5-strict start docs/requirements.md

# 2. Review and approve preflight
/f5-strict approve

# 3. Implement with traceability
# Add comments: // REQ-001: Description

# 4. Mark progress
/f5-strict mark REQ-001 done src/auth/service.ts:10-50

# 5. Validate and end
/f5-strict validate
/f5-strict end
```

---

## Core Concepts

### Scope Locking

Once approved, the scope is LOCKED. This means:
- Only listed requirements can be implemented
- New discoveries go to backlog, not current sprint
- No "while I'm here" improvements
- No undocumented features

### Traceability

Every feature must trace back to a requirement:

```typescript
// REQ-001: User authentication with JWT
export class JwtService {
  // Implementation traces to REQ-001
}

// REQ-002: Role-based access control
// REQ-003: Permission management
export class RbacGuard {
  // Implementation traces to both REQ-002 and REQ-003
}
```

### Compliance

Session ends with compliance check:
- All critical requirements done
- Traceability comments present
- No scope creep detected

---

## Implementation Rules

### Pre-Implementation

| Rule | Description |
|------|-------------|
| **RULE-001** | Read requirements first - run `/f5-strict checklist` |
| **RULE-002** | Single requirement focus - implement ONE at a time |
| **RULE-003** | Pre-flight approval required before any code |

### During Implementation

| Rule | Description |
|------|-------------|
| **RULE-004** | Traceability comments mandatory |
| **RULE-005** | No extra features beyond requirements |
| **RULE-006** | Mark progress immediately |
| **RULE-007** | Stop on ambiguity - ask for clarification |
| **RULE-008** | Scope creep prevention - verify before writing |

### Post-Implementation

| Rule | Description |
|------|-------------|
| **RULE-009** | Validation before completion |
| **RULE-010** | End session properly with report |

---

## Workflow Phases

### Phase 1: Start Session

```bash
/f5-strict start docs/requirements.md
```

**What happens:**
1. Requirements file is parsed
2. Requirements extracted and categorized
3. Preflight checklist generated
4. Session file created at `.f5/strict-session.json`

**Output:**

```
═══════════════════════════════════════════════════════════
                    PREFLIGHT CHECKLIST
═══════════════════════════════════════════════════════════

You are about to implement ONLY:

[Critical]
○ REQ-001: User authentication with JWT
○ REQ-002: Role-based access control

[High]
○ REQ-003: Password reset functionality
○ REQ-004: Session management

[Medium]
○ REQ-005: Remember me feature

═══════════════════════════════════════════════════════════

SCOPE LOCK WARNING:
Any feature NOT in this list is OUT OF SCOPE.

Next: /f5-strict approve
```

### Phase 2: Preflight Approval

```bash
/f5-strict approve
```

**What you're agreeing to:**
1. Implement ONLY listed requirements
2. Add traceability comments in code
3. Run validation before ending
4. NOT add features outside the list

### Phase 3: Implementation

1. **Start working on a requirement:**
   ```bash
   /f5-strict mark REQ-001 in_progress
   ```

2. **Add traceability comment in code:**
   ```typescript
   // REQ-001: User authentication with JWT
   export async function authenticate(credentials: Credentials): Promise<Token> {
     // Implementation
   }
   ```

3. **Complete the requirement:**
   ```bash
   /f5-strict mark REQ-001 done src/auth/jwt.service.ts:15-45
   ```

4. **If blocked:**
   ```bash
   /f5-strict mark REQ-005 blocked --reason "Waiting for API credentials"
   ```

### Phase 4: Validation

```bash
/f5-strict validate
```

**Validation checks:**
1. Scan code for traceability comments
2. Match comments with requirements
3. Detect missing traceability
4. Detect potential scope creep
5. Calculate coverage percentage

### Phase 5: End Session

```bash
/f5-strict end
```

**What happens:**
1. Final validation runs
2. Compliance report generated
3. Session archived
4. Report saved to `.f5/implementation-report-{session-id}.md`

---

## Traceability Comment Formats

### Supported Prefixes

| Prefix | Type | Example |
|--------|------|---------|
| `REQ-XXX` | General requirement | REQ-001 |
| `FR-XXX` | Functional requirement | FR-001 |
| `NFR-XXX` | Non-functional requirement | NFR-001 |
| `UC-XXX` | Use case | UC-001 |
| `US-XXX` | User story | US-001 |
| `SPEC-XXX` | Specification | SPEC-001 |

### Comment Formats

**Single Line:**
```typescript
// REQ-001: User authentication with JWT
export class JwtService { }
```

**Multiple Requirements:**
```typescript
// REQ-002: Role-based access control
// REQ-003: Permission management
export class RbacGuard { }
```

**Block Comment:**
```typescript
/**
 * REQ-004: Session management
 * REQ-005: Token refresh
 */
export class SessionService { }
```

**Inline Comment:**
```typescript
const handler = () => { /* REQ-006: Error handling */ }
```

---

## Commands Reference

### Session Management

| Command | Description |
|---------|-------------|
| `/f5-strict start <file>` | Start new session |
| `/f5-strict approve` | Approve preflight and lock scope |
| `/f5-strict check` | Quick status check |
| `/f5-strict status` | Detailed session status |
| `/f5-strict pause` | Pause current session |
| `/f5-strict resume` | Resume paused session |
| `/f5-strict end` | End session with report |
| `/f5-strict clear` | Force clear session (emergency) |

### Progress Tracking

| Command | Description |
|---------|-------------|
| `/f5-strict checklist` | View all items |
| `/f5-strict checklist --pending` | View pending items |
| `/f5-strict checklist --done` | View completed items |
| `/f5-strict checklist --critical` | View critical items only |
| `/f5-strict checklist --reload` | Reload from requirements file |
| `/f5-strict mark <ID> in_progress` | Start working on item |
| `/f5-strict mark <ID> done <file:lines>` | Complete item |
| `/f5-strict mark <ID> blocked --reason "..."` | Mark as blocked |
| `/f5-strict mark <ID> pending` | Reset to pending |

### Validation & Reporting

| Command | Description |
|---------|-------------|
| `/f5-strict validate` | Run validation scan |
| `/f5-strict report` | Generate compliance report |
| `/f5-strict report --output file.md` | Save report to file |

---

## Configuration

### Default Configuration

```json
{
  "enabled": true,
  "requirePreflightApproval": true,
  "requireTraceabilityComments": true,
  "blockOnAmbiguity": true,
  "allowExtraFeatures": false,
  "validationThreshold": 95
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `requirePreflightApproval` | `true` | Require user approval before implementation |
| `requireTraceabilityComments` | `true` | Require REQ-XXX comments in code |
| `blockOnAmbiguity` | `true` | Block implementation on ambiguous requirements |
| `allowExtraFeatures` | `false` | Allow features not in requirements |
| `validationThreshold` | `95` | Minimum coverage percentage to pass |

---

## Integration

### Pre-Implementation Check (MANDATORY)

Before writing ANY code, you MUST:

```bash
# Step 1: Check strict status
/f5-strict check

# If NO session:
/f5-strict start requirements.md
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
Implementation
    ↓
/f5-strict validate
    ↓
/f5-strict end
```

### With Requirement Quality

```
/f5-req analyze requirements.md
    ↓
(Ensure Grade A or B)
    ↓
/f5-strict start requirements.md
    ↓
Implementation
```

### With Jira

```
/f5-jira-convert requirements.xlsx
    ↓
/f5-strict start .f5/output/jira-import.csv
    ↓
Implementation
    ↓
/f5-jira-sync --push (update status)
```

### Quality Gates Integration

| Gate | SIP Checkpoint |
|------|----------------|
| D2 (SRS Approved) | Start strict session |
| G2 (Ready to Implement) | Pre-flight approved |
| G3 (Tests Pass) | Validation coverage met |
| G4 (Ready to Deploy) | Session ended successfully |

---

## Best Practices

### Do's

1. **Always start with approved requirements**
   - Don't implement from verbal instructions
   - Use documented, reviewed requirements

2. **Mark progress immediately**
   - Update status as soon as you start/finish
   - Don't batch status updates

3. **Add traceability comments first**
   - Write the comment before the code
   - Makes validation easier

4. **Validate frequently**
   - Run validation after each major milestone
   - Catch issues early

5. **Document blockers clearly**
   - Include specific reason
   - Note what's needed to unblock

6. **Atomic Commits**
   - Commit after each REQ-XXX completion

### Don'ts

1. **Don't implement without approval**
   - The preflight exists for a reason
   - Review the list carefully

2. **Don't add "quick fixes"**
   - If it's not in the list, it's out of scope
   - Document it for the next session

3. **Don't skip validation**
   - Even if you're confident
   - Automated checks catch what humans miss

4. **Don't ignore scope creep warnings**
   - Review flagged files
   - Justify or remove

5. **Don't end without compliance**
   - Address issues first
   - 95% coverage is the minimum

6. **Never bypass strict mode**
   - No workarounds to "just get it done"

---

## Troubleshooting

### "Session not found"

```bash
# Check if session exists
/f5-strict check

# Start new session
/f5-strict start requirements.md
```

### "Implementation blocked"

Check blockers:

```bash
/f5-strict status
```

Common blockers:
- Session not approved → `/f5-strict approve`
- Session paused → `/f5-strict resume`
- No session → `/f5-strict start <file>`

### "Low coverage percentage"

Review what's missing:

```bash
/f5-strict validate
/f5-strict checklist --pending
```

### "Scope creep detected"

For each flagged file:
1. If it relates to a requirement → add traceability comment
2. If it doesn't → consider removing or documenting for next sprint

### "Missing traceability"

For requirements marked done but without comments:

```bash
# Find the requirement
/f5-strict checklist --done

# Add the traceability comment to the code
// REQ-XXX: Description

# Re-validate
/f5-strict validate
```

### Session Corrupted

```bash
# Clear and restart
/f5-strict clear
/f5-strict start requirements.md
```

### Need to Add Requirement Mid-Session

```bash
# Update requirements file
# Re-load checklist
/f5-strict checklist --reload
```

---

## Metrics

### Session Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Coverage | >95% | Requirements implemented |
| Traceability | 100% | All code traced |
| Scope Creep | 0 | Unauthorized features |
| Block Rate | <10% | Blocked requirements |

### Quality Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| First-pass Validation | >90% | Pass without issues |
| Comment Accuracy | 100% | Comments match code |
| Report Completeness | 100% | All fields populated |

---

## Compliance Report Format

```markdown
# Implementation Compliance Report

## Session Information

| Field | Value |
|-------|-------|
| Session ID | strict-2024-01-15-abc123 |
| Started | 2024-01-15T09:00:00Z |
| Requirements File | docs/requirements.md |
| Status | Completed |

## Coverage Summary

| Metric | Value |
|--------|-------|
| Total Requirements | 20 |
| Implemented | 18 |
| Coverage | 90% |
| Blocked | 2 |

## Traceability Matrix

| Requirement | Priority | Status | Location |
|-------------|----------|--------|----------|
| REQ-001 | Critical | Done | src/auth/jwt.service.ts:15-45 |
| REQ-002 | Critical | Done | src/auth/rbac.guard.ts:10-80 |
| REQ-003 | High | Blocked | - |

## Compliance Status

**Result:** COMPLIANT

All critical requirements implemented with full traceability.
```

---

## Session File Format

The session is stored in `.f5/strict-session.json`:

```json
{
  "id": "strict-2024-01-15-abc123",
  "status": "active",
  "preflightApproved": true,
  "startedAt": "2024-01-15T09:00:00Z",
  "requirementsPath": "docs/requirements.md",
  "config": {
    "validationThreshold": 95,
    "allowExtraFeatures": false
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
    }
  ],
  "validation": {
    "lastRun": "2024-01-15T14:00:00Z",
    "coverage": 85,
    "issues": []
  }
}
```

---

*F5 Framework - Strict Implementation Protocol Guide v1.3.6*
