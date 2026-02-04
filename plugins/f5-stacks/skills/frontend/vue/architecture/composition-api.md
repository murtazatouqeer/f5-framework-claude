---
name: vue-composition-api
description: Vue 3 Composition API patterns and best practices
applies_to: vue
---

# Vue 3 Composition API

## Overview

The Composition API provides a function-based way to organize component
logic, enabling better code reuse, TypeScript support, and logical grouping.

## Script Setup Syntax

The recommended syntax for Vue 3 components:

```vue
<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue';

// Everything here is exposed to template
const count = ref(0);
const doubleCount = computed(() => count.value * 2);

function increment() {
  count.value++;
}

onMounted(() => {
  console.log('Component mounted');
});
</script>

<template>
  <button @click="increment">{{ count }} ({{ doubleCount }})</button>
</template>
```

## Reactive State

### ref - For Primitives

```typescript
import { ref } from 'vue';

// Primitives
const count = ref(0);
const message = ref('Hello');
const isVisible = ref(true);

// Access/modify with .value
count.value++;
message.value = 'World';

// In template, .value is auto-unwrapped
// <span>{{ count }}</span>
```

### reactive - For Objects

```typescript
import { reactive } from 'vue';

// Objects/arrays
const state = reactive({
  user: null as User | null,
  items: [] as Item[],
  isLoading: false,
});

// Direct property access (no .value)
state.isLoading = true;
state.items.push(newItem);

// CAUTION: Don't destructure - loses reactivity
const { user } = state; // NOT reactive!
```

### shallowRef - For Large Objects

```typescript
import { shallowRef, triggerRef } from 'vue';

// Only .value change is reactive, not deep changes
const largeData = shallowRef<LargeDataset | null>(null);

// Replace entire value
largeData.value = newDataset;

// Manual trigger if mutating
largeData.value.items.push(item);
triggerRef(largeData); // Force update
```

### toRefs - Preserve Reactivity

```typescript
import { reactive, toRefs } from 'vue';

const state = reactive({
  firstName: 'John',
  lastName: 'Doe',
});

// Convert to refs for destructuring
const { firstName, lastName } = toRefs(state);

// Now these are refs
firstName.value = 'Jane';
```

## Computed Properties

### Basic Computed

```typescript
import { ref, computed } from 'vue';

const firstName = ref('John');
const lastName = ref('Doe');

// Read-only computed
const fullName = computed(() => {
  return `${firstName.value} ${lastName.value}`;
});
```

### Writable Computed

```typescript
const fullName = computed({
  get() {
    return `${firstName.value} ${lastName.value}`;
  },
  set(value: string) {
    const [first, last] = value.split(' ');
    firstName.value = first;
    lastName.value = last;
  },
});

// Usage
fullName.value = 'Jane Smith';
```

### Computed with Getter Function

```typescript
// Return a function for parameterized access
const userById = computed(() => {
  return (id: string) => users.value.find(u => u.id === id);
});

// Usage in template
// {{ userById(userId)?.name }}
```

## Watchers

### watch - Explicit Sources

```typescript
import { ref, watch } from 'vue';

const searchQuery = ref('');

// Watch single ref
watch(searchQuery, (newValue, oldValue) => {
  console.log(`Search changed from "${oldValue}" to "${newValue}"`);
});

// Watch with options
watch(
  searchQuery,
  async (query) => {
    if (query.length >= 3) {
      await performSearch(query);
    }
  },
  {
    immediate: true,    // Run immediately
    deep: true,         // Deep watch objects
    flush: 'post',      // After DOM update
  }
);

// Watch multiple sources
watch(
  [searchQuery, selectedCategory],
  ([newQuery, newCategory], [oldQuery, oldCategory]) => {
    // Both changed
  }
);

// Watch getter
watch(
  () => props.user?.id,
  (newId) => {
    if (newId) loadUserData(newId);
  }
);
```

### watchEffect - Auto Tracking

```typescript
import { ref, watchEffect } from 'vue';

const count = ref(0);
const enabled = ref(true);

// Automatically tracks all reactive dependencies
watchEffect(() => {
  if (enabled.value) {
    console.log(`Count is: ${count.value}`);
  }
});

// With cleanup
watchEffect((onCleanup) => {
  const controller = new AbortController();

  fetch(url.value, { signal: controller.signal });

  onCleanup(() => {
    controller.abort();
  });
});
```

