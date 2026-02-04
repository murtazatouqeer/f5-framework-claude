# Next.js Component Generator Agent

## Role
Generate Next.js components with proper Server/Client Component patterns.

## Triggers
- "create component"
- "nextjs component"
- "server component"
- "client component"

## Capabilities
- Generate Server Components (default)
- Generate Client Components ("use client")
- Create component compositions
- Generate loading/error states
- Implement proper TypeScript types
- Handle data fetching patterns

## Input Requirements
```yaml
required:
  - name: string           # Component name (PascalCase)
  - type: string           # server | client

optional:
  - props: object          # Component props definition
  - fetches_data: boolean  # Requires data fetching
  - has_form: boolean      # Contains form elements
  - children: boolean      # Accepts children
  - variants: array        # Component variants
```

## Output Structure
```
components/
├── {name}.tsx            # Main component
├── {name}.test.tsx       # Test file (if requested)
└── {name}-skeleton.tsx   # Loading skeleton (if data-fetching)
```

## Generation Rules

### 1. Server Component (Default)
```tsx
// components/product-card.tsx
import Image from 'next/image';
import Link from 'next/link';
import { formatCurrency } from '@/lib/utils';

interface Product {
  id: string;
  name: string;
  description: string | null;
  price: number;
  imageUrl: string | null;
  category: { name: string };
}

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  return (
    <Link
      href={`/products/${product.id}`}
      className="group block rounded-lg border bg-card overflow-hidden hover:shadow-lg transition-shadow"
    >
      <div className="aspect-square relative bg-muted">
        {product.imageUrl ? (
          <Image
            src={product.imageUrl}
            alt={product.name}
            fill
            className="object-cover group-hover:scale-105 transition-transform"
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
            No image
          </div>
        )}
      </div>
      <div className="p-4">
        <p className="text-sm text-muted-foreground mb-1">
          {product.category.name}
        </p>
        <h3 className="font-semibold line-clamp-1 group-hover:text-primary transition-colors">
          {product.name}
        </h3>
        {product.description && (
          <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
            {product.description}
          </p>
        )}
        <p className="font-bold mt-2">
          {formatCurrency(product.price)}
        </p>
      </div>
    </Link>
  );
}
```

### 2. Client Component
```tsx
// components/search-input.tsx
"use client";

import { useState, useTransition } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Input } from '@/components/ui/input';
import { Search, X, Loader2 } from 'lucide-react';
import { useDebouncedCallback } from 'use-debounce';

interface SearchInputProps {
  placeholder?: string;
  paramName?: string;
}

export function SearchInput({
  placeholder = 'Search...',
  paramName = 'q'
}: SearchInputProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [isPending, startTransition] = useTransition();
  const [value, setValue] = useState(searchParams.get(paramName) ?? '');

  const handleSearch = useDebouncedCallback((term: string) => {
    startTransition(() => {
      const params = new URLSearchParams(searchParams);

      if (term) {
        params.set(paramName, term);
        params.delete('page'); // Reset pagination
      } else {
        params.delete(paramName);
      }

      router.push(`?${params.toString()}`);
    });
  }, 300);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setValue(newValue);
    handleSearch(newValue);
  };

  const handleClear = () => {
    setValue('');
    handleSearch('');
  };

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        type="search"
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        className="pl-10 pr-10"
      />
      {isPending ? (
        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-muted-foreground" />
      ) : value ? (
        <button
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      ) : null}
    </div>
  );
}
```

### 3. Data-Fetching Server Component
```tsx
// components/product-list.tsx
import { db } from '@/lib/db';
import { ProductCard } from './product-card';
import { Pagination } from './pagination';

interface ProductListProps {
  searchParams: {
    page?: string;
    q?: string;
    category?: string;
  };
}

export async function ProductList({ searchParams }: ProductListProps) {
  const page = Number(searchParams.page) || 1;
  const limit = 12;
  const skip = (page - 1) * limit;

  const where = {
    status: 'active' as const,
    ...(searchParams.q && {
      OR: [
        { name: { contains: searchParams.q, mode: 'insensitive' as const } },
        { description: { contains: searchParams.q, mode: 'insensitive' as const } },
      ],
    }),
    ...(searchParams.category && {
      categoryId: searchParams.category,
    }),
  };

  const [products, total] = await Promise.all([
    db.product.findMany({
      where,
      include: { category: true },
      skip,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    db.product.count({ where }),
  ]);

  if (products.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No products found</p>
      </div>
    );
  }

  const totalPages = Math.ceil(total / limit);

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {products.map((product) => (
          <ProductCard key={product.id} product={product} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="mt-8">
          <Pagination currentPage={page} totalPages={totalPages} />
        </div>
      )}
    </div>
  );
}
```

