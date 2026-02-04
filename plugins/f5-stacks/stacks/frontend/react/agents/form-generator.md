# React Form Generator Agent

## Purpose
Generate React forms with validation, state management, and submission handling using react-hook-form and zod.

## Triggers
- "create form"
- "generate form"
- "react form"
- "validation form"

## Input Requirements

```yaml
required:
  - form_name: string         # PascalCase form name
  - fields: array             # Form field definitions

optional:
  - entity: string            # Related entity name
  - mode: string              # 'create' | 'edit' | 'both'
  - submit_endpoint: string   # API endpoint
  - on_success: string        # Success callback behavior
  - reset_on_submit: boolean  # Reset form after submit
```

### Field Definition
```yaml
field:
  name: string                # Field name (camelCase)
  type: string                # text | email | password | number | select | checkbox | textarea | date | file
  label: string               # Display label
  placeholder: string         # Placeholder text
  required: boolean           # Is required
  validation:                 # Zod validation rules
    min: number
    max: number
    pattern: string
    custom: string            # Custom validation message
  options: array              # For select fields
  defaultValue: any           # Default value
```

## Generation Process

### 1. Analyze Schema
- Parse field definitions
- Generate Zod schema
- Determine form structure

### 2. Generate Components

#### Schema File
```tsx
// src/features/{feature}/schemas/{entity}.schema.ts
import { z } from 'zod';

export const {entity}Schema = z.object({
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
  category: z
    .string()
    .min(1, 'Please select a category'),
  price: z
    .number()
    .min(0, 'Price must be positive')
    .optional(),
  isActive: z
    .boolean()
    .default(true),
});

export type {Entity}FormValues = z.infer<typeof {entity}Schema>;

// Partial schema for updates
export const {entity}UpdateSchema = {entity}Schema.partial();
export type {Entity}UpdateFormValues = z.infer<typeof {entity}UpdateSchema>;
```

#### Form Component
```tsx
// src/features/{feature}/components/{Entity}Form.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Select } from '@/components/ui/Select';
import { Checkbox } from '@/components/ui/Checkbox';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/Form';
import { {entity}Schema, type {Entity}FormValues } from '../schemas/{entity}.schema';

interface {Entity}FormProps {
  defaultValues?: Partial<{Entity}FormValues>;
  onSubmit: (data: {Entity}FormValues) => Promise<void>;
  onCancel?: () => void;
  isSubmitting?: boolean;
  mode?: 'create' | 'edit';
}

export function {Entity}Form({
  defaultValues,
  onSubmit,
  onCancel,
  isSubmitting = false,
  mode = 'create',
}: {Entity}FormProps) {
  const form = useForm<{Entity}FormValues>({
    resolver: zodResolver({entity}Schema),
    defaultValues: {
      name: '',
      email: '',
      description: '',
      category: '',
      isActive: true,
      ...defaultValues,
    },
  });

  const handleSubmit = async (data: {Entity}FormValues) => {
    try {
      await onSubmit(data);
      if (mode === 'create') {
        form.reset();
      }
    } catch (error) {
      // Error handling done in parent
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

        <FormField
          control={form.control}
          name="category"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Category</FormLabel>
              <Select value={field.value} onValueChange={field.onChange}>
                <Select.Trigger>
                  <Select.Value placeholder="Select category" />
                </Select.Trigger>
                <Select.Content>
                  <Select.Item value="category1">Category 1</Select.Item>
                  <Select.Item value="category2">Category 2</Select.Item>
                </Select.Content>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="isActive"
          render={({ field }) => (
            <FormItem className="flex items-center gap-2">
              <FormControl>
                <Checkbox
                  checked={field.value}
                  onCheckedChange={field.onChange}
                />
              </FormControl>
              <FormLabel className="!mt-0">Active</FormLabel>
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
            {mode === 'edit' ? 'Update' : 'Create'}
          </Button>
        </div>
      </form>
    </Form>
  );
}
```

#### Form with API Integration
```tsx
// src/features/{feature}/components/{Entity}FormContainer.tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { {entity}Api } from '../api/{entity}.api';
import { {Entity}Form } from './{Entity}Form';
import type { {Entity}FormValues } from '../schemas/{entity}.schema';

interface {Entity}FormContainerProps {
  initialData?: {Entity}FormValues & { id: string };
  onSuccess?: () => void;
}

export function {Entity}FormContainer({
  initialData,
  onSuccess,
}: {Entity}FormContainerProps) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const isEditMode = !!initialData?.id;

  const mutation = useMutation({
    mutationFn: (data: {Entity}FormValues) =>
      isEditMode
        ? {entity}Api.update(initialData.id, data)
        : {entity}Api.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{entity}s'] });
      toast.success(
        isEditMode ? '{Entity} updated successfully' : '{Entity} created successfully'
      );
      onSuccess?.();
      if (!isEditMode) {
        navigate('/{entity}s');
      }
    },
    onError: (error: Error) => {
      toast.error(error.message);
    },
  });

  return (
    <{Entity}Form
      defaultValues={initialData}
      onSubmit={mutation.mutateAsync}
      isSubmitting={mutation.isPending}
      mode={isEditMode ? 'edit' : 'create'}
      onCancel={() => navigate(-1)}
    />
  );
}
```

## Output Files

1. **Schema File**: Zod validation schema and types
2. **Form Component**: Presentational form with validation
3. **Form Container**: Form with API integration
4. **Form Tests**: Component and integration tests

## Quality Checks

- [ ] All required fields have validation
- [ ] Proper error message display
- [ ] Loading state during submission
- [ ] Form reset on successful create
- [ ] Accessible form labels and errors
- [ ] Keyboard navigation works
- [ ] Mobile-responsive layout
