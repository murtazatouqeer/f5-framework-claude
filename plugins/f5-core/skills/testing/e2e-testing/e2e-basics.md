---
name: e2e-test-basics
description: End-to-end testing fundamentals
category: testing/e2e-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# End-to-End Testing Basics

## Overview

E2E tests verify complete user workflows through the entire system,
from UI to database and back.

## When to Use E2E Tests

| Good Use Cases | Poor Use Cases |
|----------------|----------------|
| Critical user journeys | Unit logic testing |
| Payment flows | Edge cases |
| Authentication | Algorithmic testing |
| Cross-service workflows | Rapid iteration |
| Smoke tests | High-frequency changes |

## Playwright Example

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should login with valid credentials', async ({ page }) => {
    // Navigate to login
    await page.click('text=Sign In');

    // Fill form
    await page.fill('[data-testid="email-input"]', 'user@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');

    // Submit
    await page.click('[data-testid="login-button"]');

    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome-message"]'))
      .toContainText('Welcome, User');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.click('text=Sign In');
    await page.fill('[data-testid="email-input"]', 'wrong@example.com');
    await page.fill('[data-testid="password-input"]', 'wrongpassword');
    await page.click('[data-testid="login-button"]');

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]'))
      .toBeVisible();
    await expect(page.locator('[data-testid="error-message"]'))
      .toContainText('Invalid credentials');

    // Should stay on login page
    await expect(page).toHaveURL('/login');
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await loginAs(page, 'user@example.com', 'password123');

    // Logout
    await page.click('[data-testid="user-menu"]');
    await page.click('text=Logout');

    // Verify redirect to home
    await expect(page).toHaveURL('/');
    await expect(page.locator('[data-testid="login-link"]')).toBeVisible();
  });
});

// e2e/helpers/auth.helper.ts
export async function loginAs(
  page: Page,
  email: string,
  password: string
): Promise<void> {
  await page.goto('/login');
  await page.fill('[data-testid="email-input"]', email);
  await page.fill('[data-testid="password-input"]', password);
  await page.click('[data-testid="login-button"]');
  await page.waitForURL('/dashboard');
}
```

## Page Object Model

```typescript
// e2e/pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly loginButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('[data-testid="email-input"]');
    this.passwordInput = page.locator('[data-testid="password-input"]');
    this.loginButton = page.locator('[data-testid="login-button"]');
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  async goto(): Promise<void> {
    await this.page.goto('/login');
  }

  async login(email: string, password: string): Promise<void> {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }
}

// e2e/pages/dashboard.page.ts
export class DashboardPage {
  readonly page: Page;
  readonly welcomeMessage: Locator;
  readonly userMenu: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.welcomeMessage = page.locator('[data-testid="welcome-message"]');
    this.userMenu = page.locator('[data-testid="user-menu"]');
    this.logoutButton = page.locator('text=Logout');
  }

  async logout(): Promise<void> {
    await this.userMenu.click();
    await this.logoutButton.click();
  }
}

