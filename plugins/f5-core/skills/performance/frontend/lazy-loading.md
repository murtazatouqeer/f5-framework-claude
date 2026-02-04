---
name: lazy-loading
description: Lazy loading techniques for images, components, and data
category: performance/frontend
applies_to: frontend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Lazy Loading

## Overview

Lazy loading defers loading of non-critical resources until they're needed,
reducing initial page load time and saving bandwidth.

## Image Lazy Loading

### Native Browser Lazy Loading

```html
<!-- Native lazy loading - simplest approach -->
<img
  src="image.jpg"
  loading="lazy"
  alt="Description"
  width="800"
  height="600"
/>

<!-- For iframes -->
<iframe
  src="video.html"
  loading="lazy"
  width="560"
  height="315"
></iframe>
```

### Intersection Observer

```typescript
// Custom lazy loading with Intersection Observer
function lazyLoadImages(): void {
  const images = document.querySelectorAll<HTMLImageElement>('img[data-src]');

  const observer = new IntersectionObserver((entries, obs) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement;
        img.src = img.dataset.src!;
        img.removeAttribute('data-src');
        obs.unobserve(img);
      }
    });
  }, {
    rootMargin: '100px', // Load 100px before visible
    threshold: 0.01,
  });

  images.forEach((img) => observer.observe(img));
}

// HTML usage
// <img data-src="image.jpg" alt="Description" />
```

### React Lazy Image Component

```typescript
import { useState, useRef, useEffect } from 'react';

interface LazyImageProps {
  src: string;
  alt: string;
  placeholder?: string;
  className?: string;
}

function LazyImage({ src, alt, placeholder, className }: LazyImageProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isInView, setIsInView] = useState(false);
  const imgRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { rootMargin: '100px' }
    );

    if (imgRef.current) {
      observer.observe(imgRef.current);
    }

    return () => observer.disconnect();
  }, []);

  return (
    <div className={`lazy-image-wrapper ${className}`}>
      {/* Placeholder */}
      {!isLoaded && (
        <div className="placeholder">
          {placeholder ? (
            <img src={placeholder} alt="" aria-hidden />
          ) : (
            <div className="skeleton" />
          )}
        </div>
      )}

      {/* Actual image */}
      <img
        ref={imgRef}
        src={isInView ? src : undefined}
        alt={alt}
        onLoad={() => setIsLoaded(true)}
        style={{ opacity: isLoaded ? 1 : 0 }}
      />
    </div>
  );
}
```

### Progressive Image Loading

```typescript
// Low quality image placeholder (LQIP)
function ProgressiveImage({ lowResSrc, highResSrc, alt }: {
  lowResSrc: string;
  highResSrc: string;
  alt: string;
}) {
  const [currentSrc, setCurrentSrc] = useState(lowResSrc);
  const [isHighResLoaded, setIsHighResLoaded] = useState(false);

  useEffect(() => {
    const img = new Image();
    img.src = highResSrc;
    img.onload = () => {
      setCurrentSrc(highResSrc);
      setIsHighResLoaded(true);
    };
  }, [highResSrc]);

  return (
    <img
      src={currentSrc}
      alt={alt}
      className={isHighResLoaded ? '' : 'blur'}
    />
  );
}

// CSS
// .blur { filter: blur(10px); transition: filter 0.3s; }
```

## Component Lazy Loading

### React.lazy with Suspense

```typescript
import { lazy, Suspense } from 'react';

// Lazy load component
const HeavyComponent = lazy(() => import('./HeavyComponent'));

// With retry logic
const HeavyComponentWithRetry = lazy(() =>
  retryImport(() => import('./HeavyComponent'), 3)
);

async function retryImport<T>(
  fn: () => Promise<T>,
  retries: number
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries > 0) {
      await new Promise((r) => setTimeout(r, 1000));
      return retryImport(fn, retries - 1);
    }
    throw error;
  }
}

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <HeavyComponent />
    </Suspense>
  );
}
```

### Conditional Component Loading

```typescript
function Dashboard() {
  const [showAnalytics, setShowAnalytics] = useState(false);

  return (
    <div>
      <button onClick={() => setShowAnalytics(true)}>
        Show Analytics
      </button>

      {showAnalytics && (
        <Suspense fallback={<AnalyticsSkeleton />}>
          <LazyAnalyticsPanel />
        </Suspense>
      )}
    </div>
  );
}

// Analytics only loaded when button clicked
const LazyAnalyticsPanel = lazy(() => import('./AnalyticsPanel'));
```

### Viewport-Based Loading

