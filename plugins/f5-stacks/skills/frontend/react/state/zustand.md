# Zustand State Management

## Overview

Minimal, flexible state management library with hooks-first approach.

## Basic Store

```tsx
import { create } from 'zustand';

interface CounterState {
  count: number;
  increment: () => void;
  decrement: () => void;
  reset: () => void;
}

const useCounterStore = create<CounterState>((set) => ({
  count: 0,
  increment: () => set((state) => ({ count: state.count + 1 })),
  decrement: () => set((state) => ({ count: state.count - 1 })),
  reset: () => set({ count: 0 }),
}));

// Usage
function Counter() {
  const { count, increment, decrement } = useCounterStore();

  return (
    <div>
      <span>{count}</span>
      <button onClick={increment}>+</button>
      <button onClick={decrement}>-</button>
    </div>
  );
}
```

## Store with Async Actions

```tsx
interface Product {
  id: string;
  name: string;
  price: number;
}

interface ProductState {
  products: Product[];
  isLoading: boolean;
  error: string | null;
  fetchProducts: () => Promise<void>;
  addProduct: (product: Omit<Product, 'id'>) => Promise<void>;
  deleteProduct: (id: string) => Promise<void>;
}

const useProductStore = create<ProductState>((set, get) => ({
  products: [],
  isLoading: false,
  error: null,

  fetchProducts: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch('/api/products');
      const products = await response.json();
      set({ products, isLoading: false });
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  addProduct: async (product) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch('/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(product),
      });
      const newProduct = await response.json();
      set((state) => ({
        products: [...state.products, newProduct],
        isLoading: false,
      }));
    } catch (error) {
      set({ error: (error as Error).message, isLoading: false });
    }
  },

  deleteProduct: async (id) => {
    // Optimistic update
    const previousProducts = get().products;
    set((state) => ({
      products: state.products.filter((p) => p.id !== id),
    }));

    try {
      await fetch(`/api/products/${id}`, { method: 'DELETE' });
    } catch (error) {
      // Rollback on error
      set({ products: previousProducts, error: (error as Error).message });
    }
  },
}));
```

## Entity Store Pattern

Normalized data structure for collections.

```tsx
interface Entity {
  id: string;
}

interface EntityState<T extends Entity> {
  ids: string[];
  entities: Record<string, T>;
  selectedId: string | null;
}

interface EntityActions<T extends Entity> {
  add: (entity: T) => void;
  update: (id: string, changes: Partial<T>) => void;
  remove: (id: string) => void;
  setSelected: (id: string | null) => void;
  getById: (id: string) => T | undefined;
  getAll: () => T[];
}

function createEntityStore<T extends Entity>(name: string) {
  return create<EntityState<T> & EntityActions<T>>((set, get) => ({
    ids: [],
    entities: {},
    selectedId: null,

    add: (entity) =>
      set((state) => ({
        ids: [...state.ids, entity.id],
        entities: { ...state.entities, [entity.id]: entity },
      })),

    update: (id, changes) =>
      set((state) => ({
        entities: {
          ...state.entities,
          [id]: { ...state.entities[id], ...changes },
        },
      })),

    remove: (id) =>
      set((state) => ({
        ids: state.ids.filter((i) => i !== id),
        entities: Object.fromEntries(
          Object.entries(state.entities).filter(([key]) => key !== id)
        ),
        selectedId: state.selectedId === id ? null : state.selectedId,
      })),

    setSelected: (id) => set({ selectedId: id }),

    getById: (id) => get().entities[id],

    getAll: () => get().ids.map((id) => get().entities[id]),
  }));
}

// Usage
interface User {
  id: string;
  name: string;
  email: string;
}

const useUserStore = createEntityStore<User>('users');
```

## Middleware

### Persist Middleware

```tsx
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface SettingsState {
  theme: 'light' | 'dark';
  language: string;
  setTheme: (theme: 'light' | 'dark') => void;
  setLanguage: (language: string) => void;
}

const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      theme: 'light',
      language: 'en',
      setTheme: (theme) => set({ theme }),
      setLanguage: (language) => set({ language }),
    }),
    {
      name: 'settings-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        theme: state.theme,
        language: state.language,
      }),
    }
  )
);
```

