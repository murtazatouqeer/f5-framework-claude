---
name: nuxt-composable-generator
description: Generates Nuxt 3 composables for reusable logic
applies_to: nuxt
---

# Nuxt Composable Generator Agent

## Purpose
Generate reusable Vue 3 composables for Nuxt applications following best practices for state management, data fetching, and logic encapsulation.

## Capabilities
- Data fetching composables
- State management composables
- Utility composables
- Auto-import integration

## Input Requirements
- Composable purpose
- State requirements
- API endpoints if data fetching
- Return interface

## Output Deliverables
1. Composable file (composables/)
2. Type definitions
3. Usage examples

## Generation Process

### 1. Analyze Requirements
```yaml
composable_analysis:
  - name: "useProducts"
  - type: "data-fetching"
  - api_endpoint: "/api/products"
  - features: ["pagination", "search", "crud"]
```

### 2. Generate Composable Patterns

#### Data Fetching Composable
```typescript
// composables/use{{Entities}}.ts
import type { {{Entity}}, PaginatedResponse, Create{{Entity}}Input } from '~/types';

interface Use{{Entities}}Options {
  immediate?: boolean;
  pageSize?: number;
}

export function use{{Entities}}(options: Use{{Entities}}Options = {}) {
  const { immediate = true, pageSize = 20 } = options;

  // State
  const items = ref<{{Entity}}[]>([]);
  const total = ref(0);
  const page = ref(1);
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  // Computed
  const totalPages = computed(() => Math.ceil(total.value / pageSize));
  const hasMore = computed(() => page.value < totalPages.value);
  const isEmpty = computed(() => !isLoading.value && items.value.length === 0);

  // Fetch list
  async function fetch(pageNum = 1) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await $fetch<PaginatedResponse<{{Entity}}>>('/api/{{entities}}', {
        query: { page: pageNum, limit: pageSize },
      });

      items.value = response.items;
      total.value = response.total;
      page.value = pageNum;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch');
    } finally {
      isLoading.value = false;
    }
  }

  // Load more (infinite scroll)
  async function loadMore() {
    if (!hasMore.value || isLoading.value) return;

    isLoading.value = true;
    try {
      const response = await $fetch<PaginatedResponse<{{Entity}}>>('/api/{{entities}}', {
        query: { page: page.value + 1, limit: pageSize },
      });

      items.value.push(...response.items);
      page.value += 1;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to load more');
    } finally {
      isLoading.value = false;
    }
  }

  // Create
  async function create(input: Create{{Entity}}Input) {
    const item = await $fetch<{{Entity}}>('/api/{{entities}}', {
      method: 'POST',
      body: input,
    });

    items.value.unshift(item);
    total.value += 1;
    return item;
  }

  // Update
  async function update(id: string, input: Partial<{{Entity}}>) {
    const updated = await $fetch<{{Entity}}>(`/api/{{entities}}/${id}`, {
      method: 'PUT',
      body: input,
    });

    const index = items.value.findIndex((item) => item.id === id);
    if (index !== -1) {
      items.value[index] = updated;
    }
    return updated;
  }

  // Delete
  async function remove(id: string) {
    await $fetch(`/api/{{entities}}/${id}`, { method: 'DELETE' });

    items.value = items.value.filter((item) => item.id !== id);
    total.value -= 1;
  }

  // Refresh
  function refresh() {
    return fetch(page.value);
  }

  // Initialize
  if (immediate) {
    fetch();
  }

  return {
    // State (readonly)
    items: readonly(items),
    total: readonly(total),
    page: readonly(page),
    isLoading: readonly(isLoading),
    error: readonly(error),
    // Computed
    totalPages,
    hasMore,
    isEmpty,
    // Actions
    fetch,
    loadMore,
    create,
    update,
    remove,
    refresh,
  };
}
```

#### Single Resource Composable
```typescript
// composables/use{{Entity}}.ts
import type { {{Entity}} } from '~/types';

export function use{{Entity}}(id: MaybeRefOrGetter<string>) {
  const resolvedId = toRef(id);

  const { data, pending, error, refresh } = useFetch<{{Entity}}>(
    () => `/api/{{entities}}/${resolvedId.value}`,
    {
      key: `{{entity}}-${resolvedId.value}`,
      watch: [resolvedId],
    }
  );

  const item = computed(() => data.value);

  return {
    item,
    isLoading: pending,
    error,
    refresh,
  };
}
```

#### State Composable
```typescript
// composables/useAuth.ts
interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export function useAuth() {
  const user = useState<User | null>('auth-user', () => null);
  const isAuthenticated = computed(() => !!user.value);

  async function login(email: string, password: string) {
    const data = await $fetch<{ user: User; token: string }>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });

    user.value = data.user;
    return data;
  }

  async function logout() {
    await $fetch('/api/auth/logout', { method: 'POST' });
    user.value = null;
    navigateTo('/login');
  }

  async function fetchUser() {
    try {
      const data = await $fetch<User>('/api/auth/me');
      user.value = data;
    } catch {
      user.value = null;
    }
  }

  return {
    user: readonly(user),
    isAuthenticated,
    login,
    logout,
    fetchUser,
  };
}
```

#### Utility Composable
```typescript
// composables/useAsync.ts
export function useAsync<T>() {
  const isLoading = ref(false);
  const error = ref<Error | null>(null);
  const data = ref<T | null>(null);

  async function execute(fn: () => Promise<T>) {
    isLoading.value = true;
    error.value = null;

    try {
      data.value = await fn();
      return data.value;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Unknown error');
      throw error.value;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    isLoading: readonly(isLoading),
    error: readonly(error),
    data: readonly(data),
    execute,
  };
}
```

#### Modal/Dialog Composable
```typescript
// composables/useModal.ts
export function useModal<T = unknown>() {
  const isOpen = ref(false);
  const data = ref<T | null>(null);

  function open(payload?: T) {
    data.value = payload ?? null;
    isOpen.value = true;
  }

  function close() {
    isOpen.value = false;
    data.value = null;
  }

  function toggle() {
    isOpen.value = !isOpen.value;
  }

  return {
    isOpen: readonly(isOpen),
    data: readonly(data),
    open,
    close,
    toggle,
  };
}
```

## Directory Structure
```
composables/
├── use{{Entities}}.ts     # Collection operations
├── use{{Entity}}.ts       # Single resource
├── useAuth.ts             # Authentication
├── useAsync.ts            # Async utilities
├── useModal.ts            # Modal state
└── useLocalStorage.ts     # Local storage
```

## Quality Checklist
- [ ] TypeScript types defined
- [ ] Proper ref/computed usage
- [ ] Error handling included
- [ ] Loading states managed
- [ ] Return values documented
- [ ] Auto-import compatible
