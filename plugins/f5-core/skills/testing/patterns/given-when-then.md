---
name: given-when-then
description: BDD-style test structure for behavior specification
category: testing/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Given-When-Then Pattern

## Overview

Given-When-Then (GWT) is a BDD-style pattern that describes test scenarios
in terms of preconditions, actions, and expected outcomes using natural language.

## Pattern Structure

```
GIVEN [preconditions/initial state]
WHEN [action/event occurs]
THEN [expected outcome/behavior]
```

## Comparison with AAA

| AAA | Given-When-Then | Focus |
|-----|-----------------|-------|
| Arrange | Given | Technical setup |
| Act | When | Action execution |
| Assert | Then | Result verification |

**Key Difference**: GWT uses business language, AAA uses technical language.

## Basic Examples

### Simple Test

```typescript
describe('UserRegistration', () => {
  it('should allow registration with valid email', () => {
    // Given a new user with valid details
    const registrationService = new RegistrationService();
    const validUserData = {
      email: 'newuser@example.com',
      password: 'SecurePass123!',
    };

    // When they register
    const result = registrationService.register(validUserData);

    // Then they should be successfully registered
    expect(result.success).toBe(true);
    expect(result.user.email).toBe('newuser@example.com');
  });
});
```

### With Multiple Conditions

```typescript
describe('ShoppingCart', () => {
  it('should apply discount for premium customer with large order', () => {
    // Given a premium customer
    const customer = createCustomer({ type: 'premium' });

    // And a cart with items totaling over $100
    const cart = new ShoppingCart(customer);
    cart.addItem({ price: 50, quantity: 3 }); // $150

    // When the discount is calculated
    const discount = cart.calculateDiscount();

    // Then a 15% discount should be applied
    expect(discount).toBe(22.5); // 15% of $150
  });
});
```

## Gherkin Syntax

### Feature File

```gherkin
Feature: User Authentication
  As a registered user
  I want to log into my account
  So that I can access my personal data

  Background:
    Given the authentication service is available

  Scenario: Successful login
    Given a user exists with email "user@test.com" and password "password123"
    When the user logs in with email "user@test.com" and password "password123"
    Then the login should be successful
    And a valid session token should be returned

  Scenario: Failed login with wrong password
    Given a user exists with email "user@test.com" and password "password123"
    When the user logs in with email "user@test.com" and password "wrongpassword"
    Then the login should fail
    And the error message should be "Invalid credentials"

  Scenario Outline: Password validation
    Given a user is registering
    When they enter password "<password>"
    Then the validation result should be <valid>
    And the message should be "<message>"

    Examples:
      | password      | valid | message                     |
      | weak          | false | Password too short          |
      | NoSpecial123  | false | Must include special char   |
      | ValidPass1!   | true  | Password accepted           |
```

### Step Definitions

```typescript
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';

let authService: AuthService;
let loginResult: LoginResult;
let existingUser: User;

Given('the authentication service is available', function () {
  authService = new AuthService();
});

Given('a user exists with email {string} and password {string}',
  async function (email: string, password: string) {
    existingUser = await authService.createUser({ email, password });
  }
);

When('the user logs in with email {string} and password {string}',
  async function (email: string, password: string) {
    loginResult = await authService.login({ email, password });
  }
);

Then('the login should be successful', function () {
  expect(loginResult.success).to.be.true;
});

Then('the login should fail', function () {
  expect(loginResult.success).to.be.false;
});

Then('a valid session token should be returned', function () {
  expect(loginResult.token).to.be.a('string');
  expect(loginResult.token.length).to.be.greaterThan(0);
});

Then('the error message should be {string}', function (message: string) {
  expect(loginResult.error).to.equal(message);
});
```

## Jest BDD Style

```typescript
describe('Feature: Order Processing', () => {
  describe('Scenario: Create order with valid items', () => {
    let orderService: OrderService;
    let customer: Customer;
    let order: Order;

    beforeAll(() => {
      // Given
      orderService = new OrderService();
      customer = createTestCustomer({ hasValidPayment: true });
    });

    it('Given a customer with valid payment', () => {
      expect(customer.hasValidPayment).toBe(true);
    });

    it('And items are in stock', async () => {
      const items = [
        { productId: 'prod-1', quantity: 2 },
        { productId: 'prod-2', quantity: 1 },
      ];

      const stockCheck = await orderService.checkStock(items);
      expect(stockCheck.allInStock).toBe(true);
    });

    it('When the order is placed', async () => {
      order = await orderService.createOrder({
        customerId: customer.id,
        items: [
          { productId: 'prod-1', quantity: 2 },
          { productId: 'prod-2', quantity: 1 },
        ],
      });
    });

    it('Then the order should be created successfully', () => {
      expect(order.id).toBeDefined();
      expect(order.status).toBe('pending');
    });

    it('And the customer should be charged', () => {
      expect(order.payment.status).toBe('captured');
    });

    it('And inventory should be updated', async () => {
      const stock = await orderService.getStock('prod-1');
      expect(stock.reserved).toBeGreaterThan(0);
    });
  });
});
```

