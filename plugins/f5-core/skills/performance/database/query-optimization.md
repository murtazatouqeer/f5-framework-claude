---
name: query-optimization
description: Database query optimization techniques
category: performance/database
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Query Optimization

## Overview

Query optimization is the process of improving database query performance
through better query structure, indexing, and execution plans.

## Analyze Query Performance

### EXPLAIN ANALYZE

```sql
-- PostgreSQL: EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.created_at > '2024-01-01'
GROUP BY u.id
ORDER BY order_count DESC
LIMIT 10;

-- Output interpretation:
-- Seq Scan         = Full table scan (expensive for large tables)
-- Index Scan       = Using index (efficient)
-- Index Only Scan  = All data from index (most efficient)
-- Hash Join        = Building hash table for join
-- Nested Loop      = For each row in outer, scan inner
-- Sort             = Sorting in memory or disk
-- Actual Time      = real execution time (planning time + execution time)
-- Rows             = actual rows processed vs estimated
```

### MySQL EXPLAIN

```sql
-- MySQL EXPLAIN
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- Key columns:
-- type: ALL (full scan), index, range, ref, eq_ref, const
-- possible_keys: indexes that could be used
-- key: index actually used
-- rows: estimated rows to examine
-- Extra: Using filesort, Using temporary (warning signs)
```

## Common Optimizations

### 1. Select Only Needed Columns

```typescript
// ❌ Bad - fetches all columns
const users = await prisma.user.findMany();

// ✅ Good - select specific columns
const users = await prisma.user.findMany({
  select: {
    id: true,
    name: true,
    email: true,
  },
});

// SQL equivalent
// ❌ SELECT * FROM users
// ✅ SELECT id, name, email FROM users
```

### 2. Use WHERE Clauses Effectively

```typescript
// ❌ Bad - filters in application
const users = await prisma.user.findMany();
const activeUsers = users.filter(u => u.status === 'active');

// ✅ Good - filter in database
const activeUsers = await prisma.user.findMany({
  where: { status: 'active' },
});

// ❌ Bad - function on column prevents index use
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE LOWER(email) = 'test@example.com'
`;

// ✅ Good - store normalized, query directly
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE email_lower = 'test@example.com'
`;
// Or use case-insensitive collation
```

### 3. Avoid OR Conditions (When Possible)

```sql
-- ❌ OR can prevent index usage
SELECT * FROM users
WHERE email = 'a@example.com' OR phone = '123456789';

-- ✅ Use UNION for index usage on both
SELECT * FROM users WHERE email = 'a@example.com'
UNION ALL
SELECT * FROM users WHERE phone = '123456789' AND email != 'a@example.com';
```

### 4. Optimize JOINs

```typescript
// ❌ Bad - implicit join with large intermediate result
const data = await prisma.$queryRaw`
  SELECT * FROM orders, users, products
  WHERE orders.user_id = users.id
  AND orders.product_id = products.id
`;

// ✅ Good - explicit joins with conditions
const data = await prisma.$queryRaw`
  SELECT o.id, u.name, p.title
  FROM orders o
  INNER JOIN users u ON o.user_id = u.id
  INNER JOIN products p ON o.product_id = p.id
  WHERE o.created_at > NOW() - INTERVAL '30 days'
`;
```

### 5. Use Appropriate JOIN Types

```sql
-- INNER JOIN: Only matching rows (most common)
SELECT * FROM orders o
INNER JOIN users u ON o.user_id = u.id;

-- LEFT JOIN: All left rows + matching right
SELECT * FROM users u
LEFT JOIN orders o ON o.user_id = u.id;
-- Good for "users with optional orders"

-- EXISTS: For existence check (often faster than JOIN)
SELECT * FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.id
);

-- NOT EXISTS: Users without orders
SELECT * FROM users u
WHERE NOT EXISTS (
  SELECT 1 FROM orders o WHERE o.user_id = u.id
);
```

### 6. Limit Results Early

```typescript
// ❌ Bad - fetch all, then slice
const allUsers = await prisma.user.findMany();
const topUsers = allUsers.slice(0, 10);

// ✅ Good - limit in query
const topUsers = await prisma.user.findMany({
  take: 10,
  orderBy: { createdAt: 'desc' },
});

// For aggregations, use subquery
const topCategories = await prisma.$queryRaw`
  SELECT category_id, COUNT(*) as count
  FROM products
  GROUP BY category_id
  ORDER BY count DESC
  LIMIT 10
`;
```

### 7. Optimize GROUP BY

```sql
-- ❌ Bad - group by all columns
SELECT users.*, COUNT(orders.id)
FROM users
LEFT JOIN orders ON orders.user_id = users.id
GROUP BY users.id, users.name, users.email, users.created_at, ...;

-- ✅ Good - group by primary key only
SELECT users.id, users.name, COUNT(orders.id)
FROM users
LEFT JOIN orders ON orders.user_id = users.id
GROUP BY users.id;
-- PostgreSQL allows this when grouping by PK
```

