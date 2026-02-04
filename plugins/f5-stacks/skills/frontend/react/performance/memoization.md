# Memoization Patterns

## Overview

Caching computed values and functions to prevent unnecessary recalculations and re-renders.

## useMemo

### When to Use

```tsx
// ✅ Good: Expensive computation
const sortedItems = useMemo(() => {
  return [...items].sort((a, b) => a.name.localeCompare(b.name));
}, [items]);

// ✅ Good: Complex filtering
const filteredProducts = useMemo(() => {
  return products
    .filter((p) => p.category === category)
    .filter((p) => p.price >= minPrice && p.price <= maxPrice)
    .map((p) => ({ ...p, discount: calculateDiscount(p) }));
}, [products, category, minPrice, maxPrice]);

// ✅ Good: Stable object reference for effect dependency
const config = useMemo(() => ({
  baseUrl: apiUrl,
  headers: { Authorization: `Bearer ${token}` },
}), [apiUrl, token]);

useEffect(() => {
  fetchData(config);
}, [config]);

// ❌ Bad: Simple computation
const doubled = useMemo(() => count * 2, [count]); // Don't need useMemo

// ❌ Bad: Primitive transformation
const fullName = useMemo(() => `${firstName} ${lastName}`, [firstName, lastName]);
```

### Complex Example

```tsx
interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
  rating: number;
}

interface Filters {
  category: string | null;
  minPrice: number;
  maxPrice: number;
  sortBy: 'price' | 'rating' | 'name';
  sortOrder: 'asc' | 'desc';
}

function ProductList({ products, filters }: { products: Product[]; filters: Filters }) {
  const processedProducts = useMemo(() => {
    let result = products;

    // Filter by category
    if (filters.category) {
      result = result.filter((p) => p.category === filters.category);
    }

    // Filter by price range
    result = result.filter(
      (p) => p.price >= filters.minPrice && p.price <= filters.maxPrice
    );

    // Sort
    result = [...result].sort((a, b) => {
      const modifier = filters.sortOrder === 'asc' ? 1 : -1;

      switch (filters.sortBy) {
        case 'price':
          return (a.price - b.price) * modifier;
        case 'rating':
          return (a.rating - b.rating) * modifier;
        case 'name':
          return a.name.localeCompare(b.name) * modifier;
        default:
          return 0;
      }
    });

    return result;
  }, [products, filters.category, filters.minPrice, filters.maxPrice, filters.sortBy, filters.sortOrder]);

  return (
    <ul>
      {processedProducts.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </ul>
  );
}
```

## useCallback

### When to Use

```tsx
// ✅ Good: Callback passed to memoized child
const MemoizedList = memo(function List({ onItemClick }: { onItemClick: (id: string) => void }) {
  // ...
});

function Parent() {
  const handleItemClick = useCallback((id: string) => {
    console.log('Clicked:', id);
  }, []);

  return <MemoizedList onItemClick={handleItemClick} />;
}

// ✅ Good: Callback used in dependency array
function SearchComponent() {
  const [results, setResults] = useState([]);

  const search = useCallback(async (query: string) => {
    const data = await api.search(query);
    setResults(data);
  }, []);

  useEffect(() => {
    search(initialQuery);
  }, [search, initialQuery]);
}

// ❌ Bad: No memoized consumers
function Parent() {
  // This useCallback is unnecessary if Child is not memoized
  const handleClick = useCallback(() => {
    console.log('clicked');
  }, []);

  return <Child onClick={handleClick} />;
}
```

### With Dependencies

```tsx
function ShoppingCart({ items }: { items: CartItem[] }) {
  const [discount, setDiscount] = useState(0);

  // Dependencies: only recreates when items or discount change
  const calculateTotal = useCallback(() => {
    const subtotal = items.reduce((sum, item) => sum + item.price * item.quantity, 0);
    return subtotal * (1 - discount / 100);
  }, [items, discount]);

  // Stable reference for external use
  const handleCheckout = useCallback(async () => {
    const total = calculateTotal();
    await processPayment(total);
  }, [calculateTotal]);

  return (
    <div>
      <ItemList items={items} />
      <CheckoutButton onCheckout={handleCheckout} />
    </div>
  );
}
```

