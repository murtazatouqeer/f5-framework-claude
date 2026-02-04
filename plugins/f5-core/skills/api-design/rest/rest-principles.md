---
name: rest-principles
description: RESTful API design principles and constraints
category: api-design/rest
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# REST Principles

## Overview

REST (Representational State Transfer) is an architectural style for designing
networked applications. It relies on stateless, client-server communication,
typically over HTTP.

## Core Constraints

```
┌─────────────────────────────────────────────────────────────────┐
│                    REST Architectural Constraints                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Client-Server Separation                                    │
│     ├── Client handles UI/UX                                    │
│     ├── Server handles data storage and business logic          │
│     └── Independent evolution of both sides                     │
│                                                                  │
│  2. Statelessness                                                │
│     ├── Each request contains all information needed            │
│     ├── No session state stored on server                       │
│     └── Enables horizontal scaling                               │
│                                                                  │
│  3. Cacheability                                                 │
│     ├── Responses define themselves as cacheable or not         │
│     ├── Reduces client-server interactions                      │
│     └── Improves scalability and performance                    │
│                                                                  │
│  4. Uniform Interface                                            │
│     ├── Resource identification (URIs)                          │
│     ├── Resource manipulation through representations           │
│     ├── Self-descriptive messages                               │
│     └── HATEOAS (Hypermedia as Engine of Application State)     │
│                                                                  │
│  5. Layered System                                               │
│     ├── Client cannot tell if connected directly to server      │
│     ├── Allows load balancers, proxies, gateways                │
│     └── Improves scalability and security                       │
│                                                                  │
│  6. Code on Demand (Optional)                                   │
│     ├── Server can send executable code to client               │
│     └── Extends client functionality                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Resource-Oriented Design

### Resources are Nouns, Not Verbs

```
# Correct - Resources as nouns
✅ GET /users              # List users
✅ GET /users/123          # Get specific user
✅ POST /users             # Create user
✅ PUT /users/123          # Update user
✅ DELETE /users/123       # Delete user

# Incorrect - Action-based (RPC-style)
❌ GET /getUsers
❌ GET /getUserById?id=123
❌ POST /createUser
❌ POST /deleteUser?id=123
❌ GET /user/delete/123
```

### Resource Relationships

```
# Hierarchical resources
GET /users/123/orders           # User's orders
GET /users/123/orders/456       # Specific order
GET /users/123/orders/456/items # Order items

# Alternative: Query parameters for filtering
GET /orders?user_id=123         # Filter orders by user

# When to use each:
# - Hierarchical: Strong ownership (user owns orders)
# - Query params: Loose association (search across all orders)
```

## URL Structure

```
https://api.example.com/v1/users/123/orders?status=pending&limit=10
\___/   \_____________/\__/\____/\_________/\___________________/
  |           |         |    |       |              |
scheme      host     version resource  sub-       query params
                              |       resource
                           collection
```

## HTTP Methods Semantics

```typescript
// GET - Retrieve resource(s) - Safe & Idempotent
GET /users              // List all users
GET /users/123          // Get user 123
GET /users/123/orders   // Get user's orders

// POST - Create new resource - NOT Idempotent
POST /users             // Create user
POST /users/123/orders  // Create order for user
POST /orders/123/cancel // Action on resource (when no better verb)

// PUT - Replace entire resource - Idempotent
PUT /users/123          // Replace user 123 completely
// Must include ALL fields, missing fields set to null/default

// PATCH - Partial update - NOT necessarily Idempotent
PATCH /users/123        // Update some fields of user 123
// Include only fields to update

// DELETE - Remove resource - Idempotent
DELETE /users/123       // Delete user 123
DELETE /users/123/avatar // Delete user's avatar
```

## Request/Response Examples

### List Resources (GET Collection)

```http
GET /api/v1/users?page=1&limit=20&sort=-created_at HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Accept: application/json
```

```json
{
  "data": [
    {
      "id": "usr_123",
      "type": "user",
      "attributes": {
        "name": "John Doe",
        "email": "john@example.com",
        "status": "active",
        "created_at": "2024-01-15T10:30:00Z"
      },
      "links": {
        "self": "/api/v1/users/usr_123"
      }
    }
  ],
  "meta": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "total_pages": 5
  },
  "links": {
    "self": "/api/v1/users?page=1&limit=20",
    "first": "/api/v1/users?page=1&limit=20",
    "next": "/api/v1/users?page=2&limit=20",
    "last": "/api/v1/users?page=5&limit=20"
  }
}
```

### Get Single Resource (GET Item)

```http
GET /api/v1/users/usr_123 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Accept: application/json
```

```json
{
  "data": {
    "id": "usr_123",
    "type": "user",
    "attributes": {
      "name": "John Doe",
      "email": "john@example.com",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    "relationships": {
      "orders": {
        "links": {
          "related": "/api/v1/users/usr_123/orders"
        }
      }
    },
    "links": {
      "self": "/api/v1/users/usr_123"
    }
  }
}
```

### Create Resource (POST)

```http
POST /api/v1/users HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "SecurePass123!"
}
```

```http
HTTP/1.1 201 Created
Location: /api/v1/users/usr_456
Content-Type: application/json

