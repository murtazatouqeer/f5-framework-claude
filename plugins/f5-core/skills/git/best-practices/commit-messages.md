---
name: commit-messages
description: Writing clear, meaningful commit messages
category: git/best-practices
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Commit Messages

## Overview

Good commit messages are essential for maintaining a readable project history.
They help team members understand changes, make debugging easier, and provide
context for code reviews and future maintenance.

## Anatomy of a Good Commit Message

```
┌─────────────────────────────────────────────────────────────────┐
│                 Commit Message Structure                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  <type>(<scope>): <subject>                                     │
│                                                                  │
│  <body>                                                         │
│                                                                  │
│  <footer>                                                       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  Example:                                                       │
│                                                                  │
│  feat(auth): add password reset functionality                   │
│                                                                  │
│  Implement password reset flow with email verification.         │
│  Users can request a reset link that expires in 24 hours.       │
│                                                                  │
│  - Add reset request endpoint                                   │
│  - Add token generation and validation                          │
│  - Add email service integration                                │
│                                                                  │
│  Closes #123                                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Conventional Commits

### Standard Types

```
┌──────────┬────────────────────────────────────────────────────┐
│ Type     │ Description                                        │
├──────────┼────────────────────────────────────────────────────┤
│ feat     │ New feature for the user                           │
│ fix      │ Bug fix for the user                               │
│ docs     │ Documentation only changes                         │
│ style    │ Formatting, missing semi colons, etc.              │
│ refactor │ Code change that neither fixes a bug nor adds a    │
│          │ feature                                            │
│ perf     │ Performance improvement                            │
│ test     │ Adding missing tests or correcting existing tests  │
│ build    │ Changes to build system or dependencies            │
│ ci       │ CI configuration files and scripts                 │
│ chore    │ Other changes that don't modify src or test files  │
│ revert   │ Reverts a previous commit                          │
└──────────┴────────────────────────────────────────────────────┘
```

### Examples

```bash
# Feature
feat(shopping-cart): add quantity selector

# Bug fix
fix(auth): prevent session timeout on active users

# Documentation
docs(readme): add installation instructions

# Styling
style(ui): format code with prettier

# Refactoring
refactor(api): extract validation logic to separate module

# Performance
perf(database): add index for user lookup queries

# Tests
test(auth): add integration tests for login flow

# Build
build(deps): upgrade webpack to v5

# CI
ci(github): add automated testing workflow

# Chore
chore(deps): update development dependencies

# Revert
revert: revert "feat(cart): add quantity selector"
```

## The Seven Rules

```
┌─────────────────────────────────────────────────────────────────┐
│           Seven Rules of Great Commit Messages                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Separate subject from body with a blank line                │
│                                                                  │
│  2. Limit the subject line to 50 characters                     │
│                                                                  │
│  3. Capitalize the subject line                                 │
│                                                                  │
│  4. Do not end the subject line with a period                   │
│                                                                  │
│  5. Use the imperative mood in the subject line                 │
│     ✅ "Add feature" NOT ❌ "Added feature"                     │
│     ✅ "Fix bug" NOT ❌ "Fixes bug"                             │
│                                                                  │
│  6. Wrap the body at 72 characters                              │
│                                                                  │
│  7. Use the body to explain what and why vs. how                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Subject Line Guidelines

### Good Subject Lines

```bash
# Clear and concise
Add user authentication with JWT
Fix memory leak in connection pool
Update dependencies for security patch
Remove deprecated API endpoints
Refactor database layer for better testability
```

### Bad Subject Lines

```bash
# Too vague
Fixed stuff
Updates
WIP
Misc changes

# Too long
Add a new feature that allows users to reset their password using email verification with a secure token

# Not imperative
Added user authentication
Fixes the bug
Adding tests

# Ends with period
Add user authentication.
```

## Body Guidelines

### When to Include a Body

```bash
# Simple change - subject only
git commit -m "Fix typo in README"

# Complex change - include body
git commit -m "Refactor authentication system

Replace session-based auth with JWT tokens to support
stateless authentication across multiple services.

The new system provides:
- Better scalability (no session storage)
- Cross-service authentication
- Reduced server memory usage

Migration steps are documented in docs/auth-migration.md"
```

### Body Format

```bash
# Use bullet points for multiple changes
Implement password reset functionality

- Add reset request endpoint (/api/auth/reset)
- Create token generation service
- Add email template for reset links
- Add token validation and expiry logic

# Explain the reasoning
Fix race condition in order processing

Orders were occasionally being processed twice when users
double-clicked the submit button. This adds a debounce
mechanism and server-side idempotency check.

The issue affected approximately 0.1% of orders.
```

## Footer Guidelines

### Issue References

```bash
# Close issues
Closes #123
Fixes #456
Resolves #789

# Reference without closing
Refs #123
See #456
Related to #789
```

### Breaking Changes

```bash
# Mark breaking changes
feat(api): change response format for user endpoint

BREAKING CHANGE: The user endpoint now returns a nested
object structure. Clients need to update their parsers.

Before: { name: "John", email: "john@example.com" }
After: { user: { name: "John", email: "john@example.com" } }

# With conventional commits
feat(api)!: change response format for user endpoint

The ! indicates a breaking change
```

