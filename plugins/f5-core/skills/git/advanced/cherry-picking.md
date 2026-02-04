---
name: cherry-picking
description: Applying specific commits to different branches
category: git/advanced
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Cherry-Picking

## Overview

Cherry-picking allows you to apply specific commits from one branch to another
without merging the entire branch. This is useful for applying bug fixes,
moving commits between branches, or selectively integrating changes.

## Cherry-Pick Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                    Cherry-Pick Concept                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before:                                                        │
│  main     ──●──●──●──▶                                          │
│               \                                                  │
│  feature       ●──●──●──●──▶                                    │
│                   A  B  C                                        │
│                                                                  │
│  Cherry-pick B to main:                                         │
│  git checkout main                                              │
│  git cherry-pick <commit-B>                                     │
│                                                                  │
│  After:                                                         │
│  main     ──●──●──●──B'──▶                                      │
│               \                                                  │
│  feature       ●──●──●──●──▶                                    │
│                   A  B  C                                        │
│                                                                  │
│  Note: B' is a NEW commit with same changes as B                │
│        but different SHA hash                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Cherry-Picking

### Single Commit

```bash
# Switch to target branch
git checkout main

# Cherry-pick a specific commit
git cherry-pick abc123

# Cherry-pick most recent commit from branch
git cherry-pick feature-branch

# Cherry-pick commit from another remote
git cherry-pick origin/feature/abc123
```

### Multiple Commits

```bash
# Cherry-pick multiple specific commits
git cherry-pick abc123 def456 ghi789

# Cherry-pick a range of commits
git cherry-pick abc123..ghi789
# Note: abc123 is NOT included, ghi789 IS included

# Include the first commit in range
git cherry-pick abc123^..ghi789

# Cherry-pick all commits from branch (since diverged from main)
git cherry-pick main..feature-branch
```

### From Different Branch

```bash
# Get commit hash from another branch
git log feature-branch --oneline
# abc123 Fix critical bug
# def456 Add new feature

# Cherry-pick to current branch
git cherry-pick abc123
```

## Cherry-Pick Options

### No Commit (Stage Only)

```bash
# Apply changes but don't commit
git cherry-pick abc123 --no-commit
# Or
git cherry-pick abc123 -n

# Useful for:
# - Combining multiple cherry-picks into one commit
# - Modifying changes before committing
# - Applying partial changes

# Then commit manually
git commit -m "Combined cherry-picked changes"
```

### Edit Commit Message

```bash
# Edit message during cherry-pick
git cherry-pick abc123 --edit
# Or
git cherry-pick abc123 -e

# Opens editor to modify commit message
```

### Preserve Original Author

```bash
# By default, cherry-pick preserves original author
# Committer becomes you, author stays original

# To also preserve committer (not typical)
git cherry-pick abc123 --no-commit
git commit --author="Original Author <email@example.com>"
```

### Append to Commit Message

```bash
# Add source info to commit message
git cherry-pick abc123 -x

# Adds line like:
# (cherry picked from commit abc123...)

# Useful for tracking where changes came from
```

### Signoff

```bash
# Add Signed-off-by line
git cherry-pick abc123 -s

# Adds:
# Signed-off-by: Your Name <your@email.com>
```

## Handling Conflicts

### During Cherry-Pick

```bash
# When conflict occurs
git cherry-pick abc123
# CONFLICT (content): Merge conflict in file.js

# 1. Check status
git status

# 2. Resolve conflicts in files
# Edit files to resolve

# 3. Stage resolved files
git add file.js

# 4. Continue cherry-pick
git cherry-pick --continue

# Or abort
git cherry-pick --abort

# Skip this commit
git cherry-pick --skip
```

### Conflict Prevention

```bash
# Preview changes before cherry-picking
git show abc123

# Check if commit exists on current branch
git branch --contains abc123

# Compare branches
git log main..feature-branch --oneline
```

## Advanced Cherry-Picking

### Cherry-Pick Merge Commits

```bash
# Merge commits have multiple parents
# Must specify which parent to use

# -m 1: Use first parent (main branch in merge)
git cherry-pick abc123 -m 1

# -m 2: Use second parent (merged branch)
git cherry-pick abc123 -m 2

# Example:
# If abc123 is: "Merge feature into main"
# -m 1 gives changes from feature's perspective
```

### Cherry-Pick Strategy

