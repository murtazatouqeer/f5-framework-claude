---
name: test-doubles
description: Understanding and using different types of test doubles
category: testing/unit-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Test Doubles

## Overview

Test doubles are objects that stand in for real dependencies during testing.
The term comes from "stunt doubles" in movies - they look like the real thing
but are designed for specific testing scenarios.

## Types of Test Doubles

```
┌─────────────────────────────────────────────────────────────┐
│                    Test Doubles Spectrum                     │
├──────────┬──────────┬──────────┬──────────┬────────────────┤
│  Dummy   │   Stub   │   Spy    │   Mock   │     Fake       │
├──────────┼──────────┼──────────┼──────────┼────────────────┤
│ No logic │ Canned   │ Record   │ Verify   │ Working        │
│ Fill     │ answers  │ calls +  │ expected │ simplified     │
│ params   │          │ optional │ behavior │ implementation │
│          │          │ real     │          │                │
└──────────┴──────────┴──────────┴──────────┴────────────────┘
```

## Dummy Objects

**Purpose**: Fill required parameters without being used.

```typescript
// Dummy: Never actually used, just satisfies type requirements
interface Logger {
  log(message: string): void;
  error(message: string): void;
}

// Dummy logger for tests that don't care about logging
const dummyLogger: Logger = {
  log: () => {},
  error: () => {},
};

// Usage
describe('Calculator', () => {
  it('should add numbers', () => {
    // Logger is required but not relevant to this test
    const calculator = new Calculator(dummyLogger);
    expect(calculator.add(2, 3)).toBe(5);
  });
});
```

## Stubs

**Purpose**: Return predetermined values for specific inputs.

```typescript
// Stub: Returns canned answers
interface PriceService {
  getPrice(productId: string): Promise<number>;
}

// Stub with fixed responses
const priceServiceStub: PriceService = {
  getPrice: async (productId: string) => {
    const prices: Record<string, number> = {
      'PROD-001': 99.99,
      'PROD-002': 149.99,
      'PROD-003': 199.99,
    };
    return prices[productId] ?? 0;
  },
};

// Usage
describe('OrderCalculator', () => {
  it('should calculate order total with stub prices', async () => {
    const calculator = new OrderCalculator(priceServiceStub);

    const total = await calculator.calculateTotal([
      { productId: 'PROD-001', quantity: 2 },
      { productId: 'PROD-002', quantity: 1 },
    ]);

    expect(total).toBe(349.97); // (99.99 * 2) + 149.99
  });
});
```

### Stub Variations

```typescript
// Stub that throws error
const errorStub: PriceService = {
  getPrice: async () => {
    throw new Error('Service unavailable');
  },
};

// Stub that delays response
const slowStub: PriceService = {
  getPrice: async (productId: string) => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    return 99.99;
  },
};

// Stub with conditional behavior
const conditionalStub: PriceService = {
  getPrice: async (productId: string) => {
    if (productId.startsWith('PREMIUM')) {
      return 999.99;
    }
    return 99.99;
  },
};
```

## Spies

**Purpose**: Record information about calls while optionally calling real implementation.

```typescript
// Spy: Wraps real object and records interactions
interface EmailService {
  send(to: string, subject: string, body: string): Promise<void>;
}

class EmailServiceSpy implements EmailService {
  public calls: Array<{ to: string; subject: string; body: string }> = [];
  private realService?: EmailService;

  constructor(realService?: EmailService) {
    this.realService = realService;
  }

  async send(to: string, subject: string, body: string): Promise<void> {
    // Record the call
    this.calls.push({ to, subject, body });

    // Optionally call real implementation
    if (this.realService) {
      await this.realService.send(to, subject, body);
    }
  }

  // Spy helper methods
  get callCount(): number {
    return this.calls.length;
  }

  wasCalledWith(to: string): boolean {
    return this.calls.some(call => call.to === to);
  }

  getLastCall() {
    return this.calls[this.calls.length - 1];
  }

  reset(): void {
    this.calls = [];
  }
}

// Usage
describe('NotificationService', () => {
  let emailSpy: EmailServiceSpy;
  let notificationService: NotificationService;

  beforeEach(() => {
    emailSpy = new EmailServiceSpy();
    notificationService = new NotificationService(emailSpy);
  });

  it('should send notification email', async () => {
    await notificationService.notifyUser('user@test.com', 'Hello!');

    expect(emailSpy.callCount).toBe(1);
    expect(emailSpy.wasCalledWith('user@test.com')).toBe(true);
    expect(emailSpy.getLastCall()?.subject).toBe('Notification');
  });
});
```

