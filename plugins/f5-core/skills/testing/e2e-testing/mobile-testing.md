---
name: mobile-testing
description: Mobile app and responsive testing strategies
category: testing/e2e-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Mobile Testing

## Overview

Mobile testing ensures applications work correctly on mobile devices,
including responsive web apps and native mobile applications.

## Mobile Web Testing with Playwright

### Device Emulation

```typescript
import { test, expect, devices } from '@playwright/test';

// Use predefined device
test.use({ ...devices['iPhone 14'] });

test.describe('Mobile Web Tests', () => {
  test('should display mobile layout', async ({ page }) => {
    await page.goto('/');

    // Mobile nav should be visible
    await expect(page.locator('[data-testid="mobile-nav"]')).toBeVisible();

    // Desktop nav should be hidden
    await expect(page.locator('[data-testid="desktop-nav"]')).toBeHidden();
  });
});
```

### Custom Mobile Configuration

```typescript
// playwright.config.ts
export default defineConfig({
  projects: [
    // iOS Devices
    {
      name: 'iPhone SE',
      use: {
        ...devices['iPhone SE'],
      },
    },
    {
      name: 'iPhone 14',
      use: {
        ...devices['iPhone 14'],
      },
    },
    {
      name: 'iPhone 14 Pro Max',
      use: {
        ...devices['iPhone 14 Pro Max'],
      },
    },

    // Android Devices
    {
      name: 'Pixel 5',
      use: {
        ...devices['Pixel 5'],
      },
    },
    {
      name: 'Galaxy S21',
      use: {
        viewport: { width: 360, height: 800 },
        userAgent: 'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36',
        deviceScaleFactor: 3,
        isMobile: true,
        hasTouch: true,
      },
    },

    // Tablets
    {
      name: 'iPad',
      use: {
        ...devices['iPad (gen 7)'],
      },
    },
    {
      name: 'iPad Pro',
      use: {
        ...devices['iPad Pro 11'],
      },
    },
  ],
});
```

## Touch Interactions

```typescript
test.describe('Touch Gestures', () => {
  test.use({ hasTouch: true });

  test('should handle tap', async ({ page }) => {
    await page.goto('/touch-demo');

    await page.tap('[data-testid="tap-target"]');

    await expect(page.locator('[data-testid="tap-result"]'))
      .toHaveText('Tapped!');
  });

  test('should handle long press', async ({ page }) => {
    await page.goto('/touch-demo');

    const element = page.locator('[data-testid="long-press-target"]');
    const box = await element.boundingBox();

    if (box) {
      await page.touchscreen.tap(box.x + box.width / 2, box.y + box.height / 2);

      // Hold for long press (500ms+)
      await page.waitForTimeout(600);
    }

    await expect(page.locator('[data-testid="context-menu"]')).toBeVisible();
  });

  test('should handle swipe on carousel', async ({ page }) => {
    await page.goto('/carousel');

    const carousel = page.locator('[data-testid="carousel"]');
    const box = await carousel.boundingBox();

    if (box) {
      const startX = box.x + box.width * 0.8;
      const endX = box.x + box.width * 0.2;
      const y = box.y + box.height / 2;

      // Swipe left
      await page.touchscreen.tap(startX, y);
      await page.mouse.move(endX, y, { steps: 10 });
      await page.mouse.up();
    }

    // Should show next slide
    await expect(page.locator('[data-testid="slide-2"]')).toBeVisible();
  });

  test('should handle pull to refresh', async ({ page }) => {
    await page.goto('/list');

    const list = page.locator('[data-testid="list-container"]');
    const box = await list.boundingBox();

    if (box) {
      const x = box.x + box.width / 2;
      const startY = box.y + 50;
      const endY = box.y + 200;

      // Pull down
      await page.touchscreen.tap(x, startY);
      await page.mouse.move(x, endY, { steps: 20 });
      await page.mouse.up();
    }

    await expect(page.locator('[data-testid="refreshing"]')).toBeVisible();
    await expect(page.locator('[data-testid="refreshing"]')).toBeHidden();
  });
});
```

