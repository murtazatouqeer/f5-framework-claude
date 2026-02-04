---
name: rebasing
description: Rebasing branches for cleaner history
category: git/advanced
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Rebasing

## Overview

Rebasing is the process of moving or combining a sequence of commits to a new
base commit. It creates a linear project history and can make complex
histories easier to understand.

## Rebase vs Merge

```
┌─────────────────────────────────────────────────────────────────┐
│                    Merge vs Rebase                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  MERGE (preserves history):                                     │
│                                                                  │
│  main     ──●────●────●─────────●──────▶                        │
│              \              /                                    │
│  feature      ●────●────●                                        │
│                         (merge commit)                           │
│                                                                  │
│  REBASE (linear history):                                       │
│                                                                  │
│  main     ──●────●────●──▶                                      │
│                        \                                         │
│  feature               ●'───●'───●'──▶                          │
│                        (commits replayed)                        │
│                                                                  │
│  After fast-forward merge:                                      │
│  main     ──●────●────●────●'───●'───●'──▶                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Rebasing

### Rebase onto Main

```bash
# On feature branch
git checkout feature/user-auth
git rebase main

# What happens:
# 1. Git finds common ancestor of feature and main
# 2. Gets the diff of each commit on feature
# 3. Resets feature to point to main
# 4. Applies each diff as new commit

# After rebase, fast-forward merge is possible
git checkout main
git merge feature/user-auth  # Fast-forward merge
```

### Rebase onto Specific Commit

```bash
# Rebase onto specific commit
git rebase abc123

# Rebase onto tag
git rebase v1.0.0
```

### Rebase with Different Branch

```bash
# Rebase current branch onto different branch
git rebase develop

# Rebase specific branch onto another
git rebase main feature/user-auth
# This rebases feature/user-auth onto main
```

## Handling Conflicts

### During Rebase

```bash
# When conflict occurs during rebase
git rebase main
# CONFLICT (content): Merge conflict in file.js

# 1. View conflicting files
git status

# 2. Resolve conflicts in each file
# Edit files, remove conflict markers

# 3. Stage resolved files
git add file.js

# 4. Continue rebase
git rebase --continue

# Or abort if too complex
git rebase --abort

# Skip the problematic commit (lose its changes)
git rebase --skip
```

### Conflict Resolution Tips

```bash
# See what commits will be rebased
git log main..HEAD --oneline

# During conflict, see original versions
git show :1:file.js   # Common ancestor
git show :2:file.js   # Ours (HEAD)
git show :3:file.js   # Theirs (incoming)

# Use merge tool
git mergetool
```

## Rebase Options

### Preserve Merge Commits

```bash
# Keep merge commits during rebase
git rebase --rebase-merges main
# Or shorter form
git rebase -r main

# Useful when rebasing a branch that has merges
```

### Keep Empty Commits

```bash
# By default, empty commits are dropped
# To keep them:
git rebase --keep-empty main
```

### Apply Root Commits

```bash
# Rebase including root commit
git rebase --root
```

### Onto Option

```bash
# Rebase subset of commits
# Syntax: git rebase --onto <newbase> <oldbase> <branch>

# Example: Move commits from feature to main, excluding develop
git rebase --onto main develop feature

# Before:
# main     ──●──●──▶
#             \
# develop      ●──●──▶
#                  \
# feature           ●──●──●──▶

# After:
# main     ──●──●──●'──●'──●'──▶ (feature rebased onto main)
#             \
# develop      ●──●──▶
```

## Rebasing Workflows

### Update Feature Branch

```bash
# Regular workflow to keep feature branch updated
git checkout feature/my-feature
git fetch origin
git rebase origin/main

# If conflicts, resolve and continue
git add .
git rebase --continue

# Push (force required since history changed)
git push --force-with-lease origin feature/my-feature
```

### Squash Before Merge

```bash
# Clean up commits before merging to main
git checkout feature/my-feature
git rebase -i main

# In editor, mark commits to squash
# pick abc123 Initial feature work
# squash def456 Fix typo
# squash ghi789 More fixes

# Result: Single clean commit for feature
```

### Pull with Rebase

```bash
# Instead of merge on pull
git pull --rebase origin main

# Set as default for branch
git config branch.main.rebase true

# Set as default globally
git config --global pull.rebase true
```

## Golden Rule of Rebasing

```
┌─────────────────────────────────────────────────────────────────┐
│                 Golden Rule of Rebasing                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ⚠️  NEVER rebase commits that exist outside your repository   │
│       and that others may have based their work on.              │
│                                                                  │
│   Safe to Rebase:                                                │
│   ✅ Local commits not yet pushed                                │
│   ✅ Your feature branch only you're working on                  │
│   ✅ Before opening a pull request                               │
│                                                                  │
│   NEVER Rebase:                                                  │
│   ❌ main or develop branches                                    │
│   ❌ Commits already pushed and used by others                   │
│   ❌ Shared feature branches without coordination                │
│                                                                  │
│   Why?                                                           │
│   Rebasing rewrites commit history (new SHA hashes).             │
│   Others who have the old commits will have problems when        │
│   they try to sync with the rewritten history.                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Recovering from Bad Rebase

### Using Reflog

```bash
# Find the state before rebase
git reflog
# abc123 HEAD@{0}: rebase finished
# def456 HEAD@{1}: rebase: checkout main
# ghi789 HEAD@{2}: commit: my last commit before rebase

# Reset to pre-rebase state
git reset --hard ghi789

# Or use ORIG_HEAD (set before rebase)
git reset --hard ORIG_HEAD
```

### Abort During Rebase

```bash
# If still in rebase process
git rebase --abort

# Returns to state before rebase started
```

## Advanced Rebase Scenarios

### Rebase with Autostash

```bash
# Automatically stash/unstash local changes
git rebase --autostash main

# Equivalent to:
git stash
git rebase main
git stash pop
```

### Rebase with Strategy

```bash
# Use specific merge strategy
git rebase -X theirs main    # Prefer incoming changes
git rebase -X ours main      # Prefer current changes

# Ignore whitespace changes
git rebase -X ignore-space-change main
```

### Exec During Rebase

```bash
# Run command after each commit during rebase
git rebase -x "npm test" main

# Useful for verifying each commit still works
# If command fails, rebase pauses for fixes
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Rebase Best Practices                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Rebase Early and Often                                      │
│     └── Keep feature branches up to date with main              │
│                                                                  │
│  2. Clean Before Sharing                                        │
│     └── Interactive rebase to clean up commits before PR        │
│                                                                  │
│  3. Never Rebase Public Branches                                │
│     └── main, develop, release branches are off limits          │
│                                                                  │
│  4. Use --force-with-lease                                      │
│     └── Safer than --force, won't overwrite others' work        │
│                                                                  │
│  5. Communicate with Team                                       │
│     └── Coordinate when rebasing shared feature branches        │
│                                                                  │
│  6. Create Backup Branches                                      │
│     └── git branch backup-feature before complex rebases        │
│                                                                  │
│  7. Test After Rebase                                           │
│     └── Run tests to ensure nothing broke                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Commands Reference

```bash
# Basic rebase
git rebase <base>

# Interactive rebase
git rebase -i <base>

# Continue after conflict
git rebase --continue

# Abort rebase
git rebase --abort

# Skip problematic commit
git rebase --skip

# Rebase with autostash
git rebase --autostash <base>

# Preserve merges
git rebase --rebase-merges <base>

# Rebase onto different base
git rebase --onto <new> <old> <branch>

# Pull with rebase
git pull --rebase

# Push rebased branch
git push --force-with-lease
```
