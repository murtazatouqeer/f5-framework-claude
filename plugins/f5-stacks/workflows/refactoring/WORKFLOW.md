# Refactoring Workflow

Workflow cho code refactoring - cải thiện code quality mà không thay đổi behavior.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Development Type |
| **Duration** | 1-3 tuần |
| **Team Size** | 1-3 người |
| **Quality Gates** | D3→G2→G2.5→G3 |
| **Risk Level** | Medium |
| **Starting Point** | refactoring-request |

## When to Use

### Ideal For

- Technical debt reduction
- Code readability improvement
- Design pattern application
- Module extraction or consolidation
- Test coverage improvement
- Dead code removal

### Not Suitable For

- Adding new features → Use [Feature Development](../feature-development/)
- Architecture changes → Use [Modernization](../modernization/)
- Bug fixes → Use [Maintenance](../maintenance/)
- Technology upgrade → Use [Platform Migration](../platform-migration/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                      REFACTORING WORKFLOW                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │                │
│  │ Assess  │  │  Plan   │  │Refactor │  │ Verify  │                │
│  │         │  │   D3    │  │G2→G2.5  │  │   G3    │                │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                │
│                                                                       │
│  Rule: Same behavior in, better code out                              │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Assess

**Duration**: 2-3 days

**Objectives**:
- Identify refactoring targets
- Measure current code quality metrics
- Assess risk and dependencies

**Activities**:
```bash
/f5-load
/f5-analyze code-quality
/f5-review code --deep
```

**Deliverables**:
- [ ] Code Quality Report
- [ ] Refactoring Targets (prioritized)
- [ ] Dependency Map
- [ ] Current Test Coverage

### Phase 2: Plan (D3)

**Duration**: 2-3 days

**Objectives**:
- Define refactoring strategy
- Plan safe refactoring steps
- Ensure test coverage before changes

**Activities**:
```bash
/f5-design generate refactoring-plan
/f5-test run --coverage
/f5-gate complete D3
```

**Deliverables**:
- [ ] Refactoring Plan
- [ ] Pre-refactoring Test Baseline
- [ ] Step-by-step Execution Order

### Phase 3: Refactor (G2→G2.5)

**Duration**: 1-2 weeks

**Objectives**:
- Execute refactoring steps
- Verify behavior unchanged at each step
- Code review all changes

**Activities**:
```bash
/f5-implement start REFACTOR-001
/f5-test run --after-each-change
/f5-review code
/f5-gate complete G2
/f5-gate complete G2.5
```

**Deliverables**:
- [ ] Refactored Code
- [ ] Code Review Approved
- [ ] All Tests Still Passing

### Phase 4: Verify (G3)

**Duration**: 2-3 days

**Objectives**:
- Full regression testing
- Code quality improvement confirmed
- No behavior changes

**Activities**:
```bash
/f5-test run --coverage
/f5-test-e2e full
/f5-analyze code-quality --compare
/f5-gate complete G3
```

**Deliverables**:
- [ ] Regression Tests Passing
- [ ] Code Quality Improvement Report
- [ ] Coverage Maintained or Improved

## Best Practices

1. **Tests first** - Ensure comprehensive tests exist before refactoring
2. **Small steps** - Make small, verifiable changes
3. **No behavior changes** - Refactoring must not alter external behavior
4. **Continuous verification** - Run tests after every change
5. **One concern at a time** - Don't mix refactoring with feature changes
