---
name: relationships
description: Database relationship types and implementation
category: database/design
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Database Relationships

## Overview

Understanding relationship types and how to implement them correctly
is fundamental to relational database design.

## Relationship Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    Relationship Types                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  One-to-One (1:1)                                               │
│  ├── User ←→ Profile                                            │
│  └── Each user has exactly one profile                          │
│                                                                  │
│  One-to-Many (1:N)                                              │
│  ├── User → Orders                                              │
│  └── One user has many orders                                   │
│                                                                  │
│  Many-to-Many (M:N)                                             │
│  ├── Students ↔ Courses                                         │
│  └── Students enroll in many courses, courses have many students│
│                                                                  │
│  Self-Referencing                                               │
│  ├── Employee → Manager (Employee)                              │
│  └── Entity references itself                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## One-to-One (1:1)

### When to Use
- Splitting large tables for performance
- Separating optional/rarely accessed data
- Security (different access levels)
- Vertical table partitioning

### Implementation Options

```sql
-- Option 1: Shared Primary Key (tight coupling)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL
);

CREATE TABLE user_profiles (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  bio TEXT,
  avatar_url VARCHAR(500),
  website VARCHAR(255),
  location VARCHAR(100)
);

-- Query with join
SELECT u.email, p.bio, p.avatar_url
FROM users u
LEFT JOIN user_profiles p ON u.id = p.user_id
WHERE u.id = 'user-uuid';

-- Option 2: Foreign Key with Unique Constraint (more flexible)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE user_settings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  theme VARCHAR(20) DEFAULT 'light',
  notifications_enabled BOOLEAN DEFAULT true,
  language VARCHAR(10) DEFAULT 'en'
);

-- Option 3: Same Table (if always accessed together)
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email VARCHAR(255) NOT NULL UNIQUE,
  -- Profile data in same table
  bio TEXT,
  avatar_url VARCHAR(500),
  -- Settings in same table
  theme VARCHAR(20) DEFAULT 'light',
  language VARCHAR(10) DEFAULT 'en'
);
```

### Real-World Examples

```sql
-- Separate sensitive data
CREATE TABLE employees (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  department VARCHAR(100)
);

CREATE TABLE employee_salaries (
  employee_id UUID PRIMARY KEY REFERENCES employees(id),
  salary DECIMAL(12, 2),
  bank_account VARCHAR(50),
  tax_id VARCHAR(20)
);
-- Different access permissions on salary table

-- Split for performance (large blob data)
CREATE TABLE documents (
  id UUID PRIMARY KEY,
  title VARCHAR(255),
  mime_type VARCHAR(100),
  size_bytes BIGINT,
  created_at TIMESTAMPTZ
);

CREATE TABLE document_contents (
  document_id UUID PRIMARY KEY REFERENCES documents(id),
  content BYTEA
);
-- Query metadata without loading content
```

## One-to-Many (1:N)

### When to Use
- Parent-child relationships
- Most common relationship type
- One entity "owns" multiple of another

### Implementation

```sql
-- Basic one-to-many
CREATE TABLE customers (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  customer_id UUID NOT NULL REFERENCES customers(id),
  total DECIMAL(12, 2) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_orders_customer ON orders(customer_id);

-- Query customer with orders
SELECT
  c.name,
  c.email,
  COUNT(o.id) as order_count,
  SUM(o.total) as total_spent
FROM customers c
LEFT JOIN orders o ON c.id = o.customer_id
GROUP BY c.id;

-- Get customer's orders
SELECT * FROM orders
WHERE customer_id = 'customer-uuid'
ORDER BY created_at DESC;
```

### Optional vs Required Relationships

```sql
-- Required relationship (NOT NULL)
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  customer_id UUID NOT NULL REFERENCES customers(id),  -- Must have customer
  ...
);

-- Optional relationship (NULL allowed)
CREATE TABLE articles (
  id UUID PRIMARY KEY,
  author_id UUID REFERENCES users(id) ON DELETE SET NULL,  -- Can be anonymous
  title VARCHAR(255) NOT NULL
);

-- With default
CREATE TABLE comments (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id) DEFAULT NULL,  -- Anonymous allowed
  ...
);
```

