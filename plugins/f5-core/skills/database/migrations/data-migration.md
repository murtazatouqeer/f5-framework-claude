---
name: data-migration
description: Data migration techniques and patterns
category: database/migrations
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Data Migration

## Overview

Data migration involves moving, transforming, or restructuring data while
maintaining integrity and minimizing downtime. This guide covers patterns
for safe and efficient data migrations.

## Migration Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Migration Types                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Backfill                                                        │
│  ├── Populate new columns with calculated values                │
│  └── Fill historical data gaps                                  │
│                                                                  │
│  Transform                                                       │
│  ├── Change data format or structure                            │
│  ├── Normalize/denormalize data                                 │
│  └── Apply business logic transformations                       │
│                                                                  │
│  Consolidate                                                     │
│  ├── Merge data from multiple tables                            │
│  └── Deduplicate records                                        │
│                                                                  │
│  Archive                                                         │
│  ├── Move old data to archive tables                            │
│  └── Partition historical data                                  │
│                                                                  │
│  Import                                                          │
│  ├── Load data from external sources                            │
│  └── Migrate between databases                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Backfill Patterns

### Simple Backfill

```sql
-- Backfill a new column with simple calculation
UPDATE products
SET sale_price = price * 0.9
WHERE sale_price IS NULL;

-- Backfill with data from related table
UPDATE orders o
SET customer_name = (
  SELECT c.name FROM customers c WHERE c.id = o.customer_id
)
WHERE customer_name IS NULL;

-- Backfill with default for specific conditions
UPDATE users
SET status = CASE
  WHEN last_login_at IS NULL THEN 'inactive'
  WHEN last_login_at < NOW() - INTERVAL '90 days' THEN 'dormant'
  ELSE 'active'
END
WHERE status IS NULL;
```

### Batched Backfill

```sql
-- Backfill large tables in batches to avoid long locks
CREATE OR REPLACE FUNCTION backfill_in_batches(
  p_batch_size INTEGER DEFAULT 1000,
  p_sleep_ms INTEGER DEFAULT 50
)
RETURNS TABLE(batches INTEGER, total_rows BIGINT) AS $$
DECLARE
  v_batch_count INTEGER := 0;
  v_total_updated BIGINT := 0;
  v_rows_updated INTEGER;
BEGIN
  LOOP
    -- Update a batch using SKIP LOCKED to avoid contention
    WITH batch AS (
      SELECT id FROM users
      WHERE full_name IS NULL
      LIMIT p_batch_size
      FOR UPDATE SKIP LOCKED
    )
    UPDATE users u
    SET full_name = first_name || ' ' || last_name
    FROM batch b
    WHERE u.id = b.id;

    GET DIAGNOSTICS v_rows_updated = ROW_COUNT;
    v_total_updated := v_total_updated + v_rows_updated;
    v_batch_count := v_batch_count + 1;

    -- Exit when no more rows to update
    EXIT WHEN v_rows_updated = 0;

    -- Brief pause to reduce load
    PERFORM pg_sleep(p_sleep_ms / 1000.0);

    -- Log progress
    RAISE NOTICE 'Batch %: % rows (total: %)',
      v_batch_count, v_rows_updated, v_total_updated;
  END LOOP;

  RETURN QUERY SELECT v_batch_count, v_total_updated;
END;
$$ LANGUAGE plpgsql;

-- Execute
SELECT * FROM backfill_in_batches(5000, 100);
```

### Resumable Backfill

