# Business Analysis Workflow Guide

Complete guide for using the F5 BA Workflow following BABOK standards.

## Overview

The F5 BA Workflow provides a structured approach to business analysis, following BABOK (Business Analysis Body of Knowledge) standards. It guides you through five phases from initial enterprise analysis to final validation.

## Quick Start

```bash
# Initialize BA workflow
/f5-ba init

# Check current status
/f5-ba status

# Progress through phases
/f5-ba elicit --interview
/f5-ba document --srs
/f5-ba gate --phase 4
```

## Workflow Phases

```
ENTERPRISE       REQUIREMENTS      ELICITATION     DOCUMENTATION     VALIDATION
ANALYSIS         PLANNING
    ↓                ↓                 ↓                ↓                ↓
 [Gate 1]        [Gate 2]          [Gate 3]         [Gate 4]         [Gate 5]
    ↓                ↓                 ↓                ↓                ↓
 Problem         Stakeholder       Interviews       BRD/SRS          Review &
 Statement       Matrix            Workshops        Documents        Sign-off
```

## Phase 1: Enterprise Analysis

**Goal:** Understand business context and define problem statement.

### Activities

1. **Problem Definition**
   - Document current state
   - Identify pain points
   - Define success criteria

2. **Stakeholder Identification**
   - List all stakeholders
   - Categorize by role
   - Initial influence assessment

3. **Scope Definition**
   - Business boundaries
   - System boundaries
   - Integration points

### Commands

```bash
# Initialize with project information
/f5-ba init

# Output: Creates ba-workflow/ directory structure
```

### Gate 1 Checklist

- [ ] Problem statement documented
- [ ] Business case clear
- [ ] Success metrics defined
- [ ] Initial stakeholders identified
- [ ] Project scope outlined

### Example Output

```markdown
## Problem Statement

**Current State:**
Manual order processing taking 48 hours average

**Pain Points:**
- Data entry errors (15% rate)
- No real-time inventory visibility
- Customer complaints about delays

**Success Criteria:**
- Reduce processing time to <4 hours
- Error rate below 1%
- Real-time inventory updates
```

## Phase 2: Requirements Planning

**Goal:** Create stakeholder matrix and plan elicitation activities.

### Activities

1. **Stakeholder Analysis**
   - Influence vs Interest matrix
   - Communication preferences
   - Decision authority

2. **Elicitation Planning**
   - Interview schedule
   - Workshop agenda
   - Survey design

3. **Communication Plan**
   - Status reporting
   - Review cycles
   - Escalation paths

### Commands

```bash
# Generate stakeholder matrix
/f5-ba stakeholders

# View matrix
/f5-ba stakeholders --matrix
```

### Stakeholder Matrix

```
            HIGH INFLUENCE
                  │
    Manage        │    Partner
    Closely       │    Closely
                  │
─────────────────────────────────────
                  │
    Monitor       │    Keep
    (Low effort)  │    Informed
                  │
            LOW INFLUENCE
    LOW INTEREST       HIGH INTEREST
```

### Example Stakeholder Mapping

| Stakeholder | Role | Influence | Interest | Strategy |
|-------------|------|-----------|----------|----------|
| VP Operations | Sponsor | High | High | Partner Closely |
| IT Manager | Technical Lead | High | Medium | Manage Closely |
| End Users | Primary Users | Low | High | Keep Informed |
| Compliance | Regulator | High | Low | Manage Closely |

### Gate 2 Checklist

- [ ] Stakeholder matrix complete
- [ ] Interview schedule created
- [ ] Communication plan approved
- [ ] Elicitation timeline defined

## Phase 3: Elicitation

**Goal:** Gather requirements through various techniques.

### Activities

1. **Interviews**
   - Structured interviews with stakeholders
   - Document responses
   - Follow-up questions

2. **Workshops**
   - Group requirements gathering
   - Consensus building
   - Prioritization sessions

3. **Document Analysis**
   - Review existing documentation
   - Process flows
   - System specifications

4. **Observation**
   - Shadow users
   - Workflow analysis
   - Pain point identification

### Commands

```bash
# Start interview elicitation
/f5-ba elicit --interview

# Workshop facilitation
/f5-ba elicit --workshop

# Document analysis
/f5-ba elicit --document-analysis
```

### Interview Template

```markdown
## Interview Record

**Date:** {{DATE}}
**Stakeholder:** {{NAME}}
**Role:** {{ROLE}}
**Duration:** {{DURATION}}

### Questions

1. What are your main responsibilities related to this project?
   > Response:

2. What pain points do you experience with the current process?
   > Response:

3. What would success look like for you?
   > Response:

### Key Insights

- [Insight 1]
- [Insight 2]

### Follow-up Items

- [ ] Item 1
- [ ] Item 2
```

### Gate 3 Checklist

- [ ] All planned interviews completed
- [ ] Workshop minutes documented
- [ ] Requirements raw data collected
- [ ] Initial requirements list created
- [ ] Stakeholder sign-off on findings

## Phase 4: Documentation

**Goal:** Create formal requirement documents.

### Activities

1. **BRD Creation**
   - Business Requirements Document
   - High-level requirements
   - Business rules

2. **SRS Generation**
   - Software Requirements Specification
   - Functional requirements
   - Non-functional requirements

3. **Use Case Documentation**
   - Actor identification
   - Use case diagrams
   - Detailed specifications

4. **Traceability Matrix**
   - Requirement tracing
   - Source tracking
   - Impact analysis

### Commands

