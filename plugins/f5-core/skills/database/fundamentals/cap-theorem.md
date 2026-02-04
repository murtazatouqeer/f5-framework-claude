---
name: cap-theorem
description: Understanding CAP theorem for distributed systems
category: database/fundamentals
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CAP Theorem

## Overview

The CAP theorem states that a distributed data store can only provide
two of three guarantees simultaneously during a network partition.

## The Three Properties

```
                    Consistency
                         ▲
                        /│\
                       / │ \
                      /  │  \
                     /   │   \
                    /    │    \
                   /     │     \
                  /      │      \
                 /   CP  │  CA   \
                /        │        \
               /         │         \
              ▼──────────┴──────────▼
        Partition              Availability
        Tolerance        AP
```

## Definitions

### Consistency (C)
Every read receives the most recent write or an error.
All nodes see the same data at the same time.

```
┌─────────────────────────────────────────────────────────────┐
│                      Consistency                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Client writes X=5 to Node A                                │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────┐    replicate    ┌─────────────┐           │
│  │   Node A    │───────────────▶│   Node B    │           │
│  │    X = 5    │                 │    X = 5    │           │
│  └─────────────┘                 └─────────────┘           │
│                                         │                   │
│                                         ▼                   │
│                                  Client reads X=5          │
│                                  (always latest)            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Availability (A)
Every request receives a non-error response, without guarantee
that it contains the most recent write.

```
┌─────────────────────────────────────────────────────────────┐
│                      Availability                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Client request to any node → Always gets a response        │
│                                                              │
│  ┌─────────────┐              ┌─────────────┐               │
│  │   Node A    │              │   Node B    │               │
│  │  responds   │              │  responds   │               │
│  └─────────────┘              └─────────────┘               │
│        ▲                             ▲                       │
│        │                             │                       │
│        └──────────┬──────────────────┘                       │
│                   │                                          │
│              Any request                                     │
│              gets response                                   │
│              (might be stale)                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Partition Tolerance (P)
The system continues to operate despite network partitions
(communication breaks between nodes).

```
┌─────────────────────────────────────────────────────────────┐
│                   Partition Tolerance                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     ✗ NETWORK ✗     ┌─────────────┐       │
│  │   Node A    │◄────PARTITION─────▶│   Node B    │       │
│  │             │       (down)        │             │       │
│  └─────────────┘                     └─────────────┘       │
│        ▲                                    ▲               │
│        │                                    │               │
│   Clients in                           Clients in          │
│   Region A                             Region B            │
│                                                              │
│  System continues operating despite partition               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Why Only Two?

During a network partition, you must choose:

### CP System (Consistency + Partition Tolerance)

```
┌─────────────────────────────────────────────────────────────┐
│                   CP: Choose Consistency                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     PARTITION     ┌─────────────┐         │
│  │   Node A    │ ◄──────✗────────▶ │   Node B    │         │
│  │  (primary)  │                    │ (secondary) │         │
│  └─────────────┘                    └─────────────┘         │
│        │                                   │                │
│        ▼                                   ▼                │
│   ✓ Accepts                          ✗ Rejects             │
│     writes                              requests            │
│   (consistent)                       (unavailable)          │
│                                                              │
│  Trade-off: Some clients can't access data during partition │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Examples**: PostgreSQL (single primary), MongoDB (with majority write concern), etcd, Zookeeper

### AP System (Availability + Partition Tolerance)

