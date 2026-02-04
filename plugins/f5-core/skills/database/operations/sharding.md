---
name: sharding
description: Database sharding strategies and implementation
category: database/operations
applies_to: [postgresql, mysql]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Database Sharding

## Overview

Sharding horizontally partitions data across multiple database instances
(shards). Each shard contains a subset of the data, allowing the system
to scale beyond a single server's capacity.

## When to Shard

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sharding Decision Matrix                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Consider Sharding When:                                        │
│  ✓ Single server can't handle write load                       │
│  ✓ Data size exceeds single server storage                     │
│  ✓ Read replicas can't handle read load                        │
│  ✓ Regulatory requirements (data locality)                     │
│                                                                  │
│  Try These First:                                                │
│  1. Optimize queries and indexes                                │
│  2. Add read replicas                                           │
│  3. Vertical scaling (bigger server)                            │
│  4. Caching layer (Redis)                                       │
│  5. Archive old data                                            │
│                                                                  │
│  Sharding Complexity:                                           │
│  ✗ Cross-shard queries difficult                               │
│  ✗ Joins across shards very expensive                          │
│  ✗ Transactions across shards complex                          │
│  ✗ Rebalancing is painful                                      │
│  ✗ Application changes required                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Sharding Strategies

### Hash-Based Sharding

```typescript
// Distribute data evenly using hash of shard key
class HashSharding {
  private shardCount: number;

  constructor(shardCount: number) {
    this.shardCount = shardCount;
  }

  getShardId(key: string): number {
    // Simple hash function
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = ((hash << 5) - hash) + key.charCodeAt(i);
      hash = hash & hash;  // Convert to 32-bit integer
    }
    return Math.abs(hash) % this.shardCount;
  }
}

// Usage
const sharding = new HashSharding(4);
const userId = 'user-12345';
const shardId = sharding.getShardId(userId);  // Returns 0-3

// Route to correct shard
const connection = shardConnections[shardId];
await connection.query('SELECT * FROM users WHERE id = $1', [userId]);
```

### Range-Based Sharding

```typescript
// Distribute data by ranges of shard key
class RangeSharding {
  private ranges: { min: number; max: number; shardId: number }[];

  constructor() {
    this.ranges = [
      { min: 0, max: 999999, shardId: 0 },
      { min: 1000000, max: 1999999, shardId: 1 },
      { min: 2000000, max: 2999999, shardId: 2 },
      { min: 3000000, max: Infinity, shardId: 3 },
    ];
  }

  getShardId(userId: number): number {
    for (const range of this.ranges) {
      if (userId >= range.min && userId <= range.max) {
        return range.shardId;
      }
    }
    throw new Error('User ID out of range');
  }
}

// Good for: Time-based data, sequential IDs
// Issue: Hot spots if data isn't evenly distributed
```

### Geographic Sharding

```typescript
// Distribute data by geographic region
const regionShards = {
  'us-east': {
    host: 'us-east-db.example.com',
    regions: ['US-NY', 'US-VA', 'US-FL'],
  },
  'us-west': {
    host: 'us-west-db.example.com',
    regions: ['US-CA', 'US-WA', 'US-OR'],
  },
  'eu': {
    host: 'eu-db.example.com',
    regions: ['DE', 'FR', 'GB', 'NL'],
  },
  'asia': {
    host: 'asia-db.example.com',
    regions: ['JP', 'SG', 'KR', 'AU'],
  },
};

function getShardByRegion(userRegion: string): string {
  for (const [shardName, config] of Object.entries(regionShards)) {
    if (config.regions.includes(userRegion)) {
      return shardName;
    }
  }
  return 'us-east';  // Default
}
```

### Directory-Based Sharding

```typescript
// Lookup table maps keys to shards
class DirectorySharding {
  private directory: Map<string, number>;

  async getShardId(userId: string): Promise<number> {
    // Check cache first
    if (this.directory.has(userId)) {
      return this.directory.get(userId)!;
    }

    // Lookup in directory database
    const result = await directoryDb.query(
      'SELECT shard_id FROM shard_directory WHERE user_id = $1',
      [userId]
    );

    if (result.rows.length > 0) {
      const shardId = result.rows[0].shard_id;
      this.directory.set(userId, shardId);
      return shardId;
    }

    // Assign new shard (round-robin, least-loaded, etc.)
    const newShardId = await this.assignNewShard(userId);
    return newShardId;
  }

  private async assignNewShard(userId: string): Promise<number> {
    // Get least-loaded shard
    const result = await directoryDb.query(`
      SELECT shard_id, COUNT(*) as user_count
      FROM shard_directory
      GROUP BY shard_id
      ORDER BY user_count ASC
      LIMIT 1
    `);

    const shardId = result.rows[0]?.shard_id ?? 0;

    // Record assignment
    await directoryDb.query(
      'INSERT INTO shard_directory (user_id, shard_id) VALUES ($1, $2)',
      [userId, shardId]
    );

    return shardId;
  }
}
```

