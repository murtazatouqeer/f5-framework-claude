# E2E Testing Patterns

End-to-end testing with Playwright, Cypress, and browser automation.

## Table of Contents

1. [Overview](#overview)
2. [Playwright Setup](#playwright-setup)
3. [Cypress Setup](#cypress-setup)
4. [Visual Regression Testing](#visual-regression-testing)
5. [Cross-Browser Testing](#cross-browser-testing)

---

## Overview

### When to Use E2E Tests

| Scenario | E2E Test? |
|----------|-----------|
| Critical user journeys | ✅ Yes |
| Payment flows | ✅ Yes |
| Authentication | ✅ Yes |
| Complex workflows | ✅ Yes |
| Simple CRUD | ⚠️ Maybe (integration preferred) |
| Business logic | ❌ No (unit test) |

### E2E Test Characteristics

- Slowest tests (seconds to minutes)
- Highest confidence level
- Most expensive to maintain
- Test full user experience
- Use real browser rendering

---

## Playwright Setup

### Installation

```bash
npm init playwright@latest

# Install browsers
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
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
  ],
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

### Basic Test Structure

```typescript
// e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('should login with valid credentials', async ({ page }) => {
    // Navigate to login
    await page.click('text=Login');

    // Fill form
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'password123');

    // Submit
    await page.click('button[type="submit"]');

    // Assert success
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Welcome back')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.click('text=Login');
    await page.fill('[name="email"]', 'wrong@example.com');
    await page.fill('[name="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('.error-message')).toContainText(
      'Invalid credentials'
    );
  });

  test('should logout user', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    // Logout
    await page.click('[data-testid="user-menu"]');
    await page.click('text=Logout');

    // Assert logged out
    await expect(page).toHaveURL('/');
    await expect(page.locator('text=Login')).toBeVisible();
  });
});
```

### Page Object Model

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
    this.emailInput = page.locator('[name="email"]');
    this.passwordInput = page.locator('[name="password"]');
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

  async getErrorMessage(): Promise<string> {
    return await this.errorMessage.textContent() || '';
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
    this.welcomeMessage = page.locator('[data-testid="welcome"]');
    this.userMenu = page.locator('[data-testid="user-menu"]');
    this.logoutButton = page.locator('text=Logout');
  }

  async logout() {
    await this.userMenu.click();
    await this.logoutButton.click();
  }
}

// e2e/auth.spec.ts (using page objects)
import { test, expect } from '@playwright/test';
import { LoginPage } from './pages/login.page';
import { DashboardPage } from './pages/dashboard.page';

test.describe('Authentication with Page Objects', () => {
  test('should login successfully', async ({ page }) => {
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    await loginPage.goto();
    await loginPage.login('user@example.com', 'password123');

    await expect(dashboardPage.welcomeMessage).toBeVisible();
  });
});
```

### Fixtures and Authentication

```typescript
// e2e/fixtures/auth.fixture.ts
import { test as base, Page } from '@playwright/test';

type AuthFixtures = {
  authenticatedPage: Page;
  adminPage: Page;
};

export const test = base.extend<AuthFixtures>({
  authenticatedPage: async ({ page }, use) => {
    // Login as regular user
    await page.goto('/login');
    await page.fill('[name="email"]', 'user@example.com');
    await page.fill('[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    await use(page);
  },

  adminPage: async ({ page }, use) => {
    // Login as admin
    await page.goto('/login');
    await page.fill('[name="email"]', 'admin@example.com');
    await page.fill('[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/admin');

    await use(page);
  },
});

export { expect } from '@playwright/test';

// Usage
import { test, expect } from './fixtures/auth.fixture';

test('user can view dashboard', async ({ authenticatedPage }) => {
  await expect(authenticatedPage.locator('h1')).toContainText('Dashboard');
});

test('admin can manage users', async ({ adminPage }) => {
  await adminPage.click('text=Users');
  await expect(adminPage.locator('table')).toBeVisible();
});
```

### API Mocking

