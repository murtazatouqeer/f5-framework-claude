---
name: merge-conflicts
description: Resolving merge conflicts effectively
category: git/collaboration
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Merge Conflicts

## Overview

Merge conflicts occur when Git cannot automatically merge changes from different
branches. Understanding how to resolve conflicts efficiently is essential for
team collaboration.

## Understanding Conflicts

### When Conflicts Occur

```
┌─────────────────────────────────────────────────────────────────┐
│                   Conflict Scenarios                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Same Line Modified:                                            │
│  main:    const x = 1;   →   const x = 10;                      │
│  feature: const x = 1;   →   const x = 20;                      │
│                          CONFLICT                               │
│                                                                  │
│  Adjacent Line Changes:                                         │
│  main:    Added line 5                                          │
│  feature: Modified line 5                                       │
│                          CONFLICT                               │
│                                                                  │
│  File Deleted vs Modified:                                      │
│  main:    Deleted file.js                                       │
│  feature: Modified file.js                                      │
│                          CONFLICT                               │
│                                                                  │
│  Binary Files:                                                  │
│  Both branches modified image.png                               │
│                          CONFLICT (must choose one)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Conflict Markers

```javascript
// File with conflict markers
function getPrice() {
<<<<<<< HEAD
  return this.basePrice * 1.1;  // main branch version
=======
  return this.basePrice * 1.2;  // feature branch version
>>>>>>> feature/new-pricing
}

// Markers explained:
// <<<<<<< HEAD       - Start of current branch changes
// =======            - Separator between versions
// >>>>>>> branch     - End of incoming branch changes
```

## Resolving Conflicts

### Basic Workflow

```bash
# 1. Attempt merge
git checkout main
git merge feature/new-pricing
# CONFLICT message appears

# 2. Check conflict status
git status
# Shows files with conflicts

# 3. Open and edit conflicted files
# Remove markers, keep correct code

# 4. Mark as resolved
git add resolved-file.js

# 5. Complete the merge
git commit -m "Merge feature/new-pricing, resolve pricing conflicts"
```

### Resolution Strategies

#### Keep Ours (Current Branch)

```bash
# Keep current branch version for specific file
git checkout --ours path/to/file.js
git add path/to/file.js

# Keep ours for all conflicts
git checkout --ours .
git add .
```

#### Keep Theirs (Incoming Branch)

```bash
# Keep incoming branch version for specific file
git checkout --theirs path/to/file.js
git add path/to/file.js

# Keep theirs for all conflicts
git checkout --theirs .
git add .
```

#### Manual Resolution

```javascript
// Before (with conflict markers)
function calculateTotal() {
<<<<<<< HEAD
  const tax = 0.08;
  return price * (1 + tax);
=======
  const tax = 0.10;
  const discount = 0.05;
  return price * (1 + tax - discount);
>>>>>>> feature/add-discount
}

// After (manually resolved - combined both changes)
function calculateTotal() {
  const tax = 0.10;        // Use new tax rate
  const discount = 0.05;   // Add discount
  return price * (1 + tax - discount);
}
```

### Using Merge Tools

```bash
# Configure merge tool
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'

# Or use other tools
git config --global merge.tool vimdiff
git config --global merge.tool meld
git config --global merge.tool kdiff3

# Launch merge tool
git mergetool

# Clean up .orig backup files
git clean -f *.orig
# Or disable backup files
git config --global mergetool.keepBackup false
```

### VS Code Merge Tool

```javascript
// VS Code shows conflicts with clickable options:
// Accept Current Change | Accept Incoming Change | Accept Both Changes | Compare Changes

function getDiscount() {
<<<<<<< HEAD (Current Change)
  return 0.10;
=======  (Incoming Change)
  return 0.15;
>>>>>>> feature/holiday-sale
}

