---
name: rn-store-generator
description: Generate Zustand stores for React Native state management
triggers:
  - "rn store"
  - "react native store"
  - "create store"
  - "zustand store"
applies_to: react-native
---

# React Native Store Generator

## Purpose

Generate Zustand stores with:
- TypeScript interfaces
- Persist middleware with AsyncStorage/MMKV
- Computed values via getters
- Async actions
- Selectors for optimized re-renders
- DevTools integration

## Input Requirements

```yaml
required:
  - store_name: string        # e.g., "auth", "cart", "settings"
  - state_shape: object       # Define state structure

optional:
  - persist: boolean          # Enable persistence
  - storage_type: async | mmkv | secure
  - actions: string[]         # List of action names
  - computed: string[]        # List of computed values
```

## Generation Templates

### Basic Store Template

```typescript
// src/stores/use{{StoreName}}Store.ts
import { create } from 'zustand';

interface {{StoreName}}State {
  // State
  items: {{Item}}[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setItems: (items: {{Item}}[]) => void;
  addItem: (item: {{Item}}) => void;
  updateItem: (id: string, updates: Partial<{{Item}}>) => void;
  removeItem: (id: string) => void;
  selectItem: (id: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

const initialState = {
  items: [],
  selectedId: null,
  isLoading: false,
  error: null,
};

export const use{{StoreName}}Store = create<{{StoreName}}State>((set) => ({
  ...initialState,

  setItems: (items) => set({ items }),

  addItem: (item) =>
    set((state) => ({
      items: [...state.items, item],
    })),

  updateItem: (id, updates) =>
    set((state) => ({
      items: state.items.map((item) =>
        item.id === id ? { ...item, ...updates } : item
      ),
    })),

  removeItem: (id) =>
    set((state) => ({
      items: state.items.filter((item) => item.id !== id),
      selectedId: state.selectedId === id ? null : state.selectedId,
    })),

  selectItem: (id) => set({ selectedId: id }),

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  reset: () => set(initialState),
}));

// Selectors
export const use{{StoreName}}Items = () =>
  use{{StoreName}}Store((state) => state.items);

export const useSelected{{Item}} = () =>
  use{{StoreName}}Store((state) =>
    state.items.find((item) => item.id === state.selectedId)
  );

export const use{{StoreName}}Loading = () =>
  use{{StoreName}}Store((state) => state.isLoading);

export const use{{StoreName}}Error = () =>
  use{{StoreName}}Store((state) => state.error);
```

### Persisted Store with AsyncStorage

```typescript
// src/stores/useAuthStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { api } from '@/lib/api';
import type { User } from '@/types';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,

      login: async (email, password) => {
        set({ isLoading: true, error: null });

        try {
          const response = await api.post('/auth/login', { email, password });
          const { user, token } = response.data;

          // Set token for future API requests
          api.defaults.headers.common.Authorization = `Bearer ${token}`;

          set({ user, token, isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Login failed',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          await api.post('/auth/logout');
        } finally {
          delete api.defaults.headers.common.Authorization;
          set({ user: null, token: null });
        }
      },

      register: async (data) => {
        set({ isLoading: true, error: null });

        try {
          const response = await api.post('/auth/register', data);
          const { user, token } = response.data;

          api.defaults.headers.common.Authorization = `Bearer ${token}`;
          set({ user, token, isLoading: false });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Registration failed',
            isLoading: false,
          });
          throw error;
        }
      },

      updateProfile: async (data) => {
        const currentUser = get().user;
        if (!currentUser) return;

        try {
          const response = await api.patch('/auth/me', data);
          set({ user: response.data });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : 'Update failed',
          });
          throw error;
        }
      },

      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => AsyncStorage),
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          api.defaults.headers.common.Authorization = `Bearer ${state.token}`;
        }
      },
    }
  )
);

// Selectors
export const useUser = () => useAuthStore((state) => state.user);
export const useIsAuthenticated = () => useAuthStore((state) => !!state.token);
export const useAuthLoading = () => useAuthStore((state) => state.isLoading);
export const useAuthError = () => useAuthStore((state) => state.error);
```

### Persisted Store with MMKV

```typescript
// src/stores/useCartStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import { MMKV } from 'react-native-mmkv';

const storage = new MMKV();

const mmkvStorage: StateStorage = {
  getItem: (name) => {
    const value = storage.getString(name);
    return value ?? null;
  },
  setItem: (name, value) => {
    storage.set(name, value);
  },
  removeItem: (name) => {
    storage.delete(name);
  },
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
}

export const useCartStore = create<CartState>()(
  persist(
    (set, get) => ({
      items: [],

      addItem: (newItem) => {
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

          return {
            items: [...state.items, { ...newItem, quantity: 1 }],
          };
        });
      },

      removeItem: (id) => {
        set((state) => ({
          items: state.items.filter((item) => item.id !== id),
        }));
      },

      updateQuantity: (id, quantity) => {
        if (quantity <= 0) {
          get().removeItem(id);
          return;
        }

        set((state) => ({
          items: state.items.map((item) =>
            item.id === id ? { ...item, quantity } : item
          ),
        }));
      },

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

### Settings Store with Secure Storage

```typescript
// src/stores/useSettingsStore.ts
import { create } from 'zustand';
import { persist, createJSONStorage, StateStorage } from 'zustand/middleware';
import * as SecureStore from 'expo-secure-store';

const secureStorage: StateStorage = {
  getItem: async (name) => {
    return await SecureStore.getItemAsync(name);
  },
  setItem: async (name, value) => {
    await SecureStore.setItemAsync(name, value);
  },
  removeItem: async (name) => {
    await SecureStore.deleteItemAsync(name);
  },
};

type Theme = 'light' | 'dark' | 'system';
type Language = 'en' | 'ja' | 'vi';

interface SettingsState {
  theme: Theme;
  language: Language;
  notificationsEnabled: boolean;
  biometricEnabled: boolean;

  // Actions
  setTheme: (theme: Theme) => void;
  setLanguage: (language: Language) => void;
  toggleNotifications: () => void;
  toggleBiometric: () => void;
  reset: () => void;
}

const defaultSettings = {
  theme: 'system' as Theme,
  language: 'en' as Language,
  notificationsEnabled: true,
  biometricEnabled: false,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...defaultSettings,

      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
      toggleNotifications: () =>
        set((state) => ({ notificationsEnabled: !state.notificationsEnabled })),
      toggleBiometric: () =>
        set((state) => ({ biometricEnabled: !state.biometricEnabled })),
      reset: () => set(defaultSettings),
    }),
    {
      name: 'settings-storage',
      storage: createJSONStorage(() => secureStorage),
    }
  )
);

// Selectors
export const useTheme = () => useSettingsStore((state) => state.theme);
export const useLanguage = () => useSettingsStore((state) => state.language);
```

## Output Structure

```
src/stores/
├── useAuthStore.ts
├── useCartStore.ts
├── useSettingsStore.ts
└── index.ts
```

## Best Practices

1. **Naming**: Use "use" prefix and "Store" suffix
2. **Selectors**: Create selector hooks to prevent re-renders
3. **Immer**: Use immer middleware for complex state updates
4. **Persistence**: Choose storage based on data sensitivity
5. **Partialize**: Only persist necessary state
6. **DevTools**: Enable devtools in development
7. **Reset**: Always include a reset action