```typescript
test('should handle API errors gracefully', async ({ page }) => {
  // Mock API to return error
  await page.route('**/api/users', route => {
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: JSON.stringify({ error: 'Internal Server Error' }),
    });
  });

  await page.goto('/users');

  await expect(page.locator('.error-banner')).toContainText(
    'Failed to load users'
  );
});

test('should show loading state', async ({ page }) => {
  // Delay API response
  await page.route('**/api/users', async route => {
    await new Promise(resolve => setTimeout(resolve, 2000));
    route.fulfill({
      status: 200,
      body: JSON.stringify([{ id: 1, name: 'User' }]),
    });
  });

  await page.goto('/users');

  await expect(page.locator('.loading-spinner')).toBeVisible();
  await expect(page.locator('.user-list')).toBeVisible({ timeout: 5000 });
});
```

---

## Cypress Setup

### Installation

```bash
npm install cypress --save-dev
npx cypress open
```

### Configuration

```typescript
// cypress.config.ts
import { defineConfig } from 'cypress';

export default defineConfig({
  e2e: {
    baseUrl: 'http://localhost:3000',
    viewportWidth: 1280,
    viewportHeight: 720,
    video: true,
    screenshotOnRunFailure: true,
    retries: {
      runMode: 2,
      openMode: 0,
    },
    setupNodeEvents(on, config) {
      // Plugins
    },
  },
});
```

### Basic Tests

```typescript
// cypress/e2e/auth.cy.ts
describe('Authentication', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should login successfully', () => {
    cy.contains('Login').click();

    cy.get('[name="email"]').type('user@example.com');
    cy.get('[name="password"]').type('password123');
    cy.get('button[type="submit"]').click();

    cy.url().should('include', '/dashboard');
    cy.contains('Welcome back').should('be.visible');
  });

  it('should show validation errors', () => {
    cy.contains('Login').click();
    cy.get('button[type="submit"]').click();

    cy.contains('Email is required').should('be.visible');
    cy.contains('Password is required').should('be.visible');
  });
});
```

### Custom Commands

```typescript
// cypress/support/commands.ts
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.session([email, password], () => {
    cy.visit('/login');
    cy.get('[name="email"]').type(email);
    cy.get('[name="password"]').type(password);
    cy.get('button[type="submit"]').click();
    cy.url().should('include', '/dashboard');
  });
});

Cypress.Commands.add('loginAsAdmin', () => {
  cy.login('admin@example.com', 'admin123');
});

// Usage
describe('Protected Routes', () => {
  beforeEach(() => {
    cy.login('user@example.com', 'password123');
  });

  it('should access dashboard', () => {
    cy.visit('/dashboard');
    cy.contains('Welcome').should('be.visible');
  });
});
```

### API Interception

```typescript
describe('API Handling', () => {
  it('should display users from API', () => {
    cy.intercept('GET', '/api/users', {
      statusCode: 200,
      body: [
        { id: 1, name: 'John' },
        { id: 2, name: 'Jane' },
      ],
    }).as('getUsers');

    cy.visit('/users');
    cy.wait('@getUsers');

    cy.contains('John').should('be.visible');
    cy.contains('Jane').should('be.visible');
  });

  it('should handle API errors', () => {
    cy.intercept('GET', '/api/users', {
      statusCode: 500,
      body: { error: 'Server Error' },
    }).as('getUsersError');

    cy.visit('/users');
    cy.wait('@getUsersError');

    cy.contains('Failed to load').should('be.visible');
  });
});
```

---

## Visual Regression Testing

### Playwright Visual Comparisons

```typescript
test('homepage should match snapshot', async ({ page }) => {
  await page.goto('/');

  // Full page screenshot
  await expect(page).toHaveScreenshot('homepage.png');
});

test('component should match snapshot', async ({ page }) => {
  await page.goto('/components');

  const button = page.locator('.primary-button');
  await expect(button).toHaveScreenshot('primary-button.png');
});

test('should compare with options', async ({ page }) => {
  await page.goto('/');

  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixels: 100, // Allow small differences
    threshold: 0.2,     // 20% threshold
    animations: 'disabled',
  });
});
```

