---
name: api-guidelines
description: API design guidelines and standards
category: api-design/best-practices
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# API Design Guidelines

## Overview

Good API design creates intuitive, consistent, and predictable interfaces. This
guide covers naming conventions, resource design, and standardization principles
that make APIs easy to learn and use.

## Design Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Design Principles                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Consistency                                                 │
│     └── Same patterns everywhere, predictable behavior          │
│                                                                  │
│  2. Simplicity                                                  │
│     └── Easy to understand, minimal learning curve              │
│                                                                  │
│  3. Discoverability                                             │
│     └── Self-documenting, explorable resources                  │
│                                                                  │
│  4. Stability                                                   │
│     └── Backwards compatible, clear versioning                  │
│                                                                  │
│  5. Security                                                    │
│     └── Secure by default, principle of least privilege         │
│                                                                  │
│  6. Performance                                                 │
│     └── Efficient operations, reasonable response times         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Naming Conventions

### URL Naming

```typescript
// Resource naming rules
const namingRules = {
  // Use nouns, not verbs
  good: '/users',
  bad: '/getUsers',

  // Use plural nouns for collections
  good: '/products',
  bad: '/product',

  // Use lowercase with hyphens
  good: '/user-profiles',
  bad: '/userProfiles',
  bad: '/user_profiles',

  // Nest resources logically
  good: '/users/{id}/orders',
  bad: '/user-orders/{userId}',

  // Use query params for filtering
  good: '/products?category=electronics',
  bad: '/products/category/electronics',
};

// Examples of well-designed URLs
const urlExamples = {
  // Collections
  listUsers: 'GET /users',
  listUserOrders: 'GET /users/{userId}/orders',

  // Individual resources
  getUser: 'GET /users/{userId}',
  getOrder: 'GET /orders/{orderId}',

  // Nested resources
  getUserAddress: 'GET /users/{userId}/addresses/{addressId}',

  // Actions (when REST doesn't fit)
  searchProducts: 'POST /products/search',
  bulkCreateUsers: 'POST /users/bulk',
  exportReport: 'POST /reports/{id}/export',
};
```

### Field Naming

```typescript
// Field naming conventions
interface NamingConventions {
  // Use snake_case (recommended for JSON)
  user_id: string;
  created_at: string;
  email_verified: boolean;

  // Or camelCase (consistent with JavaScript)
  userId: string;
  createdAt: string;
  emailVerified: boolean;

  // Never mix styles in the same API
}

// Standard field names
interface StandardFields {
  // Identifiers
  id: string; // Primary identifier
  external_id: string; // External reference

  // Timestamps
  created_at: string; // ISO 8601 UTC
  updated_at: string; // ISO 8601 UTC
  deleted_at: string | null; // Soft delete

  // Status
  status: string; // Current state
  state: string; // Alternative to status

  // Metadata
  metadata: Record<string, string>; // Custom key-value
  tags: string[]; // Labels/categories
}

// Boolean naming
interface BooleanNaming {
  // Use positive names
  is_active: boolean; // Not is_inactive
  is_verified: boolean; // Not is_not_verified
  has_access: boolean; // Not lacks_access
  can_edit: boolean; // Permission-style
}
```

### ID Formats

```typescript
// ID format options
interface IDFormats {
  // UUIDs - Universally unique
  uuid: '550e8400-e29b-41d4-a716-446655440000';

  // ULIDs - Sortable, URL-safe
  ulid: '01ARZ3NDEKTSV4RRFFQ69G5FAV';

  // Prefixed IDs - Self-documenting
  prefixed: 'usr_123abc' | 'ord_456def' | 'prod_789ghi';

  // Snowflake IDs - Time-ordered, distributed
  snowflake: '1234567890123456789';
}

// Prefixed ID implementation
function generateId(prefix: string): string {
  const timestamp = Date.now().toString(36);
  const random = Math.random().toString(36).substring(2, 10);
  return `${prefix}_${timestamp}${random}`;
}

// ID prefix conventions
const idPrefixes = {
  user: 'usr_',
  order: 'ord_',
  product: 'prod_',
  payment: 'pay_',
  subscription: 'sub_',
  invoice: 'inv_',
  customer: 'cus_',
  account: 'acc_',
  session: 'sess_',
  token: 'tok_',
};
```

