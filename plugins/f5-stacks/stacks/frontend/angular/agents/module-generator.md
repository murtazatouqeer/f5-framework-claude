# Angular Module/Routes Generator Agent

## Overview

Specialized agent for generating Angular routing configurations and feature organization. In Angular 17+, this focuses on route-based lazy loading rather than NgModules.

## Capabilities

- Generate feature route configurations
- Create lazy-loaded route structures
- Implement route guards and resolvers
- Configure route data and metadata
- Generate nested routes and outlets
- Support for standalone component routing

## Input Requirements

```yaml
required:
  - name: Feature name
  - routes: Array of route definitions

optional:
  - guards: Route guards to apply
  - resolvers: Data resolvers
  - layout: Layout component for nested routes
  - parent_route: Parent route path
```

## Generation Rules

### File Structure
```
features/{feature}/
├── {feature}.routes.ts          # Route configuration
├── pages/                       # Page components (routed)
│   ├── {page}/
│   │   └── {page}.component.ts
├── components/                  # Feature components
├── services/                    # Feature services
├── models/                      # Feature models
└── guards/                      # Feature-specific guards
```

### Route Configuration Patterns

#### Basic Feature Routes
```typescript
// features/products/products.routes.ts
import { Routes } from '@angular/router';

export const PRODUCTS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/product-list/product-list.component')
      .then(m => m.ProductListComponent),
    title: 'Products',
  },
  {
    path: 'new',
    loadComponent: () => import('./pages/product-form/product-form.component')
      .then(m => m.ProductFormComponent),
    title: 'New Product',
  },
  {
    path: ':id',
    loadComponent: () => import('./pages/product-detail/product-detail.component')
      .then(m => m.ProductDetailComponent),
  },
  {
    path: ':id/edit',
    loadComponent: () => import('./pages/product-form/product-form.component')
      .then(m => m.ProductFormComponent),
    title: 'Edit Product',
  },
];
```

#### Routes with Guards
```typescript
import { authGuard } from '../../core/guards/auth.guard';
import { roleGuard } from '../../core/guards/role.guard';

export const ADMIN_ROUTES: Routes = [
  {
    path: '',
    canActivate: [authGuard],
    canActivateChild: [roleGuard],
    data: { roles: ['admin'] },
    children: [
      {
        path: '',
        loadComponent: () => import('./pages/dashboard/dashboard.component')
          .then(m => m.DashboardComponent),
      },
      {
        path: 'users',
        loadChildren: () => import('./users/users.routes')
          .then(m => m.USERS_ROUTES),
      },
    ],
  },
];
```

#### Routes with Layout
```typescript
export const DASHBOARD_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./layouts/dashboard-layout/dashboard-layout.component')
      .then(m => m.DashboardLayoutComponent),
    children: [
      {
        path: '',
        loadComponent: () => import('./pages/overview/overview.component')
          .then(m => m.OverviewComponent),
      },
      {
        path: 'analytics',
        loadComponent: () => import('./pages/analytics/analytics.component')
          .then(m => m.AnalyticsComponent),
      },
    ],
  },
];
```

#### Routes with Resolvers
```typescript
import { productResolver } from './resolvers/product.resolver';

export const PRODUCTS_ROUTES: Routes = [
  {
    path: ':id',
    loadComponent: () => import('./pages/product-detail/product-detail.component')
      .then(m => m.ProductDetailComponent),
    resolve: {
      product: productResolver,
    },
  },
];
```

### App Routes Configuration
```typescript
// app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home.component')
      .then(m => m.HomeComponent),
    title: 'Home',
  },
  {
    path: 'products',
    loadChildren: () => import('./features/products/products.routes')
      .then(m => m.PRODUCTS_ROUTES),
  },
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadChildren: () => import('./features/dashboard/dashboard.routes')
      .then(m => m.DASHBOARD_ROUTES),
  },
  {
    path: 'auth',
    loadChildren: () => import('./features/auth/auth.routes')
      .then(m => m.AUTH_ROUTES),
  },
  {
    path: '**',
    loadComponent: () => import('./shared/components/not-found/not-found.component')
      .then(m => m.NotFoundComponent),
    title: 'Page Not Found',
  },
];
```

## Integration

- Works with: component-generator, guard-generator
- Uses templates: N/A (route configs are generated directly)
- Follows skills: router-basics, lazy-loading, guards

## Examples

### Generate E-commerce Routes
```
Input:
  name: products
  routes:
    - path: '', component: ProductList
    - path: 'category/:slug', component: CategoryProducts
    - path: ':id', component: ProductDetail
    - path: ':id/reviews', component: ProductReviews
  guards: [authGuard (for checkout)]

Output: Complete products.routes.ts with lazy loading
```

### Generate Admin Dashboard Routes
```
Input:
  name: admin
  layout: AdminLayout
  guards: [authGuard, adminGuard]
  routes:
    - path: '', component: Dashboard
    - path: 'users', children: USERS_ROUTES
    - path: 'settings', component: Settings

Output: Nested routes with layout and guards
```
