---
name: rn-feature-based
description: Feature-based architecture for React Native applications
applies_to: react-native
---

# Feature-Based Architecture

## Overview

Feature-based architecture organizes code by business domain rather than technical type. Each feature is a self-contained module with its own components, hooks, API calls, and state.

## Structure

```
src/
├── features/
│   ├── auth/
│   │   ├── components/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   ├── SocialLoginButtons.tsx
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   ├── useBiometricAuth.ts
│   │   │   └── index.ts
│   │   ├── api/
│   │   │   ├── authApi.ts
│   │   │   └── index.ts
│   │   ├── store/
│   │   │   └── useAuthStore.ts
│   │   ├── types.ts
│   │   ├── constants.ts
│   │   └── index.ts
│   │
│   ├── products/
│   │   ├── components/
│   │   │   ├── ProductCard.tsx
│   │   │   ├── ProductList.tsx
│   │   │   ├── ProductFilters.tsx
│   │   │   ├── ProductSkeleton.tsx
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   │   ├── useProducts.ts
│   │   │   ├── useProductSearch.ts
│   │   │   └── index.ts
│   │   ├── api/
│   │   │   └── productApi.ts
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   ├── cart/
│   │   ├── components/
│   │   │   ├── CartItem.tsx
│   │   │   ├── CartSummary.tsx
│   │   │   └── index.ts
│   │   ├── hooks/
│   │   │   └── useCart.ts
│   │   ├── store/
│   │   │   └── useCartStore.ts
│   │   ├── types.ts
│   │   └── index.ts
│   │
│   └── checkout/
│       ├── components/
│       │   ├── CheckoutForm.tsx
│       │   ├── PaymentMethod.tsx
│       │   ├── OrderSummary.tsx
│       │   └── index.ts
│       ├── hooks/
│       │   └── useCheckout.ts
│       ├── api/
│       │   └── checkoutApi.ts
│       ├── types.ts
│       └── index.ts
│
├── components/                  # Shared UI components
│   ├── ui/
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── index.ts
│   └── layout/
│       ├── Container.tsx
│       └── index.ts
│
├── hooks/                       # Shared hooks
│   ├── useDebounce.ts
│   └── index.ts
│
├── lib/                         # Shared utilities
│   ├── api.ts
│   └── utils.ts
│
└── types/                       # Global types
    └── index.ts
```

## Feature Module Structure

### Types Definition

```typescript
// src/features/products/types.ts
export interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  imageUrl: string;
  category: string;
  inStock: boolean;
  createdAt: string;
}

export interface ProductFilters {
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  inStock?: boolean;
  search?: string;
}

export interface ProductsResponse {
  items: Product[];
  total: number;
  page: number;
  totalPages: number;
}

export interface CreateProductInput {
  name: string;
  description: string;
  price: number;
  category: string;
}

export type UpdateProductInput = Partial<CreateProductInput>;
```

### API Layer

```typescript
// src/features/products/api/productApi.ts
import { api } from '@/lib/api';
import type {
  Product,
  ProductFilters,
  ProductsResponse,
  CreateProductInput,
  UpdateProductInput,
} from '../types';

export async function getProducts(
  filters?: ProductFilters,
  page = 1,
  limit = 20
): Promise<ProductsResponse> {
  const { data } = await api.get<ProductsResponse>('/products', {
    params: { ...filters, page, limit },
  });
  return data;
}

export async function getProduct(id: string): Promise<Product> {
  const { data } = await api.get<Product>(`/products/${id}`);
  return data;
}

export async function createProduct(input: CreateProductInput): Promise<Product> {
  const { data } = await api.post<Product>('/products', input);
  return data;
}

export async function updateProduct(
  id: string,
  input: UpdateProductInput
): Promise<Product> {
  const { data } = await api.patch<Product>(`/products/${id}`, input);
  return data;
}

export async function deleteProduct(id: string): Promise<void> {
  await api.delete(`/products/${id}`);
}
```

### Hooks Layer

