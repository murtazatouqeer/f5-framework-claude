---
name: sql-fundamentals
description: Core SQL operations and syntax
category: database/sql
applies_to: [postgresql, mysql, sql-server, sqlite]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# SQL Fundamentals

## Overview

SQL (Structured Query Language) is the standard language for
interacting with relational databases. This guide covers essential
operations every developer should know.

## Data Definition Language (DDL)

### CREATE TABLE

```sql
-- Basic table creation
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  age INT CHECK (age >= 0 AND age <= 150),
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- With foreign key
CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  total DECIMAL(10, 2) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- With composite primary key
CREATE TABLE order_items (
  order_id INT REFERENCES orders(id) ON DELETE CASCADE,
  product_id INT REFERENCES products(id),
  quantity INT NOT NULL CHECK (quantity > 0),
  price DECIMAL(10, 2) NOT NULL,
  PRIMARY KEY (order_id, product_id)
);
```

### ALTER TABLE

```sql
-- Add column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Drop column
ALTER TABLE users DROP COLUMN phone;

-- Rename column
ALTER TABLE users RENAME COLUMN name TO full_name;

-- Change column type
ALTER TABLE users ALTER COLUMN status TYPE VARCHAR(30);

-- Add constraint
ALTER TABLE users ADD CONSTRAINT email_format
  CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Drop constraint
ALTER TABLE users DROP CONSTRAINT email_format;

-- Add index
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status) WHERE status = 'active';

-- Add foreign key
ALTER TABLE orders ADD CONSTRAINT fk_orders_user
  FOREIGN KEY (user_id) REFERENCES users(id);
```

### DROP and TRUNCATE

```sql
-- Drop table (removes structure and data)
DROP TABLE IF EXISTS temp_data;
DROP TABLE users CASCADE;  -- Also drops dependent objects

-- Truncate (removes data, keeps structure)
TRUNCATE TABLE logs;
TRUNCATE TABLE orders RESTART IDENTITY CASCADE;
```

## Data Manipulation Language (DML)

### INSERT

```sql
-- Single row
INSERT INTO users (email, name)
VALUES ('john@example.com', 'John Doe');

-- Multiple rows
INSERT INTO users (email, name) VALUES
  ('alice@example.com', 'Alice Smith'),
  ('bob@example.com', 'Bob Jones'),
  ('carol@example.com', 'Carol White');

-- Insert from select
INSERT INTO archived_orders (id, user_id, total, created_at)
SELECT id, user_id, total, created_at
FROM orders
WHERE created_at < '2023-01-01';

-- Insert with returning (PostgreSQL)
INSERT INTO users (email, name)
VALUES ('new@example.com', 'New User')
RETURNING id, created_at;

-- Upsert (PostgreSQL)
INSERT INTO products (sku, name, price)
VALUES ('SKU001', 'Widget', 29.99)
ON CONFLICT (sku) DO UPDATE SET
  name = EXCLUDED.name,
  price = EXCLUDED.price;

-- Upsert (MySQL)
INSERT INTO products (sku, name, price)
VALUES ('SKU001', 'Widget', 29.99)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  price = VALUES(price);
```

### SELECT

```sql
-- Basic select
SELECT * FROM users;
SELECT id, email, name FROM users;

-- With alias
SELECT
  u.id,
  u.name AS user_name,
  u.email
FROM users u;

-- With conditions
SELECT * FROM users
WHERE status = 'active'
  AND created_at > '2024-01-01';

-- Pattern matching
SELECT * FROM users WHERE email LIKE '%@gmail.com';
SELECT * FROM users WHERE name ILIKE '%john%';  -- Case insensitive

-- IN clause
SELECT * FROM orders WHERE status IN ('pending', 'processing');

-- BETWEEN
SELECT * FROM products WHERE price BETWEEN 10 AND 50;

-- NULL handling
SELECT * FROM users WHERE phone IS NULL;
SELECT * FROM users WHERE phone IS NOT NULL;

-- Ordering
SELECT * FROM users ORDER BY created_at DESC;
SELECT * FROM users ORDER BY status ASC, name ASC;

-- Limiting
SELECT * FROM users LIMIT 10;
SELECT * FROM users LIMIT 10 OFFSET 20;  -- Pagination

-- Distinct
SELECT DISTINCT status FROM orders;
SELECT DISTINCT ON (user_id) * FROM orders ORDER BY user_id, created_at DESC;
```

### UPDATE

