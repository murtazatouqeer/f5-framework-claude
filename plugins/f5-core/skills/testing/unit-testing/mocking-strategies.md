---
name: mocking-strategies
description: Effective mocking strategies for isolated testing
category: testing/unit-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Mocking Strategies

## Types of Test Doubles

| Type | Purpose | Behavior |
|------|---------|----------|
| **Dummy** | Fill parameter lists | No implementation |
| **Stub** | Return canned answers | Predefined responses |
| **Spy** | Record interactions | Track calls + real behavior |
| **Mock** | Verify interactions | Assert on calls |
| **Fake** | Working implementation | Simplified version |

## Mocking in Jest/TypeScript

### Basic Mocking

```typescript
// Mocking a module
jest.mock('./email.service');

import { EmailService } from './email.service';
import { UserService } from './user.service';

describe('UserService', () => {
  let userService: UserService;
  let emailService: jest.Mocked<EmailService>;

  beforeEach(() => {
    // Get mocked instance
    emailService = new EmailService() as jest.Mocked<EmailService>;
    userService = new UserService(emailService);
  });

  it('should send welcome email on user creation', async () => {
    // Arrange
    emailService.sendWelcomeEmail.mockResolvedValue(undefined);

    // Act
    await userService.createUser({ email: 'test@test.com', name: 'Test' });

    // Assert
    expect(emailService.sendWelcomeEmail).toHaveBeenCalledWith('test@test.com');
  });
});
```

### Mocking Functions

```typescript
// Mock implementation
const mockFetch = jest.fn();
global.fetch = mockFetch;

describe('ApiClient', () => {
  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should make GET request', async () => {
    // Arrange
    mockFetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ data: 'test' }),
    });

    // Act
    const client = new ApiClient();
    const result = await client.get('/users');

    // Assert
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/users'),
      expect.objectContaining({ method: 'GET' })
    );
    expect(result).toEqual({ data: 'test' });
  });

  it('should throw on error response', async () => {
    // Arrange
    mockFetch.mockResolvedValue({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    // Act & Assert
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
    // Arrange
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation();
    const logger = new Logger();

    // Act
    logger.info('Test message');

    // Assert
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringMatching(/\[INFO\].*Test message/)
    );

    // Cleanup
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
    // Arrange
    const callback = jest.fn();
    const scheduler = new Scheduler();

    // Act
    scheduler.scheduleAfter(1000, callback);

    // Assert - callback not called yet
    expect(callback).not.toHaveBeenCalled();

    // Fast-forward time
    jest.advanceTimersByTime(1000);

    // Assert - callback called
    expect(callback).toHaveBeenCalledTimes(1);
  });

  it('should handle specific date', () => {
    // Set specific date
    jest.setSystemTime(new Date('2024-01-15'));

    const result = getNextMonthStart();

    expect(result).toEqual(new Date('2024-02-01'));
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
    // Only mock this method
    findByEmail: jest.fn(),
  };
});
```

## Mocking Different Scenarios

### Mocking Classes

```typescript
// Creating a typed mock class
function createMockUserRepository(): jest.Mocked<UserRepository> {
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

### Mocking Event Emitters

```typescript
describe('EventHandler', () => {
  it('should emit event on action', () => {
    const mockEmit = jest.fn();
    const handler = new EventHandler({ emit: mockEmit });

    handler.performAction();

    expect(mockEmit).toHaveBeenCalledWith('action:completed', {
      timestamp: expect.any(Number),
    });
  });
});
```

## Best Practices

### Don't Mock What You Don't Own

```typescript
// ❌ Bad - mocking third-party library directly
jest.mock('axios');

// ✅ Good - wrap in your own abstraction
// http-client.ts
export class HttpClient {
  async get<T>(url: string): Promise<T> {
    const response = await axios.get(url);
    return response.data;
  }
}

// Now mock your abstraction
jest.mock('./http-client');
```

### Mock at the Right Level

```typescript
// ❌ Too low level - mocking database driver
jest.mock('pg');

// ✅ Right level - mock repository interface
const mockUserRepository: UserRepository = {
  findById: jest.fn(),
  save: jest.fn(),
};
```

### Use Factories for Test Data

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

### Verify Important Interactions

```typescript
// ✅ Verify critical calls
it('should audit log user deletion', async () => {
  await userService.deleteUser('123');

  expect(mockAuditLog.log).toHaveBeenCalledWith({
    action: 'USER_DELETED',
    userId: '123',
    timestamp: expect.any(Date),
  });
});

// ❌ Don't over-verify
it('should get user', async () => {
  const result = await userService.getUser('123');

  // Too many verifications - testing implementation
  expect(mockRepo.findById).toHaveBeenCalledTimes(1);
  expect(mockRepo.findById).toHaveBeenCalledWith('123');
  expect(mockCache.get).toHaveBeenCalled();
  expect(mockLogger.debug).toHaveBeenCalled();
  // ...
});
```

## Fakes for Complex Dependencies

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

  // Test helper methods
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

## Mock Cleanup Patterns

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

  it('test 1', () => {
    // Fresh mocks for each test
  });

  it('test 2', () => {
    // No pollution from test 1
  });
});
```

## Summary Table

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

## Related Topics

- [Test Doubles](./test-doubles.md)
- [Factory Patterns](../patterns/factory-patterns.md)
- [Unit Test Basics](./unit-test-basics.md)
