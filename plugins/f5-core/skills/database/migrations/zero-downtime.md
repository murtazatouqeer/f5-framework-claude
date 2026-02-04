---
name: zero-downtime-migrations
description: Zero-downtime database migration techniques
category: database/migrations
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Zero-Downtime Migrations

## Overview

Zero-downtime migrations allow database changes without service interruption.
They require careful planning, backward-compatible changes, and coordination
between application and database deployments.

## Core Principles

```
┌─────────────────────────────────────────────────────────────────┐
│              Zero-Downtime Migration Principles                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Backward Compatibility                                       │
│     - New schema works with old application                     │
│     - Old schema works with new application                     │
│                                                                  │
│  2. Incremental Changes                                          │
│     - Small, reversible steps                                   │
│     - Each step is independently deployable                     │
│                                                                  │
│  3. Expansion/Contraction Pattern                               │
│     - Expand: Add new structures                                │
│     - Migrate: Move data, update code                           │
│     - Contract: Remove old structures                           │
│                                                                  │
│  4. Non-Blocking Operations                                      │
│     - Avoid table locks                                         │
│     - Use CONCURRENTLY for indexes                              │
│     - Validate constraints separately                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Expansion/Contraction Pattern

### Phase Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  Expand/Contract Timeline                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Time ─────────────────────────────────────────────────────────► │
│                                                                  │
│  EXPAND PHASE                                                    │
│  ├── Add new column/table                                       │
│  ├── Create sync triggers                                       │
│  └── Deploy app that writes to both                             │
│                                                                  │
│  MIGRATE PHASE                                                   │
│  ├── Backfill historical data                                   │
│  ├── Verify data integrity                                      │
│  └── Deploy app that reads from new                             │
│                                                                  │
│  CONTRACT PHASE                                                  │
│  ├── Deploy app that only uses new                              │
│  ├── Remove sync triggers                                       │
│  └── Drop old column/table                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Column Rename

```sql
-- Goal: Rename users.name to users.full_name

-- ┌────────────────────────────────────────┐
-- │ PHASE 1: EXPAND                        │
-- └────────────────────────────────────────┘

-- Step 1.1: Add new column
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Step 1.2: Create sync trigger
CREATE OR REPLACE FUNCTION sync_user_names()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    NEW.full_name = COALESCE(NEW.full_name, NEW.name);
    NEW.name = COALESCE(NEW.name, NEW.full_name);
  ELSIF TG_OP = 'UPDATE' THEN
    IF NEW.name IS DISTINCT FROM OLD.name THEN
      NEW.full_name = NEW.name;
    ELSIF NEW.full_name IS DISTINCT FROM OLD.full_name THEN
      NEW.name = NEW.full_name;
    END IF;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_name_sync
  BEFORE INSERT OR UPDATE ON users
  FOR EACH ROW EXECUTE FUNCTION sync_user_names();

-- ┌────────────────────────────────────────┐
-- │ PHASE 2: MIGRATE                       │
-- └────────────────────────────────────────┘

-- Step 2.1: Backfill existing data
UPDATE users
SET full_name = name
WHERE full_name IS NULL;

-- Step 2.2: Verify data integrity
SELECT COUNT(*) FROM users WHERE full_name IS NULL;
-- Should return 0

SELECT COUNT(*) FROM users WHERE name != full_name;
-- Should return 0

-- Deploy application changes:
-- - Update reads to use full_name
-- - Update writes to use full_name

-- ┌────────────────────────────────────────┐
-- │ PHASE 3: CONTRACT                      │
-- └────────────────────────────────────────┘

-- Step 3.1: Remove sync trigger
DROP TRIGGER users_name_sync ON users;
DROP FUNCTION sync_user_names();

-- Step 3.2: Drop old column
ALTER TABLE users DROP COLUMN name;

-- Step 3.3: Add NOT NULL if needed
ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;
```

## Adding Non-Nullable Column

### Safe Pattern

```sql
-- Goal: Add required 'status' column to users table

