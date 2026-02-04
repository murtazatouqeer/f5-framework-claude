---
name: pipeline-patterns
description: Common CI/CD pipeline patterns and anti-patterns
category: devops/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Pipeline Patterns

## Overview

Effective CI/CD pipelines follow proven patterns that optimize for speed,
reliability, and maintainability while avoiding common anti-patterns.

## Pipeline Architecture Patterns

### 1. Fan-Out/Fan-In Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                   Fan-Out/Fan-In Pattern                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                        ┌──────────┐                              │
│                        │  Build   │                              │
│                        └────┬─────┘                              │
│           ┌─────────────────┼─────────────────┐                  │
│           ▼                 ▼                 ▼                  │
│     ┌──────────┐      ┌──────────┐      ┌──────────┐            │
│     │Unit Tests│      │Int Tests │      │E2E Tests │            │
│     └────┬─────┘      └────┬─────┘      └────┬─────┘            │
│           └─────────────────┼─────────────────┘                  │
│                             ▼                                    │
│                        ┌──────────┐                              │
│                        │  Deploy  │                              │
│                        └──────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```yaml
# Implementation
jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      artifact-id: ${{ steps.upload.outputs.artifact-id }}
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - uses: actions/upload-artifact@v4
        id: upload
        with:
          name: build
          path: dist/

  # Fan-out: parallel test jobs
  unit-tests:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - run: npm run test:unit

  integration-tests:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - run: npm run test:integration

  e2e-tests:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/download-artifact@v4
      - run: npm run test:e2e

  # Fan-in: wait for all tests
  deploy:
    needs: [unit-tests, integration-tests, e2e-tests]
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
```

### 2. Diamond Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                      Diamond Pattern                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                        ┌──────────┐                              │
│                        │ Validate │                              │
│                        └────┬─────┘                              │
│                 ┌───────────┴───────────┐                        │
│                 ▼                       ▼                        │
│           ┌──────────┐           ┌──────────┐                    │
│           │  Build   │           │  Lint    │                    │
│           │ Frontend │           │  Check   │                    │
│           └────┬─────┘           └────┬─────┘                    │
│                 └───────────┬───────────┘                        │
│                             ▼                                    │
│                        ┌──────────┐                              │
│                        │  Test    │                              │
│                        └────┬─────┘                              │
│                 ┌───────────┴───────────┐                        │
│                 ▼                       ▼                        │
│           ┌──────────┐           ┌──────────┐                    │
│           │ Security │           │ Quality  │                    │
│           │   Scan   │           │  Gate    │                    │
│           └────┬─────┘           └────┬─────┘                    │
│                 └───────────┬───────────┘                        │
│                             ▼                                    │
│                        ┌──────────┐                              │
│                        │  Deploy  │                              │
│                        └──────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Progressive Delivery Pattern

```yaml
# Progressive environment promotion
stages:
  - build
  - test
  - deploy-dev
  - test-dev
  - deploy-staging
  - test-staging
  - deploy-production

deploy-dev:
  stage: deploy-dev
  environment: development
  script:
    - deploy --env=dev

smoke-test-dev:
  stage: test-dev
  needs: [deploy-dev]
  script:
    - npm run test:smoke -- --env=dev

deploy-staging:
  stage: deploy-staging
  needs: [smoke-test-dev]
  environment: staging
  script:
    - deploy --env=staging

integration-test-staging:
  stage: test-staging
  needs: [deploy-staging]
  script:
    - npm run test:integration -- --env=staging

deploy-production:
  stage: deploy-production
  needs: [integration-test-staging]
  environment: production
  when: manual
  script:
    - deploy --env=production --canary=10%
```

### 4. Monorepo Pattern

```yaml
# Detect changed packages and run targeted builds
name: Monorepo CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      api: ${{ steps.changes.outputs.api }}
      web: ${{ steps.changes.outputs.web }}
      shared: ${{ steps.changes.outputs.shared }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: changes
        with:
          filters: |
            api:
              - 'packages/api/**'
              - 'packages/shared/**'
            web:
              - 'packages/web/**'
              - 'packages/shared/**'
            shared:
              - 'packages/shared/**'

  build-api:
    needs: detect-changes
    if: needs.detect-changes.outputs.api == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build --workspace=@app/api

  build-web:
    needs: detect-changes
    if: needs.detect-changes.outputs.web == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build --workspace=@app/web

  test-shared:
    needs: detect-changes
    if: needs.detect-changes.outputs.shared == 'true'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test --workspace=@app/shared
```

## Testing Patterns

### Test Pyramid in Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                      Test Pyramid                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                         /\                                       │
│                        /  \     E2E Tests                        │
│                       /    \    (Slow, Few)                      │
│                      /──────\                                    │
│                     /        \   Integration Tests               │
│                    /          \  (Medium)                        │
│                   /────────────\                                 │
│                  /              \  Unit Tests                    │
│                 /________________\ (Fast, Many)                  │
│                                                                  │
│  Pipeline Order:                                                 │
│  1. Unit tests (fast feedback)                                  │
│  2. Integration tests (validate connections)                    │
│  3. E2E tests (validate user flows)                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

```yaml
test:
  parallel:
    matrix:
      - TEST_TYPE: unit
        TIMEOUT: 5m
      - TEST_TYPE: integration
        TIMEOUT: 15m
      - TEST_TYPE: e2e
        TIMEOUT: 30m
  script:
    - npm run test:$TEST_TYPE
  timeout: $TIMEOUT
```

### Shift-Left Testing

