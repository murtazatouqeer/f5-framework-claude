---
name: vue-async-composables
description: Async composable patterns for data fetching
applies_to: vue
---

# Async Composables

## Overview

Async composables handle data fetching, caching, and state management
for asynchronous operations in Vue applications.

## Basic Async Composable

```typescript
// composables/useAsync.ts
import { ref, shallowRef, computed, type Ref, type ShallowRef } from 'vue';

interface UseAsyncOptions<T> {
  immediate?: boolean;
  initialData?: T;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseAsyncReturn<T, Args extends unknown[]> {
  data: ShallowRef<T | undefined>;
  error: ShallowRef<Error | null>;
  isLoading: Ref<boolean>;
  isSuccess: Ref<boolean>;
  isError: Ref<boolean>;
  execute: (...args: Args) => Promise<T | undefined>;
  reset: () => void;
}

export function useAsync<T, Args extends unknown[] = []>(
  asyncFn: (...args: Args) => Promise<T>,
  options: UseAsyncOptions<T> = {}
): UseAsyncReturn<T, Args> {
  const {
    immediate = false,
    initialData,
    onSuccess,
    onError,
  } = options;

  const data = shallowRef<T | undefined>(initialData);
  const error = shallowRef<Error | null>(null);
  const isLoading = ref(false);
  const isSuccess = ref(false);
  const isError = ref(false);

  async function execute(...args: Args): Promise<T | undefined> {
    isLoading.value = true;
    isError.value = false;
    error.value = null;

    try {
      const result = await asyncFn(...args);
      data.value = result;
      isSuccess.value = true;
      onSuccess?.(result);
      return result;
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      isError.value = true;
      isSuccess.value = false;
      onError?.(err);
      return undefined;
    } finally {
      isLoading.value = false;
    }
  }

  function reset() {
    data.value = initialData;
    error.value = null;
    isLoading.value = false;
    isSuccess.value = false;
    isError.value = false;
  }

  if (immediate) {
    execute(...([] as unknown as Args));
  }

  return {
    data,
    error,
    isLoading,
    isSuccess,
    isError,
    execute,
    reset,
  };
}
```

## Data Fetching Composable

```typescript
// composables/useFetch.ts
import { ref, shallowRef, watch, type Ref } from 'vue';

interface UseFetchOptions<T> {
  immediate?: boolean;
  refetch?: boolean;
  initialData?: T;
  transform?: (data: unknown) => T;
}

export function useFetch<T>(
  url: Ref<string> | string,
  options: UseFetchOptions<T> = {}
) {
  const {
    immediate = true,
    refetch = false,
    initialData,
    transform,
  } = options;

  const data = shallowRef<T | undefined>(initialData);
  const error = shallowRef<Error | null>(null);
  const isLoading = ref(false);

  const controller = ref<AbortController | null>(null);

  async function execute() {
    // Abort previous request
    if (controller.value) {
      controller.value.abort();
    }
    controller.value = new AbortController();

    isLoading.value = true;
    error.value = null;

    try {
      const urlValue = typeof url === 'string' ? url : url.value;
      const response = await fetch(urlValue, {
        signal: controller.value.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      let result = await response.json();

      if (transform) {
        result = transform(result);
      }

      data.value = result;
    } catch (e) {
      if ((e as Error).name !== 'AbortError') {
        error.value = e instanceof Error ? e : new Error(String(e));
      }
    } finally {
      isLoading.value = false;
    }
  }

  function abort() {
    controller.value?.abort();
  }

  // Auto-fetch on mount
  if (immediate) {
    execute();
  }

  // Refetch on URL change
  if (refetch && typeof url !== 'string') {
    watch(url, execute);
  }

  return {
    data,
    error,
    isLoading,
    execute,
    abort,
  };
}
```

## Paginated Data Composable

```typescript
// composables/usePaginatedData.ts
import { ref, computed, watch, type Ref } from 'vue';
import { api } from '@/lib/api';

interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

interface UsePaginatedDataOptions {
  pageSize?: number;
  immediate?: boolean;
}

export function usePaginatedData<T>(
  endpoint: string | Ref<string>,
  options: UsePaginatedDataOptions = {}
) {
  const { pageSize = 20, immediate = true } = options;

  const items = ref<T[]>([]);
  const meta = ref<PaginationMeta>({
    page: 1,
    pageSize,
    total: 0,
    totalPages: 0,
  });
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  const hasNextPage = computed(() => meta.value.page < meta.value.totalPages);
  const hasPrevPage = computed(() => meta.value.page > 1);
  const isEmpty = computed(() => !isLoading.value && items.value.length === 0);

  async function fetchPage(page: number) {
    isLoading.value = true;
    error.value = null;

    try {
      const url = typeof endpoint === 'string' ? endpoint : endpoint.value;
      const response = await api.get<{
        items: T[];
        meta: PaginationMeta;
      }>(url, {
        params: { page, limit: pageSize },
      });

      items.value = response.data.items;
      meta.value = response.data.meta;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
    } finally {
      isLoading.value = false;
    }
  }

  function nextPage() {
    if (hasNextPage.value) {
      fetchPage(meta.value.page + 1);
    }
  }

  function prevPage() {
    if (hasPrevPage.value) {
      fetchPage(meta.value.page - 1);
    }
  }

  function goToPage(page: number) {
    if (page >= 1 && page <= meta.value.totalPages) {
      fetchPage(page);
    }
  }

  function refresh() {
    fetchPage(1);
  }

  if (immediate) {
    fetchPage(1);
  }

  // Refetch when endpoint changes
  if (typeof endpoint !== 'string') {
    watch(endpoint, () => fetchPage(1));
  }

  return {
    items,
    meta,
    isLoading,
    error,
    hasNextPage,
    hasPrevPage,
    isEmpty,
    fetchPage,
    nextPage,
    prevPage,
    goToPage,
    refresh,
  };
}
```

