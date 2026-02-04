---
name: shared-api-patterns
description: Common API design patterns used across F5 Framework
category: shared
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Shared API Patterns

## REST Naming Conventions

| Action | Method | Endpoint |
|--------|--------|----------|
| List | GET | /users |
| Get one | GET | /users/:id |
| Create | POST | /users |
| Update | PUT/PATCH | /users/:id |
| Delete | DELETE | /users/:id |

## Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 100
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "USER_NOT_FOUND",
    "message": "User with ID 123 not found",
    "details": []
  }
}
```

## HTTP Status Codes

| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 204 | No Content (DELETE) |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 409 | Conflict |
| 422 | Validation Error |
| 500 | Internal Error |

## Pagination Pattern

```typescript
// Query params
?page=1&limit=10&sort=createdAt&order=desc

// Response
{
  "data": [...],
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "totalPages": 10,
    "hasNext": true,
    "hasPrev": false
  }
}
```

## Versioning

```
/api/v1/users
/api/v2/users
```

## Rate Limiting Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

## DTO Pattern

```typescript
// CreateUserDto
class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(8)
  password: string;
}

// ResponseUserDto (no password)
class ResponseUserDto {
  id: string;
  email: string;
  createdAt: Date;
}
```

## Error Codes

Use domain-prefixed codes:
- `AUTH_001`: Invalid credentials
- `USER_001`: User not found
- `ORDER_001`: Invalid order status