### 4. Interactive Form Component
```tsx
// components/product-form.tsx
"use client";

import { useFormState, useFormStatus } from 'react-dom';
import { createProduct, updateProduct, type ProductActionState } from '@/lib/actions/products';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Loader2 } from 'lucide-react';

interface Category {
  id: string;
  name: string;
}

interface Product {
  id: string;
  name: string;
  description: string | null;
  price: number;
  categoryId: string;
}

interface ProductFormProps {
  product?: Product;
  categories: Category[];
}

const initialState: ProductActionState = {
  success: false,
  message: '',
};

function SubmitButton({ isEdit }: { isEdit: boolean }) {
  const { pending } = useFormStatus();

  return (
    <Button type="submit" disabled={pending}>
      {pending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {pending ? 'Saving...' : isEdit ? 'Update Product' : 'Create Product'}
    </Button>
  );
}

export function ProductForm({ product, categories }: ProductFormProps) {
  const action = product
    ? updateProduct.bind(null, product.id)
    : createProduct;
  const [state, formAction] = useFormState(action, initialState);

  return (
    <form action={formAction} className="space-y-6">
      {state.message && !state.success && (
        <Alert variant="destructive">
          <AlertDescription>{state.message}</AlertDescription>
        </Alert>
      )}

      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          name="name"
          defaultValue={product?.name}
          required
        />
        {state.errors?.name && (
          <p className="text-sm text-destructive">{state.errors.name[0]}</p>
        )}
      </div>

      <div className="space-y-2">
        <Label htmlFor="description">Description</Label>
        <Textarea
          id="description"
          name="description"
          defaultValue={product?.description ?? ''}
          rows={4}
        />
        {state.errors?.description && (
          <p className="text-sm text-destructive">{state.errors.description[0]}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="price">Price</Label>
          <Input
            id="price"
            name="price"
            type="number"
            step="0.01"
            min="0"
            defaultValue={product?.price}
            required
          />
          {state.errors?.price && (
            <p className="text-sm text-destructive">{state.errors.price[0]}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="categoryId">Category</Label>
          <Select name="categoryId" defaultValue={product?.categoryId}>
            <SelectTrigger>
              <SelectValue placeholder="Select category" />
            </SelectTrigger>
            <SelectContent>
              {categories.map((category) => (
                <SelectItem key={category.id} value={category.id}>
                  {category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {state.errors?.categoryId && (
            <p className="text-sm text-destructive">{state.errors.categoryId[0]}</p>
          )}
        </div>
      </div>

      <div className="flex gap-4">
        <SubmitButton isEdit={!!product} />
      </div>
    </form>
  );
}
```

### 5. Loading Skeleton
```tsx
// components/product-card-skeleton.tsx
import { Skeleton } from '@/components/ui/skeleton';

export function ProductCardSkeleton() {
  return (
    <div className="rounded-lg border bg-card overflow-hidden">
      <Skeleton className="aspect-square" />
      <div className="p-4 space-y-2">
        <Skeleton className="h-4 w-1/3" />
        <Skeleton className="h-5 w-3/4" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-5 w-1/4 mt-2" />
      </div>
    </div>
  );
}

export function ProductListSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <ProductCardSkeleton key={i} />
      ))}
    </div>
  );
}
```

## Component Decision Tree

```
Need interactivity?
├─ Yes → Client Component ("use client")
│   ├─ Uses hooks (useState, useEffect, etc.)
│   ├─ Event handlers (onClick, onChange, etc.)
│   ├─ Browser APIs (localStorage, etc.)
│   └─ Third-party libraries requiring browser
│
└─ No → Server Component (default)
    ├─ Data fetching (async/await)
    ├─ Direct database access
    ├─ Server-only code
    └─ Static rendering
```

## Validation Checklist
- [ ] "use client" only when needed
- [ ] Proper TypeScript interfaces for props
- [ ] Accessible markup (ARIA, semantic HTML)
- [ ] Loading/error states handled
- [ ] Proper image optimization (next/image)
- [ ] Link components use next/link
- [ ] Proper className handling (cn utility)
- [ ] No unused props or imports
