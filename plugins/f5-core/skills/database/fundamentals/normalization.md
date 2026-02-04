---
name: normalization
description: Database normalization forms and denormalization strategies
category: database/fundamentals
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Database Normalization

## Overview

Normalization is the process of organizing data to reduce redundancy
and improve data integrity. It involves dividing tables and defining
relationships between them.

## Why Normalize?

### Problems Without Normalization

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Unnormalized Orders Table                             │
├──────────┬───────────┬─────────────┬──────────────┬─────────────────────┤
│ order_id │ customer  │ cust_email  │ product      │ product_price       │
├──────────┼───────────┼─────────────┼──────────────┼─────────────────────┤
│ 1        │ John Doe  │ john@ex.com │ Widget A     │ 29.99               │
│ 2        │ John Doe  │ john@ex.com │ Widget B     │ 49.99               │
│ 3        │ Jane Doe  │ jane@ex.com │ Widget A     │ 29.99               │
│ 4        │ John Doe  │ john@ex.com │ Widget C     │ 19.99               │
└──────────┴───────────┴─────────────┴──────────────┴─────────────────────┘

Problems:
1. UPDATE ANOMALY: Change John's email → must update multiple rows
2. INSERT ANOMALY: Can't add new product without an order
3. DELETE ANOMALY: Delete order #3 → lose Jane's info entirely
4. REDUNDANCY: John's info repeated 3 times, Widget A price twice
```

## Normal Forms

### First Normal Form (1NF)

**Rule**: Each column contains atomic (indivisible) values, no repeating groups.

```
❌ VIOLATES 1NF (multi-valued column)
┌──────────┬───────────┬──────────────────────────┐
│ order_id │ customer  │ products                 │
├──────────┼───────────┼──────────────────────────┤
│ 1        │ John Doe  │ Widget A, Widget B       │  ← Multiple values
│ 2        │ Jane Doe  │ Widget C                 │
└──────────┴───────────┴──────────────────────────┘

❌ VIOLATES 1NF (repeating groups)
┌──────────┬───────────┬───────────┬───────────┬───────────┐
│ order_id │ customer  │ product1  │ product2  │ product3  │
├──────────┼───────────┼───────────┼───────────┼───────────┤
│ 1        │ John Doe  │ Widget A  │ Widget B  │ NULL      │
│ 2        │ Jane Doe  │ Widget C  │ NULL      │ NULL      │
└──────────┴───────────┴───────────┴───────────┴───────────┘

✅ IN 1NF
┌──────────┬───────────┬───────────┐
│ order_id │ customer  │ product   │
├──────────┼───────────┼───────────┤
│ 1        │ John Doe  │ Widget A  │
│ 1        │ John Doe  │ Widget B  │
│ 2        │ Jane Doe  │ Widget C  │
└──────────┴───────────┴───────────┘
```

### Second Normal Form (2NF)

**Rule**: 1NF + No partial dependencies (non-key attributes depend on the ENTIRE primary key).

```
❌ VIOLATES 2NF (partial dependency on composite key)

Primary Key: (order_id, product_id)

┌──────────┬────────────┬───────────────┬───────────────┐
│ order_id │ product_id │ product_name  │ quantity      │
├──────────┼────────────┼───────────────┼───────────────┤
│ 1        │ P001       │ Widget A      │ 2             │
│ 1        │ P002       │ Widget B      │ 1             │
│ 2        │ P001       │ Widget A      │ 3             │
└──────────┴────────────┴───────────────┴───────────────┘
                              ↑
                   product_name depends only on product_id
                   NOT on (order_id, product_id)

✅ IN 2NF (split tables)

Products Table:
┌────────────┬───────────────┬───────────┐
│ product_id │ product_name  │ price     │
├────────────┼───────────────┼───────────┤
│ P001       │ Widget A      │ 29.99     │
│ P002       │ Widget B      │ 49.99     │
└────────────┴───────────────┴───────────┘