-- ┌────────────────────────────────────────┐
-- │ STEP 1: Add nullable column            │
-- └────────────────────────────────────────┘
ALTER TABLE users ADD COLUMN status VARCHAR(20);

-- ┌────────────────────────────────────────┐
-- │ STEP 2: Set default for new rows       │
-- └────────────────────────────────────────┘
ALTER TABLE users ALTER COLUMN status SET DEFAULT 'active';

-- ┌────────────────────────────────────────┐
-- │ STEP 3: Backfill in batches            │
-- └────────────────────────────────────────┘

-- Backfill function for large tables
CREATE OR REPLACE FUNCTION backfill_user_status(
  batch_size INTEGER DEFAULT 1000,
  sleep_ms INTEGER DEFAULT 100
)
RETURNS INTEGER AS $$
DECLARE
  updated_count INTEGER := 0;
  batch_updated INTEGER;
BEGIN
  LOOP
    UPDATE users
    SET status = 'active'
    WHERE id IN (
      SELECT id FROM users
      WHERE status IS NULL
      LIMIT batch_size
      FOR UPDATE SKIP LOCKED
    );

    GET DIAGNOSTICS batch_updated = ROW_COUNT;
    updated_count := updated_count + batch_updated;

    EXIT WHEN batch_updated = 0;

    -- Sleep to reduce load
    PERFORM pg_sleep(sleep_ms / 1000.0);

    RAISE NOTICE 'Backfilled % rows (total: %)', batch_updated, updated_count;
  END LOOP;

  RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

-- Run backfill
SELECT backfill_user_status(1000, 100);

-- ┌────────────────────────────────────────┐
-- │ STEP 4: Add NOT NULL constraint        │
-- └────────────────────────────────────────┘

-- First add CHECK constraint (validated separately)
ALTER TABLE users ADD CONSTRAINT chk_status_not_null
  CHECK (status IS NOT NULL) NOT VALID;

-- Validate (allows concurrent access)
ALTER TABLE users VALIDATE CONSTRAINT chk_status_not_null;

-- Convert to actual NOT NULL
ALTER TABLE users ALTER COLUMN status SET NOT NULL;

-- Drop redundant CHECK constraint
ALTER TABLE users DROP CONSTRAINT chk_status_not_null;
```

## Table Restructuring

### Split Table Pattern

```sql
-- Goal: Split users table into users and user_profiles

-- ┌────────────────────────────────────────┐
-- │ PHASE 1: CREATE NEW STRUCTURE          │
-- └────────────────────────────────────────┘

CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY,
  bio TEXT,
  avatar_url VARCHAR(500),
  website VARCHAR(255),
  location VARCHAR(100),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ┌────────────────────────────────────────┐
-- │ PHASE 2: SETUP DUAL-WRITE              │
-- └────────────────────────────────────────┘

-- Trigger to sync writes to both tables
CREATE OR REPLACE FUNCTION sync_user_to_profile()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO user_profiles (user_id, bio, avatar_url, website, location)
    VALUES (NEW.id, NEW.bio, NEW.avatar_url, NEW.website, NEW.location)
    ON CONFLICT (user_id) DO UPDATE SET
      bio = EXCLUDED.bio,
      avatar_url = EXCLUDED.avatar_url,
      website = EXCLUDED.website,
      location = EXCLUDED.location,
      updated_at = NOW();
  ELSIF TG_OP = 'UPDATE' THEN
    UPDATE user_profiles SET
      bio = NEW.bio,
      avatar_url = NEW.avatar_url,
      website = NEW.website,
      location = NEW.location,
      updated_at = NOW()
    WHERE user_id = NEW.id;
  ELSIF TG_OP = 'DELETE' THEN
    DELETE FROM user_profiles WHERE user_id = OLD.id;
  END IF;
  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_profile_sync
  AFTER INSERT OR UPDATE OR DELETE ON users
  FOR EACH ROW EXECUTE FUNCTION sync_user_to_profile();

