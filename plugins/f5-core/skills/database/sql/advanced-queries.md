---
name: advanced-sql-queries
description: Advanced SQL query techniques and patterns
category: database/sql
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Advanced SQL Queries

## Window Functions

Window functions perform calculations across a set of rows related
to the current row, without collapsing the result set like GROUP BY.

### Basic Syntax

```sql
function_name(expression) OVER (
  [PARTITION BY column_list]
  [ORDER BY column_list]
  [frame_clause]
)
```

### Ranking Functions

```sql
-- ROW_NUMBER: Unique sequential number
SELECT
  name,
  department,
  salary,
  ROW_NUMBER() OVER (ORDER BY salary DESC) as overall_rank,
  ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as dept_rank
FROM employees;

-- RANK: Same rank for ties, gaps after
SELECT
  name,
  score,
  RANK() OVER (ORDER BY score DESC) as rank
FROM contestants;
-- Results: 100→1, 100→1, 95→3, 90→4 (skips rank 2)

-- DENSE_RANK: Same rank for ties, no gaps
SELECT
  name,
  score,
  DENSE_RANK() OVER (ORDER BY score DESC) as rank
FROM contestants;
-- Results: 100→1, 100→1, 95→2, 90→3 (no gap)

-- NTILE: Divide into N buckets
SELECT
  name,
  salary,
  NTILE(4) OVER (ORDER BY salary) as quartile
FROM employees;

-- PERCENT_RANK: Relative rank (0-1)
SELECT
  name,
  salary,
  PERCENT_RANK() OVER (ORDER BY salary) as percentile
FROM employees;
```

### Aggregate Window Functions

```sql
-- Running totals
SELECT
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) as running_total,
  SUM(amount) OVER (
    ORDER BY date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as running_total_explicit
FROM transactions;

-- Cumulative average
SELECT
  date,
  value,
  AVG(value) OVER (ORDER BY date) as cumulative_avg
FROM metrics;

-- Partition aggregates
SELECT
  department,
  name,
  salary,
  AVG(salary) OVER (PARTITION BY department) as dept_avg,
  salary - AVG(salary) OVER (PARTITION BY department) as diff_from_avg,
  salary * 100.0 / SUM(salary) OVER (PARTITION BY department) as pct_of_dept
FROM employees;

-- Count with partition
SELECT
  customer_id,
  order_id,
  order_date,
  COUNT(*) OVER (PARTITION BY customer_id) as total_orders,
  ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY order_date) as order_num
FROM orders;
```

### Value Window Functions

```sql
-- LAG: Previous row value
SELECT
  date,
  revenue,
  LAG(revenue, 1) OVER (ORDER BY date) as prev_revenue,
  revenue - LAG(revenue, 1) OVER (ORDER BY date) as change,
  ROUND(
    (revenue - LAG(revenue, 1) OVER (ORDER BY date)) * 100.0 /
    LAG(revenue, 1) OVER (ORDER BY date),
    2
  ) as pct_change
FROM daily_revenue;

-- LEAD: Next row value
SELECT
  date,
  stock_price,
  LEAD(stock_price, 1) OVER (ORDER BY date) as next_price
FROM stock_prices;

-- FIRST_VALUE / LAST_VALUE
SELECT
  department,
  name,
  salary,
  FIRST_VALUE(name) OVER (
    PARTITION BY department
    ORDER BY salary DESC
  ) as highest_paid,
  LAST_VALUE(name) OVER (
    PARTITION BY department
    ORDER BY salary DESC
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as lowest_paid
FROM employees;

-- NTH_VALUE
SELECT
  department,
  name,
  salary,
  NTH_VALUE(name, 2) OVER (
    PARTITION BY department
    ORDER BY salary DESC
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as second_highest
FROM employees;
```

### Window Frame Clauses

