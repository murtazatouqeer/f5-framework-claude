---
name: mutation-testing
description: Mutation testing to evaluate test suite effectiveness
category: testing/advanced
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Mutation Testing

## Overview

Mutation testing evaluates the quality of your test suite by introducing
small changes (mutations) to your code and checking if tests catch them.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    Mutation Testing Process                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Original Code                                              │
│   ┌────────────────────────────┐                               │
│   │ if (a > b) return a;       │                               │
│   └────────────────────────────┘                               │
│                   ↓                                              │
│   2. Create Mutants                                             │
│   ┌────────────────────────────┐                               │
│   │ if (a >= b) return a;      │  ← Mutation: > to >=          │
│   │ if (a < b) return a;       │  ← Mutation: > to <           │
│   │ if (a > b) return b;       │  ← Mutation: a to b           │
│   └────────────────────────────┘                               │
│                   ↓                                              │
│   3. Run Tests Against Mutants                                  │
│   ┌────────────────────────────┐                               │
│   │ Mutant 1: Tests FAIL → ✓ Killed                           │
│   │ Mutant 2: Tests PASS → ✗ Survived                         │
│   │ Mutant 3: Tests FAIL → ✓ Killed                           │
│   └────────────────────────────┘                               │
│                   ↓                                              │
│   4. Calculate Mutation Score                                   │
│   Score = Killed / Total = 2/3 = 66.7%                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Mutation Operators

### Arithmetic Operators

| Original | Mutation |
|----------|----------|
| `a + b` | `a - b`, `a * b`, `a / b` |
| `a - b` | `a + b`, `a * b`, `a / b` |
| `a * b` | `a + b`, `a - b`, `a / b` |
| `a / b` | `a + b`, `a - b`, `a * b` |

### Comparison Operators

| Original | Mutation |
|----------|----------|
| `a > b` | `a >= b`, `a < b`, `a <= b`, `a === b` |
| `a >= b` | `a > b`, `a < b`, `a <= b`, `a === b` |
| `a < b` | `a > b`, `a >= b`, `a <= b`, `a === b` |
| `a === b` | `a !== b` |

### Logical Operators

| Original | Mutation |
|----------|----------|
| `a && b` | `a \|\| b` |
| `a \|\| b` | `a && b` |
| `!a` | `a` |

### Value Mutations

| Original | Mutation |
|----------|----------|
| `true` | `false` |
| `0` | `1`, `-1` |
| `"string"` | `""` |
| `return x` | `return null` |

## Using Stryker (JavaScript/TypeScript)

### Installation

```bash
npm install --save-dev @stryker-mutator/core @stryker-mutator/typescript-checker @stryker-mutator/jest-runner
```

### Configuration

```javascript
// stryker.conf.js
module.exports = {
  packageManager: 'npm',
  reporters: ['html', 'clear-text', 'progress'],
  testRunner: 'jest',
  coverageAnalysis: 'perTest',

  mutator: {
    plugins: ['@stryker-mutator/typescript-checker'],
  },

  checkers: ['typescript'],
  tsconfigFile: 'tsconfig.json',

  jest: {
    configFile: 'jest.config.js',
    enableFindRelatedTests: true,
  },

  // Thresholds
  thresholds: {
    high: 80,
    low: 60,
    break: 50,
  },

  // Exclude files
  mutate: [
    'src/**/*.ts',
    '!src/**/*.spec.ts',
    '!src/**/*.test.ts',
    '!src/**/__tests__/**',
  ],
};
```

### Running

```bash
# Run mutation testing
npx stryker run

# Run with specific files
npx stryker run --files "src/utils/**/*.ts"

# Run in incremental mode (faster)
npx stryker run --incremental
```

## Interpreting Results

### Mutation States

| State | Meaning | Action |
|-------|---------|--------|
| **Killed** | Tests detected mutation | Good - tests are effective |
| **Survived** | Tests didn't detect | Add/improve tests |
| **No Coverage** | No tests cover this code | Add tests |
| **Timeout** | Tests timed out | Usually killed |
| **Compile Error** | Mutation broke compilation | Usually equivalent |

### Example Report

```
Mutant killed: src/calculator.ts:10:5
  - Replaced > with >= in add function

Mutant SURVIVED: src/validator.ts:25:3
  - Replaced && with || in validate function
  - Tests did not detect this change!

Mutant SURVIVED: src/utils.ts:42:10
  - Removed return statement
  - Missing test for this code path
```

