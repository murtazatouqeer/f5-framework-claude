---
name: branching
description: Creating and managing Git branches
category: git/fundamentals
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Branching

## Overview

Branches allow parallel development by creating independent lines of work.
They're lightweight pointers to commits, making them fast to create and switch.

## Branch Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                     Branch Model                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  main          A───B───C───────────────G───H                    │
│                        \              /                         │
│  feature               D───E───F────┘                          │
│                                                                  │
│  Legend:                                                        │
│  • Letters are commits                                          │
│  • main and feature are branch pointers                         │
│  • G is a merge commit                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Creating Branches

### Basic Branch Creation

```bash
# Create new branch (stays on current branch)
git branch feature-login

# Create and switch to new branch
git checkout -b feature-login
# or (Git 2.23+)
git switch -c feature-login

# Create branch from specific commit
git branch feature-login abc123

# Create branch from another branch
git branch feature-login develop

# Create branch from remote branch
git branch feature-login origin/feature-login

# Create and track remote branch
git checkout -b feature-login origin/feature-login
# or
git switch -c feature-login origin/feature-login
```

### Creating Orphan Branches

```bash
# Create branch with no history (for gh-pages, docs, etc.)
git checkout --orphan gh-pages

# Remove all files from staging
git rm -rf .

# Now add files for this branch
echo "Documentation" > README.md
git add README.md
git commit -m "Initial docs commit"
```

## Switching Branches

```bash
# Switch to existing branch
git checkout feature-login
# or (Git 2.23+)
git switch feature-login

# Switch to previous branch
git checkout -
# or
git switch -

# Switch and discard local changes
git checkout -f feature-login
# or
git switch -f feature-login

# Create branch if it doesn't exist, switch if it does
git switch -c feature-login 2>/dev/null || git switch feature-login
```

## Listing Branches

```bash
# List local branches
git branch

# List remote branches
git branch -r

# List all branches (local and remote)
git branch -a

# List branches with last commit info
git branch -v

# List branches with tracking info
git branch -vv

# List merged branches
git branch --merged

# List unmerged branches
git branch --no-merged

# List branches containing specific commit
git branch --contains abc123

# Filter branches by pattern
git branch --list "feature/*"
```

## Branch Information

```bash
# Show current branch
git branch --show-current
# or
git rev-parse --abbrev-ref HEAD

# Show branch commit
git rev-parse feature-login

# Show branch details
git show-branch feature-login

# Compare branches
git log main..feature-login

# Show commits in feature not in main
git log feature-login ^main

# Show commits in either but not both
git log main...feature-login

# Show graph of branch history
git log --oneline --graph --all
```

## Renaming Branches

```bash
# Rename current branch
git branch -m new-name

# Rename specific branch
git branch -m old-name new-name

# Rename branch and update remote
git branch -m old-name new-name
git push origin -u new-name
git push origin --delete old-name
```

## Deleting Branches

```bash
# Delete merged branch
git branch -d feature-login

# Force delete unmerged branch
git branch -D feature-login

# Delete remote branch
git push origin --delete feature-login
# or
git push origin :feature-login

# Delete all merged branches (except main/develop)
git branch --merged | grep -v "main\|develop" | xargs git branch -d

# Prune deleted remote branches locally
git fetch --prune
# or
git remote prune origin
```

## Tracking Branches

```bash
# Set up tracking for existing branch
git branch -u origin/feature-login
# or
git branch --set-upstream-to=origin/feature-login

# Create branch with tracking
git checkout -b feature-login origin/feature-login

# Push and set tracking
git push -u origin feature-login

# Show tracking info
git branch -vv

# Remove tracking
git branch --unset-upstream
```

## Branch Protection

### Remote Branch Protection (GitHub/GitLab)

```yaml
# .github/settings.yml (GitHub)
branches:
  - name: main
    protection:
      required_pull_request_reviews:
        required_approving_review_count: 2
        dismiss_stale_reviews: true
        require_code_owner_reviews: true
      required_status_checks:
        strict: true
        contexts:
          - ci/tests
          - ci/lint
      enforce_admins: true
      restrictions:
        users: []
        teams: []
```

### Pre-push Hook for Protection

```bash
#!/bin/sh
# .git/hooks/pre-push

protected_branches=("main" "develop" "release")
current_branch=$(git rev-parse --abbrev-ref HEAD)

for branch in "${protected_branches[@]}"; do
  if [ "$current_branch" = "$branch" ]; then
    echo "Direct push to $branch is not allowed!"
    echo "Please create a pull request."
    exit 1
  fi
done
```

## Branch Strategies

### Feature Branch

```bash
# Create feature branch from develop
git checkout develop
git pull origin develop
git checkout -b feature/user-authentication

# Work on feature
# ... make commits ...

# Keep up to date with develop
git fetch origin
git rebase origin/develop

# Push and create PR
git push -u origin feature/user-authentication
```

### Hotfix Branch

```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# Fix the issue
# ... make commits ...

# Push for urgent review
git push -u origin hotfix/critical-security-fix

# After merge, tag the release
git checkout main
git pull origin main
git tag -a v1.2.1 -m "Hotfix release"
git push origin v1.2.1
```

### Release Branch

```bash
# Create release branch from develop
git checkout develop
git pull origin develop
git checkout -b release/v2.0.0

# Final preparations
# - Version bumps
# - Changelog updates
# - Bug fixes only

# Merge to main
git checkout main
git merge --no-ff release/v2.0.0
git tag -a v2.0.0 -m "Release version 2.0.0"

# Merge back to develop
git checkout develop
git merge --no-ff release/v2.0.0

# Clean up
git branch -d release/v2.0.0
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Branching Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Keep Branches Short-Lived                                   │
│     └── Merge frequently to avoid drift                         │
│                                                                  │
│  2. Use Descriptive Names                                       │
│     └── feature/add-login, bugfix/null-pointer                  │
│                                                                  │
│  3. Branch from Latest                                          │
│     └── Always pull before creating new branch                  │
│                                                                  │
│  4. One Purpose Per Branch                                      │
│     └── Don't mix features in same branch                       │
│                                                                  │
│  5. Delete After Merge                                          │
│     └── Keep branch list clean                                  │
│                                                                  │
│  6. Protect Main Branches                                       │
│     └── Require PRs for main/develop                            │
│                                                                  │
│  7. Rebase Before Merge                                         │
│     └── Keep history clean                                      │
│                                                                  │
│  8. Use Consistent Naming                                       │
│     └── Agree on convention with team                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Aliases

```bash
# ~/.gitconfig
[alias]
  # Branch shortcuts
  b = branch
  ba = branch -a
  bd = branch -d
  bD = branch -D

  # Switch shortcuts
  co = checkout
  cob = checkout -b
  sw = switch
  swc = switch -c

  # Show branches with details
  branches = branch -vv

  # Delete merged branches
  cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"

  # Show branch graph
  tree = log --oneline --graph --all --decorate
```
