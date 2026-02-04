# NgRx Basics

## Overview

NgRx is a Redux-inspired state management library for Angular. It provides a predictable state container with actions, reducers, effects, and selectors.

## Installation

```bash
ng add @ngrx/store
ng add @ngrx/effects
ng add @ngrx/store-devtools
ng add @ngrx/entity
```

## Core Concepts

### State

```typescript
// models/product.model.ts
export interface Product {
  id: string;
  name: string;
  price: number;
  category: string;
  inStock: boolean;
}

// store/products/products.state.ts
import { EntityState, EntityAdapter, createEntityAdapter } from '@ngrx/entity';

export interface ProductsState extends EntityState<Product> {
  selectedProductId: string | null;
  loading: boolean;
  error: string | null;
}

export const productsAdapter: EntityAdapter<Product> = createEntityAdapter<Product>({
  selectId: (product: Product) => product.id,
  sortComparer: (a, b) => a.name.localeCompare(b.name),
});

export const initialProductsState: ProductsState = productsAdapter.getInitialState({
  selectedProductId: null,
  loading: false,
  error: null,
});
```

### Actions

```typescript
// store/products/products.actions.ts
import { createActionGroup, emptyProps, props } from '@ngrx/store';
import { Product } from '../../models/product.model';

export const ProductsActions = createActionGroup({
  source: 'Products',
  events: {
    // Load products
    'Load Products': emptyProps(),
    'Load Products Success': props<{ products: Product[] }>(),
    'Load Products Failure': props<{ error: string }>(),

    // CRUD operations
    'Add Product': props<{ product: Product }>(),
    'Update Product': props<{ id: string; changes: Partial<Product> }>(),
    'Remove Product': props<{ id: string }>(),

    // Selection
    'Select Product': props<{ id: string | null }>(),

    // Bulk operations
    'Clear Products': emptyProps(),
  },
});

// Alternative: Individual action creators
export const loadProducts = createAction('[Products] Load Products');

export const loadProductsSuccess = createAction(
  '[Products] Load Products Success',
  props<{ products: Product[] }>()
);

export const loadProductsFailure = createAction(
  '[Products] Load Products Failure',
  props<{ error: string }>()
);
```

### Reducers

```typescript
// store/products/products.reducer.ts
import { createReducer, on } from '@ngrx/store';
import { ProductsActions } from './products.actions';
import { productsAdapter, initialProductsState, ProductsState } from './products.state';

export const productsReducer = createReducer(
  initialProductsState,

  // Load products
  on(ProductsActions.loadProducts, (state): ProductsState => ({
    ...state,
    loading: true,
    error: null,
  })),

  on(ProductsActions.loadProductsSuccess, (state, { products }): ProductsState =>
    productsAdapter.setAll(products, {
      ...state,
      loading: false,
    })
  ),

  on(ProductsActions.loadProductsFailure, (state, { error }): ProductsState => ({
    ...state,
    loading: false,
    error,
  })),

  // CRUD
  on(ProductsActions.addProduct, (state, { product }): ProductsState =>
    productsAdapter.addOne(product, state)
  ),

  on(ProductsActions.updateProduct, (state, { id, changes }): ProductsState =>
    productsAdapter.updateOne({ id, changes }, state)
  ),

  on(ProductsActions.removeProduct, (state, { id }): ProductsState =>
    productsAdapter.removeOne(id, state)
  ),

  // Selection
  on(ProductsActions.selectProduct, (state, { id }): ProductsState => ({
    ...state,
    selectedProductId: id,
  })),

  // Clear
  on(ProductsActions.clearProducts, (state): ProductsState =>
    productsAdapter.removeAll({
      ...state,
      selectedProductId: null,
    })
  ),
);
```

### Selectors

```typescript
// store/products/products.selectors.ts
import { createFeatureSelector, createSelector } from '@ngrx/store';
import { productsAdapter, ProductsState } from './products.state';

// Feature selector
export const selectProductsState = createFeatureSelector<ProductsState>('products');

// Entity selectors
const { selectIds, selectEntities, selectAll, selectTotal } = productsAdapter.getSelectors();

export const selectAllProducts = createSelector(
  selectProductsState,
  selectAll
);

export const selectProductEntities = createSelector(
  selectProductsState,
  selectEntities
);

export const selectProductIds = createSelector(
  selectProductsState,
  selectIds
);

export const selectProductsTotal = createSelector(
  selectProductsState,
  selectTotal
);

// Custom selectors
export const selectProductsLoading = createSelector(
  selectProductsState,
  (state) => state.loading
);

export const selectProductsError = createSelector(
  selectProductsState,
  (state) => state.error
);

export const selectSelectedProductId = createSelector(
  selectProductsState,
  (state) => state.selectedProductId
);

export const selectSelectedProduct = createSelector(
  selectProductEntities,
  selectSelectedProductId,
  (entities, selectedId) => selectedId ? entities[selectedId] : null
);

// Derived selectors
export const selectProductsByCategory = (category: string) => createSelector(
  selectAllProducts,
  (products) => products.filter(p => p.category === category)
);

export const selectInStockProducts = createSelector(
  selectAllProducts,
  (products) => products.filter(p => p.inStock)
);

export const selectProductsSummary = createSelector(
  selectAllProducts,
  (products) => ({
    total: products.length,
    inStock: products.filter(p => p.inStock).length,
    outOfStock: products.filter(p => !p.inStock).length,
    totalValue: products.reduce((sum, p) => sum + p.price, 0),
  })
);
```

