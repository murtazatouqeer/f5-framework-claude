---
name: vue-component-design
description: Vue component design patterns and principles
applies_to: vue
---

# Vue Component Design

## Overview

Well-designed components are reusable, maintainable, and testable.
This guide covers patterns for creating effective Vue components.

## Component Categories

### 1. Presentational Components (Dumb)

Focus on UI, receive data via props, emit events:

```vue
<!-- components/ui/UserCard.vue -->
<script setup lang="ts">
interface Props {
  name: string;
  email: string;
  avatarUrl?: string;
}

interface Emits {
  (e: 'click'): void;
}

defineProps<Props>();
defineEmits<Emits>();
</script>

<template>
  <div class="user-card" @click="$emit('click')">
    <img :src="avatarUrl" :alt="name" />
    <h3>{{ name }}</h3>
    <p>{{ email }}</p>
  </div>
</template>
```

### 2. Container Components (Smart)

Handle data fetching, state management:

```vue
<!-- features/users/components/UserListContainer.vue -->
<script setup lang="ts">
import { onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useUserStore } from '@/stores/useUserStore';
import UserList from './UserList.vue';
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue';

const store = useUserStore();
const { users, isLoading, error } = storeToRefs(store);

onMounted(() => {
  store.fetchUsers();
});

function handleUserClick(userId: string) {
  // Handle navigation or action
}
</script>

<template>
  <LoadingSpinner v-if="isLoading" />
  <ErrorMessage v-else-if="error" :message="error" />
  <UserList v-else :users="users" @user-click="handleUserClick" />
</template>
```

### 3. Compound Components

Work together as a unit:

```vue
<!-- components/Tabs/Tabs.vue -->
<script setup lang="ts">
import { provide, ref, type Ref } from 'vue';

const activeTab = ref(0);

provide('tabs', {
  activeTab,
  setActiveTab: (index: number) => {
    activeTab.value = index;
  },
});
</script>

<template>
  <div class="tabs">
    <slot />
  </div>
</template>
```

```vue
<!-- components/Tabs/TabList.vue -->
<script setup lang="ts">
</script>

<template>
  <div class="tab-list" role="tablist">
    <slot />
  </div>
</template>
```

```vue
<!-- components/Tabs/Tab.vue -->
<script setup lang="ts">
import { inject } from 'vue';

interface Props {
  index: number;
}

const props = defineProps<Props>();

const { activeTab, setActiveTab } = inject('tabs')!;

const isActive = computed(() => activeTab.value === props.index);
</script>

<template>
  <button
    role="tab"
    :aria-selected="isActive"
    :class="{ active: isActive }"
    @click="setActiveTab(index)"
  >
    <slot />
  </button>
</template>
```

```vue
<!-- Usage -->
<Tabs>
  <TabList>
    <Tab :index="0">First</Tab>
    <Tab :index="1">Second</Tab>
  </TabList>
  <TabPanels>
    <TabPanel :index="0">Content 1</TabPanel>
    <TabPanel :index="1">Content 2</TabPanel>
  </TabPanels>
</Tabs>
```

### 4. Renderless Components

Provide logic without UI:

```vue
<!-- components/MouseTracker.vue -->
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
  <p>Mouse: {{ x }}, {{ y }}</p>
</MouseTracker>
```

## Props Design

### Required vs Optional

```typescript
interface Props {
  // Required - must be provided
  id: string;
  title: string;

  // Optional with defaults
  variant?: 'primary' | 'secondary';
  disabled?: boolean;

  // Optional, truly optional
  description?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  disabled: false,
});
```

### Props Validation

```typescript
// Complex validation with runtime checks
const props = defineProps({
  status: {
    type: String as PropType<'active' | 'inactive'>,
    required: true,
    validator: (value: string) => ['active', 'inactive'].includes(value),
  },
  count: {
    type: Number,
    default: 0,
    validator: (value: number) => value >= 0,
  },
});
```

### Boolean Props

```vue
<!-- Boolean props are false by default -->
<script setup lang="ts">
interface Props {
  disabled?: boolean;
  loading?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  loading: false,
});
</script>

<!-- Usage -->
<Button disabled />          <!-- disabled = true -->
<Button :disabled="false" /> <!-- disabled = false -->
<Button />                   <!-- disabled = false -->
```

## Events Design

### Typed Events

```typescript
interface Emits {
  // Simple event
  (e: 'click'): void;

  // Event with payload
  (e: 'update', value: string): void;

  // v-model event
  (e: 'update:modelValue', value: string): void;

  // Complex payload
  (e: 'submit', data: { id: string; values: FormValues }): void;
}

const emit = defineEmits<Emits>();
```

### v-model Support

```vue
<!-- Single v-model -->
<script setup lang="ts">
interface Props {
  modelValue: string;
}

interface Emits {
  (e: 'update:modelValue', value: string): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <input :value="modelValue" @input="handleInput" />
</template>
```

```vue
<!-- Multiple v-models -->
<script setup lang="ts">
interface Props {
  firstName: string;
  lastName: string;
}

interface Emits {
  (e: 'update:firstName', value: string): void;
  (e: 'update:lastName', value: string): void;
}

defineProps<Props>();
defineEmits<Emits>();
</script>

<!-- Usage -->
<UserName v-model:firstName="first" v-model:lastName="last" />
```

## Slots Design

### Default Slot

```vue
<script setup lang="ts">
// Component just wraps content
</script>

<template>
  <div class="card">
    <slot>Default content if empty</slot>
  </div>
</template>
```

### Named Slots

```vue
<script setup lang="ts">
interface Props {
  title: string;
}

defineProps<Props>();
</script>

<template>
  <article class="card">
    <header v-if="$slots.header || title">
      <slot name="header">
        <h2>{{ title }}</h2>
      </slot>
    </header>

    <main>
      <slot />
    </main>

    <footer v-if="$slots.footer">
      <slot name="footer" />
    </footer>
  </article>
</template>
```

### Scoped Slots

```vue
<!-- List component exposing item data -->
<script setup lang="ts">
interface Props {
  items: Item[];
}

defineProps<Props>();
</script>

<template>
  <ul>
    <li v-for="item in items" :key="item.id">
      <slot name="item" :item="item" :index="index">
        {{ item.name }}
      </slot>
    </li>
  </ul>
</template>

<!-- Usage -->
<ItemList :items="items">
  <template #item="{ item, index }">
    <span>{{ index + 1 }}. {{ item.name }}</span>
  </template>
</ItemList>
```

## Component Composition

### Using Composables

```vue
<script setup lang="ts">
import { useLocalStorage } from '@/composables/useLocalStorage';
import { useDebounce } from '@/composables/useDebounce';

// Reuse logic
const { data: theme } = useLocalStorage('theme', 'light');
const debouncedSearch = useDebounce(searchQuery, 300);
</script>
```

### Higher-Order Components

```typescript
// withLoading.ts
import { defineComponent, h, type Component } from 'vue';
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue';

export function withLoading<T extends Component>(component: T) {
  return defineComponent({
    props: {
      loading: Boolean,
    },
    setup(props, { slots }) {
      return () => {
        if (props.loading) {
          return h(LoadingSpinner);
        }
        return h(component, null, slots);
      };
    },
  });
}
```

## Best Practices

1. **Single Responsibility** - Each component does one thing well
2. **Props Down, Events Up** - Unidirectional data flow
3. **Composition over Inheritance** - Use composables
4. **Explicit Dependencies** - Type props and emits
5. **Minimal State** - Derive when possible
6. **Accessible by Default** - ARIA attributes, keyboard support
7. **Document Props** - JSDoc comments for IDE support
