---
name: request-response
description: API request and response patterns
category: api-design/patterns
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Request/Response Patterns

## Overview

Consistent request and response patterns improve API usability, make integration
easier, and reduce errors. This guide covers common patterns for structuring
API requests and responses.

## Request Patterns

### Standard Request Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                    Request Components                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Headers                                                      │
│     ├── Authentication (Authorization)                          │
│     ├── Content-Type                                            │
│     ├── Accept                                                  │
│     ├── Request ID (X-Request-ID)                               │
│     └── Custom headers (X-*)                                    │
│                                                                  │
│  2. Path Parameters                                             │
│     └── Resource identifiers (/users/{id})                      │
│                                                                  │
│  3. Query Parameters                                            │
│     ├── Filtering (?status=active)                              │
│     ├── Sorting (?sort=created_at:desc)                         │
│     ├── Pagination (?page_size=20&page_token=abc)               │
│     └── Field selection (?fields=id,name,email)                 │
│                                                                  │
│  4. Request Body                                                │
│     └── JSON payload for POST/PUT/PATCH                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Header Standards

```typescript
// Required headers
interface RequestHeaders {
  // Authentication
  Authorization: string; // "Bearer <token>" or "Basic <credentials>"

  // Content negotiation
  'Content-Type': 'application/json'; // For request body
  Accept: 'application/json'; // Expected response format

  // Request tracking
  'X-Request-ID': string; // Unique request identifier
  'X-Correlation-ID'?: string; // For distributed tracing

  // Client identification
  'User-Agent': string; // Client app identifier
  'X-Client-Version'?: string; // Client version

  // Conditional requests
  'If-Match'?: string; // ETag for updates
  'If-None-Match'?: string; // ETag for caching

  // Rate limiting
  'X-API-Key'?: string; // API key if not in Authorization
}

// Example request
fetch('https://api.example.com/v1/users', {
  method: 'GET',
  headers: {
    Authorization: 'Bearer eyJhbGciOiJIUzI1NiIs...',
    Accept: 'application/json',
    'X-Request-ID': crypto.randomUUID(),
    'User-Agent': 'MyApp/1.0.0',
  },
});
```

### Input Validation

```typescript
// Validation schema with Zod
import { z } from 'zod';

const CreateUserSchema = z.object({
  name: z
    .string()
    .min(2, 'Name must be at least 2 characters')
    .max(100, 'Name must be at most 100 characters')
    .trim(),

  email: z.string().email('Invalid email format').toLowerCase(),

  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain uppercase letter')
    .regex(/[a-z]/, 'Password must contain lowercase letter')
    .regex(/[0-9]/, 'Password must contain number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain special character'),

  role: z.enum(['user', 'admin', 'moderator']).optional().default('user'),

  metadata: z.record(z.string()).optional(),
});

type CreateUserInput = z.infer<typeof CreateUserSchema>;

// Express middleware
function validateBody<T>(schema: z.ZodSchema<T>) {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req.body);

    if (!result.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: result.error.errors.map((err) => ({
            field: err.path.join('.'),
            message: err.message,
            code: 'INVALID_VALUE',
          })),
        },
      });
    }

    req.body = result.data;
    next();
  };
}

// Usage
app.post('/users', validateBody(CreateUserSchema), createUser);
```

### Request Body Patterns

```typescript
// Create request - all required fields
interface CreateOrderRequest {
  customer_id: string;
  items: Array<{
    product_id: string;
    quantity: number;
    unit_price?: number; // Optional, server can look up
  }>;
  shipping_address: Address;
  billing_address?: Address; // Optional, defaults to shipping
  notes?: string;
  metadata?: Record<string, string>;
}

// Update request - all optional (partial update)
interface UpdateOrderRequest {
  status?: OrderStatus;
  shipping_address?: Address;
  notes?: string;
  metadata?: Record<string, string>;
}

// Bulk request
interface BulkCreateUsersRequest {
  users: CreateUserRequest[];
  options?: {
    skip_duplicates?: boolean;
    send_welcome_email?: boolean;
  };
}

// Action request
interface ProcessPaymentRequest {
  order_id: string;
  payment_method_id: string;
  amount: number;
  currency: string;
  idempotency_key: string;
}
```

