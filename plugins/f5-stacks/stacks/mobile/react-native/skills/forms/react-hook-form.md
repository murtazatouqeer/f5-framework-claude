---
name: rn-react-hook-form
description: React Hook Form for form management in React Native
applies_to: react-native
---

# React Hook Form

## Installation

```bash
npm install react-hook-form
```

## Basic Form

```typescript
// src/features/auth/screens/LoginScreen.tsx
import { View, Text, TextInput, Pressable, StyleSheet } from 'react-native';
import { useForm, Controller } from 'react-hook-form';

interface LoginFormData {
  email: string;
  password: string;
}

export function LoginScreen() {
  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (data: LoginFormData) => {
    console.log('Form data:', data);
    // Handle login
  };

  return (
    <View style={styles.container}>
      <Controller
        control={control}
        name="email"
        rules={{
          required: 'Email is required',
          pattern: {
            value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
            message: 'Invalid email address',
          },
        }}
        render={({ field: { onChange, onBlur, value } }) => (
          <View style={styles.fieldContainer}>
            <Text style={styles.label}>Email</Text>
            <TextInput
              style={[styles.input, errors.email && styles.inputError]}
              placeholder="Enter your email"
              keyboardType="email-address"
              autoCapitalize="none"
              autoComplete="email"
              onBlur={onBlur}
              onChangeText={onChange}
              value={value}
            />
            {errors.email && (
              <Text style={styles.error}>{errors.email.message}</Text>
            )}
          </View>
        )}
      />

      <Controller
        control={control}
        name="password"
        rules={{
          required: 'Password is required',
          minLength: {
            value: 8,
            message: 'Password must be at least 8 characters',
          },
        }}
        render={({ field: { onChange, onBlur, value } }) => (
          <View style={styles.fieldContainer}>
            <Text style={styles.label}>Password</Text>
            <TextInput
              style={[styles.input, errors.password && styles.inputError]}
              placeholder="Enter your password"
              secureTextEntry
              autoComplete="password"
              onBlur={onBlur}
              onChangeText={onChange}
              value={value}
            />
            {errors.password && (
              <Text style={styles.error}>{errors.password.message}</Text>
            )}
          </View>
        )}
      />

      <Pressable
        style={[styles.button, isSubmitting && styles.buttonDisabled]}
        onPress={handleSubmit(onSubmit)}
        disabled={isSubmitting}
      >
        <Text style={styles.buttonText}>
          {isSubmitting ? 'Signing in...' : 'Sign In'}
        </Text>
      </Pressable>
    </View>
  );
}
```

## Reusable Form Input Component

```typescript
// src/components/form/FormInput.tsx
import { View, Text, TextInput, TextInputProps, StyleSheet } from 'react-native';
import { Control, Controller, FieldValues, Path, RegisterOptions } from 'react-hook-form';

interface FormInputProps<T extends FieldValues> extends Omit<TextInputProps, 'value'> {
  control: Control<T>;
  name: Path<T>;
  label?: string;
  rules?: RegisterOptions<T>;
}

export function FormInput<T extends FieldValues>({
  control,
  name,
  label,
  rules,
  ...inputProps
}: FormInputProps<T>) {
  return (
    <Controller
      control={control}
      name={name}
      rules={rules}
      render={({
        field: { onChange, onBlur, value },
        fieldState: { error },
      }) => (
        <View style={styles.container}>
          {label && <Text style={styles.label}>{label}</Text>}
          <TextInput
            style={[styles.input, error && styles.inputError]}
            onBlur={onBlur}
            onChangeText={onChange}
            value={value}
            {...inputProps}
          />
          {error && <Text style={styles.error}>{error.message}</Text>}
        </View>
      )}
    />
  );
}

// Usage
function RegisterForm() {
  const { control, handleSubmit } = useForm<RegisterFormData>();

  return (
    <View>
      <FormInput
        control={control}
        name="name"
        label="Full Name"
        placeholder="Enter your name"
        rules={{ required: 'Name is required' }}
      />
      <FormInput
        control={control}
        name="email"
        label="Email"
        placeholder="Enter your email"
        keyboardType="email-address"
        autoCapitalize="none"
        rules={{
          required: 'Email is required',
          pattern: {
            value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            message: 'Invalid email',
          },
        }}
      />
    </View>
  );
}
```

## Form with Picker/Select

