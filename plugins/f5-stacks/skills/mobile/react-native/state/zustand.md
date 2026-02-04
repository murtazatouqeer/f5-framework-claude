---
name: rn-zustand
description: Zustand state management in React Native
applies_to: react-native
---

# Zustand in React Native

## Installation

```bash
npm install zustand
```

## Basic Store

```typescript
// src/stores/useCounterStore.ts
import { create } from 'zustand';

interface CounterState {
  count: number;
  increment: () => void;
  decrement: () => void;
  reset: () => void;
}

export const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  reset: () => set({ count: 0 }),
}));

// Usage
function Counter() {
  const { count, increment, decrement, reset } = useCounterStore();

  return (
    <View>
      <Text>{count}</Text>
      <Button title="+" onPress={increment} />
      <Button title="-" onPress={decrement} />
      <Button title="Reset" onPress={reset} />
    </View>
  );
}
```

## Persisted Store with AsyncStorage

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
        // Restore token to API client
        if (state?.token) {
          api.defaults.headers.common.Authorization = `Bearer ${state.token}`;
        }
      },
    }
  )
);
```

## Persisted Store with MMKV (Faster)

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
```

## Selectors for Performance

```typescript
// Avoid re-renders with selectors
// ❌ Bad - re-renders on any state change
const { items, addItem } = useCartStore();

// ✅ Good - only re-renders when items change
const items = useCartStore((state) => state.items);
const addItem = useCartStore((state) => state.addItem);

// Create custom selector hooks
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

## Immer Middleware for Complex Updates

```typescript
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

interface TodoState {
  todos: {
    id: string;
    text: string;
    completed: boolean;
    subtasks: { id: string; text: string; done: boolean }[];
  }[];
  addTodo: (text: string) => void;
  toggleTodo: (id: string) => void;
  addSubtask: (todoId: string, text: string) => void;
  toggleSubtask: (todoId: string, subtaskId: string) => void;
}

export const useTodoStore = create<TodoState>()(
  immer((set) => ({
    todos: [],

    addTodo: (text) =>
      set((state) => {
        state.todos.push({
          id: Date.now().toString(),
          text,
          completed: false,
          subtasks: [],
        });
      }),

    toggleTodo: (id) =>
      set((state) => {
        const todo = state.todos.find((t) => t.id === id);
        if (todo) {
          todo.completed = !todo.completed;
        }
      }),

    addSubtask: (todoId, text) =>
      set((state) => {
        const todo = state.todos.find((t) => t.id === todoId);
        if (todo) {
          todo.subtasks.push({
            id: Date.now().toString(),
            text,
            done: false,
          });
        }
      }),

    toggleSubtask: (todoId, subtaskId) =>
      set((state) => {
        const todo = state.todos.find((t) => t.id === todoId);
        const subtask = todo?.subtasks.find((s) => s.id === subtaskId);
        if (subtask) {
          subtask.done = !subtask.done;
        }
      }),
  }))
);
```

## DevTools Integration

```typescript
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const useStore = create<State>()(
  devtools(
    (set) => ({
      // state and actions
    }),
    {
      name: 'MyStore',
      enabled: __DEV__,
    }
  )
);
```

## Combining Middlewares

```typescript
import { create } from 'zustand';
import { persist, devtools, createJSONStorage } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';
import AsyncStorage from '@react-native-async-storage/async-storage';

const useStore = create<State>()(
  devtools(
    persist(
      immer((set, get) => ({
        // state and actions
      })),
      {
        name: 'store-storage',
        storage: createJSONStorage(() => AsyncStorage),
      }
    ),
    { name: 'MyStore' }
  )
);
```

## Store Actions Outside Components

```typescript
// Call store actions from outside React
const { addItem, removeItem } = useCartStore.getState();

// Subscribe to store changes
const unsubscribe = useCartStore.subscribe((state, prevState) => {
  if (state.items.length !== prevState.items.length) {
    // Sync with backend
    syncCart(state.items);
  }
});

// Cleanup
unsubscribe();
```

## Best Practices

1. **Use Selectors**: Prevent unnecessary re-renders
2. **Persist Wisely**: Only persist what's necessary
3. **MMKV for Speed**: Use MMKV over AsyncStorage for better performance
4. **Separate Concerns**: One store per domain (auth, cart, settings)
5. **Type Everything**: Strong TypeScript types for state and actions
6. **Keep Actions Simple**: Complex logic should be in services/hooks
