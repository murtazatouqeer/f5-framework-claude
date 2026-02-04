---
name: vue-keep-alive
description: Component caching with KeepAlive
applies_to: vue
---

# KeepAlive in Vue

## Overview

KeepAlive is a built-in component that caches component instances
when switching between dynamic components or routes.

## Basic Usage

### With Dynamic Components

```vue
<script setup lang="ts">
import { ref, shallowRef } from 'vue';
import TabA from './TabA.vue';
import TabB from './TabB.vue';
import TabC from './TabC.vue';

const tabs = [
  { name: 'Tab A', component: TabA },
  { name: 'Tab B', component: TabB },
  { name: 'Tab C', component: TabC },
];

const currentTab = shallowRef(tabs[0]);
</script>

<template>
  <div class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab.name"
      :class="{ active: currentTab === tab }"
      @click="currentTab = tab"
    >
      {{ tab.name }}
    </button>
  </div>

  <!-- Component state is preserved when switching -->
  <KeepAlive>
    <component :is="currentTab.component" />
  </KeepAlive>
</template>
```

### With v-if

```vue
<script setup lang="ts">
import { ref } from 'vue';

const showForm = ref(true);
</script>

<template>
  <button @click="showForm = !showForm">
    {{ showForm ? 'Hide' : 'Show' }} Form
  </button>

  <!-- Form state preserved when toggling -->
  <KeepAlive>
    <UserForm v-if="showForm" />
  </KeepAlive>
</template>
```

## Include and Exclude

### By Component Name

```vue
<script setup lang="ts">
import { ref } from 'vue';
</script>

<template>
  <!-- Only cache ComponentA and ComponentB -->
  <KeepAlive include="ComponentA,ComponentB">
    <component :is="currentComponent" />
  </KeepAlive>

  <!-- Cache all except ComponentC -->
  <KeepAlive exclude="ComponentC">
    <component :is="currentComponent" />
  </KeepAlive>

  <!-- Using regex -->
  <KeepAlive :include="/^Tab/">
    <component :is="currentComponent" />
  </KeepAlive>

  <!-- Using array -->
  <KeepAlive :include="['TabA', 'TabB']">
    <component :is="currentComponent" />
  </KeepAlive>
</template>
```

### Component Name Setup

```vue
<!-- TabA.vue -->
<script lang="ts">
// Must use separate script block for name
export default {
  name: 'TabA',
};
</script>

<script setup lang="ts">
// Component logic here
</script>

<template>
  <div>Tab A Content</div>
</template>
```

Or using `defineOptions`:

```vue
<script setup lang="ts">
defineOptions({
  name: 'TabA',
});

// Component logic
</script>
```

## Max Cached Instances

```vue
<template>
  <!-- Only cache last 5 components -->
  <KeepAlive :max="5">
    <component :is="currentComponent" />
  </KeepAlive>
</template>
```

## Lifecycle Hooks

### onActivated and onDeactivated

```vue
<script setup lang="ts">
import { ref, onActivated, onDeactivated, onMounted, onUnmounted } from 'vue';

const fetchCount = ref(0);

// Called on initial mount AND when re-activated from cache
onActivated(() => {
  console.log('Component activated');
  refreshData();
});

// Called when cached (deactivated) but not destroyed
onDeactivated(() => {
  console.log('Component deactivated');
  pauseTimers();
});

// Only called once on initial mount
onMounted(() => {
  console.log('Component mounted');
  setupEventListeners();
});

// Only called when component is truly destroyed
onUnmounted(() => {
  console.log('Component unmounted');
  cleanupResources();
});

async function refreshData() {
  fetchCount.value++;
  // Fetch fresh data
}

function pauseTimers() {
  // Pause any running timers or animations
}
</script>
```

### Pattern: Refresh on Activation

```vue
<script setup lang="ts">
import { ref, onActivated } from 'vue';

interface User {
  id: number;
  name: string;
  lastActive: Date;
}

const user = ref<User | null>(null);
const isStale = ref(false);

onActivated(async () => {
  // Check if data needs refresh
  if (isStale.value || !user.value) {
    await fetchUser();
  }
  isStale.value = false;
});

async function fetchUser() {
  const response = await fetch('/api/user');
  user.value = await response.json();
}

// Mark as stale when certain actions occur
function markStale() {
  isStale.value = true;
}
</script>
```

## Router Integration

### Keep Alive Routes