### Handling Dynamic Content

```typescript
test('should mask dynamic content', async ({ page }) => {
  await page.goto('/dashboard');

  await expect(page).toHaveScreenshot('dashboard.png', {
    mask: [
      page.locator('.timestamp'),
      page.locator('.user-avatar'),
      page.locator('.dynamic-chart'),
    ],
  });
});

test('should wait for stable content', async ({ page }) => {
  await page.goto('/charts');

  // Wait for animations
  await page.waitForTimeout(1000);

  // Or wait for specific element
  await page.waitForSelector('.chart-loaded');

  await expect(page).toHaveScreenshot('charts.png');
});
```

### Percy Integration

```typescript
// Install: npm install @percy/playwright

import { test } from '@playwright/test';
import percySnapshot from '@percy/playwright';

test('visual regression with Percy', async ({ page }) => {
  await page.goto('/');

  await percySnapshot(page, 'Homepage');

  await page.click('text=Login');
  await percySnapshot(page, 'Login Page');
});
```

---

## Cross-Browser Testing

### Playwright Multi-Browser

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },

    // Mobile
    { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
    { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } },

    // Tablets
    { name: 'iPad', use: { ...devices['iPad Pro'] } },
  ],
});
```

### Browser-Specific Tests

```typescript
test('should work on mobile', async ({ page, isMobile }) => {
  await page.goto('/');

  if (isMobile) {
    // Mobile-specific assertions
    await expect(page.locator('.mobile-menu')).toBeVisible();
    await expect(page.locator('.desktop-nav')).not.toBeVisible();
  } else {
    await expect(page.locator('.desktop-nav')).toBeVisible();
  }
});

test.describe('Desktop only', () => {
  test.skip(({ isMobile }) => isMobile);

  test('should show desktop features', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('.desktop-widget')).toBeVisible();
  });
});
```

### Responsive Testing

```typescript
const viewports = [
  { width: 375, height: 667, name: 'iPhone SE' },
  { width: 768, height: 1024, name: 'iPad' },
  { width: 1280, height: 720, name: 'Desktop' },
  { width: 1920, height: 1080, name: 'Full HD' },
];

for (const viewport of viewports) {
  test(`should render correctly on ${viewport.name}`, async ({ page }) => {
    await page.setViewportSize({
      width: viewport.width,
      height: viewport.height,
    });

    await page.goto('/');

    await expect(page).toHaveScreenshot(`homepage-${viewport.name}.png`);
  });
}
```

---

## Best Practices

### Reliable Selectors

```typescript
// ✅ Good - data-testid
await page.click('[data-testid="submit-button"]');

// ✅ Good - role-based
await page.click('button:has-text("Submit")');
await page.getByRole('button', { name: 'Submit' }).click();

// ⚠️ Okay - semantic HTML
await page.click('button[type="submit"]');

// ❌ Avoid - CSS classes (can change)
await page.click('.btn-primary-large');

// ❌ Avoid - complex selectors
await page.click('div > div > button:nth-child(2)');
```

### Waiting Strategies

```typescript
// ✅ Explicit waits
await page.waitForSelector('.content-loaded');
await expect(page.locator('.data')).toBeVisible();

// ✅ Wait for network
await page.waitForResponse(resp =>
  resp.url().includes('/api/data') && resp.status() === 200
);

// ❌ Avoid arbitrary waits
await page.waitForTimeout(5000);
```

### Test Isolation

```typescript
test.describe('Shopping Cart', () => {
  test.beforeEach(async ({ page }) => {
    // Clean state before each test
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());
  });

  test('should add item to cart', async ({ page }) => {
    // Test with clean state
  });
});
```

### Error Handling

```typescript
test('should handle network failure', async ({ page }) => {
  // Simulate offline
  await page.context().setOffline(true);

  await page.goto('/');

  await expect(page.locator('.offline-message')).toBeVisible();

  // Restore connection
  await page.context().setOffline(false);
  await page.reload();

  await expect(page.locator('.offline-message')).not.toBeVisible();
});
```
