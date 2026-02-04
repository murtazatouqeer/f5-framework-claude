---
name: nestjs-error-responses
description: Standardized error responses in NestJS
applies_to: nestjs
category: error-handling
---

# Standardized Error Responses

## Response Format

```typescript
// common/interfaces/error-response.interface.ts
export interface ErrorResponse {
  statusCode: number;
  error: string;
  message: string;
  timestamp: string;
  path: string;
  requestId?: string;
  code?: string;        // Business error code
  details?: any;        // Additional details
  errors?: ValidationError[]; // Validation errors
}

export interface ValidationError {
  field: string;
  value: any;
  constraints: string[];
}

// Example responses
// 400 Bad Request
{
  "statusCode": 400,
  "error": "Bad Request",
  "message": "Validation failed",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "path": "/api/users",
  "errors": [
    {
      "field": "email",
      "value": "invalid",
      "constraints": ["email must be a valid email address"]
    }
  ]
}

// 404 Not Found
{
  "statusCode": 404,
  "error": "Not Found",
  "message": "User with ID 123 not found",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "path": "/api/users/123",
  "code": "USER_NOT_FOUND"
}

// 409 Conflict
{
  "statusCode": 409,
  "error": "Conflict",
  "message": "User with email user@example.com already exists",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "path": "/api/users",
  "code": "DUPLICATE_EMAIL"
}
```

## Error Response Builder

```typescript
// common/utils/error-response.builder.ts
export class ErrorResponseBuilder {
  private response: Partial<ErrorResponse> = {};

  static create(): ErrorResponseBuilder {
    return new ErrorResponseBuilder();
  }

  statusCode(code: number): this {
    this.response.statusCode = code;
    return this;
  }

  error(error: string): this {
    this.response.error = error;
    return this;
  }

  message(message: string): this {
    this.response.message = message;
    return this;
  }

  code(code: string): this {
    this.response.code = code;
    return this;
  }

  path(path: string): this {
    this.response.path = path;
    return this;
  }

  requestId(id: string): this {
    this.response.requestId = id;
    return this;
  }

  details(details: any): this {
    this.response.details = details;
    return this;
  }

  validationErrors(errors: ValidationError[]): this {
    this.response.errors = errors;
    return this;
  }

  build(): ErrorResponse {
    return {
      statusCode: this.response.statusCode || 500,
      error: this.response.error || 'Internal Server Error',
      message: this.response.message || 'An error occurred',
      timestamp: new Date().toISOString(),
      path: this.response.path || '',
      requestId: this.response.requestId,
      code: this.response.code,
      details: this.response.details,
      errors: this.response.errors,
    };
  }
}
```

## Error Codes

```typescript
// common/constants/error-codes.ts
export const ErrorCodes = {
  // Authentication
  AUTH_INVALID_CREDENTIALS: 'AUTH_INVALID_CREDENTIALS',
  AUTH_TOKEN_EXPIRED: 'AUTH_TOKEN_EXPIRED',
  AUTH_TOKEN_INVALID: 'AUTH_TOKEN_INVALID',
  AUTH_UNAUTHORIZED: 'AUTH_UNAUTHORIZED',

  // Users
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  USER_ALREADY_EXISTS: 'USER_ALREADY_EXISTS',
  USER_INACTIVE: 'USER_INACTIVE',

  // Orders
  ORDER_NOT_FOUND: 'ORDER_NOT_FOUND',
  ORDER_ALREADY_CANCELLED: 'ORDER_ALREADY_CANCELLED',
  ORDER_CANNOT_CANCEL: 'ORDER_CANNOT_CANCEL',
  ORDER_INSUFFICIENT_STOCK: 'ORDER_INSUFFICIENT_STOCK',

  // Validation
  VALIDATION_FAILED: 'VALIDATION_FAILED',
  INVALID_INPUT: 'INVALID_INPUT',

  // Generic
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  DUPLICATE_RESOURCE: 'DUPLICATE_RESOURCE',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  SERVICE_UNAVAILABLE: 'SERVICE_UNAVAILABLE',
} as const;

export type ErrorCode = (typeof ErrorCodes)[keyof typeof ErrorCodes];
```

