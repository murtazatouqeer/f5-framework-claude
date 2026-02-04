# React Page Template

Production-ready page templates for React applications with TypeScript.

## Basic Page Template

```tsx
// pages/{{PageName}}/{{PageName}}Page.tsx
import { type FC } from 'react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { PageHeader } from '@/components/layouts/PageHeader';
import { PageContent } from '@/components/layouts/PageContent';

export interface {{PageName}}PageProps {
  /** Page title for browser tab */
  title?: string;
}

export const {{PageName}}Page: FC<{{PageName}}PageProps> = ({
  title = '{{PageName}}',
}) => {
  useDocumentTitle(title);

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title="{{PageName}}"
        description="Description of this page"
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: '{{PageName}}', href: '/{{page-name}}' },
        ]}
      />

      <PageContent>
        {/* Page content here */}
        <div className="space-y-6">
          <section>
            <h2 className="text-xl font-semibold mb-4">Section Title</h2>
            <p className="text-muted-foreground">
              Page content goes here.
            </p>
          </section>
        </div>
      </PageContent>
    </div>
  );
};

// Export for route configuration
export default {{PageName}}Page;
```

## Page with Data Fetching

```tsx
// pages/{{PageName}}/{{PageName}}Page.tsx
import { Suspense, type FC } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useSearchParams } from 'react-router-dom';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { PageHeader } from '@/components/layouts/PageHeader';
import { PageContent } from '@/components/layouts/PageContent';
import { Skeleton } from '@/components/ui/Skeleton';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { EmptyState } from '@/components/ui/EmptyState';
import { api } from '@/lib/api';
import type { {{Entity}} } from '@/types';

// Data fetching function
async function fetch{{Entity}}s(params: { page: number; search?: string }) {
  const response = await api.get<{
    data: {{Entity}}[];
    meta: { total: number; page: number; totalPages: number };
  }>('/{{entities}}', { params });
  return response.data;
}

export const {{PageName}}Page: FC = () => {
  useDocumentTitle('{{PageName}}');

  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get('page')) || 1;
  const search = searchParams.get('search') || '';

  // Data query
  const {
    data,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ['{{entities}}', { page, search }],
    queryFn: () => fetch{{Entity}}s({ page, search }),
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <PageHeader title="{{PageName}}" />
        <PageContent>
          <{{PageName}}Skeleton />
        </PageContent>
      </div>
    );
  }

  // Error state
  if (isError) {
    return (
      <div className="min-h-screen bg-background">
        <PageHeader title="{{PageName}}" />
        <PageContent>
          <ErrorState
            title="Failed to load data"
            message={error?.message || 'An error occurred'}
            onRetry={refetch}
          />
        </PageContent>
      </div>
    );
  }

  // Empty state
  if (!data?.data.length) {
    return (
      <div className="min-h-screen bg-background">
        <PageHeader title="{{PageName}}" />
        <PageContent>
          <EmptyState
            title="No {{entities}} found"
            description="Get started by creating your first {{entity}}."
            action={{
              label: 'Create {{Entity}}',
              href: '/{{entities}}/new',
            }}
          />
        </PageContent>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title="{{PageName}}"
        description={`${data.meta.total} {{entities}}`}
        actions={
          <Button asChild>
            <Link to="/{{entities}}/new">Create {{Entity}}</Link>
          </Button>
        }
      />

      <PageContent>
        <div className="space-y-6">
          {/* Search and filters */}
          <SearchFilters
            value={search}
            onChange={(value) => {
              setSearchParams({ page: '1', search: value });
            }}
          />

          {/* Data list */}
          <{{Entity}}List items={data.data} />

          {/* Pagination */}
          <Pagination
            currentPage={data.meta.page}
            totalPages={data.meta.totalPages}
            onPageChange={(newPage) => {
              setSearchParams({ page: String(newPage), search });
            }}
          />
        </div>
      </PageContent>
    </div>
  );
};

// Skeleton component
function {{PageName}}Skeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-10 w-full max-w-sm" />
      <div className="grid gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
    </div>
  );
}

export default {{PageName}}Page;
```

## Detail Page Template