### Co-authors

```bash
# Add co-authors
feat: implement new dashboard

Co-authored-by: Jane Doe <jane@example.com>
Co-authored-by: John Smith <john@example.com>
```

## Commit Message Templates

### Git Template Configuration

```bash
# Create template file
cat > ~/.gitmessage << 'EOF'
# <type>(<scope>): <subject>
# |<----  Using a Maximum Of 50 Characters  ---->|

# Explain why this change is being made
# |<----   Try To Limit Each Line to a Maximum Of 72 Characters   ---->|

# Provide links or keys to any relevant tickets, articles or other resources
# Example: Closes #23

# --- COMMIT END ---
# Type can be:
#   feat     (new feature)
#   fix      (bug fix)
#   refactor (refactoring code)
#   style    (formatting, missing semi colons, etc)
#   docs     (changes to documentation)
#   test     (adding or refactoring tests)
#   chore    (updating build tasks etc)
# --------------------
EOF

# Set as default template
git config --global commit.template ~/.gitmessage
```

### Project-Specific Template

```bash
# .gitmessage in project root
# <type>(<scope>): <subject>

# What changes were made and why?

# Related issues:
# Closes #

# Breaking changes:

# Set for project
git config commit.template .gitmessage
```

## Writing Tips

### Imperative Mood

```bash
# Think: "If applied, this commit will..."
# ✅ If applied, this commit will Add user authentication
# ✅ If applied, this commit will Fix login redirect bug
# ❌ If applied, this commit will Added user authentication
# ❌ If applied, this commit will Fixing login redirect bug

# Good (imperative)
Add feature
Fix bug
Update documentation
Remove deprecated method

# Bad (not imperative)
Added feature
Fixes bug
Updated documentation
Removing deprecated method
```

### Be Specific

```bash
# Vague (bad)
Fix bug
Update code
Changes

# Specific (good)
Fix null pointer exception in user validation
Update webpack config for production builds
Add input sanitization for search queries
```

### Atomic Commits

```bash
# Each commit should do ONE thing
# Bad: One big commit
git commit -m "Add auth, fix bugs, update deps"

# Good: Separate commits
git commit -m "Add JWT authentication"
git commit -m "Fix session timeout bug"
git commit -m "Update security dependencies"
```

## Common Patterns

### Feature Development

```bash
feat(user): add profile editing functionality

Allow users to edit their profile information including
name, email, and avatar.

- Add profile edit form component
- Add profile update API endpoint
- Add image upload handling
- Add validation for email changes

Closes #234
```

### Bug Fixes

```bash
fix(checkout): resolve payment processing race condition

Payments were occasionally failing when users rapidly
clicked the submit button. Added debounce and server-side
idempotency key to prevent duplicate charges.

Affected approximately 0.5% of checkout attempts.

Fixes #456
```

### Refactoring

```bash
refactor(database): migrate from callbacks to async/await

Convert all database operations to use async/await syntax
for improved readability and error handling.

This change has no functional impact but improves:
- Code readability
- Error stack traces
- Future maintenance

No breaking changes.
```

### Reverts

```bash
revert: feat(cart): add quantity selector

This reverts commit abc123def456.

The quantity selector caused issues with inventory
tracking. Reverting until the underlying issue is fixed.

Refs #567
```

## Team Standards

```
┌─────────────────────────────────────────────────────────────────┐
│            Team Commit Message Standards                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Required:                                                      │
│  □ Use conventional commit format                               │
│  □ Subject line ≤ 50 characters                                 │
│  □ Use imperative mood                                          │
│  □ Reference issue numbers                                      │
│                                                                  │
│  Recommended:                                                   │
│  □ Include body for complex changes                             │
│  □ Explain why, not just what                                   │
│  □ Mark breaking changes clearly                                │
│                                                                  │
│  Avoid:                                                         │
│  □ Vague messages ("fix", "update", "changes")                  │
│  □ WIP commits on main branch                                   │
│  □ Combining unrelated changes                                  │
│  □ Past tense ("fixed", "added")                                │
│                                                                  │
│  Enforcement:                                                   │
│  □ Use commitlint for validation                                │
│  □ Configure commit-msg hook                                    │
│  □ Review commits in PR                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Automation

### Commitlint

```bash
# Install commitlint
npm install --save-dev @commitlint/cli @commitlint/config-conventional

# Create config
echo "module.exports = {extends: ['@commitlint/config-conventional']}" > commitlint.config.js

# Add husky hook
npx husky add .husky/commit-msg 'npx --no -- commitlint --edit "$1"'
```

### Commitizen

```bash
# Install commitizen
npm install --save-dev commitizen cz-conventional-changelog

# Configure package.json
{
  "config": {
    "commitizen": {
      "path": "cz-conventional-changelog"
    }
  }
}

# Use instead of git commit
npx cz
# Interactive prompts guide you through commit message
```

## Useful Commands

```bash
# Commit with message
git commit -m "feat: add new feature"

# Commit with subject and body
git commit -m "feat: add feature" -m "Detailed description here"

# Open editor for message
git commit

# Amend last commit message
git commit --amend

# Edit message only (no changes)
git commit --amend --no-edit

# View commit messages
git log --oneline
git log --format="%h %s"
git log --format=full
```
