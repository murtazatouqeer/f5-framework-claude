# Render Props Pattern

## Overview

Render props is a technique for sharing code between components using a prop whose value is a function that returns a React element.

## Basic Pattern

```tsx
interface MousePosition {
  x: number;
  y: number;
}

interface MouseTrackerProps {
  render: (position: MousePosition) => ReactNode;
}

function MouseTracker({ render }: MouseTrackerProps) {
  const [position, setPosition] = useState<MousePosition>({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (event: MouseEvent) => {
      setPosition({ x: event.clientX, y: event.clientY });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return <>{render(position)}</>;
}

// Usage
<MouseTracker
  render={({ x, y }) => (
    <div>
      Mouse position: {x}, {y}
    </div>
  )}
/>
```

## Children as Function

A common variation uses `children` as the render function.

```tsx
interface ToggleProps {
  children: (props: { on: boolean; toggle: () => void }) => ReactNode;
  initial?: boolean;
}

function Toggle({ children, initial = false }: ToggleProps) {
  const [on, setOn] = useState(initial);
  const toggle = useCallback(() => setOn(prev => !prev), []);

  return <>{children({ on, toggle })}</>;
}

// Usage
<Toggle initial={false}>
  {({ on, toggle }) => (
    <button onClick={toggle}>
      {on ? 'ON' : 'OFF'}
    </button>
  )}
</Toggle>
```

## Data Fetching Example

```tsx
interface FetchProps<T> {
  url: string;
  children: (state: {
    data: T | null;
    loading: boolean;
    error: Error | null;
    refetch: () => void;
  }) => ReactNode;
}

function Fetch<T>({ url, children }: FetchProps<T>) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(url);
      if (!response.ok) throw new Error('Fetch failed');
      const json = await response.json();
      setData(json);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return <>{children({ data, loading, error, refetch: fetchData })}</>;
}

// Usage
<Fetch<User[]> url="/api/users">
  {({ data, loading, error, refetch }) => {
    if (loading) return <Spinner />;
    if (error) return <ErrorMessage error={error} onRetry={refetch} />;
    return <UserList users={data!} />;
  }}
</Fetch>
```

## Scroll Position Tracker

```tsx
interface ScrollState {
  scrollX: number;
  scrollY: number;
  scrollDirection: 'up' | 'down' | null;
  isAtTop: boolean;
  isAtBottom: boolean;
}

interface ScrollTrackerProps {
  children: (state: ScrollState) => ReactNode;
  threshold?: number;
}

function ScrollTracker({ children, threshold = 0 }: ScrollTrackerProps) {
  const [scrollState, setScrollState] = useState<ScrollState>({
    scrollX: 0,
    scrollY: 0,
    scrollDirection: null,
    isAtTop: true,
    isAtBottom: false,
  });

  const prevScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      const scrollX = window.scrollX;
      const direction = scrollY > prevScrollY.current ? 'down' : 'up';
      const maxScroll = document.documentElement.scrollHeight - window.innerHeight;

      setScrollState({
        scrollX,
        scrollY,
        scrollDirection: Math.abs(scrollY - prevScrollY.current) > threshold ? direction : null,
        isAtTop: scrollY <= threshold,
        isAtBottom: scrollY >= maxScroll - threshold,
      });

      prevScrollY.current = scrollY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, [threshold]);

  return <>{children(scrollState)}</>;
}

// Usage
<ScrollTracker threshold={50}>
  {({ scrollY, scrollDirection, isAtTop }) => (
    <header
      className={cn(
        'fixed top-0 w-full transition-transform',
        scrollDirection === 'down' && !isAtTop && '-translate-y-full'
      )}
    >
      <nav>...</nav>
    </header>
  )}
</ScrollTracker>
```

## Form Field Wrapper

```tsx
interface FieldState<T> {
  value: T;
  error: string | null;
  touched: boolean;
  dirty: boolean;
}

interface FieldActions<T> {
  setValue: (value: T) => void;
  setError: (error: string | null) => void;
  setTouched: (touched: boolean) => void;
  reset: () => void;
}

interface FieldProps<T> {
  initialValue: T;
  validate?: (value: T) => string | null;
  children: (state: FieldState<T> & FieldActions<T>) => ReactNode;
}

function Field<T>({ initialValue, validate, children }: FieldProps<T>) {
  const [value, setValueState] = useState(initialValue);
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);
  const [dirty, setDirty] = useState(false);

  const setValue = useCallback((newValue: T) => {
    setValueState(newValue);
    setDirty(true);
    if (validate) {
      setError(validate(newValue));
    }
  }, [validate]);

  const reset = useCallback(() => {
    setValueState(initialValue);
    setError(null);
    setTouched(false);
    setDirty(false);
  }, [initialValue]);

  return (
    <>
      {children({
        value,
        error,
        touched,
        dirty,
        setValue,
        setError,
        setTouched,
        reset,
      })}
    </>
  );
}

// Usage
<Field
  initialValue=""
  validate={(value) => value.length < 3 ? 'Too short' : null}
>
  {({ value, error, touched, setValue, setTouched }) => (
    <div>
      <input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onBlur={() => setTouched(true)}
      />
      {touched && error && <span className="text-red-500">{error}</span>}
    </div>
  )}
</Field>
```

## Intersection Observer

```tsx
interface IntersectionState {
  isIntersecting: boolean;
  entry: IntersectionObserverEntry | null;
}

interface IntersectionProps {
  children: (
    state: IntersectionState & { ref: React.RefObject<HTMLDivElement> }
  ) => ReactNode;
  threshold?: number | number[];
  rootMargin?: string;
}

function Intersection({
  children,
  threshold = 0,
  rootMargin = '0px',
}: IntersectionProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<IntersectionState>({
    isIntersecting: false,
    entry: null,
  });

  useEffect(() => {
    const element = ref.current;
    if (!element) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setState({
          isIntersecting: entry.isIntersecting,
          entry,
        });
      },
      { threshold, rootMargin }
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [threshold, rootMargin]);

  return <>{children({ ...state, ref })}</>;
}

// Usage - Lazy loading
<Intersection threshold={0.1}>
  {({ isIntersecting, ref }) => (
    <div ref={ref}>
      {isIntersecting ? <ExpensiveComponent /> : <Placeholder />}
    </div>
  )}
</Intersection>

// Usage - Animation on scroll
<Intersection threshold={0.5}>
  {({ isIntersecting, ref }) => (
    <div
      ref={ref}
      className={cn(
        'transition-all duration-500',
        isIntersecting ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
      )}
    >
      <Card>Content</Card>
    </div>
  )}
</Intersection>
```

## Render Props vs Hooks

### When to Use Render Props

- Need to render different UI based on state
- Building component libraries with flexible rendering
- Cross-cutting concerns that affect rendering

### When to Use Hooks

- Logic reuse without UI concerns
- Simpler API for common cases
- Better performance (no extra component in tree)

### Converting Render Props to Hooks

```tsx
// Render props version
<MouseTracker render={({ x, y }) => <Cursor x={x} y={y} />} />

// Hook version
function useMousePosition() {
  const [position, setPosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setPosition({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return position;
}

// Usage
function MyComponent() {
  const { x, y } = useMousePosition();
  return <Cursor x={x} y={y} />;
}
```

## Best Practices

1. **Use TypeScript generics** for flexible, type-safe render props
2. **Memoize render functions** to prevent unnecessary re-renders
3. **Consider hooks first** - use render props only when needed for flexibility
4. **Keep render prop APIs simple** - don't pass too many properties
5. **Document the render prop interface** clearly
