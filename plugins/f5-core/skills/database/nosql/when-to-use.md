---
name: when-to-use-nosql
description: Deciding when to use NoSQL vs relational databases
category: database/nosql
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# When to Use NoSQL

## Overview

Choosing between SQL and NoSQL depends on your data characteristics,
access patterns, scale requirements, and team expertise. There's no
universal "better" choice - each has trade-offs.

## Decision Framework

```
┌─────────────────────────────────────────────────────────────────┐
│                  Database Selection Flowchart                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  START: What are your primary requirements?                      │
│         │                                                        │
│         ├─► Complex relationships & joins?                       │
│         │   └─► YES → SQL (PostgreSQL, MySQL)                   │
│         │                                                        │
│         ├─► Schema changes frequently?                          │
│         │   └─► YES → Document DB (MongoDB)                     │
│         │                                                        │
│         ├─► High-speed caching needed?                          │
│         │   └─► YES → Key-Value (Redis)                         │
│         │                                                        │
│         ├─► Write-heavy with global distribution?               │
│         │   └─► YES → Wide-Column (Cassandra)                   │
│         │                                                        │
│         ├─► Complex graph relationships?                        │
│         │   └─► YES → Graph DB (Neo4j)                          │
│         │                                                        │
│         ├─► Time-series data?                                   │
│         │   └─► YES → Time-Series (TimescaleDB)                 │
│         │                                                        │
│         └─► General purpose?                                    │
│             └─► SQL (PostgreSQL) - most versatile               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Use SQL (Relational) When

### Complex Queries and Joins

```sql
-- SQL excels at complex relational queries
SELECT
  c.name as customer,
  COUNT(o.id) as total_orders,
  SUM(o.total) as total_spent,
  AVG(o.total) as avg_order,
  MAX(o.created_at) as last_order
FROM customers c
JOIN orders o ON c.id = o.customer_id
JOIN order_items oi ON o.id = oi.order_id
JOIN products p ON oi.product_id = p.id
WHERE p.category = 'Electronics'
  AND o.created_at > NOW() - INTERVAL '1 year'
GROUP BY c.id
HAVING SUM(o.total) > 1000
ORDER BY total_spent DESC;
```

### ACID Transactions Required

```typescript
// Financial transactions need ACID guarantees
async function transferMoney(from: string, to: string, amount: number) {
  await prisma.$transaction(async (tx) => {
    // Debit source account
    const source = await tx.account.update({
      where: { id: from },
      data: { balance: { decrement: amount } }
    });

    if (source.balance < 0) {
      throw new Error('Insufficient funds');
    }

    // Credit destination
    await tx.account.update({
      where: { id: to },
      data: { balance: { increment: amount } }
    });

    // Record transfer
    await tx.transfer.create({
      data: { fromId: from, toId: to, amount }
    });
  });
}
```

### Strong Consistency Required

- Banking and financial systems
- Inventory management (prevent overselling)
- User authentication and authorization
- Regulatory compliance systems

### Well-Defined Schema

- Enterprise systems with stable requirements
- Systems requiring data integrity enforcement
- Reporting and business intelligence

## Use Document DB (MongoDB) When

### Flexible/Evolving Schema

```javascript
// Different products have different attributes
const laptop = {
  type: 'laptop',
  brand: 'Dell',
  specs: {
    cpu: 'i7-12700H',
    ram: '32GB',
    storage: '1TB SSD',
    display: '15.6"'
  }
};

const shirt = {
  type: 'clothing',
  brand: 'Nike',
  size: 'M',
  color: 'Blue',
  material: '100% Cotton'
};

