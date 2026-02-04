---
name: rn-api
description: API service and types templates for React Native
applies_to: react-native
variables:
  - name: resourceName
    description: Name of the resource (e.g., Product, User)
---

# API Service Templates

## Types Definition

```typescript
// src/features/{{feature}}/types/index.ts

// Base entity
export interface {{resourceName}} {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
}

// Create input (omit auto-generated fields)
export type Create{{resourceName}}Input = Omit<
  {{resourceName}},
  'id' | 'createdAt' | 'updatedAt'
>;

// Update input (all fields optional)
export type Update{{resourceName}}Input = Partial<Create{{resourceName}}Input>;

// List filters
export interface {{resourceName}}Filters {
  search?: string;
  category?: string;
  status?: string;
  sortBy?: 'createdAt' | 'name' | 'price';
  sortOrder?: 'asc' | 'desc';
  page?: number;
  limit?: number;
}

// Paginated response
export interface Paginated{{resourceName}}s {
  items: {{resourceName}}[];
  total: number;
  page: number;
  limit: number;
  totalPages: number;
}
```

## API Service

```typescript
// src/features/{{feature}}/api/{{camelCase resourceName}}Service.ts
import { api } from '@/lib/api';
import type {
  {{resourceName}},
  Create{{resourceName}}Input,
  Update{{resourceName}}Input,
  {{resourceName}}Filters,
  Paginated{{resourceName}}s,
} from '../types';

const ENDPOINT = '/{{kebabCase resourceName}}s';

export const {{camelCase resourceName}}Service = {
  // Get all (paginated)
  getAll: async (filters?: {{resourceName}}Filters): Promise<Paginated{{resourceName}}s> => {
    const { data } = await api.get(ENDPOINT, { params: filters });
    return data;
  },

  // Get by ID
  getById: async (id: string): Promise<{{resourceName}}> => {
    const { data } = await api.get(`${ENDPOINT}/${id}`);
    return data;
  },

  // Create
  create: async (input: Create{{resourceName}}Input): Promise<{{resourceName}}> => {
    const { data } = await api.post(ENDPOINT, input);
    return data;
  },

  // Update
  update: async (
    id: string,
    input: Update{{resourceName}}Input
  ): Promise<{{resourceName}}> => {
    const { data } = await api.patch(`${ENDPOINT}/${id}`, input);
    return data;
  },

  // Delete
  delete: async (id: string): Promise<void> => {
    await api.delete(`${ENDPOINT}/${id}`);
  },

  // Bulk operations
  bulkDelete: async (ids: string[]): Promise<void> => {
    await api.post(`${ENDPOINT}/bulk-delete`, { ids });
  },
};
```

## Query Keys Factory

```typescript
// src/features/{{feature}}/api/queryKeys.ts
import type { {{resourceName}}Filters } from '../types';

export const {{camelCase resourceName}}Keys = {
  all: ['{{camelCase resourceName}}s'] as const,
  lists: () => [...{{camelCase resourceName}}Keys.all, 'list'] as const,
  list: (filters?: {{resourceName}}Filters) =>
    [...{{camelCase resourceName}}Keys.lists(), filters] as const,
  details: () => [...{{camelCase resourceName}}Keys.all, 'detail'] as const,
  detail: (id: string) => [...{{camelCase resourceName}}Keys.details(), id] as const,
};
```

## React Query Hooks

