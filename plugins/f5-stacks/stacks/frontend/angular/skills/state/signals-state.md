# Angular Signals State Management

## Overview

Signals provide fine-grained reactivity for state management in Angular 17+. They offer a simpler alternative to RxJS for synchronous state.

## Signal State Patterns

### Simple State Container

```typescript
import { Injectable, signal, computed } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  // State
  private _theme = signal<'light' | 'dark'>('light');
  private _fontSize = signal<'small' | 'medium' | 'large'>('medium');

  // Public selectors
  readonly theme = this._theme.asReadonly();
  readonly fontSize = this._fontSize.asReadonly();

  // Computed
  readonly isDark = computed(() => this._theme() === 'dark');

  readonly cssVars = computed(() => ({
    '--bg-color': this._theme() === 'dark' ? '#1a1a1a' : '#ffffff',
    '--text-color': this._theme() === 'dark' ? '#ffffff' : '#1a1a1a',
    '--font-size': this._fontSize() === 'small' ? '14px' :
                   this._fontSize() === 'large' ? '18px' : '16px',
  }));

  // Actions
  toggleTheme() {
    this._theme.update(t => t === 'light' ? 'dark' : 'light');
  }

  setTheme(theme: 'light' | 'dark') {
    this._theme.set(theme);
  }

  setFontSize(size: 'small' | 'medium' | 'large') {
    this._fontSize.set(size);
  }
}
```

### Entity State Pattern

```typescript
interface EntityState<T> {
  entities: Record<string, T>;
  ids: string[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;
}

function createEntityState<T>(): EntityState<T> {
  return {
    entities: {},
    ids: [],
    selectedId: null,
    isLoading: false,
    error: null,
  };
}

@Injectable({ providedIn: 'root' })
export class ProductEntityService {
  private state = signal<EntityState<Product>>(createEntityState());

  // Selectors
  readonly entities = computed(() => this.state().entities);
  readonly ids = computed(() => this.state().ids);
  readonly selectedId = computed(() => this.state().selectedId);
  readonly isLoading = computed(() => this.state().isLoading);
  readonly error = computed(() => this.state().error);

  readonly all = computed(() =>
    this.ids().map(id => this.entities()[id])
  );

  readonly selected = computed(() => {
    const id = this.selectedId();
    return id ? this.entities()[id] : null;
  });

  readonly total = computed(() => this.ids().length);

  // Entity operations
  setAll(products: Product[]) {
    const entities: Record<string, Product> = {};
    const ids: string[] = [];

    products.forEach(p => {
      entities[p.id] = p;
      ids.push(p.id);
    });

    this.state.update(s => ({
      ...s,
      entities,
      ids,
      isLoading: false,
    }));
  }

  addOne(product: Product) {
    this.state.update(s => ({
      ...s,
      entities: { ...s.entities, [product.id]: product },
      ids: s.ids.includes(product.id) ? s.ids : [...s.ids, product.id],
    }));
  }

  updateOne(id: string, changes: Partial<Product>) {
    this.state.update(s => ({
      ...s,
      entities: {
        ...s.entities,
        [id]: { ...s.entities[id], ...changes },
      },
    }));
  }

  removeOne(id: string) {
    this.state.update(s => {
      const { [id]: removed, ...entities } = s.entities;
      return {
        ...s,
        entities,
        ids: s.ids.filter(i => i !== id),
        selectedId: s.selectedId === id ? null : s.selectedId,
      };
    });
  }

  select(id: string | null) {
    this.state.update(s => ({ ...s, selectedId: id }));
  }
}
```

### Slice-Based State

```typescript
interface AppState {
  auth: AuthState;
  products: ProductState;
  cart: CartState;
  ui: UIState;
}

// Each slice manages its own state
@Injectable({ providedIn: 'root' })
export class AuthStore {
  private state = signal<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: false,
  });

  readonly user = computed(() => this.state().user);
  readonly isAuthenticated = computed(() => this.state().isAuthenticated);
  readonly isLoading = computed(() => this.state().isLoading);

  login(user: User, token: string) {
    this.state.set({
      user,
      token,
      isAuthenticated: true,
      isLoading: false,
    });
  }

  logout() {
    this.state.set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  }
}

@Injectable({ providedIn: 'root' })
export class CartStore {
  private state = signal<CartState>({
    items: [],
    isOpen: false,
  });

  readonly items = computed(() => this.state().items);
  readonly isOpen = computed(() => this.state().isOpen);
  readonly itemCount = computed(() =>
    this.items().reduce((sum, item) => sum + item.quantity, 0)
  );
  readonly total = computed(() =>
    this.items().reduce((sum, item) => sum + item.price * item.quantity, 0)
  );

  addItem(product: Product) {
    this.state.update(s => {
      const existing = s.items.find(i => i.productId === product.id);
      if (existing) {
        return {
          ...s,
          items: s.items.map(i =>
            i.productId === product.id
              ? { ...i, quantity: i.quantity + 1 }
              : i
          ),
        };
      }
      return {
        ...s,
        items: [...s.items, {
          productId: product.id,
          name: product.name,
          price: product.price,
          quantity: 1,
        }],
      };
    });
  }

  toggleCart() {
    this.state.update(s => ({ ...s, isOpen: !s.isOpen }));
  }
}
```