## Improving Test Quality

### Before: Weak Tests

```typescript
// calculator.ts
function calculateDiscount(price: number, percentage: number): number {
  if (percentage < 0 || percentage > 100) {
    throw new Error('Invalid percentage');
  }
  return price * (percentage / 100);
}

// Weak test - only tests happy path
describe('calculateDiscount', () => {
  it('should calculate discount', () => {
    expect(calculateDiscount(100, 10)).toBe(10);
  });
});

// Mutation testing reveals:
// Mutant SURVIVED: percentage < 0 → percentage <= 0
// Mutant SURVIVED: percentage > 100 → percentage >= 100
// Mutant SURVIVED: return price * ... → return 0
```

### After: Strong Tests

```typescript
describe('calculateDiscount', () => {
  // Happy path
  it('should calculate 10% discount', () => {
    expect(calculateDiscount(100, 10)).toBe(10);
  });

  // Boundary tests (kill boundary mutants)
  it('should accept 0% discount', () => {
    expect(calculateDiscount(100, 0)).toBe(0);
  });

  it('should accept 100% discount', () => {
    expect(calculateDiscount(100, 100)).toBe(100);
  });

  // Error cases (kill condition mutants)
  it('should throw for negative percentage', () => {
    expect(() => calculateDiscount(100, -1)).toThrow('Invalid percentage');
  });

  it('should throw for percentage over 100', () => {
    expect(() => calculateDiscount(100, 101)).toThrow('Invalid percentage');
  });

  // Different values (kill arithmetic mutants)
  it('should calculate 50% discount correctly', () => {
    expect(calculateDiscount(200, 50)).toBe(100);
  });

  it('should handle decimal prices', () => {
    expect(calculateDiscount(99.99, 10)).toBeCloseTo(9.999);
  });
});
```

## Strategies for Surviving Mutants

### Condition Mutations

```typescript
// Mutant: a > b → a >= b
// To kill: test where a === b

it('should return false when values are equal', () => {
  expect(isGreater(5, 5)).toBe(false);  // Kills >= mutant
});
```

### Arithmetic Mutations

```typescript
// Mutant: a + b → a - b
// To kill: test where a ≠ b and check result

it('should add correctly', () => {
  expect(add(3, 5)).toBe(8);   // 3 - 5 = -2 ≠ 8, kills mutant
});
```

### Logical Mutations

```typescript
// Mutant: a && b → a || b
// To kill: test where a is true and b is false

it('should require both conditions', () => {
  expect(validate(true, false)).toBe(false);  // Kills || mutant
});
```

### Return Value Mutations

```typescript
// Mutant: return result → return null
// To kill: verify return value is not null/undefined

it('should return the calculated value', () => {
  const result = calculate(10);
  expect(result).not.toBeNull();
  expect(result).toBe(20);
});
```

## Equivalent Mutants

Some mutants are equivalent (behavior same as original):

```typescript
// Original
function max(a: number, b: number): number {
  if (a > b) return a;
  return b;
}

// Equivalent mutant - same behavior
function max(a: number, b: number): number {
  if (a >= b) return a;  // When a === b, returning a or b is same
  return b;
}
```

## CI Integration

```yaml
# .github/workflows/mutation.yml
name: Mutation Testing

on:
  pull_request:
    branches: [main]

jobs:
  mutation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Run mutation tests
        run: npx stryker run

      - name: Upload mutation report
        uses: actions/upload-artifact@v3
        with:
          name: mutation-report
          path: reports/mutation/

      - name: Check mutation score
        run: |
          SCORE=$(cat reports/mutation/mutation.json | jq '.mutationScore')
          if (( $(echo "$SCORE < 70" | bc -l) )); then
            echo "Mutation score $SCORE% is below threshold"
            exit 1
          fi
```

## Best Practices

| Do | Don't |
|----|-------|
| Run on CI for PRs | Run on every commit |
| Focus on critical code | Mutate everything |
| Investigate survivors | Ignore survived mutants |
| Set realistic thresholds | Expect 100% score |
| Use incremental mode | Run full suite always |

## Related Topics

- [Testing Principles](../fundamentals/testing-principles.md)
- [Property-Based Testing](./property-based-testing.md)
- [Coverage Reporting](../ci-cd/coverage-reporting.md)