### Jest Spies

```typescript
// Using jest.spyOn
describe('Logger', () => {
  it('should format and log message', () => {
    const logger = new Logger();
    const consoleSpy = jest.spyOn(console, 'log');

    logger.info('Test message');

    expect(consoleSpy).toHaveBeenCalledTimes(1);
    expect(consoleSpy).toHaveBeenCalledWith(
      expect.stringContaining('Test message')
    );

    consoleSpy.mockRestore();
  });
});

// Spy with mock implementation
describe('FileService', () => {
  it('should read file content', () => {
    const readFileSpy = jest.spyOn(fs, 'readFileSync')
      .mockReturnValue('file content');

    const service = new FileService();
    const content = service.read('/path/to/file');

    expect(readFileSpy).toHaveBeenCalledWith('/path/to/file', 'utf8');
    expect(content).toBe('file content');

    readFileSpy.mockRestore();
  });
});
```

## Mocks

**Purpose**: Pre-programmed with expectations, verify interactions happened as expected.

```typescript
// Mock: Verifies expected interactions occurred
interface PaymentGateway {
  charge(amount: number, cardToken: string): Promise<{ transactionId: string }>;
  refund(transactionId: string): Promise<void>;
}

// Using Jest mock
describe('PaymentService', () => {
  let mockGateway: jest.Mocked<PaymentGateway>;
  let paymentService: PaymentService;

  beforeEach(() => {
    mockGateway = {
      charge: jest.fn(),
      refund: jest.fn(),
    };
    paymentService = new PaymentService(mockGateway);
  });

  it('should process payment through gateway', async () => {
    // Setup expectation
    mockGateway.charge.mockResolvedValue({ transactionId: 'TXN-123' });

    // Act
    await paymentService.processPayment(100, 'card_token_abc');

    // Verify mock was called correctly
    expect(mockGateway.charge).toHaveBeenCalledWith(100, 'card_token_abc');
    expect(mockGateway.charge).toHaveBeenCalledTimes(1);
  });

  it('should refund failed orders', async () => {
    mockGateway.charge.mockResolvedValue({ transactionId: 'TXN-456' });
    mockGateway.refund.mockResolvedValue(undefined);

    await paymentService.processPayment(100, 'card_token');
    await paymentService.refundLastPayment();

    // Verify sequence of calls
    expect(mockGateway.charge).toHaveBeenCalledBefore(mockGateway.refund);
    expect(mockGateway.refund).toHaveBeenCalledWith('TXN-456');
  });
});
```

### Mock Verification Patterns

```typescript
describe('Mock Verifications', () => {
  it('should verify call count', () => {
    expect(mock.method).toHaveBeenCalledTimes(3);
    expect(mock.method).toHaveBeenCalled();
    expect(mock.method).not.toHaveBeenCalled();
  });

  it('should verify call arguments', () => {
    expect(mock.method).toHaveBeenCalledWith('arg1', 'arg2');
    expect(mock.method).toHaveBeenCalledWith(
      expect.objectContaining({ id: '123' })
    );
    expect(mock.method).toHaveBeenCalledWith(
      expect.any(String),
      expect.any(Number)
    );
  });

  it('should verify call order', () => {
    expect(mock.first).toHaveBeenCalledBefore(mock.second);
    expect(mock.second).toHaveBeenCalledAfter(mock.first);
  });

  it('should verify last call', () => {
    expect(mock.method).toHaveBeenLastCalledWith('final', 'args');
  });

  it('should verify nth call', () => {
    expect(mock.method).toHaveBeenNthCalledWith(1, 'first', 'call');
    expect(mock.method).toHaveBeenNthCalledWith(2, 'second', 'call');
  });
});
```

## Fakes

**Purpose**: Working implementation with shortcuts suitable for testing.

