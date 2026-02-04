---
name: error-handling
description: API error handling patterns and standards
category: api-design/patterns
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Error Handling Patterns

## Overview

Proper error handling is crucial for API usability. Good error responses help
developers quickly identify and fix issues. This guide covers error response
formats, status codes, and implementation patterns.

## Error Response Format

### Standard Structure

```typescript
interface ErrorResponse {
  error: {
    // Machine-readable error code
    code: string;

    // Human-readable message
    message: string;

    // Detailed error information
    details?: ErrorDetail[];

    // Request tracking
    request_id?: string;

    // Link to documentation
    documentation_url?: string;

    // Timestamp
    timestamp?: string;

    // Additional context
    context?: Record<string, any>;
  };
}

interface ErrorDetail {
  // Field that caused the error
  field?: string;

  // Specific error code for this detail
  code: string;

  // Human-readable message
  message: string;

  // Rejected value (sanitized)
  rejected_value?: any;
}
```

### Example Responses

```json
// Validation error (400)
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "email",
        "code": "INVALID_FORMAT",
        "message": "Must be a valid email address",
        "rejected_value": "not-an-email"
      },
      {
        "field": "password",
        "code": "TOO_SHORT",
        "message": "Must be at least 8 characters"
      }
    ],
    "request_id": "req_abc123",
    "documentation_url": "https://docs.example.com/errors#VALIDATION_ERROR"
  }
}

// Not found error (404)
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User with ID 'usr_xyz' not found",
    "request_id": "req_def456",
    "documentation_url": "https://docs.example.com/errors#NOT_FOUND"
  }
}

// Authorization error (403)
{
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to access this resource",
    "context": {
      "required_permission": "admin",
      "user_permissions": ["user"]
    },
    "request_id": "req_ghi789"
  }
}

// Rate limit error (429)
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests. Please retry after 60 seconds.",
    "context": {
      "limit": 100,
      "remaining": 0,
      "reset_at": "2024-01-15T12:05:00Z",
      "retry_after": 60
    },
    "request_id": "req_jkl012"
  }
}

// Internal error (500)
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred. Please try again later.",
    "request_id": "req_mno345",
    "timestamp": "2024-01-15T12:00:00Z"
  }
}
```

## Error Codes Taxonomy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Code Categories                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Authentication (401)                                           │
│  ├── INVALID_CREDENTIALS                                        │
│  ├── EXPIRED_TOKEN                                              │
│  ├── INVALID_TOKEN                                              │
│  ├── MISSING_TOKEN                                              │
│  └── REVOKED_TOKEN                                              │
│                                                                  │
│  Authorization (403)                                            │
│  ├── FORBIDDEN                                                  │
│  ├── INSUFFICIENT_PERMISSIONS                                   │
│  ├── RESOURCE_ACCESS_DENIED                                     │
│  └── ACCOUNT_SUSPENDED                                          │
│                                                                  │
│  Validation (400)                                               │
│  ├── VALIDATION_ERROR                                           │
│  ├── INVALID_FORMAT                                             │
│  ├── MISSING_FIELD                                              │
│  ├── INVALID_VALUE                                              │
│  ├── VALUE_TOO_LONG                                             │
│  ├── VALUE_TOO_SHORT                                            │
│  └── INVALID_TYPE                                               │
│                                                                  │
│  Resource (404, 409, 410)                                       │
│  ├── NOT_FOUND                                                  │
│  ├── ALREADY_EXISTS                                             │
│  ├── CONFLICT                                                   │
│  ├── GONE                                                       │
│  └── RESOURCE_LOCKED                                            │
│                                                                  │
│  Rate Limiting (429)                                            │
│  ├── RATE_LIMITED                                               │
│  ├── QUOTA_EXCEEDED                                             │
│  └── CONCURRENT_LIMIT                                           │
│                                                                  │
│  Server (500, 502, 503)                                         │
│  ├── INTERNAL_ERROR                                             │
│  ├── SERVICE_UNAVAILABLE                                        │
│  ├── DEPENDENCY_FAILED                                          │
│  └── MAINTENANCE                                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation

### Error Classes

