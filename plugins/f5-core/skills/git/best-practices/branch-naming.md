---
name: branch-naming
description: Consistent branch naming conventions
category: git/best-practices
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Branch Naming

## Overview

Consistent branch naming conventions improve team collaboration, automate
CI/CD workflows, and make repository navigation easier. Good branch names
communicate purpose, ownership, and context at a glance.

## Naming Convention Patterns

```
┌─────────────────────────────────────────────────────────────────┐
│                Branch Naming Patterns                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pattern: <type>/<ticket>-<short-description>                   │
│                                                                  │
│  Examples:                                                      │
│  feature/PROJ-123-user-authentication                           │
│  bugfix/PROJ-456-fix-login-redirect                             │
│  hotfix/PROJ-789-security-patch                                 │
│  release/v2.1.0                                                 │
│  chore/PROJ-101-update-dependencies                             │
│                                                                  │
│  Alternative Pattern: <type>/<description>                      │
│                                                                  │
│  Examples:                                                      │
│  feature/user-authentication                                    │
│  bugfix/login-redirect                                          │
│  hotfix/security-patch                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Branch Types

### Standard Prefixes

```
┌──────────┬───────────────────────────────────────────────────────┐
│ Prefix   │ Purpose                                               │
├──────────┼───────────────────────────────────────────────────────┤
│ feature/ │ New feature development                               │
│ bugfix/  │ Bug fix for development                               │
│ hotfix/  │ Urgent fix for production                             │
│ release/ │ Release preparation                                   │
│ chore/   │ Maintenance tasks (deps, config)                      │
│ docs/    │ Documentation updates                                 │
│ test/    │ Test additions or modifications                       │
│ refactor/│ Code refactoring                                      │
│ style/   │ Code style/formatting                                 │
│ perf/    │ Performance improvements                              │
│ ci/      │ CI/CD pipeline changes                                │
│ exp/     │ Experimental/prototype                                │
└──────────┴───────────────────────────────────────────────────────┘
```

### Examples by Type

```bash
# Feature branches
feature/user-registration
feature/JIRA-123-shopping-cart
feature/payment-integration
feature/mobile-responsive

# Bug fixes
bugfix/login-validation
bugfix/JIRA-456-memory-leak
bugfix/null-pointer-exception

# Hotfixes
hotfix/security-vulnerability
hotfix/JIRA-789-production-crash
hotfix/data-corruption

# Releases
release/v1.0.0
release/v2.1.0-beta
release/2024-01

# Maintenance
chore/update-dependencies
chore/cleanup-unused-code
chore/configure-eslint

# Documentation
docs/api-documentation
docs/readme-update
docs/installation-guide

