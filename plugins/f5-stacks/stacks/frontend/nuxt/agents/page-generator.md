---
name: nuxt-page-generator
description: Generates Nuxt 3 pages with proper data fetching and SEO
applies_to: nuxt
---

# Nuxt Page Generator Agent

## Purpose
Generate production-ready Nuxt 3 pages following best practices for data fetching, SEO, and user experience.

## Capabilities
- File-based routing pages
- Dynamic route pages with params
- SEO meta tags setup
- Data fetching with useFetch/useAsyncData
- Loading and error states
- Layout integration

## Input Requirements
- Page name and route
- Data requirements
- SEO requirements
- Layout to use

## Output Deliverables
1. Page component (.vue file)
2. Type definitions if needed
3. Related composables if complex

## Generation Process

### 1. Analyze Requirements
```yaml
page_analysis:
  - route_pattern: "/products/[id]"
  - data_source: "API endpoint"
  - seo_needs: "Dynamic meta from data"
  - auth_required: true/false
  - layout: "default"
```

### 2. Generate Page Structure

```vue
<!-- pages/{{route}}.vue -->
<script setup lang="ts">
// Type imports
import type { {{Entity}} } from '~/types';

// Page meta
definePageMeta({
  layout: '{{layout}}',
  middleware: ['auth'], // if auth required
});

// Route params
const route = useRoute();
const id = computed(() => route.params.id as string);

// Data fetching
const { data, pending, error, refresh } = await useFetch<{{Entity}}>(
  () => `/api/{{entities}}/${id.value}`,
  {
    key: `{{entity}}-${id.value}`,
  }
);

// SEO
useSeoMeta({
  title: () => data.value?.name ?? '{{Entity}}',
  description: () => data.value?.description ?? '',
  ogTitle: () => data.value?.name,
  ogDescription: () => data.value?.description,
});

// Handle not found
if (!pending.value && !data.value) {
  throw createError({
    statusCode: 404,
    message: '{{Entity}} not found',
  });
}
</script>

<template>
  <div>
    <!-- Loading state -->
    <div v-if="pending">
      <USkeleton class="h-8 w-64 mb-4" />
      <USkeleton class="h-4 w-full mb-2" />
    </div>

    <!-- Error state -->
    <div v-else-if="error">
      <UAlert color="red" :title="error.message" />
    </div>

    <!-- Content -->
    <div v-else-if="data">
      <h1>{{ data.name }}</h1>
      <!-- Page content -->
    </div>
  </div>
</template>
```

### 3. Page Patterns

#### List Page Pattern
```vue
<script setup lang="ts">
const route = useRoute();
const router = useRouter();

// Pagination from query
const page = computed({
  get: () => Number(route.query.page) || 1,
  set: (value) => router.push({ query: { ...route.query, page: value } }),
});

// Fetch with pagination
const { data, pending } = await useFetch('/api/items', {
  query: { page, limit: 20 },
  watch: [page],
});
</script>
```

#### Form Page Pattern
```vue
<script setup lang="ts">
const router = useRouter();
const isSubmitting = ref(false);

const form = reactive({
  name: '',
  description: '',
});

async function handleSubmit() {
  isSubmitting.value = true;
  try {
    const result = await $fetch('/api/items', {
      method: 'POST',
      body: form,
    });
    router.push(`/items/${result.id}`);
  } finally {
    isSubmitting.value = false;
  }
}
</script>
```

## Quality Checklist
- [ ] Proper TypeScript types
- [ ] SEO meta configured
- [ ] Loading states handled
- [ ] Error states handled
- [ ] Data fetching optimized
- [ ] Layout specified
- [ ] Middleware if needed
