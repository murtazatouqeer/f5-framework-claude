---
name: rn-testing-library
description: React Native Testing Library for component testing
applies_to: react-native
---

# React Native Testing Library

## Installation

```bash
npm install --save-dev @testing-library/react-native @testing-library/jest-native
```

## Setup

```typescript
// jest.setup.js
import '@testing-library/jest-native/extend-expect';
```

## Basic Component Testing

```typescript
// src/components/__tests__/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react-native';
import { Button } from '../Button';

describe('Button', () => {
  it('renders correctly with title', () => {
    render(<Button title="Press Me" onPress={() => {}} />);

    expect(screen.getByText('Press Me')).toBeOnTheScreen();
  });

  it('calls onPress when pressed', () => {
    const onPress = jest.fn();
    render(<Button title="Press Me" onPress={onPress} />);

    fireEvent.press(screen.getByText('Press Me'));

    expect(onPress).toHaveBeenCalledTimes(1);
  });

  it('is disabled when loading', () => {
    render(<Button title="Press Me" onPress={() => {}} loading />);

    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('shows loading indicator when loading', () => {
    render(<Button title="Press Me" onPress={() => {}} loading />);

    expect(screen.getByTestId('loading-indicator')).toBeOnTheScreen();
  });

  it('applies variant styles', () => {
    render(<Button title="Primary" onPress={() => {}} variant="primary" />);

    const button = screen.getByRole('button');
    expect(button).toHaveStyle({ backgroundColor: '#007AFF' });
  });
});
```

## Testing Text Input

```typescript
// src/components/__tests__/SearchInput.test.tsx
import { render, screen, fireEvent } from '@testing-library/react-native';
import { SearchInput } from '../SearchInput';

describe('SearchInput', () => {
  it('renders with placeholder', () => {
    render(<SearchInput placeholder="Search products..." onSearch={() => {}} />);

    expect(screen.getByPlaceholderText('Search products...')).toBeOnTheScreen();
  });

  it('calls onChangeText when typing', () => {
    const onSearch = jest.fn();
    render(<SearchInput placeholder="Search..." onSearch={onSearch} />);

    fireEvent.changeText(screen.getByPlaceholderText('Search...'), 'phone');

    expect(onSearch).toHaveBeenCalledWith('phone');
  });

  it('submits on pressing search button', () => {
    const onSubmit = jest.fn();
    render(<SearchInput placeholder="Search..." onSubmit={onSubmit} />);

    fireEvent.changeText(screen.getByPlaceholderText('Search...'), 'laptop');
    fireEvent(screen.getByPlaceholderText('Search...'), 'submitEditing');

    expect(onSubmit).toHaveBeenCalledWith('laptop');
  });

  it('clears input when clear button pressed', () => {
    render(
      <SearchInput placeholder="Search..." onSearch={() => {}} showClear />
    );

    const input = screen.getByPlaceholderText('Search...');
    fireEvent.changeText(input, 'test');

    fireEvent.press(screen.getByTestId('clear-button'));

    expect(input.props.value).toBe('');
  });
});
```

## Testing Lists

```typescript
// src/features/products/__tests__/ProductList.test.tsx
import { render, screen, fireEvent, within } from '@testing-library/react-native';
import { ProductList } from '../ProductList';

const mockProducts = [
  { id: '1', name: 'Product 1', price: 10 },
  { id: '2', name: 'Product 2', price: 20 },
  { id: '3', name: 'Product 3', price: 30 },
];

describe('ProductList', () => {
  it('renders all products', () => {
    render(<ProductList products={mockProducts} />);

    expect(screen.getByText('Product 1')).toBeOnTheScreen();
    expect(screen.getByText('Product 2')).toBeOnTheScreen();
    expect(screen.getByText('Product 3')).toBeOnTheScreen();
  });

  it('shows empty state when no products', () => {
    render(<ProductList products={[]} />);

    expect(screen.getByText('No products found')).toBeOnTheScreen();
  });

  it('calls onProductPress when product is tapped', () => {
    const onProductPress = jest.fn();
    render(
      <ProductList products={mockProducts} onProductPress={onProductPress} />
    );

    fireEvent.press(screen.getByText('Product 1'));

    expect(onProductPress).toHaveBeenCalledWith(mockProducts[0]);
  });

  it('shows loading indicator when loading', () => {
    render(<ProductList products={[]} loading />);

    expect(screen.getByTestId('loading-spinner')).toBeOnTheScreen();
  });

  it('calls onRefresh when pulled down', () => {
    const onRefresh = jest.fn();
    render(
      <ProductList
        products={mockProducts}
        onRefresh={onRefresh}
        refreshing={false}
      />
    );

    const list = screen.getByTestId('product-list');
    fireEvent(list, 'refresh');

    expect(onRefresh).toHaveBeenCalled();
  });
});
```

