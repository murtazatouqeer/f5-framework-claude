---
name: joins-explained
description: SQL joins explained with visual diagrams
category: database/sql
applies_to: [postgresql, mysql, sql-server, sqlite]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# SQL Joins Explained

## Overview

Joins combine rows from two or more tables based on related columns.
Understanding joins is fundamental to working with relational databases.

## Sample Data

```sql
-- Users table
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(50)
);

INSERT INTO users VALUES
  (1, 'Alice'),
  (2, 'Bob'),
  (3, 'Carol'),
  (4, 'David');

-- Orders table
CREATE TABLE orders (
  id INT PRIMARY KEY,
  user_id INT,
  total DECIMAL(10, 2)
);

INSERT INTO orders VALUES
  (101, 1, 50.00),   -- Alice's order
  (102, 1, 75.00),   -- Alice's order
  (103, 2, 100.00),  -- Bob's order
  (104, 5, 25.00);   -- Unknown user (user_id 5 doesn't exist)
```

```
Users Table          Orders Table
┌────┬───────┐      ┌─────┬─────────┬────────┐
│ id │ name  │      │ id  │ user_id │ total  │
├────┼───────┤      ├─────┼─────────┼────────┤
│ 1  │ Alice │      │ 101 │ 1       │ 50.00  │
│ 2  │ Bob   │      │ 102 │ 1       │ 75.00  │
│ 3  │ Carol │      │ 103 │ 2       │ 100.00 │
│ 4  │ David │      │ 104 │ 5       │ 25.00  │
└────┴───────┘      └─────┴─────────┴────────┘
```

## INNER JOIN

Returns only rows where there's a match in **both** tables.

```
┌─────────────────────────────────────────────────────┐
│                    INNER JOIN                        │
│                                                      │
│    ┌───────────┐         ┌───────────┐              │
│    │   Users   │         │  Orders   │              │
│    │           │         │           │              │
│    │     ┌─────┴─────────┴─────┐     │              │
│    │     │    Matching Rows    │     │              │
│    │     │    (Returned)       │     │              │
│    │     └─────┬─────────┬─────┘     │              │
│    │           │         │           │              │
│    └───────────┘         └───────────┘              │
│                                                      │
└─────────────────────────────────────────────────────┘
```

```sql
SELECT u.name, o.id AS order_id, o.total
FROM users u
INNER JOIN orders o ON u.id = o.user_id;

-- Result:
-- ┌───────┬──────────┬────────┐
-- │ name  │ order_id │ total  │
-- ├───────┼──────────┼────────┤
-- │ Alice │ 101      │ 50.00  │
-- │ Alice │ 102      │ 75.00  │
-- │ Bob   │ 103      │ 100.00 │
-- └───────┴──────────┴────────┘
--
-- Carol and David excluded (no orders)
-- Order 104 excluded (user_id 5 doesn't exist)
```

### When to Use INNER JOIN
- You only want rows that have related data in both tables
- Finding customers who have placed orders
- Getting products with their categories (where category is required)

## LEFT JOIN (LEFT OUTER JOIN)

Returns **all rows from left table**, plus matching rows from right table.
NULL for non-matching right side.

```
┌─────────────────────────────────────────────────────┐
│                    LEFT JOIN                         │
│                                                      │
│    ┌───────────────────┐   ┌───────────┐            │
│    │      Users        │   │  Orders   │            │
│    │  (All Returned)   │   │           │            │
│    │           ┌───────┴───┴───┐       │            │
│    │           │   Matching    │       │            │
│    │           └───────┬───┬───┘       │            │
│    │                   │   │           │            │
│    └───────────────────┘   └───────────┘            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

```sql
SELECT u.name, o.id AS order_id, o.total
FROM users u
LEFT JOIN orders o ON u.id = o.user_id;

-- Result:
-- ┌───────┬──────────┬────────┐
-- │ name  │ order_id │ total  │
-- ├───────┼──────────┼────────┤
-- │ Alice │ 101      │ 50.00  │
-- │ Alice │ 102      │ 75.00  │
-- │ Bob   │ 103      │ 100.00 │
-- │ Carol │ NULL     │ NULL   │  ← No orders, still included
-- │ David │ NULL     │ NULL   │  ← No orders, still included
-- └───────┴──────────┴────────┘
```

### Finding Non-Matches with LEFT JOIN

```sql
-- Users without orders
SELECT u.name
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.id IS NULL;

