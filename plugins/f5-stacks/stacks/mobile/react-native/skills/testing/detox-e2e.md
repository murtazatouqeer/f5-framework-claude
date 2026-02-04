---
name: rn-detox-e2e
description: Detox end-to-end testing for React Native
applies_to: react-native
---

# Detox E2E Testing

## Overview

Detox is an end-to-end testing framework for React Native that runs tests on real devices/simulators. It's the industry standard for E2E testing in React Native.

## Installation

```bash
# Install Detox CLI globally
npm install -g detox-cli

# Install Detox as dev dependency
npm install --save-dev detox jest-circus

# For iOS, install applesimutils
brew tap wix/brew
brew install applesimutils
```

## Configuration

```javascript
// .detoxrc.js
module.exports = {
  testRunner: {
    args: {
      $0: 'jest',
      config: 'e2e/jest.config.js',
    },
    jest: {
      setupTimeout: 120000,
    },
  },
  apps: {
    'ios.debug': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Debug-iphonesimulator/MyApp.app',
      build:
        'xcodebuild -workspace ios/MyApp.xcworkspace -scheme MyApp -configuration Debug -sdk iphonesimulator -derivedDataPath ios/build',
    },
    'ios.release': {
      type: 'ios.app',
      binaryPath: 'ios/build/Build/Products/Release-iphonesimulator/MyApp.app',
      build:
        'xcodebuild -workspace ios/MyApp.xcworkspace -scheme MyApp -configuration Release -sdk iphonesimulator -derivedDataPath ios/build',
    },
    'android.debug': {
      type: 'android.apk',
      binaryPath: 'android/app/build/outputs/apk/debug/app-debug.apk',
      build:
        'cd android && ./gradlew assembleDebug assembleAndroidTest -DtestBuildType=debug',
      reversePorts: [8081],
    },
    'android.release': {
      type: 'android.apk',
      binaryPath: 'android/app/build/outputs/apk/release/app-release.apk',
      build:
        'cd android && ./gradlew assembleRelease assembleAndroidTest -DtestBuildType=release',
    },
  },
  devices: {
    simulator: {
      type: 'ios.simulator',
      device: {
        type: 'iPhone 15',
      },
    },
    emulator: {
      type: 'android.emulator',
      device: {
        avdName: 'Pixel_4_API_30',
      },
    },
  },
  configurations: {
    'ios.sim.debug': {
      device: 'simulator',
      app: 'ios.debug',
    },
    'ios.sim.release': {
      device: 'simulator',
      app: 'ios.release',
    },
    'android.emu.debug': {
      device: 'emulator',
      app: 'android.debug',
    },
    'android.emu.release': {
      device: 'emulator',
      app: 'android.release',
    },
  },
};
```

## Jest Config for Detox

```javascript
// e2e/jest.config.js
module.exports = {
  rootDir: '..',
  testMatch: ['<rootDir>/e2e/**/*.test.ts'],
  testTimeout: 120000,
  maxWorkers: 1,
  globalSetup: 'detox/runners/jest/globalSetup',
  globalTeardown: 'detox/runners/jest/globalTeardown',
  reporters: ['detox/runners/jest/reporter'],
  testEnvironment: 'detox/runners/jest/testEnvironment',
  verbose: true,
};
```

## Test Setup

```typescript
// e2e/setup.ts
import { device } from 'detox';

beforeAll(async () => {
  await device.launchApp({
    newInstance: true,
    permissions: {
      notifications: 'YES',
      camera: 'YES',
      photos: 'YES',
      location: 'always',
    },
  });
});

beforeEach(async () => {
  await device.reloadReactNative();
});
```

## Basic E2E Test

