# Migration Script Template

Flyway SQL migration templates for Spring Boot with PostgreSQL.

## Create Table Template

```sql
-- V1__create_{{table_name}}_table.sql
-- Description: Create {{table_name}} table with auditing and soft delete

CREATE TABLE {{table_name}} (
    -- Primary Key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Business Fields
    name VARCHAR(100) NOT NULL,
    description VARCHAR(2000),
    status VARCHAR(20) NOT NULL DEFAULT 'DRAFT',

    -- Foreign Keys
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,

    -- Auditing Fields
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by VARCHAR(255),
    updated_by VARCHAR(255),

    -- Soft Delete
    deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP WITH TIME ZONE,

    -- Optimistic Locking
    version BIGINT NOT NULL DEFAULT 0,

    -- Constraints
    CONSTRAINT chk_{{table_name}}_status
        CHECK (status IN ('DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED'))
);

-- Indexes
CREATE INDEX idx_{{table_name}}_name ON {{table_name}}(name);
CREATE INDEX idx_{{table_name}}_status ON {{table_name}}(status) WHERE deleted = FALSE;
CREATE INDEX idx_{{table_name}}_category ON {{table_name}}(category_id);
CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at);
CREATE INDEX idx_{{table_name}}_deleted ON {{table_name}}(deleted) WHERE deleted = FALSE;

-- Comments
COMMENT ON TABLE {{table_name}} IS '{{Entity}} table - stores {{entity}} information';
COMMENT ON COLUMN {{table_name}}.id IS 'Unique identifier (UUID)';
COMMENT ON COLUMN {{table_name}}.name IS '{{Entity}} name';
COMMENT ON COLUMN {{table_name}}.status IS '{{Entity}} status: DRAFT, ACTIVE, INACTIVE, ARCHIVED';
COMMENT ON COLUMN {{table_name}}.deleted IS 'Soft delete flag';
COMMENT ON COLUMN {{table_name}}.version IS 'Optimistic locking version';
```

## Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{Entity}}` | Entity name (PascalCase) | `Product` |
| `{{entity}}` | Entity name (camelCase) | `product` |
| `{{table_name}}` | Database table name | `products` |

## Additional Templates

### Add Column Migration

```sql
-- V2__add_{{column_name}}_to_{{table_name}}.sql
-- Description: Add {{column_name}} column to {{table_name}}

ALTER TABLE {{table_name}}
    ADD COLUMN {{column_name}} VARCHAR(100);

-- Add index if needed
CREATE INDEX idx_{{table_name}}_{{column_name}}
    ON {{table_name}}({{column_name}})
    WHERE deleted = FALSE;

-- Add comment
COMMENT ON COLUMN {{table_name}}.{{column_name}} IS 'Description of {{column_name}}';
```

### Add Foreign Key Migration

```sql
-- V3__add_{{related_table}}_fk_to_{{table_name}}.sql
-- Description: Add foreign key to {{related_table}}

ALTER TABLE {{table_name}}
    ADD COLUMN {{related_table}}_id UUID;

ALTER TABLE {{table_name}}
    ADD CONSTRAINT fk_{{table_name}}_{{related_table}}
    FOREIGN KEY ({{related_table}}_id)
    REFERENCES {{related_table}}(id)
    ON DELETE SET NULL;

CREATE INDEX idx_{{table_name}}_{{related_table}}_id
    ON {{table_name}}({{related_table}}_id);
```

### Create Join Table Migration

```sql
-- V4__create_{{table1}}_{{table2}}_junction.sql
-- Description: Create many-to-many junction table

CREATE TABLE {{table1}}_{{table2}} (
    {{table1}}_id UUID NOT NULL REFERENCES {{table1}}(id) ON DELETE CASCADE,
    {{table2}}_id UUID NOT NULL REFERENCES {{table2}}(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    PRIMARY KEY ({{table1}}_id, {{table2}}_id)
);

CREATE INDEX idx_{{table1}}_{{table2}}_{{table1}} ON {{table1}}_{{table2}}({{table1}}_id);
CREATE INDEX idx_{{table1}}_{{table2}}_{{table2}} ON {{table1}}_{{table2}}({{table2}}_id);

COMMENT ON TABLE {{table1}}_{{table2}} IS 'Junction table for {{table1}} and {{table2}} relationship';
```

### Create Enum Type Migration

```sql
-- V5__create_{{enum_name}}_type.sql
-- Description: Create {{enum_name}} enum type

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{{enum_name}}') THEN
        CREATE TYPE {{enum_name}} AS ENUM (
            'VALUE1',
            'VALUE2',
            'VALUE3'
        );
    END IF;
END$$;

-- If converting existing varchar column to enum:
-- ALTER TABLE {{table_name}}
--     ALTER COLUMN status TYPE {{enum_name}}
--     USING status::{{enum_name}};
```