```sql
-- Basic update
UPDATE users SET status = 'inactive' WHERE id = 1;

-- Multiple columns
UPDATE users SET
  name = 'John Smith',
  email = 'john.smith@example.com',
  updated_at = NOW()
WHERE id = 1;

-- Update with subquery
UPDATE products SET
  category_id = (SELECT id FROM categories WHERE name = 'Electronics')
WHERE name LIKE '%Phone%';

-- Update with join (PostgreSQL)
UPDATE orders o SET
  status = 'vip'
FROM users u
WHERE o.user_id = u.id
  AND u.total_spent > 10000;

-- Update with returning
UPDATE users SET status = 'inactive'
WHERE last_login < NOW() - INTERVAL '1 year'
RETURNING id, email;

-- Conditional update
UPDATE products SET
  price = CASE
    WHEN category = 'electronics' THEN price * 0.9
    WHEN category = 'clothing' THEN price * 0.8
    ELSE price
  END
WHERE on_sale = true;
```

### DELETE

```sql
-- Basic delete
DELETE FROM users WHERE id = 1;

-- Delete with condition
DELETE FROM sessions WHERE expires_at < NOW();

-- Delete with subquery
DELETE FROM orders
WHERE user_id IN (
  SELECT id FROM users WHERE status = 'deleted'
);

-- Delete with returning
DELETE FROM temp_data
WHERE created_at < NOW() - INTERVAL '7 days'
RETURNING *;

-- Delete all (prefer TRUNCATE for large tables)
DELETE FROM logs;
```

## Aggregation

### Basic Aggregates

```sql
-- Count
SELECT COUNT(*) FROM users;
SELECT COUNT(DISTINCT status) FROM orders;
SELECT COUNT(*) FILTER (WHERE status = 'active') FROM users;

-- Sum, Avg, Min, Max
SELECT
  SUM(total) as total_revenue,
  AVG(total) as avg_order,
  MIN(total) as min_order,
  MAX(total) as max_order
FROM orders
WHERE status = 'completed';

-- String aggregation
SELECT
  user_id,
  STRING_AGG(product_name, ', ') as products
FROM order_items
GROUP BY user_id;

-- Array aggregation (PostgreSQL)
SELECT
  user_id,
  ARRAY_AGG(DISTINCT tag ORDER BY tag) as tags
FROM user_tags
GROUP BY user_id;
```

### GROUP BY

```sql
-- Basic grouping
SELECT status, COUNT(*) as count
FROM orders
GROUP BY status;

-- Multiple columns
SELECT
  DATE_TRUNC('month', created_at) as month,
  status,
  COUNT(*) as count,
  SUM(total) as revenue
FROM orders
GROUP BY DATE_TRUNC('month', created_at), status
ORDER BY month, status;

-- With HAVING (filter after grouping)
SELECT
  user_id,
  COUNT(*) as order_count,
  SUM(total) as total_spent
FROM orders
GROUP BY user_id
HAVING COUNT(*) >= 5 AND SUM(total) > 1000;

-- ROLLUP (subtotals)
SELECT
  COALESCE(category, 'TOTAL') as category,
  COALESCE(subcategory, 'Subtotal') as subcategory,
  SUM(sales) as total_sales
FROM products
GROUP BY ROLLUP (category, subcategory);

-- CUBE (all combinations)
SELECT
  region,
  product,
  SUM(sales)
FROM sales
GROUP BY CUBE (region, product);
```

## Joins

```sql
-- INNER JOIN (matching rows only)
SELECT u.name, o.id, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- LEFT JOIN (all from left, matching from right)
SELECT u.name, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
GROUP BY u.id, u.name;

-- RIGHT JOIN (all from right, matching from left)
SELECT o.id, u.name
FROM orders o
RIGHT JOIN users u ON o.user_id = u.id;

-- FULL OUTER JOIN (all from both)
SELECT
  COALESCE(a.date, b.date) as date,
  a.online_sales,
  b.store_sales
FROM online_sales a
FULL OUTER JOIN store_sales b ON a.date = b.date;

-- CROSS JOIN (cartesian product)
SELECT p.name, c.name as color
FROM products p
CROSS JOIN colors c;

-- Self join
SELECT
  e.name as employee,
  m.name as manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;

-- Multiple joins
SELECT
  o.id as order_id,
  u.name as customer,
  p.name as product,
  oi.quantity
FROM orders o
JOIN users u ON o.user_id = u.id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id;
```

## Subqueries

```sql
-- Scalar subquery (returns single value)
SELECT
  name,
  price,
  price - (SELECT AVG(price) FROM products) as diff_from_avg
FROM products;

-- IN subquery
SELECT * FROM users
WHERE id IN (
  SELECT DISTINCT user_id FROM orders
  WHERE total > 1000
);

-- EXISTS subquery
SELECT * FROM users u
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.user_id = u.id
    AND o.status = 'completed'
);

-- NOT EXISTS
SELECT * FROM products p
WHERE NOT EXISTS (
  SELECT 1 FROM order_items oi
  WHERE oi.product_id = p.id
);

-- Correlated subquery
SELECT
  u.name,
  (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.id) as order_count
FROM users u;

-- Derived table (subquery in FROM)
SELECT
  top_customers.name,
  top_customers.total_spent
FROM (
  SELECT
    u.id,
    u.name,
    SUM(o.total) as total_spent
  FROM users u
  JOIN orders o ON u.id = o.user_id
  GROUP BY u.id, u.name
  HAVING SUM(o.total) > 5000
) top_customers
ORDER BY top_customers.total_spent DESC;
```

