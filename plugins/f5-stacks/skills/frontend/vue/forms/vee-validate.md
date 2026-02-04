---
name: vue-vee-validate
description: Form validation with VeeValidate and Zod
applies_to: vue
---

# VeeValidate Forms

## Overview

VeeValidate is a form validation library for Vue.js.
Combined with Zod, it provides type-safe schema validation.

## Setup

```bash
npm install vee-validate @vee-validate/zod zod
```

## Basic Form

```vue
<script setup lang="ts">
import { useForm, useField } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

// Define schema
const schema = toTypedSchema(
  z.object({
    email: z.string().email('Invalid email'),
    password: z.string().min(8, 'Password must be at least 8 characters'),
  })
);

// Setup form
const { handleSubmit, errors, isSubmitting } = useForm({
  validationSchema: schema,
});

// Setup fields
const { value: email } = useField('email');
const { value: password } = useField('password');

// Submit handler
const onSubmit = handleSubmit(async (values) => {
  // values is typed: { email: string; password: string }
  await login(values);
});
</script>

<template>
  <form @submit="onSubmit">
    <div>
      <label for="email">Email</label>
      <input
        id="email"
        v-model="email"
        type="email"
        :class="{ 'is-invalid': errors.email }"
      />
      <span v-if="errors.email" class="error">{{ errors.email }}</span>
    </div>

    <div>
      <label for="password">Password</label>
      <input
        id="password"
        v-model="password"
        type="password"
        :class="{ 'is-invalid': errors.password }"
      />
      <span v-if="errors.password" class="error">{{ errors.password }}</span>
    </div>

    <button type="submit" :disabled="isSubmitting">
      {{ isSubmitting ? 'Submitting...' : 'Submit' }}
    </button>
  </form>
</template>
```

## Field Component

```vue
<script setup lang="ts">
import { Field, Form, ErrorMessage } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

const schema = toTypedSchema(
  z.object({
    name: z.string().min(2),
    email: z.string().email(),
    role: z.enum(['user', 'admin']),
  })
);

function onSubmit(values: any) {
  console.log(values);
}
</script>

<template>
  <Form :validation-schema="schema" @submit="onSubmit">
    <div>
      <label for="name">Name</label>
      <Field id="name" name="name" />
      <ErrorMessage name="name" class="error" />
    </div>

    <div>
      <label for="email">Email</label>
      <Field id="email" name="email" type="email" />
      <ErrorMessage name="email" class="error" />
    </div>

    <div>
      <label for="role">Role</label>
      <Field id="role" name="role" as="select">
        <option value="">Select role</option>
        <option value="user">User</option>
        <option value="admin">Admin</option>
      </Field>
      <ErrorMessage name="role" class="error" />
    </div>

    <button type="submit">Submit</button>
  </Form>
</template>
```

## Advanced Schema

```typescript
import { z } from 'zod';
import { toTypedSchema } from '@vee-validate/zod';

const userSchema = z.object({
  // Basic fields
  name: z.string().min(2, 'Name is required'),
  email: z.string().email('Invalid email'),

  // Optional field
  phone: z.string().optional(),

  // Enum
  role: z.enum(['user', 'admin', 'moderator']),

  // Number
  age: z.number().min(18, 'Must be 18 or older'),

  // Boolean
  acceptTerms: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the terms' }),
  }),

  // Date
  birthDate: z.coerce.date().max(new Date(), 'Invalid date'),

  // Array
  skills: z.array(z.string()).min(1, 'Select at least one skill'),

  // Nested object
  address: z.object({
    street: z.string().min(1),
    city: z.string().min(1),
    zipCode: z.string().regex(/^\d{5}$/, 'Invalid zip code'),
  }),

  // Password confirmation
  password: z.string().min(8),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

const schema = toTypedSchema(userSchema);
```

## Form State Management