```tsx
// pages/{{EntityName}}/{{EntityName}}DetailPage.tsx
import { type FC } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ArrowLeft, Edit, Trash2 } from 'lucide-react';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { PageHeader } from '@/components/layouts/PageHeader';
import { PageContent } from '@/components/layouts/PageContent';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useToast } from '@/hooks/useToast';
import { api } from '@/lib/api';
import type { {{Entity}} } from '@/types';

async function fetch{{Entity}}(id: string): Promise<{{Entity}}> {
  const response = await api.get(`/{{entities}}/${id}`);
  return response.data;
}

async function delete{{Entity}}(id: string): Promise<void> {
  await api.delete(`/{{entities}}/${id}`);
}

export const {{EntityName}}DetailPage: FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  // Fetch data
  const {
    data: {{entity}},
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['{{entity}}', id],
    queryFn: () => fetch{{Entity}}(id!),
    enabled: !!id,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: delete{{Entity}},
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{{entities}}'] });
      toast({
        title: '{{Entity}} deleted',
        description: 'The {{entity}} has been deleted successfully.',
      });
      navigate('/{{entities}}');
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  useDocumentTitle({{entity}}?.name || '{{Entity}} Details');

  if (isLoading) {
    return <{{EntityName}}DetailSkeleton />;
  }

  if (isError || !{{entity}}) {
    return (
      <ErrorState
        title="{{Entity}} not found"
        message={error?.message || 'The {{entity}} could not be loaded.'}
        action={{
          label: 'Go back',
          onClick: () => navigate('/{{entities}}'),
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title={{{entity}}.name}
        description={`Created ${formatDate({{entity}}.createdAt)}`}
        breadcrumbs={[
          { label: 'Home', href: '/' },
          { label: '{{Entities}}', href: '/{{entities}}' },
          { label: {{entity}}.name },
        ]}
        backLink="/{{entities}}"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link to={`/{{entities}}/${id}/edit`}>
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Link>
            </Button>
            <ConfirmDialog
              title="Delete {{Entity}}"
              description="Are you sure you want to delete this {{entity}}? This action cannot be undone."
              onConfirm={() => deleteMutation.mutate(id!)}
              confirmText="Delete"
              variant="destructive"
            >
              <Button variant="destructive" isLoading={deleteMutation.isPending}>
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </Button>
            </ConfirmDialog>
          </div>
        }
      />

      <PageContent>
        <div className="grid gap-6 md:grid-cols-3">
          {/* Main content */}
          <div className="md:col-span-2 space-y-6">
            <Card>
              <Card.Header>
                <Card.Title>Details</Card.Title>
              </Card.Header>
              <Card.Content>
                <dl className="grid gap-4 sm:grid-cols-2">
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Name</dt>
                    <dd className="text-sm">{{{entity}}.name}</dd>
                  </div>
                  <div>
                    <dt className="text-sm font-medium text-muted-foreground">Status</dt>
                    <dd className="text-sm">
                      <Badge variant={{{entity}}.status === 'active' ? 'success' : 'secondary'}>
                        {{{entity}}.status}
                      </Badge>
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-sm font-medium text-muted-foreground">Description</dt>
                    <dd className="text-sm">{{{entity}}.description || 'No description'}</dd>
                  </div>
                </dl>
              </Card.Content>
            </Card>

            {/* Related data sections */}
            <Card>
              <Card.Header>
                <Card.Title>Related Items</Card.Title>
              </Card.Header>
              <Card.Content>
                {/* Related items list */}
              </Card.Content>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <Card.Header>
                <Card.Title>Metadata</Card.Title>
              </Card.Header>
              <Card.Content className="space-y-4">
                <div>
                  <span className="text-sm text-muted-foreground">Created</span>
                  <p className="text-sm">{formatDate({{entity}}.createdAt)}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">Updated</span>
                  <p className="text-sm">{formatDate({{entity}}.updatedAt)}</p>
                </div>
                <div>
                  <span className="text-sm text-muted-foreground">ID</span>
                  <p className="text-sm font-mono text-xs">{{{entity}}.id}</p>
                </div>
              </Card.Content>
            </Card>
          </div>
        </div>
      </PageContent>
    </div>
  );
};

function {{EntityName}}DetailSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <PageHeader title={<Skeleton className="h-8 w-48" />} />
      <PageContent>
        <div className="grid gap-6 md:grid-cols-3">
          <div className="md:col-span-2 space-y-6">
            <Card>
              <Card.Header>
                <Skeleton className="h-6 w-24" />
              </Card.Header>
              <Card.Content>
                <div className="grid gap-4 sm:grid-cols-2">
                  {Array.from({ length: 4 }).map((_, i) => (
                    <Skeleton key={i} className="h-12 w-full" />
                  ))}
                </div>
              </Card.Content>
            </Card>
          </div>
          <div>
            <Card>
              <Card.Content className="space-y-4 pt-6">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full" />
                ))}
              </Card.Content>
            </Card>
          </div>
        </div>
      </PageContent>
    </div>
  );
}

export default {{EntityName}}DetailPage;
```

