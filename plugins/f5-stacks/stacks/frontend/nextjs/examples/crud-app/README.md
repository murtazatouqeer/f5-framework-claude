# CRUD Application Example

A complete CRUD (Create, Read, Update, Delete) application built with Next.js 14+ App Router.

## Features

- Server Components for data fetching
- Server Actions for mutations
- Optimistic updates
- Form validation with Zod
- Loading and error states
- Pagination and search

## Project Structure

```
app/
├── products/
│   ├── page.tsx              # Product listing (Server Component)
│   ├── loading.tsx           # Loading state
│   ├── error.tsx             # Error boundary
│   ├── [id]/
│   │   ├── page.tsx          # Product detail
│   │   ├── edit/
│   │   │   └── page.tsx      # Edit form
│   │   └── not-found.tsx     # 404 page
│   └── new/
│       └── page.tsx          # Create form
├── api/
│   └── products/
│       ├── route.ts          # GET (list), POST (create)
│       └── [id]/
│           └── route.ts      # GET, PATCH, DELETE
lib/
├── actions/
│   └── products.ts           # Server Actions
├── db.ts                     # Database client
└── validations/
    └── product.ts            # Zod schemas
components/
├── products/
│   ├── product-list.tsx      # Product list component
│   ├── product-card.tsx      # Product card
│   ├── product-form.tsx      # Create/Edit form
│   └── delete-button.tsx     # Delete with confirmation
└── ui/
    ├── pagination.tsx
    ├── search-input.tsx
    └── skeleton.tsx
```

## Key Patterns

### Server Component (Data Fetching)

```tsx
// app/products/page.tsx
export default async function ProductsPage({
  searchParams,
}: {
  searchParams: { page?: string; search?: string };
}) {
  const page = Number(searchParams.page) || 1;
  const search = searchParams.search || '';

  const { products, total } = await getProducts({ page, search });

  return (
    <main>
      <h1>Products</h1>
      <SearchInput defaultValue={search} />
      <ProductList products={products} />
      <Pagination currentPage={page} total={total} />
    </main>
  );
}
```

### Server Action (Mutation)

```tsx
// lib/actions/products.ts
"use server";

import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const schema = z.object({
  name: z.string().min(1),
  price: z.coerce.number().positive(),
});

export async function createProduct(prevState: any, formData: FormData) {
  const validated = schema.safeParse({
    name: formData.get('name'),
    price: formData.get('price'),
  });

  if (!validated.success) {
    return { errors: validated.error.flatten().fieldErrors };
  }

  await db.product.create({ data: validated.data });

  revalidatePath('/products');
  return { success: true };
}
```

### Client Component (Form)

```tsx
// components/products/product-form.tsx
"use client";

import { useFormState, useFormStatus } from 'react-dom';
import { createProduct } from '@/lib/actions/products';

export function ProductForm() {
  const [state, formAction] = useFormState(createProduct, {});

  return (
    <form action={formAction}>
      <input name="name" />
      {state.errors?.name && <p>{state.errors.name}</p>}

      <input name="price" type="number" />
      {state.errors?.price && <p>{state.errors.price}</p>}

      <SubmitButton />
    </form>
  );
}

function SubmitButton() {
  const { pending } = useFormStatus();
  return <button disabled={pending}>{pending ? 'Saving...' : 'Save'}</button>;
}
```

### Optimistic Updates

```tsx
// components/products/product-list.tsx
"use client";

import { useOptimistic, useTransition } from 'react';
import { deleteProduct } from '@/lib/actions/products';

export function ProductList({ products }) {
  const [isPending, startTransition] = useTransition();
  const [optimisticProducts, removeProduct] = useOptimistic(
    products,
    (state, id) => state.filter((p) => p.id !== id)
  );

  const handleDelete = (id: string) => {
    startTransition(async () => {
      removeProduct(id);
      await deleteProduct(id);
    });
  };

  return (
    <ul>
      {optimisticProducts.map((product) => (
        <li key={product.id}>
          {product.name}
          <button onClick={() => handleDelete(product.id)}>Delete</button>
        </li>
      ))}
    </ul>
  );
}
```

## Database Schema (Prisma)

```prisma
model Product {
  id          String   @id @default(cuid())
  name        String
  description String?
  price       Float
  image       String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  userId      String
  user        User     @relation(fields: [userId], references: [id])
}
```

## Getting Started

```bash
# Clone the example
npx create-next-app --example f5-crud-app my-crud-app

# Install dependencies
npm install

# Set up database
npx prisma db push

# Run development server
npm run dev
```

## Environment Variables

```env
DATABASE_URL="postgresql://..."
NEXTAUTH_SECRET="your-secret"
NEXTAUTH_URL="http://localhost:3000"
```
