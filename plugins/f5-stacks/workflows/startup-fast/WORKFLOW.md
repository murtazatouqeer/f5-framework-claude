# Startup Fast Workflow

Workflow cho startup - ship nhanh nhất có thể với minimal process.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Project Type |
| **Duration** | 1-4 tuần |
| **Team Size** | 1-3 người |
| **Quality Gates** | D3→G2→G3 (minimal) |
| **Risk Level** | Low (accept tech debt) |
| **Starting Point** | idea |

## When to Use

### Ideal For

- Startup rapid prototyping
- Hackathon projects
- Quick market validation
- Internal tools
- Demo/proof-of-concept that may become product

### Not Suitable For

- Enterprise systems → Use [Enterprise](../enterprise/)
- Compliance-critical apps → Use [Enterprise](../enterprise/)
- Production systems with SLA → Use [Feature Development](../feature-development/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                     STARTUP FAST WORKFLOW                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                           │
│  │ Phase 1  │─▶│ Phase 2  │─▶│ Phase 3  │                           │
│  │  Design  │  │  Build   │  │  Ship    │                           │
│  │   D3     │  │   G2     │  │   G3     │                           │
│  │ (light)  │  │ (fast)   │  │ (basic)  │                           │
│  └──────────┘  └──────────┘  └──────────┘                           │
│                                                                       │
│  Speed > Perfection | Ship > Plan | Iterate > Predict                │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Design (D3 - Light)

**Duration**: 1-3 days

**Objectives**:
- Quick architecture sketch
- Tech stack decision
- Core feature list (max 3-5 features)

**Activities**:
```bash
/f5-load
/f5-design generate architecture --minimal
/f5-gate complete D3
```

**Deliverables**:
- [ ] Architecture Sketch
- [ ] Tech Stack Decision
- [ ] Core Feature List

### Phase 2: Build (G2 - Fast)

**Duration**: 1-3 weeks

**Objectives**:
- Implement core features
- Ship working product
- Accept reasonable tech debt

**Activities**:
```bash
/f5-implement start FEAT-001
/f5-tdd start feature
/f5-gate complete G2
```

**Deliverables**:
- [ ] Working Application
- [ ] Core Features Implemented
- [ ] Basic Error Handling

### Phase 3: Ship (G3 - Basic)

**Duration**: 1-3 days

**Objectives**:
- Basic testing (smoke tests)
- Deploy to production
- Get user feedback

**Activities**:
```bash
/f5-test run --smoke
/f5-deploy production
/f5-gate complete G3
```

**Deliverables**:
- [ ] Smoke Tests Passing
- [ ] Deployed Application
- [ ] Feedback Collection Setup

## Startup Fast Rules

1. **3-feature limit** - Focus on 3-5 core features maximum
2. **No premature optimization** - Ship first, optimize later
3. **Acceptable tech debt** - Document it, fix later
4. **User feedback > perfection** - Get real users as fast as possible
5. **Iterate quickly** - Weekly releases preferred

## After Ship: What Next?

- Getting traction → Transition to [Feature Development](../feature-development/)
- Needs scaling → Transition to [Modernization](../modernization/)
- Pivot needed → Start new Startup Fast cycle
- Failed validation → Document learnings, move on
