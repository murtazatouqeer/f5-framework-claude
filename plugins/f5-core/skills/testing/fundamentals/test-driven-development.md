---
name: test-driven-development
description: TDD methodology and practices
category: testing/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Test-Driven Development (TDD)

## Overview

TDD is a development practice where you write tests before writing
the production code. It follows a strict red-green-refactor cycle.

## The TDD Cycle

```
    ┌─────────────────────────────────────┐
    │                                     │
    ▼                                     │
┌───────┐    ┌───────┐    ┌──────────┐   │
│  RED  │───▶│ GREEN │───▶│ REFACTOR │───┘
└───────┘    └───────┘    └──────────┘
Write        Write        Improve
failing      minimal      code
test         code         quality
```

### 1. RED: Write a Failing Test

```typescript
// Step 1: Write test for behavior that doesn't exist yet
describe('UserValidator', () => {
  it('should validate email format', () => {
    const validator = new UserValidator();

    expect(validator.isValidEmail('test@example.com')).toBe(true);
    expect(validator.isValidEmail('invalid')).toBe(false);
  });
});

// This test will fail because UserValidator doesn't exist
```

### 2. GREEN: Write Minimal Code to Pass

```typescript
// Step 2: Write just enough code to make the test pass
class UserValidator {
  isValidEmail(email: string): boolean {
    return email.includes('@');
  }
}

// Test passes! But implementation is minimal
```

### 3. REFACTOR: Improve the Code

```typescript
// Step 3: Improve code while keeping tests green
class UserValidator {
  private readonly EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  isValidEmail(email: string): boolean {
    return this.EMAIL_REGEX.test(email);
  }
}

// Better implementation, tests still pass
```

## TDD Laws (Robert C. Martin)

### The Three Laws

1. **Don't write production code** until you've written a failing unit test
2. **Don't write more of a unit test** than is sufficient to fail
3. **Don't write more production code** than is sufficient to pass the test

## Complete TDD Example

### Feature: Shopping Cart

```typescript
// === CYCLE 1: Empty cart has zero total ===

// RED: Write failing test
describe('ShoppingCart', () => {
  it('should have zero total when empty', () => {
    const cart = new ShoppingCart();
    expect(cart.getTotal()).toBe(0);
  });
});

// GREEN: Minimal implementation
class ShoppingCart {
  getTotal(): number {
    return 0;
  }
}

// REFACTOR: Nothing to refactor yet
```

```typescript
// === CYCLE 2: Add single item ===

// RED: Write failing test
it('should calculate total for single item', () => {
  const cart = new ShoppingCart();
  cart.addItem({ name: 'Book', price: 29.99, quantity: 1 });
  expect(cart.getTotal()).toBe(29.99);
});

// GREEN: Make it pass
class ShoppingCart {
  private items: CartItem[] = [];

  addItem(item: CartItem): void {
    this.items.push(item);
  }

  getTotal(): number {
    if (this.items.length === 0) return 0;
    return this.items[0].price;
  }
}

// REFACTOR: Still minimal
```

```typescript
// === CYCLE 3: Multiple items ===

// RED: Write failing test
it('should calculate total for multiple items', () => {
  const cart = new ShoppingCart();
  cart.addItem({ name: 'Book', price: 29.99, quantity: 1 });
  cart.addItem({ name: 'Pen', price: 4.99, quantity: 2 });
  expect(cart.getTotal()).toBe(39.97);
});

// GREEN: Make it pass
class ShoppingCart {
  private items: CartItem[] = [];

  addItem(item: CartItem): void {
    this.items.push(item);
  }

  getTotal(): number {
    return this.items.reduce(
      (sum, item) => sum + item.price * item.quantity,
      0
    );
  }
}

// REFACTOR: Clean up
class ShoppingCart {
  private items: CartItem[] = [];

  addItem(item: CartItem): void {
    this.items.push(item);
  }

  getTotal(): number {
    return this.items.reduce(this.calculateItemTotal, 0);
  }

  private calculateItemTotal(sum: number, item: CartItem): number {
    return sum + item.price * item.quantity;
  }
}
```

