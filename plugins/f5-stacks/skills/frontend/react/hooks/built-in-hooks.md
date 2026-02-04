# React Built-in Hooks

## Overview

Essential built-in hooks for state, effects, refs, and performance optimization.

## State Hooks

### useState

```tsx
// Basic usage
const [count, setCount] = useState(0);

// Functional update
setCount(prev => prev + 1);

// Lazy initialization (for expensive computations)
const [state, setState] = useState(() => {
  return expensiveComputation();
});

// Object state
const [form, setForm] = useState({ name: '', email: '' });
setForm(prev => ({ ...prev, name: 'John' }));
```

### useReducer

```tsx
interface State {
  count: number;
  step: number;
}

type Action =
  | { type: 'increment' }
  | { type: 'decrement' }
  | { type: 'setStep'; payload: number }
  | { type: 'reset' };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'increment':
      return { ...state, count: state.count + state.step };
    case 'decrement':
      return { ...state, count: state.count - state.step };
    case 'setStep':
      return { ...state, step: action.payload };
    case 'reset':
      return { count: 0, step: 1 };
    default:
      return state;
  }
}

function Counter() {
  const [state, dispatch] = useReducer(reducer, { count: 0, step: 1 });

  return (
    <>
      <span>{state.count}</span>
      <button onClick={() => dispatch({ type: 'increment' })}>+</button>
      <button onClick={() => dispatch({ type: 'decrement' })}>-</button>
    </>
  );
}
```

## Effect Hooks

### useEffect

```tsx
// Run on every render
useEffect(() => {
  console.log('Rendered');
});

// Run once on mount
useEffect(() => {
  console.log('Mounted');
}, []);

// Run when dependencies change
useEffect(() => {
  console.log('Count changed:', count);
}, [count]);

// Cleanup function
useEffect(() => {
  const subscription = api.subscribe();
  return () => {
    subscription.unsubscribe();
  };
}, []);

// Async effect pattern
useEffect(() => {
  const controller = new AbortController();

  async function fetchData() {
    try {
      const response = await fetch('/api/data', {
        signal: controller.signal,
      });
      const data = await response.json();
      setData(data);
    } catch (error) {
      if (error.name !== 'AbortError') {
        setError(error);
      }
    }
  }

  fetchData();

  return () => controller.abort();
}, []);
```

### useLayoutEffect

```tsx
// Runs synchronously after DOM mutations, before paint
useLayoutEffect(() => {
  // Measure DOM elements
  const rect = ref.current?.getBoundingClientRect();
  setDimensions({ width: rect?.width, height: rect?.height });
}, []);

// Use cases:
// - DOM measurements
// - Scroll position adjustments
// - Animations that need to start immediately
```

### useInsertionEffect

```tsx
// For CSS-in-JS libraries - runs before useLayoutEffect
useInsertionEffect(() => {
  // Insert styles into DOM
  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);
  return () => style.remove();
}, [css]);
```

## Ref Hooks

### useRef

```tsx
// DOM reference
function TextInput() {
  const inputRef = useRef<HTMLInputElement>(null);

  const focusInput = () => {
    inputRef.current?.focus();
  };

  return <input ref={inputRef} />;
}

// Mutable value (doesn't trigger re-render)
function Timer() {
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    intervalRef.current = setInterval(() => {
      console.log('tick');
    }, 1000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);
}

// Previous value
function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}
```

### useImperativeHandle

```tsx
interface InputHandle {
  focus: () => void;
  clear: () => void;
  getValue: () => string;
}

const FancyInput = forwardRef<InputHandle, InputProps>((props, ref) => {
  const inputRef = useRef<HTMLInputElement>(null);

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
    clear: () => {
      if (inputRef.current) inputRef.current.value = '';
    },
    getValue: () => inputRef.current?.value ?? '',
  }));

  return <input ref={inputRef} {...props} />;
});

// Usage
function Parent() {
  const inputRef = useRef<InputHandle>(null);

  return (
    <>
      <FancyInput ref={inputRef} />
      <button onClick={() => inputRef.current?.focus()}>Focus</button>
      <button onClick={() => inputRef.current?.clear()}>Clear</button>
    </>
  );
}
```

