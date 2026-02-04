---
name: github-actions
description: GitHub Actions CI/CD implementation
category: devops/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GitHub Actions

## Overview

GitHub Actions is a CI/CD platform integrated into GitHub that allows you to
automate build, test, and deployment pipelines.

## Complete CI/CD Pipeline

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ==========================================================================
  # Lint & Type Check
  # ==========================================================================
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linter
        run: npm run lint

      - name: Type check
        run: npm run type-check

  # ==========================================================================
  # Unit & Integration Tests
  # ==========================================================================
  test:
    runs-on: ubuntu-latest
    needs: lint

    services:
      postgres:
        image: postgres:16-alpine
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: testdb
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run database migrations
        run: npm run db:migrate
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Run integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/testdb
          REDIS_URL: redis://localhost:6379

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}

  # ==========================================================================
  # Security Scan
  # ==========================================================================
  security:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Run npm audit
        run: npm audit --audit-level=high

  # ==========================================================================
  # Build Docker Image
  # ==========================================================================
  build:
    runs-on: ubuntu-latest
    needs: [test, security]
    permissions:
      contents: read
      packages: write

    outputs:
      image-tag: ${{ steps.meta.outputs.tags }}
      image-digest: ${{ steps.build.outputs.digest }}

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha,prefix={{branch}}-
            type=semver,pattern={{version}}

      - name: Build and push
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          build-args: |
            NODE_ENV=production

  # ==========================================================================
  # Deploy to Staging
  # ==========================================================================
  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.example.com

    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_STAGING }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build.outputs.image-digest }} \
            -n staging

      - name: Wait for rollout
        run: kubectl rollout status deployment/api -n staging --timeout=300s

      - name: Run smoke tests
        run: npm run test:smoke -- --env=staging

  # ==========================================================================
  # Deploy to Production
  # ==========================================================================
  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://example.com

    steps:
      - uses: actions/checkout@v4

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBE_CONFIG_PRODUCTION }}

      - name: Deploy canary
        run: |
          kubectl set image deployment/api-canary \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build.outputs.image-digest }} \
            -n production

      - name: Wait for canary rollout
        run: kubectl rollout status deployment/api-canary -n production --timeout=300s

      - name: Run smoke tests
        run: npm run test:smoke -- --env=production

      - name: Promote to production
        if: success()
        run: |
          kubectl set image deployment/api \
            api=${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build.outputs.image-digest }} \
            -n production

      - name: Wait for production rollout
        run: kubectl rollout status deployment/api -n production --timeout=300s

      - name: Rollback on failure
        if: failure()
        run: kubectl rollout undo deployment/api -n production
```

## Reusable Workflows

### Shared Test Workflow

```yaml
# .github/workflows/reusable-test.yml
name: Reusable Test Workflow

on:
  workflow_call:
    inputs:
      node-version:
        required: false
        type: string
        default: '20'
      run-e2e:
        required: false
        type: boolean
        default: false
    secrets:
      codecov-token:
        required: false
    outputs:
      coverage:
        description: 'Test coverage percentage'
        value: ${{ jobs.test.outputs.coverage }}

jobs:
  test:
    runs-on: ubuntu-latest
    outputs:
      coverage: ${{ steps.coverage.outputs.percentage }}

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ inputs.node-version }}
          cache: 'npm'

      - run: npm ci

      - name: Run tests
        run: npm test -- --coverage

      - name: Extract coverage
        id: coverage
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          echo "percentage=$COVERAGE" >> $GITHUB_OUTPUT

      - name: Run E2E tests
        if: inputs.run-e2e
        run: npm run test:e2e
```

### Using Reusable Workflows

```yaml
# .github/workflows/pr.yml
name: PR Checks

on:
  pull_request:
    branches: [main]

jobs:
  test:
    uses: ./.github/workflows/reusable-test.yml
    with:
      node-version: '20'
      run-e2e: true
    secrets:
      codecov-token: ${{ secrets.CODECOV_TOKEN }}

  check-coverage:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Check coverage threshold
        run: |
          if [ $(echo "${{ needs.test.outputs.coverage }} < 80" | bc) -eq 1 ]; then
            echo "Coverage is below 80%"
            exit 1
          fi