### Cascading Actions

```sql
-- CASCADE: Delete children when parent deleted
CREATE TABLE order_items (
  id UUID PRIMARY KEY,
  order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID NOT NULL,
  quantity INTEGER
);
-- Deleting order automatically deletes its items

-- SET NULL: Set FK to null when parent deleted
CREATE TABLE articles (
  id UUID PRIMARY KEY,
  category_id UUID REFERENCES categories(id) ON DELETE SET NULL
);
-- Deleting category leaves articles without category

-- RESTRICT: Prevent parent deletion if children exist
CREATE TABLE categories (
  id UUID PRIMARY KEY,
  name VARCHAR(100)
);

CREATE TABLE products (
  id UUID PRIMARY KEY,
  category_id UUID REFERENCES categories(id) ON DELETE RESTRICT
);
-- Cannot delete category if products exist
```

## Many-to-Many (M:N)

### Implementation with Junction Table

```sql
-- Main entities
CREATE TABLE students (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) UNIQUE
);

CREATE TABLE courses (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title VARCHAR(255) NOT NULL,
  credits INTEGER DEFAULT 3
);

-- Junction table (enrollment)
CREATE TABLE student_courses (
  student_id UUID REFERENCES students(id) ON DELETE CASCADE,
  course_id UUID REFERENCES courses(id) ON DELETE CASCADE,
  enrolled_at TIMESTAMPTZ DEFAULT NOW(),
  grade VARCHAR(2),
  status VARCHAR(20) DEFAULT 'enrolled',
  PRIMARY KEY (student_id, course_id)
);

-- Indexes for efficient queries from both directions
CREATE INDEX idx_student_courses_student ON student_courses(student_id);
CREATE INDEX idx_student_courses_course ON student_courses(course_id);

-- Get student's courses
SELECT c.*, sc.grade, sc.enrolled_at
FROM courses c
JOIN student_courses sc ON c.id = sc.course_id
WHERE sc.student_id = 'student-uuid';

-- Get course's students
SELECT s.*, sc.grade
FROM students s
JOIN student_courses sc ON s.id = sc.student_id
WHERE sc.course_id = 'course-uuid';

-- Count enrollments
SELECT
  c.title,
  COUNT(sc.student_id) as enrollment_count
FROM courses c
LEFT JOIN student_courses sc ON c.id = sc.course_id
GROUP BY c.id;
```

### Junction Table with Extra Data

```sql
-- E-commerce: Products and Tags with additional metadata
CREATE TABLE products (
  id UUID PRIMARY KEY,
  name VARCHAR(255)
);

CREATE TABLE tags (
  id UUID PRIMARY KEY,
  name VARCHAR(50) UNIQUE
);

CREATE TABLE product_tags (
  product_id UUID REFERENCES products(id) ON DELETE CASCADE,
  tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
  -- Extra relationship data
  added_by UUID REFERENCES users(id),
  added_at TIMESTAMPTZ DEFAULT NOW(),
  is_primary BOOLEAN DEFAULT false,
  PRIMARY KEY (product_id, tag_id)
);

-- Order: Users and Products with order details
CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
  product_id UUID REFERENCES products(id),
  -- Relationship-specific data
  quantity INTEGER NOT NULL,
  unit_price DECIMAL(10, 2) NOT NULL,
  discount_percent DECIMAL(5, 2) DEFAULT 0,
  notes TEXT
);
```

### Self-Referencing Many-to-Many