```sql
-- Track progress for resumable backfills
CREATE TABLE backfill_progress (
  id SERIAL PRIMARY KEY,
  task_name VARCHAR(100) UNIQUE NOT NULL,
  last_processed_id UUID,
  rows_processed BIGINT DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  status VARCHAR(20) DEFAULT 'running'
);

-- Resumable backfill function
CREATE OR REPLACE FUNCTION resumable_backfill(
  p_task_name VARCHAR,
  p_batch_size INTEGER DEFAULT 1000
)
RETURNS VOID AS $$
DECLARE
  v_last_id UUID;
  v_batch_ids UUID[];
  v_rows_updated INTEGER;
BEGIN
  -- Get or create progress record
  INSERT INTO backfill_progress (task_name)
  VALUES (p_task_name)
  ON CONFLICT (task_name) DO UPDATE SET
    status = 'running',
    updated_at = NOW()
  RETURNING last_processed_id INTO v_last_id;

  LOOP
    -- Get next batch of IDs
    SELECT ARRAY_AGG(id ORDER BY id) INTO v_batch_ids
    FROM (
      SELECT id FROM users
      WHERE (v_last_id IS NULL OR id > v_last_id)
        AND full_name IS NULL
      ORDER BY id
      LIMIT p_batch_size
    ) t;

    EXIT WHEN v_batch_ids IS NULL OR array_length(v_batch_ids, 1) = 0;

    -- Process batch
    UPDATE users
    SET full_name = first_name || ' ' || last_name
    WHERE id = ANY(v_batch_ids);

    GET DIAGNOSTICS v_rows_updated = ROW_COUNT;

    -- Update progress
    v_last_id := v_batch_ids[array_length(v_batch_ids, 1)];
    UPDATE backfill_progress
    SET
      last_processed_id = v_last_id,
      rows_processed = rows_processed + v_rows_updated,
      updated_at = NOW()
    WHERE task_name = p_task_name;

    -- Commit each batch (run as separate transaction if needed)
    COMMIT;
  END LOOP;

  -- Mark as completed
  UPDATE backfill_progress
  SET status = 'completed', completed_at = NOW()
  WHERE task_name = p_task_name;
END;
$$ LANGUAGE plpgsql;
```

## Data Transformation

### Type Conversion

```sql
-- Convert string dates to proper timestamp
UPDATE events
SET occurred_at = TO_TIMESTAMP(occurred_at_string, 'YYYY-MM-DD HH24:MI:SS')
WHERE occurred_at IS NULL AND occurred_at_string IS NOT NULL;

-- Convert price from cents to decimal
UPDATE products
SET price_decimal = price_cents::DECIMAL / 100
WHERE price_decimal IS NULL;

-- Convert JSON string to JSONB
UPDATE settings
SET config_jsonb = config_text::JSONB
WHERE config_jsonb IS NULL AND config_text IS NOT NULL;
```

### Data Normalization

```sql
-- Extract data into separate table
INSERT INTO addresses (user_id, street, city, state, postal_code, country)
SELECT
  id as user_id,
  address_line1 as street,
  address_city as city,
  address_state as state,
  address_zip as postal_code,
  address_country as country
FROM users
WHERE address_line1 IS NOT NULL
ON CONFLICT (user_id) DO NOTHING;

-- After application is updated to use addresses table:
-- ALTER TABLE users
--   DROP COLUMN address_line1,
--   DROP COLUMN address_city,
--   DROP COLUMN address_state,
--   DROP COLUMN address_zip,
--   DROP COLUMN address_country;
```

### Data Denormalization

```sql
-- Pre-compute aggregates for faster queries
UPDATE customers c
SET
  total_orders = (
    SELECT COUNT(*) FROM orders o WHERE o.customer_id = c.id
  ),
  total_spent = (
    SELECT COALESCE(SUM(total), 0) FROM orders o
    WHERE o.customer_id = c.id AND o.status = 'completed'
  ),
  last_order_at = (
    SELECT MAX(created_at) FROM orders o WHERE o.customer_id = c.id
  );

-- Batched version for large tables
WITH customer_stats AS (
  SELECT
    customer_id,
    COUNT(*) as order_count,
    COALESCE(SUM(total), 0) as spent,
    MAX(created_at) as last_order
  FROM orders
  WHERE status = 'completed'
  GROUP BY customer_id
)
UPDATE customers c
SET
  total_orders = cs.order_count,
  total_spent = cs.spent,
  last_order_at = cs.last_order
FROM customer_stats cs
WHERE c.id = cs.customer_id;
```

## Data Consolidation

### Merge Tables

```sql
-- Merge users from legacy system
INSERT INTO users (
  id, email, name, created_at, source
)
SELECT
  gen_random_uuid(),
  email,
  COALESCE(full_name, first_name || ' ' || last_name),
  COALESCE(registration_date, NOW()),
  'legacy_system'
FROM legacy_users lu
WHERE NOT EXISTS (
  SELECT 1 FROM users u WHERE u.email = lu.email
)
ON CONFLICT (email) DO UPDATE SET
  name = COALESCE(users.name, EXCLUDED.name),
  source = 'merged';
```

### Deduplicate Records

