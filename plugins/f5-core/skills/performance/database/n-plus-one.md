---
name: n-plus-one
description: Understanding and solving the N+1 query problem
category: performance/database
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# N+1 Query Problem

## Overview

The N+1 query problem occurs when code executes N additional queries to fetch
related data for N results from an initial query, instead of using a single query.

## The Problem Illustrated

```
Initial Query (1):
SELECT * FROM users LIMIT 10;  -- Returns 10 users

Additional Queries (N = 10):
SELECT * FROM orders WHERE user_id = 1;
SELECT * FROM orders WHERE user_id = 2;
SELECT * FROM orders WHERE user_id = 3;
...
SELECT * FROM orders WHERE user_id = 10;

Total: 1 + 10 = 11 queries (should be 1 or 2)
```

### Impact

| Users | N+1 Queries | Optimized | Overhead |
|-------|-------------|-----------|----------|
| 10 | 11 | 2 | 5.5x |
| 100 | 101 | 2 | 50.5x |
| 1000 | 1001 | 2 | 500.5x |

## Detecting N+1 Queries

### Prisma Query Logging

```typescript
// Enable query logging
const prisma = new PrismaClient({
  log: [
    { emit: 'event', level: 'query' },
  ],
});

// Count queries per request
let queryCount = 0;

prisma.$on('query', (e) => {
  queryCount++;
  console.log(`Query #${queryCount}: ${e.query}`);
});

// Reset counter per request
app.use((req, res, next) => {
  queryCount = 0;
  res.on('finish', () => {
    if (queryCount > 10) {
      console.warn(`High query count: ${queryCount} queries for ${req.url}`);
    }
  });
  next();
});
```

### Custom Detection Middleware

```typescript
// Detect N+1 patterns
class QueryAnalyzer {
  private queries: Map<string, number> = new Map();

  recordQuery(query: string): void {
    // Normalize query (remove specific IDs)
    const normalized = query.replace(/= \d+/g, '= ?').replace(/IN \([^)]+\)/g, 'IN (?)');

    const count = (this.queries.get(normalized) || 0) + 1;
    this.queries.set(normalized, count);
  }

  analyze(): { suspectedNPlusOne: string[] } {
    const suspected: string[] = [];

    for (const [query, count] of this.queries) {
      if (count > 5) { // Same query pattern executed 5+ times
        suspected.push(`${query} (executed ${count} times)`);
      }
    }

    return { suspectedNPlusOne: suspected };
  }

  reset(): void {
    this.queries.clear();
  }
}
```

## Solutions

### 1. Eager Loading with Include

```typescript
// ❌ N+1 Problem
async function getUsersWithOrders() {
  const users = await prisma.user.findMany({ take: 10 });

  // This causes N additional queries!
  for (const user of users) {
    user.orders = await prisma.order.findMany({
      where: { userId: user.id },
    });
  }

  return users;
}

// ✅ Solution: Include related data
async function getUsersWithOrders() {
  return prisma.user.findMany({
    take: 10,
    include: {
      orders: true,
    },
  });
}
// Generates: 2 queries
// 1. SELECT * FROM users LIMIT 10
// 2. SELECT * FROM orders WHERE user_id IN (1, 2, 3, ...)
```

### 2. Selective Loading with Select

```typescript
// ✅ Load only needed fields
async function getUsersWithOrderCounts() {
  return prisma.user.findMany({
    take: 10,
    select: {
      id: true,
      name: true,
      email: true,
      _count: {
        select: { orders: true },
      },
    },
  });
}
```

### 3. Nested Includes

```typescript
// ✅ Multiple levels of relations
async function getUsersWithOrdersAndItems() {
  return prisma.user.findMany({
    take: 10,
    include: {
      orders: {
        include: {
          items: {
            include: {
              product: true,
            },
          },
        },
      },
    },
  });
}
// Prisma optimizes this to ~4 queries instead of N*M*K queries
```

### 4. DataLoader Pattern

For GraphQL or complex data fetching scenarios.

```typescript
import DataLoader from 'dataloader';

// Create loader for orders
const orderLoader = new DataLoader<string, Order[]>(async (userIds) => {
  // Single batch query
  const orders = await prisma.order.findMany({
    where: { userId: { in: userIds as string[] } },
  });

  // Group by userId
  const ordersByUser = new Map<string, Order[]>();
  for (const order of orders) {
    if (!ordersByUser.has(order.userId)) {
      ordersByUser.set(order.userId, []);
    }
    ordersByUser.get(order.userId)!.push(order);
  }

  // Return in same order as input
  return userIds.map(id => ordersByUser.get(id) || []);
});

// Usage - even in loops, only 1 batch query
async function resolveUserOrders(users: User[]) {
  return Promise.all(
    users.map(user => orderLoader.load(user.id))
  );
}

