---
name: messaging-patterns
description: Common messaging patterns and architectures
category: messaging/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Messaging Patterns

## Overview

Messaging patterns define how components communicate asynchronously. Choosing the right pattern impacts system scalability, reliability, and complexity.

## Point-to-Point

One message, one consumer. Used for task distribution.

```
Producer → Queue → Consumer
```

```typescript
// Producer
await queue.send({
  type: 'process-order',
  orderId: '12345',
});

// Consumer
queue.process(async (message) => {
  await processOrder(message.orderId);
  message.ack();
});
```

### Characteristics

- Each message consumed by exactly one consumer
- Good for workload distribution
- Supports multiple competing consumers
- Message removed after processing

### Use Cases

- Background job processing
- Task queues
- Work distribution
- Order processing

## Publish-Subscribe (Pub/Sub)

One message, many consumers. Used for event broadcasting.

```
Publisher → Topic → Subscriber 1
                 → Subscriber 2
                 → Subscriber 3
```

```typescript
// Publisher
await eventBus.publish('order.placed', {
  orderId: '12345',
  customerId: 'cust-001',
  total: 99.99,
});

// Subscriber 1: Email Service
eventBus.subscribe('order.placed', async (event) => {
  await sendConfirmationEmail(event.customerId, event.orderId);
});

// Subscriber 2: Inventory Service
eventBus.subscribe('order.placed', async (event) => {
  await reserveInventory(event.orderId);
});

// Subscriber 3: Analytics Service
eventBus.subscribe('order.placed', async (event) => {
  await trackEvent('order_placed', event);
});
```

### Characteristics

- Message delivered to all subscribers
- Publishers and subscribers decoupled
- Supports dynamic subscription
- Message typically retained after delivery

### Use Cases

- Event notification
- System integration
- Real-time updates
- Audit logging

## Request-Reply

Synchronous semantics over async transport.

```
Client → Request Queue → Server
Client ← Reply Queue   ← Server
```

```typescript
// Client
const correlationId = uuid();
const response = await rpc.call('calculate-shipping', {
  correlationId,
  orderId: '12345',
  destination: 'USA',
});

// Server
rpc.handle('calculate-shipping', async (request) => {
  const cost = await calculateShipping(request);
  return { correlationId: request.correlationId, cost };
});
```

### Characteristics

- Simulates RPC over messaging
- Uses correlation IDs to match replies
- Temporary reply queues
- Timeout handling required

### Use Cases

- Service-to-service calls
- Query operations
- When response is needed
- Gradual migration from sync

## Fan-Out

Distribute work across multiple consumers.

```
Producer → Exchange → Queue 1 → Consumer 1
                   → Queue 2 → Consumer 2
                   → Queue 3 → Consumer 3
```

```typescript
// RabbitMQ Fan-out Exchange
await channel.assertExchange('notifications', 'fanout', { durable: true });

// Create queues bound to exchange
await channel.assertQueue('email-notifications');
await channel.bindQueue('email-notifications', 'notifications', '');

await channel.assertQueue('push-notifications');
await channel.bindQueue('push-notifications', 'notifications', '');

// Publish to all
channel.publish('notifications', '', Buffer.from(JSON.stringify({
  type: 'new-message',
  userId: 'user-123',
})));
```

## Topic-Based Routing

Route messages based on topic patterns.

```
Producer → Exchange → Queue (pattern: order.*)
                   → Queue (pattern: order.created)
                   → Queue (pattern: *.shipped)
```

```typescript
// RabbitMQ Topic Exchange
await channel.assertExchange('events', 'topic', { durable: true });

// Bind queues with patterns
await channel.bindQueue('order-service', 'events', 'order.*');
await channel.bindQueue('shipping-service', 'events', '*.shipped');
await channel.bindQueue('audit-service', 'events', '#'); // All events

// Publish with routing key
channel.publish('events', 'order.created', Buffer.from(JSON.stringify(event)));
channel.publish('events', 'order.shipped', Buffer.from(JSON.stringify(event)));
```

## Competing Consumers

Multiple consumers process from same queue.

```
            ┌→ Consumer 1
Producer → Queue → Consumer 2
            └→ Consumer 3
```

```typescript
// Multiple workers processing same queue
// Each message goes to only one consumer

// Worker 1
queue.process('tasks', { concurrency: 5 }, async (job) => {
  await processTask(job.data);
});

// Worker 2 (separate process)
queue.process('tasks', { concurrency: 5 }, async (job) => {
  await processTask(job.data);
});

// Load balances automatically
```

### Benefits

- Horizontal scaling
- Load distribution
- Fault tolerance
- Process isolation

## Message Router

Route messages based on content.

```typescript
// Content-based router
class MessageRouter {
  private routes: Map<string, Handler> = new Map();

  register(type: string, handler: Handler): void {
    this.routes.set(type, handler);
  }

  async route(message: Message): Promise<void> {
    const handler = this.routes.get(message.type);

    if (!handler) {
      throw new Error(`No handler for message type: ${message.type}`);
    }

    await handler(message);
  }
}

// Usage
const router = new MessageRouter();
router.register('order.created', handleOrderCreated);
router.register('order.updated', handleOrderUpdated);
router.register('order.cancelled', handleOrderCancelled);

queue.process(async (message) => {
  await router.route(message);
});
```

## Message Filter

Selectively process messages.

```typescript
// Filter pattern
class FilteredConsumer {
  constructor(
    private readonly predicate: (msg: Message) => boolean,
    private readonly handler: Handler
  ) {}

  async process(message: Message): Promise<void> {
    if (this.predicate(message)) {
      await this.handler(message);
    } else {
      // Skip or route elsewhere
      console.log('Message filtered out:', message.id);
    }
  }
}

// Usage
const highValueFilter = new FilteredConsumer(
  (msg) => msg.data.total > 1000,
  handleHighValueOrder
);
```

## Aggregator

Combine multiple messages into one.

```typescript
// Aggregator pattern
class MessageAggregator {
  private buffer: Map<string, Message[]> = new Map();
  private readonly completionSize: number;
  private readonly timeout: number;

  constructor(completionSize: number, timeout: number) {
    this.completionSize = completionSize;
    this.timeout = timeout;
  }

  async aggregate(
    correlationId: string,
    message: Message
  ): Promise<Message[] | null> {
    if (!this.buffer.has(correlationId)) {
      this.buffer.set(correlationId, []);
      // Set timeout for incomplete aggregations
      setTimeout(() => this.release(correlationId), this.timeout);
    }

    const messages = this.buffer.get(correlationId)!;
    messages.push(message);

    if (messages.length >= this.completionSize) {
      return this.release(correlationId);
    }

    return null;
  }

  private release(correlationId: string): Message[] | null {
    const messages = this.buffer.get(correlationId);
    this.buffer.delete(correlationId);
    return messages || null;
  }
}
```

## Pattern Selection Guide

| Pattern | Use When |
|---------|----------|
| Point-to-Point | Task distribution, exactly-once processing |
| Pub/Sub | Event notification, multiple interested parties |
| Request-Reply | Need response, RPC over async |
| Fan-Out | Broadcast to all, parallel processing |
| Topic Routing | Content-based filtering at broker level |
| Competing Consumers | Scale processing horizontally |
| Router | Different handlers for different message types |
| Filter | Selective processing based on content |
| Aggregator | Combine related messages |
