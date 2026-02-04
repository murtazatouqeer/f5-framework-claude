# NgRx SignalStore

## Overview

NgRx SignalStore is a modern, signal-based state management solution for Angular 17+. It combines the predictability of NgRx with the simplicity of signals.

## Installation

```bash
npm install @ngrx/signals
```

## Basic SignalStore

```typescript
import { signalStore, withState, withComputed, withMethods, patchState } from '@ngrx/signals';
import { computed } from '@angular/core';

interface CounterState {
  count: number;
}

export const CounterStore = signalStore(
  withState<CounterState>({ count: 0 }),

  withComputed(({ count }) => ({
    doubleCount: computed(() => count() * 2),
    isPositive: computed(() => count() > 0),
  })),

  withMethods(({ count, ...store }) => ({
    increment() {
      patchState(store, { count: count() + 1 });
    },
    decrement() {
      patchState(store, { count: count() - 1 });
    },
    reset() {
      patchState(store, { count: 0 });
    },
    setCount(value: number) {
      patchState(store, { count: value });
    },
  })),
);

// Usage in component
@Component({
  providers: [CounterStore],
  template: `
    <p>Count: {{ store.count() }}</p>
    <p>Double: {{ store.doubleCount() }}</p>
    <button (click)="store.increment()">+</button>
    <button (click)="store.decrement()">-</button>
  `,
})
export class CounterComponent {
  readonly store = inject(CounterStore);
}
```

## Feature Store Pattern

```typescript
import {
  signalStore,
  withState,
  withComputed,
  withMethods,
  withHooks,
  patchState,
} from '@ngrx/signals';
import { computed, inject } from '@angular/core';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, switchMap, tap } from 'rxjs';
import { tapResponse } from '@ngrx/operators';

interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
}

interface ProductsState {
  products: Product[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;
  filter: {
    category: string | null;
    search: string;
  };
}

const initialState: ProductsState = {
  products: [],
  selectedId: null,
  isLoading: false,
  error: null,
  filter: {
    category: null,
    search: '',
  },
};

export const ProductsStore = signalStore(
  { providedIn: 'root' },

  withState(initialState),

  withComputed(({ products, selectedId, filter }) => ({
    // Selected product
    selectedProduct: computed(() => {
      const id = selectedId();
      return products().find(p => p.id === id) ?? null;
    }),

    // Filtered products
    filteredProducts: computed(() => {
      const all = products();
      const { category, search } = filter();

      return all.filter(p =>
        (!category || p.category === category) &&
        p.name.toLowerCase().includes(search.toLowerCase())
      );
    }),

    // Categories
    categories: computed(() =>
      [...new Set(products().map(p => p.category))]
    ),

    // Summary
    summary: computed(() => ({
      total: products().length,
      totalValue: products().reduce((sum, p) => sum + p.price, 0),
    })),
  })),

  withMethods((store, productService = inject(ProductService)) => ({
    // Sync methods
    selectProduct(id: string | null) {
      patchState(store, { selectedId: id });
    },

    setFilter(filter: Partial<ProductsState['filter']>) {
      patchState(store, state => ({
        filter: { ...state.filter, ...filter },
      }));
    },

    clearFilter() {
      patchState(store, {
        filter: { category: null, search: '' },
      });
    },

    // Async methods with rxMethod
    loadProducts: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { isLoading: true, error: null })),
        switchMap(() =>
          productService.getAll().pipe(
            tapResponse({
              next: products => patchState(store, { products, isLoading: false }),
              error: (error: Error) =>
                patchState(store, { error: error.message, isLoading: false }),
            })
          )
        )
      )
    ),

    addProduct: rxMethod<Omit<Product, 'id'>>(
      pipe(
        switchMap(product =>
          productService.create(product).pipe(
            tapResponse({
              next: created =>
                patchState(store, state => ({
                  products: [...state.products, created],
                })),
              error: (error: Error) =>
                patchState(store, { error: error.message }),
            })
          )
        )
      )
    ),

    deleteProduct: rxMethod<string>(
      pipe(
        switchMap(id =>
          productService.delete(id).pipe(
            tapResponse({
              next: () =>
                patchState(store, state => ({
                  products: state.products.filter(p => p.id !== id),
                  selectedId: state.selectedId === id ? null : state.selectedId,
                })),
              error: (error: Error) =>
                patchState(store, { error: error.message }),
            })
          )
        )
      )
    ),
  })),

  // Lifecycle hooks
  withHooks({
    onInit(store) {
      // Load products on store initialization
      store.loadProducts();
    },
    onDestroy(store) {
      console.log('ProductsStore destroyed');
    },
  }),
);
```

## Entity Management

