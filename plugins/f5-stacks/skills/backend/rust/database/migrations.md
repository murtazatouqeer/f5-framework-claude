---
name: rust-database-migrations
description: Database migration patterns for Rust
applies_to: rust
---

# Database Migrations in Rust

## SQLx Migrations

### Setup

```bash
# Install SQLx CLI
cargo install sqlx-cli --features postgres

# Create migrations directory
mkdir migrations

# Create a new migration
sqlx migrate add create_users
```

### Migration Files

```sql
-- migrations/20240101000001_create_users.sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- Trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

```sql
-- migrations/20240101000002_create_categories.sql
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_categories_slug ON categories(slug);
CREATE INDEX idx_categories_parent ON categories(parent_id);

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

```sql
-- migrations/20240101000003_create_products.sql
CREATE TYPE product_status AS ENUM ('draft', 'active', 'inactive', 'archived');

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
    compare_price NUMERIC(10, 2) CHECK (compare_price >= 0),
    status product_status NOT NULL DEFAULT 'draft',
    category_id UUID NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    sku VARCHAR(100) UNIQUE,
    weight NUMERIC(10, 3),
    dimensions JSONB,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);

CREATE INDEX idx_products_slug ON products(slug);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_owner ON products(owner_id);
CREATE INDEX idx_products_status ON products(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_products_sku ON products(sku) WHERE sku IS NOT NULL;
CREATE INDEX idx_products_search ON products USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

### Running Migrations

```bash
# Set database URL
export DATABASE_URL="postgres://user:password@localhost/mydb"

# Run all pending migrations
sqlx migrate run

# Revert last migration
sqlx migrate revert

# Check migration status
sqlx migrate info

# Force run a specific migration
sqlx migrate run --source ./migrations --ignore-missing
```

### Programmatic Migrations

```rust
// src/infrastructure/database.rs
use sqlx::{migrate::MigrateDatabase, PgPool, Postgres};

pub async fn setup_database(database_url: &str) -> anyhow::Result<PgPool> {
    // Create database if it doesn't exist
    if !Postgres::database_exists(database_url).await? {
        Postgres::create_database(database_url).await?;
    }

    // Connect to database
    let pool = PgPool::connect(database_url).await?;

    // Run migrations
    sqlx::migrate!("./migrations")
        .run(&pool)
        .await?;

    Ok(pool)
}
```

## Diesel Migrations

### Setup

```bash
# Install Diesel CLI
cargo install diesel_cli --no-default-features --features postgres

# Setup Diesel (creates diesel.toml and migrations directory)
diesel setup

# Create a new migration
diesel migration generate create_users
```

### Migration Files

```sql
-- migrations/2024-01-01-000001_create_users/up.sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active BOOLEAN NOT NULL DEFAULT true,
    email_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- migrations/2024-01-01-000001_create_users/down.sql
DROP TABLE users;
```

### Running Migrations

```bash
# Set database URL
export DATABASE_URL="postgres://user:password@localhost/mydb"

# Run all pending migrations
diesel migration run

# Revert last migration
diesel migration revert

# Redo last migration (revert + run)
diesel migration redo

# List migration status
diesel migration list

# Print the current schema
diesel print-schema
```

### Programmatic Migrations

```rust
// src/infrastructure/database.rs
use diesel_migrations::{embed_migrations, EmbeddedMigrations, MigrationHarness};
use diesel::pg::PgConnection;

pub const MIGRATIONS: EmbeddedMigrations = embed_migrations!("./migrations");

pub fn run_migrations(conn: &mut PgConnection) -> Result<(), Box<dyn std::error::Error>> {
    conn.run_pending_migrations(MIGRATIONS)?;
    Ok(())
}
```

## SeaORM Migrations

### Setup

```bash
# Install SeaORM CLI
cargo install sea-orm-cli

# Initialize migration directory
sea-orm-cli migrate init

# Create a new migration
sea-orm-cli migrate generate create_users
```

### Migration Code

```rust
// migration/src/m20240101_000001_create_users.rs
use sea_orm_migration::prelude::*;

#[derive(DeriveMigrationName)]
pub struct Migration;

#[async_trait::async_trait]
impl MigrationTrait for Migration {
    async fn up(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager
            .create_table(
                Table::create()
                    .table(Users::Table)
                    .if_not_exists()
                    .col(
                        ColumnDef::new(Users::Id)
                            .uuid()
                            .not_null()
                            .primary_key()
                            .extra("DEFAULT gen_random_uuid()"),
                    )
                    .col(
                        ColumnDef::new(Users::Email)
                            .string()
                            .not_null()
                            .unique_key(),
                    )
                    .col(ColumnDef::new(Users::PasswordHash).string().not_null())
                    .col(ColumnDef::new(Users::Name).string().not_null())
                    .col(
                        ColumnDef::new(Users::Role)
                            .string()
                            .not_null()
                            .default("user"),
                    )
                    .col(
                        ColumnDef::new(Users::IsActive)
                            .boolean()
                            .not_null()
                            .default(true),
                    )
                    .col(ColumnDef::new(Users::EmailVerifiedAt).timestamp_with_time_zone())
                    .col(
                        ColumnDef::new(Users::CreatedAt)
                            .timestamp_with_time_zone()
                            .not_null()
                            .extra("DEFAULT NOW()"),
                    )
                    .col(
                        ColumnDef::new(Users::UpdatedAt)
                            .timestamp_with_time_zone()
                            .not_null()
                            .extra("DEFAULT NOW()"),
                    )
                    .to_owned(),
            )
            .await?;

        // Create index
        manager
            .create_index(
                Index::create()
                    .table(Users::Table)
                    .name("idx_users_email")
                    .col(Users::Email)
                    .to_owned(),
            )
            .await?;

        Ok(())
    }

