---
name: remote-repos
description: Working with remote repositories
category: git/collaboration
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Remote Repositories

## Overview

Remote repositories enable collaboration by providing a shared location for
code. Understanding remote operations is essential for team workflows.

## Remote Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                   Remote Repository Model                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Local Repository          Remote Repository (origin)           │
│  ┌─────────────────┐       ┌─────────────────┐                  │
│  │ Working Dir     │       │                 │                  │
│  │ ┌─────────────┐ │       │  main           │                  │
│  │ │ Staging     │ │       │  ┌───●───●───●  │                  │
│  │ └─────────────┘ │       │  │              │                  │
│  │ Local Branches  │ push  │  │  feature     │                  │
│  │ ┌───●───●───●   │──────▶│  └───●───●     │                  │
│  │ │               │       │                 │                  │
│  │ │               │◀──────│                 │                  │
│  │ └───●───●       │ fetch │                 │                  │
│  └─────────────────┘       └─────────────────┘                  │
│                                                                  │
│  Remote Tracking Branches:                                      │
│  origin/main - local copy of remote main                        │
│  origin/feature - local copy of remote feature                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Managing Remotes

### Adding and Removing Remotes

```bash
# View current remotes
git remote -v

# Add remote
git remote add origin https://github.com/user/repo.git

# Add additional remote (e.g., upstream for forks)
git remote add upstream https://github.com/original/repo.git

# Remove remote
git remote remove origin

# Rename remote
git remote rename origin github

# Change remote URL
git remote set-url origin https://new-url.com/repo.git

# Show remote details
git remote show origin
```

### SSH vs HTTPS

```bash
# HTTPS (requires password/token)
git remote add origin https://github.com/user/repo.git

# SSH (requires SSH key setup)
git remote add origin git@github.com:user/repo.git

# Switch existing remote from HTTPS to SSH
git remote set-url origin git@github.com:user/repo.git

# Check which protocol is being used
git remote -v
```

### Setting Up SSH

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub
# Add this to GitHub/GitLab SSH keys settings

# Test connection
ssh -T git@github.com
```

## Fetching and Pulling

### Fetch Operations

```bash
# Fetch from origin (default remote)
git fetch

# Fetch from specific remote
git fetch origin

# Fetch all remotes
git fetch --all

# Fetch specific branch
git fetch origin feature-branch

# Fetch and prune deleted remote branches
git fetch --prune

# Fetch tags
git fetch --tags
```

### Pull Operations

```bash
# Pull (fetch + merge) from tracking branch
git pull

# Pull from specific remote/branch
git pull origin main

# Pull with rebase instead of merge
git pull --rebase origin main

# Pull all branches
git pull --all

# Pull and autostash local changes
git pull --autostash
```

### Fetch vs Pull

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fetch vs Pull                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  git fetch                     git pull                         │
│  ──────────                    ────────                         │
│  • Downloads remote changes    • fetch + merge                  │
│  • Updates remote tracking     • Updates working directory      │
│  • No merge                    • May cause conflicts            │
│  • Safe operation              • Modifies local branch          │
│                                                                  │
│  Recommended Workflow:                                          │
│  1. git fetch origin                                            │
│  2. git log main..origin/main  # Review changes                 │
│  3. git merge origin/main      # Or rebase                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Pushing Changes

### Basic Push

```bash
# Push to tracking branch
git push

# Push to specific remote/branch
git push origin main

# Push and set upstream tracking
git push -u origin feature-branch
# Now 'git push' will push to origin/feature-branch

# Push all branches
git push --all origin

# Push tags
git push --tags
```

### Force Push

```bash
# Force push (overwrites remote - DANGEROUS)
git push --force origin feature-branch

# Force push with lease (safer - fails if remote has new commits)
git push --force-with-lease origin feature-branch

# When to use force push:
# - After rebase (required)
# - After amending commits
# - After interactive rebase
# NEVER on shared/protected branches (main, develop)
```

### Deleting Remote Branches

```bash
# Delete remote branch
git push origin --delete feature-branch
# Or
git push origin :feature-branch