## Resource Design

### Resource Structure

```typescript
// Base resource structure
interface Resource {
  // Always include
  id: string;
  created_at: string;
  updated_at: string;

  // Object type for polymorphism
  object: string;
}

// User resource example
interface User extends Resource {
  object: 'user';
  email: string;
  name: string;
  status: 'active' | 'inactive' | 'suspended';
  role: 'user' | 'admin' | 'moderator';

  // Expandable relationships
  organization?: Organization;
  organization_id: string;

  // Metadata
  metadata: Record<string, string>;
}

// Response with expansion
interface UserResponse {
  data: User;
  // Included expanded resources
  includes?: {
    organizations?: Organization[];
    roles?: Role[];
  };
}
```

### Collection Responses

```typescript
// Standard collection response
interface CollectionResponse<T> {
  // The resource type
  object: 'list';

  // Array of resources
  data: T[];

  // Pagination info
  pagination: {
    page_size: number;
    has_more: boolean;
    next_cursor?: string;
    prev_cursor?: string;
    total_count?: number; // Optional, can be expensive
  };

  // Request metadata
  meta: {
    request_id: string;
    timestamp: string;
  };
}

// Example: List users response
const usersResponse: CollectionResponse<User> = {
  object: 'list',
  data: [
    {
      id: 'usr_123',
      object: 'user',
      email: 'john@example.com',
      name: 'John Doe',
      status: 'active',
      role: 'user',
      organization_id: 'org_456',
      metadata: {},
      created_at: '2024-01-15T10:00:00Z',
      updated_at: '2024-01-15T10:00:00Z',
    },
  ],
  pagination: {
    page_size: 20,
    has_more: true,
    next_cursor: 'eyJpZCI6InVzcl8xMjMifQ==',
  },
  meta: {
    request_id: 'req_abc123',
    timestamp: '2024-01-15T12:00:00Z',
  },
};
```

### Filtering and Sorting

```typescript
// Filtering patterns
interface FilterPatterns {
  // Equality
  exact: '/users?status=active';
  multiple: '/users?status=active,inactive';

  // Comparison
  greaterThan: '/orders?total__gt=100';
  lessThan: '/orders?total__lt=1000';
  range: '/orders?created_at__gte=2024-01-01&created_at__lt=2024-02-01';

  // Text search
  contains: '/products?name__contains=phone';
  search: '/products?q=wireless+headphones';

  // Nested fields
  nested: '/users?profile.country=US';
}

// Sorting patterns
interface SortPatterns {
  // Single field
  ascending: '/users?sort=created_at';
  descending: '/users?sort=-created_at';

  // Multiple fields
  multiple: '/users?sort=-created_at,name';

  // Alternative syntax
  explicit: '/users?sort_by=created_at&sort_order=desc';
}

// Field selection
interface FieldSelection {
  // Include specific fields
  include: '/users?fields=id,name,email';

  // Expand relationships
  expand: '/users?expand=organization,roles';

  // Combine
  combined: '/users?fields=id,name&expand=organization';
}

// Implementation
function parseFilters(query: Record<string, string>): Filter[] {
  const filters: Filter[] = [];

  for (const [key, value] of Object.entries(query)) {
    if (key.includes('__')) {
      const [field, operator] = key.split('__');
      filters.push({ field, operator, value });
    } else if (!['sort', 'fields', 'expand', 'page_size', 'cursor'].includes(key)) {
      filters.push({ field: key, operator: 'eq', value });
    }
  }

  return filters;
}
```

## HTTP Methods

