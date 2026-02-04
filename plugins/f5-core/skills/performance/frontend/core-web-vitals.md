---
name: core-web-vitals
description: Core Web Vitals optimization strategies
category: performance/frontend
applies_to: frontend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Core Web Vitals

## Overview

Core Web Vitals are Google's metrics for measuring user experience.
They impact SEO rankings and user satisfaction.

## The Three Core Web Vitals

```
┌─────────────────────────────────────────────────────────────────┐
│                     Core Web Vitals                              │
├─────────────────┬─────────────────┬─────────────────────────────┤
│      LCP        │      INP        │         CLS                 │
│    Loading      │  Interactivity  │    Visual Stability         │
├─────────────────┼─────────────────┼─────────────────────────────┤
│  Good: ≤ 2.5s   │  Good: ≤ 200ms  │     Good: ≤ 0.1             │
│  Poor: > 4.0s   │  Poor: > 500ms  │     Poor: > 0.25            │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

## Largest Contentful Paint (LCP)

### What Triggers LCP

- `<img>` elements
- `<image>` inside SVG
- `<video>` poster images
- Background images via CSS
- Block-level text elements

### Optimizing LCP

```html
<!-- Preload LCP image -->
<head>
  <link
    rel="preload"
    as="image"
    href="/hero-image.webp"
    fetchpriority="high"
  />
</head>

<!-- Critical image with high priority -->
<img
  src="/hero-image.webp"
  alt="Hero"
  fetchpriority="high"
  decoding="sync"
/>
```

```typescript
// Identify LCP element
new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];

  console.log('LCP:', {
    element: lastEntry.element,
    time: lastEntry.startTime,
    size: lastEntry.size,
    url: lastEntry.url,
  });
}).observe({ type: 'largest-contentful-paint', buffered: true });
```

### LCP Optimization Checklist

```typescript
// Server-side: Fast TTFB
// - Use CDN
// - Enable compression
// - Optimize server response time

// Resource loading
// - Preload LCP image
// - Use optimal image format (WebP/AVIF)
// - Responsive images with srcset
// - Inline critical CSS

// Render blocking
// - Defer non-critical JavaScript
// - Remove render-blocking resources
// - Use font-display: swap
```

### Server-Side Rendering for LCP

```typescript
// Next.js - prioritize LCP content
import Image from 'next/image';

export default function HeroSection({ heroImage }: { heroImage: string }) {
  return (
    <section>
      <Image
        src={heroImage}
        alt="Hero"
        width={1920}
        height={1080}
        priority // Disables lazy loading
        placeholder="blur"
        blurDataURL={heroImage.blurUrl}
      />
      <h1>Welcome</h1>
    </section>
  );
}
```

## Interaction to Next Paint (INP)

### What INP Measures

- Click/tap handlers
- Key press handlers
- Other input handlers
- Time from input to next paint

### Optimizing INP

```typescript
// Break up long tasks
async function processLargeData(data: any[]) {
  const CHUNK_SIZE = 100;

  for (let i = 0; i < data.length; i += CHUNK_SIZE) {
    const chunk = data.slice(i, i + CHUNK_SIZE);
    processChunk(chunk);

    // Yield to main thread between chunks
    await new Promise((resolve) => setTimeout(resolve, 0));
  }
}

// Use requestIdleCallback for non-critical work
function scheduleNonCritical(callback: () => void) {
  if ('requestIdleCallback' in window) {
    requestIdleCallback(callback);
  } else {
    setTimeout(callback, 1);
  }
}

// Debounce frequent interactions
function debounce<T extends (...args: any[]) => void>(
  fn: T,
  delay: number
): T {
  let timeoutId: NodeJS.Timeout;
  return ((...args) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => fn(...args), delay);
  }) as T;
}

// Usage
const handleSearch = debounce((query: string) => {
  performSearch(query);
}, 300);
```

### React Optimization for INP

```typescript
import { useTransition, useDeferredValue, memo } from 'react';

// Use transitions for non-urgent updates
function SearchResults() {
  const [query, setQuery] = useState('');
  const [isPending, startTransition] = useTransition();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Urgent: update input immediately
    setQuery(e.target.value);

    // Non-urgent: update results later
    startTransition(() => {
      setSearchResults(search(e.target.value));
    });
  };

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending && <Spinner />}
      <Results />
    </>
  );
}

// Defer expensive rendering
function FilteredList({ items, filter }: { items: Item[]; filter: string }) {
  const deferredFilter = useDeferredValue(filter);
  const filteredItems = useMemo(
    () => items.filter((item) => item.name.includes(deferredFilter)),
    [items, deferredFilter]
  );

  return <List items={filteredItems} />;
}

// Memoize expensive components
const ExpensiveComponent = memo(function ExpensiveComponent({ data }: { data: any }) {
  // Complex rendering
  return <div>{/* ... */}</div>;
});
```

### Web Worker for Heavy Computation

```typescript
// worker.ts
self.onmessage = (e: MessageEvent) => {
  const result = heavyComputation(e.data);
  self.postMessage(result);
};

// main.ts
const worker = new Worker(new URL('./worker.ts', import.meta.url));

function processInWorker(data: any): Promise<any> {
  return new Promise((resolve) => {
    worker.onmessage = (e) => resolve(e.data);
    worker.postMessage(data);
  });
}

