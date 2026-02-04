# Legacy Migration Workflow

Workflow cho di chuyển từ hệ thống legacy sang hệ thống mới - sử dụng Strangler Fig Pattern.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Migration Type |
| **Duration** | 3-12 tháng |
| **Team Size** | 5-20 người |
| **Quality Gates** | Full + Migration Gates (M1→M4) |
| **Risk Level** | High |
| **Starting Point** | requirements |

## When to Use

### Ideal For

- Replacing old monolithic systems
- Modernizing outdated technology
- Migrating from on-premise to cloud
- Consolidating multiple legacy systems

### Prerequisites

- Legacy system documented (hoặc có người hiểu)
- Business continuity plan
- Rollback strategy
- Sufficient timeline (không rush)

## Strangler Fig Pattern

```
                    LEGACY SYSTEM
                    ┌─────────────────────────────────────┐
                    │                                     │
    Start:          │  ████████████████████████████████  │
                    │                                     │
                    └─────────────────────────────────────┘

                    STRANGLER FIG APPROACH
                    ┌─────────────────────────────────────┐
                    │  ████████     NEW SYSTEM            │
    Phase 1:        │  ████████     ░░░░░░░░░░░░         │
                    │  LEGACY                             │
                    └─────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
                    │  ████         NEW SYSTEM            │
    Phase 2:        │  ████         ░░░░░░░░░░░░░░░░░░   │
                    │  LEGACY                             │
                    └─────────────────────────────────────┘

                    ┌─────────────────────────────────────┐
    Complete:       │              NEW SYSTEM             │
                    │              ░░░░░░░░░░░░░░░░░░░░░░ │
                    └─────────────────────────────────────┘
```

## Migration Gates

Ngoài Quality Gates tiêu chuẩn, Legacy Migration có thêm:

| Gate | Name | Description |
|------|------|-------------|
| **M1** | Migration Planning Complete | Kế hoạch migration chi tiết |
| **M2** | Data Migration Validated | Dữ liệu đã migrate và verified |
| **M3** | Cutover Ready | Sẵn sàng chuyển đổi |
| **M4** | Rollback Tested | Đã test rollback procedure |

## Phases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LEGACY MIGRATION WORKFLOW                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │ Phase 1 │─▶│ Phase 2 │─▶│ Phase 3 │─▶│ Phase 4 │─▶│ Phase 5 │          │
│  │ Assess  │  │  Plan   │  │ Migrate │  │ Verify  │  │ Cutover │          │
│  │  D1     │  │ D2→M1   │  │ D3→G2   │  │ M2→G3   │  │ M3→M4   │          │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘          │
│                                                                             │
│  Duration:     Duration:    Duration:    Duration:    Duration:             │
│  2-4 weeks     3-6 weeks    3-9 months   2-4 weeks    1-2 weeks            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Assess (D1)

**Duration**: 2-4 weeks
**Gate**: D1 (Research Complete)

**Objectives**:
- Hiểu legacy system hiện tại
- Document architecture và data flows
- Identify pain points và risks
- Assess migration complexity

**Activities**:
```bash
# 1. Initialize migration project
/f5:init migration-project --workflow legacy-migration

# 2. Legacy system analysis
/f5:legacy analyze --deep

# 3. Document current state
/f5:doc architecture --source legacy

# 4. Risk assessment
/f5:risk assess migration

# 5. Complete D1
/f5:gate complete D1
```

**Legacy Analysis Checklist**:
- [ ] Technology stack documented
- [ ] Database schema extracted
- [ ] API/interface contracts documented
- [ ] Business rules identified
- [ ] Integration points mapped
- [ ] Data volumes measured
- [ ] Performance baselines captured

**Deliverables**:
- [ ] Legacy System Documentation
- [ ] Data Dictionary
- [ ] Integration Map
- [ ] Risk Assessment
- [ ] Complexity Score

### Phase 2: Plan (D2→M1)

**Duration**: 3-6 weeks
**Gates**: D2 (SRS Approved), M1 (Migration Planning Complete)

**Objectives**:
- Design target architecture
- Create migration strategy
- Plan data migration
- Define cutover approach

