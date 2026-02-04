# Event-Driven Architecture Reference

## Apache Kafka

### Setup

```typescript
import { Kafka, Partitioners } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'my-app',
  brokers: ['localhost:9092'],
});

const producer = kafka.producer({
  createPartitioner: Partitioners.DefaultPartitioner,
});

const consumer = kafka.consumer({ groupId: 'order-group' });
```

### Producer

```typescript
await producer.connect();

// Single message
await producer.send({
  topic: 'orders',
  messages: [
    {
      key: order.userId, // Partition key
      value: JSON.stringify(order),
      headers: {
        correlationId: uuid(),
        timestamp: Date.now().toString(),
      },
    },
  ],
});

// Batch messages
await producer.sendBatch({
  topicMessages: [
    {
      topic: 'orders',
      messages: orders.map((o) => ({
        key: o.userId,
        value: JSON.stringify(o),
      })),
    },
  ],
});

// Transactional producer
const txnProducer = kafka.producer({
  transactionalId: 'my-transactional-producer',
});

await txnProducer.transaction(async (tx) => {
  await tx.send({ topic: 'orders', messages });
  await tx.sendOffsets({
    consumerGroupId: 'order-group',
    topics: [{ topic: 'orders', partitions }],
  });
});
```

### Consumer

```typescript
await consumer.connect();
await consumer.subscribe({ topic: 'orders', fromBeginning: false });

await consumer.run({
  eachMessage: async ({ topic, partition, message }) => {
    const order = JSON.parse(message.value!.toString());
    console.log({
      topic,
      partition,
      offset: message.offset,
      key: message.key?.toString(),
      value: order,
    });

    await processOrder(order);
  },
});

// Batch processing
await consumer.run({
  eachBatch: async ({ batch, heartbeat, resolveOffset, commitOffsetsIfNecessary }) => {
    for (const message of batch.messages) {
      await processMessage(message);
      resolveOffset(message.offset);
      await heartbeat();
    }
    await commitOffsetsIfNecessary();
  },
});
```

### Admin Operations

```typescript
const admin = kafka.admin();
await admin.connect();

// Create topic
await admin.createTopics({
  topics: [
    {
      topic: 'orders',
      numPartitions: 6,
      replicationFactor: 3,
      configEntries: [
        { name: 'retention.ms', value: '604800000' }, // 7 days
        { name: 'cleanup.policy', value: 'delete' },
      ],
    },
  ],
});

// List topics
const topics = await admin.listTopics();

// Describe consumer group
const groupInfo = await admin.describeGroups(['order-group']);
```

## Event Sourcing

### Event Store

```typescript
interface DomainEvent {
  id: string;
  aggregateId: string;
  aggregateType: string;
  type: string;
  payload: unknown;
  version: number;
  timestamp: Date;
  metadata: Record<string, string>;
}

class EventStore {
  async appendEvents(
    aggregateId: string,
    events: DomainEvent[],
    expectedVersion: number,
  ): Promise<void> {
    await db.transaction(async (tx) => {
      // Optimistic concurrency check
      const currentVersion = await tx.query(
        'SELECT MAX(version) FROM events WHERE aggregate_id = ?',
        [aggregateId],
      );

      if (currentVersion !== expectedVersion) {
        throw new ConcurrencyError('Version mismatch');
      }

      for (const event of events) {
        await tx.query(
          `INSERT INTO events (id, aggregate_id, aggregate_type, type, payload, version, timestamp, metadata)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
          [
            event.id,
            event.aggregateId,
            event.aggregateType,
            event.type,
            JSON.stringify(event.payload),
            event.version,
            event.timestamp,
            JSON.stringify(event.metadata),
          ],
        );
      }
    });
  }

  async getEvents(aggregateId: string): Promise<DomainEvent[]> {
    return await db.query(
      'SELECT * FROM events WHERE aggregate_id = ? ORDER BY version',
      [aggregateId],
    );
  }
}
```

### Aggregate

```typescript
abstract class AggregateRoot {
  protected version: number = 0;
  private changes: DomainEvent[] = [];

  protected apply(event: DomainEvent): void {
    this.applyEvent(event);
    this.changes.push(event);
  }

  protected abstract applyEvent(event: DomainEvent): void;

