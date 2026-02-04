---
name: nestjs-guards-strategies
description: Guard patterns and strategies in NestJS
applies_to: nestjs
category: security
---

# NestJS Guards & Strategies

## Guard Fundamentals

Guards determine if a request should be handled by the route handler.
They implement the `CanActivate` interface.

```typescript
import { Injectable, CanActivate, ExecutionContext } from '@nestjs/common';

@Injectable()
export class ExampleGuard implements CanActivate {
  canActivate(context: ExecutionContext): boolean | Promise<boolean> {
    const request = context.switchToHttp().getRequest();
    // Authorization logic here
    return true;
  }
}
```

## Common Guard Patterns

### API Key Guard

```typescript
// common/guards/api-key.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  UnauthorizedException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Reflector } from '@nestjs/core';

export const API_KEY_HEADER = 'x-api-key';
export const REQUIRE_API_KEY = 'requireApiKey';
export const RequireApiKey = () => SetMetadata(REQUIRE_API_KEY, true);

@Injectable()
export class ApiKeyGuard implements CanActivate {
  constructor(
    private configService: ConfigService,
    private reflector: Reflector,
  ) {}

  canActivate(context: ExecutionContext): boolean {
    const requireApiKey = this.reflector.getAllAndOverride<boolean>(
      REQUIRE_API_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requireApiKey) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const apiKey = request.headers[API_KEY_HEADER];

    if (!apiKey) {
      throw new UnauthorizedException('API key is required');
    }

    const validApiKeys = this.configService.get<string>('API_KEYS')?.split(',') || [];

    if (!validApiKeys.includes(apiKey)) {
      throw new UnauthorizedException('Invalid API key');
    }

    return true;
  }
}

// Usage
@RequireApiKey()
@Get('external')
externalEndpoint() {
  return { data: 'protected' };
}
```

### Throttle Guard

```typescript
// common/guards/throttle.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { Redis } from 'ioredis';
import { InjectRedis } from '@liaoliaots/nestjs-redis';

export const THROTTLE_KEY = 'throttle';

export interface ThrottleConfig {
  limit: number;  // Max requests
  ttl: number;    // Time window in seconds
  keyPrefix?: string;
}

export const Throttle = (limit: number, ttl: number, keyPrefix?: string) =>
  SetMetadata(THROTTLE_KEY, { limit, ttl, keyPrefix });

@Injectable()
export class ThrottleGuard implements CanActivate {
  private defaultConfig: ThrottleConfig = {
    limit: 100,
    ttl: 60,
  };

  constructor(
    private reflector: Reflector,
    @InjectRedis() private redis: Redis,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const config = this.reflector.getAllAndOverride<ThrottleConfig>(
      THROTTLE_KEY,
      [context.getHandler(), context.getClass()],
    ) || this.defaultConfig;

    const request = context.switchToHttp().getRequest();
    const key = this.generateKey(request, config);

    const current = await this.redis.incr(key);

    if (current === 1) {
      await this.redis.expire(key, config.ttl);
    }

    // Set rate limit headers
    const response = context.switchToHttp().getResponse();
    response.setHeader('X-RateLimit-Limit', config.limit);
    response.setHeader('X-RateLimit-Remaining', Math.max(0, config.limit - current));

    if (current > config.limit) {
      const ttl = await this.redis.ttl(key);
      response.setHeader('X-RateLimit-Reset', ttl);
      throw new HttpException(
        {
          statusCode: HttpStatus.TOO_MANY_REQUESTS,
          message: 'Too many requests',
          retryAfter: ttl,
        },
        HttpStatus.TOO_MANY_REQUESTS,
      );
    }

    return true;
  }

  private generateKey(request: any, config: ThrottleConfig): string {
    const prefix = config.keyPrefix || 'throttle';
    const identifier = request.user?.id || request.ip;
    const path = request.route?.path || request.url;
    return `${prefix}:${identifier}:${path}`;
  }
}

// Usage
@Throttle(5, 60) // 5 requests per 60 seconds
@Post('login')
async login(@Body() dto: LoginDto) {}

@Throttle(100, 60, 'api') // Custom prefix
@Get('data')
async getData() {}
```

### Resource Owner Guard

