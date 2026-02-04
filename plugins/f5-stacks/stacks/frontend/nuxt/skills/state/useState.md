---
name: nuxt-useState
description: useState composable for SSR-friendly state in Nuxt 3
applies_to: nuxt
---

# useState in Nuxt 3

## Overview

`useState` is Nuxt's SSR-friendly reactive state management. It creates state that's shared across components and safely transferred from server to client.

## Basic Usage

```typescript
// Simple state
const count = useState('counter', () => 0);

// With type
const user = useState<User | null>('user', () => null);

// Access and modify
count.value++;
user.value = { id: '1', name: 'John' };
```

## Key Features

### SSR-Safe

State is serialized on server and hydrated on client:

```typescript
// Runs on server during SSR
const serverData = useState('data', () => {
  // Initial value computed on server
  return fetchInitialData();
});

// Client receives hydrated state - no re-fetch needed
```

### Shared State

Same key = same state across components:

```vue
<!-- ComponentA.vue -->
<script setup>
const count = useState('counter', () => 0);
count.value = 5;
</script>

<!-- ComponentB.vue -->
<script setup>
const count = useState('counter');
console.log(count.value); // 5
</script>
```

## Patterns

### User State

```typescript
// composables/useAuth.ts
interface User {
  id: string;
  email: string;
  name: string;
  role: string;
}

export function useAuth() {
  const user = useState<User | null>('auth-user', () => null);
  const isAuthenticated = computed(() => !!user.value);
  const isAdmin = computed(() => user.value?.role === 'admin');

  async function login(email: string, password: string) {
    const response = await $fetch<{ user: User; token: string }>('/api/auth/login', {
      method: 'POST',
      body: { email, password },
    });

    user.value = response.user;

    // Store token in cookie
    const token = useCookie('auth-token');
    token.value = response.token;
  }

  async function logout() {
    await $fetch('/api/auth/logout', { method: 'POST' });
    user.value = null;

    const token = useCookie('auth-token');
    token.value = null;

    navigateTo('/login');
  }

  async function fetchUser() {
    try {
      user.value = await $fetch<User>('/api/auth/me');
    } catch {
      user.value = null;
    }
  }

  return {
    user: readonly(user),
    isAuthenticated,
    isAdmin,
    login,
    logout,
    fetchUser,
  };
}
```

### Theme State

```typescript
// composables/useTheme.ts
type Theme = 'light' | 'dark' | 'system';

export function useTheme() {
  const theme = useState<Theme>('theme', () => 'system');

  const colorMode = useColorMode();

  const actualTheme = computed(() => {
    if (theme.value === 'system') {
      return colorMode.value;
    }
    return theme.value;
  });

  function setTheme(newTheme: Theme) {
    theme.value = newTheme;
    if (newTheme !== 'system') {
      colorMode.preference = newTheme;
    }
  }

  return {
    theme: readonly(theme),
    actualTheme,
    setTheme,
  };
}
```

### Feature Flags

```typescript
// composables/useFeatureFlags.ts
interface FeatureFlags {
  newDashboard: boolean;
  betaFeatures: boolean;
  experimentalUI: boolean;
}

export function useFeatureFlags() {
  const flags = useState<FeatureFlags>('feature-flags', () => ({
    newDashboard: false,
    betaFeatures: false,
    experimentalUI: false,
  }));

  function isEnabled(flag: keyof FeatureFlags) {
    return flags.value[flag];
  }

  async function fetchFlags() {
    flags.value = await $fetch<FeatureFlags>('/api/feature-flags');
  }

  return {
    flags: readonly(flags),
    isEnabled,
    fetchFlags,
  };
}
```

### Cart State

```typescript
// composables/useCart.ts
interface CartItem {
  id: string;
  productId: string;
  name: string;
  price: number;
  quantity: number;
}

export function useCart() {
  const items = useState<CartItem[]>('cart-items', () => []);

  const totalItems = computed(() =>
    items.value.reduce((sum, item) => sum + item.quantity, 0)
  );

  const totalPrice = computed(() =>
    items.value.reduce((sum, item) => sum + item.price * item.quantity, 0)
  );

  function addItem(product: { id: string; name: string; price: number }) {
    const existing = items.value.find((item) => item.productId === product.id);

    if (existing) {
      existing.quantity++;
    } else {
      items.value.push({
        id: crypto.randomUUID(),
        productId: product.id,
        name: product.name,
        price: product.price,
        quantity: 1,
      });
    }
  }

  function removeItem(itemId: string) {
    items.value = items.value.filter((item) => item.id !== itemId);
  }

  function updateQuantity(itemId: string, quantity: number) {
    const item = items.value.find((i) => i.id === itemId);
    if (item) {
      if (quantity <= 0) {
        removeItem(itemId);
      } else {
        item.quantity = quantity;
      }
    }
  }

  function clearCart() {
    items.value = [];
  }

  return {
    items: readonly(items),
    totalItems,
    totalPrice,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
  };
}
```

## Initialization Patterns

### Plugin Initialization

```typescript
// plugins/auth.ts
export default defineNuxtPlugin(async () => {
  const { fetchUser } = useAuth();

  // Initialize user state on app start
  await fetchUser();
});
```

### Middleware Initialization

```typescript
// middleware/auth.global.ts
export default defineNuxtRouteMiddleware(async () => {
  const { user, fetchUser } = useAuth();

  // Load user if not loaded
  if (!user.value) {
    await fetchUser();
  }
});
```

### Server Plugin

```typescript
// server/plugins/state.ts
export default defineNitroPlugin((nitro) => {
  // Initialize server-side state
  nitro.hooks.hook('request', async (event) => {
    // Set up request-scoped state
  });
});
```

## Clearing State

```typescript
// composables/useAppState.ts
export function useAppState() {
  const user = useState('user', () => null);
  const cart = useState('cart', () => []);
  const preferences = useState('preferences', () => ({}));

  function clearAllState() {
    user.value = null;
    cart.value = [];
    preferences.value = {};
  }

  return {
    clearAllState,
  };
}
```

## useState vs Other Options

```typescript
// useState - SSR-safe, shared, simple state
const count = useState('count', () => 0);

// ref - Component-local state
const localCount = ref(0);

// Pinia - Complex state with actions, getters, devtools
const store = useMyStore();

// useCookie - Persistent across sessions
const token = useCookie('token');
```

## Best Practices

1. **Unique keys** - Use descriptive, unique keys
2. **Type your state** - Use TypeScript generics
3. **Wrap in composables** - Encapsulate related state
4. **Initialize properly** - Use plugins or middleware
5. **Read-only exports** - Expose `readonly()` for immutability
6. **Clear on logout** - Reset user-specific state
