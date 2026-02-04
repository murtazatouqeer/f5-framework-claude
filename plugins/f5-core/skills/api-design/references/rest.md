# REST API Design Reference

## REST Principles

### Six Constraints

1. **Client-Server**: Separation of concerns between UI and data storage
2. **Stateless**: Each request contains all information needed
3. **Cacheable**: Responses must define cacheability
4. **Uniform Interface**: Standardized communication
5. **Layered System**: Client doesn't know if connected to end server
6. **Code on Demand** (optional): Server can extend client functionality

### Resource-Oriented Design

```
Resources are nouns, not verbs:
✅ GET /users              (list users)
✅ POST /users             (create user)
✅ GET /users/{id}         (get user)
✅ PATCH /users/{id}       (update user)
✅ DELETE /users/{id}      (delete user)

❌ GET /getUsers
❌ POST /createUser
❌ POST /deleteUser
```

### Resource Naming

```
✅ Correct:
/users                     Plural nouns
/users/{userId}/orders     Nested resources
/search?q=term             Query for searches

❌ Avoid:
/user                      Singular (inconsistent)
/getUsers                  Verb in URL
/users/getOrders           Verb in URL
```

## HTTP Methods

### Method Semantics

```typescript
// GET - Retrieve resource (safe, idempotent)
GET /api/v1/users
GET /api/v1/users/123

// POST - Create resource (not idempotent)
POST /api/v1/users
Content-Type: application/json
{"name": "John", "email": "john@example.com"}

// PUT - Replace resource (idempotent)
PUT /api/v1/users/123
Content-Type: application/json
{"name": "John Smith", "email": "john@example.com", "role": "admin"}

// PATCH - Partial update (can be idempotent)
PATCH /api/v1/users/123
Content-Type: application/json
{"name": "John Smith"}

// DELETE - Remove resource (idempotent)
DELETE /api/v1/users/123
```

### Method Properties

| Method | Idempotent | Safe | Cacheable | Request Body |
|--------|------------|------|-----------|--------------|
| GET | Yes | Yes | Yes | No |
| HEAD | Yes | Yes | Yes | No |
| POST | No | No | Rarely | Yes |
| PUT | Yes | No | No | Yes |
| PATCH | No* | No | No | Yes |
| DELETE | Yes | No | No | No |
| OPTIONS | Yes | Yes | No | No |

## HTTP Status Codes

### Success (2xx)

```http
200 OK                     # Successful GET, PUT, PATCH
201 Created                # Successful POST (include Location header)
202 Accepted               # Async operation started
204 No Content             # Successful DELETE
206 Partial Content        # Range request
```

### Client Errors (4xx)

```http
400 Bad Request            # Malformed syntax, invalid JSON
401 Unauthorized           # Authentication required/failed
403 Forbidden              # Authenticated but not authorized
404 Not Found              # Resource doesn't exist
405 Method Not Allowed     # HTTP method not supported
409 Conflict               # Resource conflict (duplicate)
410 Gone                   # Resource permanently deleted
422 Unprocessable Entity   # Validation errors
429 Too Many Requests      # Rate limit exceeded
```

### Server Errors (5xx)

```http
500 Internal Server Error  # Unexpected server error
502 Bad Gateway            # Upstream service error
503 Service Unavailable    # Temporary maintenance
504 Gateway Timeout        # Upstream timeout
```

### Decision Tree

```
Request successful?
├── Yes → GET/PUT/PATCH: 200, POST: 201, DELETE: 204, Async: 202
└── No
    ├── Client's fault?
    │   ├── Bad syntax → 400
    │   ├── Not authenticated → 401
    │   ├── Not authorized → 403
    │   ├── Not found → 404
    │   ├── Conflict → 409
    │   ├── Validation failed → 422
    │   └── Rate limited → 429
    └── Server's fault?
        ├── Internal error → 500
        ├── Upstream invalid → 502
        ├── Maintenance → 503
        └── Upstream timeout → 504
```

## Pagination

### Offset-Based Pagination

```http
GET /api/v1/users?page=2&limit=20

Response:
{
  "data": [...],
  "meta": {
    "total": 100,
    "page": 2,
    "limit": 20,
    "total_pages": 5
  },
  "links": {
    "self": "/api/v1/users?page=2&limit=20",
    "first": "/api/v1/users?page=1&limit=20",
    "prev": "/api/v1/users?page=1&limit=20",
    "next": "/api/v1/users?page=3&limit=20",
    "last": "/api/v1/users?page=5&limit=20"
  }
}
```

**Best for**: Small datasets, admin panels, search results

### Cursor-Based Pagination

```http
GET /api/v1/posts?limit=20
GET /api/v1/posts?limit=20&cursor=eyJpZCI6InBvc3RfMjAifQ

Response:
{
  "data": [...],
  "meta": { "has_more": true },
  "cursors": {
    "next": "eyJpZCI6InBvc3RfMjAiLCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNSJ9"
  }
}
```

**Best for**: Large datasets, infinite scroll, real-time feeds

### SQL Implementation

```sql
-- Offset (slow on large tables)
SELECT * FROM users ORDER BY created_at DESC LIMIT 20 OFFSET 40;

-- Cursor (fast, uses index)
SELECT * FROM users
WHERE (created_at, id) < ('2024-01-14', 'usr_20')
ORDER BY created_at DESC, id DESC
LIMIT 21;  -- Fetch one extra to check has_more
```

