---
name: interactive-rebase
description: Rewriting commit history with interactive rebase
category: git/advanced
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Interactive Rebase

## Overview

Interactive rebase (`git rebase -i`) is a powerful tool for rewriting commit
history. It allows you to edit, reorder, squash, split, and delete commits
before sharing your work.

## When to Use Interactive Rebase

```
┌─────────────────────────────────────────────────────────────────┐
│              Interactive Rebase Use Cases                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Clean up commits before creating a PR                       │
│  ✅ Squash related commits into logical units                   │
│  ✅ Edit commit messages for clarity                            │
│  ✅ Reorder commits for better logical flow                     │
│  ✅ Split large commits into smaller ones                       │
│  ✅ Remove unwanted commits                                     │
│  ✅ Fix commits that break the build                            │
│                                                                  │
│  ❌ Don't use on commits already pushed to shared branches      │
│  ❌ Don't use on main/develop branches                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Starting Interactive Rebase

### Basic Commands

```bash
# Rebase last N commits
git rebase -i HEAD~3      # Last 3 commits
git rebase -i HEAD~5      # Last 5 commits

# Rebase from specific commit
git rebase -i abc123      # Doesn't include abc123
git rebase -i abc123^     # Includes abc123

# Rebase all commits since diverging from main
git rebase -i main

# Rebase including root commit
git rebase -i --root
```

### The Interactive Editor

```bash
# When you run git rebase -i HEAD~4, editor opens:

pick abc123 Add user authentication
pick def456 Fix typo in auth
pick ghi789 Add password validation
pick jkl012 Update error messages

# Rebase abc123..jkl012 onto mno345 (4 commands)
#
# Commands:
# p, pick   = use commit
# r, reword = use commit, but edit the commit message
# e, edit   = use commit, but stop for amending
# s, squash = use commit, but meld into previous commit
# f, fixup  = like "squash", but discard this commit's log message
# x, exec   = run command (the rest of the line) using shell
# b, break  = stop here (continue rebase later with 'git rebase --continue')
# d, drop   = remove commit
# l, label  = label current HEAD with a name
# t, reset  = reset HEAD to a label
# m, merge  = create a merge commit
```

## Rebase Operations

### Pick (Keep As Is)

```bash
# Default action - keep commit unchanged
pick abc123 Add user authentication

# Commits are applied in order listed
# Reorder lines to reorder commits
```

### Reword (Edit Message)

```bash
# Change commit message
reword abc123 Add user authentication

# When this commit is processed, editor opens
# for you to edit the message
```

### Edit (Modify Commit)

```bash
# Stop at commit to make changes
edit abc123 Add user authentication

# Rebase stops at this commit
# Make your changes
git add .
git commit --amend
git rebase --continue
```

### Squash (Combine with Previous)

```bash
# Before: 4 commits
pick abc123 Add user authentication
squash def456 Fix typo in auth
squash ghi789 Add password validation
squash jkl012 Update error messages

# After: 1 commit with combined message
# Editor opens to edit final combined message
```

### Fixup (Squash, Discard Message)

```bash
# Like squash but discards the message
pick abc123 Add user authentication
fixup def456 Fix typo in auth
fixup ghi789 Add password validation

# After: 1 commit, only first message kept
# No editor opened for message
```

### Drop (Remove Commit)

```bash
# Remove commit entirely
pick abc123 Add user authentication
drop def456 Temporary debug code
pick ghi789 Add password validation

# def456 will be removed from history
# Or just delete the line
```

### Exec (Run Command)

```bash
# Run command after commit
pick abc123 Add user authentication
exec npm test
pick def456 Add more features
exec npm test

# If command fails, rebase stops
# Useful for ensuring each commit passes tests
```

### Break (Stop Point)

```bash
# Stop rebase at a point
pick abc123 First commit
break
pick def456 Second commit

# Rebase stops after first commit
# Do whatever you need
git rebase --continue  # Resume
```

## Common Workflows

### Squash All Commits

```bash
# Before: Many messy commits
git rebase -i main

# In editor:
pick abc123 Initial work
fixup def456 WIP
fixup ghi789 More WIP
fixup jkl012 Fixed stuff
fixup mno345 Final cleanup

# Result: Single clean commit
```

### Clean Up Before PR

```bash
# Start interactive rebase
git rebase -i main

# Typical cleanup:
pick abc123 Add new feature
fixup def456 Fix typo           # Merge into previous
fixup ghi789 Address review     # Merge into previous
reword jkl012 Fix bug           # Edit message
drop mno345 Debug logging       # Remove entirely
```

### Reorder Commits

```bash
# Before:
pick abc123 Add feature A
pick def456 Fix bug in B
pick ghi789 Add feature B

# After (reordered):
pick ghi789 Add feature B
pick def456 Fix bug in B
pick abc123 Add feature A
```

### Split a Commit

```bash
# Mark commit for editing
edit abc123 Add features A and B

