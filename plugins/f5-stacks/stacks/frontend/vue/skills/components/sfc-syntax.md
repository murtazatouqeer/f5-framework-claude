---
name: vue-sfc-syntax
description: Vue Single File Component syntax and features
applies_to: vue
---

# Vue Single File Component (SFC)

## Overview

Single File Components (.vue files) encapsulate template, logic,
and styles in a single file, enabling better organization and tooling.

## Basic Structure

```vue
<!-- ComponentName.vue -->
<script setup lang="ts">
// Component logic using Composition API
import { ref, computed } from 'vue';

const count = ref(0);
const doubled = computed(() => count.value * 2);
</script>

<template>
  <!-- Component template -->
  <div class="component">
    <p>Count: {{ count }}</p>
    <p>Doubled: {{ doubled }}</p>
  </div>
</template>

<style scoped>
/* Component styles */
.component {
  padding: 1rem;
}
</style>
```

## Script Setup

### Basic Usage

```vue
<script setup lang="ts">
// All top-level bindings are exposed to template
import { ref } from 'vue';
import MyComponent from './MyComponent.vue';

const message = ref('Hello');

function greet() {
  alert(message.value);
}
</script>

<template>
  <!-- message, greet, and MyComponent are all available -->
  <MyComponent />
  <button @click="greet">{{ message }}</button>
</template>
```

### TypeScript Integration

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';
import type { User } from '@/types';

// Typed refs
const user = ref<User | null>(null);
const users = ref<User[]>([]);

// Generic ref
const data = ref<{ items: string[] }>({ items: [] });

// Computed with return type inference
const userName = computed(() => user.value?.name ?? 'Guest');
</script>
```

### Async Setup

```vue
<script setup lang="ts">
// Top-level await is supported
const response = await fetch('/api/data');
const data = await response.json();

// Component will be wrapped in <Suspense>
</script>
```

## Template Syntax

### Text Interpolation

```vue
<template>
  <!-- Text interpolation -->
  <p>{{ message }}</p>

  <!-- HTML (use with caution) -->
  <div v-html="rawHtml"></div>

  <!-- JavaScript expressions -->
  <p>{{ count + 1 }}</p>
  <p>{{ message.split('').reverse().join('') }}</p>
  <p>{{ isActive ? 'Yes' : 'No' }}</p>
</template>
```

### Directives

```vue
<template>
  <!-- v-bind: Attribute binding -->
  <img :src="imageUrl" :alt="imageAlt" />
  <div :class="{ active: isActive }" :style="{ color: textColor }"></div>

  <!-- v-on: Event handling -->
  <button @click="handleClick">Click</button>
  <input @keyup.enter="submit" />

  <!-- v-model: Two-way binding -->
  <input v-model="message" />
  <select v-model="selected">...</select>

  <!-- v-if/v-else-if/v-else: Conditional -->
  <div v-if="type === 'A'">A</div>
  <div v-else-if="type === 'B'">B</div>
  <div v-else>Other</div>

  <!-- v-show: Toggle visibility -->
  <p v-show="isVisible">Visible</p>

  <!-- v-for: List rendering -->
  <li v-for="item in items" :key="item.id">{{ item.name }}</li>

  <!-- v-slot: Slot content -->
  <template v-slot:header>Header content</template>
  <template #header>Shorthand</template>
</template>
```

### Event Modifiers

```vue
<template>
  <!-- Stop propagation -->
  <button @click.stop="handleClick">Click</button>

  <!-- Prevent default -->
  <form @submit.prevent="handleSubmit">...</form>

  <!-- Capture mode -->
  <div @click.capture="handleCapture">...</div>

  <!-- Only trigger on self -->
  <div @click.self="handleSelf">...</div>

  <!-- One-time handler -->
  <button @click.once="handleOnce">Click once</button>

  <!-- Passive (for scroll performance) -->
  <div @scroll.passive="handleScroll">...</div>

  <!-- Key modifiers -->
  <input @keyup.enter="submit" />
  <input @keyup.tab="nextField" />
  <input @keyup.delete="remove" />
  <input @keyup.esc="cancel" />

  <!-- System modifiers -->
  <button @click.ctrl="handleCtrlClick">Ctrl+Click</button>
  <button @click.alt="handleAltClick">Alt+Click</button>
  <button @click.shift="handleShiftClick">Shift+Click</button>
  <button @click.meta="handleMetaClick">Meta+Click</button>

  <!-- Mouse button modifiers -->
  <button @click.left="handleLeftClick">Left</button>
  <button @click.right="handleRightClick">Right</button>
  <button @click.middle="handleMiddleClick">Middle</button>

  <!-- Exact modifier -->
  <button @click.ctrl.exact="handleCtrlOnly">Only Ctrl</button>
