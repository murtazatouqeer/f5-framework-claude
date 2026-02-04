---
name: vue-optimization
description: Performance optimization techniques for Vue applications
applies_to: vue
---

# Vue Performance Optimization

## Overview

Optimizing Vue applications involves reducing unnecessary re-renders,
minimizing bundle size, and efficient data handling.

## Reactive Optimization

### Avoid Unnecessary Reactivity

```typescript
// ❌ Bad: Making large objects fully reactive
import { reactive } from 'vue';

const state = reactive({
  largeDataset: [...Array(10000)].map((_, i) => ({
    id: i,
    data: { /* complex nested data */ }
  }))
});

// ✅ Good: Use shallowRef for large datasets
import { shallowRef } from 'vue';

const largeDataset = shallowRef([...Array(10000)].map((_, i) => ({
  id: i,
  data: { /* complex nested data */ }
})));

// Update by replacing entire array
function updateData(newData) {
  largeDataset.value = newData;
}
```

### Optimize Computed Properties

```typescript
import { ref, computed, shallowRef } from 'vue';

// ❌ Bad: Heavy computation in computed without caching awareness
const expensiveComputed = computed(() => {
  return items.value.map(item => heavyTransformation(item));
});

// ✅ Good: Ensure stable references and proper dependencies
const items = shallowRef<Item[]>([]);
const filterText = ref('');

// Separate filter logic from transformation
const filteredIds = computed(() =>
  items.value
    .filter(item => item.name.includes(filterText.value))
    .map(item => item.id)
);

// Cache expensive transformations separately
const transformedItems = computed(() => {
  const idSet = new Set(filteredIds.value);
  return items.value
    .filter(item => idSet.has(item.id))
    .map(item => heavyTransformation(item));
});
```

### Use markRaw for Non-Reactive Data

```typescript
import { reactive, markRaw } from 'vue';

// For objects that don't need reactivity
const state = reactive({
  user: { name: 'John', age: 30 },
  // Static configuration - no reactivity needed
  config: markRaw({
    apiEndpoint: 'https://api.example.com',
    timeout: 5000,
    retryCount: 3,
  }),
  // External library instances
  chart: markRaw(new ChartLibrary()),
});
```

## Component Optimization

### Use v-once for Static Content

```vue
<template>
  <!-- Render once, never update -->
  <header v-once>
    <h1>{{ appTitle }}</h1>
    <nav>
      <a href="/">Home</a>
      <a href="/about">About</a>
    </nav>
  </header>

  <!-- Dynamic content -->
  <main>
    <slot />
  </main>
</template>
```

### Use v-memo for Conditional Caching

```vue
<template>
  <div v-for="item in items" :key="item.id">
    <!-- Only re-render when item.id or selected changes -->
    <div v-memo="[item.id, selected === item.id]">
      <ExpensiveComponent :item="item" :selected="selected === item.id" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface Item {
  id: number;
  // ... other properties
}

const items = ref<Item[]>([]);
const selected = ref<number | null>(null);
</script>
```

### Optimize List Rendering

```vue
<script setup lang="ts">
import { ref, computed, shallowRef } from 'vue';

interface Item {
  id: string;
  name: string;
  // ... other properties
}

// Use shallowRef for large lists
const items = shallowRef<Item[]>([]);

// Virtual list for very large datasets
const visibleItems = computed(() => {
  const start = scrollPosition.value;
  const end = start + visibleCount.value;
  return items.value.slice(start, end);
});
</script>

<template>
  <!-- Use key for efficient updates -->
  <div v-for="item in visibleItems" :key="item.id">
    {{ item.name }}
  </div>
</template>
```

## Event Handler Optimization

### Debouncing and Throttling

```vue
<script setup lang="ts">
import { ref } from 'vue';
import { useDebounceFn, useThrottleFn } from '@vueuse/core';

const searchQuery = ref('');
const results = ref([]);

// Debounce search input
const debouncedSearch = useDebounceFn(async (query: string) => {
  results.value = await searchAPI(query);
}, 300);

// Throttle scroll handler
const onScroll = useThrottleFn(() => {
  // Handle scroll
}, 100);

function handleInput(event: Event) {
  const value = (event.target as HTMLInputElement).value;
  searchQuery.value = value;
  debouncedSearch(value);
}
</script>

<template>
  <input :value="searchQuery" @input="handleInput" />
  <div @scroll="onScroll">
    <!-- content -->
  </div>
</template>
```

### Avoid Inline Functions in Templates

