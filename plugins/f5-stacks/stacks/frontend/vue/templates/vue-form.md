---
name: vue-form
description: Vue form component template with validation
applies_to: vue
variables:
  - name: formName
    description: Form component name
  - name: fields
    description: Form field definitions
---

# Vue Form Template

## Basic Form

```vue
<script setup lang="ts">
// ============================================================
// components/{{formName}}Form.vue
// ============================================================

import { ref, computed } from 'vue';

// ------------------------------------------------------------
// Types
// ------------------------------------------------------------
interface FormData {
  // Define form fields
  // name: string;
  // email: string;
}

interface FormErrors {
  [key: string]: string | undefined;
}

// ------------------------------------------------------------
// Props & Emits
// ------------------------------------------------------------
interface Props {
  initialValues?: Partial<FormData>;
  submitLabel?: string;
}

const props = withDefaults(defineProps<Props>(), {
  submitLabel: 'Submit',
});

const emit = defineEmits<{
  (e: 'submit', data: FormData): void;
  (e: 'cancel'): void;
}>();

// ------------------------------------------------------------
// State
// ------------------------------------------------------------
const form = ref<FormData>({
  // Initialize with defaults or initial values
  // name: props.initialValues?.name ?? '',
  // email: props.initialValues?.email ?? '',
});

const errors = ref<FormErrors>({});
const touched = ref<Record<string, boolean>>({});
const isSubmitting = ref(false);

// ------------------------------------------------------------
// Computed
// ------------------------------------------------------------
const isValid = computed(() => {
  return Object.keys(errors.value).length === 0;
});

const isDirty = computed(() => {
  // Check if form has been modified
  return Object.values(form.value).some(v => v !== '');
});

// ------------------------------------------------------------
// Validation
// ------------------------------------------------------------
function validate(): boolean {
  errors.value = {};

  // Add validation rules
  // if (!form.value.name.trim()) {
  //   errors.value.name = 'Name is required';
  // }

  // if (!form.value.email.trim()) {
  //   errors.value.email = 'Email is required';
  // } else if (!/\S+@\S+\.\S+/.test(form.value.email)) {
  //   errors.value.email = 'Invalid email format';
  // }

  return Object.keys(errors.value).length === 0;
}

function validateField(field: keyof FormData) {
  // Field-level validation
  delete errors.value[field];

  // Add field-specific validation
  // switch (field) {
  //   case 'name':
  //     if (!form.value.name.trim()) {
  //       errors.value.name = 'Name is required';
  //     }
  //     break;
  // }
}

// ------------------------------------------------------------
// Event Handlers
// ------------------------------------------------------------
function handleBlur(field: keyof FormData) {
  touched.value[field] = true;
  validateField(field);
}

async function handleSubmit() {
  // Mark all fields as touched
  Object.keys(form.value).forEach(key => {
    touched.value[key] = true;
  });

  if (!validate()) {
    return;
  }

  isSubmitting.value = true;

  try {
    emit('submit', { ...form.value });
  } finally {
    isSubmitting.value = false;
  }
}

function handleCancel() {
  emit('cancel');
}

function resetForm() {
  form.value = {
    // Reset to initial values
  };
  errors.value = {};
  touched.value = {};
}

// ------------------------------------------------------------
// Expose
// ------------------------------------------------------------
defineExpose({
  resetForm,
  validate,
});
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <!-- Form Fields -->
    <div class="form__body">
      <!-- Example field structure -->
      <!--
      <div class="form-field">
        <label for="name" class="form-field__label">
          Name <span class="required">*</span>
        </label>
        <input
          id="name"
          v-model="form.name"
          type="text"
          class="form-field__input"
          :class="{ 'is-invalid': touched.name && errors.name }"
          @blur="handleBlur('name')"
        />
        <span v-if="touched.name && errors.name" class="form-field__error">
          {{ errors.name }}
        </span>
      </div>
      -->
    </div>

    <!-- Form Actions -->
    <div class="form__actions">
      <button
        type="button"
        class="btn btn--secondary"
        @click="handleCancel"
      >
        Cancel
      </button>
      <button
        type="submit"
        class="btn btn--primary"
        :disabled="isSubmitting"
      >
        {{ isSubmitting ? 'Submitting...' : submitLabel }}
      </button>
    </div>
  </form>
</template>

<style scoped>
.form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form__body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

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

.form-field__label .required {
  color: #ef4444;
}

.form-field__input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-size: 1rem;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-field__input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-field__input.is-invalid {
  border-color: #ef4444;
}

.form-field__error {
  font-size: 0.75rem;
  color: #ef4444;
}

.form__actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.btn {
  padding: 0.5rem 1rem;
  border-radius: 0.375rem;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.btn--primary {
  background-color: #3b82f6;
  color: white;
  border: none;
}

.btn--primary:hover:not(:disabled) {
  background-color: #2563eb;
}

.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn--secondary {
  background-color: white;
  color: #374151;
  border: 1px solid #d1d5db;
}

.btn--secondary:hover {
  background-color: #f9fafb;
}
</style>
```