### DevTools Middleware

```tsx
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const useStore = create<State>()(
  devtools(
    (set) => ({
      // ... state and actions
    }),
    { name: 'MyStore' }
  )
);
```

### Immer Middleware

```tsx
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';

interface TodoState {
  todos: { id: string; text: string; done: boolean }[];
  addTodo: (text: string) => void;
  toggleTodo: (id: string) => void;
}

const useTodoStore = create<TodoState>()(
  immer((set) => ({
    todos: [],
    addTodo: (text) =>
      set((state) => {
        state.todos.push({
          id: crypto.randomUUID(),
          text,
          done: false,
        });
      }),
    toggleTodo: (id) =>
      set((state) => {
        const todo = state.todos.find((t) => t.id === id);
        if (todo) {
          todo.done = !todo.done;
        }
      }),
  }))
);
```

### Combined Middleware

```tsx
import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { immer } from 'zustand/middleware/immer';

const useStore = create<State>()(
  devtools(
    persist(
      immer((set) => ({
        // ... state and actions
      })),
      { name: 'app-storage' }
    ),
    { name: 'AppStore' }
  )
);
```

## Selectors

### Basic Selectors

```tsx
// ❌ Bad: Re-renders on any state change
function Component() {
  const store = useStore();
  return <div>{store.user.name}</div>;
}

// ✅ Good: Only re-renders when user.name changes
function Component() {
  const userName = useStore((state) => state.user.name);
  return <div>{userName}</div>;
}
```

### Shallow Comparison

```tsx
import { useShallow } from 'zustand/react/shallow';

// Select multiple values with shallow comparison
function Component() {
  const { user, products } = useStore(
    useShallow((state) => ({
      user: state.user,
      products: state.products,
    }))
  );

  return (
    <div>
      <span>{user.name}</span>
      <ProductList products={products} />
    </div>
  );
}
```

### Computed Selectors

```tsx
// Create reusable selectors
const selectCartTotal = (state: CartState) =>
  state.items.reduce((sum, item) => sum + item.price * item.quantity, 0);

const selectItemCount = (state: CartState) =>
  state.items.reduce((sum, item) => sum + item.quantity, 0);

// Usage
function CartSummary() {
  const total = useCartStore(selectCartTotal);
  const itemCount = useCartStore(selectItemCount);

  return (
    <div>
      <span>Items: {itemCount}</span>
      <span>Total: ${total}</span>
    </div>
  );
}
```

## Store Slices

Split large stores into slices.

```tsx
import { create, StateCreator } from 'zustand';

// User slice
interface UserSlice {
  user: User | null;
  setUser: (user: User | null) => void;
}

const createUserSlice: StateCreator<AppState, [], [], UserSlice> = (set) => ({
  user: null,
  setUser: (user) => set({ user }),
});

// Cart slice
interface CartSlice {
  items: CartItem[];
  addItem: (item: CartItem) => void;
  removeItem: (id: string) => void;
}

const createCartSlice: StateCreator<AppState, [], [], CartSlice> = (set) => ({
  items: [],
  addItem: (item) => set((state) => ({ items: [...state.items, item] })),
  removeItem: (id) =>
    set((state) => ({ items: state.items.filter((i) => i.id !== id) })),
});

// Combined store
type AppState = UserSlice & CartSlice;

const useAppStore = create<AppState>()((...a) => ({
  ...createUserSlice(...a),
  ...createCartSlice(...a),
}));
```

## Best Practices

1. **Use selectors** - Always select specific state to prevent unnecessary re-renders
2. **Keep stores focused** - One store per domain/feature
3. **Use middleware** - persist, devtools, immer as needed
4. **Avoid over-normalization** - Keep state shape simple
5. **Colocate selectors** - Define reusable selectors near store
6. **TypeScript first** - Full type safety with create<State>()
