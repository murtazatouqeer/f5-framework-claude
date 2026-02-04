# Angular Route Guards

## Overview

Route guards control navigation by checking conditions before activating, deactivating, or loading routes. Angular 14+ uses functional guards.

## Guard Types

| Guard | Purpose |
|-------|---------|
| `canActivate` | Check before activating route |
| `canActivateChild` | Check before activating child routes |
| `canDeactivate` | Check before leaving route |
| `canMatch` | Check before matching route |
| `resolve` | Fetch data before route activation |

## Authentication Guard

```typescript
// core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn, CanActivateChildFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // Redirect to login with return URL
  return router.createUrlTree(['/auth/login'], {
    queryParams: { returnUrl: state.url },
  });
};

// For protecting child routes
export const authGuardChild: CanActivateChildFn = (route, state) => {
  return authGuard(route, state);
};

// Usage
export const routes: Routes = [
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./dashboard.component'),
  },
  {
    path: 'admin',
    canActivate: [authGuard],
    canActivateChild: [authGuardChild],
    children: [
      // All children protected
    ],
  },
];
```

## Role-Based Guard

```typescript
// core/guards/role.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredRoles = route.data['roles'] as string[];

  if (!requiredRoles || requiredRoles.length === 0) {
    return true;
  }

  const userRoles = authService.currentUser()?.roles || [];
  const hasRequiredRole = requiredRoles.some(role => userRoles.includes(role));

  if (hasRequiredRole) {
    return true;
  }

  // Redirect to unauthorized page
  return router.createUrlTree(['/unauthorized']);
};

// Usage
{
  path: 'admin',
  canActivate: [authGuard, roleGuard],
  data: { roles: ['admin', 'superadmin'] },
  loadComponent: () => import('./admin.component'),
}
```

## Permission Guard

```typescript
// core/guards/permission.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { PermissionService } from '../services/permission.service';

export const permissionGuard: CanActivateFn = (route) => {
  const permissionService = inject(PermissionService);
  const router = inject(Router);

  const requiredPermissions = route.data['permissions'] as string[];

  if (!requiredPermissions?.length) {
    return true;
  }

  // Check all permissions
  const hasAllPermissions = requiredPermissions.every(permission =>
    permissionService.hasPermission(permission)
  );

  if (hasAllPermissions) {
    return true;
  }

  return router.createUrlTree(['/access-denied']);
};

// Usage
{
  path: 'users',
  canActivate: [authGuard, permissionGuard],
  data: { permissions: ['users.read', 'users.manage'] },
  loadComponent: () => import('./users.component'),
}
```

## Unsaved Changes Guard

```typescript
// shared/guards/unsaved-changes.guard.ts
import { CanDeactivateFn } from '@angular/router';

// Interface for components with unsaved changes
export interface HasUnsavedChanges {
  hasUnsavedChanges(): boolean;
}

export const unsavedChangesGuard: CanDeactivateFn<HasUnsavedChanges> = (
  component,
  currentRoute,
  currentState,
  nextState
) => {
  if (!component.hasUnsavedChanges()) {
    return true;
  }

  // Show confirmation dialog
  return window.confirm(
    'You have unsaved changes. Are you sure you want to leave?'
  );
};

// Component implementation
@Component({...})
export class EditFormComponent implements HasUnsavedChanges {
  form = inject(FormBuilder).group({...});

  hasUnsavedChanges(): boolean {
    return this.form.dirty;
  }
}

// Usage
{
  path: 'edit/:id',
  canDeactivate: [unsavedChangesGuard],
  loadComponent: () => import('./edit-form.component'),
}
```

## Custom Unsaved Changes Dialog

```typescript
// With dialog service
export const unsavedChangesGuard: CanDeactivateFn<HasUnsavedChanges> = async (
  component
) => {
  if (!component.hasUnsavedChanges()) {
    return true;
  }

  const dialogService = inject(DialogService);

  return await dialogService.confirm({
    title: 'Unsaved Changes',
    message: 'You have unsaved changes. Do you want to save before leaving?',
    confirmText: 'Save & Leave',
    cancelText: 'Leave without Saving',
    dismissText: 'Stay',
  }).then(result => {
    if (result === 'confirm') {
      return component.save().then(() => true);
    }
    if (result === 'cancel') {
      return true;
    }
    return false;
  });
};
```

## Async Guard

