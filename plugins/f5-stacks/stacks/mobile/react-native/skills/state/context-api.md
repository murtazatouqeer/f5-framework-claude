---
name: rn-context-api
description: React Context API for local state sharing
applies_to: react-native
---

# React Context API

## When to Use Context

- **Theme/Appearance**: Dark mode, colors, fonts
- **Localization**: Language, locale settings
- **Authentication Status**: Current user state
- **Feature Flags**: Feature toggles
- **App Configuration**: API URLs, feature settings

**Avoid Context for**:
- Frequently changing state (causes re-renders)
- Complex state logic (use Zustand/Redux)
- Server state (use TanStack Query)

## Basic Context Pattern

```typescript
// src/contexts/ThemeContext.tsx
import { createContext, useContext, useState, useMemo, ReactNode } from 'react';
import { useColorScheme } from 'react-native';

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeColors {
  background: string;
  surface: string;
  primary: string;
  text: string;
  textSecondary: string;
  border: string;
}

interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  isDark: boolean;
  colors: ThemeColors;
}

const lightColors: ThemeColors = {
  background: '#FFFFFF',
  surface: '#F2F2F7',
  primary: '#007AFF',
  text: '#000000',
  textSecondary: '#3C3C43',
  border: '#C6C6C8',
};

const darkColors: ThemeColors = {
  background: '#000000',
  surface: '#1C1C1E',
  primary: '#0A84FF',
  text: '#FFFFFF',
  textSecondary: '#EBEBF5',
  border: '#38383A',
};

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const systemScheme = useColorScheme();
  const [mode, setMode] = useState<ThemeMode>('system');

  const value = useMemo(() => {
    const isDark =
      mode === 'dark' || (mode === 'system' && systemScheme === 'dark');

    return {
      mode,
      setMode,
      isDark,
      colors: isDark ? darkColors : lightColors,
    };
  }, [mode, systemScheme]);

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}

// Usage
function MyComponent() {
  const { colors, isDark, setMode } = useTheme();

  return (
    <View style={{ backgroundColor: colors.background }}>
      <Text style={{ color: colors.text }}>
        {isDark ? 'Dark Mode' : 'Light Mode'}
      </Text>
      <Button onPress={() => setMode('dark')} title="Dark" />
    </View>
  );
}
```

## Auth Context Pattern

```typescript
// src/contexts/AuthContext.tsx
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from 'react';
import * as SecureStore from 'expo-secure-store';
import { api } from '@/lib/api';
import type { User } from '@/types';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const token = await SecureStore.getItemAsync('authToken');
        if (token) {
          api.defaults.headers.common.Authorization = `Bearer ${token}`;
          const response = await api.get('/auth/me');
          setUser(response.data);
        }
      } catch {
        // Token invalid, clear it
        await SecureStore.deleteItemAsync('authToken');
      } finally {
        setIsLoading(false);
      }
    };

    restoreSession();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password });
    const { user, token } = response.data;

    await SecureStore.setItemAsync('authToken', token);
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    setUser(user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      await SecureStore.deleteItemAsync('authToken');
      delete api.defaults.headers.common.Authorization;
      setUser(null);
    }
  }, []);

  const updateUser = useCallback((data: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...data } : null));
  }, []);

  const value = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    updateUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
```

## Localization Context

```typescript
// src/contexts/LocalizationContext.tsx
import { createContext, useContext, useState, useMemo, ReactNode } from 'react';
import * as Localization from 'expo-localization';
import { I18n } from 'i18n-js';

import en from '@/locales/en.json';
import ja from '@/locales/ja.json';
import vi from '@/locales/vi.json';

type Language = 'en' | 'ja' | 'vi';

interface LocalizationContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string, options?: Record<string, any>) => string;
  locale: string;
}

const translations = { en, ja, vi };
const i18n = new I18n(translations);
i18n.enableFallback = true;

const LocalizationContext = createContext<LocalizationContextType | undefined>(
  undefined
);

export function LocalizationProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(() => {
    const deviceLang = Localization.locale.split('-')[0];
    return ['en', 'ja', 'vi'].includes(deviceLang)
      ? (deviceLang as Language)
      : 'en';
  });

  const value = useMemo(() => {
    i18n.locale = language;

    return {
      language,
      setLanguage,
      t: (key: string, options?: Record<string, any>) => i18n.t(key, options),
      locale: Localization.locale,
    };
  }, [language]);

  return (
    <LocalizationContext.Provider value={value}>
      {children}
    </LocalizationContext.Provider>
  );
}

export function useLocalization() {
  const context = useContext(LocalizationContext);
  if (!context) {
    throw new Error(
      'useLocalization must be used within a LocalizationProvider'
    );
  }
  return context;
}

// Usage
function WelcomeScreen() {
  const { t, setLanguage } = useLocalization();

  return (
    <View>
      <Text>{t('welcome.title')}</Text>
      <Text>{t('welcome.greeting', { name: 'John' })}</Text>
      <Button onPress={() => setLanguage('ja')} title="Japanese" />
    </View>
  );
}
```