```bash
# Generate BRD
/f5-ba document --brd

# Generate SRS
/f5-ba document --srs

# Generate use cases
/f5-ba document --use-cases

# Generate traceability matrix
/f5-ba document --traceability
```

### Document Structure

#### BRD (Business Requirements Document)

```markdown
1. Executive Summary
2. Business Objectives
3. Stakeholders
4. Current State Analysis
5. Future State Vision
6. Business Requirements
   - BR-001: [Requirement]
   - BR-002: [Requirement]
7. Assumptions
8. Constraints
9. Risks
10. Success Metrics
```

#### SRS (Software Requirements Specification)

```markdown
1. Introduction
   1.1 Purpose
   1.2 Scope
   1.3 Definitions
2. Overall Description
   2.1 Product Perspective
   2.2 User Classes
   2.3 Operating Environment
3. Functional Requirements
   - FR-001: [Requirement]
   - FR-002: [Requirement]
4. Non-Functional Requirements
   - NFR-001: [Performance]
   - NFR-002: [Security]
5. External Interfaces
6. Other Requirements
```

### Gate 4 Checklist

- [ ] BRD complete and reviewed
- [ ] SRS complete and reviewed
- [ ] Use cases documented
- [ ] Traceability matrix created
- [ ] Technical review passed
- [ ] Stakeholder acceptance

## Phase 5: Validation

**Goal:** Verify and validate requirements, obtain sign-off.

### Activities

1. **Quality Review**
   - Completeness check
   - Consistency check
   - Testability check

2. **Stakeholder Validation**
   - Walkthrough sessions
   - Feedback collection
   - Conflict resolution

3. **Final Approval**
   - Sign-off collection
   - Version control
   - Baseline creation

### Commands

```bash
# Run quality check
/f5-ba gate --phase 5

# Generate validation report
/f5-ba status --detailed
```

### Validation Checklist

#### Completeness

- [ ] All user classes represented
- [ ] All business processes covered
- [ ] Error scenarios documented
- [ ] Integration points defined

#### Consistency

- [ ] No conflicting requirements
- [ ] Uniform terminology
- [ ] Consistent format
- [ ] Aligned with business objectives

#### Testability

- [ ] Measurable acceptance criteria
- [ ] Verifiable conditions
- [ ] Clear success metrics
- [ ] Edge cases defined

### Gate 5 Checklist

- [ ] All quality checks passed
- [ ] Stakeholder review complete
- [ ] All comments addressed
- [ ] Sign-off obtained from all key stakeholders
- [ ] Requirements baselined
- [ ] Change control process established

## Integration with Other Commands

### With Import

```bash
# Import customer requirements Excel
/f5-import requirements.xlsx

# Run BA workflow on imported data
/f5-ba elicit --document-analysis
```

### With Jira

```bash
# After BA documentation complete
/f5-jira-convert ba-workflow/phase-4-documentation/documents/srs.md

# Sync to Jira
/f5-jira-sync --push
```

### With Strict Mode

```bash
# After BA approval
/f5-strict start ba-workflow/phase-4-documentation/documents/srs.md

# Implement with traceability
/f5-strict approve
```

### With Requirement Quality

```bash
# Check quality before approval
/f5-req analyze ba-workflow/phase-4-documentation/documents/srs.md

# Improve if needed
/f5-req improve ba-workflow/phase-4-documentation/documents/srs.md
```

## Directory Structure

After initialization, the BA workflow creates:

```
ba-workflow/
├── status.json                    # Overall workflow status
├── phase-1-enterprise-analysis/
│   ├── problem-statement.md
│   ├── stakeholders-initial.md
│   └── scope-definition.md
├── phase-2-requirements-planning/
│   ├── stakeholder-matrix.md
│   ├── elicitation-plan.md
│   └── communication-plan.md
├── phase-3-elicitation/
│   ├── interviews/
│   │   └── interview-{date}-{name}.md
│   ├── workshops/
│   │   └── workshop-{date}.md
│   └── findings.md
├── phase-4-documentation/
│   ├── documents/
│   │   ├── brd.md
│   │   ├── srs.md
│   │   └── use-cases.md
│   └── traceability-matrix.md
└── phase-5-validation/
    ├── quality-report.md
    ├── review-comments.md
    └── sign-off.md
```

## Best Practices

### Do's

1. **Complete each phase** before moving to the next
2. **Document everything** - interviews, decisions, changes
3. **Involve stakeholders** throughout the process
4. **Use traceability** from day one
5. **Review regularly** with the team

### Don'ts

1. **Don't skip gates** - they ensure quality
2. **Don't assume** - always validate with stakeholders
3. **Don't rush documentation** - quality over speed
4. **Don't ignore conflicts** - address them early
5. **Don't forget non-functional requirements** - they're critical

## Troubleshooting

### "Gate not passed"

Check the specific gate checklist and address missing items:

```bash
/f5-ba gate --phase 3 --detailed
```

### "Stakeholder matrix incomplete"

Add missing stakeholders:

```bash
/f5-ba stakeholders --add "Name" --role "Role" --influence high
```

### "Documents not generating"

Ensure elicitation data exists:

```bash
/f5-ba status --phase 3
```

## Metrics

### Quality Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Requirement Clarity | >80% | No ambiguous terms |
| Traceability | 100% | All requirements traced |
| Stakeholder Coverage | 100% | All classes represented |
| Test Coverage | >90% | Requirements testable |

### Process Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| Gate Pass Rate | >90% | First-time gate passages |
| Review Cycles | <3 | Iterations per document |
| Sign-off Time | <5 days | Time from review to sign-off |

---

*F5 Framework - BA Workflow Guide v1.0*
