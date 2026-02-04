# Unit Testing Patterns

Comprehensive guide for unit testing with Jest, Vitest, and TypeScript.

## Table of Contents

1. [Fundamentals](#fundamentals)
2. [Test Structure](#test-structure)
3. [Mocking Strategies](#mocking-strategies)
4. [Test Doubles](#test-doubles)
5. [Assertions](#assertions)
6. [Best Practices](#best-practices)

---

## Fundamentals

### FIRST Principles

| Principle | Description |
|-----------|-------------|
| **F**ast | Run in milliseconds |
| **I**ndependent | No dependencies between tests |
| **R**epeatable | Same result every time |
| **S**elf-validating | Pass or fail, no manual check |
| **T**imely | Written close to production code |

### What Makes a Good Unit Test

- Tests a single unit of behavior
- Independent of other tests
- Fast execution (milliseconds)
- Clear, descriptive name
- No external dependencies (mocked)

---

## Test Structure

### AAA Pattern (Arrange-Act-Assert)

```typescript
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
});
```

### Test Naming Conventions

```typescript
// Pattern: should [expected behavior] when [condition]
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

### Testing Edge Cases

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

  // Boundary conditions
  it('should return true for exactly 8 character valid password', () => {
    expect(validatePassword('Exact8!1')).toBe(true);
  });

  // Null/undefined handling
  it('should return false for null', () => {
    expect(validatePassword(null as any)).toBe(false);
  });

  it('should return false for undefined', () => {
    expect(validatePassword(undefined as any)).toBe(false);
  });
});
```

### Parameterized Tests

```typescript
describe('isValidEmail', () => {
  // Multiple valid inputs
  const validEmails = [
    'test@example.com',
    'user.name@domain.org',
    'user+tag@example.co.uk',
  ];

  it.each(validEmails)('should return true for valid email: %s', (email) => {
    expect(isValidEmail(email)).toBe(true);
  });

  // Invalid inputs with descriptions
  const invalidEmails = [
    ['', 'empty string'],
    ['invalid', 'missing @'],
    ['@domain.com', 'missing local part'],
    ['user@', 'missing domain'],
  ];

  it.each(invalidEmails)(
    'should return false for %s (%s)',
    (email) => {
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
    { amount: 500, customerType: 'vip', expected: 125 },
  ];

  it.each(testCases)(
    'should return $expected discount for $amount with $customerType customer',
    ({ amount, customerType, expected }) => {
      expect(calculateDiscount(amount, customerType)).toBe(expected);
    }
  );
});
```

---

## Mocking Strategies

### Types of Test Doubles

| Type | Purpose | Behavior |
|------|---------|----------|
| **Dummy** | Fill parameter lists | No implementation |
| **Stub** | Return canned answers | Predefined responses |
| **Spy** | Record interactions | Track calls + real behavior |
| **Mock** | Verify interactions | Assert on calls |
| **Fake** | Working implementation | Simplified version |

### Basic Mocking with Jest

```typescript
// Mocking a module
jest.mock('./email.service');

import { EmailService } from './email.service';
import { UserService } from './user.service';

describe('UserService', () => {
  let userService: UserService;
  let emailService: jest.Mocked<EmailService>;

  beforeEach(() => {
    emailService = new EmailService() as jest.Mocked<EmailService>;
    userService = new UserService(emailService);
  });

  it('should send welcome email on user creation', async () => {
    emailService.sendWelcomeEmail.mockResolvedValue(undefined);

    await userService.createUser({ email: 'test@test.com', name: 'Test' });

    expect(emailService.sendWelcomeEmail).toHaveBeenCalledWith('test@test.com');
  });
});
```

### Mocking Functions

```typescript
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('ApiClient', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should make GET request', async () => {
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    });

    const client = new ApiClient();
    const result = await client.get('/users');

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/users'),
      expect.objectContaining({ method: 'GET' })
    );
    expect(result).toEqual({ data: 'test' });
  });

  it('should throw on error response', async () => {
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    await expect(new ApiClient().get('/unknown'))
      .rejects
      .toThrow('Not Found');
  });
});
```

### Spying on Methods

```typescript
describe('Logger', () => {
  it('should call console.log with formatted message', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    const logger = new Logger();

    logger.info('Test message');

    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/\[INFO\].*Test message/)
    );

    consoleSpy.mockRestore();
  });
});
```

### Mocking Time

```typescript
describe('Scheduler', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should execute callback after delay', () => {
    const callback = jest.fn();
    const scheduler = new Scheduler();

    scheduler.scheduleAfter(1000, callback);

    expect(callback).not.toHaveBeenCalled();

    jest.advanceTimersByTime(1000);

    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should handle specific date', () => {
    jest.setSystemTime(new Date('2024-01-15'));

    const result = getNextMonthStart();

    expect(result).toEqual(new Date('2024-02-01'));
  });
});
```

### Mocking Promises

```typescript
describe('Async Operations', () => {
  // Resolved promise
  it('should handle success', async () => {
    mockService.fetch.mockResolvedValue({ data: 'success' });
    const result = await service.getData();
    expect(result.data).toBe('success');
  });

  // Rejected promise
  it('should handle error', async () => {
    mockService.fetch.mockRejectedValue(new Error('Network error'));
    await expect(service.getData()).rejects.toThrow('Network error');
  });

  // Sequential calls with different values
  it('should handle multiple calls', async () => {
    mockService.fetch
      .mockResolvedValueOnce({ data: 'first' })
      .mockResolvedValueOnce({ data: 'second' })
      .mockRejectedValueOnce(new Error('Third fails'));

    expect(await service.fetch()).toEqual({ data: 'first' });
    expect(await service.fetch()).toEqual({ data: 'second' });
    await expect(service.fetch()).rejects.toThrow();
  });
});
```

### Partial Mocking

```typescript
// Only mock specific methods
jest.mock('./user.repository', () => {
  const actual = jest.requireActual('./user.repository');
  return {
    ...actual,
    findByEmail: jest.fn(), // Only mock this method
  };
});
```

---

## Test Doubles

### Creating Mock Factories

```typescript
// test/factories/mock-repository.ts
export function createMockUserRepository(): jest.Mocked<UserRepository> {
  return {
    findById: jest.fn(),
    findByEmail: jest.fn(),
    save: jest.fn(),
    delete: jest.fn(),
    findAll: jest.fn(),
  };
}

// Usage
describe('UserService', () => {
  let mockRepo: jest.Mocked<UserRepository>;

  beforeEach(() => {
    mockRepo = createMockUserRepository();
  });

  it('should find user', async () => {
    mockRepo.findById.mockResolvedValue({ id: '1', name: 'John' });
    // ...
  });
});
```

### Fake Implementations

```typescript
// test/fakes/in-memory-user.repository.ts
export class InMemoryUserRepository implements UserRepository {
  private users: Map<string, User> = new Map();

  async save(user: User): Promise<void> {
    this.users.set(user.id, { ...user });
  }

  async findById(id: string): Promise<User | null> {
    return this.users.get(id) || null;
  }

  async findByEmail(email: string): Promise<User | null> {
    for (const user of this.users.values()) {
      if (user.email === email) return user;
    }
    return null;
  }

  async delete(id: string): Promise<void> {
    this.users.delete(id);
  }

  // Test helpers
  clear(): void {
    this.users.clear();
  }

  seed(users: User[]): void {
    users.forEach(u => this.users.set(u.id, u));
  }
}

// In tests
describe('UserService with fake repository', () => {
  let userService: UserService;
  let fakeRepository: InMemoryUserRepository;

  beforeEach(() => {
    fakeRepository = new InMemoryUserRepository();
    userService = new UserService(fakeRepository);
  });

  it('should create and retrieve user', async () => {
    const created = await userService.createUser({
      name: 'Test',
      email: 'test@test.com',
    });

    const found = await userService.getUser(created.id);

    expect(found).toEqual(created);
  });
});
```

### Test Data Factories

```typescript
// test/factories/user.factory.ts
export function createTestUser(overrides: Partial<User> = {}): User {
  return {
    id: 'test-id',
    name: 'Test User',
    email: 'test@example.com',
    createdAt: new Date('2024-01-01'),
    ...overrides,
  };
}

// In tests
it('should update user name', async () => {
  const user = createTestUser({ name: 'Old Name' });
  mockUserRepository.findById.mockResolvedValue(user);

  await userService.updateName('test-id', 'New Name');

  expect(mockUserRepository.save).toHaveBeenCalledWith(
    expect.objectContaining({ name: 'New Name' })
  );
});
```

---

## Assertions

### Common Jest Assertions

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

// Mock assertions
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith(arg1, arg2);
expect(mockFn).toHaveBeenLastCalledWith(arg);
```

### Custom Matchers

```typescript
// test/matchers/custom.ts
expect.extend({
  toBeValidEmail(received: string) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    const pass = emailRegex.test(received);
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be a valid email`
          : `expected ${received} to be a valid email`,
    };
  },
});

// Usage
expect('test@example.com').toBeValidEmail();
```

---

## Best Practices

### Do's and Don'ts

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

### Mock Cleanup Patterns

```typescript
describe('With Proper Cleanup', () => {
  const originalConsole = console.log;

  beforeEach(() => {
    jest.clearAllMocks();  // Clear call history
  });

  afterEach(() => {
    jest.restoreAllMocks();  // Restore spies
  });

  afterAll(() => {
    console.log = originalConsole;  // Manual restore
  });
});
```

### Don't Mock What You Don't Own

```typescript
// ❌ Bad - mocking third-party library directly
jest.mock('axios');

// ✅ Good - wrap in your own abstraction
export class HttpClient {
  async get<T>(url: string): Promise<T> {
    const response = await axios.get(url);
    return response.data;
  }
}

// Now mock your abstraction
jest.mock('./http-client');
```

### Test Isolation Techniques

```typescript
// Method 1: Fresh Instance Per Test
describe('Counter', () => {
  let counter: Counter;

  beforeEach(() => {
    counter = new Counter(); // Fresh instance
  });

  it('should start at 0', () => {
    expect(counter.value).toBe(0);
  });
});

// Method 2: Reset State
describe('Cache', () => {
  beforeEach(() => {
    Cache.clear(); // Reset singleton state
  });

  afterAll(() => {
    Cache.clear();
  });
});

// Method 3: Use Factories
const createTestUser = (overrides = {}) => ({
  id: '123',
  name: 'Test User',
  email: 'test@test.com',
  ...overrides,
});
```

---

## Summary

| Scenario | Approach |
|----------|----------|
| External API calls | Mock HttpClient wrapper |
| Database queries | Fake repository or mock |
| Time-dependent code | jest.useFakeTimers() |
| File system | Mock fs wrapper |
| Environment variables | jest.spyOn(process, 'env') |
| Third-party libraries | Wrap and mock wrapper |
| Event emitters | Mock emit function |
| Singletons | Reset between tests |
