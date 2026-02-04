---
name: git-hooks
description: Automating workflows with Git hooks
category: git/best-practices
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Git Hooks

## Overview

Git hooks are scripts that run automatically at key points in Git workflow.
They enable automation of code quality checks, commit message validation,
and deployment processes.

## Hook Types and Timing

```
┌─────────────────────────────────────────────────────────────────┐
│                    Git Hooks Overview                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Client-Side Hooks (local machine):                             │
│                                                                  │
│  Commit Workflow:                                               │
│  pre-commit ─▶ prepare-commit-msg ─▶ commit-msg ─▶ post-commit  │
│                                                                  │
│  Email Workflow:                                                │
│  applypatch-msg ─▶ pre-applypatch ─▶ post-applypatch            │
│                                                                  │
│  Other:                                                         │
│  pre-rebase, post-checkout, post-merge, pre-push               │
│                                                                  │
│  Server-Side Hooks (remote repository):                         │
│  pre-receive ─▶ update ─▶ post-receive                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Client-Side Hooks

### pre-commit

```bash
#!/bin/bash
# .git/hooks/pre-commit
# Runs before commit is created
# Exit non-zero to abort commit

# Run linter
echo "Running ESLint..."
npm run lint
if [ $? -ne 0 ]; then
    echo "ESLint failed. Please fix errors before committing."
    exit 1
fi

# Run tests
echo "Running tests..."
npm test
if [ $? -ne 0 ]; then
    echo "Tests failed. Please fix before committing."
    exit 1
fi

# Check for debug statements
if grep -r "console.log" src/ --include="*.ts"; then
    echo "Warning: console.log found in source files"
    # exit 1  # Uncomment to block commit
fi

# Check for merge conflict markers
if grep -rn "<<<<<<" .; then
    echo "Merge conflict markers found!"
    exit 1
fi

exit 0
```

### commit-msg

```bash
#!/bin/bash
# .git/hooks/commit-msg
# Validates commit message format
# $1 contains path to commit message file

COMMIT_MSG_FILE=$1
COMMIT_MSG=$(cat "$COMMIT_MSG_FILE")

# Conventional commit pattern
PATTERN="^(feat|fix|docs|style|refactor|perf|test|chore|build|ci|revert)(\([a-z-]+\))?: .{1,72}$"

if ! echo "$COMMIT_MSG" | head -1 | grep -qE "$PATTERN"; then
    echo "ERROR: Commit message doesn't follow Conventional Commits format"
    echo ""
    echo "Format: <type>(<scope>): <description>"
    echo ""
    echo "Types: feat, fix, docs, style, refactor, perf, test, chore, build, ci, revert"
    echo ""
    echo "Example: feat(auth): add password reset functionality"
    exit 1
fi

# Check subject line length
SUBJECT_LENGTH=$(echo "$COMMIT_MSG" | head -1 | wc -c)
if [ "$SUBJECT_LENGTH" -gt 72 ]; then
    echo "ERROR: Subject line is too long ($SUBJECT_LENGTH > 72 characters)"
    exit 1
fi

exit 0
```

### prepare-commit-msg

```bash
#!/bin/bash
# .git/hooks/prepare-commit-msg
# Modify commit message before editor opens
# $1: path to commit message file
# $2: source (message, template, merge, squash, commit)
# $3: commit SHA (if amending)

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Add branch name to commit message
if [ -z "$COMMIT_SOURCE" ]; then
    BRANCH=$(git rev-parse --abbrev-ref HEAD)

    # Extract ticket number from branch (e.g., feature/JIRA-123-description)
    TICKET=$(echo "$BRANCH" | grep -oE '[A-Z]+-[0-9]+' || true)

    if [ -n "$TICKET" ]; then
        # Prepend ticket to message
        sed -i.bak -e "1s/^/[$TICKET] /" "$COMMIT_MSG_FILE"
    fi
fi
```

### pre-push

```bash
#!/bin/bash
# .git/hooks/pre-push
# Runs before push to remote
# Exit non-zero to abort push

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Prevent push to main/master
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
    echo "Direct push to $BRANCH is not allowed!"
    echo "Please create a pull request instead."
    exit 1
