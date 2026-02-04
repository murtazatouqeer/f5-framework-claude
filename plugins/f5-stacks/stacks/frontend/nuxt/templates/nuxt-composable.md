---
name: nuxt-composable
description: Template for Nuxt 3 composables
applies_to: nuxt
---

# Nuxt Composable Template

## Basic Data Composable

```typescript
// composables/use{{RESOURCE}}.ts
interface {{RESOURCE}}Item {
  id: string;
  name: string;
  // Add more fields
}

interface {{RESOURCE}}Response {
  items: {{RESOURCE}}Item[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    totalPages: number;
  };
}

interface Use{{RESOURCE}}Options {
  immediate?: boolean;
  page?: number;
  limit?: number;
}

export function use{{RESOURCE}}(options: Use{{RESOURCE}}Options = {}) {
  const { immediate = true, page = 1, limit = 20 } = options;

  const items = ref<{{RESOURCE}}Item[]>([]);
  const pagination = ref({
    page,
    limit,
    total: 0,
    totalPages: 0,
  });
  const isLoading = ref(false);
  const error = ref<Error | null>(null);

  async function fetch(fetchPage?: number) {
    isLoading.value = true;
    error.value = null;

    try {
      const response = await $fetch<{{RESOURCE}}Response>('/api/{{RESOURCE_LOWER}}', {
        query: {
          page: fetchPage ?? pagination.value.page,
          limit: pagination.value.limit,
        },
      });

      items.value = response.items;
      pagination.value = response.pagination;
    } catch (e) {
      error.value = e as Error;
    } finally {
      isLoading.value = false;
    }
  }

  async function nextPage() {
    if (pagination.value.page < pagination.value.totalPages) {
      pagination.value.page++;
      await fetch();
    }
  }

  async function prevPage() {
    if (pagination.value.page > 1) {
      pagination.value.page--;
      await fetch();
    }
  }

  if (immediate) {
    fetch();
  }

  return {
    items: readonly(items),
    pagination: readonly(pagination),
    isLoading: readonly(isLoading),
    error: readonly(error),
    fetch,
    nextPage,
    prevPage,
  };
}
```

## Single Resource Composable

```typescript
// composables/use{{RESOURCE}}ById.ts
export function use{{RESOURCE}}ById(id: MaybeRef<string>) {
  const resolvedId = computed(() => toValue(id));

  const { data, pending, error, refresh } = useFetch<{{RESOURCE}}Item>(
    () => `/api/{{RESOURCE_LOWER}}/${resolvedId.value}`,
    {
      key: `{{RESOURCE_LOWER}}-${resolvedId.value}`,
      watch: [resolvedId],
    }
  );

  return {
    item: data,
    isLoading: pending,
    error,
    refresh,
  };
}
```

## CRUD Composable

```typescript
// composables/use{{RESOURCE}}Crud.ts
interface Create{{RESOURCE}}Input {
  name: string;
  description?: string;
}

interface Update{{RESOURCE}}Input {
  name?: string;
  description?: string;
}

export function use{{RESOURCE}}Crud() {
  const isCreating = ref(false);
  const isUpdating = ref(false);
  const isDeleting = ref(false);

  async function create(data: Create{{RESOURCE}}Input) {
    isCreating.value = true;
    try {
      const item = await $fetch<{{RESOURCE}}Item>('/api/{{RESOURCE_LOWER}}', {
        method: 'POST',
        body: data,
      });
      return item;
    } finally {
      isCreating.value = false;
    }
  }

  async function update(id: string, data: Update{{RESOURCE}}Input) {
    isUpdating.value = true;
    try {
      const item = await $fetch<{{RESOURCE}}Item>(`/api/{{RESOURCE_LOWER}}/${id}`, {
        method: 'PUT',
        body: data,
      });
      return item;
    } finally {
      isUpdating.value = false;
    }
  }

  async function remove(id: string) {
    isDeleting.value = true;
    try {
      await $fetch(`/api/{{RESOURCE_LOWER}}/${id}`, {
        method: 'DELETE',
      });
    } finally {
      isDeleting.value = false;
    }
  }

  return {
    create,
    update,
    remove,
    isCreating: readonly(isCreating),
    isUpdating: readonly(isUpdating),
    isDeleting: readonly(isDeleting),
  };
}
```