```sql
-- Find duplicates
SELECT email, COUNT(*) as count
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- Merge duplicates keeping the oldest record
WITH duplicates AS (
  SELECT
    email,
    MIN(id) as keep_id,
    ARRAY_AGG(id) FILTER (WHERE id != MIN(id)) as delete_ids
  FROM users
  GROUP BY email
  HAVING COUNT(*) > 1
)
-- First, merge data from duplicates to the kept record
UPDATE users u
SET
  phone = COALESCE(u.phone, (
    SELECT phone FROM users WHERE id = ANY(d.delete_ids) AND phone IS NOT NULL LIMIT 1
  )),
  last_login_at = GREATEST(u.last_login_at, (
    SELECT MAX(last_login_at) FROM users WHERE id = ANY(d.delete_ids)
  ))
FROM duplicates d
WHERE u.id = d.keep_id;

-- Then update foreign keys
WITH duplicates AS (
  SELECT
    email,
    MIN(id) as keep_id,
    ARRAY_AGG(id) FILTER (WHERE id != MIN(id)) as delete_ids
  FROM users
  GROUP BY email
  HAVING COUNT(*) > 1
)
UPDATE orders o
SET user_id = d.keep_id
FROM duplicates d
WHERE o.user_id = ANY(d.delete_ids);

-- Finally delete duplicates
WITH duplicates AS (
  SELECT
    email,
    MIN(id) as keep_id,
    ARRAY_AGG(id) FILTER (WHERE id != MIN(id)) as delete_ids
  FROM users
  GROUP BY email
  HAVING COUNT(*) > 1
)
DELETE FROM users
WHERE id IN (SELECT unnest(delete_ids) FROM duplicates);
```

## Data Archival

### Archive Old Records

```sql
-- Create archive table with same structure
CREATE TABLE orders_archive (LIKE orders INCLUDING ALL);

-- Move old records to archive
WITH moved AS (
  DELETE FROM orders
  WHERE created_at < NOW() - INTERVAL '2 years'
  RETURNING *
)
INSERT INTO orders_archive SELECT * FROM moved;

-- Create function for automated archival
CREATE OR REPLACE FUNCTION archive_old_orders(
  p_cutoff_interval INTERVAL DEFAULT '2 years',
  p_batch_size INTEGER DEFAULT 10000
)
RETURNS BIGINT AS $$
DECLARE
  v_total_archived BIGINT := 0;
  v_batch_archived INTEGER;
BEGIN
  LOOP
    WITH batch AS (
      SELECT id FROM orders
      WHERE created_at < NOW() - p_cutoff_interval
      LIMIT p_batch_size
      FOR UPDATE SKIP LOCKED
    ),
    moved AS (
      DELETE FROM orders o
      USING batch b
      WHERE o.id = b.id
      RETURNING o.*
    )
    INSERT INTO orders_archive SELECT * FROM moved;

    GET DIAGNOSTICS v_batch_archived = ROW_COUNT;
    v_total_archived := v_total_archived + v_batch_archived;

    EXIT WHEN v_batch_archived = 0;

    RAISE NOTICE 'Archived % orders (total: %)', v_batch_archived, v_total_archived;
  END LOOP;

  RETURN v_total_archived;
END;
$$ LANGUAGE plpgsql;

-- Run archival
SELECT archive_old_orders('2 years', 5000);
```

### Partitioned Archival

```sql
-- Convert to partitioned table for automatic archival
-- Step 1: Create partitioned table
CREATE TABLE orders_partitioned (
  id UUID NOT NULL,
  customer_id UUID NOT NULL,
  total DECIMAL(12, 2) NOT NULL,
  status VARCHAR(20) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Step 2: Create partitions
CREATE TABLE orders_2024_q1 PARTITION OF orders_partitioned
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders_partitioned
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

CREATE TABLE orders_2024_q3 PARTITION OF orders_partitioned
  FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');

CREATE TABLE orders_2024_q4 PARTITION OF orders_partitioned
  FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

-- Step 3: Migrate data
INSERT INTO orders_partitioned
SELECT id, customer_id, total, status, created_at
FROM orders;

-- Step 4: Archive old partitions (detach and move)
ALTER TABLE orders_partitioned
  DETACH PARTITION orders_2022_q1;

ALTER TABLE orders_2022_q1 RENAME TO orders_archive_2022_q1;
```

## External Data Import

### CSV Import

