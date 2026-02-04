---
name: window-functions
description: Comprehensive guide to SQL window functions
category: database/sql
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Window Functions

## Overview

Window functions perform calculations across a set of rows related to
the current row without collapsing the result set. Unlike GROUP BY,
window functions keep all rows while adding computed values.

## Basic Syntax

```sql
function_name(expression) OVER (
  [PARTITION BY partition_columns]
  [ORDER BY order_columns [ASC|DESC]]
  [frame_clause]
)
```

## Window Function Categories

```
┌─────────────────────────────────────────────────────────────────┐
│                   Window Function Types                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Ranking          Aggregate         Value                        │
│  ────────         ─────────         ─────                        │
│  ROW_NUMBER()     SUM()             LAG()                        │
│  RANK()           AVG()             LEAD()                       │
│  DENSE_RANK()     COUNT()           FIRST_VALUE()                │
│  NTILE()          MIN()             LAST_VALUE()                 │
│  PERCENT_RANK()   MAX()             NTH_VALUE()                  │
│  CUME_DIST()                                                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Ranking Functions

### ROW_NUMBER

Assigns unique sequential numbers. No ties.

```sql
-- Basic row numbering
SELECT
  name,
  department,
  salary,
  ROW_NUMBER() OVER (ORDER BY salary DESC) as salary_rank
FROM employees;

-- Result:
-- name    | department | salary | salary_rank
-- --------|------------|--------|------------
-- Alice   | Tech       | 120000 | 1
-- Bob     | Sales      | 100000 | 2
-- Carol   | Tech       | 100000 | 3  ← Different rank despite same salary
-- David   | HR         | 80000  | 4

-- Rank within groups
SELECT
  name,
  department,
  salary,
  ROW_NUMBER() OVER (
    PARTITION BY department
    ORDER BY salary DESC
  ) as dept_rank
FROM employees;

-- Result:
-- name    | department | salary | dept_rank
-- --------|------------|--------|----------
-- Alice   | Tech       | 120000 | 1
-- Carol   | Tech       | 100000 | 2
-- Bob     | Sales      | 100000 | 1
-- Eve     | Sales      | 90000  | 2
-- David   | HR         | 80000  | 1
```

### RANK and DENSE_RANK

Handle ties differently.

```sql
SELECT
  name,
  score,
  RANK() OVER (ORDER BY score DESC) as rank,
  DENSE_RANK() OVER (ORDER BY score DESC) as dense_rank
FROM contestants;

-- Result:
-- name    | score | rank | dense_rank
-- --------|-------|------|------------
-- Alice   | 100   | 1    | 1
-- Bob     | 100   | 1    | 1         ← Same rank (tie)
-- Carol   | 95    | 3    | 2         ← RANK skips to 3, DENSE_RANK is 2
-- David   | 90    | 4    | 3
-- Eve     | 90    | 4    | 3         ← Another tie
-- Frank   | 85    | 6    | 4         ← RANK skips to 6
```

### NTILE

Divides rows into N buckets.

```sql
-- Divide into quartiles
SELECT
  name,
  salary,
  NTILE(4) OVER (ORDER BY salary) as quartile
FROM employees;

-- Result:
-- name    | salary | quartile
-- --------|--------|----------
-- David   | 50000  | 1        ← Bottom 25%
-- Eve     | 60000  | 1
-- Carol   | 70000  | 2
-- Bob     | 80000  | 2
-- Alice   | 90000  | 3
-- Frank   | 100000 | 3
-- Grace   | 110000 | 4        ← Top 25%
-- Henry   | 120000 | 4

-- Use for tiered pricing
SELECT
  product_name,
  price,
  CASE NTILE(3) OVER (ORDER BY price)
    WHEN 1 THEN 'Budget'
    WHEN 2 THEN 'Standard'
    WHEN 3 THEN 'Premium'
  END as tier
FROM products;
```

### PERCENT_RANK and CUME_DIST

Relative position calculations.

```sql
SELECT
  name,
  salary,
  ROUND(PERCENT_RANK() OVER (ORDER BY salary)::numeric, 2) as pct_rank,
  ROUND(CUME_DIST() OVER (ORDER BY salary)::numeric, 2) as cume_dist
FROM employees;

-- PERCENT_RANK: (rank - 1) / (total - 1), range 0-1
-- CUME_DIST: rank / total, range 0-1

-- Result:
-- name    | salary | pct_rank | cume_dist
-- --------|--------|----------|----------
-- David   | 50000  | 0.00     | 0.25      ← Lowest: 0%
-- Carol   | 70000  | 0.33     | 0.50
-- Bob     | 80000  | 0.67     | 0.75
-- Alice   | 100000 | 1.00     | 1.00      ← Highest: 100%
```

## Aggregate Window Functions

### Running Calculations

```sql
-- Running total
SELECT
  date,
  amount,
  SUM(amount) OVER (ORDER BY date) as running_total
FROM transactions;

-- Result:
-- date       | amount | running_total
-- -----------|--------|---------------
-- 2024-01-01 | 100    | 100
-- 2024-01-02 | 200    | 300
-- 2024-01-03 | 150    | 450
-- 2024-01-04 | 300    | 750

