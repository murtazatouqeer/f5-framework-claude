---
name: nuxt-auth-app
description: Authentication application example with Nuxt 3
applies_to: nuxt
---

# Nuxt Authentication Application Example

A complete authentication application demonstrating JWT-based auth, protected routes, and session management.

## Project Structure

```
nuxt-auth-app/
├── nuxt.config.ts
├── app.vue
├── pages/
│   ├── index.vue
│   ├── login.vue
│   ├── register.vue
│   └── dashboard/
│       └── index.vue
├── components/
│   ├── AuthForm.vue
│   ├── LoginForm.vue
│   ├── RegisterForm.vue
│   └── UserMenu.vue
├── composables/
│   └── useAuth.ts
├── middleware/
│   ├── auth.ts
│   └── guest.ts
├── server/
│   ├── api/
│   │   └── auth/
│   │       ├── login.post.ts
│   │       ├── register.post.ts
│   │       ├── logout.post.ts
│   │       ├── me.get.ts
│   │       └── refresh.post.ts
│   ├── middleware/
│   │   └── auth.ts
│   └── utils/
│       ├── jwt.ts
│       └── password.ts
├── plugins/
│   └── auth.ts
└── types/
    └── auth.ts
```

## Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxt/ui'],
  runtimeConfig: {
    jwtSecret: process.env.JWT_SECRET,
    jwtExpiry: '15m',
    refreshTokenExpiry: '7d',
    public: {
      appName: 'Auth App',
    },
  },
});
```

## Types

```typescript
// types/auth.ts
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'user' | 'admin';
  createdAt: string;
}

export interface LoginInput {
  email: string;
  password: string;
}

export interface RegisterInput {
  email: string;
  password: string;
  name: string;
}

export interface AuthResponse {
  user: User;
  accessToken: string;
  refreshToken: string;
}

export interface TokenPayload {
  userId: string;
  email: string;
  role: string;
}
```

## Server Utilities

```typescript
// server/utils/jwt.ts
import jwt from 'jsonwebtoken';

const config = useRuntimeConfig();

export function generateAccessToken(payload: TokenPayload): string {
  return jwt.sign(payload, config.jwtSecret, {
    expiresIn: config.jwtExpiry,
  });
}

export function generateRefreshToken(payload: TokenPayload): string {
  return jwt.sign(payload, config.jwtSecret, {
    expiresIn: config.refreshTokenExpiry,
  });
}

export function verifyToken(token: string): TokenPayload {
  return jwt.verify(token, config.jwtSecret) as TokenPayload;
}
```

```typescript
// server/utils/password.ts
import bcrypt from 'bcryptjs';

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 12);
}

export async function verifyPassword(
  password: string,
  hash: string
): Promise<boolean> {
  return bcrypt.compare(password, hash);
}
```

## Server Middleware

```typescript
// server/middleware/auth.ts
export default defineEventHandler(async (event) => {
  // Skip auth routes
  if (event.path.startsWith('/api/auth')) return;

  // Check for protected routes
  if (!event.path.startsWith('/api/protected')) return;

  const token = getHeader(event, 'authorization')?.replace('Bearer ', '');

  if (!token) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
    });
  }

  try {
    const payload = verifyToken(token);
    event.context.user = payload;
  } catch {
    throw createError({
      statusCode: 401,
      statusMessage: 'Invalid token',
    });
  }
});
```

## API Routes

```typescript
// server/api/auth/register.post.ts
import { z } from 'zod';

const registerSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().min(2),
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const { email, password, name } = registerSchema.parse(body);

  // Check if user exists
  const existing = await prisma.user.findUnique({
    where: { email },
  });

  if (existing) {
    throw createError({
      statusCode: 409,
      statusMessage: 'Email already registered',
    });
  }

  // Create user
  const hashedPassword = await hashPassword(password);
  const user = await prisma.user.create({
    data: {
      email,
      password: hashedPassword,
      name,
      role: 'user',
    },
    select: {
      id: true,
      email: true,
      name: true,
      role: true,
      createdAt: true,
    },
  });

  // Generate tokens
  const payload = { userId: user.id, email: user.email, role: user.role };
  const accessToken = generateAccessToken(payload);
  const refreshToken = generateRefreshToken(payload);

  // Store refresh token
  await prisma.refreshToken.create({
    data: {
      token: refreshToken,
      userId: user.id,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    },
  });

  setResponseStatus(event, 201);
  return { user, accessToken, refreshToken };
});
```

```typescript
// server/api/auth/login.post.ts
import { z } from 'zod';

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string(),
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const { email, password } = loginSchema.parse(body);

  // Find user
  const user = await prisma.user.findUnique({
    where: { email },
  });

  if (!user) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Invalid credentials',
    });
  }

  // Verify password
  const valid = await verifyPassword(password, user.password);
  if (!valid) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Invalid credentials',
    });
  }

  // Generate tokens
  const payload = { userId: user.id, email: user.email, role: user.role };
  const accessToken = generateAccessToken(payload);
  const refreshToken = generateRefreshToken(payload);

  // Store refresh token
  await prisma.refreshToken.create({
    data: {
      token: refreshToken,
      userId: user.id,
      expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
    },
  });

  return {
    user: {
      id: user.id,
      email: user.email,
      name: user.name,
      role: user.role,
      createdAt: user.createdAt,
    },
    accessToken,
    refreshToken,
  };
});
```

```typescript
// server/api/auth/me.get.ts
export default defineEventHandler(async (event) => {
  const token = getHeader(event, 'authorization')?.replace('Bearer ', '');

  if (!token) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Unauthorized',
    });
  }

  try {
    const payload = verifyToken(token);

    const user = await prisma.user.findUnique({
      where: { id: payload.userId },
      select: {
        id: true,
        email: true,
        name: true,
        role: true,
        createdAt: true,
      },
    });

    if (!user) {
      throw createError({
        statusCode: 404,
        statusMessage: 'User not found',
      });
    }

    return user;
  } catch {
    throw createError({
      statusCode: 401,
      statusMessage: 'Invalid token',
    });
  }
});
```

```typescript
// server/api/auth/refresh.post.ts
import { z } from 'zod';

const refreshSchema = z.object({
  refreshToken: z.string(),
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const { refreshToken } = refreshSchema.parse(body);

  // Find stored token
  const storedToken = await prisma.refreshToken.findUnique({
    where: { token: refreshToken },
    include: { user: true },
  });

  if (!storedToken || storedToken.expiresAt < new Date()) {
    throw createError({
      statusCode: 401,
      statusMessage: 'Invalid refresh token',
    });
  }

  // Generate new access token
  const payload = {
    userId: storedToken.user.id,
    email: storedToken.user.email,
    role: storedToken.user.role,
  };
  const accessToken = generateAccessToken(payload);

  return { accessToken };
});
```

```typescript
// server/api/auth/logout.post.ts
import { z } from 'zod';

const logoutSchema = z.object({
  refreshToken: z.string(),
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const { refreshToken } = logoutSchema.parse(body);

  // Delete refresh token
  await prisma.refreshToken.deleteMany({
    where: { token: refreshToken },
  });

  return { success: true };
});
```

## Auth Composable

```typescript
// composables/useAuth.ts
export function useAuth() {
  const user = useState<User | null>('auth-user', () => null);
  const accessToken = useCookie('auth-token');
  const refreshToken = useCookie('auth-refresh-token', {
    maxAge: 7 * 24 * 60 * 60, // 7 days
  });

  const isAuthenticated = computed(() => !!user.value);
  const isAdmin = computed(() => user.value?.role === 'admin');

  async function login(credentials: LoginInput) {
    const response = await $fetch<AuthResponse>('/api/auth/login', {
      method: 'POST',
      body: credentials,
    });

    user.value = response.user;
    accessToken.value = response.accessToken;
    refreshToken.value = response.refreshToken;
  }

  async function register(data: RegisterInput) {
    const response = await $fetch<AuthResponse>('/api/auth/register', {
      method: 'POST',
      body: data,
    });

    user.value = response.user;
    accessToken.value = response.accessToken;
    refreshToken.value = response.refreshToken;
  }

  async function logout() {
    if (refreshToken.value) {
      await $fetch('/api/auth/logout', {
        method: 'POST',
        body: { refreshToken: refreshToken.value },
      });
    }

    user.value = null;
    accessToken.value = null;
    refreshToken.value = null;
  }

  async function fetchUser() {
    if (!accessToken.value) return;

    try {
      user.value = await $fetch<User>('/api/auth/me', {
        headers: {
          Authorization: `Bearer ${accessToken.value}`,
        },
      });
    } catch {
      // Token expired, try refresh
      await refreshAccessToken();
    }
  }

  async function refreshAccessToken() {
    if (!refreshToken.value) {
      await logout();
      return;
    }

    try {
      const response = await $fetch<{ accessToken: string }>(
        '/api/auth/refresh',
        {
          method: 'POST',
          body: { refreshToken: refreshToken.value },
        }
      );

      accessToken.value = response.accessToken;
      await fetchUser();
    } catch {
      await logout();
    }
  }

  return {
    user: readonly(user),
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    fetchUser,
    refreshAccessToken,
  };
}
```

## Middleware

```typescript
// middleware/auth.ts
export default defineNuxtRouteMiddleware((to) => {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated.value) {
    return navigateTo({
      path: '/login',
      query: { redirect: to.fullPath },
    });
  }
});
```

```typescript
// middleware/guest.ts
export default defineNuxtRouteMiddleware(() => {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated.value) {
    return navigateTo('/dashboard');
  }
});
```

## Auth Plugin

```typescript
// plugins/auth.ts
export default defineNuxtPlugin(async () => {
  const { fetchUser } = useAuth();

  // Initialize auth state on app load
  await fetchUser();
});
```

## Pages

```vue
<!-- pages/login.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  middleware: 'guest',
});

