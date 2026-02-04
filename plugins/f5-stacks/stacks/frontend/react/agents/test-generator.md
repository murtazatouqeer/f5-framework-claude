# React Test Generator Agent

## Purpose
Generate comprehensive tests for React components, hooks, and pages using React Testing Library and Vitest.

## Triggers
- "create test"
- "generate test"
- "react test"
- "unit test"
- "component test"

## Input Requirements

```yaml
required:
  - target: string           # Path to component/hook to test
  - type: string             # 'component' | 'hook' | 'page' | 'integration'

optional:
  - coverage_target: number  # Coverage percentage goal
  - include_a11y: boolean    # Include accessibility tests
  - include_snapshot: boolean # Include snapshot tests
  - mock_apis: array         # APIs to mock with MSW
```

## Generation Process

### 1. Analyze Target
- Parse component/hook structure
- Identify props and state
- Detect side effects and API calls
- List user interactions

### 2. Generate Test Structure

#### Component Test Template
```tsx
// src/components/{ComponentName}/{ComponentName}.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { {ComponentName} } from './{ComponentName}';

describe('{ComponentName}', () => {
  const user = userEvent.setup();

  // Default props
  const defaultProps = {
    onAction: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('rendering', () => {
    it('renders with default props', () => {
      render(<{ComponentName} {...defaultProps} />);

      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('renders children correctly', () => {
      render(
        <{ComponentName} {...defaultProps}>
          <span>Child content</span>
        </{ComponentName}>
      );

      expect(screen.getByText('Child content')).toBeInTheDocument();
    });

    it('renders with different variants', () => {
      const { rerender } = render(
        <{ComponentName} {...defaultProps} variant="default" />
      );
      expect(screen.getByRole('button')).toHaveClass('default');

      rerender(<{ComponentName} {...defaultProps} variant="outline" />);
      expect(screen.getByRole('button')).toHaveClass('outline');
    });

    it('renders loading state', () => {
      render(<{ComponentName} {...defaultProps} isLoading />);

      expect(screen.getByLabelText('Loading')).toBeInTheDocument();
    });

    it('renders disabled state', () => {
      render(<{ComponentName} {...defaultProps} disabled />);

      expect(screen.getByRole('button')).toBeDisabled();
    });
  });

  describe('interactions', () => {
    it('calls onClick when clicked', async () => {
      render(<{ComponentName} {...defaultProps}>Click me</{ComponentName}>);

      await user.click(screen.getByRole('button'));

      expect(defaultProps.onAction).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', async () => {
      render(
        <{ComponentName} {...defaultProps} disabled>
          Click me
        </{ComponentName}>
      );

      await user.click(screen.getByRole('button'));

      expect(defaultProps.onAction).not.toHaveBeenCalled();
    });

    it('handles keyboard navigation', async () => {
      render(<{ComponentName} {...defaultProps}>Press Enter</{ComponentName}>);

      const button = screen.getByRole('button');
      button.focus();

      await user.keyboard('{Enter}');

      expect(defaultProps.onAction).toHaveBeenCalledTimes(1);
    });
  });

  describe('accessibility', () => {
    it('has correct aria attributes', () => {
      render(<{ComponentName} {...defaultProps} disabled />);

      expect(screen.getByRole('button')).toHaveAttribute('aria-disabled', 'true');
    });

    it('is focusable', () => {
      render(<{ComponentName} {...defaultProps} />);

      const button = screen.getByRole('button');
      button.focus();

      expect(button).toHaveFocus();
    });

    it('has accessible name', () => {
      render(<{ComponentName} {...defaultProps} aria-label="Submit form" />);

      expect(screen.getByRole('button', { name: 'Submit form' })).toBeInTheDocument();
    });
  });
});
```

