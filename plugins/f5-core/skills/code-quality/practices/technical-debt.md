---
name: technical-debt
description: Managing and reducing technical debt
category: code-quality/practices
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Technical Debt

## Overview

Technical debt is the implied cost of additional rework caused by choosing an easy solution now instead of a better approach that would take longer. Like financial debt, it accrues "interest" over time.

## Types of Technical Debt

### Deliberate vs. Inadvertent

```
         Deliberate                    Inadvertent
   ┌─────────────────────┐      ┌─────────────────────┐
   │   "We don't have    │      │   "What's a design  │
   │   time for design"  │      │   pattern?"         │
   │                     │      │                     │
   │   Reckless/         │      │   Reckless/         │
   │   Deliberate        │      │   Inadvertent       │
   └─────────────────────┘      └─────────────────────┘
   
   ┌─────────────────────┐      ┌─────────────────────┐
   │   "We must ship     │      │   "Now we know how  │
   │   now, deal with    │      │   we should have    │
   │   consequences"     │      │   done it"          │
   │                     │      │                     │
   │   Prudent/          │      │   Prudent/          │
   │   Deliberate        │      │   Inadvertent       │
   └─────────────────────┘      └─────────────────────┘
```

### Common Types

| Type | Description | Example |
|------|-------------|---------|
| **Code Debt** | Poor code quality | Long methods, duplication |
| **Design Debt** | Architecture issues | Missing abstractions, tight coupling |
| **Testing Debt** | Insufficient tests | Low coverage, no integration tests |
| **Documentation Debt** | Missing/outdated docs | No API docs, stale README |
| **Infrastructure Debt** | DevOps issues | Manual deployments, no monitoring |
| **Dependency Debt** | Outdated dependencies | Old frameworks, security issues |

## Identifying Technical Debt

### Code Smells Indicating Debt

```typescript
// 1. Long methods (>50 lines)
function processOrder(order: Order) {
  // 200 lines of mixed responsibilities
}

// 2. Duplicated code
function validateUser(user: User) {
  if (!user.email) throw new Error('Email required');
  if (!user.email.includes('@')) throw new Error('Invalid email');
}

function validateAdmin(admin: Admin) {
  // Same validation repeated!
  if (!admin.email) throw new Error('Email required');
  if (!admin.email.includes('@')) throw new Error('Invalid email');
}

// 3. Magic numbers and strings
if (status === 3) { } // What is 3?
if (role === 'adm') { } // Typo risk

// 4. Excessive parameters
function createReport(
  title: string, 
  author: string, 
  date: Date, 
  format: string,
  includeCharts: boolean,
  chartType: string,
  pageSize: string,
  orientation: string
) { }

// 5. God classes
class ApplicationManager {
  handleUsers() { }
  handleOrders() { }
  handlePayments() { }
  handleNotifications() { }
  handleReports() { }
  // 50+ more methods
}
```

### Metrics That Reveal Debt

| Metric | Threshold | Tool |
|--------|-----------|------|
| Cyclomatic complexity | > 15 | SonarQube, ESLint |
| Code duplication | > 5% | SonarQube, jscpd |
| Test coverage | < 60% | Jest, NYC |
| Dependency age | > 1 year | npm-check |
| Build time | Increasing trend | CI metrics |
| Bug density | > 1 bug/1000 LOC | Bug tracker |

## Measuring Technical Debt

### Technical Debt Ratio

```
TDR = (Remediation Cost / Development Cost) × 100

Example:
- Remediation Cost: 40 hours to fix all issues
- Development Cost: 800 hours spent building
- TDR = (40/800) × 100 = 5%

Rating:
- A: 0-5% (Excellent)
- B: 5-10% (Good)
- C: 10-20% (Acceptable)
- D: 20-50% (Poor)
- E: >50% (Critical)
```

### Debt Inventory

```markdown
## Technical Debt Inventory

| ID | Description | Impact | Effort | Priority |
|----|-------------|--------|--------|----------|
| TD-001 | No API rate limiting | High | Medium | P1 |
| TD-002 | Database queries not optimized | Medium | High | P2 |
| TD-003 | Missing input validation | High | Low | P1 |
| TD-004 | Outdated React (v16) | Medium | Medium | P2 |
| TD-005 | No error boundary | Low | Low | P3 |
```

## Managing Technical Debt

### The Debt Register

Track debt items like any other backlog:

```yaml
# debt-registry.yaml
items:
  - id: TD-001
    title: Refactor authentication module
    description: |
      Current auth is tightly coupled to database.
      Need to extract interface for testing.
    type: design
    impact: high
    effort: 2 sprints
    interest: |
      - Every new test requires database setup (4hr/test)
      - Can't switch to OAuth without major rewrite
    created: 2024-01-15
    owner: backend-team

  - id: TD-002
    title: Upgrade Node.js from 16 to 20
    description: Node 16 EOL approaching
    type: infrastructure
    impact: medium
    effort: 1 sprint
    interest: |
      - Missing security patches
      - Can't use new language features
    created: 2024-02-01
    owner: devops-team
```

