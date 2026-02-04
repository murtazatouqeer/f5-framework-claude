---
name: data-modeling
description: Data modeling techniques and ER diagrams
category: database/design
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Data Modeling

## Overview

Data modeling is the process of creating a visual representation of
data structures and their relationships. Good models ensure data
integrity, reduce redundancy, and support efficient queries.

## Modeling Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Modeling Levels                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Conceptual Model (What)                                        │
│  ├── Entities and relationships                                 │
│  ├── Business-focused                                           │
│  └── No technical details                                       │
│                                                                  │
│  Logical Model (How, abstractly)                                │
│  ├── Attributes and data types                                  │
│  ├── Primary and foreign keys                                   │
│  └── Database-agnostic                                          │
│                                                                  │
│  Physical Model (How, specifically)                             │
│  ├── Tables, columns, indexes                                   │
│  ├── Database-specific syntax                                   │
│  └── Performance considerations                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Entity-Relationship Diagrams

### ER Notation

```
┌─────────────────────────────────────────────────────────────────┐
│                    ER Diagram Symbols                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Entity (Rectangle)                                              │
│  ┌─────────────┐                                                │
│  │   Customer  │                                                │
│  └─────────────┘                                                │
│                                                                  │
│  Attribute (Oval)                                               │
│       ○ name                                                    │
│                                                                  │
│  Primary Key (Underlined)                                       │
│       _id_                                                      │
│                                                                  │
│  Relationship (Diamond)                                         │
│  Customer ──◇── places ──◇── Order                             │
│                                                                  │
│  Cardinality:                                                   │
│  ──||──  One (mandatory)                                        │
│  ──|○──  Zero or one                                            │
│  ──<──   Many                                                   │
│  ──○<──  Zero or many                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Cardinality Notation (Crow's Foot)

```
One-to-One (1:1)
┌──────────┐        ┌──────────┐
│   User   │──────||│  Profile │
└──────────┘        └──────────┘
Each user has exactly one profile

One-to-Many (1:N)
┌──────────┐        ┌──────────┐
│   User   │──────<│  Order   │
└──────────┘        └──────────┘
One user has many orders

Many-to-Many (M:N)
┌──────────┐        ┌──────────┐
│ Student  │>──────<│  Course  │
└──────────┘        └──────────┘
Students enroll in many courses, courses have many students
```

## E-Commerce Example

### Conceptual Model

```
┌─────────────────────────────────────────────────────────────────┐
│                E-Commerce Conceptual Model                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐                      ┌──────────┐                 │
│  │ Customer │──places──────────────│  Order   │                 │
│  └──────────┘                      └──────────┘                 │
│       │                                 │                       │
│       │                                 │                       │
│       │ has                       contains                      │
│       │                                 │                       │
│       ▼                                 ▼                       │
│  ┌──────────┐                    ┌───────────┐                 │
│  │ Address  │                    │ OrderItem │                 │
│  └──────────┘                    └───────────┘                 │
│                                        │                       │
│                                        │ references            │
│                                        ▼                       │
│                                  ┌──────────┐                  │
│                                  │ Product  │                  │
│                                  └──────────┘                  │
│                                        │                       │
│                                        │ belongs to            │
│                                        ▼                       │
│                                  ┌──────────┐                  │
│                                  │ Category │                  │
│                                  └──────────┘                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Logical Model