-- Running total by category
SELECT
  date,
  category,
  amount,
  SUM(amount) OVER (
    PARTITION BY category
    ORDER BY date
  ) as category_running_total
FROM transactions;
```

### Comparative Analytics

```sql
-- Compare to department average
SELECT
  name,
  department,
  salary,
  ROUND(AVG(salary) OVER (PARTITION BY department)) as dept_avg,
  salary - ROUND(AVG(salary) OVER (PARTITION BY department)) as diff_from_avg,
  ROUND(
    salary * 100.0 / SUM(salary) OVER (PARTITION BY department), 2
  ) as pct_of_dept_total
FROM employees;

-- Result:
-- name  | department | salary | dept_avg | diff_from_avg | pct_of_dept_total
-- ------|------------|--------|----------|---------------|------------------
-- Alice | Tech       | 120000 | 110000   | 10000         | 54.55
-- Carol | Tech       | 100000 | 110000   | -10000        | 45.45
-- Bob   | Sales      | 100000 | 95000    | 5000          | 52.63
-- Eve   | Sales      | 90000  | 95000    | -5000         | 47.37
```

### Count and Distinct

```sql
-- Order number for each customer
SELECT
  customer_id,
  order_id,
  order_date,
  ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY order_date
  ) as order_number,
  COUNT(*) OVER (PARTITION BY customer_id) as total_orders
FROM orders;

-- Running distinct count (PostgreSQL)
SELECT
  date,
  user_id,
  COUNT(DISTINCT user_id) OVER (
    ORDER BY date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as cumulative_users
FROM user_sessions;
```

## Value Functions

### LAG and LEAD

Access previous and next rows.

```sql
-- Compare to previous period
SELECT
  date,
  revenue,
  LAG(revenue, 1) OVER (ORDER BY date) as prev_revenue,
  revenue - LAG(revenue, 1) OVER (ORDER BY date) as change,
  ROUND(
    (revenue - LAG(revenue, 1) OVER (ORDER BY date)) * 100.0 /
    LAG(revenue, 1) OVER (ORDER BY date), 2
  ) as pct_change
FROM daily_revenue;

-- Result:
-- date       | revenue | prev_revenue | change | pct_change
-- -----------|---------|--------------|--------|------------
-- 2024-01-01 | 1000    | NULL         | NULL   | NULL
-- 2024-01-02 | 1200    | 1000         | 200    | 20.00
-- 2024-01-03 | 1100    | 1200         | -100   | -8.33
-- 2024-01-04 | 1500    | 1100         | 400    | 36.36

-- Look ahead
SELECT
  date,
  stock_price,
  LEAD(stock_price, 1) OVER (ORDER BY date) as next_price,
  LEAD(stock_price, 7) OVER (ORDER BY date) as price_in_week
FROM stock_prices;

-- With default value for NULL
SELECT
  date,
  revenue,
  LAG(revenue, 1, 0) OVER (ORDER BY date) as prev_revenue
FROM daily_revenue;
```

### FIRST_VALUE, LAST_VALUE, NTH_VALUE

```sql
-- First and last in group
SELECT
  department,
  name,
  hire_date,
  salary,
  FIRST_VALUE(name) OVER (
    PARTITION BY department
    ORDER BY hire_date
  ) as first_hire,
  FIRST_VALUE(name) OVER (
    PARTITION BY department
    ORDER BY salary DESC
  ) as highest_paid
FROM employees;

-- LAST_VALUE requires explicit frame
SELECT
  department,
  name,
  salary,
  LAST_VALUE(name) OVER (
    PARTITION BY department
    ORDER BY salary
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as highest_paid
FROM employees;

-- NTH_VALUE: Get specific position
SELECT
  department,
  name,
  salary,
  NTH_VALUE(name, 2) OVER (
    PARTITION BY department
    ORDER BY salary DESC
    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
  ) as second_highest_paid
FROM employees;
```

## Window Frame Clauses

### Frame Syntax

```sql
ROWS BETWEEN frame_start AND frame_end

-- frame_start / frame_end options:
-- UNBOUNDED PRECEDING  (first row of partition)
-- n PRECEDING          (n rows before current)
-- CURRENT ROW
-- n FOLLOWING          (n rows after current)
-- UNBOUNDED FOLLOWING  (last row of partition)
```

### Common Frame Patterns

```sql
-- Default frame (when ORDER BY present)
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- Entire partition
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING

-- Moving window
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW  -- 7-day window

-- Centered window
ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING  -- 7-day centered
```

### Frame Examples

```sql
-- 7-day moving average
SELECT
  date,
  revenue,
  ROUND(AVG(revenue) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ), 2) as moving_avg_7d
FROM daily_revenue;

-- 30-day rolling sum
SELECT
  date,
  sales,
  SUM(sales) OVER (
    ORDER BY date
    ROWS BETWEEN 29 PRECEDING AND CURRENT ROW
  ) as rolling_30d
FROM daily_sales;

-- Year-to-date total
SELECT
  date,
  revenue,
  SUM(revenue) OVER (
    PARTITION BY EXTRACT(YEAR FROM date)
    ORDER BY date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
  ) as ytd_revenue
FROM daily_revenue;

-- Min/Max in window
SELECT
  date,
  price,
  MIN(price) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as min_7d,
  MAX(price) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
  ) as max_7d
