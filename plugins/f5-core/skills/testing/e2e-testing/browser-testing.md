---
name: browser-testing
description: Browser automation and cross-browser testing
category: testing/e2e-testing
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Browser Testing

## Overview

Browser testing verifies application behavior in real browser environments,
ensuring consistent user experience across different browsers and devices.

## Cross-Browser Testing Strategy

```
┌──────────────────────────────────────────────────────────────┐
│                    Browser Coverage Strategy                  │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  Primary Browsers (Must Test):                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                      │
│  │ Chrome  │  │ Firefox │  │ Safari  │                      │
│  │  (~65%) │  │  (~8%)  │  │ (~19%)  │                      │
│  └─────────┘  └─────────┘  └─────────┘                      │
│                                                               │
│  Mobile Browsers (Critical for Mobile Apps):                 │
│  ┌──────────────┐  ┌──────────────┐                         │
│  │ Mobile Safari │  │ Chrome Mobile│                         │
│  │   (iOS)      │  │  (Android)   │                         │
│  └──────────────┘  └──────────────┘                         │
│                                                               │
│  Secondary (Based on Analytics):                             │
│  ┌─────────┐  ┌─────────┐                                   │
│  │  Edge   │  │ Samsung │                                   │
│  │         │  │Internet │                                   │
│  └─────────┘  └─────────┘                                   │
└──────────────────────────────────────────────────────────────┘
```

## Playwright Multi-Browser Setup

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  projects: [
    // Desktop browsers
    {
      name: 'Desktop Chrome',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1920, height: 1080 },
      },
    },
    {
      name: 'Desktop Firefox',
      use: {
        ...devices['Desktop Firefox'],
        viewport: { width: 1920, height: 1080 },
      },
    },
    {
      name: 'Desktop Safari',
      use: {
        ...devices['Desktop Safari'],
        viewport: { width: 1920, height: 1080 },
      },
    },

    // Mobile devices
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
    {
      name: 'Pixel 7',
      use: {
        ...devices['Pixel 7'],
      },
    },
    {
      name: 'Galaxy S23',
      use: {
        ...devices['Galaxy S8'],
        viewport: { width: 360, height: 740 },
      },
    },

    // Tablets
    {
      name: 'iPad Pro',
      use: {
        ...devices['iPad Pro 11'],
      },
    },
    {
      name: 'iPad Mini',
      use: {
        ...devices['iPad Mini'],
      },
    },
  ],
});
```

## Browser-Specific Testing

### Testing Browser-Specific Features

```typescript
import { test, expect } from '@playwright/test';

