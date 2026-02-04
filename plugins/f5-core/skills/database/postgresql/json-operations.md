---
name: json-operations
description: JSON and JSONB operations in PostgreSQL
category: database/postgresql
applies_to: postgresql
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# JSON Operations in PostgreSQL

## Overview

PostgreSQL provides robust JSON support through two types: `json`
(text storage) and `jsonb` (binary, decomposed storage). For most
use cases, **JSONB is preferred** due to better indexing and performance.

## JSON vs JSONB

| Feature | JSON | JSONB |
|---------|------|-------|
| Storage | Text (exact) | Binary (parsed) |
| Preserves whitespace | Yes | No |
| Preserves key order | Yes | No |
| Allows duplicate keys | Yes | No (last wins) |
| Indexing | Limited | Full (GIN) |
| Processing speed | Slower | Faster |
| Input overhead | None | Parse on insert |

```sql
-- JSON preserves formatting
SELECT '{"b": 1,   "a": 2}'::json;
-- Returns: {"b": 1,   "a": 2}

-- JSONB normalizes
SELECT '{"b": 1,   "a": 2}'::jsonb;
-- Returns: {"a": 2, "b": 1}

-- RECOMMENDATION: Use JSONB unless you need exact text preservation
```

## Creating JSON Data

```sql
-- Literal values
SELECT '{"name": "John", "age": 30}'::jsonb;
SELECT '["a", "b", "c"]'::jsonb;

-- Build from values
SELECT jsonb_build_object(
  'name', 'John',
  'age', 30,
  'active', true
);
-- Returns: {"age": 30, "name": "John", "active": true}

-- Build array
SELECT jsonb_build_array('a', 'b', 'c', 1, 2, 3);
-- Returns: ["a", "b", "c", 1, 2, 3]

-- Aggregate rows to JSON
SELECT jsonb_agg(name) FROM users;
-- Returns: ["Alice", "Bob", "Carol"]

SELECT jsonb_object_agg(id, name) FROM users;
-- Returns: {"1": "Alice", "2": "Bob", "3": "Carol"}

-- Row to JSON
SELECT to_jsonb(users.*) FROM users WHERE id = 1;
-- Returns: {"id": 1, "name": "Alice", "email": "alice@example.com", ...}

-- Array to JSON
SELECT array_to_json(ARRAY[1, 2, 3]);
-- Returns: [1,2,3]
```

## Querying JSON

### Extraction Operators

```sql
-- -> returns JSON/JSONB
-- ->> returns TEXT
-- #> path extraction (returns JSON)
-- #>> path extraction (returns TEXT)

SELECT data -> 'name' FROM products;       -- JSONB
SELECT data ->> 'name' FROM products;      -- TEXT

-- Nested access
SELECT data -> 'address' -> 'city' FROM users;     -- JSONB
SELECT data -> 'address' ->> 'city' FROM users;    -- TEXT
SELECT data #> '{address,city}' FROM users;        -- JSONB (path)
SELECT data #>> '{address,city}' FROM users;       -- TEXT (path)

-- Array access (0-indexed)
SELECT data -> 'tags' -> 0 FROM products;          -- First tag
SELECT data -> 'tags' ->> 0 FROM products;         -- First tag as text

-- Practical example
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name TEXT,
  data JSONB DEFAULT '{}'
);

INSERT INTO products (name, data) VALUES
  ('Laptop', '{"brand": "Dell", "specs": {"ram": 16, "cpu": "i7"}, "tags": ["tech", "computer"]}'),
  ('Phone', '{"brand": "Apple", "specs": {"ram": 8, "storage": 256}, "tags": ["tech", "mobile"]}');

-- Query examples
SELECT
  name,
  data ->> 'brand' as brand,
  data -> 'specs' ->> 'ram' as ram,
  data -> 'tags' ->> 0 as primary_tag
FROM products;
```

### Containment Operators

```sql
-- @> contains
-- <@ is contained by
-- ? key exists
-- ?| any key exists
-- ?& all keys exist

-- Contains (useful with GIN index)
SELECT * FROM products WHERE data @> '{"brand": "Apple"}';
SELECT * FROM products WHERE data @> '{"specs": {"ram": 16}}';

-- Is contained by
SELECT * FROM products WHERE data <@ '{"brand": "Dell", "active": true}';

-- Key exists
SELECT * FROM products WHERE data ? 'brand';
SELECT * FROM products WHERE data -> 'specs' ? 'cpu';

-- Any key exists
SELECT * FROM products WHERE data ?| ARRAY['brand', 'manufacturer'];

-- All keys exist
SELECT * FROM products WHERE data ?& ARRAY['brand', 'specs'];
```

### Path Queries (PostgreSQL 12+)

