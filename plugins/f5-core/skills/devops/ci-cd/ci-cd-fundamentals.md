---
name: ci-cd-fundamentals
description: CI/CD pipeline fundamentals and best practices
category: devops/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CI/CD Fundamentals

## Overview

Continuous Integration (CI) and Continuous Delivery/Deployment (CD) are practices
that enable teams to deliver code changes frequently and reliably.

## CI/CD Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI/CD Pipeline Flow                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────┐   ┌───────┐   ┌──────┐   ┌──────┐   ┌────────┐     │
│  │ Source │ → │ Build │ → │ Test │ → │ Stage│ → │ Deploy │     │
│  └────────┘   └───────┘   └──────┘   └──────┘   └────────┘     │
│      │            │           │          │           │          │
│      ▼            ▼           ▼          ▼           ▼          │
│  • Commit     • Compile   • Unit     • Deploy   • Production   │
│  • PR         • Lint      • Integ    • E2E      • Monitor      │
│  • Webhook    • Package   • Security • Smoke    • Rollback     │
│                                                                  │
│  ├──────────────── CI ───────────────┤├───────── CD ──────────┤│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Continuous Integration

### Key Principles

1. **Maintain a Single Source Repository**
   - All code in version control
   - Feature branches for development
   - Protected main branch

2. **Automate the Build**
   - Every commit triggers build
   - Fast feedback loop
   - Reproducible builds

3. **Make the Build Self-Testing**
   - Run tests on every build
   - Fail fast on errors
   - Coverage requirements

4. **Everyone Commits Daily**
   - Small, frequent changes
   - Reduce merge conflicts
   - Continuous integration

### CI Pipeline Example

```yaml
# Basic CI Pipeline Structure
stages:
  - validate
  - build
  - test
  - analyze

validate:
  stage: validate
  script:
    - npm run lint
    - npm run type-check
    - npm run format:check

build:
  stage: build
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/

test:
  stage: test
  script:
    - npm run test:unit
    - npm run test:integration
  coverage: '/Coverage: \d+.\d+%/'

analyze:
  stage: analyze
  script:
    - npm audit
    - npm run security:scan
```

## Continuous Delivery vs Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Continuous Delivery                                             │
│  ────────────────────                                            │
│  Code → Build → Test → Stage → [Manual Approval] → Production   │
│                                       ↑                          │
│                               Human decision                     │
│                                                                  │
│  Continuous Deployment                                           │
│  ─────────────────────                                           │
│  Code → Build → Test → Stage → [Automated] → Production         │
│                                     ↑                            │
│                             No human intervention                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline Best Practices

### 1. Fast Feedback

```yaml
# Parallel execution for faster feedback
stages:
  - quick-checks    # < 2 minutes
  - build           # < 5 minutes
  - test            # < 10 minutes
  - deploy          # < 5 minutes

quick-checks:
  parallel:
    - lint
    - type-check
    - security-scan
```

### 2. Fail Fast

```yaml
# Run fastest tests first
test:
  stage: test
  script:
    # Quick unit tests first
    - npm run test:unit --bail
    # Then slower integration tests
    - npm run test:integration --bail
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### 3. Artifact Management

```yaml
build:
  stage: build
  script:
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
```

### 4. Environment Promotion

```yaml
# Progressive environment promotion
deploy-dev:
  stage: deploy
  environment:
    name: development
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

deploy-staging:
  stage: deploy
  environment:
    name: staging
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy-production:
  stage: deploy
  environment:
    name: production
  rules:
    - if: $CI_COMMIT_TAG
  when: manual
```

## Quality Gates

### Gate Types

```typescript
interface QualityGate {
  name: string;
  criteria: GateCriteria[];
  blocking: boolean;
}

interface GateCriteria {
  metric: string;
  operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  threshold: number;
}

