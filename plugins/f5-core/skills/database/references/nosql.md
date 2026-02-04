# NoSQL Databases

MongoDB, Redis, and DynamoDB patterns and best practices.

## Table of Contents

1. [When to Use NoSQL](#when-to-use-nosql)
2. [MongoDB](#mongodb)
3. [Redis](#redis)
4. [DynamoDB](#dynamodb)

---

## When to Use NoSQL

### Database Selection Guide

| Use Case | Recommended | Reason |
|----------|-------------|--------|
| Transactional data | PostgreSQL | ACID, complex queries |
| Document storage | MongoDB | Schema flexibility |
| Caching/Sessions | Redis | Sub-ms latency |
| Serverless scale | DynamoDB | Auto-scaling |
| Time series | TimescaleDB | Optimized queries |
| Graph relationships | Neo4j | Traversal performance |

### Decision Tree

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

---

## MongoDB

### Document Model

```javascript
// Flexible document structure
const user = {
  _id: ObjectId(),
  name: 'John Doe',
  email: 'john@example.com',
  addresses: [
    { type: 'home', city: 'NYC', zip: '10001' },
    { type: 'work', city: 'SF', zip: '94105' }
  ],
  preferences: {
    theme: 'dark',
    notifications: true
  },
  createdAt: new Date()
};
```

### CRUD Operations

```javascript
const { MongoClient } = require('mongodb');
const client = new MongoClient(process.env.MONGODB_URI);

// Insert
await db.users.insertOne({ name: 'John', email: 'john@example.com' });
await db.users.insertMany([{ name: 'Jane' }, { name: 'Bob' }]);

// Find
const user = await db.users.findOne({ email: 'john@example.com' });
const users = await db.users.find({ status: 'active' }).toArray();

// Update
await db.users.updateOne(
  { _id: userId },
  { $set: { name: 'John Smith' }, $inc: { loginCount: 1 } }
);

// Delete
await db.users.deleteOne({ _id: userId });
```

### Aggregation Pipeline

```javascript
// Complex aggregation
const result = await db.orders.aggregate([
  // Match stage
  { $match: { status: 'completed', createdAt: { $gte: startDate } } },

  // Group stage
  { $group: {
    _id: '$customerId',
    totalOrders: { $sum: 1 },
    totalSpent: { $sum: '$total' },
    avgOrder: { $avg: '$total' }
  }},

  // Lookup (join)
  { $lookup: {
    from: 'customers',
    localField: '_id',
    foreignField: '_id',
    as: 'customer'
  }},

  // Sort and limit
  { $sort: { totalSpent: -1 } },
  { $limit: 10 }
]).toArray();
```

### Indexing

```javascript
// Single field index
await db.users.createIndex({ email: 1 }, { unique: true });

// Compound index
await db.orders.createIndex({ customerId: 1, createdAt: -1 });

// Text search index
await db.articles.createIndex({ title: 'text', content: 'text' });

// TTL index (auto-expire documents)
await db.sessions.createIndex({ createdAt: 1 }, { expireAfterSeconds: 3600 });
```

---

## Redis

### Data Structures

```
┌─────────────────────────────────────────────────────────────────┐
│                    Redis Data Structures                         │
├─────────────────────────────────────────────────────────────────┤
│  String     │ Simple key-value, numbers, binary                 │
│  List       │ Ordered collection, queue/stack                   │
│  Set        │ Unordered unique values                           │
│  Sorted Set │ Unique values with score (ranking)                │
│  Hash       │ Object-like field-value pairs                     │
│  Stream     │ Append-only log (event sourcing)                  │
└─────────────────────────────────────────────────────────────────┘
```

### Common Patterns

#### Caching

```typescript
async function getUser(userId: string) {
  const cacheKey = `user:${userId}`;

  // Try cache first
  let user = await redis.get(cacheKey);
  if (user) return JSON.parse(user);

  // Cache miss - fetch from database
  user = await database.getUser(userId);

  // Store in cache with TTL
  await redis.setEx(cacheKey, 3600, JSON.stringify(user));

  return user;
}
```

#### Session Storage

```typescript
async function createSession(userId: string, data: object) {
  const sessionId = crypto.randomUUID();
  const sessionKey = `session:${sessionId}`;

  await redis.hSet(sessionKey, { userId, ...data, createdAt: Date.now() });
  await redis.expire(sessionKey, 86400);  // 24 hours

  return sessionId;
}

async function getSession(sessionId: string) {
  return await redis.hGetAll(`session:${sessionId}`);
}
```

#### Rate Limiting

```typescript
async function checkRateLimit(userId: string, limit = 100, windowSecs = 60) {
  const key = `ratelimit:${userId}:${Math.floor(Date.now() / (windowSecs * 1000))}`;

  const count = await redis.incr(key);
  if (count === 1) await redis.expire(key, windowSecs);

  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count)
  };
}
```

#### Leaderboard

```typescript
// Add/update score
await redis.zAdd('leaderboard', { score: 100, value: 'player1' });

// Increment score
await redis.zIncrBy('leaderboard', 5, 'player1');

// Get top 10 players
const top10 = await redis.zRevRange('leaderboard', 0, 9, { WITHSCORES: true });

// Get player rank (0-indexed)
const rank = await redis.zRevRank('leaderboard', 'player1');
```

#### Distributed Lock

```typescript
async function acquireLock(resource: string, ttlMs = 10000) {
  const lockKey = `lock:${resource}`;
  const lockValue = crypto.randomUUID();

  const acquired = await redis.set(lockKey, lockValue, {
    NX: true,  // Only if not exists
    PX: ttlMs  // Milliseconds TTL
  });

  return acquired ? lockValue : null;
}

async function releaseLock(resource: string, lockValue: string) {
  const script = `
    if redis.call("get", KEYS[1]) == ARGV[1] then
      return redis.call("del", KEYS[1])
    else
      return 0
    end
  `;
  return await redis.eval(script, { keys: [`lock:${resource}`], arguments: [lockValue] });
}
```

#### Pub/Sub

```typescript
// Publisher
await redis.publish('notifications', JSON.stringify({ type: 'message', data: {} }));

// Subscriber
const subscriber = redis.duplicate();
await subscriber.subscribe('notifications', (message) => {
  const data = JSON.parse(message);
  console.log('Received:', data);
});
```

---

## DynamoDB

### Key Concepts

| Concept | Description |
|---------|-------------|
| Partition Key | Primary hash key for distribution |
| Sort Key | Optional range key for ordering |
| GSI | Global Secondary Index (different partition key) |
| LSI | Local Secondary Index (same partition key) |
| RCU/WCU | Read/Write Capacity Units |

### Table Design

```javascript
// Create table with composite key
const params = {
  TableName: 'Orders',
  KeySchema: [
    { AttributeName: 'userId', KeyType: 'HASH' },   // Partition key
    { AttributeName: 'orderId', KeyType: 'RANGE' }  // Sort key
  ],
  AttributeDefinitions: [
    { AttributeName: 'userId', AttributeType: 'S' },
    { AttributeName: 'orderId', AttributeType: 'S' },
    { AttributeName: 'status', AttributeType: 'S' }
  ],
  GlobalSecondaryIndexes: [{
    IndexName: 'StatusIndex',
    KeySchema: [
      { AttributeName: 'status', KeyType: 'HASH' },
      { AttributeName: 'orderId', KeyType: 'RANGE' }
    ],
    Projection: { ProjectionType: 'ALL' }
  }],
  BillingMode: 'PAY_PER_REQUEST'
};
```

### CRUD Operations

```typescript
import { DynamoDBClient } from '@aws-sdk/client-dynamodb';
import { DynamoDBDocumentClient, PutCommand, GetCommand, QueryCommand } from '@aws-sdk/lib-dynamodb';

const client = DynamoDBDocumentClient.from(new DynamoDBClient({}));

// Put item
await client.send(new PutCommand({
  TableName: 'Orders',
  Item: {
    userId: 'user-123',
    orderId: 'order-456',
    total: 99.99,
    status: 'pending',
    createdAt: Date.now()
  }
}));

// Get item
const { Item } = await client.send(new GetCommand({
  TableName: 'Orders',
  Key: { userId: 'user-123', orderId: 'order-456' }
}));

// Query by partition key
const { Items } = await client.send(new QueryCommand({
  TableName: 'Orders',
  KeyConditionExpression: 'userId = :uid',
  ExpressionAttributeValues: { ':uid': 'user-123' }
}));

// Query with sort key condition
const { Items: recentOrders } = await client.send(new QueryCommand({
  TableName: 'Orders',
  KeyConditionExpression: 'userId = :uid AND orderId > :oid',
  ExpressionAttributeValues: {
    ':uid': 'user-123',
    ':oid': '2024-01-01'
  },
  ScanIndexForward: false,  // Descending order
  Limit: 10
}));
```

### Single Table Design

```javascript
// Store multiple entity types in one table
// PK = partition key, SK = sort key

// User entity
{ PK: 'USER#123', SK: 'PROFILE', name: 'John', email: '...' }

// User's orders
{ PK: 'USER#123', SK: 'ORDER#456', total: 99.99, status: 'pending' }
{ PK: 'USER#123', SK: 'ORDER#789', total: 149.99, status: 'completed' }

// Order details (for querying by order)
{ PK: 'ORDER#456', SK: 'USER#123', total: 99.99, status: 'pending' }

// Query all user data
const userData = await client.send(new QueryCommand({
  TableName: 'AppData',
  KeyConditionExpression: 'PK = :pk',
  ExpressionAttributeValues: { ':pk': 'USER#123' }
}));
```

### Access Patterns

| Pattern | Key Design |
|---------|------------|
| Get user by ID | PK=USER#id |
| Get user's orders | PK=USER#id, SK begins_with ORDER# |
| Get order by ID | PK=ORDER#id |
| Orders by status | GSI: PK=status, SK=createdAt |
| Recent orders | GSI: PK=ORDERS, SK=createdAt |

---

## Comparison Summary

| Feature | MongoDB | Redis | DynamoDB |
|---------|---------|-------|----------|
| Data Model | Document | Key-Value+ | Key-Value/Document |
| Query Language | MQL | Commands | PartiQL/API |
| Transactions | Yes (4.0+) | Limited | Yes |
| Scaling | Sharding | Cluster | Automatic |
| Persistence | Disk | Optional | Disk |
| Best For | Flexible docs | Caching/Real-time | Serverless scale |
| Latency | ~10ms | <1ms | ~10ms |
| Managed Options | Atlas | ElastiCache | Native AWS |
