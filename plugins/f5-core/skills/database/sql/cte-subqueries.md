---
name: cte-subqueries
description: Common Table Expressions and subquery patterns
category: database/sql
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CTEs and Subqueries

## Overview

Common Table Expressions (CTEs) and subqueries are powerful tools for
writing complex queries in a readable, maintainable way.

## Subquery Types

### Scalar Subqueries

Returns a single value. Can be used anywhere a value is expected.

```sql
-- In SELECT
SELECT
  name,
  salary,
  salary - (SELECT AVG(salary) FROM employees) as diff_from_avg
FROM employees;

-- In WHERE
SELECT * FROM employees
WHERE salary > (SELECT AVG(salary) FROM employees);

-- In UPDATE
UPDATE products
SET price = price * (
  SELECT rate FROM exchange_rates WHERE currency = 'EUR'
);
```

### Column Subqueries

Returns a single column of values. Used with IN, ANY, ALL.

```sql
-- IN subquery
SELECT * FROM users
WHERE id IN (
  SELECT DISTINCT user_id
  FROM orders
  WHERE total > 1000
);

-- NOT IN (careful with NULLs!)
SELECT * FROM products
WHERE id NOT IN (
  SELECT product_id
  FROM order_items
  WHERE product_id IS NOT NULL  -- Important!
);

-- ANY / SOME
SELECT * FROM employees
WHERE salary > ANY (
  SELECT salary FROM employees WHERE department = 'Sales'
);

-- ALL
SELECT * FROM employees
WHERE salary > ALL (
  SELECT salary FROM employees WHERE department = 'Marketing'
);
```

### Row Subqueries

Returns a single row with multiple columns.

```sql
-- Compare multiple columns
SELECT * FROM orders
WHERE (customer_id, product_id) = (
  SELECT customer_id, product_id
  FROM featured_order
  LIMIT 1
);

-- Multiple column IN
SELECT * FROM order_items
WHERE (order_id, product_id) IN (
  SELECT order_id, product_id
  FROM returns
);
```

### Table Subqueries (Derived Tables)

Returns a full table. Used in FROM clause.

```sql
-- Derived table
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
  HAVING SUM(o.total) > 10000
) top_customers
ORDER BY top_customers.total_spent DESC;

-- Inline view for aggregation
SELECT
  d.name as department,
  stats.employee_count,
  stats.avg_salary
FROM departments d
JOIN (
  SELECT
    department_id,
    COUNT(*) as employee_count,
    AVG(salary) as avg_salary
  FROM employees
  GROUP BY department_id
) stats ON d.id = stats.department_id;
```

## Correlated Subqueries

References outer query. Executes once per outer row.

```sql
-- Employee salary vs department average
SELECT
  e.name,
  e.department_id,
  e.salary,
  (SELECT AVG(salary)
   FROM employees e2
   WHERE e2.department_id = e.department_id) as dept_avg
FROM employees e;

-- Latest order per customer
SELECT * FROM orders o1
WHERE created_at = (
  SELECT MAX(created_at)
  FROM orders o2
  WHERE o2.customer_id = o1.customer_id
);

-- Running total (before window functions)
SELECT
  date,
  amount,
  (SELECT SUM(amount)
   FROM transactions t2
   WHERE t2.date <= t1.date) as running_total
FROM transactions t1
ORDER BY date;
```

## EXISTS and NOT EXISTS

More efficient than IN for large datasets.

```sql
-- EXISTS: Customers with orders
SELECT * FROM customers c
WHERE EXISTS (
  SELECT 1 FROM orders o
  WHERE o.customer_id = c.id
);

-- NOT EXISTS: Customers without orders
SELECT * FROM customers c
WHERE NOT EXISTS (
  SELECT 1 FROM orders o
  WHERE o.customer_id = c.id
);

-- EXISTS with complex conditions
SELECT * FROM products p
WHERE EXISTS (
  SELECT 1 FROM order_items oi
  JOIN orders o ON oi.order_id = o.id
  WHERE oi.product_id = p.id
    AND o.created_at > NOW() - INTERVAL '30 days'
    AND o.status = 'completed'
);

-- Double NOT EXISTS (all condition)
-- Find customers who ordered ALL products in category
SELECT * FROM customers c
WHERE NOT EXISTS (
  SELECT 1 FROM products p
  WHERE p.category_id = 5
    AND NOT EXISTS (
      SELECT 1 FROM order_items oi
      JOIN orders o ON oi.order_id = o.id
      WHERE o.customer_id = c.id
        AND oi.product_id = p.id
    )
);
```

## Common Table Expressions (CTEs)

### Basic CTE Syntax

```sql
WITH cte_name AS (
  SELECT ...
)
SELECT * FROM cte_name;
```

### Simple CTEs