## Response Patterns

### Standard Response Structure

```typescript
// Success response wrapper
interface SuccessResponse<T> {
  data: T;
  meta?: ResponseMeta;
}

interface ResponseMeta {
  request_id: string;
  timestamp: string;
  version: string;
}

// Collection response with pagination
interface CollectionResponse<T> {
  data: T[];
  pagination: {
    page_size: number;
    page_token?: string;
    next_page_token?: string;
    previous_page_token?: string;
    total_count?: number;
    has_more: boolean;
  };
  meta?: ResponseMeta;
}

// Error response
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: ErrorDetail[];
    request_id?: string;
    documentation_url?: string;
  };
}

interface ErrorDetail {
  field?: string;
  code: string;
  message: string;
}
```

### Single Resource Response

```typescript
// GET /users/usr_123
const response = {
  data: {
    id: 'usr_123',
    name: 'John Doe',
    email: 'john@example.com',
    status: 'active',
    role: 'user',
    profile: {
      bio: 'Software developer',
      avatar_url: 'https://example.com/avatar.jpg',
    },
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z',
  },
  meta: {
    request_id: 'req_abc123',
    timestamp: '2024-01-15T12:00:00Z',
    version: '2024-01-01',
  },
};
```

### Collection Response

```typescript
// GET /users?page_size=2&status=active
const response = {
  data: [
    {
      id: 'usr_123',
      name: 'John Doe',
      email: 'john@example.com',
      status: 'active',
    },
    {
      id: 'usr_456',
      name: 'Jane Smith',
      email: 'jane@example.com',
      status: 'active',
    },
  ],
  pagination: {
    page_size: 2,
    next_page_token: 'eyJpZCI6InVzcl80NTYifQ==',
    total_count: 150,
    has_more: true,
  },
  meta: {
    request_id: 'req_def456',
    timestamp: '2024-01-15T12:00:00Z',
    version: '2024-01-01',
  },
};
```

### Created Resource Response

```typescript
// POST /users
// Response: 201 Created
// Headers: Location: /users/usr_789
const response = {
  data: {
    id: 'usr_789',
    name: 'New User',
    email: 'new@example.com',
    status: 'active',
    role: 'user',
    created_at: '2024-01-15T12:00:00Z',
    updated_at: '2024-01-15T12:00:00Z',
  },
  meta: {
    request_id: 'req_ghi789',
    timestamp: '2024-01-15T12:00:00Z',
    version: '2024-01-01',
  },
};
```

### Batch Response

```typescript
// POST /users/bulk
const response = {
  data: {
    succeeded: [
      { id: 'usr_001', name: 'User 1', index: 0 },
      { id: 'usr_002', name: 'User 2', index: 1 },
    ],
    failed: [
      {
        index: 2,
        error: {
          code: 'DUPLICATE_EMAIL',
          message: 'Email already exists',
          field: 'email',
        },
      },
    ],
    summary: {
      total: 3,
      succeeded: 2,
      failed: 1,
    },
  },
  meta: {
    request_id: 'req_bulk001',
    timestamp: '2024-01-15T12:00:00Z',
    version: '2024-01-01',
  },
};
```

## Response Headers

```typescript
// Standard response headers
const responseHeaders = {
  // Content
  'Content-Type': 'application/json; charset=utf-8',
  'Content-Length': '1234',

  // Caching
  'Cache-Control': 'private, max-age=0, no-cache',
  ETag: '"abc123"',
  'Last-Modified': 'Mon, 15 Jan 2024 10:30:00 GMT',

  // Request tracking
  'X-Request-ID': 'req_abc123',

  // Rate limiting
  'X-RateLimit-Limit': '1000',
  'X-RateLimit-Remaining': '999',
  'X-RateLimit-Reset': '1705312800',

  // Pagination
  Link: '</users?page_token=abc>; rel="next", </users?page_token=xyz>; rel="prev"',

  // Security
  'X-Content-Type-Options': 'nosniff',
  'X-Frame-Options': 'DENY',

  // CORS
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, PATCH, DELETE',
  'Access-Control-Allow-Headers': 'Authorization, Content-Type',
};
```

