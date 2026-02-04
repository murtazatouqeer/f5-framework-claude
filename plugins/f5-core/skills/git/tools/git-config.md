---
name: git-config
description: Configuring Git for optimal workflow
category: git/tools
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Configuration

## Overview

Git configuration controls behavior at three levels: system, global, and local.
Proper configuration improves productivity, ensures consistent behavior across
teams, and enables advanced features.

## Configuration Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                  Configuration Hierarchy                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Priority (highest to lowest):                                  │
│                                                                  │
│  1. Local (repository)                                          │
│     Location: .git/config                                       │
│     Command:  git config --local                                │
│                                                                  │
│  2. Global (user)                                               │
│     Location: ~/.gitconfig or ~/.config/git/config              │
│     Command:  git config --global                               │
│                                                                  │
│  3. System (machine)                                            │
│     Location: /etc/gitconfig                                    │
│     Command:  git config --system                               │
│                                                                  │
│  Local overrides Global overrides System                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Essential Configuration

### User Identity

```bash
# Required for commits
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Verify settings
git config user.name
git config user.email

# Per-repository identity (for work vs personal)
git config --local user.email "work.email@company.com"
```

### Default Branch

```bash
# Set default branch name for new repositories
git config --global init.defaultBranch main

# Previously created repos still use master
# Rename manually:
git branch -m master main
```

### Editor Configuration

```bash
# Set default editor
git config --global core.editor "code --wait"    # VS Code
git config --global core.editor "vim"            # Vim
git config --global core.editor "nano"           # Nano
git config --global core.editor "subl -n -w"     # Sublime Text
git config --global core.editor "atom --wait"    # Atom

# For interactive rebase and commit messages
```

### Diff and Merge Tools

```bash
# Configure diff tool
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'

# Configure merge tool
git config --global merge.tool vscode
git config --global mergetool.vscode.cmd 'code --wait $MERGED'
git config --global mergetool.keepBackup false

# Use difftool
git difftool

# Use mergetool during conflict
git mergetool
```

## Behavior Configuration

### Line Endings

```bash
# Windows: Convert LF to CRLF on checkout
git config --global core.autocrlf true

# macOS/Linux: Convert CRLF to LF on commit
git config --global core.autocrlf input

# Disable conversion (use for binary files or consistent team setup)
git config --global core.autocrlf false

# Warn about line ending issues
git config --global core.safecrlf warn
```

### Whitespace

```bash
# Check whitespace errors
git config --global core.whitespace trailing-space,space-before-tab

# Fix whitespace on apply
git config --global apply.whitespace fix
```

### File Permissions

```bash
# Ignore file mode changes (useful on Windows)
git config --global core.fileMode false

# Trust file permissions
git config --global core.fileMode true
```

## Push and Pull Configuration

### Push Settings

```bash
# Push current branch only (safest)
git config --global push.default current

# Push to matching remote branch
git config --global push.default simple

# Auto setup remote tracking
git config --global push.autoSetupRemote true

# Require remote branch to exist
git config --global push.default nothing
```

### Pull Settings

```bash
# Rebase on pull instead of merge
git config --global pull.rebase true

# Only fast-forward pulls
git config --global pull.ff only

# Auto-stash before pull
git config --global rebase.autoStash true
```

### Fetch Settings

```bash
# Prune deleted remote branches on fetch
git config --global fetch.prune true

# Prune deleted remote tags
git config --global fetch.pruneTags true

# Fetch all remotes by default
git config --global fetch.all true
```

## Display Configuration

### Colors

```bash
# Enable colors
git config --global color.ui auto

# Customize specific colors
git config --global color.branch.current "yellow reverse"
git config --global color.branch.local yellow
git config --global color.branch.remote green

git config --global color.status.added green
git config --global color.status.changed yellow
git config --global color.status.untracked red
```

### Pager

```bash
# Use less with specific options
git config --global core.pager "less -FRSX"

# Use delta for better diffs
git config --global core.pager delta

# Disable pager for specific commands
git config --global pager.branch false
git config --global pager.stash false
```

### Log Format

```bash
# Custom log format
git config --global format.pretty "format:%C(yellow)%h%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset"

# Always show stats in log
git config --global log.stat true

# Show branch decorations
git config --global log.decorate true
```

## Advanced Configuration

### Credential Storage

```bash
# Cache credentials temporarily (15 minutes)
git config --global credential.helper cache

# Cache for longer (1 hour = 3600 seconds)
git config --global credential.helper 'cache --timeout=3600'

# Store credentials permanently (less secure)
git config --global credential.helper store

# Use OS keychain (recommended)
# macOS
git config --global credential.helper osxkeychain

# Windows
git config --global credential.helper wincred

# Linux (requires libsecret)
git config --global credential.helper libsecret
```

### Performance

