---
name: nestjs-guard
description: NestJS guard template
applies_to: nestjs
category: template
---

# NestJS Guard Template

## Basic Guard

```typescript
// common/guards/{{guard}}.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
} from '@nestjs/common';
import { Observable } from 'rxjs';

@Injectable()
export class {{Guard}}Guard implements CanActivate {
  canActivate(
    context: ExecutionContext,
  ): boolean | Promise<boolean> | Observable<boolean> {
    const request = context.switchToHttp().getRequest();
    return this.validate(request);
  }

  private validate(request: any): boolean {
    // Add validation logic
    return true;
  }
}
```

## Role-Based Guard

```typescript
// common/guards/roles.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ROLES_KEY } from '../decorators/roles.decorator';
import { Role } from '../enums/role.enum';

@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.getAllAndOverride<Role[]>(ROLES_KEY, [
      context.getHandler(),
      context.getClass(),
    ]);

    if (!requiredRoles) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();

    if (!user || !user.roles) {
      return false;
    }

    return requiredRoles.some((role) => user.roles.includes(role));
  }
}

// common/decorators/roles.decorator.ts
import { SetMetadata } from '@nestjs/common';
import { Role } from '../enums/role.enum';

export const ROLES_KEY = 'roles';
export const Roles = (...roles: Role[]) => SetMetadata(ROLES_KEY, roles);

// common/enums/role.enum.ts
export enum Role {
  USER = 'user',
  ADMIN = 'admin',
  SUPER_ADMIN = 'super_admin',
}
```

## Permission-Based Guard

```typescript
// common/guards/permissions.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { PERMISSIONS_KEY } from '../decorators/permissions.decorator';

@Injectable()
export class PermissionsGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredPermissions = this.reflector.getAllAndOverride<string[]>(
      PERMISSIONS_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requiredPermissions) {
      return true;
    }

    const { user } = context.switchToHttp().getRequest();

    if (!user || !user.permissions) {
      return false;
    }

    return requiredPermissions.every((permission) =>
      user.permissions.includes(permission),
    );
  }
}

// common/decorators/permissions.decorator.ts
import { SetMetadata } from '@nestjs/common';

export const PERMISSIONS_KEY = 'permissions';
export const Permissions = (...permissions: string[]) =>
  SetMetadata(PERMISSIONS_KEY, permissions);
```

## Resource Ownership Guard

```typescript
// common/guards/owner.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { DataSource } from 'typeorm';

export interface OwnerCheckOptions {
  entity: Function;
  userField?: string;
  paramField?: string;
}

export const OWNER_KEY = 'owner';
export const CheckOwner = (options: OwnerCheckOptions) =>
  SetMetadata(OWNER_KEY, options);

@Injectable()
export class OwnerGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private dataSource: DataSource,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const options = this.reflector.get<OwnerCheckOptions>(
      OWNER_KEY,
      context.getHandler(),
    );

    if (!options) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const user = request.user;
    const resourceId = request.params[options.paramField || 'id'];

    if (!user || !resourceId) {
      return false;
    }

    const repository = this.dataSource.getRepository(options.entity);
    const resource = await repository.findOne({
      where: { id: resourceId },
    });

    if (!resource) {
      return true; // Let 404 be handled elsewhere
    }

    const userField = options.userField || 'userId';
    if (resource[userField] !== user.id) {
      throw new ForbiddenException('You do not own this resource');
    }

    return true;
  }
}
```

## API Key Guard

```typescript
// common/guards/api-key.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class ApiKeyGuard implements CanActivate {
  constructor(private configService: ConfigService) {}

  canActivate(context: ExecutionContext): boolean {
    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers['x-api-key'];

    if (!apiKey) {
      throw new UnauthorizedException('API key is required');
    }

    const validApiKeys = this.configService
      .get<string>('API_KEYS', '')
      .split(',');

    if (!validApiKeys.includes(apiKey)) {
      throw new UnauthorizedException('Invalid API key');
    }

    return true;
  }
}
```

## Rate Limit Guard

```typescript
// common/guards/rate-limit.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Inject } from '@nestjs/common';
import { Cache } from 'cache-manager';

export interface RateLimitOptions {
  limit: number;
  windowMs: number;
}

export const RATE_LIMIT_KEY = 'rateLimit';
export const RateLimit = (options: RateLimitOptions) =>
  SetMetadata(RATE_LIMIT_KEY, options);

@Injectable()
export class RateLimitGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const options = this.reflector.get<RateLimitOptions>(
      RATE_LIMIT_KEY,
      context.getHandler(),
    );

    if (!options) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const key = this.generateKey(request);

    const current = (await this.cacheManager.get<number>(key)) || 0;

    if (current >= options.limit) {
      throw new HttpException(
        'Too many requests',
        HttpStatus.TOO_MANY_REQUESTS,
      );
    }

    await this.cacheManager.set(key, current + 1, options.windowMs);

    return true;
  }

  private generateKey(request: any): string {
    const ip = request.ip;
    const userId = request.user?.id || 'anonymous';
    const path = request.path;
    return `rate-limit:${ip}:${userId}:${path}`;
  }
}
```

## Composite Guard

```typescript
// common/guards/composite.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  Type,
} from '@nestjs/common';
import { ModuleRef } from '@nestjs/core';

export function ComposeGuards(...guards: Type<CanActivate>[]) {
  @Injectable()
  class CompositeGuard implements CanActivate {
    constructor(private moduleRef: ModuleRef) {}

    async canActivate(context: ExecutionContext): Promise<boolean> {
      for (const Guard of guards) {
        const guard = this.moduleRef.get(Guard, { strict: false });
        const result = await guard.canActivate(context);
        if (!result) {
          return false;
        }
      }
      return true;
    }
  }

  return CompositeGuard;
}

// Usage
@UseGuards(ComposeGuards(JwtAuthGuard, RolesGuard, PermissionsGuard))
@Controller('admin')
export class AdminController {}
```

## Guard Usage Examples

```typescript
// Usage in controller
@Controller('{{module}}')
export class {{Module}}Controller {
  // Apply to entire controller
  @UseGuards(JwtAuthGuard)

  // Apply to specific method
  @Get()
  @UseGuards(RolesGuard)
  @Roles(Role.ADMIN)
  findAll() {}

  @Get(':id')
  @UseGuards(OwnerGuard)
  @CheckOwner({ entity: {{Entity}}, userField: 'userId' })
  findOne(@Param('id') id: string) {}

  @Post()
  @UseGuards(PermissionsGuard)
  @Permissions('{{module}}:create')
  create(@Body() dto: Create{{Entity}}Dto) {}

  @Patch(':id')
  @RateLimit({ limit: 10, windowMs: 60000 })
  @UseGuards(RateLimitGuard)
  update(@Param('id') id: string, @Body() dto: Update{{Entity}}Dto) {}
}
```

## Global Guard Registration

```typescript
// app.module.ts
import { APP_GUARD } from '@nestjs/core';

@Module({
  providers: [
    {
      provide: APP_GUARD,
      useClass: JwtAuthGuard,
    },
    {
      provide: APP_GUARD,
      useClass: RolesGuard,
    },
  ],
})
export class AppModule {}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{guard}}` | Guard name (lowercase, kebab-case) | api-key |
| `{{Guard}}` | Guard name (PascalCase) | ApiKey |
| `{{module}}` | Module name (lowercase) | users |
| `{{Module}}` | Module name (PascalCase) | Users |
| `{{Entity}}` | Entity name (PascalCase) | User |
