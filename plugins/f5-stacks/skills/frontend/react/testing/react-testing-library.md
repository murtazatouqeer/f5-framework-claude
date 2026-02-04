# React Testing Library

## Overview

Testing library focused on testing user behavior rather than implementation details.

## Basic Component Testing

```tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi } from 'vitest';
import { Button } from './Button';

describe('Button', () => {
  it('renders with text', () => {
    render(<Button>Click me</Button>);

    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const handleClick = vi.fn();

    render(<Button onClick={handleClick}>Click me</Button>);

    await user.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<Button isLoading>Submit</Button>);

    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByLabelText('Loading')).toBeInTheDocument();
  });

  it('applies variant styles', () => {
    const { rerender } = render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-blue-600');

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-gray-100');
  });
});
```

## Query Priority

```tsx
// Priority order (best to worst):
// 1. Accessible queries (everyone can use)
screen.getByRole('button', { name: 'Submit' });
screen.getByLabelText('Email');
screen.getByPlaceholderText('Enter email');
screen.getByText('Welcome');
screen.getByDisplayValue('john@example.com');

// 2. Semantic queries (HTML5 attributes)
screen.getByAltText('Profile picture');
screen.getByTitle('Close');

// 3. Test IDs (last resort)
screen.getByTestId('custom-element');
```

## Query Variants

```tsx
// getBy - throws if not found (synchronous)
screen.getByRole('button'); // Must exist

// queryBy - returns null if not found (synchronous)
screen.queryByRole('button'); // Might not exist
expect(screen.queryByRole('alert')).not.toBeInTheDocument();

// findBy - returns promise, waits for element (async)
await screen.findByRole('alert'); // Will appear
await screen.findByText('Success', {}, { timeout: 3000 });

// *AllBy - returns array of matching elements
screen.getAllByRole('listitem');
screen.queryAllByRole('listitem');
await screen.findAllByRole('listitem');
```

## User Events

```tsx
import userEvent from '@testing-library/user-event';

describe('User interactions', () => {
  it('types in input', async () => {
    const user = userEvent.setup();

    render(<LoginForm />);

    await user.type(screen.getByLabelText('Email'), 'test@example.com');
    await user.type(screen.getByLabelText('Password'), 'password123');

    expect(screen.getByLabelText('Email')).toHaveValue('test@example.com');
  });

  it('selects option', async () => {
    const user = userEvent.setup();

    render(
      <select aria-label="Country">
        <option value="us">United States</option>
        <option value="uk">United Kingdom</option>
      </select>
    );

    await user.selectOptions(screen.getByLabelText('Country'), 'uk');

    expect(screen.getByLabelText('Country')).toHaveValue('uk');
  });

  it('handles checkbox', async () => {
    const user = userEvent.setup();

    render(<input type="checkbox" aria-label="Accept terms" />);

    const checkbox = screen.getByLabelText('Accept terms');

    await user.click(checkbox);
    expect(checkbox).toBeChecked();

    await user.click(checkbox);
    expect(checkbox).not.toBeChecked();
  });

  it('handles keyboard', async () => {
    const user = userEvent.setup();

    render(<SearchInput />);

    const input = screen.getByRole('searchbox');
    await user.type(input, 'react');
    await user.keyboard('{Enter}');

    expect(onSearch).toHaveBeenCalledWith('react');
  });
});
```

## Testing Async Behavior

```tsx
import { render, screen, waitFor, waitForElementToBeRemoved } from '@testing-library/react';

describe('Async behavior', () => {
  it('shows data after loading', async () => {
    render(<UserProfile userId="123" />);

    // Wait for loading to finish
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    // Wait for content
    await screen.findByText('John Doe');

    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  it('waits for element to be removed', async () => {
    render(<Modal onClose={handleClose} />);

    await userEvent.click(screen.getByRole('button', { name: 'Close' }));

    await waitForElementToBeRemoved(() => screen.queryByRole('dialog'));
  });

  it('waits for multiple conditions', async () => {
    render(<Form />);

    await userEvent.click(screen.getByRole('button', { name: 'Submit' }));

    await waitFor(() => {
      expect(screen.getByText('Success')).toBeInTheDocument();
      expect(handleSubmit).toHaveBeenCalled();
    });
  });
});
```

## Testing Forms

```tsx
describe('ContactForm', () => {
  it('submits form with valid data', async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<ContactForm onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText('Name'), 'John Doe');
    await user.type(screen.getByLabelText('Email'), 'john@example.com');
    await user.type(screen.getByLabelText('Message'), 'Hello world');
    await user.click(screen.getByRole('button', { name: 'Send' }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'john@example.com',
        message: 'Hello world',
      });
    });
  });

  it('shows validation errors', async () => {
    const user = userEvent.setup();

    render(<ContactForm onSubmit={vi.fn()} />);

    await user.click(screen.getByRole('button', { name: 'Send' }));

    expect(await screen.findByText('Name is required')).toBeInTheDocument();
    expect(await screen.findByText('Email is required')).toBeInTheDocument();
  });
});
```

## Custom Render with Providers

```tsx
// test-utils.tsx
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider } from './contexts/ThemeContext';

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider>
          {children}
        </ThemeProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

## Testing Hooks

```tsx
import { renderHook, act, waitFor } from '@testing-library/react';
import { useCounter } from './useCounter';

describe('useCounter', () => {
  it('increments counter', () => {
    const { result } = renderHook(() => useCounter());

    act(() => {
      result.current.increment();
    });

    expect(result.current.count).toBe(1);
  });

  it('handles async operations', async () => {
    const { result } = renderHook(() => useAsync(fetchData));

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeDefined();
  });
});
```

## Best Practices

1. **Test behavior, not implementation** - Focus on what users see and do
2. **Use accessible queries** - getByRole, getByLabelText first
3. **Avoid test IDs** - Use only as last resort
4. **Use userEvent over fireEvent** - More realistic interactions
5. **Wait properly** - Use findBy, waitFor for async
6. **Keep tests isolated** - Each test independent
