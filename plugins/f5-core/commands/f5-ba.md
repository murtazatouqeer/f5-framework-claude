---
description: Business analysis workflow
argument-hint: <start|continue|complete> [phase]
---

# /f5-ba - Business Analysis Workflow Command

Manage Business Analysis workflow following BABOK standards, from Enterprise Analysis to Validation & Sign-off.

## ARGUMENTS
The user's request is: $ARGUMENTS

## ⚠️ CRITICAL OUTPUT RULES

**BA Workflow files MUST be in `.f5/ba-workflow/` NOT in project root or `docs/`.**

**BẮT BUỘC tuân theo cấu trúc sau:**

| Document Type | Output Path |
|--------------|-------------|
| BA Workflow | `.f5/ba-workflow/` |
| Phase 1 docs | `.f5/ba-workflow/phase-1-enterprise-analysis/` |
| Phase 2 docs | `.f5/ba-workflow/phase-2-planning/` |
| Phase 3 docs | `.f5/ba-workflow/phase-3-elicitation/` |
| Phase 4 docs | `.f5/ba-workflow/phase-4-documentation/` |
| Phase 5 docs | `.f5/ba-workflow/phase-5-validation/` |
| Status file | `.f5/ba-workflow/status.json` |

**✅ CORRECT paths:**
```
.f5/ba-workflow/status.json ✅
.f5/ba-workflow/phase-1-enterprise-analysis/stakeholder-map.md ✅
.f5/ba-workflow/phase-4-documentation/documents/srs.md ✅
```

**❌ WRONG paths:**
```
ba-workflow/status.json ❌  (missing .f5/ prefix!)
docs/stakeholder-map.md ❌
phase-1/stakeholder-map.md ❌
```

## BA WORKFLOW OVERVIEW

```
BA WORKFLOW PHASES
════════════════════════════════════════════════════════════════

  Phase 1: Enterprise Analysis
  ├── Stakeholder Identification
  ├── Current State Documentation
  └── Problem Statement
          ↓ Gate 1

  Phase 2: Requirements Planning
  ├── Scope Definition
  ├── Requirements Management Plan
  └── Communication Plan
          ↓ Gate 2

  Phase 3: Requirements Elicitation
  ├── Interviews
  ├── Workshops
  ├── Document Analysis
  └── Excel Import (from customer)
          ↓ Gate 3

  Phase 4: Analysis & Documentation
  ├── BRD (Business Requirements Document)
  ├── SRS (Software Requirements Specification)
  └── FRS (Functional Requirements Specification)
          ↓ Gate 4

  Phase 5: Validation & Sign-off
  ├── Review Sessions
  ├── Approval Workflow
  └── Baseline
          ↓ Complete

════════════════════════════════════════════════════════════════
```

## STEP 1: PARSE SUBCOMMAND

| Pattern | Action |
|---------|--------|
| `init` | **INIT_WORKFLOW** |
| `status` | **SHOW_STATUS** |
| `stakeholders` | **MANAGE_STAKEHOLDERS** |
| `elicit` | **ELICITATION** |
| `gate` | **CHECK_GATE** |
| `document` | **GENERATE_DOCUMENT** |
| `iterate` | **ITERATE_PHASE** |
| (default) | **SHOW_HELP** |

---

## ACTION: INIT_WORKFLOW

### `/f5-ba init`

Initialize BA workflow for the project.

```
WORKFLOW:

1. Create directory structure:
   .f5/ba-workflow/
   ├── phase-1-enterprise-analysis/
   │   ├── stakeholder-map.md
   │   ├── current-state.md
   │   └── problem-statement.md
   ├── phase-2-planning/
   │   ├── scope.md
   │   ├── requirements-management-plan.md
   │   └── communication-plan.md
   ├── phase-3-elicitation/
   │   ├── interview-notes/
   │   ├── workshop-notes/
   │   └── imported-documents/
   ├── phase-4-documentation/
   │   ├── documents/
   │   │   ├── brd.md
   │   │   ├── srs.md
   │   │   └── frs.md
   │   └── signoff/
   ├── phase-5-validation/
   │   ├── review-notes/
   │   └── signoff/
   ├── templates/
   ├── gates/
   │   ├── gate-1-checklist.md
   │   ├── gate-2-checklist.md
   │   ├── gate-3-checklist.md
   │   ├── gate-4-checklist.md
   │   └── gate-5-checklist.md
   └── status.json

2. Create status.json to track progress
3. Copy templates from F5 Framework
4. Display next steps
```

