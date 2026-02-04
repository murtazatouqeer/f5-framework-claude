---
name: f5-quality-gates
description: F5 Framework quality gate definitions and requirements
category: core
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# F5 Quality Gates

## Design Gates (D1-D4)

### D1: Research Complete
**Purpose**: Verify all research and analysis is complete

**Required Checklist**:
- [ ] Market research documented
- [ ] Technology evaluation complete
- [ ] Stakeholder interviews conducted
- [ ] Feasibility study documented

**Approvers**: Tech Lead, Product Owner

### D2: SRS Approved
**Purpose**: Software Requirements Specification approved

**Required Checklist**:
- [ ] SRS document with all sections
- [ ] Use cases documented
- [ ] Requirements Traceability Matrix (RTM)
- [ ] Acceptance criteria defined
- [ ] Glossary complete

**Required Sections in SRS**:
1. Introduction
2. Overall Description
3. Functional Requirements
4. Non-Functional Requirements
5. External Interface Requirements
6. System Features

**Approvers**: Tech Lead, Product Owner, Customer

### D3: Basic Design Approved
**Purpose**: High-level architecture and design approved

**Required Checklist**:
- [ ] System architecture document
- [ ] Data model design
- [ ] API design
- [ ] Security design
- [ ] Technology stack finalized
- [ ] Integration design

**Required Diagrams**:
- System context diagram
- Container diagram
- Component diagram

**Approvers**: Architect, Tech Lead, Security Lead, Customer

### D4: Detail Design Approved
**Purpose**: Detailed design ready for implementation

**Required Checklist**:
- [ ] Module/component design
- [ ] Class/interface diagrams
- [ ] Database schema complete
- [ ] API contracts (OpenAPI)
- [ ] Error handling strategy
- [ ] Test strategy
- [ ] Coding standards

**Approvers**: Architect, Tech Lead, Dev Lead, Customer

## Implementation Gates (G2-G4)

### G2: Implementation Ready
**Purpose**: Code implementation meets quality standards

**Required Checklist**:
- [ ] Code implementation complete
- [ ] Unit tests written
- [ ] Code review completed
- [ ] Code documentation
- [ ] Requirements traceability

**Automated Checks**:
| Check | Threshold |
|-------|-----------|
| Lint errors | 0 |
| Type errors | 0 |
| Unit test pass rate | 100% |
| Code coverage (statements) | ≥80% |
| Code coverage (branches) | ≥75% |
| Security audit (critical/high) | 0 |

### G2.5: Verification Complete
**Purpose**: All verification checks passed before testing

**Required Checklist**:
- [ ] Asset verification (images, icons, fonts)
- [ ] Integration check (navigation, routes)
- [ ] Visual QA (matches design within 5% diff)
- [ ] Bug fixes complete

**Automated Checks**:
| Check | Threshold |
|-------|-----------|
| Asset verification | All exist |
| Visual regression | ≤5% diff |
| Open critical bugs | 0 |
| Open high bugs | 0 |

### G3: Testing Complete
**Purpose**: All testing completed with acceptable results

**Required Checklist**:
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] E2E tests passing
- [ ] Security tests passing
- [ ] Performance tests
- [ ] Regression tests
- [ ] Visual regression tests

**Automated Checks**:
| Check | Threshold |
|-------|-----------|
| All test pass rate | 100% |
| Code coverage | ≥80% |
| Security critical/high | 0 |
| Visual regression | ≤5% diff |

### G4: Deployment Ready
**Purpose**: Ready for production deployment

**Required Checklist**:
- [ ] Staging deployment successful
- [ ] UAT approved
- [ ] Release notes prepared
- [ ] Rollback plan documented
- [ ] Operations runbook
- [ ] Monitoring setup
- [ ] Backup strategy
- [ ] Security review complete

**Automated Checks**:
| Check | Threshold |
|-------|-----------|
| Staging health check | Pass |
| Staging smoke tests | 100% |
| DB migration check | Pass |
| Dependency vulnerabilities | 0 critical/high |
| Secrets detection | 0 leaks |

## Global Thresholds

```yaml
code_coverage: 80%
branch_coverage: 75%
function_coverage: 80%
complexity_max: 10
duplication_max: 5%
lint_errors: 0
type_errors: 0
security_critical: 0
security_high: 0
```

## Commands

```bash
# Check specific gate
/f5-gate check D1
/f5-gate check G2

# Show all gates status
/f5-gate status

# Generate evidence report
/f5-gate report G3
```