Order_Items Table:
┌──────────┬────────────┬──────────┐
│ order_id │ product_id │ quantity │
├──────────┼────────────┼──────────┤
│ 1        │ P001       │ 2        │
│ 1        │ P002       │ 1        │
│ 2        │ P001       │ 3        │
└──────────┴────────────┴──────────┘
```

### Third Normal Form (3NF)

**Rule**: 2NF + No transitive dependencies (non-key attributes don't depend on other non-key attributes).

```
❌ VIOLATES 3NF (transitive dependency)

┌──────────┬───────────────┬─────────────┬──────────────┐
│ order_id │ customer_id   │ cust_name   │ cust_city    │
├──────────┼───────────────┼─────────────┼──────────────┤
│ 1        │ C001          │ John Doe    │ New York     │
│ 2        │ C001          │ John Doe    │ New York     │
│ 3        │ C002          │ Jane Doe    │ Boston       │
└──────────┴───────────────┴─────────────┴──────────────┘
                                  ↑            ↑
                           cust_name and cust_city depend on
                           customer_id, not on order_id

✅ IN 3NF (separate customer table)

Customers Table:
┌─────────────┬───────────┬──────────┐
│ customer_id │ name      │ city     │
├─────────────┼───────────┼──────────┤
│ C001        │ John Doe  │ New York │
│ C002        │ Jane Doe  │ Boston   │
└─────────────┴───────────┴──────────┘

Orders Table:
┌──────────┬─────────────┬────────────┐
│ order_id │ customer_id │ order_date │
├──────────┼─────────────┼────────────┤
│ 1        │ C001        │ 2024-01-15 │
│ 2        │ C001        │ 2024-01-16 │
│ 3        │ C002        │ 2024-01-17 │
└──────────┴─────────────┴────────────┘
```

### Boyce-Codd Normal Form (BCNF)

**Rule**: 3NF + Every determinant is a candidate key.

```
❌ VIOLATES BCNF

Table: Student_Courses
┌────────────┬──────────────┬─────────────┐
│ student_id │ course       │ instructor  │
├────────────┼──────────────┼─────────────┤
│ S001       │ Database     │ Prof. Smith │
│ S002       │ Database     │ Prof. Smith │
│ S001       │ Networks     │ Prof. Jones │
│ S003       │ Database     │ Prof. Brown │  ← Different instructor!
└────────────┴──────────────┴─────────────┘

Problem: instructor → course (each instructor teaches one course)
But instructor is not a candidate key

✅ IN BCNF (separate instructor assignment)

Courses Table:
┌────────────┬─────────────┐
│ course     │ course_id   │
├────────────┼─────────────┤
│ Database   │ C001        │
│ Networks   │ C002        │
└────────────┴─────────────┘

Instructors Table:
┌───────────────┬───────────┐
│ instructor_id │ name      │
├───────────────┼───────────┤
│ I001          │ Prof. Smith│
│ I002          │ Prof. Jones│
│ I003          │ Prof. Brown│
└───────────────┴───────────┘

Course_Sections Table:
┌────────────┬───────────┬───────────────┐
│ section_id │ course_id │ instructor_id │
├────────────┼───────────┼───────────────┤
│ SEC001     │ C001      │ I001          │
│ SEC002     │ C001      │ I003          │
│ SEC003     │ C002      │ I002          │
└────────────┴───────────┴───────────────┘

Enrollments Table:
┌────────────┬────────────┐
│ student_id │ section_id │
├────────────┼────────────┤
│ S001       │ SEC001     │
│ S002       │ SEC001     │
│ S001       │ SEC003     │
│ S003       │ SEC002     │
└────────────┴────────────┘
```

## Normal Forms Summary

| Form | Rule | Eliminates |
|------|------|------------|
| 1NF | Atomic values, no repeating groups | Multi-valued attributes |
| 2NF | 1NF + no partial dependencies | Partial key dependencies |
| 3NF | 2NF + no transitive dependencies | Non-key dependencies |
| BCNF | Every determinant is candidate key | Remaining anomalies |

## Practical Normalized Schema

```sql
-- BCNF-compliant e-commerce schema

