# Vue CRUD App Example

Complete CRUD (Create, Read, Update, Delete) application example
demonstrating Vue 3 Composition API patterns.

## Overview

This example demonstrates:
- Component composition
- Pinia state management
- Form handling with validation
- API integration
- Routing patterns

## Project Structure

```
crud-app/
├── src/
│   ├── components/
│   │   ├── ItemList.vue
│   │   ├── ItemForm.vue
│   │   ├── ItemCard.vue
│   │   └── ConfirmDialog.vue
│   ├── composables/
│   │   ├── useItems.ts
│   │   └── useConfirmDialog.ts
│   ├── stores/
│   │   └── useItemStore.ts
│   ├── pages/
│   │   ├── ItemListPage.vue
│   │   ├── ItemDetailPage.vue
│   │   ├── ItemCreatePage.vue
│   │   └── ItemEditPage.vue
│   ├── services/
│   │   └── api.ts
│   ├── types/
│   │   └── index.ts
│   └── router/
│       └── index.ts
└── README.md
```

## Key Patterns

### 1. Pinia Store

```typescript
// stores/useItemStore.ts
import { ref, computed } from 'vue';
import { defineStore } from 'pinia';
import type { Item } from '@/types';
import { itemApi } from '@/services/api';

export const useItemStore = defineStore('items', () => {
  // State
  const items = ref<Item[]>([]);
  const isLoading = ref(false);
  const error = ref<string | null>(null);

  // Getters
  const itemCount = computed(() => items.value.length);

  // Actions
  async function fetchItems() {
    isLoading.value = true;
    try {
      items.value = await itemApi.getAll();
    } catch (e) {
      error.value = (e as Error).message;
    } finally {
      isLoading.value = false;
    }
  }

  async function createItem(data: Omit<Item, 'id'>) {
    const newItem = await itemApi.create(data);
    items.value.push(newItem);
    return newItem;
  }

  async function updateItem(id: string, data: Partial<Item>) {
    const updated = await itemApi.update(id, data);
    const index = items.value.findIndex(i => i.id === id);
    if (index !== -1) {
      items.value[index] = updated;
    }
    return updated;
  }

  async function deleteItem(id: string) {
    await itemApi.delete(id);
    items.value = items.value.filter(i => i.id !== id);
  }

  return {
    items,
    isLoading,
    error,
    itemCount,
    fetchItems,
    createItem,
    updateItem,
    deleteItem,
  };
});
```

### 2. List Component

```vue
<!-- components/ItemList.vue -->
<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { useItemStore } from '@/stores/useItemStore';
import ItemCard from './ItemCard.vue';

const store = useItemStore();
const { items, isLoading } = storeToRefs(store);

const emit = defineEmits<{
  (e: 'select', id: string): void;
  (e: 'delete', id: string): void;
}>();
</script>

<template>
  <div class="item-list">
    <div v-if="isLoading" class="loading">Loading...</div>

    <div v-else-if="items.length === 0" class="empty">
      No items found
    </div>

    <div v-else class="grid">
      <ItemCard
        v-for="item in items"
        :key="item.id"
        :item="item"
        @click="emit('select', item.id)"
        @delete="emit('delete', item.id)"
      />
    </div>
  </div>
</template>
```

### 3. Form Component

