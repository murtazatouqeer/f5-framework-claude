# Git Fundamentals Reference

## Basic Commands

### Repository Setup

```bash
# Initialize
git init
git init --initial-branch=main

# Clone
git clone https://github.com/org/repo.git
git clone git@github.com:org/repo.git
git clone --depth 1 https://github.com/org/repo.git  # Shallow clone
```

### Status and Diff

```bash
# Status
git status
git status -s        # Short format
git status -sb       # Short with branch

# Diff
git diff             # Unstaged changes
git diff --staged    # Staged changes
git diff HEAD        # All changes
git diff main..feature  # Between branches
git diff --stat      # Summary only
```

### Staging

```bash
# Add files
git add file.txt
git add .                    # All files
git add -A                   # All (including deletions)
git add -p                   # Interactive staging
git add -u                   # Modified and deleted only

# Unstage
git reset HEAD file.txt
git restore --staged file.txt
```

### Committing

```bash
# Commit
git commit -m "feat: add login"
git commit -am "fix: typo"   # Add + commit
git commit --amend           # Edit last commit
git commit --amend --no-edit # Amend without editing message
git commit --allow-empty -m "trigger CI"
```

## Branching

### Branch Operations

```bash
# List branches
git branch              # Local
git branch -r           # Remote
git branch -a           # All
git branch -v           # With last commit

# Create branch
git branch feature
git checkout -b feature  # Create and switch
git switch -c feature    # Modern create and switch

# Switch branch
git checkout feature
git switch feature

# Delete branch
git branch -d feature    # Safe delete
git branch -D feature    # Force delete
git push origin --delete feature  # Delete remote

# Rename branch
git branch -m old-name new-name
git branch -m new-name   # Rename current
```

### Remote Branches

```bash
# Fetch
git fetch origin
git fetch --all
git fetch --prune       # Clean up deleted remote branches

# Pull
git pull origin main
git pull --rebase
git pull --ff-only      # Fast-forward only

# Push
git push origin feature
git push -u origin feature  # Set upstream
git push --force-with-lease  # Safer force push
```

## Viewing History

```bash
# Log
git log
git log --oneline
git log --oneline -10
git log --graph --oneline --all
git log --author="name"
git log --since="2 weeks ago"
git log --grep="fix"
git log -p               # With patches
git log --stat           # With stats
git log main..feature    # Commits in feature not in main

# Show
git show HEAD
git show abc123
git show HEAD:path/to/file

# Blame
git blame file.txt
git blame -L 10,20 file.txt  # Lines 10-20
```

## Configuration

```bash
# User settings
git config --global user.name "Name"
git config --global user.email "email@example.com"

# Editor
git config --global core.editor "code --wait"

# Aliases
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.st "status -sb"
git config --global alias.lg "log --oneline --graph --all"

# Default branch
git config --global init.defaultBranch main

# Pull behavior
git config --global pull.rebase true

# View config
git config --list
git config --global --list
```

## .gitignore

```gitignore
# Dependencies
node_modules/
vendor/

# Build outputs
dist/
build/
*.o
*.pyc

# IDE
.idea/
.vscode/
*.swp

# Environment
.env
.env.local
*.env

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Temp files
*.tmp
*.temp

# Patterns
**/temp/
!important.log
```

## Stashing

```bash
# Stash changes
git stash
git stash push -m "WIP: feature"
git stash --include-untracked
git stash --keep-index    # Keep staged

# List stashes
git stash list

# Apply stash
git stash apply           # Keep stash
git stash pop             # Apply and drop
git stash apply stash@{2}

# View stash
git stash show
git stash show -p stash@{0}

# Drop stash
git stash drop stash@{0}
git stash clear           # Drop all
```

## Tagging

```bash
# Create tag
git tag v1.0.0
git tag -a v1.0.0 -m "Release 1.0.0"
git tag v1.0.0 abc123    # Tag specific commit

# List tags
git tag
git tag -l "v1.*"

# Push tags
git push origin v1.0.0
git push origin --tags

# Delete tag
git tag -d v1.0.0
git push origin --delete v1.0.0
```

## Undoing Changes

```bash
# Discard unstaged changes
git checkout -- file.txt
git restore file.txt

# Unstage files
git reset HEAD file.txt
git restore --staged file.txt

# Reset commits (keep changes)
git reset --soft HEAD~1

# Reset commits (discard changes)
git reset --hard HEAD~1

# Revert a commit (creates new commit)
git revert HEAD
git revert abc123

# Clean untracked files
git clean -n             # Dry run
git clean -f             # Force
git clean -fd            # Include directories
```