```bash
# Enable filesystem cache (Windows)
git config --global core.fscache true

# Preload index for faster status
git config --global core.preloadindex true

# Use fewer threads for packing
git config --global pack.threads 4

# Enable commit graph for faster log
git config --global core.commitGraph true
git config --global gc.writeCommitGraph true

# Enable filesystem monitor (for large repos)
git config --global core.fsmonitor true
```

### Security

```bash
# Require signed commits
git config --global commit.gpgsign true

# Set GPG key
git config --global user.signingkey YOUR_KEY_ID

# GPG program location
git config --global gpg.program gpg

# Verify signatures on pull
git config --global merge.verifySignatures true
```

### Rerere (Reuse Recorded Resolution)

```bash
# Enable rerere
git config --global rerere.enabled true

# Auto-stage rerere resolutions
git config --global rerere.autoupdate true

# This remembers how you resolved merge conflicts
# and automatically applies the same resolution next time
```

## Repository-Specific Settings

### Local Configuration

```bash
# Work email for this repo
git config --local user.email "work@company.com"

# Different signing key
git config --local user.signingkey WORK_KEY_ID

# Different remote URL
git config --local remote.origin.url git@github-work:org/repo.git
```

### Conditional Includes

```ini
# ~/.gitconfig
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work

[includeIf "gitdir:~/personal/"]
    path = ~/.gitconfig-personal
```

```ini
# ~/.gitconfig-work
[user]
    email = work@company.com
    signingkey = WORK_KEY

[core]
    sshCommand = ssh -i ~/.ssh/work_key
```

## Common Configuration File

```ini
# ~/.gitconfig - Complete example
[user]
    name = Your Name
    email = your.email@example.com

[init]
    defaultBranch = main

[core]
    editor = code --wait
    autocrlf = input
    pager = less -FRSX
    excludesfile = ~/.gitignore_global
    whitespace = trailing-space,space-before-tab

[push]
    default = current
    autoSetupRemote = true

[pull]
    rebase = true
    ff = only

[fetch]
    prune = true
    pruneTags = true

[merge]
    tool = vscode
    conflictstyle = diff3

[mergetool]
    keepBackup = false

[mergetool "vscode"]
    cmd = code --wait $MERGED

[diff]
    tool = vscode
    colorMoved = default

[difftool "vscode"]
    cmd = code --wait --diff $LOCAL $REMOTE

[rebase]
    autoStash = true
    autosquash = true

[rerere]
    enabled = true
    autoupdate = true

[color]
    ui = auto

[color "branch"]
    current = yellow reverse
    local = yellow
    remote = green

[color "status"]
    added = green
    changed = yellow
    untracked = red

[alias]
    co = checkout
    br = branch
    ci = commit
    st = status
    lg = log --graph --oneline --decorate
    unstage = reset HEAD --
    last = log -1 HEAD
    aliases = config --get-regexp alias

[credential]
    helper = osxkeychain

[commit]
    gpgsign = false
    template = ~/.gitmessage

[log]
    decorate = true
    date = relative

[help]
    autocorrect = 10
```

## Viewing Configuration

```bash
# List all settings
git config --list

# List with origin (which file)
git config --list --show-origin

# List specific level
git config --list --local
git config --list --global
git config --list --system

# Get specific value
git config user.name
git config --get remote.origin.url

# Get all values for key (if multiple)
git config --get-all user.email
```

## Modifying Configuration

```bash
# Set value
git config --global user.name "New Name"

# Unset value
git config --global --unset user.name

# Unset all values for key
git config --global --unset-all user.email

# Rename section
git config --global --rename-section alias shortcuts

# Edit config file directly
git config --global -e
git config --local -e
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Git Configuration Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Essential Settings:                                            │
│  □ Set user.name and user.email                                 │
│  □ Configure default editor                                     │
│  □ Set init.defaultBranch to main                               │
│  □ Configure credential helper                                  │
│                                                                  │
│  Recommended Settings:                                          │
│  □ Enable pull.rebase                                           │
│  □ Enable fetch.prune                                           │
│  □ Enable rerere                                                │
│  □ Set push.default to current                                  │
│                                                                  │
│  For Teams:                                                     │
│  □ Standardize line ending settings                             │
│  □ Share .gitattributes for consistent handling                 │
│  □ Document required configuration in README                    │
│  □ Use conditional includes for work/personal                   │
│                                                                  │
│  Security:                                                      │
│  □ Use SSH keys or credential helpers                           │
│  □ Consider GPG signing for important repos                     │
│  □ Never store credentials in plain text                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Reference

```bash
# Essential setup
git config --global user.name "Your Name"
git config --global user.email "email@example.com"
git config --global init.defaultBranch main
git config --global core.editor "code --wait"

# Recommended
git config --global pull.rebase true
git config --global fetch.prune true
git config --global push.autoSetupRemote true
git config --global rerere.enabled true

# View all settings
git config --list --show-origin

# Edit directly
git config --global -e
```