## Context with Reducer

```typescript
// src/contexts/CartContext.tsx
import {
  createContext,
  useContext,
  useReducer,
  useMemo,
  ReactNode,
} from 'react';

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

interface CartState {
  items: CartItem[];
}

type CartAction =
  | { type: 'ADD_ITEM'; payload: Omit<CartItem, 'quantity'> }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'UPDATE_QUANTITY'; payload: { id: string; quantity: number } }
  | { type: 'CLEAR' };

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'ADD_ITEM': {
      const existing = state.items.find((item) => item.id === action.payload.id);
      if (existing) {
        return {
          items: state.items.map((item) =>
            item.id === action.payload.id
              ? { ...item, quantity: item.quantity + 1 }
              : item
          ),
        };
      }
      return {
        items: [...state.items, { ...action.payload, quantity: 1 }],
      };
    }
    case 'REMOVE_ITEM':
      return {
        items: state.items.filter((item) => item.id !== action.payload),
      };
    case 'UPDATE_QUANTITY':
      if (action.payload.quantity <= 0) {
        return {
          items: state.items.filter((item) => item.id !== action.payload.id),
        };
      }
      return {
        items: state.items.map((item) =>
          item.id === action.payload.id
            ? { ...item, quantity: action.payload.quantity }
            : item
        ),
      };
    case 'CLEAR':
      return { items: [] };
    default:
      return state;
  }
}

interface CartContextType {
  items: CartItem[];
  itemCount: number;
  total: number;
  addItem: (item: Omit<CartItem, 'quantity'>) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clear: () => void;
}

const CartContext = createContext<CartContextType | undefined>(undefined);

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [] });

  const value = useMemo(() => ({
    items: state.items,
    itemCount: state.items.reduce((sum, item) => sum + item.quantity, 0),
    total: state.items.reduce(
      (sum, item) => sum + item.price * item.quantity,
      0
    ),
    addItem: (item: Omit<CartItem, 'quantity'>) =>
      dispatch({ type: 'ADD_ITEM', payload: item }),
    removeItem: (id: string) =>
      dispatch({ type: 'REMOVE_ITEM', payload: id }),
    updateQuantity: (id: string, quantity: number) =>
      dispatch({ type: 'UPDATE_QUANTITY', payload: { id, quantity } }),
    clear: () => dispatch({ type: 'CLEAR' }),
  }), [state.items]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
```

## Combining Providers

```typescript
// src/providers/AppProviders.tsx
import { ReactNode } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { queryClient } from '@/lib/queryClient';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { AuthProvider } from '@/contexts/AuthContext';
import { LocalizationProvider } from '@/contexts/LocalizationContext';

export function AppProviders({ children }: { children: ReactNode }) {
  return (
    <SafeAreaProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <LocalizationProvider>
            <AuthProvider>{children}</AuthProvider>
          </LocalizationProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

// App.tsx
export default function App() {
  return (
    <AppProviders>
      <NavigationContainer>
        <RootNavigator />
      </NavigationContainer>
    </AppProviders>
  );
}
```

## Best Practices

1. **Memoize Values**: Use useMemo to prevent re-renders
2. **Separate Contexts**: Don't put everything in one context
3. **Error Boundaries**: Create proper error handling hooks
4. **Type Safety**: Always define proper TypeScript types
5. **Default Values**: Provide meaningful defaults or throw errors
6. **Avoid Over-Use**: Consider Zustand for complex state
