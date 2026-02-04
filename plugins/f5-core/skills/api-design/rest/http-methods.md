---
name: http-methods
description: HTTP methods semantics and proper usage in REST APIs
category: api-design/rest
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# HTTP Methods

## Overview

HTTP methods (verbs) define the action to perform on a resource.
Understanding their semantics is crucial for RESTful API design.

## Method Properties

```
┌─────────────────────────────────────────────────────────────────┐
│                   HTTP Method Properties                         │
├──────────┬────────────┬──────┬───────────┬─────────────────────┤
│ Method   │ Idempotent │ Safe │ Cacheable │ Request Body        │
├──────────┼────────────┼──────┼───────────┼─────────────────────┤
│ GET      │ Yes        │ Yes  │ Yes       │ No                  │
│ HEAD     │ Yes        │ Yes  │ Yes       │ No                  │
│ POST     │ No         │ No   │ No*       │ Yes                 │
│ PUT      │ Yes        │ No   │ No        │ Yes                 │
│ PATCH    │ No*        │ No   │ No        │ Yes                 │
│ DELETE   │ Yes        │ No   │ No        │ Optional            │
│ OPTIONS  │ Yes        │ Yes  │ No        │ No                  │
└──────────┴────────────┴──────┴───────────┴─────────────────────┘

* POST can be cacheable if response includes caching headers
* PATCH can be idempotent depending on implementation
```

### Key Definitions

```
┌─────────────────────────────────────────────────────────────────┐
│                   Method Property Definitions                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Safe:                                                           │
│  └── Does not modify server state                               │
│      (GET, HEAD, OPTIONS)                                       │
│                                                                  │
│  Idempotent:                                                     │
│  └── Multiple identical requests have same effect as one        │
│      (GET, PUT, DELETE, HEAD, OPTIONS)                          │
│                                                                  │
│  Cacheable:                                                      │
│  └── Response can be stored and reused                          │
│      (GET, HEAD by default)                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## GET - Retrieve Resources

**Purpose**: Retrieve resource(s) without modifying server state.

```http
# List collection
GET /api/v1/users HTTP/1.1
Host: api.example.com
Accept: application/json

# Get single resource
GET /api/v1/users/usr_123 HTTP/1.1
Host: api.example.com
Accept: application/json

# With query parameters
GET /api/v1/users?status=active&sort=-created_at&limit=20 HTTP/1.1
Host: api.example.com
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: private, max-age=60
ETag: "abc123"

{
  "data": [
    {"id": "usr_123", "name": "John Doe", "email": "john@example.com"}
  ],
  "meta": {"total": 100, "page": 1}
}
```

### GET Best Practices

```
✅ Return 200 OK with resource data
✅ Return 404 Not Found if resource doesn't exist
✅ Support filtering via query parameters
✅ Include caching headers
✅ Keep URLs reasonable length (<2000 chars)

❌ Don't modify server state
❌ Don't require request body
❌ Don't return 200 for errors
```

## POST - Create Resources

**Purpose**: Create new resources or trigger operations.

```http
# Create resource
POST /api/v1/users HTTP/1.1
Host: api.example.com
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
    "name": "Jane Doe",
    "email": "jane@example.com",
    "created_at": "2024-01-15T10:00:00Z"
  }
}
```

### POST for Actions

```http
# Trigger action (when no better method fits)
POST /api/v1/orders/ord_123/cancel HTTP/1.1
Content-Type: application/json

{
  "reason": "Customer request",
  "notify_customer": true
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "id": "ord_123",
    "status": "cancelled",
    "cancelled_at": "2024-01-15T10:00:00Z"
  }
}
```

### POST Best Practices

```
✅ Return 201 Created with Location header
✅ Return created resource in response body
✅ Validate input thoroughly
✅ Generate server-side IDs
✅ Use for non-idempotent operations

❌ Don't use for retrieving data
❌ Don't assume idempotency
❌ Don't return 200 for creation (use 201)
```

## PUT - Replace Resources

**Purpose**: Replace entire resource with new representation.

```http
# Replace entire resource
PUT /api/v1/users/usr_123 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "name": "John Smith",
  "email": "john.smith@example.com",
  "status": "active",
  "settings": {
    "notifications": true,
    "theme": "dark"
  }
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "id": "usr_123",
    "name": "John Smith",
    "email": "john.smith@example.com",
    "status": "active",
    "settings": {
      "notifications": true,
      "theme": "dark"
    },
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### PUT Semantics

