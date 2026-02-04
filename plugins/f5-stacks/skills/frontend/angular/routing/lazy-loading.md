# Angular Lazy Loading

## Overview

Lazy loading delays the loading of feature modules until they're needed, reducing initial bundle size and improving application startup time.

## Basic Lazy Loading

### loadComponent (Standalone)

```typescript
// app.routes.ts
import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home.component')
      .then(m => m.HomeComponent),
  },
  {
    path: 'products',
    loadComponent: () => import('./features/products/product-list.component')
      .then(m => m.ProductListComponent),
  },
  {
    path: 'products/:id',
    loadComponent: () => import('./features/products/product-detail.component')
      .then(m => m.ProductDetailComponent),
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component')
      .then(m => m.DashboardComponent),
  },
];
```

### loadChildren (Feature Routes)

```typescript
// app.routes.ts
export const routes: Routes = [
  {
    path: 'products',
    loadChildren: () => import('./features/products/products.routes')
      .then(m => m.PRODUCTS_ROUTES),
  },
  {
    path: 'admin',
    loadChildren: () => import('./features/admin/admin.routes')
      .then(m => m.ADMIN_ROUTES),
  },
  {
    path: 'settings',
    loadChildren: () => import('./features/settings/settings.routes')
      .then(m => m.SETTINGS_ROUTES),
  },
];

// features/products/products.routes.ts
export const PRODUCTS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/product-list/product-list.component')
      .then(m => m.ProductListComponent),
  },
  {
    path: 'categories',
    loadComponent: () => import('./pages/categories/categories.component')
      .then(m => m.CategoriesComponent),
  },
  {
    path: ':id',
    loadComponent: () => import('./pages/product-detail/product-detail.component')
      .then(m => m.ProductDetailComponent),
  },
  {
    path: ':id/reviews',
    loadComponent: () => import('./pages/product-reviews/product-reviews.component')
      .then(m => m.ProductReviewsComponent),
  },
];
```

## Nested Lazy Loading

```typescript
// features/admin/admin.routes.ts
export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./layout/admin-layout.component')
      .then(m => m.AdminLayoutComponent),
    children: [
      {
        path: '',
        pathMatch: 'full',
        redirectTo: 'dashboard',
      },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard.component')
          .then(m => m.DashboardComponent),
      },
      {
        path: 'users',
        loadChildren: () => import('./features/users/users.routes')
          .then(m => m.USERS_ROUTES),
      },
      {
        path: 'products',
        loadChildren: () => import('./features/products/admin-products.routes')
          .then(m => m.ADMIN_PRODUCTS_ROUTES),
      },
      {
        path: 'settings',
        loadComponent: () => import('./pages/settings/settings.component')
          .then(m => m.SettingsComponent),
      },
    ],
  },
];

// features/admin/features/users/users.routes.ts
export const USERS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./user-list.component')
      .then(m => m.UserListComponent),
  },
  {
    path: ':id',
    loadComponent: () => import('./user-detail.component')
      .then(m => m.UserDetailComponent),
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./user-edit.component')
      .then(m => m.UserEditComponent),
  },
];
```

## Preloading Strategies

### Built-in Strategies

```typescript
// app.config.ts
import { provideRouter, PreloadAllModules, NoPreloading } from '@angular/router';

export const appConfig: ApplicationConfig = {
  providers: [
    provideRouter(
      routes,
      // Load all lazy modules in background
      withPreloading(PreloadAllModules),

      // Or: No preloading (default)
      // withPreloading(NoPreloading),
    ),
  ],
};
```

### Custom Preloading Strategy

```typescript
// core/preloading/selective-preload.strategy.ts
import { Injectable } from '@angular/core';
import { PreloadingStrategy, Route } from '@angular/router';
import { Observable, of } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class SelectivePreloadingStrategy implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<any>): Observable<any> {
    // Only preload routes marked with preload: true
    if (route.data?.['preload']) {
      console.log('Preloading:', route.path);
      return load();
    }
    return of(null);
  }
}

// Usage in routes
export const routes: Routes = [
  {
    path: 'products',
    loadChildren: () => import('./products/products.routes'),
    data: { preload: true }, // Will preload
  },
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.routes'),
    data: { preload: false }, // Won't preload
  },
];

// app.config.ts
provideRouter(routes, withPreloading(SelectivePreloadingStrategy))
```

