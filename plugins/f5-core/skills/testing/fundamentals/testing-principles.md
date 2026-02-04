---
name: testing-principles
description: Core testing principles and best practices
category: testing/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Testing Principles

## Overview

Core principles that guide effective test design and implementation
across all types of tests.

## FIRST Principles

### F - Fast
Tests should run quickly to provide rapid feedback.

```typescript
// ❌ Slow: Real network call
it('should fetch user data', async () => {
  const user = await fetch('https://api.example.com/users/1');
  expect(user.name).toBe('John');
}, 30000); // 30 second timeout

// ✅ Fast: Mocked dependency
it('should fetch user data', async () => {
  mockApi.getUser.mockResolvedValue({ name: 'John' });
  const user = await userService.getUser('1');
  expect(user.name).toBe('John');
}); // Runs in milliseconds
```

### I - Independent
Tests should not depend on each other or external state.

```typescript
// ❌ Dependent: Relies on other test's state
describe('User tests', () => {
  let userId: string;

  it('should create user', async () => {
    const user = await createUser({ name: 'John' });
    userId = user.id; // Shared state!
  });

  it('should get user', async () => {
    const user = await getUser(userId); // Depends on previous test
    expect(user.name).toBe('John');
  });
});

// ✅ Independent: Each test sets up its own state
describe('User tests', () => {
  it('should create user', async () => {
    const user = await createUser({ name: 'John' });
    expect(user.id).toBeDefined();
  });

  it('should get user', async () => {
    // Arrange: Create own test data
    const created = await createUser({ name: 'John' });

    // Act
    const user = await getUser(created.id);

    // Assert
    expect(user.name).toBe('John');
  });
});
```

### R - Repeatable
Tests should produce the same result every time.

```typescript
// ❌ Non-repeatable: Depends on current time
it('should check if event is today', () => {
  const event = { date: new Date() };
  expect(isToday(event)).toBe(true); // Fails at midnight!
});

// ✅ Repeatable: Fixed time
it('should check if event is today', () => {
  jest.useFakeTimers();
  jest.setSystemTime(new Date('2024-06-15'));

  const event = { date: new Date('2024-06-15') };
  expect(isToday(event)).toBe(true);

  jest.useRealTimers();
});

// ❌ Non-repeatable: Random data without seed
it('should process items', () => {
  const items = generateRandomItems();
  const result = processItems(items);
  expect(result).toBeDefined(); // Different each run!
});

// ✅ Repeatable: Deterministic data
it('should process items', () => {
  const items = [
    { id: 1, value: 100 },
    { id: 2, value: 200 },
  ];
  const result = processItems(items);
  expect(result.total).toBe(300);
});
```

### S - Self-Validating
Tests should clearly pass or fail without manual inspection.

```typescript
// ❌ Not self-validating: Requires manual check
it('should generate report', () => {
  const report = generateReport(data);
  console.log(report); // Human must read this!
});

// ✅ Self-validating: Clear pass/fail
it('should generate report', () => {
  const report = generateReport(data);

  expect(report.title).toBe('Monthly Sales Report');
  expect(report.sections).toHaveLength(3);
  expect(report.totalRevenue).toBe(50000);
});
```

### T - Timely
Tests should be written at the appropriate time (preferably before code).

```typescript
// ❌ Untimely: Tests written after the fact
// Code already written, tests added to increase coverage
// Often miss edge cases and real requirements

// ✅ Timely: Tests written first (TDD)
// Tests drive the design
// All requirements are captured
// Edge cases considered upfront
```

## Right-BICEP

### Right: Are the Results Right?

```typescript
// Test that results are correct
it('should calculate order total correctly', () => {
  const order = createOrder([
    { product: 'A', price: 10, quantity: 2 },
    { product: 'B', price: 15, quantity: 1 },
  ]);

  expect(order.subtotal).toBe(35);
  expect(order.tax).toBe(3.50);
  expect(order.total).toBe(38.50);
});
```

### B - Boundary Conditions

```typescript
// Test boundaries and edge cases
describe('validateAge', () => {
  // Boundary: exactly at minimum
  it('should accept age 18 (minimum)', () => {
    expect(validateAge(18)).toBe(true);
  });

  // Boundary: just below minimum
  it('should reject age 17', () => {
    expect(validateAge(17)).toBe(false);
  });

  // Boundary: exactly at maximum
  it('should accept age 120 (maximum)', () => {
    expect(validateAge(120)).toBe(true);
  });

  // Boundary: just above maximum
  it('should reject age 121', () => {
    expect(validateAge(121)).toBe(false);
  });

  // Edge: zero
  it('should reject age 0', () => {
    expect(validateAge(0)).toBe(false);
  });

  // Edge: negative
  it('should reject negative age', () => {
    expect(validateAge(-1)).toBe(false);
  });
});
```

### I - Inverse Relationships

```typescript
// Test inverse operations
describe('Encryption', () => {
  it('should decrypt what was encrypted', () => {
    const original = 'secret message';
    const encrypted = encrypt(original, key);
    const decrypted = decrypt(encrypted, key);

    expect(decrypted).toBe(original);
  });
});

describe('Serialization', () => {
  it('should deserialize what was serialized', () => {
    const original = { name: 'John', age: 30 };
    const json = serialize(original);
    const restored = deserialize(json);

    expect(restored).toEqual(original);
  });
});
```

### C - Cross-Check Results

