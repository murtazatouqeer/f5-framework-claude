# React Hook Form

## Overview

Performant, flexible forms with easy validation and minimal re-renders.

## Basic Setup

```tsx
import { useForm, SubmitHandler } from 'react-hook-form';

interface LoginFormInputs {
  email: string;
  password: string;
  rememberMe: boolean;
}

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormInputs>({
    defaultValues: {
      email: '',
      password: '',
      rememberMe: false,
    },
  });

  const onSubmit: SubmitHandler<LoginFormInputs> = async (data) => {
    await loginUser(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          {...register('email', {
            required: 'Email is required',
            pattern: {
              value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
              message: 'Invalid email address',
            },
          })}
        />
        {errors.email && <span>{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          {...register('password', {
            required: 'Password is required',
            minLength: {
              value: 8,
              message: 'Password must be at least 8 characters',
            },
          })}
        />
        {errors.password && <span>{errors.password.message}</span>}
      </div>

      <div>
        <label>
          <input type="checkbox" {...register('rememberMe')} />
          Remember me
        </label>
      </div>

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

## With Zod Validation

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const registrationSchema = z
  .object({
    username: z
      .string()
      .min(3, 'Username must be at least 3 characters')
      .max(20, 'Username must be less than 20 characters'),
    email: z.string().email('Invalid email address'),
    password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        'Password must contain uppercase, lowercase, and number'
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ['confirmPassword'],
  });

type RegistrationFormInputs = z.infer<typeof registrationSchema>;

function RegistrationForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<RegistrationFormInputs>({
    resolver: zodResolver(registrationSchema),
  });

  const onSubmit = async (data: RegistrationFormInputs) => {
    await registerUser(data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields */}
    </form>
  );
}
```

## Controlled Components

```tsx
import { useForm, Controller } from 'react-hook-form';
import { Select, DatePicker, Slider } from '@/components/ui';

interface BookingFormInputs {
  date: Date;
  guests: number;
  room: string;
}

function BookingForm() {
  const { control, handleSubmit } = useForm<BookingFormInputs>({
    defaultValues: {
      date: new Date(),
      guests: 2,
      room: '',
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Controller
        name="date"
        control={control}
        rules={{ required: 'Date is required' }}
        render={({ field, fieldState: { error } }) => (
          <DatePicker
            value={field.value}
            onChange={field.onChange}
            error={error?.message}
          />
        )}
      />

      <Controller
        name="guests"
        control={control}
        render={({ field }) => (
          <Slider
            value={field.value}
            onChange={field.onChange}
            min={1}
            max={10}
          />
        )}
      />

      <Controller
        name="room"
        control={control}
        rules={{ required: 'Please select a room' }}
        render={({ field, fieldState: { error } }) => (
          <Select
            value={field.value}
            onChange={field.onChange}
            options={roomOptions}
            error={error?.message}
          />
        )}
      />

      <button type="submit">Book</button>
    </form>
  );
}
```

## Dynamic Fields (Field Arrays)

```tsx
import { useForm, useFieldArray } from 'react-hook-form';

interface OrderFormInputs {
  customerName: string;
  items: {
    name: string;
    quantity: number;
    price: number;
  }[];
}

function OrderForm() {
  const { register, control, handleSubmit, watch } = useForm<OrderFormInputs>({
    defaultValues: {
      customerName: '',
      items: [{ name: '', quantity: 1, price: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'items',
  });

  const items = watch('items');
  const total = items.reduce((sum, item) => sum + item.quantity * item.price, 0);

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('customerName', { required: true })} />

      {fields.map((field, index) => (
        <div key={field.id}>
          <input
            {...register(`items.${index}.name`, { required: true })}
            placeholder="Item name"
          />
          <input
            type="number"
            {...register(`items.${index}.quantity`, { valueAsNumber: true })}
          />
          <input
            type="number"
            {...register(`items.${index}.price`, { valueAsNumber: true })}
          />
          <button type="button" onClick={() => remove(index)}>
            Remove
          </button>
        </div>
      ))}

      <button
        type="button"
        onClick={() => append({ name: '', quantity: 1, price: 0 })}
      >
        Add Item
      </button>

      <p>Total: ${total.toFixed(2)}</p>

      <button type="submit">Submit Order</button>
    </form>
  );
}
```

## Form State Management

```tsx
function FormWithState() {
  const {
    register,
    handleSubmit,
    watch,
    reset,
    setValue,
    getValues,
    trigger,
    formState: {
      errors,
      isDirty,
      isValid,
      isSubmitting,
      isSubmitted,
      touchedFields,
      dirtyFields,
    },
  } = useForm<FormInputs>({
    mode: 'onChange', // Validate on change
    // mode: 'onBlur', // Validate on blur
    // mode: 'onSubmit', // Validate on submit (default)
    // mode: 'all', // Validate on blur and change
  });

  // Watch specific field
  const email = watch('email');

  // Watch multiple fields
  const [email, password] = watch(['email', 'password']);

  // Watch all fields
  const allFields = watch();

  // Programmatic updates
  const handlePrefill = () => {
    setValue('email', 'test@example.com');
    setValue('name', 'John Doe', {
      shouldValidate: true,
      shouldDirty: true,
      shouldTouch: true,
    });
  };

  const handleReset = () => {
    reset(); // Reset to default values
    // or
    reset({ email: '', name: '' }); // Reset to specific values
  };

  // Manual validation
  const handleValidateEmail = async () => {
    const isValid = await trigger('email');
    console.log('Email valid:', isValid);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Form fields */}
      <button disabled={!isDirty || !isValid || isSubmitting}>Submit</button>
    </form>
  );
}
```

## Custom Form Components

```tsx
// components/forms/FormInput.tsx
import { useFormContext, RegisterOptions } from 'react-hook-form';

interface FormInputProps {
  name: string;
  label: string;
  type?: string;
  rules?: RegisterOptions;
  placeholder?: string;
}

export function FormInput({
  name,
  label,
  type = 'text',
  rules,
  placeholder,
}: FormInputProps) {
  const {
    register,
    formState: { errors },
  } = useFormContext();

  const error = errors[name];

  return (
    <div className="space-y-1">
      <label htmlFor={name} className="text-sm font-medium">
        {label}
        {rules?.required && <span className="text-red-500 ml-1">*</span>}
      </label>
      <input
        id={name}
        type={type}
        placeholder={placeholder}
        className={cn(
          'w-full px-3 py-2 border rounded',
          error ? 'border-red-500' : 'border-gray-300'
        )}
        {...register(name, rules)}
      />
      {error && (
        <p className="text-sm text-red-500">{error.message as string}</p>
      )}
    </div>
  );
}

// Usage with FormProvider
import { useForm, FormProvider } from 'react-hook-form';

function MyForm() {
  const methods = useForm();

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)}>
        <FormInput
          name="email"
          label="Email"
          type="email"
          rules={{ required: 'Email is required' }}
        />
        <FormInput
          name="name"
          label="Full Name"
          rules={{ required: 'Name is required' }}
        />
      </form>
    </FormProvider>
  );
}
```

## Best Practices

1. **Use Zod resolver** - Type-safe validation
2. **Set defaultValues** - Avoid uncontrolled to controlled warnings
3. **Use Controller for UI libraries** - Radix, shadcn, MUI components
4. **Choose validation mode wisely** - Balance UX and performance
5. **Leverage FormProvider** - Share form context in nested components
6. **Handle async validation** - Use validate function for API checks