## Testing Forms

```typescript
// src/features/auth/__tests__/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react-native';
import { LoginForm } from '../LoginForm';

describe('LoginForm', () => {
  const mockOnSubmit = jest.fn();

  beforeEach(() => {
    mockOnSubmit.mockClear();
  });

  it('renders email and password inputs', () => {
    render(<LoginForm onSubmit={mockOnSubmit} />);

    expect(screen.getByPlaceholderText('Email')).toBeOnTheScreen();
    expect(screen.getByPlaceholderText('Password')).toBeOnTheScreen();
  });

  it('shows validation errors for empty fields', async () => {
    render(<LoginForm onSubmit={mockOnSubmit} />);

    fireEvent.press(screen.getByText('Sign In'));

    await waitFor(() => {
      expect(screen.getByText('Email is required')).toBeOnTheScreen();
      expect(screen.getByText('Password is required')).toBeOnTheScreen();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('shows error for invalid email', async () => {
    render(<LoginForm onSubmit={mockOnSubmit} />);

    fireEvent.changeText(screen.getByPlaceholderText('Email'), 'invalid');
    fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
    fireEvent.press(screen.getByText('Sign In'));

    await waitFor(() => {
      expect(screen.getByText('Invalid email address')).toBeOnTheScreen();
    });
  });

  it('submits form with valid data', async () => {
    render(<LoginForm onSubmit={mockOnSubmit} />);

    fireEvent.changeText(
      screen.getByPlaceholderText('Email'),
      'test@example.com'
    );
    fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
    fireEvent.press(screen.getByText('Sign In'));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123',
      });
    });
  });

  it('disables button during submission', async () => {
    mockOnSubmit.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    render(<LoginForm onSubmit={mockOnSubmit} />);

    fireEvent.changeText(
      screen.getByPlaceholderText('Email'),
      'test@example.com'
    );
    fireEvent.changeText(screen.getByPlaceholderText('Password'), 'password123');
    fireEvent.press(screen.getByText('Sign In'));

    await waitFor(() => {
      expect(screen.getByText('Signing in...')).toBeOnTheScreen();
    });
  });
});
```

## Testing with React Query

```typescript
// src/features/products/__tests__/ProductScreen.test.tsx
import { render, screen, waitFor } from '@/test-utils';
import { ProductScreen } from '../ProductScreen';
import { api } from '@/lib/api';

jest.mock('@/lib/api');
const mockedApi = api as jest.Mocked<typeof api>;

const mockProducts = [
  { id: '1', name: 'Product 1', price: 10 },
  { id: '2', name: 'Product 2', price: 20 },
];

describe('ProductScreen', () => {
  it('shows loading state initially', () => {
    mockedApi.get.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<ProductScreen />);

    expect(screen.getByTestId('loading-spinner')).toBeOnTheScreen();
  });

  it('renders products after loading', async () => {
    mockedApi.get.mockResolvedValueOnce({ data: mockProducts });

    render(<ProductScreen />);

    await waitFor(() => {
      expect(screen.getByText('Product 1')).toBeOnTheScreen();
      expect(screen.getByText('Product 2')).toBeOnTheScreen();
    });
  });

  it('shows error state on failure', async () => {
    mockedApi.get.mockRejectedValueOnce(new Error('Network error'));

    render(<ProductScreen />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load products')).toBeOnTheScreen();
    });
  });

  it('shows retry button on error', async () => {
    mockedApi.get.mockRejectedValueOnce(new Error('Network error'));

    render(<ProductScreen />);

    await waitFor(() => {
      expect(screen.getByText('Retry')).toBeOnTheScreen();
    });
  });
});
```

