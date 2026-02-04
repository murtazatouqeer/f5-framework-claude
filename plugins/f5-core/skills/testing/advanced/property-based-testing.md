---
name: property-based-testing
description: Property-based testing for discovering edge cases
category: testing/advanced
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Property-Based Testing

## Overview

Property-based testing generates random inputs to verify that certain
properties always hold true, rather than testing specific examples.

## Traditional vs Property-Based

```
Traditional Testing:
  Input: [1, 2, 3]     → Output: 6  ✓
  Input: [0, 0, 0]     → Output: 0  ✓
  Input: [-1, 1]       → Output: 0  ✓

Property-Based Testing:
  Property: "sum of array equals sum of reversed array"
  Generator: Random arrays of integers
  Runs: 100+ random tests automatically
  Result: Property holds ✓ or counterexample found ✗
```

## Benefits

| Aspect | Example-Based | Property-Based |
|--------|---------------|----------------|
| Coverage | Limited to examples | Explores edge cases |
| Discovery | Known scenarios | Finds unknown bugs |
| Maintenance | Update examples | Properties stable |
| Documentation | Shows examples | Describes behavior |

## Fast-Check Library (JavaScript/TypeScript)

### Basic Example

```typescript
import fc from 'fast-check';

describe('Array.reverse', () => {
  it('should reverse twice to get original', () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer()),
        (arr) => {
          const reversed = [...arr].reverse().reverse();
          return JSON.stringify(arr) === JSON.stringify(reversed);
        }
      )
    );
  });

  it('should preserve length', () => {
    fc.assert(
      fc.property(
        fc.array(fc.anything()),
        (arr) => arr.length === [...arr].reverse().length
      )
    );
  });
});
```

### Testing Math Functions

```typescript
describe('Math operations', () => {
  it('addition should be commutative', () => {
    fc.assert(
      fc.property(
        fc.integer(),
        fc.integer(),
        (a, b) => a + b === b + a
      )
    );
  });

  it('addition should be associative', () => {
    fc.assert(
      fc.property(
        fc.integer(),
        fc.integer(),
        fc.integer(),
        (a, b, c) => (a + b) + c === a + (b + c)
      )
    );
  });

  it('multiplication distributes over addition', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: -1000, max: 1000 }),
        fc.integer({ min: -1000, max: 1000 }),
        fc.integer({ min: -1000, max: 1000 }),
        (a, b, c) => a * (b + c) === a * b + a * c
      )
    );
  });
});
```

### Testing String Functions

```typescript
describe('String operations', () => {
  it('concatenation length equals sum of lengths', () => {
    fc.assert(
      fc.property(
        fc.string(),
        fc.string(),
        (a, b) => (a + b).length === a.length + b.length
      )
    );
  });

  it('trim should remove leading/trailing whitespace', () => {
    fc.assert(
      fc.property(
        fc.string(),
        (s) => {
          const trimmed = s.trim();
          return !trimmed.startsWith(' ') && !trimmed.endsWith(' ');
        }
      )
    );
  });

  it('split and join should be inverse (for single char)', () => {
    fc.assert(
      fc.property(
        fc.string(),
        fc.char(),
        (str, sep) => {
          // Only for strings not containing the separator
          if (str.includes(sep)) return true;
          return str.split(sep).join(sep) === str;
        }
      )
    );
  });
});
```

## Arbitraries (Generators)

### Built-in Arbitraries

```typescript
// Primitives
fc.boolean()           // true or false
fc.integer()           // any integer
fc.integer({ min: 0, max: 100 })  // bounded integer
fc.nat()               // natural number (>= 0)
fc.float()             // floating point
fc.string()            // any string
fc.string({ maxLength: 10 })  // bounded string
fc.char()              // single character

// Arrays and objects
fc.array(fc.integer())            // array of integers
fc.array(fc.string(), { minLength: 1, maxLength: 5 })
fc.tuple(fc.integer(), fc.string())  // [number, string]
fc.record({ name: fc.string(), age: fc.nat() })

// Complex types
fc.option(fc.integer())           // integer | undefined
fc.oneof(fc.integer(), fc.string())  // integer | string
fc.constant('fixed')              // always 'fixed'
fc.constantFrom('a', 'b', 'c')    // one of the values
```

### Custom Arbitraries

```typescript
// Email arbitrary
const emailArb = fc.tuple(
  fc.stringOf(fc.char().filter(c => /[a-z0-9]/.test(c)), { minLength: 1 }),
  fc.constantFrom('gmail.com', 'yahoo.com', 'example.com')
).map(([local, domain]) => `${local}@${domain}`);

// User arbitrary
interface User {
  id: string;
  name: string;
  email: string;
  age: number;
}

const userArb: fc.Arbitrary<User> = fc.record({
  id: fc.uuid(),
  name: fc.string({ minLength: 1, maxLength: 50 }),
  email: emailArb,
  age: fc.integer({ min: 0, max: 150 }),
});

// Money arbitrary (avoiding floating point issues)
const moneyArb = fc.integer({ min: 0, max: 1000000 }).map(cents => ({
  cents,
  dollars: cents / 100,
  formatted: `$${(cents / 100).toFixed(2)}`,
}));
```

