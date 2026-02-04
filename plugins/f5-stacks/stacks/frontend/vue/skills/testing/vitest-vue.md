---
name: vue-vitest
description: Vitest setup and configuration for Vue projects
applies_to: vue
---

# Vitest for Vue

## Overview

Vitest is a fast unit test framework powered by Vite. It provides
native ESM support, TypeScript integration, and Vue-specific features.

## Setup

```bash
npm install -D vitest @vue/test-utils happy-dom @vitest/coverage-v8
```

### vitest.config.ts

```typescript
import { defineConfig } from 'vitest/config';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  plugins: [vue()],
  test: {
    environment: 'happy-dom',
    globals: true,
    include: ['**/*.{test,spec}.{js,ts,jsx,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*.{ts,vue}'],
      exclude: ['src/**/*.d.ts', 'src/**/*.spec.ts'],
    },
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
});
```

### package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:run": "vitest run",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui"
  }
}
```

## Basic Tests

### Simple Unit Test

```typescript
// utils/format.ts
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}
```

```typescript
// utils/format.spec.ts
import { describe, it, expect } from 'vitest';
import { formatCurrency, capitalize } from './format';

describe('formatCurrency', () => {
  it('formats positive numbers', () => {
    expect(formatCurrency(100)).toBe('$100.00');
  });

  it('formats decimal numbers', () => {
    expect(formatCurrency(99.99)).toBe('$99.99');
  });

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00');
  });
});

describe('capitalize', () => {
  it('capitalizes first letter', () => {
    expect(capitalize('hello')).toBe('Hello');
  });

  it('handles empty string', () => {
    expect(capitalize('')).toBe('');
  });

  it('handles already capitalized', () => {
    expect(capitalize('Hello')).toBe('Hello');
  });
});
```

## Testing Composables

### Simple Composable Test

```typescript
// composables/useCounter.ts
import { ref, computed } from 'vue';

export function useCounter(initialValue = 0) {
  const count = ref(initialValue);
  const double = computed(() => count.value * 2);

  function increment() {
    count.value++;
  }

  function decrement() {
    count.value--;
  }

  function reset() {
    count.value = initialValue;
  }

  return {
    count,
    double,
    increment,
    decrement,
    reset,
  };
}
```

```typescript
// composables/useCounter.spec.ts
import { describe, it, expect } from 'vitest';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('initializes with default value', () => {
    const { count } = useCounter();
    expect(count.value).toBe(0);
  });

  it('initializes with custom value', () => {
    const { count } = useCounter(10);
    expect(count.value).toBe(10);
  });

  it('increments count', () => {
    const { count, increment } = useCounter();
    increment();
    expect(count.value).toBe(1);
  });

  it('decrements count', () => {
    const { count, decrement } = useCounter(5);
    decrement();
    expect(count.value).toBe(4);
  });

  it('resets to initial value', () => {
    const { count, increment, reset } = useCounter(5);
    increment();
    increment();
    expect(count.value).toBe(7);
    reset();
    expect(count.value).toBe(5);
  });

  it('computes double value', () => {
    const { count, double, increment } = useCounter(5);
    expect(double.value).toBe(10);
    increment();
    expect(double.value).toBe(12);
  });
});
```

### Async Composable Test

```typescript
// composables/useFetch.ts
import { ref, shallowRef } from 'vue';

export function useFetch<T>(url: string) {
  const data = shallowRef<T | null>(null);
  const error = ref<Error | null>(null);
  const isLoading = ref(false);

  async function execute() {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      data.value = await response.json();
    } catch (e) {
      error.value = e as Error;
    } finally {
      isLoading.value = false;
    }
  }

  return { data, error, isLoading, execute };
}
```

```typescript
// composables/useFetch.spec.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useFetch } from './useFetch';

