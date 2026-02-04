---
name: nestjs-authorization
description: RBAC and ABAC authorization patterns in NestJS
applies_to: nestjs
category: security
---

# NestJS Authorization

## Overview

Authorization determines what actions authenticated users can perform.
Two common patterns: Role-Based Access Control (RBAC) and Attribute-Based Access Control (ABAC).

## Role-Based Access Control (RBAC)

### Define Roles

```typescript
// common/enums/role.enum.ts
export enum Role {
  USER = 'user',
  ADMIN = 'admin',
  MODERATOR = 'moderator',
  SUPER_ADMIN = 'super_admin',
}

// Role hierarchy (optional)
export const RoleHierarchy: Record<Role, Role[]> = {
  [Role.SUPER_ADMIN]: [Role.ADMIN, Role.MODERATOR, Role.USER],
  [Role.ADMIN]: [Role.MODERATOR, Role.USER],
  [Role.MODERATOR]: [Role.USER],
  [Role.USER]: [],
};
```

### Roles Decorator

```typescript
// common/decorators/roles.decorator.ts
import { SetMetadata } from '@nestjs/common';
import { Role } from '../enums/role.enum';

export const ROLES_KEY = 'roles';
export const Roles = (...roles: Role[]) => SetMetadata(ROLES_KEY, roles);
```

### Roles Guard

```typescript
// common/guards/roles.guard.ts
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ROLES_KEY } from '../decorators/roles.decorator';
import { Role, RoleHierarchy } from '../enums/role.enum';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<Role[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (!requiredRoles || requiredRoles.length === 0) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();

    if (!user || !user.roles) {
      return false;
    }

    // Check if user has any required role (including hierarchy)
    return requiredRoles.some((requiredRole) =>
      this.hasRole(user.roles, requiredRole),
    );
  }

  private hasRole(userRoles: Role[], requiredRole: Role): boolean {
    for (const userRole of userRoles) {
      if (userRole === requiredRole) {
        return true;
      }

      // Check role hierarchy
      const inheritedRoles = RoleHierarchy[userRole] || [];
      if (inheritedRoles.includes(requiredRole)) {
        return true;
      }
    }
    return false;
  }
}
```

### Usage

```typescript
// users.controller.ts
import { Controller, Get, Delete, Param, UseGuards } from '@nestjs/common';
import { Roles } from '../common/decorators/roles.decorator';
import { RolesGuard } from '../common/guards/roles.guard';
import { Role } from '../common/enums/role.enum';

@Controller('users')
@UseGuards(RolesGuard)
export class UsersController {
  @Get()
  @Roles(Role.ADMIN) // Only admins can list all users
  findAll() {
    return this.usersService.findAll();
  }

  @Delete(':id')
  @Roles(Role.SUPER_ADMIN) // Only super admins can delete
  remove(@Param('id') id: string) {
    return this.usersService.remove(id);
  }
}
```

## Attribute-Based Access Control (ABAC)

ABAC provides fine-grained control based on user attributes, resource attributes, and context.

### Policy Definition

```typescript
// common/authorization/policies/policy.interface.ts
import { ExecutionContext } from '@nestjs/common';

export interface Policy {
  name: string;
  handle(context: ExecutionContext, ...args: any[]): Promise<boolean> | boolean;
}

// common/authorization/policies/order-owner.policy.ts
import { Injectable } from '@nestjs/common';
import { Policy } from './policy.interface';
import { ExecutionContext } from '@nestjs/common';
import { OrdersService } from '../../../modules/orders/orders.service';

@Injectable()
export class OrderOwnerPolicy implements Policy {
  name = 'OrderOwner';

  constructor(private readonly ordersService: OrdersService) {}

  async handle(context: ExecutionContext, orderId: string): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const userId = request.user?.id;

    if (!userId || !orderId) {
      return false;
    }

    const order = await this.ordersService.findById(orderId);

    if (!order) {
      return false;
    }

    return order.customerId === userId;
  }
}

// common/authorization/policies/resource-owner.policy.ts
@Injectable()
export class ResourceOwnerPolicy implements Policy {
  name = 'ResourceOwner';

  constructor(
    private readonly moduleRef: ModuleRef,
  ) {}

  async handle(
    context: ExecutionContext,
    serviceName: string,
    resourceId: string,
    ownerField: string = 'userId',
  ): Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    const userId = request.user?.id;

    if (!userId || !resourceId) {
      return false;
    }

    const service = this.moduleRef.get(serviceName, { strict: false });
    const resource = await service.findById(resourceId);

    if (!resource) {
      return false;
    }

    return resource[ownerField] === userId;
  }
}
```