```
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP Method Usage                             │
├──────────┬────────────────┬────────────┬───────────────────────┤
│ Method   │ Operation      │ Idempotent │ Request Body          │
├──────────┼────────────────┼────────────┼───────────────────────┤
│ GET      │ Read           │ Yes        │ No                    │
│ POST     │ Create         │ No*        │ Yes                   │
│ PUT      │ Replace        │ Yes        │ Yes                   │
│ PATCH    │ Partial Update │ No*        │ Yes                   │
│ DELETE   │ Remove         │ Yes        │ No (usually)          │
├──────────┴────────────────┴────────────┴───────────────────────┤
│ * Can be made idempotent with idempotency keys                 │
└─────────────────────────────────────────────────────────────────┘
```

### Method Guidelines

```typescript
// GET - Retrieve resources
// Never modify state, always cacheable
app.get('/users/:id', async (req, res) => {
  const user = await userService.findById(req.params.id);
  res.json({ data: user });
});

// POST - Create new resources
// Returns 201 with Location header
app.post('/users', async (req, res) => {
  const user = await userService.create(req.body);
  res.status(201).header('Location', `/users/${user.id}`).json({ data: user });
});

// PUT - Replace entire resource
// Client sends complete representation
app.put('/users/:id', async (req, res) => {
  const user = await userService.replace(req.params.id, req.body);
  res.json({ data: user });
});

// PATCH - Partial update
// Client sends only changed fields
app.patch('/users/:id', async (req, res) => {
  const user = await userService.update(req.params.id, req.body);
  res.json({ data: user });
});

// DELETE - Remove resource
// Returns 204 No Content or 200 with deleted resource
app.delete('/users/:id', async (req, res) => {
  await userService.delete(req.params.id);
  res.status(204).send();
});
```

## Status Codes

```
┌─────────────────────────────────────────────────────────────────┐
│                    HTTP Status Codes                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  2xx Success                                                    │
│  ├── 200 OK           - Request succeeded                       │
│  ├── 201 Created      - Resource created                        │
│  ├── 202 Accepted     - Async processing started                │
│  └── 204 No Content   - Success, no response body               │
│                                                                  │
│  4xx Client Errors                                              │
│  ├── 400 Bad Request  - Invalid request syntax                  │
│  ├── 401 Unauthorized - Authentication required                 │
│  ├── 403 Forbidden    - Permission denied                       │
│  ├── 404 Not Found    - Resource doesn't exist                  │
│  ├── 409 Conflict     - Resource conflict                       │
│  ├── 422 Unprocessable- Validation failed                       │
│  └── 429 Too Many     - Rate limit exceeded                     │
│                                                                  │
│  5xx Server Errors                                              │
│  ├── 500 Internal     - Server error                            │
│  ├── 502 Bad Gateway  - Upstream error                          │
│  ├── 503 Unavailable  - Service temporarily down                │
│  └── 504 Timeout      - Gateway timeout                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Status Code Selection

```typescript
// Status code decision tree
function selectStatusCode(context: RequestContext): number {
  // Success cases
  if (context.operation === 'create' && context.success) {
    return 201; // Created
  }
  if (context.operation === 'delete' && context.success) {
    return 204; // No Content
  }
  if (context.async) {
    return 202; // Accepted
  }
  if (context.success) {
    return 200; // OK
  }

  // Error cases
  if (context.error === 'validation') {
    return 400; // Bad Request (syntax) or 422 (semantic)
  }
  if (context.error === 'authentication') {
    return 401; // Unauthorized
  }
  if (context.error === 'authorization') {
    return 403; // Forbidden
  }
  if (context.error === 'not_found') {
    return 404; // Not Found
  }
  if (context.error === 'conflict') {
    return 409; // Conflict
  }
  if (context.error === 'rate_limit') {
    return 429; // Too Many Requests
  }

  return 500; // Internal Server Error
}
```

## Request Validation

```typescript
import { z } from 'zod';

