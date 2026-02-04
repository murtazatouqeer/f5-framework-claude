---
name: vue-form-handling
description: Form handling patterns in Vue
applies_to: vue
---

# Vue Form Handling

## Overview

This guide covers form handling patterns in Vue 3 without
external validation libraries.

## Basic Form

```vue
<script setup lang="ts">
import { ref, computed } from 'vue';

// Form state
const form = ref({
  name: '',
  email: '',
  message: '',
});

// Errors
const errors = ref<Record<string, string>>({});

// Submission state
const isSubmitting = ref(false);
const isSubmitted = ref(false);

// Validation
function validate(): boolean {
  errors.value = {};

  if (!form.value.name.trim()) {
    errors.value.name = 'Name is required';
  }

  if (!form.value.email.trim()) {
    errors.value.email = 'Email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.value.email)) {
    errors.value.email = 'Invalid email format';
  }

  if (!form.value.message.trim()) {
    errors.value.message = 'Message is required';
  } else if (form.value.message.length < 10) {
    errors.value.message = 'Message must be at least 10 characters';
  }

  return Object.keys(errors.value).length === 0;
}

// Submit handler
async function handleSubmit() {
  if (!validate()) return;

  isSubmitting.value = true;

  try {
    await submitForm(form.value);
    isSubmitted.value = true;
    resetForm();
  } catch (error) {
    errors.value.submit = 'Submission failed. Please try again.';
  } finally {
    isSubmitting.value = false;
  }
}

// Reset
function resetForm() {
  form.value = { name: '', email: '', message: '' };
  errors.value = {};
}

// Computed
const isValid = computed(() => Object.keys(errors.value).length === 0);
const isDirty = computed(() =>
  Object.values(form.value).some((v) => v.trim() !== '')
);
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div class="form-field">
      <label for="name">Name</label>
      <input
        id="name"
        v-model="form.name"
        type="text"
        :class="{ 'is-invalid': errors.name }"
      />
      <span v-if="errors.name" class="error">{{ errors.name }}</span>
    </div>

    <div class="form-field">
      <label for="email">Email</label>
      <input
        id="email"
        v-model="form.email"
        type="email"
        :class="{ 'is-invalid': errors.email }"
      />
      <span v-if="errors.email" class="error">{{ errors.email }}</span>
    </div>

    <div class="form-field">
      <label for="message">Message</label>
      <textarea
        id="message"
        v-model="form.message"
        rows="4"
        :class="{ 'is-invalid': errors.message }"
      />
      <span v-if="errors.message" class="error">{{ errors.message }}</span>
    </div>

    <div v-if="errors.submit" class="error">{{ errors.submit }}</div>

    <div class="form-actions">
      <button type="button" @click="resetForm" :disabled="!isDirty">
        Reset
      </button>
      <button type="submit" :disabled="isSubmitting">
        {{ isSubmitting ? 'Submitting...' : 'Submit' }}
      </button>
    </div>
  </form>
</template>
```

## Form Composable

```typescript
// composables/useForm.ts
import { ref, reactive, computed, type Ref } from 'vue';

interface UseFormOptions<T extends Record<string, unknown>> {
  initialValues: T;
  validate?: (values: T) => Partial<Record<keyof T, string>>;
  onSubmit: (values: T) => Promise<void>;
}

export function useForm<T extends Record<string, unknown>>(
  options: UseFormOptions<T>
) {
  const { initialValues, validate, onSubmit } = options;

  // State
  const values = reactive({ ...initialValues }) as T;
  const errors = ref<Partial<Record<keyof T, string>>>({});
  const touched = ref<Partial<Record<keyof T, boolean>>>({});
  const isSubmitting = ref(false);
  const submitCount = ref(0);

  // Computed
  const isValid = computed(() => Object.keys(errors.value).length === 0);
  const isDirty = computed(() => {
    return Object.keys(initialValues).some(
      (key) => values[key as keyof T] !== initialValues[key as keyof T]
    );
  });

  // Methods
  function setFieldValue<K extends keyof T>(field: K, value: T[K]) {
    values[field] = value;
    touched.value[field] = true;
    if (validate) {
      const fieldErrors = validate(values);
      if (fieldErrors[field]) {
        errors.value[field] = fieldErrors[field];
      } else {
        delete errors.value[field];
      }
    }
  }

  function setFieldTouched<K extends keyof T>(field: K) {
    touched.value[field] = true;
  }

  function validateForm(): boolean {
    if (!validate) return true;

    const validationErrors = validate(values);
    errors.value = validationErrors;
    return Object.keys(validationErrors).length === 0;
  }

  async function handleSubmit() {
    submitCount.value++;

    if (!validateForm()) return;

    isSubmitting.value = true;

    try {
      await onSubmit(values);
    } finally {
      isSubmitting.value = false;
    }
  }

  function resetForm() {
    Object.assign(values, initialValues);
    errors.value = {};
    touched.value = {};
    submitCount.value = 0;
  }

  return {
    values,
    errors,
    touched,
    isSubmitting,
    submitCount,
    isValid,
    isDirty,
    setFieldValue,
    setFieldTouched,
    validateForm,
    handleSubmit,
    resetForm,
  };
}
```