const qualityGates: QualityGate[] = [
  {
    name: 'Code Quality',
    blocking: true,
    criteria: [
      { metric: 'test_coverage', operator: 'gte', threshold: 80 },
      { metric: 'lint_errors', operator: 'eq', threshold: 0 },
      { metric: 'type_errors', operator: 'eq', threshold: 0 },
    ],
  },
  {
    name: 'Security',
    blocking: true,
    criteria: [
      { metric: 'critical_vulnerabilities', operator: 'eq', threshold: 0 },
      { metric: 'high_vulnerabilities', operator: 'lte', threshold: 5 },
    ],
  },
  {
    name: 'Performance',
    blocking: false,
    criteria: [
      { metric: 'bundle_size_kb', operator: 'lte', threshold: 500 },
      { metric: 'lighthouse_score', operator: 'gte', threshold: 90 },
    ],
  },
];
```

### Implementation

```yaml
quality-gate:
  stage: quality
  script:
    - |
      # Check test coverage
      COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
      if [ $(echo "$COVERAGE < 80" | bc) -eq 1 ]; then
        echo "Coverage ${COVERAGE}% is below 80% threshold"
        exit 1
      fi

      # Check for vulnerabilities
      VULNS=$(npm audit --json | jq '.metadata.vulnerabilities.critical')
      if [ "$VULNS" -gt 0 ]; then
        echo "Found ${VULNS} critical vulnerabilities"
        exit 1
      fi
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Branch Strategy

### GitFlow

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitFlow Model                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  main ─────●─────────────────────●─────────────────●─── (tags)  │
│            ↑                     ↑                 ↑             │
│  release ──┴──●───────●──────────┴─────────────────┤             │
│               ↑       ↑                            │             │
│  develop ─●───┴───●───┴───●───●───●───●───●───●────┤             │
│           ↑       ↑       ↑   ↑   ↑               │             │
│  feature ─┴───────┴───────┴───┴───┴────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Trunk-Based Development

```
┌─────────────────────────────────────────────────────────────────┐
│                  Trunk-Based Development                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  main ────●───●───●───●───●───●───●───●───●───●───●──── (tags)  │
│           ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑   ↑             │
│  feature ─┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘             │
│           │   │   │   │   │   │   │   │   │   │                 │
│          (short-lived branches, < 1 day)                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Pipeline Triggers

```yaml
# Webhook triggers
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Nightly builds
  workflow_dispatch:      # Manual trigger
    inputs:
      environment:
        description: 'Deployment environment'
        required: true
        default: 'staging'
```

## Secrets Management

```yaml
# Using secrets in pipelines
deploy:
  stage: deploy
  script:
    - echo "$KUBECONFIG" | base64 -d > /tmp/kubeconfig
    - export KUBECONFIG=/tmp/kubeconfig
    - kubectl apply -f k8s/
  variables:
    # Masked in logs
    DATABASE_URL: $DATABASE_URL
    API_KEY: $API_KEY
  environment:
    name: production
```

## Pipeline Metrics

```yaml
# Track pipeline performance
metrics:
  - pipeline_duration_seconds
  - job_success_rate
  - deployment_frequency
  - lead_time_for_changes
  - time_to_restore_service
  - change_failure_rate
```

## Best Practices Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│              CI/CD Fundamentals Checklist                        │
├─────────────────────────────────────────────────────────────────┤
│ ☐ All code in version control                                   │
│ ☐ Automated builds on every commit                              │
│ ☐ Fast feedback (< 10 minutes for CI)                           │
│ ☐ Tests run automatically                                       │
│ ☐ Quality gates enforced                                        │
│ ☐ Artifacts versioned and stored                                │
│ ☐ Secrets securely managed                                      │
│ ☐ Environment parity (dev ≈ staging ≈ prod)                     │
│ ☐ Rollback capability                                           │
│ ☐ Pipeline as code (versioned)                                  │
│ ☐ Monitoring and alerting                                       │
│ ☐ Documentation up to date                                      │
└─────────────────────────────────────────────────────────────────┘
```
