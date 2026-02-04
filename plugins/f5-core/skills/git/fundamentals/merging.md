---
name: merging
description: Combining branches and handling merges
category: git/fundamentals
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Merging

## Overview

Merging combines the work from different branches into one. Git provides
multiple merge strategies to handle different scenarios.

## Merge Types

```
┌─────────────────────────────────────────────────────────────────┐
│                       Merge Types                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Fast-Forward Merge                                             │
│  ─────────────────                                              │
│  main:    A───B───C                                             │
│  feature:         └───D───E                                     │
│                                                                  │
│  After fast-forward:                                            │
│  main:    A───B───C───D───E                                     │
│                                                                  │
│  Three-Way Merge                                                │
│  ───────────────                                                │
│  main:    A───B───C───────F (merge commit)                      │
│  feature:     └───D───E──┘                                      │
│                                                                  │
│  Squash Merge                                                   │
│  ────────────                                                   │
│  main:    A───B───C───S (single commit with all changes)        │
│  feature:     └───D───E (branch unchanged, usually deleted)     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Merging

### Fast-Forward Merge

```bash
# When there are no new commits on target branch
git checkout main
git merge feature
# Git automatically fast-forwards

# Force a merge commit even when fast-forward possible
git merge --no-ff feature
```

### Three-Way Merge

```bash
# Standard merge creating merge commit
git checkout main
git merge feature

# Merge commit is created automatically when:
# - Both branches have new commits
# - Using --no-ff flag
```

### Merge with Message

```bash
# Specify merge commit message
git merge feature -m "Merge feature/authentication into main"

# Open editor for merge message
git merge feature --edit
```

## Squash Merge

```bash
# Combine all commits into one
git checkout main
git merge --squash feature

# This stages all changes but doesn't commit
# Now create a single commit
git commit -m "feat: add authentication feature"

# Original branch is not modified
# Usually delete after squash merge
git branch -d feature
```

### When to Use Squash

```
┌─────────────────────────────────────────────────────────────────┐
│                When to Use Squash Merge                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Good for:                                                   │
│  • Feature branches with messy history                          │
│  • WIP commits you want to clean up                             │
│  • Maintaining clean main branch history                        │
│  • PRs from external contributors                               │
│                                                                  │
│  ❌ Avoid when:                                                 │
│  • Commits are already clean and meaningful                     │
│  • You need to preserve individual commit history               │
│  • The branch will be merged elsewhere                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Merge Strategies

### Recursive (Default)

```bash
# Default strategy for two branches
git merge -s recursive feature

# With options
git merge -s recursive -X ours feature    # Prefer our changes
git merge -s recursive -X theirs feature  # Prefer their changes
git merge -s recursive -X patience feature # Better diff algorithm
```

### Ours Strategy

```bash
# Keep our version entirely, ignore theirs
git merge -s ours feature

# Useful for:
# - Marking a branch as merged without changes
# - Superseding a branch with current state
```

### Octopus Strategy

```bash
# Merge multiple branches at once
git merge -s octopus feature1 feature2 feature3

# Only works if there are no conflicts
# Good for integrating multiple independent features
```

### Subtree Strategy

```bash
# Merge into a subdirectory
git merge -s subtree --allow-unrelated-histories library-repo

# Useful for including external repos as subdirectories
```

## Handling Merge Commits

### Viewing Merge Commits

```bash
# Show merge commits in log
git log --merges

# Show non-merge commits only
git log --no-merges

# Show merge commit details
git show <merge-commit>

# Show parents of merge commit
git cat-file -p <merge-commit>
```

### Reverting Merge Commits

```bash
# Revert a merge commit
# -m 1 means keep parent 1 (usually main)
git revert -m 1 <merge-commit>

# -m 2 would keep the feature branch parent
git revert -m 2 <merge-commit>
```

## Aborting Merges

```bash
# Abort merge in progress
git merge --abort

# Reset to pre-merge state
git reset --merge

# Reset to specific commit (destructive)
git reset --hard HEAD
```

## Merge Verification

### Before Merging

```bash
# Check what will be merged
git log main..feature

# Preview merge result (dry run)
git merge --no-commit --no-ff feature
# Review changes
git diff --cached
# Then abort or commit
git merge --abort
# or
git commit
```

### After Merging

```bash
# Verify merge was successful
git log --oneline -5

# Check for any unintended changes
git diff HEAD~1

# Run tests
npm test
```

## Merge Workflows

### Feature to Develop

```bash
# Update local develop
git checkout develop
git pull origin develop

# Merge feature branch
git merge --no-ff feature/user-auth

# Push merged develop
git push origin develop

# Delete feature branch
git branch -d feature/user-auth
git push origin --delete feature/user-auth
```

### Develop to Main (Release)

```bash
# Update both branches
git checkout main
git pull origin main
git checkout develop
git pull origin develop

# Merge develop to main
git checkout main
git merge --no-ff develop -m "Release v1.2.0"

# Tag the release
git tag -a v1.2.0 -m "Version 1.2.0"

# Push everything
git push origin main
git push origin v1.2.0
```

### Pull Request Merge Strategies

```bash
# Create Merge Commit (preserves all history)
git merge --no-ff feature

# Squash and Merge (single commit)
git merge --squash feature
git commit -m "feat: add feature (#123)"

# Rebase and Merge (linear history)
git checkout feature
git rebase main
git checkout main
git merge --ff-only feature
```

## Merge vs Rebase

```
┌─────────────────────────────────────────────────────────────────┐
│                   Merge vs Rebase                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Merge                          Rebase                          │
│  ─────                          ──────                          │
│  • Preserves history            • Rewrites history              │
│  • Creates merge commits        • Linear history                │
│  • Non-destructive              • Can lose context              │
│  • Good for public branches     • Good for local branches       │
│                                                                  │
│  Use Merge:                     Use Rebase:                     │
│  • Feature into main            • Updating feature branch       │
│  • When history matters         • Before creating PR            │
│  • Public/shared branches       • Local branches only           │
│                                                                  │
│  Golden Rule:                                                   │
│  Never rebase commits that have been pushed to a shared repo!   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   Merge Best Practices                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Pull Before Merge                                           │
│     └── Always have latest changes                              │
│                                                                  │
│  2. Use --no-ff for Features                                    │
│     └── Preserves branch history in graph                       │
│                                                                  │
│  3. Write Good Merge Messages                                   │
│     └── Explain what was merged and why                         │
│                                                                  │
│  4. Test After Merge                                            │
│     └── Run tests before pushing                                │
│                                                                  │
│  5. Delete Merged Branches                                      │
│     └── Keep repository clean                                   │
│                                                                  │
│  6. Review Before Merge                                         │
│     └── Use PRs for code review                                 │
│                                                                  │
│  7. Squash Messy Branches                                       │
│     └── Clean up WIP commits                                    │
│                                                                  │
│  8. Don't Merge Conflicts Blindly                               │
│     └── Understand what you're resolving                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Aliases

```bash
# ~/.gitconfig
[alias]
  # Merge shortcuts
  m = merge
  mnf = merge --no-ff
  ms = merge --squash
  ma = merge --abort

  # Merge preview
  mp = "!f() { git merge --no-commit --no-ff $1 && git diff --cached; }; f"

  # Safe merge (only if fast-forward)
  mff = merge --ff-only

  # Show merge commits
  merges = log --merges --oneline
```
