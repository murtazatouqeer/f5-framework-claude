---
name: bisect
description: Binary search to find bug-introducing commits
category: git/advanced
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Bisect

## Overview

Git bisect uses binary search to find the commit that introduced a bug. Instead
of checking every commit, it efficiently narrows down the problematic commit
by testing commits in the middle of the search range.

## How Bisect Works

```
┌─────────────────────────────────────────────────────────────────┐
│                   Git Bisect Process                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Given 1000 commits between good and bad:                       │
│                                                                  │
│  Linear Search: Up to 1000 tests needed                         │
│  Binary Search: ~10 tests needed (log₂ 1000 ≈ 10)               │
│                                                                  │
│  Step 1: Test commit 500                                        │
│          ├── Good? → Bug is in 501-1000                         │
│          └── Bad?  → Bug is in 1-500                            │
│                                                                  │
│  Step 2: Test middle of remaining range                         │
│          Repeat until single commit identified                  │
│                                                                  │
│  Visual:                                                        │
│  ●──●──●──●──●──●──●──●──●──●──●──●──●──●──●──●                 │
│  ↑                    ↑                       ↑                 │
│  GOOD                TEST                    BAD                │
│  (known working)     (check this)    (known broken)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Bisect Workflow

### Manual Bisect

```bash
# 1. Start bisect
git bisect start

# 2. Mark current commit as bad (has bug)
git bisect bad

# 3. Mark known good commit
git bisect good v1.0.0
# Or use commit hash
git bisect good abc123

# 4. Git checks out middle commit
# Bisecting: 50 revisions left to test after this (roughly 6 steps)
# [def456...] Commit message

# 5. Test and mark result
git bisect good  # If this commit works
# or
git bisect bad   # If this commit has the bug

# 6. Repeat until found
# abc789 is the first bad commit
# commit abc789
# Author: Developer <dev@example.com>
# Date: ...
#
#     Introduce bug in feature

# 7. End bisect, return to original branch
git bisect reset
```

### Quick Start

```bash
# Start with known good and bad
git bisect start <bad-commit> <good-commit>

# Example:
git bisect start HEAD v1.0.0
# or
git bisect start HEAD~50 HEAD~100
```

## Automated Bisect

### With Test Script

```bash
# Start bisect
git bisect start HEAD v1.0.0

# Run automated bisect
git bisect run npm test

# Git will:
# 1. Checkout middle commit
# 2. Run "npm test"
# 3. Mark good (exit 0) or bad (exit 1)
# 4. Repeat until found

# Exit codes:
# 0 = good (test passed)
# 1-124, 126-127 = bad (test failed)
# 125 = skip (can't test this commit)
```

### With Custom Script

```bash
# Create test script
cat > /tmp/test.sh << 'EOF'
#!/bin/bash
# Build the project
npm install || exit 125  # Skip if can't build

# Run specific test
npm test -- --grep "user login" || exit 1

exit 0
EOF
chmod +x /tmp/test.sh

# Run automated bisect
git bisect start HEAD v1.0.0
git bisect run /tmp/test.sh
```

### With Inline Commands

```bash
git bisect start HEAD v1.0.0
git bisect run sh -c 'make && ./test-feature'
```

## Bisect Commands

### Core Commands

```bash
# Start bisect session
git bisect start

# Mark commits
git bisect good [commit]    # Working state
git bisect bad [commit]     # Broken state
git bisect skip [commit]    # Can't test (won't compile)

# End session
git bisect reset            # Return to original HEAD
git bisect reset <branch>   # Return to specific branch

# View progress
git bisect log              # Show bisect log
git bisect visualize        # Open in gitk
```

### Skip Commits

```bash
# Skip current commit (won't compile, etc.)
git bisect skip

# Skip specific commits
git bisect skip abc123 def456

# Skip range of commits
git bisect skip abc123..def456
```

## Advanced Bisect

### Bisect with Paths

```bash
# Only consider commits touching specific paths
git bisect start -- src/auth/ tests/auth/

# Useful when you know which files are involved
```

### Bisect Terms

```bash
# Use custom terms instead of good/bad
git bisect start --term-new=fixed --term-old=broken

# Then use:
git bisect fixed  # This commit is fixed
git bisect broken # This commit is broken

# Useful for finding when bug was FIXED
```

### Replay Bisect

```bash
# Save bisect log
git bisect log > bisect.log

# Later, replay the session
git bisect replay bisect.log
```

### Visualize Bisect

```bash
# Open gitk showing bisect progress
git bisect visualize

# Or use log
git bisect log