```
┌─────────────────────────────────────────────────────────────────┐
│                   PUT Behavior                                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  PUT replaces the ENTIRE resource:                              │
│                                                                  │
│  Before PUT:                                                     │
│  {                                                               │
│    "name": "John Doe",                                          │
│    "email": "john@example.com",                                 │
│    "phone": "555-1234"                                          │
│  }                                                               │
│                                                                  │
│  PUT with:                                                       │
│  {                                                               │
│    "name": "John Smith",                                        │
│    "email": "john@example.com"                                  │
│  }                                                               │
│                                                                  │
│  After PUT:                                                      │
│  {                                                               │
│    "name": "John Smith",                                        │
│    "email": "john@example.com",                                 │
│    "phone": null  ← Field removed/nulled!                       │
│  }                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### PUT Best Practices

```
✅ Include ALL fields in request
✅ Return 200 OK with updated resource
✅ Return 201 Created if resource didn't exist (upsert)
✅ Treat as idempotent (same request = same result)

❌ Don't use for partial updates (use PATCH)
❌ Don't change resource ID
```

## PATCH - Partial Update

**Purpose**: Apply partial modifications to a resource.

```http
# Partial update
PATCH /api/v1/users/usr_123 HTTP/1.1
Host: api.example.com
Content-Type: application/json

{
  "name": "John Smith"
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "data": {
    "id": "usr_123",
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "555-1234",
    "updated_at": "2024-01-15T10:00:00Z"
  }
}
```

### JSON Patch Format (RFC 6902)

```http
PATCH /api/v1/users/usr_123 HTTP/1.1
Content-Type: application/json-patch+json

[
  {"op": "replace", "path": "/name", "value": "John Smith"},
  {"op": "add", "path": "/phone", "value": "555-5678"},
  {"op": "remove", "path": "/fax"},
  {"op": "move", "from": "/old_field", "path": "/new_field"},
  {"op": "copy", "from": "/email", "path": "/backup_email"},
  {"op": "test", "path": "/version", "value": 1}
]
```

### JSON Merge Patch (RFC 7396)

```http
PATCH /api/v1/users/usr_123 HTTP/1.1
Content-Type: application/merge-patch+json

{
  "name": "John Smith",
  "phone": null,
  "settings": {
    "theme": "light"
  }
}
```

### PATCH Best Practices

```
✅ Only include fields to update
✅ Return 200 OK with full updated resource
✅ Support both JSON Patch and Merge Patch
✅ Validate partial data

❌ Don't require all fields
❌ Don't ignore provided null values
```

## DELETE - Remove Resources

**Purpose**: Remove a resource.

```http
# Delete resource
DELETE /api/v1/users/usr_123 HTTP/1.1
Host: api.example.com
```

```http
HTTP/1.1 204 No Content
```

### DELETE Variations

```http
# Soft delete (mark as deleted)
DELETE /api/v1/users/usr_123 HTTP/1.1

HTTP/1.1 200 OK
{
  "data": {
    "id": "usr_123",
    "status": "deleted",
    "deleted_at": "2024-01-15T10:00:00Z"
  }
}

# Delete with body (bulk delete)
DELETE /api/v1/users HTTP/1.1
Content-Type: application/json

{
  "ids": ["usr_123", "usr_456", "usr_789"]
}

# Alternative: Bulk delete via query
DELETE /api/v1/users?ids=usr_123,usr_456,usr_789
```

### DELETE Best Practices

```
✅ Return 204 No Content (preferred)
✅ Return 200 OK if returning deleted resource
✅ Return 404 if resource doesn't exist
✅ Handle already-deleted gracefully (idempotent)

❌ Don't return 200 with empty body
❌ Don't delete related resources without warning
```

## HEAD - Get Metadata

**Purpose**: Same as GET but without response body. Used to check existence or get headers.

```http
HEAD /api/v1/users/usr_123 HTTP/1.1
Host: api.example.com
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Content-Length: 256
ETag: "abc123"
Last-Modified: Mon, 15 Jan 2024 10:00:00 GMT
```

### HEAD Use Cases

```
# Check if resource exists
HEAD /api/v1/files/file_123
→ 200 OK (exists) or 404 Not Found

# Get metadata without downloading
HEAD /api/v1/files/large-file.zip
→ Content-Length: 1073741824

