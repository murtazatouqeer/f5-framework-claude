---
name: vue-pinia-advanced
description: Advanced Pinia patterns and plugins
applies_to: vue
---

# Advanced Pinia Patterns

## Plugins

### Creating a Plugin

```typescript
// plugins/piniaLogger.ts
import { PiniaPluginContext } from 'pinia';

export function piniaLogger({ store }: PiniaPluginContext) {
  // Subscribe to state changes
  store.$subscribe((mutation, state) => {
    console.log(`[${store.$id}] ${mutation.type}`, state);
  });

  // Subscribe to actions
  store.$onAction(({ name, args, after, onError }) => {
    const startTime = Date.now();

    after((result) => {
      console.log(
        `[${store.$id}] ${name}() took ${Date.now() - startTime}ms`,
        { args, result }
      );
    });

    onError((error) => {
      console.error(`[${store.$id}] ${name}() failed`, { args, error });
    });
  });
}

// main.ts
const pinia = createPinia();
pinia.use(piniaLogger);
```

### Persistence Plugin

```typescript
// plugins/piniaPersist.ts
import { PiniaPluginContext } from 'pinia';

interface PersistOptions {
  key?: string;
  storage?: Storage;
  paths?: string[];
}

declare module 'pinia' {
  export interface DefineStoreOptionsBase<S, Store> {
    persist?: boolean | PersistOptions;
  }
}

export function piniaPersist({ store, options }: PiniaPluginContext) {
  const persistOptions = (options as any).persist;

  if (!persistOptions) return;

  const {
    key = store.$id,
    storage = localStorage,
    paths,
  } = typeof persistOptions === 'object' ? persistOptions : {};

  // Restore state
  const savedState = storage.getItem(key);
  if (savedState) {
    store.$patch(JSON.parse(savedState));
  }

  // Subscribe to changes
  store.$subscribe((_, state) => {
    const toStore = paths
      ? paths.reduce((acc, path) => {
          acc[path] = (state as any)[path];
          return acc;
        }, {} as Record<string, unknown>)
      : state;

    storage.setItem(key, JSON.stringify(toStore));
  });
}

// Usage in store
export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    user: null,
  }),
  persist: {
    paths: ['token'],
    storage: localStorage,
  },
});
```

### Adding Properties to Stores

```typescript
// plugins/piniaRouter.ts
import type { Router } from 'vue-router';
import { PiniaPluginContext } from 'pinia';

declare module 'pinia' {
  export interface PiniaCustomProperties {
    router: Router;
  }
}

export function piniaRouter(router: Router) {
  return ({ store }: PiniaPluginContext) => {
    store.router = router;
  };
}

// main.ts
const router = createRouter({ ... });
pinia.use(piniaRouter(router));

// In store
export const useAuthStore = defineStore('auth', () => {
  async function logout() {
    // Access router via this
    this.router.push('/login');
  }
});
```

## Advanced Store Patterns

### Factory Stores

```typescript
// stores/createEntityStore.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from '@/lib/api';

interface Entity {
  id: string;
  [key: string]: unknown;
}

export function createEntityStore<T extends Entity>(
  storeName: string,
  endpoint: string
) {
  return defineStore(storeName, () => {
    const items = ref<T[]>([]);
    const isLoading = ref(false);
    const error = ref<Error | null>(null);

    const byId = computed(() => {
      return (id: string) => items.value.find((item) => item.id === id);
    });

    async function fetchAll() {
      isLoading.value = true;
      try {
        const response = await api.get<T[]>(endpoint);
        items.value = response.data;
      } catch (e) {
        error.value = e as Error;
      } finally {
        isLoading.value = false;
      }
    }

    async function create(data: Omit<T, 'id'>) {
      const response = await api.post<T>(endpoint, data);
      items.value.push(response.data);
      return response.data;
    }

    async function update(id: string, data: Partial<T>) {
      const response = await api.patch<T>(`${endpoint}/${id}`, data);
      const index = items.value.findIndex((item) => item.id === id);
      if (index !== -1) {
        items.value[index] = response.data;
      }
      return response.data;
    }

    async function remove(id: string) {
      await api.delete(`${endpoint}/${id}`);
      items.value = items.value.filter((item) => item.id !== id);
    }

    return {
      items,
      isLoading,
      error,
      byId,
      fetchAll,
      create,
      update,
      remove,
    };
  });
}

// Usage
interface Product {
  id: string;
  name: string;
  price: number;
}

export const useProductStore = createEntityStore<Product>('products', '/api/products');
export const useCategoryStore = createEntityStore<Category>('categories', '/api/categories');
```

