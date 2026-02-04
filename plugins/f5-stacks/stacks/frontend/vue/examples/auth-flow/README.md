# Vue Auth Flow Example

Complete authentication flow example demonstrating Vue 3
patterns for login, registration, and protected routes.

## Overview

This example demonstrates:
- Authentication state management
- Protected route guards
- Form validation with Zod
- Token-based authentication
- Persistent sessions

## Project Structure

```
auth-flow/
├── src/
│   ├── components/
│   │   ├── LoginForm.vue
│   │   ├── RegisterForm.vue
│   │   └── UserMenu.vue
│   ├── composables/
│   │   └── useAuth.ts
│   ├── stores/
│   │   └── useAuthStore.ts
│   ├── pages/
│   │   ├── LoginPage.vue
│   │   ├── RegisterPage.vue
│   │   ├── DashboardPage.vue
│   │   └── ProfilePage.vue
│   ├── services/
│   │   └── authService.ts
│   ├── guards/
│   │   └── authGuard.ts
│   ├── types/
│   │   └── auth.ts
│   └── router/
│       └── index.ts
└── README.md
```

## Key Patterns

### 1. Auth Store

```typescript
// stores/useAuthStore.ts
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import { useRouter } from 'vue-router';
import type { User, LoginCredentials, RegisterData } from '@/types/auth';
import { authService } from '@/services/authService';

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter();

  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('token'));
  const isLoading = ref(false);
  const error = ref<string | null>(null);
  const isInitialized = ref(false);

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value);
  const isAdmin = computed(() => user.value?.role === 'admin');

  // Actions
  async function initialize() {
    if (isInitialized.value) return;

    if (token.value) {
      try {
        user.value = await authService.getMe(token.value);
      } catch {
        // Token invalid, clear it
        logout();
      }
    }

    isInitialized.value = true;
  }

  async function login(credentials: LoginCredentials) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await authService.login(credentials);

      token.value = response.token;
      user.value = response.user;

      localStorage.setItem('token', response.token);

      // Redirect to intended page or dashboard
      const redirect = router.currentRoute.value.query.redirect as string;
      router.push(redirect || '/dashboard');

      return true;
    } catch (e) {
      error.value = (e as Error).message;
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function register(data: RegisterData) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await authService.register(data);

      token.value = response.token;
      user.value = response.user;

      localStorage.setItem('token', response.token);
      router.push('/dashboard');

      return true;
    } catch (e) {
      error.value = (e as Error).message;
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    router.push('/login');
  }

  async function updateProfile(data: Partial<User>) {
    if (!token.value) return;

    isLoading.value = true;

    try {
      user.value = await authService.updateProfile(token.value, data);
    } finally {
      isLoading.value = false;
    }
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    isAdmin,
    isInitialized,
    initialize,
    login,
    register,
    logout,
    updateProfile,
  };
});
```

### 2. Auth Guard

```typescript
// guards/authGuard.ts
import type { NavigationGuard } from 'vue-router';
import { useAuthStore } from '@/stores/useAuthStore';

export const authGuard: NavigationGuard = async (to, from) => {
  const authStore = useAuthStore();

  // Wait for auth to initialize
  if (!authStore.isInitialized) {
    await authStore.initialize();
  }

  // Check if route requires auth
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    };
  }

  // Check for role requirements
  if (to.meta.roles) {
    const roles = to.meta.roles as string[];
    const userRole = authStore.user?.role;

    if (!userRole || !roles.includes(userRole)) {
      return { name: 'forbidden' };
    }
  }

  // Redirect authenticated users away from auth pages
  if (to.meta.guestOnly && authStore.isAuthenticated) {
    return { name: 'dashboard' };
  }

  return true;
};
```

### 3. Login Form with Zod

```vue
<!-- components/LoginForm.vue -->
<script setup lang="ts">
import { useForm, useField } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';
import { useAuthStore } from '@/stores/useAuthStore';

const authStore = useAuthStore();

// Validation schema
const schema = toTypedSchema(
  z.object({
    email: z.string()
      .min(1, 'Email is required')
      .email('Invalid email format'),
    password: z.string()
      .min(1, 'Password is required')
      .min(8, 'Password must be at least 8 characters'),
  })
);

const { handleSubmit, errors } = useForm({
  validationSchema: schema,
});

const { value: email } = useField('email');
const { value: password } = useField('password');

const onSubmit = handleSubmit(async (values) => {
  await authStore.login({
    email: values.email,
    password: values.password,
  });
});
</script>

<template>
  <form @submit="onSubmit" class="auth-form">
    <h2>Login</h2>

    <div v-if="authStore.error" class="error-banner">
      {{ authStore.error }}
    </div>

    <div class="field">
      <label for="email">Email</label>
      <input
        id="email"
        v-model="email"
        type="email"
        :class="{ invalid: errors.email }"
      />
      <span v-if="errors.email" class="error">{{ errors.email }}</span>
    </div>

    <div class="field">
      <label for="password">Password</label>
      <input
        id="password"
        v-model="password"
        type="password"
        :class="{ invalid: errors.password }"
      />
      <span v-if="errors.password" class="error">{{ errors.password }}</span>
    </div>

    <button type="submit" :disabled="authStore.isLoading">
      {{ authStore.isLoading ? 'Logging in...' : 'Login' }}
    </button>

    <p class="form-footer">
      Don't have an account?
      <RouterLink to="/register">Register</RouterLink>
    </p>
  </form>
</template>
```

