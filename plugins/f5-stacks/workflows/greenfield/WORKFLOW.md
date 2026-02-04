# Greenfield Workflow

Workflow cho dự án mới hoàn toàn - xây dựng từ đầu với full process.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Project Type |
| **Duration** | 3-6 tháng |
| **Team Size** | 5-15 người |
| **Quality Gates** | Full (D1→D2→D3→D4→G2→G3→G4) |
| **Risk Level** | Medium-High |
| **Starting Point** | requirements |

## When to Use

### Ideal For

- Sản phẩm hoàn toàn mới
- Không có legacy constraints
- Full control over tech stack
- Long-term product vision
- Adequate timeline và budget

### Not Suitable For

- Quick prototypes → Use [POC](../poc/)
- MVP cần ship nhanh → Use [MVP](../mvp/)
- Adding features to existing → Use [Feature Development](../feature-development/)
- Budget/timeline constrained → Use [Startup Fast](../startup-fast/)

## Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                     GREENFIELD WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │ Phase 1 │───▶│ Phase 2 │───▶│ Phase 3 │───▶│ Phase 4 │     │
│  │Discovery│    │ Design  │    │  Build  │    │ Launch  │     │
│  │ D1→D2   │    │ D3→D4   │    │ G2→G3   │    │   G4    │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│                                                                 │
│  Duration:       Duration:      Duration:      Duration:        │
│  3-4 weeks       4-6 weeks      8-16 weeks     2-4 weeks        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: Discovery (D1→D2)

**Duration**: 3-4 weeks
**Gates**: D1 (Research Complete), D2 (SRS Approved)

**Objectives**:
- Thu thập và phân tích requirements
- Xác định scope và boundaries
- Research technical feasibility
- Create SRS document

**Activities**:
```bash
# 1. Initialize project
/f5:init my-project --workflow greenfield

# 2. Import requirements
/f5:import requirements.xlsx

# 3. Business analysis
/f5:ba analyze

# 4. Generate SRS
/f5:spec generate srs

# 5. Complete D1 gate
/f5:gate complete D1

# 6. Customer approval for D2
/f5:gate complete D2
```

**Deliverables**:
- [ ] Requirements Analysis Report
- [ ] SRS Document (SRS-v1.0.md)
- [ ] Use Case Diagrams
- [ ] Initial Project Plan
- [ ] Risk Assessment

**Quality Checklist**:
- [ ] All stakeholders interviewed
- [ ] Requirements are SMART
- [ ] No ambiguous requirements
- [ ] Acceptance criteria defined
- [ ] Customer sign-off on SRS

### Phase 2: Design (D3→D4)

**Duration**: 4-6 weeks
**Gates**: D3 (Basic Design), D4 (Detail Design)

**Objectives**:
- Architecture design
- Database design
- API design
- UI/UX design
- Security design

**Activities**:
```bash
# 1. Generate architecture design
/f5:design generate architecture

# 2. Database design
/f5:design generate database

# 3. API design
/f5:design generate api

# 4. Complete D3 (Basic Design)
/f5:gate complete D3

# 5. Detail design
/f5:design generate detail --all

# 6. Complete D4 (Detail Design)
/f5:gate complete D4
```

**Deliverables**:
- [ ] Architecture Document
- [ ] Database Design (ERD, DDL)
- [ ] API Specification (OpenAPI)
- [ ] UI Wireframes/Mockups
- [ ] Security Design Document
- [ ] Infrastructure Design

**Quality Checklist**:
- [ ] Architecture review passed
- [ ] Database normalized (3NF minimum)
- [ ] API follows REST conventions
- [ ] Security requirements addressed
- [ ] Performance requirements considered

### Phase 3: Build (G2→G3)

**Duration**: 8-16 weeks
**Gates**: G2 (Implementation Ready), G3 (Testing Complete)

**Objectives**:
- Implement all features
- Write comprehensive tests
- Code review và quality assurance
- Performance testing

