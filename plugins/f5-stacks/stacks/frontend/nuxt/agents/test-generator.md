---
name: nuxt-test-generator
description: Generates tests for Nuxt 3 applications
applies_to: nuxt
---

# Nuxt Test Generator Agent

## Purpose
Generate comprehensive tests for Nuxt 3 applications using Vitest and @nuxt/test-utils.

## Capabilities
- Unit tests for composables
- Component tests with Vue Test Utils
- API route tests
- E2E tests with Playwright
- Integration tests

## Input Requirements
- Test subject (composable, component, api, page)
- Test scenarios
- Mock requirements
- Coverage targets

## Output Deliverables
1. Test files
2. Test utilities/helpers
3. Mock configurations

## Generation Process

### 1. Analyze Requirements
```yaml
test_analysis:
  - subject: "useProducts composable"
  - type: "unit"
  - scenarios: ["fetch", "create", "error handling"]
  - mocks: ["$fetch"]
```

### 2. Generate Test Patterns

#### Composable Unit Test
```typescript
// tests/composables/useProducts.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useProducts } from '~/composables/useProducts';

// Mock $fetch
const mockFetch = vi.fn();
vi.stubGlobal('$fetch', mockFetch);

describe('useProducts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('fetch', () => {
    it('should fetch products successfully', async () => {
      const mockResponse = {
        items: [
          { id: '1', name: 'Product 1' },
          { id: '2', name: 'Product 2' },
        ],
        total: 2,
      };

      mockFetch.mockResolvedValueOnce(mockResponse);

      const { items, total, fetch } = useProducts({ immediate: false });

      await fetch();

      expect(mockFetch).toHaveBeenCalledWith('/api/products', {
        query: { page: 1, limit: 20 },
      });
      expect(items.value).toEqual(mockResponse.items);
      expect(total.value).toBe(2);
    });

    it('should handle fetch error', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      const { error, fetch } = useProducts({ immediate: false });

      await fetch();

      expect(error.value).toBeInstanceOf(Error);
      expect(error.value?.message).toBe('Network error');
    });
  });

  describe('create', () => {
    it('should create product and add to list', async () => {
      const newProduct = { id: '3', name: 'New Product' };
      mockFetch.mockResolvedValueOnce(newProduct);

      const { items, create } = useProducts({ immediate: false });

      const result = await create({ name: 'New Product' });

      expect(mockFetch).toHaveBeenCalledWith('/api/products', {
        method: 'POST',
        body: { name: 'New Product' },
      });
      expect(result).toEqual(newProduct);
      expect(items.value[0]).toEqual(newProduct);
    });
  });

  describe('pagination', () => {
    it('should calculate totalPages correctly', async () => {
      mockFetch.mockResolvedValueOnce({ items: [], total: 45 });

      const { totalPages, fetch } = useProducts({ pageSize: 20 });
      await fetch();

      expect(totalPages.value).toBe(3);
    });

    it('should load more items', async () => {
      mockFetch
        .mockResolvedValueOnce({ items: [{ id: '1' }], total: 2 })
        .mockResolvedValueOnce({ items: [{ id: '2' }], total: 2 });

      const { items, loadMore, fetch } = useProducts({ pageSize: 1 });

      await fetch();
      expect(items.value).toHaveLength(1);

      await loadMore();
      expect(items.value).toHaveLength(2);
    });
  });
});
```

#### Component Test
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
    status: 'active',
  };

  it('should render product information', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
    });

    expect(wrapper.text()).toContain('Test Product');
    expect(wrapper.text()).toContain('A test product');
    expect(wrapper.text()).toContain('99.99');
  });

  it('should emit select event on click', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
    });

    await wrapper.find('.product-card').trigger('click');

    expect(wrapper.emitted('select')).toBeTruthy();
    expect(wrapper.emitted('select')![0]).toEqual([mockProduct]);
  });

  it('should emit delete event', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
    });

    await wrapper.find('[data-testid="delete-btn"]').trigger('click');

    expect(wrapper.emitted('delete')).toBeTruthy();
    expect(wrapper.emitted('delete')![0]).toEqual([mockProduct.id]);
  });

  it('should apply disabled styles when disabled', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct, disabled: true },
    });

    expect(wrapper.classes()).toContain('product-card--disabled');
  });

  it('should render slot content', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
      slots: {
        actions: '<button>Custom Action</button>',
      },
    });

    expect(wrapper.text()).toContain('Custom Action');
  });
});
```

#### API Route Test
```typescript
// tests/server/api/products.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { createEvent } from 'h3';

