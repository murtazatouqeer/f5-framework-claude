---
name: gitflow
description: GitFlow branching model for release management
category: git/workflows
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GitFlow Workflow

## Overview

GitFlow is a branching model designed for projects with scheduled releases.
It defines strict branch roles and a structured approach to feature
development, releases, and hotfixes.

## Branch Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitFlow Branch Model                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  main      ─●────────────────●────────────────●────────────●──▶ │
│             │ v1.0           │ v1.1           │ v1.2       │     │
│             │                │                │            │     │
│  hotfix     │                │     ●─●────────┘            │     │
│             │                │       hotfix/critical       │     │
│             │                │                             │     │
│  release    │         ●──●──●                              │     │
│             │         release/1.1                          │     │
│             │          │                                   │     │
│  develop   ─●─────●───●────●────●────●────●────●──────────●──▶  │
│             │      \     /       \    \   /     \        /      │
│  feature    │       ●───●         ●────●──●      ●──●──●        │
│             │       feature/A     feature/B      feature/C      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Branch Types

### Main Branches

```
┌─────────────────────────────────────────────────────────────────┐
│                      Main Branches                               │
├──────────┬──────────────────────────────────────────────────────┤
│ Branch   │ Purpose                                              │
├──────────┼──────────────────────────────────────────────────────┤
│ main     │ Production-ready code, tagged releases               │
│ develop  │ Integration branch for features                      │
└──────────┴──────────────────────────────────────────────────────┘
```

### Supporting Branches

```
┌─────────────────────────────────────────────────────────────────┐
│                   Supporting Branches                            │
├──────────────┬──────────┬──────────┬───────────────────────────┤
│ Type         │ From     │ Into     │ Naming                    │
├──────────────┼──────────┼──────────┼───────────────────────────┤
│ feature      │ develop  │ develop  │ feature/feature-name      │
│ release      │ develop  │ main,    │ release/v1.2.0            │
│              │          │ develop  │                           │
│ hotfix       │ main     │ main,    │ hotfix/description        │
│              │          │ develop  │                           │
└──────────────┴──────────┴──────────┴───────────────────────────┘
```

## Feature Development

### Starting a Feature

```bash
# Ensure develop is up to date
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/user-authentication

# Alternative with git-flow tool
git flow feature start user-authentication
```

### Working on Feature

```bash
# Make commits
git add .
git commit -m "feat(auth): add login form"

git add .
git commit -m "feat(auth): add JWT token generation"

# Keep updated with develop
git fetch origin
git rebase origin/develop
# or
git merge origin/develop
```

### Finishing Feature

```bash
# Merge back to develop
git checkout develop
git pull origin develop
git merge --no-ff feature/user-authentication

# Push develop
git push origin develop

# Delete feature branch
git branch -d feature/user-authentication
git push origin --delete feature/user-authentication

# With git-flow tool
git flow feature finish user-authentication
```

## Release Process

### Starting a Release

```bash
# Start release from develop
git checkout develop
git pull origin develop
git checkout -b release/v1.2.0

# With git-flow tool
git flow release start v1.2.0
```

### Release Preparation

```bash
# Bump version
npm version 1.2.0 --no-git-tag-version
# or manually edit package.json

# Update changelog
# CHANGELOG.md additions

# Commit release preparation
git add .
git commit -m "chore(release): prepare v1.2.0"

# Bug fixes only from this point
git add .
git commit -m "fix: resolve last-minute bug"
```

### Finishing Release

```bash
# Merge to main
git checkout main
git pull origin main
git merge --no-ff release/v1.2.0 -m "Release v1.2.0"

# Tag the release
git tag -a v1.2.0 -m "Version 1.2.0"

# Merge back to develop
git checkout develop
git pull origin develop
git merge --no-ff release/v1.2.0 -m "Merge release/v1.2.0 back to develop"

# Push everything
git push origin main
git push origin develop
git push origin v1.2.0

# Delete release branch
git branch -d release/v1.2.0
git push origin --delete release/v1.2.0

# With git-flow tool
git flow release finish v1.2.0
```

