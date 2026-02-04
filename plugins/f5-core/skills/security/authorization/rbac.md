---
name: rbac
description: Role-Based Access Control implementation
category: security/authorization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Role-Based Access Control (RBAC)

## Overview

RBAC restricts system access based on roles assigned to users.
Users are granted permissions through their role memberships.

## RBAC Model

```
┌─────────────────────────────────────────────────────────────┐
│                     RBAC Model                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌─────────────┐           │
│  │  Users   │───>│  Roles   │───>│ Permissions │           │
│  └──────────┘    └──────────┘    └─────────────┘           │
│                       │                 │                   │
│                       │                 │                   │
│                       v                 v                   │
│               ┌──────────────────────────────┐              │
│               │        Resources             │              │
│               └──────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Database Schema

```typescript
// Prisma schema
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  name      String
  roles     UserRole[]
  createdAt DateTime @default(now())
}

model Role {
  id          String   @id @default(cuid())
  name        String   @unique
  description String?
  permissions RolePermission[]
  users       UserRole[]
  parentRole  Role?    @relation("RoleHierarchy", fields: [parentRoleId], references: [id])
  parentRoleId String?
  childRoles  Role[]   @relation("RoleHierarchy")
  createdAt   DateTime @default(now())
}

model Permission {
  id          String   @id @default(cuid())
  resource    String   // e.g., "users", "orders"
  action      String   // e.g., "read", "write", "delete"
  description String?
  roles       RolePermission[]

  @@unique([resource, action])
}

model UserRole {
  userId    String
  roleId    String
  user      User     @relation(fields: [userId], references: [id])
  role      Role     @relation(fields: [roleId], references: [id])
  assignedAt DateTime @default(now())
  assignedBy String?

  @@id([userId, roleId])
}

model RolePermission {
  roleId       String
  permissionId String
  role         Role       @relation(fields: [roleId], references: [id])
  permission   Permission @relation(fields: [permissionId], references: [id])

  @@id([roleId, permissionId])
}
```

## Implementation

### RBAC Service

```typescript
// services/rbac.service.ts
export class RBACService {
  constructor(
    private roleRepository: RoleRepository,
    private permissionRepository: PermissionRepository,
    private userRoleRepository: UserRoleRepository,
    private cache: Redis
  ) {}

  // Check if user has permission
  async hasPermission(
    userId: string,
    resource: string,
    action: string
  ): Promise<boolean> {
    // Check cache first
    const cacheKey = `rbac:${userId}:${resource}:${action}`;
    const cached = await this.cache.get(cacheKey);
    if (cached !== null) {
      return cached === 'true';
    }

    // Get user's effective permissions
    const permissions = await this.getUserPermissions(userId);
    const hasPermission = permissions.some(
      p => p.resource === resource && p.action === action
    );

    // Cache result
    await this.cache.setex(cacheKey, 300, hasPermission.toString());

    return hasPermission;
  }

  // Get all permissions for user (including inherited from role hierarchy)
  async getUserPermissions(userId: string): Promise<Permission[]> {
    const userRoles = await this.userRoleRepository.findByUserId(userId);
    const allPermissions = new Set<string>();
    const permissions: Permission[] = [];

    for (const userRole of userRoles) {
      const rolePermissions = await this.getRolePermissions(userRole.roleId);
      for (const permission of rolePermissions) {
        const key = `${permission.resource}:${permission.action}`;
        if (!allPermissions.has(key)) {
          allPermissions.add(key);
          permissions.push(permission);
        }
      }
    }

    return permissions;
  }

  // Get permissions including inherited from parent roles
  private async getRolePermissions(roleId: string): Promise<Permission[]> {
    const role = await this.roleRepository.findById(roleId);
    if (!role) return [];

    const permissions = await this.permissionRepository.findByRoleId(roleId);

    // Include parent role permissions (hierarchy)
    if (role.parentRoleId) {
      const parentPermissions = await this.getRolePermissions(role.parentRoleId);
      permissions.push(...parentPermissions);
    }

    return permissions;
  }

  // Assign role to user
  async assignRole(userId: string, roleId: string, assignedBy: string): Promise<void> {
    await this.userRoleRepository.create({
      userId,
      roleId,
      assignedBy,
    });

    // Invalidate cache
    await this.invalidateUserCache(userId);
  }

  // Remove role from user
  async removeRole(userId: string, roleId: string): Promise<void> {
    await this.userRoleRepository.delete({ userId, roleId });
    await this.invalidateUserCache(userId);
  }