```typescript
// === CYCLE 4: Apply discount ===

// RED
it('should apply percentage discount', () => {
  const cart = new ShoppingCart();
  cart.addItem({ name: 'Book', price: 100, quantity: 1 });
  cart.applyDiscount({ type: 'percentage', value: 10 });
  expect(cart.getTotal()).toBe(90);
});

// GREEN
class ShoppingCart {
  private items: CartItem[] = [];
  private discount: Discount | null = null;

  applyDiscount(discount: Discount): void {
    this.discount = discount;
  }

  getTotal(): number {
    const subtotal = this.items.reduce(this.calculateItemTotal, 0);
    return this.applyDiscountToTotal(subtotal);
  }

  private applyDiscountToTotal(subtotal: number): number {
    if (!this.discount) return subtotal;
    if (this.discount.type === 'percentage') {
      return subtotal * (1 - this.discount.value / 100);
    }
    return subtotal;
  }
}

// REFACTOR: Extract discount strategies
interface DiscountStrategy {
  apply(subtotal: number): number;
}

class PercentageDiscount implements DiscountStrategy {
  constructor(private percentage: number) {}

  apply(subtotal: number): number {
    return subtotal * (1 - this.percentage / 100);
  }
}
```

## TDD Benefits

### 1. Design Improvement
- Forces you to think about API first
- Results in more testable, modular code
- Reduces coupling

### 2. Documentation
- Tests serve as living documentation
- Show how code should be used
- Always up-to-date

### 3. Confidence
- High test coverage by default
- Safe refactoring
- Fewer bugs

### 4. Faster Development
- Less debugging time
- Immediate feedback
- Catch issues early

## TDD Anti-Patterns

### Writing Too Much Test

```typescript
// ❌ Bad: Testing implementation details
it('should add item to internal array', () => {
  const cart = new ShoppingCart();
  cart.addItem(item);
  expect(cart['items']).toContain(item); // Testing private
});

// ✅ Good: Testing behavior
it('should include added item in total', () => {
  const cart = new ShoppingCart();
  cart.addItem({ price: 10, quantity: 1 });
  expect(cart.getTotal()).toBe(10);
});
```

### Writing Production Code First

```typescript
// ❌ Bad: Writing code before test
class Calculator {
  add(a: number, b: number): number {
    return a + b;
  }

  subtract(a: number, b: number): number {
    return a - b;
  }

  // ... then writing tests
}

// ✅ Good: Test first
// 1. Write test for add
// 2. Implement add
// 3. Write test for subtract
// 4. Implement subtract
```

### Not Refactoring

```typescript
// ❌ Bad: Skipping refactor step
// Test passes, move to next feature immediately

// ✅ Good: Take time to refactor
// - Remove duplication
// - Improve naming
// - Extract methods
// - Apply design patterns
```

## TDD Workflow Tips

### Start Simple
```typescript
// Start with the simplest case
it('should return empty array for empty input', () => {
  expect(sort([])).toEqual([]);
});

// Then add complexity
it('should return single element unchanged', () => {
  expect(sort([1])).toEqual([1]);
});

it('should sort two elements', () => {
  expect(sort([2, 1])).toEqual([1, 2]);
});
```

### Use Test Lists
```typescript
// Before coding, list all tests needed
/*
 * Shopping Cart Tests:
 * - [ ] Empty cart has zero total
 * - [ ] Single item calculates correctly
 * - [ ] Multiple items sum correctly
 * - [ ] Quantity multiplies price
 * - [ ] Percentage discount applies
 * - [ ] Fixed discount applies
 * - [ ] Cannot go below zero
 * - [ ] Handles currency rounding
 */
```

### Triangulation
```typescript
// Add more test cases to drive generalization
it('should add 1 + 1', () => {
  expect(add(1, 1)).toBe(2);
});

it('should add 2 + 3', () => {
  expect(add(2, 3)).toBe(5);
});

it('should add negative numbers', () => {
  expect(add(-1, 1)).toBe(0);
});

// Now you need a real implementation, not just "return 2"
```

## When TDD Works Best

| Good Fit | Poor Fit |
|----------|----------|
| Business logic | UI layout |
| Algorithms | Exploratory code |
| API design | Prototype/spike |
| Data processing | Legacy without tests |
| Validation rules | Performance tuning |

## Related Topics

- [Behavior-Driven Development](./behavior-driven-development.md)
- [Unit Test Basics](../unit-testing/unit-test-basics.md)
- [Testing Principles](./testing-principles.md)
