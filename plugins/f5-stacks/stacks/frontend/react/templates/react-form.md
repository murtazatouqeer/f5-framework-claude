# React Form Template

Production-ready form templates using React Hook Form and Zod validation.

## Basic Form Template

```tsx
// features/{{feature}}/components/{{Entity}}Form.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/Form';

// Validation Schema
const {{entity}}Schema = z.object({
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be less than 100 characters'),
  email: z
    .string()
    .email('Invalid email address'),
  description: z
    .string()
    .max(500, 'Description must be less than 500 characters')
    .optional(),
});

type {{Entity}}FormValues = z.infer<typeof {{entity}}Schema>;

interface {{Entity}}FormProps {
  defaultValues?: Partial<{{Entity}}FormValues>;
  onSubmit: (data: {{Entity}}FormValues) => Promise<void>;
  onCancel?: () => void;
  isSubmitting?: boolean;
}

export function {{Entity}}Form({
  defaultValues,
  onSubmit,
  onCancel,
  isSubmitting = false,
}: {{Entity}}FormProps) {
  const form = useForm<{{Entity}}FormValues>({
    resolver: zodResolver({{entity}}Schema),
    defaultValues: {
      name: '',
      email: '',
      description: '',
      ...defaultValues,
    },
  });

  const handleSubmit = async (data: {{Entity}}FormValues) => {
    try {
      await onSubmit(data);
      form.reset();
    } catch (error) {
      // Error is handled by parent component
      console.error('Form submission error:', error);
    }
  };

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="Enter name" {...field} />
              </FormControl>
              <FormDescription>
                This is the display name.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="email@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="description"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Description</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Enter description..."
                  rows={4}
                  {...field}
                />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex justify-end gap-4">
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit" isLoading={isSubmitting}>
            {defaultValues ? 'Update' : 'Create'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

## Form with All Field Types

```tsx
// features/{{feature}}/components/CompleteForm.tsx
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Checkbox } from '@/components/ui/Checkbox';
import { RadioGroup } from '@/components/ui/RadioGroup';
import { Switch } from '@/components/ui/Switch';
import { DatePicker } from '@/components/ui/DatePicker';
import { FileUpload } from '@/components/ui/FileUpload';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/Form';

