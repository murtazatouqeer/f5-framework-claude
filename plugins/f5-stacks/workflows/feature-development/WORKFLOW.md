# Feature Development Workflow

Workflow cho phát triển tính năng mới trong hệ thống đang có.

## Overview

| Attribute | Value |
|-----------|-------|
| **Type** | Development Type |
| **Duration** | 1-4 tuần |
| **Team Size** | 1-5 người |
| **Quality Gates** | D3→G2→G2.5→G3 |
| **Risk Level** | Low-Medium |
| **Starting Point** | change-request |

## When to Use

### Ideal For

- Adding new features to existing product
- User-requested enhancements
- New integrations
- Feature expansions

### Not Suitable For

- Bug fixes → Use [Maintenance](../maintenance/)
- Code cleanup → Use [Refactoring](../refactoring/)
- New product → Use [Greenfield](../greenfield/) or [MVP](../mvp/)

## Phases

```
┌───────────────────────────────────────────────────────────────────────┐
│                    FEATURE DEVELOPMENT WORKFLOW                        │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐            │
│  │ Phase 1 │───▶│ Phase 2 │───▶│ Phase 3 │───▶│ Phase 4 │            │
│  │ Analyze │    │ Design  │    │ Develop │    │ Release │            │
│  │    -    │    │   D3    │    │G2→G2.5→G3│   │    -    │            │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘            │
│                                                                        │
│  Duration:       Duration:      Duration:      Duration:               │
│  2-3 days        2-5 days       1-3 weeks      1-2 days                │
│                                                                        │
│  Phase 3 Breakdown:                                                    │
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Implement (G2) ──▶ Verify (G2.5) ──▶ Test (G3)              │     │
│  │     Code            Assets/Visual      Unit/E2E              │     │
│  │     Review          Integration        Performance           │     │
│  │                     Bug Fixes                                │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Analyze

**Duration**: 2-3 days

**Objectives**:
- Understand feature requirements
- Analyze impact on existing code
- Identify dependencies
- Estimate effort

**Activities**:
```bash
# 1. Load project context
/f5:load

# 2. Analyze feature request
/f5:ba analyze-feature "Add user notifications"

# 3. Impact analysis
/f5:analyze impact --scope module

# 4. Estimate effort
/f5:estimate feature
```

**Deliverables**:
- [ ] Feature Requirements Document
- [ ] Impact Analysis Report
- [ ] Effort Estimate
- [ ] Acceptance Criteria

**Impact Analysis Template**:
```markdown
# Feature Impact Analysis

## Feature: [Feature Name]

## Affected Areas
- [ ] Database: [tables/changes]
- [ ] API: [endpoints affected]
- [ ] Frontend: [components affected]
- [ ] Services: [services affected]

## Dependencies
- [ ] External: [APIs, services]
- [ ] Internal: [modules, features]

## Risks
1. Risk 1 - Impact: High/Medium/Low
2. Risk 2 - Impact: High/Medium/Low

## Estimate
- Development: X days
- Testing: X days
- Total: X days
```

### Phase 2: Design (D3)

**Duration**: 2-5 days
**Gate**: D3 (Basic Design)

**Objectives**:
- Design feature architecture
- Define API contracts
- Create UI mockups (if applicable)
- Plan database changes

**Activities**:
```bash
# 1. Design feature architecture
/f5:design generate feature-architecture

# 2. API design
/f5:design generate api --feature notifications

# 3. Database changes
/f5:design generate migration

# 4. Complete D3
/f5:gate complete D3
```

**Deliverables**:
- [ ] Feature Architecture Document
- [ ] API Specification
- [ ] Database Migration Script
- [ ] UI Mockups (if applicable)

### Phase 3: Develop (G2→G2.5→G3)

**Duration**: 1-3 weeks
**Gates**: G2 (Implementation), G2.5 (Verification), G3 (Testing)

**Objectives**:
- Implement feature
- Verify implementation (assets, integration, visual)
- Write tests
- Code review
- Integration testing

#### Step 3.1: Implementation (G2)

**Activities**:
```bash
# 1. Create feature branch
git checkout -b feature/notifications

# 2. Implement with traceability
/f5-implement start FR-001

# 3. Code review
/f5-review code

# 4. Complete G2
/f5-gate complete G2
```

**Deliverables**:
- [ ] Feature Implementation
- [ ] Code Review Approved

#### Step 3.2: Verification (G2.5) - NEW

**Purpose**: Verify implementation matches design before testing

**Activities**:
```bash
# 1. Verify all assets exist
/f5-verify assets

