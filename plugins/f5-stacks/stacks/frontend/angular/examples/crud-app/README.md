# Angular CRUD App Example

Complete CRUD application using Angular 17+ best practices.

## Features

- Standalone components
- Signal-based state management
- NgRx SignalStore
- Reactive forms with validation
- HTTP client with interceptors
- OnPush change detection
- Lazy loading routes

## Project Structure

```
src/
├── app/
│   ├── app.component.ts
│   ├── app.config.ts
│   ├── app.routes.ts
│   ├── core/
│   │   ├── interceptors/
│   │   │   ├── auth.interceptor.ts
│   │   │   └── error.interceptor.ts
│   │   ├── services/
│   │   │   ├── api.service.ts
│   │   │   └── notification.service.ts
│   │   └── guards/
│   │       └── auth.guard.ts
│   ├── shared/
│   │   ├── components/
│   │   │   ├── loading-spinner/
│   │   │   ├── confirm-dialog/
│   │   │   └── pagination/
│   │   └── pipes/
│   │       └── truncate.pipe.ts
│   └── features/
│       └── products/
│           ├── products.routes.ts
│           ├── store/
│           │   └── products.store.ts
│           ├── services/
│           │   └── products-api.service.ts
│           ├── models/
│           │   └── product.model.ts
│           └── components/
│               ├── product-list/
│               ├── product-form/
│               └── product-detail/
└── environments/
    ├── environment.ts
    └── environment.prod.ts
```

## Key Files

### App Configuration

```typescript
// app.config.ts
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withComponentInputBinding } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withComponentInputBinding()),
    provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
  ],
};
```

### Routes

```typescript
// app.routes.ts
import { Routes } from '@angular/router';

export const routes: Routes = [
  { path: '', redirectTo: 'products', pathMatch: 'full' },
  {
    path: 'products',
    loadChildren: () => import('./features/products/products.routes'),
  },
];

// features/products/products.routes.ts
import { Routes } from '@angular/router';

export default [
  {
    path: '',
    loadComponent: () =>
      import('./components/product-list/product-list.component'),
  },
  {
    path: 'new',
    loadComponent: () =>
      import('./components/product-form/product-form.component'),
  },
  {
    path: ':id',
    loadComponent: () =>
      import('./components/product-detail/product-detail.component'),
  },
  {
    path: ':id/edit',
    loadComponent: () =>
      import('./components/product-form/product-form.component'),
  },
] satisfies Routes;
```

### Product Store (SignalStore)

```typescript
// features/products/store/products.store.ts
import {
  signalStore,
  withState,
  withComputed,
  withMethods,
  patchState,
} from '@ngrx/signals';
import { withEntities, setAllEntities, addEntity, updateEntity, removeEntity } from '@ngrx/signals/entities';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { computed, inject } from '@angular/core';
import { pipe, switchMap, tap } from 'rxjs';
import { tapResponse } from '@ngrx/operators';
import { ProductsApiService } from '../services/products-api.service';
import { Product } from '../models/product.model';

interface ProductsState {
  isLoading: boolean;
  error: string | null;
  filter: string;
}

export const ProductsStore = signalStore(
  { providedIn: 'root' },
  withEntities<Product>(),
  withState<ProductsState>({
    isLoading: false,
    error: null,
    filter: '',
  }),
  withComputed(({ entities, filter }) => ({
    filteredProducts: computed(() => {
      const f = filter().toLowerCase();
      if (!f) return entities();
      return entities().filter(p =>
        p.name.toLowerCase().includes(f) ||
        p.description?.toLowerCase().includes(f)
      );
    }),
    totalCount: computed(() => entities().length),
  })),
  withMethods((store, api = inject(ProductsApiService)) => ({
    setFilter(filter: string) {
      patchState(store, { filter });
    },

    loadAll: rxMethod<void>(
      pipe(
        tap(() => patchState(store, { isLoading: true, error: null })),
        switchMap(() => api.getAll().pipe(
          tapResponse({
            next: products => patchState(store, setAllEntities(products), { isLoading: false }),
            error: (err: Error) => patchState(store, { error: err.message, isLoading: false }),
          })
        ))
      )
    ),

    create: rxMethod<Omit<Product, 'id'>>(
      pipe(
        switchMap(product => api.create(product).pipe(
          tapResponse({
            next: created => patchState(store, addEntity(created)),
            error: (err: Error) => patchState(store, { error: err.message }),
          })
        ))
      )
    ),

    update: rxMethod<Product>(
      pipe(
        switchMap(product => api.update(product.id, product).pipe(
          tapResponse({
            next: updated => patchState(store, updateEntity({ id: updated.id, changes: updated })),
            error: (err: Error) => patchState(store, { error: err.message }),
          })
        ))
      )
    ),

    delete: rxMethod<string>(
      pipe(
        switchMap(id => api.delete(id).pipe(
          tapResponse({
            next: () => patchState(store, removeEntity(id)),
            error: (err: Error) => patchState(store, { error: err.message }),
          })
        ))
      )
    ),
  })),
);
```

