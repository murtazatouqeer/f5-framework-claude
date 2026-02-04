# Database Fundamentals

ACID properties, normalization, CAP theorem, and database types.

## Table of Contents

1. [ACID Properties](#acid-properties)
2. [Normalization](#normalization)
3. [CAP Theorem](#cap-theorem)
4. [Database Types](#database-types)

---

## ACID Properties

### Overview

ACID guarantees reliable transaction processing even during failures.

```
┌─────────────────────────────────────────────────────────────┐
│                        ACID                                  │
├───────────────┬───────────────┬──────────────┬──────────────┤
│   Atomicity   │  Consistency  │  Isolation   │  Durability  │
│               │               │              │              │
│  All or       │  Valid state  │  Concurrent  │  Committed   │
│  Nothing      │  transitions  │  isolation   │  data stays  │
└───────────────┴───────────────┴──────────────┴──────────────┘
```

### Atomicity

All operations in a transaction succeed or all fail.

```typescript
async function transferMoney(from: string, to: string, amount: number) {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    // Debit sender
    const debit = await client.query(
      'UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1 RETURNING balance',
      [amount, from]
    );
    if (debit.rowCount === 0) throw new Error('Insufficient funds');

    // Credit receiver
    await client.query(
      'UPDATE accounts SET balance = balance + $1 WHERE id = $2',
      [amount, to]
    );

    await client.query('COMMIT');
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}
```

### Consistency

Transactions bring database from one valid state to another.

```sql
-- Define consistency rules with constraints
CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  balance DECIMAL(15, 2) NOT NULL DEFAULT 0,
  CONSTRAINT positive_balance CHECK (balance >= 0)
);

-- Transaction maintains consistency
BEGIN;
UPDATE accounts SET balance = balance - 100 WHERE id = 'acc-1';
UPDATE accounts SET balance = balance + 100 WHERE id = 'acc-2';
COMMIT;
```

### Isolation Levels

| Level | Dirty Read | Non-Repeatable | Phantom | Use Case |
|-------|------------|----------------|---------|----------|
| Read Uncommitted | Yes | Yes | Yes | Never use |
| Read Committed | No | Yes | Yes | Default, most apps |
| Repeatable Read | No | No | Yes | Reports, analytics |
| Serializable | No | No | No | Financial, inventory |

```typescript
// Set isolation level in Prisma
await prisma.$transaction(
  async (tx) => {
    // Critical financial operation
  },
  { isolationLevel: 'Serializable' }
);
```

### Durability

Committed data survives system failures via Write-Ahead Log (WAL).

```sql
-- Maximum durability (default)
SET synchronous_commit = on;

-- Faster but may lose recent commits on crash
SET synchronous_commit = off;
```

---

## Normalization

### Normal Forms

| Form | Rule | Violation Example |
|------|------|-------------------|
| 1NF | Atomic values | `phones: "123,456"` |
| 2NF | No partial dependencies | Non-key depends on part of composite key |
| 3NF | No transitive dependencies | `zip → city` when key is `user_id` |
| BCNF | Every determinant is key | Multiple overlapping candidate keys |

### First Normal Form (1NF)

```sql
-- VIOLATES 1NF: Multi-valued attribute
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  phones VARCHAR(500)  -- "123-4567,234-5678" - NOT ATOMIC
);

-- 1NF COMPLIANT: Separate table
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);

CREATE TABLE user_phones (
  user_id INT REFERENCES users(id),
  phone VARCHAR(20),
  PRIMARY KEY (user_id, phone)
);
```

### Second Normal Form (2NF)

```sql
-- VIOLATES 2NF: product_name depends only on product_id
CREATE TABLE order_items (
  order_id INT,
  product_id INT,
  product_name VARCHAR(100),  -- Partial dependency!
  quantity INT,
  PRIMARY KEY (order_id, product_id)
);

-- 2NF COMPLIANT: Separate products table
CREATE TABLE products (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);

CREATE TABLE order_items (
  order_id INT,
  product_id INT REFERENCES products(id),
  quantity INT,
  PRIMARY KEY (order_id, product_id)
);
```

### Third Normal Form (3NF)

```sql
-- VIOLATES 3NF: city depends on zip, not user_id
CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  zip VARCHAR(10),
  city VARCHAR(100)  -- Transitive dependency: id → zip → city
);

-- 3NF COMPLIANT: Separate zip_codes table
CREATE TABLE zip_codes (
  zip VARCHAR(10) PRIMARY KEY,
  city VARCHAR(100)
);

CREATE TABLE users (
  id INT PRIMARY KEY,
  name VARCHAR(100),
  zip VARCHAR(10) REFERENCES zip_codes(zip)
);
```

### When to Denormalize

| Scenario | Denormalization Approach |
|----------|-------------------------|
| Read-heavy workloads | Store computed values |
| Frequent JOINs | Embed related data |
| Reporting/analytics | Materialized views |
| Caching | Duplicate for speed |

```sql
-- Denormalized for performance
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  user_name VARCHAR(100),      -- Denormalized from users
  total_amount DECIMAL(15,2),  -- Computed from items
  item_count INT               -- Computed from items
);
```

---

## CAP Theorem

### The Three Guarantees

```
       Consistency ─────────────── Availability
              │                        │
              │       CAP              │
              │      Theorem           │
              │                        │
              └──── Partition ─────────┘
                   Tolerance
```

| Property | Meaning |
|----------|---------|
| **Consistency** | All nodes see same data at same time |
| **Availability** | Every request receives a response |
| **Partition Tolerance** | System works despite network failures |

### CAP Trade-offs

| System Type | Prioritizes | Example |
|-------------|-------------|---------|
| CP | Consistency + Partition | MongoDB (with majority write) |
| AP | Availability + Partition | Cassandra, DynamoDB |
| CA | Consistency + Availability | Traditional RDBMS (single node) |

### Practical Application

```typescript
// CP System: Prefer consistency
const result = await mongodb.collection('accounts').updateOne(
  { _id: accountId },
  { $inc: { balance: -amount } },
  { writeConcern: { w: 'majority' } }  // Wait for majority
);

// AP System: Prefer availability
const result = await dynamodb.put({
  TableName: 'events',
  Item: event,
  // Eventually consistent, always available
});
```

---

## Database Types

### Relational (SQL)

| Database | Best For | Key Features |
|----------|----------|--------------|
| PostgreSQL | General purpose, complex queries | ACID, JSON, extensions |
| MySQL | Web applications | Replication, proven scale |
| SQL Server | Enterprise, .NET | Integration, BI tools |

```sql
-- PostgreSQL: Complex query with window functions
SELECT
  user_id,
  order_total,
  SUM(order_total) OVER (PARTITION BY user_id ORDER BY created_at) as running_total,
  ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) as recency
FROM orders;
```

### Document (NoSQL)

| Database | Best For | Key Features |
|----------|----------|--------------|
| MongoDB | Flexible schemas, rapid development | BSON, aggregation, sharding |
| CouchDB | Offline-first, sync | Multi-master replication |

```javascript
// MongoDB: Flexible document structure
const user = {
  _id: ObjectId(),
  name: 'John',
  addresses: [
    { type: 'home', city: 'NYC' },
    { type: 'work', city: 'SF' }
  ],
  preferences: {
    theme: 'dark',
    notifications: true
  }
};
```

### Key-Value

| Database | Best For | Key Features |
|----------|----------|--------------|
| Redis | Caching, sessions | Sub-ms latency, data structures |
| Memcached | Simple caching | Distributed, simple |
| DynamoDB | Serverless, scale | Auto-scaling, pay-per-use |

```typescript
// Redis: Various data structures
await redis.set('user:123', JSON.stringify(user));
await redis.hset('session:abc', { userId: '123', expires: Date.now() });
await redis.lpush('queue:emails', JSON.stringify(email));
await redis.zadd('leaderboard', 100, 'player1');
```

### Column-Family

| Database | Best For | Key Features |
|----------|----------|--------------|
| Cassandra | Write-heavy, time series | Linear scale, no single point of failure |
| HBase | Hadoop ecosystem | Wide columns, analytics |

### Graph

| Database | Best For | Key Features |
|----------|----------|--------------|
| Neo4j | Relationships, social networks | Cypher query language |
| Amazon Neptune | Managed graph | SPARQL, Gremlin |

```cypher
// Neo4j: Find friends of friends
MATCH (user:Person {name: 'Alice'})-[:FRIEND]->(friend)-[:FRIEND]->(fof)
WHERE NOT (user)-[:FRIEND]->(fof) AND user <> fof
RETURN fof.name, COUNT(*) as mutual_friends
ORDER BY mutual_friends DESC
```

### Time Series

| Database | Best For | Key Features |
|----------|----------|--------------|
| TimescaleDB | PostgreSQL + time series | Automatic partitioning |
| InfluxDB | Metrics, IoT | Continuous queries |

```sql
-- TimescaleDB: Time-bucketed aggregation
SELECT
  time_bucket('1 hour', time) as hour,
  AVG(temperature) as avg_temp,
  MAX(temperature) as max_temp
FROM sensor_data
WHERE time > NOW() - INTERVAL '7 days'
GROUP BY hour
ORDER BY hour DESC;
```

### Selection Decision Tree

```
Need ACID transactions?
├─ Yes → Need complex queries?
│        ├─ Yes → PostgreSQL
│        └─ No  → MySQL
└─ No  → What's the data model?
         ├─ Documents → MongoDB
         ├─ Key-Value → Need persistence?
         │              ├─ Yes → DynamoDB/Redis
         │              └─ No  → Memcached
         ├─ Relationships → Neo4j
         └─ Time Series → TimescaleDB
```
