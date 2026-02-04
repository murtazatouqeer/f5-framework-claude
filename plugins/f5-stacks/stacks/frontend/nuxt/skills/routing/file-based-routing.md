---
name: nuxt-file-based-routing
description: File-based routing system in Nuxt 3
applies_to: nuxt
---

# File-Based Routing in Nuxt 3

## Overview

Nuxt 3 automatically generates routes based on the file structure in the `pages/` directory.

## Basic Routes

```
pages/
├── index.vue          # /
├── about.vue          # /about
├── contact.vue        # /contact
└── products.vue       # /products
```

## Nested Routes

```
pages/
├── products/
│   ├── index.vue      # /products
│   └── [id].vue       # /products/:id
└── users/
    ├── index.vue      # /users
    ├── [id].vue       # /users/:id
    └── [id]/
        ├── index.vue  # /users/:id
        └── edit.vue   # /users/:id/edit
```

## Dynamic Routes

### Single Parameter

```
pages/
└── products/
    └── [id].vue       # /products/:id
```

```vue
<!-- pages/products/[id].vue -->
<script setup lang="ts">
const route = useRoute();
const id = computed(() => route.params.id as string);

const { data: product } = await useFetch(`/api/products/${id.value}`);
</script>
```

### Multiple Parameters

```
pages/
└── [category]/
    └── [id].vue       # /:category/:id
```

```vue
<!-- pages/[category]/[id].vue -->
<script setup lang="ts">
const route = useRoute();
const category = computed(() => route.params.category as string);
const id = computed(() => route.params.id as string);
</script>
```

### Optional Parameters

```
pages/
└── [[slug]].vue       # / and /:slug
```

```vue
<!-- pages/[[slug]].vue -->
<script setup lang="ts">
const route = useRoute();
const slug = computed(() => route.params.slug as string | undefined);

// Handles both / and /anything
</script>
```

## Catch-All Routes

```
pages/
├── [...slug].vue      # Catches all: /a, /a/b, /a/b/c
└── products/
    └── [...].vue      # Catches all under /products/
```

```vue
<!-- pages/[...slug].vue -->
<script setup lang="ts">
const route = useRoute();
// slug is array: ['a', 'b', 'c'] for /a/b/c
const segments = computed(() => route.params.slug as string[]);
</script>

<template>
  <div>
    <p>Path segments: {{ segments?.join('/') }}</p>
  </div>
</template>
```

## Named Routes

```vue
<script setup lang="ts">
const router = useRouter();

// Navigate by name
router.push({ name: 'products-id', params: { id: '123' } });
</script>

<template>
  <!-- Link by name -->
  <NuxtLink :to="{ name: 'products-id', params: { id: '123' } }">
    Product
  </NuxtLink>
</template>
```

Route names are auto-generated:
- `pages/index.vue` → `index`
- `pages/products/index.vue` → `products`
- `pages/products/[id].vue` → `products-id`
- `pages/users/[id]/edit.vue` → `users-id-edit`

## NuxtLink Component

```vue
<template>
  <!-- Basic link -->
  <NuxtLink to="/about">About</NuxtLink>

  <!-- With params -->
  <NuxtLink :to="`/products/${product.id}`">
    {{ product.name }}
  </NuxtLink>

  <!-- Named route -->
  <NuxtLink :to="{ name: 'products-id', params: { id: product.id } }">
    {{ product.name }}
  </NuxtLink>

  <!-- With query -->
  <NuxtLink :to="{ path: '/products', query: { page: 2 } }">
    Page 2
  </NuxtLink>

  <!-- External link -->
  <NuxtLink to="https://example.com" external>
    External
  </NuxtLink>

  <!-- Prefetch control -->
  <NuxtLink to="/heavy-page" :prefetch="false">
    Don't prefetch
  </NuxtLink>

  <!-- No prefetch -->
  <NuxtLink to="/page" no-prefetch>Link</NuxtLink>

  <!-- Active class -->
  <NuxtLink
    to="/products"
    active-class="text-primary"
    exact-active-class="font-bold"
  >
    Products
  </NuxtLink>

  <!-- Replace history -->
  <NuxtLink to="/page" replace>Replace</NuxtLink>
</template>
```

## Programmatic Navigation

```vue
<script setup lang="ts">
const router = useRouter();
const route = useRoute();

// Navigate
function goToProduct(id: string) {
  router.push(`/products/${id}`);
}

// With options
function navigate() {
  router.push({
    path: '/products',
    query: { page: 2, sort: 'name' },
    hash: '#section',
  });
}

// Replace (no history entry)
function replace() {
  router.replace('/new-page');
}

// Go back
function goBack() {
  router.back();
}

// Access current route
console.log(route.path);      // /products/123
console.log(route.params);    // { id: '123' }
console.log(route.query);     // { sort: 'name' }
console.log(route.hash);      // #section
console.log(route.fullPath);  // /products/123?sort=name#section
</script>
```

## navigateTo Utility

```typescript
// In setup, middleware, plugins
async function handleLogin() {
  await login();

  // Navigate after action
  await navigateTo('/dashboard');

  // With options
  await navigateTo('/dashboard', {
    replace: true,
    redirectCode: 301,
    external: false,
  });

  // External URL
  await navigateTo('https://example.com', { external: true });
}
```

## Query Parameters

```vue
<script setup lang="ts">
const route = useRoute();
const router = useRouter();

// Read query params
const page = computed(() => Number(route.query.page) || 1);
const search = computed(() => (route.query.q as string) || '');

// Update query params
function setPage(newPage: number) {
  router.push({
    query: { ...route.query, page: newPage },
  });
}

// Remove query param
function clearSearch() {
  const { q, ...rest } = route.query;
  router.push({ query: rest });
}
</script>
```

## Page Meta

```vue
<script setup lang="ts">
definePageMeta({
  // Page title (used by layouts)
  title: 'Products',

  // Layout to use
  layout: 'admin',

  // Middleware
  middleware: ['auth', 'admin'],

  // Transition
  pageTransition: {
    name: 'page',
    mode: 'out-in',
  },

  // Keep alive
  keepalive: true,

  // Custom meta
  customData: 'value',
});
</script>
```

## Route Validation

```vue
<script setup lang="ts">
definePageMeta({
  validate: async (route) => {
    // Check if id is valid UUID
    const id = route.params.id as string;
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

    if (!uuidRegex.test(id)) {
      return false; // Shows 404
    }

    // Or return error object
    return {
      statusCode: 404,
      statusMessage: 'Invalid product ID',
    };
  },
});
</script>
```

## Custom Routes

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  hooks: {
    'pages:extend'(pages) {
      // Add custom route
      pages.push({
        name: 'custom',
        path: '/custom-path',
        file: '~/pages/custom.vue',
      });

      // Modify existing routes
      const aboutPage = pages.find((p) => p.path === '/about');
      if (aboutPage) {
        aboutPage.path = '/about-us';
      }
    },
  },
});
```

## Route Groups (Organization Only)

```
pages/
├── (marketing)/           # Group - not in URL
│   ├── about.vue          # /about
│   └── pricing.vue        # /pricing
└── (app)/
    ├── dashboard.vue      # /dashboard
    └── settings.vue       # /settings
```

## Best Practices

1. **Use dynamic routes** - For parameterized URLs
2. **Keep structure flat** - Avoid deep nesting
3. **Validate params** - Use definePageMeta validate
4. **Use NuxtLink** - For internal navigation
5. **Define page meta** - For SEO, auth, layout
