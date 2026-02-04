---
name: vue-lazy-loading
description: Lazy loading strategies for Vue applications
applies_to: vue
---

# Lazy Loading in Vue

## Overview

Lazy loading defers loading of resources until they're needed,
improving initial page load time and reducing bandwidth usage.

## Route-Level Lazy Loading

### Basic Route Splitting

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      // Eager load - included in main bundle
      component: () => import('@/pages/HomePage.vue'),
    },
    {
      path: '/about',
      name: 'about',
      // Lazy loaded - separate chunk
      component: () => import('@/pages/AboutPage.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      // With chunk name for debugging
      component: () => import(
        /* webpackChunkName: "dashboard" */
        '@/pages/DashboardPage.vue'
      ),
    },
  ],
});
```

### Route Groups

```typescript
// Group related routes into same chunk
const routes = [
  {
    path: '/admin',
    component: () => import(
      /* webpackChunkName: "admin" */
      '@/layouts/AdminLayout.vue'
    ),
    children: [
      {
        path: '',
        component: () => import(
          /* webpackChunkName: "admin" */
          '@/pages/admin/DashboardPage.vue'
        ),
      },
      {
        path: 'users',
        component: () => import(
          /* webpackChunkName: "admin" */
          '@/pages/admin/UsersPage.vue'
        ),
      },
      {
        path: 'settings',
        component: () => import(
          /* webpackChunkName: "admin" */
          '@/pages/admin/SettingsPage.vue'
        ),
      },
    ],
  },
];
```

### Prefetching Routes

```typescript
// Prefetch likely next routes
const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/products',
      component: () => import('@/pages/ProductsPage.vue'),
      // Prefetch product detail when on products list
      meta: { prefetch: ['/products/:id'] },
    },
  ],
});

// In navigation guard
router.afterEach((to) => {
  const prefetchRoutes = to.meta.prefetch as string[] | undefined;
  if (prefetchRoutes) {
    prefetchRoutes.forEach(path => {
      const route = router.resolve(path);
      if (route.matched[0]?.components?.default) {
        // Trigger prefetch
        const component = route.matched[0].components.default;
        if (typeof component === 'function') {
          (component as () => Promise<unknown>)();
        }
      }
    });
  }
});
```

## Component-Level Lazy Loading

### defineAsyncComponent

```vue
<script setup lang="ts">
import { defineAsyncComponent, ref } from 'vue';

// Basic async component
const HeavyChart = defineAsyncComponent(
  () => import('@/components/charts/HeavyChart.vue')
);

// With configuration
const DataTable = defineAsyncComponent({
  loader: () => import('@/components/tables/DataTable.vue'),
  loadingComponent: LoadingSpinner,
  errorComponent: ErrorFallback,
  delay: 200,
  timeout: 10000,
  suspensible: false, // Opt out of Suspense
  onError(error, retry, fail, attempts) {
    if (attempts <= 3) {
      retry();
    } else {
      fail();
    }
  },
});

// Conditional loading
const showChart = ref(false);
</script>

<template>
  <button @click="showChart = true">Show Chart</button>

  <!-- Only loads when condition is true -->
  <HeavyChart v-if="showChart" :data="chartData" />
</template>
```

### Suspense for Async Components

```vue
<script setup lang="ts">
import { defineAsyncComponent } from 'vue';

const AsyncDashboard = defineAsyncComponent(
  () => import('@/components/Dashboard.vue')
);
</script>

<template>
  <Suspense>
    <template #default>
      <AsyncDashboard />
    </template>
    <template #fallback>
      <div class="loading-container">
        <LoadingSpinner />
        <p>Loading dashboard...</p>
      </div>
    </template>
  </Suspense>
</template>
```

### Nested Suspense

```vue
<template>
  <Suspense>
    <template #default>
      <div class="page">
        <header>
          <AsyncNavigation />
        </header>

        <main>
          <!-- Nested Suspense for independent loading -->
          <Suspense>
            <template #default>
              <AsyncMainContent />
            </template>
            <template #fallback>
              <ContentSkeleton />
            </template>
          </Suspense>
        </main>

        <aside>
          <Suspense>
            <template #default>
              <AsyncSidebar />
            </template>
            <template #fallback>
              <SidebarSkeleton />
            </template>
          </Suspense>
        </aside>
      </div>
    </template>
    <template #fallback>
      <PageSkeleton />
    </template>
  </Suspense>
</template>
```

## Image Lazy Loading

### Native Lazy Loading

```vue
<template>
  <img
    :src="imageUrl"
    :alt="altText"
    loading="lazy"
    decoding="async"
  />
