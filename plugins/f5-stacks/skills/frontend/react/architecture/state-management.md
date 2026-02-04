# React State Management Strategies

## Overview

Choosing the right state management approach based on application needs.

## State Categories

### Local State

Component-specific state that doesn't need to be shared.

```tsx
function Counter() {
  const [count, setCount] = useState(0);
  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;
}
```

### Shared State

State that multiple components need to access.

```tsx
// Using Context
const ThemeContext = createContext<Theme>('light');

function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

### Server State

Data fetched from external sources that needs caching, synchronization.

```tsx
// Using TanStack Query
function ProductList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['products'],
    queryFn: () => api.getProducts(),
  });
  // ...
}
```

### Global State

Application-wide state like user authentication, UI preferences.

```tsx
// Using Zustand
const useAuthStore = create<AuthState>((set) => ({
  user: null,
  login: (user) => set({ user }),
  logout: () => set({ user: null }),
}));
```

## Decision Matrix

| State Type | Solution | Use Case |
|------------|----------|----------|
| Local | useState | Form inputs, toggles, local UI |
| Lifted | Props | Parent-child data sharing |
| Shared | Context | Theme, locale, small global |
| Server | TanStack Query | API data, caching |
| Complex Global | Zustand/Redux | Large app state |

## State Colocation

### Principle

Keep state as close as possible to where it's used.

```tsx
// ❌ Wrong: State lifted too high
function App() {
  const [modalOpen, setModalOpen] = useState(false);
  const [formData, setFormData] = useState({});
  // ... many other states

  return <Dashboard modalOpen={modalOpen} formData={formData} />;
}

// ✅ Right: State colocated
function App() {
  return <Dashboard />;
}

function Dashboard() {
  // State lives where it's needed
  const [selectedTab, setSelectedTab] = useState(0);
  return <Tabs value={selectedTab} onChange={setSelectedTab} />;
}
```

## State Lifting

### When to Lift

Lift state when multiple sibling components need the same data.

```tsx
// ✅ Lifted state for siblings
function ProductPage() {
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  return (
    <div className="flex">
      <ProductList onSelect={setSelectedProduct} />
      <ProductDetail product={selectedProduct} />
    </div>
  );
}
```

## Derived State

### Compute Don't Store

```tsx
// ❌ Wrong: Storing derived state
const [items, setItems] = useState<Item[]>([]);
const [filteredItems, setFilteredItems] = useState<Item[]>([]);
const [totalPrice, setTotalPrice] = useState(0);

// ✅ Right: Compute on render
const [items, setItems] = useState<Item[]>([]);
const [filter, setFilter] = useState('');

const filteredItems = useMemo(
  () => items.filter(item => item.name.includes(filter)),
  [items, filter]
);

const totalPrice = useMemo(
  () => filteredItems.reduce((sum, item) => sum + item.price, 0),
  [filteredItems]
);
```

## State Initialization

### Lazy Initialization

```tsx
// ❌ Wrong: Expensive computation on every render
const [data, setData] = useState(expensiveComputation());

// ✅ Right: Lazy initialization
const [data, setData] = useState(() => expensiveComputation());
```

### From Props

```tsx
// ❌ Wrong: State from props (creates sync issues)
function Form({ initialValue }: { initialValue: string }) {
  const [value, setValue] = useState(initialValue);
  // Won't update when initialValue changes!
}

// ✅ Right: Use key to reset, or controlled component
// Option 1: Key-based reset
<Form key={itemId} initialValue={item.value} />

// Option 2: Effect sync (when truly needed)
function Form({ initialValue }: { initialValue: string }) {
  const [value, setValue] = useState(initialValue);

  useEffect(() => {
    setValue(initialValue);
  }, [initialValue]);
}
```

## Complex State Patterns

### useReducer for Complex Logic

```tsx
interface State {
  status: 'idle' | 'loading' | 'success' | 'error';
  data: Data | null;
  error: Error | null;
}

type Action =
  | { type: 'FETCH_START' }
  | { type: 'FETCH_SUCCESS'; payload: Data }
  | { type: 'FETCH_ERROR'; payload: Error };

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case 'FETCH_START':
      return { ...state, status: 'loading', error: null };
    case 'FETCH_SUCCESS':
      return { status: 'success', data: action.payload, error: null };
    case 'FETCH_ERROR':
      return { status: 'error', data: null, error: action.payload };
    default:
      return state;
  }
}

function DataFetcher() {
  const [state, dispatch] = useReducer(reducer, {
    status: 'idle',
    data: null,
    error: null,
  });

  const fetchData = async () => {
    dispatch({ type: 'FETCH_START' });
    try {
      const data = await api.getData();
      dispatch({ type: 'FETCH_SUCCESS', payload: data });
    } catch (error) {
      dispatch({ type: 'FETCH_ERROR', payload: error as Error });
    }
  };

  // ...
}
```

### State Machines

```tsx
type Status = 'idle' | 'loading' | 'success' | 'error';

const transitions: Record<Status, Status[]> = {
  idle: ['loading'],
  loading: ['success', 'error'],
  success: ['loading', 'idle'],
  error: ['loading', 'idle'],
};

function useStateMachine(initial: Status) {
  const [status, setStatus] = useState(initial);

  const transition = (next: Status) => {
    if (transitions[status].includes(next)) {
      setStatus(next);
    } else {
      console.warn(`Invalid transition: ${status} -> ${next}`);
    }
  };

  return [status, transition] as const;
}
```

## Performance Considerations

### State Splitting

```tsx
// ❌ Wrong: All state together
const [state, setState] = useState({
  user: null,
  theme: 'light',
  notifications: [],
  sidebar: true,
});

// ✅ Right: Split by update frequency
const [user, setUser] = useState(null);
const [theme, setTheme] = useState('light');
const [notifications, setNotifications] = useState([]);
const [sidebar, setSidebar] = useState(true);
```

### Context Splitting

```tsx
// Split contexts by update frequency
const UserContext = createContext<User | null>(null);
const ThemeContext = createContext<Theme>('light');
const NotificationContext = createContext<Notification[]>([]);

// Components only re-render when their specific context changes
```

## Best Practices Summary

1. **Start local** - Only lift state when needed
2. **Compute, don't store** - Derive state when possible
3. **Use the right tool** - Match solution to problem
4. **Split by frequency** - Separate fast-changing from slow-changing
5. **Server state is different** - Use TanStack Query for API data
6. **Keep it simple** - Don't over-engineer state management
