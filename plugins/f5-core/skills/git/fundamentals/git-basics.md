---
name: git-basics
description: Git repository initialization and basic commands
category: git/fundamentals
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Basics

## Overview

Git is a distributed version control system that tracks changes in source code.
This guide covers fundamental concepts and essential commands for getting
started with Git.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    Git Core Concepts                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Repository (Repo)                                              │
│  └── A directory containing your project and .git folder        │
│                                                                  │
│  Commit                                                         │
│  └── A snapshot of your project at a point in time              │
│                                                                  │
│  Branch                                                         │
│  └── A pointer to a specific commit (parallel development)      │
│                                                                  │
│  HEAD                                                           │
│  └── Pointer to the current branch/commit you're working on     │
│                                                                  │
│  Remote                                                         │
│  └── A reference to another copy of the repository              │
│                                                                  │
│  Working Directory                                              │
│  └── Your actual project files on disk                          │
│                                                                  │
│  Staging Area (Index)                                           │
│  └── Files prepared for the next commit                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Repository Initialization

### Create New Repository

```bash
# Initialize a new Git repository
git init

# Initialize with specific default branch name
git init --initial-branch=main

# Initialize in a specific directory
git init my-project

# Initialize bare repository (for servers)
git init --bare my-project.git
```

### Clone Existing Repository

```bash
# Clone via HTTPS
git clone https://github.com/user/repo.git

# Clone via SSH
git clone git@github.com:user/repo.git

# Clone to specific directory
git clone https://github.com/user/repo.git my-local-folder

# Clone specific branch
git clone -b develop https://github.com/user/repo.git

# Shallow clone (faster, no history)
git clone --depth 1 https://github.com/user/repo.git

# Clone with submodules
git clone --recursive https://github.com/user/repo.git
```

## Basic Commands

### Checking Status

```bash
# Full status
git status

# Short status
git status -s
# Output:
# M  modified-file.txt     (staged)
#  M unstaged-file.txt     (not staged)
# ?? untracked-file.txt    (untracked)
# A  new-file.txt          (newly added)
# D  deleted-file.txt      (deleted)
# R  old-name -> new-name  (renamed)

# Show branch info with status
git status -sb
# Output: ## main...origin/main
```

### Viewing History

```bash
# View commit history
git log

# One line per commit
git log --oneline

# Show graph
git log --oneline --graph --all

# Show last N commits
git log -5

# Show commits by author
git log --author="John"

# Show commits in date range
git log --since="2024-01-01" --until="2024-12-31"

# Show commits affecting specific file
git log -- path/to/file.txt

# Search commit messages
git log --grep="bug fix"

# Show what changed in each commit
git log -p

# Show statistics
git log --stat
```

### Viewing Changes

```bash
# Show unstaged changes
git diff

# Show staged changes
git diff --staged
# or
git diff --cached

# Show all changes (staged and unstaged)
git diff HEAD

# Show changes between commits
git diff abc123..def456

# Show changes between branches
git diff main..feature

# Show word-level diff
git diff --word-diff

# Show only names of changed files
git diff --name-only

# Show summary of changes
git diff --stat
```

### Viewing Specific Commits

```bash
# Show specific commit
git show abc123

# Show commit with file changes
git show abc123 --stat

# Show file at specific commit
git show abc123:path/to/file.txt

# Show HEAD commit
git show HEAD

# Show parent of HEAD
git show HEAD~1
# or
git show HEAD^
```

## File Operations

### Adding Files

```bash
# Add specific file
git add file.txt

# Add multiple files
git add file1.txt file2.txt

# Add all files in directory
git add src/

# Add all changes
git add .
# or
git add -A
# or
git add --all

# Add interactively
git add -i

# Add with patch mode (select hunks)
git add -p

# Add only tracked files
git add -u
```

### Removing Files

```bash
# Remove file from working directory and staging
git rm file.txt

# Remove from staging but keep in working directory
git rm --cached file.txt

# Remove directory recursively
git rm -r directory/

# Force remove (if file has local changes)
git rm -f file.txt
```

### Moving/Renaming Files

```bash
# Rename file
git mv old-name.txt new-name.txt

# Move file to directory
git mv file.txt directory/

# Move and rename
git mv src/old.txt dest/new.txt
```

### Undoing Changes

```bash
# Discard changes in working directory
git checkout -- file.txt
# or (Git 2.23+)
git restore file.txt

# Unstage file (keep changes)
git reset HEAD file.txt
# or (Git 2.23+)
git restore --staged file.txt

# Discard all unstaged changes
git checkout -- .
# or
git restore .

# Unstage all files
git reset HEAD
# or
git restore --staged .
```

## Commit Operations

### Creating Commits

```bash
# Commit staged changes
git commit -m "commit message"

# Commit with detailed message (opens editor)
git commit

# Add all tracked files and commit
git commit -a -m "message"
# or
git commit -am "message"

# Commit with co-author
git commit -m "message

Co-authored-by: Name <email@example.com>"
```

### Modifying Commits

```bash
# Amend last commit (change message or add files)
git commit --amend

# Amend without changing message
git commit --amend --no-edit

# Amend with new message
git commit --amend -m "new message"

# Change author of last commit
git commit --amend --author="Name <email@example.com>"
```

### Reverting Commits

```bash
# Create new commit that undoes changes
git revert abc123

# Revert without auto-commit
git revert --no-commit abc123

# Revert multiple commits
git revert abc123..def456

# Revert merge commit
git revert -m 1 abc123
```

## Working with Remotes

### Remote Management

```bash
# List remotes
git remote -v

# Add remote
git remote add origin https://github.com/user/repo.git

# Remove remote
git remote remove origin

# Rename remote
git remote rename origin upstream

# Change remote URL
git remote set-url origin https://new-url.com/repo.git

# Show remote info
git remote show origin
```

### Fetching and Pulling

```bash
# Fetch from remote (no merge)
git fetch origin

# Fetch all remotes
git fetch --all

# Fetch and prune deleted branches
git fetch --prune

# Pull (fetch + merge)
git pull origin main

# Pull with rebase
git pull --rebase origin main

# Pull all branches
git pull --all
```

### Pushing

```bash
# Push to remote
git push origin main

# Push and set upstream
git push -u origin main

# Push all branches
git push --all

# Push tags
git push --tags

# Force push (dangerous!)
git push --force origin main

# Force push with lease (safer)
git push --force-with-lease origin main

# Delete remote branch
git push origin --delete branch-name
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                    Git Basics Best Practices                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Commit Often                                                │
│     └── Small, focused commits are easier to review/revert      │
│                                                                  │
│  2. Write Good Messages                                         │
│     └── Clear, descriptive commit messages                      │
│                                                                  │
│  3. Pull Before Push                                            │
│     └── Always pull latest changes before pushing               │
│                                                                  │
│  4. Don't Commit Secrets                                        │
│     └── Use .gitignore for sensitive files                      │
│                                                                  │
│  5. Review Before Commit                                        │
│     └── Use git diff to check changes                           │
│                                                                  │
│  6. Use Branches                                                │
│     └── Never work directly on main/master                      │
│                                                                  │
│  7. Keep Repos Clean                                            │
│     └── Remove merged branches, use .gitignore                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
