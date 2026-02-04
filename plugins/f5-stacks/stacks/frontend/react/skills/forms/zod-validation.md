# Zod Validation

## Overview

TypeScript-first schema validation with static type inference.

## Basic Schemas

```tsx
import { z } from 'zod';

// Primitives
const stringSchema = z.string();
const numberSchema = z.number();
const booleanSchema = z.boolean();
const dateSchema = z.date();

// With constraints
const emailSchema = z.string().email('Invalid email');
const ageSchema = z.number().min(18, 'Must be 18+').max(120);
const urlSchema = z.string().url('Invalid URL');
const uuidSchema = z.string().uuid('Invalid ID');

// Optional and nullable
const optionalString = z.string().optional(); // string | undefined
const nullableString = z.string().nullable(); // string | null
const nullishString = z.string().nullish(); // string | null | undefined
```

## Object Schemas

```tsx
// Basic object
const userSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().min(2).max(100),
  age: z.number().int().positive().optional(),
  role: z.enum(['admin', 'user', 'guest']),
  createdAt: z.date(),
});

// Infer TypeScript type
type User = z.infer<typeof userSchema>;
// { id: string; email: string; name: string; age?: number; role: 'admin' | 'user' | 'guest'; createdAt: Date }

// Partial (all optional)
const partialUserSchema = userSchema.partial();

// Pick specific fields
const userCredentialsSchema = userSchema.pick({ email: true, name: true });

// Omit fields
const userWithoutIdSchema = userSchema.omit({ id: true, createdAt: true });

// Extend object
const adminSchema = userSchema.extend({
  permissions: z.array(z.string()),
  department: z.string(),
});

// Merge objects
const profileSchema = z.object({ bio: z.string(), avatar: z.string().url() });
const fullUserSchema = userSchema.merge(profileSchema);
```

## Array Schemas

```tsx
// Basic array
const stringsSchema = z.array(z.string());

// With constraints
const tagsSchema = z
  .array(z.string().min(1))
  .min(1, 'At least one tag required')
  .max(10, 'Maximum 10 tags');

// Non-empty array
const nonEmptyArray = z.array(z.string()).nonempty('Array cannot be empty');

// Tuple (fixed length, different types)
const coordinatesSchema = z.tuple([z.number(), z.number()]);
const namedTupleSchema = z.tuple([
  z.string(), // name
  z.number(), // age
  z.boolean(), // active
]);
```

## Union and Discriminated Unions

```tsx
// Simple union
const stringOrNumber = z.union([z.string(), z.number()]);

// Discriminated union (more efficient)
const eventSchema = z.discriminatedUnion('type', [
  z.object({
    type: z.literal('click'),
    x: z.number(),
    y: z.number(),
  }),
  z.object({
    type: z.literal('keypress'),
    key: z.string(),
  }),
  z.object({
    type: z.literal('scroll'),
    direction: z.enum(['up', 'down']),
  }),
]);

type Event = z.infer<typeof eventSchema>;
// { type: 'click'; x: number; y: number } | { type: 'keypress'; key: string } | { type: 'scroll'; direction: 'up' | 'down' }
```

## Refinements and Transforms

```tsx
// Custom validation
const passwordSchema = z
  .string()
  .min(8, 'Password must be at least 8 characters')
  .refine((val) => /[A-Z]/.test(val), {
    message: 'Password must contain uppercase letter',
  })
  .refine((val) => /[a-z]/.test(val), {
    message: 'Password must contain lowercase letter',
  })
  .refine((val) => /[0-9]/.test(val), {
    message: 'Password must contain number',
  });

// Transform input
const trimmedString = z.string().trim();
const lowercaseEmail = z.string().email().toLowerCase();
const numberFromString = z.string().transform((val) => parseInt(val, 10));

// Coerce types
const coercedNumber = z.coerce.number(); // "42" -> 42
const coercedDate = z.coerce.date(); // "2024-01-01" -> Date
const coercedBoolean = z.coerce.boolean(); // "true" -> true

// Preprocess
const preprocessedNumber = z.preprocess(
  (val) => (typeof val === 'string' ? parseInt(val, 10) : val),
  z.number()
);
```

