# From Basic Design Workflow

Workflow cho project đã có basic design (D3) - bắt đầu implementation từ existing design documents.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Development Type |
| **Duration** | 2-8 tuần |
| **Team Size** | 2-5 người |
| **Quality Gates** | D4→G2→G2.5→G3 |
| **Risk Level** | Medium |
| **Starting Point** | basic-design (D3 complete) |

## When to Use

### Ideal For

- Project already has architecture documents
- Basic design (D3) approved, need detail design and implementation
- Joining existing project mid-design
- Resuming paused project after basic design phase

### Not Suitable For

- No design exists → Use [Feature Development](../feature-development/) or [Greenfield](../greenfield/)
- Detail design already done → Use [From Detail Design](../from-detail-design/)
- Just prototyping → Use [POC](../poc/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                   FROM BASIC DESIGN WORKFLOW                          │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  D3 ✅     ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐     │
│  (done)───▶│ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │     │
│            │ Detail  │  │  Impl   │  │  Test   │  │ Release │     │
│            │   D4    │  │G2→G2.5  │  │   G3    │  │    -    │     │
│            └─────────┘  └─────────┘  └─────────┘  └─────────┘     │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Detail Design (D4)

**Duration**: 1-2 weeks

**Objectives**:
- Create detailed component specifications
- Define interfaces and contracts
- Plan implementation approach

**Activities**:
```bash
/f5-load
/f5-design generate detail-design
/f5-design generate api --detail
/f5-gate complete D4
```

**Deliverables**:
- [ ] Detailed Design Document
- [ ] Interface Specifications
- [ ] Implementation Plan

### Phase 2: Implementation (G2→G2.5)

**Duration**: 2-6 weeks

**Objectives**:
- Implement based on detail design
- Code review all changes
- Verify against design

**Activities**:
```bash
/f5-implement start REQ-001
/f5-review code
/f5-verify --gate
/f5-gate complete G2
/f5-gate complete G2.5
```

**Deliverables**:
- [ ] Implementation Complete
- [ ] Code Review Approved
- [ ] Verification Passed

### Phase 3: Testing (G3)

**Duration**: 1-2 weeks

**Objectives**:
- Run all test suites
- Achieve coverage targets
- Performance validation

**Activities**:
```bash
/f5-test run --coverage
/f5-test-e2e smoke
/f5-gate complete G3
```

**Deliverables**:
- [ ] Test Results
- [ ] Coverage Report
- [ ] Performance Benchmarks

### Phase 4: Release

**Duration**: 1-3 days

**Objectives**:
- Deploy to staging and production
- Monitor and validate

**Activities**:
```bash
/f5-deploy staging
/f5-deploy production
```

**Deliverables**:
- [ ] Deployed Application
- [ ] Release Notes