## Typed Exception Classes

```typescript
// common/exceptions/app.exception.ts
import { HttpException, HttpStatus } from '@nestjs/common';
import { ErrorCode, ErrorCodes } from '../constants/error-codes';

export abstract class AppException extends HttpException {
  constructor(
    message: string,
    public readonly code: ErrorCode,
    status: HttpStatus,
    public readonly details?: any,
  ) {
    super({ message, code, details }, status);
  }
}

// common/exceptions/not-found.exception.ts
export class NotFoundException extends AppException {
  constructor(resource: string, id: string) {
    super(
      `${resource} with ID ${id} not found`,
      ErrorCodes.RESOURCE_NOT_FOUND,
      HttpStatus.NOT_FOUND,
      { resource, id },
    );
  }
}

// common/exceptions/conflict.exception.ts
export class ConflictException extends AppException {
  constructor(resource: string, field: string, value: any) {
    super(
      `${resource} with ${field} '${value}' already exists`,
      ErrorCodes.DUPLICATE_RESOURCE,
      HttpStatus.CONFLICT,
      { resource, field, value },
    );
  }
}

// common/exceptions/validation.exception.ts
export class ValidationException extends AppException {
  constructor(errors: ValidationError[]) {
    super(
      'Validation failed',
      ErrorCodes.VALIDATION_FAILED,
      HttpStatus.BAD_REQUEST,
      { errors },
    );
  }
}

// Usage
throw new NotFoundException('User', userId);
throw new ConflictException('User', 'email', email);
```

## Swagger Documentation

```typescript
// common/dto/error-response.dto.ts
import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';

export class ErrorResponseDto {
  @ApiProperty({ example: 400 })
  statusCode: number;

  @ApiProperty({ example: 'Bad Request' })
  error: string;

  @ApiProperty({ example: 'Validation failed' })
  message: string;

  @ApiProperty({ example: '2024-01-15T10:30:00.000Z' })
  timestamp: string;

  @ApiProperty({ example: '/api/users' })
  path: string;

  @ApiPropertyOptional({ example: 'VALIDATION_FAILED' })
  code?: string;

  @ApiPropertyOptional()
  details?: any;
}

// In controller
@ApiResponse({
  status: 400,
  description: 'Validation error',
  type: ErrorResponseDto,
})
@ApiResponse({
  status: 404,
  description: 'Resource not found',
  type: ErrorResponseDto,
})
@Get(':id')
findOne(@Param('id') id: string) {
  return this.service.findOne(id);
}
```

## Interceptor for Consistent Responses

```typescript
// common/interceptors/response-transform.interceptor.ts
import {
  Injectable,
  NestInterceptor,
  ExecutionContext,
  CallHandler,
} from '@nestjs/common';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface SuccessResponse<T> {
  success: true;
  data: T;
  timestamp: string;
}

@Injectable()
export class ResponseTransformInterceptor<T>
  implements NestInterceptor<T, SuccessResponse<T>>
{
  intercept(
    context: ExecutionContext,
    next: CallHandler,
  ): Observable<SuccessResponse<T>> {
    return next.handle().pipe(
      map((data) => ({
        success: true,
        data,
        timestamp: new Date().toISOString(),
      })),
    );
  }
}
```

## Best Practices

1. **Consistent structure**: Same format for all errors
2. **Error codes**: Machine-readable codes for client handling
3. **User-friendly messages**: Clear, actionable messages
4. **Detailed validation**: Field-level validation errors
5. **Environment awareness**: Hide details in production
6. **Documentation**: Swagger/OpenAPI error responses

## Checklist

- [ ] Consistent error response format
- [ ] Error codes defined
- [ ] Typed exception classes
- [ ] Swagger documentation
- [ ] Environment-aware details
- [ ] Validation error formatting