-- ┌────────────────────────────────────────┐
-- │ PHASE 3: MIGRATE DATA                  │
-- └────────────────────────────────────────┘

INSERT INTO user_profiles (user_id, bio, avatar_url, website, location)
SELECT id, bio, avatar_url, website, location
FROM users
WHERE id NOT IN (SELECT user_id FROM user_profiles)
ON CONFLICT (user_id) DO NOTHING;

-- ┌────────────────────────────────────────┐
-- │ PHASE 4: UPDATE APPLICATION            │
-- └────────────────────────────────────────┘

-- Create view for backward compatibility during transition
CREATE OR REPLACE VIEW users_with_profile AS
SELECT
  u.id, u.email, u.name, u.created_at,
  p.bio, p.avatar_url, p.website, p.location
FROM users u
LEFT JOIN user_profiles p ON u.id = p.user_id;

-- ┌────────────────────────────────────────┐
-- │ PHASE 5: CLEANUP                       │
-- └────────────────────────────────────────┘

-- After app fully migrated:
DROP TRIGGER users_profile_sync ON users;
DROP FUNCTION sync_user_to_profile();

ALTER TABLE users
  DROP COLUMN bio,
  DROP COLUMN avatar_url,
  DROP COLUMN website,
  DROP COLUMN location;

DROP VIEW users_with_profile;
```

## Index Changes

### Replace Index Without Downtime

```sql
-- Goal: Add partial index to replace full index

-- ┌────────────────────────────────────────┐
-- │ STEP 1: Create new index concurrently  │
-- └────────────────────────────────────────┘

-- New partial index (more efficient)
CREATE INDEX CONCURRENTLY idx_orders_user_active_new
  ON orders(user_id, created_at DESC)
  WHERE status = 'active';

-- ┌────────────────────────────────────────┐
-- │ STEP 2: Verify new index is valid      │
-- └────────────────────────────────────────┘

SELECT indexname, indisvalid
FROM pg_indexes
JOIN pg_index ON indexname::regclass = indexrelid
WHERE indexname = 'idx_orders_user_active_new';

-- Check query uses new index
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM orders
WHERE user_id = 'user-uuid' AND status = 'active'
ORDER BY created_at DESC
LIMIT 10;

-- ┌────────────────────────────────────────┐
-- │ STEP 3: Drop old index concurrently    │
-- └────────────────────────────────────────┘

DROP INDEX CONCURRENTLY idx_orders_user_old;

-- ┌────────────────────────────────────────┐
-- │ STEP 4: Rename new index               │
-- └────────────────────────────────────────┘

ALTER INDEX idx_orders_user_active_new
  RENAME TO idx_orders_user_active;
```

### Add Unique Index Safely

```sql
-- Goal: Add unique constraint on email

-- ┌────────────────────────────────────────┐
-- │ STEP 1: Find duplicates first          │
-- └────────────────────────────────────────┘

SELECT email, COUNT(*) as count
FROM users
GROUP BY email
HAVING COUNT(*) > 1;

-- ┌────────────────────────────────────────┐
-- │ STEP 2: Handle duplicates              │
-- └────────────────────────────────────────┘

-- Option A: Merge duplicates
-- Option B: Append suffix to duplicates
UPDATE users u1
SET email = email || '_duplicate_' || u1.id::TEXT
WHERE id NOT IN (
  SELECT MIN(id) FROM users GROUP BY email
);

-- ┌────────────────────────────────────────┐
-- │ STEP 3: Create unique index            │
-- └────────────────────────────────────────┘

CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_unique
  ON users(email);

-- ┌────────────────────────────────────────┐
-- │ STEP 4: Add constraint using index     │
-- └────────────────────────────────────────┘

ALTER TABLE users ADD CONSTRAINT uniq_users_email
  UNIQUE USING INDEX idx_users_email_unique;
