---
name: rn-tanstack-query
description: TanStack Query (React Query) for server state in React Native
applies_to: react-native
---

# TanStack Query in React Native

## Installation

```bash
npm install @tanstack/react-query
```

## Setup

```typescript
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false, // Not applicable to mobile
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

```typescript
// App.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from '@/lib/queryClient';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        <RootNavigator />
      </NavigationContainer>
    </QueryClientProvider>
  );
}
```

## Query Keys

```typescript
// src/features/products/queryKeys.ts
export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (filters: ProductFilters) => [...productKeys.lists(), filters] as const,
  details: () => [...productKeys.all, 'detail'] as const,
  detail: (id: string) => [...productKeys.details(), id] as const,
};

// Usage
queryClient.invalidateQueries({ queryKey: productKeys.all });
queryClient.invalidateQueries({ queryKey: productKeys.lists() });
queryClient.invalidateQueries({ queryKey: productKeys.detail('123') });
```

## Basic Query

```typescript
// src/features/products/hooks/useProducts.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { productKeys } from '../queryKeys';
import type { Product, ProductFilters } from '../types';

async function fetchProducts(filters?: ProductFilters): Promise<Product[]> {
  const { data } = await api.get('/products', { params: filters });
  return data;
}

export function useProducts(filters?: ProductFilters) {
  return useQuery({
    queryKey: productKeys.list(filters ?? {}),
    queryFn: () => fetchProducts(filters),
  });
}

// Usage
function ProductList() {
  const { data, isLoading, isError, error, refetch } = useProducts({
    category: 'electronics',
  });

  if (isLoading) return <LoadingSpinner />;
  if (isError) return <ErrorMessage error={error} />;

  return (
    <FlatList
      data={data}
      renderItem={({ item }) => <ProductCard product={item} />}
      onRefresh={refetch}
      refreshing={false}
    />
  );
}
```

## Infinite Query

```typescript
// src/features/products/hooks/useInfiniteProducts.ts
import { useInfiniteQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { productKeys } from '../queryKeys';

interface ProductsResponse {
  items: Product[];
  page: number;
  totalPages: number;
  total: number;
}

async function fetchProducts(
  page: number,
  filters?: ProductFilters
): Promise<ProductsResponse> {
  const { data } = await api.get('/products', {
    params: { page, limit: 20, ...filters },
  });
  return data;
}

export function useInfiniteProducts(filters?: ProductFilters) {
  return useInfiniteQuery({
    queryKey: productKeys.list(filters ?? {}),
    queryFn: ({ pageParam = 1 }) => fetchProducts(pageParam, filters),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.totalPages ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
  });
}

// Usage
function ProductList() {
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteProducts();

  const products = data?.pages.flatMap((page) => page.items) ?? [];

  return (
    <FlashList
      data={products}
      renderItem={({ item }) => <ProductCard product={item} />}
      estimatedItemSize={100}
      onRefresh={refetch}
      refreshing={false}
      onEndReached={() => hasNextPage && fetchNextPage()}
      onEndReachedThreshold={0.5}
      ListFooterComponent={
        isFetchingNextPage ? <ActivityIndicator /> : null
      }
    />
  );
}
```

## Mutation

```typescript
// src/features/products/hooks/useCreateProduct.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { productKeys } from '../queryKeys';
import type { CreateProductInput, Product } from '../types';

async function createProduct(input: CreateProductInput): Promise<Product> {
  const { data } = await api.post('/products', input);
  return data;
}

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: createProduct,
    onSuccess: (newProduct) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });

      // Or optimistically add to cache
      queryClient.setQueryData<Product[]>(
        productKeys.list({}),
        (old) => old ? [...old, newProduct] : [newProduct]
      );
    },
    onError: (error) => {
      console.error('Failed to create product:', error);
    },
  });
}