### Prioritization Matrix

```
                    High Effort
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
     │    BIG BETS       │     THANKLESS     │
     │  Schedule for     │   Avoid unless    │
High │  dedicated sprint │   critical        │
Impact                   │                   │
     ├───────────────────┼───────────────────┤
     │                   │                   │
     │    QUICK WINS     │     TIME SINKS    │
     │  Do immediately   │   Don't do        │
Low  │  during sprints   │                   │
Impact                   │                   │
     └───────────────────┴───────────────────┘
                    Low Effort
```

### Repayment Strategies

#### 1. The 20% Rule

Allocate 20% of each sprint to debt reduction.

```markdown
Sprint Capacity: 100 points
- Features: 80 points
- Tech Debt: 20 points
```

#### 2. Boy Scout Rule

Leave code better than you found it.

```typescript
// While fixing a bug in this file:
// Before - spotted debt
function process(d) {
  var r = [];
  for (var i = 0; i < d.length; i++) {
    r.push(d[i].val);
  }
  return r;
}

// After - cleaned up while here
function extractValues(data: DataItem[]): string[] {
  return data.map(item => item.value);
}
```

#### 3. Strangler Fig Pattern

Gradually replace legacy system.

```typescript
// 1. Create new interface
interface UserService {
  findById(id: string): Promise<User>;
}

// 2. Wrap legacy implementation
class LegacyUserService implements UserService {
  async findById(id: string): Promise<User> {
    return legacyDatabase.getUser(id);
  }
}

// 3. Create new implementation
class ModernUserService implements UserService {
  async findById(id: string): Promise<User> {
    return prisma.user.findUnique({ where: { id } });
  }
}

// 4. Switch gradually using feature flags
const userService = featureFlags.useNewUserService
  ? new ModernUserService()
  : new LegacyUserService();
```

#### 4. Dedicated Debt Sprints

Periodically run cleanup sprints.

```markdown
## Tech Debt Sprint Q1-2024

### Goals
- Reduce complexity below 15 in all modules
- Achieve 80% test coverage
- Update all dependencies

### Results
- Complexity: 22 → 12 ✅
- Coverage: 65% → 82% ✅
- Dependencies: 15 outdated → 3 ✅
```

## Prevention Strategies

### Definition of Done

Include quality in your DoD:

```markdown
## Definition of Done
- [ ] Code reviewed
- [ ] Tests written (>80% coverage)
- [ ] No new lint warnings
- [ ] Documentation updated
- [ ] No increase in tech debt
- [ ] Performance acceptable
```

### Architecture Decision Records (ADRs)

Document decisions to prevent future debt:

```markdown
# ADR-001: Use PostgreSQL for primary database

## Status
Accepted

## Context
We need a database for our user management system.

## Decision
Use PostgreSQL.

## Consequences
- Positive: ACID compliance, strong ecosystem
- Negative: Need to manage schema migrations
- Debt Risk: Low if we use proper migrations from start
```

### Quality Gates

Enforce standards in CI:

```yaml
# .github/workflows/quality-gate.yml
quality-gate:
  runs-on: ubuntu-latest
  steps:
    - name: Check complexity
      run: |
        COMPLEXITY=$(npx eslint --max-warnings 0 src/)
        if [ $? -ne 0 ]; then
          echo "Complexity threshold exceeded"
          exit 1
        fi
    
    - name: Check coverage
      run: |
        npm run test:coverage
        COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
        if (( $(echo "$COVERAGE < 80" | bc -l) )); then
          echo "Coverage below 80%"
          exit 1
        fi
```

## Communicating Debt to Stakeholders

### Business Language

Don't say: "We have technical debt"

Say: "Our current architecture means:
- New features take 2x longer to build
- We have 3x more bugs than industry average
- Security vulnerabilities take weeks to patch"

### Visual Debt Dashboard

```
┌──────────────────────────────────────────────┐
│           Technical Debt Dashboard           │
├──────────────────────────────────────────────┤
│                                              │
│  Debt Ratio: ██████████░░░░░░ 35%            │
│  Target:     ████████░░░░░░░░ 20%            │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │ Code Quality    [████████░░] 78%        │ │
│  │ Test Coverage   [███████░░░] 65%        │ │
│  │ Dependencies    [█████░░░░░] 45%        │ │
│  │ Documentation   [██████░░░░] 55%        │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  Est. Interest Payment: 15 hrs/sprint        │
│  Trend: ↗ Increasing (+5% this quarter)      │
│                                              │
└──────────────────────────────────────────────┘
```