## Shard Key Selection

```
┌─────────────────────────────────────────────────────────────────┐
│                  Shard Key Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Good Shard Keys:                                                │
│  ✓ High cardinality (many unique values)                       │
│  ✓ Even distribution                                           │
│  ✓ Frequently used in queries                                  │
│  ✓ Immutable (doesn't change)                                  │
│  ✓ Present in most queries                                     │
│                                                                  │
│  Examples:                                                       │
│  - user_id for user data                                        │
│  - tenant_id for multi-tenant apps                              │
│  - region for geographic data                                   │
│  - order_id for order data                                      │
│                                                                  │
│  Bad Shard Keys:                                                 │
│  ✗ Low cardinality (status, boolean)                           │
│  ✗ Monotonically increasing (auto-increment)                   │
│  ✗ Frequently updated values                                   │
│  ✗ Not used in queries (requires scatter-gather)               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Application-Level Sharding

### Router Implementation

```typescript
import { Pool, PoolClient } from 'pg';

interface ShardConfig {
  host: string;
  port: number;
  database: string;
  user: string;
  password: string;
}

class ShardRouter {
  private shards: Map<number, Pool> = new Map();
  private shardCount: number;

  constructor(shardConfigs: ShardConfig[]) {
    this.shardCount = shardConfigs.length;

    shardConfigs.forEach((config, index) => {
      this.shards.set(index, new Pool(config));
    });
  }

  private hashKey(key: string): number {
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = ((hash << 5) - hash) + key.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash) % this.shardCount;
  }

  getPool(shardKey: string): Pool {
    const shardId = this.hashKey(shardKey);
    return this.shards.get(shardId)!;
  }

  // Query single shard
  async query(shardKey: string, sql: string, params?: any[]) {
    const pool = this.getPool(shardKey);
    return pool.query(sql, params);
  }

  // Query all shards (scatter-gather)
  async queryAll(sql: string, params?: any[]) {
    const promises = Array.from(this.shards.values()).map(pool =>
      pool.query(sql, params)
    );

    const results = await Promise.all(promises);
    return results.flatMap(r => r.rows);
  }

  // Transaction within single shard
  async transaction<T>(
    shardKey: string,
    callback: (client: PoolClient) => Promise<T>
  ): Promise<T> {
    const pool = this.getPool(shardKey);
    const client = await pool.connect();

    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async close() {
    for (const pool of this.shards.values()) {
      await pool.end();
    }
  }
}

// Usage
const router = new ShardRouter([
  { host: 'shard0.example.com', port: 5432, database: 'mydb', user: 'app', password: 'pass' },
  { host: 'shard1.example.com', port: 5432, database: 'mydb', user: 'app', password: 'pass' },
  { host: 'shard2.example.com', port: 5432, database: 'mydb', user: 'app', password: 'pass' },
  { host: 'shard3.example.com', port: 5432, database: 'mydb', user: 'app', password: 'pass' },
]);

// Single-shard query (fast)
const user = await router.query(userId, 'SELECT * FROM users WHERE id = $1', [userId]);

// All-shard query (slow, avoid if possible)
const allUsers = await router.queryAll('SELECT * FROM users WHERE status = $1', ['active']);

// Transaction
await router.transaction(userId, async (client) => {
  await client.query('UPDATE accounts SET balance = balance - $1 WHERE user_id = $2', [100, userId]);
  await client.query('INSERT INTO transactions (user_id, amount) VALUES ($1, $2)', [userId, -100]);
});
```

## PostgreSQL Citus (Distributed PostgreSQL)

### Installation and Setup

```sql
-- Install Citus extension
CREATE EXTENSION citus;

-- Add worker nodes
SELECT citus_add_node('worker1.example.com', 5432);
SELECT citus_add_node('worker2.example.com', 5432);

-- Check cluster status
SELECT * FROM citus_get_active_worker_nodes();
```

### Create Distributed Tables

```sql
-- Create table normally first
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  total DECIMAL(12, 2) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Distribute by user_id
SELECT create_distributed_table('orders', 'user_id');

-- Create reference table (small, replicated to all nodes)
CREATE TABLE order_statuses (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) NOT NULL
);
SELECT create_reference_table('order_statuses');

-- Colocate related tables
CREATE TABLE order_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID NOT NULL,
  user_id UUID NOT NULL,  -- Must include distribution column
  product_id UUID NOT NULL,
  quantity INTEGER NOT NULL
);
SELECT create_distributed_table('order_items', 'user_id', colocate_with => 'orders');
```

### Querying Distributed Tables

```sql
-- Single-shard query (fast)
SELECT * FROM orders WHERE user_id = 'user-uuid';

