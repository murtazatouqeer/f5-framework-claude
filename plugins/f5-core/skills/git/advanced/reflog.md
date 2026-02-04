---
name: reflog
description: Reference logs for recovery and history exploration
category: git/advanced
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Reflog

## Overview

The reflog (reference log) is Git's safety net. It records every change to
HEAD and branch tips, allowing you to recover from mistakes like accidental
resets, rebases, or deleted branches. Unlike regular history, reflog entries
are local and temporary.

## Understanding Reflog

```
┌─────────────────────────────────────────────────────────────────┐
│                  Git Reflog Concept                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Regular Git Log:                                               │
│  Shows commit history following parent pointers                 │
│                                                                  │
│  ●───●───●───●───● (HEAD)                                       │
│                                                                  │
│  Reflog:                                                        │
│  Shows every position HEAD has been at                          │
│                                                                  │
│  HEAD@{0}: checkout: moving from feature to main                │
│  HEAD@{1}: commit: add login feature                            │
│  HEAD@{2}: rebase finished                                      │
│  HEAD@{3}: commit: WIP work                                     │
│  HEAD@{4}: reset: moving to HEAD~3                              │
│  HEAD@{5}: commit: deleted commit (RECOVERABLE!)                │
│                                                                  │
│  Even "deleted" commits can be recovered if in reflog!          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Reflog Commands

### View Reflog

```bash
# Show HEAD reflog
git reflog

# Same as:
git reflog show HEAD

# Show reflog for specific branch
git reflog show main
git reflog show feature/auth

# Show reflog with dates
git reflog --date=relative
git reflog --date=iso

# Show reflog with full commit info
git reflog --all --oneline
```

### Reflog Output

```bash
$ git reflog
abc123 HEAD@{0}: commit: Add new feature
def456 HEAD@{1}: checkout: moving from feature to main
ghi789 HEAD@{2}: commit: Fix bug
jkl012 HEAD@{3}: rebase -i (finish): returning to refs/heads/feature
mno345 HEAD@{4}: rebase -i (squash): Add feature
pqr678 HEAD@{5}: rebase -i (start): checkout main
stu901 HEAD@{6}: reset: moving to HEAD~2

# Format: <sha> HEAD@{n}: <action>: <details>
# n = steps back in time (0 is most recent)
```

## Recovery Scenarios

### Recover from Hard Reset

```bash
# Accidentally reset --hard
git reset --hard HEAD~3

# Find the lost commit
git reflog
# abc123 HEAD@{0}: reset: moving to HEAD~3
# def456 HEAD@{1}: commit: Important work  <-- This was lost!

# Recover
git reset --hard def456
# Or
git reset --hard HEAD@{1}
```

### Recover Deleted Branch

```bash
# Accidentally deleted branch
git branch -D feature/important

# Find the branch's last commit
git reflog
# Look for commits from that branch

# Or search reflog for branch
git reflog | grep "feature/important"

# Recreate the branch
git branch feature/important abc123
```

### Recover from Bad Rebase

```bash
# Rebase went wrong
git rebase -i main
# Made mistakes during rebase

# Find state before rebase
git reflog
# abc123 HEAD@{0}: rebase -i (finish): ...
# def456 HEAD@{1}: rebase -i (start): checkout main
# ghi789 HEAD@{2}: commit: Last commit before rebase  <-- This!

# Restore pre-rebase state
git reset --hard ghi789

# Or use ORIG_HEAD (set before rebase)
git reset --hard ORIG_HEAD
```

### Recover from Bad Merge

```bash
# Merge created problems
git merge feature-branch

# Find pre-merge state
git reflog
# abc123 HEAD@{0}: merge feature-branch: ...
# def456 HEAD@{1}: commit: Before merge  <-- This!

# Undo merge
git reset --hard def456
```

### Recover Lost Stash

```bash
# Accidentally dropped stash
git stash drop

# Stash entries aren't in normal reflog
# But the commits exist in git's object store

# Find dangling commits
git fsck --unreachable | grep commit

# Check each commit
git show abc123

# If it's your stash, apply it
git stash apply abc123
```

## Reflog Syntax

### Time-Based References

```bash
# By position
HEAD@{0}        # Current HEAD
HEAD@{1}        # Previous position
HEAD@{5}        # 5 positions ago

# By time
HEAD@{yesterday}
HEAD@{1.week.ago}
HEAD@{2024-01-15}
HEAD@{1.hour.ago}

# Examples
git show HEAD@{yesterday}
git diff HEAD@{1.week.ago}
git log HEAD@{2.days.ago}..HEAD
```

### Branch Reflogs

```bash
# Branch-specific reflog
main@{0}           # Current main tip
main@{1}           # Previous main position
feature@{3}        # 3 positions ago on feature

# Where was main yesterday?
git show main@{yesterday}

# When did main point to abc123?
git reflog main | grep abc123
```

### Upstream References

```bash
# Remote tracking branch reflog
origin/main@{0}
origin/main@{1.week.ago}