### Output

```markdown
## BA Workflow Initialized

**Project:** {{PROJECT_NAME}}
**Created:** {{TIMESTAMP}}

### Directory Structure Created

.f5/ba-workflow/
├── phase-1-enterprise-analysis/
├── phase-2-planning/
├── phase-3-elicitation/
├── phase-4-documentation/
├── phase-5-validation/
├── templates/
├── gates/
└── status.json

### Status File

Created: .f5/ba-workflow/status.json

### Next Steps

1. Start with stakeholder identification:
   `/f5-ba stakeholders --add`

2. Document problem statement:
   `/f5-ba document --problem`

3. Check Phase 1 gate:
   `/f5-ba gate --phase 1`

4. Check overall status:
   `/f5-ba status`
```

---

## ACTION: SHOW_STATUS

### `/f5-ba status`

Display BA workflow status.

```
WORKFLOW:

1. Read .f5/ba-workflow/status.json
2. Calculate phase progress
3. Check gate statuses
4. Show document pipeline integration
5. Display next actions
```

### Output

```markdown
## BA Workflow Status

**Project:** {{PROJECT_NAME}}
**Started:** {{START_DATE}}
**Current Phase:** {{CURRENT_PHASE}}

### Phase Progress

| Phase | Status | Progress |
|-------|--------|----------|
| 1. Enterprise Analysis | {{STATUS_1}} | {{PROGRESS_1}} |
| 2. Requirements Planning | {{STATUS_2}} | {{PROGRESS_2}} |
| 3. Requirements Elicitation | {{STATUS_3}} | {{PROGRESS_3}} |
| 4. Analysis & Documentation | {{STATUS_4}} | {{PROGRESS_4}} |
| 5. Validation & Sign-off | {{STATUS_5}} | {{PROGRESS_5}} |

### Gate Status

| Gate | Status | Passed Date |
|------|--------|-------------|
| Gate 1 | {{GATE_1_STATUS}} | {{GATE_1_DATE}} |
| Gate 2 | {{GATE_2_STATUS}} | {{GATE_2_DATE}} |
| Gate 3 | {{GATE_3_STATUS}} | {{GATE_3_DATE}} |
| Gate 4 | {{GATE_4_STATUS}} | {{GATE_4_DATE}} |
| Gate 5 | {{GATE_5_STATUS}} | {{GATE_5_DATE}} |

### Document Pipeline Integration

| Metric | Value |
|--------|-------|
| Latest Version | {{DOC_VERSION}} |
| Total Versions | {{VERSION_COUNT}} |
| Requirements | {{REQ_COUNT}} |

### Stakeholders

| Category | Count |
|----------|-------|
| Executive | {{EXEC_COUNT}} |
| Business User | {{BIZ_COUNT}} |
| Technical | {{TECH_COUNT}} |
| External | {{EXT_COUNT}} |

### Next Actions

{{#each NEXT_ACTIONS}}
- {{this}}
{{/each}}
```

### Status Indicators

| Symbol | Status |
|--------|--------|
| ✅ | COMPLETED |
| 🔄 | IN PROGRESS |
| ⬜ | NOT STARTED |
| ⏸️ | ON HOLD |
| ❌ | BLOCKED |

---

## ACTION: MANAGE_STAKEHOLDERS

### `/f5-ba stakeholders`

Manage stakeholder identification and mapping.

### Options

| Option | Description |
|--------|-------------|
| `--add` | Add new stakeholder (interactive) |
| `--list` | List all stakeholders |
| `--matrix` | Display stakeholder matrix |
| `--edit <name>` | Edit existing stakeholder |
| `--remove <name>` | Remove stakeholder |