-- Cross-shard query with aggregation
SELECT status, COUNT(*), SUM(total)
FROM orders
GROUP BY status;

-- Join colocated tables (fast, within shard)
SELECT o.*, oi.*
FROM orders o
JOIN order_items oi ON o.id = oi.order_id AND o.user_id = oi.user_id
WHERE o.user_id = 'user-uuid';

-- Join with reference table (fast)
SELECT o.*, s.name as status_name
FROM orders o
JOIN order_statuses s ON o.status = s.name
WHERE o.user_id = 'user-uuid';
```

## Cross-Shard Operations

### Scatter-Gather Pattern

```typescript
// Query all shards and aggregate results
async function getGlobalStats(): Promise<Stats> {
  const shardResults = await router.queryAll(`
    SELECT
      COUNT(*) as order_count,
      SUM(total) as total_revenue,
      AVG(total) as avg_order
    FROM orders
    WHERE created_at > NOW() - INTERVAL '30 days'
  `);

  // Aggregate results from all shards
  return shardResults.reduce((acc, result) => ({
    orderCount: acc.orderCount + parseInt(result.order_count),
    totalRevenue: acc.totalRevenue + parseFloat(result.total_revenue),
    avgOrder: 0,  // Recalculate after
  }), { orderCount: 0, totalRevenue: 0, avgOrder: 0 });
}
```

### Global Secondary Index

```sql
-- Create a lookup table that spans all shards
CREATE TABLE user_email_index (
  email VARCHAR(255) PRIMARY KEY,
  user_id UUID NOT NULL,
  shard_id INTEGER NOT NULL
);

-- Application maintains this during user creation
async function createUser(user: User) {
  const shardId = router.hashKey(user.id);

  await directoryDb.query(
    'INSERT INTO user_email_index (email, user_id, shard_id) VALUES ($1, $2, $3)',
    [user.email, user.id, shardId]
  );

  await router.query(user.id,
    'INSERT INTO users (id, email, name) VALUES ($1, $2, $3)',
    [user.id, user.email, user.name]
  );
}

// Lookup by email
async function getUserByEmail(email: string): Promise<User | null> {
  const lookup = await directoryDb.query(
    'SELECT user_id, shard_id FROM user_email_index WHERE email = $1',
    [email]
  );

  if (lookup.rows.length === 0) return null;

  const { user_id, shard_id } = lookup.rows[0];
  const result = await router.query(user_id,
    'SELECT * FROM users WHERE id = $1',
    [user_id]
  );

  return result.rows[0] || null;
}
```

## Resharding

### Adding Shards

```typescript
// With Citus
// SELECT citus_add_node('new-worker.example.com', 5432);
// SELECT rebalance_table_shards();

// Application-level: Consistent hashing approach
class ConsistentHashRing {
  private ring: Map<number, string> = new Map();
  private sortedKeys: number[] = [];
  private replicas: number = 100;

  addNode(node: string) {
    for (let i = 0; i < this.replicas; i++) {
      const key = this.hash(`${node}:${i}`);
      this.ring.set(key, node);
      this.sortedKeys.push(key);
    }
    this.sortedKeys.sort((a, b) => a - b);
  }

  removeNode(node: string) {
    for (let i = 0; i < this.replicas; i++) {
      const key = this.hash(`${node}:${i}`);
      this.ring.delete(key);
      this.sortedKeys = this.sortedKeys.filter(k => k !== key);
    }
  }

  getNode(key: string): string {
    const hash = this.hash(key);
    const idx = this.sortedKeys.findIndex(k => k >= hash);
    const ringKey = this.sortedKeys[idx >= 0 ? idx : 0];
    return this.ring.get(ringKey)!;
  }

  private hash(key: string): number {
    // Use proper hash function (e.g., MurmurHash)
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = ((hash << 5) - hash) + key.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash);
  }
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Sharding Best Practices                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Exhaust Other Options First                                 │
│     - Sharding is complex and hard to undo                      │
│     - Try optimization, caching, replicas first                 │
│                                                                  │
│  2. Choose Shard Key Carefully                                  │
│     - Difficult to change later                                 │
│     - Affects all query patterns                                │
│                                                                  │
│  3. Design for Single-Shard Queries                             │
│     - Include shard key in all queries                          │
│     - Avoid cross-shard joins                                   │
│                                                                  │
│  4. Colocate Related Data                                       │
│     - Keep related tables on same shard                         │
│     - Enables local joins and transactions                      │
│                                                                  │
│  5. Plan for Growth                                             │
│     - Design for 10x current size                               │
│     - Use consistent hashing for easier resharding              │
│                                                                  │
│  6. Monitor Shard Balance                                       │
│     - Track data size per shard                                 │
│     - Rebalance before hot spots become critical                │
│                                                                  │
│  7. Test Cross-Shard Operations                                 │
│     - Understand performance implications                       │
│     - Have fallback strategies                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```