```typescript
// Fake: Simplified but working implementation
interface UserRepository {
  save(user: User): Promise<void>;
  findById(id: string): Promise<User | null>;
  findByEmail(email: string): Promise<User | null>;
  findAll(): Promise<User[]>;
  delete(id: string): Promise<void>;
}

// Fake in-memory implementation
class FakeUserRepository implements UserRepository {
  private users: Map<string, User> = new Map();

  async save(user: User): Promise<void> {
    this.users.set(user.id, { ...user });
  }

  async findById(id: string): Promise<User | null> {
    return this.users.get(id) ?? null;
  }

  async findByEmail(email: string): Promise<User | null> {
    for (const user of this.users.values()) {
      if (user.email.toLowerCase() === email.toLowerCase()) {
        return user;
      }
    }
    return null;
  }

  async findAll(): Promise<User[]> {
    return Array.from(this.users.values());
  }

  async delete(id: string): Promise<void> {
    this.users.delete(id);
  }

  // Test helpers
  seed(users: User[]): void {
    users.forEach(u => this.users.set(u.id, u));
  }

  clear(): void {
    this.users.clear();
  }

  size(): number {
    return this.users.size;
  }
}

// Usage
describe('UserService with Fake', () => {
  let fakeRepo: FakeUserRepository;
  let userService: UserService;

  beforeEach(() => {
    fakeRepo = new FakeUserRepository();
    userService = new UserService(fakeRepo);
  });

  it('should create and find user', async () => {
    const user = await userService.createUser({
      name: 'John',
      email: 'john@test.com',
    });

    const found = await userService.findByEmail('john@test.com');

    expect(found).toEqual(user);
  });

  it('should list all users', async () => {
    // Seed test data
    fakeRepo.seed([
      { id: '1', name: 'Alice', email: 'alice@test.com' },
      { id: '2', name: 'Bob', email: 'bob@test.com' },
    ]);

    const users = await userService.listUsers();

    expect(users).toHaveLength(2);
  });
});
```

### Common Fakes

```typescript
// Fake HTTP client
class FakeHttpClient implements HttpClient {
  private responses: Map<string, any> = new Map();

  setResponse(url: string, response: any): void {
    this.responses.set(url, response);
  }

  async get<T>(url: string): Promise<T> {
    if (this.responses.has(url)) {
      return this.responses.get(url);
    }
    throw new Error(`No fake response for: ${url}`);
  }
}

// Fake event bus
class FakeEventBus implements EventBus {
  private events: Array<{ event: string; payload: any }> = [];

  emit(event: string, payload: any): void {
    this.events.push({ event, payload });
  }

  getEmitted(): Array<{ event: string; payload: any }> {
    return [...this.events];
  }

  hasEmitted(event: string): boolean {
    return this.events.some(e => e.event === event);
  }
}

// Fake clock
class FakeClock implements Clock {
  private currentTime: Date;

  constructor(initialTime: Date = new Date()) {
    this.currentTime = initialTime;
  }

  now(): Date {
    return new Date(this.currentTime);
  }

  advance(ms: number): void {
    this.currentTime = new Date(this.currentTime.getTime() + ms);
  }

  setTime(date: Date): void {
    this.currentTime = date;
  }
}
```

## Choosing the Right Test Double

| Scenario | Recommended Double |
|----------|-------------------|
| Need to satisfy type | Dummy |
| Control indirect inputs | Stub |
| Verify something was called | Spy |
| Verify call arguments/order | Mock |
| Need realistic behavior | Fake |
| Testing error handling | Stub (throw) |
| Testing state changes | Fake |
| Testing side effects | Mock/Spy |

## Decision Flow

```
Need to verify how code interacts with dependency?
├── YES: Need to verify calls were made correctly?
│   ├── YES: Use MOCK
│   └── NO: Just record calls? Use SPY
└── NO: Need to control what dependency returns?
    ├── YES: Complex logic needed?
    │   ├── YES: Use FAKE
    │   └── NO: Use STUB
    └── NO: Use DUMMY
```

## Best Practices

| Do | Don't |
|----|-------|
| Use simplest double that works | Over-engineer test doubles |
| Create reusable test doubles | Duplicate test double code |
| Name doubles clearly | Use generic names |
| Reset between tests | Let state leak |
| Verify only important calls | Verify every interaction |
| Use fakes for complex logic | Mock everything |

## Related Topics

- [Mocking Strategies](./mocking-strategies.md)
- [Factory Patterns](../patterns/factory-patterns.md)
- [Testing Principles](../fundamentals/testing-principles.md)