```typescript
import { signalStore, withState, withComputed, withMethods, patchState } from '@ngrx/signals';
import { withEntities, addEntity, removeEntity, updateEntity, setAllEntities } from '@ngrx/signals/entities';
import { computed } from '@angular/core';

interface Todo {
  id: string;
  title: string;
  completed: boolean;
}

export const TodosStore = signalStore(
  { providedIn: 'root' },

  // Entity state
  withEntities<Todo>(),

  // Additional state
  withState({
    filter: 'all' as 'all' | 'active' | 'completed',
    isLoading: false,
  }),

  // Computed
  withComputed(({ entities, filter }) => ({
    filteredTodos: computed(() => {
      const all = entities();
      switch (filter()) {
        case 'active':
          return all.filter(t => !t.completed);
        case 'completed':
          return all.filter(t => t.completed);
        default:
          return all;
      }
    }),

    activeCount: computed(() =>
      entities().filter(t => !t.completed).length
    ),

    completedCount: computed(() =>
      entities().filter(t => t.completed).length
    ),

    allCompleted: computed(() =>
      entities().length > 0 && entities().every(t => t.completed)
    ),
  })),

  // Methods
  withMethods(store => ({
    addTodo(title: string) {
      const todo: Todo = {
        id: crypto.randomUUID(),
        title,
        completed: false,
      };
      patchState(store, addEntity(todo));
    },

    toggleTodo(id: string) {
      patchState(
        store,
        updateEntity({ id, changes: todo => ({ completed: !todo.completed }) })
      );
    },

    removeTodo(id: string) {
      patchState(store, removeEntity(id));
    },

    setFilter(filter: 'all' | 'active' | 'completed') {
      patchState(store, { filter });
    },

    toggleAll() {
      const allCompleted = store.allCompleted();
      patchState(
        store,
        updateEntity({
          id: (entity) => true, // Update all
          changes: { completed: !allCompleted },
        })
      );
    },

    clearCompleted() {
      const completedIds = store.entities()
        .filter(t => t.completed)
        .map(t => t.id);

      completedIds.forEach(id => patchState(store, removeEntity(id)));
    },

    loadTodos(todos: Todo[]) {
      patchState(store, setAllEntities(todos));
    },
  })),
);
```

## Custom Features

```typescript
import { signalStoreFeature, withState, withMethods, patchState } from '@ngrx/signals';

// Reusable loading feature
export function withLoading() {
  return signalStoreFeature(
    withState({ isLoading: false, error: null as string | null }),
    withMethods(store => ({
      setLoading(isLoading: boolean) {
        patchState(store, { isLoading });
      },
      setError(error: string | null) {
        patchState(store, { error, isLoading: false });
      },
      clearError() {
        patchState(store, { error: null });
      },
    })),
  );
}

// Reusable selection feature
export function withSelection<T extends { id: string }>() {
  return signalStoreFeature(
    withState({ selectedId: null as string | null }),
    withComputed(({ selectedId, entities }) => ({
      selectedEntity: computed(() => {
        const id = selectedId();
        return id ? entities().find((e: T) => e.id === id) : null;
      }),
    })),
    withMethods(store => ({
      select(id: string | null) {
        patchState(store, { selectedId: id });
      },
      clearSelection() {
        patchState(store, { selectedId: null });
      },
    })),
  );
}

// Use features in store
export const UsersStore = signalStore(
  { providedIn: 'root' },
  withEntities<User>(),
  withLoading(),
  withSelection<User>(),
  withMethods(store => ({
    // Additional methods
  })),
);
```

## RxJS Integration

```typescript
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { pipe, debounceTime, distinctUntilChanged, switchMap, tap } from 'rxjs';
import { tapResponse } from '@ngrx/operators';

export const SearchStore = signalStore(
  withState({
    query: '',
    results: [] as SearchResult[],
    isSearching: false,
  }),

  withMethods((store, searchService = inject(SearchService)) => ({
    setQuery(query: string) {
      patchState(store, { query });
    },

    // Debounced search
    search: rxMethod<string>(
      pipe(
        debounceTime(300),
        distinctUntilChanged(),
        tap(() => patchState(store, { isSearching: true })),
        switchMap(query =>
          searchService.search(query).pipe(
            tapResponse({
              next: results => patchState(store, { results, isSearching: false }),
              error: () => patchState(store, { results: [], isSearching: false }),
            })
          )
        )
      )
    ),
  })),

  withHooks({
    onInit(store) {
      // Connect query changes to search
      effect(() => {
        const query = store.query();
        if (query.length >= 2) {
          store.search(query);
        }
      });
    },
  }),
);
```

## Component Usage

```typescript
@Component({
  selector: 'app-products',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="filters">
      <input
        type="text"
        [value]="store.filter().search"
        (input)="onSearchChange($event)"
        placeholder="Search products..."
      >

      <select
        [value]="store.filter().category ?? ''"
        (change)="onCategoryChange($event)"
      >
        <option value="">All Categories</option>
        @for (category of store.categories(); track category) {
          <option [value]="category">{{ category }}</option>
        }
      </select>
    </div>

    @if (store.isLoading()) {
      <div class="loading">Loading...</div>
    }

    @if (store.error(); as error) {
      <div class="error">{{ error }}</div>
    }

    <div class="products">
      @for (product of store.filteredProducts(); track product.id) {
        <div
          class="product"
          [class.selected]="product.id === store.selectedId()"
          (click)="store.selectProduct(product.id)"
        >
          <h3>{{ product.name }}</h3>
          <p>{{ product.price | currency }}</p>
        </div>
      }
    </div>

    <div class="summary">
      <p>Total: {{ store.summary().total }} products</p>
      <p>Value: {{ store.summary().totalValue | currency }}</p>
    </div>
  `,
})
export class ProductsComponent {
  readonly store = inject(ProductsStore);

  onSearchChange(event: Event) {
    const search = (event.target as HTMLInputElement).value;
    this.store.setFilter({ search });
  }

  onCategoryChange(event: Event) {
    const category = (event.target as HTMLSelectElement).value || null;
    this.store.setFilter({ category });
  }
}
```

## Best Practices

1. **Use providedIn: 'root'**: For singleton stores
2. **Split by feature**: One store per feature/domain
3. **Create reusable features**: Extract common patterns
4. **Use rxMethod for async**: Better RxJS integration
5. **Leverage computed**: For derived state
6. **Use entity helpers**: For collection management
7. **Type your state**: Full TypeScript support
