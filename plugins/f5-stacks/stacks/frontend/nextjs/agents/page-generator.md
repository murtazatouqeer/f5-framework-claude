# Next.js Page Generator Agent

## Role
Generate Next.js App Router pages with proper Server/Client Component patterns.

## Triggers
- "create page"
- "generate page"
- "nextjs page"
- "next page"

## Capabilities
- Generate page.tsx with proper typing
- Create associated loading.tsx and error.tsx
- Generate metadata configuration
- Create generateStaticParams for static generation
- Generate layout.tsx when needed
- Implement data fetching patterns

## Input Requirements
```yaml
required:
  - route: string          # Route path (e.g., "products", "products/[id]")
  - purpose: string        # Page purpose description

optional:
  - has_params: boolean    # Has dynamic route params
  - has_search: boolean    # Has search params
  - fetch_data: boolean    # Needs data fetching
  - has_form: boolean      # Contains forms
  - is_static: boolean     # Static generation
  - metadata: object       # Page metadata
```

## Output Structure
```
app/{route}/
├── page.tsx              # Main page component
├── loading.tsx           # Loading UI
├── error.tsx             # Error boundary
├── layout.tsx            # Route layout (if needed)
├── not-found.tsx         # 404 for route (if needed)
└── components/           # Page-specific components
    ├── {entity}-list.tsx
    └── {entity}-card.tsx
```

## Generation Rules

### 1. Page Component Pattern
```tsx
// Server Component by default
import { Suspense } from 'react';
import { Metadata } from 'next';
import { notFound } from 'next/navigation';

interface PageProps {
  params: { id: string };
  searchParams: { [key: string]: string | string[] | undefined };
}

export const metadata: Metadata = {
  title: 'Page Title',
  description: 'Page description',
};

export default async function Page({ params, searchParams }: PageProps) {
  // Data fetching at page level
  const data = await fetchData(params.id);

  if (!data) {
    notFound();
  }

  return (
    <div className="container py-8">
      <Suspense fallback={<Loading />}>
        <Content data={data} />
      </Suspense>
    </div>
  );
}
```

### 2. Dynamic Metadata
```tsx
export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const data = await getData(params.id);

  if (!data) {
    return { title: 'Not Found' };
  }

  return {
    title: data.name,
    description: data.description,
    openGraph: {
      title: data.name,
      images: data.image ? [data.image] : [],
    },
  };
}
```

### 3. Static Generation
```tsx
export async function generateStaticParams() {
  const items = await db.item.findMany({
    select: { id: true },
    where: { status: 'published' },
    take: 100,
  });

  return items.map((item) => ({
    id: item.id,
  }));
}
```

### 4. Loading UI
```tsx
// loading.tsx
import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return (
    <div className="container py-8">
      <Skeleton className="h-10 w-64 mb-8" />
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-48 rounded-lg" />
        ))}
      </div>
    </div>
  );
}
```

### 5. Error Boundary
```tsx
// error.tsx
'use client';

import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { AlertCircle } from 'lucide-react';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="container py-16 text-center">
      <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
      <h2 className="text-xl font-semibold mb-2">Something went wrong!</h2>
      <p className="text-muted-foreground mb-6">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  );
}
```

## Page Types

### List Page
```tsx
// app/products/page.tsx
import { Suspense } from 'react';
import { ProductList } from './product-list';
import { ProductFilters } from './product-filters';
import { ProductListSkeleton } from './product-list-skeleton';

interface ProductsPageProps {
  searchParams: {
    page?: string;
    q?: string;
    category?: string;
  };
}

export default function ProductsPage({ searchParams }: ProductsPageProps) {
  return (
    <div className="container py-8">
      <h1 className="text-3xl font-bold mb-8">Products</h1>

      <ProductFilters />

      <Suspense
        key={JSON.stringify(searchParams)}
        fallback={<ProductListSkeleton />}
      >
        <ProductList searchParams={searchParams} />
      </Suspense>
    </div>
  );
}
```

### Detail Page
```tsx
// app/products/[id]/page.tsx
import { notFound } from 'next/navigation';
import { cache } from 'react';
import { db } from '@/lib/db';

const getProduct = cache(async (id: string) => {
  return db.product.findUnique({
    where: { id },
    include: { category: true, reviews: { take: 10 } },
  });
});

export default async function ProductPage({
  params
}: {
  params: { id: string }
}) {
  const product = await getProduct(params.id);

  if (!product) {
    notFound();
  }

  return (
    <div className="container py-8">
      <ProductDetails product={product} />
    </div>
  );
}
```

### Form Page
```tsx
// app/products/new/page.tsx
import { redirect } from 'next/navigation';
import { auth } from '@/lib/auth';
import { ProductForm } from './product-form';

export default async function NewProductPage() {
  const session = await auth();

  if (!session?.user) {
    redirect('/login');
  }

  return (
    <div className="container max-w-2xl py-8">
      <h1 className="text-2xl font-bold mb-8">Create Product</h1>
      <ProductForm />
    </div>
  );
}
```

## Validation Checklist
- [ ] Page has proper TypeScript typing
- [ ] Server Component by default (no "use client")
- [ ] Loading.tsx created for data-fetching pages
- [ ] Error.tsx created for error handling
- [ ] Metadata configured properly
- [ ] Data fetching uses async/await at page level
- [ ] Suspense boundaries for streaming
- [ ] Not-found handling with notFound()
- [ ] generateStaticParams for static routes
- [ ] Proper redirect for auth-protected pages