### Filtered and Mapped Arbitraries

```typescript
// Filter: only even numbers
const evenNumberArb = fc.integer().filter(n => n % 2 === 0);

// Map: transform generated values
const positiveArb = fc.integer().map(n => Math.abs(n) + 1);

// Chain: generate dependent values
const rangeArb = fc.integer({ min: 0, max: 100 }).chain(min =>
  fc.integer({ min, max: 100 }).map(max => ({ min, max }))
);
```

## Testing Real-World Functions

### JSON Serialization

```typescript
describe('JSON serialization', () => {
  it('should be reversible', () => {
    fc.assert(
      fc.property(
        fc.jsonValue(),
        (value) => {
          const serialized = JSON.stringify(value);
          const deserialized = JSON.parse(serialized);
          return JSON.stringify(deserialized) === serialized;
        }
      )
    );
  });
});
```

### Sorting

```typescript
describe('sort function', () => {
  it('should produce sorted output', () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer()),
        (arr) => {
          const sorted = [...arr].sort((a, b) => a - b);
          return sorted.every((val, i) =>
            i === 0 || sorted[i - 1] <= val
          );
        }
      )
    );
  });

  it('should preserve elements', () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer()),
        (arr) => {
          const sorted = [...arr].sort((a, b) => a - b);
          return arr.length === sorted.length &&
            arr.every(x => sorted.includes(x));
        }
      )
    );
  });

  it('should be idempotent', () => {
    fc.assert(
      fc.property(
        fc.array(fc.integer()),
        (arr) => {
          const sorted1 = [...arr].sort((a, b) => a - b);
          const sorted2 = [...sorted1].sort((a, b) => a - b);
          return JSON.stringify(sorted1) === JSON.stringify(sorted2);
        }
      )
    );
  });
});
```

### Encoding/Decoding

```typescript
describe('Base64 encoding', () => {
  it('should be reversible', () => {
    fc.assert(
      fc.property(
        fc.string(),
        (str) => {
          const encoded = Buffer.from(str).toString('base64');
          const decoded = Buffer.from(encoded, 'base64').toString();
          return decoded === str;
        }
      )
    );
  });
});

describe('URL encoding', () => {
  it('should be reversible', () => {
    fc.assert(
      fc.property(
        fc.string(),
        (str) => {
          const encoded = encodeURIComponent(str);
          const decoded = decodeURIComponent(encoded);
          return decoded === str;
        }
      )
    );
  });
});
```

## Finding Bugs

```typescript
// Buggy function
function divide(a: number, b: number): number {
  return a / b;  // Bug: doesn't handle b === 0
}

describe('divide function', () => {
  it('should handle all inputs', () => {
    fc.assert(
      fc.property(
        fc.float(),
        fc.float(),
        (a, b) => {
          const result = divide(a, b);
          return !Number.isNaN(result) || b === 0;
        }
      )
    );
    // fast-check will find counterexample where b === 0
  });
});

// Shrinking example
// fast-check automatically finds minimal counterexample:
// Instead of: divide(3.14159, 0) fails
// Shrinks to: divide(0, 0) fails
```

## Model-Based Testing

```typescript
// Test against a simple model
describe('Stack', () => {
  it('should behave like array model', () => {
    fc.assert(
      fc.property(
        fc.array(fc.oneof(
          fc.record({ type: fc.constant('push'), value: fc.integer() }),
          fc.record({ type: fc.constant('pop') })
        )),
        (operations) => {
          const stack = new Stack<number>();
          const model: number[] = [];

          for (const op of operations) {
            if (op.type === 'push') {
              stack.push(op.value);
              model.push(op.value);
            } else {
              const stackResult = stack.pop();
              const modelResult = model.pop();
              if (stackResult !== modelResult) return false;
            }
          }

          return stack.size() === model.length;
        }
      )
    );
  });
});
```

## Configuration

```typescript
// Custom number of runs
fc.assert(
  fc.property(fc.integer(), (n) => true),
  { numRuns: 1000 }  // Default is 100
);

// Seed for reproducibility
fc.assert(
  fc.property(fc.integer(), (n) => true),
  { seed: 42 }
);

// Verbose output
fc.assert(
  fc.property(fc.integer(), (n) => true),
  { verbose: true }
);

// Example reporting
fc.assert(
  fc.property(fc.integer(), (n) => true),
  { examples: [[0], [1], [-1], [Number.MAX_SAFE_INTEGER]] }
);
```

## Best Practices

| Do | Don't |
|----|-------|
| Test properties, not examples | Test specific values |
| Use meaningful property names | Use generic assertions |
| Start with simple arbitraries | Over-constrain generators |
| Reproduce failures with seeds | Ignore shrunk examples |
| Combine with example tests | Replace all example tests |

## Related Topics

- [Testing Principles](../fundamentals/testing-principles.md)
- [Unit Test Basics](../unit-testing/unit-test-basics.md)
- [Mutation Testing](./mutation-testing.md)