# When rebase stops:
git reset HEAD^  # Undo commit, keep changes

# Create separate commits
git add feature-a.js
git commit -m "Add feature A"

git add feature-b.js
git commit -m "Add feature B"

# Continue rebase
git rebase --continue
```

### Edit a Past Commit

```bash
# Want to change abc123 (3 commits ago)
git rebase -i abc123^

# Mark for editing
edit abc123 Original message

# When stopped:
# Make your changes
git add .
git commit --amend
git rebase --continue
```

## Autosquash Feature

### Fixup Commits

```bash
# Create commit that will auto-squash
git commit --fixup abc123

# Creates commit with message:
# "fixup! Original commit message"

# Later, autosquash arranges them
git rebase -i --autosquash main

# Editor shows:
pick abc123 Original commit
fixup 123abc fixup! Original commit
```

### Squash Commits

```bash
# Create commit that will auto-squash with message
git commit --squash abc123

# Later, autosquash arranges them
git rebase -i --autosquash main

# Editor shows:
pick abc123 Original commit
squash 123abc squash! Original commit
```

### Amend Commits

```bash
# Create amendment commit
git commit --fixup=amend:abc123

# Will edit the commit message during rebase
```

### Set Autosquash Default

```bash
# Always use autosquash
git config --global rebase.autosquash true
```

## Handling Conflicts

### During Interactive Rebase

```bash
# Conflict occurs
# CONFLICT (content): Merge conflict in file.js

# 1. Resolve conflicts
# Edit file.js

# 2. Stage resolution
git add file.js

# 3. Continue
git rebase --continue

# Or abort entire rebase
git rebase --abort
```

### After Editing a Commit

```bash
# If your edit causes conflicts with later commits
# Resolve each conflict as rebase progresses
git add .
git rebase --continue
```

## Safety and Recovery

### Backup Before Rebase

```bash
# Create backup branch
git branch backup-feature-branch

# Then rebase
git rebase -i main

# If something goes wrong
git reset --hard backup-feature-branch
```

### Using Reflog

```bash
# Find state before rebase
git reflog
# abc123 HEAD@{0}: rebase finished
# def456 HEAD@{1}: rebase: edit
# ghi789 HEAD@{2}: commit: Before rebase

# Reset to pre-rebase state
git reset --hard HEAD@{2}

# Or use ORIG_HEAD
git reset --hard ORIG_HEAD
```

### Abort at Any Time

```bash
# Stop and return to original state
git rebase --abort
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│             Interactive Rebase Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Only Rebase Unpublished Commits                             │
│     └── Never rebase commits already on shared branches         │
│                                                                  │
│  2. Create Backup Branch First                                  │
│     └── git branch backup before complex rebases                │
│                                                                  │
│  3. Keep Commits Atomic                                         │
│     └── Each commit should do one thing                         │
│                                                                  │
│  4. Write Clear Commit Messages                                 │
│     └── Use reword to improve messages                          │
│                                                                  │
│  5. Test After Rebase                                           │
│     └── Run tests to ensure nothing broke                       │
│                                                                  │
│  6. Use Autosquash for Fixups                                   │
│     └── git commit --fixup for quick fixes                      │
│                                                                  │
│  7. Verify with Exec                                            │
│     └── Add "exec npm test" to verify each commit               │
│                                                                  │
│  8. Review Before Pushing                                       │
│     └── git log --oneline to review final result                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Commands Reference

```bash
# Start interactive rebase
git rebase -i HEAD~N
git rebase -i <commit>
git rebase -i main

# With autosquash
git rebase -i --autosquash main

# Include root commit
git rebase -i --root

# Continue after conflict/edit
git rebase --continue

# Abort rebase
git rebase --abort

# Skip current commit
git rebase --skip

# Create fixup commit
git commit --fixup <commit>

# Create squash commit
git commit --squash <commit>

# Configure autosquash default
git config --global rebase.autosquash true

# View reflog for recovery
git reflog
```

## Editor Commands Cheatsheet

```
┌──────────┬────────────────────────────────────────────────────┐
│ Command  │ Description                                        │
├──────────┼────────────────────────────────────────────────────┤
│ p, pick  │ Keep commit as-is                                  │
│ r, reword│ Keep commit, edit message                          │
│ e, edit  │ Stop to amend commit                               │
│ s, squash│ Combine with previous, keep message                │
│ f, fixup │ Combine with previous, discard message             │
│ x, exec  │ Run shell command                                  │
│ b, break │ Stop here for manual intervention                  │
│ d, drop  │ Remove commit                                      │
│ l, label │ Create label for current HEAD                      │
│ t, reset │ Reset HEAD to label                                │
│ m, merge │ Create merge commit                                │
└──────────┴────────────────────────────────────────────────────┘
```
