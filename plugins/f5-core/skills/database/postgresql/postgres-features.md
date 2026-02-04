---
name: postgres-features
description: PostgreSQL-specific features and capabilities
category: database/postgresql
applies_to: postgresql
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# PostgreSQL Features

## Overview

PostgreSQL is the world's most advanced open-source database, known
for reliability, feature robustness, and extensibility.

## Data Types

### Standard Types

```sql
-- Numeric
SMALLINT          -- 2 bytes, -32768 to 32767
INTEGER           -- 4 bytes, -2B to 2B
BIGINT            -- 8 bytes, -9E18 to 9E18
DECIMAL(p, s)     -- Variable, exact precision
NUMERIC(p, s)     -- Same as DECIMAL
REAL              -- 4 bytes, 6 decimal precision
DOUBLE PRECISION  -- 8 bytes, 15 decimal precision
SERIAL            -- Auto-increment INT
BIGSERIAL         -- Auto-increment BIGINT

-- Character
CHAR(n)           -- Fixed-length, padded
VARCHAR(n)        -- Variable-length, limited
TEXT              -- Unlimited length

-- Date/Time
DATE              -- Date only
TIME              -- Time only
TIMESTAMP         -- Date and time
TIMESTAMPTZ       -- With timezone (recommended)
INTERVAL          -- Time span

-- Boolean
BOOLEAN           -- true/false/NULL
```

### PostgreSQL-Specific Types

```sql
-- UUID
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT
);

-- Arrays
CREATE TABLE posts (
  id SERIAL PRIMARY KEY,
  tags TEXT[] DEFAULT '{}',
  scores INTEGER[]
);

INSERT INTO posts (tags, scores)
VALUES (ARRAY['tech', 'sql'], ARRAY[85, 92, 78]);

SELECT * FROM posts WHERE 'sql' = ANY(tags);
SELECT * FROM posts WHERE tags @> ARRAY['tech'];

-- JSON / JSONB
CREATE TABLE events (
  id SERIAL PRIMARY KEY,
  data JSONB NOT NULL DEFAULT '{}'
);

-- JSONB is preferred (compressed, indexed, faster queries)

-- Range Types
CREATE TABLE reservations (
  id SERIAL PRIMARY KEY,
  room_id INT,
  during TSTZRANGE NOT NULL,
  EXCLUDE USING GIST (room_id WITH =, during WITH &&)
);

INSERT INTO reservations (room_id, during)
VALUES (1, '[2024-01-15 14:00, 2024-01-15 16:00)');

-- Network Types
CREATE TABLE servers (
  id SERIAL PRIMARY KEY,
  hostname TEXT,
  ip_address INET,
  subnet CIDR,
  mac MACADDR
);

SELECT * FROM servers WHERE ip_address << '192.168.1.0/24';

-- Geometric Types
CREATE TABLE places (
  id SERIAL PRIMARY KEY,
  name TEXT,
  location POINT,
  area POLYGON
);

SELECT * FROM places
WHERE location <-> POINT(0, 0) < 10;  -- Distance

-- Enum Types
CREATE TYPE status AS ENUM ('pending', 'active', 'completed');
CREATE TABLE tasks (
  id SERIAL PRIMARY KEY,
  status status DEFAULT 'pending'
);
```

## Advanced Features

### UPSERT (INSERT ON CONFLICT)

```sql
-- Insert or update
INSERT INTO products (sku, name, price)
VALUES ('SKU001', 'Widget', 29.99)
ON CONFLICT (sku) DO UPDATE SET
  name = EXCLUDED.name,
  price = EXCLUDED.price,
  updated_at = NOW();

-- Insert or do nothing
INSERT INTO visitors (ip_address, visited_at)
VALUES ('192.168.1.1', NOW())
ON CONFLICT (ip_address) DO NOTHING;

-- With partial index constraint
CREATE UNIQUE INDEX idx_active_email ON users (email) WHERE active = true;

INSERT INTO users (email, active)
VALUES ('john@example.com', true)
ON CONFLICT (email) WHERE active = true
DO UPDATE SET last_seen = NOW();
```

