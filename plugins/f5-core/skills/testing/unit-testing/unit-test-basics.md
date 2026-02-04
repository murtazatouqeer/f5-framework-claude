---
name: unit-test-basics
description: Unit testing fundamentals and best practices
category: testing/unit-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Unit Testing Basics

## What is a Unit Test?

A unit test verifies a small, isolated piece of code (a "unit")
behaves as expected. Units are typically functions, methods, or classes.

## Characteristics of Good Unit Tests

### FIRST Principles

| Principle | Description |
|-----------|-------------|
| **F**ast | Run in milliseconds |
| **I**ndependent | No dependencies between tests |
| **R**epeatable | Same result every time |
| **S**elf-validating | Pass or fail, no manual check |
| **T**imely | Written close to production code |

## Basic Structure (AAA Pattern)

```typescript
// user.service.test.ts
import { UserService } from './user.service';
import { UserRepository } from './user.repository';

describe('UserService', () => {
  let userService: UserService;
  let mockUserRepository: jest.Mocked<UserRepository>;

  beforeEach(() => {
    // Arrange - Setup
    mockUserRepository = {
      findById: jest.fn(),
      save: jest.fn(),
      delete: jest.fn(),
    };
    userService = new UserService(mockUserRepository);
  });

  describe('getUser', () => {
    it('should return user when found', async () => {
      // Arrange
      const expectedUser = { id: '1', name: 'John', email: 'john@test.com' };
      mockUserRepository.findById.mockResolvedValue(expectedUser);

      // Act
      const result = await userService.getUser('1');

      // Assert
      expect(result).toEqual(expectedUser);
      expect(mockUserRepository.findById).toHaveBeenCalledWith('1');
      expect(mockUserRepository.findById).toHaveBeenCalledTimes(1);
    });

    it('should throw error when user not found', async () => {
      // Arrange
      mockUserRepository.findById.mockResolvedValue(null);

      // Act & Assert
      await expect(userService.getUser('999'))
        .rejects
        .toThrow('User not found');
    });
  });

  describe('createUser', () => {
    it('should create user with valid data', async () => {
      // Arrange
      const userData = { name: 'Jane', email: 'jane@test.com' };
      const createdUser = { id: '2', ...userData };
      mockUserRepository.save.mockResolvedValue(createdUser);

      // Act
      const result = await userService.createUser(userData);

      // Assert
      expect(result).toEqual(createdUser);
      expect(mockUserRepository.save).toHaveBeenCalledWith(
        expect.objectContaining(userData)
      );
    });

    it('should throw error for invalid email', async () => {
      // Arrange
      const userData = { name: 'Jane', email: 'invalid-email' };

      // Act & Assert
      await expect(userService.createUser(userData))
        .rejects
        .toThrow('Invalid email format');
    });
  });
});
```

## Naming Conventions

### Pattern: `should_ExpectedBehavior_When_StateUnderTest`

```typescript
describe('Calculator', () => {
  describe('add', () => {
    it('should return sum when adding two positive numbers', () => {});
    it('should return negative when sum is negative', () => {});
    it('should throw error when input is not a number', () => {});
  });

  describe('divide', () => {
    it('should return quotient when dividing valid numbers', () => {});
    it('should throw error when dividing by zero', () => {});
  });
});
```

## Testing Edge Cases

```typescript
describe('validatePassword', () => {
  // Happy path
  it('should return true for valid password', () => {
    expect(validatePassword('SecurePass123!')).toBe(true);
  });

  // Edge cases
  it('should return false for empty string', () => {
    expect(validatePassword('')).toBe(false);
  });

  it('should return false for password shorter than 8 chars', () => {
    expect(validatePassword('Short1!')).toBe(false);
  });

  it('should return false for password without uppercase', () => {
    expect(validatePassword('lowercase123!')).toBe(false);
  });

  it('should return false for password without number', () => {
    expect(validatePassword('NoNumbers!')).toBe(false);
  });

  it('should return false for password without special char', () => {
    expect(validatePassword('NoSpecial123')).toBe(false);
  });

  // Boundary conditions
  it('should return true for exactly 8 character valid password', () => {
    expect(validatePassword('Exact8!1')).toBe(true);
  });

  it('should handle unicode characters', () => {
    expect(validatePassword('Pässwörd123!')).toBe(true);
  });

  // Null/undefined
  it('should return false for null', () => {
    expect(validatePassword(null as any)).toBe(false);
  });

  it('should return false for undefined', () => {
    expect(validatePassword(undefined as any)).toBe(false);
  });
});
```

## Test Organization