### Add Stakeholder (--add)

```markdown
## Add Stakeholder

Please provide the following information:

1. **Name:** [Enter stakeholder name]
2. **Role:** [Enter job title/role]
3. **Department:** [Enter department]
4. **Email:** [Enter email]
5. **Influence Level:** [High/Medium/Low]
6. **Interest Level:** [High/Medium/Low]
7. **Category:** [Executive/Business User/Technical/External]
8. **Preferred Communication:** [Email/Meeting/Slack/etc.]
9. **Notes:** [Any additional notes]
```

### List Stakeholders (--list)

```markdown
## Stakeholder List

| Name | Role | Department | Influence | Interest | Category |
|------|------|------------|-----------|----------|----------|
| {{NAME}} | {{ROLE}} | {{DEPT}} | {{INFLUENCE}} | {{INTEREST}} | {{CATEGORY}} |
...

Total: {{COUNT}} stakeholders
```

### Stakeholder Matrix (--matrix)

```markdown
## Stakeholder Matrix

                      INTEREST
                Low         Medium        High
            ┌───────────┬───────────┬───────────┐
    High    │  KEEP     │  KEEP     │  MANAGE   │
            │ SATISFIED │ SATISFIED │  CLOSELY  │
            │           │           │           │
INFLUENCE   ├───────────┼───────────┼───────────┤
    Medium  │  MONITOR  │  KEEP     │   KEEP    │
            │           │ SATISFIED │ INFORMED  │
            │           │           │           │
            ├───────────┼───────────┼───────────┤
    Low     │  MONITOR  │  MONITOR  │   KEEP    │
            │           │           │ INFORMED  │
            │           │           │           │
            └───────────┴───────────┴───────────┘

### MANAGE CLOSELY (High Influence, High Interest)
{{#each MANAGE_CLOSELY}}
- {{this.name}} ({{this.role}})
{{/each}}

### KEEP SATISFIED (High Influence, Low-Medium Interest)
{{#each KEEP_SATISFIED}}
- {{this.name}} ({{this.role}})
{{/each}}

### KEEP INFORMED (Low-Medium Influence, High Interest)
{{#each KEEP_INFORMED}}
- {{this.name}} ({{this.role}})
{{/each}}

### MONITOR (Low Influence, Low-Medium Interest)
{{#each MONITOR}}
- {{this.name}} ({{this.role}})
{{/each}}
```

---

## ACTION: ELICITATION

### `/f5-ba elicit`

Manage elicitation activities.

### Options

| Option | Description |
|--------|-------------|
| `--interview <name>` | Prepare interview guide for stakeholder |
| `--workshop <type>` | Prepare workshop materials |
| `--import <file>` | Import Excel/CSV feedback |
| `--list` | List elicitation activities |
| `--summary` | Show elicitation summary |

### Interview (--interview)

```markdown
## Interview Preparation: {{STAKEHOLDER_NAME}}

**Role:** {{ROLE}}
**Category:** {{CATEGORY}}
**Scheduled:** {{DATE_TIME}}

### Pre-Interview Checklist

- [ ] Confirm meeting time with stakeholder
- [ ] Review stakeholder's role and responsibilities
- [ ] Prepare list of questions
- [ ] Prepare note-taking template
- [ ] Test recording equipment (if applicable)
- [ ] Send agenda to stakeholder

### Suggested Questions

Based on stakeholder role ({{CATEGORY}}):

#### General Questions
1. What are your primary responsibilities?
2. What challenges do you face in your current workflow?
3. What would make your job easier?

#### {{CATEGORY}}-Specific Questions
{{#if EXECUTIVE}}
1. What are the business objectives for this initiative?
2. How does this align with company strategy?
3. What is the expected ROI?
4. What are the key success criteria?
{{/if}}
{{#if BUSINESS_USER}}
1. Walk me through your typical day
2. What tasks take the most time?
3. What information do you need that's hard to get?
4. How do you currently handle [process]?
{{/if}}
{{#if TECHNICAL}}
1. What are the current system limitations?
2. What integrations are needed?
3. What are the non-functional requirements?
4. What are the technical constraints?
{{/if}}

### Interview Notes Template

Created: ba-workflow/phase-3-elicitation/interview-notes/{{STAKEHOLDER_NAME}}.md
```

