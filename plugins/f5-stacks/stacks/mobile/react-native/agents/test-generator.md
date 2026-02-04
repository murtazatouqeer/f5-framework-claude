---
name: rn-test-generator
description: Generate tests for React Native components, hooks, and screens
triggers:
  - "rn test"
  - "react native test"
  - "create test"
  - "generate test"
applies_to: react-native
---

# React Native Test Generator

## Purpose

Generate comprehensive tests for:
- Components with React Native Testing Library
- Hooks with renderHook
- Screens with navigation mocking
- Stores with state assertions
- Integration tests with API mocking

## Input Requirements

```yaml
required:
  - target_file: string       # File to test
  - test_type: component | hook | screen | store | integration

optional:
  - coverage_level: basic | comprehensive
  - mock_api: boolean
  - mock_navigation: boolean
  - snapshot: boolean
```

## Generation Templates

### Component Test Template

```typescript
// src/components/ui/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react-native';
import { Button } from '../Button';

describe('Button', () => {
  describe('rendering', () => {
    it('renders with title', () => {
      render(<Button title="Press me" />);
      expect(screen.getByText('Press me')).toBeTruthy();
    });

    it('renders with children', () => {
      render(
        <Button>
          <Text>Custom content</Text>
        </Button>
      );
      expect(screen.getByText('Custom content')).toBeTruthy();
    });

    it('renders loading state', () => {
      render(<Button title="Press me" isLoading />);
      expect(screen.getByTestId('activity-indicator')).toBeTruthy();
      expect(screen.queryByText('Press me')).toBeNull();
    });

    it('renders disabled state', () => {
      render(<Button title="Press me" disabled testID="button" />);
      const button = screen.getByTestId('button');
      expect(button.props.accessibilityState.disabled).toBe(true);
    });
  });

  describe('variants', () => {
    it.each(['primary', 'secondary', 'outline', 'ghost'] as const)(
      'renders %s variant correctly',
      (variant) => {
        render(<Button title="Test" variant={variant} testID="button" />);
        expect(screen.getByTestId('button')).toBeTruthy();
      }
    );
  });

  describe('sizes', () => {
    it.each(['sm', 'md', 'lg'] as const)(
      'renders %s size correctly',
      (size) => {
        render(<Button title="Test" size={size} testID="button" />);
        expect(screen.getByTestId('button')).toBeTruthy();
      }
    );
  });

  describe('interactions', () => {
    it('calls onPress when pressed', () => {
      const onPress = jest.fn();
      render(<Button title="Press me" onPress={onPress} />);

      fireEvent.press(screen.getByText('Press me'));
      expect(onPress).toHaveBeenCalledTimes(1);
    });

    it('does not call onPress when disabled', () => {
      const onPress = jest.fn();
      render(<Button title="Press me" onPress={onPress} disabled />);

      fireEvent.press(screen.getByText('Press me'));
      expect(onPress).not.toHaveBeenCalled();
    });

    it('does not call onPress when loading', () => {
      const onPress = jest.fn();
      render(<Button title="Press me" onPress={onPress} isLoading />);

      const loadingIndicator = screen.getByTestId('activity-indicator');
      fireEvent.press(loadingIndicator);
      expect(onPress).not.toHaveBeenCalled();
    });
  });

  describe('accessibility', () => {
    it('has correct accessibility role', () => {
      render(<Button title="Press me" testID="button" />);
      const button = screen.getByTestId('button');
      expect(button.props.accessibilityRole).toBe('button');
    });

    it('has correct accessibility state when disabled', () => {
      render(<Button title="Press me" disabled testID="button" />);
      const button = screen.getByTestId('button');
      expect(button.props.accessibilityState.disabled).toBe(true);
    });
  });
});
```

### Screen Test Template

