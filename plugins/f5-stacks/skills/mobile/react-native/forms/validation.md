---
name: rn-form-validation
description: Form validation patterns with Zod and Yup in React Native
applies_to: react-native
---

# Form Validation

## Zod Integration

### Installation

```bash
npm install zod @hookform/resolvers
```

### Basic Zod Schema

```typescript
// src/features/auth/schemas/loginSchema.ts
import { z } from 'zod';

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Invalid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters'),
});

export type LoginFormData = z.infer<typeof loginSchema>;
```

### Using Zod with React Hook Form

```typescript
// src/features/auth/screens/LoginScreen.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { loginSchema, LoginFormData } from '../schemas/loginSchema';

export function LoginScreen() {
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    // data is fully typed and validated
    console.log(data);
  };

  return (
    <View>
      <FormInput
        control={control}
        name="email"
        label="Email"
        keyboardType="email-address"
        autoCapitalize="none"
      />
      <FormInput
        control={control}
        name="password"
        label="Password"
        secureTextEntry
      />
      <Button onPress={handleSubmit(onSubmit)} disabled={isSubmitting}>
        Sign In
      </Button>
    </View>
  );
}
```

## Complex Zod Schemas

### Registration Schema

```typescript
// src/features/auth/schemas/registerSchema.ts
import { z } from 'zod';

export const registerSchema = z
  .object({
    name: z
      .string()
      .min(1, 'Name is required')
      .min(2, 'Name must be at least 2 characters')
      .max(50, 'Name must be less than 50 characters'),

    email: z
      .string()
      .min(1, 'Email is required')
      .email('Invalid email address'),

    phone: z
      .string()
      .min(1, 'Phone is required')
      .regex(/^\+?[1-9]\d{9,14}$/, 'Invalid phone number'),

    password: z
      .string()
      .min(1, 'Password is required')
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain uppercase letter')
      .regex(/[a-z]/, 'Password must contain lowercase letter')
      .regex(/[0-9]/, 'Password must contain number')
      .regex(/[^A-Za-z0-9]/, 'Password must contain special character'),

    confirmPassword: z.string().min(1, 'Please confirm your password'),

    dateOfBirth: z
      .string()
      .min(1, 'Date of birth is required')
      .refine(
        (date) => {
          const age = calculateAge(new Date(date));
          return age >= 18;
        },
        { message: 'You must be at least 18 years old' }
      ),

    acceptTerms: z.literal(true, {
      errorMap: () => ({ message: 'You must accept the terms' }),
    }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  });

export type RegisterFormData = z.infer<typeof registerSchema>;

function calculateAge(birthday: Date): number {
  const today = new Date();
  let age = today.getFullYear() - birthday.getFullYear();
  const m = today.getMonth() - birthday.getMonth();
  if (m < 0 || (m === 0 && today.getDate() < birthday.getDate())) {
    age--;
  }
  return age;
}
```

### Product Schema

```typescript
// src/features/products/schemas/productSchema.ts
import { z } from 'zod';

const priceSchema = z
  .string()
  .min(1, 'Price is required')
  .refine(
    (val) => !isNaN(parseFloat(val)) && parseFloat(val) >= 0,
    'Price must be a valid positive number'
  )
  .transform((val) => parseFloat(val));

export const productSchema = z.object({
  name: z
    .string()
    .min(1, 'Name is required')
    .max(100, 'Name must be less than 100 characters'),

  description: z
    .string()
    .max(1000, 'Description must be less than 1000 characters')
    .optional(),

  price: priceSchema,

  compareAtPrice: priceSchema.optional(),

  category: z.string().min(1, 'Category is required'),

  tags: z
    .array(z.string())
    .max(10, 'Maximum 10 tags allowed')
    .optional()
    .default([]),

  images: z
    .array(z.string().url('Invalid image URL'))
    .min(1, 'At least one image is required')
    .max(5, 'Maximum 5 images allowed'),

  inventory: z.object({
    quantity: z
      .number()
      .int('Quantity must be a whole number')
      .min(0, 'Quantity cannot be negative'),
    sku: z.string().optional(),
    trackInventory: z.boolean().default(true),
  }),

  status: z.enum(['draft', 'active', 'archived']).default('draft'),
});

export type ProductFormData = z.input<typeof productSchema>;
export type ProductData = z.output<typeof productSchema>;
```

### Address Schema

```typescript
// src/features/checkout/schemas/addressSchema.ts
import { z } from 'zod';

export const addressSchema = z.object({
  firstName: z.string().min(1, 'First name is required'),
  lastName: z.string().min(1, 'Last name is required'),
  addressLine1: z.string().min(1, 'Address is required'),
  addressLine2: z.string().optional(),
  city: z.string().min(1, 'City is required'),
  state: z.string().min(1, 'State is required'),
  postalCode: z
    .string()
    .min(1, 'Postal code is required')
    .regex(/^\d{5}(-\d{4})?$/, 'Invalid postal code'),
  country: z.string().min(1, 'Country is required'),
  phone: z
    .string()
    .min(1, 'Phone is required')
    .regex(/^\+?[\d\s-()]+$/, 'Invalid phone number'),
  isDefault: z.boolean().default(false),
});

export type AddressFormData = z.infer<typeof addressSchema>;
```

## Yup Alternative

### Installation