```sql
-- Moving average (7-day)
SELECT
  date,
  revenue,
  AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as moving_avg_7d
FROM daily_revenue;

-- Moving sum (30-day)
SELECT
  date,
  sales,
  SUM(sales) OVER (
    ORDER BY date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as rolling_30d_sales
FROM daily_sales;

-- Range-based frame (by value, not rows)
SELECT
  date,
  amount,
  SUM(amount) OVER (
    ORDER BY date
    RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW
  ) as sum_last_7_days
FROM transactions;

-- Centered window
SELECT
  date,
  value,
  AVG(value) OVER (
    ORDER BY date
    ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING
  ) as centered_avg
FROM measurements;
```

## Common Table Expressions (CTEs)

### Basic CTE

```sql
-- Simple CTE
WITH active_users AS (
  SELECT id, name, email
  FROM users
  WHERE status = 'active'
    AND last_login > NOW() - INTERVAL '30 days'
)
SELECT
  au.name,
  COUNT(o.id) as order_count
FROM active_users au
LEFT JOIN orders o ON au.id = o.user_id
GROUP BY au.id, au.name;

-- Multiple CTEs
WITH
monthly_sales AS (
  SELECT
    DATE_TRUNC('month', order_date) as month,
    SUM(total) as revenue
  FROM orders
  WHERE status = 'completed'
  GROUP BY 1
),
sales_growth AS (
  SELECT
    month,
    revenue,
    LAG(revenue) OVER (ORDER BY month) as prev_revenue,
    ROUND(
      (revenue - LAG(revenue) OVER (ORDER BY month)) * 100.0 /
      LAG(revenue) OVER (ORDER BY month),
      2
    ) as growth_pct
  FROM monthly_sales
)
SELECT * FROM sales_growth
WHERE month >= DATE_TRUNC('year', CURRENT_DATE);
```

### Recursive CTE

```sql
-- Hierarchical data (org chart)
WITH RECURSIVE org_tree AS (
  -- Base case: top-level (CEO)
  SELECT
    id,
    name,
    manager_id,
    1 as level,
    ARRAY[name] as path,
    name as path_string
  FROM employees
  WHERE manager_id IS NULL

  UNION ALL

  -- Recursive case: employees with managers
  SELECT
    e.id,
    e.name,
    e.manager_id,
    ot.level + 1,
    ot.path || e.name,
    ot.path_string || ' > ' || e.name
  FROM employees e
  INNER JOIN org_tree ot ON e.manager_id = ot.id
)
SELECT
  REPEAT('  ', level - 1) || name as org_chart,
  level,
  path_string
FROM org_tree
ORDER BY path;

-- Category tree with totals
WITH RECURSIVE category_tree AS (
  SELECT
    id,
    name,
    parent_id,
    0 as depth
  FROM categories
  WHERE parent_id IS NULL

  UNION ALL

  SELECT
    c.id,
    c.name,
    c.parent_id,
    ct.depth + 1
  FROM categories c
  JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT
  ct.*,
  COALESCE(
    (SELECT COUNT(*) FROM products WHERE category_id = ct.id),
    0
  ) as product_count
FROM category_tree ct
ORDER BY depth, name;

-- Number sequence
WITH RECURSIVE numbers AS (
  SELECT 1 as n
  UNION ALL
  SELECT n + 1 FROM numbers WHERE n < 100
)
SELECT n FROM numbers;

-- Date series
WITH RECURSIVE date_series AS (
  SELECT DATE '2024-01-01' as date
  UNION ALL
  SELECT date + INTERVAL '1 day'
  FROM date_series
  WHERE date < DATE '2024-12-31'
)
SELECT
  ds.date,
  COALESCE(COUNT(o.id), 0) as order_count
FROM date_series ds
LEFT JOIN orders o ON DATE(o.created_at) = ds.date
GROUP BY ds.date
ORDER BY ds.date;
```

## Set Operations

