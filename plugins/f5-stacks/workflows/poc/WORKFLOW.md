# POC (Proof of Concept) Workflow

Workflow cho Proof of Concept - validate concept nhanh với minimal investment.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Project Type |
| **Duration** | 2-4 tuần |
| **Team Size** | 1-3 người |
| **Quality Gates** | Minimal (D1→G2) |
| **Risk Level** | Low |
| **Starting Point** | requirements |

## When to Use

### Ideal For

- Validate technical feasibility
- Test new technology/framework
- Prove concept to stakeholders
- Explore solution approaches
- Quick demonstration

### Not Suitable For

- Production-ready code
- Full feature implementation
- Long-term maintainability
- Customer-facing delivery

## POC vs MVP vs Prototype

| Aspect | POC | Prototype | MVP |
|--------|-----|-----------|-----|
| Goal | Technical feasibility | User experience | Market validation |
| Audience | Technical team | Stakeholders, Users | Real customers |
| Quality | Throwaway code | Visual polish | Production-ready |
| Duration | 1-2 weeks | 2-4 weeks | 1-3 months |

## Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                       POC WORKFLOW                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │ Phase 1 │───▶│ Phase 2 │───▶│ Phase 3 │───▶│ Phase 4 │     │
│  │ Define  │    │  Build  │    │  Demo   │    │ Decide  │     │
│  │   D1    │    │   G2    │    │    -    │    │    -    │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│                                                                 │
│  Duration:       Duration:      Duration:      Duration:        │
│  2-3 days        1-2 weeks      1 day          1 day            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: Define (D1)

**Duration**: 2-3 days
**Gate**: D1 (Research Complete)

**Objectives**:
- Xác định hypothesis cần validate
- Define success criteria
- Identify key technical challenges
- Plan POC scope

**Activities**:
```bash
# 1. Initialize POC
/f5:init my-poc --workflow poc

# 2. Define hypothesis
/f5:ba define-hypothesis

# 3. Complete D1
/f5:gate complete D1
```

**Deliverables**:
- [ ] POC Definition Document
- [ ] Success Criteria
- [ ] Technical Challenges List
- [ ] Time-boxed Plan

**POC Definition Template**:
```markdown
# POC: [Name]

## Hypothesis
We believe that [technical approach] can [achieve goal].

## Success Criteria
1. [ ] Criterion 1 (measurable)
2. [ ] Criterion 2 (measurable)
3. [ ] Criterion 3 (measurable)

## Technical Challenges
1. Challenge 1 - Risk: High/Medium/Low
2. Challenge 2 - Risk: High/Medium/Low

## Time Box
- Start: [date]
- End: [date]
- Max Duration: [X days]

## Resources
- Team: [names]
- Budget: [if any]
```

### Phase 2: Build (G2)

**Duration**: 1-2 weeks
**Gate**: G2 (Implementation Ready)

**Objectives**:
- Implement core concept
- Focus on key technical challenges
- Minimal UI (if needed)
- Gather learnings

**Activities**:
```bash
# 1. Setup minimal environment
/f5:implement setup --minimal

# 2. Implement core concept
/f5:implement start --poc-mode

# 3. Document findings
/f5:doc findings

# 4. Complete G2
/f5:gate complete G2
```

**POC Coding Guidelines**:
- **DO**: Focus on core concept validation
- **DO**: Document learnings as you go
- **DO**: Time-box ruthlessly
- **DON'T**: Write production-quality code
- **DON'T**: Add nice-to-have features
- **DON'T**: Spend time on UI polish
- **DON'T**: Write comprehensive tests

**Deliverables**:
- [ ] Working POC Code
- [ ] Technical Findings Document
- [ ] Performance Measurements (if relevant)
- [ ] Integration Notes (if relevant)

### Phase 3: Demo

**Duration**: 1 day

**Objectives**:
- Demonstrate POC to stakeholders
- Show technical feasibility
- Present findings và limitations
- Gather feedback

**Demo Structure**:
```markdown
# POC Demo Agenda

1. **Context** (5 min)
   - Why this POC?
   - What we're trying to prove

2. **Demo** (15-20 min)
   - Live demonstration
   - Key technical highlights
   - Limitations shown honestly

3. **Findings** (10 min)
   - What we learned
   - Technical challenges faced
   - Performance/scalability observations

4. **Recommendation** (5 min)
   - Go / No-Go / Pivot
   - Next steps if Go

5. **Q&A** (10 min)
```

### Phase 4: Decide

**Duration**: 1 day

**Objectives**:
- Analyze POC results
- Make Go/No-Go decision
- Plan next steps
- Archive learnings

**Decision Matrix**:
```
Success Criteria Met?
├── All criteria met → GO to MVP/Greenfield
├── Partial criteria met
│   ├── Critical criteria met → GO with adjustments
│   └── Critical criteria not met → PIVOT or NO-GO
└── No criteria met → NO-GO
```

**Deliverables**:
- [ ] POC Results Document
- [ ] Decision (Go/No-Go/Pivot)
- [ ] Lessons Learned
- [ ] Recommendations for next phase

## Success Criteria Framework

### Technical Criteria

| Criterion | Target | How to Measure |
|-----------|--------|----------------|
| Performance | <X ms response | Load testing |
| Scalability | Handle X users | Stress testing |
| Integration | Works with Y | Integration test |
| Feasibility | Can be built | Working code |