## Form Validation Schemas

```tsx
// Login form
export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
  rememberMe: z.boolean().default(false),
});

export type LoginFormValues = z.infer<typeof loginSchema>;

// Registration form with password confirmation
export const registrationSchema = z
  .object({
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(20, 'Username must be less than 20 characters')
      .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
    email: z.string().email('Invalid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        'Password must contain uppercase, lowercase, and number'
      ),
    confirmPassword: z.string(),
    acceptTerms: z.literal(true, {
      errorMap: () => ({ message: 'You must accept the terms' }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

export type RegistrationFormValues = z.infer<typeof registrationSchema>;

// Product form
export const productSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  description: z.string().max(500, 'Description too long').optional(),
  price: z.number().positive('Price must be positive'),
  category: z.enum(['electronics', 'clothing', 'food', 'other']),
  tags: z.array(z.string()).max(5, 'Maximum 5 tags'),
  inStock: z.boolean(),
  quantity: z.number().int().min(0).optional(),
  images: z
    .array(z.string().url())
    .min(1, 'At least one image required')
    .max(10, 'Maximum 10 images'),
});

export type ProductFormValues = z.infer<typeof productSchema>;
```

## Async Validation

```tsx
// Check if username is available
const usernameSchema = z
  .string()
  .min(3)
  .refine(async (username) => {
    const response = await fetch(`/api/check-username?username=${username}`);
    const { available } = await response.json();
    return available;
  }, 'Username is already taken');

// Validate with external API
const addressSchema = z
  .object({
    street: z.string(),
    city: z.string(),
    zipCode: z.string(),
    country: z.string(),
  })
  .refine(
    async (address) => {
      const isValid = await validateAddressWithAPI(address);
      return isValid;
    },
    { message: 'Invalid address' }
  );
```

## Error Handling

```tsx
import { z, ZodError } from 'zod';

const schema = z.object({
  email: z.string().email(),
  age: z.number().min(18),
});

// Parse with error handling
function validateUser(data: unknown) {
  try {
    return schema.parse(data);
  } catch (error) {
    if (error instanceof ZodError) {
      // Formatted errors
      console.log(error.format());
      // { email: { _errors: ['Invalid email'] }, age: { _errors: ['...'] } }

      // Flat errors
      console.log(error.flatten());
      // { formErrors: [], fieldErrors: { email: ['...'], age: ['...'] } }

      // All issues
      console.log(error.issues);
      // [{ code: 'invalid_type', path: ['email'], message: '...' }, ...]
    }
    throw error;
  }
}

// Safe parse (no throw)
function safeValidateUser(data: unknown) {
  const result = schema.safeParse(data);

  if (result.success) {
    return { data: result.data, error: null };
  } else {
    return { data: null, error: result.error };
  }
}
```

## Custom Error Messages

```tsx
// Global error map
z.setErrorMap((issue, ctx) => {
  if (issue.code === z.ZodIssueCode.too_small) {
    return { message: `Minimum ${issue.minimum} characters required` };
  }
  return { message: ctx.defaultError };
});

// Per-schema error map
const schema = z.string().min(5, {
  message: 'Custom error message',
});

// Complex custom errors
const formSchema = z.object({
  email: z.string({
    required_error: 'Email is required',
    invalid_type_error: 'Email must be a string',
  }).email({
    message: 'Please enter a valid email',
  }),
});
```

## Best Practices

1. **Create reusable schemas** - Export and compose schemas
2. **Use z.infer** - Get TypeScript types from schemas
3. **Handle errors gracefully** - Use safeParse for user input
4. **Coerce when needed** - Handle string inputs from forms
5. **Validate early** - At API boundaries and form submission
6. **Keep schemas close to usage** - Colocate with forms/API handlers
