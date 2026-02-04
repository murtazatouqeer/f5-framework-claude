---
name: nestjs-interceptor
description: NestJS interceptor template
applies_to: nestjs
category: template
---

# NestJS Interceptor Template

## Basic Interceptor

```typescript
// common/interceptors/{{interceptor}}.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap, map } from 'rxjs/operators';

@Injectable()
export class {{Interceptor}}Interceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const now = Date.now();

    return next.handle().pipe(
      tap(() => console.log(`After... ${Date.now() - now}ms`)),
    );
  }
}
```

## Response Transform Interceptor

```typescript
// common/interceptors/transform-response.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface Response<T> {
  success: boolean;
  data: T;
  timestamp: string;
  path: string;
}

@Injectable()
export class TransformResponseInterceptor<T>
  implements NestInterceptor<T, Response<T>>
{
  intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Observable<Response<T>> {
    const request = context.switchToHttp().getRequest();

    return next.handle().pipe(
      map((data) => ({
        success: true,
        data,
        timestamp: new Date().toISOString(),
        path: request.url,
      })),
    );
  }
}
```

## Logging Interceptor

```typescript
// common/interceptors/logging.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Logger,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

@Injectable()
export class LoggingInterceptor implements NestInterceptor {
  private readonly logger = new Logger(LoggingInterceptor.name);

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url, body, user } = request;
    const now = Date.now();

    this.logger.log(
      `Incoming Request: ${method} ${url} - User: ${user?.id || 'anonymous'}`,
    );

    return next.handle().pipe(
      tap({
        next: (data) => {
          const response = context.switchToHttp().getResponse();
          const delay = Date.now() - now;

          this.logger.log(
            `Outgoing Response: ${method} ${url} - Status: ${response.statusCode} - ${delay}ms`,
          );
        },
        error: (error) => {
          const delay = Date.now() - now;
          this.logger.error(
            `Request Error: ${method} ${url} - ${error.message} - ${delay}ms`,
          );
        },
      }),
    );
  }
}
```

## Timeout Interceptor

```typescript
// common/interceptors/timeout.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  RequestTimeoutException,
} from '@nestjs/common';
import { Observable, throwError, TimeoutError } from 'rxjs';
import { catchError, timeout } from 'rxjs/operators';
import { Reflector } from '@nestjs/core';

export const TIMEOUT_KEY = 'timeout';
export const SetTimeout = (ms: number) => SetMetadata(TIMEOUT_KEY, ms);

@Injectable()
export class TimeoutInterceptor implements NestInterceptor {
  constructor(private reflector: Reflector) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const timeoutMs =
      this.reflector.get<number>(TIMEOUT_KEY, context.getHandler()) || 30000;

    return next.handle().pipe(
      timeout(timeoutMs),
      catchError((err) => {
        if (err instanceof TimeoutError) {
          return throwError(() => new RequestTimeoutException());
        }
        return throwError(() => err);
      }),
    );
  }
}
```

## Cache Interceptor

```typescript
// common/interceptors/cache.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  Inject,
} from '@nestjs/common';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { Cache } from 'cache-manager';
import { Reflector } from '@nestjs/core';

export const CACHE_TTL_KEY = 'cacheTTL';
export const CacheTTL = (ttl: number) => SetMetadata(CACHE_TTL_KEY, ttl);

@Injectable()
export class CustomCacheInterceptor implements NestInterceptor {
  constructor(
    @Inject(CACHE_MANAGER) private cacheManager: Cache,
    private reflector: Reflector,
  ) {}

  async intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Promise<Observable<any>> {
    const request = context.switchToHttp().getRequest();

    // Only cache GET requests
    if (request.method !== 'GET') {
      return next.handle();
    }

    const ttl =
      this.reflector.get<number>(CACHE_TTL_KEY, context.getHandler()) || 60000;
    const cacheKey = this.generateCacheKey(request);

    const cachedResponse = await this.cacheManager.get(cacheKey);
    if (cachedResponse) {
      return of(cachedResponse);
    }

    return next.handle().pipe(
      tap((response) => {
        this.cacheManager.set(cacheKey, response, ttl);
      }),
    );
  }

  private generateCacheKey(request: any): string {
    const { url, query, user } = request;
    const userId = user?.id || 'public';
    return `cache:${userId}:${url}:${JSON.stringify(query)}`;
  }
}
```

## Serialize Interceptor