// Both stored in same collection without schema migration
await products.insertMany([laptop, shirt]);
```

### Hierarchical Data

```javascript
// Nested data fits naturally in documents
const article = {
  title: 'MongoDB Guide',
  author: {
    name: 'John Doe',
    bio: 'Database expert'
  },
  comments: [
    {
      user: 'Alice',
      text: 'Great article!',
      replies: [
        { user: 'Author', text: 'Thanks!' }
      ]
    }
  ],
  metadata: {
    tags: ['database', 'nosql'],
    readTime: 5
  }
};
```

### Rapid Development

- Startups with evolving requirements
- Prototyping and MVPs
- Content management systems
- Catalog systems with varying attributes

### Good Fit Use Cases

- Content management (blogs, CMS)
- Product catalogs
- User profiles
- Event logging
- Real-time analytics

## Use Key-Value (Redis) When

### High-Speed Caching

```typescript
async function getUser(userId: string) {
  // Check cache first
  const cached = await redis.get(`user:${userId}`);
  if (cached) return JSON.parse(cached);

  // Cache miss - fetch and cache
  const user = await database.getUser(userId);
  await redis.setex(`user:${userId}`, 3600, JSON.stringify(user));
  return user;
}
```

### Session Storage

```typescript
async function createSession(userId: string) {
  const sessionId = crypto.randomUUID();
  await redis.hset(`session:${sessionId}`, {
    userId,
    createdAt: Date.now()
  });
  await redis.expire(`session:${sessionId}`, 86400); // 24 hours
  return sessionId;
}
```

### Real-Time Features

```typescript
// Rate limiting
async function checkRateLimit(userId: string) {
  const key = `ratelimit:${userId}`;
  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, 60);
  return count <= 100; // 100 requests per minute
}

// Leaderboard
await redis.zadd('leaderboard', score, `player:${playerId}`);
const top10 = await redis.zrevrange('leaderboard', 0, 9, 'WITHSCORES');
```

### Good Fit Use Cases

- Session storage
- Caching layer
- Rate limiting
- Real-time leaderboards
- Pub/sub messaging
- Job queues

## Use Wide-Column (Cassandra) When

### Write-Heavy Workloads

```cql
-- Cassandra optimized for high write throughput
INSERT INTO events (user_id, event_time, event_type, data)
VALUES (uuid(), now(), 'page_view', {'page': '/home'});

-- Millions of writes per second possible
```

### Geographic Distribution

```yaml
# Multi-datacenter deployment
keyspace: analytics
replication:
  class: NetworkTopologyStrategy
  us-east: 3
  us-west: 3
  eu-west: 3
```

### Time-Series Data

```cql
-- Partition by time for efficient time-range queries
CREATE TABLE sensor_readings (
  sensor_id uuid,
  reading_date date,
  reading_time timestamp,
  value double,
  PRIMARY KEY ((sensor_id, reading_date), reading_time)
) WITH CLUSTERING ORDER BY (reading_time DESC);
```

### Good Fit Use Cases

- IoT data ingestion
- Event logging at scale
- Time-series data
- Analytics data stores
- Messaging systems

## Use Graph DB (Neo4j) When

### Complex Relationships

```cypher
// Find friends of friends who like same movies
MATCH (user:Person {name: 'Alice'})-[:FRIEND*2]-(fof:Person)
MATCH (user)-[:LIKES]->(movie:Movie)<-[:LIKES]-(fof)
WHERE user <> fof
RETURN fof.name, collect(movie.title) as common_movies
ORDER BY size(common_movies) DESC
```

### Recommendation Engines

```cypher
// Collaborative filtering
MATCH (user:User {id: $userId})-[:PURCHASED]->(product:Product)
      <-[:PURCHASED]-(similar:User)-[:PURCHASED]->(rec:Product)
WHERE NOT (user)-[:PURCHASED]->(rec)
RETURN rec, count(similar) as score
ORDER BY score DESC
LIMIT 10
```

### Network Analysis

```cypher
// Shortest path
MATCH path = shortestPath(
  (a:Person {name: 'Alice'})-[:KNOWS*]-(b:Person {name: 'Bob'})
)
RETURN path