**Activities**:
```bash
# 1. Design target architecture
/f5:design generate target-architecture

# 2. Migration strategy
/f5:migration strategy --pattern strangler-fig

# 3. Data migration plan
/f5:migration data-plan

# 4. Cutover plan
/f5:migration cutover-plan

# 5. Complete D2
/f5:gate complete D2

# 6. Complete M1
/f5:gate complete M1
```

**Migration Strategy Options**:

| Strategy | Risk | Duration | Use When |
|----------|------|----------|----------|
| Big Bang | High | Short | Small system, can afford downtime |
| Parallel Run | Medium | Long | Critical system, need validation |
| Strangler Fig | Low | Long | Large system, continuous operation |
| Feature Toggle | Low | Medium | Gradual rollout needed |

**Deliverables**:
- [ ] Target Architecture Document
- [ ] Migration Strategy Document
- [ ] Data Migration Plan
- [ ] Cutover Plan
- [ ] Rollback Plan
- [ ] Communication Plan

### Phase 3: Migrate (D3→G2)

**Duration**: 3-9 months (iterative)
**Gates**: D3 (Basic Design), G2 (Implementation)

**Objectives**:
- Build new system incrementally
- Migrate functionality module by module
- Implement anti-corruption layer
- Migrate data in phases

**Activities**:
```bash
# For each module:

# 1. Design module
/f5:design generate module-X

# 2. Build new implementation
/f5:implement module-X

# 3. Create anti-corruption layer
/f5:implement acl module-X

# 4. Data migration for module
/f5:migration data module-X

# 5. Route traffic
/f5:migration route module-X --percentage 10

# 6. Gradually increase traffic
/f5:migration route module-X --percentage 50
/f5:migration route module-X --percentage 100

# 7. Decommission legacy module
/f5:legacy decommission module-X
```

**Anti-Corruption Layer (ACL)**:
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   New System  ←→  [ACL]  ←→  Legacy System                 │
│                                                             │
│   - Translates data formats                                │
│   - Adapts APIs                                            │
│   - Handles protocol differences                           │
│   - Isolates legacy complexity                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Deliverables**:
- [ ] New System Modules
- [ ] Anti-Corruption Layer
- [ ] Data Migration Scripts
- [ ] Traffic Routing Config
- [ ] Module-by-Module Sign-off

### Phase 4: Verify (M2→G3)

**Duration**: 2-4 weeks
**Gates**: M2 (Data Migration Validated), G3 (Testing Complete)

**Objectives**:
- Validate data migration accuracy
- Comprehensive testing
- Performance validation
- User acceptance testing

**Activities**:
```bash
# 1. Data validation
/f5:migration validate-data --comprehensive

# 2. Functional testing
/f5:test run --full

# 3. Performance testing
/f5:test performance --compare-legacy

# 4. UAT
/f5:test uat

# 5. Complete M2
/f5:gate complete M2

# 6. Complete G3
/f5:gate complete G3
```

**Data Validation Checklist**:
- [ ] Record counts match
- [ ] Data integrity verified
- [ ] Business rules validated
- [ ] Edge cases tested
- [ ] Historical data preserved

**Deliverables**:
- [ ] Data Validation Report
- [ ] Test Results
- [ ] Performance Comparison
- [ ] UAT Sign-off

### Phase 5: Cutover (M3→M4→G4)

**Duration**: 1-2 weeks
**Gates**: M3 (Cutover Ready), M4 (Rollback Tested), G4 (Deployment Ready)

**Objectives**:
- Final cutover to new system
- Decommission legacy
- Monitor và stabilize
- Knowledge transfer

**Activities**:
```bash
# 1. Pre-cutover checklist
/f5:migration cutover-checklist

# 2. Rollback drill
/f5:migration rollback-test

# 3. Complete M3
/f5:gate complete M3

# 4. Complete M4
/f5:gate complete M4

# 5. Execute cutover
/f5:migration cutover --execute

# 6. Monitor
/f5:monitor intensive --duration 72h

# 7. Decommission legacy
/f5:legacy decommission --final

# 8. Complete G4
/f5:gate complete G4
```

**Cutover Checklist**:
- [ ] All stakeholders notified
- [ ] Rollback procedure ready
- [ ] Support team on standby
- [ ] Monitoring enhanced
- [ ] Communication plan active