    async fn down(&self, manager: &SchemaManager) -> Result<(), DbErr> {
        manager
            .drop_table(Table::drop().table(Users::Table).to_owned())
            .await
    }
}

#[derive(DeriveIden)]
enum Users {
    Table,
    Id,
    Email,
    PasswordHash,
    Name,
    Role,
    IsActive,
    EmailVerifiedAt,
    CreatedAt,
    UpdatedAt,
}
```

### Running Migrations

```bash
# Set database URL
export DATABASE_URL="postgres://user:password@localhost/mydb"

# Run all pending migrations
sea-orm-cli migrate up

# Revert last migration
sea-orm-cli migrate down

# Fresh - drop all tables and re-run migrations
sea-orm-cli migrate fresh

# Refresh - revert all and re-run
sea-orm-cli migrate refresh

# Generate entities from database
sea-orm-cli generate entity -o src/entities
```

## Migration Best Practices

### Naming Conventions

```
# SQLx
migrations/
├── 20240101000001_create_users.sql
├── 20240101000002_create_categories.sql
├── 20240101000003_create_products.sql
└── 20240115000001_add_products_sku.sql

# Diesel
migrations/
├── 2024-01-01-000001_create_users/
│   ├── up.sql
│   └── down.sql
├── 2024-01-01-000002_create_categories/
│   ├── up.sql
│   └── down.sql
└── 2024-01-15-000001_add_products_sku/
    ├── up.sql
    └── down.sql
```

### Safe Migrations

```sql
-- Always use IF NOT EXISTS / IF EXISTS
CREATE TABLE IF NOT EXISTS users (...);
DROP TABLE IF EXISTS users;
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- Use transactions for complex migrations
BEGIN;
ALTER TABLE products ADD COLUMN sku VARCHAR(100);
UPDATE products SET sku = 'SKU-' || id::text WHERE sku IS NULL;
ALTER TABLE products ALTER COLUMN sku SET NOT NULL;
CREATE UNIQUE INDEX idx_products_sku ON products(sku);
COMMIT;

-- For large tables, create index concurrently (outside transaction)
CREATE INDEX CONCURRENTLY idx_products_name ON products(name);
```

### Data Migrations

```sql
-- migrations/20240115000001_migrate_user_roles.sql
-- Migrate data safely

-- 1. Add new column
ALTER TABLE users ADD COLUMN new_role VARCHAR(50);

-- 2. Migrate data
UPDATE users SET new_role = CASE
    WHEN role = 'admin' THEN 'administrator'
    WHEN role = 'mod' THEN 'moderator'
    ELSE 'member'
END;

-- 3. Set NOT NULL after migration
ALTER TABLE users ALTER COLUMN new_role SET NOT NULL;

-- 4. Drop old column
ALTER TABLE users DROP COLUMN role;

-- 5. Rename new column
ALTER TABLE users RENAME COLUMN new_role TO role;
```

### Rollback Safety

```sql
-- up.sql - Adding a column with default
ALTER TABLE products
ADD COLUMN published_at TIMESTAMPTZ;

-- down.sql - Safe rollback
ALTER TABLE products
DROP COLUMN IF EXISTS published_at;
```

### Zero-Downtime Migrations

```sql
-- Phase 1: Add nullable column
ALTER TABLE products ADD COLUMN new_field VARCHAR(255);

-- Phase 2: Backfill data (run in application)
-- UPDATE products SET new_field = old_field WHERE new_field IS NULL;

-- Phase 3: Add constraint (after backfill complete)
ALTER TABLE products ALTER COLUMN new_field SET NOT NULL;

-- Phase 4: Remove old column (after application updated)
ALTER TABLE products DROP COLUMN old_field;
```

## Testing Migrations

```rust
// tests/migrations_test.rs
#[cfg(test)]
mod tests {
    use sqlx::PgPool;

    #[sqlx::test]
    async fn test_migrations_up_down(pool: PgPool) {
        // Migrations are automatically run by sqlx::test
        // Test that tables exist
        let result = sqlx::query("SELECT 1 FROM users LIMIT 1")
            .execute(&pool)
            .await;
        assert!(result.is_ok());
    }

    #[sqlx::test(fixtures("users"))]
    async fn test_with_fixtures(pool: PgPool) {
        // Uses tests/fixtures/users.sql
        let count: (i64,) = sqlx::query_as("SELECT COUNT(*) FROM users")
            .fetch_one(&pool)
            .await
            .unwrap();
        assert!(count.0 > 0);
    }
}
```