### Modular Store

```typescript
// stores/user/state.ts
export interface UserState {
  user: User | null;
  preferences: UserPreferences;
}

export const createInitialState = (): UserState => ({
  user: null,
  preferences: {
    theme: 'light',
    notifications: true,
  },
});

// stores/user/getters.ts
import type { UserState } from './state';

export const getters = {
  isLoggedIn: (state: UserState) => !!state.user,
  fullName: (state: UserState) => {
    if (!state.user) return '';
    return `${state.user.firstName} ${state.user.lastName}`;
  },
};

// stores/user/actions.ts
import type { UserState } from './state';
import { api } from '@/lib/api';

export const createActions = (state: UserState) => ({
  async login(email: string, password: string) {
    const response = await api.post('/auth/login', { email, password });
    state.user = response.data.user;
  },

  logout() {
    state.user = null;
  },

  updatePreferences(prefs: Partial<UserPreferences>) {
    state.preferences = { ...state.preferences, ...prefs };
  },
});

// stores/user/index.ts
import { defineStore } from 'pinia';
import { reactive, computed } from 'vue';
import { createInitialState } from './state';
import { getters } from './getters';
import { createActions } from './actions';

export const useUserStore = defineStore('user', () => {
  const state = reactive(createInitialState());

  const computedGetters = {
    isLoggedIn: computed(() => getters.isLoggedIn(state)),
    fullName: computed(() => getters.fullName(state)),
  };

  const actions = createActions(state);

  return {
    ...state,
    ...computedGetters,
    ...actions,
  };
});
```

### Optimistic Updates

```typescript
// stores/useTodoStore.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { api } from '@/lib/api';

export const useTodoStore = defineStore('todos', () => {
  const todos = ref<Todo[]>([]);

  async function toggleTodo(id: string) {
    const todo = todos.value.find((t) => t.id === id);
    if (!todo) return;

    // Optimistic update
    const previousState = todo.completed;
    todo.completed = !previousState;

    try {
      await api.patch(`/todos/${id}`, { completed: todo.completed });
    } catch (error) {
      // Rollback on error
      todo.completed = previousState;
      throw error;
    }
  }

  async function deleteTodo(id: string) {
    const index = todos.value.findIndex((t) => t.id === id);
    if (index === -1) return;

    // Optimistic delete
    const [removed] = todos.value.splice(index, 1);

    try {
      await api.delete(`/todos/${id}`);
    } catch (error) {
      // Rollback on error
      todos.value.splice(index, 0, removed);
      throw error;
    }
  }

  return { todos, toggleTodo, deleteTodo };
});
```

## Testing Stores

```typescript
// stores/__tests__/useCounterStore.test.ts
import { describe, it, expect, beforeEach } from 'vitest';
import { setActivePinia, createPinia } from 'pinia';
import { useCounterStore } from '../useCounterStore';

describe('useCounterStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('initializes with count 0', () => {
    const store = useCounterStore();
    expect(store.count).toBe(0);
  });

  it('increments count', () => {
    const store = useCounterStore();
    store.increment();
    expect(store.count).toBe(1);
  });

  it('computes doubleCount correctly', () => {
    const store = useCounterStore();
    store.count = 5;
    expect(store.doubleCount).toBe(10);
  });
});
```

```typescript
// Testing with mocks
import { vi } from 'vitest';
import { createTestingPinia } from '@pinia/testing';

const wrapper = mount(MyComponent, {
  global: {
    plugins: [
      createTestingPinia({
        createSpy: vi.fn,
        initialState: {
          counter: { count: 10 },
        },
      }),
    ],
  },
});

const store = useCounterStore();
store.increment(); // Spy is called
expect(store.increment).toHaveBeenCalled();
```

## Best Practices

1. **Use plugins for cross-cutting concerns** - Logging, persistence
2. **Create factory stores for repetitive patterns** - CRUD operations
3. **Keep stores focused** - One domain per store
4. **Test stores in isolation** - Use createTestingPinia
5. **Use TypeScript** - Full type safety
6. **Implement optimistic updates** - Better UX
