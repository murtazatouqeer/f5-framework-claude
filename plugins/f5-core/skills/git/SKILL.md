---
name: git
description: Git version control and collaboration workflows
category: skill
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: true
context: inject
---

# Git Skills

## Overview

Git version control knowledge for effective code management and team
collaboration. From basic operations to advanced techniques and workflow
strategies.

## Git Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Git Data Flow                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Working       Staging        Local          Remote              │
│  Directory     Area           Repository     Repository          │
│  ┌───────┐    ┌───────┐      ┌───────┐      ┌───────┐           │
│  │       │    │       │      │       │      │       │           │
│  │ Files │───▶│Staged │─────▶│Commits│─────▶│Origin │           │
│  │       │add │       │commit│       │ push │       │           │
│  └───────┘    └───────┘      └───────┘      └───────┘           │
│      ▲                           │              │                │
│      │                           │              │                │
│      └───────────────────────────┴──────────────┘                │
│                checkout / pull / fetch                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Git Object Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    Git Object Types                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐   │
│  │  Blob   │     │  Tree   │     │ Commit  │     │   Tag   │   │
│  │ (file)  │◄────│ (dir)   │◄────│         │◄────│         │   │
│  └─────────┘     └─────────┘     └─────────┘     └─────────┘   │
│                       │               │                         │
│                       ▼               ▼                         │
│                  ┌─────────┐    ┌──────────┐                   │
│                  │  Blob   │    │  Parent  │                   │
│                  │  Tree   │    │  Commit  │                   │
│                  └─────────┘    └──────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Categories

### Fundamentals
Core Git operations and concepts for daily development work.

| Skill | Description |
|-------|-------------|
| git-basics | Repository initialization and basic commands |
| staging-committing | Working with the staging area and commits |
| branching | Creating and managing branches |
| merging | Combining branches and handling merges |

### Workflows
Team collaboration patterns and branching strategies.

| Skill | Description |
|-------|-------------|
| gitflow | GitFlow branching model |
| github-flow | GitHub Flow simplified workflow |
| trunk-based | Trunk-based development |
| feature-branches | Feature branch workflow |

### Collaboration
Working with teams and remote repositories.

| Skill | Description |
|-------|-------------|
| pull-requests | Creating and reviewing PRs |
| code-review | Code review best practices |
| merge-conflicts | Resolving merge conflicts |
| remote-repos | Working with remote repositories |

### Advanced
Power user techniques for complex scenarios.

| Skill | Description |
|-------|-------------|
| rebasing | Rebase operations and strategies |
| cherry-picking | Selective commit application |
| interactive-rebase | Interactive history editing |
| bisect | Binary search for bugs |
| reflog | Recovery with reflog |

### Best Practices
Standards and conventions for clean repositories.

| Skill | Description |
|-------|-------------|
| commit-messages | Conventional commit format |
| branch-naming | Branch naming conventions |
| gitignore | File exclusion patterns |
| git-hooks | Automation with hooks |

### Tools
Configuration and productivity enhancements.

| Skill | Description |
|-------|-------------|
| git-aliases | Custom command shortcuts |
| git-config | Git configuration options |

## Quick Reference

### Essential Commands

```bash
# Repository
git init                    # Initialize new repo
git clone <url>             # Clone remote repo

# Changes
git status                  # Check status
git add <file>              # Stage file
git commit -m "message"     # Commit staged changes

# Branches
git branch                  # List branches
git checkout -b <branch>    # Create and switch
git merge <branch>          # Merge branch

# Remote
git pull                    # Fetch and merge
git push                    # Push to remote
git fetch                   # Fetch without merge
```

### Common Workflows

```bash
# Feature development
git checkout -b feature/new-feature
# ... make changes ...
git add .
git commit -m "feat: add new feature"
git push -u origin feature/new-feature
# Create PR, merge, delete branch

# Hotfix
git checkout main
git pull
git checkout -b hotfix/critical-bug
# ... fix bug ...
git commit -m "fix: resolve critical bug"
git push -u origin hotfix/critical-bug
# Create PR with priority review
```

## File Structure

```
skills/git/
├── _index.md
├── fundamentals/
│   ├── git-basics.md
│   ├── staging-committing.md
│   ├── branching.md
│   └── merging.md
├── workflows/
│   ├── gitflow.md
│   ├── github-flow.md
│   ├── trunk-based.md
│   └── feature-branches.md
├── collaboration/
│   ├── pull-requests.md
│   ├── code-review.md
│   ├── merge-conflicts.md
│   └── remote-repos.md
├── advanced/
│   ├── rebasing.md
│   ├── cherry-picking.md
│   ├── interactive-rebase.md
│   ├── bisect.md
│   └── reflog.md
├── best-practices/
│   ├── commit-messages.md
│   ├── branch-naming.md
│   ├── gitignore.md
│   └── git-hooks.md
└── tools/
    ├── git-aliases.md
    └── git-config.md
```
