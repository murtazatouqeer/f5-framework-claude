# MVP (Minimum Viable Product) Workflow

Workflow cho MVP - ship nhanh product có giá trị với minimum features.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Project Type |
| **Duration** | 1-3 tháng |
| **Team Size** | 2-5 người |
| **Quality Gates** | Essential (D1→D3→G2→G3) |
| **Risk Level** | Medium |
| **Starting Point** | requirements |

## When to Use

### Ideal For

- Validate market fit
- Launch quickly to get feedback
- Startup/new product
- Limited budget/resources
- Test business hypothesis

### Not Suitable For

- Enterprise applications → Use [Greenfield](../greenfield/)
- Just proving technical concept → Use [POC](../poc/)
- Adding to existing product → Use [Feature Development](../feature-development/)

## MVP Philosophy

```
                    ┌─────────────────────────────────┐
                    │      MVP = Minimum VIABLE       │
                    │                                 │
                    │   ✓ Solves real problem         │
                    │   ✓ Works end-to-end            │
                    │   ✓ Good enough quality         │
                    │   ✓ Can get real feedback       │
                    │                                 │
                    │   ✗ Not feature-complete        │
                    │   ✗ Not perfectly polished      │
                    │   ✗ Not fully scalable          │
                    └─────────────────────────────────┘
```

## Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                       MVP WORKFLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │ Phase 1 │───▶│ Phase 2 │───▶│ Phase 3 │───▶│ Phase 4 │     │
│  │ Define  │    │ Design  │    │  Build  │    │ Launch  │     │
│  │ D1→D3   │    │   D3    │    │ G2→G3   │    │    -    │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│                                                                 │
│  Duration:       Duration:      Duration:      Duration:        │
│  1-2 weeks       1-2 weeks      4-8 weeks      1 week           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: Define (D1→D3)

**Duration**: 1-2 weeks
**Gates**: D1 (Research), D3 (Basic Design)

**Objectives**:
- Identify core value proposition
- Define MVP scope (ruthless prioritization)
- Create lean specifications
- Identify target users

**Activities**:
```bash
# 1. Initialize MVP
/f5:init my-mvp --workflow mvp

# 2. Define value proposition
/f5:ba value-proposition

# 3. Prioritize features (MoSCoW)
/f5:ba prioritize --method moscow

# 4. MVP scope definition
/f5:spec generate mvp-scope

# 5. Complete D1
/f5:gate complete D1
```

**MVP Scope Framework (MoSCoW)**:
```markdown
## Must Have (Core MVP)
- Feature 1 - Why: [business reason]
- Feature 2 - Why: [business reason]

## Should Have (If time permits)
- Feature 3
- Feature 4

## Could Have (Nice to have)
- Feature 5
- Feature 6

## Won't Have (Explicitly out of scope)
- Feature 7
- Feature 8
```

**Deliverables**:
- [ ] Value Proposition Canvas
- [ ] MVP Scope Document (MoSCoW)
- [ ] User Personas (simplified)
- [ ] Success Metrics

### Phase 2: Design (D3)

**Duration**: 1-2 weeks
**Gate**: D3 (Basic Design)

**Objectives**:
- Simple architecture
- Core user flows
- Basic UI design
- Data model

**Activities**:
```bash
# 1. Architecture (keep simple)
/f5:design generate architecture --minimal

# 2. User flows
/f5:design generate user-flows

# 3. Basic UI wireframes
/f5:design generate wireframes --low-fidelity

# 4. Data model
/f5:design generate database --essential

# 5. Complete D3
/f5:gate complete D3
```

**MVP Architecture Principles**:
- **Monolith first**: Don't over-engineer with microservices
- **Use managed services**: Don't build what you can buy
- **Standard stack**: Don't experiment with tech in MVP
- **Scale later**: Optimize when you have users

**Deliverables**:
- [ ] Simple Architecture Diagram
- [ ] Core User Flows
- [ ] Low-fidelity Wireframes
- [ ] Essential Data Model
- [ ] API Endpoints List

### Phase 3: Build (G2→G3)

**Duration**: 4-8 weeks
**Gates**: G2 (Implementation), G3 (Testing)