```typescript
// common/guards/owner.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
  NotFoundException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { ModuleRef } from '@nestjs/core';

export const OWNER_CHECK_KEY = 'ownerCheck';

export interface OwnerCheckConfig {
  service: string;
  idParam?: string;
  ownerField?: string;
  allowAdmins?: boolean;
}

export const CheckOwner = (config: OwnerCheckConfig) =>
  SetMetadata(OWNER_CHECK_KEY, config);

@Injectable()
export class OwnerGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private moduleRef: ModuleRef,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const config = this.reflector.get<OwnerCheckConfig>(
      OWNER_CHECK_KEY,
      context.getHandler(),
    );

    if (!config) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    if (!user) {
      throw new ForbiddenException('User not authenticated');
    }

    // Allow admins if configured
    if (config.allowAdmins && user.roles?.includes('admin')) {
      return true;
    }

    const resourceId = request.params[config.idParam || 'id'];

    if (!resourceId) {
      return true; // No resource to check
    }

    const service = this.moduleRef.get(config.service, { strict: false });

    if (!service || typeof service.findById !== 'function') {
      throw new Error(`Service ${config.service} not found or missing findById`);
    }

    const resource = await service.findById(resourceId);

    if (!resource) {
      throw new NotFoundException('Resource not found');
    }

    const ownerField = config.ownerField || 'userId';
    const ownerId = resource[ownerField];

    if (ownerId !== user.id) {
      throw new ForbiddenException('You do not own this resource');
    }

    return true;
  }
}

// Usage
@Get(':id')
@CheckOwner({
  service: 'OrdersService',
  idParam: 'id',
  ownerField: 'customerId',
  allowAdmins: true,
})
findOne(@Param('id') id: string) {
  return this.ordersService.findOne(id);
}
```

### IP Whitelist Guard

```typescript
// common/guards/ip-whitelist.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
} from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { Reflector } from '@nestjs/core';

export const IP_WHITELIST_KEY = 'ipWhitelist';
export const RequireWhitelistedIP = () => SetMetadata(IP_WHITELIST_KEY, true);

@Injectable()
export class IpWhitelistGuard implements CanActivate {
  private whitelist: string[];

  constructor(
    private configService: ConfigService,
    private reflector: Reflector,
  ) {
    this.whitelist = this.configService
      .get<string>('IP_WHITELIST', '')
      .split(',')
      .filter(Boolean);
  }

  canActivate(context: ExecutionContext): boolean {
    const requireWhitelist = this.reflector.getAllAndOverride<boolean>(
      IP_WHITELIST_KEY,
      [context.getHandler(), context.getClass()],
    );

    if (!requireWhitelist) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const clientIp = this.getClientIp(request);

    if (!this.whitelist.includes(clientIp)) {
      throw new ForbiddenException('IP address not allowed');
    }

    return true;
  }

  private getClientIp(request: any): string {
    return (
      request.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
      request.headers['x-real-ip'] ||
      request.socket?.remoteAddress ||
      request.ip
    );
  }
}
```

### Feature Flag Guard

```typescript
// common/guards/feature-flag.guard.ts
import {
  Injectable,
  CanActivate,
  ExecutionContext,
  ForbiddenException,
} from '@nestjs/common';
import { Reflector } from '@nestjs/core';
import { FeatureFlagService } from '../services/feature-flag.service';

export const FEATURE_FLAG_KEY = 'featureFlag';
export const RequireFeature = (flag: string) => SetMetadata(FEATURE_FLAG_KEY, flag);

@Injectable()
export class FeatureFlagGuard implements CanActivate {
  constructor(
    private reflector: Reflector,
    private featureFlagService: FeatureFlagService,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    const requiredFlag = this.reflector.get<string>(
      FEATURE_FLAG_KEY,
      context.getHandler(),
    );

    if (!requiredFlag) {
      return true;
    }

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    const isEnabled = await this.featureFlagService.isEnabled(
      requiredFlag,
      user?.id,
    );

    if (!isEnabled) {
      throw new ForbiddenException('Feature not available');
    }

    return true;
  }
}

// Usage
@RequireFeature('new-checkout')
@Post('checkout/v2')
async newCheckout(@Body() dto: CheckoutDto) {}
```

## Passport Strategies

### OAuth2 Strategy (Google)