</template>
```

### Intersection Observer

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

interface Props {
  src: string;
  placeholder?: string;
  alt: string;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '/placeholder.jpg',
});

const imgRef = ref<HTMLImageElement | null>(null);
const isLoaded = ref(false);
const currentSrc = ref(props.placeholder);

let observer: IntersectionObserver | null = null;

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          currentSrc.value = props.src;
          isLoaded.value = true;
          observer?.disconnect();
        }
      });
    },
    {
      rootMargin: '50px',
      threshold: 0.1,
    }
  );

  if (imgRef.value) {
    observer.observe(imgRef.value);
  }
});

onUnmounted(() => {
  observer?.disconnect();
});
</script>

<template>
  <img
    ref="imgRef"
    :src="currentSrc"
    :alt="alt"
    :class="{ 'is-loaded': isLoaded }"
    @load="isLoaded = true"
  />
</template>

<style scoped>
img {
  opacity: 0;
  transition: opacity 0.3s ease;
}

img.is-loaded {
  opacity: 1;
}
</style>
```

### VueUse Integration

```vue
<script setup lang="ts">
import { useIntersectionObserver } from '@vueuse/core';
import { ref, computed } from 'vue';

const props = defineProps<{
  src: string;
  alt: string;
}>();

const target = ref<HTMLElement | null>(null);
const isVisible = ref(false);

const { stop } = useIntersectionObserver(
  target,
  ([{ isIntersecting }]) => {
    if (isIntersecting) {
      isVisible.value = true;
      stop();
    }
  },
  { rootMargin: '100px' }
);

const imageSrc = computed(() =>
  isVisible.value ? props.src : undefined
);
</script>

<template>
  <div ref="target" class="lazy-image-container">
    <img v-if="imageSrc" :src="imageSrc" :alt="alt" />
    <div v-else class="placeholder" />
  </div>
</template>
```

## List Virtualization

### Basic Virtual List

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';
import { useVirtualList } from '@vueuse/core';

interface Item {
  id: number;
  name: string;
}

const allItems = ref<Item[]>(
  Array.from({ length: 10000 }, (_, i) => ({
    id: i,
    name: `Item ${i}`,
  }))
);

const { list, containerProps, wrapperProps } = useVirtualList(
  allItems,
  {
    itemHeight: 50,
    overscan: 10,
  }
);
</script>

<template>
  <div v-bind="containerProps" class="virtual-list-container">
    <div v-bind="wrapperProps">
      <div
        v-for="{ data, index } in list"
        :key="data.id"
        class="list-item"
      >
        {{ data.name }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.virtual-list-container {
  height: 400px;
  overflow-y: auto;
}

.list-item {
  height: 50px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  border-bottom: 1px solid #eee;
}
</style>
```

## Infinite Scroll

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

interface Item {
  id: number;
  title: string;
}

const items = ref<Item[]>([]);
const page = ref(1);
const isLoading = ref(false);
const hasMore = ref(true);
const sentinel = ref<HTMLElement | null>(null);

let observer: IntersectionObserver | null = null;

async function loadMore() {
  if (isLoading.value || !hasMore.value) return;

  isLoading.value = true;

  try {
    const response = await fetch(`/api/items?page=${page.value}`);
    const newItems = await response.json();

    if (newItems.length === 0) {
      hasMore.value = false;
    } else {
      items.value.push(...newItems);
      page.value++;
    }
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting) {
        loadMore();
      }
    },
    { rootMargin: '100px' }
  );

  if (sentinel.value) {
    observer.observe(sentinel.value);
  }

  // Load initial data
  loadMore();
});

onUnmounted(() => {
  observer?.disconnect();
});
</script>

<template>
  <div class="item-list">
    <div v-for="item in items" :key="item.id" class="item">
      {{ item.title }}
    </div>

    <!-- Sentinel element for intersection observer -->
    <div ref="sentinel" class="sentinel">
      <span v-if="isLoading">Loading...</span>
      <span v-else-if="!hasMore">No more items</span>
    </div>
  </div>
</template>
```

## Best Practices

1. **Route splitting** - Split by route for automatic code splitting
2. **Component grouping** - Group related lazy components in chunks
3. **Loading states** - Always show loading feedback
4. **Error handling** - Provide fallbacks for failed loads
5. **Prefetching** - Anticipate user navigation
6. **Image optimization** - Use native loading="lazy"
7. **Virtual lists** - For 100+ item lists
8. **Intersection Observer** - For scroll-based loading
