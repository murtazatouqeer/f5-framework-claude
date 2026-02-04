---
name: delivery-guarantees
description: Understanding at-most-once, at-least-once, and exactly-once delivery
category: messaging/reliability
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Delivery Guarantees

## Overview

Delivery guarantees define how messaging systems handle message delivery in the presence of failures. Understanding these guarantees is crucial for building reliable distributed systems.

## Three Guarantees

| Guarantee | Description | Duplicates | Lost |
|-----------|-------------|------------|------|
| **At-most-once** | Fire and forget | No | Possible |
| **At-least-once** | Retry until acknowledged | Possible | No |
| **Exactly-once** | Delivered exactly one time | No | No |

## At-Most-Once

Messages are sent once without confirmation. If delivery fails, the message is lost.

```typescript
// At-most-once: Fire and forget
class AtMostOnceProducer {
  async send(message: Message): Promise<void> {
    // Send without waiting for acknowledgment
    this.transport.send(message);
    // Don't track or retry
  }
}

// Use cases:
// - Metrics/telemetry (losing some data is acceptable)
// - Logging (best-effort delivery)
// - Real-time updates where stale data is worse than no data
```

### Characteristics

```
Producer ──message──► Broker ──?──► Consumer
                              └── May be lost

Pros:
✓ Lowest latency
✓ Simplest implementation
✓ No duplicate handling needed

Cons:
✗ Messages can be lost
✗ No delivery confirmation
✗ Not suitable for critical data
```

## At-Least-Once

Messages are retried until acknowledged. Duplicates are possible if acknowledgment is lost.

```typescript
// At-least-once: Retry until acknowledged
class AtLeastOnceProducer {
  private pendingMessages: Map<string, Message> = new Map();
  private readonly maxRetries = 5;

  async send(message: Message): Promise<void> {
    const messageId = message.id;
    this.pendingMessages.set(messageId, message);

    let attempt = 0;
    while (attempt < this.maxRetries) {
      try {
        await this.transport.send(message);
        const ack = await this.waitForAck(messageId, 5000);

        if (ack) {
          this.pendingMessages.delete(messageId);
          return;
        }
      } catch (error) {
        console.log(`Attempt ${attempt + 1} failed, retrying...`);
      }
      attempt++;
    }

    throw new Error(`Failed to deliver message ${messageId} after ${this.maxRetries} attempts`);
  }

  private async waitForAck(messageId: string, timeout: number): Promise<boolean> {
    return new Promise((resolve) => {
      const timer = setTimeout(() => resolve(false), timeout);

      this.transport.onAck(messageId, () => {
        clearTimeout(timer);
        resolve(true);
      });
    });
  }
}

// Consumer must handle duplicates
class AtLeastOnceConsumer {
  async process(message: Message): Promise<void> {
    // Process message
    await this.handler(message);

    // Send acknowledgment
    await this.transport.ack(message.id);
  }
}
```

### Duplicate Scenarios

```
Scenario 1: Lost acknowledgment
Producer ──msg──► Broker ──msg──► Consumer (processes)
Producer ◄──?─── Broker ◄──ack── Consumer
Producer ──msg──► Broker ──msg──► Consumer (processes again - DUPLICATE)

Scenario 2: Consumer crash after processing
Producer ──msg──► Broker ──msg──► Consumer (processes, crashes)
Producer ◄──?─── Broker (no ack received)
Producer ──msg──► Broker ──msg──► Consumer (processes again - DUPLICATE)
```

### Handling Duplicates

```typescript
// Consumer with deduplication
class DeduplicatingConsumer {
  constructor(
    private readonly processedIds: Set<string>,
    private readonly handler: (msg: Message) => Promise<void>
  ) {}

  async process(message: Message): Promise<void> {
    // Check if already processed
    if (this.processedIds.has(message.id)) {
      console.log(`Duplicate message ${message.id}, skipping`);
      return;
    }

    // Process
    await this.handler(message);

    // Mark as processed
    this.processedIds.add(message.id);
  }
}

// Database-backed deduplication
class PersistentDeduplication {
  constructor(private readonly db: Database) {}

  async processOnce(
    message: Message,
    handler: (msg: Message) => Promise<void>
  ): Promise<void> {
    // Use database transaction for atomicity
    await this.db.transaction(async (tx) => {
      // Check if processed
      const exists = await tx.query(
        'SELECT 1 FROM processed_messages WHERE id = $1',
        [message.id]
      );

      if (exists.length > 0) {
        return; // Already processed
      }

      // Process message
      await handler(message);

      // Mark as processed (same transaction)
      await tx.query(
        'INSERT INTO processed_messages (id, processed_at) VALUES ($1, $2)',
        [message.id, new Date()]
      );
    });
  }
}
```

## Exactly-Once

Messages are delivered and processed exactly one time. This is the hardest guarantee to achieve.

