---
name: flaky-tests
description: Identifying and fixing flaky tests in CI/CD pipelines
category: testing/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Flaky Tests

## Overview

Flaky tests pass or fail inconsistently without code changes. They erode
confidence in the test suite and slow down development by requiring reruns
and manual investigation.

## Identifying Flaky Tests

```
┌─────────────────────────────────────────────────────────────────┐
│                    Flaky Test Symptoms                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ❌ Fails randomly on CI but passes locally                   │
│   ❌ Passes when run alone, fails in suite                     │
│   ❌ Fails intermittently with same code                       │
│   ❌ Different results on different machines                   │
│   ❌ Time-dependent failures (midnight, DST)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Causes

| Category | Cause | Example |
|----------|-------|---------|
| **Timing** | Race conditions | Async without await |
| **Timing** | Timeouts too short | Network latency |
| **State** | Shared mutable state | Global variables |
| **State** | Test order dependency | Unclean database |
| **Environment** | Time-based logic | Date comparisons |
| **Environment** | Random data | Unseeded random |
| **Resources** | External services | API rate limits |
| **Resources** | Resource exhaustion | Memory leaks |

## Timing Issues

### Race Conditions

```typescript
// ❌ Flaky: Race condition
it('should update user', async () => {
  updateUser('123', { name: 'New Name' }); // Missing await!
  const user = await getUser('123');
  expect(user.name).toBe('New Name'); // May fail
});

// ✅ Fixed: Proper async handling
it('should update user', async () => {
  await updateUser('123', { name: 'New Name' });
  const user = await getUser('123');
  expect(user.name).toBe('New Name');
});
```

### Insufficient Waits

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

### Animation Timing

```typescript
// ❌ Flaky: Animation not complete
it('should close modal', async () => {
  await page.click('[data-testid="close"]');
  expect(await page.isVisible('.modal')).toBe(false);
});

// ✅ Fixed: Wait for animation
it('should close modal', async () => {
  await page.click('[data-testid="close"]');
  await page.waitForSelector('.modal', { state: 'hidden' });
  expect(await page.isVisible('.modal')).toBe(false);
});
```

## State Issues

### Shared State

```typescript
// ❌ Flaky: Shared mutable state
let counter = 0;

describe('Counter tests', () => {
  it('increments counter', () => {
    counter++;
    expect(counter).toBe(1); // Depends on test order
  });

  it('decrements counter', () => {
    counter--;
    expect(counter).toBe(0); // May fail
  });
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

  it('decrements counter', () => {
    counter--;
    expect(counter).toBe(-1);
  });
});
```

### Database State

```typescript
// ❌ Flaky: Database not cleaned
describe('User tests', () => {
  it('creates user', async () => {
    await createUser({ email: 'test@example.com' });
    const user = await getUser('test@example.com');
    expect(user).toBeDefined();
  });

  it('lists users', async () => {
    const users = await listUsers();
    expect(users).toHaveLength(0); // Fails if previous test ran
  });
});

// ✅ Fixed: Clean state between tests
describe('User tests', () => {
  beforeEach(async () => {
    await clearDatabase();
  });

  afterEach(async () => {
    await clearDatabase();
  });

  it('creates user', async () => {
    await createUser({ email: 'test@example.com' });
    const user = await getUser('test@example.com');
    expect(user).toBeDefined();
  });

  it('lists users', async () => {
    const users = await listUsers();
    expect(users).toHaveLength(0);
  });
});
```

### Test Order Dependency

```typescript
// ❌ Flaky: Tests depend on order
describe('Auth flow', () => {
  it('should login', async () => {
    await login('user', 'pass');
    expect(isLoggedIn()).toBe(true);
  });

  it('should access dashboard', async () => {
    // Assumes login test ran first!
    const dashboard = await getDashboard();
    expect(dashboard).toBeDefined();
  });
});

// ✅ Fixed: Each test is independent
describe('Auth flow', () => {
  beforeEach(async () => {
    await logout();
  });

  it('should login', async () => {
    await login('user', 'pass');
    expect(isLoggedIn()).toBe(true);
  });

  it('should access dashboard when logged in', async () => {
    await login('user', 'pass'); // Setup in test
    const dashboard = await getDashboard();
    expect(dashboard).toBeDefined();
  });
});
```

## Environment Issues

### Time-Based Tests

```typescript
// ❌ Flaky: Depends on current time
it('should show greeting', () => {
  const greeting = getGreeting();
  expect(greeting).toBe('Good morning'); // Fails after noon
});

// ✅ Fixed: Mock time
it('should show morning greeting', () => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2024-01-01T09:00:00'));

  const greeting = getGreeting();
  expect(greeting).toBe('Good morning');

  jest.useRealTimers();
});

