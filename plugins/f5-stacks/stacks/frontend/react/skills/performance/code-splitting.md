# Code Splitting

## Overview

Techniques for splitting JavaScript bundles to improve initial load time.

## Route-Based Splitting

```tsx
import { lazy, Suspense } from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';

// Lazy load route components
const Home = lazy(() => import('./pages/Home'));
const Products = lazy(() => import('./pages/Products'));
const ProductDetail = lazy(() => import('./pages/ProductDetail'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings = lazy(() => import('./pages/Settings'));

// Loading component
function PageLoader() {
  return (
    <div className="flex items-center justify-center h-screen">
      <Spinner size="lg" />
    </div>
  );
}

// Router with suspense
const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: (
          <Suspense fallback={<PageLoader />}>
            <Home />
          </Suspense>
        ),
      },
      {
        path: 'products',
        element: (
          <Suspense fallback={<PageLoader />}>
            <Products />
          </Suspense>
        ),
      },
      {
        path: 'products/:id',
        element: (
          <Suspense fallback={<PageLoader />}>
            <ProductDetail />
          </Suspense>
        ),
      },
      {
        path: 'dashboard',
        element: (
          <Suspense fallback={<PageLoader />}>
            <Dashboard />
          </Suspense>
        ),
      },
      {
        path: 'settings',
        element: (
          <Suspense fallback={<PageLoader />}>
            <Settings />
          </Suspense>
        ),
      },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}
```

## Component-Based Splitting

```tsx
import { lazy, Suspense, useState } from 'react';

// Heavy components
const Chart = lazy(() => import('./components/Chart'));
const RichTextEditor = lazy(() => import('./components/RichTextEditor'));
const MapView = lazy(() => import('./components/MapView'));

function Dashboard() {
  const [showChart, setShowChart] = useState(false);
  const [showEditor, setShowEditor] = useState(false);

  return (
    <div>
      <button onClick={() => setShowChart(true)}>Show Chart</button>
      <button onClick={() => setShowEditor(true)}>Show Editor</button>

      {showChart && (
        <Suspense fallback={<Skeleton height={400} />}>
          <Chart data={chartData} />
        </Suspense>
      )}

      {showEditor && (
        <Suspense fallback={<Skeleton height={300} />}>
          <RichTextEditor />
        </Suspense>
      )}
    </div>
  );
}
```

## Feature-Based Splitting

```tsx
// features/analytics/index.ts
export const AnalyticsDashboard = lazy(
  () => import('./components/AnalyticsDashboard')
);
export const ReportGenerator = lazy(
  () => import('./components/ReportGenerator')
);

// features/admin/index.ts
export const AdminPanel = lazy(() => import('./components/AdminPanel'));
export const UserManagement = lazy(() => import('./components/UserManagement'));

// Usage
import { AnalyticsDashboard, ReportGenerator } from '@/features/analytics';
import { AdminPanel } from '@/features/admin';

function AdminRoute() {
  return (
    <Suspense fallback={<PageLoader />}>
      <AdminPanel />
    </Suspense>
  );
}
```

## Named Exports with Lazy

```tsx
// Export specific component from module
const ProductCard = lazy(() =>
  import('./components/ProductCard').then((module) => ({
    default: module.ProductCard,
  }))
);

// Multiple exports
const { ProductCard, ProductList, ProductGrid } = {
  ProductCard: lazy(() =>
    import('./components/Product').then((m) => ({ default: m.ProductCard }))
  ),
  ProductList: lazy(() =>
    import('./components/Product').then((m) => ({ default: m.ProductList }))
  ),
  ProductGrid: lazy(() =>
    import('./components/Product').then((m) => ({ default: m.ProductGrid }))
  ),
};
```

## Prefetching

```tsx
import { useEffect } from 'react';

// Preload component on hover
function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const preloadComponent = () => {
    const componentMap: Record<string, () => Promise<any>> = {
      '/dashboard': () => import('./pages/Dashboard'),
      '/settings': () => import('./pages/Settings'),
      '/profile': () => import('./pages/Profile'),
    };

    if (componentMap[to]) {
      componentMap[to]();
    }
  };

  return (
    <Link to={to} onMouseEnter={preloadComponent}>
      {children}
    </Link>
  );
}

// Preload on route transition
function usePreloadRoute(to: string, importFn: () => Promise<any>) {
  useEffect(() => {
    // Start loading after initial render
    const timer = setTimeout(() => {
      importFn();
    }, 2000);

    return () => clearTimeout(timer);
  }, [importFn]);
}

// Preload next likely route
function ProductListPage() {
  useEffect(() => {
    // User likely to click on a product
    import('./pages/ProductDetail');
  }, []);

  return <ProductList />;
}
```

## Dynamic Imports for Utilities

```tsx
// Load heavy libraries on demand
async function generatePDF(data: ReportData) {
  const { jsPDF } = await import('jspdf');
  const doc = new jsPDF();
  // Generate PDF
  return doc;
}

async function processImage(file: File) {
  const sharp = await import('sharp');
  // Process image
}

async function exportToExcel(data: any[]) {
  const XLSX = await import('xlsx');
  const worksheet = XLSX.utils.json_to_sheet(data);
  // Create workbook and download
}

// Usage in component
function ReportButton({ data }: { data: ReportData }) {
  const [isGenerating, setIsGenerating] = useState(false);

  const handleClick = async () => {
    setIsGenerating(true);
    try {
      const pdf = await generatePDF(data);
      pdf.save('report.pdf');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <button onClick={handleClick} disabled={isGenerating}>
      {isGenerating ? 'Generating...' : 'Download PDF'}
    </button>
  );
}
```

## Error Boundaries for Lazy Components

```tsx
import { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback: ReactNode;
}

interface State {
  hasError: boolean;
}

class LazyErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Lazy load error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback;
    }
    return this.props.children;
  }
}

// Usage
<LazyErrorBoundary fallback={<ErrorPage />}>
  <Suspense fallback={<PageLoader />}>
    <LazyComponent />
  </Suspense>
</LazyErrorBoundary>
```

## Vite/Webpack Configuration

```ts
// vite.config.ts
import { defineConfig } from 'vite';

export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          react: ['react', 'react-dom'],
          router: ['react-router-dom'],
          query: ['@tanstack/react-query'],
          ui: ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        },
      },
    },
  },
});
```

## Best Practices

1. **Split by route** - Each route in separate chunk
2. **Split heavy components** - Charts, editors, maps
3. **Prefetch intelligently** - Preload likely next pages
4. **Use meaningful fallbacks** - Skeleton loaders, spinners
5. **Handle errors** - Error boundaries for failed loads
6. **Analyze bundle** - Use bundle analyzer to identify opportunities
