---
name: behavior-driven-development
description: BDD methodology with Gherkin syntax and examples
category: testing/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Behavior-Driven Development (BDD)

## Overview

BDD extends TDD by focusing on user behaviors and business outcomes.
It uses natural language to describe expected behavior, making tests
readable by non-technical stakeholders.

## BDD vs TDD

| Aspect | TDD | BDD |
|--------|-----|-----|
| Focus | Code units | User behaviors |
| Language | Technical | Business/Natural |
| Audience | Developers | All stakeholders |
| Granularity | Fine | Coarse |
| Starting point | Function | User story |

## Gherkin Syntax

### Basic Structure

```gherkin
Feature: User Login
  As a registered user
  I want to log into my account
  So that I can access my personal dashboard

  Scenario: Successful login with valid credentials
    Given I am on the login page
    And I have a registered account with email "user@example.com"
    When I enter "user@example.com" as email
    And I enter "password123" as password
    And I click the "Login" button
    Then I should be redirected to the dashboard
    And I should see "Welcome back!" message
```

### Keywords

| Keyword | Purpose | Example |
|---------|---------|---------|
| **Feature** | Describe feature | `Feature: Shopping Cart` |
| **Scenario** | Specific test case | `Scenario: Add item to cart` |
| **Given** | Initial context | `Given I am logged in` |
| **When** | Action taken | `When I click "Add to Cart"` |
| **Then** | Expected outcome | `Then I should see item in cart` |
| **And/But** | Additional steps | `And total should update` |
| **Background** | Shared setup | Common preconditions |
| **Scenario Outline** | Parameterized | Multiple data variations |

## Complete Feature Example

```gherkin
Feature: Shopping Cart
  As a customer
  I want to manage items in my shopping cart
  So that I can purchase multiple items at once

  Background:
    Given the following products exist:
      | name        | price  | stock |
      | Laptop      | 999.99 | 10    |
      | Mouse       | 29.99  | 50    |
      | Keyboard    | 79.99  | 25    |
    And I am logged in as "customer@example.com"

  Scenario: Add single item to empty cart
    Given my cart is empty
    When I add "Laptop" to my cart
    Then my cart should contain 1 item
    And my cart total should be $999.99

  Scenario: Add multiple items to cart
    Given my cart is empty
    When I add "Laptop" to my cart
    And I add "Mouse" to my cart
    Then my cart should contain 2 items
    And my cart total should be $1,029.98

  Scenario: Update item quantity
    Given my cart contains:
      | product | quantity |
      | Mouse   | 1        |
    When I change the quantity of "Mouse" to 3
    Then my cart should contain 3 items
    And my cart total should be $89.97

  Scenario: Remove item from cart
    Given my cart contains:
      | product | quantity |
      | Laptop  | 1        |
      | Mouse   | 2        |
    When I remove "Mouse" from my cart
    Then my cart should contain 1 item
    And my cart total should be $999.99

  Scenario Outline: Apply discount codes
    Given my cart total is $100.00
    When I apply discount code "<code>"
    Then my cart total should be $<total>
    And I should see message "<message>"

    Examples:
      | code      | total | message                    |
      | SAVE10    | 90.00 | 10% discount applied!      |
      | FLAT20    | 80.00 | $20 off applied!           |
      | INVALID   | 100.00| Invalid discount code      |
      | EXPIRED   | 100.00| This code has expired      |

  Scenario: Prevent checkout with empty cart
    Given my cart is empty
    When I try to proceed to checkout
    Then I should see error "Your cart is empty"
    And I should remain on the cart page
```

## Implementing BDD Tests

### Using Cucumber.js (JavaScript/TypeScript)

```typescript
// features/step-definitions/cart.steps.ts
import { Given, When, Then, DataTable } from '@cucumber/cucumber';
import { expect } from 'chai';
import { CartPage } from '../pages/cart.page';
import { ProductService } from '../services/product.service';

let cartPage: CartPage;
let productService: ProductService;

Given('the following products exist:', async (dataTable: DataTable) => {
  const products = dataTable.hashes();
  for (const product of products) {
    await productService.createProduct({
      name: product.name,
      price: parseFloat(product.price),
      stock: parseInt(product.stock),
    });
  }
});

Given('I am logged in as {string}', async (email: string) => {
  await cartPage.login(email, 'password123');
});

Given('my cart is empty', async () => {
  await cartPage.clearCart();
});

Given('my cart contains:', async (dataTable: DataTable) => {
  const items = dataTable.hashes();
  for (const item of items) {
    await cartPage.addToCart(item.product, parseInt(item.quantity));
  }
});

When('I add {string} to my cart', async (productName: string) => {
  await cartPage.addToCart(productName);
});

When('I change the quantity of {string} to {int}', async (product: string, qty: number) => {
  await cartPage.updateQuantity(product, qty);
});

When('I remove {string} from my cart', async (productName: string) => {
  await cartPage.removeFromCart(productName);
});

When('I apply discount code {string}', async (code: string) => {
  await cartPage.applyDiscountCode(code);
});

When('I try to proceed to checkout', async () => {
  await cartPage.proceedToCheckout();
});

Then('my cart should contain {int} item(s)', async (count: number) => {
  const itemCount = await cartPage.getItemCount();
  expect(itemCount).to.equal(count);
});

Then('my cart total should be ${float}', async (total: number) => {
  const cartTotal = await cartPage.getTotal();
  expect(cartTotal).to.be.closeTo(total, 0.01);
});

Then('I should see message {string}', async (message: string) => {
  const displayedMessage = await cartPage.getMessage();
  expect(displayedMessage).to.include(message);
});

Then('I should see error {string}', async (error: string) => {
  const errorMessage = await cartPage.getErrorMessage();
  expect(errorMessage).to.include(error);
});

Then('I should remain on the cart page', async () => {
  const currentUrl = await cartPage.getCurrentUrl();
  expect(currentUrl).to.include('/cart');
});
```

