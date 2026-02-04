---
name: nuxt-test
description: Template for Nuxt 3 tests with Vitest and Playwright
applies_to: nuxt
---

# Nuxt Test Template

## Composable Unit Test

```typescript
// tests/composables/use{{COMPOSABLE}}.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { use{{COMPOSABLE}} } from '~/composables/use{{COMPOSABLE}}';

// Mock $fetch
const mockFetch = vi.fn();
vi.stubGlobal('$fetch', mockFetch);

describe('use{{COMPOSABLE}}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('initializes with default state', () => {
    const { items, isLoading, error } = use{{COMPOSABLE}}({ immediate: false });

    expect(items.value).toEqual([]);
    expect(isLoading.value).toBe(false);
    expect(error.value).toBeNull();
  });

  it('fetches data successfully', async () => {
    const mockData = {
      items: [{ id: '1', name: 'Test' }],
      pagination: { page: 1, limit: 20, total: 1, totalPages: 1 },
    };
    mockFetch.mockResolvedValueOnce(mockData);

    const { items, fetch, isLoading } = use{{COMPOSABLE}}({ immediate: false });
    await fetch();

    expect(items.value).toEqual(mockData.items);
    expect(isLoading.value).toBe(false);
  });

  it('handles fetch error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    const { error, fetch } = use{{COMPOSABLE}}({ immediate: false });
    await fetch();

    expect(error.value).toBeInstanceOf(Error);
    expect(error.value?.message).toBe('Network error');
  });
});
```

## Component Test

```typescript
// tests/components/{{COMPONENT}}.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import {{COMPONENT}} from '~/components/{{COMPONENT}}.vue';

describe('{{COMPONENT}}', () => {
  it('renders with default props', async () => {
    const wrapper = await mountSuspended({{COMPONENT}}, {
      props: {
        title: 'Test Title',
      },
    });

    expect(wrapper.text()).toContain('Test Title');
  });

  it('emits click event', async () => {
    const wrapper = await mountSuspended({{COMPONENT}}, {
      props: { title: 'Test' },
    });

    await wrapper.trigger('click');

    expect(wrapper.emitted('click')).toBeTruthy();
  });

  it('renders slot content', async () => {
    const wrapper = await mountSuspended({{COMPONENT}}, {
      props: { title: 'Test' },
      slots: {
        default: '<span class="custom">Custom Content</span>',
      },
    });

    expect(wrapper.find('.custom').exists()).toBe(true);
    expect(wrapper.text()).toContain('Custom Content');
  });

  it('applies variant class', async () => {
    const wrapper = await mountSuspended({{COMPONENT}}, {
      props: {
        title: 'Test',
        variant: 'primary',
      },
    });

    expect(wrapper.classes()).toContain('{{COMPONENT_LOWER}}--primary');
  });
});
```

## Page Test

```typescript
// tests/pages/{{PAGE}}.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime';
import {{PAGE}}Page from '~/pages/{{PAGE}}/index.vue';

// Mock useFetch
mockNuxtImport('useFetch', () => {
  return () => ({
    data: ref([
      { id: '1', name: 'Item 1' },
      { id: '2', name: 'Item 2' },
    ]),
    pending: ref(false),
    error: ref(null),
    refresh: vi.fn(),
  });
});

// Mock useRoute
mockNuxtImport('useRoute', () => {
  return () => ({
    params: {},
    query: { page: '1' },
    path: '/{{PAGE_LOWER}}',
  });
});

describe('{{PAGE}} Page', () => {
  it('renders item list', async () => {
    const wrapper = await mountSuspended({{PAGE}}Page);

    expect(wrapper.text()).toContain('Item 1');
    expect(wrapper.text()).toContain('Item 2');
  });

  it('shows loading state', async () => {
    mockNuxtImport('useFetch', () => {
      return () => ({
        data: ref(null),
        pending: ref(true),
        error: ref(null),
      });
    });

    const wrapper = await mountSuspended({{PAGE}}Page);

    expect(wrapper.text()).toContain('Loading');
  });
});
```

## API Route Test