-- Result:
-- ┌───────┐
-- │ name  │
-- ├───────┤
-- │ Carol │
-- │ David │
-- └───────┘
```

### When to Use LEFT JOIN
- You need all records from the primary table regardless of matches
- Getting all users and their orders (including users with no orders)
- Finding records without related data (WHERE right.id IS NULL)

## RIGHT JOIN (RIGHT OUTER JOIN)

Returns **all rows from right table**, plus matching rows from left table.
NULL for non-matching left side.

```
┌─────────────────────────────────────────────────────┐
│                    RIGHT JOIN                        │
│                                                      │
│    ┌───────────┐   ┌───────────────────┐            │
│    │   Users   │   │      Orders       │            │
│    │           │   │  (All Returned)   │            │
│    │       ┌───┴───┴───────┐           │            │
│    │       │   Matching    │           │            │
│    │       └───┬───┬───────┘           │            │
│    │           │   │                   │            │
│    └───────────┘   └───────────────────┘            │
│                                                      │
└─────────────────────────────────────────────────────┘
```

```sql
SELECT u.name, o.id AS order_id, o.total
FROM users u
RIGHT JOIN orders o ON u.id = o.user_id;

-- Result:
-- ┌───────┬──────────┬────────┐
-- │ name  │ order_id │ total  │
-- ├───────┼──────────┼────────┤
-- │ Alice │ 101      │ 50.00  │
-- │ Alice │ 102      │ 75.00  │
-- │ Bob   │ 103      │ 100.00 │
-- │ NULL  │ 104      │ 25.00  │  ← user_id 5 doesn't exist
-- └───────┴──────────┴────────┘
```

### When to Use RIGHT JOIN
- Rarely used; LEFT JOIN with tables swapped is more common
- Finding orphaned records (orders without valid users)
- When the "important" table is on the right

## FULL OUTER JOIN

Returns **all rows from both tables**, with NULL where there's no match.

```
┌─────────────────────────────────────────────────────┐
│                  FULL OUTER JOIN                     │
│                                                      │
│    ┌───────────────────────────────────────┐        │
│    │      Users           Orders           │        │
│    │  (All Returned)  (All Returned)       │        │
│    │           ┌──────────────┐            │        │
│    │           │   Matching   │            │        │
│    │           └──────────────┘            │        │
│    │                                       │        │
│    └───────────────────────────────────────┘        │
│                                                      │
└─────────────────────────────────────────────────────┘
```

```sql
SELECT u.name, o.id AS order_id, o.total
FROM users u
FULL OUTER JOIN orders o ON u.id = o.user_id;

-- Result:
-- ┌───────┬──────────┬────────┐
-- │ name  │ order_id │ total  │
-- ├───────┼──────────┼────────┤
-- │ Alice │ 101      │ 50.00  │
-- │ Alice │ 102      │ 75.00  │
-- │ Bob   │ 103      │ 100.00 │
-- │ Carol │ NULL     │ NULL   │  ← No orders
-- │ David │ NULL     │ NULL   │  ← No orders
-- │ NULL  │ 104      │ 25.00  │  ← No matching user
-- └───────┴──────────┴────────┘
```

### When to Use FULL OUTER JOIN
- Data reconciliation between two sources
- Finding all mismatches between tables
- Audit queries where you need complete picture

```sql
-- Find all mismatches
SELECT
  COALESCE(u.name, 'Unknown User') as user_name,
  o.id as order_id,
  CASE
    WHEN u.id IS NULL THEN 'Orphaned Order'
    WHEN o.id IS NULL THEN 'User Without Orders'
    ELSE 'Matched'
  END as status
FROM users u
FULL OUTER JOIN orders o ON u.id = o.user_id
WHERE u.id IS NULL OR o.id IS NULL;
```

## CROSS JOIN

Returns **Cartesian product** - every row from first table paired with every
row from second table.

```
┌─────────────────────────────────────────────────────┐
│                    CROSS JOIN                        │
│                                                      │
│    Users × Orders = All Combinations                 │
│                                                      │
│    User 1 ─┬─ Order 1                               │
│            ├─ Order 2                               │
│            ├─ Order 3                               │
│            └─ Order 4                               │
│    User 2 ─┬─ Order 1                               │
│            ├─ Order 2                               │
│            └─ ...                                   │
│    ...                                              │
│                                                      │
│    Result: 4 users × 4 orders = 16 rows             │
│                                                      │
└─────────────────────────────────────────────────────┘
```

```sql
-- Explicit CROSS JOIN
SELECT u.name, o.id AS order_id
FROM users u
CROSS JOIN orders o;

-- Implicit CROSS JOIN (comma syntax)
SELECT u.name, o.id AS order_id
FROM users u, orders o;

-- Result: 16 rows (4 users × 4 orders)
```

### When to Use CROSS JOIN
- Generate all combinations (sizes × colors)
- Create date ranges or calendars
- Matrix operations

```sql
-- All product-color combinations
SELECT p.name, c.color_name
FROM products p
CROSS JOIN colors c;

