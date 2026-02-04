---
name: pagination
description: API pagination strategies and implementation
category: performance/api
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Pagination Strategies

## Overview

Pagination is essential for APIs that return large datasets. Proper pagination
improves performance, reduces memory usage, and provides better user experience.

## Pagination Types Comparison

| Type | Performance | Consistency | Use Case |
|------|-------------|-------------|----------|
| Offset | Poor at scale | Inconsistent | Simple lists |
| Cursor | Excellent | Consistent | Infinite scroll |
| Keyset | Excellent | Consistent | Time-series |
| Page Token | Good | Consistent | Google-style APIs |

## Offset Pagination

Simple but problematic at scale.

### Implementation

```typescript
// API endpoint
app.get('/api/users', async (req, res) => {
  const page = parseInt(req.query.page as string) || 1;
  const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
  const offset = (page - 1) * limit;

  const [users, total] = await Promise.all([
    prisma.user.findMany({
      skip: offset,
      take: limit,
      orderBy: { createdAt: 'desc' },
    }),
    prisma.user.count(),
  ]);

  res.json({
    data: users,
    pagination: {
      page,
      limit,
      total,
      totalPages: Math.ceil(total / limit),
      hasMore: page * limit < total,
    },
  });
});
```

### Problems with Offset

```sql
-- Page 1: Fast
SELECT * FROM users ORDER BY created_at DESC LIMIT 20 OFFSET 0;
-- Scans: 20 rows

-- Page 100: Slow
SELECT * FROM users ORDER BY created_at DESC LIMIT 20 OFFSET 1980;
-- Scans: 2000 rows (skips 1980, returns 20)

-- Page 1000: Very slow
SELECT * FROM users ORDER BY created_at DESC LIMIT 20 OFFSET 19980;
-- Scans: 20000 rows!
```

### When to Use Offset

- Small datasets (< 10,000 records)
- Admin dashboards with page numbers
- SEO requirements (need page URLs)

## Cursor Pagination

Best for real-time data and infinite scroll.

### Implementation

```typescript
// API endpoint
app.get('/api/users', async (req, res) => {
  const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
  const cursor = req.query.cursor as string | undefined;

  const users = await prisma.user.findMany({
    take: limit + 1, // Fetch one extra to check if there's more
    ...(cursor && {
      skip: 1, // Skip the cursor itself
      cursor: { id: cursor },
    }),
    orderBy: { id: 'asc' },
  });

  const hasMore = users.length > limit;
  const data = hasMore ? users.slice(0, -1) : users;
  const nextCursor = hasMore ? data[data.length - 1].id : null;

  res.json({
    data,
    pagination: {
      nextCursor,
      hasMore,
    },
  });
});

// Client usage
async function fetchAllUsers() {
  let cursor: string | null = null;
  const allUsers: User[] = [];

  do {
    const response = await fetch(
      `/api/users?limit=100${cursor ? `&cursor=${cursor}` : ''}`
    );
    const { data, pagination } = await response.json();

    allUsers.push(...data);
    cursor = pagination.nextCursor;
  } while (cursor);

  return allUsers;
}
```

### Encoded Cursor

```typescript
// Encode cursor to hide implementation details
function encodeCursor(data: { id: string; createdAt: Date }): string {
  return Buffer.from(JSON.stringify(data)).toString('base64url');
}

function decodeCursor(cursor: string): { id: string; createdAt: Date } | null {
  try {
    return JSON.parse(Buffer.from(cursor, 'base64url').toString());
  } catch {
    return null;
  }
}

// API with encoded cursor
app.get('/api/users', async (req, res) => {
  const limit = 20;
  const cursorData = req.query.cursor
    ? decodeCursor(req.query.cursor as string)
    : null;

  const users = await prisma.user.findMany({
    take: limit + 1,
    where: cursorData ? {
      OR: [
        { createdAt: { lt: cursorData.createdAt } },
        {
          createdAt: cursorData.createdAt,
          id: { lt: cursorData.id },
        },
      ],
    } : undefined,
    orderBy: [
      { createdAt: 'desc' },
      { id: 'desc' },
    ],
  });

  const hasMore = users.length > limit;
  const data = hasMore ? users.slice(0, -1) : users;
  const nextCursor = hasMore
    ? encodeCursor({
        id: data[data.length - 1].id,
        createdAt: data[data.length - 1].createdAt,
      })
    : null;

  res.json({ data, pagination: { nextCursor, hasMore } });
});
```