```

## Foreign Key Changes

### Add Foreign Key Without Blocking

```sql
-- Goal: Add FK from orders.user_id to users.id

-- ┌────────────────────────────────────────┐
-- │ STEP 1: Add constraint NOT VALID       │
-- └────────────────────────────────────────┘

ALTER TABLE orders ADD CONSTRAINT fk_orders_user
  FOREIGN KEY (user_id) REFERENCES users(id)
  NOT VALID;

-- ┌────────────────────────────────────────┐
-- │ STEP 2: Handle orphaned records        │
-- └────────────────────────────────────────┘

-- Find orphaned records
SELECT o.id, o.user_id
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
WHERE u.id IS NULL;

-- Option A: Delete orphaned records
DELETE FROM orders
WHERE user_id NOT IN (SELECT id FROM users);

-- Option B: Set to NULL (if nullable)
UPDATE orders
SET user_id = NULL
WHERE user_id NOT IN (SELECT id FROM users);

-- Option C: Set to default user
UPDATE orders
SET user_id = 'default-user-uuid'
WHERE user_id NOT IN (SELECT id FROM users);

-- ┌────────────────────────────────────────┐
-- │ STEP 3: Validate constraint            │
-- └────────────────────────────────────────┘

ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_user;
```

## Batch Processing

### Batched Updates

```sql
-- Function for batched updates with progress tracking
CREATE OR REPLACE FUNCTION batch_update(
  table_name TEXT,
  set_clause TEXT,
  where_clause TEXT,
  batch_size INTEGER DEFAULT 1000,
  sleep_ms INTEGER DEFAULT 100
)
RETURNS TABLE(batches_run INTEGER, total_updated BIGINT) AS $$
DECLARE
  batch_count INTEGER := 0;
  rows_updated BIGINT := 0;
  batch_updated INTEGER;
BEGIN
  LOOP
    EXECUTE format(
      'UPDATE %I SET %s WHERE ctid IN (
        SELECT ctid FROM %I WHERE %s LIMIT %s FOR UPDATE SKIP LOCKED
      )',
      table_name, set_clause, table_name, where_clause, batch_size
    );

    GET DIAGNOSTICS batch_updated = ROW_COUNT;
    rows_updated := rows_updated + batch_updated;
    batch_count := batch_count + 1;

    EXIT WHEN batch_updated = 0;

    PERFORM pg_sleep(sleep_ms / 1000.0);

    RAISE NOTICE 'Batch %: updated % rows (total: %)',
      batch_count, batch_updated, rows_updated;
  END LOOP;

  RETURN QUERY SELECT batch_count, rows_updated;
END;
$$ LANGUAGE plpgsql;

-- Usage example
SELECT * FROM batch_update(
  'users',                          -- table
  'status = ''migrated''',          -- SET clause
  'status = ''pending''',           -- WHERE clause
  1000,                             -- batch size
  50                                -- sleep ms
);
```

### Progress Tracking

```sql
-- Create progress tracking table
CREATE TABLE migration_progress (
  id SERIAL PRIMARY KEY,
  migration_name VARCHAR(100) NOT NULL,
  table_name VARCHAR(100) NOT NULL,
  total_rows BIGINT,
  processed_rows BIGINT DEFAULT 0,
  started_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  completed_at TIMESTAMPTZ,
  status VARCHAR(20) DEFAULT 'running'
);

-- Function to track progress
CREATE OR REPLACE FUNCTION update_migration_progress(
  p_migration_name VARCHAR,
  p_rows_processed BIGINT
)
RETURNS VOID AS $$
BEGIN
  UPDATE migration_progress
  SET
    processed_rows = processed_rows + p_rows_processed,
    updated_at = NOW()
  WHERE migration_name = p_migration_name AND status = 'running';
END;
$$ LANGUAGE plpgsql;