### watchPostEffect / watchSyncEffect

```typescript
import { watchPostEffect, watchSyncEffect } from 'vue';

// Run after DOM update
watchPostEffect(() => {
  // DOM is updated here
});

// Run synchronously (use with caution)
watchSyncEffect(() => {
  // Runs immediately, synchronously
});
```

## Lifecycle Hooks

```typescript
import {
  onBeforeMount,
  onMounted,
  onBeforeUpdate,
  onUpdated,
  onBeforeUnmount,
  onUnmounted,
  onErrorCaptured,
  onActivated,
  onDeactivated,
} from 'vue';

// Before DOM mount
onBeforeMount(() => {
  console.log('Before mount');
});

// After DOM mount - most common
onMounted(() => {
  // Access DOM elements
  // Fetch initial data
  // Set up subscriptions
});

// Before reactive update
onBeforeUpdate(() => {
  // Cache DOM state before update
});

// After reactive update
onUpdated(() => {
  // DOM has been updated
});

// Before unmount
onBeforeUnmount(() => {
  // Start cleanup
});

// After unmount - cleanup
onUnmounted(() => {
  // Remove event listeners
  // Cancel subscriptions
  // Clear timers
});

// Error handling
onErrorCaptured((error, instance, info) => {
  console.error('Error captured:', error, info);
  return false; // Prevent propagation
});

// For <KeepAlive>
onActivated(() => {
  // Component activated from cache
});

onDeactivated(() => {
  // Component deactivated to cache
});
```

## Props and Emits

### TypeScript Props

```vue
<script setup lang="ts">
// Interface for props
interface Props {
  /** User to display */
  user: User;
  /** Show actions */
  showActions?: boolean;
  /** Custom class */
  class?: string;
}

// Define with defaults
const props = withDefaults(defineProps<Props>(), {
  showActions: true,
});

// Access
console.log(props.user.name);
</script>
```

### TypeScript Emits

```vue
<script setup lang="ts">
// Interface for emits
interface Emits {
  (e: 'update', value: string): void;
  (e: 'delete', id: string): void;
  (e: 'select', selected: boolean): void;
}

const emit = defineEmits<Emits>();

// Usage
function handleUpdate() {
  emit('update', 'new value');
}
</script>
```

## Provide/Inject

```typescript
// Parent component
import { provide, ref } from 'vue';

const theme = ref('dark');
const setTheme = (t: string) => { theme.value = t; };

provide('theme', { theme, setTheme });

// Or with InjectionKey for type safety
import type { InjectionKey, Ref } from 'vue';

interface ThemeContext {
  theme: Ref<string>;
  setTheme: (t: string) => void;
}

export const ThemeKey: InjectionKey<ThemeContext> = Symbol('theme');

provide(ThemeKey, { theme, setTheme });
```

```typescript
// Child component
import { inject } from 'vue';
import { ThemeKey } from './keys';

// With type safety
const themeContext = inject(ThemeKey);

if (themeContext) {
  console.log(themeContext.theme.value);
}

// With default
const theme = inject('theme', { theme: ref('light') });
```

## Template Refs

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue';

// Element ref
const inputRef = ref<HTMLInputElement | null>(null);

// Component ref
const modalRef = ref<InstanceType<typeof Modal> | null>(null);

onMounted(() => {
  inputRef.value?.focus();
  modalRef.value?.open();
});
</script>

<template>
  <input ref="inputRef" />
  <Modal ref="modalRef" />
</template>
```

## Expose

```vue
<script setup lang="ts">
import { ref } from 'vue';

const count = ref(0);

function reset() {
  count.value = 0;
}

function increment() {
  count.value++;
}

// Explicitly expose to parent
defineExpose({
  count,
  reset,
  // increment is NOT exposed
});
</script>
```

## Best Practices

1. **Use script setup** - Cleaner, better performance
2. **Prefer ref for primitives** - More explicit
3. **Use computed for derived state** - Automatic caching
4. **Clean up in onUnmounted** - Prevent memory leaks
5. **Type your props/emits** - Better DX and safety
6. **Extract to composables** - Reuse logic across components
