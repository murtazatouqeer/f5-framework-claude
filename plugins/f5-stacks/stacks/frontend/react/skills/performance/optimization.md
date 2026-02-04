# React Performance Optimization

## Overview

Techniques and patterns for optimizing React application performance.

## Avoiding Unnecessary Renders

### React.memo

```tsx
import { memo } from 'react';

interface UserCardProps {
  user: User;
  onSelect: (id: string) => void;
}

// Only re-renders when props change
const UserCard = memo(function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <div onClick={() => onSelect(user.id)}>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
});

// Custom comparison
const UserCard = memo(
  function UserCard({ user, onSelect }: UserCardProps) {
    // ...
  },
  (prevProps, nextProps) => {
    // Return true if props are equal (skip re-render)
    return prevProps.user.id === nextProps.user.id;
  }
);
```

### useCallback

```tsx
function ParentComponent() {
  const [count, setCount] = useState(0);

  // ❌ Bad: Creates new function every render
  const handleClick = () => {
    console.log('clicked');
  };

  // ✅ Good: Stable reference
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  // ✅ Good: With dependencies
  const handleIncrement = useCallback(() => {
    setCount((c) => c + 1);
  }, []);

  return <MemoizedChild onClick={handleClick} />;
}
```

### useMemo

```tsx
function ExpensiveComponent({ items, filter }: Props) {
  // ❌ Bad: Recalculates every render
  const filteredItems = items.filter(item => item.name.includes(filter));
  const sortedItems = filteredItems.sort((a, b) => a.name.localeCompare(b.name));

  // ✅ Good: Only recalculates when items or filter changes
  const processedItems = useMemo(() => {
    const filtered = items.filter(item => item.name.includes(filter));
    return filtered.sort((a, b) => a.name.localeCompare(b.name));
  }, [items, filter]);

  return <List items={processedItems} />;
}
```

## List Virtualization

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualList({ items }: { items: Item[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50, // Estimated row height
    overscan: 5, // Render 5 extra items above/below viewport
  });

  return (
    <div
      ref={parentRef}
      className="h-96 overflow-auto"
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            <ItemRow item={items[virtualRow.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Lazy Loading

```tsx
import { lazy, Suspense } from 'react';

// Lazy load heavy components
const HeavyChart = lazy(() => import('./HeavyChart'));
const AdminDashboard = lazy(() => import('./AdminDashboard'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/charts" element={<HeavyChart />} />
        <Route path="/admin" element={<AdminDashboard />} />
      </Routes>
    </Suspense>
  );
}

// Named exports
const HeavyComponent = lazy(() =>
  import('./HeavyComponent').then((module) => ({
    default: module.HeavyComponent,
  }))
);
```

## Image Optimization

```tsx
// Lazy loading images
function LazyImage({ src, alt }: { src: string; alt: string }) {
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
    <div ref={imgRef} className="relative">
      {!isLoaded && <Skeleton className="absolute inset-0" />}
      {isInView && (
        <img
          src={src}
          alt={alt}
          onLoad={() => setIsLoaded(true)}
          className={cn('transition-opacity', isLoaded ? 'opacity-100' : 'opacity-0')}
        />
      )}
    </div>
  );
}

// Using loading="lazy"
<img src={src} alt={alt} loading="lazy" />
```

## State Colocation

```tsx
// ❌ Bad: State too high in tree
function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);

  return (
    <div>
      <SearchBar query={searchQuery} onChange={setSearchQuery} />
      <ItemList selectedItem={selectedItem} onSelect={setSelectedItem} />
      <Modal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />
    </div>
  );
}

// ✅ Good: State colocated
function App() {
  return (
    <div>
      <SearchBar /> {/* Manages its own state */}
      <ItemList /> {/* Manages its own state */}
      <ModalContainer /> {/* Manages its own state */}
    </div>
  );
}
```

## Debouncing and Throttling

```tsx
import { useDeferredValue, useState, useMemo } from 'react';

// Using useDeferredValue
function SearchResults({ query }: { query: string }) {
  const deferredQuery = useDeferredValue(query);
  const isStale = query !== deferredQuery;

  const results = useMemo(
    () => expensiveSearch(deferredQuery),
    [deferredQuery]
  );

  return (
    <div className={isStale ? 'opacity-50' : ''}>
      {results.map((item) => (
        <ResultItem key={item.id} item={item} />
      ))}
    </div>
  );
}

// Using custom debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debouncedValue;
}
```

## Avoiding Layout Thrashing

```tsx
// ❌ Bad: Multiple reads and writes
function animate() {
  elements.forEach((el) => {
    const height = el.offsetHeight; // Read
    el.style.height = height + 10 + 'px'; // Write
  });
}

// ✅ Good: Batch reads, then writes
function animate() {
  // Batch all reads
  const heights = elements.map((el) => el.offsetHeight);

  // Batch all writes
  elements.forEach((el, i) => {
    el.style.height = heights[i] + 10 + 'px';
  });
}
```

## Performance Measurement

```tsx
import { Profiler, ProfilerOnRenderCallback } from 'react';

const onRender: ProfilerOnRenderCallback = (
  id,
  phase,
  actualDuration,
  baseDuration,
  startTime,
  commitTime
) => {
  console.log({
    id,
    phase,
    actualDuration,
    baseDuration,
  });
};

function App() {
  return (
    <Profiler id="App" onRender={onRender}>
      <MainContent />
    </Profiler>
  );
}

// Custom performance hook
function useRenderCount(componentName: string) {
  const renderCount = useRef(0);
  renderCount.current += 1;

  useEffect(() => {
    console.log(`${componentName} rendered ${renderCount.current} times`);
  });
}
```

## Best Practices Summary

1. **Profile first** - Measure before optimizing
2. **Avoid premature optimization** - Only optimize bottlenecks
3. **Use React DevTools Profiler** - Identify slow components
4. **Memoize expensive operations** - useMemo, useCallback
5. **Virtualize long lists** - Don't render 1000s of items
6. **Lazy load routes** - Code split by route
7. **Colocate state** - Keep state close to where it's used
8. **Use keys correctly** - Stable, unique keys for lists
