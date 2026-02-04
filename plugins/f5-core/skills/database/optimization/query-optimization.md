---
name: query-optimization
description: SQL query optimization techniques and patterns
category: database/optimization
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Query Optimization

## Overview

Query optimization improves database performance by reducing execution time,
minimizing resource usage, and avoiding common pitfalls. This guide covers
systematic approaches to identifying and fixing slow queries.

## Optimization Process

```
┌─────────────────────────────────────────────────────────────────┐
│                  Query Optimization Workflow                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. IDENTIFY slow queries (pg_stat_statements, slow log)        │
│         │                                                        │
│         ▼                                                        │
│  2. ANALYZE with EXPLAIN ANALYZE                                │
│         │                                                        │
│         ▼                                                        │
│  3. UNDERSTAND the execution plan                               │
│         │                                                        │
│         ▼                                                        │
│  4. OPTIMIZE (indexes, rewrites, schema changes)                │
│         │                                                        │
│         ▼                                                        │
│  5. VERIFY improvement with benchmarks                          │
│         │                                                        │
│         ▼                                                        │
│  6. MONITOR for regression                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Identifying Slow Queries

### PostgreSQL: pg_stat_statements

```sql
-- Enable extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Top 10 slowest queries by total time
SELECT
  substring(query, 1, 100) as query_preview,
  calls,
  ROUND(total_exec_time::numeric, 2) as total_time_ms,
  ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
  ROUND((total_exec_time / SUM(total_exec_time) OVER()) * 100, 2) as pct_total
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Queries with highest average time
SELECT
  substring(query, 1, 100) as query_preview,
  calls,
  ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
  ROUND(stddev_exec_time::numeric, 2) as stddev_ms
FROM pg_stat_statements
WHERE calls > 100
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Queries with most disk reads
SELECT
  substring(query, 1, 100) as query_preview,
  calls,
  shared_blks_read,
  shared_blks_hit,
  ROUND(
    100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0),
    2
  ) as cache_hit_pct
FROM pg_stat_statements
WHERE shared_blks_read > 1000
ORDER BY shared_blks_read DESC
LIMIT 10;
```

### Currently Running Queries

```sql
-- Find long-running queries
SELECT
  pid,
  now() - pg_stat_activity.query_start AS duration,
  query,
  state,
  wait_event_type,
  wait_event
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT ILIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- Kill a long-running query
SELECT pg_cancel_backend(pid);  -- Graceful
SELECT pg_terminate_backend(pid);  -- Force
```

## Query Analysis

### EXPLAIN Basics

```sql
-- Basic execution plan
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- With actual execution statistics
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- With buffer usage
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM users WHERE email = 'test@example.com';

-- Full analysis
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM users WHERE email = 'test@example.com';
```

### Reading Execution Plans

```
┌─────────────────────────────────────────────────────────────────┐
│                  Execution Plan Components                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Seq Scan on users                                              │
│    - Full table scan (slow on large tables)                     │
│                                                                  │
│  Index Scan using idx_users_email on users                      │
│    - Uses index to find rows (fast)                             │
│                                                                  │
│  Index Only Scan using idx_users_email on users                 │
│    - Data from index alone (fastest)                            │
│                                                                  │
│  Bitmap Index Scan + Bitmap Heap Scan                           │
│    - Multiple index conditions combined                          │
│                                                                  │
│  Hash Join / Merge Join / Nested Loop                           │
│    - Different join strategies                                  │
│                                                                  │
│  Sort                                                            │
│    - May spill to disk if memory insufficient                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Key Metrics:
- cost: Estimated startup..total cost
- rows: Estimated number of rows
- actual time: Real execution time (startup..total)
- loops: Number of iterations
- Buffers: shared hit (cache) / read (disk)
```

### Example Plan Analysis

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT o.id, o.total, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending'
  AND o.created_at > '2024-01-01'
ORDER BY o.created_at DESC
LIMIT 10;

/*
Limit  (cost=1234.56..1234.78 rows=10 width=52) (actual time=15.234..15.267 rows=10 loops=1)
  Buffers: shared hit=1234 read=56
  ->  Sort  (cost=1234.56..1245.67 rows=4444 width=52) (actual time=15.232..15.245 rows=10 loops=1)
        Sort Key: o.created_at DESC
        Sort Method: top-N heapsort  Memory: 26kB
        Buffers: shared hit=1234 read=56
        ->  Hash Join  (cost=123.45..1000.00 rows=4444 width=52) (actual time=1.234..12.345 rows=4500 loops=1)
              Hash Cond: (o.customer_id = c.id)
              Buffers: shared hit=1234 read=56
              ->  Seq Scan on orders o  (cost=0.00..800.00 rows=4444 width=44) (actual time=0.012..8.123 rows=4500 loops=1)
                    Filter: ((status = 'pending'::text) AND (created_at > '2024-01-01'::date))
                    Rows Removed by Filter: 95500
                    Buffers: shared hit=1000 read=50
              ->  Hash  (cost=100.00..100.00 rows=1000 width=36) (actual time=1.200..1.201 rows=1000 loops=1)
                    Buckets: 1024  Batches: 1  Memory Usage: 50kB
                    Buffers: shared hit=234 read=6
                    ->  Seq Scan on customers c  (cost=0.00..100.00 rows=1000 width=36) (actual time=0.008..0.900 rows=1000 loops=1)
                          Buffers: shared hit=234 read=6

Analysis:
- Sequential scan on orders: Need index on (status, created_at)
- 95500 rows filtered out: Filter is working but scanning too much
- Good: Hash join is efficient for this case
- Good: Sort uses memory, not disk
*/
```

