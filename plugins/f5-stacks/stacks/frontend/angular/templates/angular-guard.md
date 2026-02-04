# Angular Guard Template

## Authentication Guard

```typescript
// core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn, CanMatchFn } from '@angular/router';
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

// For protecting entire route branches
export const authGuardMatch: CanMatchFn = (route, segments) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  const returnUrl = '/' + segments.map(s => s.path).join('/');
  return router.createUrlTree(['/auth/login'], {
    queryParams: { returnUrl },
  });
};
```

## Role-Based Guard

```typescript
// core/guards/role.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn, ActivatedRouteSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route: ActivatedRouteSnapshot) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredRoles = route.data['roles'] as string[] | undefined;

  // No roles required
  if (!requiredRoles || requiredRoles.length === 0) {
    return true;
  }

  const userRoles = authService.currentUser()?.roles || [];
  const hasRole = requiredRoles.some(role => userRoles.includes(role));

  if (hasRole) {
    return true;
  }

  // Redirect to unauthorized page
  return router.createUrlTree(['/unauthorized']);
};

// Usage in routes:
// {
//   path: 'admin',
//   loadComponent: () => import('./admin.component'),
//   canActivate: [authGuard, roleGuard],
//   data: { roles: ['admin', 'superadmin'] },
// }
```

## Permission Guard

```typescript
// core/guards/permission.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { PermissionService } from '../services/permission.service';

export const permissionGuard: CanActivateFn = (route) => {
  const permissionService = inject(PermissionService);
  const router = inject(Router);

  const requiredPermissions = route.data['permissions'] as string[] | undefined;

  if (!requiredPermissions?.length) {
    return true;
  }

  // Check if user has ALL required permissions
  const hasAllPermissions = requiredPermissions.every(permission =>
    permissionService.hasPermission(permission)
  );

  if (hasAllPermissions) {
    return true;
  }

  return router.createUrlTree(['/access-denied']);
};

// Guard factory for specific permission
export function requirePermission(permission: string): CanActivateFn {
  return () => {
    const permissionService = inject(PermissionService);
    const router = inject(Router);

    if (permissionService.hasPermission(permission)) {
      return true;
    }

    return router.createUrlTree(['/access-denied']);
  };
}

// Usage:
// canActivate: [requirePermission('users.create')]
```

## Feature Flag Guard

```typescript
// core/guards/feature-flag.guard.ts
import { inject } from '@angular/core';
import { Router, CanMatchFn } from '@angular/router';
import { FeatureFlagService } from '../services/feature-flag.service';

export const featureFlagGuard: CanMatchFn = (route) => {
  const featureFlagService = inject(FeatureFlagService);
  const router = inject(Router);

  const featureFlag = route.data?.['featureFlag'] as string | undefined;

  if (!featureFlag) {
    return true;
  }

  if (featureFlagService.isEnabled(featureFlag)) {
    return true;
  }

  // Feature not available
  return router.createUrlTree(['/']);
};

// Guard factory
export function requireFeature(flagName: string): CanMatchFn {
  return () => {
    const featureFlagService = inject(FeatureFlagService);
    const router = inject(Router);

    if (featureFlagService.isEnabled(flagName)) {
      return true;
    }

    return router.createUrlTree(['/']);
  };
}

// Usage:
// canMatch: [requireFeature('NEW_DASHBOARD')]
```

## Unsaved Changes Guard

```typescript
// shared/guards/unsaved-changes.guard.ts
import { inject } from '@angular/core';
import { CanDeactivateFn } from '@angular/router';
import { DialogService } from '../services/dialog.service';

// Interface for components with unsaved changes
export interface HasUnsavedChanges {
  hasUnsavedChanges(): boolean;
  saveChanges?(): Promise<boolean>;
}

export const unsavedChangesGuard: CanDeactivateFn<HasUnsavedChanges> = async (
  component
) => {
  if (!component.hasUnsavedChanges()) {
    return true;
  }

  const dialogService = inject(DialogService);

  const result = await dialogService.confirm({
    title: 'Unsaved Changes',
    message: 'You have unsaved changes. What would you like to do?',
    confirmText: 'Save & Leave',
    cancelText: 'Discard Changes',
    dismissText: 'Stay',
  });

  if (result === 'confirm' && component.saveChanges) {
    return await component.saveChanges();
  }

  if (result === 'cancel') {
    return true; // Discard and leave
  }

  return false; // Stay on page
};

// Simple version with browser confirm
export const simpleUnsavedChangesGuard: CanDeactivateFn<HasUnsavedChanges> = (
  component
) => {
  if (!component.hasUnsavedChanges()) {
    return true;
  }

  return window.confirm(
    'You have unsaved changes. Are you sure you want to leave?'
  );
};
```

## Async Guard

```typescript
// core/guards/subscription.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { map, catchError, of } from 'rxjs';
import { SubscriptionService } from '../services/subscription.service';

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

function getPlanLevel(plan: string): number {
  const levels: Record<string, number> = {
    free: 0,
    basic: 1,
    pro: 2,
    enterprise: 3,
  };
  return levels[plan] || 0;
}
```

## Guard Factory

```typescript
// core/guards/guard-factory.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

// Create parameterized guards
export function requireRoles(...roles: string[]): CanActivateFn {
  return () => {
    const authService = inject(AuthService);
    const router = inject(Router);

    const userRoles = authService.currentUser()?.roles || [];
    const hasRole = roles.some(role => userRoles.includes(role));

    return hasRole || router.createUrlTree(['/unauthorized']);
  };
}

export function requireAuth(redirectTo = '/auth/login'): CanActivateFn {
  return (route, state) => {
    const authService = inject(AuthService);
    const router = inject(Router);

    if (authService.isAuthenticated()) {
      return true;
    }

    return router.createUrlTree([redirectTo], {
      queryParams: { returnUrl: state.url },
    });
  };
}

// Usage:
// canActivate: [requireRoles('admin', 'moderator')]
// canActivate: [requireAuth('/login')]
```

## Route Configuration Example

```typescript
// app.routes.ts
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';
import { permissionGuard } from './core/guards/permission.guard';
import { featureFlagGuard } from './core/guards/feature-flag.guard';
import { unsavedChangesGuard } from './shared/guards/unsaved-changes.guard';

export const routes: Routes = [
  // Public routes
  { path: 'login', loadComponent: () => import('./auth/login.component') },

  // Protected routes
  {
    path: 'dashboard',
    loadComponent: () => import('./dashboard/dashboard.component'),
    canActivate: [authGuard],
  },

  // Role-protected routes
  {
    path: 'admin',
    loadChildren: () => import('./admin/admin.routes'),
    canActivate: [authGuard, roleGuard],
    data: { roles: ['admin'] },
  },

  // Permission-protected routes
  {
    path: 'users',
    loadComponent: () => import('./users/users.component'),
    canActivate: [authGuard, permissionGuard],
    data: { permissions: ['users.read'] },
  },

  // Feature-flagged routes
  {
    path: 'new-feature',
    loadComponent: () => import('./features/new-feature.component'),
    canMatch: [featureFlagGuard],
    data: { featureFlag: 'NEW_FEATURE' },
  },

  // With unsaved changes protection
  {
    path: 'editor/:id',
    loadComponent: () => import('./editor/editor.component'),
    canActivate: [authGuard],
    canDeactivate: [unsavedChangesGuard],
  },
];
```
