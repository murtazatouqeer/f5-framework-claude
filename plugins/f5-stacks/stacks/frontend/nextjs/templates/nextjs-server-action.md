---
name: nextjs-server-action
description: Next.js Server Action template
applies_to: nextjs
variables:
  - name: ACTION_NAME
    description: Name of the action (e.g., createUser, updateProduct)
  - name: RESOURCE_NAME
    description: Resource being acted upon
  - name: HAS_REVALIDATION
    description: Whether action revalidates cache
---

# Next.js Server Action Template

## Basic Server Action

```ts
// lib/actions/{{RESOURCE_NAME}}.ts
"use server";

import { revalidatePath } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';

// Types
export type ActionState = {
  success?: boolean;
  error?: string;
  errors?: Record<string, string[]>;
  data?: any;
};

// Validation schemas
const create{{RESOURCE_NAME | pascal}}Schema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().max(1000).optional(),
  price: z.coerce.number().min(0).optional(),
});

const update{{RESOURCE_NAME | pascal}}Schema = create{{RESOURCE_NAME | pascal}}Schema.partial();

// CREATE
export async function create{{RESOURCE_NAME | pascal}}(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  try {
    const session = await auth();
    if (!session?.user) {
      return { error: 'Unauthorized' };
    }

    const rawData = {
      name: formData.get('name'),
      description: formData.get('description'),
      price: formData.get('price'),
    };

    const validated = create{{RESOURCE_NAME | pascal}}Schema.safeParse(rawData);

    if (!validated.success) {
      return {
        errors: validated.error.flatten().fieldErrors,
      };
    }

    const item = await db.{{RESOURCE_NAME | singular}}.create({
      data: {
        ...validated.data,
        userId: session.user.id,
      },
    });

    revalidatePath('/{{RESOURCE_NAME}}');

    return { success: true, data: item };
  } catch (error) {
    console.error('create{{RESOURCE_NAME | pascal}} error:', error);
    return { error: 'Failed to create {{RESOURCE_NAME | singular}}' };
  }
}

// UPDATE
export async function update{{RESOURCE_NAME | pascal}}(
  id: string,
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  try {
    const session = await auth();
    if (!session?.user) {
      return { error: 'Unauthorized' };
    }

    const item = await db.{{RESOURCE_NAME | singular}}.findUnique({
      where: { id },
    });

    if (!item) {
      return { error: '{{RESOURCE_NAME | pascal}} not found' };
    }

    if (item.userId !== session.user.id) {
      return { error: 'Forbidden' };
    }

    const rawData = {
      name: formData.get('name'),
      description: formData.get('description'),
      price: formData.get('price'),
    };

    const validated = update{{RESOURCE_NAME | pascal}}Schema.safeParse(rawData);

    if (!validated.success) {
      return {
        errors: validated.error.flatten().fieldErrors,
      };
    }

    const updated = await db.{{RESOURCE_NAME | singular}}.update({
      where: { id },
      data: validated.data,
    });

    revalidatePath('/{{RESOURCE_NAME}}');
    revalidatePath(`/{{RESOURCE_NAME}}/${id}`);

    return { success: true, data: updated };
  } catch (error) {
    console.error('update{{RESOURCE_NAME | pascal}} error:', error);
    return { error: 'Failed to update {{RESOURCE_NAME | singular}}' };
  }
}

// DELETE
export async function delete{{RESOURCE_NAME | pascal}}(id: string): Promise<ActionState> {
  try {
    const session = await auth();
    if (!session?.user) {
      return { error: 'Unauthorized' };
    }

    const item = await db.{{RESOURCE_NAME | singular}}.findUnique({
      where: { id },
    });

    if (!item) {
      return { error: '{{RESOURCE_NAME | pascal}} not found' };
    }

    if (item.userId !== session.user.id) {
      return { error: 'Forbidden' };
    }

    await db.{{RESOURCE_NAME | singular}}.delete({
      where: { id },
    });

    revalidatePath('/{{RESOURCE_NAME}}');

    return { success: true };
  } catch (error) {
    console.error('delete{{RESOURCE_NAME | pascal}} error:', error);
    return { error: 'Failed to delete {{RESOURCE_NAME | singular}}' };
  }
}
```

## Form Component with Server Action

