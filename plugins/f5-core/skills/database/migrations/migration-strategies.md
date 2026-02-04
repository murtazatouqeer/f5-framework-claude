---
name: migration-strategies
description: Database migration patterns and strategies
category: database/migrations
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Migration Strategies

## Overview

Database migrations are version-controlled changes to your database schema.
Good migration strategies ensure safe, reversible, and traceable changes
across environments.

## Migration Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    Migration Categories                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Schema Migrations                                               │
│  ├── DDL changes (CREATE, ALTER, DROP)                          │
│  ├── Index modifications                                        │
│  └── Constraint changes                                         │
│                                                                  │
│  Data Migrations                                                 │
│  ├── Data transformation                                        │
│  ├── Data backfill                                              │
│  └── Data cleanup                                               │
│                                                                  │
│  Hybrid Migrations                                               │
│  ├── Schema + data changes                                      │
│  ├── Multi-step transformations                                 │
│  └── Complex refactoring                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Migration File Structure

### Naming Convention

```
migrations/
├── 20240115_001_create_users_table.sql
├── 20240115_002_add_email_index.sql
├── 20240116_001_create_orders_table.sql
├── 20240120_001_add_user_status_column.sql
└── 20240120_002_backfill_user_status.sql

Format: YYYYMMDD_NNN_description.sql
- YYYYMMDD: Date of creation
- NNN: Sequential number for same-day migrations
- description: Snake_case description
```

### Migration File Template

```sql
-- Migration: 20240115_001_create_users_table
-- Description: Create users table with authentication fields
-- Author: developer@example.com
-- Created: 2024-01-15

-- Up Migration
BEGIN;

CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);

COMMIT;

-- Down Migration (Rollback)
-- BEGIN;
-- DROP TABLE IF EXISTS users;
-- COMMIT;
```

## Version Control Strategies

### Sequential Migrations

```
┌─────────────────────────────────────────────────────────────────┐
│                  Sequential Migration Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  v1 ──► v2 ──► v3 ──► v4 ──► v5 (current)                      │
│                                                                  │
│  Migration Table:                                                │
│  ┌──────────────────────────────────────────────┐               │
│  │ version │ applied_at          │ status      │               │
│  ├─────────┼─────────────────────┼─────────────┤               │
│  │ 001     │ 2024-01-15 10:00:00 │ completed   │               │
│  │ 002     │ 2024-01-15 10:00:05 │ completed   │               │
│  │ 003     │ 2024-01-16 14:30:00 │ completed   │               │
│  │ 004     │ 2024-01-20 09:15:00 │ completed   │               │
│  │ 005     │ 2024-01-20 09:15:30 │ completed   │               │
│  └──────────────────────────────────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Migration Tracking Table

```sql
-- Create migration tracking table
CREATE TABLE schema_migrations (
  id SERIAL PRIMARY KEY,
  version VARCHAR(100) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  applied_at TIMESTAMPTZ DEFAULT NOW(),
  execution_time_ms INTEGER,
  checksum VARCHAR(64),
  status VARCHAR(20) DEFAULT 'completed'
);

CREATE INDEX idx_migrations_version ON schema_migrations(version);

-- Record a migration
INSERT INTO schema_migrations (version, name, execution_time_ms, checksum)
VALUES ('20240115_001', 'create_users_table', 45, 'sha256hash...');

-- Check applied migrations
SELECT version, name, applied_at
FROM schema_migrations
ORDER BY version;

-- Check if migration was applied
SELECT EXISTS (
  SELECT 1 FROM schema_migrations WHERE version = '20240115_001'
);
```

## Safe Migration Patterns

### Adding Columns

```sql
-- Safe: Add nullable column
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Safe: Add column with default (PostgreSQL 11+)
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT false;

-- Unsafe: Add NOT NULL without default
-- ALTER TABLE users ADD COLUMN required_field VARCHAR(50) NOT NULL;

-- Safe pattern for NOT NULL column:
-- Step 1: Add nullable
ALTER TABLE users ADD COLUMN required_field VARCHAR(50);
-- Step 2: Backfill data
UPDATE users SET required_field = 'default_value' WHERE required_field IS NULL;
-- Step 3: Add NOT NULL constraint
ALTER TABLE users ALTER COLUMN required_field SET NOT NULL;
```

### Removing Columns

```sql
-- Safe: Multi-step column removal

-- Step 1: Stop writing to the column (application change)
-- Step 2: Deploy application changes
-- Step 3: Add column to ignore list or mark deprecated

-- Step 4: Remove column after deployment is stable
ALTER TABLE users DROP COLUMN deprecated_field;

-- For immediate safety, rename first:
ALTER TABLE users RENAME COLUMN old_field TO _deprecated_old_field;
-- Later:
ALTER TABLE users DROP COLUMN _deprecated_old_field;
```

### Renaming Columns

```sql
-- Unsafe: Direct rename breaks existing queries
-- ALTER TABLE users RENAME COLUMN name TO full_name;