```bash
npm install yup @hookform/resolvers
```

### Yup Schema

```typescript
// src/features/auth/schemas/loginSchemaYup.ts
import * as yup from 'yup';

export const loginSchemaYup = yup.object({
  email: yup
    .string()
    .required('Email is required')
    .email('Invalid email address'),
  password: yup
    .string()
    .required('Password is required')
    .min(8, 'Password must be at least 8 characters'),
});

export type LoginFormDataYup = yup.InferType<typeof loginSchemaYup>;
```

### Using Yup with React Hook Form

```typescript
import { useForm } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import { loginSchemaYup, LoginFormDataYup } from '../schemas/loginSchemaYup';

export function LoginScreenYup() {
  const { control, handleSubmit } = useForm<LoginFormDataYup>({
    resolver: yupResolver(loginSchemaYup),
  });

  // ... rest of component
}
```

## Custom Validation Functions

```typescript
// src/utils/validators.ts

// Email validation
export const isValidEmail = (email: string): boolean => {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return regex.test(email);
};

// Phone validation (international)
export const isValidPhone = (phone: string): boolean => {
  const regex = /^\+?[1-9]\d{9,14}$/;
  return regex.test(phone.replace(/[\s-()]/g, ''));
};

// Password strength
export const getPasswordStrength = (password: string): {
  score: number;
  label: string;
  color: string;
} => {
  let score = 0;

  if (password.length >= 8) score++;
  if (password.length >= 12) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[a-z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^A-Za-z0-9]/.test(password)) score++;

  const levels = [
    { min: 0, label: 'Very Weak', color: '#FF3B30' },
    { min: 2, label: 'Weak', color: '#FF9500' },
    { min: 3, label: 'Fair', color: '#FFCC00' },
    { min: 4, label: 'Good', color: '#34C759' },
    { min: 5, label: 'Strong', color: '#007AFF' },
  ];

  const level = [...levels].reverse().find((l) => score >= l.min)!;

  return { score, ...level };
};

// Credit card validation (Luhn algorithm)
export const isValidCreditCard = (number: string): boolean => {
  const digits = number.replace(/\D/g, '');
  if (digits.length < 13 || digits.length > 19) return false;

  let sum = 0;
  let isEven = false;

  for (let i = digits.length - 1; i >= 0; i--) {
    let digit = parseInt(digits[i], 10);

    if (isEven) {
      digit *= 2;
      if (digit > 9) digit -= 9;
    }

    sum += digit;
    isEven = !isEven;
  }

  return sum % 10 === 0;
};
```

## Password Strength Indicator

```typescript
// src/components/form/PasswordStrengthIndicator.tsx
import { View, Text, StyleSheet } from 'react-native';
import { getPasswordStrength } from '@/utils/validators';

interface Props {
  password: string;
}

export function PasswordStrengthIndicator({ password }: Props) {
  if (!password) return null;

  const { score, label, color } = getPasswordStrength(password);
  const maxScore = 6;

  return (
    <View style={styles.container}>
      <View style={styles.barContainer}>
        {Array.from({ length: maxScore }).map((_, i) => (
          <View
            key={i}
            style={[
              styles.bar,
              { backgroundColor: i < score ? color : '#E5E5EA' },
            ]}
          />
        ))}
      </View>
      <Text style={[styles.label, { color }]}>{label}</Text>
    </View>
  );
}

// Usage in form
function PasswordInput({ control }) {
  const password = useWatch({ control, name: 'password' });

  return (
    <View>
      <FormInput
        control={control}
        name="password"
        label="Password"
        secureTextEntry
      />
      <PasswordStrengthIndicator password={password} />
    </View>
  );
}
```

## Async Validation

```typescript
// src/features/auth/schemas/registerSchemaAsync.ts
import { z } from 'zod';
import { api } from '@/lib/api';

// Check if email is available
const checkEmailAvailability = async (email: string): Promise<boolean> => {
  try {
    const { data } = await api.get(`/auth/check-email?email=${email}`);
    return data.available;
  } catch {
    return true; // Assume available on error
  }
};

export const registerSchemaAsync = z.object({
  email: z
    .string()
    .email('Invalid email')
    .refine(
      async (email) => {
        const available = await checkEmailAvailability(email);
        return available;
      },
      { message: 'Email is already registered' }
    ),
  // ... other fields
});

// For React Hook Form with async validation
function RegisterForm() {
  const {
    control,
    handleSubmit,
    setError,
    formState: { isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema), // Use sync validation first
  });

  const onSubmit = async (data: RegisterFormData) => {
    // Do async validation before submit
    const emailAvailable = await checkEmailAvailability(data.email);
    if (!emailAvailable) {
      setError('email', { message: 'Email is already registered' });
      return;
    }

    // Proceed with registration
    await register(data);
  };
}
```

## Best Practices

1. **Centralized Schemas**: Keep validation schemas in dedicated files
2. **Type Inference**: Use z.infer or yup.InferType for type safety
3. **Reusable Schemas**: Compose smaller schemas for complex forms
4. **Custom Messages**: Provide clear, user-friendly error messages
5. **Client + Server**: Validate both client-side and server-side
6. **Password Feedback**: Show real-time password strength
7. **Async Sparingly**: Minimize async validation for better UX
8. **Transform Data**: Use Zod transform for data normalization