```typescript
// src/features/{{feature}}/hooks/use{{resourceName}}s.ts
import { useQuery, useMutation, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';
import { {{camelCase resourceName}}Service } from '../api/{{camelCase resourceName}}Service';
import { {{camelCase resourceName}}Keys } from '../api/queryKeys';
import type {
  {{resourceName}},
  {{resourceName}}Filters,
  Create{{resourceName}}Input,
  Update{{resourceName}}Input,
} from '../types';

// List query
export function use{{resourceName}}s(filters?: {{resourceName}}Filters) {
  return useQuery({
    queryKey: {{camelCase resourceName}}Keys.list(filters),
    queryFn: () => {{camelCase resourceName}}Service.getAll(filters),
  });
}

// Infinite list query
export function useInfinite{{resourceName}}s(filters?: Omit<{{resourceName}}Filters, 'page'>) {
  return useInfiniteQuery({
    queryKey: {{camelCase resourceName}}Keys.list(filters),
    queryFn: ({ pageParam = 1 }) =>
      {{camelCase resourceName}}Service.getAll({ ...filters, page: pageParam }),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.totalPages ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
  });
}

// Detail query
export function use{{resourceName}}(id: string) {
  return useQuery({
    queryKey: {{camelCase resourceName}}Keys.detail(id),
    queryFn: () => {{camelCase resourceName}}Service.getById(id),
    enabled: !!id,
  });
}

// Create mutation
export function useCreate{{resourceName}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Create{{resourceName}}Input) =>
      {{camelCase resourceName}}Service.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: {{camelCase resourceName}}Keys.lists() });
    },
  });
}

// Update mutation
export function useUpdate{{resourceName}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Update{{resourceName}}Input }) =>
      {{camelCase resourceName}}Service.update(id, data),
    onSuccess: (updated{{resourceName}}) => {
      queryClient.setQueryData(
        {{camelCase resourceName}}Keys.detail(updated{{resourceName}}.id),
        updated{{resourceName}}
      );
      queryClient.invalidateQueries({ queryKey: {{camelCase resourceName}}Keys.lists() });
    },
  });
}

// Delete mutation
export function useDelete{{resourceName}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => {{camelCase resourceName}}Service.delete(id),
    onSuccess: (_, id) => {
      queryClient.removeQueries({ queryKey: {{camelCase resourceName}}Keys.detail(id) });
      queryClient.invalidateQueries({ queryKey: {{camelCase resourceName}}Keys.lists() });
    },
  });
}
```

## Optimistic Update Example

```typescript
// src/features/{{feature}}/hooks/useToggle{{resourceName}}.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { {{camelCase resourceName}}Service } from '../api/{{camelCase resourceName}}Service';
import { {{camelCase resourceName}}Keys } from '../api/queryKeys';
import type { {{resourceName}} } from '../types';

export function useToggle{{resourceName}}Status() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => {{camelCase resourceName}}Service.toggleStatus(id),

    // Optimistic update
    onMutate: async (id) => {
      await queryClient.cancelQueries({ queryKey: {{camelCase resourceName}}Keys.lists() });

      const previousItems = queryClient.getQueryData<{ items: {{resourceName}}[] }>(
        {{camelCase resourceName}}Keys.list()
      );

      queryClient.setQueryData<{ items: {{resourceName}}[] }>(
        {{camelCase resourceName}}Keys.list(),
        (old) => ({
          ...old!,
          items: old!.items.map((item) =>
            item.id === id
              ? { ...item, isActive: !item.isActive }
              : item
          ),
        })
      );

      return { previousItems };
    },

    // Rollback on error
    onError: (_, __, context) => {
      if (context?.previousItems) {
        queryClient.setQueryData(
          {{camelCase resourceName}}Keys.list(),
          context.previousItems
        );
      }
    },

    // Always refetch
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: {{camelCase resourceName}}Keys.lists() });
    },
  });
}
```

## File Upload Service

```typescript
// src/features/{{feature}}/api/uploadService.ts
import { api } from '@/lib/api';
import * as FileSystem from 'expo-file-system';

interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

interface UploadResult {
  url: string;
  key: string;
}

export const uploadService = {
  uploadImage: async (
    uri: string,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<UploadResult> => {
    const formData = new FormData();

    const filename = uri.split('/').pop() ?? 'image.jpg';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1]}` : 'image/jpeg';

    formData.append('file', {
      uri,
      name: filename,
      type,
    } as any);

    const { data } = await api.post<UploadResult>('/upload/image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (onProgress && event.total) {
          onProgress({
            loaded: event.loaded,
            total: event.total,
            percentage: Math.round((event.loaded * 100) / event.total),
          });
        }
      },
    });

    return data;
  },

  uploadMultiple: async (
    uris: string[],
    onProgress?: (index: number, progress: UploadProgress) => void
  ): Promise<UploadResult[]> => {
    const results: UploadResult[] = [];

    for (let i = 0; i < uris.length; i++) {
      const result = await uploadService.uploadImage(uris[i], (progress) => {
        onProgress?.(i, progress);
      });
      results.push(result);
    }

    return results;
  },
};
```

## Usage

1. Replace `{{resourceName}}` with resource name (e.g., `Product`)
2. Replace `{{feature}}` with feature folder name
3. Adjust types to match your API response
4. Add custom endpoints as needed
5. Export from feature's index.ts