```sql
-- Single CTE
WITH active_customers AS (
  SELECT
    c.id,
    c.name,
    c.email,
    COUNT(o.id) as order_count
  FROM customers c
  JOIN orders o ON c.id = o.customer_id
  WHERE o.created_at > NOW() - INTERVAL '90 days'
  GROUP BY c.id, c.name, c.email
  HAVING COUNT(o.id) >= 3
)
SELECT
  ac.*,
  p.tier
FROM active_customers ac
JOIN loyalty_program p ON ac.order_count >= p.min_orders;
```

### Multiple CTEs

```sql
WITH
-- Monthly revenue
monthly_revenue AS (
  SELECT
    DATE_TRUNC('month', created_at) as month,
    SUM(total) as revenue
  FROM orders
  WHERE status = 'completed'
  GROUP BY 1
),
-- Monthly growth calculation
monthly_growth AS (
  SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) as prev_revenue
  FROM monthly_revenue
),
-- Growth rate
growth_rate AS (
  SELECT
    month,
    revenue,
    prev_revenue,
    CASE
      WHEN prev_revenue > 0
      THEN ROUND((revenue - prev_revenue) * 100.0 / prev_revenue, 2)
      ELSE NULL
    END as growth_pct
  FROM monthly_growth
)
SELECT * FROM growth_rate
ORDER BY month DESC;
```

### CTE with INSERT/UPDATE/DELETE

```sql
-- CTE with INSERT
WITH new_users AS (
  SELECT * FROM staging_users
  WHERE NOT EXISTS (
    SELECT 1 FROM users WHERE email = staging_users.email
  )
)
INSERT INTO users (email, name, created_at)
SELECT email, name, NOW() FROM new_users;

-- CTE with UPDATE
WITH inactive_users AS (
  SELECT id FROM users
  WHERE last_login < NOW() - INTERVAL '1 year'
)
UPDATE users SET status = 'inactive'
WHERE id IN (SELECT id FROM inactive_users);

-- CTE with DELETE and RETURNING
WITH deleted AS (
  DELETE FROM sessions
  WHERE expires_at < NOW()
  RETURNING *
)
INSERT INTO session_archive SELECT * FROM deleted;
```

## Recursive CTEs

### Basic Recursion Structure

```sql
WITH RECURSIVE cte_name AS (
  -- Base case (non-recursive term)
  SELECT ...

  UNION [ALL]

  -- Recursive case (references cte_name)
  SELECT ... FROM cte_name WHERE termination_condition
)
SELECT * FROM cte_name;
```

### Hierarchical Data

```sql
-- Organization chart
WITH RECURSIVE org_chart AS (
  -- Base: Top-level managers (no manager)
  SELECT
    id,
    name,
    manager_id,
    1 as level,
    name as path,
    ARRAY[id] as id_path
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive: Employees with managers
  SELECT
    e.id,
    e.name,
    e.manager_id,
    oc.level + 1,
    oc.path || ' > ' || e.name,
    oc.id_path || e.id
  FROM employees e
  JOIN org_chart oc ON e.manager_id = oc.id
  WHERE NOT (e.id = ANY(oc.id_path))  -- Prevent cycles
)
SELECT
  REPEAT('  ', level - 1) || name as org_chart,
  level,
  path
FROM org_chart
ORDER BY path;
```

### Category Tree

```sql
-- All descendants of a category
WITH RECURSIVE category_tree AS (
  SELECT
    id,
    name,
    parent_id,
    ARRAY[id] as ancestors
  FROM categories
  WHERE id = 5  -- Starting category

  UNION ALL

  SELECT
    c.id,
    c.name,
    c.parent_id,
    ct.ancestors || c.id
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.id
  WHERE NOT c.id = ANY(ct.ancestors)
)
SELECT * FROM category_tree;

-- All ancestors of a category
WITH RECURSIVE category_ancestors AS (
  SELECT id, name, parent_id, 0 as distance
  FROM categories
  WHERE id = 15  -- Starting category

  UNION ALL

  SELECT c.id, c.name, c.parent_id, ca.distance + 1
  FROM categories c
  JOIN category_ancestors ca ON c.id = ca.parent_id
)
SELECT * FROM category_ancestors
ORDER BY distance;
```

### Generating Series