```vue
<!-- App.vue or Layout.vue -->
<template>
  <RouterView v-slot="{ Component, route }">
    <KeepAlive :include="cachedRoutes">
      <component :is="Component" :key="route.fullPath" />
    </KeepAlive>
  </RouterView>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

// Define which routes to cache
const cachedRoutes = computed(() => {
  return route.matched
    .filter(r => r.meta.keepAlive)
    .map(r => r.name as string);
});
</script>
```

### Route Meta Configuration

```typescript
// router/index.ts
const routes = [
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/pages/DashboardPage.vue'),
    meta: { keepAlive: true },
  },
  {
    path: '/users',
    name: 'UserList',
    component: () => import('@/pages/UserListPage.vue'),
    meta: { keepAlive: true },
  },
  {
    path: '/users/:id',
    name: 'UserDetail',
    component: () => import('@/pages/UserDetailPage.vue'),
    meta: { keepAlive: false }, // Don't cache detail pages
  },
];
```

### Conditional Keep Alive

```vue
<template>
  <RouterView v-slot="{ Component, route }">
    <KeepAlive v-if="route.meta.keepAlive">
      <component :is="Component" :key="route.fullPath" />
    </KeepAlive>
    <component v-else :is="Component" :key="route.fullPath" />
  </RouterView>
</template>
```

## Advanced Patterns

### Scoped Cache Key

```vue
<script setup lang="ts">
import { computed } from 'vue';
import { useRoute } from 'vue-router';

const route = useRoute();

// Different cache key per user
const cacheKey = computed(() => {
  return `${route.name}-${route.params.userId}`;
});
</script>

<template>
  <RouterView v-slot="{ Component }">
    <KeepAlive>
      <component :is="Component" :key="cacheKey" />
    </KeepAlive>
  </RouterView>
</template>
```

### Programmatic Cache Control

```typescript
// composables/useKeepAlive.ts
import { ref, readonly } from 'vue';

const cachedComponents = ref<Set<string>>(new Set(['Dashboard', 'UserList']));

export function useKeepAlive() {
  function addToCache(name: string) {
    cachedComponents.value.add(name);
  }

  function removeFromCache(name: string) {
    cachedComponents.value.delete(name);
  }

  function clearCache() {
    cachedComponents.value.clear();
  }

  function isCached(name: string) {
    return cachedComponents.value.has(name);
  }

  return {
    cachedComponents: readonly(cachedComponents),
    addToCache,
    removeFromCache,
    clearCache,
    isCached,
  };
}
```

```vue
<!-- Usage -->
<script setup lang="ts">
import { computed } from 'vue';
import { useKeepAlive } from '@/composables/useKeepAlive';

const { cachedComponents } = useKeepAlive();

const includeList = computed(() => Array.from(cachedComponents.value));
</script>

<template>
  <KeepAlive :include="includeList">
    <RouterView />
  </KeepAlive>
</template>
```

### Memory-Aware Caching

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue';

const maxCached = ref(10);

onMounted(() => {
  // Reduce cache on low-memory devices
  if ('deviceMemory' in navigator) {
    const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
    if (memory && memory < 4) {
      maxCached.value = 3;
    }
  }
});
</script>

<template>
  <KeepAlive :max="maxCached">
    <component :is="currentComponent" />
  </KeepAlive>
</template>
```

## Best Practices

1. **Name components** - Required for include/exclude to work
2. **Use max prop** - Prevent memory issues with many cached components
3. **Refresh on activation** - Check for stale data in onActivated
4. **Clean up in onDeactivated** - Pause timers, animations
5. **Don't cache forms** - Unless you explicitly want to preserve state
6. **Consider memory** - Large cached components can consume memory
7. **Test cache behavior** - Verify correct caching in development

## Common Pitfalls

```vue
<!-- ❌ Won't work: multiple root elements -->
<KeepAlive>
  <ComponentA v-if="show" />
  <ComponentB v-else />
</KeepAlive>

<!-- ✅ Works: single dynamic component -->
<KeepAlive>
  <component :is="show ? ComponentA : ComponentB" />
</KeepAlive>

<!-- ❌ Won't work: v-for inside KeepAlive -->
<KeepAlive>
  <div v-for="item in items" :key="item.id">
    <ItemComponent :item="item" />
  </div>
</KeepAlive>

<!-- ✅ Works: wrap KeepAlive around single child -->
<div v-for="item in items" :key="item.id">
  <KeepAlive>
    <ItemComponent v-if="selectedId === item.id" :item="item" />
  </KeepAlive>
</div>
```
