---
name: staging-committing
description: Working with the staging area and commits
category: git/fundamentals
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Staging and Committing

## Overview

The staging area (index) is Git's unique feature that allows you to craft
commits precisely. Understanding staging helps you create clean, logical
commits that tell a story.

## The Three Trees

```
┌─────────────────────────────────────────────────────────────────┐
│                      Git Three Trees                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Working Directory    Staging Area (Index)    HEAD (Repository) │
│  ┌───────────────┐   ┌───────────────┐       ┌───────────────┐  │
│  │               │   │               │       │               │  │
│  │  Your actual  │   │   Snapshot    │       │  Last commit  │  │
│  │  files on     │──▶│   prepared    │──────▶│  pointer      │  │
│  │  disk         │   │   for next    │       │               │  │
│  │               │add│   commit      │commit │               │  │
│  └───────────────┘   └───────────────┘       └───────────────┘  │
│         │                                           │            │
│         └──────────────checkout/reset──────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Staging Files

### Basic Staging

```bash
# Stage specific file
git add file.txt

# Stage multiple files
git add file1.txt file2.txt file3.txt

# Stage all files in current directory
git add .

# Stage all changes in entire repo
git add -A
# or
git add --all

# Stage only tracked files (no new files)
git add -u
# or
git add --update
```

### Pattern-Based Staging

```bash
# Stage all JavaScript files
git add "*.js"

# Stage all files in src directory
git add src/

# Stage all TypeScript files recursively
git add "**/*.ts"

# Stage all files except tests
git add . ':!**/*.test.ts'
```

### Interactive Staging

```bash
# Interactive mode
git add -i

# Interactive menu:
# 1: status      2: update      3: revert
# 4: add untracked  5: patch    6: diff
# 7: quit       8: help

# Select files by number
What now> 2
Update>> 1,3,5
Update>>
# Press Enter to confirm
```

### Patch Mode (Partial Staging)

```bash
# Stage parts of files interactively
git add -p
# or
git add --patch

# For each hunk, choose:
# y - stage this hunk
# n - skip this hunk
# q - quit, don't stage remaining
# a - stage this and all remaining hunks
# d - skip this and all remaining hunks
# s - split into smaller hunks
# e - manually edit the hunk
# ? - help
```

#### Example Patch Session

```diff
diff --git a/file.js b/file.js
--- a/file.js
+++ b/file.js
@@ -1,5 +1,7 @@
 function hello() {
-  console.log("Hello");
+  console.log("Hello, World!");
+  // Added greeting
 }
+
+function goodbye() {}
Stage this hunk [y,n,q,a,d,s,e,?]? s
# Splits into smaller hunks for granular control
```

## Unstaging Files

```bash
# Unstage specific file (keep changes)
git reset HEAD file.txt
# or (Git 2.23+)
git restore --staged file.txt

# Unstage all files
git reset HEAD
# or
git restore --staged .

# Unstage and discard changes
git checkout HEAD -- file.txt
# or
git restore --source=HEAD --staged --worktree file.txt
```

## Viewing Staged Changes

```bash
# Show what's staged
git diff --staged
# or
git diff --cached

# Show staged files list
git diff --staged --name-only

# Show staged changes with stats
git diff --staged --stat

# Show what's NOT staged
git diff

# Show all changes (staged + unstaged)
git diff HEAD
```

## Creating Commits

### Basic Commits

```bash
# Commit with inline message
git commit -m "Add user authentication feature"

# Commit with editor (for longer messages)
git commit

# Commit all tracked files (skip staging)
git commit -a -m "Fix bug in login"
# or
git commit -am "Fix bug in login"

# Empty commit (useful for triggering CI)
git commit --allow-empty -m "Trigger rebuild"
```

### Commit Message Best Practices

```bash
# Good commit structure
git commit -m "feat(auth): add OAuth2 login support

