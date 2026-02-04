---
name: nuxt-vitest
description: Testing Nuxt 3 applications with Vitest
applies_to: nuxt
---

# Testing with Vitest in Nuxt 3

## Overview

Nuxt provides `@nuxt/test-utils` for testing components, composables, and API routes with Vitest.

## Setup

```bash
npm install -D @nuxt/test-utils vitest @vue/test-utils happy-dom
```

```typescript
// vitest.config.ts
import { defineVitestConfig } from '@nuxt/test-utils/config';

export default defineVitestConfig({
  test: {
    environment: 'nuxt',
    environmentOptions: {
      nuxt: {
        mock: {
          intersectionObserver: true,
          indexedDb: true,
        },
      },
    },
  },
});
```

```json
// package.json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest --coverage"
  }
}
```

## Testing Composables

### Unit Test

```typescript
// tests/composables/useCounter.test.ts
import { describe, it, expect } from 'vitest';
import { useCounter } from '~/composables/useCounter';

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
});
```

### With Mocked Fetch

```typescript
// tests/composables/useProducts.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useProducts } from '~/composables/useProducts';

const mockFetch = vi.fn();
vi.stubGlobal('$fetch', mockFetch);

describe('useProducts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches products successfully', async () => {
    const mockProducts = [
      { id: '1', name: 'Product 1' },
      { id: '2', name: 'Product 2' },
    ];

    mockFetch.mockResolvedValueOnce({
      items: mockProducts,
      total: 2,
    });

    const { products, fetch, isLoading } = useProducts({ immediate: false });

    expect(isLoading.value).toBe(false);
    await fetch();

    expect(mockFetch).toHaveBeenCalledWith('/api/products', {
      query: { page: 1, limit: 20 },
    });
    expect(products.value).toEqual(mockProducts);
  });

  it('handles fetch error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const { error, fetch } = useProducts({ immediate: false });
    await fetch();

    expect(error.value).toBeInstanceOf(Error);
    expect(error.value?.message).toBe('Network error');
  });
});
```

## Testing Components

### Basic Component Test

```typescript
// tests/components/Button.test.ts
import { describe, it, expect } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import Button from '~/components/Button.vue';

describe('Button', () => {
  it('renders with default props', async () => {
    const wrapper = await mountSuspended(Button, {
      slots: {
        default: 'Click me',
      },
    });

    expect(wrapper.text()).toBe('Click me');
    expect(wrapper.element.tagName).toBe('BUTTON');
  });

  it('emits click event', async () => {
    const wrapper = await mountSuspended(Button);

    await wrapper.trigger('click');

    expect(wrapper.emitted('click')).toBeTruthy();
  });

  it('applies variant class', async () => {
    const wrapper = await mountSuspended(Button, {
      props: { variant: 'primary' },
    });

    expect(wrapper.classes()).toContain('btn-primary');
  });

  it('is disabled when prop is set', async () => {
    const wrapper = await mountSuspended(Button, {
      props: { disabled: true },
    });

    expect(wrapper.attributes('disabled')).toBeDefined();
  });
});
```

### Component with Props and Emits

```typescript
// tests/components/ProductCard.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import ProductCard from '~/components/ProductCard.vue';

describe('ProductCard', () => {
  const mockProduct = {
    id: '1',
    name: 'Test Product',
    description: 'A test product',
    price: 99.99,
    image: '/images/product.jpg',
  };

  it('renders product information', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
    });

    expect(wrapper.text()).toContain('Test Product');
    expect(wrapper.text()).toContain('99.99');
  });

  it('emits add-to-cart event', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
    });

    await wrapper.find('[data-testid="add-to-cart"]').trigger('click');

    expect(wrapper.emitted('add-to-cart')).toBeTruthy();
    expect(wrapper.emitted('add-to-cart')![0]).toEqual([mockProduct]);
  });

  it('renders image with correct src', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
    });

    const img = wrapper.find('img');
    expect(img.attributes('src')).toBe('/images/product.jpg');
  });
});
```

### Component with Slots

```typescript
// tests/components/Card.test.ts
import { describe, it, expect } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import Card from '~/components/Card.vue';

describe('Card', () => {
  it('renders slot content', async () => {
    const wrapper = await mountSuspended(Card, {
      slots: {
        default: '<p>Card content</p>',
        header: '<h2>Card Header</h2>',
        footer: '<button>Action</button>',
      },
    });

    expect(wrapper.text()).toContain('Card content');
    expect(wrapper.text()).toContain('Card Header');
    expect(wrapper.find('button').exists()).toBe(true);
  });
});
```

## Testing Pages

```typescript
// tests/pages/products.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime';
import ProductsPage from '~/pages/products/index.vue';

mockNuxtImport('useFetch', () => {
  return () => ({
    data: ref([
      { id: '1', name: 'Product 1' },
      { id: '2', name: 'Product 2' },
    ]),
    pending: ref(false),
    error: ref(null),
  });
});

describe('Products Page', () => {
  it('renders product list', async () => {
    const wrapper = await mountSuspended(ProductsPage);

    expect(wrapper.text()).toContain('Product 1');
    expect(wrapper.text()).toContain('Product 2');
  });
});
```

## Testing API Routes

```typescript
// tests/server/api/products.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock Prisma
vi.mock('~/server/utils/db', () => ({
  prisma: {
    product: {
      findMany: vi.fn(),
      count: vi.fn(),
    },
  },
}));

import { prisma } from '~/server/utils/db';

describe('GET /api/products', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns paginated products', async () => {
    const mockProducts = [
      { id: '1', name: 'Product 1' },
      { id: '2', name: 'Product 2' },
    ];

    vi.mocked(prisma.product.findMany).mockResolvedValue(mockProducts);
    vi.mocked(prisma.product.count).mockResolvedValue(2);

    const response = await $fetch('/api/products');

    expect(response.items).toEqual(mockProducts);
    expect(response.total).toBe(2);
  });
});
```

## Mocking

### Mock $fetch

```typescript
vi.stubGlobal('$fetch', vi.fn());
```

### Mock Composables

```typescript
import { mockNuxtImport } from '@nuxt/test-utils/runtime';

mockNuxtImport('useAuth', () => {
  return () => ({
    user: ref({ id: '1', name: 'Test User' }),
    isAuthenticated: ref(true),
  });
});
```

### Mock Route

```typescript
mockNuxtImport('useRoute', () => {
  return () => ({
    params: { id: '123' },
    query: { page: '1' },
    path: '/products/123',
  });
});
```

## Coverage

```typescript
// vitest.config.ts
export default defineVitestConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      exclude: [
        'node_modules',
        '.nuxt',
        'tests',
      ],
      thresholds: {
        lines: 80,
        branches: 80,
        functions: 80,
        statements: 80,
      },
    },
  },
});
```

## Best Practices

1. **Use mountSuspended** - For async component mounting
2. **Mock external deps** - $fetch, composables
3. **Test behavior** - Not implementation details
4. **Isolate tests** - Clear mocks between tests
5. **Coverage targets** - Aim for 80%+ coverage
6. **Test edge cases** - Error states, loading, empty