## Common Optimization Techniques

### 1. Add Missing Indexes

```sql
-- Before: Seq Scan on orders (slow)
SELECT * FROM orders WHERE status = 'pending';

-- Add index
CREATE INDEX idx_orders_status ON orders(status);

-- After: Index Scan (fast)

-- Composite index for multiple conditions
CREATE INDEX idx_orders_status_date ON orders(status, created_at DESC);

-- Now this query is optimized:
SELECT * FROM orders
WHERE status = 'pending'
ORDER BY created_at DESC;
```

### 2. Use Covering Indexes

```sql
-- Query needs specific columns
SELECT id, email, name FROM users WHERE status = 'active';

-- Covering index includes all needed columns
CREATE INDEX idx_users_status_covering
  ON users(status) INCLUDE (id, email, name);

-- Results in Index Only Scan (no heap access)
```

### 3. Optimize JOINs

```sql
-- Ensure FK columns are indexed
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);

-- Use EXISTS instead of IN for subqueries
-- Bad
SELECT * FROM customers
WHERE id IN (SELECT customer_id FROM orders WHERE total > 1000);

-- Good
SELECT * FROM customers c
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.customer_id = c.id AND o.total > 1000
);

-- Use JOIN order hints if needed (PostgreSQL)
SET join_collapse_limit = 1;  -- Force join order as written
```

### 4. Avoid SELECT *

```sql
-- Bad: Retrieves all columns
SELECT * FROM users WHERE id = 'user-uuid';

-- Good: Only needed columns
SELECT id, email, name FROM users WHERE id = 'user-uuid';

-- Especially important with JOINs
-- Bad
SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id;

-- Good
SELECT o.id, o.total, c.name, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.id;
```

### 5. Optimize Pagination

```sql
-- Bad: OFFSET becomes slow on large pages
SELECT * FROM products
ORDER BY created_at DESC
LIMIT 20 OFFSET 10000;  -- Scans 10020 rows

-- Good: Keyset pagination
SELECT * FROM products
WHERE created_at < '2024-01-15 10:30:00'
ORDER BY created_at DESC
LIMIT 20;

-- Or with composite key for uniqueness
SELECT * FROM products
WHERE (created_at, id) < ('2024-01-15 10:30:00', 'last-seen-uuid')
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

### 6. Batch Operations

```sql
-- Bad: Many small queries
FOR id IN [1, 2, 3, ..., 1000]:
  SELECT * FROM users WHERE id = :id;

-- Good: Single batch query
SELECT * FROM users WHERE id = ANY(ARRAY[1, 2, 3, ..., 1000]);

-- Or use VALUES for complex conditions
SELECT u.* FROM users u
JOIN (VALUES (1), (2), (3), ..., (1000)) AS v(id) ON u.id = v.id;
```

### 7. Optimize Aggregations

```sql
-- Bad: Counting with complex conditions
SELECT COUNT(*) FROM orders WHERE status = 'pending';

-- Good: Use partial index for frequent counts
CREATE INDEX idx_orders_pending ON orders(id) WHERE status = 'pending';

-- Then count is fast
SELECT COUNT(*) FROM orders WHERE status = 'pending';

-- For approximate counts on large tables
SELECT reltuples::BIGINT FROM pg_class WHERE relname = 'orders';

-- Or use sampling
SELECT COUNT(*) * 100 FROM orders TABLESAMPLE SYSTEM(1);
```

### 8. Optimize OR Conditions

```sql
-- Bad: OR can prevent index usage
SELECT * FROM users
WHERE email = 'a@test.com' OR phone = '1234567890';