```typescript
// tests/server/api/{{RESOURCE}}.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock Prisma
vi.mock('~/server/utils/db', () => ({
  prisma: {
    {{RESOURCE}}: {
      findMany: vi.fn(),
      findUnique: vi.fn(),
      create: vi.fn(),
      update: vi.fn(),
      delete: vi.fn(),
      count: vi.fn(),
    },
  },
}));

import { prisma } from '~/server/utils/db';

describe('GET /api/{{RESOURCE}}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns paginated items', async () => {
    const mockItems = [
      { id: '1', name: 'Item 1' },
      { id: '2', name: 'Item 2' },
    ];

    vi.mocked(prisma.{{RESOURCE}}.findMany).mockResolvedValue(mockItems);
    vi.mocked(prisma.{{RESOURCE}}.count).mockResolvedValue(2);

    const response = await $fetch('/api/{{RESOURCE}}');

    expect(response.items).toEqual(mockItems);
    expect(response.pagination.total).toBe(2);
  });

  it('applies pagination parameters', async () => {
    vi.mocked(prisma.{{RESOURCE}}.findMany).mockResolvedValue([]);
    vi.mocked(prisma.{{RESOURCE}}.count).mockResolvedValue(0);

    await $fetch('/api/{{RESOURCE}}?page=2&limit=10');

    expect(prisma.{{RESOURCE}}.findMany).toHaveBeenCalledWith(
      expect.objectContaining({
        skip: 10,
        take: 10,
      })
    );
  });
});

describe('POST /api/{{RESOURCE}}', () => {
  it('creates new item', async () => {
    const newItem = { id: '1', name: 'New Item' };
    vi.mocked(prisma.{{RESOURCE}}.create).mockResolvedValue(newItem);

    const response = await $fetch('/api/{{RESOURCE}}', {
      method: 'POST',
      body: { name: 'New Item' },
    });

    expect(response).toEqual(newItem);
  });

  it('validates required fields', async () => {
    await expect(
      $fetch('/api/{{RESOURCE}}', {
        method: 'POST',
        body: {},
      })
    ).rejects.toThrow();
  });
});
```

## E2E Test with Playwright

```typescript
// tests/e2e/{{FEATURE}}.spec.ts
import { test, expect } from '@playwright/test';

test.describe('{{FEATURE}}', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/{{FEATURE_LOWER}}');
  });

  test('displays page correctly', async ({ page }) => {
    await expect(page).toHaveTitle(/{{FEATURE}}/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('lists items', async ({ page }) => {
    await expect(page.getByTestId('item-card')).toHaveCount(10);
  });

  test('searches items', async ({ page }) => {
    await page.getByPlaceholder('Search...').fill('test');
    await page.keyboard.press('Enter');

    await expect(page).toHaveURL(/\?q=test/);
  });

  test('creates new item', async ({ page }) => {
    await page.getByRole('button', { name: 'Create' }).click();
    await page.getByLabel('Name').fill('Test Item');
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Item created')).toBeVisible();
  });

  test('edits item', async ({ page }) => {
    await page.getByTestId('item-card').first().click();
    await page.getByRole('button', { name: 'Edit' }).click();
    await page.getByLabel('Name').fill('Updated Item');
    await page.getByRole('button', { name: 'Save' }).click();

    await expect(page.getByText('Item updated')).toBeVisible();
  });

  test('deletes item', async ({ page }) => {
    await page.getByTestId('item-card').first().click();
    await page.getByRole('button', { name: 'Delete' }).click();
    await page.getByRole('button', { name: 'Confirm' }).click();

    await expect(page.getByText('Item deleted')).toBeVisible();
  });
});
```

## Visual Regression Test

```typescript
// tests/e2e/visual.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Visual Regression', () => {
  test('{{PAGE}} page matches snapshot', async ({ page }) => {
    await page.goto('/{{PAGE_LOWER}}');
    await page.waitForLoadState('networkidle');

    await expect(page).toHaveScreenshot('{{PAGE_LOWER}}-page.png', {
      fullPage: true,
    });
  });

  test('{{COMPONENT}} component matches snapshot', async ({ page }) => {
    await page.goto('/{{PAGE_LOWER}}');

    const component = page.getByTestId('{{COMPONENT_LOWER}}');
    await expect(component).toHaveScreenshot('{{COMPONENT_LOWER}}.png');
  });
});
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{COMPOSABLE}}` | Composable name (PascalCase) | `Products`, `Auth` |
| `{{COMPONENT}}` | Component name (PascalCase) | `ProductCard` |
| `{{COMPONENT_LOWER}}` | Component name (lowercase) | `product-card` |
| `{{PAGE}}` | Page name (PascalCase) | `Products` |
| `{{PAGE_LOWER}}` | Page name (lowercase) | `products` |
| `{{RESOURCE}}` | Resource model name | `product` |
| `{{FEATURE}}` | Feature name (PascalCase) | `Products` |
| `{{FEATURE_LOWER}}` | Feature name (lowercase) | `products` |