- Add Google OAuth2 provider
- Add GitHub OAuth2 provider
- Update user model for OAuth tokens
- Add OAuth callback routes

Closes #123"

# Types: feat, fix, docs, style, refactor, test, chore
# Scope: optional, indicates area of change
# Subject: imperative, present tense, no period
# Body: explains what and why
# Footer: references issues, breaking changes
```

### Commit Templates

```bash
# Set up commit template
git config --global commit.template ~/.gitmessage

# ~/.gitmessage
# <type>(<scope>): <subject>
#
# <body>
#
# <footer>
#
# Types: feat, fix, docs, style, refactor, test, chore
# Scope: component or file affected
# Subject: imperative mood, no period, max 50 chars
# Body: explain what and why (not how)
# Footer: Breaking changes, issue references
```

### Signing Commits

```bash
# Configure GPG key
git config --global user.signingkey YOUR_KEY_ID

# Sign commit
git commit -S -m "Signed commit"

# Always sign commits
git config --global commit.gpgsign true

# Verify signature
git log --show-signature
```

## Amending Commits

### Modify Last Commit

```bash
# Change commit message
git commit --amend -m "New message"

# Add more changes to last commit
git add forgotten-file.txt
git commit --amend --no-edit

# Change author
git commit --amend --author="Name <email@example.com>"

# Change date
git commit --amend --date="2024-01-15T10:00:00"
```

### Amending Older Commits

```bash
# Interactive rebase to edit older commits
git rebase -i HEAD~3

# Mark commit to edit
# pick abc123 First commit
# edit def456 Second commit  <- change pick to edit
# pick ghi789 Third commit

# Make changes, then
git commit --amend
git rebase --continue
```

## Commit Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   Commit Best Practices                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Atomic Commits                                                 │
│  └── One logical change per commit                              │
│                                                                  │
│  Clear Messages                                                 │
│  └── Explain what and why, not how                              │
│                                                                  │
│  Working State                                                  │
│  └── Each commit should build and pass tests                    │
│                                                                  │
│  Related Changes                                                │
│  └── Group related changes, separate unrelated                  │
│                                                                  │
│  Review Before Commit                                           │
│  └── git diff --staged before every commit                      │
│                                                                  │
│  No Debug Code                                                  │
│  └── Remove console.log, debugger statements                    │
│                                                                  │
│  No Secrets                                                     │
│  └── Never commit passwords, keys, tokens                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Advanced Staging Techniques

### Stashing Changes

```bash
# Stash current changes
git stash

# Stash with message
git stash push -m "WIP: feature work"

# Stash including untracked files
git stash -u

# Stash including ignored files
git stash -a

# List stashes
git stash list

# Apply most recent stash
git stash pop

# Apply specific stash
git stash apply stash@{2}

# Drop stash
git stash drop stash@{0}

# Create branch from stash
git stash branch new-branch stash@{0}

# Show stash contents
git stash show -p stash@{0}
```

### Staging Deleted Files

```bash
# Stage deleted file
git add deleted-file.txt
# or
git rm deleted-file.txt

# Stage all deletions
git add -u

# Stage all deletions in directory
git add -u path/to/dir/
```

### Intent to Add

```bash
# Mark file as "intent to add" (for new files)
git add -N file.txt
# or
git add --intent-to-add file.txt

# Now git diff shows the file as new
# Useful for reviewing new files before staging content
```

## Workflow Example

```bash
# 1. Make changes to files
# Edit auth.ts, user.ts, test.ts

# 2. Review all changes
git diff

# 3. Stage related changes together
git add -p auth.ts
# Stage only authentication-related hunks

git add -p user.ts
# Stage only user model changes

# 4. Review staged changes
git diff --staged

# 5. Commit with clear message
git commit -m "feat(auth): implement JWT authentication

- Add JWT token generation
- Add token verification middleware
- Update user model with token field"

# 6. Stage and commit test changes separately
git add test.ts
git commit -m "test(auth): add JWT authentication tests"
```
