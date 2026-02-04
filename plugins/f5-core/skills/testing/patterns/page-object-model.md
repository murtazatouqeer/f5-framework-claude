---
name: page-object-model
description: Page Object Model pattern for UI test organization
category: testing/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Page Object Model (POM)

## Overview

Page Object Model is a design pattern that creates an abstraction layer
over UI pages, encapsulating page structure and interactions. It improves
test maintainability by separating page logic from test logic.

## Benefits

| Benefit | Description |
|---------|-------------|
| Maintainability | Change selectors in one place |
| Readability | Tests read like user actions |
| Reusability | Share page logic across tests |
| Abstraction | Hide implementation details |

## Basic Page Object

```typescript
// pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;

  // Locators
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;
  readonly forgotPasswordLink: Locator;
  readonly registerLink: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.loginButton = page.locator('[data-testid="login-button"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
    this.forgotPasswordLink = page.locator('a:has-text("Forgot password")');
    this.registerLink = page.locator('a:has-text("Register")');
  }

  // Navigation
  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  // Actions
  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async clickForgotPassword(): Promise<void> {
    await this.forgotPasswordLink.click();
  }

  async clickRegister(): Promise<void> {
    await this.registerLink.click();
  }

  // State checks
  async isLoaded(): Promise<boolean> {
    return this.loginButton.isVisible();
  }

  async getErrorMessage(): Promise<string> {
    return this.errorMessage.textContent() ?? '';
  }
}
```

## Using Page Objects in Tests

```typescript
// tests/auth.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

test.describe('Authentication', () => {
  let loginPage: LoginPage;
  let dashboardPage: DashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
    await loginPage.goto();
  });

  test('should login with valid credentials', async () => {
    await loginPage.login('user@example.com', 'password123');

    await expect(dashboardPage.welcomeMessage).toBeVisible();
    await expect(dashboardPage.welcomeMessage).toContainText('Welcome');
  });

  test('should show error for invalid credentials', async () => {
    await loginPage.login('wrong@example.com', 'wrongpassword');

    const error = await loginPage.getErrorMessage();
    expect(error).toContain('Invalid credentials');
  });

  test('should navigate to register page', async () => {
    await loginPage.clickRegister();

    await expect(loginPage.page).toHaveURL('/register');
  });
});
```

## Component Page Objects

```typescript
// components/header.component.ts
import { Page, Locator } from '@playwright/test';

export class HeaderComponent {
  readonly container: Locator;
  readonly logo: Locator;
  readonly searchInput: Locator;
  readonly cartButton: Locator;
  readonly cartBadge: Locator;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.container = page.locator('header');
    this.logo = this.container.locator('[data-testid="logo"]');
    this.searchInput = this.container.locator('[data-testid="search-input"]');
    this.cartButton = this.container.locator('[data-testid="cart-button"]');
    this.cartBadge = this.cartButton.locator('.badge');
    this.userMenu = this.container.locator('[data-testid="user-menu"]');
    this.logoutButton = this.container.locator('button:has-text("Logout")');
  }

  async search(query: string): Promise<void> {
    await this.searchInput.fill(query);
    await this.searchInput.press('Enter');
  }

  async openCart(): Promise<void> {
    await this.cartButton.click();
  }

  async getCartItemCount(): Promise<number> {
    const text = await this.cartBadge.textContent();
    return parseInt(text || '0', 10);
  }

  async logout(): Promise<void> {
    await this.userMenu.click();
    await this.logoutButton.click();
  }
}
```

## Page Object with Components

```typescript
// pages/product-list.page.ts
import { Page, Locator } from '@playwright/test';
import { HeaderComponent } from '../components/header.component';
import { FilterSidebar } from '../components/filter-sidebar.component';
import { ProductCard } from '../components/product-card.component';

export class ProductListPage {
  readonly page: Page;
  readonly header: HeaderComponent;
  readonly filters: FilterSidebar;
  readonly productGrid: Locator;
  readonly loadMoreButton: Locator;
  readonly noResultsMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.header = new HeaderComponent(page);
    this.filters = new FilterSidebar(page);
    this.productGrid = page.locator('[data-testid="product-grid"]');
    this.loadMoreButton = page.locator('[data-testid="load-more"]');
    this.noResultsMessage = page.locator('[data-testid="no-results"]');
  }

  async goto(category?: string): Promise<void> {
    const url = category ? `/products?category=${category}` : '/products';
    await this.page.goto(url);
  }

  async getProductCards(): Promise<ProductCard[]> {
    const cards = await this.productGrid.locator('[data-testid="product-card"]').all();
    return cards.map(locator => new ProductCard(locator));
  }

  async getProductCount(): Promise<number> {
    const cards = await this.getProductCards();
    return cards.length;
  }

  async loadMore(): Promise<void> {
    await this.loadMoreButton.click();
    await this.page.waitForLoadState('networkidle');
  }

  async searchProducts(query: string): Promise<void> {
    await this.header.search(query);
    await this.page.waitForLoadState('networkidle');
  }

  async filterByPriceRange(min: number, max: number): Promise<void> {
    await this.filters.setPriceRange(min, max);
    await this.page.waitForLoadState('networkidle');
  }
}

// components/product-card.component.ts
export class ProductCard {
  readonly container: Locator;

  constructor(container: Locator) {
    this.container = container;
  }

  async getName(): Promise<string> {
    return this.container.locator('[data-testid="product-name"]').textContent() ?? '';
  }

  async getPrice(): Promise<number> {
    const text = await this.container.locator('[data-testid="product-price"]').textContent();
    return parseFloat(text?.replace(/[^0-9.]/g, '') ?? '0');
  }

  async addToCart(): Promise<void> {
    await this.container.locator('[data-testid="add-to-cart"]').click();
  }

  async viewDetails(): Promise<void> {
    await this.container.click();
  }
}
```

