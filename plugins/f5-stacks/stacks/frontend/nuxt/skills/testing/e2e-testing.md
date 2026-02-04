---
name: nuxt-e2e-testing
description: End-to-end testing with Playwright in Nuxt 3
applies_to: nuxt
---

# E2E Testing with Playwright

## Overview

Playwright enables end-to-end testing of Nuxt applications with real browser automation.

## Setup

```bash
npm install -D @playwright/test
npx playwright install
```

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
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
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## Basic Tests

### Navigation Test

```typescript
// tests/e2e/navigation.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('homepage loads', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveTitle(/My App/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('navigates to about page', async ({ page }) => {
    await page.goto('/');

    await page.click('text=About');

    await expect(page).toHaveURL('/about');
    await expect(page.getByRole('heading', { name: 'About' })).toBeVisible();
  });

  test('404 page for invalid routes', async ({ page }) => {
    await page.goto('/invalid-page');

    await expect(page.getByText('404')).toBeVisible();
  });
});
```

### Form Interaction

```typescript
// tests/e2e/login.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Login', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('shows validation errors', async ({ page }) => {
    await page.getByRole('button', { name: 'Login' }).click();

    await expect(page.getByText('Email is required')).toBeVisible();
    await expect(page.getByText('Password is required')).toBeVisible();
  });

  test('logs in successfully', async ({ page }) => {
    await page.getByLabel('Email').fill('user@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Login' }).click();

    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByText('Welcome')).toBeVisible();
  });

  test('shows error for invalid credentials', async ({ page }) => {
    await page.getByLabel('Email').fill('user@example.com');
    await page.getByLabel('Password').fill('wrongpassword');
    await page.getByRole('button', { name: 'Login' }).click();

    await expect(page.getByText('Invalid credentials')).toBeVisible();
  });
});
```

## Data-Driven Tests

### Products CRUD

```typescript
// tests/e2e/products.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Products', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('/dashboard');
  });

  test('lists products', async ({ page }) => {
    await page.goto('/products');

    await expect(page.getByTestId('product-card')).toHaveCount(10);
  });

  test('searches products', async ({ page }) => {
    await page.goto('/products');

    await page.getByPlaceholder('Search...').fill('laptop');
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\?q=laptop/);
    await expect(page.getByTestId('product-card').first()).toContainText('laptop', { ignoreCase: true });
  });

  test('creates a new product', async ({ page }) => {
    await page.goto('/products/new');

    await page.getByLabel('Name').fill('Test Product');
    await page.getByLabel('Description').fill('A test product description');
    await page.getByLabel('Price').fill('99.99');
    await page.getByLabel('Category').selectOption('electronics');

    await page.getByRole('button', { name: 'Create' }).click();

    await expect(page.getByText('Product created')).toBeVisible();
    await expect(page).toHaveURL(/\/products\/[\w-]+/);
  });

  test('edits a product', async ({ page }) => {
    await page.goto('/products');

    await page.getByTestId('product-card').first().click();
    await page.getByRole('button', { name: 'Edit' }).click();

    await page.getByLabel('Name').fill('Updated Product');
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Product updated')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Updated Product' })).toBeVisible();
  });

  test('deletes a product', async ({ page }) => {
    await page.goto('/products');

    const firstProduct = page.getByTestId('product-card').first();
    const productName = await firstProduct.getByRole('heading').textContent();

    await firstProduct.getByRole('button', { name: 'Delete' }).click();

    // Confirm dialog
    await page.getByRole('button', { name: 'Confirm' }).click();

    await expect(page.getByText('Product deleted')).toBeVisible();
    await expect(page.getByText(productName!)).not.toBeVisible();
  });
});
```

## Authentication Fixtures

```typescript
// tests/e2e/fixtures.ts
import { test as base, expect } from '@playwright/test';

type Fixtures = {
  authenticatedPage: Page;
  adminPage: Page;
};

export const test = base.extend<Fixtures>({
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('user@example.com');
    await page.getByLabel('Password').fill('password123');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('/dashboard');

    await use(page);
  },

  adminPage: async ({ page }, use) => {
    await page.goto('/login');
    await page.getByLabel('Email').fill('admin@example.com');
    await page.getByLabel('Password').fill('admin123');
    await page.getByRole('button', { name: 'Login' }).click();
    await page.waitForURL('/dashboard');

    await use(page);
  },
});

export { expect };
```

```typescript
// tests/e2e/admin.spec.ts
import { test, expect } from './fixtures';

test.describe('Admin Panel', () => {
  test('admin can access admin panel', async ({ adminPage }) => {
    await adminPage.goto('/admin');

    await expect(adminPage.getByRole('heading', { name: 'Admin Panel' })).toBeVisible();
  });

  test('regular user cannot access admin panel', async ({ authenticatedPage }) => {
    await authenticatedPage.goto('/admin');

    await expect(authenticatedPage).toHaveURL('/unauthorized');
  });
});
```

## Visual Testing

```typescript
// tests/e2e/visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('homepage matches snapshot', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveScreenshot('homepage.png', {
      fullPage: true,
    });
  });

  test('product card matches snapshot', async ({ page }) => {
    await page.goto('/products');

    const card = page.getByTestId('product-card').first();
    await expect(card).toHaveScreenshot('product-card.png');
  });
});
```

## API Mocking

```typescript
// tests/e2e/mocked.spec.ts
import { test, expect } from '@playwright/test';

test.describe('With Mocked API', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/products', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            { id: '1', name: 'Mocked Product', price: 10 },
          ],
          total: 1,
        }),
      });
    });
  });

  test('displays mocked products', async ({ page }) => {
    await page.goto('/products');

    await expect(page.getByText('Mocked Product')).toBeVisible();
  });
});
```

## Mobile Testing

```typescript
// tests/e2e/mobile.spec.ts
import { test, expect, devices } from '@playwright/test';

test.use(devices['iPhone 13']);

test.describe('Mobile Experience', () => {
  test('shows mobile menu', async ({ page }) => {
    await page.goto('/');

    // Desktop menu should be hidden
    await expect(page.getByTestId('desktop-nav')).not.toBeVisible();

    // Mobile menu button should be visible
    const menuButton = page.getByRole('button', { name: 'Menu' });
    await expect(menuButton).toBeVisible();

    // Open mobile menu
    await menuButton.click();
    await expect(page.getByTestId('mobile-nav')).toBeVisible();
  });

  test('responsive product grid', async ({ page }) => {
    await page.goto('/products');

    // Should show 1 column on mobile
    const grid = page.getByTestId('product-grid');
    await expect(grid).toHaveCSS('grid-template-columns', '1fr');
  });
});
```

## Performance Testing

```typescript
// tests/e2e/performance.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Performance', () => {
  test('page loads within 3 seconds', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(3000);
  });

  test('measures core web vitals', async ({ page }) => {
    await page.goto('/');

    const metrics = await page.evaluate(() =>
      new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          resolve({
            lcp: entries.find((e) => e.entryType === 'largest-contentful-paint'),
            fid: entries.find((e) => e.entryType === 'first-input'),
            cls: entries.find((e) => e.entryType === 'layout-shift'),
          });
        }).observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });
      })
    );

    console.log('Web Vitals:', metrics);
  });
});
```

## Best Practices

1. **Use page objects** - Encapsulate page interactions
2. **Fixtures for auth** - Reusable authentication
3. **Mock when needed** - Control API responses
4. **Test critical paths** - Login, checkout, core features
5. **Visual regression** - Catch UI changes
6. **Cross-browser** - Test multiple browsers