## Using the Composable

```vue
<script setup lang="ts">
import { useForm } from '@/composables/useForm';

interface FormValues {
  email: string;
  password: string;
}

const {
  values,
  errors,
  touched,
  isSubmitting,
  isDirty,
  setFieldValue,
  setFieldTouched,
  handleSubmit,
  resetForm,
} = useForm<FormValues>({
  initialValues: {
    email: '',
    password: '',
  },
  validate: (values) => {
    const errors: Partial<Record<keyof FormValues, string>> = {};

    if (!values.email) {
      errors.email = 'Email is required';
    }

    if (!values.password) {
      errors.password = 'Password is required';
    } else if (values.password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }

    return errors;
  },
  onSubmit: async (values) => {
    await login(values);
  },
});
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div>
      <input
        :value="values.email"
        @input="setFieldValue('email', ($event.target as HTMLInputElement).value)"
        @blur="setFieldTouched('email')"
        type="email"
        placeholder="Email"
      />
      <span v-if="touched.email && errors.email">{{ errors.email }}</span>
    </div>

    <div>
      <input
        :value="values.password"
        @input="setFieldValue('password', ($event.target as HTMLInputElement).value)"
        @blur="setFieldTouched('password')"
        type="password"
        placeholder="Password"
      />
      <span v-if="touched.password && errors.password">{{ errors.password }}</span>
    </div>

    <button type="submit" :disabled="isSubmitting">
      {{ isSubmitting ? 'Logging in...' : 'Login' }}
    </button>
  </form>
</template>
```

## Input Components

### Text Input

```vue
<!-- components/forms/FormInput.vue -->
<script setup lang="ts">
interface Props {
  modelValue: string;
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  error?: string;
  touched?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'blur'): void;
}>();
</script>

<template>
  <div class="form-input">
    <label :for="name">{{ label }}</label>
    <input
      :id="name"
      :name="name"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :class="{ 'is-invalid': touched && error }"
      @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      @blur="emit('blur')"
    />
    <span v-if="touched && error" class="error">{{ error }}</span>
  </div>
</template>
```

### Select Input

```vue
<!-- components/forms/FormSelect.vue -->
<script setup lang="ts">
interface Option {
  value: string;
  label: string;
}

interface Props {
  modelValue: string;
  label: string;
  name: string;
  options: Option[];
  placeholder?: string;
  error?: string;
}

defineProps<Props>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();
</script>

<template>
  <div class="form-select">
    <label :for="name">{{ label }}</label>
    <select
      :id="name"
      :value="modelValue"
      :class="{ 'is-invalid': error }"
      @change="emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">
        {{ opt.label }}
      </option>
    </select>
    <span v-if="error" class="error">{{ error }}</span>
  </div>
</template>
```

### Checkbox

```vue
<!-- components/forms/FormCheckbox.vue -->
<script setup lang="ts">
interface Props {
  modelValue: boolean;
  label: string;
  name: string;
  error?: string;
}

defineProps<Props>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();
</script>

<template>
  <div class="form-checkbox">
    <label>
      <input
        type="checkbox"
        :name="name"
        :checked="modelValue"
        @change="emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      />
      {{ label }}
    </label>
    <span v-if="error" class="error">{{ error }}</span>
  </div>
</template>
```

## Best Practices

1. **Validate on blur** - Not on every keystroke
2. **Show errors after touched** - Better UX
3. **Disable submit while submitting** - Prevent double submission
4. **Reset on success** - Clear form state
5. **Handle async errors** - Show server-side errors
6. **Use composables** - Reusable form logic
