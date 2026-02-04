---
name: nuxt-middleware
description: Template for Nuxt 3 route middleware
applies_to: nuxt
---

# Nuxt Middleware Template

## Authentication Middleware

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated.value) {
    // Save intended destination
    const returnUrl = to.fullPath;

    return navigateTo({
      path: '/login',
      query: { redirect: returnUrl },
    });
  }
});
```

## Guest Middleware

```typescript
// middleware/guest.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated.value) {
    return navigateTo('/dashboard');
  }
});
```

## Role-Based Middleware

```typescript
// middleware/role.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user } = useAuth();

  // Get required roles from route meta
  const requiredRoles = to.meta.roles as string[] | undefined;

  if (!requiredRoles || requiredRoles.length === 0) {
    return;
  }

  if (!user.value) {
    return navigateTo('/login');
  }

  const hasRole = requiredRoles.some((role) =>
    user.value?.roles?.includes(role)
  );

  if (!hasRole) {
    return navigateTo('/unauthorized');
  }
});
```

Usage in page:

```vue
<script setup lang="ts">
definePageMeta({
  middleware: 'role',
  roles: ['admin', 'manager'],
});
</script>
```

## Permission Middleware

```typescript
// middleware/permission.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const { user, hasPermission } = useAuth();

  const requiredPermission = to.meta.permission as string | undefined;

  if (!requiredPermission) {
    return;
  }

  if (!user.value) {
    return navigateTo('/login');
  }

  if (!hasPermission(requiredPermission)) {
    return navigateTo('/unauthorized');
  }
});
```

## Logging Middleware

```typescript
// middleware/logger.global.ts
export default defineNuxtRouteMiddleware((to, from) => {
  if (import.meta.server) {
    console.log(`[Server] Navigation: ${from.path} -> ${to.path}`);
  }

  if (import.meta.client) {
    console.log(`[Client] Navigation: ${from.path} -> ${to.path}`);
  }
});
```

## Redirect Middleware

```typescript
// middleware/redirect.ts
const redirects: Record<string, string> = {
  '/old-page': '/new-page',
  '/legacy': '/modern',
};

export default defineNuxtRouteMiddleware((to, from) => {
  const redirect = redirects[to.path];

  if (redirect) {
    return navigateTo(redirect, { redirectCode: 301 });
  }
});
```

## Feature Flag Middleware

```typescript
// middleware/feature.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const config = useRuntimeConfig();

  const requiredFeature = to.meta.feature as string | undefined;

  if (!requiredFeature) {
    return;
  }

  const enabledFeatures = config.public.enabledFeatures as string[];

  if (!enabledFeatures.includes(requiredFeature)) {
    return navigateTo('/coming-soon');
  }
});
```

## Maintenance Middleware

```typescript
// middleware/maintenance.global.ts
export default defineNuxtRouteMiddleware((to, from) => {
  const config = useRuntimeConfig();

  if (config.public.maintenanceMode && to.path !== '/maintenance') {
    return navigateTo('/maintenance');
  }
});
```

## Rate Limiting Middleware (Server)

```typescript
// server/middleware/rate-limit.ts
const rateLimits = new Map<string, { count: number; resetAt: number }>();

export default defineEventHandler((event) => {
  const ip = getRequestIP(event) || 'unknown';
  const now = Date.now();
  const windowMs = 60 * 1000; // 1 minute
  const maxRequests = 100;

  let rateLimit = rateLimits.get(ip);

  if (!rateLimit || rateLimit.resetAt < now) {
    rateLimit = { count: 0, resetAt: now + windowMs };
  }

  rateLimit.count++;
  rateLimits.set(ip, rateLimit);

  if (rateLimit.count > maxRequests) {
    throw createError({
      statusCode: 429,
      statusMessage: 'Too Many Requests',
    });
  }

  // Add rate limit headers
  setHeader(event, 'X-RateLimit-Limit', maxRequests.toString());
  setHeader(event, 'X-RateLimit-Remaining', (maxRequests - rateLimit.count).toString());
  setHeader(event, 'X-RateLimit-Reset', rateLimit.resetAt.toString());
});
```

## Inline Middleware

```vue
<script setup lang="ts">
definePageMeta({
  middleware: [
    function (to, from) {
      // Custom inline logic
      if (to.query.preview !== 'true') {
        return navigateTo('/');
      }
    },
  ],
});
</script>
```

## Named Middleware Registration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    '/admin/**': {
      appMiddleware: ['auth', 'role'],
    },
  },
});
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| None required | Middleware are self-contained | - |
