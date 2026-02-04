---
name: visual-regression
description: Visual regression testing strategies and tools
category: testing/e2e-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Visual Regression Testing

## Overview

Visual regression testing captures screenshots of UI components or pages
and compares them against baseline images to detect unintended visual changes.

## When to Use Visual Testing

| Good Use Cases | Poor Use Cases |
|----------------|----------------|
| UI components | Dynamic content |
| Design systems | Time-based displays |
| Landing pages | Random/generated content |
| Email templates | User-specific data |
| Style changes | A/B test variations |

## Playwright Visual Testing

### Basic Screenshot Comparison

```typescript
import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('homepage should match snapshot', async ({ page }) => {
    await page.goto('/');

    // Full page screenshot
    await expect(page).toHaveScreenshot('homepage.png');
  });

  test('component should match snapshot', async ({ page }) => {
    await page.goto('/components/button');

    // Element screenshot
    const button = page.locator('[data-testid="primary-button"]');
    await expect(button).toHaveScreenshot('primary-button.png');
  });
});
```

### Configuration Options

```typescript
// playwright.config.ts
export default defineConfig({
  expect: {
    toHaveScreenshot: {
      // Maximum allowed difference threshold
      maxDiffPixels: 100,

      // Or use percentage
      maxDiffPixelRatio: 0.02, // 2%

      // Animation handling
      animations: 'disabled',

      // Wait for fonts
      fonts: 'ready',
    },
  },

  // Update snapshots
  updateSnapshots: 'missing', // 'all' | 'none' | 'missing'
});
```

### Advanced Screenshot Options

```typescript
test('screenshot with options', async ({ page }) => {
  await page.goto('/dashboard');

  await expect(page).toHaveScreenshot('dashboard.png', {
    // Only capture visible part
    fullPage: false,

    // Mask dynamic elements
    mask: [
      page.locator('[data-testid="timestamp"]'),
      page.locator('[data-testid="user-avatar"]'),
      page.locator('[data-testid="random-id"]'),
    ],

    // Disable animations
    animations: 'disabled',

    // Scale for retina
    scale: 'device',

    // Threshold for comparison
    threshold: 0.2,

    // Max different pixels
    maxDiffPixels: 50,
  });
});
```

## Handling Dynamic Content

### Masking Dynamic Elements

```typescript
test('mask dynamic content', async ({ page }) => {
  await page.goto('/user-profile');

  await expect(page).toHaveScreenshot('profile.png', {
    mask: [
      // Mask user-specific content
      page.locator('[data-testid="user-name"]'),
      page.locator('[data-testid="user-email"]'),
      page.locator('[data-testid="last-login"]'),

      // Mask images that might change
      page.locator('img.avatar'),

      // Mask dynamic ads
      page.locator('.advertisement'),
    ],
  });
});
```

### Replacing Dynamic Content

```typescript
test('replace dynamic content', async ({ page }) => {
  await page.goto('/dashboard');

  // Replace dynamic text
  await page.evaluate(() => {
    document.querySelectorAll('[data-testid="timestamp"]').forEach(el => {
      el.textContent = '2024-01-01 00:00:00';
    });

    document.querySelectorAll('[data-testid="random-number"]').forEach(el => {
      el.textContent = '12345';
    });
  });

  await expect(page).toHaveScreenshot('dashboard.png');
});
```

### Waiting for Stability

```typescript
test('wait for stable state', async ({ page }) => {
  await page.goto('/animated-page');

  // Wait for animations to complete
  await page.waitForLoadState('networkidle');

  // Wait for specific animation
  await page.waitForFunction(() => {
    const element = document.querySelector('.animated');
    return element && !element.classList.contains('animating');
  });

  // Disable remaining animations
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0s !important;
        animation-delay: 0s !important;
        transition-duration: 0s !important;
        transition-delay: 0s !important;
      }
    `,
  });

  await expect(page).toHaveScreenshot('stable-page.png');
});
```

## Component Visual Testing

### Testing Component States

```typescript
test.describe('Button Component', () => {
  test('default state', async ({ page }) => {
    await page.goto('/components/button');

    const button = page.locator('[data-testid="button-default"]');
    await expect(button).toHaveScreenshot('button-default.png');
  });

  test('hover state', async ({ page }) => {
    await page.goto('/components/button');

    const button = page.locator('[data-testid="button-default"]');
    await button.hover();
    await expect(button).toHaveScreenshot('button-hover.png');
  });

  test('focus state', async ({ page }) => {
    await page.goto('/components/button');

    const button = page.locator('[data-testid="button-default"]');
    await button.focus();
    await expect(button).toHaveScreenshot('button-focus.png');
  });

  test('disabled state', async ({ page }) => {
    await page.goto('/components/button');

    const button = page.locator('[data-testid="button-disabled"]');
    await expect(button).toHaveScreenshot('button-disabled.png');
  });

  test('all variants', async ({ page }) => {
    await page.goto('/components/button');

    const variants = ['primary', 'secondary', 'danger', 'ghost'];

    for (const variant of variants) {
      const button = page.locator(`[data-testid="button-${variant}"]`);
      await expect(button).toHaveScreenshot(`button-${variant}.png`);
    }
  });
});
```

### Testing Responsive States

```typescript
const viewports = [
  { name: 'mobile', width: 375, height: 667 },
  { name: 'tablet', width: 768, height: 1024 },
  { name: 'desktop', width: 1280, height: 800 },
];

