# CRUD App Example

Complete React Native CRUD application demonstrating TanStack Query, Zustand, and best practices.

## Features

- **Full CRUD Operations**: Create, Read, Update, Delete with TanStack Query
- **Optimistic Updates**: Immediate UI feedback with rollback on error
- **Offline Support**: Queue mutations when offline, sync when online
- **Pull to Refresh**: Native refresh control integration
- **Infinite Scroll**: Paginated data loading with FlashList
- **Form Validation**: react-hook-form with Zod schemas
- **State Management**: Zustand for local state, TanStack Query for server state

## Tech Stack

- Expo SDK 50+
- React Native 0.73+
- TypeScript 5.0+
- Expo Router (file-based routing)
- TanStack Query v5
- Zustand v4
- react-hook-form v7
- Zod validation
- FlashList
- NativeWind

## Project Structure

```
crud-app/
├── app/
│   ├── _layout.tsx              # Root layout with providers
│   ├── index.tsx                # Home screen (list)
│   ├── (tabs)/
│   │   ├── _layout.tsx          # Tab navigator
│   │   ├── index.tsx            # Items list tab
│   │   └── settings.tsx         # Settings tab
│   ├── item/
│   │   ├── [id].tsx             # Item detail screen
│   │   └── create.tsx           # Create item screen
│   └── +not-found.tsx           # 404 screen
├── src/
│   ├── components/
│   │   ├── ui/                  # Base UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   └── index.ts
│   │   ├── items/               # Feature components
│   │   │   ├── ItemCard.tsx
│   │   │   ├── ItemForm.tsx
│   │   │   ├── ItemList.tsx
│   │   │   └── index.ts
│   │   └── common/
│   │       ├── ErrorBoundary.tsx
│   │       ├── LoadingSpinner.tsx
│   │       └── EmptyState.tsx
│   ├── features/
│   │   └── items/
│   │       ├── api/
│   │       │   ├── itemService.ts
│   │       │   └── queryKeys.ts
│   │       ├── hooks/
│   │       │   ├── useItems.ts
│   │       │   ├── useItem.ts
│   │       │   ├── useCreateItem.ts
│   │       │   ├── useUpdateItem.ts
│   │       │   └── useDeleteItem.ts
│   │       ├── types/
│   │       │   └── index.ts
│   │       └── index.ts
│   ├── lib/
│   │   ├── api.ts               # Axios client
│   │   ├── queryClient.ts       # TanStack Query setup
│   │   └── storage.ts           # MMKV storage
│   ├── providers/
│   │   ├── QueryProvider.tsx
│   │   └── index.ts
│   ├── stores/
│   │   ├── useAppStore.ts
│   │   └── index.ts
│   └── utils/
│       ├── validation.ts
│       └── formatters.ts
├── __tests__/
│   ├── components/
│   ├── hooks/
│   └── screens/
├── app.json
├── package.json
├── tsconfig.json
└── tailwind.config.js
```

## Key Implementations

### 1. API Service

```typescript
// src/features/items/api/itemService.ts
import { api } from '@/lib/api';
import type { Item, CreateItemInput, UpdateItemInput, ItemFilters, PaginatedItems } from '../types';

const ENDPOINT = '/items';

export const itemService = {
  getAll: async (filters?: ItemFilters): Promise<PaginatedItems> => {
    const { data } = await api.get(ENDPOINT, { params: filters });
    return data;
  },

  getById: async (id: string): Promise<Item> => {
    const { data } = await api.get(`${ENDPOINT}/${id}`);
    return data;
  },

  create: async (input: CreateItemInput): Promise<Item> => {
    const { data } = await api.post(ENDPOINT, input);
    return data;
  },

  update: async (id: string, input: UpdateItemInput): Promise<Item> => {
    const { data } = await api.patch(`${ENDPOINT}/${id}`, input);
    return data;
  },

  delete: async (id: string): Promise<void> => {
    await api.delete(`${ENDPOINT}/${id}`);
  },
};
```

### 2. Query Keys Factory

```typescript
// src/features/items/api/queryKeys.ts
import type { ItemFilters } from '../types';

export const itemKeys = {
  all: ['items'] as const,
  lists: () => [...itemKeys.all, 'list'] as const,
  list: (filters?: ItemFilters) => [...itemKeys.lists(), filters] as const,
  details: () => [...itemKeys.all, 'detail'] as const,
  detail: (id: string) => [...itemKeys.details(), id] as const,
};
```

### 3. TanStack Query Hooks

```typescript
// src/features/items/hooks/useItems.ts
import { useInfiniteQuery } from '@tanstack/react-query';
import { itemService } from '../api/itemService';
import { itemKeys } from '../api/queryKeys';
import type { ItemFilters } from '../types';

export function useItems(filters?: Omit<ItemFilters, 'page'>) {
  return useInfiniteQuery({
    queryKey: itemKeys.list(filters),
    queryFn: ({ pageParam = 1 }) =>
      itemService.getAll({ ...filters, page: pageParam }),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.totalPages ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
  });
}
```

### 4. Optimistic Update Mutation

