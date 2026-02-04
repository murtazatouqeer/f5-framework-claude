---
name: acid-properties
description: Understanding ACID transaction guarantees
category: database/fundamentals
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# ACID Properties

## Overview

ACID is a set of properties that guarantee database transactions
are processed reliably, even in the face of errors, power failures,
or other issues.

## The Four Properties

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

## Atomicity

**Definition**: A transaction is an indivisible unit of work. Either
all operations complete successfully, or none of them do.

### Problem Without Atomicity

```sql
-- Bank transfer WITHOUT atomicity (dangerous!)
UPDATE accounts SET balance = balance - 100 WHERE id = 'alice';
-- System crash here!
UPDATE accounts SET balance = balance + 100 WHERE id = 'bob';
-- Money disappeared!
```

### Solution With Atomicity

```sql
-- Bank transfer WITH atomicity (safe)
BEGIN TRANSACTION;

UPDATE accounts SET balance = balance - 100 WHERE id = 'alice';
UPDATE accounts SET balance = balance + 100 WHERE id = 'bob';

COMMIT;  -- Both succeed or both fail
```

### Implementation Example

```typescript
// TypeScript with transaction
async function transferMoney(
  fromId: string,
  toId: string,
  amount: number
): Promise<void> {
  const client = await pool.connect();

  try {
    await client.query('BEGIN');

    // Debit sender
    const debitResult = await client.query(
      'UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1 RETURNING balance',
      [amount, fromId]
    );

    if (debitResult.rowCount === 0) {
      throw new Error('Insufficient funds or account not found');
    }

    // Credit receiver
    await client.query(
      'UPDATE accounts SET balance = balance + $1 WHERE id = $2',
      [amount, toId]
    );

    // Record transaction
    await client.query(
      'INSERT INTO transfers (from_id, to_id, amount) VALUES ($1, $2, $3)',
      [fromId, toId, amount]
    );

    await client.query('COMMIT');
  } catch (error) {
    await client.query('ROLLBACK');
    throw error;  // All changes undone
  } finally {
    client.release();
  }
}
```

## Consistency

**Definition**: A transaction brings the database from one valid
state to another valid state, maintaining all defined rules
(constraints, cascades, triggers).

### Consistency Rules

```sql
-- Define consistency rules
CREATE TABLE accounts (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id),
  balance DECIMAL(15, 2) NOT NULL DEFAULT 0,
  currency VARCHAR(3) NOT NULL DEFAULT 'USD',

  -- Consistency constraint: no negative balance
  CONSTRAINT positive_balance CHECK (balance >= 0),

  -- Consistency constraint: valid currency
  CONSTRAINT valid_currency CHECK (currency IN ('USD', 'EUR', 'GBP', 'JPY'))
);

-- This transaction maintains consistency
BEGIN;
UPDATE accounts SET balance = balance - 50 WHERE id = 'acc-1';  -- Still >= 0
UPDATE accounts SET balance = balance + 50 WHERE id = 'acc-2';
COMMIT;

-- This transaction would FAIL (violates constraint)
BEGIN;
UPDATE accounts SET balance = -100 WHERE id = 'acc-1';  -- Error!
COMMIT;  -- Never reached, constraint violation
```

### Application-Level Consistency

```typescript
// Ensure business rule consistency
async function createOrder(
  userId: string,
  items: OrderItem[]
): Promise<Order> {
  return await prisma.$transaction(async (tx) => {
    // Check inventory (consistency rule: can't oversell)
    for (const item of items) {
      const product = await tx.product.findUnique({
        where: { id: item.productId }
      });

      if (!product || product.stock < item.quantity) {
        throw new Error(`Insufficient stock for ${item.productId}`);
      }
    }

    // Reserve inventory
    for (const item of items) {
      await tx.product.update({
        where: { id: item.productId },
        data: { stock: { decrement: item.quantity } }
      });
    }

    // Create order (all constraints satisfied)
    return await tx.order.create({
      data: {
        userId,
        items: { create: items },
        status: 'pending'
      }
    });
  });
}
```

## Isolation

**Definition**: Concurrent transactions execute as if they were
running sequentially, preventing interference between transactions.

### Isolation Levels

