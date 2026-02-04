# Database Design

Schema design, data modeling, relationships, and denormalization patterns.

## Table of Contents

1. [Schema Design Principles](#schema-design-principles)
2. [Data Modeling](#data-modeling)
3. [Relationships](#relationships)
4. [Denormalization Strategies](#denormalization-strategies)

---

## Schema Design Principles

### Naming Conventions

```sql
-- Table names: plural, snake_case
CREATE TABLE users (...);
CREATE TABLE order_items (...);
CREATE TABLE user_preferences (...);

-- Column names: singular, snake_case
CREATE TABLE users (
  id UUID PRIMARY KEY,
  first_name VARCHAR(100),
  email_address VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Foreign keys: referenced_table_singular_id
CREATE TABLE orders (
  user_id UUID REFERENCES users(id),
  shipping_address_id UUID REFERENCES addresses(id)
);

-- Indexes: idx_table_columns
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);

-- Constraints: table_column_type
CONSTRAINT users_email_unique UNIQUE (email),
CONSTRAINT orders_total_positive CHECK (total > 0)
```

### Primary Key Strategies

```sql
-- UUID (recommended for distributed systems)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid()
);

-- Serial (simpler, but reveals ordering)
CREATE TABLE users (
  id SERIAL PRIMARY KEY
);

-- ULID (sortable UUID alternative)
CREATE TABLE events (
  id VARCHAR(26) PRIMARY KEY  -- ULID: 01ARZ3NDEKTSV4RRFFQ69G5FAV
);

-- Composite key (for junction tables)
CREATE TABLE user_roles (
  user_id UUID REFERENCES users(id),
  role_id UUID REFERENCES roles(id),
  PRIMARY KEY (user_id, role_id)
);
```

### Common Column Patterns

```sql
-- Timestamps pattern
CREATE TABLE entities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ  -- Soft delete
);

-- Audit columns
CREATE TABLE entities (
  created_by UUID REFERENCES users(id),
  updated_by UUID REFERENCES users(id)
);

-- Version for optimistic locking
CREATE TABLE entities (
  version INT NOT NULL DEFAULT 1
);

-- Update trigger for updated_at
CREATE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON entities
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## Data Modeling

### Entity-Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│      Users      │       │     Products    │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ email           │       │ name            │
│ name            │       │ price           │
└────────┬────────┘       │ category_id (FK)│
         │                └────────┬────────┘
         │ 1                       │ *
         │                         │
         │ *                       │
┌────────┴────────┐       ┌────────┴────────┐
│     Orders      │       │   Categories    │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │
│ user_id (FK)    │       │ name            │
│ total           │       │ parent_id (FK)  │
│ status          │       └─────────────────┘
└────────┬────────┘
         │ 1
         │
         │ *
┌────────┴────────┐
│   Order Items   │
├─────────────────┤
│ order_id (FK)   │
│ product_id (FK) │
│ quantity        │
│ unit_price      │
└─────────────────┘
```

### Multi-Tenant Design Patterns

```sql
-- Pattern 1: Shared Schema with Tenant ID
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL,
  user_id UUID NOT NULL,
  total DECIMAL(15, 2)
);

CREATE INDEX idx_orders_tenant ON orders(tenant_id);

-- Row Level Security (PostgreSQL)
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON orders
  USING (tenant_id = current_setting('app.current_tenant')::UUID);

-- Pattern 2: Schema per Tenant
CREATE SCHEMA tenant_abc;
CREATE TABLE tenant_abc.orders (...);
CREATE TABLE tenant_abc.users (...);

-- Pattern 3: Database per Tenant
-- Separate database connections per tenant
```

### Enum vs Lookup Table

```sql
-- PostgreSQL ENUM (simple, fast)
CREATE TYPE order_status AS ENUM ('pending', 'processing', 'shipped', 'delivered');

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  status order_status NOT NULL DEFAULT 'pending'
);

-- Lookup Table (flexible, can add metadata)
CREATE TABLE order_statuses (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  sort_order INT,
  is_active BOOLEAN DEFAULT true
);

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  status_id INT REFERENCES order_statuses(id)
);

-- When to use which:
-- ENUM: Fixed values, rarely change, no metadata needed
-- Lookup: Values change, need metadata, user-configurable
```

---

## Relationships

### One-to-Many

```sql
-- Users have many orders
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  total DECIMAL(15, 2) NOT NULL
);

CREATE INDEX idx_orders_user ON orders(user_id);
```

### Many-to-Many

```sql
-- Products belong to many categories, categories have many products
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL
);

CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL
);

-- Junction table
CREATE TABLE product_categories (
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  category_id UUID REFERENCES categories(id) ON DELETE CASCADE,
  is_primary BOOLEAN DEFAULT false,
  sort_order INT,
  PRIMARY KEY (product_id, category_id)
);

-- Query products with categories
SELECT p.*, array_agg(c.name) as categories
FROM products p
JOIN product_categories pc ON p.id = pc.product_id
JOIN categories c ON pc.category_id = c.id
GROUP BY p.id;
```

### Self-Referential

```sql
-- Categories with parent/child hierarchy
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  parent_id UUID REFERENCES categories(id) ON DELETE SET NULL
);

CREATE INDEX idx_categories_parent ON categories(parent_id);

-- Recursive query for full path
WITH RECURSIVE category_path AS (
  SELECT id, name, parent_id, name::TEXT as path, 1 as depth
  FROM categories
  WHERE parent_id IS NULL

  UNION ALL

  SELECT c.id, c.name, c.parent_id, cp.path || ' > ' || c.name, cp.depth + 1
  FROM categories c
  JOIN category_path cp ON c.parent_id = cp.id
)
SELECT * FROM category_path ORDER BY path;
```

### Polymorphic Associations

```sql
-- Comments can belong to posts, products, or users
-- Option 1: Separate FK columns (nullable)
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  content TEXT NOT NULL,
  post_id UUID REFERENCES posts(id),
  product_id UUID REFERENCES products(id),
  user_id UUID REFERENCES users(id),
  CHECK (
    (post_id IS NOT NULL)::INT +
    (product_id IS NOT NULL)::INT +
    (user_id IS NOT NULL)::INT = 1
  )
);

-- Option 2: Commentable pattern (type + id)
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  content TEXT NOT NULL,
  commentable_type VARCHAR(50) NOT NULL,  -- 'post', 'product', 'user'
  commentable_id UUID NOT NULL
);

CREATE INDEX idx_comments_commentable
  ON comments(commentable_type, commentable_id);

-- Option 3: Separate tables per type (cleanest)
CREATE TABLE post_comments (
  id UUID PRIMARY KEY,
  post_id UUID NOT NULL REFERENCES posts(id),
  content TEXT NOT NULL
);

CREATE TABLE product_comments (
  id UUID PRIMARY KEY,
  product_id UUID NOT NULL REFERENCES products(id),
  content TEXT NOT NULL
);
```

---

## Denormalization Strategies

### When to Denormalize

| Scenario | Solution |
|----------|----------|
| Frequent COUNT queries | Store counter column |
| Expensive JOINs | Embed related data |
| Complex aggregations | Materialized views |
| Read-heavy analytics | Summary tables |

### Counter Cache

```sql
-- Store order count on user
ALTER TABLE users ADD COLUMN orders_count INT DEFAULT 0;

-- Trigger to maintain count
CREATE FUNCTION update_user_orders_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE users SET orders_count = orders_count + 1 WHERE id = NEW.user_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE users SET orders_count = orders_count - 1 WHERE id = OLD.user_id;
  ELSIF TG_OP = 'UPDATE' AND OLD.user_id != NEW.user_id THEN
    UPDATE users SET orders_count = orders_count - 1 WHERE id = OLD.user_id;
    UPDATE users SET orders_count = orders_count + 1 WHERE id = NEW.user_id;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER orders_count_trigger
  AFTER INSERT OR UPDATE OR DELETE ON orders
  FOR EACH ROW EXECUTE FUNCTION update_user_orders_count();
```

### Computed Columns

```sql
-- Store computed total on order
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  subtotal DECIMAL(15,2),
  tax DECIMAL(15,2),
  shipping DECIMAL(15,2),
  total DECIMAL(15,2) GENERATED ALWAYS AS (subtotal + tax + shipping) STORED
);

-- Or use trigger for complex logic
CREATE FUNCTION calculate_order_total()
RETURNS TRIGGER AS $$
BEGIN
  SELECT COALESCE(SUM(quantity * unit_price), 0)
  INTO NEW.subtotal
  FROM order_items
  WHERE order_id = NEW.id;

  NEW.total = NEW.subtotal + COALESCE(NEW.tax, 0) + COALESCE(NEW.shipping, 0);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### Materialized Views

```sql
-- Pre-computed dashboard statistics
CREATE MATERIALIZED VIEW daily_sales_summary AS
SELECT
  DATE(created_at) as date,
  COUNT(*) as order_count,
  SUM(total) as total_revenue,
  AVG(total) as avg_order_value,
  COUNT(DISTINCT user_id) as unique_customers
FROM orders
WHERE status = 'completed'
GROUP BY DATE(created_at);

CREATE UNIQUE INDEX idx_daily_sales_date ON daily_sales_summary(date);

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY daily_sales_summary;

-- Schedule refresh (pg_cron)
SELECT cron.schedule('refresh_daily_sales', '0 * * * *',
  'REFRESH MATERIALIZED VIEW CONCURRENTLY daily_sales_summary');
```

### Embedded Documents (for NoSQL-like patterns)

```sql
-- Store address as JSONB instead of separate table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  addresses JSONB DEFAULT '[]'
);

-- Query JSON data
SELECT name, addresses->0->>'city' as primary_city
FROM users
WHERE addresses @> '[{"type": "home"}]';

-- Index for fast JSON queries
CREATE INDEX idx_users_addresses ON users USING GIN (addresses);
```

### Summary Tables

```sql
-- Daily aggregations for fast reporting
CREATE TABLE order_daily_stats (
  date DATE PRIMARY KEY,
  order_count INT NOT NULL,
  total_revenue DECIMAL(15,2) NOT NULL,
  avg_order_value DECIMAL(15,2),
  new_customers INT,
  returning_customers INT,
  top_products JSONB,
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Populate nightly
INSERT INTO order_daily_stats (date, order_count, total_revenue, avg_order_value)
SELECT
  DATE(created_at),
  COUNT(*),
  SUM(total),
  AVG(total)
FROM orders
WHERE DATE(created_at) = CURRENT_DATE - INTERVAL '1 day'
GROUP BY DATE(created_at)
ON CONFLICT (date) DO UPDATE SET
  order_count = EXCLUDED.order_count,
  total_revenue = EXCLUDED.total_revenue,
  avg_order_value = EXCLUDED.avg_order_value,
  updated_at = NOW();
```
