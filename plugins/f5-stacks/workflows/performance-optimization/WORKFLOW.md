# Performance Optimization Workflow

Workflow cho performance optimization - cải thiện hiệu năng dựa trên measurement.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Optimization Type |
| **Duration** | 1-4 tuần |
| **Team Size** | 1-3 người |
| **Quality Gates** | D3→G2→G2.5→G3 |
| **Risk Level** | Medium |
| **Starting Point** | performance-issue |

## When to Use

### Ideal For

- Application performance degradation
- Scaling preparation (expected traffic increase)
- Database query optimization
- API response time improvement
- Frontend load time optimization
- Memory/CPU usage reduction

### Not Suitable For

- Architecture redesign → Use [Modernization](../modernization/)
- Adding new features → Use [Feature Development](../feature-development/)
- Bug fixes → Use [Maintenance](../maintenance/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                 PERFORMANCE OPTIMIZATION WORKFLOW                      │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │                │
│  │Measure  │  │ Analyze │  │Optimize │  │ Verify  │                │
│  │ Baseline│  │   D3    │  │G2→G2.5  │  │   G3    │                │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                │
│                      │                        │                       │
│                      └────── Iterate ─────────┘                       │
│                                                                       │
│  Measure → Analyze → Optimize → Verify → Repeat                      │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Measure Baseline

**Duration**: 2-3 days

**Objectives**:
- Establish performance baselines
- Identify bottlenecks
- Set improvement targets

**Activities**:
```bash
/f5-load
/f5-analyze performance --baseline
/f5-test-e2e performance --measure
```

**Deliverables**:
- [ ] Performance Baseline Report
- [ ] Bottleneck Identification
- [ ] Improvement Targets (specific metrics)

### Phase 2: Analyze & Plan (D3)

**Duration**: 2-5 days

**Objectives**:
- Root cause analysis of bottlenecks
- Design optimization strategy
- Prioritize by impact vs effort

**Activities**:
```bash
/f5-analyze performance --deep
/f5-design generate optimization-plan
/f5-gate complete D3
```

**Deliverables**:
- [ ] Root Cause Analysis
- [ ] Optimization Plan (prioritized)
- [ ] Expected Impact Estimates

### Phase 3: Optimize (G2→G2.5)

**Duration**: 1-2 weeks

**Objectives**:
- Implement optimizations
- Code review changes
- Verify no regressions

**Activities**:
```bash
/f5-implement start PERF-001
/f5-review code
/f5-gate complete G2
/f5-gate complete G2.5
```

**Deliverables**:
- [ ] Optimizations Implemented
- [ ] Code Review Approved
- [ ] No Regressions

### Phase 4: Verify (G3)

**Duration**: 2-3 days

**Objectives**:
- Measure improvements against baseline
- Validate targets met
- Regression testing

**Activities**:
```bash
/f5-test run --coverage
/f5-test-e2e performance --compare-baseline
/f5-gate complete G3
```

**Deliverables**:
- [ ] Performance Comparison Report
- [ ] Targets Met Confirmation
- [ ] Regression Test Results

## Best Practices

1. **Measure first** - Never optimize without baseline measurements
2. **Profile, don't guess** - Use profiling tools to find real bottlenecks
3. **One change at a time** - Isolate optimizations to measure individual impact
4. **Regression test** - Performance changes can introduce bugs
5. **Document findings** - Record what worked and what didn't for future reference
