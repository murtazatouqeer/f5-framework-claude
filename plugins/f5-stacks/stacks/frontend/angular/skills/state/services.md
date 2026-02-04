# Angular Services for State Management

## Overview

Services in Angular are singleton classes that provide shared functionality and state across components. With signals, services become powerful state containers.

## Basic Service

```typescript
import { Injectable, signal, computed } from '@angular/core';

@Injectable({
  providedIn: 'root', // Singleton across the app
})
export class CounterService {
  // Private writable state
  private _count = signal(0);

  // Public read-only access
  readonly count = this._count.asReadonly();

  // Computed values
  readonly isPositive = computed(() => this._count() > 0);
  readonly displayCount = computed(() => `Count: ${this._count()}`);

  // Actions
  increment() {
    this._count.update(c => c + 1);
  }

  decrement() {
    this._count.update(c => c - 1);
  }

  reset() {
    this._count.set(0);
  }

  setCount(value: number) {
    this._count.set(value);
  }
}
```

## Service with Complex State

```typescript
interface TodoItem {
  id: string;
  title: string;
  completed: boolean;
  createdAt: Date;
}

interface TodoState {
  items: TodoItem[];
  filter: 'all' | 'active' | 'completed';
  isLoading: boolean;
  error: string | null;
}

@Injectable({ providedIn: 'root' })
export class TodoService {
  // Combined state object
  private state = signal<TodoState>({
    items: [],
    filter: 'all',
    isLoading: false,
    error: null,
  });

  // Selectors (computed from state)
  readonly items = computed(() => this.state().items);
  readonly filter = computed(() => this.state().filter);
  readonly isLoading = computed(() => this.state().isLoading);
  readonly error = computed(() => this.state().error);

  readonly filteredItems = computed(() => {
    const items = this.items();
    const filter = this.filter();

    switch (filter) {
      case 'active':
        return items.filter(item => !item.completed);
      case 'completed':
        return items.filter(item => item.completed);
      default:
        return items;
    }
  });

  readonly activeCount = computed(() =>
    this.items().filter(item => !item.completed).length
  );

  readonly completedCount = computed(() =>
    this.items().filter(item => item.completed).length
  );

  readonly allCompleted = computed(() =>
    this.items().length > 0 && this.items().every(item => item.completed)
  );

  // Actions
  addTodo(title: string) {
    const newItem: TodoItem = {
      id: crypto.randomUUID(),
      title,
      completed: false,
      createdAt: new Date(),
    };

    this.state.update(s => ({
      ...s,
      items: [...s.items, newItem],
    }));
  }

  toggleTodo(id: string) {
    this.state.update(s => ({
      ...s,
      items: s.items.map(item =>
        item.id === id ? { ...item, completed: !item.completed } : item
      ),
    }));
  }

  removeTodo(id: string) {
    this.state.update(s => ({
      ...s,
      items: s.items.filter(item => item.id !== id),
    }));
  }

  setFilter(filter: 'all' | 'active' | 'completed') {
    this.state.update(s => ({ ...s, filter }));
  }

  clearCompleted() {
    this.state.update(s => ({
      ...s,
      items: s.items.filter(item => !item.completed),
    }));
  }

  toggleAll() {
    const allCompleted = this.allCompleted();
    this.state.update(s => ({
      ...s,
      items: s.items.map(item => ({ ...item, completed: !allCompleted })),
    }));
  }
}
```

## Service with HTTP Integration

```typescript
import { Injectable, inject, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

@Injectable({ providedIn: 'root' })
export class UserService {
  private http = inject(HttpClient);
  private baseUrl = '/api/users';

  // State
  private _users = signal<User[]>([]);
  private _selectedId = signal<string | null>(null);
  private _isLoading = signal(false);
  private _error = signal<string | null>(null);

  // Selectors
  readonly users = this._users.asReadonly();
  readonly selectedId = this._selectedId.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();

  readonly selectedUser = computed(() => {
    const id = this._selectedId();
    return id ? this._users().find(u => u.id === id) : null;
  });

  readonly userCount = computed(() => this._users().length);

  // Async Actions
  async loadUsers(): Promise<void> {
    this._isLoading.set(true);
    this._error.set(null);

    try {
      const users = await firstValueFrom(
        this.http.get<User[]>(this.baseUrl)
      );
      this._users.set(users);
    } catch (err) {
      this._error.set('Failed to load users');
      console.error('Error loading users:', err);
    } finally {
      this._isLoading.set(false);
    }
  }

  async createUser(userData: Omit<User, 'id'>): Promise<User | null> {
    this._isLoading.set(true);

    try {
      const user = await firstValueFrom(
        this.http.post<User>(this.baseUrl, userData)
      );
      this._users.update(users => [...users, user]);
      return user;
    } catch (err) {
      this._error.set('Failed to create user');
      return null;
    } finally {
      this._isLoading.set(false);
    }
  }

  async updateUser(id: string, updates: Partial<User>): Promise<User | null> {
    try {
      const updated = await firstValueFrom(
        this.http.patch<User>(`${this.baseUrl}/${id}`, updates)
      );
      this._users.update(users =>
        users.map(u => (u.id === id ? updated : u))
      );
      return updated;
    } catch (err) {
      this._error.set('Failed to update user');
      return null;
    }
  }

  async deleteUser(id: string): Promise<boolean> {
    try {
      await firstValueFrom(this.http.delete(`${this.baseUrl}/${id}`));
      this._users.update(users => users.filter(u => u.id !== id));
      if (this._selectedId() === id) {
        this._selectedId.set(null);
      }
      return true;
    } catch (err) {
      this._error.set('Failed to delete user');
      return false;
    }
  }

  // Sync Actions
  selectUser(id: string | null) {
    this._selectedId.set(id);
  }

  clearError() {
    this._error.set(null);
  }
}
```