```vue
<!-- components/ItemForm.vue -->
<script setup lang="ts">
import { ref, computed, watchEffect } from 'vue';
import type { Item } from '@/types';

interface Props {
  item?: Item;
  isSubmitting?: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'submit', data: Omit<Item, 'id'>): void;
  (e: 'cancel'): void;
}>();

const form = ref({
  name: '',
  description: '',
});

const errors = ref<Record<string, string>>({});

// Initialize form with item data if editing
watchEffect(() => {
  if (props.item) {
    form.value = {
      name: props.item.name,
      description: props.item.description,
    };
  }
});

const isValid = computed(() => {
  return form.value.name.trim().length > 0;
});

function validate() {
  errors.value = {};

  if (!form.value.name.trim()) {
    errors.value.name = 'Name is required';
  }

  return Object.keys(errors.value).length === 0;
}

function handleSubmit() {
  if (!validate()) return;
  emit('submit', { ...form.value });
}
</script>

<template>
  <form @submit.prevent="handleSubmit" class="item-form">
    <div class="field">
      <label for="name">Name</label>
      <input
        id="name"
        v-model="form.name"
        type="text"
        :class="{ error: errors.name }"
      />
      <span v-if="errors.name" class="error-message">{{ errors.name }}</span>
    </div>

    <div class="field">
      <label for="description">Description</label>
      <textarea
        id="description"
        v-model="form.description"
        rows="4"
      />
    </div>

    <div class="actions">
      <button type="button" @click="emit('cancel')">Cancel</button>
      <button type="submit" :disabled="!isValid || isSubmitting">
        {{ isSubmitting ? 'Saving...' : 'Save' }}
      </button>
    </div>
  </form>
</template>
```

### 4. Page Component

```vue
<!-- pages/ItemListPage.vue -->
<script setup lang="ts">
import { onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useItemStore } from '@/stores/useItemStore';
import { useConfirmDialog } from '@/composables/useConfirmDialog';
import ItemList from '@/components/ItemList.vue';
import ConfirmDialog from '@/components/ConfirmDialog.vue';

const router = useRouter();
const store = useItemStore();
const { isOpen, confirm, cancel, onConfirm } = useConfirmDialog();

let pendingDeleteId: string | null = null;

onMounted(() => {
  store.fetchItems();
});

function handleSelect(id: string) {
  router.push({ name: 'item-detail', params: { id } });
}

function handleDelete(id: string) {
  pendingDeleteId = id;
  confirm();
}

onConfirm(async () => {
  if (pendingDeleteId) {
    await store.deleteItem(pendingDeleteId);
    pendingDeleteId = null;
  }
});

function goToCreate() {
  router.push({ name: 'item-create' });
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <h1>Items</h1>
      <button @click="goToCreate">Create New</button>
    </header>

    <ItemList @select="handleSelect" @delete="handleDelete" />

    <ConfirmDialog
      v-if="isOpen"
      title="Delete Item"
      message="Are you sure you want to delete this item?"
      @confirm="confirm"
      @cancel="cancel"
    />
  </div>
</template>
```

## Routes

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/items',
    name: 'item-list',
    component: () => import('@/pages/ItemListPage.vue'),
  },
  {
    path: '/items/create',
    name: 'item-create',
    component: () => import('@/pages/ItemCreatePage.vue'),
  },
  {
    path: '/items/:id',
    name: 'item-detail',
    component: () => import('@/pages/ItemDetailPage.vue'),
  },
  {
    path: '/items/:id/edit',
    name: 'item-edit',
    component: () => import('@/pages/ItemEditPage.vue'),
  },
];

export const router = createRouter({
  history: createWebHistory(),
  routes,
});
```

## API Service

```typescript
// services/api.ts
import type { Item } from '@/types';

const BASE_URL = '/api/items';

export const itemApi = {
  async getAll(): Promise<Item[]> {
    const response = await fetch(BASE_URL);
    return response.json();
  },

  async getById(id: string): Promise<Item> {
    const response = await fetch(`${BASE_URL}/${id}`);
    return response.json();
  },

  async create(data: Omit<Item, 'id'>): Promise<Item> {
    const response = await fetch(BASE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async update(id: string, data: Partial<Item>): Promise<Item> {
    const response = await fetch(`${BASE_URL}/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return response.json();
  },

  async delete(id: string): Promise<void> {
    await fetch(`${BASE_URL}/${id}`, { method: 'DELETE' });
  },
};
```

## Best Practices Demonstrated

1. **Separation of concerns** - Components, stores, services
2. **Type safety** - TypeScript interfaces throughout
3. **Composable patterns** - Reusable logic extraction
4. **Optimistic updates** - Better UX with immediate feedback
5. **Error handling** - Graceful error states
6. **Loading states** - User feedback during async operations