```sql
-- Number sequence
WITH RECURSIVE numbers AS (
  SELECT 1 as n
  UNION ALL
  SELECT n + 1 FROM numbers WHERE n < 100
)
SELECT n FROM numbers;

-- Date series
WITH RECURSIVE dates AS (
  SELECT DATE '2024-01-01' as date
  UNION ALL
  SELECT date + 1 FROM dates WHERE date < DATE '2024-12-31'
)
SELECT
  d.date,
  COALESCE(SUM(o.total), 0) as daily_revenue
FROM dates d
LEFT JOIN orders o ON DATE(o.created_at) = d.date
GROUP BY d.date
ORDER BY d.date;

-- Fibonacci sequence
WITH RECURSIVE fib AS (
  SELECT 1 as n, 1::bigint as fib_n, 0::bigint as fib_prev
  UNION ALL
  SELECT n + 1, fib_n + fib_prev, fib_n
  FROM fib
  WHERE n < 50
)
SELECT n, fib_n FROM fib;
```

### Graph Traversal

```sql
-- Find all connected nodes (graph)
WITH RECURSIVE reachable AS (
  -- Start from node 1
  SELECT node_id, 0 as distance, ARRAY[node_id] as path
  FROM nodes
  WHERE node_id = 1

  UNION ALL

  SELECT
    e.to_node,
    r.distance + 1,
    r.path || e.to_node
  FROM edges e
  JOIN reachable r ON e.from_node = r.node_id
  WHERE NOT e.to_node = ANY(r.path)  -- Prevent cycles
    AND r.distance < 10  -- Max depth
)
SELECT DISTINCT node_id, MIN(distance) as min_distance
FROM reachable
GROUP BY node_id;

-- Shortest path (BFS style)
WITH RECURSIVE shortest_path AS (
  SELECT
    1 as current_node,
    ARRAY[1] as path,
    0 as cost

  UNION ALL

  SELECT
    e.to_node,
    sp.path || e.to_node,
    sp.cost + e.weight
  FROM edges e
  JOIN shortest_path sp ON e.from_node = sp.current_node
  WHERE NOT e.to_node = ANY(sp.path)
)
SELECT * FROM shortest_path
WHERE current_node = 10  -- Target node
ORDER BY cost
LIMIT 1;
```

## Performance Comparison

### Subquery vs JOIN

```sql
-- Subquery (may be slower)
SELECT * FROM products
WHERE category_id IN (
  SELECT id FROM categories WHERE active = true
);

-- JOIN (often faster)
SELECT p.* FROM products p
JOIN categories c ON p.category_id = c.id
WHERE c.active = true;

-- EXISTS (best for large tables)
SELECT * FROM products p
WHERE EXISTS (
  SELECT 1 FROM categories c
  WHERE c.id = p.category_id AND c.active = true
);
```

### CTE Materialization

```sql
-- PostgreSQL 12+: CTEs may be inlined (optimized)
-- Use MATERIALIZED to force materialization

-- May be inlined (optimizer decides)
WITH recent_orders AS (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent_orders WHERE status = 'pending';

-- Force materialization (executes CTE once)
WITH recent_orders AS MATERIALIZED (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent_orders WHERE status = 'pending';

-- Force inlining (like a view)
WITH recent_orders AS NOT MATERIALIZED (
  SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
)
SELECT * FROM recent_orders WHERE status = 'pending';
```

## Best Practices

### When to Use CTEs

```sql
-- Good: Complex multi-step logic
WITH
step1 AS (...),
step2 AS (... FROM step1 ...),
step3 AS (... FROM step2 ...)
SELECT * FROM step3;

-- Good: Recursive queries
WITH RECURSIVE tree AS (...)
SELECT * FROM tree;

-- Good: Reusing same subquery
WITH common_filter AS (
  SELECT * FROM large_table WHERE complex_condition
)
SELECT * FROM common_filter a
JOIN common_filter b ON ...;
```

### When to Use Subqueries

```sql
-- Good: Simple scalar values
SELECT name, salary / (SELECT MAX(salary) FROM employees) as ratio
FROM employees;

-- Good: EXISTS checks
SELECT * FROM customers c
WHERE EXISTS (SELECT 1 FROM orders WHERE customer_id = c.id);

-- Good: Simple IN clauses
SELECT * FROM products
WHERE category_id IN (SELECT id FROM active_categories);
```

### Anti-patterns to Avoid

```sql
-- Bad: Correlated subquery in SELECT (N+1 queries conceptually)
SELECT
  o.id,
  (SELECT name FROM customers WHERE id = o.customer_id)  -- Bad!
FROM orders o;

-- Better: Use JOIN
SELECT o.id, c.name
FROM orders o
JOIN customers c ON o.customer_id = c.id;

-- Bad: NOT IN with potentially NULL values
SELECT * FROM a WHERE id NOT IN (SELECT nullable_id FROM b);  -- Wrong!

-- Better: NOT EXISTS or explicit NULL handling
SELECT * FROM a
WHERE NOT EXISTS (SELECT 1 FROM b WHERE b.nullable_id = a.id);
-- Or
SELECT * FROM a
WHERE id NOT IN (SELECT nullable_id FROM b WHERE nullable_id IS NOT NULL);
```
