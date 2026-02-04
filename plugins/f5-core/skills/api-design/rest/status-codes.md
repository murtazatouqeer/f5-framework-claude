---
name: status-codes
description: HTTP status codes usage in REST APIs
category: api-design/rest
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# HTTP Status Codes

## Overview

HTTP status codes communicate the result of a request. Using them correctly
makes APIs predictable and easier to debug.

## Status Code Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                   HTTP Status Code Categories                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1xx Informational                                              │
│  └── Request received, continuing process                       │
│                                                                  │
│  2xx Success                                                     │
│  └── Request successfully received, understood, accepted        │
│                                                                  │
│  3xx Redirection                                                 │
│  └── Further action needed to complete request                  │
│                                                                  │
│  4xx Client Error                                                │
│  └── Request contains bad syntax or cannot be fulfilled         │
│                                                                  │
│  5xx Server Error                                                │
│  └── Server failed to fulfill valid request                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Success Codes (2xx)

### 200 OK

Most common success response. Use for successful GET, PUT, PATCH, DELETE (with body).

```http
GET /api/v1/users/123 HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "id": "usr_123",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

### 201 Created

Resource successfully created. Always include Location header.

```http
POST /api/v1/users HTTP/1.1
Content-Type: application/json

{"name": "Jane Doe", "email": "jane@example.com"}

HTTP/1.1 201 Created
Location: /api/v1/users/usr_456
Content-Type: application/json

{
  "data": {
    "id": "usr_456",
    "name": "Jane Doe",
    "email": "jane@example.com"
  }
}
```

### 202 Accepted

Request accepted but processing not complete. Use for async operations.

```http
POST /api/v1/reports HTTP/1.1
Content-Type: application/json

{"type": "sales", "date_range": "2024-01"}

HTTP/1.1 202 Accepted
Content-Type: application/json

{
  "data": {
    "job_id": "job_789",
    "status": "processing",
    "check_status_at": "/api/v1/jobs/job_789",
    "estimated_completion": "2024-01-15T10:05:00Z"
  }
}
```

### 204 No Content

Successful request with no content to return. Use for DELETE.

```http
DELETE /api/v1/users/usr_123 HTTP/1.1

HTTP/1.1 204 No Content
```

### 206 Partial Content

Partial resource returned due to range request.

```http
GET /api/v1/files/large-file.zip HTTP/1.1
Range: bytes=0-1023

HTTP/1.1 206 Partial Content
Content-Range: bytes 0-1023/10240
Content-Length: 1024
Content-Type: application/octet-stream

[binary data]
```

## Client Error Codes (4xx)

### 400 Bad Request

Request is malformed or has invalid syntax.

```http
POST /api/v1/users HTTP/1.1
Content-Type: application/json

{invalid json}

HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "INVALID_JSON",
    "message": "Request body is not valid JSON",
    "details": [{
      "position": 1,
      "message": "Unexpected token 'i' at position 1"
    }]
  }
}
```

### 401 Unauthorized

Authentication required or failed.

```http
GET /api/v1/users HTTP/1.1

HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="api"
Content-Type: application/json

{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required",
    "docs_url": "https://docs.example.com/auth"
  }
}
```

### 403 Forbidden

Authenticated but not authorized for this action.

```http
DELETE /api/v1/users/usr_123 HTTP/1.1
Authorization: Bearer <token>

HTTP/1.1 403 Forbidden
Content-Type: application/json

{
  "error": {
    "code": "FORBIDDEN",
    "message": "You don't have permission to delete this user"
  }
}
```

### 404 Not Found

Resource doesn't exist.

```http
GET /api/v1/users/usr_999 HTTP/1.1
Authorization: Bearer <token>

HTTP/1.1 404 Not Found
Content-Type: application/json

{
  "error": {
    "code": "NOT_FOUND",
    "message": "User with ID 'usr_999' not found"
  }
}
```

### 405 Method Not Allowed

HTTP method not supported for this resource.

```http
DELETE /api/v1/system/config HTTP/1.1

HTTP/1.1 405 Method Not Allowed
Allow: GET, PUT
Content-Type: application/json

{
  "error": {
    "code": "METHOD_NOT_ALLOWED",
    "message": "DELETE is not allowed on this resource",
    "allowed_methods": ["GET", "PUT"]
  }
}
```

### 409 Conflict

Request conflicts with current state.

```http
POST /api/v1/users HTTP/1.1
Content-Type: application/json

