---
name: nestjs-exception-filters
description: Exception filters patterns in NestJS
applies_to: nestjs
category: error-handling
---

# NestJS Exception Filters

## Global Exception Filter

```typescript
// common/filters/global-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

export interface ErrorResponse {
  statusCode: number;
  message: string;
  error: string;
  timestamp: string;
  path: string;
  requestId?: string;
  details?: any;
}

@Catch()
export class GlobalExceptionFilter implements ExceptionFilter {
  private readonly logger = new Logger(GlobalExceptionFilter.name);

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const { status, message, error, details } = this.getErrorInfo(exception);

    const errorResponse: ErrorResponse = {
      statusCode: status,
      message,
      error,
      timestamp: new Date().toISOString(),
      path: request.url,
      requestId: request.headers['x-request-id'] as string,
      details: process.env.NODE_ENV === 'development' ? details : undefined,
    };

    // Log error
    this.logError(exception, request, status);

    response.status(status).json(errorResponse);
  }

  private getErrorInfo(exception: unknown): {
    status: number;
    message: string;
    error: string;
    details?: any;
  } {
    if (exception instanceof HttpException) {
      const response = exception.getResponse();
      const status = exception.getStatus();

      if (typeof response === 'object') {
        return {
          status,
          message: (response as any).message || exception.message,
          error: (response as any).error || HttpStatus[status],
          details: (response as any).details,
        };
      }

      return {
        status,
        message: response as string,
        error: HttpStatus[status],
      };
    }

    // Handle database errors
    if (this.isDatabaseError(exception)) {
      return this.handleDatabaseError(exception);
    }

    // Handle validation errors
    if (this.isValidationError(exception)) {
      return {
        status: HttpStatus.BAD_REQUEST,
        message: 'Validation failed',
        error: 'Bad Request',
        details: (exception as any).errors,
      };
    }

    // Default to internal server error
    return {
      status: HttpStatus.INTERNAL_SERVER_ERROR,
      message: 'Internal server error',
      error: 'Internal Server Error',
      details: exception instanceof Error ? exception.stack : undefined,
    };
  }

  private isDatabaseError(exception: unknown): boolean {
    return (
      exception instanceof Error &&
      ['QueryFailedError', 'EntityNotFoundError'].includes(exception.constructor.name)
    );
  }

  private handleDatabaseError(exception: any): {
    status: number;
    message: string;
    error: string;
  } {
    // Unique constraint violation
    if (exception.code === '23505') {
      return {
        status: HttpStatus.CONFLICT,
        message: 'Resource already exists',
        error: 'Conflict',
      };
    }

    // Foreign key violation
    if (exception.code === '23503') {
      return {
        status: HttpStatus.BAD_REQUEST,
        message: 'Referenced resource does not exist',
        error: 'Bad Request',
      };
    }

    return {
      status: HttpStatus.INTERNAL_SERVER_ERROR,
      message: 'Database error',
      error: 'Internal Server Error',
    };
  }

  private isValidationError(exception: unknown): boolean {
    return (
      exception instanceof Error &&
      exception.constructor.name === 'ValidationError'
    );
  }

  private logError(exception: unknown, request: Request, status: number): void {
    const message = exception instanceof Error ? exception.message : 'Unknown error';

    const logData = {
      method: request.method,
      url: request.url,
      status,
      message,
      userId: (request as any).user?.id,
      requestId: request.headers['x-request-id'],
    };

    if (status >= 500) {
      this.logger.error(logData, exception instanceof Error ? exception.stack : undefined);
    } else if (status >= 400) {
      this.logger.warn(logData);
    }
  }
}
```

## HTTP Exception Filter

```typescript
// common/filters/http-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
} from '@nestjs/common';
import { Response } from 'express';

@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const status = exception.getStatus();
    const exceptionResponse = exception.getResponse();

    const error =
      typeof exceptionResponse === 'object'
        ? exceptionResponse
        : { message: exceptionResponse };

    response.status(status).json({
      ...error,
      statusCode: status,
      timestamp: new Date().toISOString(),
    });
  }
}
```

## Domain Exception Filter

```typescript
// common/filters/domain-exception.filter.ts
import { ExceptionFilter, Catch, ArgumentsHost, HttpStatus } from '@nestjs/common';
import { Response } from 'express';
import { DomainException } from '../../domain/exceptions/domain.exception';

@Catch(DomainException)
export class DomainExceptionFilter implements ExceptionFilter {
  catch(exception: DomainException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    response.status(HttpStatus.UNPROCESSABLE_ENTITY).json({
      statusCode: HttpStatus.UNPROCESSABLE_ENTITY,
      error: 'Domain Error',
      message: exception.message,
      code: exception.code,
      timestamp: new Date().toISOString(),
    });
  }
}

// domain/exceptions/domain.exception.ts
export class DomainException extends Error {
  constructor(
    message: string,
    public readonly code?: string,
  ) {
    super(message);
    this.name = 'DomainException';
  }
}
```

