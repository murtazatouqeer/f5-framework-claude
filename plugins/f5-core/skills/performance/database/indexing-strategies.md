---
name: indexing-strategies
description: Database indexing strategies and best practices
category: performance/database
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Indexing Strategies

## Overview

Indexes are data structures that improve the speed of data retrieval operations.
Proper indexing is one of the most impactful performance optimizations.

## Index Types

### B-Tree Index (Default)

Most common index type, good for equality and range queries.

```sql
-- Create B-tree index
CREATE INDEX idx_users_email ON users(email);

-- Good for:
-- WHERE email = 'test@example.com'
-- WHERE email LIKE 'test%' (prefix search)
-- WHERE email > 'a' AND email < 'b'
-- ORDER BY email
```

### Hash Index

Fast for equality comparisons only.

```sql
-- PostgreSQL hash index
CREATE INDEX idx_users_email_hash ON users USING HASH (email);

-- Only good for: WHERE email = 'test@example.com'
-- NOT useful for: range queries, sorting, prefix search
```

### GiST and GIN Indexes

For full-text search and complex data types.

```sql
-- GIN for full-text search
CREATE INDEX idx_articles_content ON articles USING GIN (to_tsvector('english', content));

-- Query with full-text search
SELECT * FROM articles
WHERE to_tsvector('english', content) @@ to_tsquery('english', 'database & performance');

-- GIN for JSON/JSONB
CREATE INDEX idx_data_jsonb ON events USING GIN (data);
SELECT * FROM events WHERE data @> '{"type": "click"}';
```

### Partial Index

Index only a subset of rows.

```sql
-- Index only active users (smaller, faster index)
CREATE INDEX idx_active_users ON users(email) WHERE status = 'active';

-- Good when:
-- - Most queries filter by this condition
-- - Subset is much smaller than full table
```

### Covering Index (Include)

Include additional columns in index to avoid table lookup.

```sql
-- PostgreSQL covering index
CREATE INDEX idx_orders_user ON orders(user_id) INCLUDE (status, total, created_at);

-- This query can be satisfied entirely from index (Index Only Scan)
SELECT user_id, status, total, created_at
FROM orders
WHERE user_id = 123;
```

## Composite (Multi-Column) Indexes

### Column Order Matters

```sql
-- Index on (a, b, c)
CREATE INDEX idx_abc ON table(a, b, c);

-- Can be used for:
-- WHERE a = 1                      ✅
-- WHERE a = 1 AND b = 2            ✅
-- WHERE a = 1 AND b = 2 AND c = 3  ✅
-- WHERE a = 1 AND c = 3            ⚠️ Only uses 'a' part
-- WHERE b = 2                      ❌ Cannot use index
-- WHERE b = 2 AND c = 3            ❌ Cannot use index

-- Order columns by:
-- 1. Equality conditions first
-- 2. Range conditions last
-- 3. Higher selectivity first
```

### Practical Examples

```sql
-- For query: WHERE status = 'active' AND created_at > '2024-01-01'
-- Better: status first (equality), then created_at (range)
CREATE INDEX idx_orders_status_date ON orders(status, created_at);

-- For query: WHERE user_id = 123 ORDER BY created_at DESC
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- For query: WHERE category = 'electronics' AND price BETWEEN 100 AND 500
CREATE INDEX idx_products_cat_price ON products(category, price);
```

## Index Design for Prisma

```prisma
// schema.prisma

model User {
  id        String   @id @default(uuid())
  email     String   @unique  // Automatic unique index
  name      String
  status    String
  createdAt DateTime @default(now())

  orders    Order[]

  // Composite index for common query patterns
  @@index([status, createdAt])
}

model Order {
  id        String   @id @default(uuid())
  userId    String
  status    String
  total     Decimal
  createdAt DateTime @default(now())

  user      User     @relation(fields: [userId], references: [id])

  // Single column indexes
  @@index([userId])
  @@index([status])

  // Composite for: WHERE userId = ? AND status = ? ORDER BY createdAt
  @@index([userId, status, createdAt])
}

model Product {
  id          String   @id @default(uuid())
  categoryId  String
  name        String
  price       Decimal
  searchable  String   // denormalized search field

  @@index([categoryId, price])

  // For text search (requires raw migration)
  // CREATE INDEX idx_product_search ON products USING GIN (to_tsvector('english', searchable));
}
```

## When to Create Indexes

### DO Create Indexes For

