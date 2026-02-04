# React Context Template

Production-ready Context API templates for React applications with TypeScript.

## Basic Context Template

```tsx
// contexts/{{ContextName}}Context.tsx
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  type FC,
  type ReactNode,
} from 'react';

// Types
interface {{ContextName}}State {
  value: string;
  count: number;
  isLoading: boolean;
}

interface {{ContextName}}Actions {
  setValue: (value: string) => void;
  increment: () => void;
  decrement: () => void;
  reset: () => void;
}

interface {{ContextName}}ContextValue extends {{ContextName}}State, {{ContextName}}Actions {}

// Initial state
const initialState: {{ContextName}}State = {
  value: '',
  count: 0,
  isLoading: false,
};

// Create context
const {{ContextName}}Context = createContext<{{ContextName}}ContextValue | null>(null);

// Custom hook
export function use{{ContextName}}() {
  const context = useContext({{ContextName}}Context);

  if (!context) {
    throw new Error(
      'use{{ContextName}} must be used within a {{ContextName}}Provider'
    );
  }

  return context;
}

// Provider component
interface {{ContextName}}ProviderProps {
  children: ReactNode;
  initialValue?: Partial<{{ContextName}}State>;
}

export const {{ContextName}}Provider: FC<{{ContextName}}ProviderProps> = ({
  children,
  initialValue,
}) => {
  const [state, setState] = useState<{{ContextName}}State>({
    ...initialState,
    ...initialValue,
  });

  // Actions
  const setValue = useCallback((value: string) => {
    setState((prev) => ({ ...prev, value }));
  }, []);

  const increment = useCallback(() => {
    setState((prev) => ({ ...prev, count: prev.count + 1 }));
  }, []);

  const decrement = useCallback(() => {
    setState((prev) => ({ ...prev, count: prev.count - 1 }));
  }, []);

  const reset = useCallback(() => {
    setState(initialState);
  }, []);

  // Memoize context value
  const contextValue = useMemo<{{ContextName}}ContextValue>(
    () => ({
      ...state,
      setValue,
      increment,
      decrement,
      reset,
    }),
    [state, setValue, increment, decrement, reset]
  );

  return (
    <{{ContextName}}Context.Provider value={contextValue}>
      {children}
    </{{ContextName}}Context.Provider>
  );
};
```

## Context with Reducer Pattern

