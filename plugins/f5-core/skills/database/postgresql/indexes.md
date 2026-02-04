---
name: postgresql-indexes
description: PostgreSQL index types and strategies
category: database/postgresql
applies_to: postgresql
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# PostgreSQL Indexes

## Overview

Indexes are data structures that improve query performance by reducing
the amount of data that needs to be scanned. PostgreSQL offers several
index types, each optimized for different use cases.

## Index Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Index Types                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  B-tree    │ Default, equality and range queries               │
│  Hash      │ Equality only, rarely better than B-tree          │
│  GiST      │ Geometric, full-text, range types                  │
│  SP-GiST   │ Space-partitioned data (points, IP addresses)     │
│  GIN       │ Multiple values per row (arrays, JSONB, FTS)      │
│  BRIN      │ Block range, large sequential tables              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## B-tree Index

The default and most versatile index type.

### When to Use
- Equality comparisons (`=`)
- Range queries (`<`, `>`, `<=`, `>=`, `BETWEEN`)
- Pattern matching with fixed prefix (`LIKE 'abc%'`)
- `ORDER BY`, `MIN()`, `MAX()`
- `IS NULL` / `IS NOT NULL`

```sql
-- Basic B-tree (default)
CREATE INDEX idx_users_email ON users(email);

-- Equivalent explicit syntax
CREATE INDEX idx_users_email ON users USING btree(email);

-- Multi-column index
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);

-- Unique index
CREATE UNIQUE INDEX idx_users_email_unique ON users(email);

-- Covering index (includes non-key columns)
CREATE INDEX idx_orders_user ON orders(user_id)
  INCLUDE (total, status);

-- Query can use index-only scan
EXPLAIN SELECT user_id, total, status FROM orders WHERE user_id = 123;
```

### Multi-Column Index Order

```sql
-- Index on (a, b, c) is useful for:
-- WHERE a = 1
-- WHERE a = 1 AND b = 2
-- WHERE a = 1 AND b = 2 AND c = 3
-- ORDER BY a
-- ORDER BY a, b
-- ORDER BY a, b, c

-- NOT useful for:
-- WHERE b = 2 (leading column not used)
-- WHERE c = 3
-- ORDER BY b, a (wrong order)

-- Example
CREATE INDEX idx_orders_composite ON orders(user_id, status, created_at);

-- Uses index fully
SELECT * FROM orders
WHERE user_id = 1 AND status = 'pending'
ORDER BY created_at;

-- Uses index partially (user_id only)
SELECT * FROM orders WHERE user_id = 1;

-- Cannot use this index efficiently
SELECT * FROM orders WHERE status = 'pending';
```

## Partial Index

Index only a subset of rows, reducing size and maintenance.

```sql
-- Index only active users
CREATE INDEX idx_users_active ON users(email)
  WHERE status = 'active';

-- Index only pending orders
CREATE INDEX idx_orders_pending ON orders(created_at)
  WHERE status = 'pending';

-- Index only non-null values
CREATE INDEX idx_users_phone ON users(phone)
  WHERE phone IS NOT NULL;

-- Query must match the WHERE clause
-- This uses the index:
SELECT * FROM users WHERE status = 'active' AND email = 'test@example.com';

-- This does NOT use the index:
SELECT * FROM users WHERE email = 'test@example.com';

-- Common pattern: Unique constraint with conditions
CREATE UNIQUE INDEX idx_unique_active_email ON users(email)
  WHERE deleted_at IS NULL;
```

## Expression Index

Index on computed values.

```sql
-- Case-insensitive search
CREATE INDEX idx_users_email_lower ON users(LOWER(email));

-- Query must use same expression
SELECT * FROM users WHERE LOWER(email) = 'john@example.com';

-- Date extraction
CREATE INDEX idx_orders_month ON orders(DATE_TRUNC('month', created_at));

-- JSONB field
CREATE INDEX idx_products_brand ON products((metadata->>'brand'));

SELECT * FROM products WHERE metadata->>'brand' = 'Apple';

-- Computed column
CREATE INDEX idx_orders_total_with_tax ON orders((total * 1.1));
```

## GIN Index

