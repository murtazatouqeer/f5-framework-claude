---
name: vue-tailwind
description: Tailwind CSS integration with Vue components
applies_to: vue
---

# Tailwind CSS with Vue

## Overview

Tailwind CSS provides utility-first CSS that works excellently
with Vue's component-based architecture.

## Setup

```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### main.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

## Basic Usage

### Simple Component

```vue
<template>
  <div class="p-4 bg-white rounded-lg shadow-md">
    <h2 class="text-xl font-bold text-gray-800 mb-2">
      {{ title }}
    </h2>
    <p class="text-gray-600">
      {{ description }}
    </p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
}>();
</script>
```

### Interactive States

```vue
<template>
  <button
    class="
      px-4 py-2
      bg-blue-500 text-white font-medium
      rounded-lg
      hover:bg-blue-600
      focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
      active:bg-blue-700
      disabled:opacity-50 disabled:cursor-not-allowed
      transition-colors duration-200
    "
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{
  disabled?: boolean;
}>();
</script>
```

## Dynamic Classes

### Conditional Classes

```vue
<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  variant: 'primary' | 'secondary' | 'danger';
  size: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}>();

const buttonClasses = computed(() => {
  const base = 'font-medium rounded-lg transition-colors';

  const variants = {
    primary: 'bg-blue-500 text-white hover:bg-blue-600',
    secondary: 'bg-gray-200 text-gray-800 hover:bg-gray-300',
    danger: 'bg-red-500 text-white hover:bg-red-600',
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return [
    base,
    variants[props.variant],
    sizes[props.size],
    props.disabled && 'opacity-50 cursor-not-allowed',
  ];
});
</script>

<template>
  <button :class="buttonClasses" :disabled="disabled">
    <slot />
  </button>
</template>
```

### Object Syntax

```vue
<template>
  <div
    :class="{
      'p-4 rounded-lg': true,
      'bg-green-100 border-green-500': status === 'success',
      'bg-red-100 border-red-500': status === 'error',
      'bg-yellow-100 border-yellow-500': status === 'warning',
      'border-l-4': true,
    }"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  status: 'success' | 'error' | 'warning';
}>();
</script>
```

## Component Patterns

### Card Component

```vue
<!-- components/ui/Card.vue -->
<script setup lang="ts">
interface Props {
  variant?: 'default' | 'bordered' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  padding: 'md',
});

const cardClasses = computed(() => {
  const variants = {
    default: 'bg-white',
    bordered: 'bg-white border border-gray-200',
    elevated: 'bg-white shadow-lg',
  };

  const paddings = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  return [
    'rounded-lg',
    variants[props.variant],
    paddings[props.padding],
  ];
});
</script>

<template>
  <div :class="cardClasses">
    <div v-if="$slots.header" class="mb-4">
      <slot name="header" />
    </div>

    <div>
      <slot />
    </div>

    <div v-if="$slots.footer" class="mt-4 pt-4 border-t border-gray-100">
      <slot name="footer" />
    </div>
  </div>
</template>
```

### Input Component

```vue
<!-- components/ui/Input.vue -->
<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  modelValue: string;
  label?: string;
  placeholder?: string;
  error?: string;
  disabled?: boolean;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

const inputClasses = computed(() => [
  'w-full px-3 py-2 rounded-lg border transition-colors',
  'focus:outline-none focus:ring-2 focus:ring-offset-0',
  props.error
    ? 'border-red-500 focus:ring-red-500'
    : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500',
  props.disabled && 'bg-gray-100 cursor-not-allowed',
]);
</script>

<template>
  <div class="space-y-1">
    <label v-if="label" class="block text-sm font-medium text-gray-700">
      {{ label }}
    </label>

    <input
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />

    <p v-if="error" class="text-sm text-red-600">
      {{ error }}
    </p>
  </div>
