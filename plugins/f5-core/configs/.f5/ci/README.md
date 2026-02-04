# F5 CI/CD Integration

## Overview

F5 Framework provides CI/CD integration for automated gate enforcement, ensuring code quality and compliance with Japanese outsource workflow standards (D1-D4, G2-G4).

---

## Quick Start

```bash
# Run gate check locally
.f5/ci/gate-check.sh G2

# Run with strict mode (fail on warnings)
.f5/ci/gate-check.sh G2 --strict

# Run with verbose output
.f5/ci/gate-check.sh G3 --verbose
```

---

## GitHub Actions

### Automatic Gate Checks

The workflow `.github/workflows/f5-gate-check.yml` automatically:

1. **Detects which gate** to check based on branch naming:
   | Branch Pattern | Gate | Mode |
   |----------------|------|------|
   | `feature/*` | G2 | Normal |
   | `release/*` | G4 | Strict |
   | `hotfix/*` | G2 | Strict |
   | Other | G2 | Normal |

2. **Runs all automated checks** for that gate:
   - Lint (ESLint, TSLint, etc.)
   - Type checking (TypeScript)
   - Unit tests
   - Security audit (npm audit)
   - Code coverage

3. **Generates evidence** and uploads as artifacts

4. **Comments on PR** with results

5. **Blocks merge** if gate fails

### Manual Trigger

```bash
# Trigger via GitHub CLI
gh workflow run f5-gate-check.yml -f gate=G3

# Trigger with strict mode
gh workflow run f5-gate-check.yml -f gate=G2 -f strict=true
```

### Workflow Configuration

Located at `.github/workflows/f5-gate-check.yml`:

```yaml
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]
  workflow_dispatch:
    inputs:
      gate:
        type: choice
        options: [D1, D2, D3, D4, G2, G3, G4]
```

---

## Local Scripts

### Gate Check Script

```bash
# Check G2 (Implementation Ready)
.f5/ci/gate-check.sh G2

# Check G3 (Testing Complete)
.f5/ci/gate-check.sh G3

# Check G4 (Deployment Ready)
.f5/ci/gate-check.sh G4

# Design gates
.f5/ci/gate-check.sh D1  # Research Complete
.f5/ci/gate-check.sh D2  # SRS Approved
.f5/ci/gate-check.sh D3  # Basic Design Approved
.f5/ci/gate-check.sh D4  # Detail Design Approved
```

### Script Options

| Option | Description |
|--------|-------------|
| `--strict` | Fail on warnings (exit code 1 instead of 2) |
| `--verbose` | Show detailed output for each check |

---

## Integration with Git Hooks

### Pre-push Hook (Husky)

Add to `.husky/pre-push`:

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

echo "Running F5 Gate G2 check before push..."
.f5/ci/gate-check.sh G2

if [ $? -ne 0 ]; then
    echo "Gate G2 failed. Push aborted."
    exit 1
fi
```

### Pre-commit Hook

Add to `.husky/pre-commit`:

```bash
#!/bin/sh
. "$(dirname "$0")/_/husky.sh"

# Run lint only (quick check)
npm run lint
```

### Setup Husky

```bash
npm install husky --save-dev
npx husky init
```

---

## Evidence Collection

### Automatic Evidence

All CI runs store evidence in:

| Location | Retention | Purpose |
|----------|-----------|---------|
| GitHub Artifacts | 30 days | CI/CD audit trail |
| `.f5/evidence/` | Permanent | Local evidence |

### Evidence Structure

```
.f5/evidence/
├── D1/                     # Research Complete
│   └── D1-check-2024-01-15.md
├── D2/                     # SRS Approved
│   └── D2-check-2024-01-16.md
├── G2/                     # Implementation Ready
│   ├── G2-check-2024-01-17.md
│   └── coverage/
├── G3/                     # Testing Complete
│   ├── G3-check-2024-01-18.md
│   └── test-results/
├── G4/                     # Deployment Ready
│   └── G4-check-2024-01-20.md
└── templates/              # Report templates
```

### Artifact Contents

Each CI run uploads:

```yaml
artifacts:
  - gate-report.md        # Gate check summary
  - lint-output.txt       # Lint results
  - typecheck-output.txt  # Type check results
  - test-results.json     # Test results
  - security-output.json  # npm audit results
  - coverage/             # Coverage reports
```

---

## Configuration

### Thresholds

Configure in `.f5/gates.yaml`:

```yaml
global:
  thresholds:
    code_coverage: 80       # Minimum coverage %
    branch_coverage: 75     # Branch coverage %
    complexity_max: 10      # Max cyclomatic complexity
    duplication_max: 3      # Max code duplication %

gates:
  G2:
    automated_checks:
      lint:
        enabled: true
        required: true
      type_check:
        enabled: true
        required: false  # Warning only
      tests:
        enabled: true
        required: true
      coverage:
        enabled: true
        required: true
        threshold: 80
      security:
        enabled: true
        required: true
        audit_level: high
