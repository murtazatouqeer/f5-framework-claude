---
name: rn-hook
description: React Native custom hook templates
applies_to: react-native
variables:
  - name: hookName
    description: Name of the hook (e.g., useProducts)
  - name: resourceName
    description: Name of the resource (e.g., Product)
---

# React Native Hook Templates

## Query Hook

```typescript
// src/features/{{feature}}/hooks/use{{resourceName}}.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { {{resourceName}} } from '../types';

async function fetch{{resourceName}}(id: string): Promise<{{resourceName}}> {
  const { data } = await api.get(`/{{kebabCase resourceName}}s/${id}`);
  return data;
}

export function use{{resourceName}}(id: string) {
  return useQuery({
    queryKey: ['{{camelCase resourceName}}', id],
    queryFn: () => fetch{{resourceName}}(id),
    enabled: !!id,
  });
}
```

## List Query Hook

```typescript
// src/features/{{feature}}/hooks/use{{resourceName}}s.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { {{resourceName}}, {{resourceName}}Filters } from '../types';

interface {{resourceName}}sResponse {
  items: {{resourceName}}[];
  total: number;
}

async function fetch{{resourceName}}s(
  filters?: {{resourceName}}Filters
): Promise<{{resourceName}}sResponse> {
  const { data } = await api.get('/{{kebabCase resourceName}}s', { params: filters });
  return data;
}

export function use{{resourceName}}s(filters?: {{resourceName}}Filters) {
  return useQuery({
    queryKey: ['{{camelCase resourceName}}s', filters],
    queryFn: () => fetch{{resourceName}}s(filters),
  });
}
```

## Infinite Query Hook

```typescript
// src/features/{{feature}}/hooks/useInfinite{{resourceName}}s.ts
import { useInfiniteQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { {{resourceName}}, {{resourceName}}Filters } from '../types';

interface {{resourceName}}sPage {
  items: {{resourceName}}[];
  page: number;
  totalPages: number;
  total: number;
}

async function fetch{{resourceName}}sPage(
  page: number,
  filters?: {{resourceName}}Filters
): Promise<{{resourceName}}sPage> {
  const { data } = await api.get('/{{kebabCase resourceName}}s', {
    params: { page, limit: 20, ...filters },
  });
  return data;
}

export function useInfinite{{resourceName}}s(filters?: {{resourceName}}Filters) {
  return useInfiniteQuery({
    queryKey: ['{{camelCase resourceName}}s', 'infinite', filters],
    queryFn: ({ pageParam = 1 }) => fetch{{resourceName}}sPage(pageParam, filters),
    getNextPageParam: (lastPage) =>
      lastPage.page < lastPage.totalPages ? lastPage.page + 1 : undefined,
    initialPageParam: 1,
  });
}
```

## Mutation Hook

```typescript
// src/features/{{feature}}/hooks/useCreate{{resourceName}}.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { {{resourceName}}, Create{{resourceName}}Input } from '../types';

async function create{{resourceName}}(
  input: Create{{resourceName}}Input
): Promise<{{resourceName}}> {
  const { data } = await api.post('/{{kebabCase resourceName}}s', input);
  return data;
}

export function useCreate{{resourceName}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: create{{resourceName}},
    onSuccess: (new{{resourceName}}) => {
      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['{{camelCase resourceName}}s'] });

      // Optionally add to cache
      queryClient.setQueryData(
        ['{{camelCase resourceName}}', new{{resourceName}}.id],
        new{{resourceName}}
      );
    },
  });
}
```

## Update Mutation Hook

```typescript
// src/features/{{feature}}/hooks/useUpdate{{resourceName}}.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import type { {{resourceName}}, Update{{resourceName}}Input } from '../types';

interface Update{{resourceName}}Variables {
  id: string;
  data: Update{{resourceName}}Input;
}

async function update{{resourceName}}({
  id,
  data,
}: Update{{resourceName}}Variables): Promise<{{resourceName}}> {
  const { data: response } = await api.patch(`/{{kebabCase resourceName}}s/${id}`, data);
  return response;
}

export function useUpdate{{resourceName}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: update{{resourceName}},
    onSuccess: (updated{{resourceName}}) => {
      // Update single item cache
      queryClient.setQueryData(
        ['{{camelCase resourceName}}', updated{{resourceName}}.id],
        updated{{resourceName}}
      );

      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['{{camelCase resourceName}}s'] });
    },
  });
}
```

## Delete Mutation Hook

```typescript
// src/features/{{feature}}/hooks/useDelete{{resourceName}}.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';

async function delete{{resourceName}}(id: string): Promise<void> {
  await api.delete(`/{{kebabCase resourceName}}s/${id}`);
}

export function useDelete{{resourceName}}() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: delete{{resourceName}},
    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: ['{{camelCase resourceName}}', id] });

      // Invalidate list queries
      queryClient.invalidateQueries({ queryKey: ['{{camelCase resourceName}}s'] });
    },
  });
}
```

## Debounced Value Hook

```typescript
// src/hooks/useDebounce.ts
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number = 500): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

## Boolean Toggle Hook

```typescript
// src/hooks/useToggle.ts
import { useState, useCallback } from 'react';

export function useToggle(
  initialValue: boolean = false
): [boolean, () => void, (value: boolean) => void] {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => {
    setValue((prev) => !prev);
  }, []);

  return [value, toggle, setValue];
}
```

## Modal Control Hook

```typescript
// src/hooks/useModal.ts
import { useState, useCallback } from 'react';

interface UseModalReturn<T = undefined> {
  isOpen: boolean;
  data: T | undefined;
  open: (data?: T) => void;
  close: () => void;
}

export function useModal<T = undefined>(): UseModalReturn<T> {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<T | undefined>();

  const open = useCallback((newData?: T) => {
    setData(newData);
    setIsOpen(true);
  }, []);

  const close = useCallback(() => {
    setIsOpen(false);
    // Clear data after animation
    setTimeout(() => setData(undefined), 300);
  }, []);

  return { isOpen, data, open, close };
}
```

## Previous Value Hook

```typescript
// src/hooks/usePrevious.ts
import { useRef, useEffect } from 'react';

export function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();

  useEffect(() => {
    ref.current = value;
  }, [value]);

  return ref.current;
}
```

## Mounted Ref Hook

```typescript
// src/hooks/useIsMounted.ts
import { useRef, useEffect, useCallback } from 'react';

export function useIsMounted() {
  const isMountedRef = useRef(false);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  return useCallback(() => isMountedRef.current, []);
}

// Usage
function MyComponent() {
  const isMounted = useIsMounted();

  useEffect(() => {
    fetchData().then((data) => {
      if (isMounted()) {
        setData(data);
      }
    });
  }, []);
}
```

## Usage

1. Replace `{{resourceName}}` with resource name (e.g., `Product`)
2. Replace `{{feature}}` with feature folder name
3. Create corresponding types file
4. Export from hooks/index.ts