## Complex Scenarios

### Multiple Whens

```typescript
describe('Checkout Flow', () => {
  it('should complete multi-step checkout', async () => {
    // Given a customer with items in cart
    const customer = createAuthenticatedCustomer();
    const cart = await seedCart(customer.id, [
      { productId: 'item-1', quantity: 2 },
    ]);

    // And valid shipping address
    const address = createValidAddress();

    // And valid payment method
    const paymentMethod = createValidPaymentMethod();

    // When shipping address is submitted
    await checkoutService.setShippingAddress(cart.id, address);

    // And payment method is submitted
    await checkoutService.setPaymentMethod(cart.id, paymentMethod);

    // And order is confirmed
    const order = await checkoutService.confirm(cart.id);

    // Then order should be created with correct details
    expect(order.shippingAddress).toEqual(address);
    expect(order.paymentMethod.last4).toBe(paymentMethod.last4);
    expect(order.status).toBe('confirmed');

    // And cart should be cleared
    const updatedCart = await cartService.getCart(customer.id);
    expect(updatedCart.items).toHaveLength(0);

    // And confirmation email should be sent
    expect(mockEmailService.send).toHaveBeenCalledWith(
      expect.objectContaining({
        to: customer.email,
        template: 'order-confirmation',
      })
    );
  });
});
```

### Nested Givens

```typescript
describe('Premium User Features', () => {
  describe('Given a premium user', () => {
    let user: User;

    beforeEach(async () => {
      user = await createPremiumUser();
    });

    describe('And they have active subscription', () => {
      beforeEach(async () => {
        await activateSubscription(user.id, { plan: 'premium' });
      });

      describe('When they access exclusive content', () => {
        it('Then they should see full content', async () => {
          const content = await contentService.getExclusive(user.id, 'article-1');

          expect(content.isRestricted).toBe(false);
          expect(content.fullText).toBeDefined();
        });
      });

      describe('When they download resources', () => {
        it('Then they should get unlimited downloads', async () => {
          const downloads = await downloadService.getRemaining(user.id);

          expect(downloads).toBe(Infinity);
        });
      });
    });

    describe('And subscription has expired', () => {
      beforeEach(async () => {
        await expireSubscription(user.id);
      });

      describe('When they access exclusive content', () => {
        it('Then they should see preview only', async () => {
          const content = await contentService.getExclusive(user.id, 'article-1');

          expect(content.isRestricted).toBe(true);
          expect(content.fullText).toBeUndefined();
          expect(content.preview).toBeDefined();
        });
      });
    });
  });
});
```

## And/But Keywords

```gherkin
Scenario: Apply coupon to order
  Given a customer has items in their cart
  And the cart total is $100
  And a valid coupon "SAVE20" exists for 20% off
  When the customer applies coupon "SAVE20"
  Then the discount should be $20
  And the new total should be $80
  But the original price should still show $100

Scenario: Cannot apply expired coupon
  Given a customer has items in their cart
  And a coupon "OLDCODE" that expired yesterday
  When the customer applies coupon "OLDCODE"
  Then the coupon should be rejected
  And an error message "Coupon has expired" should show
  But the cart total should remain unchanged
```

## Best Practices

### Use Business Language

```typescript
// ✅ Good: Business-focused
// Given a customer with VIP status
// When they place an order over $100
// Then free shipping should be applied

// ❌ Bad: Technical implementation
// Given mockShippingService returns freeShipping=true
// When orderService.create() is called with amount=150
// Then order.shippingCost should equal 0
```

### Keep Scenarios Focused

```typescript
// ✅ Good: One behavior per scenario
describe('Scenario: Login with valid credentials', () => {
  // Tests successful login
});

describe('Scenario: Login with invalid password', () => {
  // Tests password failure
});

// ❌ Bad: Multiple behaviors
describe('Scenario: Login functionality', () => {
  // Tests valid login, invalid password, locked account, etc.
});
```

### Avoid Technical Details in Given

```typescript
// ✅ Good: Abstract technical details
// Given a premium user with an active subscription

// ❌ Bad: Expose implementation
// Given user.role === 'premium' && subscription.status === 'active'
```

## GWT vs AAA Decision Guide

| Use GWT When | Use AAA When |
|--------------|--------------|
| Stakeholder communication | Developer-only tests |
| Acceptance tests | Unit tests |
| BDD workflows | TDD workflows |
| Complex business rules | Simple technical logic |
| Documentation needed | Quick test writing |

## Related Topics

- [Arrange-Act-Assert](./arrange-act-assert.md)
- [Behavior-Driven Development](../fundamentals/behavior-driven-development.md)
- [E2E Testing Basics](../e2e-testing/e2e-basics.md)
