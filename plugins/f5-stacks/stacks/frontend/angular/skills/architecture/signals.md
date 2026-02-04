# Angular Signals

## Overview

Signals are Angular's reactive primitive for managing state. They provide fine-grained reactivity with automatic tracking and efficient updates.

## Basic Signals

```typescript
import { signal, computed, effect } from '@angular/core';

@Component({...})
export class CounterComponent {
  // Create a writable signal
  count = signal(0);

  // Create a computed signal (derived state)
  doubleCount = computed(() => this.count() * 2);

  // Read signal value by calling it
  increment() {
    // Set new value
    this.count.set(this.count() + 1);
  }

  decrement() {
    // Update based on previous value
    this.count.update(current => current - 1);
  }

  reset() {
    this.count.set(0);
  }
}
```

## Signal Types

### Writable Signals

```typescript
import { signal, WritableSignal } from '@angular/core';

// Basic types
const count: WritableSignal<number> = signal(0);
const name: WritableSignal<string> = signal('');
const isActive: WritableSignal<boolean> = signal(false);

// Complex types
interface User {
  id: string;
  name: string;
  email: string;
}

const user: WritableSignal<User | null> = signal(null);
const items: WritableSignal<string[]> = signal([]);
const config: WritableSignal<Record<string, unknown>> = signal({});
```

### Computed Signals

```typescript
import { signal, computed, Signal } from '@angular/core';

const firstName = signal('John');
const lastName = signal('Doe');

// Computed from other signals
const fullName: Signal<string> = computed(() =>
  `${firstName()} ${lastName()}`
);

// Computed with complex logic
const items = signal([
  { name: 'Item 1', price: 10 },
  { name: 'Item 2', price: 20 },
]);

const total = computed(() =>
  items().reduce((sum, item) => sum + item.price, 0)
);

const hasItems = computed(() => items().length > 0);

// Computed from multiple sources
const filter = signal('');
const sortOrder = signal<'asc' | 'desc'>('asc');

const filteredItems = computed(() => {
  let result = items().filter(item =>
    item.name.toLowerCase().includes(filter().toLowerCase())
  );

  return sortOrder() === 'asc'
    ? result.sort((a, b) => a.name.localeCompare(b.name))
    : result.sort((a, b) => b.name.localeCompare(a.name));
});
```

### Read-Only Signals

```typescript
import { signal, Signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class UserService {
  // Private writable signal
  private _user = signal<User | null>(null);

  // Public read-only signal
  readonly user: Signal<User | null> = this._user.asReadonly();

  // Alternative: expose as computed
  readonly isLoggedIn = computed(() => this._user() !== null);

  setUser(user: User) {
    this._user.set(user);
  }
}
```

## Effects

Effects run side effects when signals change.

```typescript
import { effect, signal, inject, DestroyRef } from '@angular/core';

@Component({...})
export class SearchComponent {
  private destroyRef = inject(DestroyRef);

  searchTerm = signal('');
  results = signal<SearchResult[]>([]);

  constructor() {
    // Effect runs when searchTerm changes
    effect(() => {
      const term = this.searchTerm();

      if (term.length >= 3) {
        this.performSearch(term);
      }
    });

    // Effect with cleanup
    effect((onCleanup) => {
      const term = this.searchTerm();
      const controller = new AbortController();

      fetch(`/api/search?q=${term}`, { signal: controller.signal })
        .then(res => res.json())
        .then(data => this.results.set(data));

      onCleanup(() => {
        controller.abort();
      });
    });
  }

  private performSearch(term: string) {
    // Search implementation
  }
}
```

### Effect Options

```typescript
import { effect, Injector, runInInjectionContext } from '@angular/core';

// Effect with explicit injector
effect(() => {
  console.log('Value changed');
}, { injector: this.injector });

// Manual cleanup
const effectRef = effect(() => {
  console.log('Tracking...');
});

// Later: stop the effect
effectRef.destroy();

// Effect outside constructor (requires injector)
class MyComponent {
  private injector = inject(Injector);

  ngOnInit() {
    runInInjectionContext(this.injector, () => {
      effect(() => {
        // Effect logic
      });
    });
  }
}
```

## Signal-Based Services

```typescript
import { Injectable, signal, computed } from '@angular/core';

interface CartItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

@Injectable({ providedIn: 'root' })
export class CartService {
  // Private state
  private _items = signal<CartItem[]>([]);

  // Public selectors
  readonly items = this._items.asReadonly();

  readonly itemCount = computed(() =>
    this._items().reduce((sum, item) => sum + item.quantity, 0)
  );

  readonly total = computed(() =>
    this._items().reduce((sum, item) => sum + item.price * item.quantity, 0)
  );

  readonly isEmpty = computed(() => this._items().length === 0);

  // Actions
  addItem(product: { id: string; name: string; price: number }) {
    this._items.update(items => {
      const existing = items.find(i => i.id === product.id);

      if (existing) {
        return items.map(i =>
          i.id === product.id ? { ...i, quantity: i.quantity + 1 } : i
        );
      }

      return [...items, { ...product, quantity: 1 }];
    });
  }

  removeItem(id: string) {
    this._items.update(items => items.filter(i => i.id !== id));
  }

  updateQuantity(id: string, quantity: number) {
    if (quantity <= 0) {
      this.removeItem(id);
      return;
    }

    this._items.update(items =>
      items.map(i => (i.id === id ? { ...i, quantity } : i))
    );
  }

  clear() {
    this._items.set([]);
  }
}
```