FROM stock_prices;
```

### RANGE vs ROWS

```sql
-- ROWS: Physical row count
SELECT
  date,
  value,
  SUM(value) OVER (
    ORDER BY date
    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
  ) as sum_last_3_rows
FROM metrics;

-- RANGE: Logical value range (handles ties differently)
SELECT
  date,
  value,
  SUM(value) OVER (
    ORDER BY date
    RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW
  ) as sum_last_7_days
FROM metrics;

-- Difference matters when there are gaps or ties
```

## Named Windows

```sql
-- Define window once, reuse multiple times
SELECT
  name,
  department,
  salary,
  ROW_NUMBER() OVER dept_salary as rank,
  SUM(salary) OVER dept_salary as running_total,
  AVG(salary) OVER dept as dept_avg
FROM employees
WINDOW
  dept AS (PARTITION BY department),
  dept_salary AS (PARTITION BY department ORDER BY salary DESC);
```

## Practical Examples

### Top N Per Group

```sql
-- Top 3 products per category by sales
WITH ranked AS (
  SELECT
    category,
    product_name,
    sales,
    ROW_NUMBER() OVER (
      PARTITION BY category
      ORDER BY sales DESC
    ) as rank
  FROM products
)
SELECT * FROM ranked WHERE rank <= 3;

-- Using LATERAL (PostgreSQL, more efficient)
SELECT c.name, top_products.*
FROM categories c
CROSS JOIN LATERAL (
  SELECT product_name, sales
  FROM products
  WHERE category_id = c.id
  ORDER BY sales DESC
  LIMIT 3
) top_products;
```

### Gap Detection

```sql
-- Find gaps in sequential data
WITH numbered AS (
  SELECT
    id,
    ROW_NUMBER() OVER (ORDER BY id) as rn
  FROM orders
)
SELECT
  id,
  id - rn as grp,
  LAG(id) OVER (ORDER BY id) as prev_id,
  id - LAG(id) OVER (ORDER BY id) as gap
FROM numbered
WHERE id - LAG(id) OVER (ORDER BY id) > 1;
```

### Session Detection

```sql
-- Group user actions into sessions (30 min inactivity = new session)
WITH events_with_lag AS (
  SELECT
    user_id,
    event_time,
    LAG(event_time) OVER (
      PARTITION BY user_id
      ORDER BY event_time
    ) as prev_event_time
  FROM user_events
),
session_starts AS (
  SELECT
    *,
    CASE
      WHEN prev_event_time IS NULL
        OR event_time - prev_event_time > INTERVAL '30 minutes'
      THEN 1
      ELSE 0
    END as is_new_session
  FROM events_with_lag
)
SELECT
  user_id,
  event_time,
  SUM(is_new_session) OVER (
    PARTITION BY user_id
    ORDER BY event_time
  ) as session_id
FROM session_starts;
```

### Funnel Analysis

```sql
-- Conversion funnel
WITH funnel AS (
  SELECT
    user_id,
    MAX(CASE WHEN event = 'view' THEN 1 ELSE 0 END) as viewed,
    MAX(CASE WHEN event = 'add_to_cart' THEN 1 ELSE 0 END) as added,
    MAX(CASE WHEN event = 'checkout' THEN 1 ELSE 0 END) as checked_out,
    MAX(CASE WHEN event = 'purchase' THEN 1 ELSE 0 END) as purchased
  FROM events
  GROUP BY user_id
)
SELECT
  SUM(viewed) as views,
  SUM(added) as adds,
  SUM(checked_out) as checkouts,
  SUM(purchased) as purchases,
  ROUND(SUM(added) * 100.0 / SUM(viewed), 2) as view_to_add_rate,
  ROUND(SUM(purchased) * 100.0 / SUM(viewed), 2) as overall_conversion
FROM funnel;
```

### Retention Analysis

```sql
-- Cohort retention
WITH first_purchase AS (
  SELECT
    user_id,
    DATE_TRUNC('month', MIN(order_date)) as cohort_month
  FROM orders
  GROUP BY user_id
),
user_activity AS (
  SELECT
    o.user_id,
    fp.cohort_month,
    DATE_TRUNC('month', o.order_date) as activity_month,
    (DATE_TRUNC('month', o.order_date) - fp.cohort_month) / INTERVAL '1 month' as month_number
  FROM orders o
  JOIN first_purchase fp ON o.user_id = fp.user_id
)
SELECT
  cohort_month,
  month_number,
  COUNT(DISTINCT user_id) as users,
  ROUND(
    COUNT(DISTINCT user_id) * 100.0 /
    FIRST_VALUE(COUNT(DISTINCT user_id)) OVER (
      PARTITION BY cohort_month
      ORDER BY month_number
    ), 2
  ) as retention_rate
FROM user_activity
GROUP BY cohort_month, month_number
ORDER BY cohort_month, month_number;
```
