---
name: nestjs-filter
description: NestJS exception filter template
applies_to: nestjs
category: template
---

# NestJS Exception Filter Template

## Basic Exception Filter

```typescript
// common/filters/{{filter}}.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  HttpStatus,
  Logger,
} from '@nestjs/common';
import { Request, Response } from 'express';

@Catch()
export class {{Filter}}Filter implements ExceptionFilter {
  private readonly logger = new Logger({{Filter}}Filter.name);

  catch(exception: unknown, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    const { status, message, error } = this.getExceptionDetails(exception);

    const errorResponse = {
      statusCode: status,
      message,
      error,
      timestamp: new Date().toISOString(),
      path: request.url,
    };

    this.logger.error(
      `${request.method} ${request.url} - ${status} - ${message}`,
      exception instanceof Error ? exception.stack : undefined,
    );

    response.status(status).json(errorResponse);
  }

  private getExceptionDetails(exception: unknown): {
    status: number;
    message: string;
    error: string;
  } {
    if (exception instanceof HttpException) {
      const response = exception.getResponse();
      const status = exception.getStatus();

      if (typeof response === 'object') {
        return {
          status,
          message: (response as any).message || exception.message,
          error: (response as any).error || HttpStatus[status],
        };
      }

      return {
        status,
        message: response as string,
        error: HttpStatus[status],
      };
    }

    return {
      status: HttpStatus.INTERNAL_SERVER_ERROR,
      message: 'Internal server error',
      error: 'Internal Server Error',
    };
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
import { Response, Request } from 'express';

@Catch(HttpException)
export class HttpExceptionFilter implements ExceptionFilter {
  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();
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
      path: request.url,
      requestId: request.headers['x-request-id'],
    });
  }
}
```

## Validation Exception Filter

```typescript
// common/filters/validation-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  BadRequestException,
} from '@nestjs/common';
import { Response } from 'express';

interface ValidationErrorResponse {
  message: string | string[];
  error: string;
  statusCode: number;
}

@Catch(BadRequestException)
export class ValidationExceptionFilter implements ExceptionFilter {
  catch(exception: BadRequestException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const exceptionResponse = exception.getResponse() as ValidationErrorResponse;

    // Check if it's a validation error (class-validator)
    if (Array.isArray(exceptionResponse.message)) {
      const formattedErrors = this.formatValidationErrors(
        exceptionResponse.message,
      );

      response.status(400).json({
        statusCode: 400,
        error: 'Validation Error',
        message: 'Validation failed',
        details: formattedErrors,
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

  private formatValidationErrors(
    messages: string[],
  ): Record<string, string[]> {
    const errors: Record<string, string[]> = {};

    for (const message of messages) {
      // Try to extract field name from message
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

## Database Exception Filter

```typescript
// common/filters/database-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpStatus,
} from '@nestjs/common';
import { Response } from 'express';
import { QueryFailedError, EntityNotFoundError } from 'typeorm';

@Catch(QueryFailedError, EntityNotFoundError)
export class DatabaseExceptionFilter implements ExceptionFilter {
  catch(
    exception: QueryFailedError | EntityNotFoundError,
    host: ArgumentsHost,
  ) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    const { status, message, error } = this.getErrorDetails(exception);

    response.status(status).json({
      statusCode: status,
      error,
      message,
      timestamp: new Date().toISOString(),
    });
  }

  private getErrorDetails(
    exception: QueryFailedError | EntityNotFoundError,
  ): { status: number; message: string; error: string } {
    if (exception instanceof EntityNotFoundError) {
      return {
        status: HttpStatus.NOT_FOUND,
        message: 'Resource not found',
        error: 'Not Found',
      };
    }

    // PostgreSQL error codes
    const queryError = exception as any;

    switch (queryError.code) {
      case '23505': // Unique violation
        return {
          status: HttpStatus.CONFLICT,
          message: 'Resource already exists',
          error: 'Conflict',
        };
      case '23503': // Foreign key violation
        return {
          status: HttpStatus.BAD_REQUEST,
          message: 'Referenced resource does not exist',
          error: 'Bad Request',
        };
      case '23502': // Not null violation
        return {
          status: HttpStatus.BAD_REQUEST,
          message: 'Required field is missing',
          error: 'Bad Request',
        };
      case '22P02': // Invalid text representation
        return {
          status: HttpStatus.BAD_REQUEST,
          message: 'Invalid input format',
          error: 'Bad Request',
        };
      default:
        return {
          status: HttpStatus.INTERNAL_SERVER_ERROR,
          message: 'Database error occurred',
          error: 'Internal Server Error',
        };
    }
  }
}
```

## Custom Business Exception Filter

```typescript
// common/filters/business-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpStatus,
} from '@nestjs/common';
import { Response, Request } from 'express';

