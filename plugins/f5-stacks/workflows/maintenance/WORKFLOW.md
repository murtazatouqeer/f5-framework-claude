# Maintenance Workflow

Workflow cho bảo trì hệ thống - bug fixes, patches, và minor updates.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Development Type |
| **Duration** | 1-5 ngày |
| **Team Size** | 1-2 người |
| **Quality Gates** | G2→G3 |
| **Risk Level** | Low |
| **Starting Point** | change-request |

## When to Use

### Ideal For

- Bug fixes
- Security patches
- Minor improvements
- Configuration changes
- Dependency updates

### Not Suitable For

- New features → Use [Feature Development](../feature-development/)
- Large refactoring → Use [Refactoring](../refactoring/)
- Performance issues → Use [Performance Optimization](../performance-optimization/)

## Maintenance Categories

| Category | Priority | SLA | Example |
|----------|----------|-----|---------|
| **Critical** | P0 | 4 hours | Security breach, system down |
| **High** | P1 | 24 hours | Major functionality broken |
| **Medium** | P2 | 3 days | Minor bug, workaround exists |
| **Low** | P3 | 1 week | Cosmetic, nice-to-have |

## Phases

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAINTENANCE WORKFLOW                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │ Phase 1 │───▶│ Phase 2 │───▶│ Phase 3 │───▶│ Phase 4 │     │
│  │ Triage  │    │  Fix    │    │ Verify  │    │ Deploy  │     │
│  │    -    │    │   G2    │    │   G3    │    │    -    │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│                                                                 │
│  Duration:       Duration:      Duration:      Duration:        │
│  1-4 hours       4h-2 days      2-4 hours      1-2 hours        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 1: Triage

**Duration**: 1-4 hours

**Objectives**:
- Assess issue severity
- Reproduce issue
- Identify root cause
- Estimate fix effort

**Activities**:
```bash
# 1. Load project context
/f5:load

# 2. Analyze bug report
/f5:bug analyze BUG-123

# 3. Reproduce issue
/f5:bug reproduce BUG-123

# 4. Root cause analysis
/f5:bug root-cause BUG-123
```

**Triage Checklist**:
- [ ] Issue can be reproduced
- [ ] Severity assessed (P0-P3)
- [ ] Root cause identified
- [ ] Fix approach determined
- [ ] Effort estimated

**Bug Analysis Template**:
```markdown
# Bug Analysis: [BUG-ID]

## Issue Summary
[Brief description]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected vs Actual
- Expected: [expected behavior]
- Actual: [actual behavior]

## Root Cause
[Technical explanation]

## Fix Approach
[How to fix]

## Severity: P[0-3]
## Estimate: [hours/days]
```

### Phase 2: Fix (G2)

**Duration**: 4 hours - 2 days
**Gate**: G2 (Implementation)

**Objectives**:
- Implement fix
- Write regression test
- Code review
- Update documentation

**Activities**:
```bash
# 1. Create fix branch
git checkout -b fix/BUG-123

# 2. Implement fix
/f5:implement fix BUG-123

# 3. Write regression test
/f5:test add-regression BUG-123

# 4. Complete G2
/f5:gate complete G2
```

**Fix Guidelines**:
- Minimal change (fix only the issue)
- Add regression test
- Don't refactor unrelated code
- Document the fix

**Deliverables**:
- [ ] Bug Fix Code
- [ ] Regression Test
- [ ] Code Review Approved

### Phase 3: Verify (G3)

**Duration**: 2-4 hours
**Gate**: G3 (Testing)

**Objectives**:
- Run all tests
- Verify fix works
- Check for regressions
- QA sign-off

**Activities**:
```bash
# 1. Run test suite
/f5:test run --all

# 2. Verify fix
/f5:test verify BUG-123

# 3. Regression check
/f5:test regression

# 4. Complete G3
/f5:gate complete G3
```

**Verification Checklist**:
- [ ] Bug is fixed
- [ ] Regression test passes
- [ ] No new issues introduced
- [ ] QA verified

### Phase 4: Deploy

**Duration**: 1-2 hours