## Create/Edit Page Template

```tsx
// pages/{{EntityName}}/{{EntityName}}FormPage.tsx
import { type FC } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { PageHeader } from '@/components/layouts/PageHeader';
import { PageContent } from '@/components/layouts/PageContent';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { {{EntityName}}Form } from '@/features/{{entities}}/components/{{EntityName}}Form';
import { useToast } from '@/hooks/useToast';
import { api } from '@/lib/api';
import type { {{Entity}}, Create{{Entity}}Input, Update{{Entity}}Input } from '@/types';

async function fetch{{Entity}}(id: string): Promise<{{Entity}}> {
  const response = await api.get(`/{{entities}}/${id}`);
  return response.data;
}

async function create{{Entity}}(data: Create{{Entity}}Input): Promise<{{Entity}}> {
  const response = await api.post('/{{entities}}', data);
  return response.data;
}

async function update{{Entity}}(id: string, data: Update{{Entity}}Input): Promise<{{Entity}}> {
  const response = await api.patch(`/{{entities}}/${id}`, data);
  return response.data;
}

export const {{EntityName}}FormPage: FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { toast } = useToast();

  const isEditing = !!id;

  // Fetch existing data for editing
  const { data: {{entity}}, isLoading } = useQuery({
    queryKey: ['{{entity}}', id],
    queryFn: () => fetch{{Entity}}(id!),
    enabled: isEditing,
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: create{{Entity}},
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['{{entities}}'] });
      toast({
        title: '{{Entity}} created',
        description: 'The {{entity}} has been created successfully.',
      });
      navigate(`/{{entities}}/${data.id}`);
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (data: Update{{Entity}}Input) => update{{Entity}}(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['{{entity}}', id] });
      queryClient.invalidateQueries({ queryKey: ['{{entities}}'] });
      toast({
        title: '{{Entity}} updated',
        description: 'The {{entity}} has been updated successfully.',
      });
      navigate(`/{{entities}}/${id}`);
    },
    onError: (error) => {
      toast({
        title: 'Error',
        description: error.message,
        variant: 'destructive',
      });
    },
  });

  const handleSubmit = async (data: Create{{Entity}}Input | Update{{Entity}}Input) => {
    if (isEditing) {
      await updateMutation.mutateAsync(data);
    } else {
      await createMutation.mutateAsync(data as Create{{Entity}}Input);
    }
  };

  const isSubmitting = createMutation.isPending || updateMutation.isPending;

  useDocumentTitle(isEditing ? `Edit ${{{entity}}?.name || '{{Entity}}'}` : 'Create {{Entity}}');

  if (isEditing && isLoading) {
    return <FormPageSkeleton />;
  }

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title={isEditing ? 'Edit {{Entity}}' : 'Create {{Entity}}'}
        description={
          isEditing
            ? 'Update the {{entity}} details below.'
            : 'Fill in the details to create a new {{entity}}.'
        }
        backLink={isEditing ? `/{{entities}}/${id}` : '/{{entities}}'}
      />

      <PageContent>
        <Card className="max-w-2xl">
          <Card.Content className="pt-6">
            <{{EntityName}}Form
              defaultValues={{{entity}}}
              onSubmit={handleSubmit}
              onCancel={() => navigate(isEditing ? `/{{entities}}/${id}` : '/{{entities}}')}
              isSubmitting={isSubmitting}
            />
          </Card.Content>
        </Card>
      </PageContent>
    </div>
  );
};

function FormPageSkeleton() {
  return (
    <div className="min-h-screen bg-background">
      <PageHeader title={<Skeleton className="h-8 w-32" />} />
      <PageContent>
        <Card className="max-w-2xl">
          <Card.Content className="pt-6 space-y-6">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-2">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-10 w-full" />
              </div>
            ))}
            <div className="flex justify-end gap-4">
              <Skeleton className="h-10 w-24" />
              <Skeleton className="h-10 w-24" />
            </div>
          </Card.Content>
        </Card>
      </PageContent>
    </div>
  );
}

export default {{EntityName}}FormPage;
```

