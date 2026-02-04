---
name: vue-router
description: Vue Router setup and configuration
applies_to: vue
---

# Vue Router

## Overview

Vue Router is the official router for Vue.js applications.
It provides navigation, nested routes, and dynamic routing.

## Setup

```typescript
// router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: () => import('@/pages/HomePage.vue'),
    meta: { title: 'Home' },
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('@/pages/AboutPage.vue'),
    meta: { title: 'About' },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition;
    }
    if (to.hash) {
      return { el: to.hash };
    }
    return { top: 0 };
  },
});

export default router;

// main.ts
import { createApp } from 'vue';
import router from './router';
import App from './App.vue';

createApp(App).use(router).mount('#app');
```

## Route Configuration

### Basic Routes

```typescript
const routes: RouteRecordRaw[] = [
  // Simple route
  {
    path: '/',
    name: 'home',
    component: () => import('@/pages/HomePage.vue'),
  },

  // Route with params
  {
    path: '/users/:id',
    name: 'user-detail',
    component: () => import('@/pages/UserDetailPage.vue'),
    props: true, // Pass params as props
  },

  // Route with query
  {
    path: '/search',
    name: 'search',
    component: () => import('@/pages/SearchPage.vue'),
  },

  // Redirect
  {
    path: '/old-path',
    redirect: '/new-path',
  },

  // Alias
  {
    path: '/users',
    alias: '/people',
    component: () => import('@/pages/UsersPage.vue'),
  },

  // Catch-all 404
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('@/pages/NotFoundPage.vue'),
  },
];
```

### Nested Routes

```typescript
const routes: RouteRecordRaw[] = [
  {
    path: '/dashboard',
    component: () => import('@/layouts/DashboardLayout.vue'),
    children: [
      {
        path: '', // /dashboard
        name: 'dashboard',
        component: () => import('@/pages/dashboard/OverviewPage.vue'),
      },
      {
        path: 'settings', // /dashboard/settings
        name: 'dashboard-settings',
        component: () => import('@/pages/dashboard/SettingsPage.vue'),
      },
      {
        path: 'users', // /dashboard/users
        name: 'dashboard-users',
        component: () => import('@/pages/dashboard/UsersPage.vue'),
        children: [
          {
            path: ':id', // /dashboard/users/:id
            name: 'dashboard-user-detail',
            component: () => import('@/pages/dashboard/UserDetailPage.vue'),
          },
        ],
      },
    ],
  },
];
```

### Named Views

```typescript
const routes: RouteRecordRaw[] = [
  {
    path: '/',
    components: {
      default: () => import('@/pages/MainContent.vue'),
      sidebar: () => import('@/components/Sidebar.vue'),
      footer: () => import('@/components/Footer.vue'),
    },
  },
];
```

```vue
<!-- App.vue -->
<template>
  <RouterView />
  <RouterView name="sidebar" />
  <RouterView name="footer" />
</template>
```

## Navigation

### Programmatic Navigation

```vue
<script setup lang="ts">
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();

// Navigate to path
function goHome() {
  router.push('/');
}

// Navigate by name
function goToUser(id: string) {
  router.push({ name: 'user-detail', params: { id } });
}

// Navigate with query
function search(query: string) {
  router.push({ path: '/search', query: { q: query } });
}

// Replace (no history entry)
function replaceRoute() {
  router.replace('/new-path');
}

// Go back/forward
function goBack() {
  router.back();
  // or router.go(-1);
}

function goForward() {
  router.forward();
  // or router.go(1);
}

// Current route info
console.log(route.path);       // '/users/123'
console.log(route.params.id);  // '123'
console.log(route.query);      // { q: 'search' }
console.log(route.name);       // 'user-detail'
console.log(route.meta);       // { requiresAuth: true }
</script>
```

### RouterLink Component

```vue
<template>
  <!-- Basic link -->
  <RouterLink to="/">Home</RouterLink>

  <!-- Named route -->
  <RouterLink :to="{ name: 'user-detail', params: { id: '123' } }">
    User Profile
  </RouterLink>

  <!-- With query -->
  <RouterLink :to="{ path: '/search', query: { q: 'vue' } }">
    Search Vue
  </RouterLink>

  <!-- Replace history -->
  <RouterLink to="/about" replace>About</RouterLink>

  <!-- Active class customization -->
  <RouterLink
    to="/about"
    active-class="text-primary"
    exact-active-class="font-bold"
  >
    About
  </RouterLink>

  <!-- Custom element -->
  <RouterLink to="/" custom v-slot="{ navigate, isActive }">
    <button
      @click="navigate"
      :class="{ 'is-active': isActive }"
    >
      Home
    </button>
  </RouterLink>
</template>
```

## Route Meta

```typescript
// Define meta types
declare module 'vue-router' {
  interface RouteMeta {
    title?: string;
    requiresAuth?: boolean;
    roles?: string[];
    layout?: 'default' | 'auth' | 'dashboard';
  }
}

const routes: RouteRecordRaw[] = [
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/pages/AdminPage.vue'),
    meta: {
      title: 'Admin Dashboard',
      requiresAuth: true,
      roles: ['admin'],
      layout: 'dashboard',
    },
  },
];

// Use meta in guards
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !isAuthenticated()) {
    return { name: 'login' };
  }
});

// Use meta in components
const route = useRoute();
console.log(route.meta.title);
```

## Lazy Loading

```typescript
// Basic lazy loading
component: () => import('@/pages/HomePage.vue')

// With webpack chunk name (Vite ignores)
component: () => import(/* webpackChunkName: "home" */ '@/pages/HomePage.vue')

// Group routes in same chunk
const UserModule = () => import('@/pages/users/UserModule.vue');

const routes = [
  { path: '/users', component: UserModule },
  { path: '/users/:id', component: UserModule },
];
```

## Router Composables

```typescript
import {
  useRouter,
  useRoute,
  useLink,
  onBeforeRouteLeave,
  onBeforeRouteUpdate,
} from 'vue-router';

// In component
const router = useRouter();
const route = useRoute();

// Before leaving current route
onBeforeRouteLeave((to, from) => {
  if (hasUnsavedChanges.value) {
    return confirm('Discard changes?');
  }
});

// Before route params change (same component)
onBeforeRouteUpdate(async (to, from) => {
  if (to.params.id !== from.params.id) {
    await loadData(to.params.id as string);
  }
});
```

## Best Practices

1. **Use named routes** - Easier to maintain and refactor
2. **Lazy load routes** - Better initial load performance
3. **Type route meta** - Declare module for type safety
4. **Use route guards** - Protect authenticated routes
5. **Handle 404** - Always have a catch-all route