describe('useFetch', () => {
  const mockData = { id: 1, name: 'Test' };

  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('fetches data successfully', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockData),
    } as Response);

    const { data, error, isLoading, execute } = useFetch('/api/test');

    expect(data.value).toBeNull();
    expect(isLoading.value).toBe(false);

    await execute();

    expect(data.value).toEqual(mockData);
    expect(error.value).toBeNull();
    expect(isLoading.value).toBe(false);
  });

  it('handles fetch error', async () => {
    vi.mocked(fetch).mockResolvedValue({
      ok: false,
      status: 404,
    } as Response);

    const { data, error, execute } = useFetch('/api/not-found');

    await execute();

    expect(data.value).toBeNull();
    expect(error.value).toBeInstanceOf(Error);
    expect(error.value?.message).toContain('404');
  });

  it('handles network error', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('Network error'));

    const { data, error, execute } = useFetch('/api/test');

    await execute();

    expect(data.value).toBeNull();
    expect(error.value?.message).toBe('Network error');
  });
});
```

## Mocking

### Mocking Modules

```typescript
// services/api.ts
export async function fetchUsers() {
  const response = await fetch('/api/users');
  return response.json();
}
```

```typescript
// services/api.spec.ts
import { describe, it, expect, vi } from 'vitest';

// Mock the entire module
vi.mock('./api', () => ({
  fetchUsers: vi.fn(),
}));

import { fetchUsers } from './api';

describe('API Service', () => {
  it('fetches users', async () => {
    const mockUsers = [{ id: 1, name: 'John' }];
    vi.mocked(fetchUsers).mockResolvedValue(mockUsers);

    const users = await fetchUsers();

    expect(users).toEqual(mockUsers);
    expect(fetchUsers).toHaveBeenCalled();
  });
});
```

### Mocking Pinia Stores

```typescript
// stores/useUserStore.spec.ts
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useUserStore } from './useUserStore';

// Mock fetch
vi.stubGlobal('fetch', vi.fn());

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetches user by id', async () => {
    const mockUser = { id: 1, name: 'John', email: 'john@example.com' };

    vi.mocked(fetch).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockUser),
    } as Response);

    const store = useUserStore();
    await store.fetchUser(1);

    expect(store.currentUser).toEqual(mockUser);
    expect(store.isLoading).toBe(false);
  });

  it('handles fetch error', async () => {
    vi.mocked(fetch).mockRejectedValue(new Error('Network error'));

    const store = useUserStore();
    await store.fetchUser(1);

    expect(store.currentUser).toBeNull();
    expect(store.error).toBe('Network error');
  });
});
```

## Test Utilities

### Custom Test Helpers

```typescript
// tests/helpers.ts
import { vi } from 'vitest';

export function mockLocalStorage() {
  const store: Record<string, string> = {};

  return {
    getItem: vi.fn((key: string) => store[key] ?? null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach((key) => delete store[key]);
    }),
  };
}

export function flushPromises() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}
```

### Setup File

```typescript
// tests/setup.ts
import { beforeAll, afterEach, vi } from 'vitest';

beforeAll(() => {
  // Setup global mocks
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  });
});

afterEach(() => {
  vi.clearAllMocks();
});
```

```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    setupFiles: ['./tests/setup.ts'],
    // ...
  },
});
```

## Snapshot Testing

```typescript
// components/UserCard.spec.ts
import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import UserCard from './UserCard.vue';

describe('UserCard', () => {
  it('matches snapshot', () => {
    const wrapper = mount(UserCard, {
      props: {
        user: {
          id: 1,
          name: 'John Doe',
          email: 'john@example.com',
          avatar: 'https://example.com/avatar.jpg',
        },
      },
    });

    expect(wrapper.html()).toMatchSnapshot();
  });
});
```

## Best Practices

1. **Use globals** - Enable `globals: true` for cleaner tests
2. **Mock external dependencies** - Don't make real API calls
3. **Test composables independently** - Isolate from components
4. **Use happy-dom** - Faster than jsdom for most cases
5. **Coverage thresholds** - Set minimum coverage requirements
6. **Setup files** - Initialize common mocks and configurations