# Testing
test/integration-tests
test/e2e-coverage
test/performance-benchmarks
```

## Naming Rules

### Character Guidelines

```
┌─────────────────────────────────────────────────────────────────┐
│                  Branch Naming Rules                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ DO:                                                         │
│  • Use lowercase letters                                        │
│  • Use hyphens (-) to separate words                            │
│  • Use forward slashes (/) for hierarchy                        │
│  • Keep names short but descriptive                             │
│  • Include ticket/issue numbers when available                  │
│  • Use alphanumeric characters and hyphens only                 │
│                                                                  │
│  ❌ DON'T:                                                      │
│  • Use spaces (git doesn't allow)                               │
│  • Use uppercase letters (case-sensitivity issues)              │
│  • Use special characters (@, &, !, etc.)                       │
│  • Use underscores (harder to read)                             │
│  • Start with numbers or hyphens                                │
│  • Use extremely long names (>50 chars)                         │
│  • Use vague names (my-branch, test-branch)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Length Guidelines

```bash
# Ideal length: 20-50 characters (excluding type prefix)
# Maximum recommended: 63 characters (some systems limit)

# Good lengths
feature/user-auth                          # 10 chars
feature/JIRA-123-shopping-cart             # 26 chars
bugfix/fix-payment-validation-error        # 31 chars

# Too short (unclear)
feature/auth                               # Too vague
bugfix/fix                                 # What does this fix?

# Too long (unwieldy)
feature/JIRA-123-add-user-registration-with-email-verification-and-password-reset
# Hard to read and type
```

## Ticket Integration

### Including Issue Numbers

```bash
# Jira-style
feature/PROJ-123-user-registration
bugfix/PROJ-456-fix-cart-total
hotfix/PROJ-789-security-patch

# GitHub-style
feature/123-user-registration
bugfix/456-fix-cart-total

# GitLab-style
feature/issue-123-user-registration

# Without ticket (internal/maintenance work)
chore/update-dependencies
docs/improve-readme
```

### Automation Benefits

```yaml
# CI/CD can extract ticket number from branch name
# Example GitHub Actions workflow
- name: Extract Jira ticket
  run: |
    BRANCH=${GITHUB_REF#refs/heads/}
    TICKET=$(echo $BRANCH | grep -oP '[A-Z]+-\d+' || echo "")
    echo "TICKET=$TICKET" >> $GITHUB_ENV

# Automatic Jira transitions based on branch
# feature/ → In Progress
# release/ → Ready for Release
```

## Team Patterns

### By Developer

```bash
# Include developer initials for personal branches
dev/jd/experiment-new-ui
dev/js/refactor-auth

# Not recommended for shared branches
# Only for personal experimentation
```

### By Sprint/Iteration

```bash
# Sprint-based naming
sprint-12/feature/user-dashboard
sprint-12/bugfix/login-issue

# Quarter-based
q4-2024/feature/analytics-dashboard
```

### By Module/Service

```bash
# For monorepos or microservices
backend/feature/add-caching
frontend/feature/new-dashboard
api/bugfix/rate-limiting
auth-service/hotfix/token-refresh
```

## Protected Branch Names

### Reserved Names

```bash
# These should NEVER be used for feature work
main              # Production code
master            # Legacy production
develop           # Integration branch
staging           # Pre-production
production        # Production alias

# These are typically protected in CI/CD
release/*         # Managed release process
hotfix/*          # Emergency fixes only
```

### Branch Protection

```yaml
# GitHub branch protection rules
branches:
  - name: main
    protection:
      required_reviews: 2
      dismiss_stale_reviews: true
      require_code_owner_reviews: true

  - name: develop
    protection:
      required_reviews: 1
      require_status_checks: true

  - name: "release/*"
    protection:
      required_reviews: 2
      require_signed_commits: true
```

## Common Anti-Patterns

### What to Avoid

```bash
# Vague names
my-branch
test
fix
update
temp

# Personal branches on main repo
john-working
my-feature-branch
johns-changes

# Dates without context
2024-01-15
january-work

# Mixed conventions
Feature_UserAuth     # Uppercase, underscore
BUGFIX/LOGIN         # All caps
fix-Bug-Login        # Mixed case

# Too much nesting
feature/auth/user/login/fix  # Too deep

# No type prefix
user-authentication   # Is this a feature? bugfix?
```

### Good Alternatives

```bash
# Instead of vague names
feature/add-user-authentication
bugfix/fix-login-redirect
test/add-integration-tests

# Instead of personal names
feature/JIRA-123-refactor-auth

# Instead of just dates
release/v2.1.0
sprint-15/feature/dashboard
```

## Naming Conventions by Workflow

### GitFlow

```bash
# Main branches
main                    # Production releases
develop                 # Integration branch

# Supporting branches
feature/JIRA-123-description
release/v1.2.0
hotfix/v1.2.1-critical-fix
```

### GitHub Flow

```bash
# Main branch
main                    # Always deployable

# Feature branches
feature/description
bugfix/description
```

### Trunk-Based

```bash
# Main branch
main                    # Trunk

# Short-lived branches
feature/short-description    # Merged within 1-2 days
```

## Automation Examples

### Pre-commit Hook for Branch Names

```bash
#!/bin/bash
# .git/hooks/pre-commit

branch=$(git rev-parse --abbrev-ref HEAD)
pattern="^(feature|bugfix|hotfix|release|chore|docs|test|refactor|perf|ci)\/[a-z0-9][a-z0-9-]*$"

if [[ ! $branch =~ $pattern ]]; then
    echo "Branch name '$branch' doesn't follow naming convention"
    echo "Expected pattern: type/description"
    echo "Example: feature/add-user-auth"
    exit 1
fi
```

### GitHub Actions Validation

```yaml
name: Validate Branch Name
on: push

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Check branch name
        run: |
          BRANCH=${GITHUB_REF#refs/heads/}
          if [[ ! "$BRANCH" =~ ^(main|develop|feature|bugfix|hotfix|release|chore)/.*$ ]]; then
            echo "Invalid branch name: $BRANCH"
            exit 1
          fi
```

## Team Guidelines Template

```
┌─────────────────────────────────────────────────────────────────┐
│              Team Branch Naming Guidelines                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Format: <type>/<ticket>-<short-description>                    │
│                                                                  │
│  Required Elements:                                             │
│  □ Type prefix (feature/, bugfix/, etc.)                        │
│  □ Ticket number when applicable (PROJ-123)                     │
│  □ Short description (2-5 words)                                │
│                                                                  │
│  Style Rules:                                                   │
│  □ Lowercase only                                               │
│  □ Hyphens between words                                        │
│  □ No special characters                                        │
│  □ Maximum 50 characters                                        │
│                                                                  │
│  Examples:                                                      │
│  ✅ feature/PROJ-123-user-registration                          │
│  ✅ bugfix/PROJ-456-fix-cart-total                              │
│  ✅ hotfix/PROJ-789-security-patch                              │
│  ❌ Feature/UserRegistration                                    │
│  ❌ my-branch                                                   │
│  ❌ fix_bug                                                     │
│                                                                  │
│  Protected Branches: main, develop, release/*                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Commands

```bash
# Create branch with proper name
git checkout -b feature/JIRA-123-user-auth

# List branches matching pattern
git branch --list "feature/*"
git branch --list "*login*"

# Rename current branch
git branch -m feature/JIRA-123-new-name

# Rename any branch
git branch -m old-name feature/JIRA-123-proper-name

# Delete branches matching pattern
git branch --list "dev/*" | xargs git branch -d

# Find branches by author
git for-each-ref --format='%(refname:short) %(authorname)' refs/heads
```