### Add JSON Column Migration

```sql
-- V6__add_metadata_to_{{table_name}}.sql
-- Description: Add JSONB metadata column

ALTER TABLE {{table_name}}
    ADD COLUMN metadata JSONB DEFAULT '{}';

-- Add GIN index for JSONB queries
CREATE INDEX idx_{{table_name}}_metadata
    ON {{table_name}}
    USING GIN (metadata);

-- For specific JSON path indexing
CREATE INDEX idx_{{table_name}}_metadata_type
    ON {{table_name}}
    USING BTREE ((metadata->>'type'))
    WHERE metadata->>'type' IS NOT NULL;

COMMENT ON COLUMN {{table_name}}.metadata IS 'JSONB column for flexible metadata storage';
```

### Add Full-Text Search Migration

```sql
-- V7__add_fulltext_search_to_{{table_name}}.sql
-- Description: Add full-text search capabilities

-- Add tsvector column
ALTER TABLE {{table_name}}
    ADD COLUMN search_vector tsvector;

-- Create GIN index
CREATE INDEX idx_{{table_name}}_search
    ON {{table_name}}
    USING GIN (search_vector);

-- Create trigger function
CREATE OR REPLACE FUNCTION {{table_name}}_search_trigger()
RETURNS trigger AS $$
BEGIN
    NEW.search_vector :=
        setweight(to_tsvector('english', COALESCE(NEW.name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(NEW.description, '')), 'B');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger
CREATE TRIGGER {{table_name}}_search_update
    BEFORE INSERT OR UPDATE ON {{table_name}}
    FOR EACH ROW
    EXECUTE FUNCTION {{table_name}}_search_trigger();

-- Update existing records
UPDATE {{table_name}} SET
    search_vector =
        setweight(to_tsvector('english', COALESCE(name, '')), 'A') ||
        setweight(to_tsvector('english', COALESCE(description, '')), 'B');
```

### Add Audit Trigger Migration

```sql
-- V8__add_audit_trigger_to_{{table_name}}.sql
-- Description: Add automatic updated_at trigger

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER {{table_name}}_updated_at
    BEFORE UPDATE ON {{table_name}}
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Create Audit Log Table Migration

```sql
-- V9__create_{{table_name}}_audit_log.sql
-- Description: Create audit log table for {{table_name}}