useSeoMeta({ title: 'Login' });

const { login } = useAuth();
const route = useRoute();

const form = reactive({
  email: '',
  password: '',
});

const error = ref('');
const isSubmitting = ref(false);

async function handleSubmit() {
  error.value = '';
  isSubmitting.value = true;

  try {
    await login(form);
    const redirect = route.query.redirect as string || '/dashboard';
    navigateTo(redirect);
  } catch (e: any) {
    error.value = e.data?.statusMessage || 'Login failed';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <h1>Login</h1>

    <form @submit.prevent="handleSubmit">
      <div v-if="error" class="error-message">{{ error }}</div>

      <div class="field">
        <label for="email">Email</label>
        <input
          id="email"
          v-model="form.email"
          type="email"
          required
          autocomplete="email"
        />
      </div>

      <div class="field">
        <label for="password">Password</label>
        <input
          id="password"
          v-model="form.password"
          type="password"
          required
          autocomplete="current-password"
        />
      </div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Signing in...' : 'Sign In' }}
      </button>
    </form>

    <p class="register-link">
      Don't have an account?
      <NuxtLink to="/register">Register</NuxtLink>
    </p>
  </div>
</template>
```

```vue
<!-- pages/register.vue -->
<script setup lang="ts">
definePageMeta({
  layout: 'auth',
  middleware: 'guest',
});

useSeoMeta({ title: 'Register' });

const { register } = useAuth();

const form = reactive({
  name: '',
  email: '',
  password: '',
  confirmPassword: '',
});

const errors = ref<Record<string, string>>({});
const isSubmitting = ref(false);

function validate() {
  errors.value = {};

  if (form.name.length < 2) {
    errors.value.name = 'Name must be at least 2 characters';
  }

  if (!form.email.includes('@')) {
    errors.value.email = 'Invalid email address';
  }

  if (form.password.length < 8) {
    errors.value.password = 'Password must be at least 8 characters';
  }

  if (form.password !== form.confirmPassword) {
    errors.value.confirmPassword = 'Passwords do not match';
  }

  return Object.keys(errors.value).length === 0;
}

async function handleSubmit() {
  if (!validate()) return;

  isSubmitting.value = true;

  try {
    await register({
      name: form.name,
      email: form.email,
      password: form.password,
    });
    navigateTo('/dashboard');
  } catch (e: any) {
    errors.value.form = e.data?.statusMessage || 'Registration failed';
  } finally {
    isSubmitting.value = false;
  }
}
</script>

<template>
  <div class="register-page">
    <h1>Register</h1>

    <form @submit.prevent="handleSubmit">
      <div v-if="errors.form" class="error-message">{{ errors.form }}</div>

      <div class="field">
        <label for="name">Name</label>
        <input id="name" v-model="form.name" type="text" required />
        <span v-if="errors.name" class="error">{{ errors.name }}</span>
      </div>

      <div class="field">
        <label for="email">Email</label>
        <input id="email" v-model="form.email" type="email" required />
        <span v-if="errors.email" class="error">{{ errors.email }}</span>
      </div>

      <div class="field">
        <label for="password">Password</label>
        <input id="password" v-model="form.password" type="password" required />
        <span v-if="errors.password" class="error">{{ errors.password }}</span>
      </div>

      <div class="field">
        <label for="confirmPassword">Confirm Password</label>
        <input
          id="confirmPassword"
          v-model="form.confirmPassword"
          type="password"
          required
        />
        <span v-if="errors.confirmPassword" class="error">
          {{ errors.confirmPassword }}
        </span>
      </div>

      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Creating account...' : 'Create Account' }}
      </button>
    </form>

    <p class="login-link">
      Already have an account?
      <NuxtLink to="/login">Login</NuxtLink>
    </p>
  </div>
</template>
```

```vue
<!-- pages/dashboard/index.vue -->
<script setup lang="ts">
definePageMeta({
  middleware: 'auth',
});

useSeoMeta({ title: 'Dashboard' });

const { user, logout } = useAuth();

async function handleLogout() {
  await logout();
  navigateTo('/login');
}
</script>

<template>
  <div class="dashboard-page">
    <header class="dashboard-header">
      <h1>Dashboard</h1>
      <UserMenu :user="user!" @logout="handleLogout" />
    </header>

    <main class="dashboard-content">
      <div class="welcome-card">
        <h2>Welcome back, {{ user?.name }}!</h2>
        <p>Email: {{ user?.email }}</p>
        <p>Role: {{ user?.role }}</p>
        <p>Member since: {{ new Date(user?.createdAt!).toLocaleDateString() }}</p>
      </div>
    </main>
  </div>
</template>
```

## Components

```vue
<!-- components/UserMenu.vue -->
<script setup lang="ts">
defineProps<{
  user: User;
}>();

const emit = defineEmits<{
  logout: [];
}>();

const isOpen = ref(false);
</script>

<template>
  <div class="user-menu">
    <button class="user-menu__trigger" @click="isOpen = !isOpen">
      <span>{{ user.name }}</span>
      <svg class="chevron" viewBox="0 0 24 24">
        <path d="M6 9l6 6 6-6" />
      </svg>
    </button>

    <div v-if="isOpen" class="user-menu__dropdown">
      <NuxtLink to="/dashboard/profile" @click="isOpen = false">
        Profile
      </NuxtLink>
      <NuxtLink to="/dashboard/settings" @click="isOpen = false">
        Settings
      </NuxtLink>
      <hr />
      <button @click="emit('logout')">Logout</button>
    </div>
  </div>
</template>
```

## Testing

```typescript
// tests/auth.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mountSuspended, mockNuxtImport } from '@nuxt/test-utils/runtime';
import LoginPage from '~/pages/login.vue';

// Mock useAuth
mockNuxtImport('useAuth', () => {
  return () => ({
    login: vi.fn(),
    isAuthenticated: ref(false),
  });
});

describe('Login Page', () => {
  it('renders login form', async () => {
    const wrapper = await mountSuspended(LoginPage);

    expect(wrapper.find('form').exists()).toBe(true);
    expect(wrapper.find('input[type="email"]').exists()).toBe(true);
    expect(wrapper.find('input[type="password"]').exists()).toBe(true);
  });

  it('shows error on failed login', async () => {
    const { login } = useAuth();
    vi.mocked(login).mockRejectedValueOnce({
      data: { statusMessage: 'Invalid credentials' },
    });

    const wrapper = await mountSuspended(LoginPage);

    await wrapper.find('input[type="email"]').setValue('test@example.com');
    await wrapper.find('input[type="password"]').setValue('wrongpassword');
    await wrapper.find('form').trigger('submit');

    await nextTick();

    expect(wrapper.text()).toContain('Invalid credentials');
  });
});
```

## Key Features Demonstrated

1. **JWT authentication** with access and refresh tokens
2. **Secure password hashing** with bcrypt
3. **Route protection** with middleware
4. **Guest middleware** for auth pages
5. **Token refresh** mechanism
6. **Server-side auth** middleware
7. **Client-side state** management
8. **Form validation** and error handling
9. **Role-based access** control
10. **Cookie-based** token storage
