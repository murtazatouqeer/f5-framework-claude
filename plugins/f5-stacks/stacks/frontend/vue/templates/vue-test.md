---
name: vue-test
description: Vue component test template
applies_to: vue
variables:
  - name: componentName
    description: Component being tested
  - name: testType
    description: Type of test (unit, integration)
---

# Vue Test Template

## Component Test

```typescript
// ============================================================
// __tests__/{{componentName}}.spec.ts
// ============================================================

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, VueWrapper } from '@vue/test-utils';
import {{componentName}} from '../{{componentName}}.vue';

// ------------------------------------------------------------
// Test Setup
// ------------------------------------------------------------
describe('{{componentName}}', () => {
  let wrapper: VueWrapper;

  // Factory function for mounting
  function createWrapper(props = {}, options = {}) {
    return mount({{componentName}}, {
      props: {
        // Default props
        ...props,
      },
      global: {
        // Global options (plugins, stubs, mocks)
        ...options,
      },
    });
  }

  beforeEach(() => {
    // Reset before each test
    vi.clearAllMocks();
  });

  // --------------------------------------------------------
  // Rendering Tests
  // --------------------------------------------------------
  describe('rendering', () => {
    it('renders correctly', () => {
      wrapper = createWrapper();

      expect(wrapper.exists()).toBe(true);
    });

    it('renders with props', () => {
      wrapper = createWrapper({
        // Add props
      });

      // Add assertions
    });

    it('renders slot content', () => {
      wrapper = mount({{componentName}}, {
        slots: {
          default: '<p>Slot content</p>',
        },
      });

      expect(wrapper.find('p').text()).toBe('Slot content');
    });

    it('matches snapshot', () => {
      wrapper = createWrapper();

      expect(wrapper.html()).toMatchSnapshot();
    });
  });

  // --------------------------------------------------------
  // Interaction Tests
  // --------------------------------------------------------
  describe('interactions', () => {
    it('handles click event', async () => {
      wrapper = createWrapper();

      await wrapper.find('[data-testid="button"]').trigger('click');

      // Add assertions
    });

    it('handles input', async () => {
      wrapper = createWrapper();

      await wrapper.find('input').setValue('test value');

      // Add assertions
    });

    it('emits event on action', async () => {
      wrapper = createWrapper();

      await wrapper.find('[data-testid="submit"]').trigger('click');

      expect(wrapper.emitted()).toHaveProperty('submit');
      expect(wrapper.emitted('submit')).toHaveLength(1);
    });
  });

  // --------------------------------------------------------
  // State Tests
  // --------------------------------------------------------
  describe('state management', () => {
    it('updates internal state', async () => {
      wrapper = createWrapper();

      // Trigger state change
      await wrapper.find('[data-testid="increment"]').trigger('click');

      // Verify state reflected in DOM
      expect(wrapper.find('[data-testid="count"]').text()).toBe('1');
    });
  });

  // --------------------------------------------------------
  // Conditional Rendering Tests
  // --------------------------------------------------------
  describe('conditional rendering', () => {
    it('shows element when condition is true', () => {
      wrapper = createWrapper({
        showElement: true,
      });

      expect(wrapper.find('[data-testid="conditional"]').exists()).toBe(true);
    });

    it('hides element when condition is false', () => {
      wrapper = createWrapper({
        showElement: false,
      });

      expect(wrapper.find('[data-testid="conditional"]').exists()).toBe(false);
    });
  });
});
```

## Composable Test

```typescript
// ============================================================
// __tests__/use{{composableName}}.spec.ts
// ============================================================

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { use{{composableName}} } from '../use{{composableName}}';

describe('use{{composableName}}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // --------------------------------------------------------
  // Initialization Tests
  // --------------------------------------------------------
  describe('initialization', () => {
    it('returns expected values', () => {
      const result = use{{composableName}}();

      // Check returned properties exist
      expect(result).toHaveProperty('state');
      expect(result).toHaveProperty('action');
    });

    it('initializes with default values', () => {
      const { state } = use{{composableName}}();

      expect(state.value).toBe(/* default value */);
    });

    it('initializes with custom options', () => {
      const { state } = use{{composableName}}({
        initialValue: 'custom',
      });

      expect(state.value).toBe('custom');
    });
  });

  // --------------------------------------------------------
  // Action Tests
  // --------------------------------------------------------
  describe('actions', () => {
    it('updates state', () => {
      const { state, updateState } = use{{composableName}}();

      updateState('new value');

      expect(state.value).toBe('new value');
    });

    it('handles async action', async () => {
      const { data, fetchData, isLoading } = use{{composableName}}();

      // Mock fetch
      vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({ id: 1, name: 'Test' }),
      }));

      expect(isLoading.value).toBe(false);

      const promise = fetchData();

      expect(isLoading.value).toBe(true);

      await promise;

      expect(isLoading.value).toBe(false);
      expect(data.value).toEqual({ id: 1, name: 'Test' });

      vi.unstubAllGlobals();
    });
  });

  // --------------------------------------------------------
  // Computed Tests
  // --------------------------------------------------------
  describe('computed values', () => {
    it('computes derived value', () => {
      const { count, doubleCount, increment } = use{{composableName}}();

      expect(doubleCount.value).toBe(0);

      increment();

      expect(count.value).toBe(1);
      expect(doubleCount.value).toBe(2);
    });
  });
});
```