**Activities**:
```bash
# 1. Sprint planning
/f5:implement plan sprint-1

# 2. Implementation with traceability
/f5:implement start REQ-001

# 3. Code review
/f5:review code

# 4. Complete G2
/f5:gate complete G2

# 5. Testing
/f5:test run --coverage

# 6. Complete G3
/f5:gate complete G3
```

**Deliverables**:
- [ ] Working Application
- [ ] Unit Tests (>80% coverage)
- [ ] Integration Tests
- [ ] E2E Tests
- [ ] API Documentation
- [ ] User Documentation

**Quality Checklist**:
- [ ] All requirements implemented
- [ ] Test coverage >= 80%
- [ ] No critical/high bugs
- [ ] Performance targets met
- [ ] Security scan passed
- [ ] Code review completed

### Phase 4: Launch (G4)

**Duration**: 2-4 weeks
**Gates**: G4 (Deployment Ready)

**Objectives**:
- Production deployment
- User training
- Monitoring setup
- Handover

**Activities**:
```bash
# 1. Pre-deployment checklist
/f5:deploy checklist

# 2. Staging deployment
/f5:deploy staging

# 3. UAT
/f5:test uat

# 4. Production deployment
/f5:deploy production

# 5. Complete G4
/f5:gate complete G4
```

**Deliverables**:
- [ ] Deployed Application
- [ ] Deployment Documentation
- [ ] Runbook
- [ ] Training Materials
- [ ] Support Handover Document

**Quality Checklist**:
- [ ] UAT passed
- [ ] Rollback tested
- [ ] Monitoring configured
- [ ] Alerts set up
- [ ] Documentation complete
- [ ] Team trained

## Team Roles

| Role | Responsibilities | Phase Focus |
|------|-----------------|-------------|
| Project Manager | Overall coordination | All phases |
| Business Analyst | Requirements | Phase 1, 2 |
| Architect | Technical design | Phase 2 |
| Tech Lead | Technical leadership | Phase 2, 3 |
| Developers | Implementation | Phase 3 |
| QA Engineer | Testing | Phase 3, 4 |
| DevOps | Infrastructure | Phase 3, 4 |

## Risk Management

### Common Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | High | Strict change control, clear SRS |
| Technical debt | Medium | Code review, refactoring sprints |
| Integration issues | Medium | Early integration, CI/CD |
| Performance issues | Medium | Performance testing, monitoring |
| Security vulnerabilities | High | Security review, pen testing |

### Risk Checkpoints

- **After D2**: Technical feasibility confirmed
- **After D4**: Design validated với team
- **Mid Phase 3**: Integration health check
- **Before G4**: Full security audit

## Customization Options

### Skip Options

```bash
# Skip POC phase (if concept is proven)
/f5:workflow greenfield --skip-poc

# Reduced documentation
/f5:workflow greenfield --docs minimal
```

### Extension Options

```bash
# Add security audit phase
/f5:workflow greenfield --add-phase security-audit

# Add performance testing phase
/f5:workflow greenfield --add-phase performance-testing
```

## Metrics & KPIs

### Progress Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Requirements coverage | 100% | Implemented/Total |
| Test coverage | >80% | Lines covered/Total |
| Bug density | <0.5/KLOC | Bugs/1000 lines |
| Technical debt | <2 days | Estimated remediation |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Code review coverage | 100% | PRs reviewed/Total |
| Security scan | Pass | No critical/high |
| Performance | <2s P95 | Response time |
| Availability | >99.9% | Uptime |

## Related Workflows

- **[POC](../poc/)**: Nếu cần validate concept trước
- **[MVP](../mvp/)**: Nếu cần ship nhanh hơn
- **[Enterprise](../enterprise/)**: Nếu scale lớn hơn

## Templates

- [Kickoff Meeting Template](./templates/kickoff-meeting.md)
- [Sprint Planning Template](./templates/sprint-planning.md)
- [Design Review Template](./templates/design-review.md)
- [Go-Live Checklist](./templates/go-live-checklist.md)

## Examples

