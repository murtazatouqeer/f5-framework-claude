# React Test Template

Production-ready test templates using React Testing Library and Vitest.

## Component Test Template

```tsx
// components/{{ComponentName}}/__tests__/{{ComponentName}}.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { {{ComponentName}} } from '../{{ComponentName}}';

describe('{{ComponentName}}', () => {
  const user = userEvent.setup();

  // Default props for testing
  const defaultProps = {
    onClick: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders with default props', () => {
      render(<{{ComponentName}} {...defaultProps}>Content</{{ComponentName}}>);

      expect(screen.getByTestId('{{component-name}}')).toBeInTheDocument();
      expect(screen.getByText('Content')).toBeInTheDocument();
    });

    it('renders with custom className', () => {
      render(
        <{{ComponentName}} {...defaultProps} className="custom-class">
          Content
        </{{ComponentName}}>
      );

      expect(screen.getByTestId('{{component-name}}')).toHaveClass('custom-class');
    });

    it('renders different variants', () => {
      const { rerender } = render(
        <{{ComponentName}} {...defaultProps} variant="default">
          Content
        </{{ComponentName}}>
      );

      expect(screen.getByTestId('{{component-name}}')).toHaveClass('variant-default');

      rerender(
        <{{ComponentName}} {...defaultProps} variant="primary">
          Content
        </{{ComponentName}}>
      );

      expect(screen.getByTestId('{{component-name}}')).toHaveClass('variant-primary');
    });

    it('renders loading state', () => {
      render(<{{ComponentName}} {...defaultProps} isLoading />);

      expect(screen.getByLabelText('Loading')).toBeInTheDocument();
    });

    it('renders disabled state', () => {
      render(<{{ComponentName}} {...defaultProps} disabled />);

      expect(screen.getByTestId('{{component-name}}')).toHaveAttribute(
        'aria-disabled',
        'true'
      );
    });
  });

  describe('interactions', () => {
    it('calls onClick when clicked', async () => {
      render(<{{ComponentName}} {...defaultProps}>Click me</{{ComponentName}}>);

      await user.click(screen.getByText('Click me'));

      expect(defaultProps.onClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      render(
        <{{ComponentName}} {...defaultProps} disabled>
          Click me
        </{{ComponentName}}>
      );

      await user.click(screen.getByText('Click me'));

      expect(defaultProps.onClick).not.toHaveBeenCalled();
    });

    it('handles keyboard navigation', async () => {
      render(
        <{{ComponentName}} {...defaultProps} tabIndex={0}>
          Focus me
        </{{ComponentName}}>
      );

      await user.tab();

      expect(screen.getByText('Focus me')).toHaveFocus();
    });

    it('handles Enter key press', async () => {
      render(<{{ComponentName}} {...defaultProps}>Press Enter</{{ComponentName}}>);

      const element = screen.getByText('Press Enter');
      element.focus();
      await user.keyboard('{Enter}');

      expect(defaultProps.onClick).toHaveBeenCalledTimes(1);
    });
  });

  describe('accessibility', () => {
    it('has correct ARIA attributes', () => {
      render(<{{ComponentName}} {...defaultProps} disabled />);

      const element = screen.getByTestId('{{component-name}}');
      expect(element).toHaveAttribute('aria-disabled', 'true');
    });

    it('is focusable when enabled', () => {
      render(<{{ComponentName}} {...defaultProps} />);

      const element = screen.getByTestId('{{component-name}}');
      element.focus();

      expect(element).toHaveFocus();
    });

    it('has accessible name', () => {
      render(
        <{{ComponentName}} {...defaultProps} aria-label="Custom label">
          Content
        </{{ComponentName}}>
      );

      expect(screen.getByLabelText('Custom label')).toBeInTheDocument();
    });
  });

  describe('edge cases', () => {
    it('handles empty children', () => {
      render(<{{ComponentName}} {...defaultProps} />);

      expect(screen.getByTestId('{{component-name}}')).toBeEmptyDOMElement();
    });

    it('handles null children', () => {
      render(<{{ComponentName}} {...defaultProps}>{null}</{{ComponentName}}>);

      expect(screen.getByTestId('{{component-name}}')).toBeEmptyDOMElement();
    });

    it('handles complex children', () => {
      render(
        <{{ComponentName}} {...defaultProps}>
          <span>First</span>
          <span>Second</span>
        </{{ComponentName}}>
      );

      expect(screen.getByText('First')).toBeInTheDocument();
      expect(screen.getByText('Second')).toBeInTheDocument();
    });
  });
});
```

## Form Component Test Template

