---
name: nuxt-crud-app
description: Complete CRUD application example with Nuxt 3
applies_to: nuxt
---

# Nuxt CRUD Application Example

A complete CRUD (Create, Read, Update, Delete) application demonstrating Nuxt 3 best practices.

## Project Structure

```
nuxt-crud-app/
├── nuxt.config.ts
├── app.vue
├── pages/
│   ├── index.vue
│   └── products/
│       ├── index.vue
│       ├── [id].vue
│       └── new.vue
├── components/
│   ├── ProductCard.vue
│   ├── ProductForm.vue
│   └── ProductList.vue
├── composables/
│   ├── useProducts.ts
│   └── useProductCrud.ts
├── server/
│   ├── api/
│   │   └── products/
│   │       ├── index.get.ts
│   │       ├── index.post.ts
│   │       ├── [id].get.ts
│   │       ├── [id].put.ts
│   │       └── [id].delete.ts
│   └── utils/
│       └── db.ts
└── types/
    └── product.ts
```

## Configuration

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxt/ui', '@pinia/nuxt'],
  runtimeConfig: {
    databaseUrl: process.env.DATABASE_URL,
  },
});
```

## Types

```typescript
// types/product.ts
export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  category: string;
  inStock: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface CreateProductInput {
  name: string;
  description?: string;
  price: number;
  category: string;
}

export interface UpdateProductInput {
  name?: string;
  description?: string;
  price?: number;
  category?: string;
  inStock?: boolean;
}

export interface ProductsResponse {
  items: Product[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}
```

## Composables

```typescript
// composables/useProducts.ts
export function useProducts() {
  const products = ref<Product[]>([]);
  const pagination = ref({
    page: 1,
    limit: 20,
    total: 0,
    totalPages: 0,
  });
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function fetch(page = 1) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await $fetch<ProductsResponse>('/api/products', {
        query: { page, limit: pagination.value.limit },
      });
      products.value = response.items;
      pagination.value = response.pagination;
    } catch (e) {
      error.value = e as Error;
    } finally {
      isLoading.value = false;
    }
  }

  return {
    products: readonly(products),
    pagination: readonly(pagination),
    isLoading: readonly(isLoading),
    error: readonly(error),
    fetch,
  };
}
```

```typescript
// composables/useProductCrud.ts
export function useProductCrud() {
  const isSubmitting = ref(false);

  async function create(data: CreateProductInput) {
    isSubmitting.value = true;
    try {
      return await $fetch<Product>('/api/products', {
        method: 'POST',
        body: data,
      });
    } finally {
      isSubmitting.value = false;
    }
  }

  async function update(id: string, data: UpdateProductInput) {
    isSubmitting.value = true;
    try {
      return await $fetch<Product>(`/api/products/${id}`, {
        method: 'PUT',
        body: data,
      });
    } finally {
      isSubmitting.value = false;
    }
  }

  async function remove(id: string) {
    isSubmitting.value = true;
    try {
      await $fetch(`/api/products/${id}`, { method: 'DELETE' });
    } finally {
      isSubmitting.value = false;
    }
  }

  return {
    create,
    update,
    remove,
    isSubmitting: readonly(isSubmitting),
  };
}
```

## API Routes

```typescript
// server/api/products/index.get.ts
import { z } from 'zod';

const querySchema = z.object({
  page: z.coerce.number().positive().default(1),
  limit: z.coerce.number().positive().max(100).default(20),
  category: z.string().optional(),
  search: z.string().optional(),
});

export default defineEventHandler(async (event) => {
  const query = getQuery(event);
  const { page, limit, category, search } = querySchema.parse(query);

  const offset = (page - 1) * limit;

  const where: any = {};
  if (category) where.category = category;
  if (search) {
    where.OR = [
      { name: { contains: search, mode: 'insensitive' } },
      { description: { contains: search, mode: 'insensitive' } },
    ];
  }

  const [items, total] = await Promise.all([
    prisma.product.findMany({
      where,
      skip: offset,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    prisma.product.count({ where }),
  ]);

  return {
    items,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
    },
  };
});
```

```typescript
// server/api/products/index.post.ts
import { z } from 'zod';

const createSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().max(1000).optional(),
  price: z.number().positive(),
  category: z.string().min(1),
});