```vue
<!-- ❌ Bad: Creates new function on every render -->
<template>
  <button @click="() => handleClick(item.id)">Click</button>
  <div v-for="item in items" :key="item.id">
    <button @click="() => deleteItem(item.id)">Delete</button>
  </div>
</template>

<!-- ✅ Good: Use methods or computed -->
<script setup lang="ts">
function handleDelete(id: number) {
  deleteItem(id);
}
</script>

<template>
  <button @click="handleClick(item.id)">Click</button>
  <div v-for="item in items" :key="item.id">
    <button @click="handleDelete(item.id)">Delete</button>
  </div>
</template>
```

## Bundle Optimization

### Dynamic Imports

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    component: () => import('@/pages/HomePage.vue'),
  },
  {
    path: '/dashboard',
    component: () => import('@/pages/DashboardPage.vue'),
  },
  // Group related pages
  {
    path: '/admin',
    component: () => import(/* webpackChunkName: "admin" */ '@/pages/AdminPage.vue'),
    children: [
      {
        path: 'users',
        component: () => import(/* webpackChunkName: "admin" */ '@/pages/admin/UsersPage.vue'),
      },
    ],
  },
];
```

### defineAsyncComponent

```vue
<script setup lang="ts">
import { defineAsyncComponent } from 'vue';

// Basic async component
const HeavyChart = defineAsyncComponent(
  () => import('@/components/HeavyChart.vue')
);

// With loading and error states
const HeavyTable = defineAsyncComponent({
  loader: () => import('@/components/HeavyTable.vue'),
  loadingComponent: () => import('@/components/LoadingSpinner.vue'),
  errorComponent: () => import('@/components/ErrorFallback.vue'),
  delay: 200, // Show loading after 200ms
  timeout: 10000, // Timeout after 10s
});
</script>

<template>
  <Suspense>
    <template #default>
      <HeavyChart :data="chartData" />
    </template>
    <template #fallback>
      <div>Loading chart...</div>
    </template>
  </Suspense>
</template>
```

### Tree Shaking

```typescript
// ❌ Bad: Import entire library
import lodash from 'lodash';
lodash.debounce(fn, 300);

// ✅ Good: Import only what you need
import { debounce } from 'lodash-es';
debounce(fn, 300);

// ✅ Better: Use VueUse for Vue-specific utilities
import { useDebounceFn } from '@vueuse/core';
const debouncedFn = useDebounceFn(fn, 300);
```

## Memory Management

### Cleanup in onUnmounted

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const intervalId = ref<number | null>(null);
const observer = ref<IntersectionObserver | null>(null);

onMounted(() => {
  // Start interval
  intervalId.value = window.setInterval(() => {
    // periodic task
  }, 1000);

  // Setup observer
  observer.value = new IntersectionObserver(callback);
  observer.value.observe(element);

  // Event listener
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  // Clean up interval
  if (intervalId.value) {
    clearInterval(intervalId.value);
  }

  // Clean up observer
  if (observer.value) {
    observer.value.disconnect();
  }

  // Remove event listener
  window.removeEventListener('resize', handleResize);
});
</script>
```

### Use effectScope for Cleanup

```typescript
import { effectScope, ref, watch, onScopeDispose } from 'vue';

export function useFeature() {
  const scope = effectScope();

  scope.run(() => {
    const data = ref(null);

    watch(data, () => {
      // side effect
    });

    onScopeDispose(() => {
      // cleanup when scope is disposed
    });
  });

  // Stop all effects in scope
  function cleanup() {
    scope.stop();
  }

  return { cleanup };
}
```

## Performance Monitoring

### Vue DevTools Performance

```typescript
// Enable in development
if (import.meta.env.DEV) {
  app.config.performance = true;
}
```

### Custom Performance Tracking

```typescript
// composables/usePerformance.ts
import { onMounted, onUpdated } from 'vue';

export function usePerformanceTracking(componentName: string) {
  let renderStart: number;

  onMounted(() => {
    const duration = performance.now() - renderStart;
    console.log(`${componentName} mount time: ${duration.toFixed(2)}ms`);
  });

  onUpdated(() => {
    const duration = performance.now() - renderStart;
    console.log(`${componentName} update time: ${duration.toFixed(2)}ms`);
  });

  renderStart = performance.now();
}
```

## Best Practices Summary

1. **Use shallowRef/shallowReactive** for large data structures
2. **Use v-once** for static content
3. **Use v-memo** for conditional caching in lists
4. **Lazy load** routes and heavy components
5. **Clean up** subscriptions and listeners
6. **Debounce/throttle** expensive operations
7. **Tree shake** imports
8. **Profile** with Vue DevTools