```

### Environment Variables

Set in GitHub repository settings or `.env`:

```bash
# Coverage threshold override
COVERAGE_THRESHOLD=80
BRANCH_COVERAGE_THRESHOLD=75

# Node version
NODE_VERSION=20

# Skip checks (use with caution)
SKIP_LINT=false
SKIP_TESTS=false
```

---

## Skip Checks

### Commit Message Flags

Skip specific checks with commit message flags:

```bash
# Skip lint check
git commit -m "fix: urgent hotfix [skip-lint]"

# Skip tests
git commit -m "docs: update readme [skip-tests]"

# Skip all CI checks
git commit -m "chore: bump version [skip-ci]"
```

### Per-File Skip

Add to specific files:

```javascript
/* eslint-disable */
// Your code here
/* eslint-enable */
```

```typescript
// @ts-nocheck
// Your code here
```

---

## Branch Protection

### Recommended GitHub Settings

**Main Branch:**
```yaml
main:
  required_status_checks:
    strict: true
    contexts:
      - "F5 Gate Check / Gate Check (G4)"
  required_pull_request_reviews:
    required_approving_review_count: 2
    dismiss_stale_reviews: true
  restrictions:
    users: []
    teams: ["release-managers"]
```

**Develop Branch:**
```yaml
develop:
  required_status_checks:
    strict: true
    contexts:
      - "F5 Gate Check / Gate Check (G2)"
  required_pull_request_reviews:
    required_approving_review_count: 1
```

### Setup via GitHub CLI

```bash
# Enable branch protection for main
gh api repos/{owner}/{repo}/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["F5 Gate Check / Gate Check (G4)"]}'
```

---

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Gate passed | Proceed |
| 1 | Gate failed | Block/Fix required |
| 2 | Passed with warnings | Review warnings |

### Using in Scripts

```bash
.f5/ci/gate-check.sh G2

case $? in
    0)
        echo "All checks passed!"
        ;;
    1)
        echo "Gate failed. Please fix issues."
        exit 1
        ;;
    2)
        echo "Passed with warnings. Review before proceeding."
        ;;
esac
```

---

## Multi-Stack Support

The gate check script auto-detects package manager:

| Package Manager | Detection | Commands |
|-----------------|-----------|----------|
| npm | `package-lock.json` | `npm run lint`, `npm test` |
| yarn | `yarn.lock` | `yarn lint`, `yarn test` |
| pnpm | `pnpm-lock.yaml` | `pnpm lint`, `pnpm test` |
| maven | `pom.xml` | `mvn test`, `mvn verify` |
| gradle | `build.gradle` | `./gradlew test` |
| go | `go.mod` | `go test ./...` |
| pip | `requirements.txt` | `pytest`, `flake8` |

---

## Troubleshooting

### Common Issues

**Gate fails with "No tests found":**
```bash
# Ensure test script exists in package.json
npm run test --if-present
```

**Coverage below threshold:**
```bash
# Check current coverage
npm run test -- --coverage

# View coverage report
open coverage/lcov-report/index.html
```

**Security audit fails:**
```bash
# View vulnerabilities
npm audit

# Fix automatically
npm audit fix

# Force fix (breaking changes)
npm audit fix --force
```

### Debug Mode

```bash
# Run with verbose output
.f5/ci/gate-check.sh G2 --verbose

# Check specific step
npm run lint 2>&1 | tee lint-debug.txt
```

---

## Integration with Other CI Systems

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - gate-check

f5-gate-check:
  stage: gate-check
  script:
    - chmod +x .f5/ci/gate-check.sh
    - .f5/ci/gate-check.sh G2
  artifacts:
    paths:
      - .f5/evidence/
    expire_in: 30 days
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any
    stages {
        stage('F5 Gate Check') {
            steps {
                sh 'chmod +x .f5/ci/gate-check.sh'
                sh '.f5/ci/gate-check.sh G2'
            }
            post {
                always {
                    archiveArtifacts artifacts: '.f5/evidence/**/*', fingerprint: true
                }
            }
        }
    }
}
```

### Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: Bash@3
    inputs:
      targetType: 'inline'
      script: |
        chmod +x .f5/ci/gate-check.sh
        .f5/ci/gate-check.sh G2
    displayName: 'F5 Gate Check'

  - task: PublishBuildArtifacts@1
    inputs:
      PathtoPublish: '.f5/evidence'
      ArtifactName: 'gate-evidence'
```

### CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  gate-check:
    docker:
      - image: cimg/node:20.0
    steps:
      - checkout
      - run:
          name: F5 Gate Check
          command: |
            chmod +x .f5/ci/gate-check.sh
            .f5/ci/gate-check.sh G2
      - store_artifacts:
          path: .f5/evidence

workflows:
  gate-workflow:
    jobs:
      - gate-check
```

---

## See Also

- `.f5/gates.yaml` - Gate configuration
- `.f5/evidence/README.md` - Evidence collection documentation
- `.f5/evidence/templates/` - Report templates
- `/f5-gate` - Gate management slash command
