# Enterprise Application Workflow

Workflow cho enterprise application development - full-scale với tất cả quality gates.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Project Type |
| **Duration** | 3-12 tháng |
| **Team Size** | 5-20 người |
| **Quality Gates** | D1→D2→D3→D4→G2→G2.5→G3→G4 |
| **Risk Level** | High |
| **Starting Point** | business-requirements |

## When to Use

### Ideal For

- Large-scale enterprise applications
- Compliance-critical systems (finance, healthcare)
- Multi-team, multi-module projects
- Systems requiring full audit trail
- Projects with strict SLA requirements

### Not Suitable For

- Quick prototypes → Use [POC](../poc/)
- Startups → Use [MVP](../mvp/) or [Startup Fast](../startup-fast/)
- Simple features → Use [Feature Development](../feature-development/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                    ENTERPRISE APPLICATION WORKFLOW                     │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│  │ D1   │▶│ D2   │▶│ D3   │▶│ D4   │▶│ G2   │▶│ G3   │▶│ G4   │   │
│  │Rsrch │ │ SRS  │ │Basic │ │Detail│ │Impl  │ │Test  │ │Deploy│   │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
│                                        │G2.5│                        │
│                                        │Rvw │                        │
│                                        └────┘                        │
│                                                                       │
│  ALL gates mandatory - No shortcuts allowed                           │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Research & Discovery (D1)

**Duration**: 2-4 weeks

**Objectives**:
- Complete market and technical research
- Define business requirements
- Stakeholder analysis

**Activities**:
```bash
/f5-load
/f5-research deep --scope enterprise
/f5-ba analyze-enterprise
/f5-gate complete D1
```

### Phase 2: SRS Approval (D2)

**Duration**: 2-3 weeks

**Objectives**:
- Create comprehensive SRS
- Stakeholder review and approval
- Requirement baseline

**Activities**:
```bash
/f5-spec generate --type srs
/f5-review spec
/f5-gate complete D2
```

### Phase 3: Basic Design (D3)

**Duration**: 1-2 weeks

**Objectives**:
- System architecture design
- API contracts
- Database design

**Activities**:
```bash
/f5-design generate architecture
/f5-design generate api
/f5-design generate database
/f5-gate complete D3
```

### Phase 4: Detail Design (D4)

**Duration**: 2-3 weeks

**Objectives**:
- Detailed component design
- Interface specifications
- Security architecture

**Activities**:
```bash
/f5-design generate detail-design
/f5-design generate security-architecture
/f5-gate complete D4
```

### Phase 5: Implementation (G2→G2.5)

**Duration**: 2-6 months

**Objectives**:
- Implement all modules
- Code review for every PR
- Traceability maintained

**Activities**:
```bash
/f5-implement start REQ-001
/f5-review code
/f5-verify --gate
/f5-gate complete G2
/f5-gate complete G2.5
```

### Phase 6: Testing (G3)

**Duration**: 2-4 weeks

**Objectives**:
- Comprehensive testing (unit, integration, E2E)
- Performance and security testing
- UAT sign-off

**Activities**:
```bash
/f5-test run --coverage
/f5-test-e2e full
/f5-test-it api --all
/f5-gate complete G3
```

### Phase 7: Deployment (G4)

**Duration**: 1-2 weeks

**Objectives**:
- Production deployment
- Monitoring setup
- Documentation complete

**Activities**:
```bash
/f5-deploy staging && /f5-deploy production
/f5-gate complete G4
```

## Best Practices

1. **All gates mandatory** - No gate can be skipped in enterprise workflow
2. **Traceability** - Every line of code traces to a requirement
3. **Code review required** - G2.5 gate ensures all code is reviewed
4. **Security first** - Security architecture in D4, security testing in G3
5. **Compliance** - Maintain full audit trail for regulatory needs
