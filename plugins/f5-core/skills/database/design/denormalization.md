---
name: denormalization
description: Strategic denormalization for performance
category: database/design
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Denormalization

## Overview

Denormalization is the deliberate introduction of redundancy to
improve read performance. It trades write complexity and storage
for faster queries.

## When to Denormalize

```
┌─────────────────────────────────────────────────────────────────┐
│                  Denormalization Decision                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Consider denormalizing when:                                   │
│  ✓ Read-heavy workload (90%+ reads)                            │
│  ✓ Complex joins are causing performance issues                │
│  ✓ Reporting queries are too slow                              │
│  ✓ Caching isn't sufficient                                    │
│  ✓ Query patterns are well-understood and stable               │
│                                                                  │
│  Avoid denormalizing when:                                      │
│  ✗ Write-heavy workload                                        │
│  ✗ Data changes frequently                                     │
│  ✗ Storage is limited                                          │
│  ✗ Data integrity is critical                                  │
│  ✗ Query patterns are unpredictable                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Denormalization Strategies

### 1. Duplicated Columns

```sql
-- Normalized: Requires join
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  customer_id UUID REFERENCES customers(id),
  total DECIMAL(12, 2)
);

-- Query requires join
SELECT o.id, o.total, c.name, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.id = 'order-uuid';

-- Denormalized: Customer info duplicated
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  customer_id UUID REFERENCES customers(id),
  -- Duplicated customer data
  customer_name VARCHAR(255),
  customer_email VARCHAR(255),
  total DECIMAL(12, 2)
);

-- Fast query without join
SELECT id, total, customer_name, customer_email
FROM orders
WHERE id = 'order-uuid';

-- Maintain consistency with trigger
CREATE OR REPLACE FUNCTION sync_order_customer()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' OR NEW.customer_id != OLD.customer_id THEN
    SELECT name, email INTO NEW.customer_name, NEW.customer_email
    FROM customers WHERE id = NEW.customer_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_customer_sync
  BEFORE INSERT OR UPDATE OF customer_id ON orders
  FOR EACH ROW
  EXECUTE FUNCTION sync_order_customer();

-- Update all orders when customer changes
CREATE OR REPLACE FUNCTION propagate_customer_changes()
RETURNS TRIGGER AS $$
BEGIN
  UPDATE orders SET
    customer_name = NEW.name,
    customer_email = NEW.email
  WHERE customer_id = NEW.id
    AND (customer_name != NEW.name OR customer_email != NEW.email);
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER customer_change_propagation
  AFTER UPDATE OF name, email ON customers
  FOR EACH ROW
  EXECUTE FUNCTION propagate_customer_changes();
```

### 2. Pre-computed Aggregates

```sql
-- Without pre-computation: Slow aggregate query
SELECT
  p.id,
  p.name,
  COUNT(r.id) as review_count,
  AVG(r.rating) as avg_rating
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id;

-- With pre-computed aggregates
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  -- Pre-computed aggregates
  review_count INTEGER DEFAULT 0,
  rating_sum INTEGER DEFAULT 0,
  avg_rating DECIMAL(3, 2) DEFAULT 0
);

-- Fast query
SELECT id, name, review_count, avg_rating
FROM products
WHERE id = 'product-uuid';

-- Maintain with trigger
CREATE OR REPLACE FUNCTION update_product_stats()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE products SET
      review_count = review_count + 1,
      rating_sum = rating_sum + NEW.rating,
      avg_rating = (rating_sum + NEW.rating)::decimal / (review_count + 1)
    WHERE id = NEW.product_id;

  ELSIF TG_OP = 'DELETE' THEN
    UPDATE products SET
      review_count = GREATEST(0, review_count - 1),
      rating_sum = rating_sum - OLD.rating,
      avg_rating = CASE
        WHEN review_count <= 1 THEN 0
        ELSE (rating_sum - OLD.rating)::decimal / (review_count - 1)
      END
    WHERE id = OLD.product_id;

  ELSIF TG_OP = 'UPDATE' AND NEW.rating != OLD.rating THEN
    UPDATE products SET
      rating_sum = rating_sum - OLD.rating + NEW.rating,
      avg_rating = (rating_sum - OLD.rating + NEW.rating)::decimal / review_count
    WHERE id = NEW.product_id;
  END IF;

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER review_stats_trigger
  AFTER INSERT OR UPDATE OR DELETE ON reviews
  FOR EACH ROW
  EXECUTE FUNCTION update_product_stats();
