---
name: nuxt-route-validation
description: Route parameter validation in Nuxt 3
applies_to: nuxt
---

# Route Validation in Nuxt 3

## Overview

Route validation ensures route parameters are valid before rendering pages, providing better UX and security.

## Basic Validation

```vue
<!-- pages/products/[id].vue -->
<script setup lang="ts">
definePageMeta({
  validate: async (route) => {
    // Simple check - return boolean
    return /^\d+$/.test(route.params.id as string);
  },
});
</script>
```

## UUID Validation

```vue
<script setup lang="ts">
const UUID_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

definePageMeta({
  validate: (route) => {
    const id = route.params.id as string;
    return UUID_REGEX.test(id);
  },
});
</script>
```

## Slug Validation

```vue
<script setup lang="ts">
definePageMeta({
  validate: (route) => {
    const slug = route.params.slug as string;

    // Only lowercase letters, numbers, and hyphens
    const slugRegex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
    return slugRegex.test(slug);
  },
});
</script>
```

## Custom Error Response

```vue
<script setup lang="ts">
definePageMeta({
  validate: (route) => {
    const id = route.params.id as string;

    if (!/^\d+$/.test(id)) {
      return {
        statusCode: 400,
        statusMessage: 'Invalid product ID format',
      };
    }

    return true;
  },
});
</script>
```

## Async Validation

```vue
<script setup lang="ts">
definePageMeta({
  validate: async (route) => {
    const id = route.params.id as string;

    // Check if resource exists
    try {
      await $fetch(`/api/products/${id}/exists`);
      return true;
    } catch {
      return {
        statusCode: 404,
        statusMessage: 'Product not found',
      };
    }
  },
});
</script>
```

## Multiple Parameters

```vue
<!-- pages/[category]/[id].vue -->
<script setup lang="ts">
const VALID_CATEGORIES = ['electronics', 'clothing', 'books', 'home'];

definePageMeta({
  validate: (route) => {
    const category = route.params.category as string;
    const id = route.params.id as string;

    // Validate category
    if (!VALID_CATEGORIES.includes(category)) {
      return {
        statusCode: 404,
        statusMessage: `Category '${category}' not found`,
      };
    }

    // Validate ID format
    if (!/^[a-zA-Z0-9-]+$/.test(id)) {
      return {
        statusCode: 400,
        statusMessage: 'Invalid product ID',
      };
    }

    return true;
  },
});
</script>
```

## Query Parameter Validation

```vue
<script setup lang="ts">
definePageMeta({
  validate: (route) => {
    const page = route.query.page;
    const limit = route.query.limit;

    // Validate pagination params if present
    if (page && (isNaN(Number(page)) || Number(page) < 1)) {
      return {
        statusCode: 400,
        statusMessage: 'Invalid page parameter',
      };
    }

    if (limit && (isNaN(Number(limit)) || Number(limit) < 1 || Number(limit) > 100)) {
      return {
        statusCode: 400,
        statusMessage: 'Invalid limit parameter (1-100)',
      };
    }

    return true;
  },
});
</script>
```

## Reusable Validators

```typescript
// utils/validators.ts
export const validators = {
  uuid: (value: string) => {
    const regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
    return regex.test(value);
  },

  slug: (value: string) => {
    const regex = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
    return regex.test(value);
  },

  numeric: (value: string) => {
    return /^\d+$/.test(value);
  },

  alphanumeric: (value: string) => {
    return /^[a-zA-Z0-9]+$/.test(value);
  },

  date: (value: string) => {
    const date = new Date(value);
    return !isNaN(date.getTime());
  },
};

// Usage in page
definePageMeta({
  validate: (route) => {
    return validators.uuid(route.params.id as string);
  },
});
```

## Validation with Zod

```typescript
// utils/route-schemas.ts
import { z } from 'zod';

export const productParamsSchema = z.object({
  id: z.string().uuid(),
});

export const categoryParamsSchema = z.object({
  category: z.enum(['electronics', 'clothing', 'books']),
  id: z.string().min(1),
});

export const searchQuerySchema = z.object({
  q: z.string().optional(),
  page: z.coerce.number().min(1).default(1),
  limit: z.coerce.number().min(1).max(100).default(20),
  sort: z.enum(['name', 'price', 'date']).optional(),
});
```

```vue
<script setup lang="ts">
import { productParamsSchema } from '~/utils/route-schemas';

definePageMeta({
  validate: (route) => {
    const result = productParamsSchema.safeParse(route.params);

    if (!result.success) {
      return {
        statusCode: 400,
        statusMessage: result.error.issues[0].message,
      };
    }

    return true;
  },
});
</script>
```

## Permission-Based Validation

```vue
<script setup lang="ts">
definePageMeta({
  validate: async (route) => {
    // Get user from cookie or session
    const user = await getCurrentUser();

    if (!user) {
      return {
        statusCode: 401,
        statusMessage: 'Unauthorized',
      };
    }

    const resourceId = route.params.id as string;

    // Check permission
    const hasAccess = await checkAccess(user.id, resourceId);

    if (!hasAccess) {
      return {
        statusCode: 403,
        statusMessage: 'You do not have access to this resource',
      };
    }

    return true;
  },
});
</script>
```

## Combining with Error Page

```vue
<!-- error.vue -->
<script setup lang="ts">
interface Props {
  error: {
    statusCode: number;
    statusMessage: string;
    message?: string;
  };
}

const props = defineProps<Props>();

const handleError = () => clearError({ redirect: '/' });
</script>

<template>
  <div class="error-page">
    <h1>{{ error.statusCode }}</h1>
    <p>{{ error.statusMessage }}</p>
    <button @click="handleError">Go Home</button>
  </div>
</template>
```

## Validation vs Middleware

```typescript
// Validation - for route parameter format
definePageMeta({
  validate: (route) => {
    // Check if ID format is valid
    return /^\d+$/.test(route.params.id as string);
  },
});

// Middleware - for access control
definePageMeta({
  middleware: ['auth'], // Check if user is logged in
});

// Both can be used together
definePageMeta({
  validate: (route) => /^\d+$/.test(route.params.id as string),
  middleware: ['auth', 'owner'],
});
```

## Best Practices

1. **Validate early** - Catch invalid params before data fetching
2. **Be specific** - Provide meaningful error messages
3. **Use reusable validators** - Keep validation logic DRY
4. **Combine approaches** - Use validation + middleware appropriately
5. **Consider UX** - Show helpful error pages
6. **Type safety** - Use Zod for complex validation
