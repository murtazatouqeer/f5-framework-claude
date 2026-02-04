---
name: nuxt-component-generator
description: Generates Nuxt 3 Vue components with proper patterns
applies_to: nuxt
---

# Nuxt Component Generator Agent

## Purpose
Generate reusable Vue 3 components for Nuxt applications following Composition API patterns and best practices.

## Capabilities
- Single File Components (SFC)
- Props with TypeScript types
- Emits with type safety
- Slots for composition
- Auto-import integration

## Input Requirements
- Component name and purpose
- Props definition
- Events to emit
- Slot requirements

## Output Deliverables
1. Component file (.vue)
2. Type exports if complex

## Generation Process

### 1. Analyze Requirements
```yaml
component_analysis:
  - name: "ProductCard"
  - props: [{name: "product", type: "Product", required: true}]
  - emits: ["select", "delete"]
  - slots: ["default", "actions"]
```

### 2. Generate Component

```vue
<!-- components/{{ComponentName}}.vue -->
<script setup lang="ts">
import type { {{PropType}} } from '~/types';

// Props
interface Props {
  {{propName}}: {{PropType}};
  variant?: 'default' | 'compact';
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  disabled: false,
});

// Emits
interface Emits {
  (e: 'select', value: {{PropType}}): void;
  (e: 'delete', id: string): void;
}

const emit = defineEmits<Emits>();

// Slots
defineSlots<{
  default?: (props: { item: {{PropType}} }) => any;
  actions?: () => any;
  header?: () => any;
}>();

// Composables
const { isLoading, execute } = useAsync();

// Computed
const computedClass = computed(() => ({
  'component--compact': props.variant === 'compact',
  'component--disabled': props.disabled,
}));

// Methods
function handleSelect() {
  if (!props.disabled) {
    emit('select', props.{{propName}});
  }
}

async function handleDelete() {
  if (confirm('Are you sure?')) {
    await execute(async () => {
      emit('delete', props.{{propName}}.id);
    });
  }
}
</script>

<template>
  <div class="component" :class="computedClass">
    <!-- Header slot -->
    <div v-if="$slots.header" class="component__header">
      <slot name="header" />
    </div>

    <!-- Main content -->
    <div class="component__content" @click="handleSelect">
      <slot :item="{{propName}}">
        <!-- Default content -->
        <h3>{{ {{propName}}.name }}</h3>
        <p>{{ {{propName}}.description }}</p>
      </slot>
    </div>

    <!-- Actions slot -->
    <div v-if="$slots.actions" class="component__actions">
      <slot name="actions" />
    </div>

    <!-- Loading overlay -->
    <div v-if="isLoading" class="component__loading">
      <UIcon name="i-heroicons-arrow-path" class="animate-spin" />
    </div>
  </div>
</template>

<style scoped>
.component {
  @apply relative rounded-lg border p-4;
}

.component--compact {
  @apply p-2;
}

.component--disabled {
  @apply opacity-50 cursor-not-allowed;
}

.component__loading {
  @apply absolute inset-0 flex items-center justify-center bg-white/50;
}
</style>
```

### 3. Component Patterns

#### Card Component
```vue
<script setup lang="ts">
interface Props {
  title?: string;
  description?: string;
  image?: string;
  to?: string;
}

defineProps<Props>();

defineSlots<{
  default?: () => any;
  header?: () => any;
  footer?: () => any;
}>();
</script>

<template>
  <component :is="to ? NuxtLink : 'div'" :to="to" class="card">
    <div v-if="image" class="card__image">
      <NuxtImg :src="image" :alt="title" />
    </div>
    <div class="card__header">
      <slot name="header">
        <h3 v-if="title">{{ title }}</h3>
        <p v-if="description">{{ description }}</p>
      </slot>
    </div>
    <div class="card__body">
      <slot />
    </div>
    <div v-if="$slots.footer" class="card__footer">
      <slot name="footer" />
    </div>
  </component>
</template>
```

#### Form Field Component
```vue
<script setup lang="ts">
interface Props {
  label: string;
  name: string;
  error?: string;
  required?: boolean;
}

defineProps<Props>();

const model = defineModel<string>();
</script>

<template>
  <div class="form-field">
    <label :for="name">
      {{ label }}
      <span v-if="required" class="text-red-500">*</span>
    </label>
    <slot>
      <input
        :id="name"
        v-model="model"
        :name="name"
        :required="required"
        class="form-input"
      />
    </slot>
    <p v-if="error" class="text-red-500 text-sm">{{ error }}</p>
  </div>
</template>
```

## Directory Organization
```
components/
├── ui/           # Base UI components
├── forms/        # Form components
├── layouts/      # Layout components
└── {{feature}}/  # Feature-specific
```

## Quality Checklist
- [ ] TypeScript props interface
- [ ] Type-safe emits
- [ ] Slots documented
- [ ] Scoped styles
- [ ] Accessible markup
- [ ] Proper naming convention