# Check for updates (conditional request)
HEAD /api/v1/users/usr_123
If-None-Match: "abc123"
→ 304 Not Modified or 200 OK with new ETag
```

## OPTIONS - Get Capabilities

**Purpose**: Describe communication options for a resource.

```http
OPTIONS /api/v1/users HTTP/1.1
Host: api.example.com
```

```http
HTTP/1.1 200 OK
Allow: GET, POST, HEAD, OPTIONS
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400
```

### CORS Preflight

```http
# Browser sends OPTIONS before cross-origin request
OPTIONS /api/v1/users HTTP/1.1
Host: api.example.com
Origin: https://app.example.com
Access-Control-Request-Method: POST
Access-Control-Request-Headers: Content-Type, Authorization

# Server responds with allowed options
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

## Method Mapping Guide

```
┌─────────────────────────────────────────────────────────────────┐
│                   CRUD to HTTP Method Mapping                    │
├────────────────┬────────────────────────────────────────────────┤
│ Operation      │ Method + Endpoint                               │
├────────────────┼────────────────────────────────────────────────┤
│ Create         │ POST /resources                                 │
│ Read (list)    │ GET /resources                                  │
│ Read (one)     │ GET /resources/{id}                             │
│ Update (full)  │ PUT /resources/{id}                             │
│ Update (part)  │ PATCH /resources/{id}                           │
│ Delete         │ DELETE /resources/{id}                          │
├────────────────┼────────────────────────────────────────────────┤
│ Search         │ GET /resources?q=term                           │
│                │ POST /resources/search (complex)                │
├────────────────┼────────────────────────────────────────────────┤
│ Action         │ POST /resources/{id}/action                     │
│ Bulk create    │ POST /resources/bulk                            │
│ Bulk update    │ PATCH /resources/bulk                           │
│ Bulk delete    │ DELETE /resources?ids=1,2,3                     │
└────────────────┴────────────────────────────────────────────────┘
```

## Implementation Example

```typescript
// Express.js router example
import { Router } from 'express';

const router = Router();

// GET /users - List users
router.get('/users', async (req, res) => {
  const { page = 1, limit = 20, status } = req.query;
  const users = await userService.list({ page, limit, status });
  res.json({ data: users.items, meta: users.pagination });
});

// GET /users/:id - Get single user
router.get('/users/:id', async (req, res) => {
  const user = await userService.findById(req.params.id);
  if (!user) {
    return res.status(404).json({
      error: { code: 'NOT_FOUND', message: 'User not found' }
    });
  }
  res.json({ data: user });
});

// POST /users - Create user
router.post('/users', async (req, res) => {
  const user = await userService.create(req.body);
  res.status(201)
    .header('Location', `/api/v1/users/${user.id}`)
    .json({ data: user });
});

// PUT /users/:id - Replace user
router.put('/users/:id', async (req, res) => {
  const user = await userService.replace(req.params.id, req.body);
  if (!user) {
    return res.status(404).json({
      error: { code: 'NOT_FOUND', message: 'User not found' }
    });
  }
  res.json({ data: user });
});

// PATCH /users/:id - Update user
router.patch('/users/:id', async (req, res) => {
  const user = await userService.update(req.params.id, req.body);
  if (!user) {
    return res.status(404).json({
      error: { code: 'NOT_FOUND', message: 'User not found' }
    });
  }
  res.json({ data: user });
});

// DELETE /users/:id - Delete user
router.delete('/users/:id', async (req, res) => {
  const deleted = await userService.delete(req.params.id);
  if (!deleted) {
    return res.status(404).json({
      error: { code: 'NOT_FOUND', message: 'User not found' }
    });
  }
  res.status(204).send();
});

// HEAD /users/:id - Check user exists
router.head('/users/:id', async (req, res) => {
  const exists = await userService.exists(req.params.id);
  res.status(exists ? 200 : 404).send();
});

// OPTIONS /users - Get allowed methods
router.options('/users', (req, res) => {
  res.header('Allow', 'GET, POST, HEAD, OPTIONS').send();
});

export default router;
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────────┐
│               HTTP Methods Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Use the right method for the operation                      │
│     └── Don't use POST for everything                           │
│                                                                  │
│  2. Respect method semantics                                    │
│     ├── GET should be safe (no side effects)                    │
│     ├── PUT/DELETE should be idempotent                         │
│     └── POST for non-idempotent operations                      │
│                                                                  │
│  3. Return appropriate status codes                             │
│     ├── 200 for successful GET/PUT/PATCH                        │
│     ├── 201 for successful POST (created)                       │
│     └── 204 for successful DELETE                               │
│                                                                  │
│  4. Include Location header for POST                            │
│     └── Points to newly created resource                        │
│                                                                  │
│  5. Handle idempotency correctly                                │
│     └── Same PUT/DELETE request = same result                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