-- Query progress
SELECT
  migration_name,
  table_name,
  processed_rows,
  total_rows,
  ROUND((processed_rows::NUMERIC / NULLIF(total_rows, 0)) * 100, 2) as percent_complete,
  NOW() - started_at as elapsed_time
FROM migration_progress
WHERE status = 'running';
```

## Deployment Coordination

### Blue-Green Database Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│                Blue-Green Database Pattern                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Blue (Current Production)     Green (New Version)              │
│  ┌─────────────────────┐      ┌─────────────────────┐          │
│  │    Database v1      │      │    Database v2      │          │
│  │                     │      │  (migrated schema)  │          │
│  └─────────────────────┘      └─────────────────────┘          │
│            │                            ▲                       │
│            │ Replicate                  │                       │
│            └────────────────────────────┘                       │
│                                                                  │
│  1. Setup replication: Blue → Green                             │
│  2. Run migrations on Green                                     │
│  3. Verify Green is healthy                                     │
│  4. Switch traffic to Green                                     │
│  5. Green becomes new Blue                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Feature Flags for Migrations

```typescript
// Application-level migration coordination
interface MigrationConfig {
  useNewSchema: boolean;
  writeToOldSchema: boolean;
  writeToNewSchema: boolean;
  readFromNewSchema: boolean;
}

const migrationPhases: Record<string, MigrationConfig> = {
  // Phase 1: Dual-write, read from old
  'expand': {
    useNewSchema: false,
    writeToOldSchema: true,
    writeToNewSchema: true,
    readFromNewSchema: false,
  },
  // Phase 2: Dual-write, read from new
  'migrate': {
    useNewSchema: false,
    writeToOldSchema: true,
    writeToNewSchema: true,
    readFromNewSchema: true,
  },
  // Phase 3: Write to new only
  'contract': {
    useNewSchema: true,
    writeToOldSchema: false,
    writeToNewSchema: true,
    readFromNewSchema: true,
  },
};

async function saveUser(user: User, phase: string) {
  const config = migrationPhases[phase];

  if (config.writeToOldSchema) {
    await db.users.update({
      where: { id: user.id },
      data: { name: user.fullName } // old column
    });
  }

  if (config.writeToNewSchema) {
    await db.users.update({
      where: { id: user.id },
      data: { full_name: user.fullName } // new column
    });
  }
}
```

## Monitoring During Migration

### Migration Health Checks

```sql
-- Check lock status during migration
SELECT
  l.locktype,
  l.relation::regclass,
  l.mode,
  l.granted,
  a.query,
  a.state,
  age(clock_timestamp(), a.query_start) as duration
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE l.relation IS NOT NULL
  AND a.query NOT LIKE '%pg_locks%'
ORDER BY duration DESC;

-- Check replication lag
SELECT
  client_addr,
  state,
  sent_lsn,
  write_lsn,
  flush_lsn,
  replay_lsn,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) as replication_lag_bytes
FROM pg_stat_replication;

-- Check table bloat during migration
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size,
  n_live_tup,
  n_dead_tup,
  ROUND((n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0)) * 100, 2) as dead_tuple_percent
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────────┐
│            Zero-Downtime Migration Checklist                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before Migration:                                               │
│  □ Test in production-like environment                          │
│  □ Verify rollback procedure works                              │
│  □ Set up monitoring and alerting                               │
│  □ Communicate with team about timeline                         │
│  □ Schedule during low-traffic period                           │
│                                                                  │
│  During Migration:                                               │
│  □ Monitor lock contention                                      │
│  □ Watch replication lag                                        │
│  □ Track progress with batched operations                       │
│  □ Be ready to pause/resume                                     │
│  □ Have rollback commands ready                                 │
│                                                                  │
│  After Migration:                                                │
│  □ Verify data integrity                                        │
│  □ Check query performance                                      │
│  □ Monitor error rates                                          │
│  □ Clean up temporary structures                                │
│  □ Document what was done                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