```typescript
// Verify using alternative calculation
it('should calculate average correctly', () => {
  const numbers = [10, 20, 30, 40, 50];

  // Primary calculation
  const average = calculateAverage(numbers);

  // Cross-check: manual calculation
  const sum = numbers.reduce((a, b) => a + b, 0);
  const expected = sum / numbers.length;

  expect(average).toBe(expected);
});
```

### E - Error Conditions

```typescript
describe('Error handling', () => {
  it('should throw on null input', () => {
    expect(() => processData(null)).toThrow('Input cannot be null');
  });

  it('should throw on empty array', () => {
    expect(() => calculateAverage([])).toThrow('Array cannot be empty');
  });

  it('should handle network failure gracefully', async () => {
    mockApi.fetch.mockRejectedValue(new Error('Network error'));

    const result = await fetchWithRetry('/api/data');

    expect(result.error).toBe('Network error');
    expect(result.data).toBeNull();
  });

  it('should validate input types', () => {
    expect(() => add('1', 2)).toThrow('Arguments must be numbers');
  });
});
```

### P - Performance Characteristics

```typescript
describe('Performance', () => {
  it('should complete within time limit', () => {
    const start = performance.now();

    processLargeDataset(generateData(10000));

    const duration = performance.now() - start;
    expect(duration).toBeLessThan(1000); // Under 1 second
  });

  it('should handle expected load', async () => {
    const results = await Promise.all(
      Array(100).fill(null).map(() => makeRequest())
    );

    expect(results.every(r => r.success)).toBe(true);
  });

  it('should have linear time complexity', () => {
    const time100 = measureTime(() => process(100));
    const time1000 = measureTime(() => process(1000));

    // Should be roughly 10x, not 100x
    expect(time1000 / time100).toBeLessThan(20);
  });
});
```

## Test Quality Principles

### Single Assertion Concept

```typescript
// ❌ Multiple unrelated assertions
it('should manage user', () => {
  const user = createUser({ name: 'John' });
  expect(user.id).toBeDefined();
  expect(user.createdAt).toBeDefined();

  updateUser(user.id, { name: 'Jane' });
  expect(getUser(user.id).name).toBe('Jane');

  deleteUser(user.id);
  expect(getUser(user.id)).toBeNull();
});

// ✅ One concept per test
it('should create user with generated id', () => {
  const user = createUser({ name: 'John' });
  expect(user.id).toBeDefined();
});

it('should set createdAt on creation', () => {
  const user = createUser({ name: 'John' });
  expect(user.createdAt).toBeInstanceOf(Date);
});

it('should update user name', () => {
  const user = createUser({ name: 'John' });
  updateUser(user.id, { name: 'Jane' });
  expect(getUser(user.id).name).toBe('Jane');
});
```

### Test Behavior, Not Implementation

```typescript
// ❌ Testing implementation details
it('should call repository save method', () => {
  userService.createUser({ name: 'John' });
  expect(mockRepository.save).toHaveBeenCalled();
});

// ✅ Testing behavior
it('should persist new user', () => {
  const user = userService.createUser({ name: 'John' });
  const found = userService.getUser(user.id);
  expect(found.name).toBe('John');
});
```

### Avoid Test Logic

```typescript
// ❌ Logic in tests
it('should process items', () => {
  const items = [1, 2, 3, 4, 5];
  let expected = 0;
  for (const item of items) {
    if (item % 2 === 0) {
      expected += item;
    }
  }
  expect(sumEvenNumbers(items)).toBe(expected);
});

// ✅ Explicit expected values
it('should sum even numbers', () => {
  const items = [1, 2, 3, 4, 5];
  expect(sumEvenNumbers(items)).toBe(6); // 2 + 4
});
```

## Test Naming Conventions

### Pattern: `should_ExpectedBehavior_When_StateUnderTest`

```typescript
// Clear, descriptive names
describe('PasswordValidator', () => {
  it('should_returnTrue_when_passwordMeetsAllRequirements', () => {});
  it('should_returnFalse_when_passwordTooShort', () => {});
  it('should_returnFalse_when_passwordMissingUppercase', () => {});
  it('should_returnFalse_when_passwordMissingNumber', () => {});
  it('should_returnFalse_when_passwordMissingSpecialChar', () => {});
  it('should_throwError_when_passwordIsNull', () => {});
});
```

### Pattern: `given_When_Then`

```typescript
describe('OrderService', () => {
  it('given_validOrder_when_submitted_then_shouldCreateOrder', () => {});
  it('given_emptyCart_when_checkout_then_shouldThrowError', () => {});
  it('given_insufficientStock_when_orderPlaced_then_shouldReject', () => {});
});
```

## Summary Table

| Principle | Description | Key Question |
|-----------|-------------|--------------|
| Fast | Tests run quickly | Can I run all tests in < 1 min? |
| Independent | No dependencies between tests | Does order matter? |
| Repeatable | Same result every run | Any randomness or time dependency? |
| Self-validating | Clear pass/fail | Is manual inspection needed? |
| Timely | Written at right time | Were tests written before code? |
| Right | Results are correct | Do tests verify requirements? |
| Boundary | Edge cases covered | What are the limits? |
| Inverse | Verify with inverse ops | Can I undo and verify? |
| Cross-check | Alternative verification | Is there another way to verify? |
| Error | Failure cases tested | What can go wrong? |
| Performance | Meets requirements | Is it fast enough? |

## Related Topics

- [Test-Driven Development](./test-driven-development.md)
- [Arrange-Act-Assert Pattern](../patterns/arrange-act-assert.md)
- [Mocking Strategies](../unit-testing/mocking-strategies.md)
