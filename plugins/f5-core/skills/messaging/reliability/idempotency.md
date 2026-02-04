---
name: idempotency
description: Designing idempotent operations for safe message reprocessing
category: messaging/reliability
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Idempotency

## Overview

An operation is idempotent if performing it multiple times has the same effect as performing it once. In messaging systems, idempotency ensures safe message reprocessing without unintended side effects.

## Why Idempotency Matters

```typescript
// ❌ Non-idempotent: Multiple calls cause different results
async function incrementBalance(userId: string, amount: number): Promise<void> {
  const user = await db.users.findById(userId);
  user.balance += amount;
  await db.users.save(user);
}
// Called twice with same message: balance += amount * 2

// ✅ Idempotent: Multiple calls have same result
async function setBalance(userId: string, newBalance: number): Promise<void> {
  await db.users.update(userId, { balance: newBalance });
}
// Called twice with same message: balance = newBalance (same result)
```

## Idempotency Patterns

### 1. Idempotency Key

```typescript
interface IdempotentRequest {
  idempotencyKey: string;
  operation: string;
  data: any;
}

class IdempotencyService {
  constructor(
    private readonly cache: Cache,
    private readonly ttl: number = 24 * 60 * 60 // 24 hours
  ) {}

  async execute<T>(
    request: IdempotentRequest,
    operation: () => Promise<T>
  ): Promise<T> {
    const key = `idempotency:${request.idempotencyKey}`;

    // Check if already processed
    const cached = await this.cache.get(key);
    if (cached) {
      return JSON.parse(cached) as T;
    }

    // Execute operation
    const result = await operation();

    // Cache result
    await this.cache.set(key, JSON.stringify(result), this.ttl);

    return result;
  }
}

// Usage
const service = new IdempotencyService(redis);

const result = await service.execute(
  {
    idempotencyKey: 'payment-abc-123',
    operation: 'charge',
    data: { amount: 100 },
  },
  async () => {
    return paymentGateway.charge(100);
  }
);
```

### 2. Natural Idempotency

```typescript
// Some operations are naturally idempotent
class NaturallyIdempotent {
  // SET operations are idempotent
  async setUserEmail(userId: string, email: string): Promise<void> {
    await db.users.update(userId, { email });
  }

  // DELETE is idempotent
  async deleteItem(itemId: string): Promise<void> {
    await db.items.delete(itemId);
    // Deleting non-existent item is fine
  }

  // UPSERT is idempotent
  async upsertProduct(product: Product): Promise<void> {
    await db.products.upsert(product);
  }
}

// Non-idempotent operations that need conversion
class ConvertToIdempotent {
  // ❌ Increment is NOT idempotent
  async increment(id: string): Promise<void> {
    await db.counters.increment(id, 1);
  }

  // ✅ Convert to set with version
  async incrementIdempotent(
    id: string,
    expectedVersion: number
  ): Promise<void> {
    const counter = await db.counters.findById(id);

    if (counter.version === expectedVersion) {
      await db.counters.update(id, {
        value: counter.value + 1,
        version: expectedVersion + 1,
      });
    }
    // If version doesn't match, already processed
  }
}
```

### 3. Database-Backed Idempotency

```typescript
interface ProcessedMessage {
  messageId: string;
  processedAt: Date;
  result: string;
}

class DatabaseIdempotency {
  constructor(private readonly db: Database) {}

  async processOnce<T>(
    messageId: string,
    operation: () => Promise<T>
  ): Promise<T> {
    return this.db.transaction(async (tx) => {
      // Try to insert processing record
      try {
        await tx.query(`
          INSERT INTO processed_messages (message_id, processing_started)
          VALUES ($1, $2)
        `, [messageId, new Date()]);
      } catch (error: any) {
        // Unique constraint violation - already processed
        if (error.code === '23505') {
          const existing = await tx.query(
            'SELECT result FROM processed_messages WHERE message_id = $1',
            [messageId]
          );
          return JSON.parse(existing[0].result);
        }
        throw error;
      }

      // Execute operation
      const result = await operation();

      // Store result
      await tx.query(`
        UPDATE processed_messages
        SET processed_at = $2, result = $3
        WHERE message_id = $1
      `, [messageId, new Date(), JSON.stringify(result)]);

      return result;
    });
  }
}
```

### 4. Outbox + Inbox Pattern

```typescript
// Producer: Outbox ensures exactly-once publish
class OutboxProducer {
  async publishWithOutbox(
    businessOperation: () => Promise<any>,
    events: Event[]
  ): Promise<void> {
    await this.db.transaction(async (tx) => {
      // Business logic
      await businessOperation();

      // Store events in outbox
      for (const event of events) {
        await tx.query(`
          INSERT INTO outbox (event_id, event_type, payload)
          VALUES ($1, $2, $3)
        `, [event.id, event.type, JSON.stringify(event)]);
      }
    });
  }
}

// Consumer: Inbox ensures exactly-once processing
class InboxConsumer {
  async processWithInbox(
    event: Event,
    handler: () => Promise<void>
  ): Promise<void> {
    await this.db.transaction(async (tx) => {
      // Check inbox
      const exists = await tx.query(
        'SELECT 1 FROM inbox WHERE event_id = $1',
        [event.id]
      );

      if (exists.length > 0) {
        return; // Already processed
      }

      // Process
      await handler();

      // Record in inbox
      await tx.query(`
        INSERT INTO inbox (event_id, processed_at)
        VALUES ($1, $2)
      `, [event.id, new Date()]);
    });
  }
}
```

