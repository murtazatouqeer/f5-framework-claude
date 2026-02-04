---
name: nextjs-test
description: Next.js test file template
applies_to: nextjs
variables:
  - name: COMPONENT_NAME
    description: Name of the component being tested
  - name: TEST_TYPE
    description: Type of test (unit, integration, e2e)
---

# Next.js Test Template

## Unit Test (Jest + Testing Library)

```tsx
// __tests__/{{COMPONENT_NAME}}.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { {{COMPONENT_NAME}} } from '@/components/{{COMPONENT_NAME | kebab}}';

describe('{{COMPONENT_NAME}}', () => {
  const defaultProps = {
    // Add default props here
  };

  it('renders correctly', () => {
    render(<{{COMPONENT_NAME}} {...defaultProps} />);

    expect(screen.getByRole('button')).toBeInTheDocument();
  });

  it('handles user interaction', async () => {
    const user = userEvent.setup();
    const onClick = jest.fn();

    render(<{{COMPONENT_NAME}} {...defaultProps} onClick={onClick} />);

    await user.click(screen.getByRole('button'));

    expect(onClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<{{COMPONENT_NAME}} {...defaultProps} isLoading />);

    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('displays error message', () => {
    render(<{{COMPONENT_NAME}} {...defaultProps} error="Something went wrong" />);

    expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong');
  });

  it('matches snapshot', () => {
    const { container } = render(<{{COMPONENT_NAME}} {...defaultProps} />);

    expect(container).toMatchSnapshot();
  });
});
```

## Form Component Test

```tsx
// __tests__/{{COMPONENT_NAME}}Form.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { {{COMPONENT_NAME}}Form } from '@/components/{{COMPONENT_NAME | kebab}}-form';

describe('{{COMPONENT_NAME}}Form', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    render(<{{COMPONENT_NAME}}Form onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'Test Name');
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'Test Name',
        email: 'test@example.com',
      });
    });
  });

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup();
    render(<{{COMPONENT_NAME}}Form onSubmit={mockOnSubmit} />);

    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(await screen.findByText(/name is required/i)).toBeInTheDocument();
    expect(await screen.findByText(/email is required/i)).toBeInTheDocument();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('shows validation error for invalid email', async () => {
    const user = userEvent.setup();
    render(<{{COMPONENT_NAME}}Form onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/email/i), 'invalid-email');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(await screen.findByText(/invalid email/i)).toBeInTheDocument();
  });

  it('disables submit button while submitting', async () => {
    const user = userEvent.setup();
    mockOnSubmit.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    render(<{{COMPONENT_NAME}}Form onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'Test');
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /submit/i }));

    expect(screen.getByRole('button', { name: /submitting/i })).toBeDisabled();
  });
});
```

## Server Action Test

```tsx
// __tests__/actions/{{COMPONENT_NAME}}.test.ts
import { create{{COMPONENT_NAME}}, update{{COMPONENT_NAME}}, delete{{COMPONENT_NAME}} } from '@/lib/actions/{{COMPONENT_NAME | kebab}}';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

// Mock dependencies
jest.mock('@/lib/db');
jest.mock('@/lib/auth');
jest.mock('next/cache', () => ({
  revalidatePath: jest.fn(),
}));

describe('{{COMPONENT_NAME}} Actions', () => {
  const mockUser = { id: 'user-1', email: 'test@example.com' };

  beforeEach(() => {
    jest.clearAllMocks();
    (auth as jest.Mock).mockResolvedValue({ user: mockUser });
  });

  describe('create{{COMPONENT_NAME}}', () => {
    it('creates item with valid data', async () => {
      const mockItem = { id: '1', name: 'Test', userId: mockUser.id };
      (db.{{COMPONENT_NAME | camel}}.create as jest.Mock).mockResolvedValue(mockItem);

      const formData = new FormData();
      formData.append('name', 'Test');

      const result = await create{{COMPONENT_NAME}}({}, formData);

      expect(result.success).toBe(true);
      expect(result.data).toEqual(mockItem);
    });

    it('returns error when not authenticated', async () => {
      (auth as jest.Mock).mockResolvedValue(null);

      const formData = new FormData();
      formData.append('name', 'Test');

      const result = await create{{COMPONENT_NAME}}({}, formData);

      expect(result.error).toBe('Unauthorized');
    });

    it('returns validation errors for invalid data', async () => {
      const formData = new FormData();
      formData.append('name', ''); // Empty name

      const result = await create{{COMPONENT_NAME}}({}, formData);

      expect(result.errors?.name).toBeDefined();
    });
  });

  describe('delete{{COMPONENT_NAME}}', () => {
    it('deletes owned item', async () => {
      const mockItem = { id: '1', userId: mockUser.id };
      (db.{{COMPONENT_NAME | camel}}.findUnique as jest.Mock).mockResolvedValue(mockItem);
      (db.{{COMPONENT_NAME | camel}}.delete as jest.Mock).mockResolvedValue(mockItem);

      const result = await delete{{COMPONENT_NAME}}('1');

      expect(result.success).toBe(true);
    });

    it('returns error when deleting others item', async () => {
      const mockItem = { id: '1', userId: 'other-user' };
      (db.{{COMPONENT_NAME | camel}}.findUnique as jest.Mock).mockResolvedValue(mockItem);

      const result = await delete{{COMPONENT_NAME}}('1');

      expect(result.error).toBe('Forbidden');
    });
  });
});
```