```typescript
// src/components/form/FormPicker.tsx
import { View, Text, StyleSheet } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { Control, Controller, FieldValues, Path } from 'react-hook-form';

interface Option {
  label: string;
  value: string;
}

interface FormPickerProps<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label?: string;
  options: Option[];
  placeholder?: string;
}

export function FormPicker<T extends FieldValues>({
  control,
  name,
  label,
  options,
  placeholder,
}: FormPickerProps<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({
        field: { onChange, value },
        fieldState: { error },
      }) => (
        <View style={styles.container}>
          {label && <Text style={styles.label}>{label}</Text>}
          <View style={[styles.pickerContainer, error && styles.pickerError]}>
            <Picker
              selectedValue={value}
              onValueChange={onChange}
              style={styles.picker}
            >
              {placeholder && (
                <Picker.Item label={placeholder} value="" enabled={false} />
              )}
              {options.map((option) => (
                <Picker.Item
                  key={option.value}
                  label={option.label}
                  value={option.value}
                />
              ))}
            </Picker>
          </View>
          {error && <Text style={styles.error}>{error.message}</Text>}
        </View>
      )}
    />
  );
}
```

## Form with Switch/Checkbox

```typescript
// src/components/form/FormSwitch.tsx
import { View, Text, Switch, StyleSheet, Pressable } from 'react-native';
import { Control, Controller, FieldValues, Path } from 'react-hook-form';

interface FormSwitchProps<T extends FieldValues> {
  control: Control<T>;
  name: Path<T>;
  label: string;
}

export function FormSwitch<T extends FieldValues>({
  control,
  name,
  label,
}: FormSwitchProps<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field: { onChange, value }, fieldState: { error } }) => (
        <View style={styles.container}>
          <Pressable style={styles.row} onPress={() => onChange(!value)}>
            <Text style={styles.label}>{label}</Text>
            <Switch value={value} onValueChange={onChange} />
          </Pressable>
          {error && <Text style={styles.error}>{error.message}</Text>}
        </View>
      )}
    />
  );
}

// Checkbox style
export function FormCheckbox<T extends FieldValues>({
  control,
  name,
  label,
}: FormSwitchProps<T>) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field: { onChange, value }, fieldState: { error } }) => (
        <View style={styles.container}>
          <Pressable style={styles.checkboxRow} onPress={() => onChange(!value)}>
            <View style={[styles.checkbox, value && styles.checkboxChecked]}>
              {value && <Ionicons name="checkmark" size={16} color="#fff" />}
            </View>
            <Text style={styles.checkboxLabel}>{label}</Text>
          </Pressable>
          {error && <Text style={styles.error}>{error.message}</Text>}
        </View>
      )}
    />
  );
}
```

## Complex Form with Arrays

```typescript
// src/features/profile/screens/ExperienceForm.tsx
import { useForm, useFieldArray, Controller } from 'react-hook-form';

interface Experience {
  company: string;
  position: string;
  startDate: string;
  endDate: string;
}

interface ProfileFormData {
  name: string;
  experiences: Experience[];
}

export function ExperienceForm() {
  const { control, handleSubmit } = useForm<ProfileFormData>({
    defaultValues: {
      name: '',
      experiences: [{ company: '', position: '', startDate: '', endDate: '' }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'experiences',
  });

  return (
    <ScrollView>
      <FormInput control={control} name="name" label="Name" />

      <Text style={styles.sectionTitle}>Work Experience</Text>

      {fields.map((field, index) => (
        <View key={field.id} style={styles.experienceCard}>
          <FormInput
            control={control}
            name={`experiences.${index}.company`}
            label="Company"
            rules={{ required: 'Company is required' }}
          />
          <FormInput
            control={control}
            name={`experiences.${index}.position`}
            label="Position"
            rules={{ required: 'Position is required' }}
          />
          <View style={styles.row}>
            <FormInput
              control={control}
              name={`experiences.${index}.startDate`}
              label="Start Date"
              placeholder="YYYY-MM"
              style={styles.halfInput}
            />
            <FormInput
              control={control}
              name={`experiences.${index}.endDate`}
              label="End Date"
              placeholder="YYYY-MM or Present"
              style={styles.halfInput}
            />
          </View>
          {fields.length > 1 && (
            <Pressable onPress={() => remove(index)} style={styles.removeButton}>
              <Text style={styles.removeText}>Remove</Text>
            </Pressable>
          )}
        </View>
      ))}

      <Pressable
        onPress={() =>
          append({ company: '', position: '', startDate: '', endDate: '' })
        }
        style={styles.addButton}
      >
        <Text style={styles.addText}>+ Add Experience</Text>
      </Pressable>

      <Pressable onPress={handleSubmit(onSubmit)} style={styles.submitButton}>
        <Text style={styles.submitText}>Save Profile</Text>
      </Pressable>
    </ScrollView>
  );
}
```