test.describe('Responsive Visual Tests', () => {
  for (const viewport of viewports) {
    test(`header at ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({
        width: viewport.width,
        height: viewport.height,
      });

      await page.goto('/');

      const header = page.locator('header');
      await expect(header).toHaveScreenshot(`header-${viewport.name}.png`);
    });
  }
});
```

## Theme Testing

```typescript
test.describe('Theme Visual Tests', () => {
  test('light theme', async ({ page }) => {
    await page.goto('/');
    await page.emulateMedia({ colorScheme: 'light' });

    await expect(page).toHaveScreenshot('homepage-light.png');
  });

  test('dark theme', async ({ page }) => {
    await page.goto('/');
    await page.emulateMedia({ colorScheme: 'dark' });

    await expect(page).toHaveScreenshot('homepage-dark.png');
  });

  test('high contrast', async ({ page }) => {
    await page.goto('/');
    await page.emulateMedia({ forcedColors: 'active' });

    await expect(page).toHaveScreenshot('homepage-high-contrast.png');
  });
});
```

## Storybook Visual Testing

```typescript
// Using @storybook/test-runner with Playwright
import { TestRunnerConfig } from '@storybook/test-runner';

const config: TestRunnerConfig = {
  async postRender(page, context) {
    // Take screenshot after story renders
    const elementHandler = await page.$('#storybook-root');

    if (elementHandler) {
      const screenshot = await elementHandler.screenshot();
      expect(screenshot).toMatchSnapshot(
        `${context.id}.png`
      );
    }
  },
};

export default config;
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/visual-tests.yml
name: Visual Regression Tests

on:
  pull_request:
    branches: [main]

jobs:
  visual-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run visual tests
        run: npm run test:visual

      - name: Upload diff artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: visual-diff
          path: test-results/
          retention-days: 7

      - name: Update snapshots (on main)
        if: github.ref == 'refs/heads/main'
        run: |
          npm run test:visual:update
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add -A
          git diff-index --quiet HEAD || git commit -m "Update visual snapshots"
          git push
```

### Snapshot Management

```typescript
// scripts/manage-snapshots.ts
import { execSync } from 'child_process';

const command = process.argv[2];

switch (command) {
  case 'update':
    execSync('npx playwright test --update-snapshots', { stdio: 'inherit' });
    break;

  case 'clean':
    execSync('rm -rf tests/**/*.png-snapshots', { stdio: 'inherit' });
    break;

  case 'review':
    // Open snapshot diffs in browser
    execSync('npx playwright show-report', { stdio: 'inherit' });
    break;

  default:
    console.log('Usage: ts-node manage-snapshots.ts [update|clean|review]');
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Mask dynamic content | Timestamps, avatars, IDs |
| Use consistent viewports | Standardize screenshot sizes |
| Disable animations | Prevent flaky comparisons |
| Wait for stability | Network idle, animations done |
| Version snapshots | Store with code |
| Review diffs carefully | Intentional vs accidental |
| Set appropriate thresholds | Balance sensitivity |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Flaky tests | Increase threshold, mask dynamic |
| Font rendering differences | Use consistent fonts, CI-specific |
| Color differences | Use perceptual diff algorithms |
| Layout shifts | Wait for load complete |
| Cross-platform issues | Use platform-specific snapshots |

## Related Topics

- [E2E Basics](./e2e-basics.md)
- [Browser Testing](./browser-testing.md)
- [Page Object Model](../patterns/page-object-model.md)
