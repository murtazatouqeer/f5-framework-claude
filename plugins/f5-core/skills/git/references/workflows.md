# Git Workflows Reference

## GitHub Flow

Simple workflow for continuous deployment.

```
main ─────●─────●─────●─────●─────●───────
           \         /
feature     ●───●───●
```

### Process

1. Create feature branch from main
2. Make changes and commit
3. Open Pull Request
4. Review and discuss
5. Deploy from feature branch (optional)
6. Merge to main
7. Delete feature branch

```bash
# Start feature
git checkout main
git pull
git checkout -b feature/user-auth

# Work on feature
git add .
git commit -m "feat: add user authentication"

# Push and create PR
git push -u origin feature/user-auth
# Create PR on GitHub

# After merge
git checkout main
git pull
git branch -d feature/user-auth
```

## GitFlow

Structured workflow for scheduled releases.

```
main      ────●─────────────────●─────────
              │                 │
release       │     ●───●───●───┤
              │    /            │
develop ──●───●───●───●───●─────●───●─────
           \     /     \       /
feature     ●───●       ●─────●
```

### Branches

| Branch | Purpose |
|--------|---------|
| main | Production releases |
| develop | Integration branch |
| feature/* | New features |
| release/* | Release preparation |
| hotfix/* | Production fixes |

### Commands

```bash
# Start feature
git checkout develop
git checkout -b feature/new-feature

# Finish feature
git checkout develop
git merge --no-ff feature/new-feature
git branch -d feature/new-feature

# Start release
git checkout develop
git checkout -b release/1.0.0

# Finish release
git checkout main
git merge --no-ff release/1.0.0
git tag -a v1.0.0 -m "Release 1.0.0"
git checkout develop
git merge --no-ff release/1.0.0
git branch -d release/1.0.0

# Start hotfix
git checkout main
git checkout -b hotfix/fix-bug

# Finish hotfix
git checkout main
git merge --no-ff hotfix/fix-bug
git tag -a v1.0.1 -m "Hotfix 1.0.1"
git checkout develop
git merge --no-ff hotfix/fix-bug
git branch -d hotfix/fix-bug
```

## Trunk-Based Development

Minimal branching, continuous integration.

```
main ─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●─●───
       \   /     \   /
short   ●─●       ●─●
```

### Principles

- Main branch is always deployable
- Short-lived feature branches (< 2 days)
- Feature flags for incomplete features
- Frequent commits to main

```bash
# Start work (small change)
git checkout main
git pull
git checkout -b feature/small-change

# Complete same day
git add .
git commit -m "feat: add small change"
git push
# Create PR, get quick review, merge

# For larger changes, use feature flags
if (featureFlags.newFeature) {
  // New code
} else {
  // Existing code
}
```

## Forking Workflow

For open source contributions.

```bash
# Fork on GitHub, then clone
git clone git@github.com:youruser/repo.git
cd repo

# Add upstream remote
git remote add upstream https://github.com/original/repo.git

# Keep fork updated
git fetch upstream
git checkout main
git merge upstream/main
git push origin main

# Create feature branch
git checkout -b feature/fix-bug

# Push to your fork
git push origin feature/fix-bug

# Create PR to original repo
```

## Branch Naming Conventions

```
feature/user-authentication
feature/JIRA-123-add-login
bugfix/login-error
hotfix/security-patch
release/v1.0.0
docs/update-readme
refactor/clean-auth-module
test/add-unit-tests
```

## Commit Message Format

### Conventional Commits

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

| Type | Description |
|------|-------------|
| feat | New feature |
| fix | Bug fix |
| docs | Documentation |
| style | Formatting |
| refactor | Code restructuring |
| perf | Performance |
| test | Tests |
| build | Build system |
| ci | CI configuration |
| chore | Maintenance |
| revert | Revert commit |

### Examples

```
feat(auth): add OAuth2 login

Implement OAuth2 authentication with Google and GitHub providers.

- Add OAuth2 strategy configuration
- Create callback handlers
- Update user model for OAuth data

Closes #123

---

fix(api): handle null response from payment provider

The payment provider occasionally returns null instead of an error object.
Added null check and appropriate error handling.

Fixes #456

---

docs: update API documentation

- Add examples for new endpoints
- Fix typos in authentication section
```

## Pull Request Template

```markdown
## Description
[Describe your changes]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings

## Related Issues
Closes #123
```
