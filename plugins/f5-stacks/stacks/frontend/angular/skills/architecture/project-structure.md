# Angular Project Structure

## Overview

Modern Angular 17+ project structure using standalone components and feature-based organization.

## Recommended Structure

```
src/
├── app/
│   ├── core/                      # Singleton services, guards, interceptors
│   │   ├── guards/
│   │   │   ├── auth.guard.ts
│   │   │   └── role.guard.ts
│   │   ├── interceptors/
│   │   │   ├── auth.interceptor.ts
│   │   │   └── error.interceptor.ts
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   ├── storage.service.ts
│   │   │   └── api.service.ts
│   │   └── models/
│   │       └── user.model.ts
│   │
│   ├── shared/                    # Reusable components, pipes, directives
│   │   ├── components/
│   │   │   ├── button/
│   │   │   ├── modal/
│   │   │   └── table/
│   │   ├── directives/
│   │   │   └── click-outside.directive.ts
│   │   ├── pipes/
│   │   │   ├── date-format.pipe.ts
│   │   │   └── currency-format.pipe.ts
│   │   └── utils/
│   │       └── validators.ts
│   │
│   ├── features/                  # Feature modules
│   │   ├── auth/
│   │   │   ├── pages/
│   │   │   │   ├── login/
│   │   │   │   └── register/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   └── auth.routes.ts
│   │   │
│   │   ├── dashboard/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── dashboard.routes.ts
│   │   │
│   │   └── products/
│   │       ├── pages/
│   │       │   ├── product-list/
│   │       │   └── product-detail/
│   │       ├── components/
│   │       │   ├── product-card/
│   │       │   └── product-filters/
│   │       ├── services/
│   │       │   └── product.service.ts
│   │       ├── models/
│   │       │   └── product.model.ts
│   │       └── products.routes.ts
│   │
│   ├── layouts/                   # Layout components
│   │   ├── main-layout/
│   │   ├── auth-layout/
│   │   └── admin-layout/
│   │
│   ├── app.component.ts
│   ├── app.config.ts              # Application configuration
│   └── app.routes.ts              # Root routes
│
├── assets/
│   ├── images/
│   ├── icons/
│   └── i18n/
│
├── environments/
│   ├── environment.ts
│   └── environment.prod.ts
│
└── styles/
    ├── _variables.scss
    ├── _mixins.scss
    └── styles.scss
```

## Core Module Organization

The `core/` folder contains singleton services and utilities.

```typescript
// core/services/auth.service.ts
@Injectable({ providedIn: 'root' })
export class AuthService {
  // Singleton - only one instance across the app
}

// core/guards/auth.guard.ts
export const authGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  return authService.isAuthenticated();
};

// core/interceptors/auth.interceptor.ts
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.token();

  if (token) {
    req = req.clone({
      headers: req.headers.set('Authorization', `Bearer ${token}`),
    });
  }

  return next(req);
};
```

## Feature Module Organization

Each feature is self-contained with its own routes, components, and services.

```typescript
// features/products/products.routes.ts
import { Routes } from '@angular/router';

export const PRODUCTS_ROUTES: Routes = [
  {
    path: '',
    loadComponent: () => import('./pages/product-list/product-list.component')
      .then(m => m.ProductListComponent),
  },
  {
    path: ':id',
    loadComponent: () => import('./pages/product-detail/product-detail.component')
      .then(m => m.ProductDetailComponent),
  },
];

// features/products/services/product.service.ts
@Injectable({ providedIn: 'root' })
export class ProductService {
  // Feature-specific state and logic
}

// features/products/models/product.model.ts
export interface Product {
  id: string;
  name: string;
  price: number;
  description: string;
}
```

## Shared Module Organization

Reusable components, pipes, and directives.

```typescript
// shared/components/button/button.component.ts
@Component({
  selector: 'app-button',
  standalone: true,
  template: `
    <button [class]="variant()" [disabled]="disabled()">
      <ng-content />
    </button>
  `,
})
export class ButtonComponent {
  variant = input<'primary' | 'secondary'>('primary');
  disabled = input(false);
}

// shared/pipes/date-format.pipe.ts
@Pipe({
  name: 'dateFormat',
  standalone: true,
})
export class DateFormatPipe implements PipeTransform {
  transform(value: Date | string, format = 'medium'): string {
    return formatDate(value, format, 'en-US');
  }
}
```

## Application Configuration

```typescript
// app.config.ts
import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter, withViewTransitions } from '@angular/router';
import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';

import { routes } from './app.routes';
import { authInterceptor } from './core/interceptors/auth.interceptor';
import { errorInterceptor } from './core/interceptors/error.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes, withViewTransitions()),
    provideHttpClient(withInterceptors([authInterceptor, errorInterceptor])),
    provideAnimationsAsync(),
  ],
};
```

## Root Routes

```typescript
// app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { MainLayoutComponent } from './layouts/main-layout/main-layout.component';

export const routes: Routes = [
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      {
        path: '',
        loadComponent: () => import('./features/home/home.component')
          .then(m => m.HomeComponent),
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
    ],
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
  },
];
```

## Best Practices

### 1. Feature Independence
- Each feature should be self-contained
- Features communicate through services in `core/`
- Minimize cross-feature dependencies

### 2. Lazy Loading
- All features should be lazy-loaded
- Use `loadComponent` for standalone components
- Use `loadChildren` for feature routes

### 3. Barrel Exports (Optional)
```typescript
// features/products/index.ts
export * from './products.routes';
export * from './services/product.service';
export * from './models/product.model';
```

### 4. Environment Configuration
```typescript
// environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:3000/api',
  features: {
    darkMode: true,
    analytics: false,
  },
};
```

### 5. Path Aliases (tsconfig.json)
```json
{
  "compilerOptions": {
    "paths": {
      "@core/*": ["src/app/core/*"],
      "@shared/*": ["src/app/shared/*"],
      "@features/*": ["src/app/features/*"],
      "@env": ["src/environments/environment"]
    }
  }
}
```