{"email": "existing@example.com"}

HTTP/1.1 409 Conflict
Content-Type: application/json

{
  "error": {
    "code": "DUPLICATE_RESOURCE",
    "message": "A user with this email already exists",
    "details": [{
      "field": "email",
      "code": "ALREADY_EXISTS",
      "message": "This email is already registered"
    }]
  }
}
```

### 410 Gone

Resource permanently deleted.

```http
GET /api/v1/users/usr_deleted HTTP/1.1

HTTP/1.1 410 Gone
Content-Type: application/json

{
  "error": {
    "code": "RESOURCE_DELETED",
    "message": "This user has been permanently deleted",
    "deleted_at": "2024-01-10T10:00:00Z"
  }
}
```

### 422 Unprocessable Entity

Request is well-formed but semantically incorrect.

```http
POST /api/v1/orders HTTP/1.1
Content-Type: application/json

{
  "user_id": "usr_123",
  "items": [
    {"product_id": "prod_456", "quantity": -5}
  ]
}

HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "items[0].quantity",
        "code": "INVALID_VALUE",
        "message": "Quantity must be a positive integer"
      }
    ]
  }
}
```

### 429 Too Many Requests

Rate limit exceeded.

```http
GET /api/v1/users HTTP/1.1

HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705315860
Content-Type: application/json

{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Rate limit exceeded. Please retry after 60 seconds",
    "retry_after": 60
  }
}
```

## Server Error Codes (5xx)

### 500 Internal Server Error

Unexpected server error.

```http
GET /api/v1/users HTTP/1.1

HTTP/1.1 500 Internal Server Error
Content-Type: application/json

{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred. Please try again later.",
    "trace_id": "abc123xyz"
  }
}
```

### 502 Bad Gateway

Upstream service returned invalid response.

```http
GET /api/v1/payments HTTP/1.1

HTTP/1.1 502 Bad Gateway
Content-Type: application/json

{
  "error": {
    "code": "BAD_GATEWAY",
    "message": "Payment service returned an invalid response",
    "trace_id": "def456uvw"
  }
}
```

### 503 Service Unavailable

Server temporarily unavailable.

```http
GET /api/v1/users HTTP/1.1

HTTP/1.1 503 Service Unavailable
Retry-After: 300
Content-Type: application/json

{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Service temporarily unavailable for maintenance",
    "retry_after": 300,
    "maintenance_window": {
      "start": "2024-01-15T10:00:00Z",
      "end": "2024-01-15T11:00:00Z"
    }
  }
}
```

### 504 Gateway Timeout

Upstream service didn't respond in time.

```http
GET /api/v1/reports/complex HTTP/1.1

HTTP/1.1 504 Gateway Timeout
Content-Type: application/json

{
  "error": {
    "code": "GATEWAY_TIMEOUT",
    "message": "Request timed out waiting for upstream service",
    "trace_id": "ghi789rst"
  }
}
```

## Status Code Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│                Which Status Code to Use?                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Request successful?                                            │
│  ├── Yes                                                         │
│  │   ├── GET/PUT/PATCH → 200 OK                                 │
│  │   ├── POST (created) → 201 Created                           │
│  │   ├── DELETE → 204 No Content                                │
│  │   └── Async operation → 202 Accepted                         │
│  │                                                               │
│  └── No                                                          │
│      ├── Client's fault?                                        │
│      │   ├── Bad JSON/syntax → 400 Bad Request                  │
│      │   ├── Not authenticated → 401 Unauthorized               │
│      │   ├── Not authorized → 403 Forbidden                     │
│      │   ├── Resource not found → 404 Not Found                 │
│      │   ├── Method not allowed → 405 Method Not Allowed        │
│      │   ├── Conflict/duplicate → 409 Conflict                  │
│      │   ├── Validation failed → 422 Unprocessable              │
│      │   └── Too many requests → 429 Too Many Requests          │
│      │                                                           │
│      └── Server's fault?                                        │
│          ├── Unexpected error → 500 Internal Server Error       │
│          ├── Upstream invalid → 502 Bad Gateway                 │
│          ├── Maintenance → 503 Service Unavailable              │
│          └── Upstream timeout → 504 Gateway Timeout             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Status Codes by HTTP Method

```
┌─────────────────────────────────────────────────────────────────┐
│                Common Status Codes by Method                     │
├──────────┬─────────────────────────────────────────────────────┤
│ Method   │ Success              │ Common Errors                 │
├──────────┼──────────────────────┼──────────────────────────────┤
│ GET      │ 200 OK               │ 400, 401, 403, 404           │
│          │ 304 Not Modified     │                               │
├──────────┼──────────────────────┼──────────────────────────────┤
│ POST     │ 201 Created          │ 400, 401, 403, 409, 422      │
│          │ 202 Accepted         │                               │
├──────────┼──────────────────────┼──────────────────────────────┤
│ PUT      │ 200 OK               │ 400, 401, 403, 404, 409, 422 │
│          │ 201 Created (upsert) │                               │
├──────────┼──────────────────────┼──────────────────────────────┤
│ PATCH    │ 200 OK               │ 400, 401, 403, 404, 422      │
├──────────┼──────────────────────┼──────────────────────────────┤
│ DELETE   │ 204 No Content       │ 401, 403, 404                │
│          │ 200 OK (with body)   │                               │
└──────────┴──────────────────────┴──────────────────────────────┘
```

## Implementation Example

```typescript
// Status code constants
export const HttpStatus = {
  // Success
  OK: 200,
  CREATED: 201,
  ACCEPTED: 202,
  NO_CONTENT: 204,

  // Client errors
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  METHOD_NOT_ALLOWED: 405,
  CONFLICT: 409,
  GONE: 410,
  UNPROCESSABLE_ENTITY: 422,
  TOO_MANY_REQUESTS: 429,

  // Server errors
  INTERNAL_SERVER_ERROR: 500,
  BAD_GATEWAY: 502,
  SERVICE_UNAVAILABLE: 503,
  GATEWAY_TIMEOUT: 504,
} as const;