// Schema definitions
const CreateUserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100),
  password: z.string().min(8).max(72),
  role: z.enum(['user', 'admin']).optional().default('user'),
  metadata: z.record(z.string()).optional().default({}),
});

const UpdateUserSchema = CreateUserSchema.partial().omit({ password: true });

const QueryParamsSchema = z.object({
  page_size: z.coerce.number().min(1).max(100).optional().default(20),
  cursor: z.string().optional(),
  sort: z.string().optional(),
  status: z.enum(['active', 'inactive', 'all']).optional().default('all'),
});

// Validation middleware
function validate<T>(schema: z.ZodSchema<T>, source: 'body' | 'query' | 'params') {
  return (req: Request, res: Response, next: NextFunction) => {
    const result = schema.safeParse(req[source]);

    if (!result.success) {
      return res.status(400).json({
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Request validation failed',
          details: result.error.errors.map((err) => ({
            field: err.path.join('.'),
            code: err.code,
            message: err.message,
          })),
        },
      });
    }

    req[source] = result.data;
    next();
  };
}

// Usage
app.post('/users', validate(CreateUserSchema, 'body'), createUser);

app.patch('/users/:id', validate(UpdateUserSchema, 'body'), updateUser);

app.get('/users', validate(QueryParamsSchema, 'query'), listUsers);
```

## Response Formatting

```typescript
// Response helper functions
class ApiResponse {
  static success<T>(data: T, meta?: ResponseMeta): SuccessResponse<T> {
    return {
      data,
      meta: {
        request_id: meta?.requestId || generateRequestId(),
        timestamp: new Date().toISOString(),
        ...meta,
      },
    };
  }

  static created<T>(data: T, location: string): SuccessResponse<T> {
    return {
      data,
      meta: {
        request_id: generateRequestId(),
        timestamp: new Date().toISOString(),
        location,
      },
    };
  }

  static list<T>(
    data: T[],
    pagination: PaginationInfo,
    meta?: ResponseMeta
  ): CollectionResponse<T> {
    return {
      object: 'list',
      data,
      pagination,
      meta: {
        request_id: meta?.requestId || generateRequestId(),
        timestamp: new Date().toISOString(),
        ...meta,
      },
    };
  }

  static error(
    code: string,
    message: string,
    statusCode: number,
    details?: ErrorDetail[]
  ): ErrorResponse {
    return {
      error: {
        code,
        message,
        details,
        request_id: generateRequestId(),
        documentation_url: `https://docs.example.com/errors#${code}`,
      },
    };
  }
}

// Usage in controllers
async function createUser(req: Request, res: Response) {
  try {
    const user = await userService.create(req.body);
    res
      .status(201)
      .header('Location', `/users/${user.id}`)
      .json(ApiResponse.created(user, `/users/${user.id}`));
  } catch (error) {
    if (error instanceof ValidationError) {
      res.status(400).json(ApiResponse.error('VALIDATION_ERROR', error.message, 400, error.details));
    } else {
      throw error;
    }
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  API Design Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Be Consistent                                               │
│     └── Same patterns, naming, errors everywhere                │
│                                                                  │
│  2. Be Explicit                                                 │
│     └── Clear names, documented behavior, no surprises          │
│                                                                  │
│  3. Be Minimal                                                  │
│     └── Only expose what's needed, YAGNI principle              │
│                                                                  │
│  4. Be Secure                                                   │
│     └── Validate all input, sanitize output, auth everywhere    │
│                                                                  │
│  5. Be Responsive                                               │
│     └── Fast responses, clear errors, helpful messages          │
│                                                                  │
│  6. Be Documented                                               │
│     └── OpenAPI spec, examples, guides, changelogs              │
│                                                                  │
│  7. Be Versioned                                                │
│     └── Clear versioning strategy, migration paths              │
│                                                                  │
│  8. Be Monitored                                                │
│     └── Logging, metrics, alerting, tracing                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
