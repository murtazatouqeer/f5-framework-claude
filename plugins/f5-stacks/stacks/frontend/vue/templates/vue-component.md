---
name: vue-component
description: Vue SFC component template
applies_to: vue
variables:
  - name: componentName
    description: PascalCase component name
  - name: props
    description: Component props with types
  - name: emits
    description: Events emitted by component
---

# Vue Component Template

## Basic Component

```vue
<script setup lang="ts">
// ============================================================
// {{componentName}}.vue
// ============================================================

// ------------------------------------------------------------
// Props
// ------------------------------------------------------------
interface Props {
  // Add your props here
  // Example:
  // title: string;
  // variant?: 'primary' | 'secondary';
  // disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  // Default values for optional props
  // variant: 'primary',
  // disabled: false,
});

// ------------------------------------------------------------
// Emits
// ------------------------------------------------------------
const emit = defineEmits<{
  // Add your events here
  // Example:
  // (e: 'click'): void;
  // (e: 'update', value: string): void;
}>();

// ------------------------------------------------------------
// State
// ------------------------------------------------------------
// const state = ref();

// ------------------------------------------------------------
// Computed
// ------------------------------------------------------------
// const computed = computed(() => {});

// ------------------------------------------------------------
// Methods
// ------------------------------------------------------------
// function handleAction() {}

// ------------------------------------------------------------
// Lifecycle
// ------------------------------------------------------------
// onMounted(() => {});
</script>

<template>
  <div class="{{componentName | kebab}}">
    <!-- Component content -->
    <slot />
  </div>
</template>

<style scoped>
.{{componentName | kebab}} {
  /* Component styles */
}
</style>
```

## With Props and Events

```vue
<script setup lang="ts">
// ============================================================
// {{componentName}}.vue
// ============================================================

import { computed } from 'vue';

// ------------------------------------------------------------
// Props
// ------------------------------------------------------------
interface Props {
  modelValue: string;
  label: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '',
  disabled: false,
});

// ------------------------------------------------------------
// Emits
// ------------------------------------------------------------
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'blur'): void;
  (e: 'focus'): void;
}>();

// ------------------------------------------------------------
// Computed
// ------------------------------------------------------------
const inputClasses = computed(() => ({
  'input': true,
  'input--error': !!props.error,
  'input--disabled': props.disabled,
}));

// ------------------------------------------------------------
// Methods
// ------------------------------------------------------------
function handleInput(event: Event) {
  const target = event.target as HTMLInputElement;
  emit('update:modelValue', target.value);
}
</script>

<template>
  <div class="form-field">
    <label v-if="label" class="form-field__label">
      {{ label }}
    </label>

    <input
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="handleInput"
      @blur="emit('blur')"
      @focus="emit('focus')"
    />

    <span v-if="error" class="form-field__error">
      {{ error }}
    </span>
  </div>
</template>

<style scoped>
.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-field__label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.input--error {
  border-color: #ef4444;
}

.input--disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}

.form-field__error {
  font-size: 0.75rem;
  color: #ef4444;
}
</style>
```

## With Slots

```vue
<script setup lang="ts">
// ============================================================
// {{componentName}}.vue - Card Component with Slots
// ============================================================

interface Props {
  variant?: 'default' | 'bordered' | 'elevated';
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
});
</script>

<template>
  <div :class="['card', `card--${variant}`]">
    <header v-if="$slots.header" class="card__header">
      <slot name="header" />
    </header>

    <div class="card__body">
      <slot />
    </div>

    <footer v-if="$slots.footer" class="card__footer">
      <slot name="footer" />
    </footer>
  </div>
</template>

<style scoped>
.card {
  border-radius: 0.5rem;
  overflow: hidden;
}

.card--default {
  background-color: white;
}

.card--bordered {
  border: 1px solid #e5e7eb;
  background-color: white;
}

.card--elevated {
  background-color: white;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

.card__header {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.card__body {
  padding: 1rem;
}

.card__footer {
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
}
</style>
```

## Usage

```vue
<template>
  <!-- Basic usage -->
  <{{componentName}} />

  <!-- With props -->
  <{{componentName}}
    v-model="value"
    label="Email"
    placeholder="Enter email"
    :error="errors.email"
    @blur="handleBlur"
  />

  <!-- With slots -->
  <{{componentName}} variant="bordered">
    <template #header>
      <h2>Card Title</h2>
    </template>

    <p>Card content goes here</p>

    <template #footer>
      <button>Action</button>
    </template>
  </{{componentName}}>
</template>
```