**Deliverables**:
- [ ] Cutover Report
- [ ] Rollback Test Results
- [ ] Go-Live Sign-off
- [ ] Legacy Decommission Plan
- [ ] Handover Documentation

## Risk Management

### High-Risk Areas

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss | Critical | Multiple backups, validation |
| Business disruption | High | Parallel run, rollback plan |
| Integration failures | High | Thorough testing, ACL |
| Performance degradation | Medium | Performance testing |
| Knowledge gap | Medium | Documentation, training |

### Risk Checkpoints

- **After Phase 1**: Go/No-Go based on complexity
- **Each module migration**: Validate before proceeding
- **Before cutover**: Full dress rehearsal
- **After cutover**: Intensive monitoring period

## Data Migration

### Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                   DATA MIGRATION APPROACH                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Historical Data (Batch)                                 │
│     └── One-time migration before cutover                  │
│                                                             │
│  2. Transactional Data (CDC)                               │
│     └── Change Data Capture for continuous sync            │
│                                                             │
│  3. Reference Data                                          │
│     └── Migrate early, validate thoroughly                 │
│                                                             │
│  4. Configuration Data                                      │
│     └── Transform and load carefully                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Validation Rules

```yaml
data_validation:
  counts:
    - source_table: users
      target_table: users
      tolerance: 0

  integrity:
    - check: foreign_keys
      action: fail_on_error

  business_rules:
    - rule: "total_orders = sum(order_lines)"
      tolerance: 0.01%
```

## Rollback Strategy

### Rollback Levels

| Level | Scope | Time to Rollback |
|-------|-------|------------------|
| L1 | Single module | Minutes |
| L2 | Multiple modules | Hours |
| L3 | Full system | 4-8 hours |

### Rollback Triggers

- Data corruption detected
- Critical functionality broken
- Performance severely degraded
- Security vulnerability discovered

### Rollback Procedure

```bash
# 1. Announce rollback
/f5:migration announce-rollback

# 2. Stop traffic to new system
/f5:migration route --to legacy

# 3. Sync data back to legacy
/f5:migration sync-back

# 4. Verify legacy operational
/f5:legacy verify

# 5. Post-mortem
/f5:doc post-mortem
```

## Team Structure

| Role | Responsibilities | Allocation |
|------|-----------------|------------|
| Migration Lead | Overall coordination | Full-time |
| Legacy Expert | Legacy system knowledge | Full-time |
| Architect | Target system design | Full-time |
| Data Engineer | Data migration | Full-time |
| QA Lead | Testing strategy | Full-time |
| DevOps | Infrastructure | Part-time |
| Business Analyst | Requirements | Part-time |

## Best Practices

### 1. Document Everything

- Legacy systems often have undocumented behavior
- Capture tribal knowledge
- Document edge cases

### 2. Incremental Migration

- Never big bang (trừ hệ thống nhỏ)
- Module by module
- Validate at each step

### 3. Parallel Operation

- Run both systems simultaneously
- Compare results
- Build confidence before cutover

### 4. Extensive Testing

- More testing than normal projects
- Include data validation
- Performance comparison

### 5. Communication

- Stakeholders need frequent updates
- Clear escalation paths
- Transparent about risks

## Templates

- [Legacy Assessment Template](./templates/legacy-assessment.md)
- [Migration Strategy Template](./templates/migration-strategy.md)
- [Data Migration Plan](./templates/data-migration-plan.md)
- [Cutover Runbook](./templates/cutover-runbook.md)
- [Rollback Procedure](./templates/rollback-procedure.md)

## Examples

- [Mainframe to Cloud Migration](./examples/mainframe-to-cloud/)
- [Monolith to Microservices](./examples/monolith-to-microservices/)
- [Oracle to PostgreSQL](./examples/oracle-to-postgresql/)

---

# ═══════════════════════════════════════════════════════════════
# F5 FEATURE INTEGRATION
# ═══════════════════════════════════════════════════════════════

## Auto-Activated Features Per Phase

| Phase | Mode | Persona | Verbosity | Recommended Agents |
|-------|------|---------|-----------|-------------------|
| Assess | 🔍 analytical | 📊 analyst | 4 | documenter |
| Plan | 🏗️ planning | 🏛️ architect | 4 | api_designer, documenter |
| Migrate | 💻 coding | ⚙️ backend | 2 | code_generator |
| Verify | 🔬 debugging | 🧪 qa | 3 | test_writer |
| Cutover | 🚀 coding | 🔧 devops | 3 | security_scanner |

