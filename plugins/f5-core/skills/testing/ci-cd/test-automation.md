---
name: test-automation
description: Automated testing strategies for CI/CD pipelines
category: testing/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Test Automation in CI/CD

## Overview

Test automation in CI/CD ensures code quality through automated testing at every
stage of the software delivery pipeline, providing fast feedback and preventing
regressions.

## CI/CD Testing Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     CI/CD Testing Pipeline                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Commit → [Lint] → [Unit] → [Integration] → [E2E] → Deploy    │
│              ↓         ↓           ↓            ↓                │
│            Fast      Fast      Medium        Slow               │
│           (<1min)   (<5min)   (<10min)     (<30min)            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## GitHub Actions Configuration

### Basic Test Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '20'
  CI: true

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run linting
        run: npm run lint

      - name: Type check
        run: npm run type-check

  unit-tests:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run unit tests
        run: npm run test:unit -- --coverage

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          flags: unit

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run migrations
        run: npm run db:migrate
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test

      - name: Run integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/test
          REDIS_URL: redis://localhost:6379

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          flags: integration

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Build application
        run: npm run build

      - name: Run E2E tests
        run: npm run test:e2e

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

### Parallel Test Execution

```yaml
# Parallel test jobs
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        shard: [1, 2, 3, 4]
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Run tests (shard ${{ matrix.shard }}/4)
        run: npm run test -- --shard=${{ matrix.shard }}/4

  merge-coverage:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Download all coverage artifacts
        uses: actions/download-artifact@v3
        with:
          pattern: coverage-*
          merge-multiple: true

      - name: Merge coverage reports
        run: npx nyc merge coverage coverage/merged.json

      - name: Upload merged coverage
        uses: codecov/codecov-action@v3
```

### Conditional Test Execution

```yaml
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
      docs: ${{ steps.filter.outputs.docs }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            frontend:
              - 'src/frontend/**'
              - 'package.json'
            backend:
              - 'src/backend/**'
              - 'package.json'
            docs:
              - 'docs/**'

  frontend-tests:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.frontend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:frontend

  backend-tests:
    needs: detect-changes
    if: ${{ needs.detect-changes.outputs.backend == 'true' }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:backend
```

## Test Configuration

### Jest Configuration for CI

```javascript
// jest.config.ci.js
module.exports = {
  ...require('./jest.config'),

  // CI-specific settings
  ci: true,
  maxWorkers: 2, // Limit parallelism in CI

  // Better error output
  verbose: true,

  // Fail fast on CI
  bail: 1,

  // Ensure clean state
  clearMocks: true,
  restoreMocks: true,

  // Coverage settings
  collectCoverage: true,
  coverageReporters: ['text', 'lcov', 'json-summary'],

  // CI reporters
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: './reports/junit',
      outputName: 'junit.xml',
    }],
  ],

  // Timeout for CI (longer due to cold starts)
  testTimeout: 30000,
};
```

### Playwright Configuration for CI

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',

  // CI settings
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,

  reporter: process.env.CI ? [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'reports/e2e-results.xml' }],
    ['github'], // GitHub annotations
  ] : 'list',

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],

  // Start server for tests
  webServer: process.env.CI ? {
    command: 'npm run start:prod',
    url: 'http://localhost:3000',
    reuseExistingServer: false,
    timeout: 120000,
  } : undefined,
});
```

## Test Results and Reporting

### JUnit Reports

```yaml
- name: Publish Test Results
  uses: EnricoMi/publish-unit-test-result-action@v2
  if: always()
  with:
    files: |
      reports/junit/*.xml
      reports/e2e-results.xml
```

### GitHub Check Annotations

```typescript
// Custom reporter for GitHub annotations
class GitHubReporter {
  onTestFailure(test: TestResult): void {
    const { testFilePath, failureMessages, location } = test;

    failureMessages.forEach(message => {
      console.log(
        `::error file=${testFilePath},line=${location?.line}::${message}`
      );
    });
  }
}
```

## Caching Strategies

### Dependency Caching

```yaml
- name: Cache node_modules
  uses: actions/cache@v3
  with:
    path: |
      node_modules
      ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-
```

### Test Result Caching

```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v3
  with:
    path: ~/.cache/ms-playwright
    key: ${{ runner.os }}-playwright-${{ hashFiles('**/package-lock.json') }}
```

### Build Caching

```yaml
- name: Cache build outputs
  uses: actions/cache@v3
  with:
    path: |
      .next/cache
      dist
    key: ${{ runner.os }}-build-${{ hashFiles('src/**') }}
```

## Test Stages

| Stage | Tests | Trigger | Duration |
|-------|-------|---------|----------|
| Pre-commit | Lint, format | git commit | <1 min |
| PR Checks | Unit, type-check | Pull request | <5 min |
| Integration | Integration tests | PR merge | <15 min |
| E2E | Full E2E suite | Main branch | <30 min |
| Nightly | Full regression | Scheduled | 1+ hour |

## Best Practices

| Do | Don't |
|----|-------|
| Run fast tests first | Run E2E before unit |
| Cache dependencies | Install fresh every time |
| Parallelize when possible | Run all tests sequentially |
| Fail fast on CI | Continue on failures |
| Use service containers | Mock everything |
| Store artifacts on failure | Discard debugging info |

## Related Topics

- [Coverage Reporting](./coverage-reporting.md)
- [Flaky Tests](./flaky-tests.md)
- [Integration Testing](../integration-testing/integration-test-basics.md)
