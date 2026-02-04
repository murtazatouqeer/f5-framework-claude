---
name: code-coverage
description: Code coverage metrics and configuration
category: code-quality/static-analysis
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Code Coverage

## Overview

Code coverage measures how much of your code is executed during tests. It helps identify untested code paths and improve test quality.

## Coverage Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Line Coverage | % of lines executed | > 80% |
| Branch Coverage | % of if/else branches covered | > 75% |
| Function Coverage | % of functions called | > 90% |
| Statement Coverage | % of statements executed | > 80% |

## Jest Configuration

### jest.config.js

```javascript
/** @type {import('jest').Config} */
export default {
  preset: 'ts-jest',
  testEnvironment: 'node',
  
  // Coverage configuration
  collectCoverage: false, // Enable with --coverage flag
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.test.{ts,tsx}',
    '!src/**/*.spec.{ts,tsx}',
    '!src/**/index.ts',
    '!src/types/**',
    '!src/mocks/**',
  ],
  
  coverageDirectory: 'coverage',
  coverageReporters: [
    'text',           // Console output
    'text-summary',   // Summary in console
    'lcov',           // For SonarQube/CodeClimate
    'html',           // HTML report
    'json-summary',   // JSON summary
  ],
  
  coverageThreshold: {
    global: {
      branches: 75,
      functions: 80,
      lines: 80,
      statements: 80,
    },
    // Per-file thresholds
    './src/services/**/*.ts': {
      branches: 90,
      functions: 90,
      lines: 90,
      statements: 90,
    },
    // Ignore coverage for specific patterns
    './src/utils/logger.ts': {
      branches: 0,
      functions: 0,
      lines: 0,
      statements: 0,
    },
  },
  
  // Other options
  testMatch: ['**/*.test.ts', '**/*.spec.ts'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
};
```

## Vitest Configuration

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8', // or 'istanbul'
      reporter: ['text', 'json', 'html', 'lcov'],
      reportsDirectory: './coverage',
      
      include: ['src/**/*.{ts,tsx}'],
      exclude: [
        'node_modules',
        'src/**/*.d.ts',
        'src/**/*.test.{ts,tsx}',
        'src/**/*.spec.{ts,tsx}',
        'src/types/**',
        'src/mocks/**',
      ],
      
      thresholds: {
        lines: 80,
        branches: 75,
        functions: 80,
        statements: 80,
      },
      
      // Fail if coverage drops below thresholds
      thresholdAutoUpdate: false,
      
      // Coverage for all files, not just imported ones
      all: true,
    },
  },
});
```

## NYC (Istanbul) Configuration

### .nycrc.json

```json
{
  "extends": "@istanbuljs/nyc-config-typescript",
  "all": true,
  "include": ["src/**/*.ts"],
  "exclude": [
    "**/*.d.ts",
    "**/*.test.ts",
    "**/*.spec.ts",
    "**/node_modules/**",
    "**/coverage/**"
  ],
  "reporter": ["text", "lcov", "html"],
  "report-dir": "coverage",
  "temp-dir": ".nyc_output",
  "check-coverage": true,
  "branches": 75,
  "lines": 80,
  "functions": 80,
  "statements": 80,
  "watermarks": {
    "lines": [70, 90],
    "functions": [70, 90],
    "branches": [70, 90],
    "statements": [70, 90]
  }
}
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/coverage.yml
name: Coverage

on: [push, pull_request]

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
        run: npm run test:coverage
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true
      
      - name: Check coverage thresholds
        run: |
          COVERAGE=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage $COVERAGE% is below 80% threshold"
            exit 1
          fi
```

### Coverage Badge

```markdown
<!-- README.md -->
[![codecov](https://codecov.io/gh/username/repo/branch/main/graph/badge.svg)](https://codecov.io/gh/username/repo)
```

## Package.json Scripts

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:coverage:ci": "jest --coverage --ci --reporters=default --reporters=jest-junit",
    "coverage:report": "open coverage/lcov-report/index.html"
  }
}
```

## Understanding Coverage Reports

### Line Coverage

```typescript
function example(x: number) {
  if (x > 0) {        // Line covered
    return x * 2;      // Line covered (branch 1)
  }
  return 0;            // Line NOT covered (branch 2)
}

// Test only covers x > 0 case
test('positive number', () => {
  expect(example(5)).toBe(10); // Only branch 1 tested
});
```

### Branch Coverage

```typescript
function classify(score: number): string {
  if (score >= 90) {           // Branch 1
    return 'A';
  } else if (score >= 80) {    // Branch 2
    return 'B';
  } else if (score >= 70) {    // Branch 3
    return 'C';
  }
  return 'F';                   // Branch 4
}

// 100% branch coverage requires tests for all 4 branches
describe('classify', () => {
  test('A grade', () => expect(classify(95)).toBe('A'));
  test('B grade', () => expect(classify(85)).toBe('B'));
  test('C grade', () => expect(classify(75)).toBe('C'));
  test('F grade', () => expect(classify(50)).toBe('F'));
});
```

## Improving Coverage

### Strategies

1. **Write tests for uncovered branches**
   - Check coverage report for red lines
   - Add tests for edge cases

2. **Test error paths**
   ```typescript
   test('handles errors', async () => {
     mockApi.mockRejectedValue(new Error('Network error'));
     await expect(fetchData()).rejects.toThrow('Network error');
   });
   ```

3. **Test boundary conditions**
   ```typescript
   test('boundary values', () => {
     expect(isAdult(17)).toBe(false);
     expect(isAdult(18)).toBe(true);
     expect(isAdult(19)).toBe(true);
   });
   ```

### What NOT to Do

```typescript
// ❌ Don't write tests just for coverage
test('useless coverage test', () => {
  const result = complexFunction(1, 2, 3);
  expect(result).toBeDefined(); // Doesn't verify correctness
});

// ✅ Write meaningful assertions
test('calculates total with tax', () => {
  const result = calculateTotal(100, 0.1);
  expect(result).toBe(110);
});
```

## Coverage Exclusions

### Istanbul Comments

```typescript
/* istanbul ignore next */
function debugOnly() {
  // Not covered - debugging utility
}

/* istanbul ignore if */
if (process.env.NODE_ENV === 'development') {
  // Development-only code
}

/* istanbul ignore else */
if (config.feature) {
  // Feature code
} else {
  // Fallback - ignored
}
```

### Coverage Ignore Patterns

```javascript
// jest.config.js
{
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.generated.ts',  // Generated files
    '!src/scripts/**',          // Build scripts
    '!src/types/**',            // Type definitions
  ]
}
```

## Quality Targets by Project Type

| Project Type | Line | Branch | Function |
|--------------|------|--------|----------|
| Library | 90% | 85% | 95% |
| API Service | 80% | 75% | 85% |
| Frontend App | 70% | 65% | 75% |
| Scripts/Tools | 60% | 50% | 70% |
