---
name: permissions
description: Permission systems and patterns
category: security/authorization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Permission Systems

## Overview

Permissions define what actions users can perform on resources.
Well-designed permission systems are granular, auditable, and maintainable.

## Permission Model

```
┌─────────────────────────────────────────────────────────────┐
│                   Permission Model                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Permission = Resource + Action + Scope                     │
│                                                             │
│  Examples:                                                  │
│  - users:read:all          (read all users)                │
│  - users:read:own          (read own profile)              │
│  - orders:write:department (write orders in department)    │
│  - reports:delete:*        (delete any report)             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Permission Schema

```typescript
// types/permission.types.ts
interface Permission {
  id: string;
  resource: string;      // e.g., "users", "orders"
  action: string;        // e.g., "read", "write", "delete"
  scope?: PermissionScope;
  conditions?: PermissionCondition[];
}

type PermissionScope =
  | 'all'           // All resources
  | 'own'           // Only user's own resources
  | 'department'    // Resources in user's department
  | 'team'          // Resources in user's team
  | 'assigned';     // Resources assigned to user

interface PermissionCondition {
  field: string;
  operator: 'eq' | 'ne' | 'in' | 'gt' | 'lt';
  value: any;
}

// Database schema
model Permission {
  id          String   @id @default(cuid())
  code        String   @unique // e.g., "users:read:all"
  resource    String
  action      String
  scope       String   @default("all")
  description String?
  createdAt   DateTime @default(now())
  roles       RolePermission[]
}
```

## Permission Constants

```typescript
// constants/permissions.ts
export const Resources = {
  USERS: 'users',
  ORDERS: 'orders',
  PRODUCTS: 'products',
  REPORTS: 'reports',
  SETTINGS: 'settings',
  AUDIT_LOGS: 'audit_logs',
} as const;

export const Actions = {
  CREATE: 'create',
  READ: 'read',
  UPDATE: 'update',
  DELETE: 'delete',
  APPROVE: 'approve',
  EXPORT: 'export',
  IMPORT: 'import',
} as const;

export const Scopes = {
  ALL: 'all',
  OWN: 'own',
  DEPARTMENT: 'department',
  TEAM: 'team',
  ASSIGNED: 'assigned',
} as const;

// Permission builder
export function permission(
  resource: keyof typeof Resources,
  action: keyof typeof Actions,
  scope: keyof typeof Scopes = 'ALL'
): string {
  return `${Resources[resource]}:${Actions[action]}:${Scopes[scope]}`;
}

// Predefined permissions
export const Permissions = {
  // User management
  USERS_CREATE: permission('USERS', 'CREATE'),
  USERS_READ_ALL: permission('USERS', 'READ', 'ALL'),
  USERS_READ_OWN: permission('USERS', 'READ', 'OWN'),
  USERS_UPDATE_ALL: permission('USERS', 'UPDATE', 'ALL'),
  USERS_UPDATE_OWN: permission('USERS', 'UPDATE', 'OWN'),
  USERS_DELETE: permission('USERS', 'DELETE'),

  // Order management
  ORDERS_CREATE: permission('ORDERS', 'CREATE'),
  ORDERS_READ_ALL: permission('ORDERS', 'READ', 'ALL'),
  ORDERS_READ_OWN: permission('ORDERS', 'READ', 'OWN'),
  ORDERS_READ_DEPT: permission('ORDERS', 'READ', 'DEPARTMENT'),
  ORDERS_UPDATE_ALL: permission('ORDERS', 'UPDATE', 'ALL'),
  ORDERS_APPROVE: permission('ORDERS', 'APPROVE'),

  // Reports
  REPORTS_READ: permission('REPORTS', 'READ'),
  REPORTS_EXPORT: permission('REPORTS', 'EXPORT'),

  // Settings
  SETTINGS_READ: permission('SETTINGS', 'READ'),
  SETTINGS_UPDATE: permission('SETTINGS', 'UPDATE'),
} as const;
```

## Permission Checking

### Service Implementation

```typescript
// services/permission.service.ts
export class PermissionService {
  constructor(
    private userRepository: UserRepository,
    private permissionRepository: PermissionRepository,
    private cache: Redis
  ) {}

  async check(
    userId: string,
    permissionCode: string,
    context?: PermissionContext
  ): Promise<boolean> {
    // Parse permission
    const [resource, action, scope] = permissionCode.split(':');

    // Get user's permissions
    const userPermissions = await this.getUserPermissions(userId);

    // Check for exact match
    if (userPermissions.has(permissionCode)) {
      return this.checkScope(userId, scope, context);
    }

    // Check for wildcard permissions
    const wildcardPatterns = [
      `${resource}:${action}:all`,  // Same action, all scope
      `${resource}:*:all`,          // All actions on resource
      `*:${action}:all`,            // Action on all resources
      '*:*:all',                    // Superadmin
    ];

    for (const pattern of wildcardPatterns) {
      if (userPermissions.has(pattern)) {
        return true;
      }
    }

    return false;
  }

  private async checkScope(
    userId: string,
    scope: string,
    context?: PermissionContext
  ): Promise<boolean> {
    if (scope === 'all' || !context) {
      return true;
    }

    const user = await this.userRepository.findById(userId);

    switch (scope) {
      case 'own':
        return context.resourceOwnerId === userId;

      case 'department':
        return context.resourceDepartment === user.departmentId;

      case 'team':
        return context.resourceTeam === user.teamId;

      case 'assigned':
        return context.assignedTo?.includes(userId) || false;

      default:
        return false;
    }
  }

