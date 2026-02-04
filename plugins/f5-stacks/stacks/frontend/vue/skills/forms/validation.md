---
name: vue-validation
description: Form validation patterns and Zod schemas
applies_to: vue
---

# Form Validation

## Overview

Form validation ensures data integrity and provides user feedback.
This guide covers validation patterns using Zod and custom validation.

## Zod Schema Validation

### Basic Schemas

```typescript
import { z } from 'zod';

// String validations
const nameSchema = z.string()
  .min(2, 'Name must be at least 2 characters')
  .max(50, 'Name must be less than 50 characters')
  .regex(/^[a-zA-Z\s]+$/, 'Name can only contain letters');

// Email
const emailSchema = z.string()
  .email('Invalid email address')
  .toLowerCase();

// Password with requirements
const passwordSchema = z.string()
  .min(8, 'Password must be at least 8 characters')
  .regex(/[A-Z]/, 'Password must contain an uppercase letter')
  .regex(/[a-z]/, 'Password must contain a lowercase letter')
  .regex(/[0-9]/, 'Password must contain a number')
  .regex(/[^A-Za-z0-9]/, 'Password must contain a special character');

// Number
const ageSchema = z.number()
  .int('Age must be a whole number')
  .min(18, 'Must be 18 or older')
  .max(120, 'Invalid age');

// Date
const birthDateSchema = z.coerce.date()
  .max(new Date(), 'Birth date cannot be in the future');

// URL
const websiteSchema = z.string()
  .url('Invalid URL')
  .optional();

// Phone
const phoneSchema = z.string()
  .regex(/^\+?[\d\s-]{10,}$/, 'Invalid phone number')
  .optional()
  .or(z.literal(''));
```

### Object Schemas

```typescript
import { z } from 'zod';

// User registration schema
export const registrationSchema = z.object({
  name: z.string().min(2).max(50),
  email: z.string().email(),
  password: z.string().min(8),
  confirmPassword: z.string(),
  age: z.coerce.number().min(18).optional(),
  acceptTerms: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the terms' }),
  }),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

// Profile update schema
export const profileSchema = z.object({
  displayName: z.string().min(2).max(30),
  bio: z.string().max(500).optional(),
  website: z.string().url().optional().or(z.literal('')),
  location: z.string().max(100).optional(),
  socialLinks: z.object({
    twitter: z.string().optional(),
    github: z.string().optional(),
    linkedin: z.string().optional(),
  }).optional(),
});

// Type inference
type RegistrationData = z.infer<typeof registrationSchema>;
type ProfileData = z.infer<typeof profileSchema>;
```

### Array and Nested Schemas

```typescript
import { z } from 'zod';

// Array of items
const tagsSchema = z.array(z.string())
  .min(1, 'Select at least one tag')
  .max(5, 'Maximum 5 tags');

// Array of objects
const addressesSchema = z.array(
  z.object({
    type: z.enum(['home', 'work', 'other']),
    street: z.string().min(1),
    city: z.string().min(1),
    state: z.string().min(1),
    zipCode: z.string().regex(/^\d{5}(-\d{4})?$/),
    isDefault: z.boolean(),
  })
).min(1, 'At least one address is required');

// Order form with items
const orderSchema = z.object({
  customer: z.object({
    name: z.string().min(1),
    email: z.string().email(),
    phone: z.string().optional(),
  }),
  items: z.array(
    z.object({
      productId: z.string(),
      quantity: z.number().min(1).max(100),
      notes: z.string().optional(),
    })
  ).min(1, 'Order must have at least one item'),
  shippingAddress: z.object({
    street: z.string().min(1),
    city: z.string().min(1),
    zipCode: z.string(),
  }),
  billingAddress: z.object({
    street: z.string().min(1),
    city: z.string().min(1),
    zipCode: z.string(),
  }).optional(),
  useSameAddress: z.boolean(),
}).refine(
  (data) => data.useSameAddress || data.billingAddress,
  {
    message: 'Billing address is required',
    path: ['billingAddress'],
  }
);
```

### Conditional Validation

