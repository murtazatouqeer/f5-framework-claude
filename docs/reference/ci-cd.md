# CI/CD Setup Guide

This document describes the CI/CD setup for F5 Framework CLI testing.

## Overview

The testing pipeline includes:
- **GitHub Actions** - Automated testing on push/PR
- **Husky Hooks** - Local pre-commit and pre-push validation
- **Coverage Reports** - Automatic coverage tracking and reporting

## GitHub Actions Workflow

### Workflow File
Location: `.github/workflows/test.yml`

### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches
- Only when changes in `packages/cli/**`

### Jobs

#### 1. Run Tests
- Installs dependencies
- Runs linter (non-blocking)
- Runs tests with coverage
- Generates coverage summary
- Checks coverage thresholds
- Uploads artifacts
- Comments coverage on PRs

#### 2. Quality Gate Check
- Downloads coverage summary
- Adds summary to GitHub workflow summary

## Branch Protection Rules

To enforce quality gates, configure branch protection for `main` and `develop`:

### Settings > Branches > Add Rule

1. **Branch name pattern:** `main` (repeat for `develop`)

2. **Protect matching branches:**
   - Require a pull request before merging
   - Require status checks to pass before merging
     - Search and select: `Run Tests`
     - Search and select: `Quality Gate Check`
   - Require branches to be up to date before merging
   - Require conversation resolution before merging

3. **Rules applied to everyone including administrators:**
   - Do not allow bypassing the above settings

## Coverage Thresholds

Current thresholds (adjustable in workflow and scripts):

| Metric | Threshold | Target |
|--------|-----------|--------|
| Statements | 25% | 80% |
| Branches | 50% | 75% |
| Functions | 60% | 80% |

**Note**: Thresholds are set conservatively based on current coverage levels. Increase as coverage improves.

## Local Development

### Pre-commit Hook
- Runs `npm test` before each commit
- Blocks commit if tests fail

### Pre-push Hook
- Runs `npm run test:coverage` before push
- Checks coverage threshold (25%)
- Blocks push if below threshold

### Setup Husky Hooks

Husky v9 is configured automatically via the `prepare` script:

```bash
# Install dependencies (runs prepare automatically)
pnpm install

# Hooks are located at repo root
ls -la .husky/
```

For Husky v9, hooks are simple shell scripts without the shebang header.

### Manual CI Test

```bash
cd packages/cli

# Run full CI test locally
node scripts/ci-test.mjs

# Or use npm script
npm run test:ci
```

## Artifacts

CI generates these artifacts (retained 30 days):

| Artifact | Description |
|----------|-------------|
| `coverage-report/` | Full HTML coverage report |
| `coverage-summary.md` | Markdown summary |
| `ci-results.json` | Machine-readable results |

## PR Coverage Comments

Every PR automatically receives a coverage comment showing:
- Overall coverage percentages
- Module breakdown
- Comparison with thresholds
- Status (pass/fail)

## Scripts

| Script | Description |
|--------|-------------|
| `npm run test` | Run tests |
| `npm run test:coverage` | Run tests with coverage |
| `npm run test:summary` | Generate coverage summary |
| `npm run test:report` | Coverage + summary |
| `npm run test:ci` | Full CI test |
| `npm run test:dashboard` | Show test dashboard |

## Troubleshooting

### Tests fail locally but pass in CI
- Check Node.js version (should be v20)
- Clear node_modules and reinstall: `rm -rf node_modules && npm ci`

### Coverage report not generated
- Ensure `.f5/testing/reports/coverage/` directory exists
- Run `npm run test:coverage` first

### Husky hooks not running
- Verify `.husky/` directory exists at repo root
- Run `pnpm install` to reinitialize (Husky v9)
- Check file permissions: `chmod +x .husky/*`
- For Husky v9, hooks don't need shebang headers

### PR comment not appearing
- Verify GitHub Actions has write permissions
- Check workflow logs for errors

## Configuration Files

| File | Purpose |
|------|---------|
| `.github/workflows/test.yml` | GitHub Actions workflow |
| `.husky/pre-commit` | Pre-commit hook (repo root) |
| `.husky/pre-push` | Pre-push hook (repo root) |
| `packages/cli/scripts/ci-test.mjs` | CI test runner |
| `packages/cli/scripts/coverage-summary.mjs` | Coverage report generator |
| `packages/cli/vitest.config.ts` | Vitest configuration |

## Updating Thresholds

To adjust coverage thresholds:

1. **GitHub Actions**: Edit `.github/workflows/test.yml`
   ```javascript
   const MIN_STATEMENTS = 25;  // Change this
   const MIN_BRANCHES = 50;
   const MIN_FUNCTIONS = 60;
   ```

2. **CI Test Script**: Edit `packages/cli/scripts/ci-test.mjs`
   ```javascript
   const thresholds = {
     statements: 25,  // Change this
     branches: 50,
     functions: 60
   };
   ```

3. **Pre-push Hook**: Edit `.husky/pre-push`
   ```bash
   MIN_COVERAGE=25  # Change this
   ```

## Best Practices

1. **Run tests before pushing**: Use pre-push hook or `npm run test:ci`
2. **Review coverage reports**: Check PR comments for coverage changes
3. **Increase thresholds gradually**: As coverage improves, raise thresholds
4. **Fix failing tests promptly**: Don't let failing tests accumulate
5. **Write tests for new code**: Maintain or improve coverage ratio

---

*Last updated: December 2024*
