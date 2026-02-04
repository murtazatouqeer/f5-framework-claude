# Modernization Workflow

Workflow cho modernization - nâng cấp technology stack và architecture mà giữ nguyên business logic.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Migration Type |
| **Duration** | 1-6 tháng |
| **Team Size** | 2-8 người |
| **Quality Gates** | D1→D3→D4→G2→G2.5→G3 |
| **Risk Level** | High |
| **Starting Point** | modernization-request |

## When to Use

### Ideal For

- Technology stack upgrade (e.g., jQuery → React)
- Monolith to microservices decomposition
- Cloud-native transformation
- Architecture modernization while preserving business logic
- Performance/scalability improvements

### Not Suitable For

- Minor updates → Use [Feature Development](../feature-development/)
- Code cleanup only → Use [Refactoring](../refactoring/)
- Full rewrite → Use [Greenfield](../greenfield/)
- Moving to different platform → Use [Platform Migration](../platform-migration/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                     MODERNIZATION WORKFLOW                             │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │─▶│ Phase 5 │  │
│  │ Assess  │  │ Plan    │  │ Execute │  │ Verify  │  │ Cutover │  │
│  │   D1    │  │  D3→D4  │  │G2→G2.5  │  │   G3    │  │    -    │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
│                                                                       │
│  Strangler Fig Pattern - Gradual replacement recommended              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Assessment (D1)

**Duration**: 1-2 weeks

**Objectives**:
- Assess current system state
- Identify modernization targets
- Evaluate technology options

**Activities**:
```bash
/f5-load
/f5-research deep --scope modernization
/f5-analyze architecture
/f5-gate complete D1
```

**Deliverables**:
- [ ] Current State Assessment
- [ ] Technology Evaluation
- [ ] Modernization Candidates
- [ ] Risk Assessment

### Phase 2: Planning (D3→D4)

**Duration**: 2-4 weeks

**Objectives**:
- Design target architecture
- Plan migration strategy (strangler fig, parallel run, etc.)
- Define rollback procedures

**Activities**:
```bash
/f5-design generate architecture --modernize
/f5-design generate migration-strategy
/f5-gate complete D3
/f5-gate complete D4
```

**Deliverables**:
- [ ] Target Architecture
- [ ] Migration Strategy Document
- [ ] Rollback Plan
- [ ] Component Migration Order

### Phase 3: Execute (G2→G2.5)

**Duration**: 1-4 months

**Objectives**:
- Modernize components incrementally
- Maintain backward compatibility
- Code review all changes

**Activities**:
```bash
/f5-implement start MOD-001
/f5-review code
/f5-verify --gate
/f5-gate complete G2
/f5-gate complete G2.5
```

**Deliverables**:
- [ ] Modernized Components
- [ ] Code Reviews Approved
- [ ] Backward Compatibility Verified

### Phase 4: Verify (G3)

**Duration**: 2-3 weeks

**Objectives**:
- Regression testing
- Performance benchmarking
- Integration validation

**Activities**:
```bash
/f5-test run --coverage
/f5-test-e2e full
/f5-test-it api --all
/f5-gate complete G3
```

**Deliverables**:
- [ ] Regression Test Results
- [ ] Performance Comparison Report
- [ ] Integration Test Results

### Phase 5: Cutover

**Duration**: 1-2 weeks

**Objectives**:
- Production deployment
- Monitor and stabilize
- Decommission old components

**Activities**:
```bash
/f5-deploy staging
/f5-deploy production
/f5-monitor performance
```

**Deliverables**:
- [ ] Production Deployment
- [ ] Performance Baseline
- [ ] Old System Decommission Plan

## Best Practices

1. **Strangler Fig Pattern** - Replace incrementally, not all at once
2. **Feature parity first** - Match existing behavior before adding new features
3. **Performance benchmarks** - Compare old vs new at every step
4. **Parallel running** - Run old and new side-by-side when possible