**Objectives**:
- Implement Must Have features
- Basic testing
- Core functionality working
- Ready for real users

**Activities**:
```bash
# 1. Setup development environment
/f5:implement setup

# 2. Implement in iterations
/f5:implement sprint --duration 1week

# 3. Daily deployments to staging
/f5:deploy staging

# 4. Complete G2
/f5:gate complete G2

# 5. Basic testing
/f5:test run --essential

# 6. Complete G3
/f5:gate complete G3
```

**MVP Development Guidelines**:
- **Ship daily**: Deploy to staging every day
- **Test core paths**: Focus testing on happy paths
- **Technical debt OK**: Document but don't fix non-critical debt
- **Feedback loops**: Get user feedback early và often

**Deliverables**:
- [ ] Working MVP Application
- [ ] Core Features Implemented
- [ ] Basic Tests (critical paths)
- [ ] Deployment Pipeline

### Phase 4: Launch

**Duration**: 1 week

**Objectives**:
- Soft launch to early users
- Collect feedback
- Monitor và fix critical issues
- Plan iteration

**Activities**:
```bash
# 1. Pre-launch checklist
/f5:deploy checklist --mvp

# 2. Soft launch
/f5:deploy production --soft-launch

# 3. Monitor
/f5:monitor setup --basic

# 4. Collect feedback
/f5:feedback collect
```

**Soft Launch Strategy**:
```
Week 1: Internal team only
Week 2: Friends & family (50 users)
Week 3: Early adopters (200 users)
Week 4: Wider release
```

**Deliverables**:
- [ ] Live MVP
- [ ] Basic Monitoring
- [ ] Feedback Collection System
- [ ] Iteration Plan

## Feature Prioritization

### MoSCoW Method

| Priority | Definition | % of Features |
|----------|------------|---------------|
| **Must** | MVP won't work without it | 20-30% |
| **Should** | Important but not critical | 20-30% |
| **Could** | Nice to have | 20-30% |
| **Won't** | Explicitly excluded | 20-30% |

### Value vs Effort Matrix

```
        High Value
            │
   Quick    │   Major
   Wins     │   Projects
   (DO NOW) │   (PLAN)
────────────┼────────────
   Fill     │   Don't
   Ins      │   Do
   (LATER)  │   (AVOID)
            │
        Low Value
    Low ←───┼───→ High
          Effort
```

## MVP Quality Standards

### What's Required

- [ ] Core features work end-to-end
- [ ] No data loss scenarios
- [ ] Basic security (auth, input validation)
- [ ] Works on target devices/browsers
- [ ] Can handle initial users (10-100)

### What's Optional

- [ ] Edge case handling
- [ ] Performance optimization
- [ ] Comprehensive error messages
- [ ] Advanced features
- [ ] Polish và animations

## Success Metrics

### Business Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| User signups | X users | Analytics |
| Activation rate | X% | Users completing core action |
| Retention | X% week 1 | Users returning |
| NPS | >0 | Survey |

### Technical Metrics

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Uptime | >95% | Monitoring |
| Core flow success | >90% | Analytics |
| Page load | <5s | RUM |
| Error rate | <5% | Error tracking |

## Post-MVP Paths

### MVP → Growth

```bash
# MVP successful, iterate and grow
/f5:workflow transition mvp growth

# Focus: Add Should Have features, improve quality
```

### MVP → Greenfield

```bash
# MVP validated, rebuild properly
/f5:init production --workflow greenfield --from-mvp ./mvp-project

# Focus: Proper architecture, full quality gates
```

### MVP → Pivot

```bash
# MVP shows different opportunity
/f5:ba pivot-analysis

# Focus: Redefine value proposition, new MVP
```

## Common Mistakes

### Over-scoping

❌ **Problem**: Too many "Must Have" features
✅ **Solution**: Ruthless prioritization, limit Must Have to 3-5 features

### Premature Optimization

❌ **Problem**: Building for scale before product-market fit
✅ **Solution**: Monolith first, scale when needed

### Perfectionism

❌ **Problem**: Polishing before validating
✅ **Solution**: Ship ugly but functional, iterate based on feedback

### No Metrics

❌ **Problem**: Launching without way to measure success
✅ **Solution**: Define success metrics upfront, implement basic analytics

