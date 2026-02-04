---
name: explain-analyze
description: Understanding and using EXPLAIN ANALYZE effectively
category: database/optimization
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# EXPLAIN ANALYZE Guide

## Overview

EXPLAIN ANALYZE is the most powerful tool for understanding query
performance. It shows exactly how the database executes your query
and where time is spent.

## EXPLAIN Variants

```sql
-- Basic plan (estimates only)
EXPLAIN SELECT * FROM users WHERE email = 'test@example.com';

-- With actual execution (runs the query)
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

-- With buffer usage statistics
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM users WHERE email = 'test@example.com';

-- Full verbose output
EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT * FROM users WHERE email = 'test@example.com';

-- JSON format (for tools)
EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
SELECT * FROM users WHERE email = 'test@example.com';

-- Settings for detailed timing
EXPLAIN (ANALYZE, BUFFERS, TIMING, SUMMARY)
SELECT * FROM users WHERE email = 'test@example.com';
```

## Reading Execution Plans

### Plan Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                  Execution Plan Structure                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Hash Join  (cost=... rows=... width=...)                       │
│    ├── Hash Cond: (o.customer_id = c.id)                        │
│    ├── -> Seq Scan on orders o                                  │
│    │      Filter: (status = 'pending')                          │
│    └── -> Hash                                                   │
│           └── -> Seq Scan on customers c                        │
│                                                                  │
│  Execution order: Bottom-up, innermost first                    │
│  - First: Seq Scan on customers → Hash                          │
│  - Then: Seq Scan on orders (filtered)                          │
│  - Finally: Hash Join combines results                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Metrics

```sql
/*
Seq Scan on users  (cost=0.00..1234.00 rows=50000 width=100)
                         ^^^^^  ^^^^^^^  ^^^^^ ^^^^^^^^ ^^^^^
                         |      |        |     |        |
                   startup cost |      rows   |     row width
                           total cost     estimated   (bytes)
*/

-- With ANALYZE:
/*
Seq Scan on users (cost=0.00..1234.00 rows=50000 width=100)
                  (actual time=0.012..45.678 rows=48523 loops=1)
                         ^^^^^^^^^^^^^  ^^^^^^^^ ^^^^^  ^^^^^
                         |              |        |      |
                   startup..total    actual   actual  iterations
                      (ms)            rows
*/

-- With BUFFERS:
/*
Buffers: shared hit=1234 read=56 dirtied=10 written=5
         ^^^^^^    ^^^^  ^^^^   ^^^^^^^     ^^^^^^^
         |         |     |      |           |
    buffer type  cache  disk   modified   written back
                 hits   reads
*/
```

## Scan Types

### Sequential Scan

```sql
EXPLAIN ANALYZE SELECT * FROM users;

/*
Seq Scan on users  (cost=0.00..1234.00 rows=50000 width=100)
                   (actual time=0.012..45.678 rows=50000 loops=1)
   Buffers: shared hit=834

Analysis:
- Reads entire table row by row
- Normal for small tables or queries needing most rows
- Warning sign on large tables with selective filters
*/
```

### Index Scan

```sql
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'test@example.com';

/*
Index Scan using idx_users_email on users (cost=0.42..8.44 rows=1 width=100)
                                          (actual time=0.024..0.025 rows=1 loops=1)
   Index Cond: (email = 'test@example.com'::text)
   Buffers: shared hit=4

Analysis:
- Uses index to find rows, then fetches from table
- Good for selective queries (returning few rows)
- Index Cond shows which part used the index
*/
```

### Index Only Scan

```sql
-- Query only needs indexed columns
EXPLAIN ANALYZE SELECT id, email FROM users WHERE email = 'test@example.com';

/*
Index Only Scan using idx_users_email_covering on users
   (cost=0.42..4.44 rows=1 width=44)
   (actual time=0.018..0.019 rows=1 loops=1)
   Index Cond: (email = 'test@example.com'::text)
   Heap Fetches: 0
   Buffers: shared hit=3

Analysis:
- Reads only from index, no table access
- "Heap Fetches: 0" confirms no table access
- Fastest scan type when possible
*/
```

### Bitmap Scan

