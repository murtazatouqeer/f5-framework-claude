---
name: schema-design
description: Database schema design principles and patterns
category: database/design
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Schema Design

## Overview

Good schema design balances data integrity, query performance, and
maintainability. This guide covers principles and patterns for
designing effective database schemas.

## Design Process

```
┌─────────────────────────────────────────────────────────────────┐
│                   Schema Design Process                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Requirements    → Understand business domain                │
│         │                                                        │
│         ▼                                                        │
│  2. Conceptual      → Entities, relationships (ER diagram)      │
│         │                                                        │
│         ▼                                                        │
│  3. Logical         → Tables, columns, keys (normalized)        │
│         │                                                        │
│         ▼                                                        │
│  4. Physical        → Indexes, partitions, storage              │
│         │                                                        │
│         ▼                                                        │
│  5. Optimization    → Denormalize for performance               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Naming Conventions

### Tables

```sql
-- Use plural, snake_case
CREATE TABLE users (...);          -- Good
CREATE TABLE User (...);           -- Bad (singular, PascalCase)
CREATE TABLE tbl_user (...);       -- Bad (prefix)

-- Junction tables: combine both entity names
CREATE TABLE user_roles (...);
CREATE TABLE order_items (...);
CREATE TABLE product_categories (...);
```

### Columns

```sql
-- Use singular, snake_case
CREATE TABLE users (
  id UUID PRIMARY KEY,             -- Simple primary key name
  first_name VARCHAR(100),         -- Descriptive snake_case
  email_address VARCHAR(255),      -- Clear naming
  created_at TIMESTAMPTZ,          -- Timestamp suffix
  is_active BOOLEAN,               -- Boolean prefix
  login_count INTEGER              -- Clear purpose
);

-- Foreign keys: referenced_table_id
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),     -- user_id not user or userId
  shipping_address_id UUID REFERENCES addresses(id)
);
```

### Indexes and Constraints

```sql
-- Indexes: idx_{table}_{columns}
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at);

-- Unique indexes: uniq_{table}_{columns}
CREATE UNIQUE INDEX uniq_users_email ON users(email);

-- Foreign keys: fk_{table}_{referenced}
ALTER TABLE orders ADD CONSTRAINT fk_orders_user
  FOREIGN KEY (user_id) REFERENCES users(id);

-- Check constraints: chk_{table}_{column}
ALTER TABLE products ADD CONSTRAINT chk_products_price
  CHECK (price >= 0);
```

## Primary Keys

### UUID vs Serial

```sql
-- UUID: Globally unique, no sequence bottleneck
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255)
);

-- Pros: Distributed-friendly, no ID guessing, merge-friendly
-- Cons: Larger (16 bytes), slightly slower indexes, not human-readable

-- Serial/BIGSERIAL: Auto-increment integer
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255)
);

-- Pros: Smaller, faster indexes, human-readable
-- Cons: Sequence bottleneck, predictable, merge conflicts

-- RECOMMENDATION: Use UUID for distributed systems, Serial for simple apps
```

### Natural vs Surrogate Keys

```sql
-- Surrogate key (recommended in most cases)
CREATE TABLE countries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code VARCHAR(2) UNIQUE NOT NULL,  -- Natural key as unique constraint
  name VARCHAR(100) NOT NULL
);

-- Natural key (when stable and meaningful)
CREATE TABLE currencies (
  code VARCHAR(3) PRIMARY KEY,  -- ISO 4217: USD, EUR, JPY
  name VARCHAR(100) NOT NULL,
  symbol VARCHAR(5)
);

-- Use natural key in FK when readable
CREATE TABLE products (
  id UUID PRIMARY KEY,
  currency_code VARCHAR(3) REFERENCES currencies(code),
  price DECIMAL(10, 2)
);
```

## Foreign Keys

### Referential Actions

```sql
-- ON DELETE options
CREATE TABLE orders (
  user_id UUID REFERENCES users(id)
    ON DELETE CASCADE,      -- Delete orders when user deleted
    -- ON DELETE SET NULL,  -- Set to NULL when user deleted
    -- ON DELETE RESTRICT,  -- Prevent user deletion if orders exist
    -- ON DELETE NO ACTION  -- Same as RESTRICT (default)
);

-- ON UPDATE options (less common)
CREATE TABLE order_items (
  product_id UUID REFERENCES products(id)
    ON UPDATE CASCADE      -- Update FK if product ID changes
);

-- Common patterns
-- CASCADE: Child records (order_items when order deleted)
-- SET NULL: Optional relationships (article.author_id)
-- RESTRICT: Prevent orphans (prevent category delete if products exist)
```

### Self-Referencing

```sql
-- Hierarchical data (org chart, categories)
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
  name VARCHAR(100) NOT NULL,
  level INTEGER GENERATED ALWAYS AS (
    CASE WHEN parent_id IS NULL THEN 0 ELSE 1 END
  ) STORED
);

-- Employees with managers
CREATE TABLE employees (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,
  name VARCHAR(100) NOT NULL,
  hire_date DATE NOT NULL
);

-- Get all reports (recursive query)
WITH RECURSIVE reports AS (
  SELECT id, name, manager_id, 1 as level
  FROM employees WHERE manager_id = 'manager-uuid'
  UNION ALL
  SELECT e.id, e.name, e.manager_id, r.level + 1
  FROM employees e JOIN reports r ON e.manager_id = r.id
)
SELECT * FROM reports;
```

## Timestamps and Audit Fields

```sql
-- Standard timestamp columns
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  -- ... other columns ...
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  deleted_at TIMESTAMPTZ  -- Soft delete
);

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON orders
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at();