```
┌─────────────────────────────────────────────────────────────────┐
│                E-Commerce Logical Model                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  customers                    orders                            │
│  ──────────                   ──────                            │
│  • id (PK)                    • id (PK)                        │
│  • email                      • customer_id (FK)               │
│  • name                       • status                         │
│  • created_at                 • total                          │
│        │                      • created_at                     │
│        │ 1:N                       │                           │
│        └───────────────────────────┘                           │
│                                    │                           │
│                                    │ 1:N                       │
│                               order_items                      │
│                               ───────────                      │
│                               • id (PK)                        │
│                               • order_id (FK)                  │
│                               • product_id (FK)                │
│                               • quantity                       │
│                               • price                          │
│                                    │                           │
│                                    │ N:1                       │
│  products                          │       categories          │
│  ────────                          │       ──────────          │
│  • id (PK)  ◄──────────────────────┘       • id (PK)          │
│  • category_id (FK) ────────────────────── • parent_id (FK)   │
│  • name                                    • name              │
│  • price                                   • slug              │
│  • stock                                                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Physical Model (PostgreSQL)

```sql
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_id UUID REFERENCES categories(id),
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  category_id UUID REFERENCES categories(id),
  name VARCHAR(255) NOT NULL,
  price DECIMAL(10, 2) NOT NULL,
  stock INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id),
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  total DECIMAL(12, 2) NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID NOT NULL REFERENCES products(id),
  quantity INTEGER NOT NULL,
  price DECIMAL(10, 2) NOT NULL
);
```

## Domain Modeling

### Identify Entities

```
Questions to identify entities:
• What things does the business track?
• What are the main nouns in requirements?
• What has a distinct identity?

E-commerce example:
- Customer: Has account, places orders
- Product: Items for sale
- Order: Purchase transaction
- OrderItem: Line items in order
- Category: Product classification
- Address: Shipping/billing location
- Payment: Transaction record
- Review: Customer feedback
```

### Define Attributes

```
For each entity, ask:
• What data do we need to store?
• What data type is appropriate?
• Is the attribute required?
• What are the constraints?

Product attributes:
- id: UUID, primary key
- sku: String, unique, required
- name: String, required, max 255 chars
- description: Text, optional
- price: Decimal, required, >= 0
- cost: Decimal, optional, >= 0
- stock: Integer, required, >= 0
- weight: Integer, optional (grams)
- status: Enum (draft, active, archived)
- created_at: Timestamp, auto-set
- updated_at: Timestamp, auto-update
```

### Establish Relationships

```
Relationship analysis:
• How do entities relate to each other?
• What is the cardinality?
• Is the relationship optional or mandatory?
• What happens on delete?

Customer → Order (1:N)
- One customer places many orders
- Order requires customer (mandatory)
- On customer delete: preserve orders (SET NULL or RESTRICT)

Order → OrderItem (1:N)
- One order contains many items
- Item requires order (mandatory)
- On order delete: cascade delete items

Product → Category (N:1)
- Many products in one category
- Category is optional
- On category delete: SET NULL

Product ↔ Tag (M:N)
- Products have many tags
- Tags apply to many products
- Junction table: product_tags
```

## Advanced Modeling Patterns

### Polymorphic Associations

```sql
-- Problem: Comments on multiple entity types

-- Option 1: Separate tables (recommended)
CREATE TABLE article_comments (
  id UUID PRIMARY KEY,
  article_id UUID REFERENCES articles(id),
  content TEXT,
  created_at TIMESTAMPTZ
);

CREATE TABLE product_comments (
  id UUID PRIMARY KEY,
  product_id UUID REFERENCES products(id),
  content TEXT,
  created_at TIMESTAMPTZ
);

-- Option 2: Polymorphic (flexible, no FK constraint)
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  commentable_type VARCHAR(50) NOT NULL,  -- 'Article' or 'Product'
  commentable_id UUID NOT NULL,
  content TEXT,
  created_at TIMESTAMPTZ,
  -- No FK constraint possible
  CONSTRAINT valid_type CHECK (commentable_type IN ('Article', 'Product'))
);

CREATE INDEX idx_comments_target ON comments(commentable_type, commentable_id);

-- Option 3: Multiple nullable FKs
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  article_id UUID REFERENCES articles(id),
  product_id UUID REFERENCES products(id),
  content TEXT,
  created_at TIMESTAMPTZ,
  -- Exactly one must be set
  CHECK (
    (article_id IS NOT NULL AND product_id IS NULL) OR
    (article_id IS NULL AND product_id IS NOT NULL)
  )
);
```

### Hierarchical Data

```sql
-- Adjacency List (simple, recursive queries)
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  parent_id UUID REFERENCES categories(id),
  name VARCHAR(100)
);

