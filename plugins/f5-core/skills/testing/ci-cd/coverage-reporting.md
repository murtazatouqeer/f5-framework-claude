---
name: coverage-reporting
description: Code coverage measurement and reporting strategies
category: testing/ci-cd
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Coverage Reporting

## Overview

Code coverage measures how much of your code is exercised by tests. While not
a complete measure of test quality, coverage helps identify untested code paths
and ensures minimum quality standards.

## Coverage Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    Coverage Types                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Line Coverage:     Which lines were executed?                 │
│   Branch Coverage:   Which branches (if/else) were taken?       │
│   Function Coverage: Which functions were called?               │
│   Statement Coverage: Which statements were executed?           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

| Type | Measures | Example |
|------|----------|---------|
| **Line** | Executed lines | 85/100 lines = 85% |
| **Branch** | Decision paths | 12/20 branches = 60% |
| **Function** | Called functions | 45/50 functions = 90% |
| **Statement** | Executed statements | 200/250 statements = 80% |

## Jest Coverage Configuration

### Basic Setup

```javascript
// jest.config.js
module.exports = {
  collectCoverage: true,
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/*.test.{js,jsx,ts,tsx}',
    '!src/**/index.{js,ts}', // Re-export files
    '!src/types/**',
  ],

  coverageDirectory: 'coverage',

  coverageReporters: [
    'text',           // Console output
    'text-summary',   // Summary in console
    'lcov',           // For Codecov/Coveralls
    'html',           // HTML report
    'json-summary',   // JSON for badges
  ],

  // Thresholds
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    // Per-file thresholds
    './src/utils/**/*.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    // Lower threshold for complex legacy code
    './src/legacy/**/*.ts': {
      branches: 50,
      functions: 50,
      lines: 50,
      statements: 50,
    },
  },
};
```

### Running Coverage

```bash
# Basic coverage
npm test -- --coverage

# With specific reporters
npm test -- --coverage --coverageReporters=text-summary

# Update snapshots with coverage
npm test -- --coverage --updateSnapshot

# Coverage for changed files only
npm test -- --coverage --changedSince=main
```

## Coverage Reports

### Console Output

```
---------------------|---------|----------|---------|---------|-------------------
File                 | % Stmts | % Branch | % Funcs | % Lines | Uncovered Line #s
---------------------|---------|----------|---------|---------|-------------------
All files            |   85.23 |    72.45 |   88.12 |   84.91 |
 src/services        |   92.45 |    85.71 |   95.00 |   92.13 |
  auth.service.ts    |   95.12 |    90.00 |  100.00 |   94.87 | 45,67
  user.service.ts    |   89.78 |    81.43 |   90.00 |   89.39 | 23-25,89,112
 src/utils           |   78.01 |    59.18 |   81.25 |   77.45 |
  validators.ts      |   65.43 |    42.86 |   70.00 |   64.71 | 15-20,45-52,78
---------------------|---------|----------|---------|---------|-------------------
```

### HTML Report

```bash
# Generate and open HTML report
npm test -- --coverage
open coverage/lcov-report/index.html
```

## CI/CD Integration

### GitHub Actions with Codecov