## Envelope Pattern

### With Envelope

```typescript
// Wrapped in data object
{
  "data": {
    "id": "usr_123",
    "name": "John Doe"
  },
  "meta": {
    "request_id": "req_abc"
  }
}

// Pros:
// - Consistent structure
// - Room for metadata
// - Easy to add fields

// Cons:
// - Extra nesting
// - More verbose
```

### Without Envelope

```typescript
// Direct response
{
  "id": "usr_123",
  "name": "John Doe"
}

// Headers carry metadata:
// X-Request-ID: req_abc

// Pros:
// - Simpler, less nesting
// - Smaller payload

// Cons:
// - Inconsistent with error responses
// - Metadata in headers (not all clients handle well)
```

### Recommendation

```typescript
// Use envelope for consistency
// Errors always need structure, so match success responses

// Success
{
  "data": { ... }
}

// Error
{
  "error": { ... }
}

// Client code is simpler:
const response = await api.get('/users');
if (response.data) {
  // Success
  return response.data;
} else if (response.error) {
  // Error
  throw new ApiError(response.error);
}
```

## HATEOAS Responses

```typescript
// Response with hypermedia links
const response = {
  data: {
    id: 'ord_123',
    status: 'pending',
    total: 9999,
    customer_id: 'cus_456',
    created_at: '2024-01-15T12:00:00Z',
  },
  links: {
    self: { href: '/orders/ord_123' },
    customer: { href: '/customers/cus_456' },
    items: { href: '/orders/ord_123/items' },
    payment: { href: '/orders/ord_123/payment', method: 'POST' },
    cancel: {
      href: '/orders/ord_123/cancel',
      method: 'POST',
      title: 'Cancel this order',
    },
  },
  actions: [
    {
      name: 'pay',
      href: '/orders/ord_123/payment',
      method: 'POST',
      fields: [
        { name: 'payment_method_id', type: 'string', required: true },
        { name: 'amount', type: 'integer', required: true },
      ],
    },
  ],
};
```

## Partial Responses (Field Selection)

```typescript
// Request: GET /users/usr_123?fields=id,name,email

// Full response
const fullResponse = {
  data: {
    id: 'usr_123',
    name: 'John Doe',
    email: 'john@example.com',
    status: 'active',
    role: 'user',
    profile: {
      bio: 'Developer',
      avatar_url: 'https://...',
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
  },
};

// Partial response (with field selection)
const partialResponse = {
  data: {
    id: 'usr_123',
    name: 'John Doe',
    email: 'john@example.com',
  },
};

// Implementation
function selectFields<T>(obj: T, fields: string[]): Partial<T> {
  if (!fields || fields.length === 0) {
    return obj;
  }

  const result: any = {};
  for (const field of fields) {
    if (field.includes('.')) {
      // Handle nested fields: "profile.bio"
      const [parent, child] = field.split('.');
      if (!result[parent]) result[parent] = {};
      result[parent][child] = (obj as any)[parent]?.[child];
    } else {
      result[field] = (obj as any)[field];
    }
  }
  return result;
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│             Request/Response Best Practices                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Be Consistent                                               │
│     └── Same structure across all endpoints                     │
│                                                                  │
│  2. Use Camel or Snake Case Consistently                        │
│     └── Pick one and stick with it                              │
│                                                                  │
│  3. Include Request IDs                                         │
│     └── For debugging and support                               │
│                                                                  │
│  4. Validate Early                                              │
│     └── Return 400 for invalid requests immediately             │
│                                                                  │
│  5. Use Appropriate Status Codes                                │
│     └── 200, 201, 204, 400, 401, 403, 404, 500                  │
│                                                                  │
│  6. Include Timestamps                                          │
│     └── ISO 8601 format in UTC                                  │
│                                                                  │
│  7. Support Partial Responses                                   │
│     └── Field selection for bandwidth savings                   │
│                                                                  │
│  8. Document Everything                                         │
│     └── Request/response examples in docs                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
