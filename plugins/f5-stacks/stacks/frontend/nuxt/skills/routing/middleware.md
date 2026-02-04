---
name: nuxt-middleware
description: Route middleware in Nuxt 3
applies_to: nuxt
---

# Route Middleware in Nuxt 3

## Overview

Middleware runs before navigating to a route, enabling authentication, authorization, and other route guards.

## Types of Middleware

1. **Named middleware** - In `middleware/` directory, explicitly referenced
2. **Anonymous middleware** - Defined inline in page
3. **Global middleware** - Runs on every route

## Named Middleware

### Basic Authentication

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user } = useAuth();

  if (!user.value) {
    // Redirect to login with return URL
    return navigateTo({
      path: '/login',
      query: { redirect: to.fullPath },
    });
  }
});
```

### Using in Pages

```vue
<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
});
</script>
```

### Multiple Middleware

```vue
<script setup lang="ts">
definePageMeta({
  middleware: ['auth', 'admin', 'verified'],
});
</script>
```

## Global Middleware

```typescript
// middleware/analytics.global.ts
export default defineNuxtRouteMiddleware((to, from) => {
  // Runs on every route change
  trackPageView(to.path);
});
```

## Anonymous Middleware

```vue
<script setup lang="ts">
definePageMeta({
  middleware: [
    function (to, from) {
      // Inline middleware logic
      const { isAdmin } = useAuth();
      if (!isAdmin.value) {
        return navigateTo('/unauthorized');
      }
    },
  ],
});
</script>
```

## Common Patterns

### Role-Based Access

```typescript
// middleware/admin.ts
export default defineNuxtRouteMiddleware(async (to, from) => {
  const { user } = useAuth();

  if (!user.value) {
    return navigateTo('/login');
  }

  if (user.value.role !== 'admin') {
    return navigateTo('/unauthorized');
  }
});
```

### Guest Only (Login/Register)

```typescript
// middleware/guest.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user } = useAuth();

  // Redirect authenticated users away from login
  if (user.value) {
    return navigateTo('/dashboard');
  }
});
```

### Email Verification

```typescript
// middleware/verified.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user } = useAuth();

  if (!user.value) {
    return navigateTo('/login');
  }

  if (!user.value.emailVerified) {
    return navigateTo('/verify-email');
  }
});
```

### Subscription Check

```typescript
// middleware/subscribed.ts
export default defineNuxtRouteMiddleware(async (to, from) => {
  const { user } = useAuth();

  if (!user.value) {
    return navigateTo('/login');
  }

  // Check subscription status
  const subscription = await $fetch('/api/subscription');

  if (!subscription.active) {
    return navigateTo('/pricing');
  }
});
```

### Feature Flag

```typescript
// middleware/feature.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const config = useRuntimeConfig();

  // Check if feature is enabled
  const feature = to.meta.feature as string;

  if (feature && !config.public.features[feature]) {
    return navigateTo('/');
  }
});

// Usage
definePageMeta({
  middleware: 'feature',
  feature: 'newDashboard',
});
```

## Async Middleware

```typescript
// middleware/load-user.ts
export default defineNuxtRouteMiddleware(async (to, from) => {
  const { user, fetchUser } = useAuth();

  // Load user if not loaded
  if (!user.value) {
    try {
      await fetchUser();
    } catch {
      // Token invalid, redirect to login
      return navigateTo('/login');
    }
  }
});
```

## Server vs Client Middleware

```typescript
// middleware/server-only.ts
export default defineNuxtRouteMiddleware((to, from) => {
  // Only run on server
  if (import.meta.server) {
    // Server-side checks
    const event = useRequestEvent();
    const ip = getHeader(event!, 'x-forwarded-for');

    if (isBlockedIP(ip)) {
      return navigateTo('/blocked');
    }
  }
});

// middleware/client-only.ts
export default defineNuxtRouteMiddleware((to, from) => {
  // Only run on client
  if (import.meta.client) {
    // Client-side checks
    const hasAcceptedTerms = localStorage.getItem('terms-accepted');

    if (!hasAcceptedTerms && to.path !== '/terms') {
      return navigateTo('/terms');
    }
  }
});
```

## Middleware Order

```vue
<script setup lang="ts">
definePageMeta({
  // Runs in order: auth → admin → verified
  middleware: ['auth', 'admin', 'verified'],
});
</script>
```

Global middleware runs before named middleware.

## Returning Values

```typescript
export default defineNuxtRouteMiddleware((to, from) => {
  // Continue navigation
  return; // or return undefined

  // Abort navigation
  return abortNavigation();

  // Abort with error
  return abortNavigation(createError({
    statusCode: 403,
    message: 'Forbidden',
  }));

  // Redirect
  return navigateTo('/login');

  // External redirect
  return navigateTo('https://example.com', { external: true });
});
```

## Dynamic Middleware

```typescript
// middleware/permission.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user, hasPermission } = useAuth();

  // Get required permission from route meta
  const permission = to.meta.permission as string;

  if (permission && !hasPermission(permission)) {
    return navigateTo('/unauthorized');
  }
});

// Usage
definePageMeta({
  middleware: 'permission',
  permission: 'manage_users',
});
```

## Composable in Middleware

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware(async (to, from) => {
  // Use composables
  const { user, isAuthenticated } = useAuth();
  const toast = useToast();

  if (!isAuthenticated.value) {
    toast.add({
      title: 'Authentication Required',
      description: 'Please log in to continue',
    });

    return navigateTo('/login');
  }
});
```

## Testing Middleware

```typescript
// tests/middleware/auth.test.ts
import { describe, it, expect, vi } from 'vitest';

describe('auth middleware', () => {
  it('redirects unauthenticated users', async () => {
    // Mock composables
    vi.mock('~/composables/useAuth', () => ({
      useAuth: () => ({
        user: ref(null),
      }),
    }));

    const navigateTo = vi.fn();
    vi.mock('#app', () => ({
      navigateTo,
    }));

    const middleware = await import('~/middleware/auth').then((m) => m.default);

    const to = { fullPath: '/protected' };
    const from = { fullPath: '/' };

    await middleware(to, from);

    expect(navigateTo).toHaveBeenCalledWith({
      path: '/login',
      query: { redirect: '/protected' },
    });
  });
});
```

## Best Practices

1. **Keep middleware focused** - One responsibility per middleware
2. **Use named middleware** - For reusability
3. **Order matters** - Auth before role checks
4. **Handle errors** - Use try/catch for async operations
5. **Global sparingly** - Only for truly global needs