```typescript
// common/interceptors/serialize.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { plainToInstance, ClassTransformOptions } from 'class-transformer';
import { Reflector } from '@nestjs/core';

export const SERIALIZE_KEY = 'serialize';
export const Serialize = (dto: any, options?: ClassTransformOptions) =>
  SetMetadata(SERIALIZE_KEY, { dto, options });

@Injectable()
export class SerializeInterceptor implements NestInterceptor {
  constructor(private reflector: Reflector) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const serializeOptions = this.reflector.get<{
      dto: any;
      options?: ClassTransformOptions;
    }>(SERIALIZE_KEY, context.getHandler());

    if (!serializeOptions) {
      return next.handle();
    }

    return next.handle().pipe(
      map((data) => {
        if (Array.isArray(data)) {
          return data.map((item) =>
            plainToInstance(serializeOptions.dto, item, {
              excludeExtraneousValues: true,
              ...serializeOptions.options,
            }),
          );
        }

        // Handle paginated response
        if (data && data.items && Array.isArray(data.items)) {
          return {
            ...data,
            items: data.items.map((item) =>
              plainToInstance(serializeOptions.dto, item, {
                excludeExtraneousValues: true,
                ...serializeOptions.options,
              }),
            ),
          };
        }

        return plainToInstance(serializeOptions.dto, data, {
          excludeExtraneousValues: true,
          ...serializeOptions.options,
        });
      }),
    );
  }
}
```

## Error Mapping Interceptor

```typescript
// common/interceptors/error-mapping.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
  HttpException,
  HttpStatus,
} from '@nestjs/common';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable()
export class ErrorMappingInterceptor implements NestInterceptor {
  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    return next.handle().pipe(
      catchError((error) => {
        // Map TypeORM errors
        if (error.name === 'QueryFailedError') {
          if (error.code === '23505') {
            return throwError(
              () =>
                new HttpException(
                  'Resource already exists',
                  HttpStatus.CONFLICT,
                ),
            );
          }
          if (error.code === '23503') {
            return throwError(
              () =>
                new HttpException(
                  'Referenced resource not found',
                  HttpStatus.BAD_REQUEST,
                ),
            );
          }
        }

        // Map validation errors
        if (error.name === 'ValidationError') {
          return throwError(
            () =>
              new HttpException(
                { message: 'Validation failed', errors: error.errors },
                HttpStatus.BAD_REQUEST,
              ),
          );
        }

        return throwError(() => error);
      }),
    );
  }
}
```

## Audit Log Interceptor

```typescript
// common/interceptors/audit-log.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { AuditLogService } from '../services/audit-log.service';

@Injectable()
export class AuditLogInterceptor implements NestInterceptor {
  constructor(private auditLogService: AuditLogService) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const { method, url, body, user, params, ip } = request;

    // Only log mutation operations
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      return next.handle().pipe(
        tap({
          next: (response) => {
            this.auditLogService.log({
              userId: user?.id,
              action: `${method} ${url}`,
              resourceId: params?.id || response?.id,
              resourceType: this.extractResourceType(url),
              changes: this.sanitizeBody(body),
              ip,
              timestamp: new Date(),
              success: true,
            });
          },
          error: (error) => {
            this.auditLogService.log({
              userId: user?.id,
              action: `${method} ${url}`,
              resourceId: params?.id,
              resourceType: this.extractResourceType(url),
              changes: this.sanitizeBody(body),
              ip,
              timestamp: new Date(),
              success: false,
              errorMessage: error.message,
            });
          },
        }),
      );
    }

    return next.handle();
  }

  private extractResourceType(url: string): string {
    const parts = url.split('/').filter(Boolean);
    return parts[0] || 'unknown';
  }

  private sanitizeBody(body: any): any {
    if (!body) return null;
    const { password, token, secret, ...safe } = body;
    return safe;
  }
}
```

## Global Interceptor Registration

```typescript
// app.module.ts
import { APP_INTERCEPTOR } from '@nestjs/core';

@Module({
  providers: [
    {
      provide: APP_INTERCEPTOR,
      useClass: LoggingInterceptor,
    },
    {
      provide: APP_INTERCEPTOR,
      useClass: TransformResponseInterceptor,
    },
    {
      provide: APP_INTERCEPTOR,
      useClass: TimeoutInterceptor,
    },
  ],
})
export class AppModule {}
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{interceptor}}` | Interceptor name (lowercase, kebab-case) | transform-response |
| `{{Interceptor}}` | Interceptor name (PascalCase) | TransformResponse |