```typescript
// src/features/items/hooks/useUpdateItem.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { itemService } from '../api/itemService';
import { itemKeys } from '../api/queryKeys';
import type { Item, UpdateItemInput } from '../types';

export function useUpdateItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UpdateItemInput }) =>
      itemService.update(id, data),

    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: itemKeys.detail(id) });

      const previousItem = queryClient.getQueryData<Item>(itemKeys.detail(id));

      queryClient.setQueryData<Item>(itemKeys.detail(id), (old) =>
        old ? { ...old, ...data } : old
      );

      return { previousItem };
    },

    onError: (_, { id }, context) => {
      if (context?.previousItem) {
        queryClient.setQueryData(itemKeys.detail(id), context.previousItem);
      }
    },

    onSettled: (_, __, { id }) => {
      queryClient.invalidateQueries({ queryKey: itemKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: itemKeys.lists() });
    },
  });
}
```

### 5. Item List Screen

```typescript
// app/(tabs)/index.tsx
import { View } from 'react-native';
import { FlashList } from '@shopify/flash-list';
import { useItems } from '@/features/items/hooks/useItems';
import { ItemCard } from '@/components/items/ItemCard';
import { LoadingSpinner, EmptyState } from '@/components/common';

export default function ItemsScreen() {
  const {
    data,
    isLoading,
    isError,
    error,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    refetch,
    isRefetching,
  } = useItems();

  const items = data?.pages.flatMap((page) => page.items) ?? [];

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (isError) {
    return <ErrorState message={error.message} onRetry={refetch} />;
  }

  return (
    <View className="flex-1 bg-white">
      <FlashList
        data={items}
        renderItem={({ item }) => <ItemCard item={item} />}
        estimatedItemSize={120}
        keyExtractor={(item) => item.id}
        onEndReached={() => hasNextPage && fetchNextPage()}
        onEndReachedThreshold={0.5}
        refreshing={isRefetching}
        onRefresh={refetch}
        ListEmptyComponent={<EmptyState message="No items found" />}
        ListFooterComponent={
          isFetchingNextPage ? <LoadingSpinner size="small" /> : null
        }
      />
    </View>
  );
}
```

### 6. Create Item Form

```typescript
// app/item/create.tsx
import { View, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { useRouter } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useCreateItem } from '@/features/items/hooks/useCreateItem';
import { Button, Input } from '@/components/ui';

const createItemSchema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().min(10, 'Description must be at least 10 characters'),
  price: z.number().min(0, 'Price must be positive'),
  category: z.string().min(1, 'Category is required'),
});

type CreateItemForm = z.infer<typeof createItemSchema>;

export default function CreateItemScreen() {
  const router = useRouter();
  const { mutate: createItem, isPending } = useCreateItem();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<CreateItemForm>({
    resolver: zodResolver(createItemSchema),
    defaultValues: {
      name: '',
      description: '',
      price: 0,
      category: '',
    },
  });

  const onSubmit = (data: CreateItemForm) => {
    createItem(data, {
      onSuccess: (newItem) => {
        router.replace(`/item/${newItem.id}`);
      },
    });
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1"
    >
      <ScrollView className="flex-1 p-4">
        <Controller
          control={control}
          name="name"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Name"
              placeholder="Enter item name"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.name?.message}
            />
          )}
        />

        <Controller
          control={control}
          name="description"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Description"
              placeholder="Enter description"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              multiline
              numberOfLines={4}
              error={errors.description?.message}
            />
          )}
        />

        <Controller
          control={control}
          name="price"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Price"
              placeholder="0.00"
              value={value.toString()}
              onChangeText={(text) => onChange(parseFloat(text) || 0)}
              onBlur={onBlur}
              keyboardType="decimal-pad"
              error={errors.price?.message}
            />
          )}
        />

        <Controller
          control={control}
          name="category"
          render={({ field: { onChange, onBlur, value } }) => (
            <Input
              label="Category"
              placeholder="Select category"
              value={value}
              onChangeText={onChange}
              onBlur={onBlur}
              error={errors.category?.message}
            />
          )}
        />

        <Button
          title={isPending ? 'Creating...' : 'Create Item'}
          onPress={handleSubmit(onSubmit)}
          disabled={isPending}
          className="mt-6"
        />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
```

## Getting Started

### Prerequisites

- Node.js 18+
- Expo CLI
- iOS Simulator or Android Emulator

### Installation

```bash
# Install dependencies
npm install

# Start development server
npx expo start

# Run on iOS
npx expo run:ios

# Run on Android
npx expo run:android
```

### Environment Setup

Create `.env` file:

```env
EXPO_PUBLIC_API_URL=https://api.example.com
```

## Testing

```bash
# Run unit tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run E2E tests
npm run test:e2e
```

## Best Practices Demonstrated

1. **Separation of Concerns**: Feature-based architecture with clear boundaries
2. **Type Safety**: Full TypeScript with Zod validation
3. **Server State Management**: TanStack Query for caching and synchronization
4. **Optimistic Updates**: Immediate UI feedback with proper rollback
5. **Error Handling**: Comprehensive error boundaries and user feedback
6. **Performance**: FlashList for efficient list rendering
7. **Accessibility**: Proper labels and screen reader support
8. **Testing**: Unit tests for hooks, components, and integration tests

## Related Templates

- [rn-api.md](../../templates/rn-api.md) - API service patterns
- [rn-hook.md](../../templates/rn-hook.md) - Query hooks patterns
- [rn-screen.md](../../templates/rn-screen.md) - Screen templates
- [rn-component.md](../../templates/rn-component.md) - Component patterns