# Delete multiple remote branches
git push origin --delete branch1 branch2 branch3

# Prune local references to deleted remote branches
git remote prune origin
# Or
git fetch --prune
```

## Working with Upstream

### Fork Workflow

```bash
# 1. Fork repository on GitHub

# 2. Clone your fork
git clone git@github.com:your-user/repo.git
cd repo

# 3. Add upstream remote
git remote add upstream git@github.com:original-owner/repo.git

# 4. Verify remotes
git remote -v
# origin    git@github.com:your-user/repo.git (fetch)
# origin    git@github.com:your-user/repo.git (push)
# upstream  git@github.com:original-owner/repo.git (fetch)
# upstream  git@github.com:original-owner/repo.git (push)
```

### Syncing Fork with Upstream

```bash
# Fetch upstream changes
git fetch upstream

# Switch to main
git checkout main

# Merge upstream changes
git merge upstream/main

# Or rebase
git rebase upstream/main

# Push to your fork
git push origin main
```

### Contributing Back

```bash
# Create feature branch from updated main
git checkout main
git pull upstream main
git checkout -b feature/my-contribution

# Make changes and push to your fork
git push -u origin feature/my-contribution

# Create pull request from your fork to upstream
# (via GitHub/GitLab web interface)
```

## Tracking Branches

### Setting Up Tracking

```bash
# Create branch tracking remote
git checkout -b feature origin/feature

# Set tracking for existing branch
git branch -u origin/feature
# Or
git branch --set-upstream-to=origin/feature

# Push and set tracking
git push -u origin feature

# View tracking information
git branch -vv
```

### Working with Tracking Branches

```bash
# See ahead/behind status
git status

# See detailed tracking info
git branch -vv
# * main     abc123 [origin/main: ahead 2, behind 1] Latest commit
#   feature  def456 [origin/feature] Feature commit

# Compare with tracking branch
git diff @{upstream}
# Or
git diff @{u}

# Log commits not yet pushed
git log @{u}..HEAD

# Log commits not yet pulled
git log HEAD..@{u}
```

## Multiple Remotes

### Working with Multiple Remotes

```bash
# Common setup for open source
git remote add origin git@github.com:your-user/repo.git     # Your fork
git remote add upstream git@github.com:original/repo.git   # Original repo

# Or for deployment
git remote add origin git@github.com:company/repo.git      # Main repo
git remote add heroku git@heroku.com:app-name.git          # Heroku deploy
git remote add production git@server.com:repo.git          # Production server

# Push to specific remote
git push origin main
git push heroku main
git push production main
```

### Fetch from All Remotes

```bash
# Fetch all remotes
git fetch --all

# See all remote branches
git branch -r

# See branches from specific remote
git branch -r | grep origin/
git branch -r | grep upstream/
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│               Remote Repository Best Practices                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  General:                                                       │
│  • Use SSH over HTTPS when possible                             │
│  • Configure push.default to 'current' or 'simple'              │
│  • Set up branch protection on main branches                    │
│                                                                  │
│  Fetching/Pulling:                                              │
│  • Fetch before starting new work                               │
│  • Use --prune to clean up deleted branches                     │
│  • Prefer fetch + merge over pull for visibility                │
│                                                                  │
│  Pushing:                                                       │
│  • Never force push to shared branches                          │
│  • Use --force-with-lease instead of --force                    │
│  • Set up pre-push hooks for validation                         │
│                                                                  │
│  Collaboration:                                                 │
│  • Keep forks synced with upstream                              │
│  • Use meaningful remote names                                  │
│  • Document remote setup in README                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Configuration

```bash
# Default push behavior
git config --global push.default current

# Automatically set up tracking
git config --global push.autoSetupRemote true

# Always prune on fetch
git config --global fetch.prune true

# Show upstream in branch list
git config --global branch.autosetupmerge always

# Useful aliases
git config --global alias.sync '!git fetch --all --prune && git pull'
git config --global alias.push-force 'push --force-with-lease'
```