```sql
-- UNION (remove duplicates)
SELECT email FROM customers
UNION
SELECT email FROM newsletter_subscribers;

-- UNION ALL (keep duplicates, faster)
SELECT id, 'order' as type, created_at FROM orders
UNION ALL
SELECT id, 'return' as type, created_at FROM returns
ORDER BY created_at;

-- INTERSECT (common rows)
SELECT product_id FROM warehouse_a
INTERSECT
SELECT product_id FROM warehouse_b;

-- EXCEPT (in first but not second)
SELECT user_id FROM users
EXCEPT
SELECT user_id FROM blocked_users;

-- Complex set operations
(
  SELECT id, email FROM premium_users
  UNION
  SELECT id, email FROM trial_users WHERE trial_end > NOW()
)
EXCEPT
SELECT id, email FROM banned_users;
```

## Advanced Joins

### Lateral Join

```sql
-- Top N per group (most efficient)
SELECT
  c.id,
  c.name,
  recent_orders.*
FROM customers c
CROSS JOIN LATERAL (
  SELECT
    o.id as order_id,
    o.total,
    o.created_at
  FROM orders o
  WHERE o.customer_id = c.id
  ORDER BY o.created_at DESC
  LIMIT 3
) recent_orders;

-- Dependent subquery in FROM
SELECT
  p.id,
  p.name,
  stats.*
FROM products p
CROSS JOIN LATERAL (
  SELECT
    COUNT(*) as order_count,
    SUM(oi.quantity) as total_sold,
    AVG(oi.price) as avg_price
  FROM order_items oi
  WHERE oi.product_id = p.id
) stats;
```

### Self Joins

```sql
-- Find duplicates
SELECT
  a.id as id1,
  b.id as id2,
  a.email
FROM users a
JOIN users b ON a.email = b.email AND a.id < b.id;

-- Gaps in sequence
SELECT
  a.id + 1 as gap_start,
  MIN(b.id) - 1 as gap_end
FROM orders a
LEFT JOIN orders b ON b.id > a.id
GROUP BY a.id
HAVING MIN(b.id) > a.id + 1;

-- Compare consecutive rows
SELECT
  curr.date,
  curr.value,
  prev.value as prev_value,
  curr.value - prev.value as change
FROM metrics curr
LEFT JOIN metrics prev ON prev.date = curr.date - INTERVAL '1 day';
```

## Pivoting Data

### Pivot (Rows to Columns)

```sql
-- Using CASE statements (standard SQL)
SELECT
  product_id,
  SUM(CASE WHEN month = 'Jan' THEN revenue ELSE 0 END) as jan,
  SUM(CASE WHEN month = 'Feb' THEN revenue ELSE 0 END) as feb,
  SUM(CASE WHEN month = 'Mar' THEN revenue ELSE 0 END) as mar,
  SUM(CASE WHEN month = 'Apr' THEN revenue ELSE 0 END) as apr
FROM monthly_sales
GROUP BY product_id;

-- Using FILTER (PostgreSQL)
SELECT
  product_id,
  SUM(revenue) FILTER (WHERE month = 'Jan') as jan,
  SUM(revenue) FILTER (WHERE month = 'Feb') as feb,
  SUM(revenue) FILTER (WHERE month = 'Mar') as mar
FROM monthly_sales
GROUP BY product_id;

-- Using crosstab (PostgreSQL tablefunc extension)
SELECT * FROM crosstab(
  'SELECT product_id, month, revenue
   FROM monthly_sales
   ORDER BY 1, 2',
  'SELECT DISTINCT month FROM monthly_sales ORDER BY 1'
) AS ct(product_id INT, jan NUMERIC, feb NUMERIC, mar NUMERIC);
```

### Unpivot (Columns to Rows)

