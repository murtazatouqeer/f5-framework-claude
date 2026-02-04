---
name: vue-css-modules
description: CSS Modules usage in Vue components
applies_to: vue
---

# CSS Modules in Vue

## Overview

CSS Modules provide automatic class name scoping with JavaScript
imports. They generate unique class names to prevent conflicts.

## Basic Usage

### Module Syntax

```vue
<template>
  <div :class="$style.container">
    <h1 :class="$style.title">{{ title }}</h1>
    <p :class="$style.content">{{ content }}</p>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  content: string;
}>();
</script>

<style module>
.container {
  padding: 1rem;
  background-color: #f5f5f5;
  border-radius: 8px;
}

.title {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
}

.content {
  color: #666;
  line-height: 1.6;
}
</style>
```

## Named Modules

### Custom Module Names

```vue
<template>
  <div :class="classes.wrapper">
    <button :class="[classes.button, classes.primary]">
      Primary
    </button>
    <button :class="[classes.button, classes.secondary]">
      Secondary
    </button>
  </div>
</template>

<script setup lang="ts">
// Access named module via useCssModule
import { useCssModule } from 'vue';

const classes = useCssModule('buttons');
</script>

<style module="buttons">
.wrapper {
  display: flex;
  gap: 0.5rem;
}

.button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.primary {
  background-color: #3b82f6;
  color: white;
}

.secondary {
  background-color: #6b7280;
  color: white;
}
</style>
```

## Dynamic Classes

### Computed Classes

```vue
<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  variant: 'success' | 'warning' | 'error';
  size: 'sm' | 'md' | 'lg';
}>();

const alertClasses = computed(() => [
  $style.alert,
  $style[props.variant],
  $style[`size-${props.size}`],
]);
</script>

<template>
  <div :class="alertClasses">
    <slot />
  </div>
</template>

<style module>
.alert {
  padding: 1rem;
  border-radius: 8px;
  border-left: 4px solid;
}

.success {
  background-color: #d1fae5;
  border-color: #10b981;
  color: #065f46;
}

.warning {
  background-color: #fef3c7;
  border-color: #f59e0b;
  color: #92400e;
}

.error {
  background-color: #fee2e2;
  border-color: #ef4444;
  color: #991b1b;
}

.size-sm {
  padding: 0.5rem;
  font-size: 0.875rem;
}

.size-md {
  padding: 1rem;
  font-size: 1rem;
}

.size-lg {
  padding: 1.5rem;
  font-size: 1.125rem;
}
</style>
```

### Conditional Classes

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

const isActive = ref(false);
const isDisabled = ref(false);

const buttonClasses = computed(() => ({
  [$style.button]: true,
  [$style.active]: isActive.value,
  [$style.disabled]: isDisabled.value,
}));
</script>

<template>
  <button :class="buttonClasses" :disabled="isDisabled">
    Click me
  </button>
</template>

<style module>
.button {
  padding: 0.5rem 1rem;
  background-color: #e5e7eb;
  border: none;
  border-radius: 4px;
  transition: all 0.2s;
}

.active {
  background-color: #3b82f6;
  color: white;
}

.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

## Composing Classes

### Composition with composes

```vue
<template>
  <div :class="$style.card">
    <header :class="$style.cardHeader">
      {{ title }}
    </header>
    <div :class="$style.cardBody">
      <slot />
    </div>
  </div>
</template>

<style module>
.baseCard {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.basePadding {
  padding: 1rem;
}

.card {
  composes: baseCard;
  background-color: white;
}

.cardHeader {
  composes: basePadding;
  font-weight: bold;
  border-bottom: 1px solid #e5e7eb;
}

.cardBody {
  composes: basePadding;
}
</style>
```

### Composing from External Files

```css
/* styles/shared.module.css */
.flexCenter {
  display: flex;
  align-items: center;
  justify-content: center;
}

.textTruncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
```

```vue
<style module>
.container {
  composes: flexCenter from '@/styles/shared.module.css';
  height: 100vh;
}

.title {
  composes: textTruncate from '@/styles/shared.module.css';
  max-width: 200px;
}
</style>
```

