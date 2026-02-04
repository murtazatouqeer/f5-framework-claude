# Database Migration Workflow

Workflow cho database migration - chuyển đổi database schema, data, và related code.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Migration Type |
| **Duration** | 1-4 tuần |
| **Team Size** | 1-3 người |
| **Quality Gates** | D3→D4→G2→G3 |
| **Risk Level** | High |
| **Starting Point** | migration-request |

## When to Use

### Ideal For

- Database schema changes (major restructuring)
- Database engine migration (e.g., MySQL → PostgreSQL)
- Data migration between systems
- Database version upgrades
- Sharding or partitioning changes

### Not Suitable For

- Simple column additions → Use [Feature Development](../feature-development/)
- Full system rewrite → Use [Greenfield](../greenfield/)
- Application-only changes → Use [Refactoring](../refactoring/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                   DATABASE MIGRATION WORKFLOW                          │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │─▶│ Phase 5 │  │
│  │ Analyze │  │ Design  │  │ Migrate │  │ Verify  │  │ Cutover │  │
│  │   D3    │  │   D4    │  │   G2    │  │   G3    │  │    -    │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
│                                                                       │
│  ⚠️  HIGH RISK - Requires rollback plan at every phase                │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Analyze (D3)

**Duration**: 2-5 days

**Objectives**:
- Analyze current database schema
- Identify migration scope and risks
- Plan data transformation rules

**Activities**:
```bash
/f5-load
/f5-db analyze-schema
/f5-design generate migration-plan
/f5-gate complete D3
```

**Deliverables**:
- [ ] Current Schema Documentation
- [ ] Migration Scope Document
- [ ] Risk Assessment
- [ ] Data Transformation Rules

### Phase 2: Design (D4)

**Duration**: 3-5 days

**Objectives**:
- Design target schema
- Create migration scripts
- Plan rollback procedures

**Activities**:
```bash
/f5-db design-schema --target
/f5-design generate rollback-plan
/f5-gate complete D4
```

**Deliverables**:
- [ ] Target Schema Design
- [ ] Migration Scripts
- [ ] Rollback Procedures
- [ ] Performance Impact Analysis

### Phase 3: Migrate (G2)

**Duration**: 1-2 weeks

**Objectives**:
- Execute migration in staging
- Run data transformation
- Validate data integrity

**Activities**:
```bash
/f5-db migrate --staging
/f5-implement start DB-MIGRATION
/f5-gate complete G2
```

**Deliverables**:
- [ ] Migration Executed in Staging
- [ ] Data Transformation Complete
- [ ] Application Code Updated

### Phase 4: Verify (G3)

**Duration**: 3-5 days

**Objectives**:
- Verify data integrity
- Run performance tests
- Validate application compatibility

**Activities**:
```bash
/f5-test run --coverage
/f5-test-it api --database
/f5-gate complete G3
```

**Deliverables**:
- [ ] Data Integrity Report
- [ ] Performance Benchmarks
- [ ] Application Test Results

### Phase 5: Cutover

**Duration**: 1-2 days

**Objectives**:
- Execute production migration
- Monitor for issues
- Confirm rollback readiness

**Activities**:
```bash
/f5-deploy production --database
/f5-monitor database
```

**Deliverables**:
- [ ] Production Migration Complete
- [ ] Monitoring Dashboard Active
- [ ] Rollback Plan Verified

## Best Practices

1. **Always have rollback** - Never migrate without tested rollback scripts
2. **Staging first** - Always test migration in staging before production
3. **Data integrity checks** - Verify row counts, checksums, relationships
4. **Downtime planning** - Communicate maintenance windows clearly