// Custom business exception
export class BusinessException extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode: number = HttpStatus.UNPROCESSABLE_ENTITY,
    public readonly details?: any,
  ) {
    super(message);
    this.name = 'BusinessException';
  }
}

@Catch(BusinessException)
export class BusinessExceptionFilter implements ExceptionFilter {
  catch(exception: BusinessException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest<Request>();

    response.status(exception.statusCode).json({
      statusCode: exception.statusCode,
      error: 'Business Error',
      code: exception.code,
      message: exception.message,
      details: exception.details,
      timestamp: new Date().toISOString(),
      path: request.url,
    });
  }
}

// Usage
throw new BusinessException(
  'Insufficient balance',
  'INSUFFICIENT_BALANCE',
  HttpStatus.UNPROCESSABLE_ENTITY,
  { currentBalance: 100, requiredAmount: 150 },
);
```

## Throttle Exception Filter

```typescript
// common/filters/throttle-exception.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpStatus,
} from '@nestjs/common';
import { ThrottlerException } from '@nestjs/throttler';
import { Response } from 'express';

@Catch(ThrottlerException)
export class ThrottleExceptionFilter implements ExceptionFilter {
  catch(exception: ThrottlerException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();

    response.status(HttpStatus.TOO_MANY_REQUESTS).json({
      statusCode: HttpStatus.TOO_MANY_REQUESTS,
      error: 'Too Many Requests',
      message: 'Rate limit exceeded. Please try again later.',
      retryAfter: response.getHeader('Retry-After'),
      timestamp: new Date().toISOString(),
    });
  }
}
```

## WebSocket Exception Filter

```typescript
// common/filters/ws-exception.filter.ts
import { Catch, ArgumentsHost } from '@nestjs/common';
import { BaseWsExceptionFilter, WsException } from '@nestjs/websockets';
import { Socket } from 'socket.io';

@Catch()
export class WsExceptionFilter extends BaseWsExceptionFilter {
  catch(exception: unknown, host: ArgumentsHost) {
    const client = host.switchToWs().getClient<Socket>();

    const error =
      exception instanceof WsException
        ? exception.getError()
        : { message: 'Internal server error' };

    const errorResponse = {
      event: 'error',
      data: {
        error: typeof error === 'string' ? { message: error } : error,
        timestamp: new Date().toISOString(),
      },
    };

    client.emit('exception', errorResponse);
  }
}
```

## Filter with Dependency Injection

```typescript
// common/filters/custom.filter.ts
import {
  ExceptionFilter,
  Catch,
  ArgumentsHost,
  HttpException,
  Inject,
} from '@nestjs/common';
import { Response } from 'express';
import { LoggerService } from '../services/logger.service';
import { ErrorTrackingService } from '../services/error-tracking.service';

@Catch(HttpException)
export class CustomFilter implements ExceptionFilter {
  constructor(
    @Inject(LoggerService) private logger: LoggerService,
    @Inject(ErrorTrackingService) private errorTracking: ErrorTrackingService,
  ) {}

  catch(exception: HttpException, host: ArgumentsHost) {
    const ctx = host.switchToHttp();
    const response = ctx.getResponse<Response>();
    const request = ctx.getRequest();
    const status = exception.getStatus();

    // Log error
    this.logger.error({
      message: exception.message,
      stack: exception.stack,
      url: request.url,
      method: request.method,
      userId: request.user?.id,
    });

    // Track error in external service
    if (status >= 500) {
      this.errorTracking.captureException(exception, {
        user: request.user,
        request: {
          url: request.url,
          method: request.method,
          body: request.body,
        },
      });
    }

    response.status(status).json({
      statusCode: status,
      message: exception.message,
      timestamp: new Date().toISOString(),
    });
  }
}
```

## Global Filter Registration

```typescript
// app.module.ts
import { APP_FILTER } from '@nestjs/core';

@Module({
  providers: [
    // Order matters: most generic last
    {
      provide: APP_FILTER,
      useClass: GlobalExceptionFilter,
    },
    {
      provide: APP_FILTER,
      useClass: HttpExceptionFilter,
    },
    {
      provide: APP_FILTER,
      useClass: ValidationExceptionFilter,
    },
    {
      provide: APP_FILTER,
      useClass: DatabaseExceptionFilter,
    },
  ],
})
export class AppModule {}

// Or in main.ts
app.useGlobalFilters(
  new GlobalExceptionFilter(),
  new HttpExceptionFilter(),
  new ValidationExceptionFilter(),
);
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{filter}}` | Filter name (lowercase, kebab-case) | global-exception |
| `{{Filter}}` | Filter name (PascalCase) | GlobalException |