```sql
-- Create staging table
CREATE TEMP TABLE import_staging (
  external_id VARCHAR(100),
  name VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(50),
  created_date VARCHAR(50),
  raw_data JSONB
);

-- Import from CSV (PostgreSQL)
COPY import_staging (external_id, name, email, phone, created_date)
FROM '/path/to/data.csv'
WITH (FORMAT CSV, HEADER true, DELIMITER ',');

-- Or use \copy in psql for client-side file
-- \copy import_staging FROM 'data.csv' WITH CSV HEADER;

-- Transform and insert with validation
INSERT INTO customers (id, name, email, phone, created_at, source)
SELECT
  gen_random_uuid(),
  TRIM(name),
  LOWER(TRIM(email)),
  REGEXP_REPLACE(phone, '[^0-9+]', '', 'g'),
  TO_TIMESTAMP(created_date, 'MM/DD/YYYY')::TIMESTAMPTZ,
  'csv_import'
FROM import_staging
WHERE email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'
ON CONFLICT (email) DO UPDATE SET
  phone = COALESCE(EXCLUDED.phone, customers.phone);

-- Log rejected records
INSERT INTO import_errors (source, data, error_reason)
SELECT
  'csv_import',
  to_jsonb(s),
  'Invalid email format'
FROM import_staging s
WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
```

### API Data Import

```typescript
// TypeScript example for API-based data import
interface ExternalUser {
  id: string;
  email: string;
  name: string;
  createdAt: string;
}

async function importUsersFromAPI(
  batchSize: number = 100,
  sleepMs: number = 1000
): Promise<{ imported: number; errors: number }> {
  let cursor: string | null = null;
  let imported = 0;
  let errors = 0;

  while (true) {
    // Fetch batch from external API
    const response = await fetch(
      `https://api.external.com/users?limit=${batchSize}&cursor=${cursor}`
    );
    const data = await response.json();

    if (data.users.length === 0) break;

    // Process batch
    for (const user of data.users as ExternalUser[]) {
      try {
        await prisma.user.upsert({
          where: { externalId: user.id },
          update: {
            name: user.name,
            email: user.email.toLowerCase(),
            updatedAt: new Date(),
          },
          create: {
            externalId: user.id,
            email: user.email.toLowerCase(),
            name: user.name,
            source: 'api_import',
            createdAt: new Date(user.createdAt),
          },
        });
        imported++;
      } catch (e) {
        await prisma.importError.create({
          data: {
            source: 'api_import',
            externalId: user.id,
            errorMessage: e.message,
            rawData: JSON.stringify(user),
          },
        });
        errors++;
      }
    }

    cursor = data.nextCursor;
    if (!cursor) break;

    // Rate limiting
    await new Promise(resolve => setTimeout(resolve, sleepMs));

    console.log(`Imported ${imported} users, ${errors} errors`);
  }

  return { imported, errors };
}
```

## Data Validation

### Pre-Migration Validation

```sql
-- Validate data before migration
DO $$
DECLARE
  v_invalid_count INTEGER;
BEGIN
  -- Check for invalid emails
  SELECT COUNT(*) INTO v_invalid_count
  FROM users
  WHERE email !~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';

  IF v_invalid_count > 0 THEN
    RAISE WARNING 'Found % users with invalid emails', v_invalid_count;
  END IF;

  -- Check for orphaned records
  SELECT COUNT(*) INTO v_invalid_count
  FROM orders o
  LEFT JOIN customers c ON o.customer_id = c.id
  WHERE c.id IS NULL;

  IF v_invalid_count > 0 THEN
    RAISE EXCEPTION 'Found % orphaned orders - migration cannot proceed', v_invalid_count;
  END IF;

  -- Check for duplicate keys
  SELECT COUNT(*) INTO v_invalid_count
  FROM (
    SELECT email, COUNT(*) FROM users GROUP BY email HAVING COUNT(*) > 1
  ) t;

  IF v_invalid_count > 0 THEN
    RAISE EXCEPTION 'Found % duplicate emails - deduplicate before migration', v_invalid_count;
  END IF;

  RAISE NOTICE 'Pre-migration validation passed';