```yaml
# .github/workflows/coverage.yml
name: Coverage

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  coverage:
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

      - name: Run tests with coverage
        run: npm test -- --coverage

      - name: Upload to Codecov
        uses: codecov/codecov-action@v3
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: ./coverage/lcov.info
          flags: unittests
          name: codecov-umbrella
          fail_ci_if_error: true

      - name: Coverage comment on PR
        uses: MishaKav/jest-coverage-comment@main
        if: github.event_name == 'pull_request'
        with:
          coverage-summary-path: ./coverage/coverage-summary.json
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

parsers:
  gcov:
    branch_detection:
      conditional: yes
      loop: yes
      method: no
      macro: no

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

### Coverage Badges

```markdown
<!-- In README.md -->
[![codecov](https://codecov.io/gh/owner/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/owner/repo)

<!-- Or using shields.io -->
![Coverage](https://img.shields.io/codecov/c/github/owner/repo)
```

## Coverage Enforcement

### Pre-commit Hook

```bash
#!/bin/sh
# .husky/pre-commit

npm test -- --coverage --coverageThreshold='{"global":{"lines":80}}'
```

### PR Gates

```yaml
# GitHub branch protection
# Settings → Branches → Branch protection rules
# Require status checks:
# - coverage/codecov/patch
# - coverage/codecov/project
```

### Diff Coverage

```yaml
# Only check coverage on changed lines
- name: Check diff coverage
  run: |
    npm test -- --coverage --changedSince=origin/main
    npx diff-cover coverage/lcov.info --compare-branch=origin/main --fail-under=80
```

## Coverage Analysis

### Identifying Coverage Gaps

```typescript
// coverage/gap-analysis.ts
import * as fs from 'fs';

interface CoverageSummary {
  total: {
    lines: { pct: number };
    branches: { pct: number };
    functions: { pct: number };
    statements: { pct: number };
  };
}

function analyzeCoverage(): void {
  const summary: CoverageSummary = JSON.parse(
    fs.readFileSync('coverage/coverage-summary.json', 'utf-8')
  );

  const files = Object.entries(summary).filter(([key]) => key !== 'total');

  // Find files below threshold
  const lowCoverage = files.filter(([_, data]) => {
    return (data as any).lines.pct < 80;
  });

  console.log('Files below 80% coverage:');
  lowCoverage.forEach(([file, data]) => {
    console.log(`  ${file}: ${(data as any).lines.pct}%`);
  });
}
```

### Coverage Trends

```yaml
# Track coverage over time
- name: Track coverage trend
  run: |
    COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
    echo "coverage=$COVERAGE" >> $GITHUB_OUTPUT

- name: Update coverage badge
  uses: schneegans/dynamic-badges-action@v1.6.0
  with:
    auth: ${{ secrets.GIST_TOKEN }}
    gistID: your-gist-id
    filename: coverage.json
    label: Coverage
    message: ${{ steps.coverage.outputs.coverage }}%
    valColorRange: ${{ steps.coverage.outputs.coverage }}
    maxColorRange: 100
    minColorRange: 0
```

## Coverage Best Practices

### What to Cover

```typescript
// ✅ High-value coverage targets
// - Business logic
// - Data transformations
// - Error handling paths
// - Edge cases

// ✅ Test the calculation logic
function calculateDiscount(price: number, discount: number): number {
  if (discount < 0 || discount > 100) {
    throw new Error('Invalid discount');
  }
  return price * (1 - discount / 100);
}

// Test covers: valid input, boundary conditions, error case
describe('calculateDiscount', () => {
  it('calculates discount correctly', () => {
    expect(calculateDiscount(100, 10)).toBe(90);
  });

  it('handles 0% discount', () => {
    expect(calculateDiscount(100, 0)).toBe(100);
  });

  it('handles 100% discount', () => {
    expect(calculateDiscount(100, 100)).toBe(0);
  });

  it('throws for negative discount', () => {
    expect(() => calculateDiscount(100, -1)).toThrow('Invalid discount');
  });

  it('throws for discount over 100', () => {
    expect(() => calculateDiscount(100, 101)).toThrow('Invalid discount');
  });
});
```

### What NOT to Focus On

```typescript
// ❌ Low-value coverage targets
// - Simple getters/setters
// - Type definitions
// - Constants
// - Framework boilerplate

// Don't obsess over covering this
class User {
  constructor(public readonly id: string, public name: string) {}

  // Simple getter - coverage not critical
  getId(): string {
    return this.id;
  }
}
```

## Coverage Thresholds

| Code Type | Recommended | Minimum |
|-----------|-------------|---------|
| **Core business logic** | 90-100% | 85% |
| **Utilities/helpers** | 85-95% | 80% |
| **API handlers** | 80-90% | 70% |
| **UI components** | 70-85% | 60% |
| **Integration code** | 60-80% | 50% |
| **Legacy code** | 40-60% | 30% |

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Coverage obsession | 100% doesn't mean bug-free | Focus on meaningful tests |
| Gaming metrics | Tests without assertions | Review test quality |
| Ignoring branches | High line, low branch | Test all conditions |
| Coverage drop | New code untested | Enforce patch coverage |

## Related Topics

- [Test Automation](./test-automation.md)
- [Flaky Tests](./flaky-tests.md)
- [Testing Principles](../fundamentals/testing-principles.md)
