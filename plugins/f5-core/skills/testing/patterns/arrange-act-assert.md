---
name: arrange-act-assert
description: The AAA pattern for structuring unit tests
category: testing/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Arrange-Act-Assert Pattern (AAA)

## Overview

The AAA pattern provides a clear structure for organizing test code
into three distinct phases, making tests easier to read, write, and maintain.

## The Three Phases

```
┌─────────────────────────────────────────────────────────┐
│                    AAA Pattern                           │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ARRANGE                                          │   │
│  │  - Set up test data                              │   │
│  │  - Configure mocks                               │   │
│  │  - Create dependencies                           │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ACT                                              │   │
│  │  - Execute the code under test                   │   │
│  │  - Usually ONE action                            │   │
│  └──────────────────────────────────────────────────┘   │
│                         ↓                               │
│  ┌──────────────────────────────────────────────────┐   │
│  │  ASSERT                                           │   │
│  │  - Verify expected outcomes                      │   │
│  │  - Check state changes                           │   │
│  │  - Validate interactions                         │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Basic Example

```typescript
describe('Calculator', () => {
  it('should add two numbers', () => {
    // Arrange
    const calculator = new Calculator();
    const a = 5;
    const b = 3;

    // Act
    const result = calculator.add(a, b);

    // Assert
    expect(result).toBe(8);
  });
});
```

## Detailed Examples

### Testing a Service

```typescript
describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with hashed password', async () => {
      // Arrange
      const mockUserRepository = {
        save: jest.fn().mockResolvedValue({ id: '123', name: 'John' }),
        findByEmail: jest.fn().mockResolvedValue(null),
      };
      const mockHashService = {
        hash: jest.fn().mockResolvedValue('hashed_password'),
      };
      const userService = new UserService(mockUserRepository, mockHashService);
      const userData = {
        name: 'John',
        email: 'john@test.com',
        password: 'plaintext_password',
      };

      // Act
      const result = await userService.createUser(userData);

      // Assert
      expect(result).toEqual({ id: '123', name: 'John' });
      expect(mockHashService.hash).toHaveBeenCalledWith('plaintext_password');
      expect(mockUserRepository.save).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'John',
          email: 'john@test.com',
          password: 'hashed_password',
        })
      );
    });
  });
});
```

### Testing Error Handling

```typescript
describe('OrderService', () => {
  describe('cancelOrder', () => {
    it('should throw error when order is already shipped', async () => {
      // Arrange
      const mockOrderRepository = {
        findById: jest.fn().mockResolvedValue({
          id: 'order-123',
          status: 'shipped',
        }),
      };
      const orderService = new OrderService(mockOrderRepository);

      // Act
      const cancelPromise = orderService.cancelOrder('order-123');

      // Assert
      await expect(cancelPromise).rejects.toThrow('Cannot cancel shipped order');
      expect(mockOrderRepository.findById).toHaveBeenCalledWith('order-123');
    });
  });
});
```

### Testing State Changes

```typescript
describe('ShoppingCart', () => {
  describe('addItem', () => {
    it('should add item and update total', () => {
      // Arrange
      const cart = new ShoppingCart();
      const item = { id: 'prod-1', name: 'Book', price: 29.99 };
      const initialItemCount = cart.items.length;
      const initialTotal = cart.total;

      // Act
      cart.addItem(item, 2);

      // Assert
      expect(cart.items.length).toBe(initialItemCount + 1);
      expect(cart.total).toBe(initialTotal + 59.98);
      expect(cart.items).toContainEqual(
        expect.objectContaining({
          id: 'prod-1',
          quantity: 2,
        })
      );
    });
  });
});
```

## Arrange Phase Best Practices

### Use Factories

```typescript
// ✅ Good: Use factories for test data
const user = createTestUser({ name: 'John', role: 'admin' });
const order = createTestOrder({ userId: user.id, items: 3 });

// ❌ Bad: Inline object creation
const user = {
  id: '123',
  name: 'John',
  email: 'john@test.com',
  role: 'admin',
  createdAt: new Date(),
  // ... many more fields
};
```

### Setup Mocks Clearly

```typescript
// ✅ Good: Clear mock setup
const mockRepository = createMockRepository();
mockRepository.findById.mockResolvedValue(testUser);
mockRepository.save.mockResolvedValue({ ...testUser, updatedAt: new Date() });