**Objectives**:
- Deploy to production
- Monitor for issues
- Close ticket
- Notify stakeholders

**Activities**:
```bash
# 1. Deploy to staging (optional for P0)
/f5:deploy staging

# 2. Deploy to production
/f5:deploy production

# 3. Monitor
/f5:monitor check --duration 1h

# 4. Close ticket
/f5:bug close BUG-123
```

## Priority-Based SLAs

### P0 - Critical (Hotfix)

```
Timeline: 4 hours total
├── Triage: 30 min
├── Fix: 2 hours
├── Verify: 30 min
└── Deploy: 1 hour

Process:
- Skip staging (if needed)
- Direct deploy to production
- Post-mortem required
```

### P1 - High

```
Timeline: 24 hours total
├── Triage: 2 hours
├── Fix: 12 hours
├── Verify: 4 hours
└── Deploy: 2 hours

Process:
- Normal process but prioritized
- Staging deployment required
```

### P2 - Medium

```
Timeline: 3 days total
├── Triage: 4 hours
├── Fix: 1-2 days
├── Verify: 4 hours
└── Deploy: Next release cycle
```

### P3 - Low

```
Timeline: 1 week
- Scheduled for next sprint
- Bundled with other fixes
- Normal release cycle
```

## Hotfix Process

For P0/Critical issues:

```bash
# 1. Create hotfix branch from production
git checkout -b hotfix/critical-bug production

# 2. Quick fix
/f5:implement hotfix BUG-123

# 3. Minimal testing
/f5:test critical-path

# 4. Deploy immediately
/f5:deploy production --hotfix

# 5. Backport to development
git checkout develop
git merge hotfix/critical-bug

# 6. Post-mortem
/f5:doc post-mortem BUG-123
```

## Bug Categories

### Functional Bugs

- Feature not working as expected
- Logic errors
- Edge case failures

```bash
/f5:bug analyze --type functional BUG-123
```

### Performance Issues

- Slow response times
- Memory leaks
- Resource exhaustion

```bash
/f5:bug analyze --type performance BUG-123
```

### Security Issues

- Vulnerabilities
- Authentication bypass
- Data exposure

```bash
/f5:bug analyze --type security BUG-123
# Requires immediate attention
```

### UI/UX Issues

- Display problems
- Usability issues
- Responsive design

```bash
/f5:bug analyze --type ui BUG-123
```

## Root Cause Analysis

### 5 Whys Method

```markdown
## Bug: User cannot login

Why 1: Login API returns 500 error
Why 2: Database query fails
Why 3: Connection pool exhausted
Why 4: Connections not being released
Why 5: Missing try-finally block

Root Cause: Missing connection cleanup in error path
Fix: Add proper connection management
```

### Fishbone Diagram

```
                    ┌─────────────────┐
        Code        │    Database     │
        ────────────┼─────────────────
        │           │                 │
        └───────────┤    BUG         │
        ────────────┼─────────────────
        Config      │    External    │
                    └─────────────────┘
```

## Quality Metrics

### Bug Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| MTTR | <24h | Mean Time To Resolution |
| Escape Rate | <5% | Bugs found in production |
| Regression Rate | <2% | Bugs reintroduced |
| Fix Rate | >95% | First-time fix success |

### Process Metrics

| Metric | Target | Description |
|--------|--------|-------------|
| SLA Compliance | >95% | Fixes within SLA |
| Code Review | 100% | All fixes reviewed |
| Test Coverage | >80% | Regression tests added |

## Best Practices

### 1. Minimal Fix

- Fix only the issue, nothing else
- Don't refactor while fixing
- Keep changes small and focused

### 2. Always Add Regression Test

- Test that specifically catches the bug
- Prevents the bug from returning
- Documents expected behavior

### 3. Document Everything

- Root cause in ticket
- Fix approach in PR
- Post-mortem for P0/P1

### 4. Monitor After Deploy

- Watch metrics for 1 hour
- Check error rates
- Be ready to rollback

## Anti-Patterns

### Fix Without Understanding

❌ **Problem**: Quick fix without understanding root cause
✅ **Solution**: Always do root cause analysis

