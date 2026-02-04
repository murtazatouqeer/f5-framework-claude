# Legacy Migration Workflow

Workflow cho migration hệ thống cũ - tạo SRS từ reverse engineering khi không có tài liệu.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Migration Type |
| **Duration** | 2-3 tháng |
| **Team Size** | 2-5 người |
| **Quality Gates** | D1→D2→D3→G2→G3 |
| **Risk Level** | High |
| **Starting Point** | legacy-system |

## When to Use

### Ideal For

- Migrating legacy systems without documentation
- Reverse engineering existing applications
- Creating SRS from running systems
- AS-IS to TO-BE transformation

### Not Suitable For

- Database-only migration → Use [Database Migration](../database-migration/)
- Platform change only → Use [Platform Migration](../platform-migration/)
- New system from scratch → Use [Greenfield](../greenfield/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                    LEGACY MIGRATION WORKFLOW                           │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │─▶│ Phase 5 │  │
│  │Discovery│  │Reverse  │  │Elicit   │  │AS-IS    │  │TO-BE    │  │
│  │         │  │Engineer │  │         │  │Document │  │Document │  │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘  │
│                                                                       │
│  ◀──── Can iterate back to any phase when gaps found ────▶           │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Discovery

**Duration**: 1-2 weeks

**Objectives**:
- Inventory all screens, modules, features
- Identify stakeholders
- Collect all available sources

**Activities**:
```bash
/f5-load
/f5-migrate inventory
/f5-ba stakeholders
```

**Deliverables**:
- [ ] System Inventory
- [ ] Stakeholder Map
- [ ] Screenshots
- [ ] Sources Inventory

### Phase 2: Reverse Engineering

**Duration**: 1-2 weeks

**Objectives**:
- Analyze database schema, APIs, and code
- Extract business rules from code
- Map user flows

**Activities**:
```bash
/f5-migrate db-analyze
/f5-migrate api-analyze
/f5-migrate code-analyze
/f5-migrate flow-map
```

**Deliverables**:
- [ ] Database Schema & ERD
- [ ] Data Dictionary
- [ ] API Inventory
- [ ] User Flow Maps
- [ ] Business Rules from Code

### Phase 3: Elicitation

**Duration**: 1-2 weeks

**Objectives**:
- Interview stakeholders
- Validate findings from reverse engineering
- Document edge cases

**Activities**:
```bash
/f5-migrate prepare-interview
/f5-ba elicit --interview
```

**Deliverables**:
- [ ] Interview Notes
- [ ] Validation Report

### Phase 4: AS-IS Documentation

**Duration**: 1 week

**Objectives**:
- Consolidate all information
- Create AS-IS SRS
- Stakeholder review

**Activities**:
```bash
/f5-migrate consolidate
/f5-migrate as-is --srs
/f5-gate complete D1
```

**Deliverables**:
- [ ] AS-IS SRS Document
- [ ] Stakeholder Sign-off

### Phase 5: TO-BE Documentation

**Duration**: 1-2 weeks

**Objectives**:
- Define changes from AS-IS
- Create TO-BE SRS
- Gap analysis and migration plan

**Activities**:
```bash
/f5-migrate changes
/f5-migrate to-be --srs
/f5-migrate gap-analysis
/f5-gate complete D2
```

**Deliverables**:
- [ ] TO-BE SRS
- [ ] Gap Analysis
- [ ] Migration Plan

## Best Practices

1. **Document everything** - Legacy systems have hidden business rules
2. **Stakeholder interviews** - Code doesn't capture all business logic
3. **Reversible approach** - Always maintain ability to rollback
4. **Iterative discovery** - Expect to revisit earlier phases