## Form with VeeValidate + Zod

```vue
<script setup lang="ts">
// ============================================================
// components/{{formName}}Form.vue (VeeValidate + Zod)
// ============================================================

import { useForm, useField } from 'vee-validate';
import { toTypedSchema } from '@vee-validate/zod';
import { z } from 'zod';

// ------------------------------------------------------------
// Schema
// ------------------------------------------------------------
const schema = toTypedSchema(
  z.object({
    name: z.string()
      .min(1, 'Name is required')
      .min(2, 'Name must be at least 2 characters'),
    email: z.string()
      .min(1, 'Email is required')
      .email('Invalid email format'),
    password: z.string()
      .min(1, 'Password is required')
      .min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string()
      .min(1, 'Please confirm your password'),
  }).refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })
);

// ------------------------------------------------------------
// Props & Emits
// ------------------------------------------------------------
const emit = defineEmits<{
  (e: 'submit', data: { name: string; email: string; password: string }): void;
  (e: 'cancel'): void;
}>();

// ------------------------------------------------------------
// Form Setup
// ------------------------------------------------------------
const { handleSubmit, errors, isSubmitting, resetForm } = useForm({
  validationSchema: schema,
  initialValues: {
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
  },
});

// Field Setup
const { value: name } = useField('name');
const { value: email } = useField('email');
const { value: password } = useField('password');
const { value: confirmPassword } = useField('confirmPassword');

// ------------------------------------------------------------
// Handlers
// ------------------------------------------------------------
const onSubmit = handleSubmit((values) => {
  emit('submit', {
    name: values.name,
    email: values.email,
    password: values.password,
  });
});

function handleCancel() {
  resetForm();
  emit('cancel');
}

// ------------------------------------------------------------
// Expose
// ------------------------------------------------------------
defineExpose({
  resetForm,
});
</script>

<template>
  <form class="form" @submit="onSubmit">
    <div class="form__body">
      <!-- Name -->
      <div class="form-field">
        <label for="name" class="form-field__label">
          Name <span class="required">*</span>
        </label>
        <input
          id="name"
          v-model="name"
          type="text"
          class="form-field__input"
          :class="{ 'is-invalid': errors.name }"
        />
        <span v-if="errors.name" class="form-field__error">
          {{ errors.name }}
        </span>
      </div>

      <!-- Email -->
      <div class="form-field">
        <label for="email" class="form-field__label">
          Email <span class="required">*</span>
        </label>
        <input
          id="email"
          v-model="email"
          type="email"
          class="form-field__input"
          :class="{ 'is-invalid': errors.email }"
        />
        <span v-if="errors.email" class="form-field__error">
          {{ errors.email }}
        </span>
      </div>

      <!-- Password -->
      <div class="form-field">
        <label for="password" class="form-field__label">
          Password <span class="required">*</span>
        </label>
        <input
          id="password"
          v-model="password"
          type="password"
          class="form-field__input"
          :class="{ 'is-invalid': errors.password }"
        />
        <span v-if="errors.password" class="form-field__error">
          {{ errors.password }}
        </span>
      </div>

      <!-- Confirm Password -->
      <div class="form-field">
        <label for="confirmPassword" class="form-field__label">
          Confirm Password <span class="required">*</span>
        </label>
        <input
          id="confirmPassword"
          v-model="confirmPassword"
          type="password"
          class="form-field__input"
          :class="{ 'is-invalid': errors.confirmPassword }"
        />
        <span v-if="errors.confirmPassword" class="form-field__error">
          {{ errors.confirmPassword }}
        </span>
      </div>
    </div>

    <div class="form__actions">
      <button type="button" class="btn btn--secondary" @click="handleCancel">
        Cancel
      </button>
      <button type="submit" class="btn btn--primary" :disabled="isSubmitting">
        {{ isSubmitting ? 'Submitting...' : 'Submit' }}
      </button>
    </div>
  </form>
</template>
```

## Usage

```vue
<script setup lang="ts">
import {{formName}}Form from '@/components/{{formName}}Form.vue';

function handleSubmit(data: FormData) {
  console.log('Form submitted:', data);
  // Process form data
}

function handleCancel() {
  console.log('Form cancelled');
  // Handle cancellation
}
</script>

<template>
  <{{formName}}Form
    :initial-values="{ name: 'John' }"
    submit-label="Save"
    @submit="handleSubmit"
    @cancel="handleCancel"
  />
</template>
```
