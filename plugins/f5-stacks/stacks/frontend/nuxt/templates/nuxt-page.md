---
name: nuxt-page
description: Template for Nuxt 3 page components
applies_to: nuxt
---

# Nuxt Page Template

## Basic Page

```vue
<script setup lang="ts">
// Page metadata
definePageMeta({
  title: '{{PAGE_TITLE}}',
  layout: '{{LAYOUT}}',
  middleware: ['{{MIDDLEWARE}}'],
});

// SEO
useSeoMeta({
  title: '{{PAGE_TITLE}}',
  description: '{{PAGE_DESCRIPTION}}',
  ogTitle: '{{PAGE_TITLE}}',
  ogDescription: '{{PAGE_DESCRIPTION}}',
});

// Data fetching
const { data, pending, error, refresh } = await useFetch('/api/{{RESOURCE}}');
</script>

<template>
  <div class="{{PAGE_NAME}}-page">
    <h1>{{PAGE_TITLE}}</h1>

    <!-- Loading state -->
    <div v-if="pending">Loading...</div>

    <!-- Error state -->
    <div v-else-if="error">
      <p>Error: {{ error.message }}</p>
      <button @click="refresh">Retry</button>
    </div>

    <!-- Content -->
    <div v-else>
      <!-- Page content here -->
    </div>
  </div>
</template>

<style scoped>
.{{PAGE_NAME}}-page {
  /* Page styles */
}
</style>
```

## Page with Parameters

```vue
<script setup lang="ts">
const route = useRoute();
const id = computed(() => route.params.id as string);

// Fetch single resource
const { data: item, pending, error } = await useFetch(
  () => `/api/{{RESOURCE}}/${id.value}`,
  { watch: [id] }
);

// 404 handling
if (!item.value && !pending.value) {
  throw createError({
    statusCode: 404,
    statusMessage: '{{RESOURCE_NAME}} not found',
  });
}

definePageMeta({
  validate: async (route) => {
    return /^\d+$/.test(route.params.id as string);
  },
});
</script>

<template>
  <div class="{{PAGE_NAME}}-detail">
    <template v-if="pending">
      <div class="skeleton">Loading...</div>
    </template>

    <template v-else-if="item">
      <h1>{{ item.name }}</h1>
      <!-- Detail content -->
    </template>
  </div>
</template>
```

## Page with Form

```vue
<script setup lang="ts">
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Invalid email'),
});

type FormData = z.infer<typeof schema>;

const form = reactive<FormData>({
  name: '',
  email: '',
});

const errors = ref<Record<string, string>>({});
const isSubmitting = ref(false);

async function handleSubmit() {
  errors.value = {};

  const result = schema.safeParse(form);
  if (!result.success) {
    result.error.errors.forEach((err) => {
      errors.value[err.path[0]] = err.message;
    });
    return;
  }

  isSubmitting.value = true;
  try {
    await $fetch('/api/{{RESOURCE}}', {
      method: 'POST',
      body: form,
    });
    navigateTo('/{{RESOURCE}}');
  } catch (err) {
    errors.value.form = 'Submission failed';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div class="{{PAGE_NAME}}-form">
    <h1>Create {{RESOURCE_NAME}}</h1>

    <form @submit.prevent="handleSubmit">
      <div class="field">
        <label for="name">Name</label>
        <input id="name" v-model="form.name" type="text" />
        <span v-if="errors.name" class="error">{{ errors.name }}</span>
      </div>

      <div class="field">
        <label for="email">Email</label>
        <input id="email" v-model="form.email" type="email" />
        <span v-if="errors.email" class="error">{{ errors.email }}</span>
      </div>

      <div v-if="errors.form" class="form-error">{{ errors.form }}</div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Saving...' : 'Save' }}
      </button>
    </form>
  </div>
</template>
```

## Protected Page

```vue
<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
});

const { user } = useAuth();
</script>

<template>
  <div class="protected-page">
    <h1>Welcome, {{ user?.name }}</h1>
    <!-- Protected content -->
  </div>
</template>
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{PAGE_NAME}}` | Page identifier | `products`, `users` |
| `{{PAGE_TITLE}}` | Display title | `Products`, `User List` |
| `{{PAGE_DESCRIPTION}}` | SEO description | `Browse our products` |
| `{{RESOURCE}}` | API resource name | `products`, `users` |
| `{{RESOURCE_NAME}}` | Human-readable name | `Product`, `User` |
| `{{LAYOUT}}` | Layout name | `default`, `admin` |
| `{{MIDDLEWARE}}` | Middleware name | `auth`, `guest` |