## Custom Business Exceptions

```typescript
// common/exceptions/business.exception.ts
import { HttpException, HttpStatus } from '@nestjs/common';

export class BusinessException extends HttpException {
  constructor(
    message: string,
    public readonly code: string,
    status: HttpStatus = HttpStatus.BAD_REQUEST,
  ) {
    super({ message, code, error: 'Business Error' }, status);
  }
}

export class ResourceNotFoundException extends HttpException {
  constructor(resource: string, id: string) {
    super(
      {
        message: `${resource} with ID ${id} not found`,
        error: 'Not Found',
        resource,
        id,
      },
      HttpStatus.NOT_FOUND,
    );
  }
}

export class DuplicateResourceException extends HttpException {
  constructor(resource: string, field: string, value: string) {
    super(
      {
        message: `${resource} with ${field} '${value}' already exists`,
        error: 'Conflict',
        resource,
        field,
      },
      HttpStatus.CONFLICT,
    );
  }
}

export class InsufficientPermissionsException extends HttpException {
  constructor(action: string, resource: string) {
    super(
      {
        message: `Insufficient permissions to ${action} ${resource}`,
        error: 'Forbidden',
        action,
        resource,
      },
      HttpStatus.FORBIDDEN,
    );
  }
}
```

## Validation Exception Filter

```typescript
// common/filters/validation-exception.filter.ts
import { ExceptionFilter, Catch, ArgumentsHost, BadRequestException } from '@nestjs/common';
import { Response } from 'express';

@Catch(BadRequestException)
export class ValidationExceptionFilter implements ExceptionFilter {
  catch(exception: BadRequestException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const exceptionResponse = exception.getResponse() as any;

    // Check if it's a validation error
    if (Array.isArray(exceptionResponse.message)) {
      const validationErrors = this.formatValidationErrors(exceptionResponse.message);

      response.status(400).json({
        statusCode: 400,
        error: 'Validation Error',
        message: 'Validation failed',
        details: validationErrors,
        timestamp: new Date().toISOString(),
      });
      return;
    }

    response.status(400).json({
      statusCode: 400,
      error: 'Bad Request',
      message: exceptionResponse.message || exception.message,
      timestamp: new Date().toISOString(),
    });
  }

  private formatValidationErrors(messages: string[]): Record<string, string[]> {
    const errors: Record<string, string[]> = {};

    for (const message of messages) {
      // Parse validation message format: "field constraint message"
      const match = message.match(/^(\w+)\s+(.+)$/);
      if (match) {
        const [, field, error] = match;
        if (!errors[field]) {
          errors[field] = [];
        }
        errors[field].push(error);
      } else {
        if (!errors['_general']) {
          errors['_general'] = [];
        }
        errors['_general'].push(message);
      }
    }

    return errors;
  }
}
```

## Register Filters

```typescript
// main.ts
import { NestFactory } from '@nestjs/core';
import { GlobalExceptionFilter } from './common/filters/global-exception.filter';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Global exception filter
  app.useGlobalFilters(new GlobalExceptionFilter());

  await app.listen(3000);
}

// Or via module
// app.module.ts
import { APP_FILTER } from '@nestjs/core';

@Module({
  providers: [
    {
      provide: APP_FILTER,
      useClass: GlobalExceptionFilter,
    },
  ],
})
export class AppModule {}
```

## Filter Order

Filters are executed in reverse order (last registered runs first for catch-all):

```typescript
// Most specific first
app.useGlobalFilters(
  new GlobalExceptionFilter(),     // Catch all - runs last
  new HttpExceptionFilter(),       // HTTP exceptions
  new DomainExceptionFilter(),     // Domain exceptions
  new ValidationExceptionFilter(), // Validation - runs first
);
```

## Best Practices

1. **Consistent format**: Same error response structure
2. **Appropriate status codes**: Use correct HTTP status
3. **Hide internals**: No stack traces in production
4. **Log errors**: Log for debugging, monitoring
5. **Specific filters**: Domain-specific exception handling
6. **Custom exceptions**: Business-meaningful errors

## Checklist

- [ ] Global exception filter
- [ ] Custom business exceptions
- [ ] Validation error formatting
- [ ] Database error handling
- [ ] Proper logging
- [ ] Environment-aware details
- [ ] Consistent response format