```typescript
// src/features/products/screens/__tests__/ProductListScreen.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NavigationContainer } from '@react-navigation/native';

import { ProductListScreen } from '../ProductListScreen';
import { getProducts } from '../../api/productApi';

// Mock API
jest.mock('../../api/productApi');
const mockGetProducts = getProducts as jest.MockedFunction<typeof getProducts>;

// Mock navigation
const mockNavigate = jest.fn();
jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => ({
    navigate: mockNavigate,
    goBack: jest.fn(),
  }),
}));

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

function renderWithProviders(component: React.ReactElement) {
  const queryClient = createTestQueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        {component}
      </NavigationContainer>
    </QueryClientProvider>
  );
}

describe('ProductListScreen', () => {
  const mockProducts = [
    { id: '1', name: 'Product 1', price: 10.99, description: 'Desc 1' },
    { id: '2', name: 'Product 2', price: 20.99, description: 'Desc 2' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('loading state', () => {
    it('shows loading indicator initially', () => {
      mockGetProducts.mockImplementation(() => new Promise(() => {}));

      renderWithProviders(<ProductListScreen />);

      expect(screen.getByTestId('loading-state')).toBeTruthy();
    });
  });

  describe('success state', () => {
    it('renders products list', async () => {
      mockGetProducts.mockResolvedValueOnce({
        items: mockProducts,
        total: 2,
        page: 1,
        totalPages: 1,
      });

      renderWithProviders(<ProductListScreen />);

      await waitFor(() => {
        expect(screen.getByText('Product 1')).toBeTruthy();
        expect(screen.getByText('Product 2')).toBeTruthy();
      });
    });

    it('navigates to detail on item press', async () => {
      mockGetProducts.mockResolvedValueOnce({
        items: mockProducts,
        total: 2,
        page: 1,
        totalPages: 1,
      });

      renderWithProviders(<ProductListScreen />);

      await waitFor(() => {
        expect(screen.getByText('Product 1')).toBeTruthy();
      });

      fireEvent.press(screen.getByText('Product 1'));

      expect(mockNavigate).toHaveBeenCalledWith('ProductDetail', { id: '1' });
    });
  });

  describe('empty state', () => {
    it('shows empty state when no products', async () => {
      mockGetProducts.mockResolvedValueOnce({
        items: [],
        total: 0,
        page: 1,
        totalPages: 0,
      });

      renderWithProviders(<ProductListScreen />);

      await waitFor(() => {
        expect(screen.getByTestId('empty-state')).toBeTruthy();
        expect(screen.getByText('No products found')).toBeTruthy();
      });
    });
  });

  describe('error state', () => {
    it('shows error state when request fails', async () => {
      mockGetProducts.mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders(<ProductListScreen />);

      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeTruthy();
      });
    });

    it('retries on error retry button press', async () => {
      mockGetProducts
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          items: mockProducts,
          total: 2,
          page: 1,
          totalPages: 1,
        });

      renderWithProviders(<ProductListScreen />);

      await waitFor(() => {
        expect(screen.getByTestId('error-state')).toBeTruthy();
      });

      fireEvent.press(screen.getByText('Retry'));

      await waitFor(() => {
        expect(screen.getByText('Product 1')).toBeTruthy();
      });
    });
  });

  describe('search functionality', () => {
    it('filters products by search query', async () => {
      mockGetProducts.mockResolvedValue({
        items: mockProducts,
        total: 2,
        page: 1,
        totalPages: 1,
      });

      renderWithProviders(<ProductListScreen />);

      await waitFor(() => {
        expect(screen.getByText('Product 1')).toBeTruthy();
      });

      const searchInput = screen.getByPlaceholderText('Search...');
      fireEvent.changeText(searchInput, 'Product 1');

      await waitFor(() => {
        expect(mockGetProducts).toHaveBeenCalledWith(
          expect.objectContaining({ search: 'Product 1' })
        );
      });
    });
  });

  describe('pull to refresh', () => {
    it('refreshes on pull down', async () => {
      mockGetProducts.mockResolvedValue({
        items: mockProducts,
        total: 2,
        page: 1,
        totalPages: 1,
      });

      renderWithProviders(<ProductListScreen />);

      await waitFor(() => {
        expect(screen.getByText('Product 1')).toBeTruthy();
      });

      const list = screen.getByTestId('products-list');
      fireEvent(list, 'refresh');

      await waitFor(() => {
        expect(mockGetProducts).toHaveBeenCalledTimes(2);
      });
    });
  });
});
```

### Hook Test Template

