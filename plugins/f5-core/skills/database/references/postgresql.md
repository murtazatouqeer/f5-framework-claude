# PostgreSQL Features

PostgreSQL-specific features: advanced indexes, JSON/JSONB, full-text search, and extensions.

## Table of Contents

1. [Index Types](#index-types)
2. [JSON and JSONB](#json-and-jsonb)
3. [Full-Text Search](#full-text-search)
4. [Useful Extensions](#useful-extensions)
5. [Advanced Features](#advanced-features)

---

## Index Types

### Index Type Overview

| Type | Use Case | Best For |
|------|----------|----------|
| B-tree | Default | Equality, range, sorting |
| Hash | Equality only | Exact matches |
| GIN | Multiple values | Arrays, JSONB, full-text |
| GiST | Geometric | Ranges, nearest neighbor |
| BRIN | Sequential data | Time-series, logs |

### B-tree (Default)

```sql
-- Standard index
CREATE INDEX idx_users_email ON users(email);

-- Multi-column (order matters)
CREATE INDEX idx_orders_composite ON orders(user_id, status, created_at DESC);

-- Covering index (index-only scans)
CREATE INDEX idx_orders_covering ON orders(user_id)
  INCLUDE (total, status, created_at);

-- Partial index (smaller, faster)
CREATE INDEX idx_users_active ON users(email)
  WHERE status = 'active' AND deleted_at IS NULL;

-- Expression index
CREATE INDEX idx_users_email_lower ON users(LOWER(email));
```

### GIN (Generalized Inverted Index)

```sql
-- Array containment
CREATE INDEX idx_posts_tags ON posts USING GIN(tags);

SELECT * FROM posts WHERE tags @> ARRAY['postgresql'];
SELECT * FROM posts WHERE tags && ARRAY['sql', 'database'];

-- JSONB (all keys and values)
CREATE INDEX idx_products_data ON products USING GIN(data);

SELECT * FROM products WHERE data @> '{"brand": "Apple"}';
SELECT * FROM products WHERE data ? 'color';

-- JSONB path ops (more compact)
CREATE INDEX idx_products_path ON products USING GIN(data jsonb_path_ops);
```

### GiST (Generalized Search Tree)

```sql
-- Range exclusion constraints
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE reservations (
  id SERIAL PRIMARY KEY,
  room_id INT,
  during TSTZRANGE,
  EXCLUDE USING GIST (room_id WITH =, during WITH &&)
);

-- Nearest neighbor search
CREATE INDEX idx_places_location ON places USING GIST(location);

SELECT * FROM places
ORDER BY location <-> POINT(40.7128, -74.0060)
LIMIT 10;
```

### BRIN (Block Range Index)

```sql
-- Best for naturally ordered data (time-series)
CREATE INDEX idx_readings_time ON sensor_readings
  USING BRIN(recorded_at)
  WITH (pages_per_range = 128);

-- Check correlation (close to 1 or -1 = good for BRIN)
SELECT attname, correlation
FROM pg_stats
WHERE tablename = 'sensor_readings' AND attname = 'recorded_at';
```

---

## JSON and JSONB

### JSON vs JSONB

| Feature | JSON | JSONB |
|---------|------|-------|
| Storage | Text (as-is) | Binary (parsed) |
| Duplicate keys | Preserved | Last value wins |
| Key order | Preserved | Not preserved |
| Indexing | No | Yes (GIN) |
| Performance | Slower queries | Faster queries |

### JSONB Operations

```sql
-- Create table with JSONB
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  data JSONB DEFAULT '{}'
);

-- Insert
INSERT INTO products (id, name, data) VALUES (
  gen_random_uuid(),
  'Laptop',
  '{"brand": "Apple", "specs": {"ram": 16, "storage": 512}, "tags": ["electronics", "computer"]}'
);

-- Access operators
SELECT
  data->>'brand' as brand,           -- Get as text
  data->'specs'->>'ram' as ram,      -- Nested access
  data->'specs'->'ram' as ram_json,  -- Get as JSON
  data#>>'{specs,ram}' as ram_path   -- Path access
FROM products;

-- Containment operators
SELECT * FROM products WHERE data @> '{"brand": "Apple"}';
SELECT * FROM products WHERE data ? 'brand';
SELECT * FROM products WHERE data ?| ARRAY['brand', 'model'];
SELECT * FROM products WHERE data ?& ARRAY['brand', 'specs'];

-- Array access
SELECT * FROM products WHERE data->'tags' ? 'electronics';
```

### JSONB Updates

```sql
-- Set/update key
UPDATE products
SET data = jsonb_set(data, '{specs,ram}', '32')
WHERE id = 'uuid';

-- Add new key
UPDATE products
SET data = data || '{"warranty": "2 years"}'
WHERE id = 'uuid';

-- Remove key
UPDATE products
SET data = data - 'warranty'
WHERE id = 'uuid';

-- Remove nested key
UPDATE products
SET data = data #- '{specs,storage}'
WHERE id = 'uuid';
```

### JSONB Aggregation

```sql
-- Build JSON object from rows
SELECT jsonb_build_object(
  'total', COUNT(*),
  'brands', jsonb_agg(DISTINCT data->>'brand')
) FROM products;

-- Group into array
SELECT
  data->>'brand' as brand,
  jsonb_agg(name) as products
FROM products
GROUP BY data->>'brand';

-- Expand JSONB to rows
SELECT
  p.name,
  tag
FROM products p,
LATERAL jsonb_array_elements_text(p.data->'tags') as tag;
```

---

## Full-Text Search

### Basic Setup

```sql
-- Create search column
ALTER TABLE articles ADD COLUMN search_vector TSVECTOR;

-- Populate search vector
UPDATE articles SET search_vector =
  setweight(to_tsvector('english', COALESCE(title, '')), 'A') ||
  setweight(to_tsvector('english', COALESCE(content, '')), 'B');

-- Create GIN index
CREATE INDEX idx_articles_search ON articles USING GIN(search_vector);

-- Auto-update trigger
CREATE FUNCTION articles_search_update() RETURNS TRIGGER AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('english', COALESCE(NEW.title, '')), 'A') ||
    setweight(to_tsvector('english', COALESCE(NEW.content, '')), 'B');
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER articles_search_trigger
  BEFORE INSERT OR UPDATE ON articles
  FOR EACH ROW EXECUTE FUNCTION articles_search_update();
```

### Searching

```sql
-- Basic search
SELECT * FROM articles
WHERE search_vector @@ to_tsquery('english', 'postgresql & performance');

-- Phrase search
SELECT * FROM articles
WHERE search_vector @@ phraseto_tsquery('english', 'database optimization');

-- OR search
SELECT * FROM articles
WHERE search_vector @@ to_tsquery('english', 'postgres | mysql');

-- Prefix search
SELECT * FROM articles
WHERE search_vector @@ to_tsquery('english', 'optim:*');

-- With ranking
SELECT
  title,
  ts_rank(search_vector, query) as rank
FROM articles, to_tsquery('english', 'postgresql & optimization') query
WHERE search_vector @@ query
ORDER BY rank DESC;

-- Headline (highlighted results)
SELECT
  title,
  ts_headline('english', content, query, 'MaxWords=50, MinWords=25')
FROM articles, to_tsquery('english', 'postgresql') query
WHERE search_vector @@ query;
```

---

## Useful Extensions

### pg_stat_statements

```sql
-- Enable
CREATE EXTENSION pg_stat_statements;

-- Find slow queries
SELECT
  substring(query, 1, 100) as query,
  calls,
  ROUND(mean_exec_time::numeric, 2) as avg_ms,
  ROUND(total_exec_time::numeric, 2) as total_ms
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

### pg_trgm (Trigram Similarity)

```sql
CREATE EXTENSION pg_trgm;

-- Fuzzy search index
CREATE INDEX idx_users_name_trgm ON users USING GIN(name gin_trgm_ops);

-- Similarity search
SELECT * FROM users
WHERE name % 'John'
ORDER BY similarity(name, 'John') DESC;

-- LIKE with index support
SELECT * FROM users WHERE name ILIKE '%john%';
```

### uuid-ossp / pgcrypto

```sql
-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

SELECT uuid_generate_v4();

-- Or use built-in (PostgreSQL 13+)
SELECT gen_random_uuid();

-- Cryptographic functions
CREATE EXTENSION pgcrypto;

-- Password hashing
SELECT crypt('password', gen_salt('bf', 10));

-- Encryption
SELECT pgp_sym_encrypt('secret data', 'encryption_key');
SELECT pgp_sym_decrypt(encrypted_data, 'encryption_key');
```

### PostGIS (Geospatial)

```sql
CREATE EXTENSION postgis;

-- Add geometry column
ALTER TABLE locations ADD COLUMN geom GEOMETRY(Point, 4326);

-- Create spatial index
CREATE INDEX idx_locations_geom ON locations USING GIST(geom);

-- Find nearby locations (within 1km)
SELECT * FROM locations
WHERE ST_DWithin(
  geom,
  ST_MakePoint(-74.0060, 40.7128)::geography,
  1000
);

-- Distance calculation
SELECT
  name,
  ST_Distance(geom::geography, ST_MakePoint(-74.0060, 40.7128)::geography) as distance_m
FROM locations
ORDER BY geom <-> ST_MakePoint(-74.0060, 40.7128)::geometry
LIMIT 10;
```

---

## Advanced Features

### Common Table Expressions (CTE)

```sql
-- Recursive CTE for hierarchical data
WITH RECURSIVE category_tree AS (
  -- Base case
  SELECT id, name, parent_id, name::TEXT as path, 1 as depth
  FROM categories
  WHERE parent_id IS NULL

  UNION ALL

  -- Recursive case
  SELECT c.id, c.name, c.parent_id, ct.path || ' > ' || c.name, ct.depth + 1
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree ORDER BY path;
```

### Window Functions

```sql
-- Ranking
SELECT
  name,
  score,
  RANK() OVER (ORDER BY score DESC) as rank,
  DENSE_RANK() OVER (ORDER BY score DESC) as dense_rank,
  ROW_NUMBER() OVER (ORDER BY score DESC) as row_num
FROM players;

-- Running totals
SELECT
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) as running_total,
  AVG(amount) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7d
FROM transactions;

-- Partitioned windows
SELECT
  department,
  name,
  salary,
  AVG(salary) OVER (PARTITION BY department) as dept_avg,
  salary - AVG(salary) OVER (PARTITION BY department) as diff_from_avg
FROM employees;
```

### Table Partitioning

```sql
-- Range partitioning
CREATE TABLE orders (
  id UUID,
  created_at TIMESTAMPTZ NOT NULL,
  total DECIMAL(15,2)
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2024_q1 PARTITION OF orders
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

-- List partitioning
CREATE TABLE orders_by_region (
  id UUID,
  region VARCHAR(50) NOT NULL
) PARTITION BY LIST (region);

CREATE TABLE orders_us PARTITION OF orders_by_region
  FOR VALUES IN ('us-east', 'us-west');

-- Hash partitioning
CREATE TABLE orders_hash (
  id UUID,
  user_id UUID NOT NULL
) PARTITION BY HASH (user_id);

CREATE TABLE orders_hash_0 PARTITION OF orders_hash
  FOR VALUES WITH (MODULUS 4, REMAINDER 0);
```

### Row-Level Security

```sql
-- Enable RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- Create policy for tenant isolation
CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- Set tenant in application
SET app.current_tenant = 'tenant-uuid';

-- Force RLS for table owner too
ALTER TABLE orders FORCE ROW LEVEL SECURITY;
```

---

## PostgreSQL Quick Reference

| Feature | Syntax |
|---------|--------|
| UUID generation | `gen_random_uuid()` |
| Current timestamp | `NOW()` or `CURRENT_TIMESTAMP` |
| JSON access | `data->>'key'` (text) or `data->'key'` (json) |
| Array contains | `array_column @> ARRAY['value']` |
| Full-text search | `tsvector @@ tsquery` |
| Upsert | `INSERT ... ON CONFLICT ... DO UPDATE` |
| Returning | `INSERT/UPDATE/DELETE ... RETURNING *` |
