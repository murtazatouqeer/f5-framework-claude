---
name: pull-requests
description: Creating and managing pull requests effectively
category: git/collaboration
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Pull Requests

## Overview

Pull requests (PRs) are the primary mechanism for code review and collaboration.
They enable discussion, review, and approval before changes are merged into
the main codebase.

## PR Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pull Request Lifecycle                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Create Branch → 2. Develop → 3. Push → 4. Open PR           │
│                                                                  │
│         ┌──────────────────────────────────────┐                │
│         │                                      │                │
│         ▼                                      │                │
│  5. Review ───▶ 6. Update ───▶ 7. Approve     │                │
│         │              │              │        │                │
│         │              └──────────────┘        │                │
│         │                                      │                │
│         └──────── Request Changes ─────────────┘                │
│                                                                  │
│  8. Merge → 9. Delete Branch → 10. Deploy                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Creating Pull Requests

### Using GitHub CLI

```bash
# Create PR with title and body
gh pr create --title "Add user authentication" --body "Description here"

# Create PR with template
gh pr create --fill

# Create draft PR
gh pr create --draft --title "WIP: User authentication"

# Create PR to specific base branch
gh pr create --base develop --title "Feature: Auth"

# Create PR with reviewers
gh pr create --title "Add auth" --reviewer user1,user2

# Create PR with labels
gh pr create --title "Add auth" --label "feature,needs-review"

# Create PR and assign
gh pr create --title "Add auth" --assignee @me
```

### PR Description Template

```markdown
## Description
<!-- What does this PR do? Why is it needed? -->
Implements user authentication with JWT tokens.

## Type of Change
- [x] New feature
- [ ] Bug fix
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Performance improvement

## Changes Made
- Add login/logout endpoints
- Add JWT token generation
- Add authentication middleware
- Add password hashing
- Add user session management

## Testing
- [x] Unit tests added
- [x] Integration tests added
- [x] Manual testing completed
- [ ] E2E tests added

## Test Instructions
1. Start the server: `npm run dev`
2. POST to `/api/auth/login` with credentials
3. Use returned token in Authorization header
4. Verify protected routes work

## Screenshots
<!-- If applicable -->
![Login Page](./screenshots/login.png)

## Performance Impact
<!-- Any performance considerations? -->
- Added ~5ms latency for token verification on protected routes
- JWT verification is cached

## Related Issues
Closes #123
Relates to #456

## Checklist
- [x] Code follows project style guidelines
- [x] Self-reviewed my code
- [x] Added necessary documentation
- [x] No new warnings generated
- [x] Tests pass locally
- [x] Updated CHANGELOG.md
```

### GitHub PR Template File

```markdown
<!-- .github/PULL_REQUEST_TEMPLATE.md -->
## Description
<!-- Describe your changes -->

## Type of Change
<!-- Check all that apply -->
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (non-breaking change adding functionality)
- [ ] 💥 Breaking change (fix or feature causing existing functionality to change)
- [ ] 📝 Documentation update
- [ ] 🔧 Refactoring (no functional changes)
- [ ] ⚡ Performance improvement

## Testing
<!-- Describe how you tested -->
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing done

## Checklist
<!-- Verify before requesting review -->
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests proving my fix/feature works
- [ ] New and existing tests pass locally

## Related Issues
<!-- Link related issues: Closes #123 -->
```

## Managing Pull Requests

### Viewing PRs

```bash
# List open PRs
gh pr list

# List PRs with filters
gh pr list --state open --author "@me"
gh pr list --label "bug"
gh pr list --search "is:open review-requested:@me"

# View specific PR
gh pr view 123

# View PR in browser
gh pr view 123 --web

# View PR diff
gh pr diff 123

# View PR checks
gh pr checks 123
```

### Updating PRs

```bash
# Add more commits
git add .
git commit -m "address review feedback"
git push origin feature-branch

# Force push after rebase (careful!)
git rebase main
git push --force-with-lease origin feature-branch

# Update PR title/body
gh pr edit 123 --title "New title"
gh pr edit 123 --body "New description"

# Add labels
gh pr edit 123 --add-label "needs-review"

# Add reviewers
gh pr edit 123 --add-reviewer user1
```

### Reviewing PRs