```typescript
// src/features/products/hooks/useProducts.ts
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import * as productApi from '../api/productApi';
import type { ProductFilters, Product } from '../types';

export const PRODUCT_KEYS = {
  all: ['products'] as const,
  lists: () => [...PRODUCT_KEYS.all, 'list'] as const,
  list: (filters: ProductFilters) => [...PRODUCT_KEYS.lists(), filters] as const,
  details: () => [...PRODUCT_KEYS.all, 'detail'] as const,
  detail: (id: string) => [...PRODUCT_KEYS.details(), id] as const,
};

export function useProducts(filters?: ProductFilters) {
  return useInfiniteQuery({
    queryKey: PRODUCT_KEYS.list(filters ?? {}),
    queryFn: ({ pageParam = 1 }) => productApi.getProducts(filters, pageParam),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.totalPages ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: PRODUCT_KEYS.detail(id),
    queryFn: () => productApi.getProduct(id),
    enabled: !!id,
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: productApi.createProduct,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PRODUCT_KEYS.lists() });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...input }: { id: string } & Parameters<typeof productApi.updateProduct>[1]) =>
      productApi.updateProduct(id, input),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: PRODUCT_KEYS.lists() });
      queryClient.setQueryData(PRODUCT_KEYS.detail(data.id), data);
    },
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: productApi.deleteProduct,
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: PRODUCT_KEYS.lists() });
      queryClient.removeQueries({ queryKey: PRODUCT_KEYS.detail(id) });
    },
  });
}
```

### Components

```typescript
// src/features/products/components/ProductCard.tsx
import { memo } from 'react';
import { View, Text, Image, Pressable, StyleSheet } from 'react-native';
import type { Product } from '../types';

interface ProductCardProps {
  product: Product;
  onPress: (product: Product) => void;
  testID?: string;
}

export const ProductCard = memo(function ProductCard({
  product,
  onPress,
  testID,
}: ProductCardProps) {
  return (
    <Pressable
      style={({ pressed }) => [styles.container, pressed && styles.pressed]}
      onPress={() => onPress(product)}
      testID={testID}
    >
      <Image
        source={{ uri: product.imageUrl }}
        style={styles.image}
        resizeMode="cover"
      />
      <View style={styles.content}>
        <Text style={styles.name} numberOfLines={2}>
          {product.name}
        </Text>
        <Text style={styles.price}>${product.price.toFixed(2)}</Text>
        {!product.inStock && (
          <Text style={styles.outOfStock}>Out of Stock</Text>
        )}
      </View>
    </Pressable>
  );
});

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  pressed: {
    opacity: 0.9,
  },
  image: {
    width: '100%',
    height: 150,
  },
  content: {
    padding: 12,
  },
  name: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  price: {
    fontSize: 18,
    fontWeight: '700',
    color: '#007AFF',
  },
  outOfStock: {
    fontSize: 12,
    color: '#ff3b30',
    marginTop: 4,
  },
});
```

### Feature Index (Public API)

```typescript
// src/features/products/index.ts

// Components - what screens import
export { ProductCard } from './components/ProductCard';
export { ProductList } from './components/ProductList';
export { ProductFilters } from './components/ProductFilters';

// Hooks - for data access
export {
  useProducts,
  useProduct,
  useCreateProduct,
  useUpdateProduct,
  useDeleteProduct,
  PRODUCT_KEYS,
} from './hooks/useProducts';

// Types - for type annotations
export type {
  Product,
  ProductFilters as ProductFiltersType,
  CreateProductInput,
  UpdateProductInput,
} from './types';

// Keep API internal - accessed through hooks only
```

## Cross-Feature Communication

### Via Shared Hooks

```typescript
// src/features/cart/hooks/useCart.ts
import { useCartStore } from '../store/useCartStore';
import type { Product } from '@/features/products';

export function useCart() {
  const { items, addItem, removeItem, updateQuantity, clear } = useCartStore();

  const addProduct = (product: Product) => {
    addItem({
      id: product.id,
      name: product.name,
      price: product.price,
      imageUrl: product.imageUrl,
    });
  };

  return {
    items,
    addProduct,
    removeItem,
    updateQuantity,
    clear,
    itemCount: items.reduce((sum, item) => sum + item.quantity, 0),
    total: items.reduce((sum, item) => sum + item.price * item.quantity, 0),
  };
}
```

### Via Events (Complex Cases)

```typescript
// src/lib/events.ts
import { EventEmitter } from 'events';

export const appEvents = new EventEmitter();

// Feature A emits
appEvents.emit('product:purchased', { productId: '123' });

// Feature B listens
appEvents.on('product:purchased', ({ productId }) => {
  // Handle event
});
```

## Rules

1. **No Direct Imports**: Features should not import from other features' internal modules
2. **Public API Only**: Export only what's needed through `index.ts`
3. **Shared Code**: If used by 3+ features, move to `/components` or `/hooks`
4. **Type Sharing**: Types can be imported across features
5. **API Isolation**: Each feature owns its API calls
