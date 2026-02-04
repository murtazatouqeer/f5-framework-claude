---
name: outbox-pattern
description: Reliable event publishing with transactional outbox
category: messaging/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Outbox Pattern

## Overview

The Outbox Pattern ensures reliable event publishing by storing events in a database table (outbox) within the same transaction as business data. A separate process then publishes these events to the message broker.

## The Problem

```typescript
// ❌ Problematic: Two-phase commit risk
async function createOrder(orderData: OrderData): Promise<Order> {
  // Step 1: Save to database
  const order = await orderRepository.save(orderData);

  // Step 2: Publish event
  // If this fails, we have inconsistent state!
  await eventBus.publish(new OrderCreatedEvent(order));

  return order;
}

// Failure scenarios:
// 1. DB succeeds, publish fails → Order exists, no event
// 2. DB fails → No order, no event (OK)
// 3. Publish succeeds, DB fails → Event sent, no order
```

## The Solution

```typescript
// ✅ Outbox Pattern: Single transaction
async function createOrder(orderData: OrderData): Promise<Order> {
  return await db.transaction(async (tx) => {
    // Step 1: Save order
    const order = await orderRepository.save(orderData, tx);

    // Step 2: Save event to outbox (same transaction)
    await outboxRepository.save({
      id: crypto.randomUUID(),
      aggregateId: order.id,
      aggregateType: 'Order',
      eventType: 'order.created',
      payload: JSON.stringify({ orderId: order.id, ...order }),
      createdAt: new Date(),
    }, tx);

    return order;
  });
  // Separate process publishes events from outbox
}
```

## Implementation

### Outbox Table Schema

```sql
CREATE TABLE outbox (
  id UUID PRIMARY KEY,
  aggregate_id VARCHAR(255) NOT NULL,
  aggregate_type VARCHAR(255) NOT NULL,
  event_type VARCHAR(255) NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  published_at TIMESTAMP,
  retry_count INTEGER DEFAULT 0,
  last_error TEXT,
  INDEX idx_outbox_unpublished (published_at) WHERE published_at IS NULL
);
```

### Outbox Repository

```typescript
interface OutboxEvent {
  id: string;
  aggregateId: string;
  aggregateType: string;
  eventType: string;
  payload: string;
  createdAt: Date;
  publishedAt?: Date;
  retryCount: number;
  lastError?: string;
}

class OutboxRepository {
  constructor(private readonly db: Database) {}

  async save(event: Omit<OutboxEvent, 'publishedAt' | 'retryCount'>, tx?: Transaction): Promise<void> {
    const connection = tx || this.db;

    await connection.query(`
      INSERT INTO outbox (id, aggregate_id, aggregate_type, event_type, payload, created_at, retry_count)
      VALUES ($1, $2, $3, $4, $5, $6, 0)
    `, [
      event.id,
      event.aggregateId,
      event.aggregateType,
      event.eventType,
      event.payload,
      event.createdAt,
    ]);
  }

  async getUnpublished(limit: number = 100): Promise<OutboxEvent[]> {
    return this.db.query(`
      SELECT * FROM outbox
      WHERE published_at IS NULL
      ORDER BY created_at ASC
      LIMIT $1
      FOR UPDATE SKIP LOCKED
    `, [limit]);
  }

  async markPublished(id: string): Promise<void> {
    await this.db.query(`
      UPDATE outbox SET published_at = NOW() WHERE id = $1
    `, [id]);
  }

  async markFailed(id: string, error: string): Promise<void> {
    await this.db.query(`
      UPDATE outbox
      SET retry_count = retry_count + 1, last_error = $2
      WHERE id = $1
    `, [id, error]);
  }

  async deletePublished(olderThan: Date): Promise<number> {
    const result = await this.db.query(`
      DELETE FROM outbox
      WHERE published_at IS NOT NULL AND published_at < $1
    `, [olderThan]);

    return result.rowCount;
  }
}
```

### Outbox Publisher

```typescript
class OutboxPublisher {
  private running = false;
  private pollInterval: NodeJS.Timer | null = null;

  constructor(
    private readonly outboxRepository: OutboxRepository,
    private readonly eventBus: EventBus,
    private readonly options: {
      pollIntervalMs: number;
      batchSize: number;
      maxRetries: number;
    } = {
      pollIntervalMs: 1000,
      batchSize: 100,
      maxRetries: 5,
    }
  ) {}

  start(): void {
    if (this.running) return;

    this.running = true;
    this.pollInterval = setInterval(
      () => this.processOutbox(),
      this.options.pollIntervalMs
    );

    console.log('Outbox publisher started');
  }

  stop(): void {
    this.running = false;

    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }

    console.log('Outbox publisher stopped');
  }

  private async processOutbox(): Promise<void> {
    try {
      const events = await this.outboxRepository.getUnpublished(
        this.options.batchSize
      );

      for (const event of events) {
        await this.publishEvent(event);
      }
    } catch (error) {
      console.error('Error processing outbox:', error);
    }
  }

  private async publishEvent(event: OutboxEvent): Promise<void> {
    if (event.retryCount >= this.options.maxRetries) {
      console.error(`Event ${event.id} exceeded max retries, skipping`);
      return;
    }

    try {
      await this.eventBus.publish({
        eventId: event.id,
        eventType: event.eventType,
        aggregateId: event.aggregateId,
        aggregateType: event.aggregateType,
        payload: JSON.parse(event.payload),
        occurredOn: event.createdAt,
      });

      await this.outboxRepository.markPublished(event.id);
    } catch (error) {
      console.error(`Failed to publish event ${event.id}:`, error);
      await this.outboxRepository.markFailed(event.id, (error as Error).message);
    }
  }
}
```