## React.memo

### Basic Usage

```tsx
import { memo } from 'react';

// Memoize entire component
const UserCard = memo(function UserCard({ user }: { user: User }) {
  return (
    <div className="card">
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
});

// With custom comparison
const ExpensiveChart = memo(
  function ExpensiveChart({ data, options }: ChartProps) {
    // Heavy rendering logic
    return <canvas />;
  },
  (prevProps, nextProps) => {
    // Only re-render if data changed
    return (
      prevProps.data === nextProps.data &&
      prevProps.options.type === nextProps.options.type
    );
  }
);
```

### When to Use memo

```tsx
// ✅ Good: Pure component with stable props
const ListItem = memo(function ListItem({ item }: { item: Item }) {
  return <li>{item.name}</li>;
});

// ✅ Good: Component renders frequently but props rarely change
const Sidebar = memo(function Sidebar({ navigation }: { navigation: NavItem[] }) {
  return <nav>{/* ... */}</nav>;
});

// ✅ Good: Expensive render
const DataGrid = memo(function DataGrid({ rows, columns }: DataGridProps) {
  // Complex table rendering
  return <table>{/* ... */}</table>;
});

// ❌ Bad: Props change on every render
function Parent() {
  // This object is recreated every render, defeating memo
  return <MemoizedChild config={{ theme: 'dark' }} />;
}

// ✅ Fix: Memoize the prop
function Parent() {
  const config = useMemo(() => ({ theme: 'dark' }), []);
  return <MemoizedChild config={config} />;
}
```

## Combining Patterns

```tsx
const MemoizedProductGrid = memo(function ProductGrid({
  products,
  onProductClick,
  sortBy,
}: {
  products: Product[];
  onProductClick: (id: string) => void;
  sortBy: string;
}) {
  // Memoize expensive computation inside memoized component
  const sortedProducts = useMemo(() => {
    return [...products].sort((a, b) => {
      if (sortBy === 'price') return a.price - b.price;
      return a.name.localeCompare(b.name);
    });
  }, [products, sortBy]);

  return (
    <div className="grid">
      {sortedProducts.map((product) => (
        <ProductCard
          key={product.id}
          product={product}
          onClick={onProductClick}
        />
      ))}
    </div>
  );
});

// Parent with stable callbacks
function ProductPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [sortBy, setSortBy] = useState('name');

  const handleProductClick = useCallback((id: string) => {
    router.push(`/products/${id}`);
  }, []);

  return (
    <MemoizedProductGrid
      products={products}
      onProductClick={handleProductClick}
      sortBy={sortBy}
    />
  );
}
```

## Creating Memoization Utilities

```tsx
// Generic memoization hook
function useMemoCompare<T>(
  value: T,
  compare: (prev: T | undefined, next: T) => boolean
): T {
  const previousRef = useRef<T>();
  const previous = previousRef.current;

  const isEqual = previous !== undefined && compare(previous, value);

  useEffect(() => {
    if (!isEqual) {
      previousRef.current = value;
    }
  });

  return isEqual ? previous! : value;
}

// Usage: Deep comparison
function Component({ data }: { data: DeepObject }) {
  const memoizedData = useMemoCompare(data, (prev, next) =>
    JSON.stringify(prev) === JSON.stringify(next)
  );

  useEffect(() => {
    // Only runs when data actually changes (deep comparison)
    processData(memoizedData);
  }, [memoizedData]);
}
```

## Best Practices

1. **Profile first** - Measure performance before optimizing
2. **Don't overuse** - Memoization has overhead
3. **Check dependencies** - Ensure dependency arrays are correct
4. **Keep deps minimal** - Fewer dependencies = fewer recalculations
5. **Combine strategically** - memo + useCallback + useMemo together
6. **Use React DevTools** - Identify unnecessary re-renders