## Infinite Scroll Composable

```typescript
// composables/useInfiniteScroll.ts
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { api } from '@/lib/api';

interface UseInfiniteScrollOptions {
  pageSize?: number;
  threshold?: number;
}

export function useInfiniteScroll<T>(
  endpoint: string,
  options: UseInfiniteScrollOptions = {}
) {
  const { pageSize = 20, threshold = 200 } = options;

  const items = ref<T[]>([]);
  const page = ref(1);
  const hasMore = ref(true);
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  const isEmpty = computed(() => !isLoading.value && items.value.length === 0);

  async function loadMore() {
    if (isLoading.value || !hasMore.value) return;

    isLoading.value = true;
    error.value = null;

    try {
      const response = await api.get<{
        items: T[];
        meta: { hasMore: boolean };
      }>(endpoint, {
        params: { page: page.value, limit: pageSize },
      });

      items.value.push(...response.data.items);
      hasMore.value = response.data.meta.hasMore;
      page.value++;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
    } finally {
      isLoading.value = false;
    }
  }

  function reset() {
    items.value = [];
    page.value = 1;
    hasMore.value = true;
    error.value = null;
  }

  function refresh() {
    reset();
    loadMore();
  }

  // Scroll handler
  function handleScroll() {
    const scrollHeight = document.documentElement.scrollHeight;
    const scrollTop = document.documentElement.scrollTop;
    const clientHeight = document.documentElement.clientHeight;

    if (scrollHeight - scrollTop - clientHeight < threshold) {
      loadMore();
    }
  }

  onMounted(() => {
    window.addEventListener('scroll', handleScroll);
    loadMore(); // Initial load
  });

  onUnmounted(() => {
    window.removeEventListener('scroll', handleScroll);
  });

  return {
    items,
    isLoading,
    error,
    hasMore,
    isEmpty,
    loadMore,
    reset,
    refresh,
  };
}
```

## CRUD Operations Composable

```typescript
// composables/useCrud.ts
import { ref, shallowRef, computed } from 'vue';
import { api } from '@/lib/api';

interface UseCrudOptions {
  endpoint: string;
  idField?: string;
}

export function useCrud<T extends { id: string }>(options: UseCrudOptions) {
  const { endpoint, idField = 'id' } = options;

  const items = ref<T[]>([]);
  const currentItem = shallowRef<T | null>(null);
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  const isEmpty = computed(() => items.value.length === 0);

  async function fetchAll() {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await api.get<T[]>(endpoint);
      items.value = response.data;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchOne(id: string) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await api.get<T>(`${endpoint}/${id}`);
      currentItem.value = response.data;
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  async function create(data: Omit<T, 'id'>) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await api.post<T>(endpoint, data);
      items.value.unshift(response.data);
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  async function update(id: string, data: Partial<T>) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await api.patch<T>(`${endpoint}/${id}`, data);
      const index = items.value.findIndex((item) => item[idField] === id);
      if (index !== -1) {
        items.value[index] = response.data;
      }
      if (currentItem.value?.[idField] === id) {
        currentItem.value = response.data;
      }
      return response.data;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
      return null;
    } finally {
      isLoading.value = false;
    }
  }

  async function remove(id: string) {
    isLoading.value = true;
    error.value = null;

    try {
      await api.delete(`${endpoint}/${id}`);
      items.value = items.value.filter((item) => item[idField] !== id);
      if (currentItem.value?.[idField] === id) {
        currentItem.value = null;
      }
      return true;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    items,
    currentItem,
    isLoading,
    error,
    isEmpty,
    fetchAll,
    fetchOne,
    create,
    update,
    remove,
  };
}
```

## Best Practices

1. **Use shallowRef for large data** - Avoid deep reactivity
2. **Handle abort/cancel** - Cancel pending requests
3. **Implement error handling** - User feedback
4. **Support retry** - Network resilience
5. **Add loading states** - UI feedback
6. **Cache when appropriate** - Reduce requests
