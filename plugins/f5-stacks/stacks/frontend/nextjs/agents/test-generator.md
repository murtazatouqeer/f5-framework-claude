# Next.js Test Generator Agent

## Role
Generate tests for Next.js applications using Jest, Testing Library, and Playwright.

## Triggers
- "create test"
- "nextjs test"
- "test page"
- "test component"

## Capabilities
- Generate unit tests with Jest
- Generate component tests with Testing Library
- Generate E2E tests with Playwright
- Mock Server Actions
- Test Server Components
- Test Client Components

## Input Requirements
```yaml
required:
  - target: string         # File/component to test
  - type: string           # unit | component | e2e | integration

optional:
  - coverage: array        # Specific scenarios to cover
  - mocks: object          # Dependencies to mock
  - setup: string          # Test setup requirements
```

## Output Structure
```
__tests__/
├── unit/
│   └── {module}.test.ts
├── components/
│   └── {component}.test.tsx
├── integration/
│   └── {feature}.test.ts
└── e2e/
    └── {flow}.spec.ts
```

## Generation Rules

### 1. Component Test (Testing Library)
```tsx
// __tests__/components/product-card.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProductCard } from '@/components/product-card';

const mockProduct = {
  id: '1',
  name: 'Test Product',
  description: 'A test product description',
  price: 29.99,
  imageUrl: '/test-image.jpg',
  category: { name: 'Electronics' },
};

describe('ProductCard', () => {
  it('renders product information correctly', () => {
    render(<ProductCard product={mockProduct} />);

    expect(screen.getByText('Test Product')).toBeInTheDocument();
    expect(screen.getByText('A test product description')).toBeInTheDocument();
    expect(screen.getByText('$29.99')).toBeInTheDocument();
    expect(screen.getByText('Electronics')).toBeInTheDocument();
  });

  it('renders product image with correct alt text', () => {
    render(<ProductCard product={mockProduct} />);

    const image = screen.getByRole('img', { name: 'Test Product' });
    expect(image).toBeInTheDocument();
  });

  it('renders placeholder when no image', () => {
    const productWithoutImage = { ...mockProduct, imageUrl: null };
    render(<ProductCard product={productWithoutImage} />);

    expect(screen.getByText('No image')).toBeInTheDocument();
  });

  it('links to product detail page', () => {
    render(<ProductCard product={mockProduct} />);

    const link = screen.getByRole('link');
    expect(link).toHaveAttribute('href', '/products/1');
  });

  it('truncates long descriptions', () => {
    const longDescription = 'A'.repeat(200);
    const product = { ...mockProduct, description: longDescription };
    render(<ProductCard product={product} />);

    const description = screen.getByText(/^A+/);
    expect(description).toHaveClass('line-clamp-2');
  });
});
```

### 2. Client Component Test with Interactions
```tsx
// __tests__/components/search-input.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useRouter, useSearchParams } from 'next/navigation';
import { SearchInput } from '@/components/search-input';

jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useSearchParams: jest.fn(),
}));

describe('SearchInput', () => {
  const mockPush = jest.fn();
  const mockSearchParams = new URLSearchParams();

  beforeEach(() => {
    jest.clearAllMocks();
    (useRouter as jest.Mock).mockReturnValue({ push: mockPush });
    (useSearchParams as jest.Mock).mockReturnValue(mockSearchParams);
  });

  it('renders with placeholder', () => {
    render(<SearchInput placeholder="Search products..." />);

    expect(screen.getByPlaceholderText('Search products...')).toBeInTheDocument();
  });

  it('updates URL on input change', async () => {
    const user = userEvent.setup();
    render(<SearchInput />);

    const input = screen.getByRole('searchbox');
    await user.type(input, 'test');

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('?q=test');
    }, { timeout: 500 });
  });

  it('clears search on clear button click', async () => {
    const user = userEvent.setup();
    const params = new URLSearchParams('q=existing');
    (useSearchParams as jest.Mock).mockReturnValue(params);

    render(<SearchInput />);

    const clearButton = screen.getByRole('button');
    await user.click(clearButton);

    await waitFor(() => {
      expect(mockPush).toHaveBeenCalledWith('?');
    });
  });

  it('shows loading indicator during transition', async () => {
    const user = userEvent.setup();
    render(<SearchInput />);

    const input = screen.getByRole('searchbox');
    await user.type(input, 'test');

    // Loading indicator should appear during transition
    expect(screen.queryByRole('progressbar')).toBeInTheDocument();
  });
});
```

