---
name: rn-test
description: Test templates for React Native components, hooks, and screens
applies_to: react-native
variables:
  - name: componentName
    description: Name of the component/hook to test
  - name: testType
    description: Type of test (component, hook, screen, store)
---

# React Native Test Templates

## Component Test

```typescript
// src/components/__tests__/{{componentName}}.test.tsx
import { render, screen, fireEvent } from '@testing-library/react-native';
import { {{componentName}} } from '../{{componentName}}';

describe('{{componentName}}', () => {
  const defaultProps = {
    // Add default props
  };

  it('renders correctly', () => {
    render(<{{componentName}} {...defaultProps} />);
    // Add assertions
  });

  it('handles press events', () => {
    const onPress = jest.fn();
    render(<{{componentName}} {...defaultProps} onPress={onPress} />);

    fireEvent.press(screen.getByRole('button'));

    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('shows loading state', () => {
    render(<{{componentName}} {...defaultProps} loading />);

    expect(screen.getByTestId('loading-indicator')).toBeOnTheScreen();
  });

  it('applies variant styles', () => {
    render(<{{componentName}} {...defaultProps} variant="primary" />);

    const element = screen.getByTestId('{{kebabCase componentName}}');
    expect(element).toHaveStyle({ backgroundColor: '#007AFF' });
  });

  it('is disabled when disabled prop is true', () => {
    render(<{{componentName}} {...defaultProps} disabled />);

    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

## Hook Test

```typescript
// src/hooks/__tests__/use{{hookName}}.test.ts
import { renderHook, act, waitFor } from '@testing-library/react-hooks';
import { use{{hookName}} } from '../use{{hookName}}';

describe('use{{hookName}}', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns initial state', () => {
    const { result } = renderHook(() => use{{hookName}}());

    expect(result.current.data).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('updates state correctly', () => {
    const { result } = renderHook(() => use{{hookName}}());

    act(() => {
      result.current.setValue('new value');
    });

    expect(result.current.value).toBe('new value');
  });

  it('handles async operations', async () => {
    const { result } = renderHook(() => use{{hookName}}());

    act(() => {
      result.current.fetchData();
    });

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toBeDefined();
  });

  it('handles errors', async () => {
    // Mock API to throw error
    jest.spyOn(api, 'get').mockRejectedValueOnce(new Error('Network error'));

    const { result } = renderHook(() => use{{hookName}}());

    act(() => {
      result.current.fetchData();
    });

    await waitFor(() => {
      expect(result.current.error).toBe('Network error');
    });
  });
});
```

## Screen Test

```typescript
// src/features/{{feature}}/screens/__tests__/{{screenName}}Screen.test.tsx
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import { {{screenName}}Screen } from '../{{screenName}}Screen';
import { api } from '@/lib/api';

jest.mock('@/lib/api');
const mockedApi = api as jest.Mocked<typeof api>;

const mockNavigation = {
  navigate: jest.fn(),
  goBack: jest.fn(),
};

jest.mock('@react-navigation/native', () => ({
  ...jest.requireActual('@react-navigation/native'),
  useNavigation: () => mockNavigation,
  useRoute: () => ({ params: { id: '123' } }),
}));

describe('{{screenName}}Screen', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows loading state initially', () => {
    mockedApi.get.mockImplementation(() => new Promise(() => {}));

    render(<{{screenName}}Screen />);

    expect(screen.getByTestId('loading-spinner')).toBeOnTheScreen();
  });

  it('renders data after loading', async () => {
    const mockData = {
      id: '123',
      title: 'Test Item',
      description: 'Test description',
    };
    mockedApi.get.mockResolvedValueOnce({ data: mockData });

    render(<{{screenName}}Screen />);

    await waitFor(() => {
      expect(screen.getByText('Test Item')).toBeOnTheScreen();
    });
  });

  it('shows error state on failure', async () => {
    mockedApi.get.mockRejectedValueOnce(new Error('Network error'));

    render(<{{screenName}}Screen />);

    await waitFor(() => {
      expect(screen.getByText(/failed to load/i)).toBeOnTheScreen();
    });
  });

  it('retries on error', async () => {
    mockedApi.get
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ data: { id: '123', title: 'Test' } });

    render(<{{screenName}}Screen />);

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeOnTheScreen();
    });

    fireEvent.press(screen.getByText('Retry'));

    await waitFor(() => {
      expect(screen.getByText('Test')).toBeOnTheScreen();
    });
  });

  it('navigates on item press', async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: { items: [{ id: '1', title: 'Item 1' }] },
    });

    render(<{{screenName}}Screen />);

    await waitFor(() => {
      expect(screen.getByText('Item 1')).toBeOnTheScreen();
    });

    fireEvent.press(screen.getByText('Item 1'));

    expect(mockNavigation.navigate).toHaveBeenCalledWith('Detail', { id: '1' });
  });
});
```

## Store Test

```typescript
// src/stores/__tests__/use{{storeName}}Store.test.ts
import { act } from '@testing-library/react-hooks';
import { use{{storeName}}Store } from '../use{{storeName}}Store';