## Form Composable

```typescript
// composables/useForm.ts
import { z } from 'zod';

interface UseFormOptions<T> {
  schema: z.ZodSchema<T>;
  initialValues: T;
  onSubmit: (values: T) => Promise<void>;
}

export function useForm<T extends Record<string, unknown>>(
  options: UseFormOptions<T>
) {
  const { schema, initialValues, onSubmit } = options;

  const values = reactive({ ...initialValues }) as T;
  const errors = ref<Record<string, string>>({});
  const isSubmitting = ref(false);
  const isDirty = ref(false);

  watch(values, () => {
    isDirty.value = true;
  }, { deep: true });

  function validate() {
    errors.value = {};
    const result = schema.safeParse(values);

    if (!result.success) {
      result.error.errors.forEach((err) => {
        const path = err.path.join('.');
        errors.value[path] = err.message;
      });
      return false;
    }

    return true;
  }

  async function submit() {
    if (!validate()) return;

    isSubmitting.value = true;
    try {
      await onSubmit(values);
    } finally {
      isSubmitting.value = false;
    }
  }

  function reset() {
    Object.assign(values, initialValues);
    errors.value = {};
    isDirty.value = false;
  }

  function setFieldError(field: string, message: string) {
    errors.value[field] = message;
  }

  return {
    values,
    errors: readonly(errors),
    isSubmitting: readonly(isSubmitting),
    isDirty: readonly(isDirty),
    validate,
    submit,
    reset,
    setFieldError,
  };
}
```

## State Composable

```typescript
// composables/use{{RESOURCE}}Store.ts
interface {{RESOURCE}}State {
  items: {{RESOURCE}}Item[];
  selectedId: string | null;
  filters: {
    search: string;
    category: string | null;
  };
}

export function use{{RESOURCE}}Store() {
  const state = useState<{{RESOURCE}}State>('{{RESOURCE_LOWER}}-store', () => ({
    items: [],
    selectedId: null,
    filters: {
      search: '',
      category: null,
    },
  }));

  const selected = computed(() =>
    state.value.items.find((item) => item.id === state.value.selectedId)
  );

  const filteredItems = computed(() => {
    let result = state.value.items;

    if (state.value.filters.search) {
      const search = state.value.filters.search.toLowerCase();
      result = result.filter((item) =>
        item.name.toLowerCase().includes(search)
      );
    }

    if (state.value.filters.category) {
      result = result.filter(
        (item) => item.category === state.value.filters.category
      );
    }

    return result;
  });

  function setItems(items: {{RESOURCE}}Item[]) {
    state.value.items = items;
  }

  function selectItem(id: string | null) {
    state.value.selectedId = id;
  }

  function setFilter(key: keyof {{RESOURCE}}State['filters'], value: string | null) {
    state.value.filters[key] = value;
  }

  return {
    state: readonly(state),
    selected,
    filteredItems,
    setItems,
    selectItem,
    setFilter,
  };
}
```

## Utility Composable

```typescript
// composables/useDebounce.ts
export function useDebounce<T>(value: Ref<T>, delay = 300) {
  const debouncedValue = ref(value.value) as Ref<T>;

  let timeout: NodeJS.Timeout;

  watch(value, (newValue) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      debouncedValue.value = newValue;
    }, delay);
  });

  return debouncedValue;
}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{RESOURCE}}` | Resource name (PascalCase) | `Product`, `User` |
| `{{RESOURCE_LOWER}}` | Resource name (lowercase) | `product`, `user` |
