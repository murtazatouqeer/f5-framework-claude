# From Detail Design Workflow

Workflow cho project đã có detail design (D4) - bắt đầu implementation ngay.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Development Type |
| **Duration** | 1-6 tuần |
| **Team Size** | 1-5 người |
| **Quality Gates** | G2→G2.5→G3 |
| **Risk Level** | Low-Medium |
| **Starting Point** | detail-design (D4 complete) |

## When to Use

### Ideal For

- Project already has detail design documents
- D4 gate passed, ready to code
- External team provided design specs
- Resuming project after design freeze

### Not Suitable For

- No design exists → Start from earlier workflow
- Only basic design → Use [From Basic Design](../from-basic-design/)
- Need requirements gathering → Use [BA Workflow](../ba/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                  FROM DETAIL DESIGN WORKFLOW                          │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  D4 ✅     ┌──────────┐  ┌──────────┐  ┌──────────┐                │
│  (done)───▶│ Phase 1  │─▶│ Phase 2  │─▶│ Phase 3  │                │
│            │  Impl    │  │  Test    │  │ Release  │                │
│            │ G2→G2.5  │  │   G3     │  │    -     │                │
│            └──────────┘  └──────────┘  └──────────┘                │
│                                                                       │
│  Fast track - Design is ready, start coding immediately              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Implementation (G2→G2.5)

**Duration**: 1-4 weeks

**Objectives**:
- Implement based on detail design specs
- Code review all changes
- Verify implementation matches design

**Activities**:
```bash
/f5-load
/f5-implement start REQ-001
/f5-tdd start feature
/f5-review code
/f5-verify --gate
/f5-gate complete G2
/f5-gate complete G2.5
```

**Deliverables**:
- [ ] Implementation Complete
- [ ] Code Review Approved
- [ ] Design Verification Passed

### Phase 2: Testing (G3)

**Duration**: 1-2 weeks

**Objectives**:
- Comprehensive testing
- Coverage targets met
- Integration validation

**Activities**:
```bash
/f5-test run --coverage
/f5-test-it api --all
/f5-test-e2e smoke
/f5-gate complete G3
```

**Deliverables**:
- [ ] All Tests Passing
- [ ] Coverage Report
- [ ] Integration Test Results

### Phase 3: Release

**Duration**: 1-3 days

**Objectives**:
- Deploy and monitor

**Activities**:
```bash
/f5-deploy staging
/f5-deploy production
```

**Deliverables**:
- [ ] Deployed Application
- [ ] Release Notes
- [ ] Monitoring Active
