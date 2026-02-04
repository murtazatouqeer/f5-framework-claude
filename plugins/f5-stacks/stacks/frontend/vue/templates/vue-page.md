---
name: vue-page
description: Vue page component template for routes
applies_to: vue
variables:
  - name: pageName
    description: Page component name
  - name: routePath
    description: Route path for this page
---

# Vue Page Template

## Basic Page

```vue
<script setup lang="ts">
// ============================================================
// pages/{{pageName}}Page.vue
// ============================================================

import { ref, onMounted } from 'vue';

// ------------------------------------------------------------
// Page Meta
// ------------------------------------------------------------
defineOptions({
  name: '{{pageName}}Page',
});

// ------------------------------------------------------------
// State
// ------------------------------------------------------------
const isLoading = ref(true);

// ------------------------------------------------------------
// Lifecycle
// ------------------------------------------------------------
onMounted(async () => {
  try {
    // Initialize page data
  } finally {
    isLoading.value = false;
  }
});
</script>

<template>
  <div class="page page-{{pageName | kebab}}">
    <header class="page__header">
      <h1>{{pageName}}</h1>
    </header>

    <main class="page__content">
      <div v-if="isLoading" class="page__loading">
        Loading...
      </div>

      <template v-else>
        <!-- Page content -->
      </template>
    </main>
  </div>
</template>

<style scoped>
.page {
  min-height: 100vh;
  padding: 1rem;
}

.page__header {
  margin-bottom: 1.5rem;
}

.page__header h1 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #111827;
}

.page__content {
  max-width: 1200px;
  margin: 0 auto;
}

.page__loading {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style>
```

## Page with Route Params

```vue
<script setup lang="ts">
// ============================================================
// pages/{{pageName}}DetailPage.vue
// ============================================================

import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// ------------------------------------------------------------
// Page Meta
// ------------------------------------------------------------
defineOptions({
  name: '{{pageName}}DetailPage',
});

// ------------------------------------------------------------
// Types
// ------------------------------------------------------------
interface {{pageName}} {
  id: string;
  name: string;
  // Add other fields
}

// ------------------------------------------------------------
// Router
// ------------------------------------------------------------
const route = useRoute();
const router = useRouter();

const id = computed(() => route.params.id as string);

// ------------------------------------------------------------
// State
// ------------------------------------------------------------
const item = ref<{{pageName}} | null>(null);
const isLoading = ref(true);
const error = ref<string | null>(null);

// ------------------------------------------------------------
// Data Fetching
// ------------------------------------------------------------
async function fetchItem() {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await fetch(`/api/{{pageName | kebab}}s/${id.value}`);

    if (!response.ok) {
      if (response.status === 404) {
        throw new Error('Item not found');
      }
      throw new Error('Failed to fetch item');
    }

    item.value = await response.json();
  } catch (e) {
    error.value = (e as Error).message;
  } finally {
    isLoading.value = false;
  }
}

// ------------------------------------------------------------
// Navigation
// ------------------------------------------------------------
function goBack() {
  router.back();
}

function goToEdit() {
  router.push({ name: '{{pageName}}Edit', params: { id: id.value } });
}

// ------------------------------------------------------------
// Watchers
// ------------------------------------------------------------
watch(id, () => {
  fetchItem();
});

// ------------------------------------------------------------
// Lifecycle
// ------------------------------------------------------------
onMounted(() => {
  fetchItem();
});
</script>

<template>
  <div class="page page-{{pageName | kebab}}-detail">
    <header class="page__header">
      <button class="btn-back" @click="goBack">
        ← Back
      </button>
      <h1>{{pageName}} Details</h1>
    </header>

    <main class="page__content">
      <!-- Loading State -->
      <div v-if="isLoading" class="page__loading">
        <span>Loading...</span>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="page__error">
        <p>{{ error }}</p>
        <button @click="fetchItem">Retry</button>
      </div>

      <!-- Content -->
      <template v-else-if="item">
        <div class="detail-card">
          <h2>{{ item.name }}</h2>
          <!-- Add other fields -->
        </div>

        <div class="page__actions">
          <button class="btn btn--primary" @click="goToEdit">
            Edit
          </button>
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page__header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.btn-back {
  padding: 0.5rem;
  background: none;
  border: none;
  cursor: pointer;
  color: #6b7280;
}

.page__error {
  text-align: center;
  padding: 2rem;
  color: #ef4444;
}

.detail-card {
  background: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.page__actions {
  margin-top: 1.5rem;
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
}

.btn--primary {
  background-color: #3b82f6;
  color: white;
  border: none;
}
</style>
```

## List Page with Pagination

