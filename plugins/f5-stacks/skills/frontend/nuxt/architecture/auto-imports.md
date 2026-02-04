---
name: nuxt-auto-imports
description: Nuxt 3 auto-import system for components and composables
applies_to: nuxt
---

# Nuxt Auto-Imports

## Overview

Nuxt 3 automatically imports components, composables, and utilities without explicit import statements.

## Auto-Imported Directories

### Components (components/)

```
components/
├── Button.vue           # <Button />
├── ui/
│   └── Card.vue         # <UiCard />
└── forms/
    └── Input.vue        # <FormsInput />
```

Usage:
```vue
<template>
  <div>
    <!-- No import needed -->
    <Button>Click me</Button>
    <UiCard>Content</UiCard>
    <FormsInput v-model="value" />
  </div>
</template>
```

### Composables (composables/)

```
composables/
├── useAuth.ts           # useAuth()
├── useProducts.ts       # useProducts()
└── api/
    └── useApi.ts        # useApi()
```

```typescript
// composables/useCounter.ts
export function useCounter(initial = 0) {
  const count = ref(initial);
  const increment = () => count.value++;
  const decrement = () => count.value--;
  return { count, increment, decrement };
}

// Usage in any component - no import needed
const { count, increment } = useCounter(10);
```

### Utils (utils/)

```
utils/
├── format.ts            # formatDate(), formatCurrency()
└── validation.ts        # validateEmail()
```

```typescript
// utils/format.ts
export function formatDate(date: Date): string {
  return new Intl.DateTimeFormat('en-US').format(date);
}

export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
}

// Usage anywhere - no import needed
const formatted = formatDate(new Date());
```

## Vue & Nuxt Auto-Imports

### Vue Reactivity
```typescript
// All Vue APIs auto-imported
const count = ref(0);
const doubled = computed(() => count.value * 2);
const state = reactive({ name: '', email: '' });

watch(count, (newVal) => console.log(newVal));
watchEffect(() => console.log(count.value));

onMounted(() => console.log('Mounted'));
onUnmounted(() => console.log('Unmounted'));
```

### Nuxt Composables
```typescript
// Route & Navigation
const route = useRoute();
const router = useRouter();
navigateTo('/dashboard');

// Data Fetching
const { data } = await useFetch('/api/products');
const { data: asyncData } = await useAsyncData('key', () => fetchData());

// State
const user = useState('user', () => null);

// Runtime Config
const config = useRuntimeConfig();
console.log(config.public.apiBase);

// App Config
const appConfig = useAppConfig();

// Head/SEO
useHead({ title: 'Page Title' });
useSeoMeta({ title: 'SEO Title' });

// Cookies
const token = useCookie('auth-token');

// Error
const error = useError();
clearError();
createError({ statusCode: 404 });

// Request
const event = useRequestEvent();
const headers = useRequestHeaders();
const url = useRequestURL();
```

## Custom Auto-Import Configuration

### nuxt.config.ts
```typescript
export default defineNuxtConfig({
  imports: {
    // Add custom directories
    dirs: [
      'composables/**',
      'utils/**',
      'stores',
    ],

    // Disable auto-imports (not recommended)
    autoImport: true,

    // Add custom imports
    imports: [
      {
        name: 'default',
        as: 'dayjs',
        from: 'dayjs',
      },
      {
        name: 'useI18n',
        from: 'vue-i18n',
      },
    ],
  },

  components: {
    dirs: [
      '~/components',
      {
        path: '~/components/ui',
        prefix: 'Ui',
      },
    ],
  },
});
```

## Component Auto-Import Patterns

### Prefixed Components
```
components/
├── base/
│   └── Button.vue       # <BaseButton />
├── app/
│   └── Header.vue       # <AppHeader />
└── lazy/
    └── HeavyChart.vue   # <LazyHeavyChart /> (lazy loaded)
```

### Global Components
```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  components: {
    global: true,  // Make all components global
    dirs: ['~/components'],
  },
});
```

### Lazy Loading Components
```vue
<template>
  <!-- Prefix with Lazy for automatic code splitting -->
  <LazyHeavyChart v-if="showChart" />

  <!-- Or use explicit lazy loading -->
  <LazyModal v-if="isOpen" />
</template>
```

## Server Auto-Imports

### Server Utils (server/utils/)
```typescript
// server/utils/auth.ts
export function requireAuth(event: H3Event) {
  const token = getHeader(event, 'authorization');
  if (!token) {
    throw createError({ statusCode: 401 });
  }
  return verifyToken(token);
}

// Usage in API routes - no import needed
export default defineEventHandler(async (event) => {
  const user = await requireAuth(event);
  // ...
});
```

### H3 Utilities
```typescript
// Auto-imported from H3
defineEventHandler((event) => {
  const query = getQuery(event);
  const body = await readBody(event);
  const params = getRouterParams(event);
  const headers = getHeaders(event);
  const cookies = parseCookies(event);

  setResponseStatus(event, 201);
  setHeader(event, 'X-Custom', 'value');
  setCookie(event, 'session', 'value');

  return { success: true };
});
```

## Type Support

### Generated Types
```typescript
// .nuxt/types/imports.d.ts (auto-generated)
// Provides type definitions for all auto-imports

// Your composables get full type support
const { data } = await useFetch<Product[]>('/api/products');
//      ^? Ref<Product[] | null>
```

### Explicit Types
```typescript
// composables/useProducts.ts
import type { Product } from '~/types';

export function useProducts() {
  const products = ref<Product[]>([]);
  // ...
  return { products };
}
```

## Best Practices

1. **Trust auto-imports** - Don't manually import what Nuxt provides
2. **Naming conventions** - Use prefixes for organization (useAuth, UiButton)
3. **Type definitions** - Keep types in separate files for clarity
4. **Avoid circular deps** - Be careful with cross-imports between composables
5. **Check .nuxt/types** - For debugging auto-import issues
