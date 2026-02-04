---
name: nuxt-component
description: Template for Nuxt 3 Vue components
applies_to: nuxt
---

# Nuxt Component Template

## Basic Component

```vue
<script setup lang="ts">
interface Props {
  title: string;
  description?: string;
  variant?: 'primary' | 'secondary';
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
});

const emit = defineEmits<{
  click: [event: MouseEvent];
  change: [value: string];
}>();
</script>

<template>
  <div :class="['{{COMPONENT_NAME}}', `{{COMPONENT_NAME}}--${variant}`]">
    <h2>{{ title }}</h2>
    <p v-if="description">{{ description }}</p>
    <slot />
  </div>
</template>

<style scoped>
.{{COMPONENT_NAME}} {
  /* Component styles */
}

.{{COMPONENT_NAME}}--primary {
  /* Primary variant */
}

.{{COMPONENT_NAME}}--secondary {
  /* Secondary variant */
}
</style>
```

## Component with Slots

```vue
<script setup lang="ts">
interface Props {
  loading?: boolean;
}

defineProps<Props>();
</script>

<template>
  <div class="{{COMPONENT_NAME}}">
    <!-- Header slot -->
    <header v-if="$slots.header" class="{{COMPONENT_NAME}}__header">
      <slot name="header" />
    </header>

    <!-- Default slot with loading state -->
    <main class="{{COMPONENT_NAME}}__body">
      <div v-if="loading" class="{{COMPONENT_NAME}}__loading">
        <slot name="loading">Loading...</slot>
      </div>
      <slot v-else />
    </main>

    <!-- Footer slot -->
    <footer v-if="$slots.footer" class="{{COMPONENT_NAME}}__footer">
      <slot name="footer" />
    </footer>
  </div>
</template>
```

## Component with v-model

```vue
<script setup lang="ts">
interface Props {
  modelValue: string;
  label?: string;
  placeholder?: string;
  error?: string;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const inputValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});
</script>

<template>
  <div class="form-input">
    <label v-if="label" class="form-input__label">{{ label }}</label>
    <input
      v-model="inputValue"
      :placeholder="placeholder"
      :class="{ 'form-input__field--error': error }"
      class="form-input__field"
    />
    <span v-if="error" class="form-input__error">{{ error }}</span>
  </div>
</template>
```

## Component with Composable

```vue
<script setup lang="ts">
interface Props {
  id: string;
}

const props = defineProps<Props>();

// Use composable for data
const { data, isLoading, error, refresh } = use{{RESOURCE}}(props.id);

// Expose methods to parent
defineExpose({
  refresh,
});
</script>

<template>
  <div class="{{COMPONENT_NAME}}">
    <div v-if="isLoading">Loading...</div>
    <div v-else-if="error">{{ error.message }}</div>
    <div v-else>
      <!-- Render data -->
      <slot :data="data" />
    </div>
  </div>
</template>
```

## Async Component

```vue
<script setup lang="ts">
// This component can be lazy-loaded
// <LazyMyComponent /> or defineAsyncComponent

interface Props {
  resourceId: string;
}

const props = defineProps<Props>();

// Data is fetched when component loads
const { data } = await useFetch(`/api/resource/${props.resourceId}`);
</script>

<template>
  <div class="async-component">
    <slot :data="data" />
  </div>
</template>
```

## Generic Component

```vue
<script setup lang="ts" generic="T extends { id: string; name: string }">
interface Props {
  items: T[];
  selected?: T;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  select: [item: T];
}>();
</script>

<template>
  <ul class="item-list">
    <li
      v-for="item in items"
      :key="item.id"
      :class="{ active: selected?.id === item.id }"
      @click="emit('select', item)"
    >
      {{ item.name }}
    </li>
  </ul>
</template>
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{COMPONENT_NAME}}` | Component class name | `product-card`, `user-avatar` |
| `{{RESOURCE}}` | Related resource | `Product`, `User` |