```yaml
# Run tests as early as possible
stages:
  - pre-commit  # Fastest checks first
  - build
  - test
  - security
  - deploy

pre-commit:
  stage: pre-commit
  script:
    - npm run lint
    - npm run type-check
    - npm run test:unit -- --bail --findRelatedTests
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Build Patterns

### Incremental Builds

```yaml
build:
  script:
    - |
      # Check if rebuild is needed
      CACHE_KEY=$(cat package-lock.json src/**/*.ts | md5sum | cut -d' ' -f1)
      if [ -f ".build-cache/$CACHE_KEY" ]; then
        echo "Using cached build"
        cp -r .build-cache/$CACHE_KEY dist/
      else
        npm run build
        mkdir -p .build-cache
        cp -r dist .build-cache/$CACHE_KEY
      fi
  cache:
    key: build-cache
    paths:
      - .build-cache/
```

### Multi-Architecture Builds

```yaml
build:
  runs-on: ubuntu-latest
  strategy:
    matrix:
      platform:
        - linux/amd64
        - linux/arm64
  steps:
    - uses: docker/setup-qemu-action@v3
    - uses: docker/setup-buildx-action@v3
    - uses: docker/build-push-action@v5
      with:
        platforms: ${{ matrix.platform }}
        push: true
        tags: myapp:${{ github.sha }}-${{ matrix.platform }}

  # Combine manifests
  create-manifest:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: |
          docker manifest create myapp:${{ github.sha }} \
            myapp:${{ github.sha }}-linux-amd64 \
            myapp:${{ github.sha }}-linux-arm64
          docker manifest push myapp:${{ github.sha }}
```

## Security Patterns

### Security Gate Pattern

```yaml
security-gate:
  stage: security
  parallel:
    matrix:
      - SCAN_TYPE: sast
      - SCAN_TYPE: dependency
      - SCAN_TYPE: container
      - SCAN_TYPE: secrets
  script:
    - |
      case $SCAN_TYPE in
        sast)
          semgrep --config=auto .
          ;;
        dependency)
          npm audit --audit-level=high
          ;;
        container)
          trivy image --severity CRITICAL,HIGH $IMAGE
          ;;
        secrets)
          gitleaks detect --source . --verbose
          ;;
      esac
  allow_failure:
    exit_codes: 1  # Continue on warning-level findings
```

### SBOM (Software Bill of Materials)

```yaml
generate-sbom:
  stage: build
  script:
    - syft packages . -o spdx-json > sbom.json
    - grype sbom:sbom.json --fail-on critical
  artifacts:
    paths:
      - sbom.json
    reports:
      sbom: sbom.json
```

## Deployment Patterns

### GitOps Pattern

```yaml
# Update GitOps repo on successful build
update-gitops:
  stage: deploy
  script:
    - |
      git clone https://github.com/org/gitops-repo.git
      cd gitops-repo
      yq eval ".spec.template.spec.containers[0].image = \"$IMAGE_TAG\"" \
        -i apps/api/deployment.yaml
      git add .
      git commit -m "Update api to $IMAGE_TAG"
      git push
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Feature Flag Deployment

```yaml
deploy:
  script:
    - |
      # Deploy with feature flags
      kubectl set env deployment/api \
        FEATURE_NEW_UI=${{ vars.FEATURE_NEW_UI }} \
        FEATURE_BETA_API=${{ vars.FEATURE_BETA_API }}

      # Gradual rollout based on flags
      if [ "$GRADUAL_ROLLOUT" == "true" ]; then
        kubectl rollout restart deployment/api --strategy=rolling
      else
        kubectl rollout restart deployment/api
      fi
```

## Anti-Patterns to Avoid

### 1. Snowflake Pipelines

```yaml
# ❌ Bad: Inconsistent configurations
job1:
  image: node:18
  script: npm test

job2:
  image: node:20
  script: npm test

# ✅ Good: Centralized configuration
.node-template:
  image: node:20
  before_script:
    - npm ci

job1:
  extends: .node-template
  script: npm test

job2:
  extends: .node-template
  script: npm run lint
```

### 2. Long-Running Monolithic Jobs

```yaml
# ❌ Bad: One huge job
all-in-one:
  script:
    - npm ci
    - npm run lint
    - npm run build
    - npm run test:unit
    - npm run test:integration
    - npm run test:e2e
    - docker build
    - docker push
    - kubectl apply

# ✅ Good: Separated, parallel jobs
lint:
  script: npm run lint
test-unit:
  script: npm run test:unit
test-integration:
  script: npm run test:integration
build:
  needs: [lint, test-unit]
  script: npm run build
```

### 3. Manual Dependencies

```yaml
# ❌ Bad: Implicit dependency on shared state
build:
  script:
    - npm run build
    - aws s3 cp dist/ s3://bucket/

deploy:
  script:
    - aws s3 cp s3://bucket/ dist/  # Hoping build ran first
    - kubectl apply

# ✅ Good: Explicit artifacts
build:
  script: npm run build
  artifacts:
    paths:
      - dist/

deploy:
  needs: [build]
  script:
    # dist/ is automatically downloaded
    - kubectl apply
```

## Best Practices Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│              Pipeline Patterns Checklist                         │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Fast feedback (unit tests first)                              │
│ ☐ Parallel execution where possible                             │
│ ☐ Explicit dependencies (needs/depends_on)                      │
│ ☐ Fail fast on critical issues                                  │
│ ☐ Incremental builds with caching                               │
│ ☐ Security scanning integrated                                  │
│ ☐ Environment promotion gates                                   │
│ ☐ Artifact versioning and retention                             │
│ ☐ Reusable templates/workflows                                  │
│ ☐ Monorepo-aware (if applicable)                                │
│ ☐ Feature flag integration                                      │
│ ☐ Rollback capability                                           │
└─────────────────────────────────────────────────────────────────┘
```