## Keyset Pagination

Best for sorted data with unique keys.

### Implementation

```typescript
// For time-series data
app.get('/api/events', async (req, res) => {
  const limit = 50;
  const afterTimestamp = req.query.after
    ? new Date(req.query.after as string)
    : null;
  const afterId = req.query.afterId as string | undefined;

  const events = await prisma.event.findMany({
    take: limit + 1,
    where: afterTimestamp ? {
      OR: [
        { timestamp: { gt: afterTimestamp } },
        {
          timestamp: afterTimestamp,
          id: { gt: afterId },
        },
      ],
    } : undefined,
    orderBy: [
      { timestamp: 'asc' },
      { id: 'asc' },
    ],
  });

  const hasMore = events.length > limit;
  const data = hasMore ? events.slice(0, -1) : events;

  res.json({
    data,
    pagination: {
      hasMore,
      ...(hasMore && {
        after: data[data.length - 1].timestamp.toISOString(),
        afterId: data[data.length - 1].id,
      }),
    },
  });
});
```

### Bidirectional Keyset

```typescript
// Support both forward and backward navigation
app.get('/api/messages', async (req, res) => {
  const limit = 50;
  const { before, after } = req.query;

  let where: any = {};
  let orderBy: any = { createdAt: 'desc' };

  if (after) {
    where = { createdAt: { gt: new Date(after as string) } };
    orderBy = { createdAt: 'asc' };
  } else if (before) {
    where = { createdAt: { lt: new Date(before as string) } };
  }

  let messages = await prisma.message.findMany({
    take: limit + 1,
    where,
    orderBy,
  });

  // Reverse if fetching "after" to maintain consistent order
  if (after) {
    messages = messages.reverse();
  }

  const hasMore = messages.length > limit;
  const data = hasMore ? messages.slice(0, -1) : messages;

  res.json({
    data,
    pagination: {
      hasPrevious: !!after || (!!before && hasMore),
      hasNext: !!before || (!after && hasMore),
      oldest: data[data.length - 1]?.createdAt?.toISOString(),
      newest: data[0]?.createdAt?.toISOString(),
    },
  });
});
```

## Page Token Pagination

Google-style opaque tokens.

### Implementation

```typescript
interface PageToken {
  offset: number;
  filters: Record<string, any>;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

function encodePageToken(data: PageToken): string {
  return Buffer.from(JSON.stringify(data)).toString('base64url');
}

function decodePageToken(token: string): PageToken | null {
  try {
    return JSON.parse(Buffer.from(token, 'base64url').toString());
  } catch {
    return null;
  }
}

app.get('/api/search', async (req, res) => {
  const pageSize = 25;
  const { query, pageToken } = req.query;

  let tokenData: PageToken;

  if (pageToken) {
    const decoded = decodePageToken(pageToken as string);
    if (!decoded) {
      return res.status(400).json({ error: 'Invalid page token' });
    }
    tokenData = decoded;
  } else {
    tokenData = {
      offset: 0,
      filters: { query },
      sortBy: 'relevance',
      sortOrder: 'desc',
    };
  }

  const results = await searchService.search({
    query: tokenData.filters.query,
    offset: tokenData.offset,
    limit: pageSize + 1,
    sortBy: tokenData.sortBy,
    sortOrder: tokenData.sortOrder,
  });

  const hasMore = results.length > pageSize;
  const data = hasMore ? results.slice(0, -1) : results;

  const nextPageToken = hasMore
    ? encodePageToken({
        ...tokenData,
        offset: tokenData.offset + pageSize,
      })
    : null;

  res.json({
    data,
    nextPageToken,
  });
});
```