```
┌─────────────────────────────────────────────────────────────┐
│                   AP: Choose Availability                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐     PARTITION     ┌─────────────┐         │
│  │   Node A    │ ◄──────✗────────▶ │   Node B    │         │
│  │    X = 5    │                    │    X = 3    │         │
│  └─────────────┘                    └─────────────┘         │
│        │                                   │                │
│        ▼                                   ▼                │
│   ✓ Accepts                          ✓ Accepts             │
│     requests                            requests            │
│   (returns X=5)                      (returns X=3)          │
│                                                              │
│  Trade-off: Clients may see different (stale) data          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Examples**: Cassandra, DynamoDB (default), CouchDB, Riak

### CA System (Consistency + Availability)

Only possible when there are NO partitions (single node or reliable network).

**Examples**: Single-node PostgreSQL, traditional RDBMS

```
┌─────────────────────────────────────────────────────────────┐
│                   CA: No Partition Tolerance                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌───────────────────────────────────────────────┐          │
│  │                 Single Node                    │          │
│  │                                                │          │
│  │    ✓ Consistent (one source of truth)         │          │
│  │    ✓ Available (always responds)              │          │
│  │    ✗ No partition tolerance (single point)    │          │
│  │                                                │          │
│  └───────────────────────────────────────────────┘          │
│                                                              │
│  Trade-off: System fails completely if node goes down       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## PACELC: Beyond CAP

CAP only describes behavior during partitions. PACELC extends this:

**P**artition → **A**vailability vs **C**onsistency
**E**lse → **L**atency vs **C**onsistency

```
┌─────────────────────────────────────────────────────────────┐
│                        PACELC                                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  IF Partition:                                               │
│    Choose Availability OR Consistency (CAP)                  │
│                                                              │
│  ELSE (normal operation):                                    │
│    Choose Latency OR Consistency                             │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  Database          │ During Partition │ Normal Operation    │
│                    │    (P: A or C)   │    (E: L or C)      │
├────────────────────┼──────────────────┼─────────────────────┤
│  PostgreSQL        │       PC         │        EC           │
│  MongoDB (default) │       PA         │        EC           │
│  Cassandra         │       PA         │        EL           │
│  DynamoDB          │       PA         │        EL           │
│  Spanner           │       PC         │        EC           │
└─────────────────────────────────────────────────────────────┘
```

## Database Classification

### CP Databases

| Database | Trade-off | Use Case |
|----------|-----------|----------|
| PostgreSQL | Unavailable during failover | Financial, ACID needed |
| etcd | Unavailable without quorum | Configuration, coordination |
| Zookeeper | Unavailable without quorum | Distributed coordination |
| MongoDB (strict) | Waits for majority | Consistent reads required |
| CockroachDB | Higher latency | Global ACID transactions |

### AP Databases

| Database | Trade-off | Use Case |
|----------|-----------|----------|
| Cassandra | Eventual consistency | Write-heavy, global |
| DynamoDB | Eventual (default) | Serverless, scalable |
| CouchDB | Conflict resolution needed | Offline-first, sync |
| Riak | Vector clocks for conflicts | High availability |

## Consistency Models

### Strong Consistency
- Every read returns the most recent write
- As if there's only one copy of data
- Higher latency, lower availability

```typescript
// Strong consistency in MongoDB
await collection.insertOne(
  { _id: 'order-1', status: 'pending' },
  { writeConcern: { w: 'majority', j: true } }
);

const order = await collection.findOne(
  { _id: 'order-1' },
  { readConcern: { level: 'majority' } }
);
// Guaranteed to see latest write
```

### Eventual Consistency
- Reads may return stale data
- System will become consistent eventually
- Lower latency, higher availability

```typescript
// Eventual consistency in DynamoDB
await dynamodb.put({
  TableName: 'Orders',
  Item: { id: 'order-1', status: 'pending' }
}).promise();

// Might return stale data immediately after write
const result = await dynamodb.get({
  TableName: 'Orders',
  Key: { id: 'order-1' },
  ConsistentRead: false  // Eventual consistency (default)
}).promise();
```

### Causal Consistency
- Preserves causally related operations
- If A causes B, everyone sees A before B
- Balance between strong and eventual

```typescript
// Causal consistency in MongoDB (sessions)
const session = client.startSession({ causalConsistency: true });

// Write A
await collection.insertOne(
  { _id: 'a', value: 1 },
  { session }
);

// Write B (causally after A)
await collection.insertOne(
  { _id: 'b', value: 2, refersTo: 'a' },
  { session }
);

// Reads will see A before B (causal order preserved)
```