### 4. Register Form

```vue
<!-- components/RegisterForm.vue -->
<script setup lang="ts">
import { useForm, useField } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';
import { useAuthStore } from '@/stores/useAuthStore';

const authStore = useAuthStore();

const schema = toTypedSchema(
  z.object({
    name: z.string()
      .min(1, 'Name is required')
      .min(2, 'Name must be at least 2 characters'),
    email: z.string()
      .min(1, 'Email is required')
      .email('Invalid email format'),
    password: z.string()
      .min(1, 'Password is required')
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Must contain uppercase letter')
      .regex(/[0-9]/, 'Must contain number'),
    confirmPassword: z.string()
      .min(1, 'Please confirm password'),
  }).refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })
);

const { handleSubmit, errors } = useForm({
  validationSchema: schema,
});

const { value: name } = useField('name');
const { value: email } = useField('email');
const { value: password } = useField('password');
const { value: confirmPassword } = useField('confirmPassword');

const onSubmit = handleSubmit(async (values) => {
  await authStore.register({
    name: values.name,
    email: values.email,
    password: values.password,
  });
});
</script>

<template>
  <form @submit="onSubmit" class="auth-form">
    <h2>Create Account</h2>

    <div v-if="authStore.error" class="error-banner">
      {{ authStore.error }}
    </div>

    <div class="field">
      <label for="name">Name</label>
      <input id="name" v-model="name" type="text" />
      <span v-if="errors.name" class="error">{{ errors.name }}</span>
    </div>

    <div class="field">
      <label for="email">Email</label>
      <input id="email" v-model="email" type="email" />
      <span v-if="errors.email" class="error">{{ errors.email }}</span>
    </div>

    <div class="field">
      <label for="password">Password</label>
      <input id="password" v-model="password" type="password" />
      <span v-if="errors.password" class="error">{{ errors.password }}</span>
    </div>

    <div class="field">
      <label for="confirmPassword">Confirm Password</label>
      <input id="confirmPassword" v-model="confirmPassword" type="password" />
      <span v-if="errors.confirmPassword" class="error">
        {{ errors.confirmPassword }}
      </span>
    </div>

    <button type="submit" :disabled="authStore.isLoading">
      {{ authStore.isLoading ? 'Creating account...' : 'Register' }}
    </button>

    <p class="form-footer">
      Already have an account?
      <RouterLink to="/login">Login</RouterLink>
    </p>
  </form>
</template>
```

### 5. Router Configuration

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';
import { authGuard } from '@/guards/authGuard';

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/pages/RegisterPage.vue'),
    meta: { guestOnly: true },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('@/pages/DashboardPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile',
    name: 'profile',
    component: () => import('@/pages/ProfilePage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/admin',
    name: 'admin',
    component: () => import('@/pages/AdminPage.vue'),
    meta: { requiresAuth: true, roles: ['admin'] },
  },
  {
    path: '/forbidden',
    name: 'forbidden',
    component: () => import('@/pages/ForbiddenPage.vue'),
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Apply auth guard globally
router.beforeEach(authGuard);
```

### 6. Auth Service

```typescript
// services/authService.ts
import type { User, LoginCredentials, RegisterData, AuthResponse } from '@/types/auth';

const API_URL = '/api/auth';

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Login failed');
    }

    return response.json();
  },

  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }

    return response.json();
  },

  async getMe(token: string): Promise<User> {
    const response = await fetch(`${API_URL}/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      throw new Error('Failed to get user');
    }

    return response.json();
  },

  async updateProfile(token: string, data: Partial<User>): Promise<User> {
    const response = await fetch(`${API_URL}/profile`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error('Failed to update profile');
    }

    return response.json();
  },
};
```

## Best Practices Demonstrated

1. **Centralized auth state** - Single source of truth in Pinia
2. **Route guards** - Protect routes at router level
3. **Type-safe validation** - Zod schemas with VeeValidate
4. **Token persistence** - localStorage for session persistence
5. **Error handling** - User-friendly error messages
6. **Loading states** - Disable buttons during async operations
7. **Role-based access** - Route meta for role requirements