## Dashboard Page Template

```tsx
// pages/Dashboard/DashboardPage.tsx
import { type FC } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useDocumentTitle } from '@/hooks/useDocumentTitle';
import { PageHeader } from '@/components/layouts/PageHeader';
import { PageContent } from '@/components/layouts/PageContent';
import { Card } from '@/components/ui/Card';
import { Skeleton } from '@/components/ui/Skeleton';
import { StatsCard } from '@/components/dashboard/StatsCard';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { ChartCard } from '@/components/dashboard/ChartCard';
import { api } from '@/lib/api';

interface DashboardStats {
  totalUsers: number;
  totalOrders: number;
  revenue: number;
  growth: number;
}

async function fetchDashboardStats(): Promise<DashboardStats> {
  const response = await api.get('/dashboard/stats');
  return response.data;
}

export const DashboardPage: FC = () => {
  useDocumentTitle('Dashboard');

  const { data: stats, isLoading } = useQuery({
    queryKey: ['dashboard', 'stats'],
    queryFn: fetchDashboardStats,
  });

  return (
    <div className="min-h-screen bg-background">
      <PageHeader
        title="Dashboard"
        description="Overview of your application"
      />

      <PageContent>
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {isLoading ? (
              Array.from({ length: 4 }).map((_, i) => (
                <Card key={i}>
                  <Card.Content className="pt-6">
                    <Skeleton className="h-4 w-24 mb-2" />
                    <Skeleton className="h-8 w-16" />
                  </Card.Content>
                </Card>
              ))
            ) : (
              <>
                <StatsCard
                  title="Total Users"
                  value={stats?.totalUsers || 0}
                  icon="users"
                  trend={{ value: 12, isPositive: true }}
                />
                <StatsCard
                  title="Total Orders"
                  value={stats?.totalOrders || 0}
                  icon="shopping-cart"
                  trend={{ value: 8, isPositive: true }}
                />
                <StatsCard
                  title="Revenue"
                  value={stats?.revenue || 0}
                  icon="dollar-sign"
                  format="currency"
                  trend={{ value: 15, isPositive: true }}
                />
                <StatsCard
                  title="Growth"
                  value={stats?.growth || 0}
                  icon="trending-up"
                  format="percentage"
                />
              </>
            )}
          </div>

          {/* Charts Row */}
          <div className="grid gap-6 md:grid-cols-2">
            <ChartCard
              title="Revenue Over Time"
              chartType="line"
              dataKey="revenue"
            />
            <ChartCard
              title="Orders by Category"
              chartType="bar"
              dataKey="orders"
            />
          </div>

          {/* Bottom Row */}
          <div className="grid gap-6 md:grid-cols-3">
            <Card className="md:col-span-2">
              <Card.Header>
                <Card.Title>Recent Activity</Card.Title>
              </Card.Header>
              <Card.Content>
                <RecentActivity />
              </Card.Content>
            </Card>

            <Card>
              <Card.Header>
                <Card.Title>Quick Actions</Card.Title>
              </Card.Header>
              <Card.Content className="space-y-2">
                <Button className="w-full justify-start" variant="ghost">
                  Create New Order
                </Button>
                <Button className="w-full justify-start" variant="ghost">
                  Add User
                </Button>
                <Button className="w-full justify-start" variant="ghost">
                  View Reports
                </Button>
              </Card.Content>
            </Card>
          </div>
        </div>
      </PageContent>
    </div>
  );
};

export default DashboardPage;
```

## Page Layout Components