### 3. Server Action Test
```tsx
// __tests__/actions/products.test.ts
import { createProduct, updateProduct, deleteProduct } from '@/lib/actions/products';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';
import { revalidatePath, revalidateTag } from 'next/cache';

jest.mock('@/lib/db', () => ({
  db: {
    product: {
      create: jest.fn(),
      update: jest.fn(),
      delete: jest.fn(),
      findUnique: jest.fn(),
    },
  },
}));

jest.mock('@/lib/auth', () => ({
  auth: jest.fn(),
}));

jest.mock('next/cache', () => ({
  revalidatePath: jest.fn(),
  revalidateTag: jest.fn(),
}));

describe('Product Actions', () => {
  const mockSession = { user: { id: 'user-1' } };

  beforeEach(() => {
    jest.clearAllMocks();
    (auth as jest.Mock).mockResolvedValue(mockSession);
  });

  describe('createProduct', () => {
    it('creates product with valid data', async () => {
      const formData = new FormData();
      formData.set('name', 'Test Product');
      formData.set('description', 'A test product');
      formData.set('price', '29.99');
      formData.set('categoryId', '123e4567-e89b-12d3-a456-426614174000');

      (db.product.create as jest.Mock).mockResolvedValue({
        id: 'product-1',
        name: 'Test Product',
      });

      const result = await createProduct({ success: false, message: '' }, formData);

      expect(result.success).toBe(true);
      expect(result.message).toBe('Product created successfully');
      expect(db.product.create).toHaveBeenCalledWith({
        data: expect.objectContaining({
          name: 'Test Product',
          price: 29.99,
          userId: 'user-1',
        }),
      });
      expect(revalidatePath).toHaveBeenCalledWith('/products');
      expect(revalidateTag).toHaveBeenCalledWith('products');
    });

    it('returns error for invalid data', async () => {
      const formData = new FormData();
      formData.set('name', 'A'); // Too short
      formData.set('price', '-10'); // Negative

      const result = await createProduct({ success: false, message: '' }, formData);

      expect(result.success).toBe(false);
      expect(result.errors).toBeDefined();
      expect(db.product.create).not.toHaveBeenCalled();
    });

    it('returns error when not authenticated', async () => {
      (auth as jest.Mock).mockResolvedValue(null);

      const formData = new FormData();
      formData.set('name', 'Test Product');

      const result = await createProduct({ success: false, message: '' }, formData);

      expect(result.success).toBe(false);
      expect(result.message).toBe('Unauthorized');
    });
  });

  describe('updateProduct', () => {
    it('updates product when user owns it', async () => {
      (db.product.findUnique as jest.Mock).mockResolvedValue({
        userId: 'user-1',
      });
      (db.product.update as jest.Mock).mockResolvedValue({
        id: 'product-1',
      });

      const formData = new FormData();
      formData.set('name', 'Updated Name');

      const result = await updateProduct(
        'product-1',
        { success: false, message: '' },
        formData
      );

      expect(result.success).toBe(true);
      expect(db.product.update).toHaveBeenCalled();
    });

    it('returns error when user does not own product', async () => {
      (db.product.findUnique as jest.Mock).mockResolvedValue({
        userId: 'other-user',
      });

      const formData = new FormData();
      formData.set('name', 'Updated Name');

      const result = await updateProduct(
        'product-1',
        { success: false, message: '' },
        formData
      );

      expect(result.success).toBe(false);
      expect(result.message).toBe('Forbidden');
      expect(db.product.update).not.toHaveBeenCalled();
    });
  });

  describe('deleteProduct', () => {
    it('deletes product when user owns it', async () => {
      (db.product.findUnique as jest.Mock).mockResolvedValue({
        userId: 'user-1',
      });

      const result = await deleteProduct('product-1');

      expect(result.success).toBe(true);
      expect(db.product.delete).toHaveBeenCalledWith({
        where: { id: 'product-1' },
      });
    });
  });
});
```