it('should show evening greeting', () => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2024-01-01T18:00:00'));

  const greeting = getGreeting();
  expect(greeting).toBe('Good evening');

  jest.useRealTimers();
});
```

### Random Data

```typescript
// ❌ Flaky: Unseeded random
it('should generate valid ID', () => {
  const id = generateId();
  expect(id).toHaveLength(8); // May fail with certain random values
});

// ✅ Fixed: Seeded random for reproducibility
it('should generate valid ID', () => {
  // Seed the random generator
  jest.spyOn(Math, 'random').mockReturnValue(0.5);

  const id = generateId();
  expect(id).toHaveLength(8);
  expect(id).toBe('expected-id'); // Deterministic

  jest.restoreAllMocks();
});
```

## CI/CD Strategies

### Retry Configuration

```yaml
# Jest retry
# jest.config.js
module.exports = {
  // Retry failed tests
  testRetries: 2,
};

# Playwright retry
# playwright.config.ts
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

### Quarantine Flaky Tests

```typescript
// Mark flaky tests
describe.skip('Flaky test suite', () => {
  // Temporarily disabled while investigating
});

// Or use custom annotation
it.todo('should handle edge case (flaky - investigating)');

// Jest with custom runner
it.flaky('sometimes fails due to timing', async () => {
  // Test code
}, { retries: 3 });
```

### Flaky Test Detection

```yaml
# .github/workflows/flaky-detection.yml
name: Flaky Test Detection

on:
  schedule:
    - cron: '0 0 * * *' # Daily

jobs:
  detect-flaky:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        run: [1, 2, 3, 4, 5] # Run 5 times
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
          # Compare results across runs
          # Flag tests that passed in some runs but failed in others
```

### Flaky Test Tracking

```typescript
// scripts/track-flaky-tests.ts
interface TestResult {
  name: string;
  passed: boolean;
  duration: number;
  retries: number;
}

async function trackFlakyTests(results: TestResult[]): Promise<void> {
  const db = await getDatabase();

  for (const result of results) {
    await db.collection('test_results').insertOne({
      ...result,
      timestamp: new Date(),
      commit: process.env.GITHUB_SHA,
    });
  }

  // Find tests that have failed > 10% of the time
  const flakyTests = await db.collection('test_results').aggregate([
    { $group: {
      _id: '$name',
      totalRuns: { $sum: 1 },
      failures: { $sum: { $cond: ['$passed', 0, 1] } },
    }},
    { $match: {
      $expr: { $gt: [{ $divide: ['$failures', '$totalRuns'] }, 0.1] }
    }},
  ]).toArray();

  console.log('Flaky tests detected:', flakyTests);
}
```

## Debugging Flaky Tests

### Verbose Logging

```typescript
// Add detailed logging
it('should complete checkout', async () => {
  console.log('Starting checkout test');
  console.log('Cart state:', await getCartState());

  await clickCheckout();
  console.log('After checkout click');

  await waitFor(() => {
    console.log('Checking for confirmation...');
    expect(screen.getByText('Order confirmed')).toBeVisible();
  });
});
```

### Screenshot on Failure

```typescript
// playwright.config.ts
export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    video: 'retain-on-failure',
  },
});

// Custom failure handling
afterEach(async function() {
  if (this.currentTest?.state === 'failed') {
    await page.screenshot({
      path: `screenshots/${this.currentTest.title}.png`,
      fullPage: true,
    });
  }
});
```

### Reproduce Locally

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

## Prevention Strategies

| Strategy | Implementation |
|----------|----------------|
| **Proper async handling** | Always await, use waitFor |
| **Isolated test state** | beforeEach/afterEach cleanup |
| **Mock external services** | Don't hit real APIs in tests |
| **Deterministic time** | Use fake timers |
| **Seeded random** | Control randomness |
| **Sufficient timeouts** | Account for CI slowness |
| **Resource cleanup** | Close connections, clear caches |

## Flaky Test Metrics

| Metric | Good | Needs Work | Critical |
|--------|------|------------|----------|
| Flaky rate | <1% | 1-5% | >5% |
| Retry success | >95% | 80-95% | <80% |
| Time to fix | <1 day | 1-7 days | >7 days |
| Quarantined tests | <5 | 5-20 | >20 |

## Best Practices

| Do | Don't |
|----|-------|
| Mock time-dependent code | Depend on current time |
| Use explicit waits | Use arbitrary sleep/timeout |
| Isolate test state | Share state between tests |
| Seed random generators | Use unseeded random |
| Clean up resources | Leave database dirty |
| Retry strategically | Retry indefinitely |
| Track flaky tests | Ignore intermittent failures |
| Fix root causes | Just add more retries |

## Related Topics

- [Test Automation](./test-automation.md)
- [Coverage Reporting](./coverage-reporting.md)
- [Testing Principles](../fundamentals/testing-principles.md)