#### Hook Test Template
```tsx
// src/hooks/{hookName}.test.ts
import { renderHook, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { {hookName} } from './{hookName}';

describe('{hookName}', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('returns initial state', () => {
    const { result } = renderHook(() => {hookName}());

    expect(result.current.value).toBe(initialValue);
    expect(result.current.isLoading).toBe(false);
  });

  it('updates state correctly', () => {
    const { result } = renderHook(() => {hookName}());

    act(() => {
      result.current.setValue('new value');
    });

    expect(result.current.value).toBe('new value');
  });

  it('handles async operations', async () => {
    const { result } = renderHook(() => {hookName}());

    act(() => {
      result.current.fetchData();
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeDefined();
  });

  it('cleans up on unmount', () => {
    const cleanup = vi.fn();
    const { unmount } = renderHook(() => {hookName}({ onCleanup: cleanup }));

    unmount();

    expect(cleanup).toHaveBeenCalled();
  });

  it('handles errors', async () => {
    const { result } = renderHook(() => {hookName}({ shouldFail: true }));

    act(() => {
      result.current.fetchData();
    });

    await waitFor(() => {
      expect(result.current.error).toBeDefined();
    });
  });
});
```

#### Form Test Template
```tsx
// src/features/{feature}/components/{Entity}Form.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { {Entity}Form } from './{Entity}Form';

describe('{Entity}Form', () => {
  const user = userEvent.setup();

  const defaultProps = {
    onSubmit: vi.fn(),
    onCancel: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all form fields', () => {
    render(<{Entity}Form {...defaultProps} />);

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create/i })).toBeInTheDocument();
  });

  it('shows validation errors for empty required fields', async () => {
    render(<{Entity}Form {...defaultProps} />);

    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText(/name must be at least/i)).toBeInTheDocument();
    });

    expect(defaultProps.onSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    defaultProps.onSubmit.mockResolvedValueOnce(undefined);

    render(<{Entity}Form {...defaultProps} />);

    await user.type(screen.getByLabelText(/name/i), 'Test Name');
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(defaultProps.onSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Test Name',
          email: 'test@example.com',
        })
      );
    });
  });

  it('shows Update button when defaultValues provided', () => {
    render(
      <{Entity}Form
        {...defaultProps}
        defaultValues={{ name: 'Existing' }}
        mode="edit"
      />
    );

    expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument();
  });

  it('disables submit button while submitting', () => {
    render(<{Entity}Form {...defaultProps} isSubmitting />);

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled();
  });
});
```

#### Integration Test with MSW
```tsx
// src/features/{feature}/__tests__/{Feature}.integration.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, beforeAll, afterAll, afterEach } from 'vitest';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { {Feature}Page } from '../pages/{Feature}Page';

const server = setupServer(
  http.get('/api/{entity}s', () => {
    return HttpResponse.json({
      data: [
        { id: '1', name: 'Item 1' },
        { id: '2', name: 'Item 2' },
      ],
    });
  }),

  http.post('/api/{entity}s', async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({ id: '3', ...body }, { status: 201 });
  }),
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {ui}
      </BrowserRouter>
    </QueryClientProvider>
  );
}

describe('{Feature} Integration', () => {
  const user = userEvent.setup();

  it('loads and displays {entity}s', async () => {
    renderWithProviders(<{Feature}Page />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Item 1')).toBeInTheDocument();
      expect(screen.getByText('Item 2')).toBeInTheDocument();
    });
  });

  it('handles API errors gracefully', async () => {
    server.use(
      http.get('/api/{entity}s', () => {
        return HttpResponse.json({ message: 'Server error' }, { status: 500 });
      })
    );

    renderWithProviders(<{Feature}Page />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

## Output Files

1. **Component Test**: Unit tests for component
2. **Hook Test**: Tests for custom hooks
3. **Form Test**: Form validation and submission tests
4. **Integration Test**: End-to-end feature tests with MSW

## Quality Checks

- [ ] Tests cover happy path
- [ ] Tests cover error states
- [ ] Tests cover edge cases
- [ ] Accessibility tests included
- [ ] No implementation details tested
- [ ] Tests are maintainable
- [ ] Proper use of queries (getBy, queryBy, findBy)