// Influence detection
MATCH (user:User)-[:FOLLOWS]->(influencer:User)
WITH influencer, count(user) as followers
WHERE followers > 10000
RETURN influencer.name, followers
```

### Good Fit Use Cases

- Social networks
- Recommendation systems
- Fraud detection
- Knowledge graphs
- Network/IT infrastructure

## Comparison Matrix

| Factor | SQL | Document | Key-Value | Wide-Column | Graph |
|--------|-----|----------|-----------|-------------|-------|
| **Schema** | Fixed | Flexible | None | Semi-fixed | Flexible |
| **Scaling** | Vertical | Horizontal | Horizontal | Horizontal | Limited |
| **Consistency** | Strong | Eventual* | Eventual | Eventual | Strong |
| **Joins** | Excellent | Limited | None | Limited | Excellent |
| **Transactions** | Full ACID | Multi-doc | Single-key | Per-partition | Yes |
| **Query** | SQL | JSON | Get/Set | CQL | Cypher |
| **Use Case** | General | Documents | Cache | Time-series | Graphs |

*MongoDB 4.0+ supports multi-document ACID transactions

## Anti-Patterns

### Don't Use NoSQL When

```
❌ Using MongoDB for:
   - Complex reporting with many JOINs
   - Financial transactions requiring ACID
   - Highly relational data

❌ Using Redis as primary database for:
   - Data that must persist reliably
   - Complex queries
   - Data larger than memory

❌ Using Cassandra for:
   - Small datasets (< millions of rows)
   - Applications requiring strong consistency
   - Frequent schema changes

❌ Using Graph DB for:
   - Simple key-value lookups
   - High-volume transactional data
   - When relationships are simple (1:N)
```

### Don't Use SQL When

```
❌ Using PostgreSQL for:
   - Simple key-value with high throughput → Use Redis
   - Schema-less logging at massive scale → Use Elasticsearch
   - Global write-heavy distribution → Use Cassandra
   - Complex graph traversals → Use Neo4j
```

## Hybrid Approaches

Most real-world systems use multiple databases:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Polyglot Persistence                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Application Layer                       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│    ┌─────────────────────────┼─────────────────────────┐        │
│    │                         │                         │        │
│    ▼                         ▼                         ▼        │
│  ┌───────────┐        ┌───────────┐        ┌───────────┐       │
│  │ PostgreSQL│        │   Redis   │        │Elasticsearch│      │
│  │ (Primary) │        │  (Cache)  │        │  (Search)  │       │
│  │           │        │           │        │            │       │
│  │ • Users   │        │ • Sessions│        │ • Products │       │
│  │ • Orders  │        │ • Rate    │        │ • Logs     │       │
│  │ • Payments│        │   limits  │        │            │       │
│  └───────────┘        └───────────┘        └───────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Example Architecture

```typescript
class DataService {
  constructor(
    private postgres: PostgresClient,  // Primary data
    private redis: RedisClient,        // Caching
    private elastic: ElasticClient     // Search
  ) {}

  async getProduct(id: string) {
    // 1. Check cache
    const cached = await this.redis.get(`product:${id}`);
    if (cached) return JSON.parse(cached);

    // 2. Fetch from primary DB
    const product = await this.postgres.query(
      'SELECT * FROM products WHERE id = $1',
      [id]
    );

    // 3. Cache for future requests
    await this.redis.setex(`product:${id}`, 3600, JSON.stringify(product));

    return product;
  }

  async searchProducts(query: string) {
    // Use Elasticsearch for search
    return this.elastic.search({
      index: 'products',
      body: {
        query: { match: { name: query } }
      }
    });
  }

  async createOrder(order: Order) {
    // Use PostgreSQL for transactional data
    return this.postgres.transaction(async (tx) => {
      // ACID transaction for order creation
      await tx.insert('orders', order);
      await tx.update('inventory', ...);
      await tx.insert('payments', ...);
    });
  }
}
```

## Quick Decision Guide

| If you need... | Consider |
|----------------|----------|
| Complex queries with JOINs | PostgreSQL |
| Flexible schema for varying data | MongoDB |
| Sub-millisecond caching | Redis |
| Write-heavy at global scale | Cassandra |
| Graph relationships | Neo4j |
| Full-text search | Elasticsearch |
| Time-series analytics | TimescaleDB |
| Serverless simplicity | DynamoDB |
| Embedded/edge database | SQLite |