// Click "Accept Incoming Change" to resolve
function getDiscount() {
  return 0.15;
}
```

## Conflict Prevention

### Strategies to Avoid Conflicts

```
┌─────────────────────────────────────────────────────────────────┐
│               Conflict Prevention Strategies                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Keep Branches Short-Lived                                   │
│     └── Merge frequently to reduce divergence                   │
│                                                                  │
│  2. Sync with Main Regularly                                    │
│     └── Rebase or merge main into feature daily                 │
│                                                                  │
│  3. Communicate with Team                                       │
│     └── Coordinate on same-file changes                         │
│                                                                  │
│  4. Small, Focused Changes                                      │
│     └── Less overlap with others' work                          │
│                                                                  │
│  5. Modular Code Structure                                      │
│     └── Separate concerns, less file sharing                    │
│                                                                  │
│  6. Code Ownership                                              │
│     └── Assign files/areas to team members                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Regular Syncing

```bash
# Daily sync with main using rebase
git checkout feature/my-feature
git fetch origin
git rebase origin/main

# Or using merge (preserves history)
git merge origin/main

# Push updated branch
git push --force-with-lease origin feature/my-feature
```

## Complex Conflict Scenarios

### Rebase Conflicts

```bash
# During rebase, conflicts may occur at each commit
git rebase main

# Resolve conflict
# Edit file, remove markers
git add resolved-file.js

# Continue rebase
git rebase --continue

# Or abort if too complex
git rebase --abort

# Skip this commit (lose its changes)
git rebase --skip
```

### Cherry-pick Conflicts

```bash
# Cherry-pick may conflict
git cherry-pick abc123

# Resolve similar to merge
git add resolved-file.js
git cherry-pick --continue

# Or abort
git cherry-pick --abort
```

### Submodule Conflicts

```bash
# Submodule conflicts show different commit references
# Edit .gitmodules or submodule reference

# Update submodule to desired commit
cd submodule-path
git checkout desired-commit
cd ..
git add submodule-path
```

### Binary File Conflicts

```bash
# Binary files can't be merged
# Must choose one version

# Keep current version
git checkout --ours path/to/image.png

# Keep incoming version
git checkout --theirs path/to/image.png

# Stage the resolved file
git add path/to/image.png
```

## Conflict Resolution Tips

### Finding the Source

```bash
# See what commits touched the conflicting file
git log --oneline --all -- path/to/file.js

# See the common ancestor
git merge-base HEAD feature-branch

# View file at common ancestor
git show $(git merge-base HEAD feature-branch):path/to/file.js

# Three-way diff
git diff --base path/to/file.js    # Common ancestor
git diff --ours path/to/file.js    # Current branch
git diff --theirs path/to/file.js  # Incoming branch
```

### Testing After Resolution

```bash
# After resolving, verify the code works
npm test

# Check for merge markers accidentally left behind
grep -rn "<<<<<<" .
grep -rn "======" .
grep -rn ">>>>>>" .

# Run linter
npm run lint
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│               Merge Conflict Best Practices                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before Merging:                                                │
│  □ Pull latest changes from target branch                       │
│  □ Sync your branch with target                                 │
│  □ Run tests to ensure your changes work                        │
│                                                                  │
│  During Resolution:                                             │
│  □ Understand both changes before resolving                     │
│  □ Don't just accept one side blindly                           │
│  □ Test after resolving each file                               │
│  □ Use merge tools for complex conflicts                        │
│                                                                  │
│  After Resolution:                                              │
│  □ Search for leftover conflict markers                         │
│  □ Run full test suite                                          │
│  □ Review the diff before committing                            │
│  □ Write descriptive commit message                             │
│                                                                  │
│  General:                                                       │
│  □ Communicate with teammates about conflicts                   │
│  □ Get help if conflict is in unfamiliar code                   │
│  □ Consider pair resolution for complex cases                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Commands Reference

```bash
# Check conflict status
git status

# See conflicted files only
git diff --name-only --diff-filter=U

# Abort merge
git merge --abort

# Abort rebase
git rebase --abort

# Show merge base
git merge-base HEAD other-branch

# Three-way diff for file
git diff :1:file :2:file :3:file
# :1 = common ancestor, :2 = ours, :3 = theirs

# Resolve using specific version
git checkout --ours file.js
git checkout --theirs file.js

# Mark file as resolved
git add file.js

# Complete merge
git commit

# Search for conflict markers
git diff --check
```