fi

# Run full test suite before push
echo "Running full test suite before push..."
npm run test:all
if [ $? -ne 0 ]; then
    echo "Tests failed. Push aborted."
    exit 1
fi

exit 0
```

### post-commit

```bash
#!/bin/bash
# .git/hooks/post-commit
# Runs after commit is created
# Cannot abort commit (already done)

# Display commit info
echo "Commit created: $(git log -1 --format='%h %s')"

# Notify team (optional)
# curl -X POST -d "New commit by $USER" https://slack-webhook-url
```

### post-checkout

```bash
#!/bin/bash
# .git/hooks/post-checkout
# Runs after checkout
# $1: previous HEAD, $2: new HEAD, $3: 1=branch checkout, 0=file checkout

PREV_HEAD=$1
NEW_HEAD=$2
IS_BRANCH=$3

# Only run for branch checkouts
if [ "$IS_BRANCH" = "1" ]; then
    # Check if dependencies changed
    if ! git diff --quiet "$PREV_HEAD" "$NEW_HEAD" -- package.json package-lock.json; then
        echo "Dependencies changed. Running npm install..."
        npm install
    fi

    # Check if migrations exist
    if ! git diff --quiet "$PREV_HEAD" "$NEW_HEAD" -- migrations/; then
        echo "New migrations detected. Consider running migrations."
    fi
fi
```

### post-merge

```bash
#!/bin/bash
# .git/hooks/post-merge
# Runs after merge
# $1: 1 if squash merge, 0 otherwise

# Check if dependencies changed
CHANGED_FILES=$(git diff-tree -r --name-only --no-commit-id ORIG_HEAD HEAD)

if echo "$CHANGED_FILES" | grep -qE "package\.json|package-lock\.json"; then
    echo "Dependencies changed. Running npm install..."
    npm install
fi

if echo "$CHANGED_FILES" | grep -qE "requirements\.txt|Pipfile"; then
    echo "Python dependencies changed. Running pip install..."
    pip install -r requirements.txt
fi
```

## Hook Installation

### Manual Installation

```bash
# Hooks are stored in .git/hooks/
ls .git/hooks/