## Testing Navigation

```typescript
// src/features/products/__tests__/ProductCard.test.tsx
import { render, screen, fireEvent } from '@/test-utils';
import { ProductCard } from '../ProductCard';
import { useRouter } from 'expo-router';

jest.mock('expo-router');
const mockRouter = useRouter as jest.MockedFunction<typeof useRouter>;

describe('ProductCard', () => {
  const mockPush = jest.fn();

  beforeEach(() => {
    mockRouter.mockReturnValue({
      push: mockPush,
      replace: jest.fn(),
      back: jest.fn(),
    } as any);
  });

  it('navigates to product detail on press', () => {
    const product = { id: '123', name: 'Test Product', price: 99 };

    render(<ProductCard product={product} />);

    fireEvent.press(screen.getByText('Test Product'));

    expect(mockPush).toHaveBeenCalledWith('/product/123');
  });
});
```

## Testing Modals

```typescript
// src/components/__tests__/ConfirmModal.test.tsx
import { render, screen, fireEvent } from '@testing-library/react-native';
import { ConfirmModal } from '../ConfirmModal';

describe('ConfirmModal', () => {
  const defaultProps = {
    visible: true,
    title: 'Confirm Action',
    message: 'Are you sure?',
    onConfirm: jest.fn(),
    onCancel: jest.fn(),
  };

  it('renders when visible', () => {
    render(<ConfirmModal {...defaultProps} />);

    expect(screen.getByText('Confirm Action')).toBeOnTheScreen();
    expect(screen.getByText('Are you sure?')).toBeOnTheScreen();
  });

  it('does not render when not visible', () => {
    render(<ConfirmModal {...defaultProps} visible={false} />);

    expect(screen.queryByText('Confirm Action')).not.toBeOnTheScreen();
  });

  it('calls onConfirm when confirm button pressed', () => {
    render(<ConfirmModal {...defaultProps} />);

    fireEvent.press(screen.getByText('Confirm'));

    expect(defaultProps.onConfirm).toHaveBeenCalled();
  });

  it('calls onCancel when cancel button pressed', () => {
    render(<ConfirmModal {...defaultProps} />);

    fireEvent.press(screen.getByText('Cancel'));

    expect(defaultProps.onCancel).toHaveBeenCalled();
  });
});
```

## Query Methods

```typescript
// Finding elements
screen.getByText('Hello');           // Throws if not found
screen.queryByText('Hello');         // Returns null if not found
screen.findByText('Hello');          // Async, waits for element

// By role
screen.getByRole('button');
screen.getByRole('button', { name: 'Submit' });

// By placeholder
screen.getByPlaceholderText('Enter email');

// By test ID
screen.getByTestId('submit-button');

// By display value
screen.getByDisplayValue('john@example.com');

// Multiple elements
screen.getAllByText('Item');
screen.queryAllByText('Item');
screen.findAllByText('Item');
```

## Best Practices

1. **Query Priority**: Prefer accessible queries (getByRole, getByText) over testID
2. **Async Handling**: Use findBy* or waitFor for async content
3. **User Behavior**: Test from user perspective, not implementation
4. **Test IDs**: Use sparingly, only when necessary
5. **Assertions**: Use jest-native matchers (toBeOnTheScreen, toHaveStyle)
6. **Cleanup**: Testing Library handles cleanup automatically
7. **Providers**: Wrap with necessary providers in test utils
8. **Mock Navigation**: Mock expo-router or react-navigation
