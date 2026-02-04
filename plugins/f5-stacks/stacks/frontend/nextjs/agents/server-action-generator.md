# Next.js Server Action Generator Agent

## Role
Generate Next.js Server Actions for form handling and data mutations.

## Triggers
- "server action"
- "create action"
- "form action"

## Capabilities
- Generate Server Actions with "use server"
- Implement Zod validation
- Handle authentication
- Cache revalidation
- Redirect handling
- Optimistic updates support
- useFormState integration

## Input Requirements
```yaml
required:
  - name: string           # Action name (camelCase)
  - entity: string         # Entity to operate on

optional:
  - operation: string      # create | update | delete | toggle
  - auth_required: boolean # Requires authentication
  - validation: object     # Zod schema definition
  - revalidate: array      # Paths to revalidate
  - redirect_to: string    # Redirect after success
```

## Output Structure
```
lib/actions/
├── {entities}.ts         # Actions for entity
└── types.ts              # Shared action types (if needed)
```

## Generation Rules

### 1. Basic Server Action
```tsx
// lib/actions/products.ts
"use server";

import { revalidatePath, revalidateTag } from 'next/cache';
import { redirect } from 'next/navigation';
import { z } from 'zod';
import { db } from '@/lib/db';
import { auth } from '@/lib/auth';

// Schema definitions
const createProductSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(100),
  description: z.string().max(1000).optional(),
  price: z.coerce.number().min(0, 'Price must be positive'),
  categoryId: z.string().uuid('Invalid category'),
});

const updateProductSchema = createProductSchema.partial();

// Action state type
export type ProductActionState = {
  success: boolean;
  message: string;
  errors?: Record<string, string[]>;
  data?: unknown;
};

// Initial state
const initialState: ProductActionState = {
  success: false,
  message: '',
};

// Create action
export async function createProduct(
  prevState: ProductActionState,
  formData: FormData
): Promise<ProductActionState> {
  // Auth check
  const session = await auth();
  if (!session?.user) {
    return { success: false, message: 'Unauthorized' };
  }

  // Validate
  const validatedFields = createProductSchema.safeParse({
    name: formData.get('name'),
    description: formData.get('description'),
    price: formData.get('price'),
    categoryId: formData.get('categoryId'),
  });

  if (!validatedFields.success) {
    return {
      success: false,
      message: 'Validation failed',
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  try {
    const product = await db.product.create({
      data: {
        ...validatedFields.data,
        userId: session.user.id,
        slug: slugify(validatedFields.data.name),
      },
    });

    revalidatePath('/products');
    revalidateTag('products');

    return {
      success: true,
      message: 'Product created successfully',
      data: { id: product.id },
    };
  } catch (error) {
    console.error('Create product error:', error);
    return { success: false, message: 'Failed to create product' };
  }
}

// Update action
export async function updateProduct(
  id: string,
  prevState: ProductActionState,
  formData: FormData
): Promise<ProductActionState> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, message: 'Unauthorized' };
  }

  // Check ownership
  const existing = await db.product.findUnique({
    where: { id },
    select: { userId: true },
  });

  if (!existing) {
    return { success: false, message: 'Product not found' };
  }

  if (existing.userId !== session.user.id) {
    return { success: false, message: 'Forbidden' };
  }

  // Validate
  const validatedFields = updateProductSchema.safeParse({
    name: formData.get('name') || undefined,
    description: formData.get('description') || undefined,
    price: formData.get('price') || undefined,
    categoryId: formData.get('categoryId') || undefined,
  });

  if (!validatedFields.success) {
    return {
      success: false,
      message: 'Validation failed',
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  try {
    await db.product.update({
      where: { id },
      data: validatedFields.data,
    });

    revalidatePath(`/products/${id}`);
    revalidatePath('/products');

    return { success: true, message: 'Product updated successfully' };
  } catch (error) {
    console.error('Update product error:', error);
    return { success: false, message: 'Failed to update product' };
  }
}

// Delete action
export async function deleteProduct(id: string): Promise<ProductActionState> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, message: 'Unauthorized' };
  }

  const product = await db.product.findUnique({
    where: { id },
    select: { userId: true },
  });

  if (!product) {
    return { success: false, message: 'Product not found' };
  }

  if (product.userId !== session.user.id) {
    return { success: false, message: 'Forbidden' };
  }

  try {
    await db.product.delete({ where: { id } });

    revalidatePath('/products');
    revalidateTag('products');

    return { success: true, message: 'Product deleted successfully' };
  } catch (error) {
    console.error('Delete product error:', error);
    return { success: false, message: 'Failed to delete product' };
  }
}

// Helper
function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}
```