```sql
-- Primary keys (automatic)
-- Foreign keys
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- Frequently filtered columns
CREATE INDEX idx_users_status ON users(status);

-- Columns in JOIN conditions
CREATE INDEX idx_order_items_order_id ON order_items(order_id);

-- Columns used in ORDER BY
CREATE INDEX idx_orders_created_at ON orders(created_at);

-- Columns with high selectivity in WHERE
CREATE INDEX idx_users_email ON users(email);
```

### DON'T Create Indexes For

```sql
-- Small tables (full scan is fast enough)
-- Low selectivity columns (e.g., boolean with 50/50 distribution)
-- Frequently updated columns (index maintenance overhead)
-- Columns rarely used in queries
-- Too many indexes on write-heavy tables
```

## Index Maintenance

### Analyze Index Usage

```sql
-- PostgreSQL: Check index usage
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Find unused indexes
SELECT
  schemaname || '.' || tablename as table,
  indexname,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
AND indexrelname NOT LIKE '%pkey%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Index Size

```sql
-- Check index sizes
SELECT
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Rebuild Indexes

```sql
-- PostgreSQL: Rebuild bloated index
REINDEX INDEX idx_users_email;

-- Concurrent rebuild (no lock)
REINDEX INDEX CONCURRENTLY idx_users_email;

-- MySQL: Optimize table (rebuilds indexes)
OPTIMIZE TABLE users;
```

## Index Design Patterns

### Pattern 1: Lookup Table Pattern

```sql
-- For frequently joined lookup tables
CREATE TABLE categories (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  category_id INT REFERENCES categories(id),
  name VARCHAR(255)
);

-- Index on foreign key
CREATE INDEX idx_products_category ON products(category_id);
```

### Pattern 2: Time-Series Data

```sql
-- For time-series queries
CREATE TABLE events (
  id BIGSERIAL,
  event_type VARCHAR(50),
  created_at TIMESTAMPTZ,
  data JSONB
);

-- Composite index for time-range queries by type
CREATE INDEX idx_events_type_time ON events(event_type, created_at DESC);

-- Partial index for recent data
CREATE INDEX idx_events_recent ON events(created_at)
WHERE created_at > NOW() - INTERVAL '30 days';
```

### Pattern 3: Search Pattern

```sql
-- For search with multiple optional filters
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  category_id INT,
  brand_id INT,
  price DECIMAL,
  rating DECIMAL,
  name VARCHAR(255)
);

-- Separate indexes for flexible filtering
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand_id);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_rating ON products(rating DESC);

-- For combined filters, consider composite
CREATE INDEX idx_products_cat_price ON products(category_id, price);
```

### Pattern 4: Soft Delete Pattern

```sql
-- For soft-deleted records
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255),
  deleted_at TIMESTAMPTZ
);

-- Partial index for active records only
CREATE UNIQUE INDEX idx_users_email_active ON users(email)
WHERE deleted_at IS NULL;

-- This ensures uniqueness only among non-deleted users
```

### Pattern 5: Multi-Tenant Pattern

```sql
-- For multi-tenant applications
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  tenant_id UUID NOT NULL,
  title VARCHAR(255),
  created_at TIMESTAMPTZ
);

-- Always include tenant_id first in indexes
CREATE INDEX idx_documents_tenant ON documents(tenant_id);
CREATE INDEX idx_documents_tenant_created ON documents(tenant_id, created_at DESC);

-- Queries always filter by tenant first
SELECT * FROM documents
WHERE tenant_id = 'abc' AND created_at > '2024-01-01';
```

## Monitoring Query Plans

```typescript
// Log queries that don't use indexes
async function checkQueryPlan(query: string): Promise<void> {
  const plan = await prisma.$queryRaw`EXPLAIN ${query}`;

  const planStr = JSON.stringify(plan);
  if (planStr.includes('Seq Scan') && !planStr.includes('Index')) {
    console.warn('Query not using index:', query);
  }
}
```

## Best Practices

1. **Index foreign keys** - Always index columns used in JOINs
2. **Column order matters** - Put equality columns before range columns
3. **Don't over-index** - Each index slows writes
4. **Use partial indexes** - For filtered subsets of data
5. **Consider covering indexes** - Avoid table lookups
6. **Monitor usage** - Remove unused indexes
7. **Analyze regularly** - Keep statistics up to date
8. **Test with production data** - Query plans depend on data distribution