-- Good: Use UNION for separate index scans
SELECT * FROM users WHERE email = 'a@test.com'
UNION
SELECT * FROM users WHERE phone = '1234567890';

-- Or create covering index
CREATE INDEX idx_users_email_phone ON users(email, phone);
```

## Advanced Techniques

### Materialized Views

```sql
-- Pre-compute expensive aggregations
CREATE MATERIALIZED VIEW order_stats AS
SELECT
  customer_id,
  COUNT(*) as total_orders,
  SUM(total) as total_spent,
  AVG(total) as avg_order,
  MAX(created_at) as last_order
FROM orders
WHERE status = 'completed'
GROUP BY customer_id;

CREATE UNIQUE INDEX idx_order_stats_customer ON order_stats(customer_id);

-- Fast query
SELECT * FROM order_stats WHERE customer_id = 'uuid';

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY order_stats;
```

### Partial Indexes

```sql
-- Index only the rows you frequently query
CREATE INDEX idx_orders_pending ON orders(created_at DESC)
  WHERE status = 'pending';

CREATE INDEX idx_users_active ON users(email)
  WHERE status = 'active' AND deleted_at IS NULL;

-- Smaller index, faster maintenance, better performance
```

### Expression Indexes

```sql
-- Index on function result
CREATE INDEX idx_users_email_lower ON users(LOWER(email));

-- Now this uses the index
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- Index on date part
CREATE INDEX idx_orders_month ON orders(DATE_TRUNC('month', created_at));

-- Index on JSON field
CREATE INDEX idx_products_category ON products((metadata->>'category'));
```

### Query Hints

```sql
-- Force index scan (PostgreSQL)
SET enable_seqscan = off;
SELECT * FROM large_table WHERE indexed_column = 'value';
SET enable_seqscan = on;

-- Adjust work_mem for sorting
SET work_mem = '256MB';
SELECT * FROM orders ORDER BY created_at DESC;
RESET work_mem;

-- Parallel query settings
SET max_parallel_workers_per_gather = 4;
SELECT COUNT(*) FROM very_large_table;
```

## Anti-Patterns to Avoid

```sql
-- ❌ Functions on indexed columns
SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';
-- ✅ Use expression index or store normalized

-- ❌ Implicit type conversion
SELECT * FROM orders WHERE id = '123';  -- id is integer
-- ✅ Use correct type
SELECT * FROM orders WHERE id = 123;

-- ❌ Leading wildcard in LIKE
SELECT * FROM products WHERE name LIKE '%widget%';
-- ✅ Use full-text search or trigram index

-- ❌ NOT IN with NULLs
SELECT * FROM users WHERE id NOT IN (SELECT user_id FROM deleted_users);
-- ✅ Use NOT EXISTS
SELECT * FROM users u WHERE NOT EXISTS (
  SELECT 1 FROM deleted_users d WHERE d.user_id = u.id
);

-- ❌ Correlated subquery in SELECT
SELECT
  o.*,
  (SELECT COUNT(*) FROM order_items WHERE order_id = o.id) as item_count
FROM orders o;
-- ✅ Use JOIN
SELECT o.*, COALESCE(oi.item_count, 0) as item_count
FROM orders o
LEFT JOIN (
  SELECT order_id, COUNT(*) as item_count
  FROM order_items GROUP BY order_id
) oi ON o.id = oi.order_id;
```

## Performance Monitoring

### Key Metrics

```sql
-- Cache hit ratio (should be > 99%)
SELECT
  ROUND(
    100.0 * SUM(heap_blks_hit) /
    NULLIF(SUM(heap_blks_hit) + SUM(heap_blks_read), 0),
    2
  ) as cache_hit_ratio
FROM pg_statio_user_tables;

-- Index usage ratio
SELECT
  relname,
  ROUND(
    100.0 * idx_scan / NULLIF(idx_scan + seq_scan, 0),
    2
  ) as index_usage_pct,
  seq_scan,
  idx_scan
FROM pg_stat_user_tables
WHERE seq_scan + idx_scan > 100
ORDER BY index_usage_pct ASC;

-- Unused indexes
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) as index_size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE 'pg_%'
ORDER BY pg_relation_size(indexrelid) DESC;
```

## Optimization Checklist

| Check | Status |
|-------|--------|
| All WHERE columns indexed | ☐ |
| All JOIN columns indexed | ☐ |
| No SELECT * in production | ☐ |
| Pagination uses keyset | ☐ |
| Complex aggregations materialized | ☐ |
| No functions on indexed columns | ☐ |
| Cache hit ratio > 99% | ☐ |
| Slow queries monitored | ☐ |