export default defineEventHandler(async (event) => {
  const body = await readBody(event);
  const data = createSchema.parse(body);

  const product = await prisma.product.create({
    data: {
      ...data,
      inStock: true,
    },
  });

  setResponseStatus(event, 201);
  return product;
});
```

```typescript
// server/api/products/[id].get.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  const product = await prisma.product.findUnique({
    where: { id },
  });

  if (!product) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Product not found',
    });
  }

  return product;
});
```

```typescript
// server/api/products/[id].put.ts
import { z } from 'zod';

const updateSchema = z.object({
  name: z.string().min(1).max(255).optional(),
  description: z.string().max(1000).optional(),
  price: z.number().positive().optional(),
  category: z.string().min(1).optional(),
  inStock: z.boolean().optional(),
});

export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');
  const body = await readBody(event);
  const data = updateSchema.parse(body);

  const product = await prisma.product.update({
    where: { id },
    data,
  });

  return product;
});
```

```typescript
// server/api/products/[id].delete.ts
export default defineEventHandler(async (event) => {
  const id = getRouterParam(event, 'id');

  await prisma.product.delete({ where: { id } });

  setResponseStatus(event, 204);
  return null;
});
```

## Pages

```vue
<!-- pages/products/index.vue -->
<script setup lang="ts">
useSeoMeta({
  title: 'Products',
  description: 'Browse our product catalog',
});

const { products, pagination, isLoading, error, fetch } = useProducts();
const route = useRoute();

const currentPage = computed(() => Number(route.query.page) || 1);

watch(currentPage, (page) => fetch(page), { immediate: true });

function goToPage(page: number) {
  navigateTo({ query: { ...route.query, page } });
}
</script>

<template>
  <div class="products-page">
    <header class="products-page__header">
      <h1>Products</h1>
      <NuxtLink to="/products/new" class="btn btn-primary">
        Add Product
      </NuxtLink>
    </header>

    <div v-if="isLoading" class="loading">Loading...</div>
    <div v-else-if="error" class="error">{{ error.message }}</div>

    <template v-else>
      <ProductList :products="products" />

      <div class="pagination">
        <button
          :disabled="currentPage === 1"
          @click="goToPage(currentPage - 1)"
        >
          Previous
        </button>
        <span>Page {{ currentPage }} of {{ pagination.totalPages }}</span>
        <button
          :disabled="currentPage === pagination.totalPages"
          @click="goToPage(currentPage + 1)"
        >
          Next
        </button>
      </div>
    </template>
  </div>
</template>
```

```vue
<!-- pages/products/[id].vue -->
<script setup lang="ts">
const route = useRoute();
const id = computed(() => route.params.id as string);

const { data: product, pending, error } = await useFetch<Product>(
  () => `/api/products/${id.value}`
);

if (!product.value && !pending.value) {
  throw createError({
    statusCode: 404,
    statusMessage: 'Product not found',
  });
}

useSeoMeta({
  title: () => product.value?.name || 'Product',
});

const { remove, isSubmitting } = useProductCrud();

async function handleDelete() {
  if (!confirm('Are you sure you want to delete this product?')) return;

  await remove(id.value);
  navigateTo('/products');
}
</script>

<template>
  <div class="product-detail">
    <div v-if="pending">Loading...</div>
    <div v-else-if="error">{{ error.message }}</div>

    <template v-else-if="product">
      <h1>{{ product.name }}</h1>
      <p class="price">${{ product.price.toFixed(2) }}</p>
      <p class="description">{{ product.description }}</p>
      <p class="category">Category: {{ product.category }}</p>
      <p class="stock" :class="{ 'in-stock': product.inStock }">
        {{ product.inStock ? 'In Stock' : 'Out of Stock' }}
      </p>

      <div class="actions">
        <NuxtLink :to="`/products/${id}/edit`" class="btn">Edit</NuxtLink>
        <button
          class="btn btn-danger"
          :disabled="isSubmitting"
          @click="handleDelete"
        >
          Delete
        </button>
      </div>
    </template>
  </div>
</template>
```

```vue
<!-- pages/products/new.vue -->
<script setup lang="ts">
useSeoMeta({ title: 'New Product' });