```tsx
// contexts/{{ContextName}}Context.tsx
import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useMemo,
  type FC,
  type ReactNode,
  type Dispatch,
} from 'react';

// State type
interface {{ContextName}}State {
  items: Item[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;
}

// Action types
type {{ContextName}}Action =
  | { type: 'SET_ITEMS'; payload: Item[] }
  | { type: 'ADD_ITEM'; payload: Item }
  | { type: 'UPDATE_ITEM'; payload: { id: string; data: Partial<Item> } }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'SELECT_ITEM'; payload: string | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'RESET' };

// Initial state
const initialState: {{ContextName}}State = {
  items: [],
  selectedId: null,
  isLoading: false,
  error: null,
};

// Reducer
function {{contextName}}Reducer(
  state: {{ContextName}}State,
  action: {{ContextName}}Action
): {{ContextName}}State {
  switch (action.type) {
    case 'SET_ITEMS':
      return { ...state, items: action.payload, error: null };

    case 'ADD_ITEM':
      return { ...state, items: [...state.items, action.payload] };

    case 'UPDATE_ITEM':
      return {
        ...state,
        items: state.items.map((item) =>
          item.id === action.payload.id
            ? { ...item, ...action.payload.data }
            : item
        ),
      };

    case 'REMOVE_ITEM':
      return {
        ...state,
        items: state.items.filter((item) => item.id !== action.payload),
        selectedId:
          state.selectedId === action.payload ? null : state.selectedId,
      };

    case 'SELECT_ITEM':
      return { ...state, selectedId: action.payload };

    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload, isLoading: false };

    case 'RESET':
      return initialState;

    default:
      return state;
  }
}

// Context type
interface {{ContextName}}ContextValue {
  state: {{ContextName}}State;
  dispatch: Dispatch<{{ContextName}}Action>;
  actions: {
    setItems: (items: Item[]) => void;
    addItem: (item: Item) => void;
    updateItem: (id: string, data: Partial<Item>) => void;
    removeItem: (id: string) => void;
    selectItem: (id: string | null) => void;
  };
  selectors: {
    selectedItem: Item | undefined;
    itemCount: number;
  };
}

// Create context
const {{ContextName}}Context = createContext<{{ContextName}}ContextValue | null>(null);

// Custom hook
export function use{{ContextName}}() {
  const context = useContext({{ContextName}}Context);

  if (!context) {
    throw new Error(
      'use{{ContextName}} must be used within a {{ContextName}}Provider'
    );
  }

  return context;
}

// Selector hooks for performance
export function use{{ContextName}}State() {
  return use{{ContextName}}().state;
}

export function use{{ContextName}}Actions() {
  return use{{ContextName}}().actions;
}

export function use{{ContextName}}Selectors() {
  return use{{ContextName}}().selectors;
}

// Provider
interface {{ContextName}}ProviderProps {
  children: ReactNode;
  initialItems?: Item[];
}

export const {{ContextName}}Provider: FC<{{ContextName}}ProviderProps> = ({
  children,
  initialItems = [],
}) => {
  const [state, dispatch] = useReducer({{contextName}}Reducer, {
    ...initialState,
    items: initialItems,
  });

  // Memoized actions
  const actions = useMemo(
    () => ({
      setItems: (items: Item[]) =>
        dispatch({ type: 'SET_ITEMS', payload: items }),
      addItem: (item: Item) =>
        dispatch({ type: 'ADD_ITEM', payload: item }),
      updateItem: (id: string, data: Partial<Item>) =>
        dispatch({ type: 'UPDATE_ITEM', payload: { id, data } }),
      removeItem: (id: string) =>
        dispatch({ type: 'REMOVE_ITEM', payload: id }),
      selectItem: (id: string | null) =>
        dispatch({ type: 'SELECT_ITEM', payload: id }),
    }),
    []
  );

  // Memoized selectors
  const selectors = useMemo(
    () => ({
      selectedItem: state.items.find((item) => item.id === state.selectedId),
      itemCount: state.items.length,
    }),
    [state.items, state.selectedId]
  );

  const contextValue = useMemo<{{ContextName}}ContextValue>(
    () => ({
      state,
      dispatch,
      actions,
      selectors,
    }),
    [state, actions, selectors]
  );

  return (
    <{{ContextName}}Context.Provider value={contextValue}>
      {children}
    </{{ContextName}}Context.Provider>
  );
};
```

## Async Context Pattern

