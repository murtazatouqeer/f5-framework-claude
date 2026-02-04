# Form Design Patterns

## Overview

Best practices and patterns for building robust, user-friendly forms in React.

## Multi-Step Forms (Wizard)

```tsx
import { useState } from 'react';
import { useForm, FormProvider } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Step schemas
const personalInfoSchema = z.object({
  firstName: z.string().min(2),
  lastName: z.string().min(2),
  email: z.string().email(),
});

const addressSchema = z.object({
  street: z.string().min(5),
  city: z.string().min(2),
  zipCode: z.string().regex(/^\d{5}$/),
});

const paymentSchema = z.object({
  cardNumber: z.string().regex(/^\d{16}$/),
  expiryDate: z.string().regex(/^\d{2}\/\d{2}$/),
  cvv: z.string().regex(/^\d{3}$/),
});

// Combined schema
const checkoutSchema = personalInfoSchema.merge(addressSchema).merge(paymentSchema);
type CheckoutFormValues = z.infer<typeof checkoutSchema>;

// Step schemas for validation
const stepSchemas = [personalInfoSchema, addressSchema, paymentSchema];

interface WizardStep {
  title: string;
  fields: (keyof CheckoutFormValues)[];
  component: React.ComponentType;
}

const steps: WizardStep[] = [
  { title: 'Personal Info', fields: ['firstName', 'lastName', 'email'], component: PersonalInfoStep },
  { title: 'Address', fields: ['street', 'city', 'zipCode'], component: AddressStep },
  { title: 'Payment', fields: ['cardNumber', 'expiryDate', 'cvv'], component: PaymentStep },
];

function CheckoutWizard() {
  const [currentStep, setCurrentStep] = useState(0);

  const methods = useForm<CheckoutFormValues>({
    resolver: zodResolver(checkoutSchema),
    mode: 'onChange',
    defaultValues: {
      firstName: '',
      lastName: '',
      email: '',
      street: '',
      city: '',
      zipCode: '',
      cardNumber: '',
      expiryDate: '',
      cvv: '',
    },
  });

  const { handleSubmit, trigger } = methods;

  const nextStep = async () => {
    // Validate current step fields
    const currentFields = steps[currentStep].fields;
    const isValid = await trigger(currentFields);

    if (isValid && currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const onSubmit = async (data: CheckoutFormValues) => {
    await processCheckout(data);
  };

  const StepComponent = steps[currentStep].component;

  return (
    <FormProvider {...methods}>
      <form onSubmit={handleSubmit(onSubmit)}>
        {/* Progress indicator */}
        <div className="flex justify-between mb-8">
          {steps.map((step, index) => (
            <div
              key={step.title}
              className={cn(
                'flex items-center',
                index <= currentStep ? 'text-blue-600' : 'text-gray-400'
              )}
            >
              <span className="w-8 h-8 rounded-full border flex items-center justify-center">
                {index + 1}
              </span>
              <span className="ml-2">{step.title}</span>
            </div>
          ))}
        </div>

        {/* Step content */}
        <StepComponent />

        {/* Navigation */}
        <div className="flex justify-between mt-8">
          <button
            type="button"
            onClick={prevStep}
            disabled={currentStep === 0}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Previous
          </button>

          {currentStep === steps.length - 1 ? (
            <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded">
              Complete Order
            </button>
          ) : (
            <button
              type="button"
              onClick={nextStep}
              className="px-4 py-2 bg-blue-600 text-white rounded"
            >
              Next
            </button>
          )}
        </div>
      </form>
    </FormProvider>
  );
}
```

## Conditional Fields

```tsx
import { useForm, useWatch } from 'react-hook-form';

interface ShippingFormValues {
  shippingMethod: 'standard' | 'express' | 'pickup';
  address?: string;
  city?: string;
  pickupLocation?: string;
  pickupDate?: string;
}

function ShippingForm() {
  const { register, control } = useForm<ShippingFormValues>();

  // Watch for conditional rendering
  const shippingMethod = useWatch({ control, name: 'shippingMethod' });

  return (
    <form>
      <div>
        <label>Shipping Method</label>
        <select {...register('shippingMethod')}>
          <option value="standard">Standard Delivery</option>
          <option value="express">Express Delivery</option>
          <option value="pickup">Store Pickup</option>
        </select>
      </div>

      {/* Show address fields for delivery */}
      {(shippingMethod === 'standard' || shippingMethod === 'express') && (
        <>
          <div>
            <label>Address</label>
            <input {...register('address', { required: true })} />
          </div>
          <div>
            <label>City</label>
            <input {...register('city', { required: true })} />
          </div>
        </>
      )}

      {/* Show pickup fields for pickup */}
      {shippingMethod === 'pickup' && (
        <>
          <div>
            <label>Pickup Location</label>
            <select {...register('pickupLocation', { required: true })}>
              <option value="store1">Downtown Store</option>
              <option value="store2">Mall Location</option>
            </select>
          </div>
          <div>
            <label>Pickup Date</label>
            <input type="date" {...register('pickupDate', { required: true })} />
          </div>
        </>
      )}
    </form>
  );
}
```

## Auto-Save Form