// Usage - keeps main thread responsive
const handleClick = async () => {
  const result = await processInWorker(largeDataset);
  setResults(result);
};
```

## Cumulative Layout Shift (CLS)

### What Causes CLS

- Images without dimensions
- Ads and embeds without space
- Dynamically injected content
- Web fonts causing FOIT/FOUT
- Actions waiting for network

### Fixing CLS Issues

```css
/* Reserve space for images */
img {
  aspect-ratio: attr(width) / attr(height);
  width: 100%;
  height: auto;
}

/* Reserve space for ads */
.ad-slot {
  min-height: 250px;
  background: #f0f0f0;
}

/* Prevent font swap layout shift */
@font-face {
  font-family: 'CustomFont';
  src: url('/fonts/custom.woff2') format('woff2');
  font-display: optional; /* or swap with size-adjust */
  size-adjust: 100.5%;
  ascent-override: 95%;
  descent-override: 22%;
}
```

```html
<!-- Always set dimensions -->
<img src="photo.jpg" width="800" height="600" alt="Photo" />

<!-- Or use aspect-ratio -->
<img
  src="photo.jpg"
  alt="Photo"
  style="aspect-ratio: 16/9; width: 100%;"
/>

<!-- Reserve space for dynamic content -->
<div class="skeleton" style="min-height: 200px;">
  <!-- Content loads here -->
</div>
```

### React Skeleton Components

```typescript
// Skeleton that matches final content size
function CardSkeleton() {
  return (
    <div className="card-skeleton" style={{ height: 300 }}>
      <div className="skeleton-image" style={{ height: 200 }} />
      <div className="skeleton-text" style={{ height: 20, width: '80%' }} />
      <div className="skeleton-text" style={{ height: 20, width: '60%' }} />
    </div>
  );
}

function ProductCard({ product }: { product: Product | null }) {
  if (!product) return <CardSkeleton />;

  return (
    <div className="card" style={{ height: 300 }}>
      <img
        src={product.image}
        alt={product.name}
        width={300}
        height={200}
      />
      <h3>{product.name}</h3>
      <p>{product.description}</p>
    </div>
  );
}
```

### Animation Without Layout Shift

```css
/* ❌ Bad - causes layout shift */
.expanding {
  height: 0;
  transition: height 0.3s;
}
.expanding.open {
  height: 200px;
}

/* ✅ Good - use transform */
.expanding {
  transform: scaleY(0);
  transform-origin: top;
  transition: transform 0.3s;
}
.expanding.open {
  transform: scaleY(1);
}

/* ✅ Alternative - animate max-height */
.expanding {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.3s;
}
.expanding.open {
  max-height: 500px; /* larger than content */
}
```

## Measuring Core Web Vitals

### Web Vitals Library

```typescript
import { onLCP, onINP, onCLS } from 'web-vitals';

function sendToAnalytics({ name, delta, id, value }: Metric) {
  // Send to analytics service
  analytics.track('web-vital', {
    name,
    value: Math.round(name === 'CLS' ? delta * 1000 : delta),
    id,
  });
}

// Measure all Core Web Vitals
onLCP(sendToAnalytics);
onINP(sendToAnalytics);
onCLS(sendToAnalytics);

// With attribution for debugging
import { onLCP, onINP, onCLS } from 'web-vitals/attribution';

onLCP((metric) => {
  console.log('LCP:', {
    value: metric.value,
    element: metric.attribution.element,
    url: metric.attribution.url,
    timeToFirstByte: metric.attribution.timeToFirstByte,
    resourceLoadDelay: metric.attribution.resourceLoadDelay,
  });
});

onCLS((metric) => {
  console.log('CLS:', {
    value: metric.value,
    largestShiftEntry: metric.attribution.largestShiftEntry,
    largestShiftTarget: metric.attribution.largestShiftTarget,
  });
});
```

### Monitoring Dashboard

```typescript
// Report to monitoring service
interface WebVitalReport {
  name: 'LCP' | 'INP' | 'CLS';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  page: string;
  timestamp: number;
}

function reportWebVital(metric: Metric): void {
  const report: WebVitalReport = {
    name: metric.name as WebVitalReport['name'],
    value: metric.value,
    rating: metric.rating,
    page: window.location.pathname,
    timestamp: Date.now(),
  };

  // Send to backend
  navigator.sendBeacon('/api/analytics/web-vitals', JSON.stringify(report));
}
```

## Performance Budget

```json
// performance-budget.json
{
  "lcp": {
    "target": 2500,
    "warning": 2000,
    "error": 4000
  },
  "inp": {
    "target": 200,
    "warning": 150,
    "error": 500
  },
  "cls": {
    "target": 0.1,
    "warning": 0.05,
    "error": 0.25
  }
}
```

```typescript
// CI check for web vitals
import { playAudit } from 'playwright-lighthouse';

test('Core Web Vitals meet targets', async ({ page }) => {
  await page.goto('/');

  const result = await playAudit({
    page,
    thresholds: {
      'largest-contentful-paint': 2500,
      'cumulative-layout-shift': 0.1,
      'total-blocking-time': 200, // Proxy for INP in lab
    },
  });

  expect(result.lhr.audits['largest-contentful-paint'].numericValue)
    .toBeLessThan(2500);
});
```

## Quick Wins Summary

| Metric | Quick Wins |
|--------|------------|
| **LCP** | Preload hero image, optimize server TTFB, inline critical CSS |
| **INP** | Break long tasks, use web workers, debounce inputs |
| **CLS** | Set image dimensions, reserve ad space, use font-display |