```typescript
// Group related tests
describe('OrderService', () => {
  // Setup shared across all tests
  let orderService: OrderService;

  beforeAll(() => {
    // Run once before all tests
  });

  beforeEach(() => {
    // Run before each test
    orderService = new OrderService();
  });

  afterEach(() => {
    // Cleanup after each test
    jest.clearAllMocks();
  });

  afterAll(() => {
    // Run once after all tests
  });

  // Group by method
  describe('createOrder', () => {
    describe('with valid input', () => {
      it('should create order', () => {});
      it('should calculate total correctly', () => {});
    });

    describe('with invalid input', () => {
      it('should throw for empty items', () => {});
      it('should throw for negative quantity', () => {});
    });
  });

  describe('cancelOrder', () => {
    it('should cancel pending order', () => {});
    it('should throw for shipped order', () => {});
  });
});
```

## Parameterized Tests

```typescript
describe('isValidEmail', () => {
  // Test multiple inputs with same expected result
  const validEmails = [
    'test@example.com',
    'user.name@domain.org',
    'user+tag@example.co.uk',
  ];

  it.each(validEmails)('should return true for valid email: %s', (email) => {
    expect(isValidEmail(email)).toBe(true);
  });

  const invalidEmails = [
    ['', 'empty string'],
    ['invalid', 'missing @'],
    ['@domain.com', 'missing local part'],
    ['user@', 'missing domain'],
  ];

  it.each(invalidEmails)(
    'should return false for %s (%s)',
    (email, description) => {
      expect(isValidEmail(email)).toBe(false);
    }
  );
});

// Table-driven tests
describe('calculateDiscount', () => {
  const testCases = [
    { amount: 100, customerType: 'regular', expected: 0 },
    { amount: 100, customerType: 'premium', expected: 10 },
    { amount: 100, customerType: 'vip', expected: 20 },
    { amount: 500, customerType: 'vip', expected: 125 }, // 25% for large orders
  ];

  it.each(testCases)(
    'should return $expected discount for $amount with $customerType customer',
    ({ amount, customerType, expected }) => {
      expect(calculateDiscount(amount, customerType)).toBe(expected);
    }
  );
});
```

## Test Isolation Techniques

### Method 1: Fresh Instance Per Test

```typescript
describe('Counter', () => {
  let counter: Counter;

  beforeEach(() => {
    counter = new Counter(); // Fresh instance
  });

  it('should start at 0', () => {
    expect(counter.value).toBe(0);
  });

  it('should increment', () => {
    counter.increment();
    expect(counter.value).toBe(1);
  });
});
```

### Method 2: Reset State

```typescript
describe('Cache', () => {
  beforeEach(() => {
    Cache.clear(); // Reset singleton state
  });

  afterAll(() => {
    Cache.clear();
  });

  it('should cache value', () => {
    Cache.set('key', 'value');
    expect(Cache.get('key')).toBe('value');
  });
});
```

### Method 3: Use Factories

```typescript
const createTestUser = (overrides = {}) => ({
  id: '123',
  name: 'Test User',
  email: 'test@test.com',
  ...overrides,
});

it('should update user name', () => {
  const user = createTestUser({ name: 'Original' });
  // Test with fresh data each time
});
```

## Common Assertions

```typescript
// Equality
expect(result).toBe(expected);           // Strict equality
expect(result).toEqual(expected);        // Deep equality
expect(result).toStrictEqual(expected);  // Deep + type equality

// Truthiness
expect(result).toBeTruthy();
expect(result).toBeFalsy();
expect(result).toBeNull();
expect(result).toBeUndefined();
expect(result).toBeDefined();

// Numbers
expect(result).toBeGreaterThan(5);
expect(result).toBeGreaterThanOrEqual(5);
expect(result).toBeLessThan(10);
expect(result).toBeCloseTo(0.3, 5); // Floating point

// Strings
expect(result).toMatch(/pattern/);
expect(result).toContain('substring');
expect(result).toHaveLength(5);

// Arrays
expect(array).toContain(item);
expect(array).toContainEqual({ id: 1 });
expect(array).toHaveLength(3);

// Objects
expect(object).toHaveProperty('key');
expect(object).toHaveProperty('key', 'value');
expect(object).toMatchObject({ partial: 'match' });

// Exceptions
expect(() => fn()).toThrow();
expect(() => fn()).toThrow('message');
expect(() => fn()).toThrow(ErrorType);

// Async
await expect(promise).resolves.toBe(value);
await expect(promise).rejects.toThrow('error');
```

## Best Practices Summary

| Do | Don't |
|----|-------|
| Test behavior, not implementation | Test private methods directly |
| One concept per test | Multiple unrelated assertions |
| Use descriptive test names | Use generic names like "test1" |
| Keep tests independent | Share state between tests |
| Test edge cases | Only test happy paths |
| Use test factories | Duplicate setup code |
| Mock external dependencies | Mock everything |
| Run tests frequently | Run tests only before commit |

## Related Topics

- [Mocking Strategies](./mocking-strategies.md)
- [Test Doubles](./test-doubles.md)
- [Assertion Patterns](./assertion-patterns.md)
- [Arrange-Act-Assert Pattern](../patterns/arrange-act-assert.md)