```typescript
// auth/strategies/google.strategy.ts
import { Injectable } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { Strategy, VerifyCallback, Profile } from 'passport-google-oauth20';
import { ConfigService } from '@nestjs/config';
import { AuthService } from '../auth.service';

@Injectable()
export class GoogleStrategy extends PassportStrategy(Strategy, 'google') {
  constructor(
    private configService: ConfigService,
    private authService: AuthService,
  ) {
    super({
      clientID: configService.get('GOOGLE_CLIENT_ID'),
      clientSecret: configService.get('GOOGLE_CLIENT_SECRET'),
      callbackURL: configService.get('GOOGLE_CALLBACK_URL'),
      scope: ['email', 'profile'],
    });
  }

  async validate(
    accessToken: string,
    refreshToken: string,
    profile: Profile,
    done: VerifyCallback,
  ): Promise<any> {
    const { emails, displayName, photos } = profile;

    const user = await this.authService.validateOAuthUser({
      email: emails[0].value,
      name: displayName,
      picture: photos?.[0]?.value,
      provider: 'google',
      providerId: profile.id,
    });

    done(null, user);
  }
}

// auth/auth.controller.ts
@Get('google')
@UseGuards(AuthGuard('google'))
googleAuth() {
  // Redirects to Google
}

@Get('google/callback')
@UseGuards(AuthGuard('google'))
async googleAuthCallback(@CurrentUser() user: User) {
  return this.authService.login(user);
}
```

### API Key Strategy

```typescript
// auth/strategies/api-key.strategy.ts
import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { Strategy } from 'passport-http-header-strategy';
import { ApiKeyService } from '../services/api-key.service';

@Injectable()
export class ApiKeyStrategy extends PassportStrategy(Strategy, 'api-key') {
  constructor(private apiKeyService: ApiKeyService) {
    super({
      header: 'x-api-key',
      param: 'api_key',
    });
  }

  async validate(apiKey: string) {
    const client = await this.apiKeyService.validateApiKey(apiKey);

    if (!client) {
      throw new UnauthorizedException('Invalid API key');
    }

    return client;
  }
}
```

## Combining Guards

```typescript
// Multiple guards - all must pass
@UseGuards(JwtAuthGuard, RolesGuard, ThrottleGuard)
@Controller('admin')
export class AdminController {}

// Guard composition
@Injectable()
export class CompositeGuard implements CanActivate {
  constructor(
    private jwtGuard: JwtAuthGuard,
    private rolesGuard: RolesGuard,
  ) {}

  async canActivate(context: ExecutionContext): Promise<boolean> {
    // JWT first
    const jwtResult = await this.jwtGuard.canActivate(context);
    if (!jwtResult) return false;

    // Then roles
    return this.rolesGuard.canActivate(context);
  }
}
```

## Global Guards

```typescript
// app.module.ts
import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';

@Module({
  providers: [
    // Order matters - first registered runs first
    {
      provide: APP_GUARD,
      useClass: ThrottleGuard,
    },
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

## Testing Guards

```typescript
describe('RolesGuard', () => {
  let guard: RolesGuard;
  let reflector: Reflector;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [RolesGuard, Reflector],
    }).compile();

    guard = module.get<RolesGuard>(RolesGuard);
    reflector = module.get<Reflector>(Reflector);
  });

  it('should allow when no roles required', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue(null);

    const context = createMockExecutionContext();
    expect(guard.canActivate(context)).toBe(true);
  });

  it('should allow user with required role', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue([Role.ADMIN]);

    const context = createMockExecutionContext({
      user: { roles: [Role.ADMIN] },
    });

    expect(guard.canActivate(context)).toBe(true);
  });

  it('should deny user without required role', () => {
    jest.spyOn(reflector, 'getAllAndOverride').mockReturnValue([Role.ADMIN]);

    const context = createMockExecutionContext({
      user: { roles: [Role.USER] },
    });

    expect(guard.canActivate(context)).toBe(false);
  });
});

function createMockExecutionContext(request: any = {}): ExecutionContext {
  return {
    switchToHttp: () => ({
      getRequest: () => request,
    }),
    getHandler: () => ({}),
    getClass: () => ({}),
  } as ExecutionContext;
}
```

## Best Practices

1. **Single Responsibility**: Each guard handles one concern
2. **Order Matters**: Authentication before authorization
3. **Fail Fast**: Return early for efficiency
4. **Clear Errors**: Provide meaningful error messages
5. **Test Thoroughly**: Test all guard combinations
6. **Use Decorators**: Combine decorators for readability

## Checklist

- [ ] Authentication guards (JWT, API Key, OAuth)
- [ ] Authorization guards (Roles, Permissions)
- [ ] Rate limiting implemented
- [ ] Resource ownership checks
- [ ] Global guards configured
- [ ] Guards properly ordered
- [ ] Error messages clear
- [ ] Guards unit tested