</template>
```

### Badge Component

```vue
<!-- components/ui/Badge.vue -->
<script setup lang="ts">
type Variant = 'default' | 'success' | 'warning' | 'error' | 'info';

const props = withDefaults(defineProps<{
  variant?: Variant;
}>(), {
  variant: 'default',
});

const variantClasses: Record<Variant, string> = {
  default: 'bg-gray-100 text-gray-800',
  success: 'bg-green-100 text-green-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  info: 'bg-blue-100 text-blue-800',
};
</script>

<template>
  <span
    :class="[
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      variantClasses[variant],
    ]"
  >
    <slot />
  </span>
</template>
```

## Responsive Design

```vue
<template>
  <div class="container mx-auto px-4">
    <!-- Grid that changes columns based on screen size -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      <div
        v-for="item in items"
        :key="item.id"
        class="
          p-4 bg-white rounded-lg shadow
          hover:shadow-lg transition-shadow
        "
      >
        {{ item.name }}
      </div>
    </div>

    <!-- Hide/show based on screen size -->
    <nav class="hidden md:flex space-x-4">
      <!-- Desktop navigation -->
    </nav>

    <button class="md:hidden">
      <!-- Mobile menu button -->
    </button>
  </div>
</template>
```

## Dark Mode

### Setup

```javascript
// tailwind.config.js
export default {
  darkMode: 'class', // or 'media'
  // ...
}
```

### Usage

```vue
<script setup lang="ts">
import { useDark, useToggle } from '@vueuse/core';

const isDark = useDark();
const toggleDark = useToggle(isDark);
</script>

<template>
  <div class="min-h-screen bg-white dark:bg-gray-900 transition-colors">
    <header class="p-4 bg-gray-100 dark:bg-gray-800">
      <h1 class="text-gray-900 dark:text-white">
        My App
      </h1>

      <button
        @click="toggleDark()"
        class="p-2 rounded-lg bg-gray-200 dark:bg-gray-700"
      >
        <span v-if="isDark">🌙</span>
        <span v-else>☀️</span>
      </button>
    </header>

    <main class="p-4">
      <p class="text-gray-700 dark:text-gray-300">
        Content that adapts to dark mode
      </p>
    </main>
  </div>
</template>
```

## Custom Classes with @apply

```vue
<template>
  <button class="btn btn-primary">
    Primary Button
  </button>
</template>

<style>
@layer components {
  .btn {
    @apply px-4 py-2 rounded-lg font-medium transition-colors;
    @apply focus:outline-none focus:ring-2 focus:ring-offset-2;
  }

  .btn-primary {
    @apply bg-blue-500 text-white;
    @apply hover:bg-blue-600;
    @apply focus:ring-blue-500;
  }

  .btn-secondary {
    @apply bg-gray-200 text-gray-800;
    @apply hover:bg-gray-300;
    @apply focus:ring-gray-500;
  }
}
</style>
```

## Animations

```vue
<script setup lang="ts">
import { ref } from 'vue';

const isOpen = ref(false);
</script>

<template>
  <div>
    <button
      @click="isOpen = !isOpen"
      class="flex items-center space-x-2"
    >
      <span>Toggle</span>
      <svg
        :class="[
          'w-4 h-4 transition-transform duration-200',
          isOpen && 'rotate-180'
        ]"
      >
        <!-- chevron icon -->
      </svg>
    </button>

    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-if="isOpen" class="mt-2 p-4 bg-gray-100 rounded-lg">
        Dropdown content
      </div>
    </Transition>
  </div>
</template>
```

## Best Practices

1. **Extract repeated patterns** - Use composables or @apply for reusable styles
2. **Use computed for complex classes** - Keep templates readable
3. **Leverage variants** - Use props to control appearance
4. **Responsive-first** - Design for mobile, enhance for larger screens
5. **Dark mode support** - Plan for both themes from the start
6. **Consistent spacing** - Use Tailwind's spacing scale consistently