### Policy Decorator

```typescript
// common/decorators/check-policy.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const CHECK_POLICY_KEY = 'checkPolicy';

export interface PolicyMetadata {
  policy: string;
  args?: any[];
}

export const CheckPolicy = (policy: string, ...args: any[]) =>
  SetMetadata(CHECK_POLICY_KEY, { policy, args });
```

### Policy Guard

```typescript
// common/guards/policies.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ModuleRef } from '@nestjs/core';
import { CHECK_POLICY_KEY, PolicyMetadata } from '../decorators/check-policy.decorator';
import { Policy } from '../authorization/policies/policy.interface';

@Injectable()
export class PoliciesGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private moduleRef: ModuleRef,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const policyMetadata = this.reflector.get<PolicyMetadata>(
      CHECK_POLICY_KEY,
      context.getHandler(),
    );

    if (!policyMetadata) {
      return true;
    }

    const policy = this.moduleRef.get<Policy>(policyMetadata.policy, {
      strict: false,
    });

    if (!policy) {
      throw new Error(`Policy ${policyMetadata.policy} not found`);
    }

    // Get dynamic args from request params
    const request = context.switchToHttp().getRequest();
    const args = this.resolveArgs(policyMetadata.args || [], request);

    const allowed = await policy.handle(context, ...args);

    if (!allowed) {
      throw new ForbiddenException('Access denied by policy');
    }

    return true;
  }

  private resolveArgs(args: any[], request: any): any[] {
    return args.map((arg) => {
      if (typeof arg === 'string' && arg.startsWith(':')) {
        // Resolve from request params
        const paramName = arg.substring(1);
        return request.params[paramName];
      }
      return arg;
    });
  }
}
```

### ABAC Usage

```typescript
// orders.controller.ts
@Controller('orders')
@UseGuards(PoliciesGuard)
export class OrdersController {
  @Get(':id')
  @CheckPolicy('OrderOwnerPolicy', ':id')
  findOne(@Param('id') id: string) {
    return this.ordersService.findOne(id);
  }

  @Patch(':id')
  @CheckPolicy('OrderOwnerPolicy', ':id')
  update(@Param('id') id: string, @Body() dto: UpdateOrderDto) {
    return this.ordersService.update(id, dto);
  }
}
```

## CASL Integration

CASL is a powerful authorization library that works well with NestJS.

```bash
npm install @casl/ability @casl/nestjs
```

### Define Abilities

```typescript
// common/authorization/casl/casl-ability.factory.ts
import {
  AbilityBuilder,
  AbilityClass,
  ExtractSubjectType,
  InferSubjects,
  PureAbility,
} from '@casl/ability';
import { Injectable } from '@nestjs/common';
import { User } from '../../users/entities/user.entity';
import { Order } from '../../orders/entities/order.entity';
import { Article } from '../../articles/entities/article.entity';
import { Role } from '../enums/role.enum';

export enum Action {
  Manage = 'manage', // All actions
  Create = 'create',
  Read = 'read',
  Update = 'update',
  Delete = 'delete',
}

type Subjects = InferSubjects<typeof Order | typeof Article | typeof User> | 'all';

export type AppAbility = PureAbility<[Action, Subjects]>;

@Injectable()
export class CaslAbilityFactory {
  createForUser(user: User) {
    const { can, cannot, build } = new AbilityBuilder<AppAbility>(
      PureAbility as AbilityClass<AppAbility>,
    );

    if (user.roles.includes(Role.SUPER_ADMIN)) {
      // Super admin can do everything
      can(Action.Manage, 'all');
    } else if (user.roles.includes(Role.ADMIN)) {
      // Admin can manage most things
      can(Action.Manage, 'all');
      cannot(Action.Delete, User); // But cannot delete users
    } else if (user.roles.includes(Role.MODERATOR)) {
      // Moderator can manage articles
      can(Action.Manage, Article);
      can(Action.Read, Order);
      can(Action.Read, User);
    } else {
      // Regular user
      can(Action.Read, Article);

      // Can manage own orders
      can(Action.Create, Order);
      can([Action.Read, Action.Update], Order, { customerId: user.id });

      // Can read and update own profile
      can([Action.Read, Action.Update], User, { id: user.id });
    }

    return build({
      detectSubjectType: (item) =>
        item.constructor as ExtractSubjectType<Subjects>,
    });
  }
}
```