```sql
-- Social network: Friends (bidirectional)
CREATE TABLE friendships (
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  friend_id UUID REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (user_id, friend_id),
  CHECK (user_id < friend_id)  -- Prevent duplicates like (A,B) and (B,A)
);

-- Get user's friends
SELECT u.*
FROM users u
JOIN friendships f ON u.id = f.friend_id OR u.id = f.user_id
WHERE (f.user_id = 'user-uuid' OR f.friend_id = 'user-uuid')
  AND u.id != 'user-uuid'
  AND f.status = 'accepted';

-- Following (directional)
CREATE TABLE follows (
  follower_id UUID REFERENCES users(id) ON DELETE CASCADE,
  following_id UUID REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  PRIMARY KEY (follower_id, following_id)
);

-- Get followers
SELECT u.* FROM users u
JOIN follows f ON u.id = f.follower_id
WHERE f.following_id = 'user-uuid';

-- Get following
SELECT u.* FROM users u
JOIN follows f ON u.id = f.following_id
WHERE f.follower_id = 'user-uuid';
```

## Self-Referencing Relationships

### Hierarchical (Parent-Child)

```sql
-- Organization hierarchy
CREATE TABLE employees (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  manager_id UUID REFERENCES employees(id) ON DELETE SET NULL,
  title VARCHAR(100),
  hire_date DATE
);

CREATE INDEX idx_employees_manager ON employees(manager_id);

-- Get employee with manager
SELECT
  e.name as employee,
  e.title,
  m.name as manager_name
FROM employees e
LEFT JOIN employees m ON e.manager_id = m.id;

-- Get direct reports
SELECT * FROM employees
WHERE manager_id = 'manager-uuid';

-- Recursive: Get all reports (direct and indirect)
WITH RECURSIVE all_reports AS (
  -- Direct reports
  SELECT id, name, manager_id, 1 as level
  FROM employees
  WHERE manager_id = 'manager-uuid'

  UNION ALL

  -- Indirect reports
  SELECT e.id, e.name, e.manager_id, ar.level + 1
  FROM employees e
  JOIN all_reports ar ON e.manager_id = ar.id
)
SELECT * FROM all_reports ORDER BY level, name;
```

### Category Tree

```sql
CREATE TABLE categories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  parent_id UUID REFERENCES categories(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  slug VARCHAR(100) NOT NULL,
  depth INTEGER DEFAULT 0,
  path TEXT,  -- Materialized path for fast queries
  UNIQUE (parent_id, slug)
);

-- Trigger to maintain depth and path
CREATE OR REPLACE FUNCTION update_category_path()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.parent_id IS NULL THEN
    NEW.depth = 0;
    NEW.path = '/' || NEW.id::text;
  ELSE
    SELECT depth + 1, path || '/' || NEW.id::text
    INTO NEW.depth, NEW.path
    FROM categories WHERE id = NEW.parent_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER category_path_trigger
  BEFORE INSERT OR UPDATE OF parent_id ON categories
  FOR EACH ROW
  EXECUTE FUNCTION update_category_path();

-- Get all descendants
SELECT * FROM categories
WHERE path LIKE (SELECT path FROM categories WHERE id = 'parent-uuid') || '/%';

-- Get ancestors
WITH RECURSIVE ancestors AS (
  SELECT * FROM categories WHERE id = 'child-uuid'
  UNION ALL
  SELECT c.* FROM categories c
  JOIN ancestors a ON c.id = a.parent_id
)
SELECT * FROM ancestors;
```

## Relationship Best Practices

```sql
-- 1. Always index foreign keys
CREATE INDEX idx_orders_customer ON orders(customer_id);

-- 2. Choose appropriate ON DELETE action
ON DELETE CASCADE   -- Child depends on parent (order_items)
ON DELETE SET NULL  -- Child can exist without parent (articles.author)
ON DELETE RESTRICT  -- Protect referenced data (products.category)

-- 3. Use composite primary keys for junction tables
PRIMARY KEY (student_id, course_id)

-- 4. Add timestamps to junction tables for auditing
created_at TIMESTAMPTZ DEFAULT NOW()

-- 5. Consider soft deletes for important relationships
deleted_at TIMESTAMPTZ  -- NULL means not deleted

-- 6. Use CHECK constraints for self-referencing
CHECK (id != parent_id)  -- Prevent self-reference

-- 7. Document relationships in comments
COMMENT ON COLUMN orders.customer_id IS 'References customers.id - customer who placed order';
```