```typescript
// Base error class
export class ApiError extends Error {
  constructor(
    public code: string,
    public message: string,
    public statusCode: number,
    public details?: ErrorDetail[],
    public context?: Record<string, any>
  ) {
    super(message);
    this.name = 'ApiError';
  }

  toJSON() {
    return {
      error: {
        code: this.code,
        message: this.message,
        details: this.details,
        context: this.context,
      },
    };
  }
}

// Specific error classes
export class ValidationError extends ApiError {
  constructor(details: ErrorDetail[]) {
    super('VALIDATION_ERROR', 'Request validation failed', 400, details);
  }
}

export class NotFoundError extends ApiError {
  constructor(resource: string, id: string) {
    super('NOT_FOUND', `${resource} with ID '${id}' not found`, 404);
  }
}

export class UnauthorizedError extends ApiError {
  constructor(message = 'Authentication required') {
    super('UNAUTHORIZED', message, 401);
  }
}

export class ForbiddenError extends ApiError {
  constructor(message = 'Access denied', context?: Record<string, any>) {
    super('FORBIDDEN', message, 403, undefined, context);
  }
}

export class ConflictError extends ApiError {
  constructor(message: string, context?: Record<string, any>) {
    super('CONFLICT', message, 409, undefined, context);
  }
}

export class RateLimitError extends ApiError {
  constructor(retryAfter: number, limit: number) {
    super('RATE_LIMITED', `Too many requests. Retry after ${retryAfter} seconds.`, 429, undefined, {
      retry_after: retryAfter,
      limit,
    });
  }
}

export class InternalError extends ApiError {
  constructor(message = 'An unexpected error occurred') {
    super('INTERNAL_ERROR', message, 500);
  }
}
```

### Error Handler Middleware

```typescript
// Express error handler
import { Request, Response, NextFunction } from 'express';

export function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  next: NextFunction
) {
  const requestId = req.headers['x-request-id'] || generateRequestId();

  // Log error
  logger.error({
    error: err,
    request_id: requestId,
    method: req.method,
    path: req.path,
    user_id: req.user?.id,
  });

  // Handle known API errors
  if (err instanceof ApiError) {
    return res.status(err.statusCode).json({
      error: {
        code: err.code,
        message: err.message,
        details: err.details,
        context: err.context,
        request_id: requestId,
        documentation_url: getDocUrl(err.code),
      },
    });
  }

  // Handle Zod validation errors
  if (err instanceof ZodError) {
    return res.status(400).json({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Request validation failed',
        details: err.errors.map((e) => ({
          field: e.path.join('.'),
          code: 'INVALID_VALUE',
          message: e.message,
        })),
        request_id: requestId,
      },
    });
  }

  // Handle Prisma errors
  if (err.name === 'PrismaClientKnownRequestError') {
    const prismaError = err as any;
    if (prismaError.code === 'P2002') {
      return res.status(409).json({
        error: {
          code: 'ALREADY_EXISTS',
          message: 'A record with this value already exists',
          details: [
            {
              field: prismaError.meta?.target?.[0],
              code: 'DUPLICATE_VALUE',
              message: 'This value is already in use',
            },
          ],
          request_id: requestId,
        },
      });
    }
    if (prismaError.code === 'P2025') {
      return res.status(404).json({
        error: {
          code: 'NOT_FOUND',
          message: 'Record not found',
          request_id: requestId,
        },
      });
    }
  }

  // Handle unknown errors (don't leak details)
  return res.status(500).json({
    error: {
      code: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred. Please try again later.',
      request_id: requestId,
    },
  });
}

function getDocUrl(code: string): string {
  return `https://docs.example.com/errors#${code}`;
}
```

### Route-Level Error Handling

```typescript
// Async handler wrapper
const asyncHandler =
  (fn: Function) => (req: Request, res: Response, next: NextFunction) => {
    Promise.resolve(fn(req, res, next)).catch(next);
  };

// Route with error handling
router.get(
  '/users/:id',
  asyncHandler(async (req: Request, res: Response) => {
    const user = await userService.findById(req.params.id);

    if (!user) {
      throw new NotFoundError('User', req.params.id);
    }

    if (!canAccessUser(req.user, user)) {
      throw new ForbiddenError('You cannot access this user', {
        required_permission: 'admin',
      });
    }

    res.json({ data: user });
  })
);

router.post(
  '/users',
  validateBody(CreateUserSchema),
  asyncHandler(async (req: Request, res: Response) => {
    const existingUser = await userService.findByEmail(req.body.email);

    if (existingUser) {
      throw new ConflictError('A user with this email already exists', {
        field: 'email',
      });
    }

    const user = await userService.create(req.body);
    res.status(201).json({ data: user });
  })
);
```

## Problem Details (RFC 7807)

```typescript
// RFC 7807 Problem Details format
interface ProblemDetails {
  // URI reference for error type
  type: string;

  // Short summary
  title: string;

  // HTTP status code
  status: number;

  // Human-readable explanation
  detail?: string;

  // URI for the specific occurrence
  instance?: string;

  // Extension members
  [key: string]: any;
}

// Example
const problemDetails: ProblemDetails = {
  type: 'https://api.example.com/problems/validation-error',
  title: 'Validation Error',
  status: 400,
  detail: 'The provided email address is invalid',
  instance: '/users',
  invalid_params: [
    {
      name: 'email',
      reason: 'must be a valid email address',
    },
  ],
};