### Workshop (--workshop)

```markdown
## Workshop Preparation

Workshop Types:
1. **requirements** - Requirements Discovery Workshop
2. **process** - Process Mapping Workshop
3. **prioritization** - Prioritization Workshop (MoSCoW)
4. **validation** - Requirements Validation Workshop

Selected: {{WORKSHOP_TYPE}}

### Workshop: {{WORKSHOP_NAME}}

**Duration:** {{DURATION}}
**Participants:** {{PARTICIPANT_COUNT}}
**Facilitator:** {{FACILITATOR}}

### Agenda

{{#if REQUIREMENTS_WORKSHOP}}
1. Introduction & Objectives (15 min)
2. Current State Review (30 min)
3. Future State Visioning (45 min)
4. Requirements Brainstorming (60 min)
5. Prioritization (30 min)
6. Wrap-up & Next Steps (15 min)
{{/if}}

{{#if PROCESS_WORKSHOP}}
1. Introduction & Scope (15 min)
2. As-Is Process Mapping (60 min)
3. Pain Points Identification (30 min)
4. To-Be Process Design (60 min)
5. Gap Analysis (30 min)
6. Action Items (15 min)
{{/if}}

{{#if PRIORITIZATION_WORKSHOP}}
1. Introduction & Method Overview (15 min)
2. Requirements Review (30 min)
3. MoSCoW Categorization (60 min)
   - Must Have
   - Should Have
   - Could Have
   - Won't Have
4. Validation & Agreement (30 min)
5. Documentation (15 min)
{{/if}}

### Materials Checklist

- [ ] Agenda distributed
- [ ] Presentation slides
- [ ] Whiteboard/Miro board
- [ ] Sticky notes (if in-person)
- [ ] Requirements list
- [ ] Stakeholder matrix
```

### Import (--import)

```markdown
## Import Customer Feedback

**File:** {{FILENAME}}

This will:
1. Call `/f5-import {{FILENAME}} --type requirements`
2. Store in ba-workflow/phase-3-elicitation/imported-documents/
3. Update elicitation log
4. Link to document pipeline

### Processing...

{{IMPORT_RESULT}}

### Import Summary

| Metric | Value |
|--------|-------|
| Total Items | {{TOTAL}} |
| Requirements | {{REQ_COUNT}} |
| Issues | {{ISSUE_COUNT}} |
| Duplicates | {{DUP_COUNT}} |

### Files Created

- Imported: ba-workflow/phase-3-elicitation/imported-documents/{{FILENAME}}
- Requirements: .f5/input/requirements/{{VERSION}}/

### Next Steps

1. Review imported requirements
2. Validate quality: `/f5-req validate`
3. If issues present: `/f5-jira-convert`
```

---

## ACTION: CHECK_GATE

### `/f5-ba gate --phase <1-5>`

Check quality gate for a phase.

### Gate Checklists

#### Gate 1: Enterprise Analysis Complete

```markdown
## Gate 1: Enterprise Analysis Complete

### Required Items

| Item | Status | Notes |
|------|--------|-------|
| Stakeholder map documented | {{STATUS}} | {{NOTES}} |
| Problem statement defined | {{STATUS}} | {{NOTES}} |
| Current state documented | {{STATUS}} | {{NOTES}} |

### Optional Items

| Item | Status | Notes |
|------|--------|-------|
| Business objectives identified | {{STATUS}} | {{NOTES}} |
| Success criteria defined | {{STATUS}} | {{NOTES}} |
| Constraints documented | {{STATUS}} | {{NOTES}} |

### Pass Criteria

- Required items: {{REQUIRED_DONE}}/{{REQUIRED_TOTAL}} (must be 100%)
- Optional items: {{OPTIONAL_DONE}}/{{OPTIONAL_TOTAL}}

### Result: {{GATE_RESULT}}

{{#if PASSED}}
Gate 1 PASSED - You may proceed to Phase 2.
{{else}}
Gate 1 NOT PASSED - Complete required items before proceeding.

Missing Items:
{{#each MISSING_ITEMS}}
- {{this}}
{{/each}}
{{/if}}
```

