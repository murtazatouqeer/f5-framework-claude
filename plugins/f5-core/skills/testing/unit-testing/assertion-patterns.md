---
name: assertion-patterns
description: Effective assertion patterns and best practices
category: testing/unit-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Assertion Patterns

## Overview

Assertions are the verification step in tests. Good assertions clearly
communicate intent and provide helpful failure messages.

## Basic Assertions

### Equality Assertions

```typescript
// Primitive equality (same value and type)
expect(result).toBe(5);
expect(name).toBe('John');
expect(isValid).toBe(true);

// Object/Array deep equality
expect(user).toEqual({ id: 1, name: 'John' });
expect(items).toEqual([1, 2, 3]);

// Strict equality (includes undefined properties)
expect(obj).toStrictEqual({ a: 1, b: undefined });

// Reference equality
expect(obj1).toBe(obj2); // Same reference
expect(obj1).toEqual(obj2); // Same content
```

### Truthiness Assertions

```typescript
// Truthy/Falsy
expect(value).toBeTruthy();
expect(value).toBeFalsy();

// Null/Undefined
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();

// Specific boolean
expect(isValid).toBe(true);
expect(isDeleted).toBe(false);
```

### Numeric Assertions

```typescript
// Comparisons
expect(count).toBeGreaterThan(5);
expect(count).toBeGreaterThanOrEqual(5);
expect(count).toBeLessThan(10);
expect(count).toBeLessThanOrEqual(10);

// Range
expect(value).toBeGreaterThanOrEqual(0);
expect(value).toBeLessThanOrEqual(100);

// Floating point (avoid precision issues)
expect(0.1 + 0.2).toBeCloseTo(0.3);
expect(pi).toBeCloseTo(3.14159, 5); // 5 decimal places

// NaN and Infinity
expect(result).toBeNaN();
expect(Number.POSITIVE_INFINITY).toBe(Infinity);
```

### String Assertions

```typescript
// Contains
expect(message).toContain('error');

// Match pattern
expect(email).toMatch(/^[\w-]+@[\w-]+\.\w+$/);
expect(uuid).toMatch(
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
);

// Length
expect(password).toHaveLength(8);

// Starts/Ends with (using match)
expect(path).toMatch(/^\/api/);
expect(filename).toMatch(/\.json$/);
```

### Array Assertions

```typescript
// Contains element
expect(array).toContain(5);
expect(array).toContainEqual({ id: 1 }); // Deep equality

// Length
expect(items).toHaveLength(3);

// Empty
expect(results).toHaveLength(0);
expect(results).toEqual([]);

// Contains all elements (any order)
expect(array).toEqual(expect.arrayContaining([1, 2, 3]));

// Exact elements in order
expect(array).toEqual([1, 2, 3]);
```

### Object Assertions

```typescript
// Has property
expect(user).toHaveProperty('name');
expect(user).toHaveProperty('name', 'John');
expect(user).toHaveProperty('address.city', 'NYC');

// Partial match
expect(user).toMatchObject({
  name: 'John',
  email: 'john@test.com',
});

// Contains keys
expect(Object.keys(user)).toEqual(
  expect.arrayContaining(['id', 'name', 'email'])
);
```

## Advanced Assertion Patterns

### expect.any() and expect.anything()

```typescript
// Match any value of type
expect(response).toEqual({
  id: expect.any(String),
  createdAt: expect.any(Date),
  count: expect.any(Number),
  data: expect.anything(), // Any non-null value
});

// Match any function call
expect(callback).toHaveBeenCalledWith(
  expect.any(String),
  expect.any(Object)
);
```

### expect.objectContaining()

```typescript
// Partial object matching
expect(user).toEqual(
  expect.objectContaining({
    name: 'John',
    email: expect.stringContaining('@'),
  })
);

// Nested matching
expect(response).toEqual({
  status: 200,
  body: expect.objectContaining({
    user: expect.objectContaining({
      id: expect.any(String),
    }),
  }),
});
```

### expect.arrayContaining()

```typescript
// Array contains subset
expect(permissions).toEqual(
  expect.arrayContaining(['read', 'write'])
);

// Not contains
expect(permissions).toEqual(
  expect.not.arrayContaining(['admin'])
);
```

### expect.stringContaining() and expect.stringMatching()

```typescript
expect(message).toEqual(
  expect.stringContaining('Error')
);

expect(message).toEqual(
  expect.stringMatching(/Error: .+/)
);
```

## Exception Assertions

### Synchronous Exceptions

```typescript
// Throws any error
expect(() => throwingFunction()).toThrow();

// Throws specific message
expect(() => validate(null)).toThrow('Input required');

// Throws matching message
expect(() => validate(null)).toThrow(/required/i);

// Throws specific error type
expect(() => divide(1, 0)).toThrow(DivisionByZeroError);

// Custom error properties
expect(() => {
  throw new CustomError('msg', 404);
}).toThrow(
  expect.objectContaining({
    message: 'msg',
    code: 404,
  })
);
```

### Asynchronous Exceptions