## Form with API Integration

```typescript
// src/features/products/screens/ProductForm.tsx
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigation } from '@react-navigation/native';

interface ProductFormData {
  name: string;
  description: string;
  price: string;
  category: string;
}

export function ProductForm({ productId }: { productId?: string }) {
  const navigation = useNavigation();
  const queryClient = useQueryClient();

  const { control, handleSubmit, setError, formState } = useForm<ProductFormData>();

  const mutation = useMutation({
    mutationFn: async (data: ProductFormData) => {
      const payload = {
        ...data,
        price: parseFloat(data.price),
      };

      if (productId) {
        return api.patch(`/products/${productId}`, payload);
      }
      return api.post('/products', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      navigation.goBack();
    },
    onError: (error: ApiError) => {
      if (error.errors) {
        // Set field-level errors
        error.errors.forEach((e) => {
          setError(e.field as keyof ProductFormData, {
            message: e.message,
          });
        });
      }
    },
  });

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <FormInput
        control={control}
        name="name"
        label="Product Name"
        rules={{ required: 'Name is required' }}
      />

      <FormInput
        control={control}
        name="description"
        label="Description"
        multiline
        numberOfLines={4}
        textAlignVertical="top"
      />

      <FormInput
        control={control}
        name="price"
        label="Price"
        keyboardType="decimal-pad"
        rules={{
          required: 'Price is required',
          pattern: {
            value: /^\d+(\.\d{1,2})?$/,
            message: 'Invalid price format',
          },
        }}
      />

      <FormPicker
        control={control}
        name="category"
        label="Category"
        options={[
          { label: 'Electronics', value: 'electronics' },
          { label: 'Clothing', value: 'clothing' },
          { label: 'Food', value: 'food' },
        ]}
        placeholder="Select a category"
      />

      {mutation.error && !mutation.error.errors && (
        <Text style={styles.globalError}>{mutation.error.message}</Text>
      )}

      <Pressable
        style={[styles.button, mutation.isPending && styles.buttonDisabled]}
        onPress={handleSubmit((data) => mutation.mutate(data))}
        disabled={mutation.isPending}
      >
        <Text style={styles.buttonText}>
          {mutation.isPending ? 'Saving...' : productId ? 'Update' : 'Create'}
        </Text>
      </Pressable>
    </ScrollView>
  );
}
```

## Watch and Conditional Fields

```typescript
function ShippingForm() {
  const { control, watch } = useForm<ShippingFormData>();
  const shippingMethod = watch('shippingMethod');

  return (
    <View>
      <FormPicker
        control={control}
        name="shippingMethod"
        label="Shipping Method"
        options={[
          { label: 'Standard', value: 'standard' },
          { label: 'Express', value: 'express' },
          { label: 'Pickup', value: 'pickup' },
        ]}
      />

      {shippingMethod !== 'pickup' && (
        <>
          <FormInput control={control} name="address" label="Address" />
          <FormInput control={control} name="city" label="City" />
          <FormInput control={control} name="zipCode" label="ZIP Code" />
        </>
      )}

      {shippingMethod === 'pickup' && (
        <FormPicker
          control={control}
          name="pickupLocation"
          label="Pickup Location"
          options={pickupLocations}
        />
      )}
    </View>
  );
}
```

## Best Practices

1. **Controller for RN**: Always use Controller wrapper for React Native inputs
2. **Reusable Components**: Create typed form components for consistency
3. **Validation Rules**: Define rules inline or with Zod/Yup schemas
4. **Error Display**: Show field-level and form-level errors
5. **Loading States**: Disable form during submission
6. **API Errors**: Map server validation errors to form fields
7. **Watch Sparingly**: Use watch only when needed for conditional logic
8. **Default Values**: Always provide defaultValues to avoid controlled/uncontrolled warnings