```typescript
// e2e/login.test.ts
import { by, device, element, expect } from 'detox';

describe('Login Flow', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
  });

  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should show login screen', async () => {
    await expect(element(by.id('login-screen'))).toBeVisible();
    await expect(element(by.id('email-input'))).toBeVisible();
    await expect(element(by.id('password-input'))).toBeVisible();
  });

  it('should show error for invalid credentials', async () => {
    await element(by.id('email-input')).typeText('invalid@email.com');
    await element(by.id('password-input')).typeText('wrongpassword');
    await element(by.id('login-button')).tap();

    await expect(element(by.text('Invalid credentials'))).toBeVisible();
  });

  it('should login successfully with valid credentials', async () => {
    await element(by.id('email-input')).typeText('test@example.com');
    await element(by.id('password-input')).typeText('password123');
    await element(by.id('login-button')).tap();

    // Wait for navigation to home screen
    await waitFor(element(by.id('home-screen')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should navigate to forgot password', async () => {
    await element(by.id('forgot-password-link')).tap();

    await expect(element(by.id('forgot-password-screen'))).toBeVisible();
  });
});
```

## Testing Navigation

```typescript
// e2e/navigation.test.ts
import { by, device, element, expect } from 'detox';

describe('Navigation', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    // Login first
    await loginUser();
  });

  it('should navigate through bottom tabs', async () => {
    // Start on Home tab
    await expect(element(by.id('home-screen'))).toBeVisible();

    // Navigate to Search tab
    await element(by.id('tab-search')).tap();
    await expect(element(by.id('search-screen'))).toBeVisible();

    // Navigate to Cart tab
    await element(by.id('tab-cart')).tap();
    await expect(element(by.id('cart-screen'))).toBeVisible();

    // Navigate to Profile tab
    await element(by.id('tab-profile')).tap();
    await expect(element(by.id('profile-screen'))).toBeVisible();
  });

  it('should navigate to product detail and back', async () => {
    await element(by.id('tab-home')).tap();

    // Tap first product
    await element(by.id('product-item-0')).tap();

    // Should show product detail
    await expect(element(by.id('product-detail-screen'))).toBeVisible();

    // Go back
    await element(by.id('back-button')).tap();

    // Should be back on home
    await expect(element(by.id('home-screen'))).toBeVisible();
  });
});

async function loginUser() {
  await element(by.id('email-input')).typeText('test@example.com');
  await element(by.id('password-input')).typeText('password123');
  await element(by.id('login-button')).tap();
  await waitFor(element(by.id('home-screen')))
    .toBeVisible()
    .withTimeout(5000);
}
```

## Testing Lists and Scrolling

```typescript
// e2e/productList.test.ts
import { by, device, element, expect, waitFor } from 'detox';

describe('Product List', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    await loginUser();
  });

  it('should display products', async () => {
    await expect(element(by.id('product-list'))).toBeVisible();
    await expect(element(by.id('product-item-0'))).toBeVisible();
  });

  it('should scroll to load more products', async () => {
    // Scroll down
    await element(by.id('product-list')).scroll(500, 'down');

    // Wait for more items to load
    await waitFor(element(by.id('product-item-10')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should pull to refresh', async () => {
    await element(by.id('product-list')).scroll(200, 'down');
    await element(by.id('product-list')).scroll(300, 'up');

    // Product list should still be visible after refresh
    await expect(element(by.id('product-item-0'))).toBeVisible();
  });

  it('should scroll to specific item', async () => {
    await waitFor(element(by.id('product-item-15')))
      .toBeVisible()
      .whileElement(by.id('product-list'))
      .scroll(100, 'down');
  });
});
```

## Testing Forms