-- Full audit fields
CREATE TABLE sensitive_data (
  id UUID PRIMARY KEY,
  -- ... data columns ...
  created_at TIMESTAMPTZ DEFAULT NOW(),
  created_by UUID REFERENCES users(id),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  updated_by UUID REFERENCES users(id),
  version INTEGER DEFAULT 1  -- Optimistic locking
);
```

## Enum vs Lookup Tables

```sql
-- PostgreSQL ENUM (simple, performant, hard to modify)
CREATE TYPE order_status AS ENUM (
  'pending', 'confirmed', 'processing',
  'shipped', 'delivered', 'cancelled'
);

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  status order_status NOT NULL DEFAULT 'pending'
);

-- Lookup table (flexible, requires join)
CREATE TABLE order_statuses (
  id SERIAL PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  sort_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true
);

CREATE TABLE orders (
  id UUID PRIMARY KEY,
  status_id INTEGER REFERENCES order_statuses(id)
);

-- CHECK constraint (simple, no extra table)
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  status VARCHAR(20) NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'confirmed', 'shipped', 'delivered'))
);

-- RECOMMENDATION:
-- ENUM: Fixed, rarely-changing values (status, type)
-- Lookup table: User-manageable values, need metadata
-- CHECK: Quick solution, limited values
```

## Common Schema Patterns

### User Authentication

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  email_verified_at TIMESTAMPTZ,
  password_hash VARCHAR(255) NOT NULL,
  name VARCHAR(255) NOT NULL,
  avatar_url VARCHAR(500),
  role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('user', 'admin', 'moderator')),
  status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'suspended', 'deleted')),
  last_login_at TIMESTAMPTZ,
  failed_login_attempts INTEGER DEFAULT 0,
  locked_until TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status) WHERE status = 'active';

-- Password reset tokens
CREATE TABLE password_reset_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_password_tokens_user ON password_reset_tokens(user_id);

-- Sessions
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  token_hash VARCHAR(255) NOT NULL UNIQUE,
  ip_address INET,
  user_agent TEXT,
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
```

### E-commerce Core

```sql
-- Products with categories
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_id UUID REFERENCES categories(id),
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE,
  description TEXT,
  image_url VARCHAR(500),
  sort_order INTEGER DEFAULT 0,
  is_active BOOLEAN DEFAULT true
);

CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id UUID REFERENCES categories(id),
  sku VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  slug VARCHAR(255) NOT NULL UNIQUE,
  description TEXT,
  price DECIMAL(10, 2) NOT NULL CHECK (price >= 0),
  compare_at_price DECIMAL(10, 2) CHECK (compare_at_price >= 0),
  cost DECIMAL(10, 2) CHECK (cost >= 0),
  stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
  low_stock_threshold INTEGER DEFAULT 10,
  weight_grams INTEGER,
  status VARCHAR(20) DEFAULT 'draft'
    CHECK (status IN ('draft', 'active', 'archived')),
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_status ON products(status) WHERE status = 'active';
CREATE INDEX idx_products_metadata ON products USING GIN(metadata);

-- Orders
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number VARCHAR(20) NOT NULL UNIQUE,
  user_id UUID REFERENCES users(id),
  status VARCHAR(20) DEFAULT 'pending'
    CHECK (status IN ('pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled')),
  subtotal DECIMAL(12, 2) NOT NULL,
  tax DECIMAL(12, 2) DEFAULT 0,
  shipping DECIMAL(12, 2) DEFAULT 0,
  discount DECIMAL(12, 2) DEFAULT 0,
  total DECIMAL(12, 2) NOT NULL,
  shipping_address JSONB NOT NULL,
  billing_address JSONB,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created ON orders(created_at DESC);

-- Order items
CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  sku VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  quantity INTEGER NOT NULL CHECK (quantity > 0),
  subtotal DECIMAL(12, 2) NOT NULL
);

CREATE INDEX idx_order_items_order ON order_items(order_id);
```

### Multi-tenant

```sql
-- Tenant isolation via tenant_id
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  subdomain VARCHAR(100) UNIQUE,
  plan VARCHAR(20) DEFAULT 'free',
  status VARCHAR(20) DEFAULT 'active',
  settings JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE tenant_users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role VARCHAR(20) DEFAULT 'member',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (tenant_id, user_id)
);

-- All tenant data includes tenant_id
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  -- ...
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_projects_tenant ON projects(tenant_id);

-- Row-level security (PostgreSQL)
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON projects
  USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

## Data Integrity

### Constraints Best Practices

```sql
CREATE TABLE products (
  id UUID PRIMARY KEY,
  sku VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  stock INTEGER NOT NULL DEFAULT 0,

  -- NOT NULL for required fields
  -- Prevents NULL where it doesn't make sense

  -- UNIQUE for natural keys
  CONSTRAINT uniq_products_sku UNIQUE (sku),

  -- CHECK for business rules
  CONSTRAINT chk_products_price CHECK (price >= 0),
  CONSTRAINT chk_products_stock CHECK (stock >= 0),
  CONSTRAINT chk_products_name CHECK (LENGTH(name) >= 1),

  -- Complex check
  CONSTRAINT chk_products_pricing CHECK (
    compare_at_price IS NULL OR compare_at_price >= price
  )
);

-- Exclusion constraint (prevents overlapping)
CREATE TABLE room_bookings (
  id UUID PRIMARY KEY,
  room_id UUID NOT NULL,
  during TSTZRANGE NOT NULL,
  EXCLUDE USING GIST (room_id WITH =, during WITH &&)
);
```