### Network-Aware Preloading

```typescript
@Injectable({ providedIn: 'root' })
export class NetworkAwarePreloadingStrategy implements PreloadingStrategy {
  preload(route: Route, load: () => Observable<any>): Observable<any> {
    // Check network conditions
    const connection = (navigator as any).connection;

    // Don't preload on slow connections
    if (connection?.saveData || connection?.effectiveType === '2g') {
      return of(null);
    }

    // Preload if marked
    if (route.data?.['preload']) {
      return load();
    }

    return of(null);
  }
}
```

### On-Demand Preloading

```typescript
// services/preload.service.ts
import { Injectable, inject } from '@angular/core';
import { Router, RouterPreloader } from '@angular/router';

@Injectable({ providedIn: 'root' })
export class PreloadService {
  private router = inject(Router);

  // Preload specific route on hover or viewport entry
  preloadRoute(path: string) {
    const route = this.findRoute(this.router.config, path);
    if (route?.loadChildren || route?.loadComponent) {
      // Trigger preload
      if (route.loadChildren) {
        route.loadChildren();
      }
      if (route.loadComponent) {
        route.loadComponent();
      }
    }
  }

  private findRoute(routes: Routes, path: string): Route | null {
    for (const route of routes) {
      if (route.path === path) return route;
      if (route.children) {
        const child = this.findRoute(route.children, path);
        if (child) return child;
      }
    }
    return null;
  }
}

// Usage with directive
@Directive({
  selector: '[appPreloadOnHover]',
  standalone: true,
})
export class PreloadOnHoverDirective {
  private preloadService = inject(PreloadService);

  appPreloadOnHover = input.required<string>();

  @HostListener('mouseenter')
  onMouseEnter() {
    this.preloadService.preloadRoute(this.appPreloadOnHover());
  }
}

// Template
<a routerLink="/admin" appPreloadOnHover="/admin">Admin Panel</a>
```

## Loading Indicators

```typescript
@Component({
  selector: 'app-root',
  template: `
    @if (isNavigating()) {
      <app-loading-bar />
    }
    <router-outlet />
  `,
})
export class AppComponent {
  private router = inject(Router);

  isNavigating = signal(false);

  constructor() {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationStart) {
        this.isNavigating.set(true);
      }
      if (event instanceof NavigationEnd ||
          event instanceof NavigationCancel ||
          event instanceof NavigationError) {
        this.isNavigating.set(false);
      }
    });
  }
}
```

## Code Splitting Best Practices

```typescript
// Optimal feature organization
features/
├── auth/                    # Auth feature (lazy)
│   ├── auth.routes.ts
│   └── pages/
├── dashboard/               # Dashboard feature (lazy)
│   ├── dashboard.routes.ts
│   └── pages/
├── products/                # Products feature (lazy)
│   ├── products.routes.ts
│   ├── pages/
│   └── components/         # Feature-specific components
└── shared/                  # Eager loaded
    └── components/

// Route structure
export const routes: Routes = [
  // Eager - essential for initial render
  {
    path: '',
    component: HomeComponent,
  },

  // Lazy - loaded on demand
  {
    path: 'products',
    loadChildren: () => import('./features/products/products.routes'),
    data: { preload: true },
  },

  // Lazy - rarely accessed
  {
    path: 'admin',
    loadChildren: () => import('./features/admin/admin.routes'),
    data: { preload: false },
  },
];
```

## Chunk Naming

```typescript
// Named chunks for better debugging
{
  path: 'products',
  loadChildren: () => import(
    /* webpackChunkName: "products" */
    './features/products/products.routes'
  ).then(m => m.PRODUCTS_ROUTES),
}
```

## Best Practices

1. **Lazy load feature modules**: Not individual components
2. **Use selective preloading**: Don't preload everything
3. **Consider network conditions**: Adapt preloading strategy
4. **Show loading indicators**: Improve perceived performance
5. **Group related routes**: In feature route files
6. **Monitor bundle sizes**: Use webpack-bundle-analyzer
7. **Use route-level code splitting**: For optimal chunks