## Context Hook

### useContext

```tsx
// Create context
interface ThemeContextType {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | null>(null);

// Provider
function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const toggleTheme = () => setTheme(t => t === 'light' ? 'dark' : 'light');

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Custom hook with safety
function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}

// Usage
function ThemedButton() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      className={theme === 'dark' ? 'bg-black' : 'bg-white'}
    >
      Toggle Theme
    </button>
  );
}
```

## Performance Hooks

### useMemo

```tsx
// Memoize expensive computation
const sortedItems = useMemo(() => {
  return items.sort((a, b) => a.name.localeCompare(b.name));
}, [items]);

// Memoize object to prevent re-renders
const config = useMemo(() => ({
  baseUrl: '/api',
  timeout: 5000,
}), []);

// Don't overuse - only for:
// 1. Expensive computations
// 2. Referential equality for effect dependencies
// 3. Props for memoized children
```

### useCallback

```tsx
// Memoize callback function
const handleSubmit = useCallback((data: FormData) => {
  api.submit(data);
}, []);

// With dependencies
const handleSearch = useCallback((query: string) => {
  setResults(items.filter(item => item.name.includes(query)));
}, [items]);

// Common pattern with children
function Parent() {
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return <MemoizedChild onClick={handleClick} />;
}

const MemoizedChild = memo(({ onClick }: { onClick: () => void }) => {
  return <button onClick={onClick}>Click</button>;
});
```

### useTransition

```tsx
function SearchResults() {
  const [query, setQuery] = useState('');
  const [isPending, startTransition] = useTransition();

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Urgent update
    setQuery(e.target.value);

    // Non-urgent update (can be interrupted)
    startTransition(() => {
      setFilteredResults(filterResults(e.target.value));
    });
  };

  return (
    <>
      <input value={query} onChange={handleChange} />
      {isPending && <Spinner />}
      <ResultsList results={filteredResults} />
    </>
  );
}
```

### useDeferredValue

```tsx
function SearchResults({ query }: { query: string }) {
  // Deferred version of query
  const deferredQuery = useDeferredValue(query);

  // Use deferred value for expensive computations
  const results = useMemo(
    () => expensiveFilter(items, deferredQuery),
    [items, deferredQuery]
  );

  // Show stale indicator
  const isStale = query !== deferredQuery;

  return (
    <div className={isStale ? 'opacity-50' : ''}>
      {results.map(item => <ResultItem key={item.id} item={item} />)}
    </div>
  );
}
```

## Utility Hooks

### useId

```tsx
function FormField({ label }: { label: string }) {
  const id = useId();

  return (
    <>
      <label htmlFor={id}>{label}</label>
      <input id={id} />
    </>
  );
}

// For multiple IDs
function PasswordField() {
  const id = useId();
  const passwordId = `${id}-password`;
  const confirmId = `${id}-confirm`;

  return (
    <>
      <label htmlFor={passwordId}>Password</label>
      <input id={passwordId} type="password" />
      <label htmlFor={confirmId}>Confirm</label>
      <input id={confirmId} type="password" />
    </>
  );
}
```

### useSyncExternalStore

```tsx
// Subscribe to external store
function useOnlineStatus() {
  const isOnline = useSyncExternalStore(
    // subscribe function
    (callback) => {
      window.addEventListener('online', callback);
      window.addEventListener('offline', callback);
      return () => {
        window.removeEventListener('online', callback);
        window.removeEventListener('offline', callback);
      };
    },
    // get snapshot (client)
    () => navigator.onLine,
    // get server snapshot (SSR)
    () => true
  );

  return isOnline;
}
```

## Hook Rules

1. **Only call at top level** - Not inside loops, conditions, or nested functions
2. **Only call from React functions** - Components or custom hooks
3. **Start with "use"** - Convention for custom hooks
4. **Keep dependencies accurate** - Include all values used inside effect