## E2E Test (Playwright)

```ts
// e2e/{{COMPONENT_NAME | kebab}}.spec.ts
import { test, expect } from '@playwright/test';

test.describe('{{COMPONENT_NAME}}', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/{{COMPONENT_NAME | kebab}}');
  });

  test('displays page correctly', async ({ page }) => {
    await expect(page).toHaveTitle(/{{COMPONENT_NAME}}/);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
  });

  test('creates new item', async ({ page }) => {
    await page.getByRole('button', { name: /create/i }).click();

    await page.getByLabel(/name/i).fill('New Item');
    await page.getByLabel(/description/i).fill('Item description');
    await page.getByRole('button', { name: /save/i }).click();

    await expect(page.getByText('New Item')).toBeVisible();
    await expect(page.getByText(/created successfully/i)).toBeVisible();
  });

  test('edits existing item', async ({ page }) => {
    await page.getByRole('button', { name: /edit/i }).first().click();

    await page.getByLabel(/name/i).clear();
    await page.getByLabel(/name/i).fill('Updated Item');
    await page.getByRole('button', { name: /save/i }).click();

    await expect(page.getByText('Updated Item')).toBeVisible();
  });

  test('deletes item', async ({ page }) => {
    const itemName = await page.locator('[data-testid="item-name"]').first().textContent();

    await page.getByRole('button', { name: /delete/i }).first().click();
    await page.getByRole('button', { name: /confirm/i }).click();

    await expect(page.getByText(itemName!)).not.toBeVisible();
  });

  test('shows validation errors', async ({ page }) => {
    await page.getByRole('button', { name: /create/i }).click();
    await page.getByRole('button', { name: /save/i }).click();

    await expect(page.getByText(/name is required/i)).toBeVisible();
  });

  test('handles empty state', async ({ page }) => {
    // Assuming empty state scenario
    await expect(page.getByText(/no items found/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /create/i })).toBeVisible();
  });
});
```

## API Route Test

```ts
// __tests__/api/{{COMPONENT_NAME | kebab}}.test.ts
/**
 * @jest-environment node
 */

import { GET, POST } from '@/app/api/{{COMPONENT_NAME | kebab}}/route';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

jest.mock('@/lib/db');
jest.mock('@/lib/auth');

describe('{{COMPONENT_NAME}} API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('GET /api/{{COMPONENT_NAME | kebab}}', () => {
    it('returns items', async () => {
      const mockItems = [{ id: '1', name: 'Test' }];
      (db.{{COMPONENT_NAME | camel}}.findMany as jest.Mock).mockResolvedValue(mockItems);
      (db.{{COMPONENT_NAME | camel}}.count as jest.Mock).mockResolvedValue(1);

      const request = new Request('http://localhost/api/{{COMPONENT_NAME | kebab}}');
      const response = await GET(request);
      const data = await response.json();

      expect(response.status).toBe(200);
      expect(data.items).toEqual(mockItems);
    });

    it('supports pagination', async () => {
      (db.{{COMPONENT_NAME | camel}}.findMany as jest.Mock).mockResolvedValue([]);
      (db.{{COMPONENT_NAME | camel}}.count as jest.Mock).mockResolvedValue(100);

      const request = new Request(
        'http://localhost/api/{{COMPONENT_NAME | kebab}}?page=2&limit=10'
      );
      const response = await GET(request);
      const data = await response.json();

      expect(data.pagination.page).toBe(2);
      expect(data.pagination.totalPages).toBe(10);
    });
  });

  describe('POST /api/{{COMPONENT_NAME | kebab}}', () => {
    it('creates item when authenticated', async () => {
      const mockUser = { id: 'user-1' };
      (auth as jest.Mock).mockResolvedValue({ user: mockUser });

      const mockItem = { id: '1', name: 'New Item', userId: mockUser.id };
      (db.{{COMPONENT_NAME | camel}}.create as jest.Mock).mockResolvedValue(mockItem);

      const request = new Request('http://localhost/api/{{COMPONENT_NAME | kebab}}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'New Item' }),
      });

      const response = await POST(request);
      const data = await response.json();

      expect(response.status).toBe(201);
      expect(data.name).toBe('New Item');
    });

    it('returns 401 when not authenticated', async () => {
      (auth as jest.Mock).mockResolvedValue(null);

      const request = new Request('http://localhost/api/{{COMPONENT_NAME | kebab}}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'New Item' }),
      });

      const response = await POST(request);

      expect(response.status).toBe(401);
    });
  });
});
```

## Usage

```bash
f5 generate test ProductCard --type unit
f5 generate test LoginForm --type integration
f5 generate test Checkout --type e2e
f5 generate test products --type api
```