END $$;
```

### Post-Migration Validation

```sql
-- Validate data after migration
CREATE OR REPLACE FUNCTION validate_migration()
RETURNS TABLE(check_name TEXT, status TEXT, details TEXT) AS $$
BEGIN
  -- Check row counts match
  RETURN QUERY
  SELECT
    'row_count_match'::TEXT,
    CASE WHEN (SELECT COUNT(*) FROM users) = (SELECT COUNT(*) FROM users_new)
      THEN 'PASS' ELSE 'FAIL'
    END,
    format('Old: %s, New: %s',
      (SELECT COUNT(*) FROM users),
      (SELECT COUNT(*) FROM users_new)
    );

  -- Check no NULL values in required fields
  RETURN QUERY
  SELECT
    'required_fields_not_null'::TEXT,
    CASE WHEN NOT EXISTS (
      SELECT 1 FROM users_new WHERE email IS NULL OR name IS NULL
    ) THEN 'PASS' ELSE 'FAIL' END,
    COALESCE(
      (SELECT format('%s rows with NULL required fields',
        COUNT(*)) FROM users_new WHERE email IS NULL OR name IS NULL),
      'All required fields populated'
    );

  -- Check referential integrity
  RETURN QUERY
  SELECT
    'referential_integrity'::TEXT,
    CASE WHEN NOT EXISTS (
      SELECT 1 FROM orders_new o
      LEFT JOIN users_new u ON o.user_id = u.id
      WHERE u.id IS NULL
    ) THEN 'PASS' ELSE 'FAIL' END,
    'Foreign key references validated';

  -- Check data transformations
  RETURN QUERY
  SELECT
    'email_lowercase'::TEXT,
    CASE WHEN NOT EXISTS (
      SELECT 1 FROM users_new WHERE email != LOWER(email)
    ) THEN 'PASS' ELSE 'FAIL' END,
    'All emails are lowercase';

  -- Check computed values
  RETURN QUERY
  SELECT
    'computed_values_correct'::TEXT,
    CASE WHEN NOT EXISTS (
      SELECT 1 FROM orders_new
      WHERE total != subtotal + tax - discount
    ) THEN 'PASS' ELSE 'FAIL' END,
    'Order totals computed correctly';
END;
$$ LANGUAGE plpgsql;

-- Run validation
SELECT * FROM validate_migration();
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Data Migration Best Practices                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Always Backup First                                          │
│     - Full backup before migration                              │
│     - Point-in-time recovery enabled                            │
│                                                                  │
│  2. Test on Production-Like Data                                │
│     - Use anonymized production data                            │
│     - Test with full data volume                                │
│                                                                  │
│  3. Make Migrations Idempotent                                  │
│     - Can be run multiple times safely                          │
│     - Use ON CONFLICT / UPSERT patterns                         │
│                                                                  │
│  4. Process in Batches                                          │
│     - Avoid long-running transactions                           │
│     - Use SKIP LOCKED for concurrent safety                     │
│                                                                  │
│  5. Track Progress                                               │
│     - Resumable from any point                                  │
│     - Log progress for monitoring                               │
│                                                                  │
│  6. Validate Before and After                                   │
│     - Pre-migration data quality checks                         │
│     - Post-migration integrity verification                     │
│                                                                  │
│  7. Plan for Rollback                                           │
│     - Keep original data until verified                         │
│     - Document rollback procedures                              │
│                                                                  │
│  8. Monitor During Execution                                    │
│     - Watch for lock contention                                 │
│     - Monitor replication lag                                   │
│     - Track disk space usage                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Migration Checklist

| Phase | Task | Status |
|-------|------|--------|
| **Plan** | Document data mapping | ☐ |
| | Identify transformation rules | ☐ |
| | Estimate migration time | ☐ |
| | Plan rollback procedure | ☐ |
| **Prepare** | Create staging tables | ☐ |
| | Write migration scripts | ☐ |
| | Create validation queries | ☐ |
| | Full backup completed | ☐ |
| **Test** | Test on staging environment | ☐ |
| | Validate data integrity | ☐ |
| | Test rollback procedure | ☐ |
| | Measure execution time | ☐ |
| **Execute** | Run pre-migration validation | ☐ |
| | Execute migration | ☐ |
| | Monitor progress | ☐ |
| | Run post-migration validation | ☐ |
| **Verify** | Compare row counts | ☐ |
| | Verify computed values | ☐ |
| | Check referential integrity | ☐ |
| | Application testing | ☐ |
| **Cleanup** | Remove staging tables | ☐ |
| | Archive old data if needed | ☐ |
| | Document migration | ☐ |