## Versioning

### URL Path Versioning (Most Common)

```http
GET /api/v1/users
GET /api/v2/users
```

**Pros**: Easy to understand, visible in browser
**Cons**: Not truly RESTful, URL pollution

### Header Versioning

```http
GET /api/users
X-API-Version: 2

# Or Accept header
Accept: application/vnd.myapi.v2+json
```

**Pros**: Clean URLs, more RESTful
**Cons**: Less visible, harder to test

### Date-Based Versioning (Stripe-style)

```http
GET /api/users
Stripe-Version: 2024-01-01
```

**Pros**: Clear timeline, gradual rollout
**Cons**: Many versions, complex compatibility

### Version Transformation

```typescript
const transformers = {
  v1: {
    user: (user: User) => ({
      id: user.id,
      name: `${user.firstName} ${user.lastName}`,
      email: user.email,
    }),
  },
  v2: {
    user: (user: User) => ({
      id: user.id,
      first_name: user.firstName,
      last_name: user.lastName,
      email: user.email,
      created_at: user.createdAt.toISOString(),
    }),
  },
};
```

### Deprecation Strategy

```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Jun 2024 00:00:00 GMT
Link: <https://api.example.com/v2/users>; rel="successor-version"

{
  "data": [...],
  "meta": {
    "deprecation_notice": "This API version is deprecated. Migrate to v2 by June 1, 2024."
  }
}
```

## Filtering and Sorting

### Query Parameters

```http
# Filtering
GET /api/v1/users?status=active&role=admin
GET /api/v1/users?created_after=2024-01-01
GET /api/v1/orders?status[]=pending&status[]=processing

# Sorting
GET /api/v1/users?sort=created_at:desc
GET /api/v1/users?sort=-created_at  # Prefix - for descending
GET /api/v1/users?sort=name:asc,created_at:desc

# Field selection
GET /api/v1/users?fields=id,name,email
```

### Implementation

```typescript
interface QueryParams {
  filter?: Record<string, string | string[]>;
  sort?: Array<{ field: string; order: 'asc' | 'desc' }>;
  fields?: string[];
  page?: number;
  limit?: number;
}

function buildQuery(params: QueryParams) {
  let query = db.users;

  // Apply filters
  if (params.filter) {
    Object.entries(params.filter).forEach(([key, value]) => {
      query = query.where(key, Array.isArray(value) ? 'in' : '=', value);
    });
  }

  // Apply sorting
  if (params.sort) {
    params.sort.forEach(({ field, order }) => {
      query = query.orderBy(field, order);
    });
  }

  // Apply field selection
  if (params.fields) {
    query = query.select(params.fields);
  }

  return query;
}
```

## HATEOAS (Level 3 REST)

### Hypermedia Responses

```json
{
  "data": {
    "id": "order_123",
    "status": "pending",
    "total": 99.99
  },
  "links": {
    "self": { "href": "/api/v1/orders/order_123" },
    "cancel": { "href": "/api/v1/orders/order_123/cancel", "method": "POST" },
    "pay": { "href": "/api/v1/orders/order_123/pay", "method": "POST" },
    "items": { "href": "/api/v1/orders/order_123/items" }
  }
}
```

### State-Driven Links

```typescript
function getOrderLinks(order: Order) {
  const links: Record<string, Link> = {
    self: { href: `/api/v1/orders/${order.id}` },
  };

  // Available actions depend on order state
  switch (order.status) {
    case 'pending':
      links.cancel = { href: `/api/v1/orders/${order.id}/cancel`, method: 'POST' };
      links.pay = { href: `/api/v1/orders/${order.id}/pay`, method: 'POST' };
      break;
    case 'paid':
      links.ship = { href: `/api/v1/orders/${order.id}/ship`, method: 'POST' };
      links.refund = { href: `/api/v1/orders/${order.id}/refund`, method: 'POST' };
      break;
    case 'shipped':
      links.track = { href: `/api/v1/orders/${order.id}/tracking` };
      break;
  }

  return links;
}
```

## Caching

### Cache Headers

```http
# Response headers
Cache-Control: max-age=3600, private
ETag: "abc123"
Last-Modified: Wed, 15 Jan 2024 10:00:00 GMT

# Request headers for validation
If-None-Match: "abc123"
If-Modified-Since: Wed, 15 Jan 2024 10:00:00 GMT

# Conditional response
HTTP/1.1 304 Not Modified
```

### Cache-Control Directives

```
public          # Can be cached by shared caches
private         # Only browser can cache
no-cache        # Must revalidate before using
no-store        # Don't cache at all
max-age=3600    # Cache for 1 hour
s-maxage=3600   # Shared cache max age
must-revalidate # Must check after expiry
```

## Best Practices

1. **Use nouns, not verbs** for resource URLs
2. **Version from day one** - easier than adding later
3. **Use appropriate status codes** - be specific
4. **Consistent error format** across all endpoints
5. **Include request IDs** for debugging
6. **Implement pagination** for all list endpoints
7. **Use HTTPS** always
8. **Document with OpenAPI** specification
