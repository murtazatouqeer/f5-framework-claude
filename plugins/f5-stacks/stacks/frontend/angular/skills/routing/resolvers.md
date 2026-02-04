# Angular Route Resolvers

## Overview

Resolvers fetch data before a route is activated, ensuring data is available when the component loads. They prevent empty states and loading spinners.

## Basic Resolver

```typescript
// features/products/resolvers/product.resolver.ts
import { inject } from '@angular/core';
import { ResolveFn, Router } from '@angular/router';
import { catchError, of } from 'rxjs';
import { Product } from '../models/product.model';
import { ProductService } from '../services/product.service';

export const productResolver: ResolveFn<Product | null> = (route) => {
  const productService = inject(ProductService);
  const router = inject(Router);
  const id = route.paramMap.get('id');

  if (!id) {
    router.navigate(['/products']);
    return of(null);
  }

  return productService.getById(id).pipe(
    catchError(() => {
      router.navigate(['/products']);
      return of(null);
    })
  );
};

// Route configuration
{
  path: 'products/:id',
  loadComponent: () => import('./product-detail.component'),
  resolve: {
    product: productResolver,
  },
}
```

## Accessing Resolved Data

### Input Binding (Recommended)

```typescript
// With withComponentInputBinding() enabled in provideRouter
@Component({
  selector: 'app-product-detail',
  template: `
    @if (product()) {
      <h1>{{ product()!.name }}</h1>
      <p>{{ product()!.description }}</p>
      <p>{{ product()!.price | currency }}</p>
    }
  `,
})
export class ProductDetailComponent {
  // Resolved data bound automatically to input
  product = input<Product | null>(null);
}
```

### ActivatedRoute

```typescript
@Component({...})
export class ProductDetailComponent {
  private route = inject(ActivatedRoute);

  product = signal<Product | null>(null);

  constructor() {
    // Reactive approach
    this.route.data.subscribe(data => {
      this.product.set(data['product']);
    });
  }

  // Or snapshot
  ngOnInit() {
    this.product.set(this.route.snapshot.data['product']);
  }
}
```

## Multiple Resolvers

```typescript
// Route with multiple resolvers
{
  path: 'products/:id',
  loadComponent: () => import('./product-detail.component'),
  resolve: {
    product: productResolver,
    reviews: productReviewsResolver,
    related: relatedProductsResolver,
  },
}

// Product reviews resolver
export const productReviewsResolver: ResolveFn<Review[]> = (route) => {
  const reviewService = inject(ReviewService);
  const productId = route.paramMap.get('id');

  return reviewService.getByProductId(productId!).pipe(
    catchError(() => of([]))
  );
};

// Related products resolver
export const relatedProductsResolver: ResolveFn<Product[]> = (route) => {
  const productService = inject(ProductService);
  const productId = route.paramMap.get('id');

  return productService.getRelated(productId!).pipe(
    catchError(() => of([]))
  );
};

// Component
@Component({...})
export class ProductDetailComponent {
  product = input<Product | null>(null);
  reviews = input<Review[]>([]);
  related = input<Product[]>([]);
}
```

## Dependent Resolvers

```typescript
// Parent route resolves user
{
  path: 'users/:userId',
  resolve: {
    user: userResolver,
  },
  children: [
    {
      path: 'orders',
      resolve: {
        orders: userOrdersResolver, // Depends on parent's user
      },
      loadComponent: () => import('./user-orders.component'),
    },
  ],
}

// Child resolver accessing parent data
export const userOrdersResolver: ResolveFn<Order[]> = (route) => {
  const orderService = inject(OrderService);

  // Access parent resolved data
  const user = route.parent?.data['user'] as User;

  if (!user) {
    return of([]);
  }

  return orderService.getByUserId(user.id);
};
```

## Resolver with Loading State

```typescript
// Store-based resolver with loading indication
export const productsResolver: ResolveFn<Product[]> = () => {
  const store = inject(ProductStore);

  // If already loaded, return current data
  if (store.products().length > 0 && !store.isStale()) {
    return of(store.products());
  }

  // Otherwise, load and wait
  store.setLoading(true);

  return inject(ProductService).getAll().pipe(
    tap(products => {
      store.setProducts(products);
      store.setLoading(false);
    }),
    catchError(error => {
      store.setError(error.message);
      store.setLoading(false);
      return of([]);
    })
  );
};
```

## Conditional Resolver

```typescript
// Resolve only if needed
export const conditionalProductResolver: ResolveFn<Product | null> = (route) => {
  const productService = inject(ProductService);
  const productStore = inject(ProductStore);

  const id = route.paramMap.get('id')!;

  // Check if already in store
  const cached = productStore.getById(id);
  if (cached) {
    return of(cached);
  }

  // Otherwise fetch
  return productService.getById(id);
};
```

## Error Handling