// Response with content type
res.status(400).set('Content-Type', 'application/problem+json').json(problemDetails);
```

## Client-Side Error Handling

```typescript
// API client with error handling
class ApiClient {
  private baseUrl: string;
  private apiKey: string;

  async request<T>(method: string, path: string, options?: RequestOptions): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
        'X-Request-ID': crypto.randomUUID(),
      },
      body: options?.body ? JSON.stringify(options.body) : undefined,
    });

    if (!response.ok) {
      const error = await response.json();
      throw this.handleError(response.status, error);
    }

    return response.json();
  }

  private handleError(status: number, body: any): Error {
    const error = body.error || body;

    switch (error.code) {
      case 'VALIDATION_ERROR':
        return new ValidationApiError(error.message, error.details);

      case 'NOT_FOUND':
        return new NotFoundApiError(error.message);

      case 'UNAUTHORIZED':
      case 'INVALID_TOKEN':
      case 'EXPIRED_TOKEN':
        return new UnauthorizedApiError(error.message);

      case 'FORBIDDEN':
        return new ForbiddenApiError(error.message);

      case 'RATE_LIMITED':
        return new RateLimitApiError(error.message, error.context?.retry_after);

      case 'CONFLICT':
      case 'ALREADY_EXISTS':
        return new ConflictApiError(error.message);

      default:
        return new ApiError(error.code || 'UNKNOWN_ERROR', error.message, status);
    }
  }
}

// Usage with retry
async function createUserWithRetry(data: CreateUserInput, maxRetries = 3): Promise<User> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await api.users.create(data);
    } catch (error) {
      if (error instanceof RateLimitApiError) {
        if (attempt < maxRetries) {
          await sleep(error.retryAfter * 1000);
          continue;
        }
      }

      if (error instanceof ValidationApiError) {
        // Don't retry validation errors
        console.error('Validation failed:', error.details);
        throw error;
      }

      if (error instanceof ConflictApiError) {
        // Don't retry conflicts
        throw error;
      }

      // Retry other errors with backoff
      if (attempt < maxRetries) {
        await sleep(Math.pow(2, attempt) * 1000);
        continue;
      }

      throw error;
    }
  }

  throw new Error('Max retries exceeded');
}
```

## Error Logging

```typescript
// Structured error logging
interface ErrorLog {
  timestamp: string;
  level: 'error' | 'warn';
  error: {
    code: string;
    message: string;
    stack?: string;
  };
  request: {
    id: string;
    method: string;
    path: string;
    query?: Record<string, any>;
    body?: Record<string, any>;
    headers?: Record<string, string>;
  };
  user?: {
    id: string;
    email?: string;
  };
  context?: Record<string, any>;
}

function logError(err: Error, req: Request, context?: Record<string, any>) {
  const log: ErrorLog = {
    timestamp: new Date().toISOString(),
    level: err instanceof ApiError && err.statusCode < 500 ? 'warn' : 'error',
    error: {
      code: err instanceof ApiError ? err.code : 'UNKNOWN',
      message: err.message,
      stack: process.env.NODE_ENV !== 'production' ? err.stack : undefined,
    },
    request: {
      id: req.headers['x-request-id'] as string,
      method: req.method,
      path: req.path,
      query: req.query,
      // Sanitize sensitive fields
      body: sanitizeBody(req.body),
    },
    user: req.user ? { id: req.user.id, email: req.user.email } : undefined,
    context,
  };

  logger.log(log);
}

function sanitizeBody(body: any): any {
  if (!body) return undefined;

  const sensitiveFields = ['password', 'token', 'secret', 'api_key', 'credit_card'];
  const sanitized = { ...body };

  for (const field of sensitiveFields) {
    if (sanitized[field]) {
      sanitized[field] = '[REDACTED]';
    }
  }

  return sanitized;
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Error Handling Best Practices                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Consistent Error Format                                 │
│     └── Same structure for all errors                           │
│                                                                  │
│  2. Include Machine-Readable Codes                              │
│     └── Don't rely only on HTTP status                          │
│                                                                  │
│  3. Provide Helpful Messages                                    │
│     └── Tell users how to fix the problem                       │
│                                                                  │
│  4. Include Request IDs                                         │
│     └── For debugging and support                               │
│                                                                  │
│  5. Don't Leak Sensitive Info                                   │
│     └── No stack traces, passwords, or internal details         │
│                                                                  │
│  6. Log All Errors                                              │
│     └── With context for debugging                              │
│                                                                  │
│  7. Document All Error Codes                                    │
│     └── Include in API documentation                            │
│                                                                  │
│  8. Use Appropriate Status Codes                                │
│     └── 4xx for client errors, 5xx for server errors            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