CREATE TABLE {{table_name}}_audit (
    id BIGSERIAL PRIMARY KEY,
    {{table_name}}_id UUID NOT NULL,
    action VARCHAR(10) NOT NULL,
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_{{table_name}}_audit_entity
    ON {{table_name}}_audit({{table_name}}_id);
CREATE INDEX idx_{{table_name}}_audit_changed_at
    ON {{table_name}}_audit(changed_at);

-- Audit trigger function
CREATE OR REPLACE FUNCTION {{table_name}}_audit_trigger()
RETURNS trigger AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO {{table_name}}_audit ({{table_name}}_id, action, new_data, changed_by)
        VALUES (NEW.id, 'INSERT', row_to_json(NEW), NEW.created_by);
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO {{table_name}}_audit ({{table_name}}_id, action, old_data, new_data, changed_by)
        VALUES (NEW.id, 'UPDATE', row_to_json(OLD), row_to_json(NEW), NEW.updated_by);
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO {{table_name}}_audit ({{table_name}}_id, action, old_data, changed_by)
        VALUES (OLD.id, 'DELETE', row_to_json(OLD), current_user);
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER {{table_name}}_audit
    AFTER INSERT OR UPDATE OR DELETE ON {{table_name}}
    FOR EACH ROW
    EXECUTE FUNCTION {{table_name}}_audit_trigger();
```

### Add Unique Constraint Migration

```sql
-- V10__add_unique_constraint_to_{{table_name}}.sql
-- Description: Add unique constraint

-- Simple unique constraint
ALTER TABLE {{table_name}}
    ADD CONSTRAINT uq_{{table_name}}_{{column_name}}
    UNIQUE ({{column_name}});

-- Partial unique constraint (only for non-deleted records)
CREATE UNIQUE INDEX uq_{{table_name}}_{{column_name}}_active
    ON {{table_name}}({{column_name}})
    WHERE deleted = FALSE;

-- Composite unique constraint
ALTER TABLE {{table_name}}
    ADD CONSTRAINT uq_{{table_name}}_composite
    UNIQUE (column1, column2);
```

### Data Migration Template

```sql
-- V11__migrate_{{table_name}}_data.sql
-- Description: Data migration for {{table_name}}

-- Create backup
CREATE TABLE {{table_name}}_backup AS
SELECT * FROM {{table_name}};

-- Perform data migration
UPDATE {{table_name}}
SET status = 'ACTIVE'
WHERE status = 'ENABLED';

UPDATE {{table_name}}
SET status = 'INACTIVE'
WHERE status = 'DISABLED';

-- Verify migration
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM {{table_name}}_backup;
    SELECT COUNT(*) INTO new_count FROM {{table_name}};

    IF old_count != new_count THEN
        RAISE EXCEPTION 'Data migration verification failed: count mismatch';
    END IF;
END$$;

-- Optional: drop backup after verification
-- DROP TABLE {{table_name}}_backup;
```

### Rollback Migration Template

```sql
-- V12__rollback_example.sql
-- Description: Example rollback migration (for documentation)
-- Note: Flyway uses undo migrations with U prefix for rollbacks

-- This is an example of what a rollback might look like
-- In practice, create U12__rollback_example.sql for Flyway Pro

-- Rollback steps:
-- 1. DROP INDEX IF EXISTS idx_new_index;
-- 2. ALTER TABLE table_name DROP COLUMN IF EXISTS new_column;
-- 3. DROP TABLE IF EXISTS new_table;
```

### Create Partitioned Table Migration

```sql
-- V13__create_partitioned_{{table_name}}.sql
-- Description: Create partitioned table for time-series data

CREATE TABLE {{table_name}} (
    id UUID NOT NULL DEFAULT gen_random_uuid(),
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE {{table_name}}_2024_q1 PARTITION OF {{table_name}}
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE {{table_name}}_2024_q2 PARTITION OF {{table_name}}
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

CREATE TABLE {{table_name}}_2024_q3 PARTITION OF {{table_name}}
    FOR VALUES FROM ('2024-07-01') TO ('2024-10-01');

CREATE TABLE {{table_name}}_2024_q4 PARTITION OF {{table_name}}
    FOR VALUES FROM ('2024-10-01') TO ('2025-01-01');

-- Create default partition for future data
CREATE TABLE {{table_name}}_default PARTITION OF {{table_name}} DEFAULT;

-- Create indexes on partitioned table
CREATE INDEX idx_{{table_name}}_event_type ON {{table_name}}(event_type);
CREATE INDEX idx_{{table_name}}_created_at ON {{table_name}}(created_at);
```

### Add Check Constraint Migration

```sql
-- V14__add_check_constraints_to_{{table_name}}.sql
-- Description: Add business rule constraints

-- Price must be positive
ALTER TABLE {{table_name}}
    ADD CONSTRAINT chk_{{table_name}}_price_positive
    CHECK (price >= 0);

-- Quantity must be within range
ALTER TABLE {{table_name}}
    ADD CONSTRAINT chk_{{table_name}}_quantity_range
    CHECK (quantity >= 0 AND quantity <= 10000);

-- Email format validation
ALTER TABLE {{table_name}}
    ADD CONSTRAINT chk_{{table_name}}_email_format
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Date range validation
ALTER TABLE {{table_name}}
    ADD CONSTRAINT chk_{{table_name}}_date_range
    CHECK (end_date IS NULL OR end_date >= start_date);
```

## Naming Conventions

| Type | Pattern | Example |
|------|---------|---------|
| Create Table | `V{n}__create_{table}_table.sql` | `V1__create_products_table.sql` |
| Add Column | `V{n}__add_{column}_to_{table}.sql` | `V2__add_sku_to_products.sql` |
| Add Index | `V{n}__add_{index}_index.sql` | `V3__add_products_sku_index.sql` |
| Add FK | `V{n}__add_{table}_fk_to_{table}.sql` | `V4__add_category_fk_to_products.sql` |
| Modify Column | `V{n}__modify_{column}_in_{table}.sql` | `V5__modify_price_in_products.sql` |
| Drop Column | `V{n}__drop_{column}_from_{table}.sql` | `V6__drop_legacy_from_products.sql` |
| Data Migration | `V{n}__migrate_{description}.sql` | `V7__migrate_status_values.sql` |

## Best Practices

1. **Always use transactions** - PostgreSQL DDL is transactional
2. **Include rollback comments** - Document how to reverse changes
3. **Test migrations locally** - Run against test database first
4. **Use IF EXISTS/IF NOT EXISTS** - Make migrations idempotent where possible
5. **Add comments** - Document tables and columns
6. **Create indexes concurrently** - Use `CONCURRENTLY` for production
7. **Backup before major changes** - Create backup tables for data migrations
