---
name: indexing-strategies
description: Database indexing strategies and best practices
category: database/optimization
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Indexing Strategies

## Overview

Indexes are the primary tool for improving query performance. Strategic
indexing balances read performance gains against write overhead and
storage costs.

## Index Fundamentals

```
┌─────────────────────────────────────────────────────────────────┐
│                    Index Concepts                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  What indexes do:                                                │
│  ✓ Speed up SELECT queries with WHERE clauses                   │
│  ✓ Speed up JOIN operations on indexed columns                  │
│  ✓ Speed up ORDER BY when matching index order                  │
│  ✓ Enable unique constraints efficiently                        │
│                                                                  │
│  Trade-offs:                                                     │
│  - Slower INSERT/UPDATE/DELETE (index maintenance)              │
│  - Additional storage space                                     │
│  - More complex query planning                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Index Types

### B-Tree (Default)

```sql
-- B-tree: Best for equality and range queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_created ON orders(created_at);

-- Supports operators: <, <=, =, >=, >, BETWEEN, IN, IS NULL
-- Also: LIKE 'prefix%' (but not '%suffix')

-- Good for:
SELECT * FROM users WHERE email = 'test@example.com';
SELECT * FROM orders WHERE created_at > '2024-01-01';
SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31';

-- Not good for:
SELECT * FROM users WHERE email LIKE '%@gmail.com';  -- Leading wildcard
```

### Hash Index

```sql
-- Hash: Only for equality comparisons (PostgreSQL 10+)
CREATE INDEX idx_users_email_hash ON users USING HASH (email);

-- Faster than B-tree for = only
SELECT * FROM users WHERE email = 'test@example.com';

-- Does NOT support:
-- Range queries, ORDER BY, LIKE, IS NULL
```

### GIN (Generalized Inverted Index)

```sql
-- GIN: For multi-valued columns (arrays, JSONB, full-text)
CREATE INDEX idx_products_tags ON products USING GIN (tags);
CREATE INDEX idx_products_metadata ON products USING GIN (metadata);
CREATE INDEX idx_articles_search ON articles USING GIN (search_vector);

-- Array queries
SELECT * FROM products WHERE tags @> ARRAY['electronics'];
SELECT * FROM products WHERE 'sale' = ANY(tags);

-- JSONB queries
SELECT * FROM products WHERE metadata @> '{"category": "shoes"}';
SELECT * FROM products WHERE metadata ? 'discount';

-- Full-text search
SELECT * FROM articles WHERE search_vector @@ to_tsquery('postgresql & index');
```

### GiST (Generalized Search Tree)

```sql
-- GiST: For geometric data, ranges, full-text
CREATE INDEX idx_locations_point ON locations USING GiST (coordinates);
CREATE INDEX idx_events_during ON events USING GiST (time_range);

-- Geometric queries
SELECT * FROM locations
WHERE coordinates <-> point(40.7128, -74.0060) < 0.01;

-- Range queries
SELECT * FROM events
WHERE time_range && tstzrange('2024-01-01', '2024-01-31');

-- Full-text (alternative to GIN)
CREATE INDEX idx_articles_fts ON articles USING GiST (search_vector);
```

### BRIN (Block Range Index)

```sql
-- BRIN: For large tables with natural ordering
CREATE INDEX idx_logs_created ON logs USING BRIN (created_at);

-- Very small index size, good for sequential data
-- Best when: table is physically ordered by the indexed column

-- Ideal for:
-- - Time-series data (logs, events, metrics)
-- - Append-only tables
-- - Very large tables (millions+ rows)

-- Check correlation (should be close to 1.0 or -1.0)
SELECT correlation FROM pg_stats
WHERE tablename = 'logs' AND attname = 'created_at';
```

## Composite Indexes

### Column Order Matters

```sql
-- Index on (a, b, c) supports:
-- ✓ WHERE a = ?
-- ✓ WHERE a = ? AND b = ?
-- ✓ WHERE a = ? AND b = ? AND c = ?
-- ✓ WHERE a = ? ORDER BY b
-- ✗ WHERE b = ?
-- ✗ WHERE c = ?
-- ✗ WHERE b = ? AND c = ?

-- Example
CREATE INDEX idx_orders_customer_status_date
  ON orders(customer_id, status, created_at);

-- Uses index fully:
SELECT * FROM orders
WHERE customer_id = 'uuid' AND status = 'pending'
ORDER BY created_at DESC;

-- Uses partial index (customer_id only):
SELECT * FROM orders
WHERE customer_id = 'uuid';