# Show remaining range
git log --oneline HEAD...BISECT_HEAD
```

## Common Scenarios

### Find When Bug Was Introduced

```bash
# Current version is broken, v1.0 worked
git bisect start
git bisect bad HEAD
git bisect good v1.0.0

# Test each commit
# Run your test, mark good or bad
git bisect good  # or git bisect bad

# When found:
# abc123 is the first bad commit
```

### Find When Bug Was Fixed

```bash
# Current version works, want to find fix
git bisect start --term-new=fixed --term-old=broken
git bisect fixed HEAD
git bisect broken v1.0.0

# Mark commits
git bisect fixed   # This commit has the fix
git bisect broken  # This commit still has bug
```

### Find Performance Regression

```bash
# Create performance test script
cat > /tmp/perf-test.sh << 'EOF'
#!/bin/bash
npm install || exit 125
time=$(npm run benchmark | grep "Time:" | awk '{print $2}')
if [ "$time" -gt 1000 ]; then
    exit 1  # Too slow (bad)
fi
exit 0      # Fast enough (good)
EOF

git bisect start HEAD v1.0.0
git bisect run /tmp/perf-test.sh
```

### Bisect with Build Issues

```bash
# Some commits may not compile
cat > /tmp/test.sh << 'EOF'
#!/bin/bash
# Try to build
if ! npm install; then
    exit 125  # Skip - can't build
fi

# Run actual test
npm test
EOF

git bisect start HEAD v1.0.0
git bisect run /tmp/test.sh
```

## Bisect Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   Bisect Workflow                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Identify Range                                              │
│     ├── Find known good commit (feature worked)                 │
│     └── Bad commit is usually HEAD                              │
│                                                                  │
│  2. Start Bisect                                                │
│     git bisect start HEAD <good-commit>                         │
│                                                                  │
│  3. Test Commit                                                 │
│     ├── Run your test/reproduce bug                             │
│     ├── Working? → git bisect good                              │
│     ├── Broken?  → git bisect bad                               │
│     └── Can't test? → git bisect skip                           │
│                                                                  │
│  4. Repeat                                                      │
│     Git checks out next commit to test                          │
│     Continue until culprit found                                │
│                                                                  │
│  5. Analyze                                                     │
│     git show <bad-commit>                                       │
│     Understand what change caused the bug                       │
│                                                                  │
│  6. Cleanup                                                     │
│     git bisect reset                                            │
│     Fix the bug based on findings                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                 Bisect Best Practices                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before Starting:                                               │
│  • Ensure you can reliably reproduce the bug                    │
│  • Find a known good commit (release tag, date)                 │
│  • Stash any local changes                                      │
│                                                                  │
│  During Bisect:                                                 │
│  • Test consistently - same steps each time                     │
│  • Skip commits that can't be tested (exit 125)                 │
│  • Use automated scripts when possible                          │
│  • Save bisect log for complex sessions                         │
│                                                                  │
│  Script Tips:                                                   │
│  • Exit 0 for good, 1-124 for bad, 125 for skip                 │
│  • Handle build failures with exit 125                          │
│  • Make scripts idempotent (clean state each run)               │
│                                                                  │
│  After Finding:                                                 │
│  • Always git bisect reset when done                            │
│  • Verify the found commit with git show                        │
│  • Create a targeted fix based on findings                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

```bash
# Wrong bisect result
# Sometimes test is flaky or wrong commit marked
git bisect log        # Review what was marked
git bisect reset
# Start again with more careful testing

# Bisect on merge-heavy history
# Results can be confusing with many merges
git bisect start HEAD v1.0.0 -- path/to/file
# Limit to specific paths

# Can't find good commit
git log --oneline --all | head -50
git checkout abc123
# Manually test various points
```

### Reset Issues

```bash
# If bisect reset fails
git bisect reset HEAD

# Force return to branch
git checkout main

# Remove bisect files manually (last resort)
rm -rf .git/BISECT_*
```

## Useful Commands Reference

```bash
# Start bisect
git bisect start
git bisect start <bad> <good>
git bisect start <bad> <good> -- <paths>

# Mark commits
git bisect good [commit]
git bisect bad [commit]
git bisect skip [commit]

# Automated bisect
git bisect run <script>
git bisect run npm test
git bisect run sh -c 'make && ./test'

# Custom terms
git bisect start --term-new=fixed --term-old=broken

# View/replay
git bisect log
git bisect log > bisect.log
git bisect replay bisect.log
git bisect visualize

# End bisect
git bisect reset
git bisect reset <branch>
```