```

## Matrix Builds

```yaml
# .github/workflows/matrix.yml
name: Matrix Build

on: [push, pull_request]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [18, 20, 22]
        exclude:
          - os: windows-latest
            node: 18
        include:
          - os: ubuntu-latest
            node: 20
            coverage: true
      fail-fast: false

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}

      - run: npm ci
      - run: npm test

      - name: Upload coverage
        if: matrix.coverage
        uses: codecov/codecov-action@v3
```

## Composite Actions

```yaml
# .github/actions/setup-project/action.yml
name: 'Setup Project'
description: 'Setup Node.js and install dependencies'

inputs:
  node-version:
    description: 'Node.js version'
    required: false
    default: '20'

runs:
  using: 'composite'
  steps:
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: ${{ inputs.node-version }}
        cache: 'npm'

    - name: Install dependencies
      shell: bash
      run: npm ci

    - name: Cache Prisma
      uses: actions/cache@v3
      with:
        path: node_modules/.prisma
        key: prisma-${{ hashFiles('prisma/schema.prisma') }}
```

```yaml
# Usage in workflow
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-project
        with:
          node-version: '20'
      - run: npm run build
```

## Environment and Secrets

```yaml
# Environment-specific deployments
deploy:
  runs-on: ubuntu-latest
  environment:
    name: production
    url: https://example.com

  steps:
    - name: Deploy
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
        API_KEY: ${{ secrets.API_KEY }}
      run: |
        # Secrets are masked in logs
        echo "Deploying to ${{ vars.ENVIRONMENT_NAME }}"
```

## Caching Strategies

```yaml
# Effective caching
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # npm cache
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      # Custom cache for build artifacts
      - uses: actions/cache@v3
        with:
          path: |
            .next/cache
            dist
          key: build-${{ hashFiles('**/package-lock.json') }}-${{ hashFiles('src/**') }}
          restore-keys: |
            build-${{ hashFiles('**/package-lock.json') }}-
            build-

      - run: npm ci
      - run: npm run build
```

## Artifacts

```yaml
# Upload and download artifacts
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run build

      - name: Upload build artifact
        uses: actions/upload-artifact@v4
        with:
          name: build
          path: dist/
          retention-days: 7

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download build artifact
        uses: actions/download-artifact@v4
        with:
          name: build
          path: dist/

      - name: Deploy
        run: ./deploy.sh dist/
```

## Scheduled Workflows

```yaml
# .github/workflows/scheduled.yml
name: Scheduled Tasks

on:
  schedule:
    # Run at 2 AM UTC every day
    - cron: '0 2 * * *'
  workflow_dispatch:  # Allow manual trigger

jobs:
  nightly-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:e2e

  dependency-update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update dependencies
        run: |
          npm update
          npm audit fix

      - name: Create PR if changes
        uses: peter-evans/create-pull-request@v5
        with:
          title: 'chore: update dependencies'
          commit-message: 'chore: update dependencies'
          branch: deps/update
```

## Status Checks and Branch Protection

```yaml
# Required status checks
name: Required Checks

on:
  pull_request:
    branches: [main]

jobs:
  # This job name is used in branch protection rules
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run lint
      - run: npm test
      - run: npm run build
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              GitHub Actions Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Pin action versions (uses: actions/checkout@v4)               │
│ ☐ Use caching for dependencies                                  │
│ ☐ Run jobs in parallel when possible                            │
│ ☐ Use matrix builds for cross-platform testing                  │
│ ☐ Extract reusable workflows                                    │
│ ☐ Use environments for deployment protection                    │
│ ☐ Store secrets securely                                        │
│ ☐ Use GITHUB_TOKEN when possible (vs PAT)                       │
│ ☐ Set timeout-minutes to prevent hung jobs                      │
│ ☐ Use concurrency to cancel redundant runs                      │
│ ☐ Add workflow_dispatch for manual triggers                     │
│ ☐ Document workflows with comments                              │
└─────────────────────────────────────────────────────────────────┘
```