## Mobile-Specific Features

### Orientation Testing

```typescript
test.describe('Orientation', () => {
  test('should handle portrait orientation', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/');

    await expect(page.locator('[data-testid="portrait-layout"]')).toBeVisible();
  });

  test('should handle landscape orientation', async ({ page }) => {
    await page.setViewportSize({ width: 812, height: 375 });
    await page.goto('/');

    await expect(page.locator('[data-testid="landscape-layout"]')).toBeVisible();
  });

  test('should adapt on orientation change', async ({ page }) => {
    // Start in portrait
    await page.setViewportSize({ width: 375, height: 812 });
    await page.goto('/video-player');

    await expect(page.locator('[data-testid="portrait-controls"]')).toBeVisible();

    // Change to landscape
    await page.setViewportSize({ width: 812, height: 375 });

    // Should show landscape controls
    await expect(page.locator('[data-testid="landscape-controls"]')).toBeVisible();
    await expect(page.locator('[data-testid="fullscreen-button"]')).toBeVisible();
  });
});
```

### Mobile Inputs

```typescript
test.describe('Mobile Inputs', () => {
  test('should show mobile keyboard', async ({ page }) => {
    await page.goto('/form');

    const input = page.locator('[data-testid="text-input"]');
    await input.focus();

    // Check that input has focus
    await expect(input).toBeFocused();
  });

  test('should use numeric keyboard for number input', async ({ page }) => {
    await page.goto('/form');

    const phoneInput = page.locator('input[type="tel"]');
    const inputMode = await phoneInput.getAttribute('inputmode');

    expect(inputMode).toBe('tel');
  });

  test('should handle camera/gallery access', async ({ page, context }) => {
    await context.grantPermissions(['camera']);

    await page.goto('/upload');

    // Click file input that should trigger camera/gallery
    const fileInput = page.locator('input[type="file"][accept="image/*"]');
    const capture = await fileInput.getAttribute('capture');

    // Mobile should have capture attribute for camera
    expect(capture).toBeDefined();
  });
});
```

### Mobile Navigation

```typescript
test.describe('Mobile Navigation', () => {
  test('should open hamburger menu', async ({ page }) => {
    await page.goto('/');

    await page.click('[data-testid="hamburger-menu"]');

    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();
    await expect(page.locator('[data-testid="menu-overlay"]')).toBeVisible();
  });

  test('should close menu on outside tap', async ({ page }) => {
    await page.goto('/');

    // Open menu
    await page.click('[data-testid="hamburger-menu"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeVisible();

    // Tap overlay to close
    await page.click('[data-testid="menu-overlay"]');
    await expect(page.locator('[data-testid="mobile-menu"]')).toBeHidden();
  });

  test('should handle bottom navigation', async ({ page }) => {
    await page.goto('/');

    const bottomNav = page.locator('[data-testid="bottom-nav"]');
    await expect(bottomNav).toBeVisible();

    // Navigate using bottom tabs
    await page.click('[data-testid="nav-search"]');
    await expect(page).toHaveURL('/search');

    await page.click('[data-testid="nav-profile"]');
    await expect(page).toHaveURL('/profile');
  });

  test('should handle back gesture', async ({ page }) => {
    await page.goto('/');
    await page.goto('/details');

    // Simulate back navigation
    await page.goBack();

    await expect(page).toHaveURL('/');
  });
});
```

## Native Mobile Testing with Appium

