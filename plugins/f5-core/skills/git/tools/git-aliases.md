---
name: git-aliases
description: Creating shortcuts for common Git commands
category: git/tools
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Aliases

## Overview

Git aliases are custom shortcuts for frequently used commands. They improve
productivity by reducing typing, preventing errors, and encapsulating complex
command sequences into simple, memorable names.

## Creating Aliases

### Using Git Config

```bash
# Basic syntax
git config --global alias.<name> '<command>'

# Simple alias
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.st status

# With options
git config --global alias.unstage 'reset HEAD --'
git config --global alias.last 'log -1 HEAD'

# Complex commands (use quotes)
git config --global alias.lg "log --graph --oneline --decorate"
```

### Editing Config Directly

```bash
# Open global config in editor
git config --global -e

# Or edit file directly
# ~/.gitconfig (global)
# .git/config (local repository)
```

```ini
# ~/.gitconfig
[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
    unstage = reset HEAD --
    last = log -1 HEAD
    lg = log --graph --oneline --decorate
```

## Essential Aliases

### Basic Shortcuts

```ini
[alias]
    # Shortcuts
    co = checkout
    br = branch
    ci = commit
    st = status
    df = diff
    dc = diff --cached

    # Common operations
    aa = add --all
    ap = add --patch
    cm = commit -m
    ca = commit --amend
    can = commit --amend --no-edit
```

### Branch Operations

```ini
[alias]
    # Branch management
    branches = branch -a
    remotes = remote -v

    # Create and switch
    cob = checkout -b
    com = checkout main
    cod = checkout develop

    # Delete branches
    bd = branch -d
    bD = branch -D

    # List merged/unmerged
    merged = branch --merged
    unmerged = branch --no-merged

    # Clean merged branches
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"
```

### Log Viewing

```ini
[alias]
    # Pretty logs
    lg = log --graph --oneline --decorate
    lga = log --graph --oneline --decorate --all
    lgb = log --graph --oneline --decorate --all --branches

    # Detailed log
    ll = log --pretty=format:'%C(yellow)%h%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit

    # Log with stats
    ls = log --stat --oneline

    # Last N commits
    l1 = log -1
    l5 = log -5 --oneline
    l10 = log -10 --oneline

    # Show files changed in each commit
    lf = log --name-status --oneline

    # Log for specific author
    my = log --author='Your Name'

    # What changed today
    today = log --since='00:00:00' --oneline

    # What did I do yesterday
    yesterday = log --since='yesterday 00:00:00' --until='today 00:00:00' --oneline
```

### Diff Aliases

```ini
[alias]
    # Diff shortcuts
    d = diff
    ds = diff --staged
    dc = diff --cached
    dw = diff --word-diff

    # Show what changed in last commit
    dlast = diff HEAD~1

    # Diff with specific branch
    dm = diff main
    dd = diff develop

    # Stats only
    stat = diff --stat
```

### Stash Operations

```ini
[alias]
    # Stash shortcuts
    ss = stash save
    sl = stash list
    sp = stash pop
    sa = stash apply
    sd = stash drop
    sshow = stash show -p

    # Stash with message
    save = stash save

    # Show stash contents
    stashls = stash list --format='%gd: %cr | %gs'
```

### Remote Operations

```ini
[alias]
    # Fetch/pull/push
    f = fetch
    fa = fetch --all
    fp = fetch --prune

    pl = pull
    plr = pull --rebase

    ps = push
    psu = push -u origin HEAD
    psf = push --force-with-lease

    # Remote management
    rv = remote -v
    ra = remote add
    rr = remote remove
```

### Undo/Reset Operations

```ini
[alias]
    # Undo changes
    unstage = reset HEAD --
    discard = checkout --
    undo = reset --soft HEAD~1

    # Reset variations
    uncommit = reset --soft HEAD~1
    unadd = reset HEAD

    # Clean untracked
    clean-all = clean -fd

    # Hard reset to remote
    resethard = reset --hard origin/main
```

## Advanced Aliases

### Shell Commands

```ini
[alias]
    # Aliases starting with ! run in shell
    # Get current branch name
    current = !git branch --show-current

    # Open in browser (GitHub)
    web = !open $(git remote get-url origin | sed 's/git@github.com:/https:\\/\\/github.com\\//' | sed 's/.git$//')

    # Create branch and push
    publish = "!git push -u origin $(git branch --show-current)"

    # Delete branch locally and remotely
    nuke = "!f() { git branch -D $1 && git push origin --delete $1; }; f"

    # Sync with main
    sync = "!git fetch origin && git rebase origin/main"

    # Interactive fixup
    fixup = "!git log -n 50 --pretty=format:'%h %s' | fzf | cut -c -7 | xargs -o git commit --fixup"
```

### Git Flow Aliases

```ini
[alias]
    # Feature workflow
    feature-start = "!f() { git checkout develop && git pull && git checkout -b feature/$1; }; f"
    feature-finish = "!f() { git checkout develop && git merge --no-ff feature/$1 && git branch -d feature/$1; }; f"

    # Hotfix workflow
    hotfix-start = "!f() { git checkout main && git pull && git checkout -b hotfix/$1; }; f"
    hotfix-finish = "!f() { git checkout main && git merge --no-ff hotfix/$1 && git checkout develop && git merge --no-ff hotfix/$1 && git branch -d hotfix/$1; }; f"

    # Release workflow
    release-start = "!f() { git checkout develop && git pull && git checkout -b release/$1; }; f"
```

