---
name: nuxt-useFetch
description: Data fetching with useFetch in Nuxt 3
applies_to: nuxt
---

# useFetch in Nuxt 3

## Overview

`useFetch` is the primary composable for data fetching in Nuxt 3. It provides SSR support, caching, and reactive data handling.

## Basic Usage

```vue
<script setup lang="ts">
interface Product {
  id: string;
  name: string;
  price: number;
}

// Simple fetch
const { data, pending, error, refresh } = await useFetch<Product[]>('/api/products');
</script>

<template>
  <div v-if="pending">Loading...</div>
  <div v-else-if="error">Error: {{ error.message }}</div>
  <ul v-else>
    <li v-for="product in data" :key="product.id">
      {{ product.name }} - ${{ product.price }}
    </li>
  </ul>
</template>
```

## Return Values

```typescript
const {
  data,        // Ref<T | null> - Response data
  pending,     // Ref<boolean> - Loading state
  error,       // Ref<Error | null> - Error if any
  status,      // Ref<'idle' | 'pending' | 'success' | 'error'>
  refresh,     // () => Promise<void> - Re-fetch data
  execute,     // () => Promise<void> - Same as refresh
  clear,       // () => void - Clear data and error
} = await useFetch('/api/products');
```

## Options

### Request Options

```typescript
const { data } = await useFetch('/api/products', {
  // HTTP method
  method: 'GET', // 'POST', 'PUT', 'DELETE', etc.

  // Query parameters
  query: {
    page: 1,
    limit: 20,
    search: 'test',
  },

  // Request body (for POST, PUT)
  body: {
    name: 'Product',
    price: 99.99,
  },

  // Headers
  headers: {
    'X-Custom-Header': 'value',
  },

  // Base URL
  baseURL: 'https://api.example.com',

  // Timeout
  timeout: 5000,
});
```

### Behavior Options

```typescript
const { data } = await useFetch('/api/products', {
  // Don't block navigation
  lazy: false, // default: false

  // Fetch immediately
  immediate: true, // default: true

  // Fetch on server
  server: true, // default: true

  // Default value
  default: () => [],

  // Cache key
  key: 'products-list',

  // Watch reactive sources
  watch: [page, filters],

  // Deep watch
  deep: true,

  // Pick specific fields from response
  pick: ['items', 'total'],

  // Transform response
  transform: (response) => response.items,
});
```

## Dynamic URLs

```typescript
// Computed URL
const productId = ref('123');
const { data } = await useFetch(() => `/api/products/${productId.value}`);

// URL changes trigger re-fetch
productId.value = '456'; // Automatically re-fetches
```

## Query Parameters

```typescript
// Reactive query params
const page = ref(1);
const search = ref('');

const { data } = await useFetch('/api/products', {
  query: {
    page,
    search,
    limit: 20,
  },
  // Re-fetch when page or search changes
  watch: [page, search],
});
```

## Request Interceptors

```typescript
const { data } = await useFetch('/api/products', {
  // Before request
  onRequest({ request, options }) {
    // Add auth header
    const token = useCookie('auth-token');
    options.headers = options.headers || {};
    options.headers.Authorization = `Bearer ${token.value}`;
  },

  // Request error
  onRequestError({ request, options, error }) {
    console.error('Request failed:', error);
  },

  // After response
  onResponse({ request, response, options }) {
    // Log response
    console.log('Response:', response._data);
  },

  // Response error
  onResponseError({ request, response, options }) {
    if (response.status === 401) {
      navigateTo('/login');
    }
  },
});
```

## Lazy Fetch

```typescript
// Don't block navigation - fetch after mount
const { data, pending } = await useLazyFetch('/api/products');

// Or with option
const { data } = await useFetch('/api/products', { lazy: true });
```

## Manual Fetch

```typescript
// Don't fetch automatically
const { data, execute } = await useFetch('/api/products', {
  immediate: false,
});

// Fetch when needed
async function loadProducts() {
  await execute();
}
</script>

<template>
  <button @click="loadProducts">Load Products</button>
  <ProductList v-if="data" :products="data" />
</template>
```

## POST/PUT/DELETE

```typescript
// POST
async function createProduct(productData: CreateProductInput) {
  const { data, error } = await useFetch('/api/products', {
    method: 'POST',
    body: productData,
  });

  if (!error.value) {
    navigateTo(`/products/${data.value.id}`);
  }
}

// PUT
async function updateProduct(id: string, updates: Partial<Product>) {
  const { data } = await useFetch(`/api/products/${id}`, {
    method: 'PUT',
    body: updates,
  });
  return data.value;
}

// DELETE
async function deleteProduct(id: string) {
  await useFetch(`/api/products/${id}`, {
    method: 'DELETE',
  });
}
```

## Caching

```typescript
// Default caching by key
const { data } = await useFetch('/api/products', {
  key: 'products',
});

// Custom cache control
const { data } = await useFetch('/api/products', {
  key: 'products',
  getCachedData: (key) => {
    const cached = nuxtApp.payload.data[key];
    if (!cached) return null;

    // Check if cache is stale (5 minutes)
    const expiresAt = cached._expiresAt;
    if (expiresAt && Date.now() > expiresAt) return null;

    return cached;
  },
  transform: (data) => ({
    ...data,
    _expiresAt: Date.now() + 5 * 60 * 1000,
  }),
});
```

## Error Handling

```typescript
const { data, error } = await useFetch('/api/products');

// Check for error
if (error.value) {
  // Handle specific status codes
  if (error.value.statusCode === 404) {
    throw createError({
      statusCode: 404,
      message: 'Products not found',
    });
  }

  // Handle network errors
  console.error('Fetch error:', error.value.message);
}
```

## Composable Pattern

```typescript
// composables/useProducts.ts
export function useProducts() {
  const route = useRoute();

  const page = computed(() => Number(route.query.page) || 1);
  const search = computed(() => (route.query.q as string) || '');

  const { data, pending, error, refresh } = useFetch<ProductsResponse>(
    '/api/products',
    {
      query: { page, search, limit: 20 },
      watch: [page, search],
    }
  );

  const products = computed(() => data.value?.items ?? []);
  const total = computed(() => data.value?.total ?? 0);

  return {
    products,
    total,
    pending,
    error,
    refresh,
  };
}
```

## Best Practices

1. **Type your responses** - Use TypeScript generics
2. **Use keys for caching** - Explicit keys for predictable caching
3. **Handle loading states** - Always show loading indicators
4. **Handle errors gracefully** - Show user-friendly messages
5. **Use composables** - Wrap complex fetch logic
6. **Avoid waterfalls** - Parallelize independent fetches