```tsx
// components/layouts/PageHeader.tsx
import { type FC, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: ReactNode;
  description?: ReactNode;
  breadcrumbs?: Breadcrumb[];
  backLink?: string;
  actions?: ReactNode;
  className?: string;
}

export const PageHeader: FC<PageHeaderProps> = ({
  title,
  description,
  breadcrumbs,
  backLink,
  actions,
  className,
}) => {
  return (
    <header className={cn('border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60', className)}>
      <div className="container py-6">
        {/* Breadcrumbs */}
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="flex items-center text-sm text-muted-foreground mb-4">
            {breadcrumbs.map((crumb, index) => (
              <span key={index} className="flex items-center">
                {index > 0 && <ChevronRight className="h-4 w-4 mx-2" />}
                {crumb.href ? (
                  <Link to={crumb.href} className="hover:text-foreground transition-colors">
                    {crumb.label}
                  </Link>
                ) : (
                  <span className="text-foreground">{crumb.label}</span>
                )}
              </span>
            ))}
          </nav>
        )}

        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-4">
              {backLink && (
                <Button variant="ghost" size="icon" asChild>
                  <Link to={backLink}>
                    <ArrowLeft className="h-4 w-4" />
                  </Link>
                </Button>
              )}
              <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
            </div>
            {description && (
              <p className="text-muted-foreground">{description}</p>
            )}
          </div>

          {actions && (
            <div className="flex items-center gap-2 shrink-0">
              {actions}
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

// components/layouts/PageContent.tsx
import { type FC, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface PageContentProps {
  children: ReactNode;
  className?: string;
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
}

const maxWidthClasses = {
  sm: 'max-w-screen-sm',
  md: 'max-w-screen-md',
  lg: 'max-w-screen-lg',
  xl: 'max-w-screen-xl',
  '2xl': 'max-w-screen-2xl',
  full: 'max-w-full',
};

export const PageContent: FC<PageContentProps> = ({
  children,
  className,
  maxWidth = 'full',
}) => {
  return (
    <main className={cn('container py-6', maxWidthClasses[maxWidth], className)}>
      {children}
    </main>
  );
};
```

## Route Configuration

```tsx
// app/routes.tsx
import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider, Outlet } from 'react-router-dom';
import { MainLayout } from '@/components/layouts/MainLayout';
import { LoadingPage } from '@/components/LoadingPage';
import { ErrorPage } from '@/components/ErrorPage';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

// Lazy load pages
const DashboardPage = lazy(() => import('@/pages/Dashboard/DashboardPage'));
const {{EntityName}}ListPage = lazy(() => import('@/pages/{{EntityName}}/{{EntityName}}ListPage'));
const {{EntityName}}DetailPage = lazy(() => import('@/pages/{{EntityName}}/{{EntityName}}DetailPage'));
const {{EntityName}}FormPage = lazy(() => import('@/pages/{{EntityName}}/{{EntityName}}FormPage'));
const LoginPage = lazy(() => import('@/pages/Auth/LoginPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

// Suspense wrapper
function SuspenseWrapper({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<LoadingPage />}>{children}</Suspense>;
}

const router = createBrowserRouter([
  {
    path: '/',
    element: <MainLayout />,
    errorElement: <ErrorPage />,
    children: [
      {
        index: true,
        element: (
          <ProtectedRoute>
            <SuspenseWrapper>
              <DashboardPage />
            </SuspenseWrapper>
          </ProtectedRoute>
        ),
      },
      {
        path: '{{entities}}',
        element: <Outlet />,
        children: [
          {
            index: true,
            element: (
              <ProtectedRoute>
                <SuspenseWrapper>
                  <{{EntityName}}ListPage />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: 'new',
            element: (
              <ProtectedRoute>
                <SuspenseWrapper>
                  <{{EntityName}}FormPage />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: ':id',
            element: (
              <ProtectedRoute>
                <SuspenseWrapper>
                  <{{EntityName}}DetailPage />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
          {
            path: ':id/edit',
            element: (
              <ProtectedRoute>
                <SuspenseWrapper>
                  <{{EntityName}}FormPage />
                </SuspenseWrapper>
              </ProtectedRoute>
            ),
          },
        ],
      },
    ],
  },
  {
    path: '/login',
    element: (
      <SuspenseWrapper>
        <LoginPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: '*',
    element: (
      <SuspenseWrapper>
        <NotFoundPage />
      </SuspenseWrapper>
    ),
  },
]);

export function AppRoutes() {
  return <RouterProvider router={router} />;
}
```

## Best Practices

1. **Use layouts for consistent structure** - PageHeader, PageContent
2. **Handle all states** - Loading, error, empty, success
3. **Lazy load pages** - Code splitting for performance
4. **Protect routes** - Authentication guards
5. **Set document title** - useDocumentTitle hook
6. **Breadcrumbs** - Navigation context
7. **Consistent actions** - Edit, delete, create patterns