### RETURNING Clause

```sql
-- Get inserted data
INSERT INTO orders (user_id, total)
VALUES (1, 100.00)
RETURNING id, created_at;

-- Get updated data
UPDATE products SET price = price * 1.1
WHERE category = 'electronics'
RETURNING id, name, price as new_price;

-- Delete with returning
DELETE FROM sessions
WHERE expires_at < NOW()
RETURNING user_id, id;

-- Use in CTE
WITH inserted AS (
  INSERT INTO orders (user_id, total)
  VALUES (1, 100.00)
  RETURNING id
)
INSERT INTO order_audit (order_id, action)
SELECT id, 'created' FROM inserted;
```

### Lateral Joins

```sql
-- Top N per group (efficient)
SELECT c.name, recent.*
FROM customers c
CROSS JOIN LATERAL (
  SELECT o.id, o.total, o.created_at
  FROM orders o
  WHERE o.customer_id = c.id
  ORDER BY o.created_at DESC
  LIMIT 3
) recent;

-- Dependent subquery in FROM
SELECT p.name, stats.*
FROM products p
CROSS JOIN LATERAL (
  SELECT
    COUNT(*) as total_orders,
    SUM(quantity) as total_sold
  FROM order_items oi
  WHERE oi.product_id = p.id
) stats;
```

### Generate Series

```sql
-- Number series
SELECT generate_series(1, 10);
SELECT generate_series(1, 100, 5);  -- Step of 5

-- Date series
SELECT generate_series(
  '2024-01-01'::date,
  '2024-12-31'::date,
  '1 day'::interval
)::date as date;

-- Fill gaps in time series
WITH dates AS (
  SELECT generate_series(
    '2024-01-01',
    '2024-01-31',
    '1 day'
  )::date as date
)
SELECT
  d.date,
  COALESCE(SUM(o.total), 0) as revenue
FROM dates d
LEFT JOIN orders o ON DATE(o.created_at) = d.date
GROUP BY d.date
ORDER BY d.date;

-- Timestamp series
SELECT generate_series(
  NOW() - INTERVAL '24 hours',
  NOW(),
  INTERVAL '1 hour'
);
```

### Array Operations

```sql
-- Array construction
SELECT ARRAY[1, 2, 3];
SELECT ARRAY(SELECT id FROM users LIMIT 5);
SELECT array_agg(name) FROM users;

-- Array access
SELECT tags[1] FROM posts;  -- First element (1-indexed)
SELECT tags[1:2] FROM posts;  -- Slice

-- Array functions
SELECT
  array_length(tags, 1),      -- Length
  array_upper(tags, 1),       -- Upper bound
  array_position(tags, 'sql'), -- Find position
  array_cat(tags, ARRAY['new']), -- Concatenate
  array_remove(tags, 'old'),   -- Remove element
  array_replace(tags, 'old', 'new')
FROM posts;

-- Array operators
SELECT * FROM posts WHERE tags @> ARRAY['sql'];  -- Contains
SELECT * FROM posts WHERE tags && ARRAY['sql', 'db'];  -- Overlap
SELECT * FROM posts WHERE 'sql' = ANY(tags);  -- Element exists

-- Unnest array
SELECT id, unnest(tags) as tag FROM posts;

-- Array aggregation
SELECT
  category,
  array_agg(name ORDER BY name) as products
FROM products
GROUP BY category;
```

### Table Inheritance

```sql
-- Parent table
CREATE TABLE cities (
  name TEXT,
  population BIGINT,
  elevation INT
);

-- Child table
CREATE TABLE capitals (
  state TEXT
) INHERITS (cities);

-- Insert into child
INSERT INTO capitals (name, population, elevation, state)
VALUES ('Austin', 1000000, 149, 'Texas');

-- Query parent includes children
SELECT * FROM cities;  -- Includes capitals

-- Query only parent
SELECT * FROM ONLY cities;

-- Check tableoid
SELECT tableoid::regclass, * FROM cities;
```