### Using Jest with BDD Style

```typescript
// cart.spec.ts
import { ShoppingCart } from './shopping-cart';
import { Product } from './product';

describe('Feature: Shopping Cart', () => {
  let cart: ShoppingCart;
  let products: Map<string, Product>;

  beforeEach(() => {
    // Background setup
    products = new Map([
      ['Laptop', { name: 'Laptop', price: 999.99, stock: 10 }],
      ['Mouse', { name: 'Mouse', price: 29.99, stock: 50 }],
      ['Keyboard', { name: 'Keyboard', price: 79.99, stock: 25 }],
    ]);
    cart = new ShoppingCart();
  });

  describe('Scenario: Add single item to empty cart', () => {
    it('should add item and update total', () => {
      // Given my cart is empty
      expect(cart.isEmpty()).toBe(true);

      // When I add "Laptop" to my cart
      cart.addItem(products.get('Laptop')!);

      // Then my cart should contain 1 item
      expect(cart.getItemCount()).toBe(1);

      // And my cart total should be $999.99
      expect(cart.getTotal()).toBeCloseTo(999.99);
    });
  });

  describe('Scenario: Add multiple items to cart', () => {
    it('should calculate correct total', () => {
      // Given my cart is empty
      // When I add "Laptop" and "Mouse" to my cart
      cart.addItem(products.get('Laptop')!);
      cart.addItem(products.get('Mouse')!);

      // Then my cart should contain 2 items
      expect(cart.getItemCount()).toBe(2);

      // And my cart total should be $1,029.98
      expect(cart.getTotal()).toBeCloseTo(1029.98);
    });
  });

  describe('Scenario Outline: Apply discount codes', () => {
    const testCases = [
      { code: 'SAVE10', total: 90.00, message: '10% discount applied!' },
      { code: 'FLAT20', total: 80.00, message: '$20 off applied!' },
      { code: 'INVALID', total: 100.00, message: 'Invalid discount code' },
      { code: 'EXPIRED', total: 100.00, message: 'This code has expired' },
    ];

    testCases.forEach(({ code, total, message }) => {
      it(`should handle discount code "${code}"`, () => {
        // Given my cart total is $100.00
        cart.addItem({ name: 'Test', price: 100, stock: 1 });

        // When I apply discount code
        const result = cart.applyDiscount(code);

        // Then my cart total should be $<total>
        expect(cart.getTotal()).toBeCloseTo(total);

        // And I should see message
        expect(result.message).toBe(message);
      });
    });
  });
});
```

## BDD Best Practices

### Write User-Centric Scenarios

```gherkin
# ❌ Bad: Technical implementation details
Scenario: Insert user record into database
  Given the database connection is established
  When I execute INSERT INTO users VALUES (...)
  Then the row count should increase by 1

# ✅ Good: User behavior focus
Scenario: New user registration
  Given I am a new visitor
  When I complete the registration form with valid details
  Then I should receive a welcome email
  And I should be able to log in with my new account
```

### Use Domain Language

```gherkin
# ❌ Bad: Generic terms
Scenario: Click button and check result
  Given I am on page1
  When I click button1
  Then label1 should show "Success"

# ✅ Good: Business domain terms
Scenario: Submit expense report for approval
  Given I am an employee with pending expenses
  When I submit my expense report
  Then my manager should receive an approval request
  And the report status should be "Pending Approval"
```

### One Behavior Per Scenario

```gherkin
# ❌ Bad: Multiple behaviors
Scenario: User management
  When I create a user
  Then user should exist
  When I update the user
  Then changes should be saved
  When I delete the user
  Then user should not exist

# ✅ Good: Separate scenarios
Scenario: Create new user
  When I create a user with valid details
  Then the user should be saved successfully

Scenario: Update existing user
  Given a user exists
  When I update the user's email
  Then the change should be saved

Scenario: Delete user
  Given a user exists
  When I delete the user
  Then the user should no longer exist
```

### Avoid UI Details

```gherkin
# ❌ Bad: Too many UI details
Scenario: Login
  Given I navigate to "http://example.com/login"
  When I type "user@test.com" into the input with id "email"
  And I type "pass123" into the input with id "password"
  And I click the button with class "submit-btn"
  Then the div with class "welcome" should contain "Hello"

# ✅ Good: Behavior focused
Scenario: Login
  Given I am on the login page
  When I log in with valid credentials
  Then I should see my dashboard
```

## BDD Tools by Language

| Language | Tool | Notes |
|----------|------|-------|
| JavaScript | Cucumber.js | Full Gherkin support |
| TypeScript | Cucumber.js | With ts-node |
| Python | Behave | Pythonic syntax |
| Ruby | Cucumber | Original Cucumber |
| Java | Cucumber-JVM | JUnit integration |
| C# | SpecFlow | .NET integration |
| Go | Godog | Go implementation |

## Related Topics

- [Test-Driven Development](./test-driven-development.md)
- [Given-When-Then Pattern](../patterns/given-when-then.md)
- [E2E Testing Basics](../e2e-testing/e2e-basics.md)