## Best Practices

### 1. Ruthless Scope Management

- Cut features, not corners
- Every feature must justify its existence
- "No" is the default answer

### 2. Continuous Deployment

- Deploy daily to staging
- Get feedback early
- Fix forward, not backward

### 3. User Feedback Loops

- Talk to users weekly
- Watch users use the product
- Measure behavior, not just opinions

### 4. Technical Debt Management

- Document all shortcuts
- Accept debt consciously
- Plan cleanup in future sprints

## Templates

- [MVP Canvas](./templates/mvp-canvas.md)
- [Feature Prioritization](./templates/feature-prioritization.md)
- [Launch Checklist](./templates/launch-checklist.md)
- [Feedback Form](./templates/feedback-form.md)

## Examples

- [SaaS MVP](./examples/saas-mvp/)
- [Mobile App MVP](./examples/mobile-mvp/)
- [Marketplace MVP](./examples/marketplace-mvp/)

---

# ═══════════════════════════════════════════════════════════════
# F5 FEATURE INTEGRATION
# ═══════════════════════════════════════════════════════════════

## Auto-Activated Features Per Phase

| Phase | Mode | Persona | Verbosity | Recommended Agents |
|-------|------|---------|-----------|-------------------|
| Define | 🔍 analytical | 📊 analyst | 4 | documenter |
| Design | 🏗️ planning | 🏛️ architect | 4 | api_designer |
| Build | 💻 coding | ⚙️ backend | 2 | code_generator, test_writer |
| Launch | 🚀 coding | 🔧 devops | 3 | security_scanner |

## Phase-Specific Commands

### Phase 1: Define (D1→D3)

**Essential:**
```bash
/f5-ba value-proposition       # Define value prop
/f5-ba prioritize --moscow     # Prioritize features
/f5-spec generate mvp-scope    # MVP scope doc
/f5-gate complete D1           # Complete D1
```

**Recommended:**
```bash
/f5-mode set analytical        # Deep analysis
/f5-session checkpoint 'scope-defined'
```

### Phase 2: Design (D3)

**Essential:**
```bash
/f5-design generate --minimal  # Simple architecture
/f5-design api                 # API endpoints
/f5-gate check D3              # Verify D3
```

**Recommended:**
```bash
/f5-agent invoke api_designer  # API help
/f5-persona architect          # Architecture focus
```

### Phase 3: Build (G2→G3)

**Essential:**
```bash
/f5-implement feature --tdd    # TDD implementation
/f5-test run --coverage        # Run tests
/f5-gate check G2              # Verify G2
```

**Recommended:**
```bash
/f5-agent pipeline feature_development  # Full pipeline
/f5-review quick                        # Before commit
/f5-session checkpoint 'feature-x'      # Save progress
```

### Phase 4: Launch

**Essential:**
```bash
/f5-deploy staging             # Test deployment
/f5-deploy production          # Go live
/f5-agent invoke security_scanner  # Final security
```

## Agent Pipelines

| Phase | Recommended Pipeline |
|-------|---------------------|
| Build | `feature_development` |
| Build (bugs) | `bug_fix` |
| Launch | `security_audit` |

## Checkpoints

Create checkpoints at:
- [ ] After scope defined (Define phase)
- [ ] After API design (Design phase)
- [ ] After each major feature (Build phase)
- [ ] Before production deploy (Launch phase)

## Integration with Other F5 Features

### TDD Mode
- Recommended in: Build phase
- Start with: `/f5-tdd start feature-name`

### Code Review
- Required before: G2 gate
- Run: `/f5-review quick`

### Analytics
- Track progress: `/f5-analytics summary`
- Get insights: `/f5-analytics insights`

### Health Check
- Before gates: `/f5-selftest`
- Monitor: `/f5-status health`

## MVP-Specific Tips

### Speed vs Quality
- Use **verbosity 2** for faster coding
- Skip D2, D4 gates (MVP doesn't need full specs)
- Focus tests on **happy paths only**

### When to Use Agents

| Task | Agent/Pipeline |
|------|---------------|
| Generating boilerplate | `code_generator` |
| Writing tests | `test_writer` |
| Before launch | `security_audit` pipeline |