```sql
EXPLAIN ANALYZE
SELECT * FROM orders WHERE status = 'pending' OR status = 'processing';

/*
Bitmap Heap Scan on orders  (cost=12.34..567.89 rows=1000 width=100)
                            (actual time=0.234..2.345 rows=987 loops=1)
   Recheck Cond: ((status = 'pending') OR (status = 'processing'))
   Heap Blocks: exact=234
   Buffers: shared hit=250
   ->  BitmapOr  (cost=12.34..12.34 rows=1000 width=0)
         ->  Bitmap Index Scan on idx_orders_status
               Index Cond: (status = 'pending')
         ->  Bitmap Index Scan on idx_orders_status
               Index Cond: (status = 'processing')

Analysis:
- First: Build bitmap of matching rows
- Then: Fetch rows in physical order (reduces random I/O)
- Good for OR conditions or low selectivity
*/
```

## Join Types

### Nested Loop

```sql
EXPLAIN ANALYZE
SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id
WHERE o.id = 'order-uuid';

/*
Nested Loop  (cost=0.85..16.89 rows=1 width=200)
             (actual time=0.045..0.048 rows=1 loops=1)
   ->  Index Scan using orders_pkey on orders o
         Index Cond: (id = 'order-uuid')
         Buffers: shared hit=3
   ->  Index Scan using customers_pkey on customers c
         Index Cond: (id = o.customer_id)
         Buffers: shared hit=3

Analysis:
- For each row in outer (orders), lookup in inner (customers)
- Efficient for small result sets with indexed joins
- loops=1 means outer returned 1 row
*/
```

### Hash Join

```sql
EXPLAIN ANALYZE
SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending';

/*
Hash Join  (cost=100.00..800.00 rows=5000 width=200)
           (actual time=2.345..25.678 rows=4987 loops=1)
   Hash Cond: (o.customer_id = c.id)
   ->  Seq Scan on orders o
         Filter: (status = 'pending')
         Rows Removed by Filter: 45000
   ->  Hash  (cost=80.00..80.00 rows=1000 width=100)
         Buckets: 1024  Batches: 1  Memory Usage: 80kB
         ->  Seq Scan on customers c

Analysis:
- Build hash table from smaller table (customers)
- Probe with larger table (orders)
- Memory Usage shows hash table size
- Batches > 1 means spilled to disk (bad)
*/
```

### Merge Join

```sql
EXPLAIN ANALYZE
SELECT o.*, c.name FROM orders o JOIN customers c ON o.customer_id = c.id
ORDER BY o.customer_id;

/*
Merge Join  (cost=500.00..1000.00 rows=50000 width=200)
            (actual time=10.234..45.678 rows=50000 loops=1)
   Merge Cond: (o.customer_id = c.id)
   ->  Index Scan using idx_orders_customer on orders o
   ->  Index Scan using customers_pkey on customers c

Analysis:
- Both inputs are sorted
- Walks through both in order
- Efficient for large sorted datasets
- No memory for hash table needed
*/
```

## Aggregation and Sorting

### Sort Operations

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders ORDER BY created_at DESC LIMIT 100;

/*
Limit  (cost=1234.56..1234.78 rows=100 width=100)
       (actual time=45.678..45.789 rows=100 loops=1)
   ->  Sort  (cost=1234.56..1345.67 rows=50000 width=100)
             (actual time=45.676..45.700 rows=100 loops=1)
         Sort Key: created_at DESC
         Sort Method: top-N heapsort  Memory: 30kB
         ->  Seq Scan on orders

Good: "Sort Method: top-N heapsort" - efficient for LIMIT
      "Memory: 30kB" - fits in work_mem

Bad pattern:
         Sort Method: external merge  Disk: 45MB
         - Spilled to disk, increase work_mem or add index
*/
```

### HashAggregate vs GroupAggregate

```sql
-- HashAggregate (hash-based grouping)
EXPLAIN ANALYZE
SELECT status, COUNT(*) FROM orders GROUP BY status;

/*
HashAggregate  (cost=1000.00..1000.05 rows=5 width=20)
               (actual time=25.678..25.680 rows=5 loops=1)
   Group Key: status
   Batches: 1  Memory Usage: 24kB
   ->  Seq Scan on orders

Analysis:
- Builds hash table of groups
- Good for few groups
- Memory Usage shows hash table size
*/

-- GroupAggregate (sorted grouping)
EXPLAIN ANALYZE
SELECT customer_id, COUNT(*) FROM orders GROUP BY customer_id;