# 2. Check integration (links, routes)
/f5-verify integration

# 3. Visual comparison with Figma
/f5-test-visual --compare-figma

# 4. Fix any issues found
/f5-fix <bug-id>

# 5. Full G2.5 gate check
/f5-verify --gate

# 6. Complete G2.5
/f5-gate complete G2.5
```

**Deliverables**:
- [ ] Asset Verification Passed
- [ ] Integration Check Passed
- [ ] Visual QA Passed (≤5% diff)
- [ ] All Bugs Fixed

#### Step 3.3: Testing (G3)

**Activities**:
```bash
# 1. Run unit tests
/f5-test-unit src/ --coverage

# 2. Run integration tests
/f5-test-it api [endpoints]

# 3. Run E2E tests
/f5-test-e2e smoke

# 4. Run visual regression
/f5-test-visual --ci

# 5. Complete G3
/f5-gate complete G3
```

**Development Guidelines**:
- Follow existing code patterns
- Add traceability comments
- Write tests alongside code
- Keep PR size manageable (<400 lines)

**Deliverables**:
- [ ] Feature Implementation
- [ ] Unit Tests
- [ ] Integration Tests
- [ ] Code Review Approved
- [ ] Documentation Updated

### Phase 4: Release

**Duration**: 1-2 days

**Objectives**:
- Deploy to staging
- Perform UAT
- Deploy to production
- Monitor

**Activities**:
```bash
# 1. Deploy to staging
/f5:deploy staging

# 2. UAT
/f5:test uat

# 3. Deploy to production
/f5:deploy production

# 4. Monitor
/f5:monitor feature notifications
```

**Deliverables**:
- [ ] Deployed Feature
- [ ] UAT Sign-off
- [ ] Release Notes
- [ ] Monitoring Dashboard

## Feature Size Guidelines

### Small Feature (1-3 days)

- Single component change
- No database changes
- No new dependencies
- Example: Add filter to list view

```bash
/f5:workflow feature --size small
# Simplified flow: Analyze → Develop → Release
```

### Medium Feature (1-2 weeks)

- Multiple component changes
- Minor database changes
- Some new endpoints
- Example: User notifications system

```bash
/f5:workflow feature --size medium
# Standard flow: Analyze → Design → Develop → Release
```

### Large Feature (2-4 weeks)

- Major architectural changes
- New module/service
- Multiple integrations
- Example: Real-time collaboration

```bash
/f5:workflow feature --size large
# Extended flow with more reviews and testing
```

## Integration Patterns

### Feature Flags

```typescript
// Use feature flags for gradual rollout
if (featureFlags.isEnabled('notifications')) {
  // New feature code
} else {
  // Existing behavior
}
```

### Backward Compatibility

```typescript
// API versioning for backward compatibility
// v1 - existing behavior
// v2 - new feature

@Controller('api/v2/users')
export class UsersV2Controller {
  // New endpoints
}
```

### Database Migration

```sql
-- Use reversible migrations
-- Up
ALTER TABLE users ADD COLUMN notification_preferences JSONB;

-- Down
ALTER TABLE users DROP COLUMN notification_preferences;
```

## Quality Checklist

### Pre-Development

- [ ] Requirements clear and signed off
- [ ] Impact analysis completed
- [ ] Design reviewed
- [ ] Estimate approved

### During Development

- [ ] Code follows existing patterns
- [ ] Tests written for new code
- [ ] No regressions introduced
- [ ] Documentation updated

### Pre-Release

- [ ] All tests passing
- [ ] Code review approved
- [ ] UAT completed
- [ ] Release notes ready

## Best Practices

### 1. Small Iterations

- Break large features into smaller deliverables
- Deploy frequently to reduce risk
- Get feedback early

### 2. Feature Flags

- Use feature flags for big changes
- Enable gradual rollout
- Easy rollback if issues

### 3. Backward Compatibility

- Don't break existing functionality
- Version APIs when needed
- Migrate data carefully

### 4. Documentation

- Update API docs
- Update user docs
- Add inline code comments

## Common Patterns

### Feature Module Structure

```
src/
├── modules/
│   └── notifications/          # New feature module
│       ├── controllers/
│       ├── services/
│       ├── repositories/
│       ├── dto/
│       ├── entities/
│       └── notifications.module.ts
```

### Test Structure

```
test/
├── unit/
│   └── notifications/
│       ├── notification.service.spec.ts
│       └── notification.controller.spec.ts
├── integration/
│   └── notifications/
│       └── notification.integration.spec.ts
└── e2e/
    └── notifications.e2e.spec.ts