// Comprehensive schema
const formSchema = z.object({
  // Text inputs
  name: z.string().min(2).max(100),
  email: z.string().email(),
  password: z.string().min(8).regex(
    /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
    'Password must contain uppercase, lowercase, and number'
  ),
  phone: z.string().regex(/^\+?[\d\s-()]+$/, 'Invalid phone number').optional(),

  // Number inputs
  age: z.coerce.number().min(18).max(120),
  price: z.coerce.number().positive().multipleOf(0.01),

  // Selection
  category: z.string().min(1, 'Please select a category'),
  tags: z.array(z.string()).min(1, 'Select at least one tag'),
  priority: z.enum(['low', 'medium', 'high']),

  // Boolean
  acceptTerms: z.literal(true, {
    errorMap: () => ({ message: 'You must accept the terms' }),
  }),
  newsletter: z.boolean().default(false),
  notifications: z.boolean().default(true),

  // Date
  birthDate: z.date().max(new Date(), 'Birth date cannot be in the future'),
  startDate: z.date(),

  // File
  avatar: z.instanceof(File).optional(),
  documents: z.array(z.instanceof(File)).optional(),

  // Textarea
  bio: z.string().max(1000).optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface CompleteFormProps {
  onSubmit: (data: FormValues) => Promise<void>;
}

export function CompleteForm({ onSubmit }: CompleteFormProps) {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      name: '',
      email: '',
      password: '',
      phone: '',
      age: 18,
      price: 0,
      category: '',
      tags: [],
      priority: 'medium',
      acceptTerms: false,
      newsletter: false,
      notifications: true,
      bio: '',
    },
  });

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
        {/* Text Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Personal Information</h3>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full Name</FormLabel>
                  <FormControl>
                    <Input placeholder="John Doe" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Email</FormLabel>
                  <FormControl>
                    <Input type="email" placeholder="john@example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>

          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input type="password" {...field} />
                </FormControl>
                <FormDescription>
                  Must contain uppercase, lowercase, and number.
                </FormDescription>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Number Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Numbers</h3>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="age"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Age</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      min={18}
                      max={120}
                      {...field}
                      onChange={(e) => field.onChange(e.target.valueAsNumber)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="price"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Price</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      step="0.01"
                      min={0}
                      placeholder="0.00"
                      {...field}
                      onChange={(e) => field.onChange(e.target.valueAsNumber)}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </div>
        </div>

        {/* Selection Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Selections</h3>

          <FormField
            control={form.control}
            name="category"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Category</FormLabel>
                <Select
                  value={field.value}
                  onValueChange={field.onChange}
                >
                  <FormControl>
                    <Select.Trigger>
                      <Select.Value placeholder="Select category" />
                    </Select.Trigger>
                  </FormControl>
                  <Select.Content>
                    <Select.Item value="tech">Technology</Select.Item>
                    <Select.Item value="business">Business</Select.Item>
                    <Select.Item value="design">Design</Select.Item>
                  </Select.Content>
                </Select>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="priority"
            render={({ field }) => (
              <FormItem className="space-y-3">
                <FormLabel>Priority</FormLabel>
                <FormControl>
                  <RadioGroup
                    value={field.value}
                    onValueChange={field.onChange}
                    className="flex gap-4"
                  >
                    <RadioGroup.Item value="low" label="Low" />
                    <RadioGroup.Item value="medium" label="Medium" />
                    <RadioGroup.Item value="high" label="High" />
                  </RadioGroup>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Boolean Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Preferences</h3>

          <FormField
            control={form.control}
            name="acceptTerms"
            render={({ field }) => (
              <FormItem className="flex items-start space-x-3 space-y-0">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
                <div className="space-y-1 leading-none">
                  <FormLabel>Accept terms and conditions</FormLabel>
                  <FormDescription>
                    You agree to our Terms of Service and Privacy Policy.
                  </FormDescription>
                </div>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="notifications"
            render={({ field }) => (
              <FormItem className="flex items-center justify-between rounded-lg border p-4">
                <div className="space-y-0.5">
                  <FormLabel>Push Notifications</FormLabel>
                  <FormDescription>
                    Receive notifications about updates.
                  </FormDescription>
                </div>
                <FormControl>
                  <Switch
                    checked={field.value}
                    onCheckedChange={field.onChange}
                  />
                </FormControl>
              </FormItem>
            )}
          />
        </div>

        {/* Date Section */}
        <div className="space-y-4">
          <h3 className="text-lg font-medium">Dates</h3>

          <FormField
            control={form.control}
            name="birthDate"
            render={({ field }) => (
              <FormItem className="flex flex-col">
                <FormLabel>Birth Date</FormLabel>
                <FormControl>
                  <DatePicker
                    value={field.value}
                    onChange={field.onChange}
                    maxDate={new Date()}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
        </div>

        {/* Textarea Section */}
        <FormField
          control={form.control}
          name="bio"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Bio</FormLabel>
              <FormControl>
                <Textarea
                  placeholder="Tell us about yourself..."
                  rows={4}
                  {...field}
                />
              </FormControl>
              <FormDescription>
                Max 1000 characters. {1000 - (field.value?.length || 0)} remaining.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit" className="w-full">
          Submit
        </Button>
      </form>
    </Form>
  );
}
```

## Multi-Step Form Template

```tsx
// features/{{feature}}/components/MultiStepForm.tsx
import { useState } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/Button';
import { Progress } from '@/components/ui/Progress';

// Step schemas
const step1Schema = z.object({
  firstName: z.string().min(2),
  lastName: z.string().min(2),
  email: z.string().email(),
});

const step2Schema = z.object({
  company: z.string().min(2),
  role: z.string().min(2),
  experience: z.coerce.number().min(0),
});

const step3Schema = z.object({
  plan: z.enum(['basic', 'pro', 'enterprise']),
  billingCycle: z.enum(['monthly', 'yearly']),
  acceptTerms: z.literal(true),
});

// Combined schema
const formSchema = step1Schema.merge(step2Schema).merge(step3Schema);

type FormValues = z.infer<typeof formSchema>;

const steps = [
  { title: 'Personal Info', schema: step1Schema },
  { title: 'Professional Info', schema: step2Schema },
  { title: 'Plan Selection', schema: step3Schema },
];

interface MultiStepFormProps {
  onSubmit: (data: FormValues) => Promise<void>;
}