describe('use{{storeName}}Store', () => {
  beforeEach(() => {
    // Reset store state
    use{{storeName}}Store.setState({
      items: [],
      selectedId: null,
      isLoading: false,
    });
  });

  describe('addItem', () => {
    it('adds item to store', () => {
      const item = { id: '1', name: 'Test Item' };

      act(() => {
        use{{storeName}}Store.getState().addItem(item);
      });

      expect(use{{storeName}}Store.getState().items).toHaveLength(1);
      expect(use{{storeName}}Store.getState().items[0]).toEqual(item);
    });
  });

  describe('removeItem', () => {
    it('removes item from store', () => {
      use{{storeName}}Store.setState({
        items: [{ id: '1', name: 'Test' }],
      });

      act(() => {
        use{{storeName}}Store.getState().removeItem('1');
      });

      expect(use{{storeName}}Store.getState().items).toHaveLength(0);
    });
  });

  describe('selectItem', () => {
    it('sets selected item id', () => {
      act(() => {
        use{{storeName}}Store.getState().selectItem('123');
      });

      expect(use{{storeName}}Store.getState().selectedId).toBe('123');
    });
  });

  describe('reset', () => {
    it('resets store to initial state', () => {
      use{{storeName}}Store.setState({
        items: [{ id: '1', name: 'Test' }],
        selectedId: '1',
        isLoading: true,
      });

      act(() => {
        use{{storeName}}Store.getState().reset();
      });

      const state = use{{storeName}}Store.getState();
      expect(state.items).toHaveLength(0);
      expect(state.selectedId).toBeNull();
      expect(state.isLoading).toBe(false);
    });
  });
});
```

## Form Test

```typescript
// src/features/{{feature}}/screens/__tests__/{{formName}}Form.test.tsx
import { render, screen, fireEvent, waitFor } from '@/test-utils';
import { {{formName}}Form } from '../{{formName}}Form';

describe('{{formName}}Form', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders all form fields', () => {
    render(<{{formName}}Form onSubmit={mockOnSubmit} />);

    expect(screen.getByPlaceholderText('Name')).toBeOnTheScreen();
    expect(screen.getByPlaceholderText('Email')).toBeOnTheScreen();
    expect(screen.getByText('Submit')).toBeOnTheScreen();
  });

  it('shows validation errors for empty fields', async () => {
    render(<{{formName}}Form onSubmit={mockOnSubmit} />);

    fireEvent.press(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Name is required')).toBeOnTheScreen();
      expect(screen.getByText('Email is required')).toBeOnTheScreen();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('shows validation error for invalid email', async () => {
    render(<{{formName}}Form onSubmit={mockOnSubmit} />);

    fireEvent.changeText(screen.getByPlaceholderText('Name'), 'John');
    fireEvent.changeText(screen.getByPlaceholderText('Email'), 'invalid');
    fireEvent.press(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Invalid email address')).toBeOnTheScreen();
    });
  });

  it('submits form with valid data', async () => {
    render(<{{formName}}Form onSubmit={mockOnSubmit} />);

    fireEvent.changeText(screen.getByPlaceholderText('Name'), 'John Doe');
    fireEvent.changeText(
      screen.getByPlaceholderText('Email'),
      'john@example.com'
    );
    fireEvent.press(screen.getByText('Submit'));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        name: 'John Doe',
        email: 'john@example.com',
      });
    });
  });

  it('disables submit button during submission', async () => {
    mockOnSubmit.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    render(<{{formName}}Form onSubmit={mockOnSubmit} />);

    fireEvent.changeText(screen.getByPlaceholderText('Name'), 'John');
    fireEvent.changeText(
      screen.getByPlaceholderText('Email'),
      'john@example.com'
    );
    fireEvent.press(screen.getByText('Submit'));

    await waitFor(() => {
      expect(screen.getByText('Submitting...')).toBeOnTheScreen();
    });
  });
});
```

## Test Utils

```typescript
// src/test-utils/index.tsx
import { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react-native';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { NavigationContainer } from '@react-navigation/native';
import { SafeAreaProvider } from 'react-native-safe-area-context';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

const AllProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createTestQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <NavigationContainer>
          {children}
        </NavigationContainer>
      </SafeAreaProvider>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

export * from '@testing-library/react-native';
export { customRender as render };
```

## Usage

1. Replace placeholders with actual names
2. Add test-specific mocks as needed
3. Adjust assertions for your component's behavior
4. Run tests with `npm test`