- [E-Commerce Platform](./examples/e-commerce/)
- [SaaS Application](./examples/saas/)
- [Mobile App Backend](./examples/mobile-backend/)

---

# ═══════════════════════════════════════════════════════════════
# F5 FEATURE INTEGRATION
# ═══════════════════════════════════════════════════════════════

## Auto-Activated Features Per Phase

| Phase | Mode | Persona | Verbosity | Recommended Agents |
|-------|------|---------|-----------|-------------------|
| Discovery | 🔍 analytical | 📊 analyst | 4 | documenter |
| Design | 🏗️ planning | 🏛️ architect | 4 | api_designer, documenter |
| Build | 💻 coding | ⚙️ backend | 2 | code_generator, test_writer |
| Launch | 🚀 coding | 🔧 devops | 3 | security_scanner, documenter |

## Phase-Specific Commands

### Phase 1: Discovery (D1→D2)

**Essential:**
```bash
/f5-import requirements.xlsx     # Import requirements
/f5-ba analyze                   # Business analysis
/f5-spec generate srs            # Generate SRS
/f5-gate complete D1             # Complete D1
/f5-gate complete D2             # Complete D2 (customer approval)
```

**Recommended:**
```bash
/f5-mode set analytical          # Deep analysis mode
/f5-agent invoke documenter      # Documentation help
/f5-session checkpoint 'srs-approved'
```

### Phase 2: Design (D3→D4)

**Essential:**
```bash
/f5-design generate architecture # Architecture design
/f5-design generate database     # Database design
/f5-design generate api          # API design
/f5-gate complete D3             # Complete D3
/f5-gate complete D4             # Complete D4
```

**Recommended:**
```bash
/f5-persona architect            # Architecture focus
/f5-agent invoke api_designer    # API help
/f5-persona security             # Security review
/f5-session checkpoint 'design-approved'
```

### Phase 3: Build (G2→G3)

**Essential:**
```bash
/f5-implement start REQ-001      # Start implementation
/f5-tdd start feature            # TDD mode
/f5-test run --coverage          # Run tests
/f5-gate complete G2             # Complete G2
/f5-gate complete G3             # Complete G3
```

**Recommended:**
```bash
/f5-agent pipeline feature_development  # Full pipeline
/f5-review code                         # Code review
/f5-session checkpoint 'sprint-x'       # Per sprint
```

### Phase 4: Launch (G4)

**Essential:**
```bash
/f5-deploy staging               # Staging deployment
/f5-test uat                     # UAT
/f5-deploy production            # Production deployment
/f5-gate complete G4             # Complete G4
```

**Recommended:**
```bash
/f5-agent pipeline security_audit  # Final security
/f5-agent invoke documenter        # Release notes
```

## Agent Pipelines

| Phase | Recommended Pipeline |
|-------|---------------------|
| Discovery | - |
| Design | - |
| Build | `feature_development`, `code_quality` |
| Launch | `security_audit` |

## Checkpoints

Create checkpoints at:
- [ ] After SRS approval (D2)
- [ ] After design approval (D4)
- [ ] After each sprint (Build phase)
- [ ] Before production deploy (G4)

## Integration with Other F5 Features

### TDD Mode
- Recommended in: Build phase
- Start with: `/f5-tdd start feature`

### Code Review
- Required before: G2, G3 gates
- Run: `/f5-review code`

### Analytics
- Track progress: `/f5-analytics summary`
- Get insights: `/f5-analytics insights`

### Health Check
- Before gates: `/f5-selftest`
- Monitor: `/f5-status health`

## Greenfield-Specific Tips

### Full Quality Gates
- All 7 gates required (D1→D2→D3→D4→G2→G3→G4)
- Customer approval needed for D2, D3, D4

### When to Use Agents

| Task | Agent/Pipeline |
|------|---------------|
| SRS documentation | `documenter` |
| API design | `api_designer` |
| Feature development | `feature_development` pipeline |
| Security audit | `security_audit` pipeline |
| Code quality | `code_quality` pipeline |