### Scope Creep

❌ **Problem**: "While I'm here, let me also..."
✅ **Solution**: Separate ticket for improvements

### Skip Testing

❌ **Problem**: "It's a small fix, no need to test"
✅ **Solution**: Always run tests, add regression test

### No Communication

❌ **Problem**: Fix deployed without notifying stakeholders
✅ **Solution**: Always update ticket, notify affected parties

## Templates

- [Bug Report Template](./templates/bug-report.md)
- [Root Cause Analysis](./templates/root-cause-analysis.md)
- [Hotfix Checklist](./templates/hotfix-checklist.md)
- [Post-Mortem Template](./templates/post-mortem.md)

## Examples

- [Authentication Bug Fix](./examples/auth-bugfix/)
- [Performance Hotfix](./examples/performance-hotfix/)
- [Security Patch](./examples/security-patch/)

---

# ═══════════════════════════════════════════════════════════════
# F5 FEATURE INTEGRATION
# ═══════════════════════════════════════════════════════════════

## Auto-Activated Features Per Phase

| Phase | Mode | Persona | Verbosity | Recommended Agents |
|-------|------|---------|-----------|-------------------|
| Triage | 🔬 debugging | 🧪 qa | 3 | debugger |
| Fix | 💻 coding | ⚙️ backend | 2 | code_generator, test_writer |
| Verify | 🔬 debugging | 🧪 qa | 3 | test_writer |
| Deploy | 🚀 coding | 🔧 devops | 3 | - |

## Phase-Specific Commands

### Phase 1: Triage

**Essential:**
```bash
/f5-load                         # Load project context
/f5-bug analyze BUG-123          # Analyze bug
/f5-bug reproduce BUG-123        # Reproduce issue
/f5-bug root-cause BUG-123       # Root cause analysis
```

**Recommended:**
```bash
/f5-mode set debugging           # Debug mode
/f5-agent invoke debugger        # Debug help
```

### Phase 2: Fix (G2)

**Essential:**
```bash
/f5-implement fix BUG-123        # Implement fix
/f5-test add-regression BUG-123  # Add regression test
/f5-gate complete G2             # Complete G2
```

**Recommended:**
```bash
/f5-agent pipeline bug_fix       # Bug fix pipeline
/f5-review quick                 # Quick review
```

### Phase 3: Verify (G3)

**Essential:**
```bash
/f5-test run --all               # Run all tests
/f5-test verify BUG-123          # Verify fix
/f5-gate complete G3             # Complete G3
```

**Recommended:**
```bash
/f5-test regression              # Regression check
```

### Phase 4: Deploy

**Essential:**
```bash
/f5-deploy production            # Deploy fix
/f5-bug close BUG-123            # Close ticket
```

**Recommended:**
```bash
/f5-monitor check --duration 1h  # Monitor after deploy
```

## Agent Pipelines

| Phase | Recommended Pipeline |
|-------|---------------------|
| Triage | - |
| Fix | `bug_fix` |
| Verify | - |

## Checkpoints

Create checkpoints at:
- [ ] After root cause identified (Triage)
- [ ] After fix implemented (Fix)
- [ ] After tests pass (Verify)

## Integration with Other F5 Features

### TDD Mode
- Use for regression test: `/f5-tdd start regression-BUG-123`

### Code Review
- Required: quick review before deploy
- Run: `/f5-review quick`

### Analytics
- Track bugs: `/f5-analytics errors`
- View trends: `/f5-analytics --dashboard errors`

### Health Check
- After deploy: `/f5-status health`

## Maintenance-Specific Tips

### Minimal Fix Principle
- Fix only the bug, nothing else
- Add regression test
- Don't refactor while fixing

### Priority-Based Process
| Priority | Skip Staging? | Post-mortem? |
|----------|---------------|--------------|
| P0 | Yes (hotfix) | Required |
| P1 | No | Recommended |
| P2-P3 | No | No |

### When to Use Agents

| Task | Agent/Pipeline |
|------|---------------|
| Debug analysis | `debugger` |
| Bug fix | `bug_fix` pipeline |
| Regression test | `test_writer` |