{
  "data": {
    "id": "usr_456",
    "type": "user",
    "attributes": {
      "name": "Jane Doe",
      "email": "jane@example.com",
      "status": "active",
      "created_at": "2024-01-15T11:00:00Z"
    },
    "links": {
      "self": "/api/v1/users/usr_456"
    }
  }
}
```

### Update Resource (PATCH)

```http
PATCH /api/v1/users/usr_456 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Jane Smith"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "id": "usr_456",
    "type": "user",
    "attributes": {
      "name": "Jane Smith",
      "email": "jane@example.com",
      "status": "active",
      "updated_at": "2024-01-15T12:00:00Z"
    }
  }
}
```

### Delete Resource (DELETE)

```http
DELETE /api/v1/users/usr_456 HTTP/1.1
Host: api.example.com
Authorization: Bearer <token>
```

```http
HTTP/1.1 204 No Content
```

## HATEOAS (Hypermedia)

Hypermedia as the Engine of Application State enables API discoverability.

```json
{
  "data": {
    "id": "ord_789",
    "type": "order",
    "attributes": {
      "status": "pending",
      "total": 99.99,
      "currency": "USD"
    },
    "links": {
      "self": "/api/v1/orders/ord_789",
      "customer": "/api/v1/users/usr_123",
      "items": "/api/v1/orders/ord_789/items",
      "shipping": "/api/v1/orders/ord_789/shipping"
    },
    "actions": {
      "cancel": {
        "href": "/api/v1/orders/ord_789/cancel",
        "method": "POST",
        "title": "Cancel this order"
      },
      "pay": {
        "href": "/api/v1/orders/ord_789/pay",
        "method": "POST",
        "title": "Pay for this order",
        "fields": [
          {"name": "payment_method", "type": "string", "required": true}
        ]
      }
    }
  }
}
```

### Benefits of HATEOAS

```
┌─────────────────────────────────────────────────────────────────┐
│                    HATEOAS Benefits                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Discoverability                                             │
│     └── Clients discover available actions from response        │
│                                                                  │
│  2. Decoupling                                                   │
│     └── URLs can change without breaking clients                │
│                                                                  │
│  3. Self-Documentation                                          │
│     └── API describes itself through links                      │
│                                                                  │
│  4. State-Driven UI                                             │
│     └── Available actions depend on resource state              │
│         (e.g., "cancel" only shown for pending orders)          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Content Negotiation

```http
# Request specific format
GET /api/v1/users HTTP/1.1
Accept: application/json

# Request specific version via header
GET /api/v1/users HTTP/1.1
Accept: application/vnd.api.v2+json

# Request different representation
GET /api/v1/reports/sales HTTP/1.1
Accept: text/csv

GET /api/v1/reports/sales HTTP/1.1
Accept: application/pdf
```

## Caching Headers

```http
# Response with caching headers
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: private, max-age=3600
ETag: "abc123"
Last-Modified: Mon, 15 Jan 2024 10:00:00 GMT

# Conditional request
GET /api/v1/users/123 HTTP/1.1
If-None-Match: "abc123"

# Response if not modified
HTTP/1.1 304 Not Modified
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   REST Best Practices                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use Nouns for Resources                                     │
│     ✅ /users, /orders, /products                               │
│     ❌ /getUsers, /createOrder                                  │
│                                                                  │
│  2. Use Plural Nouns                                            │
│     ✅ /users/123                                               │
│     ❌ /user/123                                                │
│                                                                  │
│  3. Use Lowercase and Hyphens                                   │
│     ✅ /user-profiles                                           │
│     ❌ /userProfiles, /user_profiles                            │
│                                                                  │
│  4. Don't Include File Extensions                               │
│     ✅ /users (use Accept header)                               │
│     ❌ /users.json                                              │
│                                                                  │
│  5. Use Query Parameters for Filtering                          │
│     ✅ /users?status=active                                     │
│     ❌ /users/active                                            │
│                                                                  │
│  6. Version Your API                                            │
│     ✅ /v1/users or Accept: application/vnd.api.v1+json         │
│                                                                  │
│  7. Use Proper HTTP Status Codes                                │
│     └── 2xx for success, 4xx for client errors, 5xx for server  │
│                                                                  │
│  8. Provide Meaningful Error Messages                           │
│     └── Include error code, message, and details                │
│                                                                  │
│  9. Support Pagination for Lists                                │
│     └── Use consistent pagination parameters                    │
│                                                                  │
│  10. Use SSL/TLS for All Endpoints                              │
│      └── Always HTTPS, never HTTP                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Common Anti-Patterns

```
# Anti-pattern: Verbs in URLs
❌ POST /api/createUser
❌ GET /api/getUser/123
❌ POST /api/user/123/delete

# Better: Use HTTP methods
✅ POST /api/users
✅ GET /api/users/123
✅ DELETE /api/users/123

# Anti-pattern: Deeply nested resources
❌ /users/123/orders/456/items/789/reviews/012

# Better: Flatten when relationship is weak
✅ /order-items/789/reviews/012
✅ /reviews/012

# Anti-pattern: Returning 200 for errors
❌ HTTP 200 OK
   {"success": false, "error": "User not found"}

# Better: Use proper status codes
✅ HTTP 404 Not Found
   {"error": {"code": "NOT_FOUND", "message": "User not found"}}
```