```tsx
// contexts/{{ContextName}}Context.tsx
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
  type FC,
  type ReactNode,
} from 'react';

interface {{ContextName}}State {
  data: Data | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
}

interface {{ContextName}}Actions {
  fetch: () => Promise<void>;
  refresh: () => Promise<void>;
  update: (data: Partial<Data>) => Promise<void>;
  reset: () => void;
}

interface {{ContextName}}ContextValue extends {{ContextName}}State, {{ContextName}}Actions {}

const {{ContextName}}Context = createContext<{{ContextName}}ContextValue | null>(null);

export function use{{ContextName}}() {
  const context = useContext({{ContextName}}Context);

  if (!context) {
    throw new Error(
      'use{{ContextName}} must be used within a {{ContextName}}Provider'
    );
  }

  return context;
}

interface {{ContextName}}ProviderProps {
  children: ReactNode;
  fetchFn: () => Promise<Data>;
  updateFn?: (data: Partial<Data>) => Promise<Data>;
  autoFetch?: boolean;
}

export const {{ContextName}}Provider: FC<{{ContextName}}ProviderProps> = ({
  children,
  fetchFn,
  updateFn,
  autoFetch = true,
}) => {
  const [state, setState] = useState<{{ContextName}}State>({
    data: null,
    isLoading: false,
    isError: false,
    error: null,
  });

  const fetch = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true, isError: false, error: null }));

    try {
      const data = await fetchFn();
      setState({ data, isLoading: false, isError: false, error: null });
    } catch (error) {
      setState({
        data: null,
        isLoading: false,
        isError: true,
        error: error as Error,
      });
    }
  }, [fetchFn]);

  const refresh = useCallback(async () => {
    await fetch();
  }, [fetch]);

  const update = useCallback(
    async (data: Partial<Data>) => {
      if (!updateFn) {
        console.warn('Update function not provided');
        return;
      }

      setState((prev) => ({ ...prev, isLoading: true }));

      try {
        const updatedData = await updateFn(data);
        setState((prev) => ({ ...prev, data: updatedData, isLoading: false }));
      } catch (error) {
        setState((prev) => ({
          ...prev,
          isLoading: false,
          isError: true,
          error: error as Error,
        }));
      }
    },
    [updateFn]
  );

  const reset = useCallback(() => {
    setState({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
    });
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetch();
    }
  }, [autoFetch, fetch]);

  const contextValue = useMemo<{{ContextName}}ContextValue>(
    () => ({
      ...state,
      fetch,
      refresh,
      update,
      reset,
    }),
    [state, fetch, refresh, update, reset]
  );

  return (
    <{{ContextName}}Context.Provider value={contextValue}>
      {children}
    </{{ContextName}}Context.Provider>
  );
};
```

## Theme Context Example

```tsx
// contexts/ThemeContext.tsx
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
  type FC,
  type ReactNode,
} from 'react';

type Theme = 'light' | 'dark' | 'system';
type ResolvedTheme = 'light' | 'dark';

interface ThemeContextValue {
  theme: Theme;
  resolvedTheme: ResolvedTheme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function useTheme() {
  const context = useContext(ThemeContext);

  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }

  return context;
}

interface ThemeProviderProps {
  children: ReactNode;
  defaultTheme?: Theme;
  storageKey?: string;
}

export const ThemeProvider: FC<ThemeProviderProps> = ({
  children,
  defaultTheme = 'system',
  storageKey = 'theme',
}) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === 'undefined') return defaultTheme;
    return (localStorage.getItem(storageKey) as Theme) || defaultTheme;
  });

  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>('light');

  // Resolve system theme
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const resolveTheme = () => {
      if (theme === 'system') {
        setResolvedTheme(mediaQuery.matches ? 'dark' : 'light');
      } else {
        setResolvedTheme(theme);
      }
    };

    resolveTheme();
    mediaQuery.addEventListener('change', resolveTheme);

    return () => mediaQuery.removeEventListener('change', resolveTheme);
  }, [theme]);

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolvedTheme);
  }, [resolvedTheme]);

  const setTheme = useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme);
      localStorage.setItem(storageKey, newTheme);
    },
    [storageKey]
  );

  const toggleTheme = useCallback(() => {
    setTheme(resolvedTheme === 'dark' ? 'light' : 'dark');
  }, [resolvedTheme, setTheme]);

  const contextValue = useMemo<ThemeContextValue>(
    () => ({
      theme,
      resolvedTheme,
      setTheme,
      toggleTheme,
    }),
    [theme, resolvedTheme, setTheme, toggleTheme]
  );

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
};
```

## Auth Context Example

