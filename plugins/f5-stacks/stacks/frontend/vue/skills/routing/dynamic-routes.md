---
name: vue-dynamic-routes
description: Dynamic and advanced routing patterns
applies_to: vue
---

# Dynamic Routes

## Overview

Dynamic routes allow flexible URL patterns with parameters,
optional segments, and programmatic route management.

## Route Parameters

### Basic Parameters

```typescript
const routes: RouteRecordRaw[] = [
  // Required parameter
  {
    path: '/users/:id',
    name: 'user-detail',
    component: () => import('@/pages/UserDetailPage.vue'),
  },

  // Multiple parameters
  {
    path: '/users/:userId/posts/:postId',
    name: 'user-post',
    component: () => import('@/pages/UserPostPage.vue'),
  },
];
```

```vue
<script setup lang="ts">
import { useRoute } from 'vue-router';

const route = useRoute();

// Access params
const userId = route.params.id; // string
const postId = route.params.postId; // string
</script>
```

### Optional Parameters

```typescript
const routes = [
  // Optional parameter with ?
  {
    path: '/users/:id?',
    name: 'users',
    component: () => import('@/pages/UsersPage.vue'),
  },
  // /users -> all users
  // /users/123 -> specific user
];
```

### Repeatable Parameters

```typescript
const routes = [
  // Matches /articles/a/b/c
  {
    path: '/articles/:sections+', // One or more
    component: () => import('@/pages/ArticlePage.vue'),
  },

  // Matches /files or /files/a/b/c
  {
    path: '/files/:path*', // Zero or more
    component: () => import('@/pages/FileBrowserPage.vue'),
  },
];

// Accessing
const route = useRoute();
console.log(route.params.sections); // ['a', 'b', 'c']
```

### Parameter Constraints

```typescript
const routes = [
  // Only numeric IDs
  {
    path: '/users/:id(\\d+)',
    component: UserPage,
  },

  // Specific values
  {
    path: '/posts/:type(draft|published)',
    component: PostsPage,
  },

  // Custom regex
  {
    path: '/files/:filename([\\w-]+\\.\\w+)',
    component: FilePage,
  },
];
```

## Props from Routes

### Boolean Props

```typescript
const routes = [
  {
    path: '/users/:id',
    component: UserPage,
    props: true, // Pass params as props
  },
];
```

```vue
<!-- UserPage.vue -->
<script setup lang="ts">
// Receive as prop instead of route.params
defineProps<{
  id: string;
}>();
</script>
```

### Object Props

```typescript
const routes = [
  {
    path: '/about',
    component: AboutPage,
    props: { newsletter: true, version: '2.0' },
  },
];
```

### Function Props

```typescript
const routes = [
  {
    path: '/search',
    component: SearchPage,
    props: (route) => ({
      query: route.query.q,
      page: Number(route.query.page) || 1,
    }),
  },
];
```

## Dynamic Route Addition

### Adding Routes at Runtime

```typescript
import { useRouter } from 'vue-router';

const router = useRouter();

// Add a single route
router.addRoute({
  path: '/new-feature',
  name: 'new-feature',
  component: () => import('@/pages/NewFeaturePage.vue'),
});

// Add nested route
router.addRoute('dashboard', {
  path: 'analytics',
  name: 'dashboard-analytics',
  component: () => import('@/pages/dashboard/AnalyticsPage.vue'),
});

// Check if route exists
if (!router.hasRoute('new-feature')) {
  router.addRoute({ ... });
}

// Remove route
router.removeRoute('new-feature');

// Get all routes
const routes = router.getRoutes();
```

### Module-Based Routes

```typescript
// features/admin/routes.ts
export const adminRoutes: RouteRecordRaw[] = [
  {
    path: '/admin',
    component: () => import('./AdminLayout.vue'),
    children: [
      {
        path: '',
        name: 'admin-dashboard',
        component: () => import('./pages/DashboardPage.vue'),
      },
      {
        path: 'users',
        name: 'admin-users',
        component: () => import('./pages/UsersPage.vue'),
      },
    ],
  },
];

// router/index.ts
import { adminRoutes } from '@/features/admin/routes';

const routes = [
  ...baseRoutes,
  ...adminRoutes,
];
```

### Permission-Based Routes

```typescript
// Load routes based on user permissions
async function loadUserRoutes() {
  const authStore = useAuthStore();

  if (authStore.user?.permissions.includes('admin')) {
    const { adminRoutes } = await import('@/features/admin/routes');
    adminRoutes.forEach((route) => router.addRoute(route));
  }

  if (authStore.user?.permissions.includes('analytics')) {
    const { analyticsRoutes } = await import('@/features/analytics/routes');
    analyticsRoutes.forEach((route) => router.addRoute(route));
  }
}

// Call after auth
router.beforeEach(async (to, from) => {
  if (!routesLoaded.value && authStore.isAuthenticated) {
    await loadUserRoutes();
    routesLoaded.value = true;
    return to.fullPath; // Re-navigate to trigger new routes
  }
});
```

## Query Parameters

### Working with Query

```vue
<script setup lang="ts">
import { useRoute, useRouter } from 'vue-router';
import { computed, watch } from 'vue';

const route = useRoute();
const router = useRouter();

// Read query params
const searchQuery = computed(() => route.query.q as string || '');
const page = computed(() => Number(route.query.page) || 1);
const filters = computed(() => {
  const f = route.query.filter;
  return Array.isArray(f) ? f : f ? [f] : [];
});

// Update query params
function setPage(newPage: number) {
  router.push({
    query: { ...route.query, page: newPage },
  });
}

function setFilters(newFilters: string[]) {
  router.push({
    query: { ...route.query, filter: newFilters },
  });
}

// Watch query changes
watch(
  () => route.query,
  (newQuery) => {
    fetchData(newQuery);
  },
  { immediate: true }
);
</script>
```

### Typed Query Helpers

```typescript
// composables/useQueryParams.ts
import { computed } from 'vue';
import { useRoute, useRouter, type LocationQueryValue } from 'vue-router';

export function useQueryParams<T extends Record<string, unknown>>(
  defaults: T
) {
  const route = useRoute();
  const router = useRouter();

  const params = computed<T>(() => {
    const result = { ...defaults };

    for (const key in defaults) {
      const value = route.query[key];
      const defaultValue = defaults[key];

      if (value !== undefined) {
        if (typeof defaultValue === 'number') {
          result[key] = Number(value) as T[typeof key];
        } else if (typeof defaultValue === 'boolean') {
          result[key] = (value === 'true') as T[typeof key];
        } else if (Array.isArray(defaultValue)) {
          result[key] = (Array.isArray(value) ? value : [value]) as T[typeof key];
        } else {
          result[key] = value as T[typeof key];
        }
      }
    }

    return result;
  });

  function setParams(newParams: Partial<T>) {
    router.push({
      query: {
        ...route.query,
        ...Object.fromEntries(
          Object.entries(newParams).map(([k, v]) => [k, String(v)])
        ),
      },
    });
  }

  return { params, setParams };
}

// Usage
const { params, setParams } = useQueryParams({
  page: 1,
  search: '',
  sort: 'name',
});

setParams({ page: 2, search: 'vue' });
```

## Best Practices

1. **Use props for params** - Better component isolation
2. **Type your params** - Create interfaces for route params
3. **Validate params** - Use constraints or guards
4. **Handle missing params** - Provide defaults
5. **Clean URLs** - Use semantic, readable paths
6. **Preserve query** - When navigating, keep relevant query params