-- Safe: Multi-step rename
-- Step 1: Add new column
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Step 2: Backfill data
UPDATE users SET full_name = name WHERE full_name IS NULL;

-- Step 3: Add trigger to keep in sync during transition
CREATE OR REPLACE FUNCTION sync_user_name()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' OR NEW.name IS DISTINCT FROM OLD.name THEN
    NEW.full_name = COALESCE(NEW.full_name, NEW.name);
  END IF;
  IF TG_OP = 'INSERT' OR NEW.full_name IS DISTINCT FROM OLD.full_name THEN
    NEW.name = COALESCE(NEW.name, NEW.full_name);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_name_sync
  BEFORE INSERT OR UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION sync_user_name();

-- Step 4: Update application to use new column
-- Step 5: Remove trigger and old column
DROP TRIGGER user_name_sync ON users;
ALTER TABLE users DROP COLUMN name;
```

### Modifying Column Types

```sql
-- Safe: Widening conversion
ALTER TABLE products ALTER COLUMN description TYPE TEXT;
ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(500);

-- Unsafe: Narrowing conversion (may lose data)
-- ALTER TABLE users ALTER COLUMN name TYPE VARCHAR(50);

-- Safe pattern for type change:
-- Step 1: Add new column with new type
ALTER TABLE products ADD COLUMN price_decimal DECIMAL(12, 4);

-- Step 2: Backfill with conversion
UPDATE products SET price_decimal = price::DECIMAL(12, 4);

-- Step 3: Sync via trigger during transition
-- Step 4: Swap columns
ALTER TABLE products DROP COLUMN price;
ALTER TABLE products RENAME COLUMN price_decimal TO price;
```

## Index Migrations

### Creating Indexes Safely

```sql
-- Unsafe: Blocks writes on large tables
-- CREATE INDEX idx_orders_user ON orders(user_id);

-- Safe: Create index concurrently (PostgreSQL)
CREATE INDEX CONCURRENTLY idx_orders_user ON orders(user_id);

-- Note: CONCURRENTLY cannot be in a transaction
-- Handle in migration framework:
-- @disable-transaction
CREATE INDEX CONCURRENTLY idx_orders_created ON orders(created_at);
```

### Dropping Indexes Safely

```sql
-- Safe: Drop index concurrently
DROP INDEX CONCURRENTLY IF EXISTS idx_old_index;

-- Verify index isn't used before dropping
SELECT
  indexrelname,
  idx_scan,
  idx_tup_read,
  idx_tup_fetch
FROM pg_stat_user_indexes
WHERE indexrelname = 'idx_old_index';
```

### Index Replacement

```sql
-- Replace index without downtime
-- Step 1: Create new index concurrently
CREATE INDEX CONCURRENTLY idx_users_email_new ON users(email) WHERE status = 'active';

-- Step 2: Verify new index is valid
SELECT indexname, indisvalid
FROM pg_indexes
JOIN pg_index ON indexname::regclass = indexrelid
WHERE indexname = 'idx_users_email_new';

-- Step 3: Drop old index concurrently
DROP INDEX CONCURRENTLY idx_users_email;

-- Step 4: Rename new index
ALTER INDEX idx_users_email_new RENAME TO idx_users_email;
```

## Constraint Migrations

### Adding Constraints

```sql
-- Unsafe: Adding constraint validates all rows (locks table)
-- ALTER TABLE orders ADD CONSTRAINT fk_orders_user
--   FOREIGN KEY (user_id) REFERENCES users(id);

-- Safe: Add constraint without validation, then validate separately
ALTER TABLE orders ADD CONSTRAINT fk_orders_user
  FOREIGN KEY (user_id) REFERENCES users(id)
  NOT VALID;

-- Validate in separate transaction (allows concurrent access)
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_user;
```

### Adding CHECK Constraints

```sql
-- Safe: Add CHECK constraint without initial validation
ALTER TABLE products ADD CONSTRAINT chk_products_price
  CHECK (price >= 0) NOT VALID;

-- Validate separately
ALTER TABLE products VALIDATE CONSTRAINT chk_products_price;
```

### Adding NOT NULL Constraints

```sql
-- Safe: Use CHECK constraint instead (PostgreSQL)
ALTER TABLE users ADD CONSTRAINT chk_users_email_not_null
  CHECK (email IS NOT NULL) NOT VALID;

ALTER TABLE users VALIDATE CONSTRAINT chk_users_email_not_null;

-- Then convert to actual NOT NULL
ALTER TABLE users ALTER COLUMN email SET NOT NULL;
DROP CONSTRAINT chk_users_email_not_null;
```

## Rollback Strategies

### Automatic Rollback Script

```sql
-- Up migration
BEGIN;