const { create, isSubmitting } = useProductCrud();

async function handleSubmit(data: CreateProductInput) {
  const product = await create(data);
  navigateTo(`/products/${product.id}`);
}
</script>

<template>
  <div class="new-product">
    <h1>New Product</h1>
    <ProductForm :submitting="isSubmitting" @submit="handleSubmit" />
  </div>
</template>
```

## Components

```vue
<!-- components/ProductCard.vue -->
<script setup lang="ts">
defineProps<{
  product: Product;
}>();
</script>

<template>
  <NuxtLink :to="`/products/${product.id}`" class="product-card">
    <h3>{{ product.name }}</h3>
    <p class="price">${{ product.price.toFixed(2) }}</p>
    <p class="category">{{ product.category }}</p>
    <span class="stock" :class="{ available: product.inStock }">
      {{ product.inStock ? '✓ In Stock' : '✗ Out of Stock' }}
    </span>
  </NuxtLink>
</template>
```

```vue
<!-- components/ProductForm.vue -->
<script setup lang="ts">
import { z } from 'zod';

const props = defineProps<{
  product?: Product;
  submitting?: boolean;
}>();

const emit = defineEmits<{
  submit: [data: CreateProductInput | UpdateProductInput];
}>();

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional(),
  price: z.number().positive('Price must be positive'),
  category: z.string().min(1, 'Category is required'),
});

const form = reactive({
  name: props.product?.name || '',
  description: props.product?.description || '',
  price: props.product?.price || 0,
  category: props.product?.category || '',
});

const errors = ref<Record<string, string>>({});

function handleSubmit() {
  errors.value = {};

  const result = schema.safeParse(form);
  if (!result.success) {
    result.error.errors.forEach((err) => {
      errors.value[err.path[0]] = err.message;
    });
    return;
  }

  emit('submit', result.data);
}
</script>

<template>
  <form class="product-form" @submit.prevent="handleSubmit">
    <div class="field">
      <label for="name">Name</label>
      <input id="name" v-model="form.name" type="text" />
      <span v-if="errors.name" class="error">{{ errors.name }}</span>
    </div>

    <div class="field">
      <label for="description">Description</label>
      <textarea id="description" v-model="form.description" rows="3" />
    </div>

    <div class="field">
      <label for="price">Price</label>
      <input id="price" v-model.number="form.price" type="number" step="0.01" />
      <span v-if="errors.price" class="error">{{ errors.price }}</span>
    </div>

    <div class="field">
      <label for="category">Category</label>
      <select id="category" v-model="form.category">
        <option value="">Select category</option>
        <option value="electronics">Electronics</option>
        <option value="clothing">Clothing</option>
        <option value="books">Books</option>
        <option value="home">Home & Garden</option>
      </select>
      <span v-if="errors.category" class="error">{{ errors.category }}</span>
    </div>

    <button type="submit" :disabled="submitting">
      {{ submitting ? 'Saving...' : 'Save Product' }}
    </button>
  </form>
</template>
```

## Testing

```typescript
// tests/products.test.ts
import { describe, it, expect, vi } from 'vitest';
import { mountSuspended } from '@nuxt/test-utils/runtime';
import ProductCard from '~/components/ProductCard.vue';

describe('ProductCard', () => {
  const mockProduct = {
    id: '1',
    name: 'Test Product',
    description: 'A test product',
    price: 29.99,
    category: 'electronics',
    inStock: true,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  it('renders product information', async () => {
    const wrapper = await mountSuspended(ProductCard, {
      props: { product: mockProduct },
    });

    expect(wrapper.text()).toContain('Test Product');
    expect(wrapper.text()).toContain('$29.99');
    expect(wrapper.text()).toContain('electronics');
  });
});
```

## Key Features Demonstrated

1. **Type-safe development** with TypeScript
2. **Data fetching** with useFetch and composables
3. **Form validation** with Zod
4. **Server API routes** with Nitro
5. **Pagination** and filtering
6. **SEO** with useSeoMeta
7. **Navigation** with NuxtLink
8. **Error handling** throughout the stack
9. **Component composition** with props and emits
10. **Testing** with Vitest
