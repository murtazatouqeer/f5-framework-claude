# React Context API

## Overview

Built-in React API for sharing state across components without prop drilling.

## Basic Context Pattern

```tsx
import { createContext, useContext, useState, ReactNode } from 'react';

// 1. Define types
interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

// 2. Create context with default value
const AuthContext = createContext<AuthContextType | null>(null);

// 3. Create provider component
interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);

  const login = async (email: string, password: string) => {
    const response = await api.login(email, password);
    setUser(response.user);
  };

  const logout = () => {
    setUser(null);
    api.logout();
  };

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// 4. Create custom hook with error handling
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

// 5. Usage in components
function LoginButton() {
  const { isAuthenticated, login, logout } = useAuth();

  if (isAuthenticated) {
    return <button onClick={logout}>Logout</button>;
  }

  return <button onClick={() => login('email', 'pass')}>Login</button>;
}
```

## Context with Reducer

For complex state logic, combine Context with useReducer.

```tsx
import { createContext, useContext, useReducer, ReactNode, Dispatch } from 'react';

// State and Action types
interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

interface CartState {
  items: CartItem[];
  total: number;
}

type CartAction =
  | { type: 'ADD_ITEM'; payload: Omit<CartItem, 'quantity'> }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'UPDATE_QUANTITY'; payload: { id: string; quantity: number } }
  | { type: 'CLEAR_CART' };

// Reducer
function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'ADD_ITEM': {
      const existingIndex = state.items.findIndex(i => i.id === action.payload.id);
      let newItems: CartItem[];

      if (existingIndex >= 0) {
        newItems = state.items.map((item, index) =>
          index === existingIndex
            ? { ...item, quantity: item.quantity + 1 }
            : item
        );
      } else {
        newItems = [...state.items, { ...action.payload, quantity: 1 }];
      }

      return {
        items: newItems,
        total: newItems.reduce((sum, item) => sum + item.price * item.quantity, 0),
      };
    }

    case 'REMOVE_ITEM': {
      const newItems = state.items.filter(item => item.id !== action.payload);
      return {
        items: newItems,
        total: newItems.reduce((sum, item) => sum + item.price * item.quantity, 0),
      };
    }

    case 'UPDATE_QUANTITY': {
      const newItems = state.items.map(item =>
        item.id === action.payload.id
          ? { ...item, quantity: action.payload.quantity }
          : item
      );
      return {
        items: newItems,
        total: newItems.reduce((sum, item) => sum + item.price * item.quantity, 0),
      };
    }

    case 'CLEAR_CART':
      return { items: [], total: 0 };

    default:
      return state;
  }
}

// Context
interface CartContextType {
  state: CartState;
  dispatch: Dispatch<CartAction>;
  addItem: (item: Omit<CartItem, 'quantity'>) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clearCart: () => void;
}

const CartContext = createContext<CartContextType | null>(null);

// Provider
export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [], total: 0 });

  const addItem = (item: Omit<CartItem, 'quantity'>) => {
    dispatch({ type: 'ADD_ITEM', payload: item });
  };

  const removeItem = (id: string) => {
    dispatch({ type: 'REMOVE_ITEM', payload: id });
  };

  const updateQuantity = (id: string, quantity: number) => {
    dispatch({ type: 'UPDATE_QUANTITY', payload: { id, quantity } });
  };

  const clearCart = () => {
    dispatch({ type: 'CLEAR_CART' });
  };

  return (
    <CartContext.Provider
      value={{ state, dispatch, addItem, removeItem, updateQuantity, clearCart }}
    >
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
```

## Context Composition

Compose multiple contexts for separation of concerns.

```tsx
// providers.tsx
import { ReactNode } from 'react';
import { AuthProvider } from './AuthContext';
import { ThemeProvider } from './ThemeContext';
import { CartProvider } from './CartContext';
import { NotificationProvider } from './NotificationContext';

interface AppProvidersProps {
  children: ReactNode;
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <AuthProvider>
      <ThemeProvider>
        <NotificationProvider>
          <CartProvider>
            {children}
          </CartProvider>
        </NotificationProvider>
      </ThemeProvider>
    </AuthProvider>
  );
}

// App.tsx
function App() {
  return (
    <AppProviders>
      <Router>
        <Routes />
      </Router>
    </AppProviders>
  );
}
```

## Performance Optimization

### Split Context by Update Frequency

```tsx
// ❌ Bad: One context for everything
const AppContext = createContext({
  user: null,
  theme: 'light',
  notifications: [],
  sidebarOpen: false,
});

// ✅ Good: Split by update frequency
const UserContext = createContext<User | null>(null);
const ThemeContext = createContext<'light' | 'dark'>('light');
const NotificationContext = createContext<Notification[]>([]);
const UIContext = createContext({ sidebarOpen: false });
```

### Memoize Provider Value

```tsx
function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);

  // ✅ Memoize the value object
  const value = useMemo(
    () => ({
      user,
      isAuthenticated: !!user,
      login: async (email: string, password: string) => {
        const result = await api.login(email, password);
        setUser(result.user);
      },
      logout: () => setUser(null),
    }),
    [user]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
```

### Split State and Dispatch

```tsx
// Separate contexts for state and dispatch
const CartStateContext = createContext<CartState | null>(null);
const CartDispatchContext = createContext<Dispatch<CartAction> | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, initialState);

  return (
    <CartStateContext.Provider value={state}>
      <CartDispatchContext.Provider value={dispatch}>
        {children}
      </CartDispatchContext.Provider>
    </CartStateContext.Provider>
  );
}

// Components that only dispatch don't re-render on state changes
export function useCartDispatch() {
  const dispatch = useContext(CartDispatchContext);
  if (!dispatch) {
    throw new Error('useCartDispatch must be used within CartProvider');
  }
  return dispatch;
}

export function useCartState() {
  const state = useContext(CartStateContext);
  if (!state) {
    throw new Error('useCartState must be used within CartProvider');
  }
  return state;
}
```

## Context with Selectors

Prevent unnecessary re-renders with selectors.

```tsx
import { useSyncExternalStore } from 'react';

interface Store<T> {
  getState: () => T;
  subscribe: (listener: () => void) => () => void;
  setState: (partial: Partial<T>) => void;
}

function createStore<T>(initialState: T): Store<T> {
  let state = initialState;
  const listeners = new Set<() => void>();

  return {
    getState: () => state,
    subscribe: (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    setState: (partial) => {
      state = { ...state, ...partial };
      listeners.forEach(listener => listener());
    },
  };
}

// Usage with selector
function useSelector<T, S>(store: Store<T>, selector: (state: T) => S): S {
  return useSyncExternalStore(
    store.subscribe,
    () => selector(store.getState()),
    () => selector(store.getState())
  );
}
```

## Best Practices

### When to Use Context

✅ **Good use cases:**
- Theme/locale preferences
- Current authenticated user
- Feature flags
- UI state (sidebar open, modals)

❌ **Avoid for:**
- Frequently changing data
- Server state (use TanStack Query)
- Large application state (use Zustand/Redux)

### Pattern Checklist

1. ✅ Always provide TypeScript types
2. ✅ Create custom hooks with error handling
3. ✅ Memoize provider values
4. ✅ Split contexts by update frequency
5. ✅ Consider separating state and dispatch
6. ✅ Use meaningful default values or null
