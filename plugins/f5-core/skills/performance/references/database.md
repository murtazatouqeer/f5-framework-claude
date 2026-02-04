# Database Performance Reference

## Query Analysis with EXPLAIN ANALYZE

### PostgreSQL EXPLAIN

```sql
-- Basic explain
EXPLAIN ANALYZE
SELECT u.*, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
WHERE u.status = 'active'
GROUP BY u.id;

-- Output interpretation:
-- Seq Scan: Full table scan (bad for large tables)
-- Index Scan: Using index (good)
-- Bitmap Index Scan: Multiple index conditions
-- Hash Join: In-memory join (fast)
-- Nested Loop: Row-by-row join (slow for large sets)
```

### Query Optimization Patterns

```sql
-- BAD: SELECT *
SELECT * FROM users WHERE id = 1;

-- GOOD: Select only needed columns
SELECT id, name, email FROM users WHERE id = 1;

-- BAD: Function on indexed column
SELECT * FROM users WHERE YEAR(created_at) = 2024;

-- GOOD: Range query on indexed column
SELECT * FROM users
WHERE created_at >= '2024-01-01'
  AND created_at < '2025-01-01';

-- BAD: OR on different columns
SELECT * FROM products
WHERE category_id = 5 OR brand_id = 10;

-- GOOD: UNION for different indexes
SELECT * FROM products WHERE category_id = 5
UNION ALL
SELECT * FROM products WHERE brand_id = 10 AND category_id != 5;
```

## Indexing Strategies

### Index Types

```sql
-- B-Tree (default, most common)
CREATE INDEX idx_users_email ON users(email);

-- Composite index (column order matters)
CREATE INDEX idx_orders_user_status
ON orders(user_id, status, created_at);

-- Partial index (filtered subset)
CREATE INDEX idx_active_users
ON users(email) WHERE status = 'active';

-- Covering index (includes all needed columns)
CREATE INDEX idx_orders_covering
ON orders(user_id, status) INCLUDE (total, created_at);

-- Hash index (equality only)
CREATE INDEX idx_sessions_token ON sessions USING HASH(token);

-- GIN index (arrays, JSONB, full-text)
CREATE INDEX idx_products_tags ON products USING GIN(tags);
```

### Index Selection Guide

| Query Pattern | Index Type |
|--------------|------------|
| `WHERE col = value` | B-Tree or Hash |
| `WHERE col > value` | B-Tree |
| `WHERE col LIKE 'prefix%'` | B-Tree |
| `ORDER BY col` | B-Tree |
| `WHERE col @> array` | GIN |
| `WHERE jsonb_col @> '{}'` | GIN |
| `Full-text search` | GIN/GiST |

## N+1 Query Problem

### Problem Pattern

```typescript
// BAD: N+1 queries (1 + N queries)
const users = await User.findAll();
for (const user of users) {
  // Executes N additional queries!
  const orders = await Order.findAll({ where: { userId: user.id } });
  user.orders = orders;
}
```

### Solutions

```typescript
// Sequelize: Eager loading
const users = await User.findAll({
  include: [{ model: Order, as: 'orders' }]
});

// Prisma: Include relations
const users = await prisma.user.findMany({
  include: { orders: true }
});

// TypeORM: Relations
const users = await userRepository.find({
  relations: ['orders']
});

// DataLoader: Batching (GraphQL)
const orderLoader = new DataLoader(async (userIds) => {
  const orders = await Order.findAll({
    where: { userId: userIds }
  });
  return userIds.map(id =>
    orders.filter(o => o.userId === id)
  );
});
```

## Connection Pooling

### Node.js with pg-pool

```typescript
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST,
  port: 5432,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,

  // Pool configuration
  min: 5,              // Minimum connections
  max: 20,             // Maximum connections
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

// Use pool
const result = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);
```

### Prisma Connection Pool

```typescript
// prisma/schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

// Connection string with pool settings
// DATABASE_URL="postgresql://user:pass@host:5432/db?connection_limit=20&pool_timeout=10"
```

## Query Caching

### Redis Query Cache

```typescript
import Redis from 'ioredis';

const redis = new Redis();

async function getCachedQuery<T>(
  key: string,
  queryFn: () => Promise<T>,
  ttlSeconds: number = 300
): Promise<T> {
  // Try cache first
  const cached = await redis.get(key);
  if (cached) {
    return JSON.parse(cached);
  }

  // Execute query
  const result = await queryFn();

  // Cache result
  await redis.setex(key, ttlSeconds, JSON.stringify(result));

  return result;
}

// Usage
const users = await getCachedQuery(
  'users:active:list',
  () => User.findAll({ where: { status: 'active' } }),
  60 // 1 minute TTL
);
```

### Cache Invalidation

```typescript
class CacheService {
  constructor(private redis: Redis) {}

  // Pattern-based invalidation
  async invalidatePattern(pattern: string): Promise<void> {
    const keys = await this.redis.keys(pattern);
    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }

  // Tag-based invalidation
  async invalidateByTag(tag: string): Promise<void> {
    const keys = await this.redis.smembers(`tag:${tag}`);
    if (keys.length > 0) {
      await this.redis.del(...keys);
      await this.redis.del(`tag:${tag}`);
    }
  }
}

// Usage: Invalidate all user-related cache
await cacheService.invalidatePattern('users:*');
```

## Batch Operations

### Bulk Insert

```typescript
// BAD: Individual inserts
for (const user of users) {
  await User.create(user);
}

// GOOD: Bulk insert
await User.bulkCreate(users, {
  ignoreDuplicates: true,
  updateOnDuplicate: ['name', 'email']
});

// Raw SQL bulk insert
const values = users.map(u => `('${u.name}', '${u.email}')`).join(',');
await sequelize.query(`
  INSERT INTO users (name, email)
  VALUES ${values}
  ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
`);
```

### Batch Updates

```typescript
// Update multiple records efficiently
await User.update(
  { status: 'inactive' },
  {
    where: {
      lastLoginAt: { [Op.lt]: thirtyDaysAgo }
    }
  }
);

// Batch update with CASE
await sequelize.query(`
  UPDATE products
  SET price = CASE id
    WHEN 1 THEN 10.99
    WHEN 2 THEN 20.99
    WHEN 3 THEN 30.99
  END
  WHERE id IN (1, 2, 3)
`);
```

## Read Replicas

### Prisma Read Replicas

```typescript
// Using Prisma with read replica
const prisma = new PrismaClient({
  datasources: {
    db: {
      url: process.env.DATABASE_URL_REPLICA
    }
  }
});

// Read from replica
const users = await prismaReplica.user.findMany();

// Write to primary
const newUser = await prismaPrimary.user.create({ data });
```

### TypeORM Replication

```typescript
// typeorm.config.ts
export default {
  type: 'postgres',
  replication: {
    master: {
      host: 'primary.db.com',
      port: 5432,
      username: 'user',
      password: 'pass',
      database: 'app'
    },
    slaves: [
      { host: 'replica1.db.com', port: 5432, username: 'user', password: 'pass', database: 'app' },
      { host: 'replica2.db.com', port: 5432, username: 'user', password: 'pass', database: 'app' }
    ]
  }
};
```