```vue
<script setup lang="ts">
// ============================================================
// pages/{{pageName}}ListPage.vue
// ============================================================

import { ref, computed, watch, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';

// ------------------------------------------------------------
// Page Meta
// ------------------------------------------------------------
defineOptions({
  name: '{{pageName}}ListPage',
});

// ------------------------------------------------------------
// Types
// ------------------------------------------------------------
interface {{pageName}} {
  id: string;
  name: string;
}

interface PaginationMeta {
  page: number;
  pageSize: number;
  total: number;
  totalPages: number;
}

// ------------------------------------------------------------
// Router
// ------------------------------------------------------------
const route = useRoute();
const router = useRouter();

// ------------------------------------------------------------
// State
// ------------------------------------------------------------
const items = ref<{{pageName}}[]>([]);
const pagination = ref<PaginationMeta>({
  page: 1,
  pageSize: 10,
  total: 0,
  totalPages: 0,
});
const isLoading = ref(true);
const searchQuery = ref('');

// ------------------------------------------------------------
// Computed
// ------------------------------------------------------------
const currentPage = computed({
  get: () => Number(route.query.page) || 1,
  set: (value) => {
    router.push({
      query: { ...route.query, page: String(value) },
    });
  },
});

// ------------------------------------------------------------
// Data Fetching
// ------------------------------------------------------------
async function fetchItems() {
  isLoading.value = true;

  try {
    const params = new URLSearchParams({
      page: String(currentPage.value),
      pageSize: String(pagination.value.pageSize),
      ...(searchQuery.value && { search: searchQuery.value }),
    });

    const response = await fetch(`/api/{{pageName | kebab}}s?${params}`);
    const data = await response.json();

    items.value = data.items;
    pagination.value = data.pagination;
  } finally {
    isLoading.value = false;
  }
}

// ------------------------------------------------------------
// Actions
// ------------------------------------------------------------
function handleSearch() {
  currentPage.value = 1;
  fetchItems();
}

function goToDetail(id: string) {
  router.push({ name: '{{pageName}}Detail', params: { id } });
}

function goToCreate() {
  router.push({ name: '{{pageName}}Create' });
}

// ------------------------------------------------------------
// Watchers
// ------------------------------------------------------------
watch(currentPage, () => {
  fetchItems();
});

// ------------------------------------------------------------
// Lifecycle
// ------------------------------------------------------------
onMounted(() => {
  fetchItems();
});
</script>

<template>
  <div class="page page-{{pageName | kebab}}-list">
    <header class="page__header">
      <h1>{{pageName}}s</h1>
      <button class="btn btn--primary" @click="goToCreate">
        Create New
      </button>
    </header>

    <div class="page__toolbar">
      <input
        v-model="searchQuery"
        type="search"
        placeholder="Search..."
        @keyup.enter="handleSearch"
      />
      <button @click="handleSearch">Search</button>
    </div>

    <main class="page__content">
      <div v-if="isLoading" class="page__loading">
        Loading...
      </div>

      <template v-else>
        <div v-if="items.length === 0" class="page__empty">
          No items found
        </div>

        <ul v-else class="item-list">
          <li
            v-for="item in items"
            :key="item.id"
            class="item-list__item"
            @click="goToDetail(item.id)"
          >
            {{ item.name }}
          </li>
        </ul>

        <!-- Pagination -->
        <nav v-if="pagination.totalPages > 1" class="pagination">
          <button
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            Previous
          </button>

          <span>
            Page {{ currentPage }} of {{ pagination.totalPages }}
          </span>

          <button
            :disabled="currentPage === pagination.totalPages"
            @click="currentPage++"
          >
            Next
          </button>
        </nav>
      </template>
    </main>
  </div>
</template>

<style scoped>
.page__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.page__toolbar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.page__toolbar input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
}

.item-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.item-list__item {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  cursor: pointer;
}

.item-list__item:hover {
  background-color: #f9fafb;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1.5rem;
}

.page__empty {
  text-align: center;
  padding: 2rem;
  color: #6b7280;
}
</style>
```

## Route Configuration

```typescript
// router/index.ts
import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/{{pageName | kebab}}s',
    name: '{{pageName}}List',
    component: () => import('@/pages/{{pageName}}ListPage.vue'),
    meta: { title: '{{pageName}}s' },
  },
  {
    path: '/{{pageName | kebab}}s/create',
    name: '{{pageName}}Create',
    component: () => import('@/pages/{{pageName}}CreatePage.vue'),
    meta: { title: 'Create {{pageName}}' },
  },
  {
    path: '/{{pageName | kebab}}s/:id',
    name: '{{pageName}}Detail',
    component: () => import('@/pages/{{pageName}}DetailPage.vue'),
    meta: { title: '{{pageName}} Details' },
  },
  {
    path: '/{{pageName | kebab}}s/:id/edit',
    name: '{{pageName}}Edit',
    component: () => import('@/pages/{{pageName}}EditPage.vue'),
    meta: { title: 'Edit {{pageName}}' },
  },
];
```