#### Gate 2: Requirements Planning Complete

```markdown
## Gate 2: Requirements Planning Complete

### Required Items

| Item | Status |
|------|--------|
| Scope document created | {{STATUS}} |
| Requirements management plan | {{STATUS}} |
| Communication plan defined | {{STATUS}} |

### Optional Items

| Item | Status |
|------|--------|
| Risk register started | {{STATUS}} |
| Change management plan | {{STATUS}} |
```

#### Gate 3: Elicitation Complete

```markdown
## Gate 3: Elicitation Complete

### Required Items

| Item | Status |
|------|--------|
| Key stakeholder interviews completed | {{STATUS}} |
| Document analysis done | {{STATUS}} |
| Requirements gathered | {{STATUS}} |

### Optional Items

| Item | Status |
|------|--------|
| Workshop conducted | {{STATUS}} |
| Survey completed | {{STATUS}} |
| Prototypes reviewed | {{STATUS}} |
```

#### Gate 4: Documentation Complete

```markdown
## Gate 4: Documentation Complete

### Required Items

| Item | Status |
|------|--------|
| BRD or SRS created | {{STATUS}} |
| Requirements quality score >= 70 | {{STATUS}} (Score: {{SCORE}}) |
| Traceability matrix updated | {{STATUS}} |

### Optional Items

| Item | Status |
|------|--------|
| FRS created | {{STATUS}} |
| Use cases documented | {{STATUS}} |
| Non-functional requirements | {{STATUS}} |

### Quality Check

Run `/f5-req validate` to check requirement quality before passing this gate.
```

#### Gate 5: Validation Complete

```markdown
## Gate 5: Validation Complete

### Required Items

| Item | Status |
|------|--------|
| Stakeholder review completed | {{STATUS}} |
| Sign-off obtained | {{STATUS}} |
| Baseline created | {{STATUS}} |

### Optional Items

| Item | Status |
|------|--------|
| All feedback addressed | {{STATUS}} |
| Change requests logged | {{STATUS}} |
```

---

## ACTION: GENERATE_DOCUMENT

### `/f5-ba document`

Generate BA documents.

### Options

| Option | Description |
|--------|-------------|
| `--problem` | Create Problem Statement |
| `--brd` | Generate Business Requirements Document |
| `--srs` | Generate Software Requirements Specification |
| `--frs` | Generate Functional Requirements Specification |
| `--from-doc [version]` | Generate from doc pipeline version |
| `--lang <code>` | Translate output to specified language. Codes: `en` (English), `vn` (Vietnamese), `ja` (Japanese). Adds `_{lang}` suffix to filename (e.g., `srs_vn.md`, `brd_ja.md`) |

### Problem Statement (--problem)

```markdown
## Problem Statement Template

Created: ba-workflow/phase-1-enterprise-analysis/problem-statement.md

### Template Contents:

# Problem Statement

## Background
[Describe the current situation and context]

## Problem Description
[Clearly state the problem]

## Impact
[Describe the business impact of this problem]
- Financial impact:
- Operational impact:
- Customer impact:

## Affected Stakeholders
[List who is affected by this problem]

## Current Workarounds
[Describe any existing workarounds]

## Constraints
[List any constraints for the solution]

## Success Criteria
[Define measurable success criteria]
```

### BRD (--brd)

```markdown
## Business Requirements Document

Generated: ba-workflow/phase-4-documentation/documents/brd.md

### Structure:

1. Executive Summary
2. Business Objectives
3. Scope
   - In Scope
   - Out of Scope
4. Stakeholders
5. Business Requirements
6. Business Rules
7. Assumptions & Constraints
8. Dependencies
9. Risks
10. Glossary
11. Appendix: Stakeholder Sign-off
```