## Relay-Style Pagination

GraphQL Relay specification.

### Implementation

```typescript
interface Edge<T> {
  node: T;
  cursor: string;
}

interface PageInfo {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor: string | null;
  endCursor: string | null;
}

interface Connection<T> {
  edges: Edge<T>[];
  pageInfo: PageInfo;
  totalCount: number;
}

async function paginateUsers(
  first?: number,
  after?: string,
  last?: number,
  before?: string
): Promise<Connection<User>> {
  const limit = first || last || 20;
  const isForward = !!first || !last;

  let where: any = {};
  if (after) {
    const cursor = decodeCursor(after);
    where.id = { gt: cursor.id };
  } else if (before) {
    const cursor = decodeCursor(before);
    where.id = { lt: cursor.id };
  }

  const [users, totalCount] = await Promise.all([
    prisma.user.findMany({
      take: limit + 1,
      where,
      orderBy: { id: isForward ? 'asc' : 'desc' },
    }),
    prisma.user.count(),
  ]);

  const hasMore = users.length > limit;
  const data = hasMore ? users.slice(0, -1) : users;

  if (!isForward) {
    data.reverse();
  }

  const edges = data.map(user => ({
    node: user,
    cursor: encodeCursor({ id: user.id }),
  }));

  return {
    edges,
    pageInfo: {
      hasNextPage: isForward ? hasMore : !!before,
      hasPreviousPage: isForward ? !!after : hasMore,
      startCursor: edges[0]?.cursor || null,
      endCursor: edges[edges.length - 1]?.cursor || null,
    },
    totalCount,
  };
}
```

## Pagination Utilities

### Generic Pagination Helper

```typescript
interface PaginationOptions {
  page?: number;
  limit?: number;
  cursor?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

interface PaginatedResult<T> {
  data: T[];
  pagination: {
    total?: number;
    page?: number;
    limit: number;
    hasMore: boolean;
    nextCursor?: string;
  };
}

async function paginate<T>(
  model: any,
  options: PaginationOptions,
  where?: any
): Promise<PaginatedResult<T>> {
  const limit = Math.min(options.limit || 20, 100);

  if (options.cursor) {
    // Cursor pagination
    const items = await model.findMany({
      take: limit + 1,
      skip: 1,
      cursor: { id: options.cursor },
      where,
      orderBy: { [options.sortBy || 'id']: options.sortOrder || 'asc' },
    });

    const hasMore = items.length > limit;
    const data = hasMore ? items.slice(0, -1) : items;

    return {
      data,
      pagination: {
        limit,
        hasMore,
        nextCursor: hasMore ? data[data.length - 1].id : undefined,
      },
    };
  } else {
    // Offset pagination
    const page = options.page || 1;
    const offset = (page - 1) * limit;

    const [items, total] = await Promise.all([
      model.findMany({
        skip: offset,
        take: limit,
        where,
        orderBy: { [options.sortBy || 'id']: options.sortOrder || 'asc' },
      }),
      model.count({ where }),
    ]);

    return {
      data: items,
      pagination: {
        total,
        page,
        limit,
        hasMore: page * limit < total,
      },
    };
  }
}

// Usage
const result = await paginate(prisma.user, {
  cursor: 'abc123',
  limit: 50,
  sortBy: 'createdAt',
  sortOrder: 'desc',
}, {
  status: 'active',
});
```

## Best Practices

1. **Default to cursor pagination** - Better performance at scale
2. **Set maximum limits** - Prevent abuse (e.g., max 100 items)
3. **Use consistent ordering** - Include unique column for deterministic results
4. **Encode cursors** - Hide implementation details
5. **Include total count judiciously** - Expensive for large tables
6. **Handle edge cases** - Empty results, invalid cursors
7. **Document pagination** - Clear API documentation
8. **Consider caching** - Cache first pages of popular queries
