---
name: rn-store
description: Zustand store templates for React Native
applies_to: react-native
variables:
  - name: storeName
    description: Name of the store (e.g., Auth, Cart, Theme)
  - name: hasPersist
    description: Include persistence with MMKV or AsyncStorage
---

# Zustand Store Templates

## Basic Store

```typescript
// src/stores/use{{storeName}}Store.ts
import { create } from 'zustand';

interface {{storeName}}State {
  // State
  items: Item[];
  selectedId: string | null;
  isLoading: boolean;

  // Actions
  setItems: (items: Item[]) => void;
  addItem: (item: Item) => void;
  removeItem: (id: string) => void;
  selectItem: (id: string | null) => void;
  setLoading: (loading: boolean) => void;
  reset: () => void;
}

const initialState = {
  items: [],
  selectedId: null,
  isLoading: false,
};

export const use{{storeName}}Store = create<{{storeName}}State>((set) => ({
  ...initialState,

  setItems: (items) => set({ items }),

  addItem: (item) =>
    set((state) => ({ items: [...state.items, item] })),

  removeItem: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
    })),

  selectItem: (id) => set({ selectedId: id }),

  setLoading: (isLoading) => set({ isLoading }),

  reset: () => set(initialState),
}));
```

## Persisted Store with MMKV

```typescript
// src/stores/use{{storeName}}Store.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: '{{kebabCase storeName}}-storage' });

const mmkvStorage: StateStorage = {
  getItem: (name) => storage.getString(name) ?? null,
  setItem: (name, value) => storage.set(name, value),
  removeItem: (name) => storage.delete(name),
};

interface {{storeName}}State {
  // State
  data: Record<string, any>;
  preferences: {
    theme: 'light' | 'dark' | 'system';
    notifications: boolean;
  };

  // Actions
  setData: (key: string, value: any) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  toggleNotifications: () => void;
  reset: () => void;
}

const initialState = {
  data: {},
  preferences: {
    theme: 'system' as const,
    notifications: true,
  },
};

export const use{{storeName}}Store = create<{{storeName}}State>()(
  persist(
    (set) => ({
      ...initialState,

      setData: (key, value) =>
        set((state) => ({
          data: { ...state.data, [key]: value },
        })),

      setTheme: (theme) =>
        set((state) => ({
          preferences: { ...state.preferences, theme },
        })),

      toggleNotifications: () =>
        set((state) => ({
          preferences: {
            ...state.preferences,
            notifications: !state.preferences.notifications,
          },
        })),

      reset: () => set(initialState),
    }),
    {
      name: '{{kebabCase storeName}}-storage',
      storage: createJSONStorage(() => mmkvStorage),
    }
  )
);
```

## Auth Store

```typescript
// src/stores/useAuthStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';
import { api } from '@/lib/api';
import type { User } from '@/types';

const storage = new MMKV({ id: 'auth-storage' });

const mmkvStorage: StateStorage = {
  getItem: (name) => storage.getString(name) ?? null,
  setItem: (name, value) => storage.set(name, value),
  removeItem: (name) => storage.delete(name),
};

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (data: Partial<User>) => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      isAuthenticated: false,

      login: async (email, password) => {
        set({ isLoading: true });
        try {
          const { data } = await api.post('/auth/login', { email, password });
          api.defaults.headers.common.Authorization = `Bearer ${data.token}`;
          set({
            user: data.user,
            token: data.token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      logout: async () => {
        try {
          await api.post('/auth/logout');
        } finally {
          delete api.defaults.headers.common.Authorization;
          set({
            user: null,
            token: null,
            isAuthenticated: false,
          });
        }
      },

      updateUser: (data) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...data } : null,
        })),

      setLoading: (isLoading) => set({ isLoading }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => mmkvStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          api.defaults.headers.common.Authorization = `Bearer ${state.token}`;
        }
      },
    }
  )
);
```

## Cart Store

```typescript
// src/stores/useCartStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV({ id: 'cart-storage' });

const mmkvStorage: StateStorage = {
  getItem: (name) => storage.getString(name) ?? null,
  setItem: (name, value) => storage.set(name, value),
  removeItem: (name) => storage.delete(name),
};

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
  imageUrl?: string;
}

interface CartState {
  items: CartItem[];

  // Actions
  addItem: (item: Omit<CartItem, 'quantity'>) => void;
  removeItem: (id: string) => void;
  updateQuantity: (id: string, quantity: number) => void;
  clear: () => void;

  // Computed (using selectors)
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],

      addItem: (newItem) =>
        set((state) => {
          const existing = state.items.find((item) => item.id === newItem.id);
          if (existing) {
            return {
              items: state.items.map((item) =>
                item.id === newItem.id
                  ? { ...item, quantity: item.quantity + 1 }
                  : item
              ),
            };
          }
          return { items: [...state.items, { ...newItem, quantity: 1 }] };
        }),

      removeItem: (id) =>
        set((state) => ({
          items: state.items.filter((item) => item.id !== id),
        })),

      updateQuantity: (id, quantity) =>
        set((state) => {
          if (quantity <= 0) {
            return { items: state.items.filter((item) => item.id !== id) };
          }
          return {
            items: state.items.map((item) =>
              item.id === id ? { ...item, quantity } : item
            ),
          };
        }),

      clear: () => set({ items: [] }),
    }),
    {
      name: 'cart-storage',
      storage: createJSONStorage(() => mmkvStorage),
    }
  )
);

// Selectors
export const useCartItems = () => useCartStore((state) => state.items);

export const useCartItemCount = () =>
  useCartStore((state) =>
    state.items.reduce((sum, item) => sum + item.quantity, 0)
  );

export const useCartTotal = () =>
  useCartStore((state) =>
    state.items.reduce((sum, item) => sum + item.price * item.quantity, 0)
  );

export const useCartItem = (id: string) =>
  useCartStore((state) => state.items.find((item) => item.id === id));
```

## Theme Store

```typescript
// src/stores/useThemeStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';
import { Appearance } from 'react-native';

const storage = new MMKV({ id: 'theme-storage' });

const mmkvStorage: StateStorage = {
  getItem: (name) => storage.getString(name) ?? null,
  setItem: (name, value) => storage.set(name, value),
  removeItem: (name) => storage.delete(name),
};

type ThemeMode = 'light' | 'dark' | 'system';

interface ThemeState {
  mode: ThemeMode;
  isDark: boolean;

  setMode: (mode: ThemeMode) => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'system',
      isDark: Appearance.getColorScheme() === 'dark',

      setMode: (mode) => {
        const systemIsDark = Appearance.getColorScheme() === 'dark';
        const isDark = mode === 'dark' || (mode === 'system' && systemIsDark);
        set({ mode, isDark });
      },
    }),
    {
      name: 'theme-storage',
      storage: createJSONStorage(() => mmkvStorage),
      partialize: (state) => ({ mode: state.mode }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          const systemIsDark = Appearance.getColorScheme() === 'dark';
          state.isDark =
            state.mode === 'dark' ||
            (state.mode === 'system' && systemIsDark);
        }
      },
    }
  )
);

// Listen to system theme changes
Appearance.addChangeListener(({ colorScheme }) => {
  const { mode } = useThemeStore.getState();
  if (mode === 'system') {
    useThemeStore.setState({ isDark: colorScheme === 'dark' });
  }
});
```

## Usage

1. Replace `{{storeName}}` with store name
2. Choose persistence strategy (MMKV recommended)
3. Define state interface and actions
4. Create selectors for computed values
5. Export from stores/index.ts