## Phase-Specific Commands

### Phase 1: Assess (D1)

**Essential:**
```bash
/f5-load                         # Load project context
/f5-legacy analyze --deep        # Analyze legacy system
/f5-risk assess migration        # Risk assessment
/f5-gate complete D1             # Complete D1
```

**Recommended:**
```bash
/f5-mode set analytical          # Deep analysis mode
/f5-agent invoke documenter      # Document findings
/f5-session checkpoint 'assessment-complete'
```

### Phase 2: Plan (D2→M1)

**Essential:**
```bash
/f5-design generate target-architecture
/f5-migration strategy --pattern strangler-fig
/f5-migration data-plan          # Data migration plan
/f5-gate complete D2             # Complete D2
/f5-gate complete M1             # Complete M1
```

**Recommended:**
```bash
/f5-persona architect            # Architecture focus
/f5-agent invoke api_designer    # API design help
/f5-session checkpoint 'plan-approved'
```

### Phase 3: Migrate (D3→G2)

**Essential:**
```bash
/f5-implement module-X           # Implement new system
/f5-implement acl module-X       # Anti-corruption layer
/f5-migration route module-X --percentage 10
/f5-gate complete D3             # Complete D3
/f5-gate complete G2             # Complete G2
```

**Recommended:**
```bash
/f5-mode set coding              # Fast implementation
/f5-tdd start migration-module   # TDD for migration
/f5-session checkpoint 'module-X-migrated'
```

### Phase 4: Verify (M2→G3)

**Essential:**
```bash
/f5-migration validate-data --comprehensive
/f5-test run --full              # Full test suite
/f5-test performance --compare-legacy
/f5-gate complete M2             # Complete M2
/f5-gate complete G3             # Complete G3
```

**Recommended:**
```bash
/f5-mode set debugging           # Debug mode
/f5-agent invoke test_writer     # Generate tests
```

### Phase 5: Cutover (M3→M4→G4)

**Essential:**
```bash
/f5-migration rollback-test      # Test rollback
/f5-gate complete M3             # Complete M3
/f5-gate complete M4             # Complete M4
/f5-migration cutover --execute  # Execute cutover
/f5-gate complete G4             # Complete G4
```

**Recommended:**
```bash
/f5-agent pipeline security_audit  # Security check
/f5-monitor intensive --duration 72h
```

## Agent Pipelines

| Phase | Recommended Pipeline |
|-------|---------------------|
| Assess | - |
| Plan | - |
| Migrate | `feature_development` |
| Verify | - |
| Cutover | `security_audit` |

## Checkpoints

Create checkpoints at:
- [ ] After legacy assessment (Assess)
- [ ] After migration plan approved (Plan)
- [ ] After each module migrated (Migrate)
- [ ] After data validation (Verify)
- [ ] After rollback tested (Cutover)

## Integration with Other F5 Features

### TDD Mode
- Recommended in: Migrate phase
- Start with: `/f5-tdd start migration-test`

### Code Review
- Required before: G2 gate
- Run: `/f5-review code`

### Analytics
- Track progress: `/f5-analytics summary`
- View migration metrics: `/f5-analytics --dashboard migration`

### Health Check
- Before gates: `/f5-selftest`
- Monitor: `/f5-status health`

## Legacy Migration-Specific Tips

### Migration Gates (M1-M4)
- M1: Migration planning complete
- M2: Data migration validated
- M3: Cutover ready
- M4: Rollback tested

### Strangler Fig Pattern
- Migrate module by module
- Use Anti-Corruption Layer (ACL)
- Gradually route traffic to new system

### When to Use Agents

| Task | Agent/Pipeline |
|------|---------------|
| Legacy documentation | `documenter` |
| API design for new system | `api_designer` |
| Module implementation | `feature_development` pipeline |
| Data validation | `test_writer` |
| Security audit pre-cutover | `security_audit` pipeline |

### Risk Management Checkpoints
- After Phase 1: Go/No-Go decision
- Each module: Validate before proceeding
- Before cutover: Full dress rehearsal