# Sample hooks exist with .sample extension
ls .git/hooks/*.sample

# To activate, remove .sample and make executable
cp .git/hooks/pre-commit.sample .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Or create new hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
npm run lint
EOF
chmod +x .git/hooks/pre-commit
```

### Using Husky (Node.js)

```bash
# Install husky
npm install husky --save-dev

# Enable Git hooks
npx husky install

# Add to package.json scripts (runs after npm install)
npm pkg set scripts.prepare="husky install"

# Create pre-commit hook
npx husky add .husky/pre-commit "npm run lint"

# Create commit-msg hook
npx husky add .husky/commit-msg 'npx --no -- commitlint --edit "$1"'
```

### Using pre-commit (Python)

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### Using lefthook (Go)

```yaml
# lefthook.yml
pre-commit:
  parallel: true
  commands:
    lint:
      run: npm run lint
    test:
      run: npm test

commit-msg:
  commands:
    validate:
      run: npx commitlint --edit {1}
```

```bash
# Install lefthook
npm install lefthook --save-dev

# Install hooks
npx lefthook install
```

## Sharing Hooks with Team

### Git Hooks Directory

```bash
# Create hooks directory in repo
mkdir -p .githooks

# Add hooks
cp .git/hooks/pre-commit .githooks/

# Configure git to use this directory
git config core.hooksPath .githooks

# Add to repo
git add .githooks
git commit -m "Add git hooks"

# Team members set hooks path after clone
git config core.hooksPath .githooks
```

### Make Hooks Executable

```bash
# In .githooks/pre-commit
#!/bin/bash
# Make sure all hooks are executable
chmod +x .githooks/*

# Then run the actual checks
npm run lint
```

## Server-Side Hooks

### pre-receive

```bash
#!/bin/bash
# Runs once before any refs are updated
# Receives oldrev, newrev, refname on stdin

while read oldrev newrev refname; do
    # Prevent force push to protected branches
    if [[ "$refname" == "refs/heads/main" ]]; then
        # Check if this is a force push
        if [ "$oldrev" != "0000000000000000000000000000000000000000" ]; then
            if ! git merge-base --is-ancestor "$oldrev" "$newrev"; then
                echo "Force push to main is not allowed!"
                exit 1
            fi
        fi
    fi
done

exit 0
```

### update

```bash
#!/bin/bash
# Runs once per branch being updated
# $1: refname, $2: oldrev, $3: newrev

REFNAME=$1
OLDREV=$2
NEWREV=$3

# Block updates to protected tags
if [[ "$REFNAME" == refs/tags/v* ]]; then
    if [ "$OLDREV" != "0000000000000000000000000000000000000000" ]; then
        echo "Cannot update existing version tags!"
        exit 1
    fi
fi

exit 0
```

### post-receive

```bash
#!/bin/bash
# Runs after all refs are updated
# Good for deployment, notifications

while read oldrev newrev refname; do
    if [[ "$refname" == "refs/heads/main" ]]; then
        echo "Main branch updated. Triggering deployment..."
        # /path/to/deploy.sh

        # Send notification
        # curl -X POST https://slack-webhook-url -d '{"text":"Deployed to production"}'
    fi
done
```

## Practical Hook Examples

### Lint-Staged (Only Changed Files)

```json
// package.json
{
  "lint-staged": {
    "*.{js,ts}": ["eslint --fix", "prettier --write"],
    "*.{css,scss}": ["stylelint --fix"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

```bash
# .husky/pre-commit
#!/bin/bash
npx lint-staged
```

### Prevent Large Files

```bash
#!/bin/bash
# .git/hooks/pre-commit

MAX_SIZE=5242880  # 5MB in bytes

for file in $(git diff --cached --name-only); do
    if [ -f "$file" ]; then
        size=$(wc -c < "$file")
        if [ "$size" -gt "$MAX_SIZE" ]; then
            echo "Error: $file is larger than 5MB"
            exit 1
        fi
    fi
done
```

### Check for Secrets

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Patterns that might indicate secrets
PATTERNS=(
    "api[_-]?key"
    "secret[_-]?key"
    "password"
    "aws[_-]?access"
    "private[_-]?key"
)

for pattern in "${PATTERNS[@]}"; do
    if git diff --cached --diff-filter=d | grep -iE "$pattern"; then
        echo "Warning: Possible secret detected matching '$pattern'"
        echo "Please review the changes before committing."
        # exit 1  # Uncomment to block
    fi
done
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Git Hooks Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Performance:                                                   │
│  • Keep hooks fast (< 5 seconds)                                │
│  • Run full test suites in pre-push, not pre-commit             │
│  • Use lint-staged to check only changed files                  │
│                                                                  │
│  Reliability:                                                   │
│  • Make hooks idempotent                                        │
│  • Handle errors gracefully                                     │
│  • Provide helpful error messages                               │
│  • Test hooks before sharing                                    │
│                                                                  │
│  Team:                                                          │
│  • Use hook managers (Husky, pre-commit)                        │
│  • Document how to install hooks                                │
│  • Keep hooks in version control                                │
│  • Allow bypassing for emergencies (--no-verify)                │
│                                                                  │
│  Security:                                                      │
│  • Don't run arbitrary commands from repo                       │
│  • Review hooks from external sources                           │
│  • Be careful with post-checkout hooks                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Bypassing Hooks

```bash
# Skip all hooks for a commit
git commit --no-verify -m "Emergency fix"
# Or
git commit -n -m "Emergency fix"

# Skip hooks for push
git push --no-verify

# Skip specific hook (by handling in hook)
SKIP_TESTS=1 git commit -m "WIP"
# Hook should check: if [ -n "$SKIP_TESTS" ]; then exit 0; fi
```

## Useful Commands Reference

```bash
# List available hooks
ls .git/hooks/*.sample

# View hook content
cat .git/hooks/pre-commit

# Make hook executable
chmod +x .git/hooks/pre-commit

# Set hooks directory
git config core.hooksPath .githooks

# Skip hooks
git commit --no-verify
git push --no-verify

# Debug hooks
GIT_TRACE=1 git commit -m "test"
```
