# React Page Generator Agent

## Purpose
Generate React page components with routing, data fetching, and layout integration.

## Triggers
- "create page"
- "generate page"
- "react page"
- "new route"

## Input Requirements

```yaml
required:
  - page_name: string       # PascalCase page name
  - route_path: string      # URL path for routing

optional:
  - layout: string          # Layout component to use
  - auth_required: boolean  # Requires authentication
  - data_fetching: string   # 'server' | 'client' | 'hybrid'
  - params: array           # Route parameters
  - search_params: array    # Query parameters
  - meta: object            # Page metadata (title, description)
```

## Generation Process

### 1. Analyze Requirements
- Determine data fetching strategy
- Identify required hooks and state
- Check authentication requirements
- Plan component structure

### 2. Generate Page Structure
```
src/features/{feature}/pages/
├── {PageName}Page.tsx        # Main page component
├── {PageName}Page.test.tsx   # Page tests
└── components/               # Page-specific components
    └── {PageName}Content.tsx
```

### 3. Apply Patterns

#### Basic Page Template
```tsx
// src/features/{feature}/pages/{PageName}Page.tsx
import { Suspense } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { PageLayout } from '@/components/layouts/PageLayout';
import { PageHeader } from '@/components/ui/PageHeader';
import { Skeleton } from '@/components/ui/Skeleton';
import { {PageName}Content } from './components/{PageName}Content';

export function {PageName}Page() {
  const params = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();

  return (
    <PageLayout>
      <PageHeader
        title="{Page Title}"
        description="{Page description}"
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: '{Page Name}', href: '/{route}' },
        ]}
      />

      <Suspense fallback={<Skeleton className="h-96" />}>
        <{PageName}Content id={params.id} />
      </Suspense>
    </PageLayout>
  );
}
```

#### Page with Data Fetching
```tsx
// src/features/{feature}/pages/{PageName}Page.tsx
import { useQuery } from '@tanstack/react-query';
import { PageLayout } from '@/components/layouts/PageLayout';
import { LoadingState } from '@/components/ui/LoadingState';
import { ErrorState } from '@/components/ui/ErrorState';
import { {entity}Api } from '../api/{entity}.api';
import { {PageName}Content } from './components/{PageName}Content';

export function {PageName}Page() {
  const { id } = useParams<{ id: string }>();

  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['{entity}', id],
    queryFn: () => {entity}Api.getById(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return <LoadingState message="Loading {entity}..." />;
  }

  if (isError) {
    return (
      <ErrorState
        title="Failed to load {entity}"
        message={error.message}
        onRetry={refetch}
      />
    );
  }

  if (!data) {
    return <ErrorState title="{Entity} not found" />;
  }

  return (
    <PageLayout>
      <{PageName}Content data={data} />
    </PageLayout>
  );
}
```

#### Protected Page Template
```tsx
// src/features/{feature}/pages/{PageName}Page.tsx
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { PageLayout } from '@/components/layouts/PageLayout';
import { LoadingState } from '@/components/ui/LoadingState';

export function {PageName}Page() {
  const { user, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return <LoadingState />;
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <PageLayout>
      {/* Page content */}
    </PageLayout>
  );
}
```

### 4. Generate Route Configuration
```tsx
// src/app/routes.tsx
import { lazy } from 'react';
import { RouteObject } from 'react-router-dom';

const {PageName}Page = lazy(() =>
  import('@/features/{feature}/pages/{PageName}Page').then(m => ({ default: m.{PageName}Page }))
);

export const routes: RouteObject[] = [
  {
    path: '/{route}',
    element: <{PageName}Page />,
    // loader: async ({ params }) => { ... }, // Optional data loader
  },
  {
    path: '/{route}/:id',
    element: <{PageName}DetailPage />,
  },
];
```

## Output Files

1. **Page Component**: Main page with layout and data fetching
2. **Page Content**: Separated content component
3. **Page Tests**: Testing file with route and data tests
4. **Route Config**: Route configuration update

## Quality Checks

- [ ] Proper loading and error states
- [ ] SEO metadata configured
- [ ] Authentication checks if required
- [ ] Responsive layout
- [ ] Accessibility (page title, landmarks)
- [ ] Route parameters typed correctly
- [ ] Data fetching optimized