```

### 3. Materialized Views

```sql
-- Create materialized view for complex report
CREATE MATERIALIZED VIEW customer_stats AS
SELECT
  c.id as customer_id,
  c.name,
  c.email,
  c.created_at as customer_since,
  COUNT(DISTINCT o.id) as total_orders,
  COALESCE(SUM(o.total), 0) as total_spent,
  COALESCE(AVG(o.total), 0) as avg_order_value,
  MAX(o.created_at) as last_order_date,
  COUNT(DISTINCT oi.product_id) as unique_products_purchased
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id AND o.status = 'completed'
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY c.id, c.name, c.email, c.created_at;

-- Create indexes on materialized view
CREATE UNIQUE INDEX idx_customer_stats_id ON customer_stats(customer_id);
CREATE INDEX idx_customer_stats_spent ON customer_stats(total_spent DESC);

-- Fast query
SELECT * FROM customer_stats
WHERE total_spent > 1000
ORDER BY total_spent DESC
LIMIT 100;

-- Refresh strategies
-- Full refresh (blocks reads during refresh)
REFRESH MATERIALIZED VIEW customer_stats;

-- Concurrent refresh (allows reads, requires unique index)
REFRESH MATERIALIZED VIEW CONCURRENTLY customer_stats;

-- Automated refresh with pg_cron
-- SELECT cron.schedule('refresh_customer_stats', '0 * * * *',
--   'REFRESH MATERIALIZED VIEW CONCURRENTLY customer_stats');
```

### 4. JSON Aggregation

```sql
-- Store related data as JSON for single-table queries
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  customer_id UUID REFERENCES customers(id),
  status VARCHAR(20),
  total DECIMAL(12, 2),
  -- Embedded items as JSON
  items_json JSONB,
  -- Embedded shipping info
  shipping_json JSONB,
  created_at TIMESTAMPTZ
);

-- Populate items_json on order creation
CREATE OR REPLACE FUNCTION populate_order_items_json()
RETURNS TRIGGER AS $$
BEGIN
  NEW.items_json = (
    SELECT jsonb_agg(jsonb_build_object(
      'product_id', oi.product_id,
      'product_name', p.name,
      'quantity', oi.quantity,
      'unit_price', oi.unit_price,
      'subtotal', oi.quantity * oi.unit_price
    ))
    FROM order_items oi
    JOIN products p ON oi.product_id = p.id
    WHERE oi.order_id = NEW.id
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Single query returns complete order
SELECT
  id,
  status,
  total,
  items_json,
  shipping_json
FROM orders
WHERE id = 'order-uuid';
```

### 5. Hierarchical Denormalization

```sql
-- Normalized category tree (requires recursive queries)
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES categories(id),
  name VARCHAR(100)
);

-- Denormalized with materialized path
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES categories(id),
  name VARCHAR(100),
  -- Denormalized fields
  full_path TEXT,           -- '/Electronics/Computers/Laptops'
  path_ids UUID[],          -- Array of ancestor IDs
  depth INTEGER,
  root_id UUID              -- Top-level category
);

-- Fast queries without recursion
-- Get all ancestors
SELECT * FROM categories
WHERE id = ANY(
  SELECT unnest(path_ids) FROM categories WHERE id = 'category-uuid'
);

-- Get all descendants
SELECT * FROM categories
WHERE full_path LIKE (
  SELECT full_path FROM categories WHERE id = 'parent-uuid'
) || '/%';

-- Maintain with trigger
CREATE OR REPLACE FUNCTION update_category_hierarchy()
RETURNS TRIGGER AS $$
DECLARE
  parent_record categories%ROWTYPE;