### 5. Version-Based Idempotency

```typescript
interface VersionedEntity {
  id: string;
  version: number;
  data: any;
}

class OptimisticLocking {
  async update(
    id: string,
    expectedVersion: number,
    newData: any
  ): Promise<boolean> {
    const result = await this.db.query(`
      UPDATE entities
      SET data = $3, version = version + 1
      WHERE id = $1 AND version = $2
    `, [id, expectedVersion, JSON.stringify(newData)]);

    return result.rowCount > 0;
  }
}

// Command with version
interface VersionedCommand {
  entityId: string;
  expectedVersion: number;
  operation: string;
  data: any;
}

class VersionedCommandHandler {
  async handle(command: VersionedCommand): Promise<void> {
    const entity = await this.db.entities.findById(command.entityId);

    if (entity.version !== command.expectedVersion) {
      // Already processed or conflict
      console.log('Version mismatch, skipping');
      return;
    }

    // Process command
    const newData = this.applyOperation(entity, command);

    // Update with version check
    const updated = await this.optimisticLocking.update(
      command.entityId,
      command.expectedVersion,
      newData
    );

    if (!updated) {
      console.log('Concurrent modification, command may be duplicate');
    }
  }

  private applyOperation(entity: VersionedEntity, command: VersionedCommand): any {
    // Apply business logic
    return { ...entity.data, ...command.data };
  }
}
```

## Message Handler Idempotency

```typescript
// Complete idempotent message handler
class IdempotentMessageHandler {
  constructor(
    private readonly db: Database,
    private readonly handlers: Map<string, (data: any) => Promise<any>>
  ) {}

  async handle(message: Message): Promise<void> {
    await this.db.transaction(async (tx) => {
      // 1. Check if already processed
      const processed = await tx.query(
        'SELECT status, result FROM message_processing WHERE message_id = $1 FOR UPDATE',
        [message.id]
      );

      if (processed.length > 0) {
        const record = processed[0];

        if (record.status === 'completed') {
          console.log(`Message ${message.id} already processed`);
          return;
        }

        if (record.status === 'processing') {
          // Another worker is processing - let it finish
          throw new Error('Message being processed by another worker');
        }
      }

      // 2. Mark as processing
      await tx.query(`
        INSERT INTO message_processing (message_id, status, started_at)
        VALUES ($1, 'processing', $2)
        ON CONFLICT (message_id) DO UPDATE SET status = 'processing', started_at = $2
      `, [message.id, new Date()]);

      try {
        // 3. Process message
        const handler = this.handlers.get(message.type);
        if (!handler) {
          throw new Error(`No handler for message type: ${message.type}`);
        }

        const result = await handler(message.data);

        // 4. Mark as completed
        await tx.query(`
          UPDATE message_processing
          SET status = 'completed', result = $2, completed_at = $3
          WHERE message_id = $1
        `, [message.id, JSON.stringify(result), new Date()]);

      } catch (error) {
        // 5. Mark as failed
        await tx.query(`
          UPDATE message_processing
          SET status = 'failed', error = $2
          WHERE message_id = $1
        `, [message.id, (error as Error).message]);

        throw error;
      }
    });
  }
}
```

## Testing Idempotency

```typescript
describe('IdempotentHandler', () => {
  it('should produce same result when called twice', async () => {
    const message = { id: 'test-1', type: 'create_order', data: { amount: 100 } };

    // First call
    const result1 = await handler.handle(message);

    // Second call with same message
    const result2 = await handler.handle(message);

    // Should be identical
    expect(result1).toEqual(result2);

    // Side effects should only happen once
    const orders = await db.orders.findAll();
    expect(orders).toHaveLength(1);
  });

  it('should handle concurrent duplicate messages', async () => {
    const message = { id: 'test-2', type: 'create_order', data: { amount: 100 } };

    // Process concurrently
    const results = await Promise.allSettled([
      handler.handle(message),
      handler.handle(message),
      handler.handle(message),
    ]);

    // At least one should succeed
    const successful = results.filter(r => r.status === 'fulfilled');
    expect(successful.length).toBeGreaterThan(0);

    // Only one order should be created
    const orders = await db.orders.findAll();
    expect(orders).toHaveLength(1);
  });
});
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use unique message IDs** | Enable deduplication |
| **Store processing results** | Return same result on retry |
| **Use database transactions** | Ensure atomicity |
| **Clean up old records** | Prevent storage growth |
| **Handle partial failures** | Track processing state |
| **Test with duplicates** | Verify idempotency |

## Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| Time-based IDs | Use UUIDs or sequence numbers |
| In-memory deduplication | Use persistent storage |
| No result caching | Return cached result on retry |
| Race conditions | Use locking or transactions |
| Infinite storage | Set TTL on processing records |