// Error response helper
interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Array<{
      field?: string;
      code: string;
      message: string;
    }>;
    trace_id?: string;
  };
}

function errorResponse(
  code: string,
  message: string,
  details?: ApiErrorResponse['error']['details']
): ApiErrorResponse {
  return {
    error: {
      code,
      message,
      details,
      trace_id: crypto.randomUUID(),
    },
  };
}

// Usage in Express
app.get('/users/:id', async (req, res) => {
  try {
    const user = await userService.findById(req.params.id);

    if (!user) {
      return res.status(HttpStatus.NOT_FOUND).json(
        errorResponse('NOT_FOUND', `User '${req.params.id}' not found`)
      );
    }

    return res.status(HttpStatus.OK).json({ data: user });
  } catch (error) {
    console.error('Error fetching user:', error);
    return res.status(HttpStatus.INTERNAL_SERVER_ERROR).json(
      errorResponse('INTERNAL_ERROR', 'An unexpected error occurred')
    );
  }
});

app.post('/users', async (req, res) => {
  try {
    const validation = validateUser(req.body);

    if (!validation.valid) {
      return res.status(HttpStatus.UNPROCESSABLE_ENTITY).json(
        errorResponse('VALIDATION_ERROR', 'Validation failed', validation.errors)
      );
    }

    const existing = await userService.findByEmail(req.body.email);
    if (existing) {
      return res.status(HttpStatus.CONFLICT).json(
        errorResponse('DUPLICATE_RESOURCE', 'Email already registered')
      );
    }

    const user = await userService.create(req.body);

    return res
      .status(HttpStatus.CREATED)
      .header('Location', `/api/v1/users/${user.id}`)
      .json({ data: user });
  } catch (error) {
    console.error('Error creating user:', error);
    return res.status(HttpStatus.INTERNAL_SERVER_ERROR).json(
      errorResponse('INTERNAL_ERROR', 'An unexpected error occurred')
    );
  }
});
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Status Code Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Specific Codes Over Generic                             │
│     ├── 422 for validation errors (not 400)                     │
│     ├── 409 for conflicts (not 400)                             │
│     └── 403 for authorization (not 401)                         │
│                                                                  │
│  2. Be Consistent                                                │
│     └── Same situation = same status code everywhere            │
│                                                                  │
│  3. Include Helpful Error Messages                              │
│     ├── Machine-readable code                                   │
│     ├── Human-readable message                                  │
│     └── Debug information (trace_id)                            │
│                                                                  │
│  4. Don't Leak Sensitive Information                            │
│     ├── 404 vs 403 for hidden resources                         │
│     └── Generic messages for 500 errors                         │
│                                                                  │
│  5. Document Your Status Codes                                  │
│     └── List all possible codes per endpoint                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
