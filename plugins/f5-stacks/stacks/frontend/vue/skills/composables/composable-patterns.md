---
name: vue-composable-patterns
description: Vue composable patterns and best practices
applies_to: vue
---

# Vue Composable Patterns

## Overview

Composables are functions that encapsulate and reuse stateful logic.
They follow the `use` prefix convention and leverage the Composition API.

## Basic Structure

```typescript
// composables/useFeatureName.ts
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import type { Ref, ComputedRef } from 'vue';

// Types
interface UseFeatureOptions {
  initialValue?: string;
  debounce?: number;
}

interface UseFeatureReturn {
  value: Ref<string>;
  computed: ComputedRef<string>;
  method: () => void;
}

/**
 * Description of what this composable does.
 *
 * @param options - Configuration options
 * @returns Reactive state and methods
 *
 * @example
 * ```vue
 * const { value, method } = useFeature({ initialValue: 'test' });
 * ```
 */
export function useFeature(
  options: UseFeatureOptions = {}
): UseFeatureReturn {
  const { initialValue = '', debounce = 300 } = options;

  // State
  const value = ref(initialValue);

  // Computed
  const computed = computed(() => value.value.toUpperCase());

  // Methods
  function method() {
    value.value = '';
  }

  // Lifecycle
  onMounted(() => {
    // Setup
  });

  onUnmounted(() => {
    // Cleanup
  });

  return {
    value,
    computed,
    method,
  };
}
```

## Common Patterns

### State with Actions

```typescript
// composables/useCounter.ts
import { ref, computed } from 'vue';

export function useCounter(initial = 0, options: { min?: number; max?: number } = {}) {
  const { min = -Infinity, max = Infinity } = options;

  const count = ref(initial);

  const atMin = computed(() => count.value <= min);
  const atMax = computed(() => count.value >= max);

  function increment() {
    if (count.value < max) {
      count.value++;
    }
  }

  function decrement() {
    if (count.value > min) {
      count.value--;
    }
  }

  function set(value: number) {
    count.value = Math.max(min, Math.min(max, value));
  }

  function reset() {
    count.value = initial;
  }

  return {
    count,
    atMin,
    atMax,
    increment,
    decrement,
    set,
    reset,
  };
}
```

### Toggle State

```typescript
// composables/useToggle.ts
import { ref, type Ref } from 'vue';

export function useToggle(
  initialValue = false
): [Ref<boolean>, (value?: boolean) => void] {
  const state = ref(initialValue);

  function toggle(value?: boolean) {
    state.value = value !== undefined ? value : !state.value;
  }

  return [state, toggle];
}

// Usage
// const [isOpen, toggleOpen] = useToggle();
// toggleOpen();      // Toggle
// toggleOpen(true);  // Set to true
// toggleOpen(false); // Set to false
```

### Async Data

```typescript
// composables/useAsyncData.ts
import { ref, shallowRef, type Ref, type ShallowRef } from 'vue';

interface UseAsyncDataReturn<T> {
  data: ShallowRef<T | undefined>;
  error: ShallowRef<Error | null>;
  isLoading: Ref<boolean>;
  isSuccess: Ref<boolean>;
  isError: Ref<boolean>;
  execute: (...args: unknown[]) => Promise<T | undefined>;
  reset: () => void;
}

export function useAsyncData<T>(
  asyncFn: (...args: unknown[]) => Promise<T>,
  options: { immediate?: boolean } = {}
): UseAsyncDataReturn<T> {
  const { immediate = false } = options;

  const data = shallowRef<T | undefined>(undefined);
  const error = shallowRef<Error | null>(null);
  const isLoading = ref(false);
  const isSuccess = ref(false);
  const isError = ref(false);

  async function execute(...args: unknown[]): Promise<T | undefined> {
    isLoading.value = true;
    isSuccess.value = false;
    isError.value = false;
    error.value = null;

    try {
      const result = await asyncFn(...args);
      data.value = result;
      isSuccess.value = true;
      return result;
    } catch (e) {
      error.value = e instanceof Error ? e : new Error(String(e));
      isError.value = true;
      return undefined;
    } finally {
      isLoading.value = false;
    }
  }

  function reset() {
    data.value = undefined;
    error.value = null;
    isLoading.value = false;
    isSuccess.value = false;
    isError.value = false;
  }

  if (immediate) {
    execute();
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

### Event Listener

```typescript
// composables/useEventListener.ts
import { onMounted, onUnmounted, unref, watch, type Ref } from 'vue';

type MaybeRef<T> = T | Ref<T>;
type EventTarget = Window | Document | HTMLElement | null;