### Effects

```typescript
// store/products/products.effects.ts
import { Injectable, inject } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { catchError, map, exhaustMap, of } from 'rxjs';
import { ProductsActions } from './products.actions';
import { ProductService } from '../../services/product.service';

@Injectable()
export class ProductsEffects {
  private actions$ = inject(Actions);
  private productService = inject(ProductService);

  loadProducts$ = createEffect(() =>
    this.actions$.pipe(
      ofType(ProductsActions.loadProducts),
      exhaustMap(() =>
        this.productService.getAll().pipe(
          map(products => ProductsActions.loadProductsSuccess({ products })),
          catchError(error =>
            of(ProductsActions.loadProductsFailure({ error: error.message }))
          )
        )
      )
    )
  );

  // Effect without dispatch (for side effects only)
  logActions$ = createEffect(
    () =>
      this.actions$.pipe(
        ofType(ProductsActions.loadProductsSuccess),
        map(action => console.log('Products loaded:', action.products.length))
      ),
    { dispatch: false }
  );
}
```

## Store Setup

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideStore } from '@ngrx/store';
import { provideEffects } from '@ngrx/effects';
import { provideStoreDevtools } from '@ngrx/store-devtools';
import { productsReducer } from './store/products/products.reducer';
import { ProductsEffects } from './store/products/products.effects';

export const appConfig: ApplicationConfig = {
  providers: [
    provideStore({
      products: productsReducer,
    }),
    provideEffects(ProductsEffects),
    provideStoreDevtools({
      maxAge: 25,
      logOnly: false,
    }),
  ],
};
```

## Component Integration

```typescript
// components/product-list/product-list.component.ts
import { Component, inject } from '@angular/core';
import { Store } from '@ngrx/store';
import { CommonModule, AsyncPipe } from '@angular/common';
import { ProductsActions } from '../../store/products/products.actions';
import {
  selectAllProducts,
  selectProductsLoading,
  selectProductsError,
} from '../../store/products/products.selectors';

@Component({
  selector: 'app-product-list',
  standalone: true,
  imports: [CommonModule, AsyncPipe],
  template: `
    @if (loading$ | async) {
      <div class="loading">Loading products...</div>
    }

    @if (error$ | async; as error) {
      <div class="error">{{ error }}</div>
    }

    <div class="product-grid">
      @for (product of products$ | async; track product.id) {
        <app-product-card
          [product]="product"
          (select)="onSelect(product.id)"
        />
      }
    </div>
  `,
})
export class ProductListComponent {
  private store = inject(Store);

  products$ = this.store.select(selectAllProducts);
  loading$ = this.store.select(selectProductsLoading);
  error$ = this.store.select(selectProductsError);

  ngOnInit() {
    this.store.dispatch(ProductsActions.loadProducts());
  }

  onSelect(id: string) {
    this.store.dispatch(ProductsActions.selectProduct({ id }));
  }
}
```

## With Signals (selectSignal)

```typescript
import { Component, inject } from '@angular/core';
import { Store } from '@ngrx/store';

@Component({...})
export class ProductListComponent {
  private store = inject(Store);

  // Use selectSignal for signal-based selection (NgRx 17+)
  products = this.store.selectSignal(selectAllProducts);
  loading = this.store.selectSignal(selectProductsLoading);
  error = this.store.selectSignal(selectProductsError);

  // In template: {{ products() }}, {{ loading() }}
}
```

## Best Practices

1. **Use createActionGroup**: For related actions
2. **Use Entity Adapter**: For collections
3. **Keep reducers pure**: No side effects
4. **Use selectors**: Never access state directly
5. **Handle errors in effects**: Always catch errors
6. **Use exhaustMap for loads**: Prevents duplicate requests
7. **Enable DevTools**: For debugging
