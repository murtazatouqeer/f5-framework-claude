# Angular E2E Testing

## Overview

End-to-end (E2E) testing verifies the complete user flow through the application. Angular CLI projects can use Cypress, Playwright, or other E2E frameworks.

## Playwright Setup

### Installation

```bash
# Add Playwright to Angular project
ng add @playwright/test

# Or install directly
npm install -D @playwright/test
npx playwright install
```

### Configuration

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
    baseURL: 'http://localhost:4200',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
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
  ],
  webServer: {
    command: 'ng serve',
    url: 'http://localhost:4200',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Basic E2E Tests

### Navigation Test

```typescript
// e2e/navigation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should navigate to home page', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/My App/);
    await expect(page.locator('h1')).toContainText('Welcome');
  });

  test('should navigate to about page', async ({ page }) => {
    await page.goto('/');

    await page.click('a[href="/about"]');

    await expect(page).toHaveURL('/about');
    await expect(page.locator('h1')).toContainText('About');
  });

  test('should show 404 for invalid route', async ({ page }) => {
    await page.goto('/invalid-route');

    await expect(page.locator('.not-found')).toBeVisible();
  });
});
```

### Authentication Flow

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('.user-name')).toContainText('user@example.com');
  });

  test('should show validation errors', async ({ page }) => {
    await page.goto('/login');

    await page.click('button[type="submit"]');

    await expect(page.locator('.error-message')).toHaveCount(2);
    await expect(page.locator('.error-message').first()).toContainText('Email is required');
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login');

    await page.fill('input[name="email"]', 'wrong@example.com');
    await page.fill('input[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('.login-error')).toContainText('Invalid credentials');
  });

  test('should logout', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('input[name="email"]', 'user@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Then logout
    await page.click('button.logout');

    await expect(page).toHaveURL('/login');
  });
});
```

## Form Testing

```typescript
// e2e/forms.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Registration Form', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/register');
  });

  test('should register new user', async ({ page }) => {
    await page.fill('input[name="firstName"]', 'John');
    await page.fill('input[name="lastName"]', 'Doe');
    await page.fill('input[name="email"]', `test${Date.now()}@example.com`);
    await page.fill('input[name="password"]', 'SecurePass123!');
    await page.fill('input[name="confirmPassword"]', 'SecurePass123!');

    await page.check('input[name="acceptTerms"]');

    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('.welcome-message')).toContainText('Welcome, John');
  });

  test('should validate password match', async ({ page }) => {
    await page.fill('input[name="password"]', 'password123');
    await page.fill('input[name="confirmPassword"]', 'different');

    await page.click('button[type="submit"]');

    await expect(page.locator('.error-message')).toContainText('Passwords do not match');
  });

  test('should validate email format', async ({ page }) => {
    await page.fill('input[name="email"]', 'invalid-email');
    await page.press('input[name="email"]', 'Tab');

    await expect(page.locator('.error-message')).toContainText('Invalid email');
  });
});
```

## CRUD Operations

```typescript
// e2e/products.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Product Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('input[name="email"]', 'admin@example.com');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.goto('/products');
  });

  test('should display product list', async ({ page }) => {
    await expect(page.locator('.product-card')).toHaveCount.greaterThan(0);
  });

  test('should search products', async ({ page }) => {
    await page.fill('input[name="search"]', 'laptop');
    await page.waitForResponse('**/api/products?*');

    const products = page.locator('.product-card');
    await expect(products).toHaveCount.greaterThan(0);

    for (const product of await products.all()) {
      await expect(product).toContainText(/laptop/i);
    }
  });

  test('should create new product', async ({ page }) => {
    await page.click('button.add-product');

    await page.fill('input[name="name"]', 'Test Product');
    await page.fill('input[name="price"]', '99.99');
    await page.fill('textarea[name="description"]', 'Test description');
    await page.selectOption('select[name="category"]', 'electronics');

    await page.click('button[type="submit"]');

    await expect(page.locator('.toast-success')).toContainText('Product created');
    await expect(page.locator('.product-card:has-text("Test Product")')).toBeVisible();
  });

  test('should edit product', async ({ page }) => {
    await page.click('.product-card:first-child .edit-button');

    await page.fill('input[name="price"]', '149.99');
    await page.click('button[type="submit"]');

    await expect(page.locator('.toast-success')).toContainText('Product updated');
  });

  test('should delete product', async ({ page }) => {
    const productCount = await page.locator('.product-card').count();

    await page.click('.product-card:first-child .delete-button');
    await page.click('.confirm-dialog .confirm-button');

    await expect(page.locator('.product-card')).toHaveCount(productCount - 1);
  });
});
```

## API Mocking

```typescript
// e2e/mocking.spec.ts
import { test, expect } from '@playwright/test';