</template>
```

### Class and Style Bindings

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

const isActive = ref(true);
const hasError = ref(false);

// Object syntax
const classObject = computed(() => ({
  active: isActive.value,
  'text-danger': hasError.value,
}));

// Array syntax
const activeClass = ref('active');
const errorClass = ref('text-danger');

// Style object
const styleObject = ref({
  color: 'red',
  fontSize: '13px',
});
</script>

<template>
  <!-- Object syntax -->
  <div :class="{ active: isActive, 'text-danger': hasError }"></div>
  <div :class="classObject"></div>

  <!-- Array syntax -->
  <div :class="[activeClass, errorClass]"></div>
  <div :class="[isActive ? activeClass : '', errorClass]"></div>

  <!-- Combined -->
  <div :class="[{ active: isActive }, errorClass]"></div>

  <!-- Style binding -->
  <div :style="{ color: activeColor, fontSize: fontSize + 'px' }"></div>
  <div :style="styleObject"></div>
  <div :style="[baseStyles, overridingStyles]"></div>
</template>
```

## Style Block

### Scoped Styles

```vue
<style scoped>
/* Only affects this component */
.example {
  color: red;
}

/* Deep selector - affects child components */
.parent :deep(.child) {
  color: blue;
}

/* Slotted selector - affects slot content */
:slotted(.slot-class) {
  font-weight: bold;
}

/* Global selector - escapes scoping */
:global(.global-class) {
  color: green;
}
</style>
```

### CSS Modules

```vue
<template>
  <p :class="$style.red">Red text</p>
  <p :class="[$style.red, $style.bold]">Red bold</p>
</template>

<style module>
.red {
  color: red;
}
.bold {
  font-weight: bold;
}
</style>
```

### Named CSS Modules

```vue
<template>
  <p :class="classes.red">Red text</p>
</template>

<style module="classes">
.red {
  color: red;
}
</style>
```

### CSS v-bind

```vue
<script setup lang="ts">
import { ref } from 'vue';

const color = ref('red');
const fontSize = ref(14);
</script>

<template>
  <p class="text">Hello</p>
</template>

<style scoped>
.text {
  color: v-bind(color);
  font-size: v-bind(fontSize + 'px');
}
</style>
```

### SCSS/Sass Support

```vue
<style lang="scss" scoped>
$primary: #42b983;

.component {
  color: $primary;

  &__title {
    font-weight: bold;
  }

  &--active {
    background: lighten($primary, 40%);
  }
}
</style>
```

## Special Blocks

### Multiple Script Blocks

```vue
<!-- Normal script for options that can't use <script setup> -->
<script lang="ts">
export default {
  name: 'MyComponent',
  inheritAttrs: false,
};
</script>

<script setup lang="ts">
// Composition API logic
</script>
```

### Custom Blocks

```vue
<template>...</template>
<script setup>...</script>

<!-- Documentation block -->
<docs>
# MyComponent

This component does something amazing.

## Usage

```vue
<MyComponent :prop="value" />
```
</docs>

<!-- i18n block -->
<i18n>
{
  "en": { "hello": "Hello" },
  "ja": { "hello": "こんにちは" }
}
</i18n>
```

## Best Practices

1. **Use script setup** - Cleaner, better performance
2. **Type everything** - Use lang="ts"
3. **Scope styles** - Prevent leakage
4. **Organize blocks** - script, template, style order
5. **Use semantic HTML** - Proper elements in template