```typescript
// src/hooks/__tests__/useDebounce.test.ts
import { renderHook, act } from '@testing-library/react-hooks';
import { useDebounce } from '../useDebounce';

describe('useDebounce', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500));
    expect(result.current).toBe('initial');
  });

  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 500 } }
    );

    rerender({ value: 'updated', delay: 500 });
    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(499);
    });
    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(1);
    });
    expect(result.current).toBe('updated');
  });

  it('cancels pending debounce on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      { initialProps: { value: 'initial', delay: 500 } }
    );

    rerender({ value: 'change1', delay: 500 });
    act(() => {
      jest.advanceTimersByTime(200);
    });

    rerender({ value: 'change2', delay: 500 });
    act(() => {
      jest.advanceTimersByTime(200);
    });

    rerender({ value: 'final', delay: 500 });
    act(() => {
      jest.advanceTimersByTime(500);
    });

    expect(result.current).toBe('final');
  });
});
```

### Store Test Template

```typescript
// src/stores/__tests__/useCartStore.test.ts
import { act, renderHook } from '@testing-library/react-hooks';
import { useCartStore } from '../useCartStore';

describe('useCartStore', () => {
  beforeEach(() => {
    // Reset store before each test
    useCartStore.setState({ items: [] });
  });

  const mockItem = {
    id: '1',
    name: 'Test Product',
    price: 10.99,
    imageUrl: 'https://example.com/image.jpg',
  };

  describe('addItem', () => {
    it('adds new item with quantity 1', () => {
      const { result } = renderHook(() => useCartStore());

      act(() => {
        result.current.addItem(mockItem);
      });

      expect(result.current.items).toHaveLength(1);
      expect(result.current.items[0]).toEqual({ ...mockItem, quantity: 1 });
    });

    it('increments quantity for existing item', () => {
      const { result } = renderHook(() => useCartStore());

      act(() => {
        result.current.addItem(mockItem);
        result.current.addItem(mockItem);
      });

      expect(result.current.items).toHaveLength(1);
      expect(result.current.items[0].quantity).toBe(2);
    });
  });

  describe('removeItem', () => {
    it('removes item from cart', () => {
      const { result } = renderHook(() => useCartStore());

      act(() => {
        result.current.addItem(mockItem);
        result.current.removeItem('1');
      });

      expect(result.current.items).toHaveLength(0);
    });
  });

  describe('updateQuantity', () => {
    it('updates item quantity', () => {
      const { result } = renderHook(() => useCartStore());

      act(() => {
        result.current.addItem(mockItem);
        result.current.updateQuantity('1', 5);
      });

      expect(result.current.items[0].quantity).toBe(5);
    });

    it('removes item when quantity is 0', () => {
      const { result } = renderHook(() => useCartStore());

      act(() => {
        result.current.addItem(mockItem);
        result.current.updateQuantity('1', 0);
      });

      expect(result.current.items).toHaveLength(0);
    });
  });

  describe('clear', () => {
    it('clears all items', () => {
      const { result } = renderHook(() => useCartStore());

      act(() => {
        result.current.addItem(mockItem);
        result.current.addItem({ ...mockItem, id: '2' });
        result.current.clear();
      });

      expect(result.current.items).toHaveLength(0);
    });
  });

  describe('computed values', () => {
    it('calculates total correctly', () => {
      const { result } = renderHook(() => useCartStore());

      act(() => {
        result.current.addItem({ ...mockItem, price: 10 });
        result.current.addItem({ ...mockItem, id: '2', price: 20 });
        result.current.updateQuantity('1', 2);
      });

      const items = result.current.items;
      const total = items.reduce(
        (sum, item) => sum + item.price * item.quantity,
        0
      );
      expect(total).toBe(40); // (10 * 2) + (20 * 1)
    });
  });
});
```

## Test Utilities

```typescript
// src/test/utils.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NavigationContainer } from '@react-navigation/native';
import { render, RenderOptions } from '@testing-library/react-native';

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });
}

interface WrapperProps {
  children: React.ReactNode;
}

export function createWrapper() {
  const queryClient = createTestQueryClient();

  return function Wrapper({ children }: WrapperProps) {
    return (
      <QueryClientProvider client={queryClient}>
        <NavigationContainer>
          {children}
        </NavigationContainer>
      </QueryClientProvider>
    );
  };
}

export function renderWithProviders(
  ui: React.ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  return render(ui, { wrapper: createWrapper(), ...options });
}

export * from '@testing-library/react-native';
```

## Best Practices

1. **Isolation**: Reset mocks and stores before each test
2. **Provider Wrapper**: Always wrap with necessary providers
3. **User Perspective**: Test what users see and interact with
4. **Async Handling**: Use waitFor for async operations
5. **Accessibility**: Test accessibility props and roles
6. **Coverage**: Test happy path, edge cases, and error states