# Check what remote looked like before fetch
git diff origin/main@{1}..origin/main
```

## Advanced Reflog Usage

### Search Reflog

```bash
# Search reflog for specific message
git reflog | grep "checkout"
git reflog | grep "reset"
git reflog | grep "merge"

# Find specific commit in reflog
git reflog | grep abc123

# Show reflog entries for specific file
git log -g --oneline -- path/to/file
```

### Reflog with Dates

```bash
# Show reflog with relative dates
git reflog --date=relative
# abc123 HEAD@{2 hours ago}: commit: Fix bug

# Show with ISO dates
git reflog --date=iso
# abc123 HEAD@{2024-01-15 14:30:22}: commit: Fix bug

# Show with human-readable dates
git reflog --date=human
# abc123 HEAD@{Jan 15 14:30}: commit: Fix bug
```

### Expire Reflog

```bash
# Reflog entries expire (default: 90 days for reachable, 30 for unreachable)

# View expire settings
git config gc.reflogExpire
git config gc.reflogExpireUnreachable

# Manually expire old entries
git reflog expire --expire=now --all

# Expire entries older than specific date
git reflog expire --expire=30.days.ago --all
```

### All Reflogs

```bash
# Show reflogs for all refs
git reflog --all

# Show reflogs for a specific ref
git reflog show refs/stash
```

## Recovery Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Reflog Recovery Best Practices                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Immediate Actions:                                             │
│  • Don't panic - reflog probably has your data                  │
│  • Don't run git gc - it can delete unreachable commits         │
│  • Check reflog immediately: git reflog                         │
│                                                                  │
│  Recovery Steps:                                                │
│  1. git reflog - find the commit you want                       │
│  2. Identify the correct HEAD@{n} reference                     │
│  3. git show HEAD@{n} - verify it's correct                     │
│  4. git reset --hard HEAD@{n} - restore (destructive)           │
│     or git branch recovery HEAD@{n} - safer approach            │
│                                                                  │
│  Prevention:                                                    │
│  • Create backup branches before risky operations               │
│  • Use --force-with-lease instead of --force                    │
│  • Understand what you're doing before reset --hard             │
│  • Consider pushing to remote as backup                         │
│                                                                  │
│  Limitations:                                                   │
│  • Reflog is local only - not shared with others                │
│  • Entries expire (default 90 days)                             │
│  • git gc can remove unreachable commits                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Recovery Commands

```bash
# View full reflog
git reflog

# See what changed
git show HEAD@{1}

# Compare positions
git diff HEAD@{0} HEAD@{3}

# Recover to specific point
git reset --hard HEAD@{n}

# Create branch at old position
git branch recovered HEAD@{n}

# Check out without changing HEAD
git checkout HEAD@{n} -- file.txt
```

## Reflog vs Log

```
┌─────────────────────────────────────────────────────────────────┐
│                  Reflog vs Log Comparison                        │
├────────────────────────┬────────────────────────────────────────┤
│ Feature                │ git log        │ git reflog            │
├────────────────────────┼────────────────┼───────────────────────┤
│ Shows                  │ Commit history │ HEAD movement history │
│ Follows                │ Parent commits │ Chronological order   │
│ Scope                  │ Repository     │ Local only            │
│ Includes               │ Ancestors only │ All HEAD positions    │
│ Shared with push       │ Yes            │ No                    │
│ Shows deleted commits  │ No             │ Yes (if recent)       │
│ Default expiry         │ Never          │ 90 days               │
└────────────────────────┴────────────────┴───────────────────────┘
```

## Useful Commands Reference

```bash
# View reflog
git reflog
git reflog show HEAD
git reflog show <branch>
git reflog --date=relative
git reflog --all

# Time-based references
HEAD@{n}
HEAD@{yesterday}
HEAD@{1.week.ago}
main@{2.hours.ago}

# Recovery operations
git reset --hard HEAD@{n}
git branch <name> HEAD@{n}
git cherry-pick HEAD@{n}
git checkout HEAD@{n} -- <file>

# Search reflog
git reflog | grep <pattern>
git log -g --grep=<pattern>

# Maintenance
git reflog expire --expire=now --all
git gc --prune=now
```

## Example Recovery Session

```bash
# Situation: Accidentally ran git reset --hard HEAD~5

# Step 1: Don't panic, check reflog
$ git reflog
abc123 HEAD@{0}: reset: moving to HEAD~5
def456 HEAD@{1}: commit: Feature complete
ghi789 HEAD@{2}: commit: Add tests
jkl012 HEAD@{3}: commit: Implement logic
mno345 HEAD@{4}: commit: Add structure
pqr678 HEAD@{5}: commit: Initial feature

# Step 2: Identify what we want (def456 - our lost work)
$ git show def456
# Verify this is the right commit

# Step 3: Recover
$ git reset --hard def456
HEAD is now at def456 Feature complete

# All 5 commits are back!
$ git log --oneline -6
def456 Feature complete
ghi789 Add tests
jkl012 Implement logic
mno345 Add structure
pqr678 Initial feature
... earlier commits
```