### Partitioning

```sql
-- Range partitioning
CREATE TABLE measurements (
  id BIGSERIAL,
  device_id INT,
  measured_at TIMESTAMPTZ NOT NULL,
  value NUMERIC
) PARTITION BY RANGE (measured_at);

CREATE TABLE measurements_2024_q1 PARTITION OF measurements
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE measurements_2024_q2 PARTITION OF measurements
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- List partitioning
CREATE TABLE orders (
  id BIGSERIAL,
  region TEXT NOT NULL,
  total NUMERIC
) PARTITION BY LIST (region);

CREATE TABLE orders_americas PARTITION OF orders
  FOR VALUES IN ('US', 'CA', 'MX', 'BR');

CREATE TABLE orders_europe PARTITION OF orders
  FOR VALUES IN ('UK', 'DE', 'FR', 'IT');

-- Hash partitioning
CREATE TABLE logs (
  id BIGSERIAL,
  user_id INT,
  message TEXT
) PARTITION BY HASH (user_id);

CREATE TABLE logs_0 PARTITION OF logs FOR VALUES WITH (MODULUS 4, REMAINDER 0);
CREATE TABLE logs_1 PARTITION OF logs FOR VALUES WITH (MODULUS 4, REMAINDER 1);
CREATE TABLE logs_2 PARTITION OF logs FOR VALUES WITH (MODULUS 4, REMAINDER 2);
CREATE TABLE logs_3 PARTITION OF logs FOR VALUES WITH (MODULUS 4, REMAINDER 3);
```

### Advisory Locks

```sql
-- Session-level lock
SELECT pg_advisory_lock(12345);
-- ... do work ...
SELECT pg_advisory_unlock(12345);

-- Transaction-level lock (auto-released on commit)
SELECT pg_advisory_xact_lock(12345);

-- Try lock (non-blocking)
SELECT pg_try_advisory_lock(12345);  -- Returns true/false

-- Application-level mutex pattern
CREATE OR REPLACE FUNCTION process_order(p_order_id INT)
RETURNS BOOLEAN AS $$
DECLARE
  lock_obtained BOOLEAN;
BEGIN
  -- Try to get lock for this specific order
  SELECT pg_try_advisory_xact_lock('orders'::regclass::int, p_order_id)
  INTO lock_obtained;

  IF NOT lock_obtained THEN
    RETURN FALSE;  -- Another process is handling this
  END IF;

  -- Process order...
  UPDATE orders SET status = 'processing' WHERE id = p_order_id;

  RETURN TRUE;
END;
$$ LANGUAGE plpgsql;
```

### Listen/Notify

```sql
-- Subscribe to channel
LISTEN order_events;

-- Publish notification
NOTIFY order_events, '{"order_id": 123, "status": "completed"}';

-- Or using function
SELECT pg_notify('order_events', '{"order_id": 123}');

-- Trigger-based notification
CREATE OR REPLACE FUNCTION notify_order_change()
RETURNS TRIGGER AS $$
BEGIN
  PERFORM pg_notify(
    'order_events',
    json_build_object(
      'operation', TG_OP,
      'id', COALESCE(NEW.id, OLD.id),
      'status', NEW.status
    )::text
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_notify
  AFTER INSERT OR UPDATE ON orders
  FOR EACH ROW
  EXECUTE FUNCTION notify_order_change();
```

### Exclusion Constraints

```sql
-- Prevent overlapping ranges (requires btree_gist extension)
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE room_bookings (
  id SERIAL PRIMARY KEY,
  room_id INT NOT NULL,
  booked_during TSTZRANGE NOT NULL,
  EXCLUDE USING GIST (
    room_id WITH =,
    booked_during WITH &&
  )
);

-- This will succeed
INSERT INTO room_bookings (room_id, booked_during)
VALUES (1, '[2024-01-15 10:00, 2024-01-15 12:00)');

-- This will fail (overlapping)
INSERT INTO room_bookings (room_id, booked_during)
VALUES (1, '[2024-01-15 11:00, 2024-01-15 13:00)');
```

