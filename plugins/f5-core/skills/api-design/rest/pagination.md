---
name: pagination
description: REST API pagination strategies
category: api-design/rest
applies_to: [all]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Pagination

## Overview

Pagination divides large datasets into manageable chunks, improving performance
and user experience. Choose the right strategy based on your use case.

## Pagination Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                  Pagination Strategies Comparison                │
├──────────────────┬──────────────────────────────────────────────┤
│ Strategy         │ Pros                   │ Cons                │
├──────────────────┼────────────────────────┼─────────────────────┤
│ Offset-based     │ Simple, random access  │ Inconsistent pages, │
│ (page/limit)     │ Easy to implement      │ slow on large sets  │
├──────────────────┼────────────────────────┼─────────────────────┤
│ Cursor-based     │ Consistent, fast       │ No random access,   │
│ (keyset)         │ Works with real-time   │ complex cursors     │
├──────────────────┼────────────────────────┼─────────────────────┤
│ Time-based       │ Good for feeds         │ Limited use cases   │
│ (since/until)    │ Natural for timelines  │ Complex ordering    │
├──────────────────┼────────────────────────┼─────────────────────┤
│ Seek-based       │ Very fast, scalable    │ Implementation      │
│ (after ID)       │ Consistent results     │ complexity          │
└──────────────────┴────────────────────────┴─────────────────────┘
```

## Offset-Based Pagination

### Implementation

```http
GET /api/v1/users?page=2&limit=20 HTTP/1.1
```

```json
{
  "data": [
    {"id": "usr_21", "name": "User 21"},
    {"id": "usr_22", "name": "User 22"}
  ],
  "meta": {
    "total": 100,
    "page": 2,
    "limit": 20,
    "total_pages": 5,
    "has_next": true,
    "has_prev": true
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

### Alternative: Offset/Limit

```http
GET /api/v1/users?offset=20&limit=20 HTTP/1.1
```

```json
{
  "data": [...],
  "meta": {
    "total": 100,
    "offset": 20,
    "limit": 20
  },
  "links": {
    "self": "/api/v1/users?offset=20&limit=20",
    "next": "/api/v1/users?offset=40&limit=20",
    "prev": "/api/v1/users?offset=0&limit=20"
  }
}
```

### SQL Implementation

```sql
-- Page 2 with 20 items per page
SELECT *
FROM users
ORDER BY created_at DESC
LIMIT 20 OFFSET 20;  -- (page - 1) * limit

-- Problem: Slow on large tables
-- OFFSET requires scanning skipped rows
EXPLAIN ANALYZE SELECT * FROM users ORDER BY created_at DESC LIMIT 20 OFFSET 100000;
-- Seq Scan... rows=100020
```

### Code Implementation

```typescript
interface PaginationParams {
  page?: number;
  limit?: number;
}

interface PaginatedResponse<T> {
  data: T[];
  meta: {
    total: number;
    page: number;
    limit: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
  links: {
    self: string;
    first: string;
    prev: string | null;
    next: string | null;
    last: string;
  };
}

async function paginateOffset<T>(
  query: QueryBuilder,
  params: PaginationParams,
  baseUrl: string
): Promise<PaginatedResponse<T>> {
  const page = Math.max(1, params.page || 1);
  const limit = Math.min(100, Math.max(1, params.limit || 20));
  const offset = (page - 1) * limit;

  const [data, total] = await Promise.all([
    query.limit(limit).offset(offset).execute(),
    query.count().execute(),
  ]);

  const totalPages = Math.ceil(total / limit);

  return {
    data,
    meta: {
      total,
      page,
      limit,
      total_pages: totalPages,
      has_next: page < totalPages,
      has_prev: page > 1,
    },
    links: {
      self: `${baseUrl}?page=${page}&limit=${limit}`,
      first: `${baseUrl}?page=1&limit=${limit}`,
      prev: page > 1 ? `${baseUrl}?page=${page - 1}&limit=${limit}` : null,
      next: page < totalPages ? `${baseUrl}?page=${page + 1}&limit=${limit}` : null,
      last: `${baseUrl}?page=${totalPages}&limit=${limit}`,
    },
  };
}
```

### When to Use Offset

```
✅ Good for:
  - Small to medium datasets (<100K rows)
  - Admin panels with page numbers
  - Search results with "page X of Y"
  - Data that doesn't change frequently

❌ Avoid for:
  - Large datasets (millions of rows)
  - Real-time data (new items cause page drift)
  - High-traffic APIs (COUNT is expensive)
  - Mobile infinite scroll
```

## Cursor-Based Pagination

### Implementation

```http
# Initial request
GET /api/v1/posts?limit=20 HTTP/1.1

# Next page
GET /api/v1/posts?limit=20&cursor=eyJpZCI6InBvc3RfMjAiLCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNVQxMDowMDowMFoifQ HTTP/1.1
```

```json
{
  "data": [
    {"id": "post_1", "title": "First Post", "created_at": "2024-01-15T10:00:00Z"},
    {"id": "post_2", "title": "Second Post", "created_at": "2024-01-15T09:00:00Z"}
  ],
  "meta": {
    "has_more": true
  },
  "cursors": {
    "next": "eyJpZCI6InBvc3RfMjAiLCJjcmVhdGVkX2F0IjoiMjAyNC0wMS0xNFQxMDowMDowMFoifQ",
    "prev": "eyJpZCI6InBvc3RfMSIsImNyZWF0ZWRfYXQiOiIyMDI0LTAxLTE1VDEwOjAwOjAwWiJ9"
  },
  "links": {
    "next": "/api/v1/posts?limit=20&cursor=eyJpZCI6InBvc3RfMjAi..."
  }
}
```

### Cursor Structure

```typescript
// Cursor contains the last item's sorting fields
interface Cursor {
  id: string;
  created_at: string;
  // Include all ORDER BY columns
}

function encodeCursor(cursor: Cursor): string {
  return Buffer.from(JSON.stringify(cursor)).toString('base64url');
}

function decodeCursor(encoded: string): Cursor {
  return JSON.parse(Buffer.from(encoded, 'base64url').toString('utf8'));
}
```

### SQL Implementation

```sql
-- First page
SELECT id, title, created_at
FROM posts
ORDER BY created_at DESC, id DESC
LIMIT 21;  -- Fetch one extra to check has_more

-- Next page (keyset pagination)
SELECT id, title, created_at
FROM posts
WHERE (created_at, id) < ('2024-01-14T10:00:00Z', 'post_20')
ORDER BY created_at DESC, id DESC
LIMIT 21;

-- Why include ID in cursor?
-- To handle ties when multiple items have same created_at
```

### Code Implementation

```typescript
interface CursorParams {
  cursor?: string;
  limit?: number;
  direction?: 'forward' | 'backward';
}

interface CursorResponse<T> {
  data: T[];
  meta: {
    has_more: boolean;
    count: number;
  };
  cursors: {
    next: string | null;
    prev: string | null;
  };
}

async function paginateCursor<T extends { id: string; created_at: Date }>(
  query: QueryBuilder,
  params: CursorParams,
  baseUrl: string
): Promise<CursorResponse<T>> {
  const limit = Math.min(100, Math.max(1, params.limit || 20));
  const direction = params.direction || 'forward';

  let q = query.orderBy('created_at', 'desc').orderBy('id', 'desc');

  if (params.cursor) {
    const cursor = decodeCursor(params.cursor);

    if (direction === 'forward') {
      q = q.where(
        raw('(created_at, id) < (?, ?)', [cursor.created_at, cursor.id])
      );
    } else {
      q = q.where(
        raw('(created_at, id) > (?, ?)', [cursor.created_at, cursor.id])
      );
    }
  }

  // Fetch one extra to determine has_more
  const items = await q.limit(limit + 1).execute();
  const hasMore = items.length > limit;
  const data = items.slice(0, limit);

  // Reverse if going backward
  if (direction === 'backward') {
    data.reverse();
  }

  const firstItem = data[0];
  const lastItem = data[data.length - 1];

  return {
    data,
    meta: {
      has_more: hasMore,
      count: data.length,
    },
    cursors: {
      next: hasMore ? encodeCursor({
        id: lastItem.id,
        created_at: lastItem.created_at.toISOString(),
      }) : null,
      prev: firstItem ? encodeCursor({
        id: firstItem.id,
        created_at: firstItem.created_at.toISOString(),
      }) : null,
    },
  };
}
```

### When to Use Cursor

```
✅ Good for:
  - Large datasets (millions of rows)
  - Real-time feeds (social media, news)
  - Infinite scroll interfaces
  - Data that changes frequently

❌ Avoid for:
  - Need to jump to specific page
  - Need total count
  - Complex multi-column sorting
  - Data without stable sort order
```

## Time-Based Pagination

### Implementation

```http
# Get posts since a timestamp
GET /api/v1/posts?since=2024-01-15T00:00:00Z&limit=50 HTTP/1.1

# Get posts before a timestamp
GET /api/v1/posts?until=2024-01-15T00:00:00Z&limit=50 HTTP/1.1
```

```json
{
  "data": [...],
  "meta": {
    "newest_at": "2024-01-15T12:00:00Z",
    "oldest_at": "2024-01-15T10:00:00Z"
  },
  "links": {
    "newer": "/api/v1/posts?since=2024-01-15T12:00:00Z&limit=50",
    "older": "/api/v1/posts?until=2024-01-15T10:00:00Z&limit=50"
  }
}
```

### SQL Implementation

```sql
-- Posts since timestamp
SELECT *
FROM posts
WHERE created_at > '2024-01-15T00:00:00Z'
ORDER BY created_at ASC
LIMIT 50;

-- Posts before timestamp
SELECT *
FROM posts
WHERE created_at < '2024-01-15T00:00:00Z'
ORDER BY created_at DESC
LIMIT 50;
```

## Seek-Based Pagination

### Implementation

```http
# Get items after a specific ID
GET /api/v1/users?after=usr_100&limit=20 HTTP/1.1

# Get items before a specific ID
GET /api/v1/users?before=usr_100&limit=20 HTTP/1.1
```

```json
{
  "data": [
    {"id": "usr_101", "name": "User 101"},
    {"id": "usr_102", "name": "User 102"}
  ],
  "meta": {
    "has_more": true
  },
  "links": {
    "next": "/api/v1/users?after=usr_120&limit=20"
  }
}
```

### SQL Implementation

```sql
-- Using indexed ID (very fast)
SELECT *
FROM users
WHERE id > 'usr_100'
ORDER BY id ASC
LIMIT 21;

-- With composite key
CREATE INDEX idx_users_pagination ON users(status, id);

SELECT *
FROM users
WHERE status = 'active' AND id > 'usr_100'
ORDER BY id ASC
LIMIT 21;
```

## Response Headers for Pagination

```http
HTTP/1.1 200 OK
Content-Type: application/json
Link: </api/v1/users?page=1>; rel="first",
      </api/v1/users?page=2>; rel="prev",
      </api/v1/users?page=4>; rel="next",
      </api/v1/users?page=10>; rel="last"
X-Total-Count: 200
X-Page-Count: 10
X-Current-Page: 3
X-Per-Page: 20
```

## Pagination Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Pagination Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Set Reasonable Defaults                                     │
│     ├── Default limit: 20-50 items                              │
│     ├── Maximum limit: 100-200 items                            │
│     └── Document limits in API docs                             │
│                                                                  │
│  2. Validate Parameters                                         │
│     ├── Reject negative values                                  │
│     ├── Cap at maximum limit                                    │
│     └── Handle invalid cursors gracefully                       │
│                                                                  │
│  3. Include Navigation Links                                    │
│     ├── HATEOAS links (next, prev, first, last)                │
│     └── Allow clients to navigate without building URLs         │
│                                                                  │
│  4. Consider Total Count Carefully                              │
│     ├── COUNT(*) is expensive on large tables                   │
│     ├── Consider approximate counts                             │
│     └── Or omit total for cursor pagination                     │
│                                                                  │
│  5. Use Consistent Ordering                                     │
│     ├── Always include unique field in ORDER BY                 │
│     └── Prevents duplicate/missing items                        │
│                                                                  │
│  6. Handle Empty Results                                        │
│     └── Return empty array, not 404                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Comparison Summary

| Feature | Offset | Cursor | Time | Seek |
|---------|--------|--------|------|------|
| Random access | Yes | No | No | No |
| Total count | Yes | Optional | No | No |
| Performance | O(n) | O(1) | O(1) | O(1) |
| Consistency | Low | High | Medium | High |
| Complexity | Low | Medium | Low | Low |
| Real-time data | Poor | Excellent | Good | Good |