## Practical Considerations

### Choosing CP vs AP

```
┌─────────────────────────────────────────────────────────────┐
│              When to Choose CP (Consistency)                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✓ Financial transactions                                   │
│  ✓ Inventory management (avoid overselling)                 │
│  ✓ User authentication/authorization                        │
│  ✓ Configuration management                                 │
│  ✓ Order processing                                         │
│                                                              │
│  Accept: Higher latency, possible unavailability            │
│                                                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              When to Choose AP (Availability)                │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ✓ Shopping cart (merge conflicts)                          │
│  ✓ Social media feeds                                       │
│  ✓ Analytics/metrics                                        │
│  ✓ Content delivery                                         │
│  ✓ Session storage                                          │
│                                                              │
│  Accept: Stale reads, conflict resolution                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Hybrid Approaches

```typescript
// Different consistency per operation type
class OrderService {
  // CP: Financial operations need consistency
  async processPayment(orderId: string): Promise<void> {
    await this.db.transaction(async (tx) => {
      // Use strong consistency
      const order = await tx.orders.findUnique({
        where: { id: orderId },
        // PostgreSQL: automatic strong consistency
      });

      await this.paymentGateway.charge(order.total);
      await tx.orders.update({
        where: { id: orderId },
        data: { status: 'paid' }
      });
    });
  }

  // AP: Product views can be eventually consistent
  async getProductRecommendations(userId: string): Promise<Product[]> {
    // Use cache (AP) - stale data is acceptable
    const cached = await this.redis.get(`recs:${userId}`);
    if (cached) return JSON.parse(cached);

    const recs = await this.computeRecommendations(userId);
    await this.redis.setex(`recs:${userId}`, 300, JSON.stringify(recs));
    return recs;
  }
}
```

### Handling Eventual Consistency

```typescript
// Technique 1: Read-your-writes consistency
class UserService {
  async updateProfile(userId: string, data: ProfileData): Promise<Profile> {
    const updated = await this.primaryDb.update(userId, data);

    // Store in session for immediate read-back
    await this.session.set(`user:${userId}:profile`, updated);

    return updated;
  }

  async getProfile(userId: string): Promise<Profile> {
    // Check session first (read-your-writes)
    const sessionData = await this.session.get(`user:${userId}:profile`);
    if (sessionData) return sessionData;

    // Fall back to replica (eventually consistent)
    return this.replicaDb.findUser(userId);
  }
}

// Technique 2: Version vectors / timestamps
interface VersionedData {
  data: any;
  version: number;
  timestamp: Date;
}

async function resolveConflict(
  localData: VersionedData,
  remoteData: VersionedData
): Promise<VersionedData> {
  // Last-write-wins (simple)
  if (localData.timestamp > remoteData.timestamp) {
    return localData;
  }
  return remoteData;

  // Or: merge (for shopping carts, etc.)
  // return merge(localData, remoteData);
}
```

## Summary

| Aspect | CP System | AP System |
|--------|-----------|-----------|
| **During partition** | Some nodes unavailable | All nodes available |
| **Data accuracy** | Always correct | May be stale |
| **Latency** | Higher (waits for sync) | Lower (local reads) |
| **Use case** | Banking, inventory | Social, analytics |
| **Conflict handling** | Prevention | Resolution |
| **Examples** | PostgreSQL, etcd | Cassandra, DynamoDB |

### Key Takeaways

1. **CAP is about partitions**: Normal operation often allows both C and A
2. **Partitions are inevitable**: In distributed systems, P is not optional
3. **Choose per use case**: Different data may need different trade-offs
4. **PACELC gives fuller picture**: Consider latency vs consistency too
5. **Eventual consistency needs strategy**: Plan for stale reads and conflicts
