# Query Optimization

Query performance tuning, indexing strategies, EXPLAIN analysis, and connection pooling.

## Table of Contents

1. [Optimization Process](#optimization-process)
2. [Finding Slow Queries](#finding-slow-queries)
3. [Query Analysis](#query-analysis)
4. [Indexing Strategies](#indexing-strategies)
5. [Common Optimizations](#common-optimizations)
6. [Connection Pooling](#connection-pooling)

---

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

---

## Finding Slow Queries

### pg_stat_statements (PostgreSQL)

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

---

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

-- Full analysis in JSON
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM users WHERE email = 'test@example.com';
```

### Reading Execution Plans

| Scan Type | Description | Performance |
|-----------|-------------|-------------|
| Seq Scan | Full table scan | Slow on large tables |
| Index Scan | Uses index to find rows | Fast |
| Index Only Scan | Data from index alone | Fastest |
| Bitmap Index Scan | Multiple index conditions | Good for OR |
| Hash Join | Hash table for join | Fast for equality |
| Merge Join | Sorted data join | Fast for sorted data |
| Nested Loop | Loop through rows | Fast for small sets |

### Key Metrics

```
cost: Estimated startup..total cost
rows: Estimated number of rows
actual time: Real execution time (startup..total)
loops: Number of iterations
Buffers: shared hit (cache) / read (disk)
```

---

## Indexing Strategies

### Index Types (PostgreSQL)

| Type | Use Case | Operators |
|------|----------|-----------|
| B-tree | Default, equality/range | =, <, >, <=, >=, BETWEEN |
| Hash | Equality only | = |
| GIN | Arrays, JSONB, full-text | @>, <@, &&, @@ |
| GiST | Geometric, range types | <<, >>, &&, @> |
| BRIN | Large sequential tables | <, <=, =, >=, > |

### Composite Index

```sql
-- Order matters: most selective first
CREATE INDEX idx_orders_composite ON orders(status, user_id, created_at);

-- Good for:
WHERE status = 'pending' AND user_id = 123
WHERE status = 'pending'
ORDER BY status, user_id, created_at

-- NOT good for:
WHERE user_id = 123  -- Leading column not used
```

### Partial Index

```sql
-- Index only active users (smaller, faster)
CREATE INDEX idx_users_active ON users(email)
  WHERE status = 'active';

-- Index only pending orders
CREATE INDEX idx_orders_pending ON orders(created_at)
  WHERE status = 'pending';
```

### Covering Index

```sql
-- Include extra columns for index-only scans
CREATE INDEX idx_orders_covering ON orders(user_id)
  INCLUDE (total, status, created_at);

-- Query satisfied entirely from index
SELECT user_id, total, status FROM orders WHERE user_id = 123;
-- Shows "Index Only Scan"
```

### Expression Index

```sql
-- Case-insensitive search
CREATE INDEX idx_users_email_lower ON users(LOWER(email));

SELECT * FROM users WHERE LOWER(email) = 'test@example.com';

-- JSONB field
CREATE INDEX idx_products_brand ON products((metadata->>'brand'));
```

---

## Common Optimizations

### 1. Avoid SELECT *

```sql
-- Bad: Retrieves all columns
SELECT * FROM users WHERE id = 'uuid';

-- Good: Only needed columns
SELECT id, email, name FROM users WHERE id = 'uuid';
```

### 2. Use EXISTS Instead of IN

```sql
-- Slower
SELECT * FROM customers
WHERE id IN (SELECT customer_id FROM orders WHERE total > 1000);

-- Faster
SELECT * FROM customers c
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.customer_id = c.id AND o.total > 1000
);
```

### 3. Keyset Pagination

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
```

### 4. Batch Operations

```sql
-- Bad: Many small queries
FOR id IN [1, 2, 3, ..., 1000]:
  SELECT * FROM users WHERE id = :id;

-- Good: Single batch query
SELECT * FROM users WHERE id = ANY(ARRAY[1, 2, 3, ..., 1000]);
```

### 5. Avoid Functions on Indexed Columns

```sql
-- Bad: Cannot use index
SELECT * FROM users WHERE UPPER(email) = 'TEST@EXAMPLE.COM';

-- Good: Use expression index or store normalized
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
SELECT * FROM users WHERE LOWER(email) = 'test@example.com';
```

### 6. Optimize OR Conditions

```sql
-- Can prevent index usage
SELECT * FROM users
WHERE email = 'a@test.com' OR phone = '1234567890';

-- Use UNION for separate index scans
SELECT * FROM users WHERE email = 'a@test.com'
UNION
SELECT * FROM users WHERE phone = '1234567890';
```

---

## Connection Pooling

### Why Connection Pooling?

| Problem | Solution |
|---------|----------|
| Connection overhead | Reuse existing connections |
| Too many connections | Limit concurrent connections |
| Connection storms | Queue requests |
| Memory pressure | Bound resource usage |

### Node.js Connection Pool

```typescript
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: 20,                    // Max connections
  idleTimeoutMillis: 30000,   // Close idle connections
  connectionTimeoutMillis: 5000,
});

// Always release connections
async function query(sql: string, params?: any[]) {
  const client = await pool.connect();
  try {
    return await client.query(sql, params);
  } finally {
    client.release();
  }
}
```

### PgBouncer Configuration

```ini
# pgbouncer.ini
[databases]
mydb = host=localhost port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = transaction    # transaction, session, or statement
max_client_conn = 1000
default_pool_size = 25
min_pool_size = 5
reserve_pool_size = 5
```

### Pool Mode Comparison

| Mode | Use Case | Pros | Cons |
|------|----------|------|------|
| Session | General | Full features | Most connections |
| Transaction | Web apps | Efficient | No prepared statements |
| Statement | Simple queries | Most efficient | Very limited |

---

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

-- Unused indexes (candidates for removal)
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

---

## Optimization Checklist

| Check | Status |
|-------|--------|
| All WHERE columns indexed | ☐ |
| All JOIN columns indexed | ☐ |
| No SELECT * in production | ☐ |
| Pagination uses keyset | ☐ |
| Connection pooling configured | ☐ |
| Cache hit ratio > 99% | ☐ |
| Slow query logging enabled | ☐ |
| Unused indexes removed | ☐ |
