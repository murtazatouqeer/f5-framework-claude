---
name: vue-navigation-guards
description: Vue Router navigation guards
applies_to: vue
---

# Navigation Guards

## Overview

Navigation guards are hooks to control navigation flow.
They can be used for authentication, data fetching, and more.

## Global Guards

### beforeEach

```typescript
// router/guards.ts
import type { Router } from 'vue-router';
import { useAuthStore } from '@/stores/useAuthStore';

export function setupGuards(router: Router) {
  router.beforeEach(async (to, from) => {
    const authStore = useAuthStore();

    // Update document title
    document.title = to.meta.title
      ? `${to.meta.title} | My App`
      : 'My App';

    // Check authentication
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      // Redirect to login with return URL
      return {
        name: 'login',
        query: { redirect: to.fullPath },
      };
    }

    // Check roles
    if (to.meta.roles && to.meta.roles.length > 0) {
      const hasRole = to.meta.roles.some((role) =>
        authStore.user?.roles.includes(role)
      );

      if (!hasRole) {
        return { name: 'forbidden' };
      }
    }

    // Guest only routes (login, register)
    if (to.meta.guestOnly && authStore.isAuthenticated) {
      return { name: 'home' };
    }

    // Allow navigation
    return true;
  });
}
```

### beforeResolve

```typescript
router.beforeResolve(async (to) => {
  // Called after all in-component guards and async components are resolved
  // Good for data fetching

  if (to.meta.requiresData) {
    try {
      await loadRequiredData(to);
    } catch (error) {
      // Handle error, redirect to error page
      return { name: 'error' };
    }
  }
});
```

### afterEach

```typescript
router.afterEach((to, from, failure) => {
  // Called after navigation is complete
  // No return value, cannot block navigation

  // Track page views
  analytics.trackPageView(to.fullPath);

  // Handle navigation failures
  if (failure) {
    console.error('Navigation failed:', failure);

    if (isNavigationFailure(failure, NavigationFailureType.aborted)) {
      console.log('Navigation aborted');
    }
  }

  // Scroll to top
  window.scrollTo(0, 0);
});
```

## Per-Route Guards

### Route Definition Guard

```typescript
const routes: RouteRecordRaw[] = [
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/pages/AdminPage.vue'),
    beforeEnter: (to, from) => {
      // Only for this route
      const authStore = useAuthStore();

      if (!authStore.isAdmin) {
        return { name: 'forbidden' };
      }
    },
  },

  // Multiple guards
  {
    path: '/checkout',
    component: () => import('@/pages/CheckoutPage.vue'),
    beforeEnter: [checkAuth, checkCart, loadCheckoutData],
  },
];

// Guard functions
function checkAuth(to, from) {
  if (!isAuthenticated()) {
    return { name: 'login' };
  }
}

function checkCart(to, from) {
  const cartStore = useCartStore();
  if (cartStore.isEmpty) {
    return { name: 'cart' };
  }
}

async function loadCheckoutData(to, from) {
  await loadPaymentMethods();
}
```

## In-Component Guards

### Composition API Guards

```vue
<script setup lang="ts">
import {
  onBeforeRouteLeave,
  onBeforeRouteUpdate,
} from 'vue-router';
import { ref } from 'vue';

const hasUnsavedChanges = ref(false);

// Called when leaving this component's route
onBeforeRouteLeave((to, from) => {
  if (hasUnsavedChanges.value) {
    const answer = window.confirm(
      'You have unsaved changes. Are you sure you want to leave?'
    );

    if (!answer) {
      return false; // Cancel navigation
    }
  }
});

// Called when route params change but same component is reused
onBeforeRouteUpdate(async (to, from) => {
  // e.g., /users/1 -> /users/2
  if (to.params.id !== from.params.id) {
    // Reset form state
    hasUnsavedChanges.value = false;
    // Fetch new data
    await fetchUser(to.params.id as string);
  }
});
</script>
```

## Common Guard Patterns

### Authentication Guard

```typescript
// router/guards/auth.ts
import { NavigationGuard } from 'vue-router';
import { useAuthStore } from '@/stores/useAuthStore';

export const authGuard: NavigationGuard = async (to, from) => {
  const authStore = useAuthStore();

  // Wait for auth to initialize
  if (!authStore.isInitialized) {
    await authStore.initialize();
  }

  if (!authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    };
  }

  return true;
};

// Apply to routes
const routes = [
  {
    path: '/dashboard',
    component: DashboardPage,
    beforeEnter: authGuard,
  },
];

// Or apply globally
router.beforeEach(authGuard);
```

### Role-Based Guard

```typescript
// router/guards/role.ts
import { NavigationGuard } from 'vue-router';
import { useAuthStore } from '@/stores/useAuthStore';

export function createRoleGuard(allowedRoles: string[]): NavigationGuard {
  return (to, from) => {
    const authStore = useAuthStore();

    if (!authStore.user) {
      return { name: 'login' };
    }

    const hasRole = allowedRoles.some((role) =>
      authStore.user!.roles.includes(role)
    );

    if (!hasRole) {
      return { name: 'forbidden' };
    }

    return true;
  };
}

// Usage
const routes = [
  {
    path: '/admin',
    component: AdminPage,
    beforeEnter: createRoleGuard(['admin']),
  },
  {
    path: '/moderator',
    component: ModeratorPage,
    beforeEnter: createRoleGuard(['admin', 'moderator']),
  },
];
```

### Data Loading Guard

```typescript
// router/guards/data.ts
export const dataLoadingGuard: NavigationGuard = async (to) => {
  const dataLoader = to.meta.dataLoader as DataLoader | undefined;

  if (!dataLoader) return true;

  try {
    // Store data for component to access
    to.meta.preloadedData = await dataLoader(to);
    return true;
  } catch (error) {
    console.error('Data loading failed:', error);
    return { name: 'error', query: { message: 'Data loading failed' } };
  }
};

// Route config
const routes = [
  {
    path: '/users/:id',
    component: UserPage,
    meta: {
      dataLoader: async (to) => {
        return await fetchUser(to.params.id);
      },
    },
  },
];
```

### Progress Indicator

```typescript
import NProgress from 'nprogress';

router.beforeEach(() => {
  NProgress.start();
});

router.afterEach(() => {
  NProgress.done();
});

router.onError(() => {
  NProgress.done();
});
```

## Best Practices

1. **Keep guards focused** - Single responsibility
2. **Handle async properly** - Use async/await
3. **Always return** - Return navigation target or true
4. **Handle errors** - Redirect to error pages
5. **Consider UX** - Show loading states
6. **Type guards** - Use NavigationGuard type
