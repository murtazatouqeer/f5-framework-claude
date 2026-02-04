---
name: vue-scoped-styles
description: Scoped styles and CSS features in Vue SFCs
applies_to: vue
---

# Scoped Styles

## Overview

Vue Single File Components support scoped CSS that only applies to
the current component. This prevents style leakage and conflicts.

## Basic Scoped Styles

```vue
<template>
  <div class="container">
    <h1 class="title">{{ title }}</h1>
    <p class="content">{{ content }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  content: string;
}>();
</script>

<style scoped>
.container {
  padding: 1rem;
  border-radius: 8px;
  background-color: #f5f5f5;
}

.title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 0.5rem;
}

.content {
  color: #666;
  line-height: 1.6;
}
</style>
```

## How Scoped Works

Vue adds data attributes to elements and selectors:

```html
<!-- Compiled output -->
<div class="container" data-v-7ba5bd90>
  <h1 class="title" data-v-7ba5bd90>Title</h1>
</div>

<style>
.container[data-v-7ba5bd90] {
  padding: 1rem;
}
</style>
```

## Deep Selectors

### Targeting Child Components

```vue
<style scoped>
/* Target child component elements */
.parent :deep(.child-class) {
  color: red;
}

/* Alternative syntax */
.parent ::v-deep(.child-class) {
  color: red;
}

/* Legacy syntax (Vue 2) */
.parent >>> .child-class {
  color: red;
}
</style>
```

### Practical Example

```vue
<template>
  <div class="form-wrapper">
    <FormInput label="Name" />
    <FormInput label="Email" />
  </div>
</template>

<style scoped>
.form-wrapper {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

/* Style child FormInput component */
.form-wrapper :deep(.form-input) {
  border: 1px solid #ccc;
}

.form-wrapper :deep(.form-input:focus) {
  border-color: #3b82f6;
}
</style>
```

## Slotted Selectors

### Styling Slot Content

```vue
<template>
  <div class="card">
    <slot></slot>
  </div>
</template>

<style scoped>
.card {
  padding: 1rem;
  border: 1px solid #e5e7eb;
}

/* Target slotted content */
.card :slotted(p) {
  margin: 0;
  color: #374151;
}

.card :slotted(.highlight) {
  background-color: yellow;
}
</style>
```

## Global Selectors

### Within Scoped Block

```vue
<style scoped>
/* This is scoped */
.button {
  padding: 0.5rem 1rem;
}

/* This is global */
:global(.global-class) {
  color: inherit;
}

/* Target body or html */
:global(body.dark-mode) .button {
  background-color: #1f2937;
}
</style>
```

### Separate Global Block

```vue
<style>
/* Global styles */
.global-utility {
  display: flex;
  align-items: center;
}
</style>

<style scoped>
/* Scoped styles */
.component-specific {
  color: blue;
}
</style>
```

## CSS Variables

### Component-Scoped Variables

```vue
<template>
  <div class="themed-box">
    <h2>{{ title }}</h2>
    <p>{{ description }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  description: string;
}>();
</script>

<style scoped>
.themed-box {
  --box-bg: #f0f9ff;
  --box-border: #0ea5e9;
  --box-text: #0369a1;

  background-color: var(--box-bg);
  border: 2px solid var(--box-border);
  color: var(--box-text);
  padding: 1rem;
  border-radius: 8px;
}

.themed-box h2 {
  color: var(--box-border);
}
</style>
```

### Dynamic CSS Variables (v-bind)

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  color?: string;
  size?: 'sm' | 'md' | 'lg';
}>();

const themeColor = ref(props.color || '#3b82f6');

const fontSize = computed(() => {
  const sizes = { sm: '0.875rem', md: '1rem', lg: '1.25rem' };
  return sizes[props.size || 'md'];
});
</script>

<template>
  <button class="dynamic-button">
    <slot>Click me</slot>
  </button>
</template>

<style scoped>
.dynamic-button {
  /* Use reactive values in CSS */
  background-color: v-bind(themeColor);
  font-size: v-bind(fontSize);

  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.dynamic-button:hover {
  filter: brightness(1.1);
}
</style>
```

### Complex Expressions

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

const isActive = ref(false);
const progress = ref(50);

const progressWidth = computed(() => `${progress.value}%`);
const activeColor = computed(() => isActive.value ? '#10b981' : '#6b7280');
</script>

<template>
  <div class="progress-bar">
    <div class="progress-fill"></div>
  </div>
</template>

<style scoped>
.progress-bar {
  width: 100%;
  height: 8px;
  background-color: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  width: v-bind(progressWidth);
  background-color: v-bind(activeColor);
  transition: width 0.3s ease, background-color 0.3s ease;
}
</style>
```

## CSS Preprocessing

### SCSS with Scoped

```vue
<style lang="scss" scoped>
$primary: #3b82f6;
$spacing: 1rem;

.card {
  padding: $spacing;

  &__header {
    font-weight: bold;
    margin-bottom: $spacing / 2;
  }

  &__body {
    color: #666;
  }

  &:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  }

  &--highlighted {
    border-left: 4px solid $primary;
  }
}

// Mixins work too
@mixin flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.centered {
  @include flex-center;
}
</style>
```

### Less with Scoped

```vue
<style lang="less" scoped>
@primary: #3b82f6;

.button {
  background-color: @primary;

  &:hover {
    background-color: darken(@primary, 10%);
  }
}
</style>
```

## Best Practices

### Component Styling Pattern

```vue
<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  disabled: false,
});
</script>

<template>
  <button
    :class="[
      'btn',
      `btn--${variant}`,
      `btn--${size}`,
      { 'btn--disabled': disabled }
    ]"
    :disabled="disabled"
  >
    <slot />
  </button>
</template>

<style scoped>
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.2s ease;
  cursor: pointer;
}

/* Sizes */
.btn--sm {
  padding: 0.375rem 0.75rem;
  font-size: 0.875rem;
}

.btn--md {
  padding: 0.5rem 1rem;
  font-size: 1rem;
}

.btn--lg {
  padding: 0.75rem 1.5rem;
  font-size: 1.125rem;
}

/* Variants */
.btn--primary {
  background-color: #3b82f6;
  color: white;
  border: none;
}

.btn--primary:hover:not(.btn--disabled) {
  background-color: #2563eb;
}

.btn--secondary {
  background-color: #6b7280;
  color: white;
  border: none;
}

.btn--outline {
  background-color: transparent;
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.btn--outline:hover:not(.btn--disabled) {
  background-color: #3b82f6;
  color: white;
}

/* States */
.btn--disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

## Summary

1. **Use scoped by default** - Prevents style conflicts
2. **Deep selectors** - For styling child components
3. **Slotted selectors** - For styling slot content
4. **v-bind** - For reactive CSS values
5. **CSS variables** - For theming and dynamic values
6. **Preprocessors** - SCSS/Less work with scoped
</style>