test.describe('API Mocking', () => {
  test('should display mocked data', async ({ page }) => {
    // Mock API response
    await page.route('**/api/users', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: 'Mock User 1' },
          { id: 2, name: 'Mock User 2' },
        ]),
      });
    });

    await page.goto('/users');

    await expect(page.locator('.user-item')).toHaveCount(2);
    await expect(page.locator('.user-item').first()).toContainText('Mock User 1');
  });

  test('should handle API error', async ({ page }) => {
    await page.route('**/api/users', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Server error' }),
      });
    });

    await page.goto('/users');

    await expect(page.locator('.error-message')).toContainText('Failed to load users');
  });

  test('should handle slow API', async ({ page }) => {
    await page.route('**/api/users', async (route) => {
      await new Promise(resolve => setTimeout(resolve, 2000));
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([]),
      });
    });

    await page.goto('/users');

    // Should show loading state
    await expect(page.locator('.loading-spinner')).toBeVisible();

    // Then show content
    await expect(page.locator('.loading-spinner')).not.toBeVisible({ timeout: 5000 });
  });
});
```

## Page Object Model

```typescript
// e2e/pages/login.page.ts
import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.locator('input[name="email"]');
    this.passwordInput = page.locator('input[name="password"]');
    this.submitButton = page.locator('button[type="submit"]');
    this.errorMessage = page.locator('.error-message');
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async getErrorMessage() {
    return this.errorMessage.textContent();
  }
}

// e2e/pages/dashboard.page.ts
export class DashboardPage {
  readonly page: Page;
  readonly welcomeMessage: Locator;
  readonly logoutButton: Locator;

  constructor(page: Page) {
    this.page = page;
    this.welcomeMessage = page.locator('.welcome-message');
    this.logoutButton = page.locator('button.logout');
  }

  async logout() {
    await this.logoutButton.click();
  }
}

// e2e/auth-pom.spec.ts
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/login.page';
import { DashboardPage } from './pages/dashboard.page';

test.describe('Authentication with POM', () => {
  test('should login successfully', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    await loginPage.goto();
    await loginPage.login('user@example.com', 'password123');

    await expect(page).toHaveURL('/dashboard');
    await expect(dashboardPage.welcomeMessage).toBeVisible();
  });
});
```

## Fixtures and Hooks

```typescript
// e2e/fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/login.page';
import { DashboardPage } from './pages/dashboard.page';

type MyFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
  authenticatedPage: void;
};

export const test = base.extend<MyFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },

  authenticatedPage: async ({ page }, use) => {
    // Login before test
    const loginPage = new LoginPage(page);
    await loginPage.goto();
    await loginPage.login('user@example.com', 'password123');

    await use();

    // Logout after test (cleanup)
    const dashboardPage = new DashboardPage(page);
    await dashboardPage.logout();
  },
});

export { expect } from '@playwright/test';

// Usage
import { test, expect } from './fixtures';

test('should access dashboard', async ({ authenticatedPage, dashboardPage }) => {
  await expect(dashboardPage.welcomeMessage).toBeVisible();
});
```

## Visual Testing

```typescript
// e2e/visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('should match homepage snapshot', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveScreenshot('homepage.png');
  });

  test('should match component snapshot', async ({ page }) => {
    await page.goto('/components/button');

    const button = page.locator('.primary-button');
    await expect(button).toHaveScreenshot('primary-button.png');
  });

  test('should match full page snapshot', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page).toHaveScreenshot('dashboard-full.png', {
      fullPage: true,
    });
  });

  test('should handle responsive snapshots', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');

    await expect(page).toHaveScreenshot('homepage-mobile.png');
  });
});
```

## Accessibility Testing

```typescript
// e2e/accessibility.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('Accessibility', () => {
  test('should not have accessibility violations on homepage', async ({ page }) => {
    await page.goto('/');

    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should not have accessibility violations on login form', async ({ page }) => {
    await page.goto('/login');

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('form')
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper focus management', async ({ page }) => {
    await page.goto('/login');

    // Tab through form elements
    await page.keyboard.press('Tab');
    await expect(page.locator('input[name="email"]')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('input[name="password"]')).toBeFocused();

    await page.keyboard.press('Tab');
    await expect(page.locator('button[type="submit"]')).toBeFocused();
  });
});
```

## Running Tests

```bash
# Run all tests
npx playwright test

# Run specific test file
npx playwright test e2e/auth.spec.ts

# Run tests in headed mode
npx playwright test --headed

# Run tests in specific browser
npx playwright test --project=chromium

# Run tests with UI
npx playwright test --ui

# Show report
npx playwright show-report

# Debug tests
npx playwright test --debug
```

## Best Practices

1. **Use Page Object Model**: Encapsulate page interactions
2. **Keep tests independent**: Each test should set up its own state
3. **Use meaningful selectors**: data-testid, roles, labels
4. **Handle async properly**: Use proper waits and assertions
5. **Mock external services**: For reliable, fast tests
6. **Test realistic scenarios**: Focus on user journeys
7. **Run in CI/CD**: Automate test execution
8. **Monitor test stability**: Track flaky tests
