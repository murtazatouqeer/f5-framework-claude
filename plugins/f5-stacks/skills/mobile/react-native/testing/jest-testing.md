---
name: rn-jest-testing
description: Jest configuration and testing patterns for React Native
applies_to: react-native
---

# Jest Testing in React Native

## Setup with Expo

Jest comes pre-configured with Expo. Check your package.json:

```json
{
  "scripts": {
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  },
  "jest": {
    "preset": "jest-expo"
  }
}
```

## Jest Configuration

```javascript
// jest.config.js
module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?)|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-native-svg)',
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70,
    },
  },
  testMatch: ['**/__tests__/**/*.[jt]s?(x)', '**/?(*.)+(spec|test).[jt]s?(x)'],
};
```

## Setup File

```typescript
// jest.setup.js
import '@testing-library/jest-native/extend-expect';

// Mock AsyncStorage
jest.mock('@react-native-async-storage/async-storage', () =>
  require('@react-native-async-storage/async-storage/jest/async-storage-mock')
);

// Mock expo-secure-store
jest.mock('expo-secure-store', () => ({
  getItemAsync: jest.fn(),
  setItemAsync: jest.fn(),
  deleteItemAsync: jest.fn(),
}));

// Mock expo-router
jest.mock('expo-router', () => ({
  useRouter: () => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
  }),
  useLocalSearchParams: () => ({}),
  useSegments: () => [],
  Link: 'Link',
}));

// Mock react-native-reanimated
jest.mock('react-native-reanimated', () => {
  const Reanimated = require('react-native-reanimated/mock');
  Reanimated.default.call = () => {};
  return Reanimated;
});

// Silence warnings
jest.spyOn(console, 'warn').mockImplementation(() => {});

// Global test timeout
jest.setTimeout(10000);
```

## Basic Unit Tests

```typescript
// src/utils/__tests__/formatters.test.ts
import { formatPrice, formatDate, truncate } from '../formatters';

describe('formatPrice', () => {
  it('formats number as currency', () => {
    expect(formatPrice(1234.56)).toBe('$1,234.56');
  });

  it('handles zero', () => {
    expect(formatPrice(0)).toBe('$0.00');
  });

  it('handles negative numbers', () => {
    expect(formatPrice(-100)).toBe('-$100.00');
  });
});

describe('formatDate', () => {
  it('formats date correctly', () => {
    const date = new Date('2024-01-15');
    expect(formatDate(date)).toBe('Jan 15, 2024');
  });

  it('handles string input', () => {
    expect(formatDate('2024-01-15')).toBe('Jan 15, 2024');
  });
});

describe('truncate', () => {
  it('truncates long text', () => {
    const text = 'This is a very long text that should be truncated';
    expect(truncate(text, 20)).toBe('This is a very long...');
  });

  it('returns original if shorter than max', () => {
    expect(truncate('Short', 20)).toBe('Short');
  });
});
```

## Testing Async Functions

```typescript
// src/services/__tests__/userService.test.ts
import { userService } from '../userService';
import { api } from '@/lib/api';

jest.mock('@/lib/api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('userService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getProfile', () => {
    it('fetches user profile successfully', async () => {
      const mockUser = { id: '1', name: 'John', email: 'john@example.com' };
      mockedApi.get.mockResolvedValueOnce({ data: mockUser });

      const result = await userService.getProfile();

      expect(mockedApi.get).toHaveBeenCalledWith('/users/me');
      expect(result).toEqual(mockUser);
    });

    it('throws error on failure', async () => {
      mockedApi.get.mockRejectedValueOnce(new Error('Network error'));

      await expect(userService.getProfile()).rejects.toThrow('Network error');
    });
  });

  describe('updateProfile', () => {
    it('updates user profile successfully', async () => {
      const updateData = { name: 'John Updated' };
      const mockResponse = { id: '1', ...updateData };
      mockedApi.patch.mockResolvedValueOnce({ data: mockResponse });

      const result = await userService.updateProfile(updateData);

      expect(mockedApi.patch).toHaveBeenCalledWith('/users/me', updateData);
      expect(result).toEqual(mockResponse);
    });
  });
});
```

## Testing Custom Hooks