```tsx
// contexts/AuthContext.tsx
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
  type FC,
  type ReactNode,
} from 'react';

interface User {
  id: string;
  email: string;
  name: string;
  avatar?: string;
  role: 'admin' | 'user';
}

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

interface AuthActions {
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
}

interface AuthContextValue extends AuthState, AuthActions {}

const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }

  return context;
}

// Convenience hooks
export const useUser = () => useAuth().user;
export const useIsAuthenticated = () => useAuth().isAuthenticated;

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch('/api/auth/me', {
          credentials: 'include',
        });

        if (response.ok) {
          const user = await response.json();
          setState({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } else {
          setState({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } catch {
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    };

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Login failed');
      }

      const user = await response.json();
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: (error as Error).message,
      }));
      throw error;
    }
  }, []);

  const logout = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));

    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include',
      });
    } finally {
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        error: null,
      });
    }
  }, []);

  const register = useCallback(async (data: RegisterData) => {
    setState((prev) => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || 'Registration failed');
      }

      const user = await response.json();
      setState({
        user,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: (error as Error).message,
      }));
      throw error;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const response = await fetch('/api/auth/me', {
        credentials: 'include',
      });

      if (response.ok) {
        const user = await response.json();
        setState((prev) => ({ ...prev, user }));
      }
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: null }));
  }, []);

  const contextValue = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      logout,
      register,
      refreshUser,
      clearError,
    }),
    [state, login, logout, register, refreshUser, clearError]
  );

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};
```

## Usage Examples

### Basic Usage
```tsx
// App.tsx
import { {{ContextName}}Provider } from '@/contexts/{{ContextName}}Context';

function App() {
  return (
    <{{ContextName}}Provider>
      <MainContent />
    </{{ContextName}}Provider>
  );
}

// Component.tsx
import { use{{ContextName}} } from '@/contexts/{{ContextName}}Context';

function Component() {
  const { value, setValue, isLoading } = use{{ContextName}}();

  if (isLoading) return <Loading />;

  return (
    <div>
      <span>{value}</span>
      <button onClick={() => setValue('new value')}>Update</button>
    </div>
  );
}
```

### Nested Providers
```tsx
// providers.tsx
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { AppProvider } from '@/contexts/AppContext';

export function Providers({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppProvider>
          {children}
        </AppProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
```

## Testing Context

```tsx
// __tests__/{{ContextName}}Context.test.tsx
import { render, screen, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { {{ContextName}}Provider, use{{ContextName}} } from '../{{ContextName}}Context';

// Test component that uses the context
function TestComponent() {
  const { value, setValue } = use{{ContextName}}();
  return (
    <div>
      <span data-testid="value">{value}</span>
      <button onClick={() => setValue('updated')}>Update</button>
    </div>
  );
}

describe('{{ContextName}}Context', () => {
  it('provides initial value', () => {
    render(
      <{{ContextName}}Provider initialValue={{ value: 'initial' }}>
        <TestComponent />
      </{{ContextName}}Provider>
    );

    expect(screen.getByTestId('value')).toHaveTextContent('initial');
  });

  it('updates value', async () => {
    const user = userEvent.setup();

    render(
      <{{ContextName}}Provider>
        <TestComponent />
      </{{ContextName}}Provider>
    );

    await user.click(screen.getByRole('button', { name: /update/i }));

    expect(screen.getByTestId('value')).toHaveTextContent('updated');
  });

  it('throws error when used outside provider', () => {
    const consoleSpy = jest.spyOn(console, 'error').mockImplementation();

    expect(() => render(<TestComponent />)).toThrow(
      'use{{ContextName}} must be used within a {{ContextName}}Provider'
    );

    consoleSpy.mockRestore();
  });
});
```

## Best Practices

1. **Split state and actions** - Separate state from dispatch for cleaner API
2. **Memoize context value** - Prevent unnecessary re-renders
3. **Use selector hooks** - Create specific hooks for common selections
4. **Keep contexts focused** - One concern per context
5. **Provide default values** - Make context easier to test
6. **Handle loading states** - Include isLoading for async operations
7. **Type everything** - Full TypeScript coverage for safety