### 4. API Route Test
```tsx
// __tests__/api/products.test.ts
import { GET, POST } from '@/app/api/products/route';
import { db } from '@/lib/db';
import { NextResponse } from 'next/server';

jest.mock('@/lib/db', () => ({
  db: {
    product: {
      findMany: jest.fn(),
      count: jest.fn(),
      create: jest.fn(),
    },
  },
}));

describe('GET /api/products', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns paginated products', async () => {
    const mockProducts = [
      { id: '1', name: 'Product 1' },
      { id: '2', name: 'Product 2' },
    ];

    (db.product.findMany as jest.Mock).mockResolvedValue(mockProducts);
    (db.product.count as jest.Mock).mockResolvedValue(2);

    const request = new Request('http://localhost/api/products?page=1&limit=10');
    const response = await GET(request);
    const data = await response.json();

    expect(response.status).toBe(200);
    expect(data.data).toEqual(mockProducts);
    expect(data.pagination).toEqual({
      page: 1,
      limit: 10,
      total: 2,
      totalPages: 1,
    });
  });

  it('handles errors gracefully', async () => {
    (db.product.findMany as jest.Mock).mockRejectedValue(new Error('DB Error'));

    const request = new Request('http://localhost/api/products');
    const response = await GET(request);

    expect(response.status).toBe(500);
  });
});

describe('POST /api/products', () => {
  it('creates product with valid data', async () => {
    const mockProduct = { id: '1', name: 'New Product' };
    (db.product.create as jest.Mock).mockResolvedValue(mockProduct);

    const request = new Request('http://localhost/api/products', {
      method: 'POST',
      body: JSON.stringify({
        name: 'New Product',
        price: 29.99,
        categoryId: '123e4567-e89b-12d3-a456-426614174000',
      }),
    });

    const response = await POST(request);
    const data = await response.json();

    expect(response.status).toBe(201);
    expect(data.name).toBe('New Product');
  });

  it('returns 400 for invalid data', async () => {
    const request = new Request('http://localhost/api/products', {
      method: 'POST',
      body: JSON.stringify({
        name: 'A', // Too short
      }),
    });

    const response = await POST(request);

    expect(response.status).toBe(400);
  });
});
```

### 5. E2E Test (Playwright)
```tsx
// e2e/products.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Products', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/products');
  });

  test('displays product list', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Products' })).toBeVisible();

    // Wait for products to load
    await expect(page.locator('[data-testid="product-card"]').first()).toBeVisible();
  });

  test('filters products by search', async ({ page }) => {
    const searchInput = page.getByPlaceholder('Search products...');
    await searchInput.fill('laptop');

    // Wait for URL to update
    await expect(page).toHaveURL(/q=laptop/);

    // Verify filtered results
    await expect(page.locator('[data-testid="product-card"]')).toContainText('laptop');
  });

  test('navigates to product detail', async ({ page }) => {
    const firstProduct = page.locator('[data-testid="product-card"]').first();
    const productName = await firstProduct.locator('h3').textContent();

    await firstProduct.click();

    await expect(page).toHaveURL(/\/products\/\w+/);
    await expect(page.getByRole('heading', { level: 1 })).toContainText(productName!);
  });

  test('pagination works correctly', async ({ page }) => {
    // Click next page
    await page.getByRole('button', { name: 'Next' }).click();

    await expect(page).toHaveURL(/page=2/);

    // Click previous
    await page.getByRole('button', { name: 'Previous' }).click();

    await expect(page).not.toHaveURL(/page=2/);
  });
});

test.describe('Product CRUD', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
  });

  test('creates new product', async ({ page }) => {
    await page.goto('/products/new');

    await page.fill('input[name="name"]', 'Test Product');
    await page.fill('textarea[name="description"]', 'A test product');
    await page.fill('input[name="price"]', '29.99');
    await page.selectOption('select[name="categoryId"]', { index: 1 });

    await page.click('button[type="submit"]');

    await expect(page.getByText('Product created successfully')).toBeVisible();
  });

  test('edits existing product', async ({ page }) => {
    await page.goto('/products');

    // Click first product's edit button
    await page.locator('[data-testid="product-card"]').first().click();
    await page.click('button:has-text("Edit")');

    await page.fill('input[name="name"]', 'Updated Product Name');
    await page.click('button[type="submit"]');

    await expect(page.getByText('Product updated successfully')).toBeVisible();
  });

  test('deletes product', async ({ page }) => {
    await page.goto('/products');

    const productCard = page.locator('[data-testid="product-card"]').first();
    await productCard.click();

    await page.click('button:has-text("Delete")');
    await page.click('button:has-text("Confirm")');

    await expect(page.getByText('Product deleted successfully')).toBeVisible();
    await expect(page).toHaveURL('/products');
  });
});
```

## Test Utilities
```tsx
// __tests__/utils/test-utils.tsx
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';

// Custom providers wrapper
function AllTheProviders({ children }: { children: React.ReactNode }) {
  return (
    <>{children}</>
  );
}

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

## Validation Checklist
- [ ] Tests follow AAA pattern (Arrange, Act, Assert)
- [ ] All mocks are properly typed
- [ ] beforeEach clears mocks
- [ ] Edge cases covered (errors, empty states)
- [ ] Async operations properly awaited
- [ ] User interactions use userEvent
- [ ] Proper test isolation
- [ ] Meaningful test descriptions
