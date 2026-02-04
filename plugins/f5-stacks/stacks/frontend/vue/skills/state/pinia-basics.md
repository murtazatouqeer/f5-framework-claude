---
name: vue-pinia-basics
description: Pinia state management fundamentals
applies_to: vue
---

# Pinia State Management

## Overview

Pinia is the official state management library for Vue 3.
It provides a simple, intuitive API with full TypeScript support.

## Setup

```typescript
// main.ts
import { createApp } from 'vue';
import { createPinia } from 'pinia';
import App from './App.vue';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia);
app.mount('#app');
```

## Store Definition

### Setup Store (Composition API)

```typescript
// stores/useCounterStore.ts
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';

export const useCounterStore = defineStore('counter', () => {
  // State
  const count = ref(0);

  // Getters (computed)
  const doubleCount = computed(() => count.value * 2);
  const isPositive = computed(() => count.value > 0);

  // Actions
  function increment() {
    count.value++;
  }

  function decrement() {
    count.value--;
  }

  function reset() {
    count.value = 0;
  }

  async function incrementAsync() {
    await new Promise((resolve) => setTimeout(resolve, 1000));
    count.value++;
  }

  // Return all state, getters, and actions
  return {
    count,
    doubleCount,
    isPositive,
    increment,
    decrement,
    reset,
    incrementAsync,
  };
});
```

### Options Store

```typescript
// stores/useUserStore.ts
import { defineStore } from 'pinia';
import type { User } from '@/types';

interface UserState {
  user: User | null;
  isLoading: boolean;
  error: string | null;
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    user: null,
    isLoading: false,
    error: null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.user,
    fullName: (state) => {
      if (!state.user) return '';
      return `${state.user.firstName} ${state.user.lastName}`;
    },
    // Getter with argument
    hasRole: (state) => {
      return (role: string) => state.user?.roles.includes(role) ?? false;
    },
  },

  actions: {
    async login(email: string, password: string) {
      this.isLoading = true;
      this.error = null;

      try {
        const response = await api.post('/auth/login', { email, password });
        this.user = response.data.user;
      } catch (e) {
        this.error = e instanceof Error ? e.message : 'Login failed';
        throw e;
      } finally {
        this.isLoading = false;
      }
    },

    logout() {
      this.user = null;
      this.error = null;
    },
  },
});
```

## Using Stores

### In Components

```vue
<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { useCounterStore } from '@/stores/useCounterStore';
import { useUserStore } from '@/stores/useUserStore';

const counterStore = useCounterStore();
const userStore = useUserStore();

// Destructure reactive state (preserves reactivity)
const { count, doubleCount } = storeToRefs(counterStore);
const { user, isLoading } = storeToRefs(userStore);

// Actions can be destructured directly
const { increment, decrement } = counterStore;
const { login, logout } = userStore;

// Or access directly from store
function handleClick() {
  counterStore.increment();
  // counterStore.count is also reactive
}
</script>

<template>
  <div>
    <p>Count: {{ count }}</p>
    <p>Double: {{ doubleCount }}</p>
    <button @click="increment">+</button>
    <button @click="decrement">-</button>

    <div v-if="user">
      Welcome, {{ user.name }}
      <button @click="logout">Logout</button>
    </div>
  </div>
</template>
```

### storeToRefs vs Direct Access

```typescript
// DON'T: Destructure state directly (loses reactivity)
const { count } = counterStore; // Not reactive!

// DO: Use storeToRefs for state/getters
const { count } = storeToRefs(counterStore); // Reactive!

// DO: Destructure actions directly (they don't need reactivity)
const { increment, decrement } = counterStore;

// DO: Access directly from store
counterStore.count; // Reactive
counterStore.increment(); // Works
```

## State Patterns

### Resetting State

```typescript
// Setup store
export const useStore = defineStore('store', () => {
  const count = ref(0);
  const name = ref('');

  // Manual reset function
  function $reset() {
    count.value = 0;
    name.value = '';
  }

  return { count, name, $reset };
});

// Options store has automatic $reset
const store = useStore();
store.$reset(); // Resets to initial state
```

### Patching State

```typescript
const store = useUserStore();

// Single property
store.user = newUser;

// Multiple properties
store.$patch({
  user: newUser,
  isLoading: false,
});

// Function patch (for arrays, complex updates)
store.$patch((state) => {
  state.items.push(newItem);
  state.total += 1;
});
```

### Subscribing to Changes

```typescript
const store = useUserStore();

// Subscribe to state changes
const unsubscribe = store.$subscribe((mutation, state) => {
  console.log('Mutation type:', mutation.type);
  console.log('Store ID:', mutation.storeId);
  console.log('New state:', state);

  // Persist to localStorage
  localStorage.setItem('user', JSON.stringify(state));
});

// Subscribe to actions
store.$onAction(({ name, store, args, after, onError }) => {
  console.log(`Action ${name} called with:`, args);

  after((result) => {
    console.log(`Action ${name} finished with:`, result);
  });

  onError((error) => {
    console.error(`Action ${name} failed:`, error);
  });
});
```

## Composing Stores

```typescript
// stores/useCartStore.ts
import { defineStore } from 'pinia';
import { useUserStore } from './useUserStore';
import { useProductStore } from './useProductStore';

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([]);

  // Use other stores
  const userStore = useUserStore();
  const productStore = useProductStore();

  const total = computed(() => {
    return items.value.reduce((sum, item) => {
      const product = productStore.getById(item.productId);
      return sum + (product?.price ?? 0) * item.quantity;
    }, 0);
  });

  const discount = computed(() => {
    // Premium users get 10% off
    if (userStore.user?.isPremium) {
      return total.value * 0.1;
    }
    return 0;
  });

  const finalTotal = computed(() => total.value - discount.value);

  return { items, total, discount, finalTotal };
});
```

## Best Practices

1. **One store per domain** - Keep stores focused
2. **Use storeToRefs** - Preserve reactivity when destructuring
3. **Type your state** - Full TypeScript support
4. **Prefer setup stores** - Better TypeScript inference
5. **Name stores clearly** - `use[Domain]Store` convention
6. **Keep actions in stores** - Not in components