## Feature Store Pattern

```typescript
// Base store class for reusability
abstract class BaseStore<T extends object> {
  protected state: WritableSignal<T>;

  constructor(initialState: T) {
    this.state = signal(initialState);
  }

  protected select<K extends keyof T>(key: K): Signal<T[K]> {
    return computed(() => this.state()[key]);
  }

  protected update(updater: (state: T) => Partial<T>) {
    this.state.update(s => ({ ...s, ...updater(s) }));
  }

  protected set(newState: Partial<T>) {
    this.state.update(s => ({ ...s, ...newState }));
  }
}

// Concrete store implementation
interface ProductState {
  products: Product[];
  categories: Category[];
  selectedProductId: string | null;
  filters: {
    category: string | null;
    minPrice: number;
    maxPrice: number;
    search: string;
  };
  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };
  isLoading: boolean;
  error: string | null;
}

const initialProductState: ProductState = {
  products: [],
  categories: [],
  selectedProductId: null,
  filters: {
    category: null,
    minPrice: 0,
    maxPrice: Infinity,
    search: '',
  },
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },
  isLoading: false,
  error: null,
};

@Injectable({ providedIn: 'root' })
export class ProductStore extends BaseStore<ProductState> {
  private http = inject(HttpClient);

  constructor() {
    super(initialProductState);
  }

  // Selectors
  readonly products = this.select('products');
  readonly categories = this.select('categories');
  readonly isLoading = this.select('isLoading');
  readonly error = this.select('error');
  readonly filters = this.select('filters');
  readonly pagination = this.select('pagination');

  readonly selectedProduct = computed(() => {
    const id = this.state().selectedProductId;
    return id ? this.products().find(p => p.id === id) : null;
  });

  readonly filteredProducts = computed(() => {
    const { products, filters } = this.state();
    return products.filter(p =>
      (!filters.category || p.category === filters.category) &&
      p.price >= filters.minPrice &&
      p.price <= filters.maxPrice &&
      p.name.toLowerCase().includes(filters.search.toLowerCase())
    );
  });

  readonly paginatedProducts = computed(() => {
    const { page, pageSize } = this.pagination();
    const filtered = this.filteredProducts();
    const start = (page - 1) * pageSize;
    return filtered.slice(start, start + pageSize);
  });

  // Actions
  async loadProducts() {
    this.set({ isLoading: true, error: null });

    try {
      const products = await firstValueFrom(
        this.http.get<Product[]>('/api/products')
      );
      this.set({ products, isLoading: false });
    } catch {
      this.set({ error: 'Failed to load products', isLoading: false });
    }
  }

  setFilters(filters: Partial<ProductState['filters']>) {
    this.update(s => ({
      filters: { ...s.filters, ...filters },
      pagination: { ...s.pagination, page: 1 },
    }));
  }

  setPage(page: number) {
    this.update(s => ({
      pagination: { ...s.pagination, page },
    }));
  }

  selectProduct(id: string | null) {
    this.set({ selectedProductId: id });
  }
}
```

## Multi-Instance Services

```typescript
// Service that creates new instance for each injection
@Injectable() // Not providedIn: 'root'
export class FormStateService {
  private formData = signal<Record<string, unknown>>({});
  private isDirty = signal(false);
  private isSubmitting = signal(false);

  readonly data = this.formData.asReadonly();
  readonly dirty = this.isDirty.asReadonly();
  readonly submitting = this.isSubmitting.asReadonly();

  setField(key: string, value: unknown) {
    this.formData.update(data => ({ ...data, [key]: value }));
    this.isDirty.set(true);
  }

  reset(initialData: Record<string, unknown> = {}) {
    this.formData.set(initialData);
    this.isDirty.set(false);
  }

  async submit<T>(submitFn: (data: Record<string, unknown>) => Promise<T>): Promise<T> {
    this.isSubmitting.set(true);
    try {
      const result = await submitFn(this.formData());
      this.isDirty.set(false);
      return result;
    } finally {
      this.isSubmitting.set(false);
    }
  }
}

// Usage in component
@Component({
  providers: [FormStateService], // New instance per component
})
export class UserFormComponent {
  private formState = inject(FormStateService);
}
```

## Best Practices

1. **Use providedIn: 'root' for singletons**: Tree-shakable and simple
2. **Make state private**: Expose read-only selectors
3. **Use computed for derived state**: Automatic caching and updates
4. **Keep actions focused**: Single responsibility
5. **Handle errors gracefully**: Store error state for UI feedback
6. **Use firstValueFrom for HTTP**: Convert Observable to Promise
7. **Prefer immutable updates**: Use spread operator or update()