export function useEventListener<K extends keyof WindowEventMap>(
  target: MaybeRef<EventTarget>,
  event: K,
  handler: (event: WindowEventMap[K]) => void,
  options?: AddEventListenerOptions
) {
  const add = (el: EventTarget) => {
    el?.addEventListener(event, handler as EventListener, options);
  };

  const remove = (el: EventTarget) => {
    el?.removeEventListener(event, handler as EventListener, options);
  };

  onMounted(() => {
    add(unref(target));
  });

  onUnmounted(() => {
    remove(unref(target));
  });

  // Handle reactive target
  watch(
    () => unref(target),
    (newEl, oldEl) => {
      remove(oldEl);
      add(newEl);
    }
  );
}
```

### Local Storage

```typescript
// composables/useLocalStorage.ts
import { ref, watch, type Ref } from 'vue';

export function useLocalStorage<T>(
  key: string,
  defaultValue: T
): { data: Ref<T>; remove: () => void } {
  // Read initial value
  const stored = localStorage.getItem(key);
  const data = ref<T>(stored ? JSON.parse(stored) : defaultValue) as Ref<T>;

  // Sync to localStorage
  watch(
    data,
    (newValue) => {
      if (newValue === null || newValue === undefined) {
        localStorage.removeItem(key);
      } else {
        localStorage.setItem(key, JSON.stringify(newValue));
      }
    },
    { deep: true }
  );

  // Listen for changes in other tabs
  const handler = (e: StorageEvent) => {
    if (e.key === key) {
      data.value = e.newValue ? JSON.parse(e.newValue) : defaultValue;
    }
  };

  window.addEventListener('storage', handler);

  function remove() {
    localStorage.removeItem(key);
    data.value = defaultValue;
  }

  return { data, remove };
}
```

### Debounce

```typescript
// composables/useDebounce.ts
import { ref, watch, type Ref } from 'vue';

export function useDebounce<T>(value: Ref<T>, delay = 300): Ref<T> {
  const debouncedValue = ref(value.value) as Ref<T>;
  let timeout: ReturnType<typeof setTimeout>;

  watch(value, (newValue) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      debouncedValue.value = newValue;
    }, delay);
  });

  return debouncedValue;
}

// Debounced function version
export function useDebounceFn<T extends (...args: unknown[]) => unknown>(
  fn: T,
  delay = 300
): T {
  let timeout: ReturnType<typeof setTimeout>;

  return ((...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => fn(...args), delay);
  }) as T;
}
```

### Window Size

```typescript
// composables/useWindowSize.ts
import { ref, onMounted, onUnmounted } from 'vue';

export function useWindowSize() {
  const width = ref(window.innerWidth);
  const height = ref(window.innerHeight);

  function update() {
    width.value = window.innerWidth;
    height.value = window.innerHeight;
  }

  onMounted(() => {
    window.addEventListener('resize', update);
  });

  onUnmounted(() => {
    window.removeEventListener('resize', update);
  });

  return { width, height };
}
```

### Click Outside

```typescript
// composables/useClickOutside.ts
import { onMounted, onUnmounted, type Ref } from 'vue';

export function useClickOutside(
  elementRef: Ref<HTMLElement | null>,
  callback: () => void
) {
  function handler(event: MouseEvent) {
    const el = elementRef.value;
    if (el && !el.contains(event.target as Node)) {
      callback();
    }
  }

  onMounted(() => {
    document.addEventListener('click', handler);
  });

  onUnmounted(() => {
    document.removeEventListener('click', handler);
  });
}
```

## Composable Composition

```typescript
// composables/useSearch.ts
import { ref, watch } from 'vue';
import { useDebounce } from './useDebounce';
import { useAsyncData } from './useAsyncData';
import { api } from '@/lib/api';

export function useSearch<T>(endpoint: string) {
  const query = ref('');
  const debouncedQuery = useDebounce(query, 300);

  const { data: results, isLoading, error, execute } = useAsyncData<T[]>(
    async () => {
      if (!debouncedQuery.value) return [];
      const response = await api.get(endpoint, {
        params: { q: debouncedQuery.value },
      });
      return response.data;
    }
  );

  watch(debouncedQuery, () => {
    if (debouncedQuery.value.length >= 2) {
      execute();
    }
  });

  return {
    query,
    results,
    isLoading,
    error,
  };
}
```

## Best Practices

1. **Use `use` prefix** - Convention for composables
2. **Return reactive refs** - Not raw values
3. **Clean up in onUnmounted** - Prevent memory leaks
4. **Type everything** - Better DX
5. **Document with JSDoc** - Usage examples
6. **Keep focused** - Single responsibility
7. **Compose composables** - Build on each other
