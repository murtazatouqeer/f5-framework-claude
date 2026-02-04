---
name: feature-branches
description: Feature branch workflow for team collaboration
category: git/workflows
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Feature Branch Workflow

## Overview

Feature Branch Workflow is a Git workflow where all feature development takes
place in dedicated branches instead of the main branch. This enables multiple
developers to work on features independently.

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                  Feature Branch Workflow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  main        ──●────●────●────────●─────────●────●─────────●──▶ │
│               │          │        ↑         ↑    ↑         ↑    │
│               │          │        │         │    │         │    │
│  feature-1    └──●───●───●────────┘         │    │         │    │
│                  │   │   │                  │    │         │    │
│                  └───┴───┘ PR + Review      │    │         │    │
│                                             │    │         │    │
│  feature-2            └───●───●───●─────────┘    │         │    │
│                           │   │   │              │         │    │
│                           └───┴───┘ PR + Review  │         │    │
│                                                  │         │    │
│  feature-3                     └───●───●───●─────┘         │    │
│                                    │   │   │               │    │
│                                    └───┴───┘ PR + Review   │    │
│                                                            │    │
│  bugfix-1                               └───●───●──────────┘    │
│                                             │   │               │
│                                             └───┘ Quick PR      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Branch Naming Convention

```
┌─────────────────────────────────────────────────────────────────┐
│                 Branch Naming Convention                         │
├──────────────────┬──────────────────────────────────────────────┤
│ Pattern          │ Examples                                     │
├──────────────────┼──────────────────────────────────────────────┤
│ feature/<name>   │ feature/user-authentication                  │
│                  │ feature/shopping-cart                        │
│                  │ feature/JIRA-123-add-search                  │
├──────────────────┼──────────────────────────────────────────────┤
│ bugfix/<name>    │ bugfix/login-redirect                        │
│                  │ bugfix/JIRA-456-null-pointer                 │
├──────────────────┼──────────────────────────────────────────────┤
│ hotfix/<name>    │ hotfix/security-patch                        │
│                  │ hotfix/critical-data-loss                    │
├──────────────────┼──────────────────────────────────────────────┤
│ chore/<name>     │ chore/update-dependencies                    │
│                  │ chore/cleanup-tests                          │
├──────────────────┼──────────────────────────────────────────────┤
│ docs/<name>      │ docs/api-documentation                       │
│                  │ docs/readme-update                           │
├──────────────────┼──────────────────────────────────────────────┤
│ refactor/<name>  │ refactor/database-layer                      │
│                  │ refactor/component-structure                 │
└──────────────────┴──────────────────────────────────────────────┘
```

## Complete Workflow

### 1. Start New Feature

```bash
# Update main branch
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/user-profile

# Verify branch
git branch
# * feature/user-profile
#   main
```

### 2. Develop Feature

```bash
# Make changes and commit frequently
git add src/components/Profile.tsx
git commit -m "feat(profile): add profile component skeleton"

git add src/api/profile.ts
git commit -m "feat(api): add profile API endpoints"

git add src/components/Profile.tsx src/styles/profile.css
git commit -m "feat(profile): implement profile form UI"

git add tests/profile.test.ts
git commit -m "test(profile): add profile component tests"
```

### 3. Keep Branch Updated

```bash
# Regularly sync with main
git fetch origin
git rebase origin/main

# Or use merge (preserves branch history)
git merge origin/main

# Resolve any conflicts if they occur
# ... fix conflicts ...
git add .
git rebase --continue
```

### 4. Push and Create PR

```bash
# Push feature branch
git push -u origin feature/user-profile

# Create pull request
gh pr create \
  --title "Add user profile feature" \
  --body "## Description
Implements user profile page with editing capabilities.

## Changes
- Add Profile component
- Add profile API endpoints
- Add form validation
- Add unit tests

## Testing
- Tested locally
- All tests pass

## Screenshots
[Add screenshots]

Closes #123"
```

### 5. Code Review

```bash
# Address review feedback
git add .
git commit -m "refactor(profile): address review feedback"
git push origin feature/user-profile

# Or amend if small changes
git add .
git commit --amend --no-edit
git push --force-with-lease origin feature/user-profile
```

### 6. Merge and Cleanup

```bash
# After approval, merge via GitHub/GitLab UI
# Or via CLI:
gh pr merge feature/user-profile --squash --delete-branch

# Update local main
git checkout main
git pull origin main

# Delete local branch
git branch -d feature/user-profile
```

## Handling Long-Running Features

### Strategy 1: Regular Rebasing

```bash
# Rebase onto main regularly (daily)
git checkout feature/large-feature
git fetch origin
git rebase origin/main

# Push with force-with-lease
git push --force-with-lease origin feature/large-feature
```

### Strategy 2: Integration Branch