```typescript
import { z } from 'zod';

// Discriminated union
const paymentSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('credit_card'),
    cardNumber: z.string().regex(/^\d{16}$/),
    expiryDate: z.string().regex(/^\d{2}\/\d{2}$/),
    cvv: z.string().regex(/^\d{3,4}$/),
  }),
  z.object({
    type: z.literal('bank_transfer'),
    accountNumber: z.string().min(10),
    routingNumber: z.string().length(9),
  }),
  z.object({
    type: z.literal('paypal'),
    email: z.string().email(),
  }),
]);

// Conditional with refine
const shippingSchema = z.object({
  method: z.enum(['standard', 'express', 'pickup']),
  address: z.string().optional(),
  pickupLocation: z.string().optional(),
}).refine(
  (data) => {
    if (data.method === 'pickup') {
      return !!data.pickupLocation;
    }
    return !!data.address;
  },
  {
    message: 'Address or pickup location is required',
  }
);
```

## Validation Helpers

### Validation Composable

```typescript
// composables/useValidation.ts
import { ref, computed } from 'vue';
import { z, type ZodSchema, type ZodError } from 'zod';

export function useValidation<T extends Record<string, unknown>>(
  schema: ZodSchema<T>
) {
  const errors = ref<Partial<Record<keyof T, string>>>({});

  function validate(data: unknown): data is T {
    try {
      schema.parse(data);
      errors.value = {};
      return true;
    } catch (e) {
      if (e instanceof z.ZodError) {
        errors.value = formatZodErrors(e);
      }
      return false;
    }
  }

  function validateField(field: keyof T, value: unknown) {
    const fieldSchema = schema.shape[field as string];
    if (!fieldSchema) return true;

    try {
      fieldSchema.parse(value);
      delete errors.value[field];
      return true;
    } catch (e) {
      if (e instanceof z.ZodError) {
        errors.value[field] = e.errors[0]?.message;
      }
      return false;
    }
  }

  function formatZodErrors(error: ZodError): Partial<Record<keyof T, string>> {
    const formatted: Partial<Record<keyof T, string>> = {};

    error.errors.forEach((err) => {
      const path = err.path[0] as keyof T;
      if (!formatted[path]) {
        formatted[path] = err.message;
      }
    });

    return formatted;
  }

  function clearErrors() {
    errors.value = {};
  }

  const isValid = computed(() => Object.keys(errors.value).length === 0);

  return {
    errors,
    isValid,
    validate,
    validateField,
    clearErrors,
  };
}
```

### Custom Validators

```typescript
// lib/validators.ts
import { z } from 'zod';

// Credit card validation
export const creditCardSchema = z.string()
  .transform((val) => val.replace(/\s/g, ''))
  .refine((val) => /^\d{13,19}$/.test(val), 'Invalid card number')
  .refine((val) => luhnCheck(val), 'Invalid card number');

function luhnCheck(cardNumber: string): boolean {
  let sum = 0;
  let isEven = false;

  for (let i = cardNumber.length - 1; i >= 0; i--) {
    let digit = parseInt(cardNumber[i], 10);

    if (isEven) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }

    sum += digit;
    isEven = !isEven;
  }

  return sum % 10 === 0;
}

// File validation
export const imageFileSchema = z.custom<File>()
  .refine((file) => file instanceof File, 'Please select a file')
  .refine((file) => file.size <= 5 * 1024 * 1024, 'File must be less than 5MB')
  .refine(
    (file) => ['image/jpeg', 'image/png', 'image/webp'].includes(file.type),
    'File must be JPEG, PNG, or WebP'
  );

// Async validation (email uniqueness)
export async function validateUniqueEmail(email: string): Promise<boolean> {
  const response = await fetch(`/api/check-email?email=${email}`);
  const { available } = await response.json();
  return available;
}
```

## Error Display Patterns

### Error Message Component

```vue
<!-- components/forms/ErrorMessage.vue -->
<script setup lang="ts">
interface Props {
  message?: string;
  show?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  show: true,
});
</script>

<template>
  <transition name="error-fade">
    <p v-if="show && message" class="error-message" role="alert">
      {{ message }}
    </p>
  </transition>
</template>

<style scoped>
.error-message {
  color: var(--color-error);
  font-size: 0.875rem;
  margin-top: 0.25rem;
}

.error-fade-enter-active,
.error-fade-leave-active {
  transition: opacity 0.2s ease;
}

.error-fade-enter-from,
.error-fade-leave-to {
  opacity: 0;
}
</style>
```

## Best Practices

1. **Use Zod for schemas** - Type-safe, composable
2. **Validate on blur** - Better UX than instant validation
3. **Show errors contextually** - Near the field
4. **Provide clear messages** - Actionable error text
5. **Handle async validation** - Email uniqueness, etc.
6. **Reuse schemas** - Create schema library