```typescript
// Resolver with comprehensive error handling
export const productResolver: ResolveFn<Product | null> = (route) => {
  const productService = inject(ProductService);
  const router = inject(Router);
  const errorHandler = inject(ErrorHandlerService);

  const id = route.paramMap.get('id');

  if (!id) {
    return of(null);
  }

  return productService.getById(id).pipe(
    catchError(error => {
      // Log error
      errorHandler.handleError(error);

      // Handle different error types
      if (error.status === 404) {
        router.navigate(['/not-found']);
      } else if (error.status === 403) {
        router.navigate(['/forbidden']);
      } else {
        router.navigate(['/error'], {
          queryParams: { message: 'Failed to load product' },
        });
      }

      return of(null);
    })
  );
};
```

## Typed Resolvers

```typescript
// Define resolver data type
interface ProductRouteData {
  product: Product;
  reviews: Review[];
  related: Product[];
}

// Type-safe route
{
  path: 'products/:id',
  loadComponent: () => import('./product-detail.component'),
  resolve: {
    product: productResolver,
    reviews: productReviewsResolver,
    related: relatedProductsResolver,
  } satisfies { [K in keyof ProductRouteData]: ResolveFn<ProductRouteData[K]> },
}

// Type-safe component
@Component({...})
export class ProductDetailComponent {
  private route = inject(ActivatedRoute);

  // Type-safe access
  get resolvedData(): ProductRouteData {
    return this.route.snapshot.data as ProductRouteData;
  }
}
```

## Resolver Factory

```typescript
// Factory for creating resolvers
export function createEntityResolver<T>(
  serviceToken: Type<{ getById(id: string): Observable<T> }>,
  idParam = 'id',
  redirectOnError = '/not-found'
): ResolveFn<T | null> {
  return (route) => {
    const service = inject(serviceToken);
    const router = inject(Router);
    const id = route.paramMap.get(idParam);

    if (!id) {
      return of(null);
    }

    return service.getById(id).pipe(
      catchError(() => {
        router.navigate([redirectOnError]);
        return of(null);
      })
    );
  };
}

// Usage
export const productResolver = createEntityResolver(ProductService, 'id', '/products');
export const userResolver = createEntityResolver(UserService, 'userId', '/users');
```

## Parallel vs Sequential Resolution

```typescript
// Parallel (default) - all resolvers run simultaneously
{
  path: 'dashboard',
  resolve: {
    stats: statsResolver,      // Runs in parallel
    notifications: notificationsResolver,  // Runs in parallel
    activity: activityResolver,  // Runs in parallel
  },
}

// Sequential - using parent-child or combining in single resolver
export const dashboardResolver: ResolveFn<DashboardData> = () => {
  const dashboardService = inject(DashboardService);

  return forkJoin({
    stats: dashboardService.getStats(),
    notifications: dashboardService.getNotifications(),
    activity: dashboardService.getActivity(),
  });
};
```

## Testing Resolvers

```typescript
// product.resolver.spec.ts
import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, convertToParamMap } from '@angular/router';
import { of, throwError } from 'rxjs';
import { productResolver } from './product.resolver';
import { ProductService } from '../services/product.service';

describe('productResolver', () => {
  let productService: jasmine.SpyObj<ProductService>;
  let router: jasmine.SpyObj<Router>;

  const mockProduct = { id: '1', name: 'Test Product' };

  beforeEach(() => {
    productService = jasmine.createSpyObj('ProductService', ['getById']);
    router = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: ProductService, useValue: productService },
        { provide: Router, useValue: router },
      ],
    });
  });

  it('should resolve product', (done) => {
    productService.getById.and.returnValue(of(mockProduct));

    const route = {
      paramMap: convertToParamMap({ id: '1' }),
    } as ActivatedRouteSnapshot;

    TestBed.runInInjectionContext(() => {
      const result$ = productResolver(route, {} as any);
      result$.subscribe(product => {
        expect(product).toEqual(mockProduct);
        done();
      });
    });
  });

  it('should redirect on error', (done) => {
    productService.getById.and.returnValue(throwError(() => new Error()));

    const route = {
      paramMap: convertToParamMap({ id: '1' }),
    } as ActivatedRouteSnapshot;

    TestBed.runInInjectionContext(() => {
      const result$ = productResolver(route, {} as any);
      result$.subscribe(product => {
        expect(product).toBeNull();
        expect(router.navigate).toHaveBeenCalledWith(['/products']);
        done();
      });
    });
  });
});
```

## Best Practices

1. **Use resolvers for critical data**: Data needed immediately
2. **Handle errors gracefully**: Redirect or show fallback
3. **Consider loading states**: Show skeletons while resolving
4. **Use input binding**: For clean data access
5. **Keep resolvers fast**: Avoid slow operations
6. **Cache when appropriate**: Prevent redundant fetches
7. **Type your data**: For type safety
