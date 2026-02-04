# Platform Migration Workflow

Workflow cho platform migration - chuyển đổi platform (OS, cloud provider, runtime).

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Migration Type |
| **Duration** | 1-3 tháng |
| **Team Size** | 2-5 người |
| **Quality Gates** | D1→D3→D4→G2→G3 |
| **Risk Level** | High |
| **Starting Point** | migration-request |

## When to Use

### Ideal For

- Cloud provider migration (AWS → GCP, on-prem → cloud)
- Runtime migration (Java 8 → Java 21, Python 2 → 3)
- OS migration (Windows Server → Linux)
- Container platform migration (Docker → Kubernetes)
- CI/CD platform migration

### Not Suitable For

- Database-only changes → Use [Database Migration](../database-migration/)
- Architecture changes → Use [Modernization](../modernization/)
- Application rewrite → Use [Greenfield](../greenfield/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                   PLATFORM MIGRATION WORKFLOW                         │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │─▶│ Phase 5 │  │
│  │ Assess  │  │  Plan   │  │ Execute │  │ Verify  │  │ Cutover │  │
│  │   D1    │  │  D3→D4  │  │   G2    │  │   G3    │  │    -    │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
│                                                                       │
│  ⚠️  Requires parallel environment during migration                   │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Assessment (D1)

**Duration**: 1-2 weeks

**Objectives**:
- Inventory current platform dependencies
- Evaluate target platform compatibility
- Identify migration blockers

**Activities**:
```bash
/f5-load
/f5-analyze platform-dependencies
/f5-research deep --scope platform-migration
/f5-gate complete D1
```

**Deliverables**:
- [ ] Platform Dependency Inventory
- [ ] Compatibility Assessment
- [ ] Migration Blockers List
- [ ] Cost Analysis

### Phase 2: Planning (D3→D4)

**Duration**: 1-2 weeks

**Objectives**:
- Design migration architecture
- Create migration scripts/playbooks
- Plan parallel running strategy

**Activities**:
```bash
/f5-design generate migration-architecture
/f5-design generate infrastructure
/f5-gate complete D3
/f5-gate complete D4
```

**Deliverables**:
- [ ] Migration Architecture
- [ ] Infrastructure as Code
- [ ] Rollback Procedures
- [ ] Parallel Run Plan

### Phase 3: Execute (G2)

**Duration**: 2-6 weeks

**Objectives**:
- Set up target platform
- Migrate application components
- Configure infrastructure

**Activities**:
```bash
/f5-implement start MIG-001
/f5-deploy staging --target-platform
/f5-gate complete G2
```

**Deliverables**:
- [ ] Target Platform Ready
- [ ] Application Migrated
- [ ] Infrastructure Configured

### Phase 4: Verify (G3)

**Duration**: 1-2 weeks

**Objectives**:
- Full regression testing on new platform
- Performance comparison
- Security validation

**Activities**:
```bash
/f5-test run --coverage
/f5-test-e2e full --platform new
/f5-gate complete G3
```

**Deliverables**:
- [ ] Regression Test Results
- [ ] Performance Comparison
- [ ] Security Validation

### Phase 5: Cutover

**Duration**: 1-5 days

**Objectives**:
- DNS/traffic cutover
- Monitor new platform
- Decommission old platform

**Activities**:
```bash
/f5-deploy production --cutover
/f5-monitor platform
```

**Deliverables**:
- [ ] Production Cutover Complete
- [ ] Monitoring Active
- [ ] Old Platform Decommission Schedule

## Best Practices

1. **Parallel environments** - Run old and new simultaneously during migration
2. **Automated testing** - Comprehensive test suite is essential
3. **Incremental cutover** - Use canary or blue-green deployment
4. **Rollback ready** - Always maintain ability to revert to old platform
