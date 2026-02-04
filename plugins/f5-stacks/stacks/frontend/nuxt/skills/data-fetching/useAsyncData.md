---
name: nuxt-useAsyncData
description: Custom async operations with useAsyncData in Nuxt 3
applies_to: nuxt
---

# useAsyncData in Nuxt 3

## Overview

`useAsyncData` provides SSR-friendly async data fetching for complex operations beyond simple HTTP requests.

## Basic Usage

```typescript
const { data, pending, error, refresh } = await useAsyncData(
  'unique-key',
  async () => {
    // Any async operation
    const result = await someAsyncFunction();
    return result;
  }
);
```

## When to Use

### useAsyncData vs useFetch

```typescript
// useFetch - Simple API calls
const { data } = await useFetch('/api/products');

// useAsyncData - Complex operations
const { data } = await useAsyncData('products-with-processing', async () => {
  const products = await $fetch('/api/products');
  const categories = await $fetch('/api/categories');

  // Process and combine data
  return products.map((product) => ({
    ...product,
    categoryName: categories.find((c) => c.id === product.categoryId)?.name,
  }));
});
```

## Key Parameter

The key uniquely identifies the data and enables caching:

```typescript
// Static key
const { data } = await useAsyncData('user-profile', fetchProfile);

// Dynamic key
const route = useRoute();
const { data } = await useAsyncData(
  `product-${route.params.id}`,
  () => fetchProduct(route.params.id as string)
);

// Computed key
const { data } = await useAsyncData(
  () => `search-${searchQuery.value}`,
  () => searchProducts(searchQuery.value)
);
```

## Options

```typescript
const { data } = await useAsyncData('key', fetchFunction, {
  // Server-side execution
  server: true, // default

  // Lazy loading (don't block navigation)
  lazy: false, // default

  // Execute immediately
  immediate: true, // default

  // Default value
  default: () => [],

  // Transform response
  transform: (data) => data.items,

  // Pick specific fields
  pick: ['name', 'email'],

  // Watch reactive sources
  watch: [page, filters],

  // Deep watch
  deep: true,

  // Custom cache behavior
  getCachedData: (key) => nuxtApp.payload.data[key],
});
```

## Parallel Fetching

```typescript
// Bad - Sequential (slow)
const { data: users } = await useAsyncData('users', fetchUsers);
const { data: posts } = await useAsyncData('posts', fetchPosts);

// Good - Parallel (fast)
const [{ data: users }, { data: posts }] = await Promise.all([
  useAsyncData('users', fetchUsers),
  useAsyncData('posts', fetchPosts),
]);
```

## Dependent Fetching

```typescript
// Fetch user first, then their posts
const { data: user } = await useAsyncData('user', () =>
  $fetch(`/api/users/${userId}`)
);

// Only fetch posts when user exists
const { data: posts } = await useAsyncData(
  'user-posts',
  () => $fetch(`/api/users/${user.value?.id}/posts`),
  {
    // Wait for user
    watch: [user],
    // Only execute when user exists
    immediate: !!user.value,
  }
);
```

## Transform Data

```typescript
interface ApiResponse {
  data: {
    items: Product[];
    pagination: {
      total: number;
      page: number;
    };
  };
}

const { data } = await useAsyncData<ApiResponse, Product[]>(
  'products',
  () => $fetch('/api/products'),
  {
    transform: (response) => response.data.items,
  }
);
// data is Ref<Product[] | null>
```

## Error Handling

```typescript
const { data, error, status } = await useAsyncData('products', async () => {
  const response = await $fetch('/api/products');

  if (!response.success) {
    throw createError({
      statusCode: 400,
      message: response.message,
    });
  }

  return response.data;
});

// In template
<template>
  <div v-if="status === 'pending'">Loading...</div>
  <div v-else-if="status === 'error'">
    <p>Error: {{ error?.message }}</p>
    <button @click="refresh()">Retry</button>
  </div>
  <div v-else-if="data">
    <!-- Content -->
  </div>
</template>
```

## Refresh and Execute

```typescript
const { data, refresh, execute, clear } = await useAsyncData(
  'products',
  fetchProducts
);

// Re-fetch data
async function handleRefresh() {
  await refresh(); // Uses cache if available
  // or
  await refresh({ dedupe: true }); // Dedupe concurrent calls
}

// Force re-fetch (ignore cache)
async function forceRefresh() {
  await execute({ force: true });
}

// Clear data
function clearData() {
  clear(); // Sets data to default, clears error
}
```

## Lazy Async Data

```typescript
// Don't block navigation
const { data, pending } = await useLazyAsyncData('products', fetchProducts);

// Or with option
const { data } = await useAsyncData('products', fetchProducts, {
  lazy: true,
});
```

## Server-Only Fetch

```typescript
// Only run on server, skip on client navigation
const { data } = await useAsyncData(
  'server-data',
  async () => {
    // This only runs on SSR
    const secrets = await getServerSecrets();
    return processData(secrets);
  },
  {
    server: true,
    // Don't re-fetch on client
    lazy: true,
    getCachedData: (key) => nuxtApp.payload.data[key],
  }
);
```

## With Database Queries

```typescript
// Server-side database query
const { data: products } = await useAsyncData('products', async () => {
  // This runs on server during SSR
  if (import.meta.server) {
    const { prisma } = await import('~/server/utils/db');
    return prisma.product.findMany({
      include: { category: true },
    });
  }

  // Falls back to API on client
  return $fetch('/api/products');
});
```

## Pagination Pattern

```typescript
const route = useRoute();
const router = useRouter();

const page = computed({
  get: () => Number(route.query.page) || 1,
  set: (value) => router.push({ query: { ...route.query, page: value } }),
});

const { data, pending, refresh } = await useAsyncData(
  () => `products-page-${page.value}`,
  () =>
    $fetch('/api/products', {
      query: { page: page.value, limit: 20 },
    }),
  {
    watch: [page],
  }
);
```

## Composable Pattern

```typescript
// composables/useProductsData.ts
export function useProductsData(options?: { categoryId?: string }) {
  const key = computed(() =>
    options?.categoryId ? `products-${options.categoryId}` : 'products-all'
  );

  return useAsyncData(
    key,
    async () => {
      const query = options?.categoryId
        ? { categoryId: options.categoryId }
        : {};

      const response = await $fetch<ProductsResponse>('/api/products', {
        query,
      });

      return {
        products: response.items,
        total: response.total,
        hasMore: response.page < response.totalPages,
      };
    },
    {
      default: () => ({ products: [], total: 0, hasMore: false }),
    }
  );
}
```

## Best Practices

1. **Unique keys** - Always use descriptive, unique keys
2. **Type your data** - Use TypeScript generics
3. **Parallelize fetches** - Use Promise.all for independent data
4. **Transform on server** - Reduce client-side processing
5. **Handle all states** - pending, error, success
6. **Use composables** - Encapsulate complex logic