```bash
# Use specific merge strategy
git cherry-pick abc123 -X theirs  # Prefer cherry-picked changes
git cherry-pick abc123 -X ours    # Prefer current changes
```

### Interactive Range

```bash
# Cherry-pick multiple, choosing which to apply
git cherry-pick abc123^..ghi789 --no-commit

# Then review and selectively stage
git status
git diff --staged
git commit -m "Selected changes"
```

## Common Use Cases

### Hotfix to Multiple Branches

```bash
# Apply hotfix to release branches
git checkout release/1.0
git cherry-pick abc123  # hotfix commit

git checkout release/1.1
git cherry-pick abc123

git checkout main
git cherry-pick abc123
```

### Move Commit to Correct Branch

```bash
# Committed to wrong branch
git checkout wrong-branch
git log --oneline
# abc123 Accidental commit here

# Move to correct branch
git checkout correct-branch
git cherry-pick abc123

# Remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1
```

### Backport to Older Version

```bash
# Backport feature from main to older release
git checkout release/1.0

# Find commits to backport
git log main --oneline | grep "feature"
# abc123 Add important feature

git cherry-pick abc123

# May need conflict resolution for older codebase
```

### Extract Specific Changes

```bash
# Pull specific fixes from feature branch
git checkout main

# Cherry-pick only bug fixes, not new features
git cherry-pick fix-commit-1
git cherry-pick fix-commit-2
# Skip feature commits
```

## Cherry-Pick Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                 Cherry-Pick Workflow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Identify the Commit                                         │
│     git log --oneline <source-branch>                           │
│                                                                  │
│  2. Switch to Target Branch                                     │
│     git checkout <target-branch>                                │
│                                                                  │
│  3. Cherry-Pick the Commit                                      │
│     git cherry-pick <commit-hash>                               │
│                                                                  │
│  4. Handle Conflicts (if any)                                   │
│     - Resolve conflicts                                         │
│     - git add <resolved-files>                                  │
│     - git cherry-pick --continue                                │
│                                                                  │
│  5. Verify                                                      │
│     git log --oneline                                           │
│     git diff HEAD~1                                             │
│                                                                  │
│  6. Push                                                        │
│     git push origin <target-branch>                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│               Cherry-Pick Best Practices                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Use Cherry-Pick For:                                           │
│  ✅ Hotfixes that need to go to multiple branches               │
│  ✅ Backporting specific changes to older releases              │
│  ✅ Moving commits accidentally made to wrong branch            │
│  ✅ Extracting useful commits from abandoned branches           │
│                                                                  │
│  Avoid Cherry-Pick For:                                         │
│  ❌ Regular integration (use merge or rebase)                   │
│  ❌ Large number of commits (merge the branch)                  │
│  ❌ Commits with complex dependencies                           │
│                                                                  │
│  Tips:                                                          │
│  • Use -x to track origin of cherry-picked commits              │
│  • Test after cherry-picking                                    │
│  • Document why commits were cherry-picked                      │
│  • Consider creating a tracking issue/ticket                    │
│  • Be aware that cherry-picked commits create duplicates        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Potential Issues

### Duplicate Commits

```bash
# Cherry-picking creates duplicate commits
# Same changes exist in both branches with different SHAs

# Can cause confusion in git log
# May cause conflicts if branches are later merged

# Track with -x flag
git cherry-pick abc123 -x
# Message includes "(cherry picked from commit abc123)"
```

### Dependency Issues

```bash
# Commit B depends on changes from Commit A
# Cherry-picking only B may not work

# Solution 1: Cherry-pick both
git cherry-pick A B

# Solution 2: Cherry-pick range
git cherry-pick A^..B

# Solution 3: Merge the branch instead
git merge feature-branch
```

## Useful Commands Reference

```bash
# Basic cherry-pick
git cherry-pick <commit>

# Multiple commits
git cherry-pick <commit1> <commit2>

# Range of commits
git cherry-pick <start>^..<end>

# No commit (stage only)
git cherry-pick -n <commit>

# Edit message
git cherry-pick -e <commit>

# Track origin
git cherry-pick -x <commit>

# Merge commit
git cherry-pick -m <parent-number> <merge-commit>

# Continue after conflict
git cherry-pick --continue

# Abort cherry-pick
git cherry-pick --abort

# Skip commit
git cherry-pick --skip
```
