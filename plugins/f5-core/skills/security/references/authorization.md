# Authorization Patterns

RBAC, ABAC, permissions management, and access control implementation.

## Table of Contents

1. [RBAC Overview](#rbac-overview)
2. [RBAC Implementation](#rbac-implementation)
3. [ABAC Pattern](#abac-pattern)
4. [Permissions Management](#permissions-management)
5. [Access Control Middleware](#access-control-middleware)

---

## RBAC Overview

### Model Structure

```
┌──────────┐    ┌──────────┐    ┌─────────────┐
│  Users   │───>│  Roles   │───>│ Permissions │
└──────────┘    └──────────┘    └─────────────┘
                     │                 │
                     v                 v
             ┌──────────────────────────────┐
             │        Resources             │
             └──────────────────────────────┘
```

### Database Schema (Prisma)

```prisma
model User {
  id        String     @id @default(cuid())
  email     String     @unique
  name      String
  roles     UserRole[]
  createdAt DateTime   @default(now())
}

model Role {
  id          String           @id @default(cuid())
  name        String           @unique
  description String?
  permissions RolePermission[]
  users       UserRole[]
  parentRole  Role?            @relation("RoleHierarchy", fields: [parentRoleId], references: [id])
  parentRoleId String?
  childRoles  Role[]           @relation("RoleHierarchy")
}

model Permission {
  id          String           @id @default(cuid())
  resource    String
  action      String
  description String?
  roles       RolePermission[]

  @@unique([resource, action])
}

model UserRole {
  userId     String
  roleId     String
  user       User     @relation(fields: [userId], references: [id])
  role       Role     @relation(fields: [roleId], references: [id])
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

---

## RBAC Implementation

### RBAC Service

```typescript
export class RBACService {
  constructor(
    private roleRepository: RoleRepository,
    private permissionRepository: PermissionRepository,
    private userRoleRepository: UserRoleRepository,
    private cache: Redis
  ) {}

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
      p => this.matchesPermission({ resource, action }, p)
    );

    // Cache result for 5 minutes
    await this.cache.setex(cacheKey, 300, hasPermission.toString());

    return hasPermission;
  }

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

  // Include inherited from parent roles
  private async getRolePermissions(roleId: string): Promise<Permission[]> {
    const role = await this.roleRepository.findById(roleId);
    if (!role) return [];

    const permissions = await this.permissionRepository.findByRoleId(roleId);

    if (role.parentRoleId) {
      const parentPermissions = await this.getRolePermissions(role.parentRoleId);
      permissions.push(...parentPermissions);
    }

    return permissions;
  }

  // Wildcard matching
  private matchesPermission(
    required: { resource: string; action: string },
    permission: Permission
  ): boolean {
    if (permission.resource === '*' && permission.action === '*') {
      return true;
    }

    const resourceMatch =
      permission.resource === required.resource ||
      permission.resource === '*';

    const actionMatch =
      permission.action === required.action ||
      permission.action === '*';

    return resourceMatch && actionMatch;
  }

  async assignRole(userId: string, roleId: string, assignedBy: string): Promise<void> {
    await this.userRoleRepository.create({ userId, roleId, assignedBy });
    await this.invalidateUserCache(userId);
  }

  async removeRole(userId: string, roleId: string): Promise<void> {
    await this.userRoleRepository.delete({ userId, roleId });
    await this.invalidateUserCache(userId);
  }

  private async invalidateUserCache(userId: string): Promise<void> {
    const keys = await this.cache.keys(`rbac:${userId}:*`);
    if (keys.length > 0) {
      await this.cache.del(...keys);
    }
  }
}
```

### Role Hierarchy

```typescript
const roleHierarchy = {
  super_admin: {
    inherits: null,
    permissions: ['*:*'],
  },
  admin: {
    inherits: null,
    permissions: ['users:*', 'orders:*', 'products:*'],
  },
  manager: {
    inherits: null,
    permissions: ['orders:read', 'orders:update', 'products:read'],
  },
  staff: {
    inherits: 'manager',
    permissions: ['reports:read'],
  },
  user: {
    inherits: null,
    permissions: ['profile:read', 'profile:update', 'orders:create'],
  },
};
```

### Predefined Roles Configuration

```typescript
export const predefinedRoles = {
  SUPER_ADMIN: 'super_admin',
  ADMIN: 'admin',
  MANAGER: 'manager',
  STAFF: 'staff',
  USER: 'user',
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

---

## ABAC Pattern

### Attribute-Based Access Control

```typescript
interface AccessRequest {
  subject: {
    id: string;
    roles: string[];
    department: string;
    clearanceLevel: number;
  };
  resource: {
    type: string;
    id: string;
    owner: string;
    classification: string;
  };
  action: string;
  context: {
    time: Date;
    ip: string;
    location?: string;
  };
}

type PolicyRule = (request: AccessRequest) => boolean;

export class ABACService {
  private policies: Map<string, PolicyRule[]> = new Map();

  registerPolicy(resourceType: string, rule: PolicyRule) {
    const rules = this.policies.get(resourceType) || [];
    rules.push(rule);
    this.policies.set(resourceType, rules);
  }

  async evaluate(request: AccessRequest): Promise<boolean> {
    const rules = this.policies.get(request.resource.type) || [];

    // All rules must pass (AND logic)
    return rules.every(rule => rule(request));
  }
}

// Define policies
const abac = new ABACService();

// Document access policy
abac.registerPolicy('document', (req) => {
  // Owner can do anything
  if (req.resource.owner === req.subject.id) return true;

  // Check clearance level for classified documents
  if (req.resource.classification === 'confidential') {
    return req.subject.clearanceLevel >= 2;
  }
  if (req.resource.classification === 'secret') {
    return req.subject.clearanceLevel >= 3;
  }

  return true;
});

// Time-based access
abac.registerPolicy('document', (req) => {
  const hour = req.context.time.getHours();
  // Only allow access during business hours for external users
  if (!req.subject.roles.includes('internal')) {
    return hour >= 9 && hour < 17;
  }
  return true;
});

// Department-based access
abac.registerPolicy('document', (req) => {
  // Finance documents only for finance department
  if (req.resource.type === 'finance_document') {
    return req.subject.department === 'finance';
  }
  return true;
});
```

### ABAC vs RBAC Comparison

| Aspect | RBAC | ABAC |
|--------|------|------|
| Complexity | Simple | Complex |
| Flexibility | Limited | Very flexible |
| Scalability | Role explosion risk | Scales with attributes |
| Use case | Standard apps | Fine-grained control |
| Maintenance | Role management | Policy management |

---

## Permissions Management

### Dynamic Permission Checking

```typescript
// NestJS Guard
@Injectable()
export class PermissionGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private rbacService: RBACService
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const permission = this.reflector.get<{ resource: string; action: string }>(
      'permission',
      context.getHandler()
    );

    if (!permission) return true;

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    if (!user) return false;

    return this.rbacService.hasPermission(
      user.id,
      permission.resource,
      permission.action
    );
  }
}

// Decorator
export function RequirePermission(resource: string, action: string) {
  return applyDecorators(
    SetMetadata('permission', { resource, action }),
    UseGuards(AuthGuard, PermissionGuard)
  );
}

// Usage
@Controller('users')
export class UsersController {
  @Get()
  @RequirePermission('users', 'read')
  findAll() {
    return this.usersService.findAll();
  }

  @Post()
  @RequirePermission('users', 'create')
  create(@Body() dto: CreateUserDto) {
    return this.usersService.create(dto);
  }

  @Delete(':id')
  @RequirePermission('users', 'delete')
  remove(@Param('id') id: string) {
    return this.usersService.remove(id);
  }
}
```

### Resource-Level Permissions

```typescript
// Check if user can access specific resource
export class ResourcePermissionService {
  async canAccessResource(
    userId: string,
    resourceType: string,
    resourceId: string,
    action: string
  ): Promise<boolean> {
    // Check global permission first
    const hasGlobalPermission = await this.rbacService.hasPermission(
      userId,
      resourceType,
      action
    );

    if (hasGlobalPermission) return true;

    // Check resource-specific permission
    const resourcePermission = await this.resourcePermissionRepository.find({
      userId,
      resourceType,
      resourceId,
      action,
    });

    return !!resourcePermission;
  }

  async grantResourcePermission(
    userId: string,
    resourceType: string,
    resourceId: string,
    action: string
  ): Promise<void> {
    await this.resourcePermissionRepository.create({
      userId,
      resourceType,
      resourceId,
      action,
    });
  }
}
```

---

## Access Control Middleware

### Express Middleware

```typescript
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

// Usage
router.get('/users', authorize('users', 'read'), listUsers);
router.post('/users', authorize('users', 'create'), createUser);
router.delete('/users/:id', authorize('users', 'delete'), deleteUser);
```

### Ownership Verification

```typescript
export function authorizeOwner(resourceFetcher: (req: Request) => Promise<{ ownerId: string }>) {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const resource = await resourceFetcher(req);

      if (resource.ownerId !== req.user.id) {
        // Check if user has admin override
        const hasOverride = await rbacService.hasPermission(
          req.user.id,
          'resources',
          'admin'
        );

        if (!hasOverride) {
          return res.status(403).json({ error: 'Not authorized' });
        }
      }

      next();
    } catch (error) {
      next(error);
    }
  };
}

// Usage
router.put('/orders/:id',
  authorizeOwner(async (req) => orderService.findById(req.params.id)),
  updateOrder
);
```

---

## Best Practices

| Practice | Description |
|----------|-------------|
| Least privilege | Grant minimum required permissions |
| Deny by default | Explicit allow, implicit deny |
| Separation of duties | Critical operations require multiple roles |
| Role granularity | Balance between too few and too many roles |
| Regular audits | Review role assignments periodically |
| Cache permissions | Cache for performance, invalidate on changes |
| Audit logging | Log all permission checks and changes |

### Audit Logging

```typescript
export class AuditService {
  async logPermissionCheck(
    userId: string,
    resource: string,
    action: string,
    granted: boolean
  ) {
    await this.auditRepository.create({
      type: 'permission_check',
      userId,
      resource,
      action,
      result: granted ? 'granted' : 'denied',
      timestamp: new Date(),
    });
  }

  async logRoleChange(
    userId: string,
    roleId: string,
    operation: 'assign' | 'remove',
    performedBy: string
  ) {
    await this.auditRepository.create({
      type: 'role_change',
      userId,
      roleId,
      operation,
      performedBy,
      timestamp: new Date(),
    });
  }
}
```