test.describe('Browser-Specific Features', () => {
  test('should use native date picker on supported browsers', async ({ page, browserName }) => {
    await page.goto('/forms/date-input');

    const dateInput = page.locator('input[type="date"]');

    if (browserName === 'webkit') {
      // Safari might need special handling
      await dateInput.fill('2024-01-15');
    } else {
      // Chrome/Firefox have native date pickers
      await dateInput.click();
      await page.locator('.date-picker-day:has-text("15")').click();
    }

    await expect(dateInput).toHaveValue('2024-01-15');
  });

  test('should handle file download', async ({ page, browserName }) => {
    await page.goto('/downloads');

    const downloadPromise = page.waitForEvent('download');
    await page.click('[data-testid="download-button"]');
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toBe('report.pdf');

    // Save file for verification
    const path = await download.path();
    expect(path).toBeTruthy();
  });
});
```

### Handling Browser Differences

```typescript
test.describe('Cross-Browser Compatibility', () => {
  test('should render flexbox layout correctly', async ({ page }) => {
    await page.goto('/layout-test');

    // Get computed styles
    const container = page.locator('.flex-container');
    const display = await container.evaluate(el =>
      window.getComputedStyle(el).display
    );

    expect(display).toBe('flex');

    // Check children alignment
    const children = await page.locator('.flex-container > *').all();
    const positions = await Promise.all(
      children.map(child =>
        child.boundingBox()
      )
    );

    // All children should be on the same row
    const firstY = positions[0]?.y;
    positions.forEach(pos => {
      expect(pos?.y).toBeCloseTo(firstY!, 5);
    });
  });

  test('should handle CSS grid', async ({ page }) => {
    await page.goto('/grid-layout');

    const grid = page.locator('.grid-container');
    const gridStyle = await grid.evaluate(el => {
      const styles = window.getComputedStyle(el);
      return {
        display: styles.display,
        gridTemplateColumns: styles.gridTemplateColumns,
      };
    });

    expect(gridStyle.display).toBe('grid');
  });
});
```

## Responsive Testing

```typescript
test.describe('Responsive Design', () => {
  const viewports = [
    { name: 'mobile', width: 375, height: 667 },
    { name: 'tablet', width: 768, height: 1024 },
    { name: 'desktop', width: 1280, height: 800 },
    { name: 'large-desktop', width: 1920, height: 1080 },
  ];

  for (const viewport of viewports) {
    test(`should display correctly on ${viewport.name}`, async ({ page }) => {
      await page.setViewportSize({ width: viewport.width, height: viewport.height });
      await page.goto('/');

      // Mobile: hamburger menu visible
      if (viewport.width < 768) {
        await expect(page.locator('[data-testid="hamburger-menu"]')).toBeVisible();
        await expect(page.locator('[data-testid="desktop-nav"]')).toBeHidden();
      }

      // Tablet/Desktop: full nav visible
      if (viewport.width >= 768) {
        await expect(page.locator('[data-testid="desktop-nav"]')).toBeVisible();
        await expect(page.locator('[data-testid="hamburger-menu"]')).toBeHidden();
      }

      // Large desktop: sidebar visible
      if (viewport.width >= 1280) {
        await expect(page.locator('[data-testid="sidebar"]')).toBeVisible();
      }
    });
  }

  test('should adapt layout on resize', async ({ page }) => {
    await page.goto('/');

    // Start at desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await expect(page.locator('[data-testid="desktop-nav"]')).toBeVisible();

    // Resize to mobile
    await page.setViewportSize({ width: 375, height: 667 });
    await expect(page.locator('[data-testid="hamburger-menu"]')).toBeVisible();

    // Resize back to desktop
    await page.setViewportSize({ width: 1280, height: 800 });
    await expect(page.locator('[data-testid="desktop-nav"]')).toBeVisible();
  });
});
```

## Touch and Gesture Testing

```typescript
test.describe('Touch Interactions', () => {
  test.use({ hasTouch: true });

  test('should handle tap', async ({ page }) => {
    await page.goto('/touch-test');

    await page.tap('[data-testid="tap-button"]');

    await expect(page.locator('[data-testid="tap-result"]'))
      .toContainText('Tapped!');
  });

  test('should handle swipe', async ({ page }) => {
    await page.goto('/carousel');

    const carousel = page.locator('[data-testid="carousel"]');
    const box = await carousel.boundingBox();

    if (box) {
      // Swipe left
      await page.touchscreen.tap(box.x + box.width * 0.8, box.y + box.height / 2);
      await page.mouse.move(box.x + box.width * 0.2, box.y + box.height / 2);
    }

    await expect(page.locator('[data-testid="slide-2"]')).toBeVisible();
  });

  test('should handle pinch zoom', async ({ page }) => {
    await page.goto('/image-viewer');

    // Note: Playwright has limited pinch-zoom support
    // Consider using CDP for complex gestures
    const client = await page.context().newCDPSession(page);

    await client.send('Input.dispatchTouchEvent', {
      type: 'touchStart',
      touchPoints: [
        { x: 200, y: 200 },
        { x: 300, y: 300 },
      ],
    });

    await client.send('Input.dispatchTouchEvent', {
      type: 'touchMove',
      touchPoints: [
        { x: 150, y: 150 },
        { x: 350, y: 350 },
      ],
    });

    await client.send('Input.dispatchTouchEvent', {
      type: 'touchEnd',
      touchPoints: [],
    });
  });
});
```

## Browser Capabilities Testing

```typescript
test.describe('Browser Capabilities', () => {
  test('should detect WebGL support', async ({ page }) => {
    await page.goto('/3d-viewer');

    const hasWebGL = await page.evaluate(() => {
      const canvas = document.createElement('canvas');
      return !!(
        canvas.getContext('webgl') ||
        canvas.getContext('experimental-webgl')
      );
    });

    if (hasWebGL) {
      await expect(page.locator('[data-testid="3d-canvas"]')).toBeVisible();
    } else {
      await expect(page.locator('[data-testid="webgl-fallback"]')).toBeVisible();
    }
  });

  test('should handle service worker', async ({ page, context }) => {
    await page.goto('/');

    // Check service worker registration
    const swRegistration = await page.evaluate(async () => {
      if ('serviceWorker' in navigator) {
        const registration = await navigator.serviceWorker.ready;
        return registration.active !== null;
      }
      return false;
    });

    expect(swRegistration).toBe(true);
  });

  test('should handle geolocation', async ({ page, context }) => {
    // Grant geolocation permission
    await context.grantPermissions(['geolocation']);

    // Mock geolocation
    await context.setGeolocation({ latitude: 40.7128, longitude: -74.0060 });

    await page.goto('/location-based');

    await page.click('[data-testid="get-location"]');

    await expect(page.locator('[data-testid="location-result"]'))
      .toContainText('New York');
  });
});
```

## Performance Testing in Browser

```typescript
test.describe('Browser Performance', () => {
  test('should load within acceptable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto('/', { waitUntil: 'networkidle' });

    const loadTime = Date.now() - startTime;
    expect(loadTime).toBeLessThan(3000); // 3 seconds
  });

  test('should have good Core Web Vitals', async ({ page }) => {
    await page.goto('/');

    // Get performance metrics
    const metrics = await page.evaluate(() => {
      return new Promise<any>(resolve => {
        new PerformanceObserver(list => {
          const entries = list.getEntries();
          resolve({
            lcp: entries.find(e => e.entryType === 'largest-contentful-paint'),
            fid: entries.find(e => e.entryType === 'first-input'),
            cls: entries.find(e => e.entryType === 'layout-shift'),
          });
        }).observe({ entryTypes: ['largest-contentful-paint', 'first-input', 'layout-shift'] });

        // Trigger interactions to measure
        setTimeout(() => resolve({}), 5000);
      });
    });

    // LCP should be under 2.5s
    if (metrics.lcp) {
      expect(metrics.lcp.startTime).toBeLessThan(2500);
    }
  });

  test('should not have memory leaks', async ({ page }) => {
    await page.goto('/data-heavy-page');

    const initialMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize;
    });

    // Perform memory-intensive operations
    for (let i = 0; i < 10; i++) {
      await page.click('[data-testid="load-more"]');
      await page.waitForTimeout(500);
    }

    const finalMemory = await page.evaluate(() => {
      return (performance as any).memory?.usedJSHeapSize;
    });

    // Memory shouldn't grow excessively (2x initial)
    if (initialMemory && finalMemory) {
      expect(finalMemory).toBeLessThan(initialMemory * 2);
    }
  });
});
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Test real browsers | Don't just emulate |
| Prioritize by usage | Focus on popular browsers |
| Test responsive layouts | Multiple viewports |
| Handle browser differences | Conditional test logic |
| Monitor performance | Track load times |
| Use device emulation | Test mobile features |

## Related Topics

- [E2E Basics](./e2e-basics.md)
- [Mobile Testing](./mobile-testing.md)
- [Visual Regression](./visual-regression.md)
