---
name: vue-composable
description: Vue composable function template
applies_to: vue
variables:
  - name: composableName
    description: Composable name (use prefix)
  - name: returnType
    description: Return type interface
---

# Vue Composable Template

## Basic Composable

```typescript
// ============================================================
// composables/{{composableName}}.ts
// ============================================================

import { ref, computed, readonly, type Ref, type ComputedRef } from 'vue';

// ------------------------------------------------------------
// Types
// ------------------------------------------------------------
interface {{composableName | pascal}}Options {
  // Add options here
  // initialValue?: string;
}

interface {{composableName | pascal}}Return {
  // Define return type
  // value: Readonly<Ref<string>>;
  // isValid: ComputedRef<boolean>;
  // setValue: (val: string) => void;
}

// ------------------------------------------------------------
// Composable
// ------------------------------------------------------------
export function {{composableName}}(
  options: {{composableName | pascal}}Options = {}
): {{composableName | pascal}}Return {
  // Destructure options with defaults
  // const { initialValue = '' } = options;

  // ------------------------------------------------------------
  // State
  // ------------------------------------------------------------
  // const value = ref(initialValue);
  // const error = ref<string | null>(null);

  // ------------------------------------------------------------
  // Computed
  // ------------------------------------------------------------
  // const isValid = computed(() => !error.value);

  // ------------------------------------------------------------
  // Methods
  // ------------------------------------------------------------
  // function setValue(val: string) {
  //   value.value = val;
  // }

  // ------------------------------------------------------------
  // Return
  // ------------------------------------------------------------
  return {
    // Expose readonly refs to prevent external mutation
    // value: readonly(value),
    // isValid,
    // setValue,
  };
}
```

## State Composable

```typescript
// ============================================================
// composables/useCounter.ts
// ============================================================

import { ref, computed, readonly, type Ref, type ComputedRef } from 'vue';

interface UseCounterOptions {
  initial?: number;
  min?: number;
  max?: number;
  step?: number;
}

interface UseCounterReturn {
  count: Readonly<Ref<number>>;
  double: ComputedRef<number>;
  isAtMin: ComputedRef<boolean>;
  isAtMax: ComputedRef<boolean>;
  increment: () => void;
  decrement: () => void;
  set: (value: number) => void;
  reset: () => void;
}

export function useCounter(options: UseCounterOptions = {}): UseCounterReturn {
  const { initial = 0, min = -Infinity, max = Infinity, step = 1 } = options;

  // State
  const count = ref(initial);

  // Computed
  const double = computed(() => count.value * 2);
  const isAtMin = computed(() => count.value <= min);
  const isAtMax = computed(() => count.value >= max);

  // Methods
  function increment() {
    const next = count.value + step;
    if (next <= max) {
      count.value = next;
    }
  }

  function decrement() {
    const next = count.value - step;
    if (next >= min) {
      count.value = next;
    }
  }

  function set(value: number) {
    count.value = Math.min(Math.max(value, min), max);
  }

  function reset() {
    count.value = initial;
  }

  return {
    count: readonly(count),
    double,
    isAtMin,
    isAtMax,
    increment,
    decrement,
    set,
    reset,
  };
}
```

## Async Composable

```typescript
// ============================================================
// composables/useFetch.ts
// ============================================================

import { ref, shallowRef, computed, readonly, type Ref, type ComputedRef } from 'vue';

interface UseFetchOptions<T> {
  immediate?: boolean;
  initialData?: T;
  onSuccess?: (data: T) => void;
  onError?: (error: Error) => void;
}

interface UseFetchReturn<T> {
  data: Readonly<Ref<T | null>>;
  error: Readonly<Ref<Error | null>>;
  isLoading: Readonly<Ref<boolean>>;
  isSuccess: ComputedRef<boolean>;
  isError: ComputedRef<boolean>;
  execute: () => Promise<void>;
  refresh: () => Promise<void>;
}

export function useFetch<T>(
  url: string | Ref<string>,
  options: UseFetchOptions<T> = {}
): UseFetchReturn<T> {
  const { immediate = true, initialData = null, onSuccess, onError } = options;

  // State
  const data = shallowRef<T | null>(initialData);
  const error = ref<Error | null>(null);
  const isLoading = ref(false);

  // Computed
  const isSuccess = computed(() => !isLoading.value && !error.value && data.value !== null);
  const isError = computed(() => !isLoading.value && error.value !== null);

  // Get URL value
  const getUrl = () => (typeof url === 'string' ? url : url.value);

  // Execute fetch
  async function execute() {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(getUrl());

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      data.value = result;
      onSuccess?.(result);
    } catch (e) {
      const err = e instanceof Error ? e : new Error(String(e));
      error.value = err;
      onError?.(err);
    } finally {
      isLoading.value = false;
    }
  }

  // Alias for execute
  const refresh = execute;

  // Execute immediately if option is set
  if (immediate) {
    execute();
  }

  return {
    data: readonly(data) as Readonly<Ref<T | null>>,
    error: readonly(error),
    isLoading: readonly(isLoading),
    isSuccess,
    isError,
    execute,
    refresh,
  };
}
```

## Event Composable

```typescript
// ============================================================
// composables/useEventListener.ts
// ============================================================

import { onMounted, onUnmounted, type Ref, unref } from 'vue';

type Target = Window | Document | HTMLElement | Ref<HTMLElement | null>;

export function useEventListener<K extends keyof WindowEventMap>(
  target: Target,
  event: K,
  handler: (event: WindowEventMap[K]) => void,
  options?: AddEventListenerOptions
): void {
  const getTarget = () => {
    const t = unref(target);
    return t;
  };

  onMounted(() => {
    const t = getTarget();
    if (t) {
      t.addEventListener(event, handler as EventListener, options);
    }
  });

  onUnmounted(() => {
    const t = getTarget();
    if (t) {
      t.removeEventListener(event, handler as EventListener, options);
    }
  });
}
```

## Usage

```vue
<script setup lang="ts">
import { useCounter } from '@/composables/useCounter';
import { useFetch } from '@/composables/useFetch';

// Counter composable
const { count, increment, decrement, isAtMax } = useCounter({
  initial: 0,
  max: 10,
});

// Fetch composable
interface User {
  id: number;
  name: string;
}

const { data: user, isLoading, error, refresh } = useFetch<User>(
  '/api/user/1',
  {
    immediate: true,
    onSuccess: (data) => console.log('Loaded:', data),
  }
);
</script>

<template>
  <div>
    <p>Count: {{ count }}</p>
    <button @click="decrement">-</button>
    <button @click="increment" :disabled="isAtMax">+</button>
  </div>

  <div v-if="isLoading">Loading...</div>
  <div v-else-if="error">Error: {{ error.message }}</div>
  <div v-else-if="user">
    <p>{{ user.name }}</p>
    <button @click="refresh">Refresh</button>
  </div>
</template>
```
