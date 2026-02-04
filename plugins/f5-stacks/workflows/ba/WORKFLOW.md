# Business Analysis Workflow

Real-world business analysis process following BABOK standards with iterative requirements management.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Analysis Type |
| **Duration** | 3-6 tuần |
| **Team Size** | 1-3 người |
| **Quality Gates** | D1→D2 |
| **Risk Level** | Low-Medium |
| **Starting Point** | business-need |

## When to Use

### Ideal For

- New project requirements gathering
- Stakeholder-driven requirement elicitation
- BABOK-compliant business analysis
- Document pipeline with versioned requirements
- SRS generation from Excel imports

### Not Suitable For

- Pure technical analysis → Use code analysis tools
- Quick prototyping → Use [MVP](../mvp/) or [POC](../poc/)
- Existing spec refinement → Use [Feature Development](../feature-development/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                  BUSINESS ANALYSIS WORKFLOW                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │ Phase 1  │─▶│ Phase 2  │─▶│ Phase 3  │─▶│ Phase 4  │─▶│Phase 5 ││
│  │Enterprise│  │ Planning │  │Elicitation│  │  Docs    │  │Validate││
│  │ Analysis │  │          │  │          │  │          │  │        ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └────────┘│
│                                                                       │
│  ◀──────────── Iteration allowed at any phase ──────────────▶        │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Enterprise Analysis

**Duration**: 3-5 days

**Objectives**:
- Understand business context and identify problems
- Map stakeholders
- Define problem statement and business case

**Activities**:
```bash
/f5-load
/f5-ba analyze-enterprise
/f5-import --analyze initial-requirements.xlsx
```

**Deliverables**:
- [ ] Stakeholder Map
- [ ] AS-IS Process
- [ ] Problem Statement
- [ ] Business Case

### Phase 2: Requirement Planning

**Duration**: 2-3 days

**Objectives**:
- Plan requirements gathering activities
- Schedule interviews
- Create communication plan

**Activities**:
```bash
/f5-ba plan-elicitation
/f5-design generate communication-plan
```

**Deliverables**:
- [ ] Project Approach
- [ ] Interview Schedule
- [ ] Communication Plan

### Phase 3: Requirements Elicitation

**Duration**: 1-2 weeks

**Objectives**:
- Gather requirements from stakeholders
- Conduct interviews and workshops
- Document raw requirements

**Activities**:
```bash
/f5-ba elicit --interview
/f5-import feedback.xlsx --type patch
/f5-question track
```

**Deliverables**:
- [ ] Interview Notes
- [ ] Workshop Outcomes
- [ ] Raw Requirements

### Phase 4: Analysis & Documentation

**Duration**: 1 week

**Objectives**:
- Analyze and document requirements
- Create BRD and SRS documents
- Build traceability matrix

**Activities**:
```bash
/f5-ba document-requirements
/f5-strict start docs/srs.md
/f5-gate complete D1
```

**Deliverables**:
- [ ] BRD Document
- [ ] SRS Document
- [ ] Traceability Matrix

### Phase 5: Validation & Sign-off

**Duration**: 3-5 days

**Objectives**:
- Confirm with stakeholders
- Establish requirement baseline
- Get final sign-off

**Activities**:
```bash
/f5-ba validate-requirements
/f5-strict validate
/f5-gate complete D2
```

**Deliverables**:
- [ ] Signed SRS
- [ ] Baseline Version
- [ ] Approval Record

## Document Pipeline Integration

This workflow integrates with F5 Document Pipeline for version-controlled requirements:

```bash
# Import Excel requirements
f5 doc import requirements.xlsx --type minor

# Compare versions
f5 doc diff v1.0.0 v1.1.0

# Export to Markdown
f5 doc export --format brs,srs

# Resolve conflicts
f5 doc conflicts
```

## Best Practices

1. **Iterate frequently** - Return to any phase when gaps are discovered
2. **Version everything** - Use document pipeline for requirement versioning
3. **Stakeholder engagement** - Regular checkpoints with stakeholders
4. **Traceability** - Link every requirement to business need