```tsx
// components/{{RESOURCE_NAME}}-form.tsx
"use client";

import { useFormState, useFormStatus } from 'react-dom';
import { create{{RESOURCE_NAME | pascal}}, type ActionState } from '@/lib/actions/{{RESOURCE_NAME}}';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useEffect } from 'react';
import { toast } from 'sonner';

const initialState: ActionState = {};

function SubmitButton() {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" disabled={pending}>
      {pending ? 'Creating...' : 'Create'}
    </Button>
  );
}

export function {{RESOURCE_NAME | pascal}}Form() {
  const [state, formAction] = useFormState(create{{RESOURCE_NAME | pascal}}, initialState);

  useEffect(() => {
    if (state.success) {
      toast.success('{{RESOURCE_NAME | pascal}} created successfully');
    }
    if (state.error) {
      toast.error(state.error);
    }
  }, [state]);

  return (
    <form action={formAction} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          name="name"
          required
          aria-describedby="name-error"
        />
        {state.errors?.name && (
          <p id="name-error" className="text-sm text-destructive">
            {state.errors.name[0]}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          name="description"
          aria-describedby="description-error"
        />
        {state.errors?.description && (
          <p id="description-error" className="text-sm text-destructive">
            {state.errors.description[0]}
          </p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="price">Price</Label>
        <Input
          id="price"
          name="price"
          type="number"
          step="0.01"
          min="0"
          aria-describedby="price-error"
        />
        {state.errors?.price && (
          <p id="price-error" className="text-sm text-destructive">
            {state.errors.price[0]}
          </p>
        )}
      </div>

      <SubmitButton />
    </form>
  );
}
```

## Action with Optimistic Updates

```tsx
// components/{{RESOURCE_NAME}}-list.tsx
"use client";

import { useOptimistic, useTransition } from 'react';
import { delete{{RESOURCE_NAME | pascal}} } from '@/lib/actions/{{RESOURCE_NAME}}';
import { Button } from '@/components/ui/button';
import { Trash2 } from 'lucide-react';

interface {{RESOURCE_NAME | pascal}}ListProps {
  items: Array<{ id: string; name: string }>;
}

export function {{RESOURCE_NAME | pascal}}List({ items }: {{RESOURCE_NAME | pascal}}ListProps) {
  const [isPending, startTransition] = useTransition();
  const [optimisticItems, removeOptimistic] = useOptimistic(
    items,
    (state, deletedId: string) => state.filter((item) => item.id !== deletedId)
  );

  const handleDelete = (id: string) => {
    startTransition(async () => {
      removeOptimistic(id);
      await delete{{RESOURCE_NAME | pascal}}(id);
    });
  };

  return (
    <ul className="space-y-2">
      {optimisticItems.map((item) => (
        <li
          key={item.id}
          className="flex items-center justify-between p-4 border rounded-lg"
        >
          <span>{item.name}</span>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => handleDelete(item.id)}
            disabled={isPending}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </li>
      ))}
    </ul>
  );
}
```

## Action with Redirect

```ts
// lib/actions/auth.ts
"use server";

import { redirect } from 'next/navigation';
import { signIn, signOut } from '@/lib/auth';

export async function login(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  try {
    await signIn('credentials', {
      email: formData.get('email'),
      password: formData.get('password'),
      redirect: false,
    });
  } catch (error) {
    return { error: 'Invalid credentials' };
  }

  redirect('/dashboard');
}

export async function logout() {
  await signOut({ redirect: false });
  redirect('/');
}
```

## Action with File Upload

```ts
// lib/actions/upload.ts
"use server";

import { put } from '@vercel/blob';
import { auth } from '@/lib/auth';
import { db } from '@/lib/db';
import { revalidatePath } from 'next/cache';

export async function uploadAvatar(
  prevState: ActionState,
  formData: FormData
): Promise<ActionState> {
  try {
    const session = await auth();
    if (!session?.user) {
      return { error: 'Unauthorized' };
    }

    const file = formData.get('avatar') as File;

    if (!file || file.size === 0) {
      return { error: 'No file provided' };
    }

    // Validate file
    if (!file.type.startsWith('image/')) {
      return { error: 'File must be an image' };
    }

    if (file.size > 2 * 1024 * 1024) {
      return { error: 'File must be less than 2MB' };
    }

    // Upload to blob storage
    const blob = await put(`avatars/${session.user.id}`, file, {
      access: 'public',
    });

    // Update user record
    await db.user.update({
      where: { id: session.user.id },
      data: { image: blob.url },
    });

    revalidatePath('/settings');
    revalidatePath('/dashboard');

    return { success: true, data: { url: blob.url } };
  } catch (error) {
    console.error('uploadAvatar error:', error);
    return { error: 'Upload failed' };
  }
}
```

## Usage

```bash
f5 generate action createProduct --resource products
f5 generate action updateUser --resource users --revalidate
f5 generate action deleteItem --resource items
```