```bash
# Start review
gh pr review 123

# Approve PR
gh pr review 123 --approve

# Request changes
gh pr review 123 --request-changes --body "Please fix X"

# Comment without approval
gh pr review 123 --comment --body "Looks good, minor suggestion..."

# View PR files changed
gh pr diff 123
```

### Merging PRs

```bash
# Merge with merge commit
gh pr merge 123 --merge

# Squash and merge
gh pr merge 123 --squash

# Rebase and merge
gh pr merge 123 --rebase

# Merge and delete branch
gh pr merge 123 --squash --delete-branch

# Auto-merge when checks pass
gh pr merge 123 --auto --squash
```

## PR Best Practices

### PR Size Guidelines

```
┌─────────────────────────────────────────────────────────────────┐
│                    PR Size Guidelines                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ideal Size:                                                    │
│  • 50-200 lines of code (excluding tests)                       │
│  • 1-2 hours to review                                          │
│  • Single responsibility                                        │
│                                                                  │
│  Maximum Size:                                                  │
│  • 400 lines of code                                            │
│  • 4 hours to review                                            │
│  • Consider breaking up                                         │
│                                                                  │
│  Breaking Up Large PRs:                                         │
│  • Split by feature area                                        │
│  • Split frontend/backend                                       │
│  • Split implementation/tests                                   │
│  • Use stacked PRs                                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Stacked PRs

```bash
# PR 1: Foundation
git checkout -b feature/auth-foundation main
# Add base models, interfaces
git push -u origin feature/auth-foundation
gh pr create --title "Auth: Foundation" --base main

# PR 2: Implementation (depends on PR 1)
git checkout -b feature/auth-implementation feature/auth-foundation
# Add implementation
git push -u origin feature/auth-implementation
gh pr create --title "Auth: Implementation" --base feature/auth-foundation

# PR 3: Tests (depends on PR 2)
git checkout -b feature/auth-tests feature/auth-implementation
# Add tests
git push -u origin feature/auth-tests
gh pr create --title "Auth: Tests" --base feature/auth-implementation

# After PR 1 merges, update PR 2's base to main
gh pr edit <pr2-number> --base main
git rebase main
git push --force-with-lease
```

### Draft PRs

```bash
# Create draft PR for early feedback
gh pr create --draft --title "WIP: New feature"

# Convert draft to ready for review
gh pr ready 123

# Good uses for draft PRs:
# - Get early feedback on approach
# - Show work in progress
# - Run CI without requesting review
# - Discuss implementation before finishing
```

## PR Automation

### GitHub Actions for PRs

```yaml
# .github/workflows/pr.yml
name: PR Checks

on:
  pull_request:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm test

  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm ci
      - run: npm run build

  pr-size:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Check PR size
        run: |
          LINES=$(git diff --numstat origin/main | awk '{sum+=$1+$2} END {print sum}')
          if [ "$LINES" -gt 1000 ]; then
            echo "::warning::PR is large ($LINES lines). Consider breaking it up."
          fi
```

### Auto-labeling

```yaml
# .github/labeler.yml
frontend:
  - 'src/components/**/*'
  - 'src/styles/**/*'
  - '*.css'
  - '*.tsx'

backend:
  - 'src/api/**/*'
  - 'src/services/**/*'
  - 'src/models/**/*'

documentation:
  - 'docs/**/*'
  - '*.md'

tests:
  - 'tests/**/*'
  - '**/*.test.ts'
  - '**/*.spec.ts'
```

## PR Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│                    PR Checklist                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before Creating PR:                                            │
│  □ Code compiles without errors                                 │
│  □ All tests pass locally                                       │
│  □ Linting passes                                               │
│  □ Branch is up to date with target                             │
│  □ Self-reviewed the diff                                       │
│                                                                  │
│  PR Description:                                                │
│  □ Clear, descriptive title                                     │
│  □ Explains what and why                                        │
│  □ Lists all changes                                            │
│  □ Includes testing instructions                                │
│  □ Links related issues                                         │
│  □ Screenshots if UI changes                                    │
│                                                                  │
│  During Review:                                                 │
│  □ Respond to all comments                                      │
│  □ Update code based on feedback                                │
│  □ Re-request review after changes                              │
│  □ Don't merge until approved                                   │
│                                                                  │
│  After Merge:                                                   │
│  □ Delete feature branch                                        │
│  □ Update local main branch                                     │
│  □ Verify deployment (if applicable)                            │
│  □ Close related issues                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
