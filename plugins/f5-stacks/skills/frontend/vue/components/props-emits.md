---
name: vue-props-emits
description: Vue props and emits patterns with TypeScript
applies_to: vue
---

# Vue Props and Emits

## Overview

Props and emits are Vue's primary mechanisms for component communication.
Props flow data down, emits flow events up.

## Defining Props

### TypeScript Interface Pattern

```vue
<script setup lang="ts">
// Define interface
interface Props {
  /** User ID - required */
  id: string;
  /** User name - required */
  name: string;
  /** User email - optional */
  email?: string;
  /** Is active - optional with default */
  isActive?: boolean;
  /** Role - union type */
  role?: 'admin' | 'user' | 'guest';
  /** Complex type */
  metadata?: Record<string, unknown>;
}

// Define with defaults
const props = withDefaults(defineProps<Props>(), {
  isActive: true,
  role: 'user',
});

// Access props
console.log(props.id);
console.log(props.isActive); // true if not provided
</script>
```

### Runtime Declaration (Alternative)

```vue
<script setup lang="ts">
import type { PropType } from 'vue';

interface User {
  id: string;
  name: string;
}

// Runtime declaration with PropType
const props = defineProps({
  user: {
    type: Object as PropType<User>,
    required: true,
  },
  items: {
    type: Array as PropType<string[]>,
    default: () => [],
  },
  status: {
    type: String as PropType<'pending' | 'active' | 'done'>,
    default: 'pending',
    validator: (value: string) => {
      return ['pending', 'active', 'done'].includes(value);
    },
  },
});
</script>
```

## Defining Emits

### TypeScript Interface Pattern

```vue
<script setup lang="ts">
// Define emits with payload types
interface Emits {
  (e: 'click'): void;
  (e: 'update', value: string): void;
  (e: 'submit', data: { id: string; values: FormData }): void;
  (e: 'delete', id: string, confirm: boolean): void;
}

const emit = defineEmits<Emits>();

// Usage
function handleClick() {
  emit('click');
}

function handleUpdate(value: string) {
  emit('update', value);
}

function handleSubmit(data: FormData) {
  emit('submit', { id: '123', values: data });
}
</script>
```

### Runtime Declaration (Alternative)

```vue
<script setup lang="ts">
const emit = defineEmits({
  // No validation
  click: null,

  // With validation
  submit: (payload: { email: string }) => {
    if (payload.email && payload.email.includes('@')) {
      return true;
    }
    console.warn('Invalid submit event payload!');
    return false;
  },
});
</script>
```

## v-model Pattern

### Single v-model

```vue
<!-- Child: TextInput.vue -->
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
  <input
    :value="modelValue"
    @input="handleInput"
    type="text"
  />
</template>
```

```vue
<!-- Parent usage -->
<script setup lang="ts">
import { ref } from 'vue';
import TextInput from './TextInput.vue';

const name = ref('');
</script>

<template>
  <TextInput v-model="name" />
  <!-- Equivalent to: -->
  <TextInput :modelValue="name" @update:modelValue="name = $event" />
</template>
```

### Multiple v-models

```vue
<!-- Child: UserForm.vue -->
<script setup lang="ts">
interface Props {
  firstName: string;
  lastName: string;
  email: string;
}

interface Emits {
  (e: 'update:firstName', value: string): void;
  (e: 'update:lastName', value: string): void;
  (e: 'update:email', value: string): void;
}

defineProps<Props>();
const emit = defineEmits<Emits>();
</script>

<template>
  <input
    :value="firstName"
    @input="emit('update:firstName', ($event.target as HTMLInputElement).value)"
  />
  <input
    :value="lastName"
    @input="emit('update:lastName', ($event.target as HTMLInputElement).value)"
  />
  <input
    :value="email"
    @input="emit('update:email', ($event.target as HTMLInputElement).value)"
  />
</template>
```

```vue
<!-- Parent usage -->
<template>
  <UserForm
    v-model:firstName="user.firstName"
    v-model:lastName="user.lastName"
    v-model:email="user.email"
  />
</template>
```

### v-model with Modifiers

```vue
<!-- Child: CustomInput.vue -->
<script setup lang="ts">
interface Props {
  modelValue: string;
  modelModifiers?: {
    capitalize?: boolean;
    uppercase?: boolean;
  };
}

const props = withDefaults(defineProps<Props>(), {
  modelModifiers: () => ({}),
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();

function handleInput(event: Event) {
  let value = (event.target as HTMLInputElement).value;

  if (props.modelModifiers.capitalize) {
    value = value.charAt(0).toUpperCase() + value.slice(1);
  }
  if (props.modelModifiers.uppercase) {
    value = value.toUpperCase();
  }

  emit('update:modelValue', value);
}
</script>

<template>
  <input :value="modelValue" @input="handleInput" />
</template>
```

```vue
<!-- Usage with modifiers -->
<CustomInput v-model.capitalize="name" />
<CustomInput v-model.uppercase="code" />
```

## Props Patterns

### Boolean Props

```vue
<script setup lang="ts">
interface Props {
  disabled?: boolean;
  loading?: boolean;
  visible?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
  loading: false,
  visible: true,
});
</script>

<!-- Usage -->
<!-- All equivalent ways to pass true -->
<MyComponent disabled />
<MyComponent :disabled="true" />

<!-- Explicit false -->
<MyComponent :disabled="false" />

<!-- Omitted = default value -->
<MyComponent />
```

### Object/Array Props

```vue
<script setup lang="ts">
interface User {
  id: string;
  name: string;
}

interface Props {
  user: User;
  items: string[];
  config: Record<string, unknown>;
}

// IMPORTANT: Use factory functions for defaults
const props = withDefaults(defineProps<Props>(), {
  items: () => [],
  config: () => ({}),
});
</script>
```

### Union Type Props

```vue
<script setup lang="ts">
type Size = 'sm' | 'md' | 'lg' | 'xl';
type Variant = 'primary' | 'secondary' | 'danger' | 'ghost';

interface Props {
  size?: Size;
  variant?: Variant;
}

const props = withDefaults(defineProps<Props>(), {
  size: 'md',
  variant: 'primary',
});
</script>
```

### Generic Props

```vue
<script setup lang="ts" generic="T extends { id: string }">
interface Props {
  items: T[];
  selected?: T;
}

interface Emits {
  (e: 'select', item: T): void;
}

defineProps<Props>();
defineEmits<Emits>();
</script>

<!-- Usage -->
<GenericList
  :items="users"
  @select="handleSelect"
/>
```

## Emits Patterns

### Event with Validation

```vue
<script setup lang="ts">
interface SubmitPayload {
  email: string;
  password: string;
}

interface Emits {
  (e: 'submit', payload: SubmitPayload): void;
}

const emit = defineEmits<Emits>();

function handleSubmit(data: SubmitPayload) {
  // Validate before emitting
  if (!data.email || !data.password) {
    console.error('Invalid form data');
    return;
  }
  emit('submit', data);
}
</script>
```

### Async Event Handler

```vue
<script setup lang="ts">
interface Emits {
  (e: 'delete', id: string): void;
}

const emit = defineEmits<Emits>();

async function handleDelete(id: string) {
  const confirmed = await showConfirmDialog('Delete this item?');
  if (confirmed) {
    emit('delete', id);
  }
}
</script>
```

## Best Practices

1. **Use TypeScript interfaces** - Better type safety
2. **Document props with JSDoc** - IDE support
3. **Use withDefaults** - Type-safe defaults
4. **Validate complex props** - Runtime checks
5. **Emit typed events** - Consistent payloads
6. **Avoid mutating props** - One-way data flow
