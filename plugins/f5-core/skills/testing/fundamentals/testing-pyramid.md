---
name: testing-pyramid
description: Understanding the test pyramid and optimal test distribution
category: testing/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Testing Pyramid

## Overview

The testing pyramid is a framework for balancing different types of tests
to achieve optimal coverage with efficient resource usage.

## The Pyramid Structure

```
              ╱╲
             ╱  ╲           E2E / UI Tests
            ╱────╲          ~10% of tests
           ╱      ╲         Slow, Expensive, Brittle
          ╱────────╲
         ╱          ╲       Integration Tests
        ╱────────────╲      ~20% of tests
       ╱              ╲     Medium Speed, Medium Cost
      ╱────────────────╲
     ╱                  ╲   Unit Tests
    ╱____________________╲  ~70% of tests
                            Fast, Cheap, Stable
```

## Test Type Comparison

| Aspect | Unit | Integration | E2E |
|--------|------|-------------|-----|
| **Speed** | Milliseconds | Seconds | Minutes |
| **Isolation** | Complete | Partial | None |
| **Setup** | Minimal | Moderate | Complex |
| **Maintenance** | Low | Medium | High |
| **Confidence** | Low-Medium | Medium-High | High |
| **Debugging** | Easy | Medium | Hard |
| **Cost** | Low | Medium | High |

## Ideal Distribution

### Traditional Pyramid (70-20-10)

```yaml
distribution:
  unit_tests: 70%
  integration_tests: 20%
  e2e_tests: 10%
```

### Modern Approach (Trophy)

Some teams prefer the "testing trophy" for web applications:

```
        ╱╲         E2E (Few)
       ╱──╲
      ╱    ╲       Integration (Most)
     ╱──────╲
    ╱        ╲     Unit (Some)
   ╱──────────╲
  ╱            ╲   Static Analysis (Base)
 ╱______________╲
```

## Unit Tests (Base Layer)

### Characteristics
- Test single units in isolation
- No external dependencies (DB, network, filesystem)
- Run in milliseconds
- Provide fast feedback

### When to Write
```typescript
// Pure business logic
function calculateTax(amount: number, rate: number): number {
  return amount * rate;
}

// Validation rules
function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

// State transformations
function applyDiscount(cart: Cart, discount: Discount): Cart {
  // ...
}
```

### Example
```typescript
describe('calculateTax', () => {
  it('should calculate tax correctly', () => {
    expect(calculateTax(100, 0.1)).toBe(10);
  });

  it('should return 0 for 0 rate', () => {
    expect(calculateTax(100, 0)).toBe(0);
  });

  it('should handle decimal amounts', () => {
    expect(calculateTax(99.99, 0.1)).toBeCloseTo(9.999);
  });
});
```

## Integration Tests (Middle Layer)

### Characteristics
- Test interactions between components
- May include real databases, APIs
- Run in seconds
- Verify contracts between units

### When to Write
```typescript
// Repository with database
class UserRepository {
  async findByEmail(email: string): Promise<User | null> {
    // Real database query
  }
}

// Service with external API
class PaymentService {
  async processPayment(payment: Payment): Promise<Result> {
    // External payment gateway
  }
}

// Multiple service orchestration
class OrderService {
  async createOrder(order: OrderDTO): Promise<Order> {
    // Coordinates user, inventory, payment services
  }
}
```

### Example
```typescript
describe('UserRepository Integration', () => {
  let repository: UserRepository;
  let database: TestDatabase;

  beforeAll(async () => {
    database = await TestDatabase.start();
    repository = new UserRepository(database.connection);
  });

  afterAll(async () => {
    await database.stop();
  });

  beforeEach(async () => {
    await database.clean();
  });

  it('should save and retrieve user', async () => {
    const user = new User('test@example.com', 'Test User');

    await repository.save(user);
    const found = await repository.findByEmail('test@example.com');

    expect(found).toEqual(user);
  });
});
```

## E2E Tests (Top Layer)

### Characteristics
- Test complete user workflows
- Use real UI, backend, database
- Run in minutes
- Highest confidence but most brittle

### When to Write
```typescript
// Critical user journeys
// - User registration and login
// - Checkout and payment
// - Core business workflows

// Smoke tests
// - Application starts
// - Key pages load
// - Basic navigation works
```

### Example
```typescript
describe('Checkout Flow', () => {
  it('should complete purchase successfully', async () => {
    // Login
    await page.goto('/login');
    await page.fill('#email', 'user@test.com');
    await page.fill('#password', 'password');
    await page.click('button[type="submit"]');

    // Add to cart
    await page.goto('/products/123');
    await page.click('[data-testid="add-to-cart"]');

    // Checkout
    await page.goto('/checkout');
    await page.fill('#card-number', '4242424242424242');
    await page.click('[data-testid="place-order"]');

    // Verify
    await expect(page).toHaveURL(/\/orders\/\d+/);
  });
});
```

## Anti-Patterns

### Ice Cream Cone (Inverted Pyramid)

```
     ____________________
    ╲                    ╱   Too many E2E tests
     ╲                  ╱    Slow, brittle, expensive
      ╲────────────────╱
       ╲              ╱      Some integration tests
        ╲────────────╱
         ╲          ╱        Few unit tests
          ╲────────╱
           ╲      ╱          Fast tests missing!
            ╲────╱
             ╲  ╱
              ╲╱
```

**Problems:**
- Slow feedback loops
- High maintenance cost
- Difficult debugging
- Expensive CI/CD

### Cupcake (No Strategy)

```
   🧁    🧁    🧁    🧁
  E2E   Int  Unit Random
```

**Problems:**
- Inconsistent coverage
- Random test selection
- No clear strategy
- Gaps in coverage

## Best Practices

### 1. Start with Unit Tests
```typescript
// Write unit tests first for:
// - Business logic
// - Validation
// - Calculations
// - Transformations
```

### 2. Add Integration Tests for Boundaries
```typescript
// Write integration tests for:
// - Database operations
// - External APIs
// - Message queues
// - File systems
```

### 3. E2E for Critical Paths Only
```typescript
// Limit E2E tests to:
// - Money transactions
// - User registration
// - Core workflows
// - Smoke tests
```

### 4. Maintain the Pyramid
```yaml
# Review test distribution regularly
metrics:
  unit_test_count: 500
  integration_test_count: 100
  e2e_test_count: 20

# Calculate ratios
ratios:
  unit_percentage: 80.6%
  integration_percentage: 16.1%
  e2e_percentage: 3.2%
```

## Decision Matrix

| Scenario | Primary Test Type |
|----------|-------------------|
| Business logic | Unit |
| Database queries | Integration |
| API contracts | Integration |
| External services | Integration (with mocks) |
| User workflows | E2E |
| Visual appearance | E2E + Visual |
| Performance | Load testing (separate) |

## Related Topics

- [Test-Driven Development](./test-driven-development.md)
- [Unit Test Basics](../unit-testing/unit-test-basics.md)
- [Integration Test Basics](../integration-testing/integration-test-basics.md)
- [E2E Basics](../e2e-testing/e2e-basics.md)
