# TanStack Query (React Query)

## Overview

Powerful data fetching and server state management library for React.

## Setup

```tsx
// app/providers.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 30, // 30 minutes (formerly cacheTime)
      retry: 3,
      refetchOnWindowFocus: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

export function QueryProvider({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

## Basic Queries

```tsx
import { useQuery } from '@tanstack/react-query';

interface User {
  id: string;
  name: string;
  email: string;
}

// Basic query
function UserProfile({ userId }: { userId: string }) {
  const {
    data: user,
    isLoading,
    isError,
    error,
    refetch,
    isFetching,
  } = useQuery<User, Error>({
    queryKey: ['user', userId],
    queryFn: async () => {
      const response = await fetch(`/api/users/${userId}`);
      if (!response.ok) throw new Error('Failed to fetch user');
      return response.json();
    },
    enabled: !!userId, // Only fetch if userId exists
  });

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorMessage error={error} onRetry={refetch} />;

  return (
    <div className={isFetching ? 'opacity-50' : ''}>
      <h1>{user?.name}</h1>
      <p>{user?.email}</p>
    </div>
  );
}
```

## Query with Parameters

```tsx
interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
}

interface ProductFilters {
  category?: string;
  minPrice?: number;
  maxPrice?: number;
  search?: string;
}

function useProducts(filters: ProductFilters) {
  return useQuery<Product[]>({
    queryKey: ['products', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.category) params.set('category', filters.category);
      if (filters.minPrice) params.set('minPrice', String(filters.minPrice));
      if (filters.maxPrice) params.set('maxPrice', String(filters.maxPrice));
      if (filters.search) params.set('search', filters.search);

      const response = await fetch(`/api/products?${params}`);
      if (!response.ok) throw new Error('Failed to fetch products');
      return response.json();
    },
    placeholderData: (previousData) => previousData, // Keep previous data while fetching
  });
}
```

## Mutations

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface CreateProductInput {
  name: string;
  price: number;
  category: string;
}

function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation<Product, Error, CreateProductInput>({
    mutationFn: async (newProduct) => {
      const response = await fetch('/api/products', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newProduct),
      });
      if (!response.ok) throw new Error('Failed to create product');
      return response.json();
    },
    onSuccess: (data) => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['products'] });
      // Or update cache directly
      queryClient.setQueryData<Product[]>(['products'], (old) =>
        old ? [...old, data] : [data]
      );
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });
}

// Usage
function ProductForm() {
  const createProduct = useCreateProduct();

  const handleSubmit = async (data: CreateProductInput) => {
    try {
      await createProduct.mutateAsync(data);
      toast.success('Product created!');
    } catch (error) {
      // Error handled in mutation
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* form fields */}
      <button type="submit" disabled={createProduct.isPending}>
        {createProduct.isPending ? 'Creating...' : 'Create Product'}
      </button>
    </form>
  );
}
```

## Optimistic Updates

```tsx
function useUpdateProduct() {
  const queryClient = useQueryClient();

  return useMutation<Product, Error, { id: string; data: Partial<Product> }>({
    mutationFn: async ({ id, data }) => {
      const response = await fetch(`/api/products/${id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error('Failed to update product');
      return response.json();
    },
    onMutate: async ({ id, data }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['product', id] });

      // Snapshot previous value
      const previousProduct = queryClient.getQueryData<Product>(['product', id]);

      // Optimistically update
      queryClient.setQueryData<Product>(['product', id], (old) =>
        old ? { ...old, ...data } : undefined
      );

      // Return context for rollback
      return { previousProduct };
    },
    onError: (err, variables, context) => {
      // Rollback on error
      if (context?.previousProduct) {
        queryClient.setQueryData(
          ['product', variables.id],
          context.previousProduct
        );
      }
    },
    onSettled: (data, error, variables) => {
      // Refetch after error or success
      queryClient.invalidateQueries({ queryKey: ['product', variables.id] });
    },
  });
}
```

## Infinite Queries

```tsx
import { useInfiniteQuery } from '@tanstack/react-query';

interface ProductsPage {
  products: Product[];
  nextCursor: string | null;
  hasMore: boolean;
}

function useInfiniteProducts() {
  return useInfiniteQuery<ProductsPage, Error>({
    queryKey: ['products', 'infinite'],
    queryFn: async ({ pageParam }) => {
      const url = pageParam
        ? `/api/products?cursor=${pageParam}`
        : '/api/products';
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch products');
      return response.json();
    },
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) =>
      lastPage.hasMore ? lastPage.nextCursor : undefined,
  });
}

function InfiniteProductList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteProducts();

  const products = data?.pages.flatMap((page) => page.products) ?? [];

  return (
    <div>
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}

      {hasNextPage && (
        <button
          onClick={() => fetchNextPage()}
          disabled={isFetchingNextPage}
        >
          {isFetchingNextPage ? 'Loading...' : 'Load More'}
        </button>
      )}
    </div>
  );
}
```

## Prefetching

```tsx
import { useQueryClient } from '@tanstack/react-query';

function ProductListItem({ product }: { product: Product }) {
  const queryClient = useQueryClient();

  // Prefetch on hover
  const handleMouseEnter = () => {
    queryClient.prefetchQuery({
      queryKey: ['product', product.id],
      queryFn: () => fetchProduct(product.id),
      staleTime: 1000 * 60 * 5,
    });
  };

  return (
    <Link
      to={`/products/${product.id}`}
      onMouseEnter={handleMouseEnter}
    >
      {product.name}
    </Link>
  );
}
```

## Custom Hook Pattern

```tsx
// hooks/useProducts.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { productApi } from '@/lib/api';

export const productKeys = {
  all: ['products'] as const,
  lists: () => [...productKeys.all, 'list'] as const,
  list: (filters: ProductFilters) => [...productKeys.lists(), filters] as const,
  details: () => [...productKeys.all, 'detail'] as const,
  detail: (id: string) => [...productKeys.details(), id] as const,
};

export function useProducts(filters: ProductFilters = {}) {
  return useQuery({
    queryKey: productKeys.list(filters),
    queryFn: () => productApi.getAll(filters),
  });
}

export function useProduct(id: string) {
  return useQuery({
    queryKey: productKeys.detail(id),
    queryFn: () => productApi.getById(id),
    enabled: !!id,
  });
}

export function useCreateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: productApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Product> }) =>
      productApi.update(id, data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: productKeys.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
    },
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: productApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productKeys.lists() });
    },
  });
}
```

## Suspense Mode

```tsx
import { useSuspenseQuery } from '@tanstack/react-query';
import { Suspense } from 'react';

function ProductDetails({ id }: { id: string }) {
  const { data: product } = useSuspenseQuery({
    queryKey: ['product', id],
    queryFn: () => fetchProduct(id),
  });

  // No loading check needed - Suspense handles it
  return <div>{product.name}</div>;
}

function ProductPage({ id }: { id: string }) {
  return (
    <Suspense fallback={<ProductSkeleton />}>
      <ProductDetails id={id} />
    </Suspense>
  );
}
```

## Best Practices

1. **Use query keys factories** - Consistent, type-safe key management
2. **Create custom hooks** - Encapsulate query logic
3. **Configure defaults** - Set sensible staleTime and gcTime
4. **Use optimistic updates** - Better UX for mutations
5. **Prefetch data** - Improve perceived performance
6. **Handle loading/error states** - Consistent UX patterns
7. **Use Suspense** - Cleaner component code
