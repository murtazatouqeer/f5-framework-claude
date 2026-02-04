---
name: vue-store
description: Pinia store template
applies_to: vue
variables:
  - name: storeName
    description: Store name (without use prefix)
  - name: entityName
    description: Entity type managed by store
---

# Vue Store Template

## Setup Store (Recommended)

```typescript
// ============================================================
// stores/use{{storeName}}Store.ts
// ============================================================

import { ref, computed } from 'vue';
import { defineStore } from 'pinia';

// ------------------------------------------------------------
// Types
// ------------------------------------------------------------
interface {{entityName}} {
  id: string;
  // Add entity fields
}

interface {{storeName}}State {
  items: {{entityName}}[];
  currentItem: {{entityName}} | null;
  isLoading: boolean;
  error: string | null;
}

// ------------------------------------------------------------
// Store
// ------------------------------------------------------------
export const use{{storeName}}Store = defineStore('{{storeName | kebab}}', () => {
  // --------------------------------------------------------
  // State
  // --------------------------------------------------------
  const items = ref<{{entityName}}[]>([]);
  const currentItem = ref<{{entityName}} | null>(null);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // --------------------------------------------------------
  // Getters
  // --------------------------------------------------------
  const itemCount = computed(() => items.value.length);

  const itemById = computed(() => {
    return (id: string) => items.value.find(item => item.id === id);
  });

  const hasItems = computed(() => items.value.length > 0);

  // --------------------------------------------------------
  // Actions
  // --------------------------------------------------------
  async function fetchItems() {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/{{entityName | kebab}}s');

      if (!response.ok) {
        throw new Error('Failed to fetch items');
      }

      items.value = await response.json();
    } catch (e) {
      error.value = (e as Error).message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  async function fetchItemById(id: string) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/{{entityName | kebab}}s/${id}`);

      if (!response.ok) {
        throw new Error('Failed to fetch item');
      }

      currentItem.value = await response.json();
      return currentItem.value;
    } catch (e) {
      error.value = (e as Error).message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  async function createItem(data: Omit<{{entityName}}, 'id'>) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/{{entityName | kebab}}s', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to create item');
      }

      const newItem = await response.json();
      items.value.push(newItem);
      return newItem;
    } catch (e) {
      error.value = (e as Error).message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  async function updateItem(id: string, data: Partial<{{entityName}}>) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/{{entityName | kebab}}s/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to update item');
      }

      const updatedItem = await response.json();

      // Update in list
      const index = items.value.findIndex(item => item.id === id);
      if (index !== -1) {
        items.value[index] = updatedItem;
      }

      // Update current if same
      if (currentItem.value?.id === id) {
        currentItem.value = updatedItem;
      }

      return updatedItem;
    } catch (e) {
      error.value = (e as Error).message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  async function deleteItem(id: string) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch(`/api/{{entityName | kebab}}s/${id}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete item');
      }

      // Remove from list
      items.value = items.value.filter(item => item.id !== id);

      // Clear current if same
      if (currentItem.value?.id === id) {
        currentItem.value = null;
      }
    } catch (e) {
      error.value = (e as Error).message;
      throw e;
    } finally {
      isLoading.value = false;
    }
  }

  function clearError() {
    error.value = null;
  }

  function clearCurrent() {
    currentItem.value = null;
  }

  function $reset() {
    items.value = [];
    currentItem.value = null;
    isLoading.value = false;
    error.value = null;
  }

  // --------------------------------------------------------
  // Return
  // --------------------------------------------------------
  return {
    // State
    items,
    currentItem,
    isLoading,
    error,

    // Getters
    itemCount,
    itemById,
    hasItems,

    // Actions
    fetchItems,
    fetchItemById,
    createItem,
    updateItem,
    deleteItem,
    clearError,
    clearCurrent,
    $reset,
  };
});
```

## Options Store

```typescript
// ============================================================
// stores/use{{storeName}}Store.ts (Options API style)
// ============================================================

import { defineStore } from 'pinia';

interface {{entityName}} {
  id: string;
  // Add entity fields
}

interface State {
  items: {{entityName}}[];
  currentItem: {{entityName}} | null;
  isLoading: boolean;
  error: string | null;
}

export const use{{storeName}}Store = defineStore('{{storeName | kebab}}', {
  state: (): State => ({
    items: [],
    currentItem: null,
    isLoading: false,
    error: null,
  }),

  getters: {
    itemCount: (state) => state.items.length,

    itemById: (state) => {
      return (id: string) => state.items.find(item => item.id === id);
    },

    hasItems: (state) => state.items.length > 0,
  },

  actions: {
    async fetchItems() {
      this.isLoading = true;
      this.error = null;

      try {
        const response = await fetch('/api/{{entityName | kebab}}s');
        this.items = await response.json();
      } catch (e) {
        this.error = (e as Error).message;
      } finally {
        this.isLoading = false;
      }
    },

    async createItem(data: Omit<{{entityName}}, 'id'>) {
      this.isLoading = true;

      try {
        const response = await fetch('/api/{{entityName | kebab}}s', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        });

        const newItem = await response.json();
        this.items.push(newItem);
        return newItem;
      } finally {
        this.isLoading = false;
      }
    },
  },
});
```

## Auth Store Example

```typescript
// ============================================================
// stores/useAuthStore.ts
// ============================================================

import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import { useRouter } from 'vue-router';

interface User {
  id: string;
  email: string;
  name: string;
  roles: string[];
}

interface LoginCredentials {
  email: string;
  password: string;
}

export const useAuthStore = defineStore('auth', () => {
  const router = useRouter();

  // State
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('token'));
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Getters
  const isAuthenticated = computed(() => !!token.value && !!user.value);
  const isAdmin = computed(() => user.value?.roles.includes('admin') ?? false);

  // Actions
  async function login(credentials: LoginCredentials) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        throw new Error('Invalid credentials');
      }

      const data = await response.json();

      token.value = data.token;
      user.value = data.user;

      localStorage.setItem('token', data.token);

      return true;
    } catch (e) {
      error.value = (e as Error).message;
      return false;
    } finally {
      isLoading.value = false;
    }
  }

  async function logout() {
    token.value = null;
    user.value = null;
    localStorage.removeItem('token');
    router.push('/login');
  }

  async function fetchUser() {
    if (!token.value) return;

    try {
      const response = await fetch('/api/auth/me', {
        headers: { Authorization: `Bearer ${token.value}` },
      });

      if (response.ok) {
        user.value = await response.json();
      } else {
        logout();
      }
    } catch {
      logout();
    }
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    logout,
    fetchUser,
  };
});
```

## Usage

```vue
<script setup lang="ts">
import { onMounted } from 'vue';
import { use{{storeName}}Store } from '@/stores/use{{storeName}}Store';
import { storeToRefs } from 'pinia';

const store = use{{storeName}}Store();

// Destructure reactive state
const { items, isLoading, error } = storeToRefs(store);

// Actions don't need storeToRefs
const { fetchItems, createItem, deleteItem } = store;

onMounted(() => {
  fetchItems();
});

async function handleCreate() {
  await createItem({ name: 'New Item' });
}

async function handleDelete(id: string) {
  await deleteItem(id);
}
</script>

<template>
  <div v-if="isLoading">Loading...</div>
  <div v-else-if="error">Error: {{ error }}</div>
  <ul v-else>
    <li v-for="item in items" :key="item.id">
      {{ item.name }}
      <button @click="handleDelete(item.id)">Delete</button>
    </li>
  </ul>
  <button @click="handleCreate">Add Item</button>
</template>
```
