---
name: nuxt-universal-rendering
description: Server-side rendering and hydration in Nuxt 3
applies_to: nuxt
---

# Universal Rendering in Nuxt 3

## Overview

Universal rendering (SSR) renders pages on the server first, then hydrates them on the client for interactivity.

## How It Works

```
1. User requests page
2. Server renders Vue components to HTML
3. HTML sent to browser (fast initial paint)
4. JavaScript loads and hydrates components
5. Page becomes interactive (SPA behavior)
```

## Default Behavior

Nuxt 3 uses universal rendering by default.

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  // Default - universal rendering
  ssr: true,
});
```

## SSR Data Fetching

### useFetch
```vue
<script setup lang="ts">
// Fetches on server during SSR, then hydrates
const { data, pending, error } = await useFetch('/api/products');
</script>

<template>
  <div v-if="pending">Loading...</div>
  <div v-else-if="error">{{ error.message }}</div>
  <ul v-else>
    <li v-for="product in data" :key="product.id">
      {{ product.name }}
    </li>
  </ul>
</template>
```

### useAsyncData
```vue
<script setup lang="ts">
// Custom async operation
const { data: user } = await useAsyncData('user', async () => {
  const session = await getSession();
  if (!session) return null;
  return await fetchUser(session.userId);
});
</script>
```

## SSR vs Client-Only Data

```vue
<script setup lang="ts">
// Runs on both server and client
const { data: products } = await useFetch('/api/products');

// Client-only - won't run during SSR
onMounted(() => {
  // Browser-only code
  window.scrollTo(0, 0);
});
</script>
```

## Lifecycle in SSR

```vue
<script setup lang="ts">
// Runs on server AND client
console.log('Setup runs on both');

// Server only
if (import.meta.server) {
  console.log('Server only');
}

// Client only
if (import.meta.client) {
  console.log('Client only');
}

// Never runs on server
onMounted(() => {
  console.log('Client only - after hydration');
});

// Runs on both for cleanup
onUnmounted(() => {
  console.log('Cleanup');
});
</script>
```

## Handling Hydration Mismatches

### Common Causes
1. Browser-only APIs used during render
2. Date/time differences
3. Random values
4. Dynamic IDs

### Solutions

```vue
<script setup lang="ts">
// Bad - causes mismatch
const timestamp = Date.now();

// Good - consistent between server/client
const { data: timestamp } = await useAsyncData('time', () => Date.now());

// Good - render different content with ClientOnly
</script>

<template>
  <!-- Shows placeholder on server, real content on client -->
  <ClientOnly>
    <BrowserOnlyComponent />
    <template #fallback>
      <p>Loading...</p>
    </template>
  </ClientOnly>
</template>
```

## Request Context in SSR

```vue
<script setup lang="ts">
// Access request during SSR
const event = useRequestEvent();
const headers = useRequestHeaders(['cookie', 'authorization']);
const url = useRequestURL();

// Get cookies
const sessionId = useCookie('session-id');

// Runtime config (server secrets available on server)
const config = useRuntimeConfig();
if (import.meta.server) {
  console.log(config.apiSecret); // Server only
}
console.log(config.public.apiBase); // Both
</script>
```

## SSR-Safe Patterns

### ID Generation
```vue
<script setup lang="ts">
// Good - stable across server/client
const id = useId();
</script>

<template>
  <label :for="id">Name</label>
  <input :id="id" name="name" />
</template>
```

### Random Data
```vue
<script setup lang="ts">
// Bad
const items = products.sort(() => Math.random() - 0.5);

// Good - seed on server, use same on client
const { data: shuffled } = await useAsyncData('shuffled', () => {
  return shuffleWithSeed(products, Date.now());
});
</script>
```

## Head Management in SSR

```vue
<script setup lang="ts">
const { data: product } = await useFetch(`/api/products/${id}`);

// Rendered in server HTML
useHead({
  title: product.value?.name,
  meta: [
    { name: 'description', content: product.value?.description },
  ],
});

// Or use useSeoMeta for SEO
useSeoMeta({
  title: product.value?.name,
  ogTitle: product.value?.name,
  description: product.value?.description,
  ogDescription: product.value?.description,
  ogImage: product.value?.image,
});
</script>
```

## Error Handling in SSR

```vue
<script setup lang="ts">
const { data, error } = await useFetch('/api/products');

// Throw error page
if (error.value) {
  throw createError({
    statusCode: 500,
    message: 'Failed to load products',
  });
}

// Or show 404
if (!data.value) {
  throw createError({
    statusCode: 404,
    message: 'Product not found',
  });
}
</script>
```

## Performance Optimization

### Caching
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  routeRules: {
    // Cache for 1 hour
    '/api/**': { cache: { maxAge: 60 * 60 } },
    // Prerender at build
    '/about': { prerender: true },
  },
});
```

### Streaming
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  nitro: {
    experimental: {
      // Enable streaming responses
      streamResponse: true,
    },
  },
});
```

## Best Practices

1. **Use appropriate data fetching** - useFetch for SSR data
2. **Avoid browser APIs** - Use ClientOnly or import.meta.client
3. **Handle errors properly** - createError for error pages
4. **Optimize with caching** - Use routeRules for caching
5. **SEO with useHead** - Set meta during SSR