-- Customers
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Addresses (separate from customers, 3NF)
CREATE TABLE addresses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL CHECK (type IN ('billing', 'shipping')),
  street VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100),
  postal_code VARCHAR(20),
  country VARCHAR(2) NOT NULL,
  is_default BOOLEAN DEFAULT false,
  UNIQUE (customer_id, type, is_default) -- Only one default per type
);

-- Categories (self-referencing for hierarchy)
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_id UUID REFERENCES categories(id),
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(100) UNIQUE NOT NULL
);

-- Products
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id UUID REFERENCES categories(id),
  sku VARCHAR(50) UNIQUE NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price DECIMAL(10, 2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Product attributes (EAV pattern for flexibility)
CREATE TABLE product_attributes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  attribute_name VARCHAR(50) NOT NULL,
  attribute_value VARCHAR(255) NOT NULL,
  UNIQUE (product_id, attribute_name)
);

-- Orders
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id),
  billing_address_id UUID REFERENCES addresses(id),
  shipping_address_id UUID REFERENCES addresses(id),
  status VARCHAR(20) DEFAULT 'pending',
  subtotal DECIMAL(12, 2) NOT NULL,
  tax DECIMAL(12, 2) NOT NULL DEFAULT 0,
  total DECIMAL(12, 2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Order items (junction table, 2NF compliant)
CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id),
  quantity INT NOT NULL CHECK (quantity > 0),
  unit_price DECIMAL(10, 2) NOT NULL,  -- Snapshot of price at order time
  subtotal DECIMAL(12, 2) NOT NULL,
  UNIQUE (order_id, product_id)
);

-- Payments (separate from orders)
CREATE TABLE payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id),
  method VARCHAR(20) NOT NULL,
  amount DECIMAL(12, 2) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  transaction_id VARCHAR(255),
  processed_at TIMESTAMPTZ
);
```

## When to Denormalize

Normalization optimizes for writes and data integrity.
Denormalization optimizes for reads at the cost of redundancy.

### Denormalization Scenarios

```
┌─────────────────────────────────────────────────────────────┐
│              When to Consider Denormalization                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✓ Read-heavy workloads (90%+ reads)                        │
│  ✓ Complex queries with many joins are slow                 │
│  ✓ Reporting/analytics dashboards                           │
│  ✓ Caching layer data                                       │
│  ✓ Search indexes                                           │
│                                                              │
│  ✗ Write-heavy workloads (high update frequency)            │
│  ✗ Data integrity is critical                               │
│  ✗ Storage cost is a concern                                │
│  ✗ Simple queries with few joins                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Denormalization Strategies

#### 1. Duplicated Columns

```sql
-- Normalized: Need join to get customer name
SELECT o.id, o.total, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;

-- Denormalized: Customer name stored in order
ALTER TABLE orders ADD COLUMN customer_name VARCHAR(100);

-- Faster query, no join needed
SELECT id, total, customer_name FROM orders;

-- But need to update on customer name change
UPDATE orders SET customer_name = 'New Name'
WHERE customer_id = 'customer-uuid';
```

#### 2. Computed/Cached Columns

```sql
-- Instead of calculating order total every time
ALTER TABLE orders ADD COLUMN item_count INT DEFAULT 0;

-- Update via trigger
CREATE OR REPLACE FUNCTION update_order_item_count()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    UPDATE orders SET item_count = item_count + NEW.quantity
    WHERE id = NEW.order_id;
  ELSIF TG_OP = 'DELETE' THEN
    UPDATE orders SET item_count = item_count - OLD.quantity
    WHERE id = OLD.order_id;
  ELSIF TG_OP = 'UPDATE' THEN
    UPDATE orders SET item_count = item_count - OLD.quantity + NEW.quantity
    WHERE id = NEW.order_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_items_count_trigger
AFTER INSERT OR UPDATE OR DELETE ON order_items
FOR EACH ROW EXECUTE FUNCTION update_order_item_count();
```

#### 3. Materialized Views

