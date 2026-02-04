---
name: nextjs-page
description: Next.js App Router page template
applies_to: nextjs
variables:
  - name: PAGE_NAME
    description: Name of the page (e.g., Dashboard, Products)
  - name: ROUTE_PATH
    description: Route path for the page
  - name: IS_DYNAMIC
    description: Whether page has dynamic params
  - name: PARAM_NAME
    description: Dynamic parameter name if applicable
---

# Next.js Page Template

## Static Page

```tsx
// app/{{ROUTE_PATH}}/page.tsx
import { Metadata } from 'next';
import { {{PAGE_NAME}}View } from './_components/{{PAGE_NAME | kebab}}-view';

export const metadata: Metadata = {
  title: '{{PAGE_NAME}}',
  description: '{{PAGE_NAME}} page description',
};

export default async function {{PAGE_NAME}}Page() {
  // Fetch data on the server
  const data = await getData();

  return (
    <main className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">{{PAGE_NAME}}</h1>
      <{{PAGE_NAME}}View data={data} />
    </main>
  );
}

async function getData() {
  // Server-side data fetching
  const res = await fetch('{{API_URL}}/{{ROUTE_PATH}}', {
    cache: 'force-cache', // or 'no-store' for dynamic
  });

  if (!res.ok) {
    throw new Error('Failed to fetch data');
  }

  return res.json();
}
```

## Dynamic Page

```tsx
// app/{{ROUTE_PATH}}/[{{PARAM_NAME}}]/page.tsx
import { Metadata } from 'next';
import { notFound } from 'next/navigation';
import { {{PAGE_NAME}}Detail } from './_components/{{PAGE_NAME | kebab}}-detail';

interface {{PAGE_NAME}}PageProps {
  params: { {{PARAM_NAME}}: string };
}

export async function generateMetadata({
  params,
}: {{PAGE_NAME}}PageProps): Promise<Metadata> {
  const item = await getItem(params.{{PARAM_NAME}});

  if (!item) {
    return { title: 'Not Found' };
  }

  return {
    title: item.name,
    description: item.description,
  };
}

export async function generateStaticParams() {
  const items = await getItems();

  return items.map((item) => ({
    {{PARAM_NAME}}: item.id,
  }));
}

export default async function {{PAGE_NAME}}Page({ params }: {{PAGE_NAME}}PageProps) {
  const item = await getItem(params.{{PARAM_NAME}});

  if (!item) {
    notFound();
  }

  return (
    <main className="container mx-auto py-8">
      <{{PAGE_NAME}}Detail item={item} />
    </main>
  );
}

async function getItem(id: string) {
  const res = await fetch(`{{API_URL}}/{{ROUTE_PATH}}/${id}`, {
    next: { revalidate: 3600 },
  });

  if (!res.ok) return null;
  return res.json();
}

async function getItems() {
  const res = await fetch('{{API_URL}}/{{ROUTE_PATH}}');
  if (!res.ok) return [];
  return res.json();
}
```

## Protected Page

```tsx
// app/{{ROUTE_PATH}}/page.tsx
import { Metadata } from 'next';
import { redirect } from 'next/navigation';
import { auth } from '@/lib/auth';
import { {{PAGE_NAME}}View } from './_components/{{PAGE_NAME | kebab}}-view';

export const metadata: Metadata = {
  title: '{{PAGE_NAME}}',
};

export default async function {{PAGE_NAME}}Page() {
  const session = await auth();

  if (!session?.user) {
    redirect('/login?callbackUrl=/{{ROUTE_PATH}}');
  }

  const data = await getData(session.user.id);

  return (
    <main className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">{{PAGE_NAME}}</h1>
      <{{PAGE_NAME}}View data={data} user={session.user} />
    </main>
  );
}

async function getData(userId: string) {
  // Fetch user-specific data
  return [];
}
```

## Page with Search Params

```tsx
// app/{{ROUTE_PATH}}/page.tsx
import { Metadata } from 'next';
import { {{PAGE_NAME}}List } from './_components/{{PAGE_NAME | kebab}}-list';
import { Pagination } from '@/components/ui/pagination';
import { SearchForm } from './_components/search-form';

interface {{PAGE_NAME}}PageProps {
  searchParams: {
    page?: string;
    search?: string;
    sort?: string;
  };
}

export const metadata: Metadata = {
  title: '{{PAGE_NAME}}',
};

export default async function {{PAGE_NAME}}Page({
  searchParams,
}: {{PAGE_NAME}}PageProps) {
  const page = Number(searchParams.page) || 1;
  const search = searchParams.search || '';
  const sort = searchParams.sort || 'createdAt';

  const { items, total } = await getItems({ page, search, sort });

  return (
    <main className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">{{PAGE_NAME}}</h1>

      <SearchForm defaultValue={search} />

      <{{PAGE_NAME}}List items={items} />

      <Pagination
        currentPage={page}
        totalPages={Math.ceil(total / 10)}
        basePath="/{{ROUTE_PATH}}"
      />
    </main>
  );
}

async function getItems({
  page,
  search,
  sort,
}: {
  page: number;
  search: string;
  sort: string;
}) {
  const params = new URLSearchParams({
    page: String(page),
    search,
    sort,
    limit: '10',
  });

  const res = await fetch(`{{API_URL}}/{{ROUTE_PATH}}?${params}`, {
    next: { revalidate: 60 },
  });

  if (!res.ok) {
    return { items: [], total: 0 };
  }

  return res.json();
}
```

## Usage

Generate a page:
```bash
f5 generate page Dashboard --route dashboard
f5 generate page ProductDetail --route products --dynamic --param id
```
