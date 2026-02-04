# Vitest Testing Framework

## Overview

Fast, Vite-native testing framework with Jest-compatible API.

## Setup

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom
```

```ts
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
});
```

```ts
// src/test/setup.ts
import '@testing-library/jest-dom';
import { afterEach, vi } from 'vitest';
import { cleanup } from '@testing-library/react';

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

// Mock ResizeObserver
global.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));
```

## Test Structure

```tsx
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Component', () => {
  beforeEach(() => {
    // Setup before each test
  });

  afterEach(() => {
    // Cleanup after each test
    vi.clearAllMocks();
  });

  it('should render correctly', () => {
    render(<Component />);
    expect(screen.getByText('Hello')).toBeInTheDocument();
  });

  it.skip('skipped test', () => {
    // Will be skipped
  });

  it.todo('implement this test');

  it.only('focused test', () => {
    // Only this test runs when using .only
  });
});

// Nested describes
describe('Component', () => {
  describe('when logged in', () => {
    it('shows user menu', () => {});
  });

  describe('when logged out', () => {
    it('shows login button', () => {});
  });
});
```

## Mocking

```tsx
import { vi, Mock } from 'vitest';

// Mock function
const mockFn = vi.fn();
mockFn.mockReturnValue('value');
mockFn.mockReturnValueOnce('first');
mockFn.mockResolvedValue('async value');
mockFn.mockRejectedValue(new Error('error'));
mockFn.mockImplementation((x) => x * 2);

// Mock module
vi.mock('@/lib/api', () => ({
  fetchUsers: vi.fn(() => Promise.resolve([{ id: 1, name: 'John' }])),
  createUser: vi.fn(),
}));

// Import mocked module
import { fetchUsers, createUser } from '@/lib/api';

// In test
it('fetches users', async () => {
  (fetchUsers as Mock).mockResolvedValueOnce([{ id: 2, name: 'Jane' }]);

  render(<UserList />);

  await screen.findByText('Jane');
});

// Mock module with factory
vi.mock('@/hooks/useAuth', () => ({
  useAuth: vi.fn(() => ({
    user: { id: '1', name: 'Test User' },
    isAuthenticated: true,
    login: vi.fn(),
    logout: vi.fn(),
  })),
}));

// Spy on existing function
const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
// Later
expect(consoleSpy).toHaveBeenCalled();
consoleSpy.mockRestore();
```

## Mocking Timers

```tsx
import { vi, beforeEach, afterEach } from 'vitest';

describe('Timer tests', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('debounces input', async () => {
    const onSearch = vi.fn();
    render(<SearchInput onSearch={onSearch} debounce={300} />);

    await userEvent.type(screen.getByRole('searchbox'), 'react');

    expect(onSearch).not.toHaveBeenCalled();

    vi.advanceTimersByTime(300);

    expect(onSearch).toHaveBeenCalledWith('react');
  });

  it('shows timer', () => {
    render(<Countdown seconds={10} />);

    expect(screen.getByText('10')).toBeInTheDocument();

    vi.advanceTimersByTime(1000);
    expect(screen.getByText('9')).toBeInTheDocument();

    vi.advanceTimersByTime(9000);
    expect(screen.getByText('0')).toBeInTheDocument();
  });
});
```

## Assertions

```tsx
import { expect } from 'vitest';

// Equality
expect(value).toBe(expected);
expect(value).toEqual(expected);
expect(value).toStrictEqual(expected);

// Truthiness
expect(value).toBeTruthy();
expect(value).toBeFalsy();
expect(value).toBeNull();
expect(value).toBeUndefined();
expect(value).toBeDefined();

// Numbers
expect(value).toBeGreaterThan(3);
expect(value).toBeGreaterThanOrEqual(3);
expect(value).toBeLessThan(5);
expect(value).toBeCloseTo(0.3, 5);

// Strings
expect(string).toMatch(/pattern/);
expect(string).toContain('substring');

// Arrays/Objects
expect(array).toContain(item);
expect(array).toHaveLength(3);
expect(object).toHaveProperty('key');
expect(object).toMatchObject({ key: 'value' });

// Exceptions
expect(() => fn()).toThrow();
expect(() => fn()).toThrow(Error);
expect(() => fn()).toThrow('error message');

// Async
await expect(promise).resolves.toBe(value);
await expect(promise).rejects.toThrow();

// Mock functions
expect(mockFn).toHaveBeenCalled();
expect(mockFn).toHaveBeenCalledTimes(2);
expect(mockFn).toHaveBeenCalledWith(arg1, arg2);
expect(mockFn).toHaveBeenLastCalledWith(arg);

// DOM (jest-dom)
expect(element).toBeInTheDocument();
expect(element).toHaveClass('class-name');
expect(element).toHaveAttribute('disabled');
expect(element).toHaveValue('value');
expect(element).toBeVisible();
expect(element).toBeDisabled();
expect(element).toHaveFocus();
```

## Snapshot Testing

```tsx
import { expect, it } from 'vitest';
import { render } from '@testing-library/react';

it('matches snapshot', () => {
  const { container } = render(<Button>Click me</Button>);
  expect(container).toMatchSnapshot();
});

it('matches inline snapshot', () => {
  const { container } = render(<Badge variant="success">Active</Badge>);
  expect(container.innerHTML).toMatchInlineSnapshot(
    `"<span class="badge badge-success">Active</span>"`
  );
});
```

## Coverage

```bash
# Run with coverage
npx vitest --coverage

# Watch mode with coverage
npx vitest --coverage --watch
```

```ts
// vitest.config.ts
export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/types/',
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
});
```

## Best Practices

1. **Use globals: true** - Cleaner test files without imports
2. **Setup file** - Configure matchers, mocks, cleanup
3. **Mock external deps** - API calls, browser APIs
4. **Use fake timers** - For setTimeout, setInterval
5. **Test behavior** - Not implementation details
6. **Meaningful assertions** - One concept per test
