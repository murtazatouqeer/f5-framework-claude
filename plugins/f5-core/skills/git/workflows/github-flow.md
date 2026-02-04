---
name: github-flow
description: GitHub Flow simplified workflow for continuous deployment
category: git/workflows
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GitHub Flow

## Overview

GitHub Flow is a lightweight, branch-based workflow ideal for teams practicing
continuous deployment. It emphasizes simplicity with just one main branch and
feature branches.

## Core Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                  GitHub Flow Principles                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Main branch is always deployable                            │
│  2. Create descriptive branches for work                        │
│  3. Push to named branches constantly                           │
│  4. Open a pull request at any time                             │
│  5. Merge only after pull request review                        │
│  6. Deploy immediately after merge                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Flow Model                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  main     ──●────●────●────●────●────●────●────●────●────●──▶   │
│             │         │         │         │         │           │
│             │    ●────┘         │         │    ●────┘           │
│             │    │              │         │    │                │
│  feature-a  └────●              │         │    │                │
│                  PR → Review    │         │    │                │
│                  → Merge        │         │    │                │
│                  → Deploy       │         │    │                │
│                                 │         │    │                │
│  feature-b       ●───●───●──────┘         │    │                │
│                      PR → Review          │    │                │
│                      → Merge              │    │                │
│                      → Deploy             │    │                │
│                                           │    │                │
│  bugfix-c                  ●───●──────────┘    │                │
│                            PR → Review         │                │
│                            → Merge             │                │
│                            → Deploy            │                │
│                                                │                │
│  feature-d                      ●───●───●──────┘                │
│                                     PR → Review                 │
│                                     → Merge                     │
│                                     → Deploy                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Workflow

### 1. Create a Branch

```bash
# Always start from updated main
git checkout main
git pull origin main

# Create descriptive branch name
git checkout -b feature/add-user-search

# Good branch names:
# feature/add-user-search
# bugfix/fix-login-redirect
# hotfix/security-patch
# chore/update-dependencies
# docs/update-readme
```

### 2. Add Commits

```bash
# Make changes and commit frequently
git add src/search.ts
git commit -m "feat(search): add basic search component"

git add src/search.test.ts
git commit -m "test(search): add search component tests"

git add src/api/search.ts
git commit -m "feat(api): add search API endpoint"

# Push to remote regularly
git push -u origin feature/add-user-search
```

### 3. Open Pull Request

```bash
# Push latest changes
git push origin feature/add-user-search

# Create PR via GitHub CLI
gh pr create --title "Add user search functionality" \
  --body "## Description
Adds search functionality to find users.

## Changes
- Add search component
- Add search API endpoint
- Add tests

## Testing
- [x] Unit tests pass
- [x] Manual testing complete

Closes #123"

# Or use GitHub web interface
```

### 4. Discuss and Review

```bash
# Address review comments
git add .
git commit -m "refactor: address review feedback"
git push origin feature/add-user-search

# Request re-review
gh pr review --request

# View PR status
gh pr status
gh pr checks
```

### 5. Deploy for Testing

```bash
# Deploy branch to staging (varies by setup)
# GitHub Actions example:
# Automatic deployment on PR creation

# Or manual deployment
./deploy.sh staging feature/add-user-search

# Verify deployment
curl https://staging.example.com/health
```

### 6. Merge

```bash
# Ensure branch is up to date
git checkout feature/add-user-search
git fetch origin
git rebase origin/main
git push --force-with-lease

# Merge via GitHub CLI
gh pr merge --squash --delete-branch

# Or merge options:
gh pr merge --merge          # Create merge commit
gh pr merge --squash         # Squash and merge
gh pr merge --rebase         # Rebase and merge
```

### 7. Deploy to Production

```bash
# Automatic deployment after merge (recommended)
# Triggered by CI/CD pipeline

# Or manual deployment
git checkout main
git pull origin main
./deploy.sh production
```

## Pull Request Best Practices

### PR Template

```markdown
<!-- .github/pull_request_template.md -->
## Description
<!-- What does this PR do? -->

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
<!-- List the changes -->
-
-

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing complete

## Screenshots
<!-- If applicable -->

## Related Issues
<!-- Link to issues -->
Closes #

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-reviewed code
- [ ] Added necessary documentation
- [ ] No new warnings
```

### Small PRs

```
┌─────────────────────────────────────────────────────────────────┐
│                    PR Size Guidelines                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ideal PR Size:                                                 │
│  • < 400 lines of code                                          │
│  • Single feature or fix                                        │
│  • Can be reviewed in < 1 hour                                  │
│                                                                  │
│  Large Feature Strategy:                                        │
│  1. Break into multiple PRs                                     │
│  2. Use feature flags for incomplete features                   │
│  3. Stack PRs (PR depends on PR)                                │
│                                                                  │
│  Benefits of Small PRs:                                         │
│  • Faster reviews                                               │
│  • Easier to understand                                         │
│  • Less risky deployments                                       │
│  • Quicker feedback                                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test
      - run: npm run lint

  deploy-staging:
    needs: test
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh staging

  deploy-production:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production
```

### Branch Protection Rules

```yaml
# Settings for main branch:
# - Require pull request reviews (1+ approvals)
# - Dismiss stale PR approvals when new commits pushed
# - Require status checks to pass
# - Require branches to be up to date
# - Include administrators in rules
# - Restrict who can push to matching branches
```

## Feature Flags

```typescript
// For incomplete features merged to main

interface FeatureFlags {
  newSearch: boolean;
  betaDashboard: boolean;
  experimentalApi: boolean;
}

const flags: FeatureFlags = {
  newSearch: process.env.FEATURE_NEW_SEARCH === 'true',
  betaDashboard: process.env.FEATURE_BETA_DASHBOARD === 'true',
  experimentalApi: false,
};

// Usage
if (flags.newSearch) {
  return <NewSearchComponent />;
} else {
  return <LegacySearch />;
}
```

## When to Use GitHub Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                 When to Use GitHub Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Good For:                                                   │
│  • Continuous deployment                                        │
│  • Web applications / SaaS                                      │
│  • Teams with good CI/CD                                        │
│  • Projects with single production version                      │
│  • Agile teams with frequent releases                           │
│                                                                  │
│  ❌ Not Ideal For:                                              │
│  • Multiple production versions                                 │
│  • Scheduled releases                                           │
│  • Projects without automated testing                           │
│  • Strict release management needs                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                GitHub Flow Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Main is Always Deployable                                   │
│     └── Never merge broken code                                 │
│                                                                  │
│  2. Branch Names Describe Work                                  │
│     └── feature/JIRA-123-add-search                             │
│                                                                  │
│  3. Small, Focused PRs                                          │
│     └── One feature or fix per PR                               │
│                                                                  │
│  4. Review All Code                                             │
│     └── No direct pushes to main                                │
│                                                                  │
│  5. Deploy Immediately                                          │
│     └── Merge = Deploy                                          │
│                                                                  │
│  6. Use Feature Flags                                           │
│     └── For incomplete features                                 │
│                                                                  │
│  7. Automate Everything                                         │
│     └── Tests, linting, deployment                              │
│                                                                  │
│  8. Delete Branches After Merge                                 │
│     └── Keep repository clean                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