### 8. Use Subqueries Wisely

```sql
-- ❌ Bad - correlated subquery (runs for each row)
SELECT *,
  (SELECT COUNT(*) FROM orders WHERE orders.user_id = users.id) as order_count
FROM users;

-- ✅ Good - use JOIN with aggregate
SELECT users.*, COALESCE(o.order_count, 0) as order_count
FROM users
LEFT JOIN (
  SELECT user_id, COUNT(*) as order_count
  FROM orders
  GROUP BY user_id
) o ON o.user_id = users.id;
```

## Query Patterns

### Batch Queries

```typescript
// ❌ Bad - individual queries in loop
for (const userId of userIds) {
  const user = await prisma.user.findUnique({ where: { id: userId } });
  results.push(user);
}

// ✅ Good - batch query
const users = await prisma.user.findMany({
  where: { id: { in: userIds } },
});
```

### Upsert Pattern

```typescript
// ❌ Bad - check then insert/update
const existing = await prisma.user.findUnique({ where: { email } });
if (existing) {
  await prisma.user.update({ where: { email }, data });
} else {
  await prisma.user.create({ data: { email, ...data } });
}

// ✅ Good - atomic upsert
await prisma.user.upsert({
  where: { email },
  update: data,
  create: { email, ...data },
});
```

### Bulk Operations

```typescript
// ❌ Bad - individual inserts
for (const item of items) {
  await prisma.item.create({ data: item });
}

// ✅ Good - bulk insert
await prisma.item.createMany({
  data: items,
  skipDuplicates: true,
});

// For updates, use transaction
await prisma.$transaction(
  items.map(item =>
    prisma.item.update({
      where: { id: item.id },
      data: { status: item.status },
    })
  )
);
```

### Conditional Aggregation

```sql
-- Count by status in single query
SELECT
  COUNT(*) FILTER (WHERE status = 'pending') as pending_count,
  COUNT(*) FILTER (WHERE status = 'active') as active_count,
  COUNT(*) FILTER (WHERE status = 'completed') as completed_count
FROM orders;

-- MySQL equivalent
SELECT
  SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_count,
  SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_count,
  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_count
FROM orders;
```

### Window Functions

```sql
-- Ranking without subquery
SELECT
  id,
  name,
  score,
  RANK() OVER (ORDER BY score DESC) as rank,
  ROW_NUMBER() OVER (PARTITION BY category_id ORDER BY score DESC) as category_rank
FROM products;

-- Running totals
SELECT
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) as running_total
FROM transactions;

-- Moving average
SELECT
  date,
  amount,
  AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as week_avg
FROM transactions;
```

## Query Caching

### Prepared Statements

```typescript
// Prisma automatically uses prepared statements

// Raw queries with parameters (prepared)
const users = await prisma.$queryRaw`
  SELECT * FROM users WHERE id = ${userId}
`;
// SQL: PREPARE stmt AS SELECT * FROM users WHERE id = $1
// EXECUTE stmt(123)
```

### Result Caching

```typescript
// Cache expensive queries
class QueryCache {
  constructor(private cache: Redis) {}

  async cachedQuery<T>(
    key: string,
    query: () => Promise<T>,
    ttl: number = 300
  ): Promise<T> {
    const cached = await this.cache.get(key);
    if (cached) {
      return JSON.parse(cached);
    }

    const result = await query();
    await this.cache.set(key, JSON.stringify(result), 'EX', ttl);
    return result;
  }
}

// Usage
const stats = await queryCache.cachedQuery(
  'stats:daily:2024-01-15',
  () => prisma.$queryRaw`
    SELECT
      COUNT(*) as total_orders,
      SUM(total) as revenue
    FROM orders
    WHERE DATE(created_at) = '2024-01-15'
  `,
  3600 // Cache for 1 hour
);
```

## Query Monitoring

```typescript
// Log slow queries
const prisma = new PrismaClient({
  log: [
    { emit: 'event', level: 'query' },
  ],
});

prisma.$on('query', (e) => {
  if (e.duration > 100) { // Queries over 100ms
    console.warn('Slow query:', {
      query: e.query,
      params: e.params,
      duration: e.duration,
    });
  }
});

// Or use middleware
prisma.$use(async (params, next) => {
  const start = performance.now();
  const result = await next(params);
  const duration = performance.now() - start;

  if (duration > 100) {
    console.warn(`Slow ${params.model}.${params.action}: ${duration}ms`);
  }

  return result;
});
```

## Best Practices

1. **Analyze before optimizing** - Use EXPLAIN to understand query plans
2. **Index strategically** - Based on actual query patterns
3. **Select only needed columns** - Reduce I/O and memory
4. **Filter early** - Reduce intermediate result sets
5. **Avoid N+1 queries** - Use JOINs or batch loading
6. **Use appropriate joins** - EXISTS vs JOIN for existence checks
7. **Monitor query performance** - Log and alert on slow queries
8. **Cache expensive queries** - Especially aggregations