export function MultiStepForm({ onSubmit }: MultiStepFormProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      company: '',
      role: '',
      experience: 0,
      plan: 'basic',
      billingCycle: 'monthly',
      acceptTerms: false,
    },
    mode: 'onChange',
  });

  const progress = ((currentStep + 1) / steps.length) * 100;

  const validateCurrentStep = async () => {
    const currentSchema = steps[currentStep].schema;
    const fieldsToValidate = Object.keys(currentSchema.shape) as (keyof FormValues)[];

    const isValid = await form.trigger(fieldsToValidate);
    return isValid;
  };

  const handleNext = async () => {
    const isValid = await validateCurrentStep();
    if (isValid && currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = async (data: FormValues) => {
    setIsSubmitting(true);
    try {
      await onSubmit(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      {/* Progress */}
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          {steps.map((step, index) => (
            <span
              key={step.title}
              className={`text-sm font-medium ${
                index <= currentStep ? 'text-primary' : 'text-muted-foreground'
              }`}
            >
              {step.title}
            </span>
          ))}
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      {/* Form */}
      <FormProvider {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)}>
          {/* Step 1: Personal Info */}
          {currentStep === 0 && <Step1Fields />}

          {/* Step 2: Professional Info */}
          {currentStep === 1 && <Step2Fields />}

          {/* Step 3: Plan Selection */}
          {currentStep === 2 && <Step3Fields />}

          {/* Navigation */}
          <div className="flex justify-between mt-8">
            <Button
              type="button"
              variant="outline"
              onClick={handlePrevious}
              disabled={currentStep === 0}
            >
              Previous
            </Button>

            {currentStep < steps.length - 1 ? (
              <Button type="button" onClick={handleNext}>
                Next
              </Button>
            ) : (
              <Button type="submit" isLoading={isSubmitting}>
                Complete Setup
              </Button>
            )}
          </div>
        </form>
      </FormProvider>
    </div>
  );
}

// Step components
function Step1Fields() {
  return (
    <div className="space-y-4">
      {/* Personal info fields */}
    </div>
  );
}

function Step2Fields() {
  return (
    <div className="space-y-4">
      {/* Professional info fields */}
    </div>
  );
}

function Step3Fields() {
  return (
    <div className="space-y-4">
      {/* Plan selection fields */}
    </div>
  );
}
```

## Form with Dynamic Fields (Array)

```tsx
// features/{{feature}}/components/DynamicForm.tsx
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/Form';

const itemSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  quantity: z.coerce.number().min(1, 'Quantity must be at least 1'),
  price: z.coerce.number().min(0, 'Price must be positive'),
});

const formSchema = z.object({
  orderName: z.string().min(2),
  items: z.array(itemSchema).min(1, 'At least one item is required'),
});

type FormValues = z.infer<typeof formSchema>;

