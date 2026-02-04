---
name: nuxt-ui
description: Nuxt UI component library
applies_to: nuxt
---

# Nuxt UI

## Overview

Nuxt UI is the official component library for Nuxt, built on Tailwind CSS and Headless UI.

## Setup

```bash
npx nuxi@latest module add ui
```

```typescript
// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxt/ui'],

  ui: {
    global: true,
    icons: ['heroicons'],
  },
});
```

## Basic Components

### Buttons

```vue
<template>
  <div class="space-x-2">
    <UButton>Default</UButton>
    <UButton color="primary">Primary</UButton>
    <UButton color="red" variant="outline">Danger</UButton>
    <UButton loading>Loading</UButton>
    <UButton disabled>Disabled</UButton>
    <UButton icon="i-heroicons-plus" />
    <UButton trailing-icon="i-heroicons-arrow-right">
      Next
    </UButton>
  </div>
</template>
```

### Inputs

```vue
<script setup lang="ts">
const email = ref('');
const password = ref('');
</script>

<template>
  <UFormGroup label="Email" required>
    <UInput
      v-model="email"
      type="email"
      placeholder="you@example.com"
      icon="i-heroicons-envelope"
    />
  </UFormGroup>

  <UFormGroup label="Password" required>
    <UInput
      v-model="password"
      type="password"
      placeholder="Enter password"
    />
  </UFormGroup>
</template>
```

### Select

```vue
<script setup lang="ts">
const options = [
  { label: 'Option 1', value: '1' },
  { label: 'Option 2', value: '2' },
  { label: 'Option 3', value: '3' },
];
const selected = ref('');
</script>

<template>
  <USelect
    v-model="selected"
    :options="options"
    placeholder="Select an option"
  />
</template>
```

### Cards

```vue
<template>
  <UCard>
    <template #header>
      <h3 class="font-semibold">Card Title</h3>
    </template>

    <p>Card content goes here.</p>

    <template #footer>
      <UButton color="primary">Action</UButton>
    </template>
  </UCard>
</template>
```

## Form Handling

### With Validation

```vue
<script setup lang="ts">
import { z } from 'zod';
import type { FormSubmitEvent } from '#ui/types';

const schema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Must be at least 8 characters'),
});

type Schema = z.output<typeof schema>;

const state = reactive({
  email: '',
  password: '',
});

async function onSubmit(event: FormSubmitEvent<Schema>) {
  console.log(event.data);
  // Submit to API
}
</script>

<template>
  <UForm :schema="schema" :state="state" @submit="onSubmit">
    <UFormGroup label="Email" name="email">
      <UInput v-model="state.email" />
    </UFormGroup>

    <UFormGroup label="Password" name="password">
      <UInput v-model="state.password" type="password" />
    </UFormGroup>

    <UButton type="submit">Submit</UButton>
  </UForm>
</template>
```

## Navigation

### Tabs

```vue
<script setup lang="ts">
const items = [
  { label: 'Account', icon: 'i-heroicons-user' },
  { label: 'Security', icon: 'i-heroicons-lock-closed' },
  { label: 'Notifications', icon: 'i-heroicons-bell' },
];
</script>

<template>
  <UTabs :items="items">
    <template #item="{ item }">
      <div v-if="item.label === 'Account'">
        Account settings...
      </div>
      <div v-else-if="item.label === 'Security'">
        Security settings...
      </div>
      <div v-else>
        Notification settings...
      </div>
    </template>
  </UTabs>
</template>
```

### Dropdown

```vue
<script setup lang="ts">
const items = [
  [{
    label: 'Profile',
    icon: 'i-heroicons-user',
    click: () => navigateTo('/profile'),
  }],
  [{
    label: 'Settings',
    icon: 'i-heroicons-cog',
    click: () => navigateTo('/settings'),
  }],
  [{
    label: 'Logout',
    icon: 'i-heroicons-arrow-left-on-rectangle',
    click: () => logout(),
  }],
];
</script>

<template>
  <UDropdown :items="items">
    <UButton icon="i-heroicons-user" />
  </UDropdown>
</template>
```