  getUncommittedChanges(): DomainEvent[] {
    return this.changes;
  }

  markChangesAsCommitted(): void {
    this.changes = [];
  }

  loadFromHistory(events: DomainEvent[]): void {
    for (const event of events) {
      this.applyEvent(event);
      this.version = event.version;
    }
  }
}

class Order extends AggregateRoot {
  private status: string = 'pending';
  private items: OrderItem[] = [];

  create(id: string, items: OrderItem[]): void {
    this.apply({
      id: uuid(),
      aggregateId: id,
      aggregateType: 'Order',
      type: 'OrderCreated',
      payload: { items },
      version: this.version + 1,
      timestamp: new Date(),
      metadata: {},
    });
  }

  confirm(): void {
    if (this.status !== 'pending') {
      throw new Error('Order cannot be confirmed');
    }

    this.apply({
      id: uuid(),
      aggregateId: this.id,
      aggregateType: 'Order',
      type: 'OrderConfirmed',
      payload: {},
      version: this.version + 1,
      timestamp: new Date(),
      metadata: {},
    });
  }

  protected applyEvent(event: DomainEvent): void {
    switch (event.type) {
      case 'OrderCreated':
        this.items = event.payload.items;
        this.status = 'pending';
        break;
      case 'OrderConfirmed':
        this.status = 'confirmed';
        break;
    }
  }
}
```

## Pub/Sub Pattern

### Simple Event Bus

```typescript
type EventHandler = (event: unknown) => Promise<void>;

class EventBus {
  private handlers = new Map<string, EventHandler[]>();

  subscribe(eventType: string, handler: EventHandler): void {
    const handlers = this.handlers.get(eventType) || [];
    handlers.push(handler);
    this.handlers.set(eventType, handlers);
  }

  async publish(eventType: string, event: unknown): Promise<void> {
    const handlers = this.handlers.get(eventType) || [];
    await Promise.all(handlers.map((h) => h(event)));
  }
}

// Usage
const eventBus = new EventBus();

eventBus.subscribe('order.created', async (event) => {
  await sendOrderConfirmationEmail(event);
});

eventBus.subscribe('order.created', async (event) => {
  await notifyWarehouse(event);
});

await eventBus.publish('order.created', { orderId: '123' });
```

### NestJS Event Emitter

```typescript
import { EventEmitter2 } from '@nestjs/event-emitter';

@Injectable()
export class OrderService {
  constructor(private eventEmitter: EventEmitter2) {}

  async createOrder(data: CreateOrderDTO): Promise<Order> {
    const order = await this.orderRepo.create(data);

    this.eventEmitter.emit('order.created', new OrderCreatedEvent(order));

    return order;
  }
}

@Injectable()
export class NotificationService {
  @OnEvent('order.created')
  async handleOrderCreated(event: OrderCreatedEvent) {
    await this.sendEmail(event.order.userId, 'Order confirmed');
  }
}
```

## CQRS Pattern

```typescript
// Command
interface CreateOrderCommand {
  userId: string;
  items: OrderItem[];
}

// Query
interface GetOrderQuery {
  orderId: string;
}

// Command Handler
@Injectable()
class CreateOrderHandler {
  async execute(command: CreateOrderCommand): Promise<string> {
    const order = Order.create(uuid(), command.items);
    await this.eventStore.appendEvents(order.id, order.getUncommittedChanges(), 0);
    return order.id;
  }
}

// Query Handler (reads from read model)
@Injectable()
class GetOrderHandler {
  async execute(query: GetOrderQuery): Promise<OrderReadModel> {
    return await this.readModelRepo.findById(query.orderId);
  }
}

// Projection (updates read model from events)
@Injectable()
class OrderProjection {
  @OnEvent('OrderCreated')
  async handleOrderCreated(event: OrderCreatedEvent) {
    await this.readModelRepo.insert({
      id: event.aggregateId,
      status: 'pending',
      items: event.payload.items,
      createdAt: event.timestamp,
    });
  }

  @OnEvent('OrderConfirmed')
  async handleOrderConfirmed(event: OrderConfirmedEvent) {
    await this.readModelRepo.update(event.aggregateId, {
      status: 'confirmed',
      confirmedAt: event.timestamp,
    });
  }
}
```
