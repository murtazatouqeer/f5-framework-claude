# Database Migrations

Zero-downtime migrations, expand/contract pattern, and safe schema changes.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Expand/Contract Pattern](#expandcontract-pattern)
3. [Safe Schema Changes](#safe-schema-changes)
4. [Index Changes](#index-changes)
5. [Data Migrations](#data-migrations)
6. [Deployment Coordination](#deployment-coordination)

---

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
│  3. Non-Blocking Operations                                      │
│     - Avoid table locks                                         │
│     - Use CONCURRENTLY for indexes                              │
│     - Validate constraints separately                           │
│                                                                  │
│  4. Expansion/Contraction Pattern                               │
│     - Expand: Add new structures                                │
│     - Migrate: Move data, update code                           │
│     - Contract: Remove old structures                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Expand/Contract Pattern

### Phase Overview

```
Time ─────────────────────────────────────────────────────────►

EXPAND PHASE
├── Add new column/table
├── Create sync triggers
└── Deploy app that writes to both

MIGRATE PHASE
├── Backfill historical data
├── Verify data integrity
└── Deploy app that reads from new

CONTRACT PHASE
├── Deploy app that only uses new
├── Remove sync triggers
└── Drop old column/table
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
UPDATE users SET full_name = name WHERE full_name IS NULL;

-- Step 2.2: Verify data integrity
SELECT COUNT(*) FROM users WHERE full_name IS NULL;  -- Should be 0
SELECT COUNT(*) FROM users WHERE name != full_name;  -- Should be 0

-- Deploy application changes to read/write full_name

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

---

## Safe Schema Changes

### Adding Non-Nullable Column

```sql
-- Goal: Add required 'status' column to users table

-- Step 1: Add nullable column
ALTER TABLE users ADD COLUMN status VARCHAR(20);

-- Step 2: Set default for new rows
ALTER TABLE users ALTER COLUMN status SET DEFAULT 'active';

-- Step 3: Backfill in batches
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

    PERFORM pg_sleep(sleep_ms / 1000.0);
  END LOOP;

  RETURN updated_count;
END;
$$ LANGUAGE plpgsql;

SELECT backfill_user_status(1000, 100);

-- Step 4: Add NOT NULL constraint safely
ALTER TABLE users ADD CONSTRAINT chk_status_not_null
  CHECK (status IS NOT NULL) NOT VALID;

ALTER TABLE users VALIDATE CONSTRAINT chk_status_not_null;

ALTER TABLE users ALTER COLUMN status SET NOT NULL;

ALTER TABLE users DROP CONSTRAINT chk_status_not_null;
```

### Adding Foreign Key Without Blocking

```sql
-- Step 1: Add constraint NOT VALID
ALTER TABLE orders ADD CONSTRAINT fk_orders_user
  FOREIGN KEY (user_id) REFERENCES users(id)
  NOT VALID;

-- Step 2: Handle orphaned records
DELETE FROM orders
WHERE user_id NOT IN (SELECT id FROM users);

-- Step 3: Validate constraint (non-blocking)
ALTER TABLE orders VALIDATE CONSTRAINT fk_orders_user;
```

---

## Index Changes

### Create Index Without Downtime

```sql
-- Use CONCURRENTLY (doesn't lock table)
CREATE INDEX CONCURRENTLY idx_orders_user ON orders(user_id);

-- Verify index is valid
SELECT indexname, indisvalid
FROM pg_indexes
JOIN pg_index ON indexname::regclass = indexrelid
WHERE indexname = 'idx_orders_user';
```

### Replace Index Safely

```sql
-- Step 1: Create new index concurrently
CREATE INDEX CONCURRENTLY idx_orders_user_new
  ON orders(user_id, created_at DESC);

-- Step 2: Verify new index works
EXPLAIN (ANALYZE)
SELECT * FROM orders WHERE user_id = 'uuid' ORDER BY created_at DESC;

-- Step 3: Drop old index concurrently
DROP INDEX CONCURRENTLY idx_orders_user_old;

-- Step 4: Rename new index
ALTER INDEX idx_orders_user_new RENAME TO idx_orders_user;
```

### Add Unique Index Safely

```sql
-- Step 1: Find duplicates first
SELECT email, COUNT(*) FROM users
GROUP BY email HAVING COUNT(*) > 1;

-- Step 2: Handle duplicates
UPDATE users u1
SET email = email || '_duplicate_' || u1.id::TEXT
WHERE id NOT IN (
  SELECT MIN(id) FROM users GROUP BY email
);

-- Step 3: Create unique index
CREATE UNIQUE INDEX CONCURRENTLY idx_users_email_unique
  ON users(email);

-- Step 4: Add constraint using index
ALTER TABLE users ADD CONSTRAINT uniq_users_email
  UNIQUE USING INDEX idx_users_email_unique;
```

---

## Data Migrations

### Batched Updates

```sql
-- Function for batched updates with progress
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
  END LOOP;

  RETURN QUERY SELECT batch_count, rows_updated;
END;
$$ LANGUAGE plpgsql;

-- Usage
SELECT * FROM batch_update(
  'users',
  'status = ''migrated''',
  'status = ''pending''',
  1000,
  50
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
  completed_at TIMESTAMPTZ,
  status VARCHAR(20) DEFAULT 'running'
);

-- Query progress
SELECT
  migration_name,
  ROUND((processed_rows::NUMERIC / NULLIF(total_rows, 0)) * 100, 2) as percent_complete,
  NOW() - started_at as elapsed_time
FROM migration_progress
WHERE status = 'running';
```

---

## Deployment Coordination

### Feature Flags for Migrations

```typescript
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
      data: { name: user.fullName }
    });
  }

  if (config.writeToNewSchema) {
    await db.users.update({
      where: { id: user.id },
      data: { full_name: user.fullName }
    });
  }
}
```

### Monitoring During Migration

```sql
-- Check lock status
SELECT
  l.locktype,
  l.relation::regclass,
  l.mode,
  l.granted,
  a.query,
  age(clock_timestamp(), a.query_start) as duration
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE l.relation IS NOT NULL
ORDER BY duration DESC;

-- Check table bloat
SELECT
  tablename,
  n_live_tup,
  n_dead_tup,
  ROUND((n_dead_tup::NUMERIC / NULLIF(n_live_tup + n_dead_tup, 0)) * 100, 2) as dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 10000
ORDER BY n_dead_tup DESC;
```

---

## Migration Checklist

```
Before Migration:
□ Test in production-like environment
□ Verify rollback procedure works
□ Set up monitoring and alerting
□ Schedule during low-traffic period

During Migration:
□ Monitor lock contention
□ Track progress with batched operations
□ Be ready to pause/resume
□ Have rollback commands ready

After Migration:
□ Verify data integrity
□ Check query performance
□ Monitor error rates
□ Clean up temporary structures
□ Document what was done
```

---

## Common Dangerous Operations

| Operation | Risk | Safe Alternative |
|-----------|------|------------------|
| ALTER TABLE ... ADD COLUMN NOT NULL | Locks table | Add nullable → backfill → add constraint |
| CREATE INDEX | Locks table | CREATE INDEX CONCURRENTLY |
| ALTER TABLE ... DROP COLUMN | Data loss | Keep column, deprecate in code first |
| TRUNCATE TABLE | Data loss | DELETE in batches |
| ALTER TYPE | Locks table | Create new column, migrate data |