```tsx
// features/{{feature}}/components/__tests__/{{Entity}}Form.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { {{Entity}}Form } from '../{{Entity}}Form';

// Mock dependencies
vi.mock('@/hooks/useToast', () => ({
  useToast: () => ({
    toast: vi.fn(),
  }),
}));

describe('{{Entity}}Form', () => {
  const user = userEvent.setup();

  const mockOnSubmit = vi.fn();
  const mockOnCancel = vi.fn();

  const defaultProps = {
    onSubmit: mockOnSubmit,
    onCancel: mockOnCancel,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders all form fields', () => {
      render(<{{Entity}}Form {...defaultProps} />);

      expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    });

    it('renders Create button when no defaultValues', () => {
      render(<{{Entity}}Form {...defaultProps} />);

      expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument();
    });

    it('renders Update button when defaultValues provided', () => {
      render(
        <{{Entity}}Form
          {...defaultProps}
          defaultValues={{ name: 'Test', email: 'test@example.com' }}
        />
      );

      expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument();
    });

    it('pre-fills form with defaultValues', () => {
      render(
        <{{Entity}}Form
          {...defaultProps}
          defaultValues={{ name: 'Test Name', email: 'test@example.com' }}
        />
      );

      expect(screen.getByLabelText(/name/i)).toHaveValue('Test Name');
      expect(screen.getByLabelText(/email/i)).toHaveValue('test@example.com');
    });
  });

  describe('validation', () => {
    it('shows error for empty required fields', async () => {
      render(<{{Entity}}Form {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(screen.getByText(/name must be at least/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('shows error for invalid email', async () => {
      render(<{{Entity}}Form {...defaultProps} />);

      await user.type(screen.getByLabelText(/name/i), 'Test Name');
      await user.type(screen.getByLabelText(/email/i), 'invalid-email');
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(screen.getByText(/invalid email/i)).toBeInTheDocument();
      });

      expect(mockOnSubmit).not.toHaveBeenCalled();
    });

    it('clears error when field is corrected', async () => {
      render(<{{Entity}}Form {...defaultProps} />);

      // Trigger error
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(screen.getByText(/name must be at least/i)).toBeInTheDocument();
      });

      // Fix error
      await user.type(screen.getByLabelText(/name/i), 'Valid Name');

      await waitFor(() => {
        expect(screen.queryByText(/name must be at least/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('submission', () => {
    it('submits form with valid data', async () => {
      mockOnSubmit.mockResolvedValueOnce(undefined);
      render(<{{Entity}}Form {...defaultProps} />);

      await user.type(screen.getByLabelText(/name/i), 'Test Name');
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(mockOnSubmit).toHaveBeenCalledWith(
          expect.objectContaining({
            name: 'Test Name',
            email: 'test@example.com',
          })
        );
      });
    });

    it('disables submit button while submitting', () => {
      render(<{{Entity}}Form {...defaultProps} isSubmitting />);

      expect(screen.getByRole('button', { name: /create/i })).toBeDisabled();
    });

    it('resets form after successful submission', async () => {
      mockOnSubmit.mockResolvedValueOnce(undefined);
      render(<{{Entity}}Form {...defaultProps} />);

      await user.type(screen.getByLabelText(/name/i), 'Test Name');
      await user.type(screen.getByLabelText(/email/i), 'test@example.com');
      await user.click(screen.getByRole('button', { name: /create/i }));

      await waitFor(() => {
        expect(screen.getByLabelText(/name/i)).toHaveValue('');
      });
    });
  });

  describe('cancel', () => {
    it('calls onCancel when cancel button clicked', async () => {
      render(<{{Entity}}Form {...defaultProps} />);

      await user.click(screen.getByRole('button', { name: /cancel/i }));

      expect(mockOnCancel).toHaveBeenCalledTimes(1);
    });
  });
});
```

## Hook Test Template

