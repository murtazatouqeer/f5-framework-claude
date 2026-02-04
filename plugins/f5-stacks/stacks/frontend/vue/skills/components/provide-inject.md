---
name: vue-provide-inject
description: Vue provide/inject for dependency injection
applies_to: vue
---

# Vue Provide/Inject

## Overview

Provide/inject enables dependency injection in Vue, allowing ancestor
components to serve as dependency providers for all descendants.

## Basic Usage

### Providing Data

```vue
<!-- Parent/Provider component -->
<script setup lang="ts">
import { provide, ref, readonly } from 'vue';

// Provide a static value
provide('appName', 'My Application');

// Provide a reactive value
const theme = ref('light');
provide('theme', theme);

// Provide as readonly to prevent mutation by children
provide('readonlyTheme', readonly(theme));

// Provide a function
const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light';
};
provide('toggleTheme', toggleTheme);
</script>
```

### Injecting Data

```vue
<!-- Child/Consumer component (any level deep) -->
<script setup lang="ts">
import { inject } from 'vue';

// Inject with potential undefined
const appName = inject('appName');

// Inject with default value
const theme = inject('theme', 'light');

// Inject function
const toggleTheme = inject('toggleTheme', () => {});
</script>

<template>
  <div :class="`theme-${theme}`">
    <h1>{{ appName }}</h1>
    <button @click="toggleTheme">Toggle Theme</button>
  </div>
</template>
```

## Type-Safe Provide/Inject

### Using InjectionKey

```typescript
// keys.ts
import type { InjectionKey, Ref } from 'vue';

// Define typed injection keys
export interface ThemeContext {
  theme: Ref<'light' | 'dark'>;
  toggleTheme: () => void;
  setTheme: (theme: 'light' | 'dark') => void;
}

export const ThemeKey: InjectionKey<ThemeContext> = Symbol('theme');

export interface AuthContext {
  user: Ref<User | null>;
  isAuthenticated: Ref<boolean>;
  login: (credentials: Credentials) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthKey: InjectionKey<AuthContext> = Symbol('auth');
```

### Providing with Type Safety

```vue
<!-- ThemeProvider.vue -->
<script setup lang="ts">
import { provide, ref, readonly } from 'vue';
import { ThemeKey, type ThemeContext } from '@/keys';

const theme = ref<'light' | 'dark'>('light');

const toggleTheme = () => {
  theme.value = theme.value === 'light' ? 'dark' : 'light';
};

const setTheme = (newTheme: 'light' | 'dark') => {
  theme.value = newTheme;
};

// Provide typed context
const themeContext: ThemeContext = {
  theme: readonly(theme),
  toggleTheme,
  setTheme,
};

provide(ThemeKey, themeContext);
</script>

<template>
  <div :data-theme="theme">
    <slot />
  </div>
</template>
```

### Injecting with Type Safety

```vue
<script setup lang="ts">
import { inject } from 'vue';
import { ThemeKey } from '@/keys';

// Inject with type safety
const themeContext = inject(ThemeKey);

// Type guard for safety
if (!themeContext) {
  throw new Error('ThemeProvider not found');
}

// Now fully typed
const { theme, toggleTheme } = themeContext;
</script>
```

### Creating Composable for Injection

```typescript
// composables/useTheme.ts
import { inject } from 'vue';
import { ThemeKey, type ThemeContext } from '@/keys';

export function useTheme(): ThemeContext {
  const context = inject(ThemeKey);

  if (!context) {
    throw new Error(
      'useTheme must be used within a ThemeProvider'
    );
  }

  return context;
}
```

```vue
<!-- Usage in any child component -->
<script setup lang="ts">
import { useTheme } from '@/composables/useTheme';

// Clean, type-safe usage
const { theme, toggleTheme } = useTheme();
</script>
```

## Provider Pattern

### Creating a Provider Component

```vue
<!-- AuthProvider.vue -->
<script setup lang="ts">
import { provide, ref, computed, onMounted } from 'vue';
import { AuthKey, type AuthContext } from '@/keys';
import { api } from '@/lib/api';
import type { User, Credentials } from '@/types';

const user = ref<User | null>(null);
const isLoading = ref(true);

const isAuthenticated = computed(() => !!user.value);

async function login(credentials: Credentials) {
  const response = await api.post('/auth/login', credentials);
  user.value = response.data.user;
  localStorage.setItem('token', response.data.token);
}

async function logout() {
  await api.post('/auth/logout');
  user.value = null;
  localStorage.removeItem('token');
}

async function checkAuth() {
  const token = localStorage.getItem('token');
  if (!token) {
    isLoading.value = false;
    return;
  }

  try {
    const response = await api.get('/auth/me');
    user.value = response.data;
  } catch {
    localStorage.removeItem('token');
  } finally {
    isLoading.value = false;
  }
}

onMounted(checkAuth);

const authContext: AuthContext = {
  user: readonly(user),
  isAuthenticated,
  login,
  logout,
};

provide(AuthKey, authContext);
</script>

<template>
  <slot v-if="!isLoading" />
  <div v-else class="loading">Loading...</div>
</template>
```

### App Setup with Providers

```vue
<!-- App.vue -->
<script setup lang="ts">
import ThemeProvider from '@/providers/ThemeProvider.vue';
import AuthProvider from '@/providers/AuthProvider.vue';
import { RouterView } from 'vue-router';
</script>

<template>
  <ThemeProvider>
    <AuthProvider>
      <RouterView />
    </AuthProvider>
  </ThemeProvider>
</template>
```

## Common Patterns

### Form Context

```typescript
// keys/form.ts
import type { InjectionKey, Ref } from 'vue';

export interface FormContext {
  values: Ref<Record<string, unknown>>;
  errors: Ref<Record<string, string>>;
  touched: Ref<Record<string, boolean>>;
  setFieldValue: (field: string, value: unknown) => void;
  setFieldError: (field: string, error: string) => void;
  registerField: (field: string) => void;
  unregisterField: (field: string) => void;
}

export const FormKey: InjectionKey<FormContext> = Symbol('form');
```

```vue
<!-- Form.vue -->
<script setup lang="ts">
import { provide, ref } from 'vue';
import { FormKey, type FormContext } from '@/keys/form';

const values = ref<Record<string, unknown>>({});
const errors = ref<Record<string, string>>({});
const touched = ref<Record<string, boolean>>({});

const context: FormContext = {
  values,
  errors,
  touched,
  setFieldValue: (field, value) => {
    values.value[field] = value;
  },
  setFieldError: (field, error) => {
    errors.value[field] = error;
  },
  registerField: (field) => {
    if (!(field in values.value)) {
      values.value[field] = '';
    }
  },
  unregisterField: (field) => {
    delete values.value[field];
    delete errors.value[field];
    delete touched.value[field];
  },
};

provide(FormKey, context);
</script>

<template>
  <form @submit.prevent>
    <slot />
  </form>
</template>
```

### Modal/Dialog Context

```typescript
// keys/modal.ts
export interface ModalContext {
  isOpen: Ref<boolean>;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

export const ModalKey: InjectionKey<ModalContext> = Symbol('modal');
```

## Best Practices

1. **Use InjectionKey** - Type safety with Symbol keys
2. **Create composables** - Wrap inject for cleaner API
3. **Provide readonly** - Prevent unintended mutations
4. **Check for undefined** - Handle missing providers
5. **Document providers** - What context is required
6. **Keep context focused** - Single responsibility