-- Cannot use index:
SELECT * FROM orders
WHERE status = 'pending';  -- Missing leading column
```

### Equality Before Range

```sql
-- Put equality columns before range columns

-- Bad: Range column first
CREATE INDEX idx_bad ON orders(created_at, status);

-- Good: Equality column first
CREATE INDEX idx_good ON orders(status, created_at);

-- Query:
SELECT * FROM orders
WHERE status = 'pending'
  AND created_at > '2024-01-01';
```

### Include Columns for Covering Index

```sql
-- Covering index: Include all needed columns
CREATE INDEX idx_orders_covering
  ON orders(customer_id, status)
  INCLUDE (total, created_at);

-- Index-only scan (no heap access):
SELECT customer_id, status, total, created_at
FROM orders
WHERE customer_id = 'uuid' AND status = 'pending';
```

## Partial Indexes

```sql
-- Index only rows that match a condition
CREATE INDEX idx_orders_pending
  ON orders(created_at DESC)
  WHERE status = 'pending';

-- Smaller index, faster queries for common case
SELECT * FROM orders
WHERE status = 'pending'
ORDER BY created_at DESC;

-- Other examples:
-- Active users only
CREATE INDEX idx_users_active_email
  ON users(email)
  WHERE status = 'active' AND deleted_at IS NULL;

-- Recent orders only
CREATE INDEX idx_orders_recent
  ON orders(customer_id, created_at DESC)
  WHERE created_at > NOW() - INTERVAL '90 days';

-- Non-null values only
CREATE INDEX idx_users_phone
  ON users(phone)
  WHERE phone IS NOT NULL;
```

## Expression Indexes

```sql
-- Index on computed values
CREATE INDEX idx_users_email_lower
  ON users(LOWER(email));

-- Query must match expression exactly:
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- Date extraction
CREATE INDEX idx_orders_month
  ON orders(DATE_TRUNC('month', created_at));

SELECT * FROM orders
WHERE DATE_TRUNC('month', created_at) = '2024-01-01';

-- JSON field extraction
CREATE INDEX idx_products_category
  ON products((metadata->>'category'));

SELECT * FROM products
WHERE metadata->>'category' = 'electronics';

-- Computed status
CREATE INDEX idx_orders_overdue
  ON orders((created_at + interval '7 days'))
  WHERE status = 'pending';
```

## Index Selection Strategy

### When to Create Indexes

```
┌─────────────────────────────────────────────────────────────────┐
│                  Index Decision Matrix                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ALWAYS INDEX:                                                   │
│  ✓ Primary keys (automatic)                                     │
│  ✓ Foreign keys                                                 │
│  ✓ Columns in WHERE with high selectivity                       │
│  ✓ Columns used in JOIN conditions                              │
│  ✓ Columns used for ORDER BY frequently                         │
│                                                                  │
│  CONSIDER INDEXING:                                              │
│  ~ Columns in WHERE with medium selectivity                     │
│  ~ Columns used in GROUP BY                                     │
│  ~ Covering indexes for critical queries                        │
│                                                                  │
│  AVOID INDEXING:                                                 │
│  ✗ Low cardinality columns (boolean, status with few values)   │
│  ✗ Columns rarely used in queries                               │
│  ✗ Small tables (< 1000 rows)                                   │
│  ✗ Frequently updated columns                                   │
│  ✗ Wide columns (long strings)                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cardinality Analysis

```sql
-- Check column cardinality
SELECT
  attname as column_name,
  n_distinct,
  CASE
    WHEN n_distinct < 0 THEN
      ROUND((-n_distinct * reltuples)::numeric, 0)
    ELSE n_distinct
  END as estimated_unique_values,
  ROUND(
    CASE
      WHEN n_distinct < 0 THEN -n_distinct * 100
      ELSE (n_distinct / NULLIF(reltuples, 0)) * 100
    END::numeric,
    2
  ) as selectivity_pct
FROM pg_stats s
JOIN pg_class c ON c.relname = s.tablename
WHERE tablename = 'orders'
ORDER BY n_distinct DESC;

-- High selectivity (>10%) = good index candidate
-- Low selectivity (<1%) with few values = poor candidate
```

### Query Pattern Analysis

```sql
-- Analyze which columns are queried
SELECT
  query,
  calls,
  total_exec_time,
  mean_exec_time
FROM pg_stat_statements
WHERE query LIKE '%users%'
ORDER BY total_exec_time DESC;

-- Extract WHERE clause patterns
-- Look for columns that appear frequently with = or range operators
```

## Index Maintenance

### Monitor Index Usage

```sql
-- Find unused indexes
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as times_used,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Index usage statistics
SELECT
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;
```