## Common Functions

### String Functions

```sql
-- Concatenation
SELECT first_name || ' ' || last_name AS full_name FROM users;
SELECT CONCAT(first_name, ' ', last_name) AS full_name FROM users;

-- Case conversion
SELECT UPPER(name), LOWER(email) FROM users;
SELECT INITCAP(name) FROM users;  -- Title Case

-- Substring
SELECT SUBSTRING(phone FROM 1 FOR 3) AS area_code FROM users;
SELECT LEFT(name, 1) AS initial FROM users;

-- Trim
SELECT TRIM(BOTH ' ' FROM name) FROM users;
SELECT LTRIM(RTRIM(name)) FROM users;

-- Replace
SELECT REPLACE(phone, '-', '') FROM users;

-- Length
SELECT name, LENGTH(name) AS name_length FROM users;

-- Position
SELECT POSITION('@' IN email) FROM users;
```

### Date/Time Functions

```sql
-- Current date/time
SELECT NOW(), CURRENT_DATE, CURRENT_TIME, CURRENT_TIMESTAMP;

-- Extract parts
SELECT
  EXTRACT(YEAR FROM created_at) AS year,
  EXTRACT(MONTH FROM created_at) AS month,
  EXTRACT(DAY FROM created_at) AS day,
  EXTRACT(DOW FROM created_at) AS day_of_week
FROM orders;

-- Date truncation
SELECT DATE_TRUNC('month', created_at) AS month FROM orders;
SELECT DATE_TRUNC('week', created_at) AS week FROM orders;

-- Date arithmetic
SELECT created_at + INTERVAL '30 days' AS expires_at FROM tokens;
SELECT NOW() - INTERVAL '1 year' AS one_year_ago;
SELECT AGE(NOW(), created_at) AS account_age FROM users;

-- Formatting
SELECT TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI:SS') FROM orders;
SELECT TO_CHAR(created_at, 'Mon DD, YYYY') FROM orders;
```

### Conditional Functions

```sql
-- CASE expression
SELECT
  name,
  price,
  CASE
    WHEN price < 10 THEN 'budget'
    WHEN price < 50 THEN 'standard'
    WHEN price < 100 THEN 'premium'
    ELSE 'luxury'
  END AS tier
FROM products;

-- Simple CASE
SELECT
  status,
  CASE status
    WHEN 'pending' THEN 'Awaiting Processing'
    WHEN 'shipped' THEN 'On The Way'
    WHEN 'delivered' THEN 'Complete'
    ELSE 'Unknown'
  END AS status_text
FROM orders;

-- COALESCE (first non-null)
SELECT COALESCE(nickname, name, email) AS display_name FROM users;

-- NULLIF (returns null if equal)
SELECT NULLIF(discount, 0) FROM products;  -- Avoid division by zero

-- GREATEST / LEAST
SELECT GREATEST(price, min_price, 0) AS final_price FROM products;
SELECT LEAST(stock, max_order_qty) AS available FROM products;
```

### Type Casting

```sql
-- CAST
SELECT CAST(price AS INTEGER) FROM products;
SELECT CAST('2024-01-15' AS DATE);

-- PostgreSQL shorthand
SELECT price::INTEGER FROM products;
SELECT '2024-01-15'::DATE;

-- Converting to string
SELECT CAST(id AS VARCHAR) FROM users;
SELECT id::TEXT FROM users;
```

## Best Practices

```sql
-- 1. Use explicit column names (not SELECT *)
-- BAD
SELECT * FROM users;
-- GOOD
SELECT id, email, name, status FROM users;

-- 2. Use table aliases consistently
-- GOOD
SELECT u.name, o.total
FROM users u
JOIN orders o ON u.id = o.user_id;

-- 3. Use meaningful aliases
-- BAD
SELECT a.x, b.y FROM table1 a JOIN table2 b ON a.id = b.fk;
-- GOOD
SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id;

-- 4. Format for readability
SELECT
  u.id,
  u.name,
  COUNT(o.id) AS order_count,
  SUM(o.total) AS total_spent
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.status = 'active'
GROUP BY u.id, u.name
HAVING COUNT(o.id) > 0
ORDER BY total_spent DESC
LIMIT 10;

-- 5. Use parameterized queries (prevent SQL injection)
-- Application code, not raw SQL with user input
```
