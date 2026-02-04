# Custom Hooks

## Overview

Custom hooks encapsulate reusable stateful logic that can be shared across components.

## useAsync

```tsx
interface AsyncState<T> {
  data: T | null;
  error: Error | null;
  status: 'idle' | 'pending' | 'success' | 'error';
}

interface UseAsyncReturn<T> extends AsyncState<T> {
  execute: (...args: unknown[]) => Promise<T>;
  reset: () => void;
}

function useAsync<T>(
  asyncFunction: (...args: unknown[]) => Promise<T>,
  immediate = false
): UseAsyncReturn<T> {
  const [state, setState] = useState<AsyncState<T>>({
    data: null,
    error: null,
    status: 'idle',
  });

  const execute = useCallback(
    async (...args: unknown[]) => {
      setState({ data: null, error: null, status: 'pending' });
      try {
        const data = await asyncFunction(...args);
        setState({ data, error: null, status: 'success' });
        return data;
      } catch (error) {
        setState({ data: null, error: error as Error, status: 'error' });
        throw error;
      }
    },
    [asyncFunction]
  );

  const reset = useCallback(() => {
    setState({ data: null, error: null, status: 'idle' });
  }, []);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return { ...state, execute, reset };
}

// Usage
function UserProfile({ userId }: { userId: string }) {
  const { data: user, error, status, execute } = useAsync(
    () => fetchUser(userId),
    true
  );

  if (status === 'pending') return <Spinner />;
  if (status === 'error') return <Error message={error?.message} />;
  if (!user) return null;

  return <Profile user={user} />;
}
```

## useLocalStorage

```tsx
function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((prev: T) => T)) => void, () => void] {
  // Get from localStorage or use initial value
  const [storedValue, setStoredValue] = useState<T>(() => {
    if (typeof window === 'undefined') {
      return initialValue;
    }
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  // Update localStorage when state changes
  const setValue = useCallback(
    (value: T | ((prev: T) => T)) => {
      try {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        if (typeof window !== 'undefined') {
          window.localStorage.setItem(key, JSON.stringify(valueToStore));
        }
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // Remove from localStorage
  const removeValue = useCallback(() => {
    try {
      setStoredValue(initialValue);
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(key);
      }
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  return [storedValue, setValue, removeValue];
}

// Usage
function Settings() {
  const [theme, setTheme, resetTheme] = useLocalStorage('theme', 'light');

  return (
    <select value={theme} onChange={e => setTheme(e.target.value)}>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
    </select>
  );
}
```

## useDebounce

```tsx
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

// Usage
function Search() {
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 300);

  useEffect(() => {
    if (debouncedQuery) {
      searchApi(debouncedQuery);
    }
  }, [debouncedQuery]);

  return (
    <input
      value={query}
      onChange={e => setQuery(e.target.value)}
      placeholder="Search..."
    />
  );
}
```

## useMediaQuery

```tsx
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia(query).matches;
    }
    return false;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia(query);

    const handleChange = (event: MediaQueryListEvent) => {
      setMatches(event.matches);
    };

    // Initial check
    setMatches(mediaQuery.matches);

    // Listen for changes
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [query]);

  return matches;
}

// Usage
function ResponsiveComponent() {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const isTablet = useMediaQuery('(min-width: 769px) and (max-width: 1024px)');
  const isDesktop = useMediaQuery('(min-width: 1025px)');
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');

  return (
    <div>
      {isMobile && <MobileNav />}
      {(isTablet || isDesktop) && <DesktopNav />}
    </div>
  );
}
```

## useClickOutside

```tsx
function useClickOutside<T extends HTMLElement>(
  handler: () => void
): React.RefObject<T> {
  const ref = useRef<T>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent | TouchEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        handler();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [handler]);

  return ref;
}

// Usage
function Dropdown() {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useClickOutside<HTMLDivElement>(() => setIsOpen(false));

  return (
    <div ref={dropdownRef}>
      <button onClick={() => setIsOpen(!isOpen)}>Toggle</button>
      {isOpen && <div className="dropdown-menu">Menu content</div>}
    </div>
  );
}
```

## useIntersectionObserver