// ❌ Bad: Confusing inline mock
const service = new UserService({
  findById: jest.fn(() => Promise.resolve({ id: '1', name: 'Test' })),
  save: jest.fn(x => Promise.resolve(x)),
});
```

### Minimize Arrangement

```typescript
// ✅ Good: Only arrange what's needed
it('should validate email format', () => {
  // Arrange - only what we need
  const validator = new Validator();
  const invalidEmail = 'not-an-email';

  // Act
  const result = validator.isValidEmail(invalidEmail);

  // Assert
  expect(result).toBe(false);
});

// ❌ Bad: Over-arrangement
it('should validate email format', () => {
  // Arrange - unnecessary complexity
  const config = new Config({ strictMode: true, locale: 'en-US' });
  const logger = new Logger({ level: 'debug' });
  const validator = new Validator(config, logger);
  const userData = createFullUserProfile();
  const invalidEmail = 'not-an-email';
  // ...
});
```

## Act Phase Best Practices

### Single Action

```typescript
// ✅ Good: One clear action
it('should process payment', async () => {
  // Arrange
  const payment = createTestPayment();

  // Act
  const result = await paymentService.process(payment);

  // Assert
  expect(result.success).toBe(true);
});

// ❌ Bad: Multiple actions
it('should process and notify', async () => {
  // Arrange
  const payment = createTestPayment();

  // Act - too many actions!
  await paymentService.process(payment);
  await notificationService.send(payment.userId);
  await auditService.log('payment_processed');

  // Assert - what are we actually testing?
  expect(something).toBe(true);
});
```

### Store Result for Assertions

```typescript
// ✅ Good: Store result
const result = await service.calculate(input);
expect(result).toBe(expected);

// ❌ Bad: Inline in assertion
expect(await service.calculate(input)).toBe(expected);
```

## Assert Phase Best Practices

### Related Assertions Together

```typescript
// ✅ Good: Related assertions
it('should create order with correct details', async () => {
  // ... Arrange & Act ...

  // Assert - all about the created order
  expect(order.id).toBeDefined();
  expect(order.status).toBe('pending');
  expect(order.items).toHaveLength(2);
  expect(order.total).toBe(149.98);
});

// ❌ Bad: Unrelated assertions
it('should create order', async () => {
  // ... Arrange & Act ...

  // Assert - mixing concerns
  expect(order.id).toBeDefined();
  expect(mockLogger.log).toHaveBeenCalled(); // Different concern
  expect(cache.get('orders')).toContain(order); // Different concern
});
```

### Specific Assertions

```typescript
// ✅ Good: Specific assertions
expect(result.status).toBe('success');
expect(result.data.id).toBe('123');
expect(result.data.name).toBe('John');

// ❌ Bad: Vague assertions
expect(result).toBeTruthy();
expect(result.data).toBeDefined();
```

## With Setup and Teardown

```typescript
describe('DatabaseUserRepository', () => {
  let repository: DatabaseUserRepository;
  let testUser: User;

  beforeEach(async () => {
    // Shared Arrange
    repository = new DatabaseUserRepository(testDb);
    testUser = await repository.save(createTestUser());
  });

  afterEach(async () => {
    // Cleanup
    await testDb.clean();
  });

  it('should find user by id', async () => {
    // Arrange - minimal, use shared setup

    // Act
    const found = await repository.findById(testUser.id);

    // Assert
    expect(found).toEqual(testUser);
  });

  it('should update user', async () => {
    // Arrange - test-specific additions
    const updateData = { name: 'Updated Name' };

    // Act
    const updated = await repository.update(testUser.id, updateData);

    // Assert
    expect(updated.name).toBe('Updated Name');
    expect(updated.id).toBe(testUser.id);
  });
});
```

## Common Variations

### Act and Assert Together (for exceptions)

```typescript
it('should throw for invalid input', () => {
  // Arrange
  const calculator = new Calculator();

  // Act & Assert (combined for exceptions)
  expect(() => calculator.divide(10, 0)).toThrow('Division by zero');
});
```

### Multiple Assertions on Same Result

```typescript
it('should return complete user profile', async () => {
  // Arrange
  const userId = '123';

  // Act
  const profile = await userService.getProfile(userId);

  // Assert - multiple assertions on single result
  expect(profile).toMatchObject({
    id: '123',
    name: expect.any(String),
    email: expect.stringMatching(/@/),
    settings: expect.objectContaining({
      theme: expect.any(String),
    }),
  });
});
```

## Summary

| Phase | Purpose | Guidelines |
|-------|---------|------------|
| **Arrange** | Setup | Use factories, mock only what's needed |
| **Act** | Execute | Single action, store result |
| **Assert** | Verify | Specific, related assertions |

## Related Topics

- [Given-When-Then](./given-when-then.md)
- [Test Fixtures](./test-fixtures.md)
- [Factory Patterns](./factory-patterns.md)