### Effect-Based Side Effects

```typescript
import { Injectable, signal, effect, inject, DestroyRef } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private http = inject(HttpClient);
  private destroyRef = inject(DestroyRef);

  // State
  private _query = signal('');
  private _results = signal<SearchResult[]>([]);
  private _isLoading = signal(false);

  readonly query = this._query.asReadonly();
  readonly results = this._results.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();

  readonly hasResults = computed(() => this._results().length > 0);

  constructor() {
    // Debounced search effect
    let timeoutId: number;

    effect((onCleanup) => {
      const query = this._query();

      onCleanup(() => clearTimeout(timeoutId));

      if (!query || query.length < 3) {
        this._results.set([]);
        return;
      }

      timeoutId = window.setTimeout(() => {
        this.performSearch(query);
      }, 300);
    });
  }

  setQuery(query: string) {
    this._query.set(query);
  }

  private async performSearch(query: string) {
    this._isLoading.set(true);

    try {
      const results = await firstValueFrom(
        this.http.get<SearchResult[]>(`/api/search?q=${encodeURIComponent(query)}`)
      );
      this._results.set(results);
    } catch {
      this._results.set([]);
    } finally {
      this._isLoading.set(false);
    }
  }
}
```

### Local Storage Persistence

```typescript
@Injectable({ providedIn: 'root' })
export class SettingsService {
  private readonly STORAGE_KEY = 'app_settings';

  private state = signal(this.loadFromStorage());

  readonly settings = this.state.asReadonly();
  readonly theme = computed(() => this.state().theme);
  readonly language = computed(() => this.state().language);
  readonly notifications = computed(() => this.state().notifications);

  constructor() {
    // Persist to localStorage on changes
    effect(() => {
      const settings = this.state();
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(settings));
    });
  }

  private loadFromStorage(): Settings {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      return stored ? JSON.parse(stored) : this.getDefaults();
    } catch {
      return this.getDefaults();
    }
  }

  private getDefaults(): Settings {
    return {
      theme: 'light',
      language: 'en',
      notifications: true,
    };
  }

  updateSettings(updates: Partial<Settings>) {
    this.state.update(s => ({ ...s, ...updates }));
  }

  resetToDefaults() {
    this.state.set(this.getDefaults());
  }
}
```

### Computed Chains

```typescript
@Injectable({ providedIn: 'root' })
export class DashboardStore {
  private _data = signal<DashboardData | null>(null);
  private _dateRange = signal<DateRange>({ start: new Date(), end: new Date() });
  private _groupBy = signal<'day' | 'week' | 'month'>('day');

  readonly data = this._data.asReadonly();
  readonly dateRange = this._dateRange.asReadonly();
  readonly groupBy = this._groupBy.asReadonly();

  // Computed chain
  readonly filteredData = computed(() => {
    const data = this._data();
    const range = this._dateRange();

    if (!data) return null;

    return {
      ...data,
      entries: data.entries.filter(e =>
        e.date >= range.start && e.date <= range.end
      ),
    };
  });

  readonly groupedData = computed(() => {
    const filtered = this.filteredData();
    const groupBy = this._groupBy();

    if (!filtered) return null;

    return groupEntries(filtered.entries, groupBy);
  });

  readonly summary = computed(() => {
    const grouped = this.groupedData();

    if (!grouped) return null;

    return {
      totalRevenue: grouped.reduce((sum, g) => sum + g.revenue, 0),
      totalOrders: grouped.reduce((sum, g) => sum + g.orders, 0),
      avgOrderValue: /* calculate */,
    };
  });

  readonly chartData = computed(() => {
    const grouped = this.groupedData();

    if (!grouped) return { labels: [], datasets: [] };

    return {
      labels: grouped.map(g => g.label),
      datasets: [{
        label: 'Revenue',
        data: grouped.map(g => g.revenue),
      }],
    };
  });
}
```

## Signal Equality

```typescript
// Custom equality function
const userSignal = signal(
  { id: '1', name: 'John' },
  {
    equal: (a, b) => a.id === b.id,
  }
);

// Update triggers only if ID changes
userSignal.set({ id: '1', name: 'Jane' }); // No update
userSignal.set({ id: '2', name: 'Jane' }); // Updates
```

## Best Practices

1. **Keep signals simple**: Prefer flat state over deeply nested
2. **Use computed liberally**: Derive values, don't duplicate state
3. **Make state read-only**: Expose via `asReadonly()`
4. **Clean up effects**: Use `onCleanup` for side effects
5. **Avoid effects for derived state**: Use `computed` instead
6. **Use entity patterns**: For collections of items
7. **Consider persistence**: For settings and preferences