```typescript
// For native mobile apps
import { remote } from 'webdriverio';

describe('Native Mobile App', () => {
  let driver: WebdriverIO.Browser;

  beforeAll(async () => {
    driver = await remote({
      capabilities: {
        platformName: 'iOS',
        'appium:deviceName': 'iPhone 14',
        'appium:app': '/path/to/app.ipa',
        'appium:automationName': 'XCUITest',
      },
    });
  });

  afterAll(async () => {
    await driver.deleteSession();
  });

  it('should login successfully', async () => {
    const emailInput = await driver.$('~email-input');
    await emailInput.setValue('user@test.com');

    const passwordInput = await driver.$('~password-input');
    await passwordInput.setValue('password123');

    const loginButton = await driver.$('~login-button');
    await loginButton.click();

    const welcomeText = await driver.$('~welcome-message');
    await expect(welcomeText).toHaveText('Welcome, User!');
  });

  it('should handle native gestures', async () => {
    // Scroll
    await driver.execute('mobile: scroll', {
      direction: 'down',
    });

    // Swipe
    await driver.execute('mobile: swipe', {
      direction: 'left',
      element: await driver.$('~carousel'),
    });
  });
});
```

## Mobile Performance Testing

```typescript
test.describe('Mobile Performance', () => {
  test('should load quickly on 3G', async ({ page }) => {
    // Simulate 3G network
    const client = await page.context().newCDPSession(page);
    await client.send('Network.emulateNetworkConditions', {
      offline: false,
      downloadThroughput: (750 * 1024) / 8, // 750 kbps
      uploadThroughput: (250 * 1024) / 8,
      latency: 100,
    });

    const startTime = Date.now();
    await page.goto('/', { waitUntil: 'domcontentloaded' });
    const loadTime = Date.now() - startTime;

    // Should load within 5 seconds on 3G
    expect(loadTime).toBeLessThan(5000);
  });

  test('should work offline', async ({ page, context }) => {
    await page.goto('/');

    // Enable offline mode
    await context.setOffline(true);

    // Should show cached content or offline message
    await page.reload();

    await expect(page.locator('[data-testid="offline-banner"]')).toBeVisible();
    // Or cached content should still be visible
  });

  test('should be touch-friendly', async ({ page }) => {
    await page.goto('/');

    // Check touch target sizes (44x44 minimum)
    const buttons = await page.locator('button').all();

    for (const button of buttons) {
      const box = await button.boundingBox();
      if (box) {
        expect(box.width).toBeGreaterThanOrEqual(44);
        expect(box.height).toBeGreaterThanOrEqual(44);
      }
    }
  });
});
```

## Mobile Accessibility

```typescript
test.describe('Mobile Accessibility', () => {
  test('should have proper touch targets', async ({ page }) => {
    await page.goto('/');

    const interactiveElements = await page.locator('a, button, input, [role="button"]').all();

    for (const element of interactiveElements) {
      const box = await element.boundingBox();
      if (box && box.width > 0) {
        // Minimum 44x44 pixels
        expect(box.width).toBeGreaterThanOrEqual(44);
        expect(box.height).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('should have readable font sizes', async ({ page }) => {
    await page.goto('/');

    const textElements = await page.locator('p, span, a, button').all();

    for (const element of textElements) {
      const fontSize = await element.evaluate(el =>
        parseFloat(window.getComputedStyle(el).fontSize)
      );

      // Minimum 16px for body text
      expect(fontSize).toBeGreaterThanOrEqual(14);
    }
  });

  test('should support screen reader', async ({ page }) => {
    await page.goto('/');

    // Check ARIA labels
    const images = await page.locator('img').all();
    for (const img of images) {
      const alt = await img.getAttribute('alt');
      const ariaLabel = await img.getAttribute('aria-label');
      expect(alt || ariaLabel).toBeTruthy();
    }

    // Check button labels
    const buttons = await page.locator('button').all();
    for (const button of buttons) {
      const text = await button.textContent();
      const ariaLabel = await button.getAttribute('aria-label');
      expect(text?.trim() || ariaLabel).toBeTruthy();
    }
  });
});
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Test real devices | Emulators miss edge cases |
| Test multiple screen sizes | Cover common device dimensions |
| Test touch gestures | Swipe, tap, long press |
| Test orientation changes | Portrait and landscape |
| Test offline scenarios | Handle network loss |
| Test performance | 3G and slow networks |
| Test accessibility | Touch targets, fonts |

## Related Topics

- [Browser Testing](./browser-testing.md)
- [E2E Basics](./e2e-basics.md)
- [Visual Regression](./visual-regression.md)