```typescript
import { useInView } from 'react-intersection-observer';

function LazySection() {
  const { ref, inView } = useInView({
    triggerOnce: true,
    rootMargin: '200px',
  });

  return (
    <div ref={ref}>
      {inView ? (
        <Suspense fallback={<SectionSkeleton />}>
          <HeavySection />
        </Suspense>
      ) : (
        <SectionPlaceholder />
      )}
    </div>
  );
}
```

## Data Lazy Loading

### Infinite Scroll

```typescript
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';

function ProductList() {
  const { ref, inView } = useInView();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['products'],
    queryFn: ({ pageParam = 0 }) => fetchProducts(pageParam),
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  return (
    <div>
      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.products.map((product) => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ))}

      <div ref={ref}>
        {isFetchingNextPage && <LoadingSpinner />}
      </div>
    </div>
  );
}
```

### Virtualized Lists

```typescript
import { FixedSizeList as List } from 'react-window';

function VirtualizedProductList({ products }: { products: Product[] }) {
  const Row = ({ index, style }: { index: number; style: React.CSSProperties }) => (
    <div style={style}>
      <ProductCard product={products[index]} />
    </div>
  );

  return (
    <List
      height={600}
      itemCount={products.length}
      itemSize={100}
      width="100%"
    >
      {Row}
    </List>
  );
}

// For variable size items
import { VariableSizeList } from 'react-window';

function VariableHeightList({ items }: { items: Item[] }) {
  const getItemSize = (index: number) => items[index].height;

  return (
    <VariableSizeList
      height={600}
      itemCount={items.length}
      itemSize={getItemSize}
      width="100%"
    >
      {Row}
    </VariableSizeList>
  );
}
```

### Lazy Data Fetching

```typescript
// Load data only when component mounts
function UserProfile({ userId }: { userId: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
    enabled: true, // Or conditionally enable
  });

  if (isLoading) return <ProfileSkeleton />;
  return <Profile user={data} />;
}

// Prefetch on hover
function UserLink({ userId }: { userId: string }) {
  const queryClient = useQueryClient();

  const prefetchUser = () => {
    queryClient.prefetchQuery({
      queryKey: ['user', userId],
      queryFn: () => fetchUser(userId),
      staleTime: 60000,
    });
  };

  return (
    <Link
      to={`/users/${userId}`}
      onMouseEnter={prefetchUser}
    >
      View Profile
    </Link>
  );
}
```

## Script Lazy Loading

```typescript
// Load third-party scripts lazily
function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = src;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load ${src}`));
    document.body.appendChild(script);
  });
}

// Load analytics on user interaction
function initAnalytics() {
  // Load after first interaction
  const events = ['mousedown', 'keydown', 'touchstart', 'scroll'];

  const loadAnalytics = async () => {
    events.forEach((e) => document.removeEventListener(e, loadAnalytics));

    await loadScript('https://www.google-analytics.com/analytics.js');
    // Initialize analytics
  };

  events.forEach((e) => document.addEventListener(e, loadAnalytics, { once: true }));
}

// Load on idle
if ('requestIdleCallback' in window) {
  requestIdleCallback(() => loadScript('non-critical.js'));
} else {
  setTimeout(() => loadScript('non-critical.js'), 2000);
}
```

## Preloading for Better UX

```typescript
// Preload on route change intention
function NavLink({ to, children }: { to: string; children: React.ReactNode }) {
  const preload = () => {
    // Preload the route's code
    switch (to) {
      case '/dashboard':
        import('./pages/Dashboard');
        break;
      case '/settings':
        import('./pages/Settings');
        break;
    }
  };

  return (
    <Link to={to} onMouseEnter={preload}>
      {children}
    </Link>
  );
}

// Resource hints
function Head() {
  return (
    <head>
      {/* Preload critical resources */}
      <link rel="preload" href="/fonts/main.woff2" as="font" crossOrigin="" />
      <link rel="preload" href="/api/critical-data" as="fetch" crossOrigin="" />

      {/* Prefetch likely next pages */}
      <link rel="prefetch" href="/dashboard.js" />

      {/* DNS prefetch for third parties */}
      <link rel="dns-prefetch" href="//api.example.com" />
      <link rel="preconnect" href="//api.example.com" />
    </head>
  );
}
```

## Best Practices

1. **Use native loading="lazy"** - Simplest for images/iframes
2. **Set dimensions** - Prevent layout shift
3. **Use placeholders** - Better perceived performance
4. **Preload critical resources** - Above-the-fold content
5. **Virtualize long lists** - Don't render invisible items
6. **Prefetch on intent** - Hover, focus events
7. **Handle errors gracefully** - Retry logic for failed loads
8. **Test on slow connections** - Simulate 3G speeds