```sql
-- Using UNION ALL
SELECT product_id, 'jan' as month, jan as revenue FROM pivoted_sales
UNION ALL
SELECT product_id, 'feb' as month, feb as revenue FROM pivoted_sales
UNION ALL
SELECT product_id, 'mar' as month, mar as revenue FROM pivoted_sales;

-- Using LATERAL (PostgreSQL)
SELECT
  p.product_id,
  m.month,
  m.revenue
FROM pivoted_sales p
CROSS JOIN LATERAL (
  VALUES
    ('jan', p.jan),
    ('feb', p.feb),
    ('mar', p.mar)
) AS m(month, revenue);

-- Using unnest with arrays (PostgreSQL)
SELECT
  product_id,
  unnest(ARRAY['jan', 'feb', 'mar']) as month,
  unnest(ARRAY[jan, feb, mar]) as revenue
FROM pivoted_sales;
```

## Advanced Aggregation

### GROUPING SETS

```sql
-- Multiple grouping levels in one query
SELECT
  COALESCE(region, 'All Regions') as region,
  COALESCE(category, 'All Categories') as category,
  SUM(sales) as total_sales
FROM sales
GROUP BY GROUPING SETS (
  (region, category),  -- By region and category
  (region),            -- By region only
  (category),          -- By category only
  ()                   -- Grand total
)
ORDER BY region NULLS FIRST, category NULLS FIRST;

-- ROLLUP (hierarchical subtotals)
SELECT
  year,
  quarter,
  month,
  SUM(revenue) as revenue
FROM sales
GROUP BY ROLLUP (year, quarter, month);
-- Produces: year/quarter/month, year/quarter, year, total

-- CUBE (all combinations)
SELECT
  region,
  category,
  SUM(sales)
FROM sales
GROUP BY CUBE (region, category);
-- Produces: region/category, region, category, total

-- GROUPING function (identify aggregation level)
SELECT
  CASE WHEN GROUPING(region) = 1 THEN 'All' ELSE region END as region,
  CASE WHEN GROUPING(category) = 1 THEN 'All' ELSE category END as category,
  SUM(sales),
  GROUPING(region, category) as level
FROM sales
GROUP BY CUBE (region, category);
```

### Conditional Aggregation

```sql
-- Count by condition
SELECT
  COUNT(*) as total_orders,
  COUNT(*) FILTER (WHERE status = 'completed') as completed,
  COUNT(*) FILTER (WHERE status = 'pending') as pending,
  COUNT(*) FILTER (WHERE status = 'cancelled') as cancelled,
  COUNT(*) FILTER (WHERE total > 100) as high_value
FROM orders;

-- Sum by condition
SELECT
  customer_id,
  SUM(total) as total_revenue,
  SUM(total) FILTER (WHERE EXTRACT(YEAR FROM order_date) = 2024) as revenue_2024,
  SUM(total) FILTER (WHERE category = 'electronics') as electronics_revenue
FROM orders
GROUP BY customer_id;

-- Percentage calculations
SELECT
  category,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE rating >= 4) as good_ratings,
  ROUND(
    COUNT(*) FILTER (WHERE rating >= 4) * 100.0 / COUNT(*),
    2
  ) as good_rating_pct
FROM reviews
GROUP BY category;
```

## Performance Tips

```sql
-- 1. Use EXISTS instead of IN for large subqueries
-- Slower
SELECT * FROM orders WHERE user_id IN (SELECT id FROM vip_users);
-- Faster
SELECT * FROM orders o WHERE EXISTS (
  SELECT 1 FROM vip_users v WHERE v.id = o.user_id
);

-- 2. Use CTEs for readability, but be aware of optimization barriers
-- PostgreSQL < 12 materialized CTEs, >= 12 may inline

-- 3. Limit early in CTEs when possible
WITH recent_orders AS (
  SELECT * FROM orders
  WHERE created_at > NOW() - INTERVAL '30 days'
  -- Filter early, not in final query
)
SELECT * FROM recent_orders WHERE status = 'pending';

-- 4. Use appropriate indexes for window functions
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at DESC);
-- Helps: ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC)

-- 5. Avoid SELECT * in CTEs
WITH user_data AS (
  SELECT id, name, email  -- Only needed columns
  FROM users
  WHERE status = 'active'
)
SELECT * FROM user_data;
```