```tsx
// hooks/__tests__/use{{HookName}}.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { use{{HookName}} } from '../use{{HookName}}';

describe('use{{HookName}}', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('initial state', () => {
    it('returns initial value', () => {
      const { result } = renderHook(() => use{{HookName}}('initial'));

      expect(result.current.value).toBe('initial');
    });

    it('returns default value when no initial provided', () => {
      const { result } = renderHook(() => use{{HookName}}());

      expect(result.current.value).toBe(null);
    });
  });

  describe('state updates', () => {
    it('updates value', () => {
      const { result } = renderHook(() => use{{HookName}}('initial'));

      act(() => {
        result.current.setValue('updated');
      });

      expect(result.current.value).toBe('updated');
    });

    it('resets value', () => {
      const { result } = renderHook(() => use{{HookName}}('initial'));

      act(() => {
        result.current.setValue('updated');
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.value).toBe('initial');
    });
  });

  describe('async operations', () => {
    it('handles async fetch', async () => {
      const mockFetch = vi.fn().mockResolvedValue({ data: 'fetched' });

      const { result } = renderHook(() => use{{HookName}}({ fetch: mockFetch }));

      expect(result.current.isLoading).toBe(true);

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false);
      });

      expect(result.current.data).toEqual({ data: 'fetched' });
    });

    it('handles fetch error', async () => {
      const mockFetch = vi.fn().mockRejectedValue(new Error('Fetch failed'));

      const { result } = renderHook(() => use{{HookName}}({ fetch: mockFetch }));

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error?.message).toBe('Fetch failed');
    });
  });

  describe('cleanup', () => {
    it('cleans up on unmount', () => {
      const cleanup = vi.fn();
      const { unmount } = renderHook(() =>
        use{{HookName}}({ onCleanup: cleanup })
      );

      unmount();

      expect(cleanup).toHaveBeenCalledTimes(1);
    });
  });
});
```

## Context Test Template

```tsx
// contexts/__tests__/{{ContextName}}Context.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { {{ContextName}}Provider, use{{ContextName}} } from '../{{ContextName}}Context';

// Test component that uses the context
function TestConsumer() {
  const { value, setValue, isLoading } = use{{ContextName}}();

  return (
    <div>
      {isLoading ? (
        <span>Loading...</span>
      ) : (
        <>
          <span data-testid="value">{value}</span>
          <button onClick={() => setValue('updated')}>Update</button>
        </>
      )}
    </div>
  );
}

// Wrapper for rendering with provider
function renderWithProvider(ui: React.ReactElement, providerProps = {}) {
  return render(
    <{{ContextName}}Provider {...providerProps}>{ui}</{{ContextName}}Provider>
  );
}

describe('{{ContextName}}Context', () => {
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Provider', () => {
    it('provides initial value', () => {
      renderWithProvider(<TestConsumer />, { initialValue: { value: 'initial' } });

      expect(screen.getByTestId('value')).toHaveTextContent('initial');
    });

    it('provides default value when no initial provided', () => {
      renderWithProvider(<TestConsumer />);

      expect(screen.getByTestId('value')).toHaveTextContent('');
    });
  });

  describe('Consumer', () => {
    it('throws error when used outside provider', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => render(<TestConsumer />)).toThrow(
        'use{{ContextName}} must be used within a {{ContextName}}Provider'
      );

      consoleSpy.mockRestore();
    });

    it('updates value through context', async () => {
      renderWithProvider(<TestConsumer />);

      await user.click(screen.getByRole('button', { name: /update/i }));

      expect(screen.getByTestId('value')).toHaveTextContent('updated');
    });
  });

  describe('async operations', () => {
    it('shows loading state during fetch', () => {
      renderWithProvider(<TestConsumer />, {
        fetchOnMount: true,
      });

      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('shows data after fetch completes', async () => {
      renderWithProvider(<TestConsumer />, {
        fetchOnMount: true,
        mockData: { value: 'fetched' },
      });

      await waitFor(() => {
        expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
      });

      expect(screen.getByTestId('value')).toHaveTextContent('fetched');
    });
  });
});
```

## Integration Test Template