```

## Templates

- [Feature Request Template](./templates/feature-request.md)
- [Impact Analysis Template](./templates/impact-analysis.md)
- [Design Document Template](./templates/design-document.md)
- [Release Notes Template](./templates/release-notes.md)

## Examples

- [Add Search Feature](./examples/search-feature/)
- [Add Export to PDF](./examples/export-feature/)
- [Add OAuth Integration](./examples/oauth-integration/)

---

# ═══════════════════════════════════════════════════════════════
# F5 FEATURE INTEGRATION
# ═══════════════════════════════════════════════════════════════

## Auto-Activated Features Per Phase

| Phase | Mode | Persona | Verbosity | Recommended Agents |
|-------|------|---------|-----------|-------------------|
| Analyze | 🔍 analytical | 📊 analyst | 4 | - |
| Design | 🏗️ planning | 🏛️ architect | 4 | api_designer |
| Develop (G2) | 💻 coding | ⚙️ backend | 2 | code_generator, test_writer |
| Verify (G2.5) | 🔍 debugging | 🎨 frontend | 3 | visual_tester |
| Test (G3) | 🧪 testing | 🔬 qa | 3 | test_runner |
| Release | 🚀 coding | 🔧 devops | 3 | security_scanner |

## Phase-Specific Commands

### Phase 1: Analyze

**Essential:**
```bash
/f5-load                         # Load project context
/f5-ba analyze-feature "feature" # Analyze requirements
/f5-analyze impact --scope module
```

**Recommended:**
```bash
/f5-estimate feature             # Estimate effort
```

### Phase 2: Design (D3)

**Essential:**
```bash
/f5-design generate feature-architecture
/f5-design generate api --feature X
/f5-gate complete D3             # Complete D3
```

**Recommended:**
```bash
/f5-agent invoke api_designer    # API help
```

### Phase 3: Develop (G2→G2.5→G3)

**Step 3.1 - Implementation (G2):**
```bash
/f5-implement start FR-001       # Start with traceability
/f5-tdd start feature            # TDD mode
/f5-review code                  # Code review
/f5-gate complete G2             # Complete G2
```

**Step 3.2 - Verification (G2.5):**
```bash
/f5-verify assets                # Check all assets exist
/f5-verify integration           # Check links and routes
/f5-test-visual --compare-figma  # Visual QA
/f5-fix <bug-id>                 # Fix issues found
/f5-verify --gate                # Full G2.5 check
/f5-gate complete G2.5           # Complete G2.5
```

**Step 3.3 - Testing (G3):**
```bash
/f5-test run --coverage          # Run tests
/f5-test-visual --ci             # Visual regression
/f5-gate complete G3             # Complete G3
```

**Recommended:**
```bash
/f5-agent pipeline feature_development  # Full pipeline
/f5-session checkpoint 'feature-done'
```

### Phase 4: Release

**Essential:**
```bash
/f5-deploy staging               # Staging deployment
/f5-test uat                     # UAT
/f5-deploy production            # Production deployment
```

**Recommended:**
```bash
/f5-monitor feature X            # Monitor new feature
```

## Agent Pipelines

| Phase | Recommended Pipeline |
|-------|---------------------|
| Develop | `feature_development` |
| Develop (bugs) | `bug_fix` |
| Release | `security_audit` (if needed) |

## Checkpoints

Create checkpoints at:
- [ ] After impact analysis (Analyze)
- [ ] After design complete (Design)
- [ ] Before merging PR (Develop)
- [ ] After production deploy (Release)

## Integration with Other F5 Features

### TDD Mode
- Recommended in: Develop phase
- Start with: `/f5-tdd start feature`

### Code Review
- Required before: G2 gate
- Run: `/f5-review code`

### Analytics
- Track progress: `/f5-analytics summary`

### Health Check
- Before gates: `/f5-selftest`

## Feature Development Tips

### Follow Existing Patterns
- Use **verbosity 3** to understand patterns
- Match existing code style
- Reuse existing components

### When to Use Agents

| Task | Agent/Pipeline |
|------|---------------|
| API design | `api_designer` |
| Feature implementation | `feature_development` pipeline |
| Code quality check | `code_quality` pipeline |