## Store Test

```typescript
// ============================================================
// __tests__/use{{storeName}}Store.spec.ts
// ============================================================

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { use{{storeName}}Store } from '../use{{storeName}}Store';

describe('use{{storeName}}Store', () => {
  beforeEach(() => {
    // Create fresh Pinia instance for each test
    setActivePinia(createPinia());

    // Mock fetch
    vi.stubGlobal('fetch', vi.fn());
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  // --------------------------------------------------------
  // State Tests
  // --------------------------------------------------------
  describe('initial state', () => {
    it('has correct initial state', () => {
      const store = use{{storeName}}Store();

      expect(store.items).toEqual([]);
      expect(store.isLoading).toBe(false);
      expect(store.error).toBeNull();
    });
  });

  // --------------------------------------------------------
  // Getter Tests
  // --------------------------------------------------------
  describe('getters', () => {
    it('computes itemCount correctly', () => {
      const store = use{{storeName}}Store();

      expect(store.itemCount).toBe(0);

      store.items = [{ id: '1' }, { id: '2' }];

      expect(store.itemCount).toBe(2);
    });

    it('finds item by id', () => {
      const store = use{{storeName}}Store();
      store.items = [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' },
      ];

      expect(store.itemById('1')).toEqual({ id: '1', name: 'Item 1' });
      expect(store.itemById('3')).toBeUndefined();
    });
  });

  // --------------------------------------------------------
  // Action Tests
  // --------------------------------------------------------
  describe('actions', () => {
    it('fetches items successfully', async () => {
      const mockItems = [{ id: '1', name: 'Test' }];

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(mockItems),
      } as Response);

      const store = use{{storeName}}Store();

      await store.fetchItems();

      expect(store.items).toEqual(mockItems);
      expect(store.isLoading).toBe(false);
      expect(store.error).toBeNull();
    });

    it('handles fetch error', async () => {
      vi.mocked(fetch).mockRejectedValue(new Error('Network error'));

      const store = use{{storeName}}Store();

      await expect(store.fetchItems()).rejects.toThrow();

      expect(store.items).toEqual([]);
      expect(store.error).toBe('Network error');
    });

    it('creates item and adds to list', async () => {
      const newItem = { id: '1', name: 'New Item' };

      vi.mocked(fetch).mockResolvedValue({
        ok: true,
        json: () => Promise.resolve(newItem),
      } as Response);

      const store = use{{storeName}}Store();

      const result = await store.createItem({ name: 'New Item' });

      expect(result).toEqual(newItem);
      expect(store.items).toContainEqual(newItem);
    });

    it('resets state', () => {
      const store = use{{storeName}}Store();

      store.items = [{ id: '1' }];
      store.error = 'Some error';

      store.$reset();

      expect(store.items).toEqual([]);
      expect(store.error).toBeNull();
    });
  });
});
```

## Test Utilities

```typescript
// ============================================================
// __tests__/helpers/index.ts
// ============================================================

import { mount, MountingOptions } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import type { Component } from 'vue';

// Create test router
export function createTestRouter(routes: RouteRecordRaw[] = []) {
  return createRouter({
    history: createWebHistory(),
    routes,
  });
}

// Mount with common plugins
export function mountWithPlugins<T extends Component>(
  component: T,
  options: MountingOptions<T> = {}
) {
  const pinia = createPinia();
  setActivePinia(pinia);

  return mount(component, {
    global: {
      plugins: [pinia],
      ...options.global,
    },
    ...options,
  });
}

// Factory helpers
export function createMockUser(overrides = {}) {
  return {
    id: '1',
    name: 'Test User',
    email: 'test@example.com',
    ...overrides,
  };
}

// Wait helpers
export function flushPromises() {
  return new Promise(resolve => setTimeout(resolve, 0));
}
```

## Usage

```typescript
// Import test utilities
import { mountWithPlugins, createMockUser } from './helpers';

describe('UserProfile', () => {
  it('displays user information', () => {
    const user = createMockUser({ name: 'John Doe' });

    const wrapper = mountWithPlugins(UserProfile, {
      props: { user },
    });

    expect(wrapper.text()).toContain('John Doe');
  });
});
```