### Information Aliases

```ini
[alias]
    # Show aliases
    aliases = config --get-regexp alias

    # Show current config
    whoami = "!git config user.name && git config user.email"

    # Count commits by author
    contributors = shortlog -sn --all

    # File statistics
    file-stats = "!git log --all --numstat | grep -v '^-' | cut -f3 | sort | uniq -c | sort -rn | head -20"

    # Branch age
    branch-age = "!git for-each-ref --sort=committerdate refs/heads/ --format='%(committerdate:short) %(refname:short)'"

    # Find file in history
    find-file = "!f() { git log --all --full-history -- \"*/$1\"; }; f"

    # Search commits by message
    search = "!f() { git log --all --oneline --grep=\"$1\"; }; f"
```

### Workflow Aliases

```ini
[alias]
    # Morning routine
    morning = "!git fetch --all --prune && git status"

    # End of day
    wip = "!git add -A && git commit -m 'WIP: work in progress [skip ci]'"
    unwip = "!git log -1 --format=%s | grep -q '^WIP' && git reset HEAD~1"

    # Quick save
    save = "!git add -A && git commit -m 'SAVEPOINT'"

    # Amend without editing
    oops = "!git add -A && git commit --amend --no-edit"

    # Start fresh PR
    fresh = "!git checkout main && git pull && git checkout -b"

    # Update PR from main
    update = "!git fetch origin main:main && git rebase main"
```

## Alias Categories Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                 Alias Categories                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Shortcuts (1-2 chars):                                         │
│  co, br, ci, st, df, lg, pl, ps, f                              │
│                                                                  │
│  Actions (verb):                                                │
│  unstage, uncommit, discard, publish, sync, cleanup             │
│                                                                  │
│  Information (noun):                                            │
│  aliases, whoami, contributors, branches, remotes               │
│                                                                  │
│  Workflow (process):                                            │
│  morning, wip, unwip, save, oops, fresh, update                 │
│                                                                  │
│  Complex (shell):                                               │
│  Start with !, can use functions, pipes, other tools            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Tips and Tricks

### Alias Functions

```ini
[alias]
    # Function syntax: "!f() { commands; }; f"

    # Accept parameters
    cob = "!f() { git checkout -b $1; }; f"

    # Multiple parameters
    publish = "!f() { git push -u ${1:-origin} ${2:-HEAD}; }; f"

    # Default values
    lg = "!f() { git log --oneline -${1:-10}; }; f"

    # Conditional logic
    done = "!f() { \
        branch=$(git branch --show-current); \
        git checkout main && \
        git branch -d $branch; \
    }; f"
```

### Debugging Aliases

```bash
# See what alias expands to
git config --get alias.lg

# List all aliases
git config --get-regexp alias

# Test alias expansion
GIT_TRACE=1 git lg
```

### Sharing Aliases

```bash
# Export aliases
git config --global --list | grep alias > aliases.txt

# Import aliases (add to ~/.gitconfig)
cat aliases.txt >> ~/.gitconfig

# Share via dotfiles repo
# Keep .gitconfig in version control
```

## Complete Alias Set

```ini
# ~/.gitconfig
[alias]
    # === Shortcuts ===
    co = checkout
    br = branch
    ci = commit
    st = status
    df = diff
    dc = diff --cached

    # === Commit ===
    cm = commit -m
    ca = commit --amend
    can = commit --amend --no-edit
    aa = add --all
    ap = add --patch

    # === Branch ===
    cob = checkout -b
    com = checkout main
    cod = checkout develop
    bd = branch -d
    bD = branch -D
    branches = branch -a
    cleanup = "!git branch --merged | grep -v '\\*\\|main\\|develop' | xargs -n 1 git branch -d"

    # === Log ===
    lg = log --graph --oneline --decorate
    lga = log --graph --oneline --decorate --all
    ll = log --pretty=format:'%C(yellow)%h%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset'
    l5 = log -5 --oneline
    today = log --since='00:00:00' --oneline

    # === Remote ===
    f = fetch
    fa = fetch --all --prune
    pl = pull
    plr = pull --rebase
    ps = push
    psu = push -u origin HEAD
    psf = push --force-with-lease

    # === Stash ===
    ss = stash save
    sl = stash list
    sp = stash pop
    sa = stash apply

    # === Undo ===
    unstage = reset HEAD --
    uncommit = reset --soft HEAD~1
    discard = checkout --

    # === Workflow ===
    wip = "!git add -A && git commit -m 'WIP'"
    save = "!git add -A && git commit -m 'SAVEPOINT'"
    oops = "!git add -A && git commit --amend --no-edit"
    sync = "!git fetch origin && git rebase origin/main"

    # === Info ===
    aliases = config --get-regexp alias
    whoami = "!git config user.name && git config user.email"
    contributors = shortlog -sn --all
```

## Useful Commands

```bash
# Create alias
git config --global alias.name 'command'

# Remove alias
git config --global --unset alias.name

# List aliases
git config --get-regexp alias

# Edit config directly
git config --global -e

# Use alias
git name

# Override alias temporarily
git --no-optional-locks command
```