```typescript
// src/hooks/__tests__/useDebounce.test.ts
import { renderHook, act } from '@testing-library/react-hooks';
import { useDebounce } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500));
    expect(result.current).toBe('initial');
  });

  it('debounces value updates', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'initial' } }
    );

    // Update value
    rerender({ value: 'updated' });

    // Value should still be initial
    expect(result.current).toBe('initial');

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Now should be updated
    expect(result.current).toBe('updated');
  });

  it('cancels previous timeout on new value', () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 500),
      { initialProps: { value: 'first' } }
    );

    rerender({ value: 'second' });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    rerender({ value: 'third' });
    act(() => {
      jest.advanceTimersByTime(300);
    });

    // Still first because timers keep resetting
    expect(result.current).toBe('first');

    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Now should be third
    expect(result.current).toBe('third');
  });
});
```

## Testing Zustand Stores

```typescript
// src/stores/__tests__/useCartStore.test.ts
import { useCartStore } from '../useCartStore';
import { act } from '@testing-library/react-hooks';

describe('useCartStore', () => {
  beforeEach(() => {
    // Reset store state
    useCartStore.setState({ items: [] });
  });

  describe('addItem', () => {
    it('adds new item to cart', () => {
      const item = { id: '1', name: 'Product', price: 10 };

      act(() => {
        useCartStore.getState().addItem(item);
      });

      const { items } = useCartStore.getState();
      expect(items).toHaveLength(1);
      expect(items[0]).toEqual({ ...item, quantity: 1 });
    });

    it('increments quantity for existing item', () => {
      const item = { id: '1', name: 'Product', price: 10 };

      act(() => {
        useCartStore.getState().addItem(item);
        useCartStore.getState().addItem(item);
      });

      const { items } = useCartStore.getState();
      expect(items).toHaveLength(1);
      expect(items[0].quantity).toBe(2);
    });
  });

  describe('removeItem', () => {
    it('removes item from cart', () => {
      act(() => {
        useCartStore.setState({
          items: [{ id: '1', name: 'Product', price: 10, quantity: 1 }],
        });
        useCartStore.getState().removeItem('1');
      });

      expect(useCartStore.getState().items).toHaveLength(0);
    });
  });

  describe('computed values', () => {
    it('calculates total correctly', () => {
      act(() => {
        useCartStore.setState({
          items: [
            { id: '1', name: 'Product 1', price: 10, quantity: 2 },
            { id: '2', name: 'Product 2', price: 15, quantity: 1 },
          ],
        });
      });

      // If you have a selector
      const total = useCartStore.getState().items.reduce(
        (sum, item) => sum + item.price * item.quantity,
        0
      );
      expect(total).toBe(35);
    });
  });
});
```

## Mocking Modules

```typescript
// src/__mocks__/expo-secure-store.ts
const store: Record<string, string> = {};

export const getItemAsync = jest.fn((key: string) => {
  return Promise.resolve(store[key] || null);
});

export const setItemAsync = jest.fn((key: string, value: string) => {
  store[key] = value;
  return Promise.resolve();
});

export const deleteItemAsync = jest.fn((key: string) => {
  delete store[key];
  return Promise.resolve();
});

// Reset function for tests
export const __resetStore = () => {
  Object.keys(store).forEach((key) => delete store[key]);
};
```

## Test Utilities

```typescript
// src/test-utils/index.ts
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NavigationContainer } from '@react-navigation/native';

// Create a new QueryClient for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

interface WrapperProps {
  children: React.ReactNode;
}

function AllTheProviders({ children }: WrapperProps) {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        {children}
      </NavigationContainer>
    </QueryClientProvider>
  );
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

// Re-export everything
export * from '@testing-library/react-native';
export { customRender as render };
```

## Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm test -- --watch

# Coverage report
npm test -- --coverage

# Run specific file
npm test -- Button.test.tsx

# Run tests matching pattern
npm test -- --testNamePattern="should render"

# Update snapshots
npm test -- -u
```

## Best Practices

1. **Isolation**: Reset state/mocks between tests
2. **Mock External**: Mock API calls, native modules, navigation
3. **Test Behavior**: Test what component does, not implementation
4. **Descriptive Names**: Use clear test descriptions
5. **AAA Pattern**: Arrange, Act, Assert structure
6. **Coverage Goals**: Aim for 70%+ coverage on critical paths
7. **Fast Tests**: Keep tests fast by avoiding unnecessary waits
8. **CI Integration**: Run tests in CI/CD pipeline
