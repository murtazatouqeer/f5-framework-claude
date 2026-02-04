# Angular Guard Generator Agent

## Overview

Specialized agent for generating Angular route guards using functional guard pattern (Angular 14+). Creates type-safe guards for authentication, authorization, and data validation.

## Capabilities

- Generate functional guards (canActivate, canActivateChild, canDeactivate, canMatch)
- Create authentication guards with redirect
- Implement role-based authorization guards
- Generate form unsaved changes guards
- Create feature flag guards
- Support for async guard logic

## Input Requirements

```yaml
required:
  - name: Guard name (camelCase)
  - type: auth | role | permission | unsaved | feature | custom

optional:
  - redirect_to: Route to redirect on failure
  - roles: Array of required roles (for role guard)
  - permissions: Array of required permissions
  - services: Services to inject
  - async: Whether guard is async
```

## Generation Rules

### Naming Conventions
- Guard function: `{name}Guard`
- File: `{kebab-case-name}.guard.ts`
- Test file: `{kebab-case-name}.guard.spec.ts`

### Guard Location
```
core/guards/                    # Global guards
├── auth.guard.ts
├── role.guard.ts
└── permission.guard.ts

features/{feature}/guards/      # Feature-specific guards
└── {feature}-specific.guard.ts
```

### Code Patterns

#### Authentication Guard
```typescript
// core/guards/auth.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // Store attempted URL for redirecting
  router.navigate(['/auth/login'], {
    queryParams: { returnUrl: state.url },
  });

  return false;
};
```

#### Role-Based Guard
```typescript
// core/guards/role.guard.ts
import { inject } from '@angular/core';
import { Router, CanActivateFn, CanActivateChildFn } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredRoles = route.data['roles'] as string[];

  if (!requiredRoles || requiredRoles.length === 0) {
    return true;
  }

  const userRoles = authService.currentUser()?.roles || [];
  const hasRole = requiredRoles.some(role => userRoles.includes(role));

  if (hasRole) {
    return true;
  }

  router.navigate(['/unauthorized']);
  return false;
};

// Can also be used for child routes
export const roleGuardChild: CanActivateChildFn = (childRoute, state) => {
  return roleGuard(childRoute, state);
};
```

#### Permission Guard
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

  const hasPermission = requiredPermissions.every(
    permission => permissionService.hasPermission(permission)
  );

  if (hasPermission) {
    return true;
  }

  router.navigate(['/forbidden']);
  return false;
};
```

#### Unsaved Changes Guard
```typescript
// shared/guards/unsaved-changes.guard.ts
import { CanDeactivateFn } from '@angular/router';

export interface HasUnsavedChanges {
  hasUnsavedChanges(): boolean;
}

export const unsavedChangesGuard: CanDeactivateFn<HasUnsavedChanges> = (
  component,
  currentRoute,
  currentState,
  nextState
) => {
  if (component.hasUnsavedChanges()) {
    return window.confirm(
      'You have unsaved changes. Do you really want to leave?'
    );
  }
  return true;
};
```

#### Async Guard with Observable
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
      if (subscription.plan === requiredPlan || subscription.plan === 'enterprise') {
        return true;
      }
      router.navigate(['/upgrade'], {
        queryParams: { requiredPlan },
      });
      return false;
    }),
    catchError(() => {
      router.navigate(['/error']);
      return of(false);
    })
  );
};
```

#### Feature Flag Guard
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

  router.navigate(['/']);
  return false;
};
```

## Usage in Routes

```typescript
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';
import { unsavedChangesGuard } from './shared/guards/unsaved-changes.guard';

export const routes: Routes = [
  {
    path: 'dashboard',
    canActivate: [authGuard],
    loadComponent: () => import('./dashboard.component'),
  },
  {
    path: 'admin',
    canActivate: [authGuard, roleGuard],
    canActivateChild: [roleGuard],
    data: { roles: ['admin'] },
    children: [...],
  },
  {
    path: 'editor',
    canDeactivate: [unsavedChangesGuard],
    loadComponent: () => import('./editor.component'),
  },
];
```

## Integration

- Works with: module-generator, service-generator
- Uses templates: angular-guard.md
- Follows skills: guards, routing

## Examples

### Generate Admin Guard
```
Input:
  name: admin
  type: role
  roles: ['admin', 'super-admin']
  redirect_to: /unauthorized

Output: Role-based guard checking for admin roles
```

### Generate Form Guard
```
Input:
  name: formUnsaved
  type: unsaved

Output: CanDeactivate guard for unsaved form changes
```