### SRS (--srs)

```markdown
## Software Requirements Specification

Generated: ba-workflow/phase-4-documentation/documents/srs.md

### Structure:

1. Introduction
   1.1 Purpose
   1.2 Scope
   1.3 Definitions
   1.4 References
2. Overall Description
   2.1 Product Perspective
   2.2 Product Functions
   2.3 User Classes
   2.4 Operating Environment
   2.5 Constraints
   2.6 Assumptions
3. Functional Requirements
   [Generated from imported requirements]
4. Non-Functional Requirements
   4.1 Performance
   4.2 Security
   4.3 Reliability
   4.4 Availability
5. External Interface Requirements
6. Traceability Matrix
7. Appendix
```

### From Doc Pipeline (--from-doc)

```markdown
## Generate from Document Pipeline

Source Version: {{VERSION}}
Requirements: {{REQ_COUNT}}

This will:
1. Load requirements from .f5/input/requirements/{{VERSION}}/
2. Generate structured SRS document
3. Create traceability matrix
4. Link to source documents

### Processing...

### Generated Documents

- SRS: ba-workflow/phase-4-documentation/documents/srs.md
- Traceability: ba-workflow/phase-4-documentation/documents/traceability.md

### Requirements Summary

| Category | Count |
|----------|-------|
| Functional | {{FR_COUNT}} |
| Non-Functional | {{NFR_COUNT}} |
| Business Rules | {{BR_COUNT}} |

### Next Steps

1. Review generated documents
2. Validate quality: `/f5-req validate`
3. Check Gate 4: `/f5-ba gate --phase 4`
```

---

## ACTION: ITERATE_PHASE

### `/f5-ba iterate --to <phase> --reason "<reason>"`

Iterate back to a previous phase.

```markdown
## Iteration Request

**Current Phase:** {{CURRENT_PHASE}}
**Target Phase:** {{TARGET_PHASE}}
**Reason:** {{REASON}}

### Iteration Log

| Date | From | To | Reason | Initiated By |
|------|------|----|----- --|--------------|
| {{DATE}} | Phase {{FROM}} | Phase {{TO}} | {{REASON}} | {{USER}} |

### Impact Assessment

Reverting to Phase {{TARGET}} will:
{{#each IMPACTS}}
- {{this}}
{{/each}}

### Confirmation

Are you sure you want to iterate back to Phase {{TARGET}}?

[Y/N]?

### Result

Phase set to {{TARGET_PHASE}}.
Status updated in ba-workflow/status.json.

### Next Steps

{{#each NEXT_STEPS}}
- {{this}}
{{/each}}
```

---

## INTEGRATION WITH OTHER COMMANDS

### Integration Flow

```
/f5-ba elicit --import file.xlsx
    ↓
/f5-import file.xlsx --type requirements (Phase 1)
    ↓
.f5/input/requirements/...
    ↓
/f5-req validate (Phase 3)
    ↓
/f5-jira-convert (if issues) (Phase 2)
    ↓
/f5-ba document --srs
    ↓
/f5-strict start srs.md (Implementation)
```

### Example Workflow

```
# 1. Initialize BA workflow
/f5-ba init

# 2. Add stakeholders
/f5-ba stakeholders --add
/f5-ba stakeholders --matrix

# 3. Document problem statement
/f5-ba document --problem

# 4. Check Gate 1
/f5-ba gate --phase 1

# 5. Import customer feedback
/f5-ba elicit --import customer_feedback.xlsx

# 6. Validate requirements quality
/f5-req validate .f5/input/requirements/v1.0/

# 7. Check Gate 3
/f5-ba gate --phase 3

# 8. Generate SRS
/f5-ba document --srs

# 9. Check Gate 4
/f5-ba gate --phase 4

# 10. Get sign-off
/f5-ba gate --phase 5
```

---

## STATUS FILE FORMAT