```typescript
// core/guards/subscription.guard.ts
import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { SubscriptionService } from '../services/subscription.service';
import { map, catchError, of } from 'rxjs';

export const subscriptionGuard: CanActivateFn = (route) => {
  const subscriptionService = inject(SubscriptionService);
  const router = inject(Router);

  const requiredPlan = route.data['plan'] as string;

  return subscriptionService.checkSubscription().pipe(
    map(subscription => {
      if (subscription.plan === requiredPlan ||
          subscription.planLevel >= getPlanLevel(requiredPlan)) {
        return true;
      }

      return router.createUrlTree(['/upgrade'], {
        queryParams: { plan: requiredPlan },
      });
    }),
    catchError(() => of(router.createUrlTree(['/error']))),
  );
};

// Usage
{
  path: 'premium-features',
  canActivate: [authGuard, subscriptionGuard],
  data: { plan: 'premium' },
  loadComponent: () => import('./premium.component'),
}
```

## Feature Flag Guard

```typescript
// core/guards/feature-flag.guard.ts
import { inject } from '@angular/core';
import { CanMatchFn, Router } from '@angular/router';
import { FeatureFlagService } from '../services/feature-flag.service';

export const featureFlagGuard: CanMatchFn = (route) => {
  const featureFlagService = inject(FeatureFlagService);
  const router = inject(Router);

  const featureFlag = route.data?.['featureFlag'] as string;

  if (!featureFlag) {
    return true;
  }

  if (featureFlagService.isEnabled(featureFlag)) {
    return true;
  }

  // Feature not available - redirect
  return router.createUrlTree(['/']);
};

// Usage with canMatch
{
  path: 'new-feature',
  canMatch: [featureFlagGuard],
  data: { featureFlag: 'NEW_FEATURE_ENABLED' },
  loadComponent: () => import('./new-feature.component'),
}
```

## Combining Guards

```typescript
// Order matters - guards run in array order
{
  path: 'admin/users',
  canActivate: [
    authGuard,           // First: Check authentication
    roleGuard,           // Second: Check role
    permissionGuard,     // Third: Check specific permissions
  ],
  data: {
    roles: ['admin'],
    permissions: ['users.manage'],
  },
  loadComponent: () => import('./users.component'),
}
```

## Guard Factory

```typescript
// Create parameterized guards
export function requireRole(...roles: string[]): CanActivateFn {
  return (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    const userRoles = authService.currentUser()?.roles || [];
    const hasRole = roles.some(role => userRoles.includes(role));

    return hasRole || router.createUrlTree(['/unauthorized']);
  };
}

// Usage
{
  path: 'admin',
  canActivate: [authGuard, requireRole('admin', 'superadmin')],
  loadComponent: () => import('./admin.component'),
}
```

## Testing Guards

```typescript
// auth.guard.spec.ts
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { authGuard } from './auth.guard';
import { AuthService } from '../services/auth.service';

describe('authGuard', () => {
  let authService: jasmine.SpyObj<AuthService>;
  let router: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authService = jasmine.createSpyObj('AuthService', ['isAuthenticated']);
    router = jasmine.createSpyObj('Router', ['createUrlTree']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authService },
        { provide: Router, useValue: router },
      ],
    });
  });

  it('should allow access when authenticated', () => {
    authService.isAuthenticated.and.returnValue(true);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, { url: '/dashboard' } as any)
    );

    expect(result).toBe(true);
  });

  it('should redirect to login when not authenticated', () => {
    authService.isAuthenticated.and.returnValue(false);
    const urlTree = {} as any;
    router.createUrlTree.and.returnValue(urlTree);

    const result = TestBed.runInInjectionContext(() =>
      authGuard({} as any, { url: '/dashboard' } as any)
    );

    expect(result).toBe(urlTree);
    expect(router.createUrlTree).toHaveBeenCalledWith(
      ['/auth/login'],
      { queryParams: { returnUrl: '/dashboard' } }
    );
  });
});
```

## Best Practices

1. **Use functional guards**: Not class-based (Angular 14+)
2. **Return UrlTree for redirects**: Not boolean false
3. **Order guards correctly**: Auth before role before permission
4. **Keep guards focused**: Single responsibility
5. **Use canMatch for conditionals**: Route matching conditions
6. **Test thoroughly**: Guards are critical for security
7. **Handle async properly**: Use Observables or Promises