### Domain Service with Outbox

```typescript
class OrderService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly outboxRepository: OutboxRepository,
    private readonly db: Database
  ) {}

  async createOrder(input: CreateOrderInput): Promise<Order> {
    return this.db.transaction(async (tx) => {
      // Create order
      const order = Order.create(input);
      await this.orderRepository.save(order, tx);

      // Store events in outbox
      for (const event of order.uncommittedEvents) {
        await this.outboxRepository.save({
          id: event.eventId,
          aggregateId: order.id,
          aggregateType: 'Order',
          eventType: event.eventType,
          payload: JSON.stringify(event),
          createdAt: event.occurredOn,
        }, tx);
      }

      order.clearUncommittedEvents();
      return order;
    });
  }

  async cancelOrder(orderId: string, reason: string): Promise<void> {
    return this.db.transaction(async (tx) => {
      const order = await this.orderRepository.getById(orderId, tx);

      if (!order) {
        throw new Error(`Order ${orderId} not found`);
      }

      order.cancel(reason);
      await this.orderRepository.save(order, tx);

      for (const event of order.uncommittedEvents) {
        await this.outboxRepository.save({
          id: event.eventId,
          aggregateId: order.id,
          aggregateType: 'Order',
          eventType: event.eventType,
          payload: JSON.stringify(event),
          createdAt: event.occurredOn,
        }, tx);
      }

      order.clearUncommittedEvents();
    });
  }
}
```

## Change Data Capture (CDC) Alternative

```typescript
// Using Debezium or similar CDC tool
// Database changes are captured and published automatically

// 1. Configure CDC to watch outbox table
// 2. CDC publishes changes to Kafka
// 3. No polling needed

// Kafka Connect configuration (Debezium)
const debeziumConfig = {
  'name': 'outbox-connector',
  'config': {
    'connector.class': 'io.debezium.connector.postgresql.PostgresConnector',
    'database.hostname': 'localhost',
    'database.port': '5432',
    'database.user': 'postgres',
    'database.password': 'password',
    'database.dbname': 'mydb',
    'table.include.list': 'public.outbox',
    'transforms': 'outbox',
    'transforms.outbox.type': 'io.debezium.transforms.outbox.EventRouter',
    'transforms.outbox.table.field.event.key': 'aggregate_id',
    'transforms.outbox.table.field.event.type': 'event_type',
    'transforms.outbox.table.field.event.payload': 'payload',
    'transforms.outbox.route.topic.replacement': 'events.${routedByValue}',
  },
};
```

## Inbox Pattern (Consumer Side)

```typescript
// Prevent duplicate event processing
interface InboxEvent {
  eventId: string;
  eventType: string;
  processedAt: Date;
}

class InboxRepository {
  constructor(private readonly db: Database) {}

  async isProcessed(eventId: string): Promise<boolean> {
    const result = await this.db.query(`
      SELECT 1 FROM inbox WHERE event_id = $1
    `, [eventId]);

    return result.length > 0;
  }

  async markProcessed(eventId: string, eventType: string, tx?: Transaction): Promise<void> {
    const connection = tx || this.db;

    await connection.query(`
      INSERT INTO inbox (event_id, event_type, processed_at)
      VALUES ($1, $2, NOW())
      ON CONFLICT (event_id) DO NOTHING
    `, [eventId, eventType]);
  }
}

// Idempotent event handler
class IdempotentEventHandler {
  constructor(
    private readonly inboxRepository: InboxRepository,
    private readonly db: Database
  ) {}

  async handle(event: DomainEvent, handler: (event: DomainEvent) => Promise<void>): Promise<void> {
    // Check if already processed
    if (await this.inboxRepository.isProcessed(event.eventId)) {
      console.log(`Event ${event.eventId} already processed, skipping`);
      return;
    }

    // Process in transaction
    await this.db.transaction(async (tx) => {
      // Process event
      await handler(event);

      // Mark as processed
      await this.inboxRepository.markProcessed(event.eventId, event.eventType, tx);
    });
  }
}
```

## Complete Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRODUCER SERVICE                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Business   │───►│   Database   │◄───│   Outbox     │      │
│  │   Logic      │    │   (Orders)   │    │   Table      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                              │                   │              │
│                              └───────────────────┘              │
│                          Same Transaction                        │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐                          │
│  │   Outbox     │───►│   Message    │                          │
│  │   Publisher  │    │   Broker     │                          │
│  └──────────────┘    └──────────────┘                          │
│       Polling              │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                       CONSUMER SERVICE                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Event      │───►│   Inbox      │───►│   Business   │      │
│  │   Handler    │    │   Check      │    │   Logic      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                              │                   │              │
│                              ▼                   ▼              │
│                       ┌──────────────┐    ┌──────────────┐      │
│                       │   Inbox      │    │   Database   │      │
│                       │   Table      │    │   (State)    │      │
│                       └──────────────┘    └──────────────┘      │
│                              │                   │              │
│                              └───────────────────┘              │
│                          Same Transaction                        │
└─────────────────────────────────────────────────────────────────┘
```

## Benefits and Trade-offs

| Benefit | Trade-off |
|---------|-----------|
| Guaranteed delivery | Additional table and process |
| Atomic with business data | Polling latency |
| Simple recovery | Storage for events |
| No distributed transactions | Complexity |

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use database transaction** | Ensure atomicity |
| **Index outbox table** | Fast unpublished queries |
| **Clean up published events** | Prevent table growth |
| **Handle retries** | Set max retry limits |
| **Monitor lag** | Alert on growing backlog |
| **Use CDC when available** | Lower latency than polling |