```json
// ba-workflow/status.json
{
  "project": "my-project",
  "createdAt": "2024-01-10T09:00:00Z",
  "currentPhase": 2,
  "phases": {
    "1": {
      "name": "Enterprise Analysis",
      "status": "completed",
      "startedAt": "2024-01-10T09:00:00Z",
      "completedAt": "2024-01-12T15:00:00Z",
      "progress": 100
    },
    "2": {
      "name": "Requirements Planning",
      "status": "in_progress",
      "startedAt": "2024-01-12T15:00:00Z",
      "completedAt": null,
      "progress": 60
    }
  },
  "gates": {
    "1": { "status": "passed", "passedAt": "2024-01-12T15:00:00Z" },
    "2": { "status": "not_started", "passedAt": null }
  },
  "stakeholders": [...],
  "elicitationLog": [...],
  "iterations": [...]
}
```

---

## MANDATORY: VERIFY OUTPUT AFTER GENERATE

After ANY BA workflow command, Claude MUST verify:

### Step 1: Create directories FIRST (MANDATORY)
```bash
mkdir -p .f5/ba-workflow/{phase-1-enterprise-analysis,phase-2-planning,phase-3-elicitation/{interview-notes,workshop-notes,imported-documents},phase-4-documentation/{documents,signoff},phase-5-validation/{review-notes,signoff},templates,gates}
```

### Step 2: Check file location
```bash
ls -la .f5/ba-workflow/
ls -la .f5/ba-workflow/phase-1-enterprise-analysis/
ls -la .f5/ba-workflow/phase-4-documentation/documents/
```

### Step 3: If files in wrong location, FIX IMMEDIATELY
```bash
# Fix 1: Files in root ba-workflow/ (missing .f5/ prefix!)
if [ -d "ba-workflow" ]; then
  mv ba-workflow .f5/
fi

# Fix 2: Files in docs/
if [ -d "docs" ]; then
  mv docs/*.md .f5/ba-workflow/phase-4-documentation/documents/ 2>/dev/null
  rmdir docs 2>/dev/null
fi
```

### Step 4: Report final location
**Correct file locations:**
| File | Correct Location |
|------|------------------|
| status.json | `.f5/ba-workflow/status.json` |
| stakeholder-map.md | `.f5/ba-workflow/phase-1-enterprise-analysis/stakeholder-map.md` |
| problem-statement.md | `.f5/ba-workflow/phase-1-enterprise-analysis/problem-statement.md` |
| srs.md | `.f5/ba-workflow/phase-4-documentation/documents/srs.md` |
| brd.md | `.f5/ba-workflow/phase-4-documentation/documents/brd.md` |

**⛔ Claude MUST NOT report success until files are in correct `.f5/ba-workflow/` path!**

---

## EXAMPLES

```
# Initialize BA workflow
/f5-ba init

# Check status
/f5-ba status

# Add stakeholder
/f5-ba stakeholders --add

# View stakeholder matrix
/f5-ba stakeholders --matrix

# Prepare interview
/f5-ba elicit --interview "Product Manager"

# Prepare workshop
/f5-ba elicit --workshop requirements

# Import customer Excel
/f5-ba elicit --import feedback.xlsx

# Check Gate 2
/f5-ba gate --phase 2

# Generate Problem Statement
/f5-ba document --problem

# Generate SRS
/f5-ba document --srs

# Generate from imported requirements
/f5-ba document --from-doc v1.2.0

# Iterate back to Phase 2
/f5-ba iterate --to 2 --reason "New requirements discovered"

# Generate SRS with Vietnamese translation
/f5-ba document --srs --lang vn
# Output: ba-workflow/phase-4-documentation/documents/srs_vn.md

# Generate BRD with Japanese translation
/f5-ba document --brd --lang ja
# Output: ba-workflow/phase-4-documentation/documents/brd_ja.md
```

---

**Remember:** BA workflow integrates with `/f5-import`, `/f5-jira-convert`, `/f5-req`, and `/f5-strict` for end-to-end requirements management!