## Hotfix Process

### Starting a Hotfix

```bash
# Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# With git-flow tool
git flow hotfix start critical-security-fix
```

### Applying the Fix

```bash
# Make the fix
git add .
git commit -m "fix(security): patch XSS vulnerability"

# Bump patch version
npm version patch --no-git-tag-version
git add .
git commit -m "chore: bump version to 1.2.1"
```

### Finishing Hotfix

```bash
# Merge to main
git checkout main
git merge --no-ff hotfix/critical-security-fix -m "Hotfix: critical security patch"

# Tag the hotfix release
git tag -a v1.2.1 -m "Hotfix v1.2.1"

# Merge to develop (or current release branch if one exists)
git checkout develop
git merge --no-ff hotfix/critical-security-fix -m "Merge hotfix to develop"

# Push everything
git push origin main
git push origin develop
git push origin v1.2.1

# Delete hotfix branch
git branch -d hotfix/critical-security-fix
git push origin --delete hotfix/critical-security-fix

# With git-flow tool
git flow hotfix finish critical-security-fix
```

## Git-Flow Tool

### Installation

```bash
# macOS
brew install git-flow-avh

# Ubuntu/Debian
apt-get install git-flow

# Windows (with Git for Windows)
# Included in Git for Windows
```

### Initialization

```bash
# Initialize git-flow in repository
git flow init

# Prompts:
# Branch name for production releases: [main]
# Branch name for "next release" development: [develop]
# Feature branches prefix: [feature/]
# Release branches prefix: [release/]
# Hotfix branches prefix: [hotfix/]
# Support branches prefix: [support/]
# Version tag prefix: [v]
```

### Common Commands

```bash
# Features
git flow feature start <name>
git flow feature finish <name>
git flow feature publish <name>
git flow feature pull origin <name>

# Releases
git flow release start <version>
git flow release finish <version>
git flow release publish <version>

# Hotfixes
git flow hotfix start <name>
git flow hotfix finish <name>
```

## Version Tagging

```bash
# Semantic versioning
# MAJOR.MINOR.PATCH
# 1.2.3

# Create annotated tag
git tag -a v1.2.0 -m "Version 1.2.0

Features:
- User authentication
- Dashboard redesign

Bug Fixes:
- Fix login redirect
- Fix date formatting"

# List tags
git tag -l "v1.*"

# Push tags
git push origin v1.2.0
git push origin --tags
```

## When to Use GitFlow

```
┌─────────────────────────────────────────────────────────────────┐
│                   When to Use GitFlow                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Good For:                                                   │
│  • Scheduled release cycles (e.g., monthly)                     │
│  • Multiple versions in production                              │
│  • Strict release management requirements                       │
│  • Teams that need parallel development                         │
│  • Products requiring version maintenance                       │
│                                                                  │
│  ❌ Not Ideal For:                                              │
│  • Continuous deployment                                        │
│  • Small teams with simple workflows                            │
│  • Projects needing rapid iterations                            │
│  • Single version in production                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  GitFlow Best Practices                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Never Commit Directly to Main                               │
│     └── Always through release or hotfix                        │
│                                                                  │
│  2. Keep Develop Stable                                         │
│     └── Should always be deployable                             │
│                                                                  │
│  3. Use Meaningful Branch Names                                 │
│     └── feature/JIRA-123-user-login                             │
│                                                                  │
│  4. Delete Branches After Merge                                 │
│     └── Keep repository clean                                   │
│                                                                  │
│  5. Tag All Releases                                            │
│     └── Use semantic versioning                                 │
│                                                                  │
│  6. Hotfixes Go to Both Main and Develop                        │
│     └── Don't forget to merge back                              │
│                                                                  │
│  7. Release Branches for Stabilization                          │
│     └── Only bug fixes, no new features                         │
│                                                                  │
│  8. Code Review Before Merge                                    │
│     └── Use pull requests                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