## With TypeScript

### Type-Safe CSS Modules

```typescript
// types/css-modules.d.ts
declare module '*.module.css' {
  const classes: { [key: string]: string };
  export default classes;
}

declare module '*.module.scss' {
  const classes: { [key: string]: string };
  export default classes;
}
```

### Using in Components

```vue
<script setup lang="ts">
import { computed } from 'vue';

// Type the $style object
interface Styles {
  container: string;
  title: string;
  active: string;
  [key: string]: string;
}

// Access via useCssModule for type safety
import { useCssModule } from 'vue';
const $style = useCssModule() as Styles;

const props = defineProps<{
  isActive: boolean;
}>();

const containerClass = computed(() => [
  $style.container,
  props.isActive && $style.active,
]);
</script>
```

## Multiple Style Blocks

```vue
<template>
  <div :class="$style.wrapper">
    <button :class="buttons.primary">Primary</button>
    <button :class="buttons.secondary">Secondary</button>
  </div>
</template>

<script setup lang="ts">
import { useCssModule } from 'vue';

const buttons = useCssModule('buttons');
</script>

<!-- Default module accessed via $style -->
<style module>
.wrapper {
  display: flex;
  gap: 1rem;
  padding: 1rem;
}
</style>

<!-- Named module accessed via useCssModule -->
<style module="buttons">
.primary {
  background-color: #3b82f6;
  color: white;
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
}

.secondary {
  background-color: transparent;
  color: #3b82f6;
  padding: 0.5rem 1rem;
  border: 1px solid #3b82f6;
  border-radius: 4px;
}
</style>
```

## CSS Modules vs Scoped CSS

| Feature | CSS Modules | Scoped CSS |
|---------|-------------|------------|
| Class naming | Hash-based unique names | Data attribute selectors |
| JavaScript access | Via $style or useCssModule | Not available |
| Composition | composes keyword | Not available |
| External file import | Supported | Not supported |
| Performance | Slightly better | Good |
| Deep styling | Manual class passing | :deep() selector |

## Best Practices

### Component Pattern

```vue
<script setup lang="ts">
import { computed, useCssModule } from 'vue';

interface Props {
  variant?: 'filled' | 'outlined' | 'text';
  color?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'filled',
  color: 'primary',
  size: 'md',
  disabled: false,
});

const $style = useCssModule();

const buttonClasses = computed(() => [
  $style.button,
  $style[props.variant],
  $style[props.color],
  $style[props.size],
  props.disabled && $style.disabled,
]);
</script>

<template>
  <button :class="buttonClasses" :disabled="disabled">
    <slot />
  </button>
</template>

<style module>
.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 500;
  border-radius: 6px;
  transition: all 0.2s ease;
  cursor: pointer;
}

/* Sizes */
.sm { padding: 0.375rem 0.75rem; font-size: 0.875rem; }
.md { padding: 0.5rem 1rem; font-size: 1rem; }
.lg { padding: 0.75rem 1.5rem; font-size: 1.125rem; }

/* Variants */
.filled { border: none; }
.outlined { background: transparent; border-width: 1px; border-style: solid; }
.text { background: transparent; border: none; }

/* Colors - Filled */
.filled.primary { background-color: #3b82f6; color: white; }
.filled.secondary { background-color: #6b7280; color: white; }
.filled.danger { background-color: #ef4444; color: white; }

/* Colors - Outlined */
.outlined.primary { border-color: #3b82f6; color: #3b82f6; }
.outlined.secondary { border-color: #6b7280; color: #6b7280; }
.outlined.danger { border-color: #ef4444; color: #ef4444; }

/* States */
.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

## Summary

1. **Use `module` attribute** - Enables CSS Modules in style block
2. **Access via `$style`** - Default module available in template
3. **Named modules** - Use `useCssModule('name')` for custom names
4. **Composition** - Use `composes` to extend classes
5. **Type safety** - Add type declarations for TypeScript
6. **Choose wisely** - Use CSS Modules when you need JS access to classes
