---
name: vue-slots
description: Vue slot patterns for component composition
applies_to: vue
---

# Vue Slots

## Overview

Slots allow parent components to inject content into child components,
enabling flexible and composable UI patterns.

## Default Slot

### Basic Usage

```vue
<!-- Child: Card.vue -->
<template>
  <div class="card">
    <slot>
      <!-- Fallback content when slot is empty -->
      <p>No content provided</p>
    </slot>
  </div>
</template>
```

```vue
<!-- Parent usage -->
<Card>
  <p>This content goes into the default slot</p>
</Card>

<!-- With fallback -->
<Card />
<!-- Renders: <div class="card"><p>No content provided</p></div> -->
```

### Checking for Slot Content

```vue
<script setup lang="ts">
import { useSlots } from 'vue';

const slots = useSlots();

// Check if slot has content
const hasDefaultSlot = !!slots.default;
</script>

<template>
  <div class="card">
    <!-- Using $slots in template -->
    <div v-if="$slots.default" class="card-body">
      <slot />
    </div>
    <p v-else class="empty-state">No content</p>
  </div>
</template>
```

## Named Slots

### Basic Named Slots

```vue
<!-- Child: PageLayout.vue -->
<template>
  <div class="page">
    <header class="page-header">
      <slot name="header">
        <h1>Default Header</h1>
      </slot>
    </header>

    <main class="page-content">
      <slot>
        <!-- Default slot -->
      </slot>
    </main>

    <aside v-if="$slots.sidebar" class="page-sidebar">
      <slot name="sidebar" />
    </aside>

    <footer class="page-footer">
      <slot name="footer" />
    </footer>
  </div>
</template>
```

```vue
<!-- Parent usage -->
<PageLayout>
  <template #header>
    <h1>My Page Title</h1>
  </template>

  <!-- Default slot content -->
  <p>Main content here</p>

  <template #sidebar>
    <nav>Sidebar navigation</nav>
  </template>

  <template #footer>
    <p>Footer content</p>
  </template>
</PageLayout>
```

### Dynamic Slot Names

```vue
<script setup lang="ts">
import { ref } from 'vue';

const currentSlot = ref('header');
</script>

<template>
  <BaseLayout>
    <template #[currentSlot]>
      Dynamic slot content
    </template>
  </BaseLayout>
</template>
```

## Scoped Slots

### Basic Scoped Slot

```vue
<!-- Child: List.vue -->
<script setup lang="ts">
interface Props {
  items: { id: string; name: string }[];
}

defineProps<Props>();
</script>

<template>
  <ul>
    <li v-for="(item, index) in items" :key="item.id">
      <slot :item="item" :index="index">
        <!-- Fallback: just show name -->
        {{ item.name }}
      </slot>
    </li>
  </ul>
</template>
```

```vue
<!-- Parent usage -->
<script setup lang="ts">
const items = [
  { id: '1', name: 'Apple' },
  { id: '2', name: 'Banana' },
];
</script>

<template>
  <List :items="items">
    <template #default="{ item, index }">
      <span class="index">{{ index + 1 }}.</span>
      <span class="name">{{ item.name }}</span>
    </template>
  </List>
</template>
```

### Named Scoped Slots

```vue
<!-- Child: DataTable.vue -->
<script setup lang="ts">
import type { Column, Row } from './types';

interface Props {
  columns: Column[];
  rows: Row[];
}

defineProps<Props>();
</script>

<template>
  <table>
    <thead>
      <tr>
        <th v-for="column in columns" :key="column.key">
          <slot :name="`header-${column.key}`" :column="column">
            {{ column.label }}
          </slot>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="row in rows" :key="row.id">
        <td v-for="column in columns" :key="column.key">
          <slot :name="`cell-${column.key}`" :row="row" :column="column">
            {{ row[column.key] }}
          </slot>
        </td>
      </tr>
    </tbody>
  </table>
</template>
```

```vue
<!-- Parent usage -->
<DataTable :columns="columns" :rows="users">
  <!-- Custom header -->
  <template #header-name="{ column }">
    <strong>{{ column.label }}</strong>
    <SortIcon />
  </template>

  <!-- Custom cell -->
  <template #cell-name="{ row }">
    <div class="user-cell">
      <Avatar :src="row.avatar" />
      <span>{{ row.name }}</span>
    </div>
  </template>

  <!-- Custom actions cell -->
  <template #cell-actions="{ row }">
    <Button @click="edit(row)">Edit</Button>
    <Button @click="remove(row)">Delete</Button>
  </template>
</DataTable>
```

### Typed Scoped Slots

```vue
<!-- Child with typed slot props -->
<script setup lang="ts">
interface Item {
  id: string;
  name: string;
  price: number;
}

interface Props {
  items: Item[];
}

// Define slot types using defineSlots (Vue 3.3+)
defineSlots<{
  default(props: { item: Item; index: number }): any;
  header(): any;
  footer(props: { total: number }): any;
}>();

defineProps<Props>();
</script>
```

## Renderless Components

### Pattern for Logic-Only Components

```vue
<!-- MouseTracker.vue -->
<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

const x = ref(0);
const y = ref(0);

function update(event: MouseEvent) {
  x.value = event.pageX;
  y.value = event.pageY;
}

onMounted(() => window.addEventListener('mousemove', update));
onUnmounted(() => window.removeEventListener('mousemove', update));
</script>

<template>
  <slot :x="x" :y="y" />
</template>
```

```vue
<!-- Usage -->
<MouseTracker v-slot="{ x, y }">
  <div class="cursor-position">
    Cursor: {{ x }}, {{ y }}
  </div>
</MouseTracker>
```

### Fetch Component

```vue
<!-- FetchData.vue -->
<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';

interface Props {
  url: string;
  immediate?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  immediate: true,
});

const data = ref<unknown>(null);
const error = ref<Error | null>(null);
const isLoading = ref(false);

async function fetchData() {
  isLoading.value = true;
  error.value = null;

  try {
    const response = await fetch(props.url);
    if (!response.ok) throw new Error('Fetch failed');
    data.value = await response.json();
  } catch (e) {
    error.value = e instanceof Error ? e : new Error('Unknown error');
  } finally {
    isLoading.value = false;
  }
}

if (props.immediate) {
  onMounted(fetchData);
}

watch(() => props.url, fetchData);
</script>

<template>
  <slot
    :data="data"
    :error="error"
    :isLoading="isLoading"
    :refetch="fetchData"
  />
</template>
```

```vue
<!-- Usage -->
<FetchData url="/api/users" v-slot="{ data, error, isLoading, refetch }">
  <div v-if="isLoading">Loading...</div>
  <div v-else-if="error">Error: {{ error.message }}</div>
  <div v-else>
    <UserList :users="data" />
    <button @click="refetch">Refresh</button>
  </div>
</FetchData>
```

## Slot Shorthand

```vue
<!-- Full syntax -->
<template v-slot:header>Header</template>
<template v-slot:default="{ item }">{{ item }}</template>

<!-- Shorthand # -->
<template #header>Header</template>
<template #default="{ item }">{{ item }}</template>

<!-- Default slot shorthand -->
<List :items="items" v-slot="{ item }">
  {{ item }}
</List>
```

## Best Practices

1. **Provide fallback content** - Default content for empty slots
2. **Check slot existence** - Conditionally render wrappers
3. **Type scoped slots** - Use defineSlots for type safety
4. **Use semantic names** - header, footer, content, actions
5. **Document slot props** - JSDoc for scoped slot data
6. **Keep slots focused** - Single purpose per slot
