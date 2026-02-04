# Database Migrations

Managing database schema changes with golang-migrate.

## Setup

```bash
# Install golang-migrate CLI
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@latest

# Create migrations directory
mkdir -p migrations
```

## Migration Files

```sql
-- migrations/001_create_users.up.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);

-- migrations/001_create_users.down.sql
DROP TABLE IF EXISTS users;
```

```sql
-- migrations/002_create_profiles.up.sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    avatar_url VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);

-- migrations/002_create_profiles.down.sql
DROP TABLE IF EXISTS profiles;
```

```sql
-- migrations/003_create_posts.up.sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    content TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    author_id UUID NOT NULL REFERENCES users(id),
    published_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_slug ON posts(slug);
CREATE INDEX idx_posts_published_at ON posts(published_at);

-- migrations/003_create_posts.down.sql
DROP TABLE IF EXISTS posts;
```

## Programmatic Migration

```go
// pkg/database/migrate.go
package database

import (
    "errors"
    "fmt"

    "github.com/golang-migrate/migrate/v4"
    "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
    "github.com/jmoiron/sqlx"
)

type Migrator struct {
    db        *sqlx.DB
    sourceURL string
}

func NewMigrator(db *sqlx.DB, migrationsPath string) *Migrator {
    return &Migrator{
        db:        db,
        sourceURL: "file://" + migrationsPath,
    }
}

func (m *Migrator) Up() error {
    migrator, err := m.getMigrate()
    if err != nil {
        return err
    }

    if err := migrator.Up(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
        return fmt.Errorf("running migrations: %w", err)
    }

    return nil
}

func (m *Migrator) Down() error {
    migrator, err := m.getMigrate()
    if err != nil {
        return err
    }

    if err := migrator.Down(); err != nil && !errors.Is(err, migrate.ErrNoChange) {
        return fmt.Errorf("rolling back migrations: %w", err)
    }

    return nil
}

func (m *Migrator) Steps(n int) error {
    migrator, err := m.getMigrate()
    if err != nil {
        return err
    }

    if err := migrator.Steps(n); err != nil && !errors.Is(err, migrate.ErrNoChange) {
        return fmt.Errorf("running migration steps: %w", err)
    }

    return nil
}

func (m *Migrator) Version() (uint, bool, error) {
    migrator, err := m.getMigrate()
    if err != nil {
        return 0, false, err
    }

    return migrator.Version()
}

func (m *Migrator) getMigrate() (*migrate.Migrate, error) {
    driver, err := postgres.WithInstance(m.db.DB, &postgres.Config{})
    if err != nil {
        return nil, fmt.Errorf("creating driver: %w", err)
    }

    migrator, err := migrate.NewWithDatabaseInstance(m.sourceURL, "postgres", driver)
    if err != nil {
        return nil, fmt.Errorf("creating migrator: %w", err)
    }

    return migrator, nil
}
```

## CLI Usage

```makefile
# Makefile
DATABASE_URL ?= postgres://user:pass@localhost:5432/dbname?sslmode=disable
MIGRATIONS_PATH = ./migrations

.PHONY: migrate-create
migrate-create:
	@read -p "Migration name: " name; \
	migrate create -ext sql -dir $(MIGRATIONS_PATH) -seq $$name

.PHONY: migrate-up
migrate-up:
	migrate -path $(MIGRATIONS_PATH) -database "$(DATABASE_URL)" up

.PHONY: migrate-down
migrate-down:
	migrate -path $(MIGRATIONS_PATH) -database "$(DATABASE_URL)" down 1

.PHONY: migrate-force
migrate-force:
	@read -p "Version: " version; \
	migrate -path $(MIGRATIONS_PATH) -database "$(DATABASE_URL)" force $$version

.PHONY: migrate-version
migrate-version:
	migrate -path $(MIGRATIONS_PATH) -database "$(DATABASE_URL)" version
```

## Migration Best Practices

```sql
-- migrations/004_add_indexes.up.sql
-- Add indexes concurrently to avoid locking
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_posts_content_search
ON posts USING gin(to_tsvector('english', title || ' ' || content));

-- migrations/004_add_indexes.down.sql
DROP INDEX CONCURRENTLY IF EXISTS idx_posts_content_search;
```

```sql
-- migrations/005_alter_column_safe.up.sql
-- Safe column addition (with default)
ALTER TABLE users ADD COLUMN IF NOT EXISTS verified_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS two_factor_enabled BOOLEAN DEFAULT FALSE;

-- migrations/005_alter_column_safe.down.sql
ALTER TABLE users DROP COLUMN IF EXISTS verified_at;
ALTER TABLE users DROP COLUMN IF EXISTS two_factor_enabled;
```

```sql
-- migrations/006_add_constraint.up.sql
-- Add constraint with validation
ALTER TABLE posts ADD CONSTRAINT chk_posts_status
CHECK (status IN ('draft', 'published', 'archived'));

-- migrations/006_add_constraint.down.sql
ALTER TABLE posts DROP CONSTRAINT IF EXISTS chk_posts_status;
```

## Migration Tips

1. **One Change Per Migration**: Easier to debug and rollback
2. **Test Both Directions**: Always test up and down
3. **Use Transactions**: Wrap DDL in transactions when possible
4. **Avoid Data Migrations**: Separate schema and data changes
5. **Use CONCURRENTLY**: For index creation on production
6. **Version Control**: Keep migrations in git
7. **Naming Convention**: Use sequential numbering with descriptive names