Generalized Inverted Index - best for multiple values per row.

### When to Use
- Array containment (`@>`, `<@`, `&&`)
- JSONB operations
- Full-text search (tsvector)
- hstore key-value

```sql
-- Array index
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);

SELECT * FROM posts WHERE tags @> ARRAY['postgresql'];
SELECT * FROM posts WHERE tags && ARRAY['sql', 'database'];

-- JSONB index (all keys and values)
CREATE INDEX idx_products_data ON products USING GIN(data);

SELECT * FROM products WHERE data @> '{"brand": "Apple"}';
SELECT * FROM products WHERE data ? 'color';
SELECT * FROM products WHERE data ?| ARRAY['color', 'size'];

-- JSONB path ops (more compact, fewer operators)
CREATE INDEX idx_products_data_path ON products
  USING GIN(data jsonb_path_ops);

-- Only supports @> operator, but smaller and faster
SELECT * FROM products WHERE data @> '{"brand": "Apple"}';

-- Full-text search
CREATE INDEX idx_articles_search ON articles USING GIN(to_tsvector('english', title || ' ' || content));

SELECT * FROM articles
WHERE to_tsvector('english', title || ' ' || content) @@ to_tsquery('postgresql & performance');
```

### GIN Pending List

```sql
-- Check pending list size (large = slow inserts)
SELECT * FROM pg_stat_all_indexes WHERE indexrelname LIKE '%gin%';

-- Tune fastupdate
CREATE INDEX idx_posts_tags ON posts USING GIN(tags)
  WITH (fastupdate = off);  -- Slower inserts, faster reads

-- Or adjust pending list limit
ALTER INDEX idx_posts_tags SET (gin_pending_list_limit = 256);

-- Force cleanup
VACUUM posts;
```

## GiST Index

Generalized Search Tree - flexible, lossy indexing.

### When to Use
- Geometric data (points, boxes, polygons)
- Range types (overlap queries)
- Full-text search (alternative to GIN)
- Nearest neighbor searches

```sql
-- Enable extension for exclusion constraints
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Range overlap exclusion
CREATE TABLE reservations (
  id SERIAL PRIMARY KEY,
  room_id INT,
  during TSTZRANGE,
  EXCLUDE USING GIST (room_id WITH =, during WITH &&)
);

-- Geometric index
CREATE INDEX idx_places_location ON places USING GIST(location);

-- Nearest neighbor search (KNN)
SELECT * FROM places
ORDER BY location <-> POINT(40.7128, -74.0060)
LIMIT 10;

-- PostGIS example
CREATE INDEX idx_buildings_geom ON buildings USING GIST(geom);

SELECT * FROM buildings
WHERE ST_DWithin(geom, ST_MakePoint(-74.0060, 40.7128)::geography, 1000);
```

## BRIN Index

Block Range Index - very small, great for naturally ordered data.

### When to Use
- Large tables (millions of rows)
- Naturally correlated data (e.g., timestamps)
- Append-only or time-series data
- When index size matters

```sql
-- Time-series data
CREATE TABLE sensor_readings (
  id BIGSERIAL PRIMARY KEY,
  sensor_id INT,
  reading NUMERIC,
  recorded_at TIMESTAMPTZ NOT NULL
);

-- BRIN index (tiny compared to B-tree)
CREATE INDEX idx_readings_time ON sensor_readings
  USING BRIN(recorded_at)
  WITH (pages_per_range = 128);

-- Compare sizes
SELECT
  pg_size_pretty(pg_relation_size('idx_readings_time')) as brin_size;
-- vs B-tree would be much larger

-- Works well when data is physically ordered
INSERT INTO sensor_readings (sensor_id, reading, recorded_at)
SELECT
  (random() * 100)::int,
  random() * 100,
  NOW() - (generate_series * INTERVAL '1 second')
FROM generate_series(1, 10000000);

-- Query range
SELECT * FROM sensor_readings
WHERE recorded_at BETWEEN '2024-01-01' AND '2024-01-02';
```

### BRIN Limitations

