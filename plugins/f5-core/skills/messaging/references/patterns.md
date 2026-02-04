# Messaging Patterns Reference

## Saga Pattern

Manage distributed transactions across multiple services.

### Choreography-Based Saga

```typescript
// Each service listens for events and publishes next event

// Order Service
orderQueue.process(async (job) => {
  const order = await createOrder(job.data);
  await eventBus.publish('order.created', { orderId: order.id });
});

// Payment Service
eventBus.subscribe('order.created', async (event) => {
  try {
    await processPayment(event.orderId);
    await eventBus.publish('payment.completed', { orderId: event.orderId });
  } catch (err) {
    await eventBus.publish('payment.failed', {
      orderId: event.orderId,
      reason: err.message,
    });
  }
});

// Inventory Service
eventBus.subscribe('payment.completed', async (event) => {
  try {
    await reserveInventory(event.orderId);
    await eventBus.publish('inventory.reserved', { orderId: event.orderId });
  } catch (err) {
    await eventBus.publish('inventory.failed', { orderId: event.orderId });
  }
});

// Compensation handlers
eventBus.subscribe('inventory.failed', async (event) => {
  await refundPayment(event.orderId);
  await cancelOrder(event.orderId);
});
```

### Orchestration-Based Saga

```typescript
class OrderSaga {
  async execute(orderData: CreateOrderDTO): Promise<Order> {
    const saga = new Saga('create-order');

    try {
      // Step 1: Create Order
      const order = await saga.step('create-order', {
        action: () => this.orderService.create(orderData),
        compensation: (order) => this.orderService.cancel(order.id),
      });

      // Step 2: Process Payment
      await saga.step('process-payment', {
        action: () => this.paymentService.process(order.id, orderData.total),
        compensation: () => this.paymentService.refund(order.id),
      });

      // Step 3: Reserve Inventory
      await saga.step('reserve-inventory', {
        action: () => this.inventoryService.reserve(order.items),
        compensation: () => this.inventoryService.release(order.items),
      });

      // Step 4: Ship Order
      await saga.step('ship-order', {
        action: () => this.shippingService.create(order.id),
        compensation: () => this.shippingService.cancel(order.id),
      });

      return order;
    } catch (err) {
      await saga.rollback();
      throw err;
    }
  }
}
```

## Outbox Pattern

Ensure reliable message publishing with database transactions.

```typescript
// 1. Write to database and outbox in same transaction
async function createOrder(data: CreateOrderDTO) {
  return await db.transaction(async (tx) => {
    // Create order
    const order = await tx.insert(orders).values(data).returning();

    // Write to outbox
    await tx.insert(outbox).values({
      id: uuid(),
      aggregateType: 'Order',
      aggregateId: order.id,
      eventType: 'OrderCreated',
      payload: JSON.stringify(order),
      createdAt: new Date(),
    });

    return order;
  });
}

// 2. Outbox processor publishes messages
async function processOutbox() {
  const messages = await db
    .select()
    .from(outbox)
    .where(eq(outbox.processedAt, null))
    .limit(100);

  for (const msg of messages) {
    try {
      await messageQueue.publish(msg.eventType, JSON.parse(msg.payload));
      await db
        .update(outbox)
        .set({ processedAt: new Date() })
        .where(eq(outbox.id, msg.id));
    } catch (err) {
      console.error('Failed to process outbox message', err);
    }
  }
}

// Run processor periodically
setInterval(processOutbox, 5000);
```

## Idempotency Pattern

Ensure messages can be processed multiple times safely.

```typescript
class IdempotentProcessor {
  constructor(
    private redis: Redis,
    private ttlSeconds: number = 86400,
  ) {}

  async process<T>(
    messageId: string,
    handler: () => Promise<T>,
  ): Promise<T | null> {
    const key = `processed:${messageId}`;

    // Check if already processed
    const exists = await this.redis.exists(key);
    if (exists) {
      console.log(`Message ${messageId} already processed`);
      return null;
    }

    // Try to acquire lock
    const acquired = await this.redis.set(
      key,
      'processing',
      'EX',
      this.ttlSeconds,
      'NX',
    );

    if (!acquired) {
      console.log(`Message ${messageId} is being processed`);
      return null;
    }

    try {
      const result = await handler();
      await this.redis.set(key, 'completed', 'EX', this.ttlSeconds);
      return result;
    } catch (err) {
      await this.redis.del(key);
      throw err;
    }
  }
}

// Usage
const processor = new IdempotentProcessor(redis);

worker.process(async (job) => {
  await processor.process(job.data.messageId, async () => {
    await processOrder(job.data);
  });
});
```

## Retry Strategies

### Exponential Backoff

```typescript
function calculateBackoff(attempt: number, baseDelay: number = 1000): number {
  return Math.min(baseDelay * Math.pow(2, attempt), 30000);
}

// BullMQ configuration
const queue = new Queue('tasks', {
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'exponential',
      delay: 1000, // 1s, 2s, 4s, 8s, 16s
    },
  },
});
```

### Fixed Delay with Jitter

```typescript
function calculateDelayWithJitter(baseDelay: number): number {
  const jitter = Math.random() * 0.3 * baseDelay; // 30% jitter
  return baseDelay + jitter;
}

const queue = new Queue('tasks', {
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'custom',
      delay: (attemptsMade) => calculateDelayWithJitter(1000 * attemptsMade),
    },
  },
});
```

## Dead Letter Queue

```typescript
class DeadLetterHandler {
  constructor(
    private dlqQueue: Queue,
    private alertService: AlertService,
  ) {}

  async handleFailedJob(job: Job, err: Error): Promise<void> {
    // Add to DLQ with context
    await this.dlqQueue.add('failed', {
      originalQueue: job.queue.name,
      originalJob: {
        id: job.id,
        data: job.data,
        opts: job.opts,
      },
      error: {
        message: err.message,
        stack: err.stack,
      },
      attempts: job.attemptsMade,
      failedAt: new Date(),
    });

    // Alert for critical failures
    if (this.isCritical(job)) {
      await this.alertService.notify({
        level: 'critical',
        message: `Job ${job.id} failed after ${job.attemptsMade} attempts`,
        context: { queue: job.queue.name, error: err.message },
      });
    }
  }

  async reprocessDLQ(): Promise<void> {
    const jobs = await this.dlqQueue.getJobs(['waiting']);

    for (const job of jobs) {
      try {
        // Re-add to original queue
        const originalQueue = new Queue(job.data.originalQueue);
        await originalQueue.add(
          job.data.originalJob.data.type,
          job.data.originalJob.data,
        );

        // Remove from DLQ
        await job.remove();
      } catch (err) {
        console.error('Failed to reprocess DLQ job', err);
      }
    }
  }
}
```

## Priority Queue

```typescript
// BullMQ priority (lower = higher priority)
await queue.add('urgent', data, { priority: 1 });
await queue.add('normal', data, { priority: 5 });
await queue.add('low', data, { priority: 10 });

// Custom priority based on user tier
function getPriority(user: User): number {
  switch (user.tier) {
    case 'enterprise':
      return 1;
    case 'business':
      return 3;
    case 'free':
      return 10;
    default:
      return 5;
  }
}
```

## Rate Limiting

```typescript
// BullMQ rate limiting
const queue = new Queue('api-calls', {
  limiter: {
    max: 100,
    duration: 1000, // 100 per second
  },
});

// Per-key rate limiting
const queue = new Queue('api-calls', {
  limiter: {
    max: 10,
    duration: 1000,
    groupKey: 'userId', // 10 per second per user
  },
});
```