/*
GroupAggregate  (cost=0.43..2500.00 rows=1000 width=24)
                (actual time=0.034..35.678 rows=1000 loops=1)
   Group Key: customer_id
   ->  Index Only Scan using idx_orders_customer on orders

Analysis:
- Requires sorted input
- Good for many groups or when data is already sorted
- Lower memory usage than hash
*/
```

## Problem Patterns

### Sequential Scan on Large Table

```sql
/*
Problem:
Seq Scan on orders  (cost=0.00..50000.00 rows=1000000 width=100)
                    (actual time=0.012..456.789 rows=1000000 loops=1)
   Filter: (status = 'pending')
   Rows Removed by Filter: 950000

Solution: Add index
CREATE INDEX idx_orders_status ON orders(status);
*/
```

### High Rows Removed by Filter

```sql
/*
Problem:
Index Scan using idx_orders_customer on orders
   Rows Removed by Filter: 99000
   Rows: 1000

Analysis: Index finds rows but filter removes most
Solution: Add composite index or partial index

CREATE INDEX idx_orders_customer_pending
  ON orders(customer_id, created_at)
  WHERE status = 'pending';
*/
```

### Sort Spilling to Disk

```sql
/*
Problem:
Sort  (actual time=1234.567..2345.678 rows=1000000 loops=1)
   Sort Key: created_at
   Sort Method: external merge  Disk: 450MB

Solutions:
1. Increase work_mem: SET work_mem = '512MB';
2. Add index: CREATE INDEX idx_orders_created ON orders(created_at DESC);
3. Use LIMIT if applicable
*/
```

### Nested Loop with Many Loops

```sql
/*
Problem:
Nested Loop  (actual time=0.045..345.678 rows=100000 loops=1)
   ->  Seq Scan on orders o
         (actual time=0.012..12.345 rows=10000 loops=1)
   ->  Index Scan using customers_pkey on customers c
         (actual time=0.002..0.003 rows=10 loops=10000)

Analysis: Inner loop runs 10000 times
Solution: Consider Hash Join or ensure both sides indexed
*/
```

### Estimate vs Actual Mismatch

```sql
/*
Problem:
Seq Scan on users  (cost=0.00..1234.00 rows=1 width=100)
                   (actual time=0.012..45.678 rows=50000 loops=1)
                                        ^^^^^      ^^^^^
                              Estimated 1, actual 50000

Solution: Update statistics
ANALYZE users;

Or for persistent issues:
ALTER TABLE users ALTER COLUMN status SET STATISTICS 1000;
ANALYZE users;
*/
```

## Optimization Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                  EXPLAIN ANALYZE Workflow                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Run EXPLAIN (ANALYZE, BUFFERS)                              │
│         │                                                        │
│         ▼                                                        │
│  2. Identify the slowest node (highest actual time)             │
│         │                                                        │
│         ▼                                                        │
│  3. Check for warning signs:                                    │
│     - Seq Scan on large table                                   │
│     - High "Rows Removed by Filter"                             │
│     - Sort using disk                                           │
│     - Estimate/actual mismatch                                  │
│     - Nested Loop with many loops                               │
│         │                                                        │
│         ▼                                                        │
│  4. Apply appropriate fix:                                      │
│     - Add/modify indexes                                        │
│     - Rewrite query                                             │
│     - Update statistics (ANALYZE)                               │
│     - Adjust work_mem                                           │
│         │                                                        │
│         ▼                                                        │
│  5. Re-run EXPLAIN ANALYZE to verify improvement                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Useful Settings

```sql
-- Show more detail in plans
SET track_io_timing = on;  -- Include I/O timing

-- Adjust planner behavior for testing
SET enable_seqscan = off;   -- Force index usage
SET enable_hashjoin = off;  -- Force different join
SET enable_mergejoin = off;

-- Adjust memory for testing
SET work_mem = '256MB';     -- More memory for sorts
SET effective_cache_size = '4GB';  -- Planner hint

-- Reset to defaults
RESET ALL;
```

## Quick Reference

| Pattern | Meaning | Typical Solution |
|---------|---------|------------------|
| Seq Scan | Full table scan | Add index |
| Rows Removed by Filter | Inefficient filter | Better index |
| Sort Disk | Memory exceeded | Increase work_mem or add index |
| Nested Loop many loops | Expensive join | Add index or force Hash Join |
| Bitmap Heap Scan | Multiple conditions | May be optimal |
| Index Only Scan | Best case | Keep it this way |
| Heap Fetches > 0 | VACUUM needed | Run VACUUM |
| Estimate mismatch | Stale statistics | ANALYZE table |
