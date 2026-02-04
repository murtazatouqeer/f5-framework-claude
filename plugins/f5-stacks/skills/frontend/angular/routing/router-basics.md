# Angular Router Basics

## Overview

Angular Router enables navigation between views in a single-page application. It maps URL paths to components and supports lazy loading, guards, and resolvers.

## Basic Route Configuration

```typescript
// app.routes.ts
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home.component')
      .then(m => m.HomeComponent),
    title: 'Home',
  },
  {
    path: 'about',
    loadComponent: () => import('./features/about/about.component')
      .then(m => m.AboutComponent),
    title: 'About Us',
  },
  {
    path: 'products',
    loadComponent: () => import('./features/products/product-list.component')
      .then(m => m.ProductListComponent),
    title: 'Products',
  },
  {
    path: 'products/:id',
    loadComponent: () => import('./features/products/product-detail.component')
      .then(m => m.ProductDetailComponent),
    title: 'Product Details',
  },
  {
    path: '**',
    loadComponent: () => import('./shared/not-found.component')
      .then(m => m.NotFoundComponent),
    title: 'Page Not Found',
  },
];
```

## App Configuration

```typescript
// app.config.ts
import { ApplicationConfig } from '@angular/core';
import { provideRouter, withViewTransitions, withComponentInputBinding } from '@angular/router';
import { routes } from './app.routes';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(
      routes,
      withViewTransitions(),        // Enable view transitions
      withComponentInputBinding(),  // Bind route params to inputs
    ),
  ],
};
```

## Router Outlet

```typescript
// app.component.ts
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: `
    <header>
      <app-navbar />
    </header>
    <main>
      <router-outlet />
    </main>
    <footer>
      <app-footer />
    </footer>
  `,
})
export class AppComponent {}
```

## Navigation

### RouterLink Directive

```html
<!-- Basic link -->
<a routerLink="/products">Products</a>

<!-- With parameters -->
<a [routerLink]="['/products', product.id]">{{ product.name }}</a>

<!-- With query params -->
<a [routerLink]="['/products']" [queryParams]="{ category: 'electronics' }">
  Electronics
</a>

<!-- Active link styling -->
<a routerLink="/home"
   routerLinkActive="active"
   [routerLinkActiveOptions]="{ exact: true }">
  Home
</a>

<!-- Preserve query params -->
<a [routerLink]="['/search']" queryParamsHandling="preserve">
  Search Again
</a>

<!-- Fragment -->
<a [routerLink]="['/page']" fragment="section1">Go to Section 1</a>
```

### Programmatic Navigation

```typescript
import { Component, inject } from '@angular/core';
import { Router, ActivatedRoute } from '@angular/router';

@Component({...})
export class ProductComponent {
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  // Navigate to absolute path
  goToProducts() {
    this.router.navigate(['/products']);
  }

  // Navigate with parameters
  goToProduct(id: string) {
    this.router.navigate(['/products', id]);
  }

  // Navigate with query params
  searchProducts(query: string) {
    this.router.navigate(['/products'], {
      queryParams: { q: query, page: 1 },
    });
  }

  // Navigate relative to current route
  goToEdit() {
    this.router.navigate(['edit'], { relativeTo: this.route });
  }

  // Navigate with state
  goToCheckout(items: CartItem[]) {
    this.router.navigate(['/checkout'], {
      state: { items },
    });
  }

  // Navigate and replace history
  redirect() {
    this.router.navigate(['/new-location'], {
      replaceUrl: true,
    });
  }

  // Navigate by URL
  goToUrl(url: string) {
    this.router.navigateByUrl(url);
  }
}
```

## Accessing Route Parameters

### Input Binding (Angular 16+)

```typescript
// With withComponentInputBinding() enabled
@Component({...})
export class ProductDetailComponent {
  // Route parameter as input
  id = input.required<string>();

  // Query parameter as input
  tab = input<string>('details');

  // Fragment as input
  fragment = input<string>();

  // Resolved data as input
  product = input<Product>();
}
```

### ActivatedRoute

```typescript
import { Component, inject, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';

@Component({...})
export class ProductDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);

  // Signal-based approach
  productId = signal<string>('');
  queryParams = signal<Record<string, string>>({});

  constructor() {
    // Subscribe to route params
    this.route.paramMap
      .pipe(takeUntilDestroyed())
      .subscribe(params => {
        this.productId.set(params.get('id') || '');
      });

    // Subscribe to query params
    this.route.queryParamMap
      .pipe(takeUntilDestroyed())
      .subscribe(params => {
        this.queryParams.set({
          category: params.get('category') || '',
          sort: params.get('sort') || 'name',
        });
      });
  }

  // Alternative: Snapshot (non-reactive)
  ngOnInit() {
    const id = this.route.snapshot.paramMap.get('id');
    const category = this.route.snapshot.queryParamMap.get('category');
  }
}
```

### Router State

```typescript
import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';

@Component({...})
export class CheckoutComponent {
  private router = inject(Router);

  // Access navigation state
  items: CartItem[] = [];

  constructor() {
    const navigation = this.router.getCurrentNavigation();
    this.items = navigation?.extras?.state?.['items'] || [];
  }
}
```

## Route Data

```typescript
// Route configuration
{
  path: 'admin',
  loadComponent: () => import('./admin.component'),
  data: {
    title: 'Admin Panel',
    roles: ['admin', 'superadmin'],
    breadcrumb: 'Administration',
  },
}

// Accessing in component
@Component({...})
export class AdminComponent {
  private route = inject(ActivatedRoute);

  title = this.route.snapshot.data['title'];
  roles = this.route.snapshot.data['roles'];

  // Or reactive
  constructor() {
    this.route.data.subscribe(data => {
      console.log(data['title']);
    });
  }
}
```

## Router Events

```typescript
import { Component, inject } from '@angular/core';
import { Router, NavigationStart, NavigationEnd, NavigationError } from '@angular/router';
import { filter } from 'rxjs';

@Component({...})
export class AppComponent {
  private router = inject(Router);

  isNavigating = signal(false);

  constructor() {
    this.router.events
      .pipe(filter(e => e instanceof NavigationStart))
      .subscribe(() => this.isNavigating.set(true));

    this.router.events
      .pipe(filter(e => e instanceof NavigationEnd || e instanceof NavigationError))
      .subscribe(() => this.isNavigating.set(false));
  }
}
```

## Named Outlets

```typescript
// Route configuration
{
  path: 'products',
  component: ProductsLayoutComponent,
  children: [
    { path: '', component: ProductListComponent },
    { path: ':id', component: ProductDetailComponent, outlet: 'detail' },
  ],
}

// Template
<router-outlet></router-outlet>
<router-outlet name="detail"></router-outlet>

// Navigation
this.router.navigate(['/products', { outlets: { detail: ['123'] } }]);
```

## Best Practices

1. **Use loadComponent**: For lazy loading
2. **Enable component input binding**: Simpler param access
3. **Use title**: For page titles
4. **Handle 404**: Always have a wildcard route
5. **Use relative navigation**: When appropriate
6. **Clean up subscriptions**: Use takeUntilDestroyed