```bash
# Create integration branch for large feature
git checkout -b integration/v2-redesign main

# Feature sub-branches merge to integration
git checkout -b feature/v2-header integration/v2-redesign
# ... work ...
git checkout integration/v2-redesign
git merge feature/v2-header

# Integration branch eventually merges to main
git checkout main
git merge integration/v2-redesign
```

### Strategy 3: Feature Flags

```bash
# Merge incomplete feature with flag
git checkout main
git merge feature/large-feature

# Code is deployed but hidden
if (featureFlags.isEnabled('V2_REDESIGN')) {
  // New feature code
}
```

## Branch Protection

### GitHub Settings

```yaml
# Repository Settings → Branches → Branch protection rules
branch_protection:
  pattern: main
  rules:
    - require_pull_request_reviews:
        required_approving_review_count: 1
        dismiss_stale_reviews: true
        require_code_owner_reviews: false
    - require_status_checks:
        strict: true
        checks:
          - ci/test
          - ci/lint
          - ci/build
    - require_conversation_resolution: true
    - require_signed_commits: false
    - require_linear_history: false
    - allow_force_pushes: false
    - allow_deletions: false
```

### Pre-push Hook

```bash
#!/bin/bash
# .git/hooks/pre-push

protected_branch='main'
current_branch=$(git symbolic-ref HEAD | sed -e 's,.*/\(.*\),\1,')

if [ $protected_branch = $current_branch ]; then
    echo "Direct push to main is not allowed."
    echo "Please create a pull request."
    exit 1
fi
```

## Merge Strategies

### Merge Commit

```bash
# Creates merge commit, preserves feature branch history
git checkout main
git merge --no-ff feature/user-profile

# Result:
# *   abc123 Merge branch 'feature/user-profile'
# |\
# | * def456 feat: add profile tests
# | * ghi789 feat: add profile UI
# | * jkl012 feat: add profile API
# |/
# * mno345 previous main commit
```

### Squash Merge

```bash
# Combines all commits into one
git checkout main
git merge --squash feature/user-profile
git commit -m "feat: add user profile feature"

# Result:
# * abc123 feat: add user profile feature
# * mno345 previous main commit
```

### Rebase Merge

```bash
# Replays commits on top of main
git checkout feature/user-profile
git rebase main
git checkout main
git merge --ff-only feature/user-profile

# Result:
# * abc123 feat: add profile tests
# * def456 feat: add profile UI
# * ghi789 feat: add profile API
# * mno345 previous main commit
```

## Team Collaboration

### Code Owners

```yaml
# .github/CODEOWNERS
# Default owners
*       @team-leads

# Frontend
/src/components/    @frontend-team
/src/styles/        @frontend-team

# Backend
/src/api/           @backend-team
/src/services/      @backend-team

# Infrastructure
/deploy/            @devops-team
/.github/           @devops-team

# Documentation
/docs/              @tech-writers
*.md                @tech-writers
```

### Review Assignment

```yaml
# .github/settings.yml
reviewers:
  # Auto-assign reviewers
  users: []
  teams:
    - developers
  # Require at least 1 review
  required: 1
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│             Feature Branch Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. One Feature Per Branch                                      │
│     └── Keep branches focused and small                         │
│                                                                  │
│  2. Descriptive Names                                           │
│     └── Include ticket number if available                      │
│                                                                  │
│  3. Keep Branches Short-Lived                                   │
│     └── Ideally < 1 week                                        │
│                                                                  │
│  4. Sync with Main Regularly                                    │
│     └── Rebase or merge daily                                   │
│                                                                  │
│  5. Small, Atomic Commits                                       │
│     └── Each commit should be meaningful                        │
│                                                                  │
│  6. Test Before Push                                            │
│     └── Run tests locally before pushing                        │
│                                                                  │
│  7. Write Good PR Descriptions                                  │
│     └── Help reviewers understand changes                       │
│                                                                  │
│  8. Delete After Merge                                          │
│     └── Keep repository clean                                   │
│                                                                  │
│  9. Use Draft PRs                                               │
│     └── For work-in-progress or early feedback                  │
│                                                                  │
│  10. Review Promptly                                            │
│      └── Don't block teammates                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Issues

### Stale Branch

```bash
# Branch is behind main
git checkout feature/old-feature
git fetch origin
git rebase origin/main

# Many conflicts - consider starting fresh
git checkout main
git pull origin main
git checkout -b feature/old-feature-v2

# Cherry-pick relevant commits from old branch
git cherry-pick abc123 def456
```

### Accidental Commit to Main

```bash
# If not pushed
git checkout main
git reset --soft HEAD~1
git checkout -b feature/accidental-work
git commit -m "feat: accidental commit"
git push -u origin feature/accidental-work

# If pushed (need to coordinate with team)
# Revert the commit
git revert HEAD
git push origin main
```