// Reset per request to prevent stale data
app.use((req, res, next) => {
  orderLoader.clearAll();
  next();
});
```

### 5. Raw SQL with JOIN

```typescript
// ✅ Single query with JOIN
async function getUsersWithOrderTotals() {
  return prisma.$queryRaw`
    SELECT
      u.id,
      u.name,
      u.email,
      COALESCE(SUM(o.total), 0) as order_total,
      COUNT(o.id) as order_count
    FROM users u
    LEFT JOIN orders o ON o.user_id = u.id
    GROUP BY u.id, u.name, u.email
    LIMIT 10
  `;
}
```

### 6. Batch Loading Helper

```typescript
// Generic batch loading utility
async function batchLoad<T, K extends keyof T, R>(
  items: T[],
  key: K,
  fetcher: (ids: T[K][]) => Promise<R[]>,
  groupKey: keyof R
): Promise<Map<T[K], R[]>> {
  const ids = items.map(item => item[key]);
  const uniqueIds = [...new Set(ids)];

  const results = await fetcher(uniqueIds);

  const grouped = new Map<T[K], R[]>();
  for (const result of results) {
    const groupValue = result[groupKey] as T[K];
    if (!grouped.has(groupValue)) {
      grouped.set(groupValue, []);
    }
    grouped.get(groupValue)!.push(result);
  }

  return grouped;
}

// Usage
async function getUsersWithOrders() {
  const users = await prisma.user.findMany({ take: 10 });

  const ordersMap = await batchLoad(
    users,
    'id',
    (userIds) => prisma.order.findMany({
      where: { userId: { in: userIds } },
    }),
    'userId'
  );

  return users.map(user => ({
    ...user,
    orders: ordersMap.get(user.id) || [],
  }));
}
```

## Common Scenarios

### Scenario 1: Listing with Relations

```typescript
// ❌ Bad
async function getProductsWithCategories() {
  const products = await prisma.product.findMany();
  for (const product of products) {
    product.category = await prisma.category.findUnique({
      where: { id: product.categoryId },
    });
  }
}

// ✅ Good
async function getProductsWithCategories() {
  return prisma.product.findMany({
    include: { category: true },
  });
}
```

### Scenario 2: Nested Counts

```typescript
// ❌ Bad - N+1 for each count
async function getCategoriesWithCounts() {
  const categories = await prisma.category.findMany();
  for (const category of categories) {
    category.productCount = await prisma.product.count({
      where: { categoryId: category.id },
    });
  }
}

// ✅ Good - Include count
async function getCategoriesWithCounts() {
  return prisma.category.findMany({
    include: {
      _count: {
        select: { products: true },
      },
    },
  });
}
```

### Scenario 3: Conditional Relations

```typescript
// ❌ Bad - Fetch conditionally in loop
async function getUsersWithRecentOrders() {
  const users = await prisma.user.findMany();
  for (const user of users) {
    if (user.status === 'active') {
      user.recentOrders = await prisma.order.findMany({
        where: {
          userId: user.id,
          createdAt: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
        },
        take: 5,
      });
    }
  }
}

// ✅ Good - Filter in include
async function getUsersWithRecentOrders() {
  return prisma.user.findMany({
    where: { status: 'active' },
    include: {
      orders: {
        where: {
          createdAt: { gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000) },
        },
        take: 5,
        orderBy: { createdAt: 'desc' },
      },
    },
  });
}
```

### Scenario 4: GraphQL Resolvers

```typescript
// ❌ Bad - N+1 in resolver
const resolvers = {
  User: {
    orders: (parent) => prisma.order.findMany({
      where: { userId: parent.id },
    }),
  },
};

// ✅ Good - DataLoader
const orderLoader = new DataLoader(async (userIds: string[]) => {
  const orders = await prisma.order.findMany({
    where: { userId: { in: userIds } },
  });
  return userIds.map(id => orders.filter(o => o.userId === id));
});

const resolvers = {
  User: {
    orders: (parent, args, context) => context.loaders.orders.load(parent.id),
  },
};
```

## Prevention Strategies

### 1. Code Review Checklist

- [ ] Any loops that execute database queries?
- [ ] Resolvers loading related data individually?
- [ ] Missing `include` statements?
- [ ] Query count per request measured?

### 2. Testing for N+1

```typescript
// Jest test for N+1
describe('API Performance', () => {
  it('should not have N+1 queries', async () => {
    let queryCount = 0;
    prisma.$on('query', () => queryCount++);

    await request(app).get('/api/users-with-orders');

    // Expect 2-3 queries, not 11+
    expect(queryCount).toBeLessThan(5);
  });
});
```

### 3. Automated Detection

```typescript
// Add to CI/CD pipeline
async function checkForNPlusOne(handler: () => Promise<void>): Promise<void> {
  const queries: string[] = [];

  prisma.$on('query', (e) => queries.push(e.query));

  await handler();

  // Detect repeated patterns
  const patterns = new Map<string, number>();
  for (const query of queries) {
    const pattern = query.replace(/\d+/g, '?');
    patterns.set(pattern, (patterns.get(pattern) || 0) + 1);
  }

  for (const [pattern, count] of patterns) {
    if (count > 5) {
      throw new Error(`Potential N+1: "${pattern}" executed ${count} times`);
    }
  }
}
```

## Best Practices

1. **Always use includes/joins** - Don't fetch relations in loops
2. **Use DataLoader for GraphQL** - Batches requests automatically
3. **Monitor query counts** - Track queries per request
4. **Test for N+1** - Include in test suite
5. **Review code for loops** - Database queries in loops are a red flag
6. **Profile in development** - Catch issues early
7. **Use Prisma's `_count`** - For counting relations
8. **Consider denormalization** - For read-heavy data
