# CI/CD Testing Strategies

Test automation pipelines, coverage reporting, and flaky test management.

## Table of Contents

1. [Test Automation Pipeline](#test-automation-pipeline)
2. [GitHub Actions Configuration](#github-actions-configuration)
3. [Coverage Reporting](#coverage-reporting)
4. [Flaky Test Management](#flaky-test-management)
5. [Performance Optimization](#performance-optimization)

---

## Test Automation Pipeline

### Pipeline Stages

```
Commit → [Lint] → [Unit] → [Integration] → [E2E] → Deploy
           ↓         ↓           ↓            ↓
         Fast      Fast      Medium        Slow
        (<1min)   (<5min)   (<10min)     (<30min)
```

### Stage Summary

| Stage | Tests | Trigger | Duration |
|-------|-------|---------|----------|
| Pre-commit | Lint, format | git commit | <1 min |
| PR Checks | Unit, type-check | Pull request | <5 min |
| Integration | Integration tests | PR merge | <15 min |
| E2E | Full E2E suite | Main branch | <30 min |
| Nightly | Full regression | Scheduled | 1+ hour |

---

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

### Conditional Execution

```yaml
jobs:
  detect-changes:
    runs-on: ubuntu-latest
    outputs:
      frontend: ${{ steps.filter.outputs.frontend }}
      backend: ${{ steps.filter.outputs.backend }}
    steps:
      - uses: actions/checkout@v4
      - uses: dorny/paths-filter@v2
        id: filter
        with:
          filters: |
            frontend:
              - 'src/frontend/**'
            backend:
              - 'src/backend/**'

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

---

## Coverage Reporting

### Coverage Types

| Type | Measures | Example |
|------|----------|---------|
| **Line** | Executed lines | 85/100 lines = 85% |
| **Branch** | Decision paths | 12/20 branches = 60% |
| **Function** | Called functions | 45/50 functions = 90% |
| **Statement** | Executed statements | 200/250 = 80% |

### Jest Coverage Configuration

```javascript
// jest.config.js
module.exports = {
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!src/**/index.{js,ts}',
    '!src/types/**',
  ],

  coverageDirectory: 'coverage',

  coverageReporters: [
    'text',           // Console output
    'text-summary',   // Summary
    'lcov',           // For Codecov
    'html',           // HTML report
    'json-summary',   // JSON for badges
  ],

  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    // Higher for critical modules
    './src/utils/**/*.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    // Lower for legacy code
    './src/legacy/**/*.ts': {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },
};
```

### Codecov Configuration

```yaml
# codecov.yml
coverage:
  precision: 2
  round: down
  range: "70...100"

  status:
    project:
      default:
        target: 80%
        threshold: 1%

    patch:
      default:
        target: 80%
        threshold: 5%

comment:
  layout: "reach,diff,flags,files,footer"
  behavior: default
  require_changes: true

flags:
  unit:
    paths:
      - src/
    carryforward: true

  integration:
    paths:
      - src/
    carryforward: true
```

### GitHub Actions Coverage

```yaml
- name: Run tests with coverage
  run: npm test -- --coverage

- name: Upload to Codecov
  uses: codecov/codecov-action@v3
  with:
    token: ${{ secrets.CODECOV_TOKEN }}
    files: ./coverage/lcov.info
    flags: unittests
    fail_ci_if_error: true

- name: Coverage comment on PR
  uses: MishaKav/jest-coverage-comment@main
  if: github.event_name == 'pull_request'
  with:
    coverage-summary-path: ./coverage/coverage-summary.json
```

### Coverage Thresholds

| Code Type | Recommended | Minimum |
|-----------|-------------|---------|
| **Core business logic** | 90-100% | 85% |
| **Utilities/helpers** | 85-95% | 80% |
| **API handlers** | 80-90% | 70% |
| **UI components** | 70-85% | 60% |
| **Integration code** | 60-80% | 50% |
| **Legacy code** | 40-60% | 30% |

---

## Flaky Test Management

### Common Causes

| Category | Cause | Example |
|----------|-------|---------|
| **Timing** | Race conditions | Async without await |
| **Timing** | Timeouts too short | Network latency |
| **State** | Shared mutable state | Global variables |
| **State** | Test order dependency | Unclean database |
| **Environment** | Time-based logic | Date comparisons |
| **Environment** | Random data | Unseeded random |

### Timing Issues

```typescript
// ❌ Flaky: Race condition
it('should update user', async () => {
  updateUser('123', { name: 'New Name' }); // Missing await!
  const user = await getUser('123');
  expect(user.name).toBe('New Name');
});

// ✅ Fixed: Proper async handling
it('should update user', async () => {
  await updateUser('123', { name: 'New Name' });
  const user = await getUser('123');
  expect(user.name).toBe('New Name');
});
```

```typescript
// ❌ Flaky: Arbitrary timeout
it('should show notification', async () => {
  await clickButton('submit');
  await new Promise(resolve => setTimeout(resolve, 100));
  expect(screen.getByText('Success')).toBeVisible();
});

// ✅ Fixed: Wait for specific condition
it('should show notification', async () => {
  await clickButton('submit');
  await waitFor(() => {
    expect(screen.getByText('Success')).toBeVisible();
  });
});
```

### State Issues

```typescript
// ❌ Flaky: Shared state
let counter = 0;

it('increments counter', () => {
  counter++;
  expect(counter).toBe(1);  // Depends on test order
});

// ✅ Fixed: Isolated state
describe('Counter tests', () => {
  let counter: number;

  beforeEach(() => {
    counter = 0;
  });

  it('increments counter', () => {
    counter++;
    expect(counter).toBe(1);
  });
});
```

### Time-Based Tests

```typescript
// ❌ Flaky: Depends on current time
it('should show greeting', () => {
  const greeting = getGreeting();
  expect(greeting).toBe('Good morning');  // Fails after noon
});

// ✅ Fixed: Mock time
it('should show morning greeting', () => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2024-01-01T09:00:00'));

  const greeting = getGreeting();
  expect(greeting).toBe('Good morning');

  jest.useRealTimers();
});
```

### Retry Configuration

```yaml
# Jest retry
module.exports = {
  testRetries: 2,
};

# Playwright retry
export default defineConfig({
  retries: process.env.CI ? 2 : 0,
});

# GitHub Actions retry
- name: Run tests with retry
  uses: nick-fields/retry@v2
  with:
    max_attempts: 3
    timeout_minutes: 10
    command: npm test
```

### Flaky Test Detection

```yaml
name: Flaky Test Detection

on:
  schedule:
    - cron: '0 0 * * *'  # Daily

jobs:
  detect-flaky:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        run: [1, 2, 3, 4, 5]
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test -- --json --outputFile=results-${{ matrix.run }}.json

  analyze:
    needs: detect-flaky
    runs-on: ubuntu-latest
    steps:
      - name: Compare results
        run: |
          # Flag tests that passed/failed inconsistently
```

### Debugging Flaky Tests

```bash
# Run test multiple times
for i in {1..10}; do npm test -- --testNamePattern="flaky test" || break; done

# Run with same seed
npm test -- --randomize --seed=12345

# Run in isolation
npm test -- --runInBand --testNamePattern="specific test"

# Run with CI environment
CI=true npm test
```

---

## Performance Optimization

### Caching Strategies

```yaml
# Dependency caching
- name: Cache node_modules
  uses: actions/cache@v3
  with:
    path: |
      node_modules
      ~/.npm
    key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
    restore-keys: |
      ${{ runner.os }}-node-

# Playwright browser caching
- name: Cache Playwright browsers
  uses: actions/cache@v3
  with:
    path: ~/.cache/ms-playwright
    key: ${{ runner.os }}-playwright-${{ hashFiles('**/package-lock.json') }}

# Build caching
- name: Cache build outputs
  uses: actions/cache@v3
  with:
    path: |
      .next/cache
      dist
    key: ${{ runner.os }}-build-${{ hashFiles('src/**') }}
```

### Jest CI Configuration

```javascript
// jest.config.ci.js
module.exports = {
  ...require('./jest.config'),

  ci: true,
  maxWorkers: 2,
  verbose: true,
  bail: 1,
  clearMocks: true,
  restoreMocks: true,
  collectCoverage: true,
  coverageReporters: ['text', 'lcov', 'json-summary'],
  reporters: [
    'default',
    ['jest-junit', {
      outputDirectory: './reports/junit',
      outputName: 'junit.xml',
    }],
  ],
  testTimeout: 30000,
};
```

### Playwright CI Configuration

```typescript
// playwright.config.ts
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 2 : undefined,

  reporter: process.env.CI ? [
    ['html', { outputFolder: 'playwright-report' }],
    ['junit', { outputFile: 'reports/e2e-results.xml' }],
    ['github'],
  ] : 'list',

  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  webServer: process.env.CI ? {
    command: 'npm run start:prod',
    url: 'http://localhost:3000',
    reuseExistingServer: false,
    timeout: 120000,
  } : undefined,
});
```

---

## Best Practices Summary

| Do | Don't |
|----|-------|
| Run fast tests first | Run E2E before unit |
| Cache dependencies | Install fresh every time |
| Parallelize when possible | Run all tests sequentially |
| Fail fast on CI | Continue on failures |
| Use service containers | Mock everything |
| Store artifacts on failure | Discard debugging info |
| Track flaky test metrics | Ignore intermittent failures |
| Fix root causes | Just add more retries |

### Flaky Test Metrics

| Metric | Good | Needs Work | Critical |
|--------|------|------------|----------|
| Flaky rate | <1% | 1-5% | >5% |
| Retry success | >95% | 80-95% | <80% |
| Time to fix | <1 day | 1-7 days | >7 days |
| Quarantined tests | <5 | 5-20 | >20 |