```tsx
// features/{{feature}}/__tests__/{{Feature}}.integration.test.tsx
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { {{Feature}}Page } from '../pages/{{Feature}}Page';
import { {{Feature}}DetailPage } from '../pages/{{Feature}}DetailPage';

// MSW server setup
const server = setupServer(
  http.get('/api/{{features}}', () => {
    return HttpResponse.json({
      data: [
        { id: '1', name: 'Item 1', status: 'active' },
        { id: '2', name: 'Item 2', status: 'inactive' },
      ],
      meta: { total: 2, page: 1, totalPages: 1 },
    });
  }),

  http.get('/api/{{features}}/:id', ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: `Item ${params.id}`,
      status: 'active',
      description: 'Test description',
    });
  }),

  http.post('/api/{{features}}', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: '3',
      ...body,
    }, { status: 201 });
  }),

  http.delete('/api/{{features}}/:id', () => {
    return new HttpResponse(null, { status: 204 });
  })
);

// Test utilities
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderWithProviders(
  ui: React.ReactElement,
  { route = '/{{features}}' } = {}
) {
  const queryClient = createTestQueryClient();

  return {
    ...render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[route]}>
          <Routes>
            <Route path="/{{features}}" element={<{{Feature}}Page />} />
            <Route path="/{{features}}/:id" element={<{{Feature}}DetailPage />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    ),
    queryClient,
  };
}

describe('{{Feature}} Integration', () => {
  const user = userEvent.setup();

  beforeAll(() => server.listen());
  afterEach(() => server.resetHandlers());
  afterAll(() => server.close());

  describe('List Page', () => {
    it('loads and displays items', async () => {
      renderWithProviders(<{{Feature}}Page />);

      // Loading state
      expect(screen.getByText(/loading/i)).toBeInTheDocument();

      // Data loaded
      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
        expect(screen.getByText('Item 2')).toBeInTheDocument();
      });
    });

    it('shows empty state when no data', async () => {
      server.use(
        http.get('/api/{{features}}', () => {
          return HttpResponse.json({
            data: [],
            meta: { total: 0, page: 1, totalPages: 0 },
          });
        })
      );

      renderWithProviders(<{{Feature}}Page />);

      await waitFor(() => {
        expect(screen.getByText(/no {{features}} found/i)).toBeInTheDocument();
      });
    });

    it('handles API error', async () => {
      server.use(
        http.get('/api/{{features}}', () => {
          return new HttpResponse(null, { status: 500 });
        })
      );

      renderWithProviders(<{{Feature}}Page />);

      await waitFor(() => {
        expect(screen.getByText(/error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Detail Page', () => {
    it('loads and displays item details', async () => {
      renderWithProviders(<{{Feature}}DetailPage />, {
        route: '/{{features}}/1',
      });

      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
        expect(screen.getByText('Test description')).toBeInTheDocument();
      });
    });

    it('navigates to edit page', async () => {
      renderWithProviders(<{{Feature}}DetailPage />, {
        route: '/{{features}}/1',
      });

      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('link', { name: /edit/i }));

      // Check navigation or form appearance
    });

    it('deletes item and navigates back', async () => {
      renderWithProviders(<{{Feature}}DetailPage />, {
        route: '/{{features}}/1',
      });

      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
      });

      await user.click(screen.getByRole('button', { name: /delete/i }));

      // Confirm dialog
      await user.click(screen.getByRole('button', { name: /confirm/i }));

      await waitFor(() => {
        // Should navigate away or show success message
      });
    });
  });

  describe('Create Flow', () => {
    it('creates new item and shows success', async () => {
      renderWithProviders(<{{Feature}}Page />);

      await waitFor(() => {
        expect(screen.getByText('Item 1')).toBeInTheDocument();
      });

      // Click create button
      await user.click(screen.getByRole('link', { name: /create/i }));

      // Fill form
      await user.type(screen.getByLabelText(/name/i), 'New Item');
      await user.click(screen.getByRole('button', { name: /submit/i }));

      // Success feedback
      await waitFor(() => {
        expect(screen.getByText(/created successfully/i)).toBeInTheDocument();
      });
    });
  });
});
```

## Test Utilities

```tsx
// test/utils.tsx
import { type ReactElement, type ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';

// Create a fresh query client for each test
function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
      mutations: {
        retry: false,
      },
    },
  });
}

interface WrapperProps {
  children: ReactNode;
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  route?: string;
  queryClient?: QueryClient;
}

function createWrapper(options: CustomRenderOptions = {}) {
  const queryClient = options.queryClient ?? createTestQueryClient();

  return function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={[options.route ?? '/']}>
          <ThemeProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </ThemeProvider>
        </MemoryRouter>
      </QueryClientProvider>
    );
  };
}

function customRender(ui: ReactElement, options: CustomRenderOptions = {}) {
  const queryClient = options.queryClient ?? createTestQueryClient();

  return {
    ...render(ui, {
      wrapper: createWrapper({ ...options, queryClient }),
      ...options,
    }),
    queryClient,
  };
}

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };
export { createTestQueryClient };
```

## Vitest Setup

```ts
// vitest.setup.ts
import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, vi } from 'vitest';

// Cleanup after each test
afterEach(() => {
  cleanup();
});

// Mock window.matchMedia
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

// Mock IntersectionObserver
const mockIntersectionObserver = vi.fn();
mockIntersectionObserver.mockReturnValue({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
});
window.IntersectionObserver = mockIntersectionObserver;

// Mock ResizeObserver
window.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

// Mock scrollTo
window.scrollTo = vi.fn();
Element.prototype.scrollIntoView = vi.fn();
```

## Best Practices

1. **Use userEvent over fireEvent** - More realistic user interactions
2. **Query by role first** - Accessible queries are preferred
3. **Use waitFor for async** - Don't use arbitrary delays
4. **Mock at boundaries** - API calls, not internal functions
5. **Test behavior, not implementation** - Focus on user experience
6. **Keep tests isolated** - No shared state between tests
7. **Write descriptive test names** - Clear intent of what's tested