// Using Page Objects
test('should complete checkout flow', async ({ page }) => {
  const loginPage = new LoginPage(page);
  const productPage = new ProductPage(page);
  const cartPage = new CartPage(page);
  const checkoutPage = new CheckoutPage(page);

  // Login
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password');

  // Add product to cart
  await productPage.goto('product-123');
  await productPage.addToCart();

  // Checkout
  await cartPage.goto();
  await cartPage.proceedToCheckout();

  await checkoutPage.fillShippingAddress({
    street: '123 Main St',
    city: 'New York',
    zip: '10001',
  });
  await checkoutPage.fillPaymentDetails({
    cardNumber: '4242424242424242',
    expiry: '12/25',
    cvv: '123',
  });
  await checkoutPage.placeOrder();

  // Verify
  await expect(page).toHaveURL(/\/orders\/\d+/);
  await expect(page.locator('[data-testid="order-confirmation"]'))
    .toContainText('Order placed successfully');
});
```

## API E2E Testing

```typescript
// e2e/api/orders.api.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Orders API', () => {
  let authToken: string;

  test.beforeAll(async ({ request }) => {
    // Get auth token
    const response = await request.post('/api/auth/login', {
      data: {
        email: 'test@example.com',
        password: 'password123',
      },
    });
    const body = await response.json();
    authToken = body.token;
  });

  test('should create order via API', async ({ request }) => {
    const response = await request.post('/api/orders', {
      headers: {
        Authorization: `Bearer ${authToken}`,
      },
      data: {
        items: [
          { productId: 'p1', quantity: 2 },
          { productId: 'p2', quantity: 1 },
        ],
      },
    });

    expect(response.ok()).toBeTruthy();

    const order = await response.json();
    expect(order.id).toBeDefined();
    expect(order.items).toHaveLength(2);
    expect(order.status).toBe('pending');
  });

  test('should get order details', async ({ request }) => {
    // Create order first
    const createResponse = await request.post('/api/orders', {
      headers: { Authorization: `Bearer ${authToken}` },
      data: { items: [{ productId: 'p1', quantity: 1 }] },
    });
    const { id } = await createResponse.json();

    // Get order
    const response = await request.get(`/api/orders/${id}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    expect(response.ok()).toBeTruthy();
    const order = await response.json();
    expect(order.id).toBe(id);
  });
});
```

## Test Configuration

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  webServer: {
    command: 'npm run start',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Test Data Setup

```typescript
// e2e/fixtures/test-data.ts
import { test as base } from '@playwright/test';

interface TestData {
  user: { email: string; password: string };
  product: { id: string; name: string; price: number };
}

export const test = base.extend<{ testData: TestData }>({
  testData: async ({ request }, use) => {
    // Setup test data via API
    const userResponse = await request.post('/api/test/users', {
      data: { email: `test-${Date.now()}@example.com` },
    });
    const user = await userResponse.json();

    const productResponse = await request.post('/api/test/products', {
      data: { name: 'Test Product', price: 99.99 },
    });
    const product = await productResponse.json();

    // Provide data to test
    await use({
      user: { email: user.email, password: 'password123' },
      product,
    });

    // Cleanup after test
    await request.delete(`/api/test/users/${user.id}`);
    await request.delete(`/api/test/products/${product.id}`);
  },
});

// Usage
test('should add product to cart', async ({ page, testData }) => {
  await page.goto(`/products/${testData.product.id}`);
  await page.click('[data-testid="add-to-cart"]');
  // ...
});
```

## Best Practices

| Do | Don't |
|----|-------|
| Use data-testid attributes | Rely on text or CSS classes |
| Implement Page Object Model | Put selectors in tests |
| Test critical user paths | Test every feature |
| Use proper waits | Use sleep/fixed delays |
| Clean up test data | Leave test data behind |
| Run in CI pipeline | Only run locally |

## Common Patterns

### Waiting for Elements

```typescript
// Wait for element to be visible
await page.waitForSelector('[data-testid="modal"]');

// Wait for element to disappear
await page.waitForSelector('[data-testid="loading"]', { state: 'hidden' });

// Wait for navigation
await Promise.all([
  page.waitForNavigation(),
  page.click('[data-testid="submit"]'),
]);

// Wait for network idle
await page.waitForLoadState('networkidle');

// Wait for specific response
const responsePromise = page.waitForResponse('**/api/orders');
await page.click('[data-testid="submit"]');
const response = await responsePromise;
```

### Handling Dialogs

```typescript
// Accept dialog
page.on('dialog', dialog => dialog.accept());

// Dismiss dialog
page.on('dialog', dialog => dialog.dismiss());

// Custom handling
page.on('dialog', async dialog => {
  expect(dialog.message()).toContain('Are you sure?');
  await dialog.accept();
});
```

## Related Topics

- [Browser Testing](./browser-testing.md)
- [Visual Regression](./visual-regression.md)
- [Page Object Model](../patterns/page-object-model.md)