```sql
-- BRIN doesn't help when:
-- 1. Data is not correlated with physical order
-- 2. You need exact matches frequently
-- 3. Table is small

-- Check correlation
SELECT
  attname,
  correlation
FROM pg_stats
WHERE tablename = 'sensor_readings'
  AND attname = 'recorded_at';
-- Correlation close to 1 or -1 = good for BRIN
```

## Hash Index

Equality-only, WAL-logged since PostgreSQL 10.

```sql
-- Hash index (rarely better than B-tree)
CREATE INDEX idx_sessions_token ON sessions USING HASH(token);

-- Only supports equality
SELECT * FROM sessions WHERE token = 'abc123';

-- B-tree is usually better because:
-- - Supports range queries
-- - Smaller for many data types
-- - More battle-tested
```

## Index Maintenance

### Monitoring

```sql
-- Index usage stats
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Unused indexes (candidates for removal)
SELECT
  schemaname || '.' || relname as table,
  indexrelname as index,
  pg_size_pretty(pg_relation_size(i.indexrelid)) as size,
  idx_scan as scans
FROM pg_stat_user_indexes i
JOIN pg_index using (indexrelid)
WHERE idx_scan < 50
  AND NOT indisunique
ORDER BY pg_relation_size(i.indexrelid) DESC;

-- Index bloat
SELECT
  schemaname || '.' || tablename as table,
  indexname,
  pg_size_pretty(pg_relation_size(indexrelid)) as size,
  ROUND(100 * pg_relation_size(indexrelid) / pg_relation_size(indrelid)) as index_ratio
FROM pg_stat_user_indexes
JOIN pg_index USING (indexrelid)
ORDER BY pg_relation_size(indexrelid) DESC;
```

### Rebuilding

```sql
-- Rebuild index (locks table)
REINDEX INDEX idx_users_email;
REINDEX TABLE users;

-- Concurrent rebuild (no lock, PostgreSQL 12+)
REINDEX INDEX CONCURRENTLY idx_users_email;

-- Create new, swap, drop (manual concurrent)
CREATE INDEX CONCURRENTLY idx_users_email_new ON users(email);
-- Test new index
DROP INDEX idx_users_email;
ALTER INDEX idx_users_email_new RENAME TO idx_users_email;
```

## Index Design Patterns

### Covering Indexes

```sql
-- Include extra columns to enable index-only scans
CREATE INDEX idx_orders_covering ON orders(user_id)
  INCLUDE (total, status, created_at);

-- Query satisfied entirely from index
EXPLAIN ANALYZE
SELECT user_id, total, status FROM orders WHERE user_id = 123;
-- Should show "Index Only Scan"
```

### Composite Key Strategy

```sql
-- Order matters: most selective or most filtered first
CREATE INDEX idx_orders_composite ON orders(status, user_id, created_at);

-- Good for:
WHERE status = 'pending' AND user_id = 123
WHERE status = 'pending'
ORDER BY status, user_id, created_at

-- Not useful for:
WHERE user_id = 123  -- Leading column not used
```

### Partial + Expression Combo

```sql
-- Optimized for specific query pattern
CREATE INDEX idx_orders_recent_total ON orders(total DESC)
  WHERE status = 'completed'
    AND created_at > NOW() - INTERVAL '30 days';

-- Perfect for:
SELECT * FROM orders
WHERE status = 'completed'
  AND created_at > NOW() - INTERVAL '30 days'
ORDER BY total DESC
LIMIT 10;
```

## Best Practices

```sql
-- 1. Always check EXPLAIN ANALYZE
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM users WHERE email = 'test@example.com';

-- 2. Consider selectivity
-- High selectivity (few matches) = good index candidate
SELECT
  attname,
  n_distinct,
  most_common_vals,
  most_common_freqs
FROM pg_stats
WHERE tablename = 'orders' AND attname = 'status';

-- 3. Foreign keys should almost always be indexed
ALTER TABLE orders ADD CONSTRAINT fk_user
  FOREIGN KEY (user_id) REFERENCES users(id);
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- 4. Consider maintenance overhead
-- More indexes = slower writes
-- Balance read vs write performance

-- 5. Use CONCURRENTLY for production
CREATE INDEX CONCURRENTLY idx_name ON table(column);
-- Takes longer but doesn't lock table
```