// Usage
function CreateProductForm() {
  const { mutate, isPending, isError, error } = useCreateProduct();

  const handleSubmit = (values: CreateProductInput) => {
    mutate(values, {
      onSuccess: () => {
        navigation.goBack();
      },
    });
  };

  return (
    <Form onSubmit={handleSubmit}>
      {/* Form fields */}
      <Button
        title={isPending ? 'Creating...' : 'Create'}
        disabled={isPending}
        onPress={handleSubmit}
      />
      {isError && <Text style={styles.error}>{error.message}</Text>}
    </Form>
  );
}
```

## Optimistic Updates

```typescript
// src/features/todos/hooks/useToggleTodo.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { todoKeys } from '../queryKeys';
import type { Todo } from '../types';

export function useToggleTodo() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.patch(`/todos/${id}/toggle`);
      return data;
    },

    // Optimistic update
    onMutate: async (id) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: todoKeys.lists() });

      // Snapshot previous value
      const previousTodos = queryClient.getQueryData<Todo[]>(todoKeys.list({}));

      // Optimistically update
      queryClient.setQueryData<Todo[]>(todoKeys.list({}), (old) =>
        old?.map((todo) =>
          todo.id === id ? { ...todo, completed: !todo.completed } : todo
        )
      );

      // Return context with snapshot
      return { previousTodos };
    },

    // Rollback on error
    onError: (err, id, context) => {
      if (context?.previousTodos) {
        queryClient.setQueryData(todoKeys.list({}), context.previousTodos);
      }
    },

    // Always refetch after error or success
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: todoKeys.lists() });
    },
  });
}
```

## Prefetching

```typescript
// Prefetch on hover/focus
function ProductCard({ product }: { product: Product }) {
  const queryClient = useQueryClient();

  const prefetchDetails = () => {
    queryClient.prefetchQuery({
      queryKey: productKeys.detail(product.id),
      queryFn: () => fetchProduct(product.id),
      staleTime: 1000 * 60 * 5,
    });
  };

  return (
    <Pressable
      onPress={() => navigate('ProductDetail', { id: product.id })}
      onPressIn={prefetchDetails} // Prefetch on touch start
    >
      {/* ... */}
    </Pressable>
  );
}

// Prefetch in screen effect
function ProductListScreen() {
  const queryClient = useQueryClient();

  useFocusEffect(
    useCallback(() => {
      // Prefetch commonly accessed data
      queryClient.prefetchQuery({
        queryKey: productKeys.list({ featured: true }),
        queryFn: () => fetchProducts({ featured: true }),
      });
    }, [queryClient])
  );
}
```

## Dependent Queries

```typescript
// Second query depends on first
function useUserOrders(userId?: string) {
  const userQuery = useUser();

  return useQuery({
    queryKey: ['orders', userId ?? userQuery.data?.id],
    queryFn: () => fetchOrders(userId ?? userQuery.data!.id),
    // Only run when user is available
    enabled: !!(userId || userQuery.data?.id),
  });
}
```

## Parallel Queries

```typescript
// Multiple independent queries
function useDashboard() {
  const results = useQueries({
    queries: [
      {
        queryKey: ['stats'],
        queryFn: fetchStats,
      },
      {
        queryKey: ['recentOrders'],
        queryFn: fetchRecentOrders,
      },
      {
        queryKey: ['notifications'],
        queryFn: fetchNotifications,
      },
    ],
  });

  const [stats, orders, notifications] = results;

  return {
    stats: stats.data,
    orders: orders.data,
    notifications: notifications.data,
    isLoading: results.some((r) => r.isLoading),
  };
}
```

## Placeholder Data

```typescript
// Show cached data while fetching
function useProduct(id: string) {
  const queryClient = useQueryClient();

  return useQuery({
    queryKey: productKeys.detail(id),
    queryFn: () => fetchProduct(id),
    placeholderData: () => {
      // Use data from list cache
      return queryClient
        .getQueryData<Product[]>(productKeys.list({}))
        ?.find((p) => p.id === id);
    },
  });
}
```

## Best Practices

1. **Query Keys**: Use factory functions for consistent keys
2. **Stale Time**: Set appropriate stale times per query type
3. **Error Handling**: Use error boundaries or per-query error handling
4. **Optimistic Updates**: Use for better UX on mutations
5. **Prefetching**: Prefetch likely-needed data
6. **Selectors**: Use select option to transform data
7. **Parallel Queries**: Use useQueries for independent data