## Input/Output Signals

### Input Signals (Angular 17.1+)

```typescript
import { Component, input } from '@angular/core';

@Component({
  selector: 'app-user-profile',
  template: `<h1>{{ user().name }}</h1>`,
})
export class UserProfileComponent {
  // Required input
  user = input.required<User>();

  // Optional with default
  showAvatar = input(true);

  // With transform
  size = input(100, {
    transform: (v: number | string) => typeof v === 'string' ? parseInt(v, 10) : v,
  });

  // With alias
  data = input.required<Data>({ alias: 'userData' });
}
```

### Output Signals (Angular 17+)

```typescript
import { Component, output } from '@angular/core';

@Component({
  selector: 'app-button',
  template: `<button (click)="handleClick()">Click me</button>`,
})
export class ButtonComponent {
  // Basic output
  clicked = output<void>();

  // Typed output
  valueChange = output<string>();

  // With alias
  save = output<Data>({ alias: 'onSave' });

  handleClick() {
    this.clicked.emit();
  }
}
```

### Model Signals (Two-Way Binding)

```typescript
import { Component, model } from '@angular/core';

@Component({
  selector: 'app-slider',
  template: `
    <input
      type="range"
      [value]="value()"
      (input)="value.set($any($event.target).value)"
    >
  `,
})
export class SliderComponent {
  value = model(50);
}

// Usage
@Component({
  template: `
    <app-slider [(value)]="volume" />
    <p>Volume: {{ volume() }}</p>
  `,
})
export class PlayerComponent {
  volume = signal(50);
}
```

## RxJS Interoperability

```typescript
import { toSignal, toObservable } from '@angular/core/rxjs-interop';
import { HttpClient } from '@angular/common/http';
import { debounceTime, switchMap, of } from 'rxjs';

@Component({...})
export class SearchComponent {
  private http = inject(HttpClient);

  // Convert Observable to Signal
  users = toSignal(
    this.http.get<User[]>('/api/users'),
    { initialValue: [] }
  );

  // Convert Signal to Observable
  searchTerm = signal('');

  searchResults = toSignal(
    toObservable(this.searchTerm).pipe(
      debounceTime(300),
      switchMap(term =>
        term ? this.http.get<User[]>(`/api/search?q=${term}`) : of([])
      )
    ),
    { initialValue: [] }
  );
}
```

## Signal Patterns

### Feature Store Pattern

```typescript
interface FeatureState {
  items: Item[];
  selectedId: string | null;
  isLoading: boolean;
  error: string | null;
}

@Injectable({ providedIn: 'root' })
export class FeatureStore {
  private state = signal<FeatureState>({
    items: [],
    selectedId: null,
    isLoading: false,
    error: null,
  });

  // Selectors
  readonly items = computed(() => this.state().items);
  readonly selectedId = computed(() => this.state().selectedId);
  readonly isLoading = computed(() => this.state().isLoading);
  readonly error = computed(() => this.state().error);

  readonly selected = computed(() => {
    const id = this.selectedId();
    return id ? this.items().find(item => item.id === id) : null;
  });

  // Actions
  setItems(items: Item[]) {
    this.state.update(s => ({ ...s, items, isLoading: false }));
  }

  setLoading(isLoading: boolean) {
    this.state.update(s => ({ ...s, isLoading }));
  }

  select(id: string) {
    this.state.update(s => ({ ...s, selectedId: id }));
  }
}
```

### Signal Equality

```typescript
import { signal } from '@angular/core';

// Default equality (===)
const obj = signal({ name: 'John' });

// Custom equality
const user = signal(
  { id: '1', name: 'John' },
  { equal: (a, b) => a.id === b.id }
);

// Updates only if ID changes
user.set({ id: '1', name: 'Jane' }); // No update (same ID)
user.set({ id: '2', name: 'Jane' }); // Updates
```

## Best Practices

1. **Use computed for derived state**: Never duplicate state that can be computed
2. **Keep signals immutable**: Always use `set` or `update`, never mutate directly
3. **Make signals read-only when possible**: Use `asReadonly()` for public APIs
4. **Use effects sparingly**: Prefer computed signals over effects when possible
5. **Clean up effects**: Use `onCleanup` for subscriptions and async operations
6. **Type your signals**: Always specify types for complex data structures