-- Generate calendar
WITH dates AS (
  SELECT generate_series('2024-01-01', '2024-12-31', INTERVAL '1 day')::DATE as date
),
hours AS (
  SELECT generate_series(0, 23) as hour
)
SELECT d.date, h.hour
FROM dates d
CROSS JOIN hours h;
```

## SELF JOIN

A table joined with itself. Useful for hierarchical or comparative data.

```sql
-- Employee-Manager relationship
CREATE TABLE employees (
  id INT PRIMARY KEY,
  name VARCHAR(50),
  manager_id INT REFERENCES employees(id)
);

INSERT INTO employees VALUES
  (1, 'CEO', NULL),
  (2, 'VP Sales', 1),
  (3, 'VP Tech', 1),
  (4, 'Sales Rep', 2),
  (5, 'Engineer', 3);

-- Get employees with their managers
SELECT
  e.name AS employee,
  m.name AS manager
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;

-- Result:
-- ┌───────────┬──────────┐
-- │ employee  │ manager  │
-- ├───────────┼──────────┤
-- │ CEO       │ NULL     │
-- │ VP Sales  │ CEO      │
-- │ VP Tech   │ CEO      │
-- │ Sales Rep │ VP Sales │
-- │ Engineer  │ VP Tech  │
-- └───────────┴──────────┘
```

### Self Join Use Cases

```sql
-- Find pairs with same value
SELECT
  a.id AS id1,
  b.id AS id2,
  a.email
FROM users a
JOIN users b ON a.email = b.email AND a.id < b.id;

-- Compare consecutive records
SELECT
  curr.date,
  curr.value,
  prev.value AS prev_value,
  curr.value - prev.value AS change
FROM metrics curr
LEFT JOIN metrics prev ON prev.id = curr.id - 1;
```

## Multiple Joins

```sql
-- Three-table join
SELECT
  u.name AS customer,
  p.name AS product,
  oi.quantity,
  o.order_date
FROM users u
JOIN orders o ON u.id = o.user_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE o.status = 'completed';

-- Mixed join types
SELECT
  c.name AS category,
  p.name AS product,
  COALESCE(SUM(oi.quantity), 0) AS total_sold
FROM categories c
LEFT JOIN products p ON c.id = p.category_id
LEFT JOIN order_items oi ON p.id = oi.product_id
GROUP BY c.id, c.name, p.id, p.name
ORDER BY c.name, total_sold DESC;
```

## Join Conditions

### Equality Join (Equi-Join)

```sql
-- Most common: ON a.column = b.column
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id;

-- USING clause (when column names match)
SELECT * FROM users
JOIN orders USING (user_id);  -- Both tables have user_id
```

### Non-Equality Joins

```sql
-- Range join
SELECT e.name, s.grade, s.min_salary, s.max_salary
FROM employees e
JOIN salary_grades s ON e.salary BETWEEN s.min_salary AND s.max_salary;

-- Comparison join
SELECT
  a.name AS product_a,
  b.name AS product_b,
  a.price AS price_a,
  b.price AS price_b
FROM products a
JOIN products b ON a.price < b.price AND a.category_id = b.category_id;

-- Pattern join
SELECT u.*, d.*
FROM users u
JOIN domains d ON u.email LIKE '%@' || d.domain;
```

### Multiple Conditions

```sql
-- AND conditions
SELECT *
FROM orders o
JOIN order_items oi ON o.id = oi.order_id
                   AND oi.status = 'active';

-- Complex conditions
SELECT *
FROM products p
JOIN inventory i ON p.id = i.product_id
                AND i.warehouse_id = 1
                AND i.quantity > 0;
```

## Join Performance

### Index Recommendations

```sql
-- Create indexes on join columns
CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);

-- Composite index for multiple join conditions
CREATE INDEX idx_inventory_product_warehouse
ON inventory(product_id, warehouse_id);
```

### Join Order

```sql
-- Optimizer usually finds best order, but for complex queries:
-- Start with most restrictive table

-- Less efficient (if users is much larger than orders)
SELECT * FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.status = 'pending';

-- More efficient (filter early)
SELECT * FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.status = 'pending';
```

## Visual Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                       JOIN Types Summary                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  INNER JOIN       LEFT JOIN        RIGHT JOIN      FULL OUTER   │
│  ┌───┬───┐       ┌───┬───┐        ┌───┬───┐       ┌───┬───┐    │
│  │   │███│       │███│███│        │███│███│       │███│███│    │
│  │   │███│       │███│███│        │███│███│       │███│███│    │
│  └───┴───┘       └───┴───┘        └───┴───┘       └───┴───┘    │
│  Match only      All left +       All right +     All both +   │
│                  matches          matches         matches       │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CROSS JOIN      SELF JOIN                                       │
│  A × B           ┌───┐                                          │
│  All combos      │ A │──┐                                       │
│                  └───┘  │ A joins A                             │
│                    ▲────┘                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