```typescript
// Exactly-once using idempotency and transactions
class ExactlyOnceProcessor {
  constructor(
    private readonly db: Database,
    private readonly eventStore: EventStore
  ) {}

  async process(message: Message): Promise<void> {
    await this.db.transaction(async (tx) => {
      // 1. Check if message was processed
      const processed = await tx.query(
        'SELECT 1 FROM inbox WHERE message_id = $1',
        [message.id]
      );

      if (processed.length > 0) {
        return; // Idempotent - already processed
      }

      // 2. Process message (within transaction)
      const result = await this.handleMessage(message, tx);

      // 3. Store output events (within transaction)
      for (const event of result.events) {
        await this.eventStore.append(event, tx);
      }

      // 4. Mark as processed (within transaction)
      await tx.query(
        'INSERT INTO inbox (message_id, processed_at) VALUES ($1, $2)',
        [message.id, new Date()]
      );
    });
    // Transaction commits atomically - all or nothing
  }

  private async handleMessage(
    message: Message,
    tx: Transaction
  ): Promise<{ events: Event[] }> {
    // Business logic
    return { events: [] };
  }
}
```

### Kafka Exactly-Once

```typescript
import { Kafka, Producer, Consumer, EachMessagePayload } from 'kafkajs';

// Idempotent producer prevents duplicates on producer side
const producer: Producer = kafka.producer({
  idempotent: true,
  maxInFlightRequests: 5,
});

// Transactional producer for exactly-once semantics
const transactionalProducer: Producer = kafka.producer({
  idempotent: true,
  transactionalId: 'my-transactional-producer',
});

await transactionalProducer.connect();

// Exactly-once: Read → Process → Write in single transaction
async function processExactlyOnce(
  inputTopic: string,
  outputTopic: string,
  processor: (msg: any) => any
): Promise<void> {
  const consumer = kafka.consumer({
    groupId: 'exactly-once-group',
    readUncommitted: false, // Only read committed messages
  });

  await consumer.connect();
  await consumer.subscribe({ topic: inputTopic });

  await consumer.run({
    autoCommit: false, // Manual commit control
    eachMessage: async ({ topic, partition, message }: EachMessagePayload) => {
      const transaction = await transactionalProducer.transaction();

      try {
        // Process message
        const input = JSON.parse(message.value?.toString() || '{}');
        const output = processor(input);

        // Send to output topic (within transaction)
        await transaction.send({
          topic: outputTopic,
          messages: [{ value: JSON.stringify(output) }],
        });

        // Commit consumer offset (within transaction)
        await transaction.sendOffsets({
          consumerGroupId: 'exactly-once-group',
          topics: [{
            topic,
            partitions: [{
              partition,
              offset: (BigInt(message.offset) + 1n).toString(),
            }],
          }],
        });

        // Commit transaction
        await transaction.commit();
      } catch (error) {
        // Abort transaction - nothing is committed
        await transaction.abort();
        throw error;
      }
    },
  });
}
```

## Comparison

| Aspect | At-Most-Once | At-Least-Once | Exactly-Once |
|--------|--------------|---------------|--------------|
| Complexity | Low | Medium | High |
| Latency | Lowest | Medium | Highest |
| Throughput | Highest | High | Lower |
| Data loss | Possible | No | No |
| Duplicates | No | Possible | No |
| Use case | Metrics | Events | Payments |

## Choosing the Right Guarantee

```
Is data loss acceptable?
├── Yes → At-most-once
└── No → Are duplicates acceptable?
    ├── Yes → At-least-once (simplest)
    └── No → Can consumer be idempotent?
        ├── Yes → At-least-once + idempotent consumer
        └── No → Exactly-once (most complex)
```

### Decision Guide

| Scenario | Recommended | Reason |
|----------|-------------|--------|
| Metrics/Analytics | At-most-once | Losing some data is fine |
| Logging | At-most-once | Best effort sufficient |
| Notifications | At-least-once | Duplicate notification OK |
| Order processing | At-least-once + idempotent | Can deduplicate |
| Financial transactions | Exactly-once | Cannot lose or duplicate |
| Event sourcing | At-least-once + idempotent | Events have IDs |

## Implementation Patterns

### Producer Acknowledgments

```typescript
// Kafka producer acknowledgment levels
const producer = kafka.producer();

// acks=0: Fire and forget (at-most-once)
await producer.send({
  topic: 'logs',
  messages: [{ value: 'log entry' }],
  acks: 0,
});

// acks=1: Leader acknowledgment (at-least-once, some data loss risk)
await producer.send({
  topic: 'events',
  messages: [{ value: 'event' }],
  acks: 1,
});

// acks=-1 (all): All replicas acknowledge (at-least-once, no data loss)
await producer.send({
  topic: 'orders',
  messages: [{ value: 'order' }],
  acks: -1,
});
```

### Consumer Acknowledgment Patterns

```typescript
// Manual acknowledgment for at-least-once
await consumer.run({
  autoCommit: false,
  eachMessage: async ({ message }) => {
    try {
      await processMessage(message);
      await consumer.commitOffsets([{
        topic: 'orders',
        partition: 0,
        offset: (BigInt(message.offset) + 1n).toString(),
      }]);
    } catch (error) {
      // Don't commit - message will be redelivered
      throw error;
    }
  },
});

// Auto commit (simpler but less control)
await consumer.run({
  autoCommit: true,
  autoCommitInterval: 5000,
  eachMessage: async ({ message }) => {
    await processMessage(message);
    // Commits automatically
  },
});
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Default to at-least-once** | Most common requirement |
| **Make consumers idempotent** | Handle duplicates gracefully |
| **Use message IDs** | Enable deduplication |
| **Store processing state** | Track what's been processed |
| **Consider trade-offs** | Complexity vs guarantees |
| **Test failure scenarios** | Verify guarantees under failure |
