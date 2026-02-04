---
name: pinia-nuxt
description: Pinia state management with Nuxt 3
applies_to: nuxt
---

# Pinia with Nuxt 3

## Overview

Pinia is the official state management solution for Vue 3, with first-class Nuxt integration for SSR-safe stores.

## Setup

```bash
npx nuxi@latest module add pinia
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@pinia/nuxt'],
});
```

## Basic Store

```typescript
// stores/counter.ts
export const useCounterStore = defineStore('counter', {
  state: () => ({
    count: 0,
  }),

  getters: {
    doubled: (state) => state.count * 2,
  },

  actions: {
    increment() {
      this.count++;
    },

    async incrementAsync() {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      this.count++;
    },
  },
});
```

## Setup Store Syntax

```typescript
// stores/products.ts
export const useProductStore = defineStore('products', () => {
  // State
  const products = ref<Product[]>([]);
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  // Getters
  const totalProducts = computed(() => products.value.length);

  const activeProducts = computed(() =>
    products.value.filter((p) => p.status === 'active')
  );

  const getById = computed(() => (id: string) =>
    products.value.find((p) => p.id === id)
  );

  // Actions
  async function fetchProducts() {
    isLoading.value = true;
    error.value = null;

    try {
      products.value = await $fetch<Product[]>('/api/products');
    } catch (e) {
      error.value = e instanceof Error ? e : new Error('Failed to fetch');
    } finally {
      isLoading.value = false;
    }
  }

  async function createProduct(data: CreateProductInput) {
    const product = await $fetch<Product>('/api/products', {
      method: 'POST',
      body: data,
    });

    products.value.push(product);
    return product;
  }

  async function updateProduct(id: string, data: Partial<Product>) {
    const updated = await $fetch<Product>(`/api/products/${id}`, {
      method: 'PUT',
      body: data,
    });

    const index = products.value.findIndex((p) => p.id === id);
    if (index !== -1) {
      products.value[index] = updated;
    }

    return updated;
  }

  async function deleteProduct(id: string) {
    await $fetch(`/api/products/${id}`, { method: 'DELETE' });
    products.value = products.value.filter((p) => p.id !== id);
  }

  return {
    // State
    products,
    isLoading,
    error,
    // Getters
    totalProducts,
    activeProducts,
    getById,
    // Actions
    fetchProducts,
    createProduct,
    updateProduct,
    deleteProduct,
  };
});
```

## Using Stores in Components

```vue
<script setup lang="ts">
const productStore = useProductStore();

// Access state
const { products, isLoading, error } = storeToRefs(productStore);

// Access getters
const { totalProducts, activeProducts } = storeToRefs(productStore);

// Call actions
await productStore.fetchProducts();

// Or destructure actions directly
const { createProduct, deleteProduct } = productStore;
</script>

<template>
  <div v-if="isLoading">Loading...</div>
  <div v-else-if="error">{{ error.message }}</div>
  <div v-else>
    <p>Total: {{ totalProducts }}</p>
    <ProductList :products="activeProducts" @delete="deleteProduct" />
  </div>
</template>
```

## SSR Hydration

```typescript
// stores/user.ts
export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null);

  async function fetchUser() {
    // Use $fetch for SSR compatibility
    user.value = await $fetch<User>('/api/auth/me');
  }

  return { user, fetchUser };
});
```

```typescript
// plugins/user.ts
export default defineNuxtPlugin(async () => {
  const userStore = useUserStore();

  // Fetch on server, hydrate on client
  if (import.meta.server) {
    await userStore.fetchUser();
  }
});
```

## Store Persistence

```bash
npm install @pinia-plugin-persistedstate/nuxt
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: [
    '@pinia/nuxt',
    '@pinia-plugin-persistedstate/nuxt',
  ],
});
```

```typescript
// stores/settings.ts
export const useSettingsStore = defineStore('settings', () => {
  const theme = ref<'light' | 'dark'>('light');
  const language = ref('en');

  return { theme, language };
}, {
  persist: true, // Persist to localStorage
});

// Custom persistence
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([]);

  return { items };
}, {
  persist: {
    storage: persistedState.localStorage,
    paths: ['items'],
  },
});
```

## Store Composition

```typescript
// stores/checkout.ts
export const useCheckoutStore = defineStore('checkout', () => {
  // Use other stores
  const cartStore = useCartStore();
  const userStore = useUserStore();

  const shippingAddress = ref<Address | null>(null);
  const paymentMethod = ref<string | null>(null);

  const canCheckout = computed(() =>
    cartStore.items.length > 0 &&
    userStore.user &&
    shippingAddress.value &&
    paymentMethod.value
  );

  async function processOrder() {
    if (!canCheckout.value) {
      throw new Error('Cannot process order');
    }

    const order = await $fetch('/api/orders', {
      method: 'POST',
      body: {
        items: cartStore.items,
        userId: userStore.user!.id,
        shippingAddress: shippingAddress.value,
        paymentMethod: paymentMethod.value,
      },
    });

    // Clear cart after order
    cartStore.clearCart();

    return order;
  }

  return {
    shippingAddress,
    paymentMethod,
    canCheckout,
    processOrder,
  };
});
```

## Store Subscriptions

```typescript
// plugins/store-logger.ts
export default defineNuxtPlugin(() => {
  const productStore = useProductStore();

  // Subscribe to state changes
  productStore.$subscribe((mutation, state) => {
    console.log('Store changed:', mutation.type, state);

    // Sync to external service
    if (mutation.type === 'direct') {
      syncToAnalytics(state);
    }
  });

  // Subscribe to actions
  productStore.$onAction(({ name, args, after, onError }) => {
    console.log(`Action ${name} called with:`, args);

    after((result) => {
      console.log(`Action ${name} completed:`, result);
    });

    onError((error) => {
      console.error(`Action ${name} failed:`, error);
    });
  });
});
```

## Testing Stores

```typescript
// tests/stores/products.test.ts
import { setActivePinia, createPinia } from 'pinia';
import { useProductStore } from '~/stores/products';

describe('Product Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetches products', async () => {
    const mockProducts = [{ id: '1', name: 'Product 1' }];
    vi.mocked($fetch).mockResolvedValueOnce(mockProducts);

    const store = useProductStore();
    await store.fetchProducts();

    expect(store.products).toEqual(mockProducts);
    expect(store.isLoading).toBe(false);
  });

  it('handles fetch error', async () => {
    vi.mocked($fetch).mockRejectedValueOnce(new Error('Network error'));

    const store = useProductStore();
    await store.fetchProducts();

    expect(store.error).toBeInstanceOf(Error);
    expect(store.products).toEqual([]);
  });
});
```

## Best Practices

1. **Use Setup syntax** - More flexible, better TypeScript
2. **$fetch for API calls** - SSR compatible
3. **storeToRefs for reactivity** - Preserve reactivity when destructuring
4. **Compose stores** - Keep stores focused, combine when needed
5. **Persist wisely** - Only persist necessary data
6. **Type everything** - Full TypeScript support