```sql
-- Create materialized view for reporting
CREATE MATERIALIZED VIEW customer_stats AS
SELECT
  c.id as customer_id,
  c.name,
  c.email,
  COUNT(DISTINCT o.id) as order_count,
  COALESCE(SUM(o.total), 0) as total_spent,
  MAX(o.created_at) as last_order_date
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id AND o.status = 'completed'
GROUP BY c.id, c.name, c.email;

-- Create index on materialized view
CREATE INDEX idx_customer_stats_total ON customer_stats(total_spent DESC);

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY customer_stats;

-- Fast query
SELECT * FROM customer_stats
WHERE total_spent > 1000
ORDER BY total_spent DESC;
```

#### 4. JSON Aggregation

```sql
-- Store related data as JSON
ALTER TABLE orders ADD COLUMN items_json JSONB;

-- Populate on order creation
UPDATE orders o SET items_json = (
  SELECT jsonb_agg(jsonb_build_object(
    'product_id', oi.product_id,
    'name', p.name,
    'quantity', oi.quantity,
    'price', oi.unit_price
  ))
  FROM order_items oi
  JOIN products p ON oi.product_id = p.id
  WHERE oi.order_id = o.id
);

-- Fast single-table query with all order details
SELECT id, customer_id, total, items_json
FROM orders
WHERE id = 'order-uuid';
```

## Normalization Decision Guide

```
┌─────────────────────────────────────────────────────────────┐
│            Should I Normalize Further?                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Start with 3NF (good default for most applications)        │
│                                                              │
│  Consider BCNF if:                                           │
│  • Complex business rules around data                        │
│  • Data integrity is paramount                               │
│  • Storage is cheap, queries are simple                      │
│                                                              │
│  Consider denormalizing if:                                  │
│  • Queries consistently slow despite indexes                 │
│  • Read:Write ratio is 10:1 or higher                       │
│  • Joins span 4+ tables regularly                           │
│  • Analytics/reporting requirements                          │
│                                                              │
│  Best Practice:                                              │
│  • Normalize for transactions (OLTP)                        │
│  • Denormalize for analytics (OLAP)                         │
│  • Use materialized views as middle ground                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Anti-Patterns to Avoid

### 1. Over-normalization

```sql
-- Too many small tables
-- BAD: Separate table for every attribute
CREATE TABLE user_names (user_id UUID, name VARCHAR);
CREATE TABLE user_emails (user_id UUID, email VARCHAR);
CREATE TABLE user_phones (user_id UUID, phone VARCHAR);

-- GOOD: Single users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(255),
  phone VARCHAR(20)
);
```

### 2. EAV Abuse

```sql
-- Entity-Attribute-Value: Flexible but query nightmare
-- Use sparingly, not for core attributes

-- BAD: Everything in EAV
SELECT
  e.entity_id,
  MAX(CASE WHEN a.name = 'name' THEN v.value END) as name,
  MAX(CASE WHEN a.name = 'email' THEN v.value END) as email,
  MAX(CASE WHEN a.name = 'status' THEN v.value END) as status
FROM entities e
JOIN values v ON e.id = v.entity_id
JOIN attributes a ON v.attribute_id = a.id
GROUP BY e.entity_id;

-- GOOD: EAV only for truly dynamic attributes
-- Core fields in proper columns, extras in JSONB or EAV
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,  -- Core field
  price DECIMAL NOT NULL,      -- Core field
  attributes JSONB             -- Dynamic attributes
);
```

### 3. Ignoring Natural Keys

```sql
-- Sometimes natural keys make sense

-- Country codes (ISO 3166-1)
CREATE TABLE countries (
  code VARCHAR(2) PRIMARY KEY,  -- Natural key: 'US', 'JP', etc.
  name VARCHAR(100) NOT NULL
);

-- Currency codes (ISO 4217)
CREATE TABLE currencies (
  code VARCHAR(3) PRIMARY KEY,  -- Natural key: 'USD', 'EUR', etc.
  name VARCHAR(100) NOT NULL,
  symbol VARCHAR(5)
);

-- Use natural key as foreign key
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  currency_code VARCHAR(3) REFERENCES currencies(code),
  -- No join needed to display 'USD', already readable
  price DECIMAL(10, 2)
);
```
