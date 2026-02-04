# Frontend Performance Reference

## Core Web Vitals

### LCP (Largest Contentful Paint) < 2.5s

```typescript
// 1. Preload critical resources
// In HTML head:
<link rel="preload" href="/hero-image.webp" as="image" />
<link rel="preload" href="/critical-font.woff2" as="font" crossorigin />

// 2. Priority hints for images
<img
  src="/hero.webp"
  alt="Hero"
  fetchpriority="high"
  loading="eager"
/>

// 3. Inline critical CSS
<style>
  /* Critical above-the-fold styles */
  .hero { ... }
</style>

// 4. Server-side rendering for LCP element
// Next.js - ensure LCP content is in initial HTML
export default function Page({ data }) {
  return <HeroSection data={data} />;
}

export async function getServerSideProps() {
  const data = await fetchHeroData();
  return { props: { data } };
}
```

### INP (Interaction to Next Paint) < 200ms

```typescript
// 1. Use React transitions for non-urgent updates
import { useTransition, useState } from 'react';

function SearchComponent() {
  const [isPending, startTransition] = useTransition();
  const [results, setResults] = useState([]);

  const handleSearch = (query: string) => {
    // Urgent: Update input immediately
    setQuery(query);

    // Non-urgent: Defer expensive filtering
    startTransition(() => {
      setResults(filterResults(query));
    });
  };

  return (
    <>
      <input onChange={e => handleSearch(e.target.value)} />
      {isPending ? <Spinner /> : <Results data={results} />}
    </>
  );
}

// 2. Debounce expensive handlers
import { useDebouncedCallback } from 'use-debounce';

function ExpensiveComponent() {
  const debouncedHandler = useDebouncedCallback(
    (value) => performExpensiveOperation(value),
    300
  );

  return <input onChange={e => debouncedHandler(e.target.value)} />;
}

// 3. Web Workers for heavy computation
const worker = new Worker(new URL('./heavy-worker.ts', import.meta.url));

worker.postMessage({ data: largeDataset });
worker.onmessage = (e) => {
  setProcessedData(e.data);
};
```

### CLS (Cumulative Layout Shift) < 0.1

```css
/* 1. Always set dimensions for media */
img, video {
  width: 100%;
  height: auto;
  aspect-ratio: 16 / 9;
}

/* 2. Reserve space for dynamic content */
.ad-container {
  min-height: 250px;
}

.skeleton {
  height: 200px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

/* 3. Prevent font swap layout shift */
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: swap;
  size-adjust: 100%;
  ascent-override: 90%;
  descent-override: 20%;
}
```

```typescript
// 4. Skeleton UI component
function SkeletonCard() {
  return (
    <div className="skeleton-card">
      <div className="skeleton skeleton-image" style={{ aspectRatio: '16/9' }} />
      <div className="skeleton skeleton-title" style={{ height: '24px' }} />
      <div className="skeleton skeleton-text" style={{ height: '16px' }} />
    </div>
  );
}

// 5. Avoid layout-triggering properties in animations
// BAD: Triggers layout
.animated {
  animation: move 0.3s;
}
@keyframes move {
  to { left: 100px; }
}

// GOOD: Use transform (GPU accelerated)
.animated {
  animation: move 0.3s;
}
@keyframes move {
  to { transform: translateX(100px); }
}
```

## Bundle Optimization

### Code Splitting

```typescript
// Next.js dynamic imports
import dynamic from 'next/dynamic';

const HeavyChart = dynamic(() => import('@/components/HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false // Client-side only
});

// React.lazy with Suspense
import { lazy, Suspense } from 'react';

const LazyModal = lazy(() => import('./Modal'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      {showModal && <LazyModal />}
    </Suspense>
  );
}

// Route-based splitting (React Router)
const routes = [
  {
    path: '/dashboard',
    element: lazy(() => import('./pages/Dashboard'))
  },
  {
    path: '/settings',
    element: lazy(() => import('./pages/Settings'))
  }
];
```

### Tree Shaking

```typescript
// BAD: Import entire library
import _ from 'lodash';
_.debounce(fn, 300);

// GOOD: Import specific function
import debounce from 'lodash/debounce';
debounce(fn, 300);

// GOOD: Use lodash-es for ES modules
import { debounce } from 'lodash-es';

// Package.json sideEffects for tree shaking
{
  "sideEffects": [
    "**/*.css",
    "**/*.scss"
  ]
}
```

