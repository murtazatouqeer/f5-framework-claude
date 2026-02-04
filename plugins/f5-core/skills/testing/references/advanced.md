# Advanced Testing Techniques

Property-based testing, mutation testing, contract testing, and chaos engineering.

## Table of Contents

1. [Property-Based Testing](#property-based-testing)
2. [Mutation Testing](#mutation-testing)
3. [Contract Testing](#contract-testing)
4. [Chaos Engineering](#chaos-engineering)

---

## Property-Based Testing

### Overview

Property-based testing generates random inputs to verify that properties always hold true.

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

| Aspect | Example-Based | Property-Based |
|--------|---------------|----------------|
| Coverage | Limited to examples | Explores edge cases |
| Discovery | Known scenarios | Finds unknown bugs |
| Maintenance | Update examples | Properties stable |

### Fast-Check Library

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

### Testing Math Operations

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
});
```

### Built-in Arbitraries

```typescript
// Primitives
fc.boolean()                              // true or false
fc.integer()                              // any integer
fc.integer({ min: 0, max: 100 })          // bounded integer
fc.float()                                // floating point
fc.string()                               // any string
fc.string({ maxLength: 10 })              // bounded string

// Arrays and objects
fc.array(fc.integer())                    // array of integers
fc.tuple(fc.integer(), fc.string())       // [number, string]
fc.record({ name: fc.string(), age: fc.nat() })

// Complex types
fc.option(fc.integer())                   // integer | undefined
fc.oneof(fc.integer(), fc.string())       // integer | string
fc.uuid()                                 // UUID format
```

### Custom Arbitraries

```typescript
// Email arbitrary
const emailArb = fc.tuple(
  fc.stringOf(fc.char().filter(c => /[a-z0-9]/.test(c)), { minLength: 1 }),
  fc.constantFrom('gmail.com', 'yahoo.com', 'example.com')
).map(([local, domain]) => `${local}@${domain}`);

// User arbitrary
const userArb: fc.Arbitrary<User> = fc.record({
  id: fc.uuid(),
  name: fc.string({ minLength: 1, maxLength: 50 }),
  email: emailArb,
  age: fc.integer({ min: 0, max: 150 }),
});
```

### Testing Sorting

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

---

## Mutation Testing

### Overview

Mutation testing evaluates test quality by introducing code changes and checking if tests catch them.

```
1. Original Code: if (a > b) return a;
                         ↓
2. Create Mutants:
   - if (a >= b) return a;  ← Mutation: > to >=
   - if (a < b) return a;   ← Mutation: > to <
   - if (a > b) return b;   ← Mutation: a to b
                         ↓
3. Run Tests:
   - Mutant 1: Tests FAIL → ✓ Killed
   - Mutant 2: Tests PASS → ✗ Survived
   - Mutant 3: Tests FAIL → ✓ Killed
                         ↓
4. Mutation Score = Killed/Total = 2/3 = 66.7%
```

### Mutation Operators

| Category | Original | Mutations |
|----------|----------|-----------|
| Arithmetic | `a + b` | `a - b`, `a * b`, `a / b` |
| Comparison | `a > b` | `a >= b`, `a < b`, `a <= b`, `a === b` |
| Logical | `a && b` | `a \|\| b` |
| Value | `true` | `false` |
| Return | `return x` | `return null` |

### Stryker Configuration

```javascript
// stryker.conf.js
module.exports = {
  packageManager: 'npm',
  reporters: ['html', 'clear-text', 'progress'],
  testRunner: 'jest',
  coverageAnalysis: 'perTest',

  checkers: ['typescript'],
  tsconfigFile: 'tsconfig.json',

  thresholds: {
    high: 80,
    low: 60,
    break: 50,
  },

  mutate: [
    'src/**/*.ts',
    '!src/**/*.spec.ts',
    '!src/**/*.test.ts',
  ],
};
```

### Improving Test Quality

```typescript
// ❌ Weak test - only tests happy path
describe('calculateDiscount', () => {
  it('should calculate discount', () => {
    expect(calculateDiscount(100, 10)).toBe(10);
  });
});

// Mutation testing reveals:
// Mutant SURVIVED: percentage < 0 → percentage <= 0
// Mutant SURVIVED: percentage > 100 → percentage >= 100

// ✅ Strong tests - kills boundary mutants
describe('calculateDiscount', () => {
  it('should calculate 10% discount', () => {
    expect(calculateDiscount(100, 10)).toBe(10);
  });

  it('should accept 0% discount', () => {
    expect(calculateDiscount(100, 0)).toBe(0);
  });

  it('should accept 100% discount', () => {
    expect(calculateDiscount(100, 100)).toBe(100);
  });

  it('should throw for negative percentage', () => {
    expect(() => calculateDiscount(100, -1)).toThrow('Invalid percentage');
  });

  it('should throw for percentage over 100', () => {
    expect(() => calculateDiscount(100, 101)).toThrow('Invalid percentage');
  });
});
```

### Killing Mutants

```typescript
// Condition mutation: a > b → a >= b
// To kill: test where a === b
it('should return false when values are equal', () => {
  expect(isGreater(5, 5)).toBe(false);
});

// Arithmetic mutation: a + b → a - b
// To kill: test where a ≠ b and verify result
it('should add correctly', () => {
  expect(add(3, 5)).toBe(8);  // 3 - 5 = -2 ≠ 8
});

// Logical mutation: a && b → a || b
// To kill: test where a is true and b is false
it('should require both conditions', () => {
  expect(validate(true, false)).toBe(false);
});
```

---

## Contract Testing

### Overview

Contract testing verifies service communication by testing against shared contracts.

```
Traditional Integration:
  Consumer ──────────▶ Provider
  Problems: Provider must be running, tests slow, flaky

Contract Testing:
  Consumer ──────▶ Contract ◀────── Provider
  Benefits: No provider needed, fast, reliable
```

### Consumer Side (Pact.js)

```typescript
import { PactV3, MatchersV3 } from '@pact-foundation/pact';

const { like, string, regex, uuid } = MatchersV3;

const provider = new PactV3({
  consumer: 'WebApp',
  provider: 'UserService',
});

describe('UserClient Contract', () => {
  it('should return user when exists', async () => {
    await provider
      .given('user with id 123 exists')
      .uponReceiving('a request for user 123')
      .withRequest({
        method: 'GET',
        path: '/users/123',
        headers: { Accept: 'application/json' },
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: like('123'),
          name: string('John Doe'),
          email: regex(/.*@.*/, 'john@example.com'),
        },
      });

    await provider.executeTest(async (mockServer) => {
      const client = new UserClient(mockServer.url);
      const user = await client.getUser('123');

      expect(user.id).toBe('123');
      expect(user.name).toBeDefined();
    });
  });
});
```

### Provider Verification

```typescript
import { Verifier } from '@pact-foundation/pact';

describe('UserService Contract Verification', () => {
  it('should validate contracts', async () => {
    const verifier = new Verifier({
      provider: 'UserService',
      providerBaseUrl: 'http://localhost:3001',
      pactUrls: ['./pacts/webapp-userservice.json'],

      stateHandlers: {
        'user with id 123 exists': async () => {
          await seedUser({ id: '123', name: 'John Doe' });
        },
        'user with id 999 does not exist': async () => {
          await clearUsers();
        },
      },
    });

    await verifier.verifyProvider();
  });
});
```

### Pact Matchers

```typescript
import { MatchersV3 } from '@pact-foundation/pact';

const {
  like,           // Matches type, not value
  eachLike,       // Array with matching elements
  integer,        // Integer type
  decimal,        // Decimal type
  string,         // String type
  regex,          // Matches regex pattern
  datetime,       // Date/time format
  uuid,           // UUID format
} = MatchersV3;

const userMatcher = {
  id: uuid(),
  name: string('John'),
  age: integer(25),
  email: regex(/^[\w-]+@[\w-]+\.\w+$/, 'test@example.com'),
  orders: eachLike({
    id: uuid(),
    total: decimal(99.99),
  }),
};
```

### Can-I-Deploy

```bash
# Check if safe to deploy consumer
pact-broker can-i-deploy \
  --pacticipant WebApp \
  --version $(git rev-parse HEAD) \
  --to-environment production

# Check if safe to deploy provider
pact-broker can-i-deploy \
  --pacticipant UserService \
  --version $(git rev-parse HEAD) \
  --to-environment production
```

---

## Chaos Engineering

### Principles

```
1. Define "steady state" (normal behavior metrics)
                 ↓
2. Hypothesize: "System maintains steady state when X fails"
                 ↓
3. Introduce failure (inject chaos)
                 ↓
4. Observe: Did steady state continue?
                 ↓
5. Learn and improve (fix vulnerabilities)
```

### Types of Chaos Experiments

| Category | Experiments |
|----------|-------------|
| **Network** | Latency, packet loss, DNS failure |
| **Resources** | CPU stress, memory pressure, disk full |
| **Application** | Process kill, dependency failure |
| **Infrastructure** | Node failure, zone outage |

### Network Chaos (Toxiproxy)

```typescript
import { Toxiproxy } from 'toxiproxy-node-client';

describe('Latency Resilience', () => {
  let proxy: any;

  beforeAll(async () => {
    const toxiproxy = new Toxiproxy('http://localhost:8474');
    proxy = await toxiproxy.createProxy({
      name: 'database',
      listen: '0.0.0.0:5433',
      upstream: 'postgres:5432',
    });
  });

  it('should handle database latency gracefully', async () => {
    // Add 500ms latency
    await proxy.addToxic({
      name: 'latency',
      type: 'latency',
      attributes: { latency: 500 },
    });

    const start = Date.now();
    const result = await userService.getUser('123');
    const duration = Date.now() - start;

    expect(result).toBeDefined();
    expect(duration).toBeGreaterThan(500);
    expect(duration).toBeLessThan(5000);

    await proxy.removeToxic('latency');
  });

  it('should timeout on extreme latency', async () => {
    await proxy.addToxic({
      name: 'extreme_latency',
      type: 'latency',
      attributes: { latency: 10000 },
    });

    await expect(userService.getUser('123')).rejects.toThrow('Timeout');

    await proxy.removeToxic('extreme_latency');
  });
});
```

### Dependency Failure

```typescript
describe('Dependency Failure Resilience', () => {
  it('should use circuit breaker on repeated failures', async () => {
    mockPaymentService.charge.mockRejectedValue(new Error('Service unavailable'));

    // First few calls should retry
    for (let i = 0; i < 5; i++) {
      await expect(orderService.processOrder(order)).rejects.toThrow();
    }

    // Circuit should be open - fail fast
    const start = Date.now();
    await expect(orderService.processOrder(order)).rejects.toThrow('Circuit open');
    const duration = Date.now() - start;

    expect(duration).toBeLessThan(100);  // Should fail immediately
  });

  it('should recover when dependency returns', async () => {
    await sleep(5000);  // Wait for circuit half-open

    mockPaymentService.charge.mockResolvedValue({ transactionId: 'txn-123' });

    const result = await orderService.processOrder(order);
    expect(result.status).toBe('completed');
  });
});
```

### Chaos Test Framework

```typescript
interface ChaosExperiment {
  name: string;
  description: string;
  steadyStateHypothesis: () => Promise<boolean>;
  method: () => Promise<void>;
  rollback: () => Promise<void>;
}

class ChaosRunner {
  async run(experiment: ChaosExperiment): Promise<ChaosResult> {
    // 1. Verify steady state before
    const steadyStateBefore = await experiment.steadyStateHypothesis();
    if (!steadyStateBefore) {
      throw new Error('System not in steady state');
    }

    try {
      // 2. Run chaos
      await experiment.method();

      // 3. Wait for stabilization
      await sleep(5000);

      // 4. Verify steady state after
      const steadyStateAfter = await experiment.steadyStateHypothesis();

      return { success: steadyStateAfter, experiment: experiment.name };
    } finally {
      // 5. Always rollback
      await experiment.rollback();
    }
  }
}
```

### Chaos Tools

| Tool | Type | Use Case |
|------|------|----------|
| **Chaos Monkey** | Random termination | Kill random instances |
| **Litmus** | Kubernetes | K8s-native experiments |
| **Toxiproxy** | Network proxy | Simulate network issues |
| **Gremlin** | Platform | Enterprise chaos |
| **Pumba** | Docker | Container chaos |

---

## Best Practices Summary

| Technique | When to Use | Benefit |
|-----------|-------------|---------|
| Property-Based | Algorithms, data transformations | Discovers edge cases |
| Mutation | Evaluating test quality | Improves test effectiveness |
| Contract | Microservices | Decouples service testing |
| Chaos | Resilience validation | Finds system weaknesses |

| Do | Don't |
|----|-------|
| Start chaos experiments small | Run in production first |
| Use property-based for invariants | Replace all example tests |
| Track mutation score trends | Expect 100% mutation score |
| Define steady state first | Skip hypothesis in chaos |
| Use Pact Broker for contracts | Store pacts in repo |