### 2. Toggle/Status Action
```tsx
// lib/actions/products.ts (continued)

export async function toggleProductStatus(
  id: string,
  status: 'active' | 'draft' | 'archived'
): Promise<ProductActionState> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, message: 'Unauthorized' };
  }

  try {
    await db.product.update({
      where: {
        id,
        userId: session.user.id,
      },
      data: { status },
    });

    revalidatePath(`/products/${id}`);
    revalidatePath('/products');

    return { success: true, message: `Product ${status}` };
  } catch (error) {
    console.error('Toggle product status error:', error);
    return { success: false, message: 'Failed to update status' };
  }
}

export async function toggleFavorite(productId: string): Promise<ProductActionState> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, message: 'Unauthorized' };
  }

  try {
    const existing = await db.favorite.findUnique({
      where: {
        userId_productId: {
          userId: session.user.id,
          productId,
        },
      },
    });

    if (existing) {
      await db.favorite.delete({
        where: { id: existing.id },
      });
      return { success: true, message: 'Removed from favorites' };
    } else {
      await db.favorite.create({
        data: {
          userId: session.user.id,
          productId,
        },
      });
      return { success: true, message: 'Added to favorites' };
    }
  } catch (error) {
    console.error('Toggle favorite error:', error);
    return { success: false, message: 'Failed to toggle favorite' };
  }
}
```

### 3. Batch Operations
```tsx
// lib/actions/products.ts (continued)

export async function deleteProducts(
  ids: string[]
): Promise<ProductActionState> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, message: 'Unauthorized' };
  }

  if (ids.length === 0) {
    return { success: false, message: 'No products selected' };
  }

  try {
    // Verify ownership
    const products = await db.product.findMany({
      where: {
        id: { in: ids },
        userId: session.user.id,
      },
      select: { id: true },
    });

    const ownedIds = products.map(p => p.id);

    if (ownedIds.length === 0) {
      return { success: false, message: 'No valid products to delete' };
    }

    await db.product.deleteMany({
      where: { id: { in: ownedIds } },
    });

    revalidatePath('/products');
    revalidateTag('products');

    return {
      success: true,
      message: `Deleted ${ownedIds.length} product(s)`
    };
  } catch (error) {
    console.error('Delete products error:', error);
    return { success: false, message: 'Failed to delete products' };
  }
}

export async function updateProductsStatus(
  ids: string[],
  status: 'active' | 'draft' | 'archived'
): Promise<ProductActionState> {
  const session = await auth();
  if (!session?.user) {
    return { success: false, message: 'Unauthorized' };
  }

  try {
    const result = await db.product.updateMany({
      where: {
        id: { in: ids },
        userId: session.user.id,
      },
      data: { status },
    });

    revalidatePath('/products');

    return {
      success: true,
      message: `Updated ${result.count} product(s)`
    };
  } catch (error) {
    console.error('Update products status error:', error);
    return { success: false, message: 'Failed to update products' };
  }
}
```

### 4. Form with Redirect
```tsx
// lib/actions/auth.ts
"use server";

import { z } from 'zod';
import { redirect } from 'next/navigation';
import { signIn, signOut } from '@/lib/auth';
import { AuthError } from 'next-auth';

export type AuthActionState = {
  success: boolean;
  message: string;
  errors?: Record<string, string[]>;
};

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
});

export async function login(
  prevState: AuthActionState,
  formData: FormData
): Promise<AuthActionState> {
  const validatedFields = loginSchema.safeParse({
    email: formData.get('email'),
    password: formData.get('password'),
  });

  if (!validatedFields.success) {
    return {
      success: false,
      message: 'Validation failed',
      errors: validatedFields.error.flatten().fieldErrors,
    };
  }

  try {
    await signIn('credentials', {
      email: validatedFields.data.email,
      password: validatedFields.data.password,
      redirect: false,
    });
  } catch (error) {
    if (error instanceof AuthError) {
      switch (error.type) {
        case 'CredentialsSignin':
          return { success: false, message: 'Invalid credentials' };
        default:
          return { success: false, message: 'Something went wrong' };
      }
    }
    throw error;
  }

  redirect('/dashboard');
}

export async function logout() {
  await signOut({ redirectTo: '/' });
}
```

### 5. Client Component Integration
```tsx
// components/delete-button.tsx
"use client";

import { useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { deleteProduct } from '@/lib/actions/products';
import { Button } from '@/components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Trash2, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface DeleteButtonProps {
  productId: string;
  productName: string;
}

export function DeleteButton({ productId, productName }: DeleteButtonProps) {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const handleDelete = () => {
    startTransition(async () => {
      const result = await deleteProduct(productId);

      if (result.success) {
        toast.success(result.message);
        router.push('/products');
      } else {
        toast.error(result.message);
      }
    });
  };

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive" size="sm" disabled={isPending}>
          {isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
          <span className="ml-2">Delete</span>
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Product</AlertDialogTitle>
          <AlertDialogDescription>
            Are you sure you want to delete "{productName}"?
            This action cannot be undone.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction onClick={handleDelete}>
            Delete
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

## Validation Checklist
- [ ] "use server" directive at top
- [ ] Zod validation for all inputs
- [ ] Authentication checks
- [ ] Authorization (ownership) checks
- [ ] Proper error handling with try/catch
- [ ] Meaningful error messages
- [ ] revalidatePath/revalidateTag for cache
- [ ] TypeScript types for state
- [ ] No sensitive data in responses
- [ ] Logging for debugging