### Product List Component

```typescript
// features/products/components/product-list/product-list.component.ts
import { Component, inject, effect } from '@angular/core';
import { RouterLink } from '@angular/router';
import { ProductsStore } from '../../store/products.store';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [RouterLink],
  template: `
    <div class="product-list">
      <header>
        <h1>Products</h1>
        <a routerLink="new" class="btn-primary">Add Product</a>
      </header>

      <input
        type="search"
        placeholder="Filter products..."
        [value]="store.filter()"
        (input)="onFilter($event)"
      />

      @if (store.isLoading()) {
        <div class="loading">Loading...</div>
      } @else if (store.error(); as error) {
        <div class="error">{{ error }}</div>
      } @else {
        <div class="grid">
          @for (product of store.filteredProducts(); track product.id) {
            <div class="card">
              <h3>{{ product.name }}</h3>
              <p>{{ product.description }}</p>
              <p class="price">\${{ product.price }}</p>
              <div class="actions">
                <a [routerLink]="[product.id]">View</a>
                <a [routerLink]="[product.id, 'edit']">Edit</a>
                <button (click)="onDelete(product.id)">Delete</button>
              </div>
            </div>
          } @empty {
            <p>No products found</p>
          }
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export default class ProductListComponent {
  protected store = inject(ProductsStore);

  constructor() {
    this.store.loadAll();
  }

  onFilter(event: Event) {
    const value = (event.target as HTMLInputElement).value;
    this.store.setFilter(value);
  }

  onDelete(id: string) {
    if (confirm('Are you sure?')) {
      this.store.delete(id);
    }
  }
}
```

### Product Form Component

```typescript
// features/products/components/product-form/product-form.component.ts
import { Component, inject, input, effect } from '@angular/core';
import { Router } from '@angular/router';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { ProductsStore } from '../../store/products.store';
import { ProductsApiService } from '../../services/products-api.service';
import { toSignal } from '@angular/core/rxjs-interop';

@Component({
  selector: 'app-product-form',
  standalone: true,
  imports: [ReactiveFormsModule],
  template: `
    <div class="product-form">
      <h1>{{ id() ? 'Edit' : 'Create' }} Product</h1>

      <form [formGroup]="form" (ngSubmit)="onSubmit()">
        <div class="field">
          <label for="name">Name</label>
          <input id="name" formControlName="name" />
          @if (form.controls.name.errors?.['required'] && form.controls.name.touched) {
            <span class="error">Name is required</span>
          }
        </div>

        <div class="field">
          <label for="description">Description</label>
          <textarea id="description" formControlName="description"></textarea>
        </div>

        <div class="field">
          <label for="price">Price</label>
          <input id="price" type="number" formControlName="price" />
          @if (form.controls.price.errors?.['min']) {
            <span class="error">Price must be positive</span>
          }
        </div>

        <div class="actions">
          <button type="button" (click)="onCancel()">Cancel</button>
          <button type="submit" [disabled]="form.invalid">Save</button>
        </div>
      </form>
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export default class ProductFormComponent {
  private fb = inject(FormBuilder);
  private router = inject(Router);
  private store = inject(ProductsStore);
  private api = inject(ProductsApiService);

  id = input<string>();

  form = this.fb.nonNullable.group({
    name: ['', [Validators.required, Validators.minLength(2)]],
    description: [''],
    price: [0, [Validators.required, Validators.min(0)]],
  });

  constructor() {
    effect(() => {
      const productId = this.id();
      if (productId) {
        this.api.getById(productId).subscribe(product => {
          this.form.patchValue(product);
        });
      }
    });
  }

  onSubmit() {
    if (this.form.invalid) return;

    const value = this.form.getRawValue();
    const productId = this.id();

    if (productId) {
      this.store.update({ id: productId, ...value });
    } else {
      this.store.create(value);
    }

    this.router.navigate(['/products']);
  }

  onCancel() {
    this.router.navigate(['/products']);
  }
}
```

## Running the Example

```bash
# Create new Angular project
ng new crud-app --standalone --style=scss

# Install NgRx SignalStore
npm install @ngrx/signals

# Copy example files to project
# Start development server
ng serve
```

## API Endpoints Expected

```
GET    /api/products        - List all products
GET    /api/products/:id    - Get single product
POST   /api/products        - Create product
PATCH  /api/products/:id    - Update product
DELETE /api/products/:id    - Delete product
```