### Business Criteria

| Criterion | Target | How to Measure |
|-----------|--------|----------------|
| Cost estimate | Within budget | Development estimate |
| Timeline | Can ship in X | Team assessment |
| Risk | Acceptable | Risk analysis |

## Common POC Types

### 1. Technology Evaluation

```bash
/f5:init tech-poc --workflow poc --type technology-evaluation

# Evaluate new framework/library
# Compare alternatives
# Benchmark performance
```

### 2. Integration POC

```bash
/f5:init integration-poc --workflow poc --type integration

# Test third-party integration
# Verify API compatibility
# Check data flow
```

### 3. Performance POC

```bash
/f5:init perf-poc --workflow poc --type performance

# Test performance hypothesis
# Benchmark different approaches
# Identify bottlenecks
```

### 4. Architecture POC

```bash
/f5:init arch-poc --workflow poc --type architecture

# Validate architecture decisions
# Test distributed systems
# Verify scalability approach
```

## Best Practices

### Time Management

- **Time-box strictly**: Set hard deadline và stick to it
- **Daily check-ins**: Track progress against deadline
- **Cut scope, not time**: If falling behind, reduce scope

### Documentation

- **Document as you go**: Don't leave to end
- **Focus on learnings**: What worked, what didn't
- **Be honest about limitations**: Don't oversell results

### Code Quality

- **Minimal but functional**: Good enough to prove concept
- **Clear structure**: Easy to understand for demo
- **Isolated**: Don't pollute existing codebase

## Anti-Patterns

### POC Creep

❌ **Problem**: POC keeps growing, becomes mini-project
✅ **Solution**: Strict time-boxing, scope freeze after Phase 1

### Gold Plating

❌ **Problem**: Making POC code "production-ready"
✅ **Solution**: Remember POC is throwaway, focus on validation

### Confirmation Bias

❌ **Problem**: Only showing success scenarios
✅ **Solution**: Test failure scenarios, be honest about limitations

### No Decision

❌ **Problem**: POC ends without clear Go/No-Go
✅ **Solution**: Force decision at end of Phase 4

## Transition Paths

### POC → Greenfield

```bash
# If POC successful, start fresh with learnings
/f5:init production-project --workflow greenfield --from-poc ./poc-project

# Learnings are copied to .f5/memory/learnings.md
```

### POC → MVP

```bash
# If POC successful and need quick launch
/f5:init mvp-project --workflow mvp --from-poc ./poc-project
```

### POC → No-Go

```bash
# Archive learnings even if no-go
/f5:archive poc-project --reason "technical-infeasible"
```

## Templates

- [POC Definition Template](./templates/poc-definition.md)
- [POC Findings Template](./templates/poc-findings.md)
- [POC Decision Template](./templates/poc-decision.md)

## Examples

- [Redis vs Memcached POC](./examples/cache-comparison/)
- [GraphQL Integration POC](./examples/graphql-integration/)
- [Microservices POC](./examples/microservices/)

---

# ═══════════════════════════════════════════════════════════════
# F5 FEATURE INTEGRATION
# ═══════════════════════════════════════════════════════════════

## Auto-Activated Features Per Phase

| Phase | Mode | Persona | Verbosity | Recommended Agents |
|-------|------|---------|-----------|-------------------|
| Define | 🔍 analytical | 📊 analyst | 4 | - |
| Build | 💻 coding | ⚙️ backend | 2 | code_generator |
| Demo | 🏗️ planning | 📊 analyst | 3 | documenter |
| Decide | 🔍 analytical | 📊 analyst | 4 | documenter |

## Phase-Specific Commands

### Phase 1: Define (D1)

**Essential:**
```bash
/f5-ba define-hypothesis         # Define what to prove
/f5-gate complete D1             # Complete D1
```

**Recommended:**
```bash
/f5-mode set analytical          # Deep analysis
```

### Phase 2: Build (G2)

**Essential:**
```bash
/f5-implement setup --minimal    # Minimal setup
/f5-implement start --poc-mode   # POC implementation
/f5-gate complete G2             # Complete G2
```

**Recommended:**
```bash
/f5-mode set coding              # Fast coding
```

### Phase 3: Demo

**Essential:**
```bash
/f5-doc findings                 # Document findings
```

**Recommended:**
```bash
/f5-agent invoke documenter      # Document help
```

### Phase 4: Decide

**Essential:**
```bash
# Document decision
```

**Recommended:**
```bash
/f5-session checkpoint 'poc-complete'
```

## Agent Pipelines

| Phase | Recommended Pipeline |
|-------|---------------------|
| Build | - (minimal for POC) |

## Checkpoints

Create checkpoints at:
- [ ] After hypothesis defined (Define)
- [ ] After POC complete (Build)
- [ ] After decision made (Decide)

## Integration with Other F5 Features

### TDD Mode
- Not recommended for POC (throwaway code)

### Code Review
- Optional for POC

### Analytics
- Track time: `/f5-analytics summary`

### Health Check
- Not required for POC

## POC-Specific Tips

### Minimal Process
- Only 2 gates: D1, G2
- Focus on validating concept
- Code is throwaway

### Speed Over Quality
- Use **verbosity 2** for fast coding
- Skip tests (POC is throwaway)
- Document learnings, not code