  async getUserPermissions(userId: string): Promise<Set<string>> {
    const cacheKey = `permissions:${userId}`;
    const cached = await this.cache.get(cacheKey);

    if (cached) {
      return new Set(JSON.parse(cached));
    }

    const permissions = await this.permissionRepository.findByUserId(userId);
    const permissionSet = new Set(permissions.map(p => p.code));

    await this.cache.setex(cacheKey, 300, JSON.stringify([...permissionSet]));

    return permissionSet;
  }

  async grant(userId: string, permissionCode: string): Promise<void> {
    await this.permissionRepository.grantToUser(userId, permissionCode);
    await this.invalidateCache(userId);
  }

  async revoke(userId: string, permissionCode: string): Promise<void> {
    await this.permissionRepository.revokeFromUser(userId, permissionCode);
    await this.invalidateCache(userId);
  }

  private async invalidateCache(userId: string): Promise<void> {
    await this.cache.del(`permissions:${userId}`);
  }
}
```

### Middleware and Decorators

```typescript
// middleware/permission.middleware.ts
export function requirePermission(permissionCode: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    if (!req.user) {
      return res.status(401).json({ error: 'Authentication required' });
    }

    const context: PermissionContext = {
      resourceOwnerId: req.resourceOwner,
      resourceDepartment: req.resourceDepartment,
      resourceTeam: req.resourceTeam,
      assignedTo: req.resourceAssignees,
    };

    const hasPermission = await permissionService.check(
      req.user.id,
      permissionCode,
      context
    );

    if (!hasPermission) {
      return res.status(403).json({ error: 'Permission denied' });
    }

    next();
  };
}

// Usage
router.get('/users', requirePermission(Permissions.USERS_READ_ALL), getUsers);
router.get('/users/me', requirePermission(Permissions.USERS_READ_OWN), getMe);
router.delete('/users/:id', requirePermission(Permissions.USERS_DELETE), deleteUser);
```

### Frontend Permission Checking

```typescript
// hooks/usePermission.ts
import { useMemo } from 'react';
import { useAuth } from './useAuth';

export function usePermission(permissionCode: string): boolean {
  const { user } = useAuth();

  return useMemo(() => {
    if (!user?.permissions) return false;
    return user.permissions.includes(permissionCode);
  }, [user?.permissions, permissionCode]);
}

export function usePermissions(permissionCodes: string[]): Record<string, boolean> {
  const { user } = useAuth();

  return useMemo(() => {
    if (!user?.permissions) {
      return permissionCodes.reduce((acc, code) => ({ ...acc, [code]: false }), {});
    }

    return permissionCodes.reduce((acc, code) => ({
      ...acc,
      [code]: user.permissions.includes(code),
    }), {});
  }, [user?.permissions, permissionCodes]);
}

// Permission-aware component
export function PermissionGate({
  permission,
  children,
  fallback = null,
}: {
  permission: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const hasPermission = usePermission(permission);
  return hasPermission ? <>{children}</> : <>{fallback}</>;
}

// Usage
function UserActions({ userId }: { userId: string }) {
  return (
    <div>
      <PermissionGate permission={Permissions.USERS_UPDATE_ALL}>
        <Button onClick={() => editUser(userId)}>Edit</Button>
      </PermissionGate>

      <PermissionGate permission={Permissions.USERS_DELETE}>
        <Button onClick={() => deleteUser(userId)} variant="danger">
          Delete
        </Button>
      </PermissionGate>
    </div>
  );
}
```

## Permission Inheritance

```typescript
// Permission hierarchy with inheritance
interface PermissionHierarchy {
  [key: string]: string[]; // parent -> children
}

const permissionHierarchy: PermissionHierarchy = {
  'users:*:all': [
    'users:create:all',
    'users:read:all',
    'users:update:all',
    'users:delete:all',
  ],
  'orders:*:all': [
    'orders:create:all',
    'orders:read:all',
    'orders:update:all',
    'orders:delete:all',
    'orders:approve:all',
  ],
  '*:*:all': Object.values(Resources).map(r => `${r}:*:all`),
};

// Expand permission to include inherited
function expandPermissions(permissions: string[]): Set<string> {
  const expanded = new Set<string>();

  function expand(permission: string) {
    expanded.add(permission);
    const children = permissionHierarchy[permission];
    if (children) {
      children.forEach(child => expand(child));
    }
  }

  permissions.forEach(p => expand(p));
  return expanded;
}
```

## Permission Audit

```typescript
// services/permission-audit.service.ts
export class PermissionAuditService {
  async logCheck(
    userId: string,
    permission: string,
    result: boolean,
    context?: any
  ): Promise<void> {
    await this.auditRepository.create({
      type: 'PERMISSION_CHECK',
      userId,
      permission,
      result,
      context,
      timestamp: new Date(),
    });
  }

  async logGrant(
    grantedBy: string,
    grantedTo: string,
    permission: string
  ): Promise<void> {
    await this.auditRepository.create({
      type: 'PERMISSION_GRANT',
      actorId: grantedBy,
      targetUserId: grantedTo,
      permission,
      timestamp: new Date(),
    });
  }

  async logRevoke(
    revokedBy: string,
    revokedFrom: string,
    permission: string
  ): Promise<void> {
    await this.auditRepository.create({
      type: 'PERMISSION_REVOKE',
      actorId: revokedBy,
      targetUserId: revokedFrom,
      permission,
      timestamp: new Date(),
    });
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Naming convention | Use consistent resource:action:scope format |
| Granularity | Balance between too fine and too coarse |
| Documentation | Document all permissions clearly |
| Testing | Test permission checks thoroughly |
| Audit trail | Log all permission changes and checks |
| Cache invalidation | Clear cache on permission changes |