### Bundle Analysis

```bash
# Next.js bundle analyzer
npm install @next/bundle-analyzer

# next.config.js
const withBundleAnalyzer = require('@next/bundle-analyzer')({
  enabled: process.env.ANALYZE === 'true',
});
module.exports = withBundleAnalyzer({ /* config */ });

# Run analysis
ANALYZE=true npm run build

# Webpack bundle analyzer
npx webpack-bundle-analyzer stats.json
```

## Image Optimization

### Next.js Image Component

```typescript
import Image from 'next/image';

// Optimized image with automatic WebP/AVIF
<Image
  src="/hero.jpg"
  alt="Hero"
  width={1200}
  height={600}
  priority // LCP image
  placeholder="blur"
  blurDataURL={blurDataUrl}
/>

// Responsive images
<Image
  src="/product.jpg"
  alt="Product"
  fill
  sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
  style={{ objectFit: 'cover' }}
/>
```

### Native Lazy Loading

```html
<!-- Lazy load below-fold images -->
<img
  src="image.jpg"
  alt="Description"
  loading="lazy"
  decoding="async"
  width="400"
  height="300"
/>

<!-- Responsive images with srcset -->
<img
  src="image-800.jpg"
  srcset="
    image-400.jpg 400w,
    image-800.jpg 800w,
    image-1200.jpg 1200w
  "
  sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
  alt="Responsive image"
  loading="lazy"
/>

<!-- Modern format with fallback -->
<picture>
  <source srcset="image.avif" type="image/avif" />
  <source srcset="image.webp" type="image/webp" />
  <img src="image.jpg" alt="Fallback" />
</picture>
```

## Caching Strategies

### Service Worker (Workbox)

```typescript
// next.config.js with next-pwa
const withPWA = require('next-pwa')({
  dest: 'public',
  runtimeCaching: [
    {
      urlPattern: /^https:\/\/api\.example\.com\/.*/,
      handler: 'StaleWhileRevalidate',
      options: {
        cacheName: 'api-cache',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 60 * 60 // 1 hour
        }
      }
    },
    {
      urlPattern: /\.(?:png|jpg|jpeg|svg|webp)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'image-cache',
        expiration: {
          maxEntries: 200,
          maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
        }
      }
    }
  ]
});
```

### HTTP Cache Headers

```typescript
// Next.js API route caching
export async function GET() {
  const data = await fetchData();

  return Response.json(data, {
    headers: {
      'Cache-Control': 'public, s-maxage=60, stale-while-revalidate=300'
    }
  });
}

// Static assets (next.config.js)
module.exports = {
  async headers() {
    return [
      {
        source: '/static/:path*',
        headers: [
          {
            key: 'Cache-Control',
            value: 'public, max-age=31536000, immutable'
          }
        ]
      }
    ];
  }
};
```

## Performance Monitoring

### Web Vitals Reporting

```typescript
// app/layout.tsx (Next.js App Router)
import { useReportWebVitals } from 'next/web-vitals';

export function WebVitals() {
  useReportWebVitals((metric) => {
    // Send to analytics
    gtag('event', metric.name, {
      value: Math.round(metric.value),
      event_category: 'Web Vitals',
      event_label: metric.id,
      non_interaction: true,
    });
  });

  return null;
}

// Custom performance marks
performance.mark('feature-start');
// ... feature code
performance.mark('feature-end');
performance.measure('feature-duration', 'feature-start', 'feature-end');

const measure = performance.getEntriesByName('feature-duration')[0];
console.log(`Feature took ${measure.duration}ms`);
```

### React Profiler

```typescript
import { Profiler } from 'react';

function onRenderCallback(
  id: string,
  phase: 'mount' | 'update',
  actualDuration: number,
  baseDuration: number,
  startTime: number,
  commitTime: number
) {
  // Log slow renders
  if (actualDuration > 16) { // > 1 frame
    console.warn(`Slow render: ${id} took ${actualDuration}ms`);
  }
}

function App() {
  return (
    <Profiler id="App" onRender={onRenderCallback}>
      <MainContent />
    </Profiler>
  );
}
```