```sql
-- @? path exists
-- @@ path predicate

-- Check if path exists with value
SELECT * FROM products
WHERE data @? '$.specs.cpu';

-- Path predicate
SELECT * FROM products
WHERE data @@ '$.specs.ram > 8';

SELECT * FROM products
WHERE data @@ '$.tags[*] == "tech"';

-- Complex path queries
SELECT * FROM products
WHERE data @@ '$.specs.ram >= 8 && $.brand == "Apple"';

-- jsonpath functions
SELECT jsonb_path_query(data, '$.tags[*]') FROM products;
SELECT jsonb_path_query_array(data, '$.tags[*]') FROM products;
SELECT jsonb_path_exists(data, '$.specs.cpu') FROM products;
```

## Modifying JSON

### Update Operators

```sql
-- || concatenate/merge (JSONB only)
SELECT '{"a": 1}'::jsonb || '{"b": 2}'::jsonb;
-- Returns: {"a": 1, "b": 2}

-- Overwrite existing key
SELECT '{"a": 1, "b": 2}'::jsonb || '{"b": 3}'::jsonb;
-- Returns: {"a": 1, "b": 3}

-- - remove key
SELECT '{"a": 1, "b": 2}'::jsonb - 'a';
-- Returns: {"b": 2}

-- - remove array element by index
SELECT '["a", "b", "c"]'::jsonb - 1;
-- Returns: ["a", "c"]

-- #- remove at path
SELECT '{"a": {"b": 1, "c": 2}}'::jsonb #- '{a,b}';
-- Returns: {"a": {"c": 2}}
```

### Update Functions

```sql
-- jsonb_set: Set value at path
UPDATE products SET data = jsonb_set(
  data,
  '{specs,ram}',
  '32'::jsonb
) WHERE id = 1;

-- Create missing path
UPDATE products SET data = jsonb_set(
  data,
  '{specs,gpu}',
  '"RTX 4080"'::jsonb,
  true  -- create_missing
) WHERE id = 1;

-- jsonb_insert: Insert into array
UPDATE products SET data = jsonb_insert(
  data,
  '{tags,0}',  -- Insert at position 0
  '"new-tag"'::jsonb,
  false  -- Insert before (false) or after (true)
) WHERE id = 1;

-- Nested object update
UPDATE products SET data = jsonb_set(
  data,
  '{address}',
  jsonb_build_object(
    'street', '123 Main St',
    'city', 'New York'
  )
) WHERE id = 1;

-- Increment numeric value
UPDATE products SET data = jsonb_set(
  data,
  '{views}',
  to_jsonb(COALESCE((data->>'views')::int, 0) + 1)
) WHERE id = 1;

-- Remove key
UPDATE products SET data = data - 'deprecated_field';

-- Remove nested key
UPDATE products SET data = data #- '{specs,old_field}';
```

### Strip Nulls

```sql
-- Remove null values
SELECT jsonb_strip_nulls('{"a": 1, "b": null, "c": {"d": null}}'::jsonb);
-- Returns: {"a": 1, "c": {}}
```

## Expanding JSON

### jsonb_each / jsonb_each_text

```sql
-- Expand object to rows
SELECT * FROM jsonb_each('{"a": 1, "b": 2}'::jsonb);
-- key | value
-- ----+-------
-- a   | 1
-- b   | 2

-- Practical use
SELECT
  p.id,
  p.name,
  specs.key as spec_name,
  specs.value as spec_value
FROM products p,
  jsonb_each(p.data -> 'specs') as specs;
```

### jsonb_array_elements

```sql
-- Expand array to rows
SELECT * FROM jsonb_array_elements('["a", "b", "c"]'::jsonb);
-- value
-- -------
-- "a"
-- "b"
-- "c"

-- Array elements as text
SELECT * FROM jsonb_array_elements_text('["a", "b", "c"]'::jsonb);
-- value
-- -------
-- a
-- b
-- c

-- Practical use: Find products with specific tag
SELECT DISTINCT p.id, p.name
FROM products p,
  jsonb_array_elements_text(p.data -> 'tags') as tag
WHERE tag = 'tech';
```

### jsonb_to_record

```sql
-- Convert JSON to record
SELECT * FROM jsonb_to_record('{"id": 1, "name": "Test"}'::jsonb)
  AS x(id int, name text);

-- Array to records
SELECT * FROM jsonb_to_recordset(
  '[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'::jsonb
) AS x(id int, name text);

-- Practical: Parse JSON array from API response
SELECT
  (item->>'id')::int as product_id,
  item->>'name' as product_name,
  (item->>'price')::numeric as price
FROM jsonb_array_elements(api_response) as item;
```

## Indexing JSON

### GIN Index

```sql
-- Default GIN operator class (all operators)
CREATE INDEX idx_products_data ON products USING GIN(data);

-- Supports: @>, ?, ?|, ?&
SELECT * FROM products WHERE data @> '{"brand": "Apple"}';
SELECT * FROM products WHERE data ? 'brand';

-- jsonb_path_ops (smaller, faster, @> only)
CREATE INDEX idx_products_data_path ON products
  USING GIN(data jsonb_path_ops);

-- Only supports @>
SELECT * FROM products WHERE data @> '{"brand": "Apple"}';
```