-- With recursive query for tree
WITH RECURSIVE category_tree AS (
  SELECT id, name, parent_id, 1 as level
  FROM categories WHERE parent_id IS NULL
  UNION ALL
  SELECT c.id, c.name, c.parent_id, ct.level + 1
  FROM categories c JOIN category_tree ct ON c.parent_id = ct.id
)
SELECT * FROM category_tree;

-- Materialized Path (fast reads)
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(100),
  path TEXT NOT NULL,  -- '/root/parent/child'
  depth INTEGER NOT NULL
);

-- Find all descendants
SELECT * FROM categories WHERE path LIKE '/electronics/%';

-- Nested Sets (complex updates, fast subtree queries)
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(100),
  lft INTEGER NOT NULL,
  rgt INTEGER NOT NULL
);

-- Find all descendants
SELECT * FROM categories WHERE lft > 1 AND rgt < 10;

-- Closure Table (flexible, extra space)
CREATE TABLE category_paths (
  ancestor_id UUID REFERENCES categories(id),
  descendant_id UUID REFERENCES categories(id),
  depth INTEGER NOT NULL,
  PRIMARY KEY (ancestor_id, descendant_id)
);
```

### Temporal Data

```sql
-- Temporal table (history of changes)
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  price DECIMAL(10, 2)
);

CREATE TABLE products_history (
  id UUID,
  name VARCHAR(255),
  price DECIMAL(10, 2),
  valid_from TIMESTAMPTZ NOT NULL,
  valid_to TIMESTAMPTZ,
  PRIMARY KEY (id, valid_from)
);

-- Trigger to capture history
CREATE OR REPLACE FUNCTION record_product_history()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    UPDATE products_history
    SET valid_to = NOW()
    WHERE id = OLD.id AND valid_to IS NULL;

    INSERT INTO products_history (id, name, price, valid_from)
    VALUES (NEW.id, NEW.name, NEW.price, NOW());
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Query historical data
SELECT * FROM products_history
WHERE id = 'product-uuid'
  AND valid_from <= '2024-01-15'
  AND (valid_to IS NULL OR valid_to > '2024-01-15');
```

### Event Sourcing

```sql
-- Event store
CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  stream_id UUID NOT NULL,
  stream_type VARCHAR(100) NOT NULL,
  event_type VARCHAR(100) NOT NULL,
  event_data JSONB NOT NULL,
  metadata JSONB DEFAULT '{}',
  version INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (stream_id, version)
);

CREATE INDEX idx_events_stream ON events(stream_id, version);

-- Snapshot for performance
CREATE TABLE snapshots (
  stream_id UUID PRIMARY KEY,
  stream_type VARCHAR(100) NOT NULL,
  state JSONB NOT NULL,
  version INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Example: Order events
INSERT INTO events (stream_id, stream_type, event_type, event_data, version)
VALUES
  ('order-uuid', 'Order', 'OrderCreated', '{"items": [...]}', 1),
  ('order-uuid', 'Order', 'PaymentReceived', '{"amount": 99.99}', 2),
  ('order-uuid', 'Order', 'OrderShipped', '{"tracking": "..."}', 3);
```

## Modeling Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Data Modeling Checklist                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✓ Identify all entities from requirements                      │
│  ✓ Define primary keys for each entity                         │
│  ✓ Document all relationships with cardinality                 │
│  ✓ Normalize to at least 3NF                                   │
│  ✓ Add appropriate constraints (NOT NULL, CHECK, UNIQUE)       │
│  ✓ Plan for soft deletes if needed                             │
│  ✓ Include audit fields (created_at, updated_at)               │
│  ✓ Consider future query patterns                              │
│  ✓ Plan for data growth and archival                           │
│  ✓ Review with stakeholders before implementation              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