```tsx
interface UseIntersectionObserverOptions {
  threshold?: number | number[];
  root?: Element | null;
  rootMargin?: string;
  freezeOnceVisible?: boolean;
}

function useIntersectionObserver<T extends HTMLElement>(
  options: UseIntersectionObserverOptions = {}
): [React.RefObject<T>, boolean, IntersectionObserverEntry | null] {
  const {
    threshold = 0,
    root = null,
    rootMargin = '0px',
    freezeOnceVisible = false,
  } = options;

  const ref = useRef<T>(null);
  const [isIntersecting, setIsIntersecting] = useState(false);
  const [entry, setEntry] = useState<IntersectionObserverEntry | null>(null);
  const frozen = useRef(false);

  useEffect(() => {
    const element = ref.current;
    if (!element || (frozen.current && freezeOnceVisible)) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsIntersecting(entry.isIntersecting);
        setEntry(entry);

        if (entry.isIntersecting && freezeOnceVisible) {
          frozen.current = true;
        }
      },
      { threshold, root, rootMargin }
    );

    observer.observe(element);
    return () => observer.disconnect();
  }, [threshold, root, rootMargin, freezeOnceVisible]);

  return [ref, isIntersecting, entry];
}

// Usage - Lazy loading
function LazyImage({ src, alt }: { src: string; alt: string }) {
  const [ref, isVisible] = useIntersectionObserver<HTMLDivElement>({
    freezeOnceVisible: true,
  });

  return (
    <div ref={ref}>
      {isVisible ? (
        <img src={src} alt={alt} />
      ) : (
        <div className="placeholder" />
      )}
    </div>
  );
}

// Usage - Infinite scroll
function InfiniteList() {
  const [ref, isIntersecting] = useIntersectionObserver<HTMLDivElement>({
    threshold: 0.1,
  });

  useEffect(() => {
    if (isIntersecting) {
      loadMoreItems();
    }
  }, [isIntersecting]);

  return (
    <>
      <ItemList items={items} />
      <div ref={ref} className="h-10" /> {/* Sentinel element */}
    </>
  );
}
```

## useFetch

```tsx
interface UseFetchOptions extends RequestInit {
  immediate?: boolean;
}

interface UseFetchReturn<T> {
  data: T | null;
  error: Error | null;
  loading: boolean;
  refetch: () => Promise<void>;
}

function useFetch<T>(url: string, options: UseFetchOptions = {}): UseFetchReturn<T> {
  const { immediate = true, ...fetchOptions } = options;
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(url, fetchOptions);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const json = await response.json();
      setData(json);
    } catch (e) {
      setError(e as Error);
    } finally {
      setLoading(false);
    }
  }, [url, JSON.stringify(fetchOptions)]);

  useEffect(() => {
    if (immediate) {
      fetchData();
    }
  }, [immediate, fetchData]);

  return { data, error, loading, refetch: fetchData };
}

// Usage
function UserList() {
  const { data: users, loading, error, refetch } = useFetch<User[]>('/api/users');

  if (loading) return <Spinner />;
  if (error) return <Error message={error.message} onRetry={refetch} />;

  return <UserTable users={users ?? []} />;
}
```

## useToggle

```tsx
function useToggle(
  initialValue = false
): [boolean, () => void, (value: boolean) => void] {
  const [value, setValue] = useState(initialValue);

  const toggle = useCallback(() => setValue(v => !v), []);
  const setToggle = useCallback((v: boolean) => setValue(v), []);

  return [value, toggle, setToggle];
}

// Usage
function Modal() {
  const [isOpen, toggle, setIsOpen] = useToggle(false);

  return (
    <>
      <button onClick={toggle}>Toggle Modal</button>
      <button onClick={() => setIsOpen(true)}>Open</button>
      {isOpen && <ModalContent onClose={() => setIsOpen(false)} />}
    </>
  );
}
```

## Best Practices

1. **Start with "use"** - Convention that enables ESLint rules
2. **Compose hooks** - Build complex hooks from simpler ones
3. **Return consistent types** - Use tuples or objects consistently
4. **Handle cleanup** - Always clean up subscriptions and timers
5. **Use TypeScript generics** - For flexible, type-safe hooks
6. **Memoize callbacks** - Prevent unnecessary re-renders
7. **Document dependencies** - Make dependency arrays explicit