| Level | Dirty Read | Non-Repeatable Read | Phantom Read | Performance |
|-------|------------|---------------------|--------------|-------------|
| Read Uncommitted | Possible | Possible | Possible | Fastest |
| Read Committed | Prevented | Possible | Possible | Fast |
| Repeatable Read | Prevented | Prevented | Possible | Medium |
| Serializable | Prevented | Prevented | Prevented | Slowest |

### Isolation Problems Explained

```sql
-- Dirty Read: Reading uncommitted data
-- Transaction A:
BEGIN;
UPDATE accounts SET balance = 1000 WHERE id = 1;  -- Not committed yet

-- Transaction B (dirty read):
SELECT balance FROM accounts WHERE id = 1;  -- Sees 1000
-- Transaction A:
ROLLBACK;  -- Balance reverts, B read invalid data


-- Non-Repeatable Read: Different results for same query
-- Transaction A:
BEGIN;
SELECT balance FROM accounts WHERE id = 1;  -- Returns 500

-- Transaction B:
UPDATE accounts SET balance = 600 WHERE id = 1;
COMMIT;

-- Transaction A:
SELECT balance FROM accounts WHERE id = 1;  -- Returns 600 (different!)


-- Phantom Read: New rows appear
-- Transaction A:
BEGIN;
SELECT COUNT(*) FROM orders WHERE status = 'pending';  -- Returns 10

-- Transaction B:
INSERT INTO orders (status) VALUES ('pending');
COMMIT;

-- Transaction A:
SELECT COUNT(*) FROM orders WHERE status = 'pending';  -- Returns 11 (phantom!)
```

### Setting Isolation Level

```sql
-- PostgreSQL: Set for transaction
BEGIN TRANSACTION ISOLATION LEVEL SERIALIZABLE;
-- or
BEGIN;
SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

-- PostgreSQL: Set session default
SET default_transaction_isolation = 'read committed';

-- MySQL
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
```

### Practical Isolation Choices

```typescript
// Read Committed (default, good for most cases)
// Use when: Basic CRUD operations
await prisma.$transaction(
  async (tx) => {
    // ... operations
  },
  { isolationLevel: 'ReadCommitted' }
);

// Repeatable Read
// Use when: Need consistent snapshot within transaction
await prisma.$transaction(
  async (tx) => {
    const account = await tx.account.findUnique({ where: { id } });
    // account value won't change if re-queried
    // ... complex calculations
  },
  { isolationLevel: 'RepeatableRead' }
);

// Serializable
// Use when: Critical financial operations, inventory
await prisma.$transaction(
  async (tx) => {
    // Guaranteed sequential execution
    // ... critical operation
  },
  { isolationLevel: 'Serializable' }
);
```

## Durability

**Definition**: Once a transaction is committed, the data is
permanently saved, even if the system crashes immediately after.

### How Durability Works

```
┌─────────────────────────────────────────────────────────────┐
│                     Write-Ahead Log (WAL)                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Transaction starts                                       │
│  2. Changes written to WAL (sequential, fast)                │
│  3. WAL flushed to disk (fsync)                             │
│  4. COMMIT returns to client                                 │
│  5. Changes applied to data files (async, later)            │
│                                                              │
│  On crash recovery:                                          │
│  - Replay WAL to recover committed transactions              │
│  - Rollback uncommitted transactions                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### PostgreSQL Durability Settings

```sql
-- Maximum durability (default)
SET synchronous_commit = on;

-- Faster but slightly less durable (crash may lose recent commits)
SET synchronous_commit = off;

-- For replicated setups
SET synchronous_commit = remote_write;  -- Replica received
SET synchronous_commit = remote_apply;  -- Replica applied
```

### Application Considerations

```typescript
// Ensure durability for critical operations
async function processPayment(orderId: string): Promise<void> {
  const client = await pool.connect();

  try {
    // Ensure synchronous commit for payment
    await client.query('SET synchronous_commit = on');
    await client.query('BEGIN');

    // Process payment...
    await client.query(
      'UPDATE orders SET status = $1, paid_at = NOW() WHERE id = $2',
      ['paid', orderId]
    );

    await client.query(
      'INSERT INTO payment_log (order_id, status) VALUES ($1, $2)',
      [orderId, 'success']
    );

    await client.query('COMMIT');
    // After COMMIT returns, data is guaranteed on disk

  } catch (error) {
    await client.query('ROLLBACK');
    throw error;
  } finally {
    client.release();
  }
}
```

## ACID in Different Databases

| Database | ACID Support | Notes |
|----------|--------------|-------|
| PostgreSQL | Full | Strong ACID, MVCC |
| MySQL (InnoDB) | Full | Full ACID with InnoDB |
| MongoDB | Partial→Full | Multi-doc transactions since 4.0 |
| Redis | Limited | Single-command atomic only |
| Cassandra | Limited | Per-partition atomicity |
| DynamoDB | Partial | TransactWriteItems for multi-item |

### MongoDB ACID Transactions

```javascript
// MongoDB multi-document transaction (v4.0+)
const session = client.startSession();