## Functions and Procedures

### PL/pgSQL Functions

```sql
-- Basic function
CREATE OR REPLACE FUNCTION calculate_discount(
  price NUMERIC,
  discount_pct NUMERIC DEFAULT 10
)
RETURNS NUMERIC AS $$
BEGIN
  RETURN price * (1 - discount_pct / 100);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function with OUT parameters
CREATE OR REPLACE FUNCTION get_order_stats(
  p_user_id INT,
  OUT total_orders INT,
  OUT total_amount NUMERIC,
  OUT avg_amount NUMERIC
) AS $$
BEGIN
  SELECT
    COUNT(*),
    COALESCE(SUM(total), 0),
    COALESCE(AVG(total), 0)
  INTO total_orders, total_amount, avg_amount
  FROM orders
  WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql STABLE;

-- Table-returning function
CREATE OR REPLACE FUNCTION get_top_customers(limit_count INT DEFAULT 10)
RETURNS TABLE (
  customer_id INT,
  customer_name TEXT,
  total_spent NUMERIC
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    u.id,
    u.name,
    SUM(o.total)
  FROM users u
  JOIN orders o ON u.id = o.user_id
  GROUP BY u.id, u.name
  ORDER BY SUM(o.total) DESC
  LIMIT limit_count;
END;
$$ LANGUAGE plpgsql STABLE;
```

### Stored Procedures (PostgreSQL 11+)

```sql
-- Procedure (can have transactions)
CREATE OR REPLACE PROCEDURE transfer_funds(
  from_account INT,
  to_account INT,
  amount NUMERIC
)
LANGUAGE plpgsql AS $$
BEGIN
  -- Debit
  UPDATE accounts SET balance = balance - amount
  WHERE id = from_account AND balance >= amount;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Insufficient funds or invalid account';
  END IF;

  -- Credit
  UPDATE accounts SET balance = balance + amount
  WHERE id = to_account;

  IF NOT FOUND THEN
    RAISE EXCEPTION 'Invalid destination account';
  END IF;

  COMMIT;
END;
$$;

-- Call procedure
CALL transfer_funds(1, 2, 100.00);
```

### Triggers

```sql
-- Audit trigger
CREATE TABLE audit_log (
  id SERIAL PRIMARY KEY,
  table_name TEXT,
  operation TEXT,
  old_data JSONB,
  new_data JSONB,
  changed_at TIMESTAMPTZ DEFAULT NOW(),
  changed_by TEXT DEFAULT current_user
);

CREATE OR REPLACE FUNCTION audit_trigger_func()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO audit_log (table_name, operation, old_data, new_data)
  VALUES (
    TG_TABLE_NAME,
    TG_OP,
    CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN to_jsonb(OLD) END,
    CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN to_jsonb(NEW) END
  );

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER orders_audit
  AFTER INSERT OR UPDATE OR DELETE ON orders
  FOR EACH ROW
  EXECUTE FUNCTION audit_trigger_func();

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON products
  FOR EACH ROW
  EXECUTE FUNCTION update_timestamp();
```

## Extensions

```sql
-- List available extensions
SELECT * FROM pg_available_extensions;

-- Common useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- Cryptography
CREATE EXTENSION IF NOT EXISTS "hstore";         -- Key-value pairs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Trigram matching
CREATE EXTENSION IF NOT EXISTS "btree_gist";     -- GiST index for scalar types
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN index for scalar types
CREATE EXTENSION IF NOT EXISTS "tablefunc";      -- Crosstab/pivot
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Query statistics
CREATE EXTENSION IF NOT EXISTS "postgis";        -- Geospatial
```