### CASL Guard

```typescript
// common/guards/casl.guard.ts
import { Injectable, CanActivate, ExecutionContext, ForbiddenException } from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { CaslAbilityFactory, Action } from '../authorization/casl/casl-ability.factory';

export const CHECK_ABILITY_KEY = 'checkAbility';

export interface AbilityMetadata {
  action: Action;
  subject: any;
}

export const CheckAbility = (action: Action, subject: any) =>
  SetMetadata(CHECK_ABILITY_KEY, { action, subject });

@Injectable()
export class CaslGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private caslAbilityFactory: CaslAbilityFactory,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const metadata = this.reflector.get<AbilityMetadata>(
      CHECK_ABILITY_KEY,
      context.getHandler(),
    );

    if (!metadata) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    if (!user) {
      throw new ForbiddenException('User not authenticated');
    }

    const ability = this.caslAbilityFactory.createForUser(user);
    const allowed = ability.can(metadata.action, metadata.subject);

    if (!allowed) {
      throw new ForbiddenException('Access denied');
    }

    return true;
  }
}
```

### CASL Usage

```typescript
// articles.controller.ts
@Controller('articles')
@UseGuards(CaslGuard)
export class ArticlesController {
  @Post()
  @CheckAbility(Action.Create, Article)
  create(@Body() dto: CreateArticleDto) {
    return this.articlesService.create(dto);
  }

  @Delete(':id')
  @CheckAbility(Action.Delete, Article)
  remove(@Param('id') id: string) {
    return this.articlesService.remove(id);
  }
}
```

## Permission-Based Access

```typescript
// common/enums/permission.enum.ts
export enum Permission {
  // User permissions
  USER_READ = 'user:read',
  USER_CREATE = 'user:create',
  USER_UPDATE = 'user:update',
  USER_DELETE = 'user:delete',

  // Order permissions
  ORDER_READ = 'order:read',
  ORDER_CREATE = 'order:create',
  ORDER_UPDATE = 'order:update',
  ORDER_DELETE = 'order:delete',

  // Admin permissions
  ADMIN_ACCESS = 'admin:access',
  SYSTEM_SETTINGS = 'system:settings',
}

// Role-Permission mapping
export const RolePermissions: Record<Role, Permission[]> = {
  [Role.USER]: [
    Permission.USER_READ,
    Permission.ORDER_READ,
    Permission.ORDER_CREATE,
  ],
  [Role.MODERATOR]: [
    ...RolePermissions[Role.USER],
    Permission.USER_CREATE,
    Permission.ORDER_UPDATE,
  ],
  [Role.ADMIN]: [
    ...RolePermissions[Role.MODERATOR],
    Permission.USER_UPDATE,
    Permission.ORDER_DELETE,
    Permission.ADMIN_ACCESS,
  ],
  [Role.SUPER_ADMIN]: Object.values(Permission),
};

// common/decorators/permissions.decorator.ts
export const PERMISSIONS_KEY = 'permissions';
export const RequirePermissions = (...permissions: Permission[]) =>
  SetMetadata(PERMISSIONS_KEY, permissions);

// common/guards/permissions.guard.ts
@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredPermissions = this.reflector.getAllAndOverride<Permission[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requiredPermissions || requiredPermissions.length === 0) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();

    if (!user || !user.roles) {
      return false;
    }

    const userPermissions = this.getUserPermissions(user.roles);

    return requiredPermissions.every((permission) =>
      userPermissions.includes(permission),
    );
  }

  private getUserPermissions(roles: Role[]): Permission[] {
    const permissions = new Set<Permission>();

    for (const role of roles) {
      const rolePerms = RolePermissions[role] || [];
      rolePerms.forEach((p) => permissions.add(p));
    }

    return Array.from(permissions);
  }
}
```

## Best Practices

1. **Defense in depth**: Combine multiple authorization layers
2. **Least privilege**: Grant minimum required permissions
3. **Explicit deny**: Default to deny if no rules match
4. **Audit logging**: Log authorization decisions
5. **Centralized policies**: Keep authorization logic in one place
6. **Test thoroughly**: Test all permission combinations

## Checklist

- [ ] Roles defined and documented
- [ ] Role hierarchy if needed
- [ ] Roles guard implemented
- [ ] Permission system if granular control needed
- [ ] ABAC for resource-level control
- [ ] CASL for complex rules
- [ ] Guards applied globally or per-controller
- [ ] Authorization tested