```tsx
import { useForm, useWatch } from 'react-hook-form';
import { useDebounce } from '@/hooks/useDebounce';

function AutoSaveForm({ initialData }: { initialData: FormValues }) {
  const { register, control, formState: { isDirty } } = useForm<FormValues>({
    defaultValues: initialData,
  });

  // Watch all form values
  const formValues = useWatch({ control });

  // Debounce the values
  const debouncedValues = useDebounce(formValues, 1000);

  // Auto-save effect
  useEffect(() => {
    if (isDirty) {
      saveForm(debouncedValues).then(() => {
        toast.success('Draft saved');
      });
    }
  }, [debouncedValues, isDirty]);

  return (
    <form>
      <div className="text-sm text-gray-500 mb-4">
        {isDirty ? 'Saving...' : 'All changes saved'}
      </div>
      {/* Form fields */}
    </form>
  );
}
```

## Dependent Select Fields

```tsx
import { useForm, useWatch } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';

interface LocationFormValues {
  country: string;
  state: string;
  city: string;
}

function LocationForm() {
  const { register, control, setValue } = useForm<LocationFormValues>();

  const country = useWatch({ control, name: 'country' });
  const state = useWatch({ control, name: 'state' });

  // Fetch states when country changes
  const { data: states } = useQuery({
    queryKey: ['states', country],
    queryFn: () => fetchStates(country),
    enabled: !!country,
  });

  // Fetch cities when state changes
  const { data: cities } = useQuery({
    queryKey: ['cities', country, state],
    queryFn: () => fetchCities(country, state),
    enabled: !!country && !!state,
  });

  // Reset dependent fields when parent changes
  useEffect(() => {
    setValue('state', '');
    setValue('city', '');
  }, [country, setValue]);

  useEffect(() => {
    setValue('city', '');
  }, [state, setValue]);

  return (
    <form>
      <select {...register('country')}>
        <option value="">Select Country</option>
        <option value="US">United States</option>
        <option value="CA">Canada</option>
      </select>

      <select {...register('state')} disabled={!country}>
        <option value="">Select State</option>
        {states?.map((s) => (
          <option key={s.code} value={s.code}>{s.name}</option>
        ))}
      </select>

      <select {...register('city')} disabled={!state}>
        <option value="">Select City</option>
        {cities?.map((c) => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </select>
    </form>
  );
}
```

## Inline Editing

```tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';

interface EditableFieldProps {
  value: string;
  onSave: (value: string) => Promise<void>;
  label: string;
}

function EditableField({ value, onSave, label }: EditableFieldProps) {
  const [isEditing, setIsEditing] = useState(false);
  const { register, handleSubmit, reset } = useForm({
    defaultValues: { value },
  });

  const onSubmit = async (data: { value: string }) => {
    try {
      await onSave(data.value);
      setIsEditing(false);
    } catch (error) {
      // Handle error
    }
  };

  const handleCancel = () => {
    reset({ value });
    setIsEditing(false);
  };

  if (!isEditing) {
    return (
      <div className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
        <div>
          <span className="text-sm text-gray-500">{label}</span>
          <p>{value}</p>
        </div>
        <button
          onClick={() => setIsEditing(true)}
          className="text-blue-600 hover:text-blue-800"
        >
          Edit
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="p-2">
      <label className="text-sm text-gray-500">{label}</label>
      <div className="flex gap-2">
        <input
          {...register('value', { required: true })}
          className="flex-1 border rounded px-2 py-1"
          autoFocus
        />
        <button type="submit" className="text-green-600">Save</button>
        <button type="button" onClick={handleCancel} className="text-gray-600">
          Cancel
        </button>
      </div>
    </form>
  );
}
```

## Form with File Upload

```tsx
import { useForm, Controller } from 'react-hook-form';

interface ProfileFormValues {
  name: string;
  avatar: FileList | null;
  documents: FileList | null;
}

function ProfileForm() {
  const { register, control, handleSubmit, watch } = useForm<ProfileFormValues>();

  const avatar = watch('avatar');
  const avatarPreview = avatar?.[0] ? URL.createObjectURL(avatar[0]) : null;

  const onSubmit = async (data: ProfileFormValues) => {
    const formData = new FormData();
    formData.append('name', data.name);

    if (data.avatar?.[0]) {
      formData.append('avatar', data.avatar[0]);
    }

    if (data.documents) {
      Array.from(data.documents).forEach((file, index) => {
        formData.append(`documents[${index}]`, file);
      });
    }

    await uploadProfile(formData);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <div>
        <label>Name</label>
        <input {...register('name', { required: true })} />
      </div>

      <div>
        <label>Avatar</label>
        {avatarPreview && (
          <img src={avatarPreview} alt="Preview" className="w-20 h-20 rounded-full" />
        )}
        <input
          type="file"
          accept="image/*"
          {...register('avatar')}
        />
      </div>

      <div>
        <label>Documents</label>
        <input
          type="file"
          multiple
          accept=".pdf,.doc,.docx"
          {...register('documents')}
        />
      </div>

      <button type="submit">Save Profile</button>
    </form>
  );
}
```

## Best Practices Summary

1. **Validate early, show errors late** - Validate on change, show on blur/submit
2. **Use controlled components** - Better control and testing
3. **Provide immediate feedback** - Loading states, success messages
4. **Handle errors gracefully** - Clear error messages, retry options
5. **Support keyboard navigation** - Tab order, enter to submit
6. **Make forms accessible** - Labels, ARIA, error associations
7. **Persist draft data** - Auto-save, localStorage backup
8. **Progressive disclosure** - Show fields as needed