### Monitor Index Bloat

```sql
-- Check for bloated indexes
SELECT
  schemaname,
  tablename,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size,
  idx_scan,
  idx_tup_read
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- Reindex bloated indexes
REINDEX INDEX CONCURRENTLY idx_name;

-- Or rebuild
CREATE INDEX CONCURRENTLY idx_name_new ON table(column);
DROP INDEX idx_name;
ALTER INDEX idx_name_new RENAME TO idx_name;
```

### Index Maintenance Commands

```sql
-- Rebuild index (PostgreSQL 12+)
REINDEX INDEX CONCURRENTLY idx_users_email;

-- Rebuild all indexes on table
REINDEX TABLE CONCURRENTLY users;

-- Update statistics
ANALYZE users;

-- Full maintenance
VACUUM ANALYZE users;
```

## Common Indexing Patterns

### User Lookup Pattern

```sql
-- Login by email
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- Search by name (case-insensitive)
CREATE INDEX idx_users_name_lower ON users(LOWER(name));

-- Active users only
CREATE INDEX idx_users_active ON users(id)
  WHERE status = 'active' AND deleted_at IS NULL;
```

### Order Management Pattern

```sql
-- Orders by customer
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- Recent orders (with status filter)
CREATE INDEX idx_orders_customer_recent
  ON orders(customer_id, created_at DESC)
  WHERE status != 'cancelled';

-- Pending orders for processing
CREATE INDEX idx_orders_pending_queue
  ON orders(created_at)
  WHERE status = 'pending';

-- Order search
CREATE INDEX idx_orders_search
  ON orders(order_number, customer_id);
```

### Product Catalog Pattern

```sql
-- Category browsing
CREATE INDEX idx_products_category ON products(category_id);

-- Price filtering
CREATE INDEX idx_products_category_price
  ON products(category_id, price);

-- Search with tags (GIN)
CREATE INDEX idx_products_tags ON products USING GIN (tags);

-- Full-text search
CREATE INDEX idx_products_search
  ON products USING GIN (to_tsvector('english', name || ' ' || description));

-- Active products only
CREATE INDEX idx_products_active
  ON products(category_id, created_at DESC)
  WHERE status = 'active' AND stock > 0;
```

### Time-Series Pattern

```sql
-- Large log table with BRIN
CREATE INDEX idx_logs_created ON logs USING BRIN (created_at);

-- Partition by time (more effective than indexes alone)
CREATE TABLE logs (
  id BIGSERIAL,
  created_at TIMESTAMPTZ NOT NULL,
  ...
) PARTITION BY RANGE (created_at);

-- Recent data queries
CREATE INDEX idx_logs_recent
  ON logs(created_at DESC, type)
  WHERE created_at > NOW() - INTERVAL '7 days';
```

## Anti-Patterns

```sql
-- ❌ Duplicate indexes
CREATE INDEX idx1 ON users(email);
CREATE INDEX idx2 ON users(email, name);  -- idx1 is redundant

-- ❌ Over-indexing
CREATE INDEX idx1 ON orders(status);
CREATE INDEX idx2 ON orders(status, customer_id);
CREATE INDEX idx3 ON orders(status, customer_id, created_at);
-- Keep only idx3, it covers all cases

-- ❌ Index on boolean/low-cardinality
CREATE INDEX idx_users_active ON users(is_active);  -- Only 2 values
-- Better: partial index
CREATE INDEX idx_users_active ON users(id) WHERE is_active = true;

-- ❌ Wide indexes on frequently updated columns
CREATE INDEX idx_users_all ON users(name, email, phone, address, city);
-- Causes excessive write overhead

-- ❌ Forgetting NULL behavior
SELECT * FROM users WHERE deleted_at = NULL;  -- WRONG
SELECT * FROM users WHERE deleted_at IS NULL;  -- CORRECT
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                  Indexing Best Practices                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Start with query patterns, not table structure              │
│                                                                  │
│  2. Index foreign keys always                                   │
│                                                                  │
│  3. Use composite indexes strategically                         │
│     - Equality columns before range columns                     │
│     - Most selective columns first                              │
│                                                                  │
│  4. Consider partial indexes for common filters                 │
│                                                                  │
│  5. Use covering indexes for critical queries                   │
│                                                                  │
│  6. Monitor and remove unused indexes                           │
│                                                                  │
│  7. Test index changes with production-like data                │
│                                                                  │
│  8. Create indexes CONCURRENTLY in production                   │
│                                                                  │
│  9. Balance read performance vs write overhead                  │
│                                                                  │
│  10. Document why each index exists                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