```typescript
// e2e/checkout.test.ts
import { by, device, element, expect } from 'detox';

describe('Checkout Flow', () => {
  beforeAll(async () => {
    await device.launchApp({ newInstance: true });
    await loginUser();
    await addItemToCart();
  });

  it('should complete checkout form', async () => {
    await element(by.id('tab-cart')).tap();
    await element(by.id('checkout-button')).tap();

    // Fill shipping address
    await element(by.id('first-name-input')).typeText('John');
    await element(by.id('last-name-input')).typeText('Doe');
    await element(by.id('address-input')).typeText('123 Main St');
    await element(by.id('city-input')).typeText('New York');

    // Select state from picker
    await element(by.id('state-picker')).tap();
    await element(by.text('New York')).tap();

    await element(by.id('zip-input')).typeText('10001');
    await element(by.id('phone-input')).typeText('5551234567');

    // Continue to payment
    await element(by.id('continue-button')).tap();

    // Should show payment screen
    await expect(element(by.id('payment-screen'))).toBeVisible();
  });

  it('should show validation errors', async () => {
    await element(by.id('tab-cart')).tap();
    await element(by.id('checkout-button')).tap();

    // Try to continue without filling form
    await element(by.id('continue-button')).tap();

    // Should show validation errors
    await expect(element(by.text('First name is required'))).toBeVisible();
    await expect(element(by.text('Last name is required'))).toBeVisible();
  });
});

async function addItemToCart() {
  await element(by.id('product-item-0')).tap();
  await element(by.id('add-to-cart-button')).tap();
  await element(by.id('back-button')).tap();
}
```

## Testing Modals and Alerts

```typescript
// e2e/modals.test.ts
import { by, device, element, expect } from 'detox';

describe('Modals and Alerts', () => {
  it('should show and dismiss modal', async () => {
    await element(by.id('open-modal-button')).tap();

    await expect(element(by.id('modal-content'))).toBeVisible();

    await element(by.id('close-modal-button')).tap();

    await expect(element(by.id('modal-content'))).not.toBeVisible();
  });

  it('should handle system alert', async () => {
    await element(by.id('delete-button')).tap();

    // Handle system alert
    await expect(element(by.text('Are you sure?'))).toBeVisible();
    await element(by.text('Delete')).tap();

    // Verify deletion
    await expect(element(by.id('deleted-item'))).not.toBeVisible();
  });
});
```

## Test Utilities

```typescript
// e2e/utils/helpers.ts
import { by, device, element, waitFor } from 'detox';

export async function loginUser(
  email = 'test@example.com',
  password = 'password123'
) {
  await element(by.id('email-input')).clearText();
  await element(by.id('email-input')).typeText(email);
  await element(by.id('password-input')).clearText();
  await element(by.id('password-input')).typeText(password);
  await element(by.id('login-button')).tap();

  await waitFor(element(by.id('home-screen')))
    .toBeVisible()
    .withTimeout(10000);
}

export async function logout() {
  await element(by.id('tab-profile')).tap();
  await element(by.id('logout-button')).tap();

  await waitFor(element(by.id('login-screen')))
    .toBeVisible()
    .withTimeout(5000);
}

export async function scrollToElement(
  elementId: string,
  scrollViewId: string,
  direction: 'up' | 'down' = 'down'
) {
  await waitFor(element(by.id(elementId)))
    .toBeVisible()
    .whileElement(by.id(scrollViewId))
    .scroll(100, direction);
}

export async function takeScreenshot(name: string) {
  const screenshot = await device.takeScreenshot(name);
  console.log(`Screenshot saved: ${screenshot}`);
}
```

## Running Tests

```bash
# Build app for testing
detox build --configuration ios.sim.debug

# Run all E2E tests
detox test --configuration ios.sim.debug

# Run specific test file
detox test --configuration ios.sim.debug e2e/login.test.ts

# Run with recording (iOS only)
detox test --configuration ios.sim.debug --record-videos all

# Run in headless mode (CI)
detox test --configuration ios.sim.release --headless
```

## Best Practices

1. **Test IDs**: Add testID props to elements you need to interact with
2. **Stability**: Use waitFor instead of hardcoded delays
3. **Isolation**: Each test should be independent
4. **Setup**: Use beforeAll for common setup like login
5. **Screenshots**: Take screenshots on failure for debugging
6. **CI/CD**: Run E2E tests in CI pipelines
7. **Real Devices**: Test on real devices periodically
8. **Coverage**: Focus on critical user flows