### Expression Index

```sql
-- Index specific field
CREATE INDEX idx_products_brand ON products((data->>'brand'));

-- Use in queries
SELECT * FROM products WHERE data->>'brand' = 'Apple';

-- Index nested field
CREATE INDEX idx_products_ram ON products(((data->'specs'->>'ram')::int));

SELECT * FROM products WHERE (data->'specs'->>'ram')::int >= 16;

-- Partial index on JSON condition
CREATE INDEX idx_active_products ON products(id)
  WHERE (data->>'active')::boolean = true;
```

## Aggregating to JSON

```sql
-- Aggregate rows to JSON array
SELECT jsonb_agg(
  jsonb_build_object(
    'id', id,
    'name', name,
    'total', total
  )
) as orders_json
FROM orders
WHERE user_id = 1;

-- Aggregate with ordering
SELECT jsonb_agg(
  jsonb_build_object('id', id, 'name', name)
  ORDER BY name
) FROM users;

-- Group and aggregate
SELECT
  category,
  jsonb_agg(jsonb_build_object(
    'id', id,
    'name', name,
    'price', price
  )) as products
FROM products
GROUP BY category;

-- Nested aggregation
SELECT jsonb_build_object(
  'user', jsonb_build_object('id', u.id, 'name', u.name),
  'orders', (
    SELECT jsonb_agg(jsonb_build_object(
      'id', o.id,
      'total', o.total
    ))
    FROM orders o
    WHERE o.user_id = u.id
  )
)
FROM users u
WHERE u.id = 1;
```

## Common Patterns

### Schema Flexibility

```sql
-- Base columns + flexible metadata
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  sku VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  -- Flexible attributes
  attributes JSONB DEFAULT '{}',
  -- Searchable metadata
  search_data JSONB DEFAULT '{}'
);

-- Different products have different attributes
INSERT INTO products (sku, name, price, attributes) VALUES
  ('LAPTOP-001', 'Laptop Pro', 999.99, '{"brand": "Dell", "ram_gb": 16, "screen_size": 15.6}'),
  ('SHIRT-001', 'Cotton Shirt', 29.99, '{"brand": "Zara", "size": "M", "color": "blue"}');
```

### Event Sourcing Payload

```sql
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  stream_id UUID NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  payload JSONB NOT NULL,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_stream ON events(stream_id, id);
CREATE INDEX idx_events_type ON events USING GIN(payload jsonb_path_ops);

INSERT INTO events (stream_id, event_type, payload) VALUES
  ('uuid-1', 'OrderCreated', '{"order_id": 123, "customer_id": 456, "items": [{"sku": "A", "qty": 2}]}'),
  ('uuid-1', 'OrderPaid', '{"order_id": 123, "amount": 99.99, "method": "card"}');
```

### Audit Trail

```sql
CREATE TABLE audit_log (
  id BIGSERIAL PRIMARY KEY,
  table_name TEXT NOT NULL,
  record_id TEXT NOT NULL,
  action TEXT NOT NULL,
  old_data JSONB,
  new_data JSONB,
  changed_fields TEXT[],
  changed_by TEXT DEFAULT current_user,
  changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
DECLARE
  changed_fields TEXT[];
BEGIN
  IF TG_OP = 'UPDATE' THEN
    SELECT array_agg(key)
    INTO changed_fields
    FROM (
      SELECT key
      FROM jsonb_each(to_jsonb(NEW.*))
      EXCEPT
      SELECT key
      FROM jsonb_each(to_jsonb(OLD.*))
      WHERE to_jsonb(OLD.*)->key = to_jsonb(NEW.*)->key
    ) diff;
  END IF;

  INSERT INTO audit_log (table_name, record_id, action, old_data, new_data, changed_fields)
  VALUES (
    TG_TABLE_NAME,
    COALESCE(NEW.id::text, OLD.id::text),
    TG_OP,
    CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD.*) END,
    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW.*) END,
    changed_fields
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

### Configuration Storage

```sql
CREATE TABLE app_config (
  key VARCHAR(100) PRIMARY KEY,
  value JSONB NOT NULL,
  description TEXT,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

INSERT INTO app_config (key, value, description) VALUES
  ('feature_flags', '{"new_checkout": true, "dark_mode": false}', 'Feature toggles'),
  ('rate_limits', '{"api": {"requests": 1000, "window": 3600}}', 'API rate limits');

-- Get config value
SELECT value->'new_checkout' FROM app_config WHERE key = 'feature_flags';

-- Update single flag
UPDATE app_config
SET value = jsonb_set(value, '{new_checkout}', 'false')
WHERE key = 'feature_flags';
```
