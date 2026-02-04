---
name: vue-reactive-patterns
description: Vue reactivity patterns and best practices
applies_to: vue
---

# Vue Reactivity Patterns

## Overview

Vue's reactivity system tracks dependencies and updates the DOM efficiently.
Understanding these patterns helps write performant applications.

## Core Reactivity APIs

### ref vs reactive

```typescript
import { ref, reactive, isRef, isReactive, toRaw } from 'vue';

// ref - for primitives and single values
const count = ref(0);
const message = ref('Hello');
const user = ref<User | null>(null);

// Access with .value
count.value++;
message.value = 'World';

// reactive - for objects
const state = reactive({
  count: 0,
  items: [] as string[],
  nested: { value: 1 },
});

// Direct property access
state.count++;
state.items.push('new item');

// Type guards
isRef(count); // true
isReactive(state); // true

// Get raw (non-reactive) value
const rawState = toRaw(state);
```

### When to Use Which

```typescript
// Use ref when:
// 1. Working with primitives
const isLoading = ref(false);
const total = ref(0);

// 2. You need to replace the entire value
const selectedUser = ref<User | null>(null);
selectedUser.value = newUser; // Replaces entire object

// 3. Passing to functions (keeps reactivity)
function processValue(val: Ref<number>) {
  val.value++;
}

// Use reactive when:
// 1. Working with objects you'll mutate
const form = reactive({
  name: '',
  email: '',
});
form.name = 'John';

// 2. You have deeply nested state
const appState = reactive({
  user: { profile: { settings: {} } },
});

// CAUTION: reactive loses reactivity on destructure
const { count } = reactive({ count: 0 }); // NOT reactive!
```

### shallowRef and shallowReactive

```typescript
import { shallowRef, shallowReactive, triggerRef } from 'vue';

// shallowRef - only .value change is tracked
const largeObject = shallowRef({ items: [] as Item[] });

// This WON'T trigger updates
largeObject.value.items.push(newItem);

// This WILL trigger updates
largeObject.value = { items: [...largeObject.value.items, newItem] };

// Or manually trigger
largeObject.value.items.push(newItem);
triggerRef(largeObject);

// shallowReactive - only first-level properties are reactive
const state = shallowReactive({
  nested: { value: 0 }, // NOT reactive
});

state.nested = { value: 1 }; // Triggers update
state.nested.value = 2; // Does NOT trigger update
```

### toRef and toRefs

```typescript
import { reactive, toRef, toRefs } from 'vue';

const state = reactive({
  firstName: 'John',
  lastName: 'Doe',
  age: 30,
});

// toRef - create ref from reactive property
const firstNameRef = toRef(state, 'firstName');
firstNameRef.value = 'Jane'; // Also updates state.firstName

// toRefs - create refs from all properties
const { firstName, lastName, age } = toRefs(state);

// Now all are reactive refs
firstName.value = 'Jane'; // Updates state.firstName
```

## Computed Patterns

### Basic Computed

```typescript
import { ref, computed } from 'vue';

const items = ref<Item[]>([]);
const filter = ref('');

// Read-only computed
const filteredItems = computed(() => {
  if (!filter.value) return items.value;
  return items.value.filter((item) =>
    item.name.toLowerCase().includes(filter.value.toLowerCase())
  );
});

const total = computed(() =>
  items.value.reduce((sum, item) => sum + item.price, 0)
);
```

### Writable Computed

```typescript
import { ref, computed } from 'vue';

const firstName = ref('John');
const lastName = ref('Doe');

const fullName = computed({
  get() {
    return `${firstName.value} ${lastName.value}`;
  },
  set(value: string) {
    const [first, ...rest] = value.split(' ');
    firstName.value = first;
    lastName.value = rest.join(' ');
  },
});

fullName.value = 'Jane Smith'; // Sets both firstName and lastName
```

### Computed with Getter

```typescript
const users = ref<User[]>([]);

// Return a getter function
const userById = computed(() => {
  return (id: string) => users.value.find((u) => u.id === id);
});

// Usage
const user = userById.value('123');
```

## Watch Patterns

### Basic Watch

```typescript
import { ref, watch } from 'vue';

const query = ref('');

// Watch single source
watch(query, (newValue, oldValue) => {
  console.log(`Changed from ${oldValue} to ${newValue}`);
});

// With options
watch(
  query,
  (value) => {
    fetchResults(value);
  },
  {
    immediate: true, // Run on mount
    deep: true, // Deep watch objects
    flush: 'post', // After DOM update
    once: true, // Only trigger once
  }
);
```

### Watch Multiple Sources

```typescript
const firstName = ref('');
const lastName = ref('');

watch([firstName, lastName], ([newFirst, newLast], [oldFirst, oldLast]) => {
  console.log('Names changed');
});
```

### Watch Getter

```typescript
const user = ref<User | null>(null);

// Watch a computed value
watch(
  () => user.value?.id,
  (newId) => {
    if (newId) {
      loadUserData(newId);
    }
  }
);
```

### watchEffect

```typescript
import { ref, watchEffect } from 'vue';

const userId = ref('');

// Auto-tracks all reactive dependencies
watchEffect(() => {
  if (userId.value) {
    fetchUser(userId.value);
  }
});

// With cleanup
watchEffect((onCleanup) => {
  const controller = new AbortController();

  fetchData(userId.value, { signal: controller.signal });

  onCleanup(() => {
    controller.abort();
  });
});
```

### Stopping Watchers

```typescript
const stop = watch(source, callback);
const stopEffect = watchEffect(() => {});

// Later, stop watching
stop();
stopEffect();
```

## Advanced Patterns

### Debounced Watch

```typescript
import { ref, watch } from 'vue';

const searchQuery = ref('');

let timeout: ReturnType<typeof setTimeout>;

watch(searchQuery, (value) => {
  clearTimeout(timeout);
  timeout = setTimeout(() => {
    performSearch(value);
  }, 300);
});

// Or use watchDebounced from @vueuse/core
import { watchDebounced } from '@vueuse/core';

watchDebounced(
  searchQuery,
  (value) => performSearch(value),
  { debounce: 300 }
);
```

### Conditional Reactivity

```typescript
import { ref, computed, effectScope } from 'vue';

// Create isolated effect scope
const scope = effectScope();

scope.run(() => {
  const count = ref(0);
  const doubled = computed(() => count.value * 2);

  watch(count, (val) => console.log(val));
});

// Stop all effects in scope
scope.stop();
```

### Custom Refs

```typescript
import { customRef } from 'vue';

function useDebouncedRef<T>(value: T, delay = 200) {
  let timeout: ReturnType<typeof setTimeout>;

  return customRef<T>((track, trigger) => {
    return {
      get() {
        track();
        return value;
      },
      set(newValue) {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          value = newValue;
          trigger();
        }, delay);
      },
    };
  });
}

// Usage
const searchTerm = useDebouncedRef('', 300);
```

## Performance Tips

1. **Use shallowRef for large objects** - Avoid deep reactivity
2. **Avoid unnecessary watchers** - Use computed when possible
3. **Clean up watchers** - Stop when no longer needed
4. **Use markRaw for non-reactive data** - Skip reactivity
5. **Batch updates with nextTick** - Reduce re-renders