BEGIN
  IF NEW.parent_id IS NULL THEN
    NEW.full_path = '/' || NEW.name;
    NEW.path_ids = ARRAY[NEW.id];
    NEW.depth = 0;
    NEW.root_id = NEW.id;
  ELSE
    SELECT * INTO parent_record FROM categories WHERE id = NEW.parent_id;
    NEW.full_path = parent_record.full_path || '/' || NEW.name;
    NEW.path_ids = parent_record.path_ids || NEW.id;
    NEW.depth = parent_record.depth + 1;
    NEW.root_id = parent_record.root_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 6. Counter Caches

```sql
-- Add counter to parent table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  -- Counter caches
  posts_count INTEGER DEFAULT 0,
  followers_count INTEGER DEFAULT 0,
  following_count INTEGER DEFAULT 0
);

-- Maintain counters
CREATE OR REPLACE FUNCTION update_user_posts_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE users SET posts_count = posts_count + 1
    WHERE id = NEW.user_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE users SET posts_count = posts_count - 1
    WHERE id = OLD.user_id;
  ELSIF TG_OP = 'UPDATE' AND NEW.user_id != OLD.user_id THEN
    UPDATE users SET posts_count = posts_count - 1 WHERE id = OLD.user_id;
    UPDATE users SET posts_count = posts_count + 1 WHERE id = NEW.user_id;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER posts_count_trigger
  AFTER INSERT OR UPDATE OR DELETE ON posts
  FOR EACH ROW
  EXECUTE FUNCTION update_user_posts_count();
```

## Consistency Maintenance

### Trigger-Based Sync

```sql
-- Generic sync function template
CREATE OR REPLACE FUNCTION sync_denormalized_data()
RETURNS TRIGGER AS $$
BEGIN
  -- Update denormalized data based on operation
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Deferred triggers (execute at transaction end)
CREATE CONSTRAINT TRIGGER sync_after_commit
  AFTER INSERT OR UPDATE ON source_table
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW
  EXECUTE FUNCTION sync_denormalized_data();
```

### Batch Updates

```sql
-- For heavy denormalization, use batch updates
CREATE OR REPLACE PROCEDURE refresh_product_stats()
LANGUAGE plpgsql AS $$
BEGIN
  -- Update all products in batches
  WITH stats AS (
    SELECT
      product_id,
      COUNT(*) as review_count,
      COALESCE(AVG(rating), 0) as avg_rating
    FROM reviews
    GROUP BY product_id
  )
  UPDATE products p SET
    review_count = COALESCE(s.review_count, 0),
    avg_rating = COALESCE(s.avg_rating, 0)
  FROM stats s
  WHERE p.id = s.product_id;

  -- Reset products with no reviews
  UPDATE products SET
    review_count = 0,
    avg_rating = 0
  WHERE id NOT IN (SELECT DISTINCT product_id FROM reviews);

  COMMIT;
END;
$$;

-- Schedule batch refresh
-- CALL refresh_product_stats(); -- Run periodically
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Denormalization Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Start normalized, denormalize only when needed              │
│                                                                  │
│  2. Measure before and after                                    │
│     - Query performance (EXPLAIN ANALYZE)                       │
│     - Write overhead                                            │
│     - Storage impact                                            │
│                                                                  │
│  3. Document denormalization decisions                          │
│     - Why it was done                                           │
│     - How consistency is maintained                             │
│     - When to refresh                                           │
│                                                                  │
│  4. Use triggers for real-time consistency                      │
│                                                                  │
│  5. Use materialized views for complex aggregates               │
│                                                                  │
│  6. Consider application-level caching first                    │
│                                                                  │
│  7. Monitor for data drift                                      │
│     - Periodic verification jobs                                │
│     - Alerts on inconsistencies                                 │
│                                                                  │
│  8. Keep FK constraints where possible                          │
│     - Denormalize data, not relationships                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Trade-off Summary

| Strategy | Read Performance | Write Overhead | Storage | Consistency |
|----------|------------------|----------------|---------|-------------|
| Duplicated columns | Excellent | Medium | Higher | Trigger-based |
| Pre-computed aggregates | Excellent | Medium-High | Low | Trigger-based |
| Materialized views | Good | Low (batch) | Higher | Manual refresh |
| JSON aggregation | Good | Medium | Higher | Application |
| Counter caches | Excellent | Low | Minimal | Trigger-based |