## Data Display

### Table

```vue
<script setup lang="ts">
const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: 'Name' },
  { key: 'email', label: 'Email' },
  { key: 'actions' },
];

const users = ref([
  { id: 1, name: 'John Doe', email: 'john@example.com' },
  { id: 2, name: 'Jane Smith', email: 'jane@example.com' },
]);

const selected = ref([]);
</script>

<template>
  <UTable
    v-model="selected"
    :columns="columns"
    :rows="users"
  >
    <template #actions-data="{ row }">
      <UDropdown :items="getActions(row)">
        <UButton icon="i-heroicons-ellipsis-horizontal" variant="ghost" />
      </UDropdown>
    </template>
  </UTable>
</template>
```

### Pagination

```vue
<script setup lang="ts">
const page = ref(1);
const pageSize = ref(10);
const total = ref(100);
</script>

<template>
  <UPagination
    v-model="page"
    :page-count="pageSize"
    :total="total"
  />
</template>
```

## Feedback

### Toast

```vue
<script setup lang="ts">
const toast = useToast();

function showToast() {
  toast.add({
    title: 'Success!',
    description: 'Your changes have been saved.',
    icon: 'i-heroicons-check-circle',
    color: 'green',
  });
}
</script>

<template>
  <UButton @click="showToast">Show Toast</UButton>
</template>
```

### Modal

```vue
<script setup lang="ts">
const isOpen = ref(false);
</script>

<template>
  <UButton @click="isOpen = true">Open Modal</UButton>

  <UModal v-model="isOpen">
    <UCard>
      <template #header>
        <h3>Modal Title</h3>
      </template>

      <p>Modal content...</p>

      <template #footer>
        <div class="flex justify-end space-x-2">
          <UButton variant="ghost" @click="isOpen = false">
            Cancel
          </UButton>
          <UButton color="primary" @click="handleConfirm">
            Confirm
          </UButton>
        </div>
      </template>
    </UCard>
  </UModal>
</template>
```

### Slideover

```vue
<script setup lang="ts">
const isOpen = ref(false);
</script>

<template>
  <UButton @click="isOpen = true">Open Panel</UButton>

  <USlideover v-model="isOpen">
    <UCard class="h-full">
      <template #header>
        <h3>Panel Title</h3>
      </template>

      <div class="space-y-4">
        <!-- Panel content -->
      </div>
    </UCard>
  </USlideover>
</template>
```

## Theming

### app.config.ts

```typescript
export default defineAppConfig({
  ui: {
    primary: 'blue',
    gray: 'slate',

    button: {
      default: {
        size: 'md',
        color: 'primary',
      },
    },

    input: {
      default: {
        size: 'md',
      },
    },

    card: {
      base: 'overflow-hidden',
      ring: 'ring-1 ring-gray-200 dark:ring-gray-800',
    },
  },
});
```

### Component Variants

```vue
<template>
  <UButton
    :ui="{
      rounded: 'rounded-full',
      font: 'font-bold',
    }"
  >
    Custom Button
  </UButton>
</template>
```

## Dark Mode

```vue
<script setup lang="ts">
const colorMode = useColorMode();
</script>

<template>
  <UButton
    :icon="colorMode.value === 'dark' ? 'i-heroicons-sun' : 'i-heroicons-moon'"
    @click="colorMode.preference = colorMode.value === 'dark' ? 'light' : 'dark'"
  />
</template>
```

## Best Practices

1. **Use form validation** - Integrate Zod with UForm
2. **Leverage icons** - Heroicons are included
3. **Customize via app.config** - Global theming
4. **Use composables** - useToast, useModal
5. **Dark mode built-in** - Works out of the box
6. **Accessible** - Built on Headless UI