CREATE TABLE new_feature (
  id UUID PRIMARY KEY,
  name VARCHAR(255)
);

-- Store rollback script
INSERT INTO migration_rollbacks (version, rollback_script)
VALUES ('20240120_001', 'DROP TABLE IF EXISTS new_feature;');

COMMIT;

-- Rollback procedure
CREATE OR REPLACE FUNCTION rollback_migration(target_version VARCHAR)
RETURNS VOID AS $$
DECLARE
  rollback_sql TEXT;
BEGIN
  SELECT rollback_script INTO rollback_sql
  FROM migration_rollbacks
  WHERE version = target_version;

  IF rollback_sql IS NOT NULL THEN
    EXECUTE rollback_sql;
    DELETE FROM schema_migrations WHERE version = target_version;
    DELETE FROM migration_rollbacks WHERE version = target_version;
  END IF;
END;
$$ LANGUAGE plpgsql;
```

### Manual Rollback Patterns

```sql
-- Migration with explicit up/down
-- migrations/20240120_001_add_user_preferences.sql

-- === UP ===
CREATE TABLE user_preferences (
  user_id UUID PRIMARY KEY REFERENCES users(id),
  theme VARCHAR(20) DEFAULT 'light',
  notifications_enabled BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- === DOWN ===
-- Run manually if rollback needed:
-- DROP TABLE IF EXISTS user_preferences;
```

## Migration Testing

### Test Migration Script

```sql
-- Test migration in transaction that rolls back
BEGIN;

-- Run migration
CREATE TABLE test_table (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100)
);

-- Verify migration worked
DO $$
BEGIN
  -- Check table exists
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_name = 'test_table'
  ) THEN
    RAISE EXCEPTION 'Migration failed: table not created';
  END IF;

  -- Check columns exist
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'test_table' AND column_name = 'name'
  ) THEN
    RAISE EXCEPTION 'Migration failed: column not created';
  END IF;

  RAISE NOTICE 'Migration test passed';
END $$;

-- Rollback to clean up
ROLLBACK;
```

### Pre-Migration Validation

```sql
-- Check for potential issues before migration
DO $$
DECLARE
  row_count BIGINT;
  null_count BIGINT;
BEGIN
  -- Check table size
  SELECT COUNT(*) INTO row_count FROM users;
  IF row_count > 1000000 THEN
    RAISE WARNING 'Large table: % rows. Migration may take time.', row_count;
  END IF;

  -- Check for NULLs before adding NOT NULL
  SELECT COUNT(*) INTO null_count FROM users WHERE email IS NULL;
  IF null_count > 0 THEN
    RAISE EXCEPTION 'Cannot add NOT NULL: % rows have NULL email', null_count;
  END IF;

  RAISE NOTICE 'Pre-migration checks passed';
END $$;
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                 Migration Best Practices                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. One Change Per Migration                                    │
│     - Single responsibility principle                           │
│     - Easier to rollback individual changes                     │
│                                                                  │
│  2. Always Write Rollback Scripts                               │
│     - Test rollbacks in staging                                 │
│     - Verify data isn't lost on rollback                        │
│                                                                  │
│  3. Test in Production-Like Environment                         │
│     - Use production data volume                                │
│     - Test with realistic load                                  │
│                                                                  │
│  4. Use Transactions Where Possible                             │
│     - Ensure atomicity                                          │
│     - Note: Some operations can't be in transactions            │
│                                                                  │
│  5. Never Edit Applied Migrations                               │
│     - Create new migration for fixes                            │
│     - Maintain migration history integrity                      │
│                                                                  │
│  6. Include Checksums                                           │
│     - Detect unauthorized changes                               │
│     - Ensure consistency across environments                    │
│                                                                  │
│  7. Document Breaking Changes                                   │
│     - Note required application changes                         │
│     - Coordinate with deployment process                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Migration Execution Order

```
┌─────────────────────────────────────────────────────────────────┐
│                  Migration Deployment Flow                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Pre-Deployment                                               │
│     ├── Backup database                                         │
│     ├── Run pre-migration checks                                │
│     └── Verify rollback procedures                              │
│                                                                  │
│  2. Schema Migration                                             │
│     ├── Add new tables/columns                                  │
│     ├── Create indexes CONCURRENTLY                             │
│     └── Add constraints NOT VALID                               │
│                                                                  │
│  3. Application Deployment                                       │
│     ├── Deploy new application code                             │
│     └── Application handles old + new schema                    │
│                                                                  │
│  4. Data Migration                                               │
│     ├── Backfill new columns                                    │
│     ├── Validate constraints                                    │
│     └── Transform data if needed                                │
│                                                                  │
│  5. Cleanup                                                      │
│     ├── Remove deprecated columns                               │
│     ├── Drop old indexes                                        │
│     └── Update constraints to final state                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