try {
  session.startTransaction({
    readConcern: { level: 'snapshot' },
    writeConcern: { w: 'majority' }
  });

  // Debit account
  await accounts.updateOne(
    { _id: 'alice', balance: { $gte: 100 } },
    { $inc: { balance: -100 } },
    { session }
  );

  // Credit account
  await accounts.updateOne(
    { _id: 'bob' },
    { $inc: { balance: 100 } },
    { session }
  );

  await session.commitTransaction();
} catch (error) {
  await session.abortTransaction();
  throw error;
} finally {
  session.endSession();
}
```

## Common Patterns

### Optimistic Locking (Version-based)

```sql
-- Add version column
ALTER TABLE products ADD COLUMN version INT DEFAULT 1;

-- Update with version check
UPDATE products
SET
  stock = stock - 1,
  version = version + 1
WHERE
  id = 'prod-1'
  AND version = 5  -- Expected version
  AND stock > 0;

-- Check if update succeeded
-- If 0 rows affected, someone else modified it
```

```typescript
// TypeScript implementation
async function updateProduct(
  id: string,
  updates: Partial<Product>,
  expectedVersion: number
): Promise<Product> {
  const result = await prisma.product.updateMany({
    where: {
      id,
      version: expectedVersion
    },
    data: {
      ...updates,
      version: { increment: 1 }
    }
  });

  if (result.count === 0) {
    throw new OptimisticLockError('Product was modified by another transaction');
  }

  return prisma.product.findUnique({ where: { id } });
}
```

### Pessimistic Locking (SELECT FOR UPDATE)

```sql
-- Lock row for update
BEGIN;
SELECT * FROM accounts WHERE id = 'acc-1' FOR UPDATE;
-- Row is now locked, other transactions must wait
UPDATE accounts SET balance = balance - 100 WHERE id = 'acc-1';
COMMIT;
-- Lock released

-- With NOWAIT (fail immediately if locked)
SELECT * FROM accounts WHERE id = 'acc-1' FOR UPDATE NOWAIT;

-- With SKIP LOCKED (skip locked rows, useful for queues)
SELECT * FROM tasks
WHERE status = 'pending'
ORDER BY created_at
LIMIT 1
FOR UPDATE SKIP LOCKED;
```

## Best Practices

### 1. Keep Transactions Short

```typescript
// BAD: Long transaction holding locks
await prisma.$transaction(async (tx) => {
  const data = await tx.product.findMany();
  await processData(data);  // Slow external call!
  await tx.product.updateMany({...});
});

// GOOD: Read outside, write in transaction
const data = await prisma.product.findMany();
const processed = await processData(data);

await prisma.$transaction(async (tx) => {
  await tx.product.updateMany({...});  // Quick update only
});
```

### 2. Choose Appropriate Isolation

```typescript
// Don't use SERIALIZABLE everywhere
// Match isolation to requirements

// Reports: Read Committed is fine
const report = await prisma.order.findMany({
  where: { status: 'completed' }
});

// Financial: Use higher isolation
await prisma.$transaction(
  async (tx) => {...},
  { isolationLevel: 'Serializable' }
);
```

### 3. Handle Conflicts Gracefully

```typescript
async function safeTransfer(from: string, to: string, amount: number) {
  const maxRetries = 3;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await transferWithTransaction(from, to, amount);
    } catch (error) {
      if (isSerializationError(error) && attempt < maxRetries) {
        await sleep(Math.random() * 100 * attempt);  // Backoff
        continue;
      }
      throw error;
    }
  }
}
```