export function DynamicForm({ onSubmit }: { onSubmit: (data: FormValues) => Promise<void> }) {
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      orderName: '',
      items: [{ name: '', quantity: 1, price: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control: form.control,
    name: 'items',
  });

  const watchedItems = form.watch('items');
  const total = watchedItems.reduce(
    (sum, item) => sum + (item.quantity || 0) * (item.price || 0),
    0
  );

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="orderName"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Order Name</FormLabel>
              <FormControl>
                <Input placeholder="My Order" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium">Items</h3>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ name: '', quantity: 1, price: 0 })}
            >
              <Plus className="h-4 w-4 mr-2" />
              Add Item
            </Button>
          </div>

          {fields.map((field, index) => (
            <div
              key={field.id}
              className="flex gap-4 items-start p-4 border rounded-lg"
            >
              <FormField
                control={form.control}
                name={`items.${index}.name`}
                render={({ field }) => (
                  <FormItem className="flex-1">
                    <FormLabel>Name</FormLabel>
                    <FormControl>
                      <Input placeholder="Item name" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name={`items.${index}.quantity`}
                render={({ field }) => (
                  <FormItem className="w-24">
                    <FormLabel>Qty</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min={1}
                        {...field}
                        onChange={(e) => field.onChange(e.target.valueAsNumber)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name={`items.${index}.price`}
                render={({ field }) => (
                  <FormItem className="w-32">
                    <FormLabel>Price</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.01"
                        min={0}
                        {...field}
                        onChange={(e) => field.onChange(e.target.valueAsNumber)}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="mt-8"
                onClick={() => remove(index)}
                disabled={fields.length === 1}
              >
                <Trash2 className="h-4 w-4 text-destructive" />
              </Button>
            </div>
          ))}

          {form.formState.errors.items?.root && (
            <p className="text-sm text-destructive">
              {form.formState.errors.items.root.message}
            </p>
          )}
        </div>

        <div className="flex items-center justify-between pt-4 border-t">
          <div className="text-lg font-semibold">
            Total: ${total.toFixed(2)}
          </div>
          <Button type="submit">Submit Order</Button>
        </div>
      </form>
    </Form>
  );
}
```

## Form Components

### Form UI Components

```tsx
// components/ui/Form.tsx
import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import {
  Controller,
  FormProvider,
  useFormContext,
  type ControllerProps,
  type FieldPath,
  type FieldValues,
} from 'react-hook-form';
import { cn } from '@/lib/utils';

const Form = FormProvider;

interface FormFieldContextValue<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> {
  name: TName;
}

const FormFieldContext = React.createContext<FormFieldContextValue | null>(null);

const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  ...props
}: ControllerProps<TFieldValues, TName>) => {
  return (
    <FormFieldContext.Provider value={{ name: props.name }}>
      <Controller {...props} />
    </FormFieldContext.Provider>
  );
};

const useFormField = () => {
  const fieldContext = React.useContext(FormFieldContext);
  const { getFieldState, formState } = useFormContext();

  if (!fieldContext) {
    throw new Error('useFormField should be used within <FormField>');
  }

  const fieldState = getFieldState(fieldContext.name, formState);

  return {
    name: fieldContext.name,
    ...fieldState,
  };
};

interface FormItemContextValue {
  id: string;
}

const FormItemContext = React.createContext<FormItemContextValue | null>(null);

const FormItem = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => {
  const id = React.useId();

  return (
    <FormItemContext.Provider value={{ id }}>
      <div ref={ref} className={cn('space-y-2', className)} {...props} />
    </FormItemContext.Provider>
  );
});
FormItem.displayName = 'FormItem';

const FormLabel = React.forwardRef<
  HTMLLabelElement,
  React.LabelHTMLAttributes<HTMLLabelElement>
>(({ className, ...props }, ref) => {
  const { error } = useFormField();
  const formItemContext = React.useContext(FormItemContext);

  return (
    <label
      ref={ref}
      htmlFor={formItemContext?.id}
      className={cn(
        'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70',
        error && 'text-destructive',
        className
      )}
      {...props}
    />
  );
});
FormLabel.displayName = 'FormLabel';

const FormControl = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement>
>(({ ...props }, ref) => {
  const { error } = useFormField();
  const formItemContext = React.useContext(FormItemContext);

  return (
    <Slot
      ref={ref}
      id={formItemContext?.id}
      aria-describedby={
        error
          ? `${formItemContext?.id}-error`
          : `${formItemContext?.id}-description`
      }
      aria-invalid={!!error}
      {...props}
    />
  );
});
FormControl.displayName = 'FormControl';

const FormDescription = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => {
  const formItemContext = React.useContext(FormItemContext);

  return (
    <p
      ref={ref}
      id={`${formItemContext?.id}-description`}
      className={cn('text-sm text-muted-foreground', className)}
      {...props}
    />
  );
});
FormDescription.displayName = 'FormDescription';

const FormMessage = React.forwardRef<
  HTMLParagraphElement,
  React.HTMLAttributes<HTMLParagraphElement>
>(({ className, children, ...props }, ref) => {
  const { error } = useFormField();
  const formItemContext = React.useContext(FormItemContext);
  const body = error ? String(error?.message) : children;

  if (!body) return null;

  return (
    <p
      ref={ref}
      id={`${formItemContext?.id}-error`}
      className={cn('text-sm font-medium text-destructive', className)}
      {...props}
    >
      {body}
    </p>
  );
});
FormMessage.displayName = 'FormMessage';

export {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
  useFormField,
};
```

## Form Testing

```tsx
// __tests__/{{Entity}}Form.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { {{Entity}}Form } from '../{{Entity}}Form';

describe('{{Entity}}Form', () => {
  const mockOnSubmit = vi.fn();
  const user = userEvent.setup();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders all form fields', () => {
    render(<{{Entity}}Form onSubmit={mockOnSubmit} />);

    expect(screen.getByLabelText(/name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
  });

  it('shows validation errors for empty required fields', async () => {
    render(<{{Entity}}Form onSubmit={mockOnSubmit} />);

    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(screen.getByText(/name must be at least/i)).toBeInTheDocument();
    });

    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits form with valid data', async () => {
    mockOnSubmit.mockResolvedValueOnce(undefined);
    render(<{{Entity}}Form onSubmit={mockOnSubmit} />);

    await user.type(screen.getByLabelText(/name/i), 'Test Name');
    await user.type(screen.getByLabelText(/email/i), 'test@example.com');
    await user.click(screen.getByRole('button', { name: /create/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Test Name',
          email: 'test@example.com',
        })
      );
    });
  });

  it('shows Update button when defaultValues provided', () => {
    render(
      <{{Entity}}Form
        onSubmit={mockOnSubmit}
        defaultValues={{ name: 'Existing', email: 'existing@example.com' }}
      />
    );

    expect(screen.getByRole('button', { name: /update/i })).toBeInTheDocument();
  });

  it('calls onCancel when cancel button clicked', async () => {
    const mockOnCancel = vi.fn();
    render(<{{Entity}}Form onSubmit={mockOnSubmit} onCancel={mockOnCancel} />);

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('disables submit button while submitting', () => {
    render(<{{Entity}}Form onSubmit={mockOnSubmit} isSubmitting />);

    expect(screen.getByRole('button', { name: /create/i })).toBeDisabled();
  });
});
```

## Best Practices

1. **Use Zod for validation** - Type-safe schema validation
2. **Separate schema from component** - Reusable validation logic
3. **Handle async submission** - Show loading states
4. **Provide user feedback** - Error messages and success states
5. **Support controlled/uncontrolled** - defaultValues vs values
6. **Make forms accessible** - Labels, error messages, ARIA
7. **Test form interactions** - Submit, validation, field changes