// Mock Prisma
vi.mock('~/server/utils/db', () => ({
  prisma: {
    product: {
      findMany: vi.fn(),
      count: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
    },
  },
}));

import { prisma } from '~/server/utils/db';
import getProducts from '~/server/api/products/index.get';
import createProduct from '~/server/api/products/index.post';

describe('Products API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('GET /api/products', () => {
    it('should return paginated products', async () => {
      const mockProducts = [
        { id: '1', name: 'Product 1' },
        { id: '2', name: 'Product 2' },
      ];

      vi.mocked(prisma.product.findMany).mockResolvedValue(mockProducts);
      vi.mocked(prisma.product.count).mockResolvedValue(2);

      const event = createEvent({
        method: 'GET',
        url: '/api/products?page=1&limit=20',
      });

      const result = await getProducts(event);

      expect(result.items).toEqual(mockProducts);
      expect(result.total).toBe(2);
      expect(result.page).toBe(1);
    });

    it('should filter by search query', async () => {
      const event = createEvent({
        method: 'GET',
        url: '/api/products?search=test',
      });

      await getProducts(event);

      expect(prisma.product.findMany).toHaveBeenCalledWith(
        expect.objectContaining({
          where: expect.objectContaining({
            OR: expect.arrayContaining([
              { name: { contains: 'test', mode: 'insensitive' } },
            ]),
          }),
        })
      );
    });
  });

  describe('POST /api/products', () => {
    it('should create a new product', async () => {
      const newProduct = { id: '1', name: 'New Product' };
      vi.mocked(prisma.product.create).mockResolvedValue(newProduct);

      const event = createEvent({
        method: 'POST',
        url: '/api/products',
        body: { name: 'New Product', price: 99 },
      });

      // Mock auth
      event.context.user = { id: 'user-1' };

      const result = await createProduct(event);

      expect(result).toEqual(newProduct);
    });

    it('should return 400 for invalid data', async () => {
      const event = createEvent({
        method: 'POST',
        url: '/api/products',
        body: { name: '' }, // Invalid: empty name
      });

      await expect(createProduct(event)).rejects.toThrow();
    });
  });
});
```

#### E2E Test with Playwright
```typescript
// tests/e2e/products.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Products Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/products');
  });

  test('should display products list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();
    await expect(page.getByTestId('product-card')).toHaveCount(20);
  });

  test('should search products', async ({ page }) => {
    await page.getByPlaceholder('Search...').fill('test');
    await page.waitForURL(/\?q=test/);

    await expect(page.getByTestId('product-card')).toHaveCount(5);
  });

  test('should navigate to product detail', async ({ page }) => {
    await page.getByTestId('product-card').first().click();

    await expect(page).toHaveURL(/\/products\/[\w-]+/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('should create new product', async ({ page }) => {
    await page.getByRole('link', { name: 'Create Product' }).click();

    await page.getByLabel('Name').fill('New Product');
    await page.getByLabel('Price').fill('99.99');
    await page.getByRole('button', { name: 'Create' }).click();

    await expect(page.getByText('Product created')).toBeVisible();
  });
});
```

## Test Configuration

### vitest.config.ts
```typescript
import { defineVitestConfig } from '@nuxt/test-utils/config';

export default defineVitestConfig({
  test: {
    environment: 'nuxt',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: ['node_modules', 'tests'],
    },
  },
});
```

## Quality Checklist
- [ ] Unit tests for composables
- [ ] Component tests with proper mounts
- [ ] API route tests with mocked DB
- [ ] E2E tests for critical flows
- [ ] Coverage meets targets (80%+)
- [ ] Tests are isolated and repeatable