```vue
<script setup lang="ts">
import { useForm } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

const schema = toTypedSchema(
  z.object({
    name: z.string().min(2),
    email: z.string().email(),
  })
);

const {
  // Values
  values,
  // Errors
  errors,
  // Meta
  meta,
  // Actions
  handleSubmit,
  resetForm,
  setFieldValue,
  setFieldError,
  setErrors,
  setValues,
  validate,
  validateField,
  // Submission state
  isSubmitting,
  submitCount,
} = useForm({
  validationSchema: schema,
  initialValues: {
    name: '',
    email: '',
  },
});

// Check form state
console.log(meta.value.valid); // Is form valid
console.log(meta.value.dirty); // Has form been modified
console.log(meta.value.touched); // Has any field been touched

// Programmatic operations
function handleReset() {
  resetForm();
}

function handleSetValue() {
  setFieldValue('name', 'John');
}

function handleSetError() {
  setFieldError('email', 'Email already exists');
}

async function handleValidate() {
  const result = await validate();
  if (result.valid) {
    console.log('Form is valid');
  }
}
</script>
```

## Field State

```vue
<script setup lang="ts">
import { useField } from 'vee-validate';

const {
  value,
  errorMessage,
  errors,
  meta,
  handleChange,
  handleBlur,
  handleReset,
  setValue,
  setErrors,
  validate,
} = useField('email');

// Field meta
console.log(meta.value.valid);
console.log(meta.value.dirty);
console.log(meta.value.touched);
console.log(meta.value.pending); // Async validation
</script>

<template>
  <div>
    <input
      :value="value"
      @input="handleChange"
      @blur="handleBlur"
      :class="{ 'is-invalid': meta.touched && !meta.valid }"
    />
    <span v-if="errorMessage">{{ errorMessage }}</span>
  </div>
</template>
```

## Custom Input Components

```vue
<!-- components/forms/TextInput.vue -->
<script setup lang="ts">
import { useField } from 'vee-validate';

interface Props {
  name: string;
  label: string;
  type?: string;
  placeholder?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
});

const { value, errorMessage, handleBlur, meta } = useField(
  () => props.name
);
</script>

<template>
  <div class="form-field">
    <label :for="name">{{ label }}</label>
    <input
      :id="name"
      v-model="value"
      :type="type"
      :placeholder="placeholder"
      :class="{ 'is-invalid': meta.touched && errorMessage }"
      @blur="handleBlur"
    />
    <span v-if="meta.touched && errorMessage" class="error">
      {{ errorMessage }}
    </span>
  </div>
</template>
```

## Form Arrays

```vue
<script setup lang="ts">
import { useForm, useFieldArray } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

const schema = toTypedSchema(
  z.object({
    users: z.array(
      z.object({
        name: z.string().min(1),
        email: z.string().email(),
      })
    ).min(1, 'Add at least one user'),
  })
);

const { handleSubmit, errors } = useForm({
  validationSchema: schema,
  initialValues: {
    users: [{ name: '', email: '' }],
  },
});

const { fields, push, remove, move } = useFieldArray('users');
</script>

<template>
  <form @submit="handleSubmit(onSubmit)">
    <div v-for="(field, idx) in fields" :key="field.key">
      <input
        v-model="field.value.name"
        :name="`users[${idx}].name`"
        placeholder="Name"
      />
      <input
        v-model="field.value.email"
        :name="`users[${idx}].email`"
        placeholder="Email"
      />
      <button type="button" @click="remove(idx)">Remove</button>
    </div>

    <button type="button" @click="push({ name: '', email: '' })">
      Add User
    </button>

    <button type="submit">Submit</button>
  </form>
</template>
```

## Best Practices

1. **Use Zod schemas** - Type safety and validation
2. **Create reusable inputs** - Custom field components
3. **Handle async validation** - Show loading states
4. **Show errors on blur** - Better UX than immediate validation
5. **Provide clear messages** - User-friendly error text
6. **Reset on success** - Clear form after submission