  // Invalidate user's permission cache
  private async invalidateUserCache(userId: string): Promise<void> {
    const pattern = `rbac:${userId}:*`;
    const keys = await this.cache.keys(pattern);
    if (keys.length > 0) {
      await this.cache.del(...keys);
    }
  }
}
```

### Authorization Middleware

```typescript
// middleware/authorize.middleware.ts
export function authorize(resource: string, action: string) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      if (!req.user) {
        return res.status(401).json({ error: 'Authentication required' });
      }

      const hasPermission = await rbacService.hasPermission(
        req.user.id,
        resource,
        action
      );

      if (!hasPermission) {
        return res.status(403).json({ error: 'Insufficient permissions' });
      }

      next();
    } catch (error) {
      next(error);
    }
  };
}

// Usage in routes
router.get('/users', authorize('users', 'read'), listUsers);
router.post('/users', authorize('users', 'create'), createUser);
router.put('/users/:id', authorize('users', 'update'), updateUser);
router.delete('/users/:id', authorize('users', 'delete'), deleteUser);
```

### Decorator-Based Authorization (NestJS)

```typescript
// decorators/authorize.decorator.ts
import { SetMetadata, applyDecorators, UseGuards } from '@nestjs/common';

export const PERMISSION_KEY = 'permission';

export interface PermissionRequirement {
  resource: string;
  action: string;
}

export function Authorize(resource: string, action: string) {
  return applyDecorators(
    SetMetadata(PERMISSION_KEY, { resource, action }),
    UseGuards(AuthorizationGuard)
  );
}

// guards/authorization.guard.ts
@Injectable()
export class AuthorizationGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private rbacService: RBACService
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requirement = this.reflector.get<PermissionRequirement>(
      PERMISSION_KEY,
      context.getHandler()
    );

    if (!requirement) return true;

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    if (!user) return false;

    return this.rbacService.hasPermission(
      user.id,
      requirement.resource,
      requirement.action
    );
  }
}

// Usage in controller
@Controller('users')
export class UsersController {
  @Get()
  @Authorize('users', 'read')
  findAll() {
    return this.usersService.findAll();
  }

  @Post()
  @Authorize('users', 'create')
  create(@Body() createUserDto: CreateUserDto) {
    return this.usersService.create(createUserDto);
  }
}
```

## Role Hierarchy

```typescript
// Example role hierarchy
const roleHierarchy = {
  'super_admin': {
    inherits: null,
    permissions: ['*:*'], // All permissions
  },
  'admin': {
    inherits: null,
    permissions: ['users:*', 'orders:*', 'products:*'],
  },
  'manager': {
    inherits: null,
    permissions: ['orders:read', 'orders:update', 'products:read'],
  },
  'staff': {
    inherits: 'manager',
    permissions: ['reports:read'],
  },
  'user': {
    inherits: null,
    permissions: ['profile:read', 'profile:update', 'orders:create'],
  },
};

// Check with wildcard support
function matchesPermission(
  required: { resource: string; action: string },
  permission: { resource: string; action: string }
): boolean {
  // Check for superadmin wildcard
  if (permission.resource === '*' && permission.action === '*') {
    return true;
  }

  // Check resource match (exact or wildcard)
  const resourceMatch =
    permission.resource === required.resource ||
    permission.resource === '*';

  // Check action match (exact or wildcard)
  const actionMatch =
    permission.action === required.action ||
    permission.action === '*';

  return resourceMatch && actionMatch;
}
```

## Predefined Roles

```typescript
// config/roles.config.ts
export const predefinedRoles = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  MANAGER: 'manager',
  STAFF: 'staff',
  USER: 'user',
  GUEST: 'guest',
};

export const defaultPermissions = {
  [predefinedRoles.SUPER_ADMIN]: [
    { resource: '*', action: '*' },
  ],
  [predefinedRoles.ADMIN]: [
    { resource: 'users', action: '*' },
    { resource: 'roles', action: '*' },
    { resource: 'settings', action: '*' },
  ],
  [predefinedRoles.MANAGER]: [
    { resource: 'users', action: 'read' },
    { resource: 'users', action: 'update' },
    { resource: 'reports', action: '*' },
  ],
  [predefinedRoles.USER]: [
    { resource: 'profile', action: 'read' },
    { resource: 'profile', action: 'update' },
  ],
};

// Seed roles on startup
async function seedRoles() {
  for (const [roleName, permissions] of Object.entries(defaultPermissions)) {
    let role = await roleRepository.findByName(roleName);
    if (!role) {
      role = await roleRepository.create({ name: roleName });
    }

    for (const perm of permissions) {
      let permission = await permissionRepository.findByResourceAction(
        perm.resource,
        perm.action
      );
      if (!permission) {
        permission = await permissionRepository.create(perm);
      }
      await rolePermissionRepository.upsert({
        roleId: role.id,
        permissionId: permission.id,
      });
    }
  }
}
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Least privilege | Grant minimum required permissions |
| Role granularity | Balance between too few and too many roles |
| Separation of duties | Critical operations require multiple roles |
| Regular audits | Review role assignments periodically |
| Cache permissions | Cache for performance, invalidate on changes |
| Audit logging | Log all permission checks and changes |