```typescript
// Async function rejects
await expect(asyncFn()).rejects.toThrow();
await expect(asyncFn()).rejects.toThrow('Error message');
await expect(asyncFn()).rejects.toThrow(CustomError);

// Promise rejects
await expect(promise).rejects.toEqual({
  error: 'Not found',
  code: 404,
});

// Async with specific error
await expect(fetchUser('invalid')).rejects.toThrow(
  expect.objectContaining({
    message: expect.stringContaining('not found'),
  })
);
```

## Mock Assertions

### Call Verification

```typescript
// Was called
expect(mockFn).toHaveBeenCalled();
expect(mockFn).not.toHaveBeenCalled();

// Call count
expect(mockFn).toHaveBeenCalledTimes(3);

// Called with arguments
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2');
expect(mockFn).toHaveBeenCalledWith(
  expect.objectContaining({ id: '123' })
);

// Last call
expect(mockFn).toHaveBeenLastCalledWith('final', 'args');

// Nth call
expect(mockFn).toHaveBeenNthCalledWith(1, 'first');
expect(mockFn).toHaveBeenNthCalledWith(2, 'second');
```

### Return Value Verification

```typescript
// Check returned value
expect(mockFn).toHaveReturnedWith('value');
expect(mockFn).toHaveReturnedTimes(2);
expect(mockFn).toHaveLastReturnedWith('last');
expect(mockFn).toHaveNthReturnedWith(1, 'first');
```

## Custom Matchers

### Creating Custom Matchers

```typescript
// Define custom matcher
expect.extend({
  toBeValidEmail(received: string) {
    const emailRegex = /^[\w-]+@[\w-]+\.\w+$/;
    const pass = emailRegex.test(received);
    return {
      pass,
      message: () =>
        pass
          ? `expected ${received} not to be a valid email`
          : `expected ${received} to be a valid email`,
    };
  },

  toBeWithinRange(received: number, floor: number, ceiling: number) {
    const pass = received >= floor && received <= ceiling;
    return {
      pass,
      message: () =>
        `expected ${received} ${pass ? 'not ' : ''}to be within range ${floor}-${ceiling}`,
    };
  },
});

// Usage
expect('test@example.com').toBeValidEmail();
expect(50).toBeWithinRange(0, 100);
```

### TypeScript Declaration

```typescript
// types/jest.d.ts
declare global {
  namespace jest {
    interface Matchers<R> {
      toBeValidEmail(): R;
      toBeWithinRange(floor: number, ceiling: number): R;
    }
  }
}
```

## Assertion Organization

### Single Concept Per Test

```typescript
// ❌ Bad: Multiple unrelated assertions
it('should process user', () => {
  const user = processUser(input);
  expect(user.id).toBeDefined();
  expect(user.name).toBe('John');
  expect(user.email).toMatch(/@/);
  expect(user.createdAt).toBeInstanceOf(Date);
  expect(mockLogger.log).toHaveBeenCalled();
});

// ✅ Good: Related assertions that test one concept
it('should generate valid user ID', () => {
  const user = processUser(input);
  expect(user.id).toBeDefined();
  expect(user.id).toMatch(/^usr_[a-z0-9]+$/);
});

it('should set user name from input', () => {
  const user = processUser({ name: 'John' });
  expect(user.name).toBe('John');
});
```

### Assertion Order

```typescript
// Arrange assertions from general to specific
it('should create order', async () => {
  const order = await createOrder(data);

  // 1. Check it exists
  expect(order).toBeDefined();

  // 2. Check structure
  expect(order).toHaveProperty('id');
  expect(order).toHaveProperty('items');
  expect(order).toHaveProperty('total');

  // 3. Check specific values
  expect(order.items).toHaveLength(2);
  expect(order.total).toBe(149.98);
});
```

## Assertion Messages

```typescript
// Custom failure messages
expect(user.age).toBeGreaterThanOrEqual(18);
// Better: with context
expect(user.age >= 18).toBe(true);
// Even better: descriptive test name explains context

// For complex conditions
const isValidUser = user.age >= 18 && user.verified;
expect(isValidUser).toBe(true);
// Failure message won't be helpful!

// Instead, test separately
expect(user.age).toBeGreaterThanOrEqual(18);
expect(user.verified).toBe(true);
```

## Summary: Common Patterns

| Pattern | Use Case |
|---------|----------|
| `toBe()` | Primitives, same reference |
| `toEqual()` | Objects, arrays (deep) |
| `toMatchObject()` | Partial object match |
| `toContain()` | Array/string contains |
| `toHaveProperty()` | Object has property |
| `toThrow()` | Sync exceptions |
| `rejects.toThrow()` | Async exceptions |
| `toHaveBeenCalledWith()` | Mock verification |
| `expect.any()` | Type matching |
| `expect.objectContaining()` | Partial deep match |

## Related Topics

- [Unit Test Basics](./unit-test-basics.md)
- [Mocking Strategies](./mocking-strategies.md)
- [Arrange-Act-Assert Pattern](../patterns/arrange-act-assert.md)