## Page Object with Flows

```typescript
// pages/checkout.page.ts
import { Page, Locator } from '@playwright/test';

export class CheckoutPage {
  readonly page: Page;

  // Step indicators
  readonly stepIndicator: Locator;
  readonly currentStep: Locator;

  // Shipping form
  readonly shippingForm: Locator;
  readonly addressInput: Locator;
  readonly cityInput: Locator;
  readonly zipInput: Locator;
  readonly countrySelect: Locator;

  // Payment form
  readonly paymentForm: Locator;
  readonly cardNumberInput: Locator;
  readonly expiryInput: Locator;
  readonly cvvInput: Locator;

  // Review
  readonly orderSummary: Locator;
  readonly placeOrderButton: Locator;

  // Navigation
  readonly nextButton: Locator;
  readonly backButton: Locator;

  constructor(page: Page) {
    this.page = page;
    // ... initialize locators
  }

  // Step-specific actions
  async fillShippingAddress(address: ShippingAddress): Promise<void> {
    await this.addressInput.fill(address.street);
    await this.cityInput.fill(address.city);
    await this.zipInput.fill(address.zip);
    await this.countrySelect.selectOption(address.country);
  }

  async fillPaymentDetails(payment: PaymentDetails): Promise<void> {
    await this.cardNumberInput.fill(payment.cardNumber);
    await this.expiryInput.fill(payment.expiry);
    await this.cvvInput.fill(payment.cvv);
  }

  async goToNextStep(): Promise<void> {
    await this.nextButton.click();
    await this.page.waitForLoadState('networkidle');
  }

  async goBack(): Promise<void> {
    await this.backButton.click();
  }

  async placeOrder(): Promise<void> {
    await this.placeOrderButton.click();
    await this.page.waitForURL(/\/orders\/\d+/);
  }

  // Complete flow
  async completeCheckout(
    shipping: ShippingAddress,
    payment: PaymentDetails
  ): Promise<string> {
    // Step 1: Shipping
    await this.fillShippingAddress(shipping);
    await this.goToNextStep();

    // Step 2: Payment
    await this.fillPaymentDetails(payment);
    await this.goToNextStep();

    // Step 3: Review & Place Order
    await this.placeOrder();

    // Return order ID from URL
    const url = this.page.url();
    const match = url.match(/\/orders\/(\d+)/);
    return match?.[1] ?? '';
  }

  async getCurrentStepName(): Promise<string> {
    return this.currentStep.textContent() ?? '';
  }
}
```

## Playwright Fixtures with POM

```typescript
// fixtures/pages.fixture.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';
import { ProductListPage } from '../pages/product-list.page';
import { CheckoutPage } from '../pages/checkout.page';

interface PageObjects {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  productListPage: ProductListPage;
  checkoutPage: CheckoutPage;
}

export const test = base.extend<PageObjects>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  productListPage: async ({ page }, use) => {
    await use(new ProductListPage(page));
  },

  checkoutPage: async ({ page }, use) => {
    await use(new CheckoutPage(page));
  },
});

export { expect } from '@playwright/test';

// Usage
test('should complete purchase', async ({ loginPage, productListPage, checkoutPage }) => {
  await loginPage.goto();
  await loginPage.login('user@test.com', 'password');

  await productListPage.goto();
  const products = await productListPage.getProductCards();
  await products[0].addToCart();

  // ... continue with checkout
});
```

## Best Practices

### Locator Strategy

```typescript
// ✅ Good: Use data-testid
readonly submitButton = page.locator('[data-testid="submit-button"]');

// ✅ Good: Use accessible roles
readonly submitButton = page.getByRole('button', { name: 'Submit' });

// ❌ Bad: Use CSS classes or complex selectors
readonly submitButton = page.locator('.btn.btn-primary.submit');

// ❌ Bad: Use XPath
readonly submitButton = page.locator('//button[@class="submit"]');
```

### Keep Page Objects Focused

```typescript
// ✅ Good: One page, one page object
class LoginPage { /* login functionality only */ }
class RegistrationPage { /* registration functionality only */ }

// ❌ Bad: God page object
class AuthPage {
  // Login, registration, password reset, 2FA, social login...
}
```

### Don't Assert in Page Objects

```typescript
// ✅ Good: Return data, assert in tests
async getErrorMessage(): Promise<string> {
  return this.errorMessage.textContent() ?? '';
}

// In test:
const error = await loginPage.getErrorMessage();
expect(error).toContain('Invalid');

// ❌ Bad: Assert inside page object
async verifyErrorMessage(expected: string): Promise<void> {
  const actual = await this.errorMessage.textContent();
  expect(actual).toContain(expected);
}
```

## Summary

| Element | Location |
|---------|----------|
| Locators | Page Object properties |
| Actions | Page Object methods |
| Assertions | Test files only |
| Wait logic | Page Object methods |
| Navigation | Page Object methods |

## Related Topics

- [E2E Testing Basics](../e2e-testing/e2e-basics.md)
- [Browser Testing](../e2e-testing/browser-testing.md)
- [Test Fixtures](./test-fixtures.md)
