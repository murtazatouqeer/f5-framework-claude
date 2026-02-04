---
name: data-consistency
description: Patterns for maintaining data consistency across distributed services
category: architecture/distributed-systems
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Data Consistency Patterns

## Overview

In distributed systems, maintaining data consistency across services is challenging.
Different consistency models offer trade-offs between availability, performance,
and correctness.

## Consistency Models

```
┌─────────────────────────────────────────────────────────────┐
│              CONSISTENCY SPECTRUM                           │
│                                                             │
│  Strong ◄──────────────────────────────────────► Eventual   │
│                                                             │
│  • Linearizable    • Causal      • Read-your-   • Eventual  │
│  • Sequential      • Session     writes                     │
│                                                             │
│  ◄─── Consistency                    Availability ───►      │
│  ◄─── Latency                        Performance ───►       │
└─────────────────────────────────────────────────────────────┘
```

## Saga Pattern

### Choreography-Based Saga

```typescript
// Each service listens for events and publishes results
// No central coordinator

// Order Service
class OrderService {
  constructor(private eventBus: EventBus) {
    this.eventBus.subscribe('payment.completed', this.handlePaymentCompleted.bind(this));
    this.eventBus.subscribe('payment.failed', this.handlePaymentFailed.bind(this));
    this.eventBus.subscribe('inventory.reserved', this.handleInventoryReserved.bind(this));
    this.eventBus.subscribe('inventory.failed', this.handleInventoryFailed.bind(this));
  }

  async createOrder(data: CreateOrderData): Promise<Order> {
    const order = await this.orderRepository.create({
      ...data,
      status: 'pending',
    });

    // Start saga by publishing event
    await this.eventBus.publish(new OrderCreatedEvent(order.id, data.items, data.total));

    return order;
  }

  async handlePaymentCompleted(event: PaymentCompletedEvent): Promise<void> {
    await this.orderRepository.updateStatus(event.orderId, 'payment_completed');
  }

  async handlePaymentFailed(event: PaymentFailedEvent): Promise<void> {
    await this.orderRepository.updateStatus(event.orderId, 'payment_failed');
    // Compensating action: cancel order
    await this.cancelOrder(event.orderId);
  }

  async handleInventoryReserved(event: InventoryReservedEvent): Promise<void> {
    await this.orderRepository.updateStatus(event.orderId, 'confirmed');
  }

  async handleInventoryFailed(event: InventoryFailedEvent): Promise<void> {
    // Compensating action: refund payment
    await this.eventBus.publish(new RefundRequestedEvent(event.orderId));
    await this.orderRepository.updateStatus(event.orderId, 'cancelled');
  }
}

// Payment Service
class PaymentService {
  constructor(private eventBus: EventBus) {
    this.eventBus.subscribe('order.created', this.handleOrderCreated.bind(this));
    this.eventBus.subscribe('refund.requested', this.handleRefundRequested.bind(this));
  }

  async handleOrderCreated(event: OrderCreatedEvent): Promise<void> {
    try {
      const payment = await this.processPayment(event.orderId, event.total);

      await this.eventBus.publish(new PaymentCompletedEvent(
        event.orderId,
        payment.id
      ));
    } catch (error) {
      await this.eventBus.publish(new PaymentFailedEvent(
        event.orderId,
        error.message
      ));
    }
  }

  async handleRefundRequested(event: RefundRequestedEvent): Promise<void> {
    await this.processRefund(event.orderId);
  }
}

// Inventory Service
class InventoryService {
  constructor(private eventBus: EventBus) {
    this.eventBus.subscribe('payment.completed', this.handlePaymentCompleted.bind(this));
  }

  async handlePaymentCompleted(event: PaymentCompletedEvent): Promise<void> {
    try {
      await this.reserveInventory(event.orderId);

      await this.eventBus.publish(new InventoryReservedEvent(event.orderId));
    } catch (error) {
      await this.eventBus.publish(new InventoryFailedEvent(
        event.orderId,
        error.message
      ));
    }
  }
}
```

### Orchestration-Based Saga

```typescript
// Central saga coordinator manages the workflow

interface SagaStep<T> {
  name: string;
  execute(context: T): Promise<void>;
  compensate(context: T): Promise<void>;
}

class SagaOrchestrator<T> {
  private steps: SagaStep<T>[] = [];
  private executedSteps: SagaStep<T>[] = [];

  addStep(step: SagaStep<T>): this {
    this.steps.push(step);
    return this;
  }

  async execute(context: T): Promise<void> {
    for (const step of this.steps) {
      try {
        await step.execute(context);
        this.executedSteps.push(step);
      } catch (error) {
        await this.compensate(context);
        throw new SagaExecutionError(step.name, error);
      }
    }
  }

  private async compensate(context: T): Promise<void> {
    // Compensate in reverse order
    for (const step of [...this.executedSteps].reverse()) {
      try {
        await step.compensate(context);
      } catch (error) {
        // Log but continue compensation
        console.error(`Compensation failed for ${step.name}:`, error);
      }
    }
  }
}

// Order placement saga
interface OrderSagaContext {
  orderId: string;
  customerId: string;
  items: OrderItem[];
  total: number;
  paymentId?: string;
  reservationId?: string;
  shipmentId?: string;
}

const orderSaga = new SagaOrchestrator<OrderSagaContext>()
  .addStep({
    name: 'CreateOrder',
    async execute(ctx) {
      ctx.orderId = await orderService.create(ctx);
    },
    async compensate(ctx) {
      await orderService.cancel(ctx.orderId);
    },
  })
  .addStep({
    name: 'ProcessPayment',
    async execute(ctx) {
      ctx.paymentId = await paymentService.charge(ctx.customerId, ctx.total);
    },
    async compensate(ctx) {
      if (ctx.paymentId) {
        await paymentService.refund(ctx.paymentId);
      }
    },
  })
  .addStep({
    name: 'ReserveInventory',
    async execute(ctx) {
      ctx.reservationId = await inventoryService.reserve(ctx.items);
    },
    async compensate(ctx) {
      if (ctx.reservationId) {
        await inventoryService.release(ctx.reservationId);
      }
    },
  })
  .addStep({
    name: 'CreateShipment',
    async execute(ctx) {
      ctx.shipmentId = await shippingService.create(ctx.orderId, ctx.items);
    },
    async compensate(ctx) {
      if (ctx.shipmentId) {
        await shippingService.cancel(ctx.shipmentId);
      }
    },
  });

// Usage
try {
  await orderSaga.execute({
    customerId: 'cust-123',
    items: orderItems,
    total: 99.99,
  });
} catch (error) {
  // Saga failed and compensated
  console.error('Order saga failed:', error);
}
```

## Two-Phase Commit (2PC)

```typescript
// Distributed transaction coordinator
interface TransactionParticipant {
  prepare(transactionId: string): Promise<boolean>;
  commit(transactionId: string): Promise<void>;
  rollback(transactionId: string): Promise<void>;
}

class TwoPhaseCommitCoordinator {
  private participants: TransactionParticipant[] = [];
  private preparedParticipants: TransactionParticipant[] = [];

  addParticipant(participant: TransactionParticipant): void {
    this.participants.push(participant);
  }

  async execute(transactionId: string): Promise<void> {
    // Phase 1: Prepare
    const prepared = await this.preparePhase(transactionId);

    if (prepared) {
      // Phase 2: Commit
      await this.commitPhase(transactionId);
    } else {
      // Phase 2: Rollback
      await this.rollbackPhase(transactionId);
      throw new TransactionAbortedError(transactionId);
    }
  }

  private async preparePhase(transactionId: string): Promise<boolean> {
    for (const participant of this.participants) {
      try {
        const ready = await participant.prepare(transactionId);
        if (!ready) {
          return false;
        }
        this.preparedParticipants.push(participant);
      } catch (error) {
        return false;
      }
    }
    return true;
  }

  private async commitPhase(transactionId: string): Promise<void> {
    const commitPromises = this.preparedParticipants.map(p =>
      p.commit(transactionId)
    );
    await Promise.all(commitPromises);
  }

  private async rollbackPhase(transactionId: string): Promise<void> {
    const rollbackPromises = this.preparedParticipants.map(p =>
      p.rollback(transactionId)
    );
    await Promise.allSettled(rollbackPromises);
  }
}

// Participant implementation
class OrderParticipant implements TransactionParticipant {
  private pendingOrders: Map<string, Order> = new Map();

  async prepare(transactionId: string): Promise<boolean> {
    try {
      // Validate and lock resources
      const order = await this.orderRepository.findByTransactionId(transactionId);
      if (!order) return false;

      await this.lockOrder(order.id);
      this.pendingOrders.set(transactionId, order);
      return true;
    } catch {
      return false;
    }
  }

  async commit(transactionId: string): Promise<void> {
    const order = this.pendingOrders.get(transactionId);
    if (order) {
      await this.orderRepository.confirm(order.id);
      await this.unlockOrder(order.id);
      this.pendingOrders.delete(transactionId);
    }
  }

  async rollback(transactionId: string): Promise<void> {
    const order = this.pendingOrders.get(transactionId);
    if (order) {
      await this.orderRepository.cancel(order.id);
      await this.unlockOrder(order.id);
      this.pendingOrders.delete(transactionId);
    }
  }
}
```

## Eventual Consistency with Outbox Pattern

```typescript
// Outbox pattern ensures reliable event publishing
interface OutboxMessage {
  id: string;
  aggregateType: string;
  aggregateId: string;
  eventType: string;
  payload: any;
  createdAt: Date;
  processedAt?: Date;
}

class OutboxRepository {
  async save(message: OutboxMessage): Promise<void> {
    await this.db.query(
      `INSERT INTO outbox (id, aggregate_type, aggregate_id, event_type, payload, created_at)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [message.id, message.aggregateType, message.aggregateId,
       message.eventType, JSON.stringify(message.payload), message.createdAt]
    );
  }

  async getUnprocessed(limit: number): Promise<OutboxMessage[]> {
    const rows = await this.db.query(
      `SELECT * FROM outbox WHERE processed_at IS NULL
       ORDER BY created_at ASC LIMIT $1 FOR UPDATE SKIP LOCKED`,
      [limit]
    );
    return rows.map(this.toMessage);
  }

  async markProcessed(id: string): Promise<void> {
    await this.db.query(
      'UPDATE outbox SET processed_at = NOW() WHERE id = $1',
      [id]
    );
  }
}

// Service using outbox pattern
class OrderService {
  constructor(
    private orderRepository: OrderRepository,
    private outboxRepository: OutboxRepository,
    private db: Database
  ) {}

  async createOrder(data: CreateOrderData): Promise<Order> {
    return this.db.transaction(async (trx) => {
      // Create order
      const order = await this.orderRepository.create(data, trx);

      // Add event to outbox (same transaction)
      await this.outboxRepository.save({
        id: crypto.randomUUID(),
        aggregateType: 'Order',
        aggregateId: order.id,
        eventType: 'OrderCreated',
        payload: {
          orderId: order.id,
          customerId: data.customerId,
          items: data.items,
          total: data.total,
        },
        createdAt: new Date(),
      }, trx);

      return order;
    });
  }
}

// Outbox processor (separate process/thread)
class OutboxProcessor {
  constructor(
    private outboxRepository: OutboxRepository,
    private eventBus: EventBus
  ) {}

  async process(): Promise<void> {
    const messages = await this.outboxRepository.getUnprocessed(100);

    for (const message of messages) {
      try {
        await this.eventBus.publish(message.eventType, message.payload);
        await this.outboxRepository.markProcessed(message.id);
      } catch (error) {
        console.error(`Failed to process outbox message ${message.id}:`, error);
        // Will be retried on next run
      }
    }
  }

  // Run periodically
  startPolling(intervalMs: number = 1000): void {
    setInterval(() => this.process(), intervalMs);
  }
}
```

## Change Data Capture (CDC)

```typescript
// CDC using Debezium-style approach
interface ChangeEvent {
  source: {
    table: string;
    db: string;
    timestamp: number;
  };
  operation: 'c' | 'u' | 'd'; // create, update, delete
  before: Record<string, any> | null;
  after: Record<string, any> | null;
}

class CDCProcessor {
  private handlers: Map<string, ChangeHandler[]> = new Map();

  onTable(tableName: string, handler: ChangeHandler): void {
    const handlers = this.handlers.get(tableName) || [];
    handlers.push(handler);
    this.handlers.set(tableName, handlers);
  }

  async processChange(event: ChangeEvent): Promise<void> {
    const handlers = this.handlers.get(event.source.table) || [];

    for (const handler of handlers) {
      try {
        await handler(event);
      } catch (error) {
        console.error(`CDC handler error for ${event.source.table}:`, error);
      }
    }
  }
}

// Usage: Sync order data to search index
const cdcProcessor = new CDCProcessor();

cdcProcessor.onTable('orders', async (event) => {
  switch (event.operation) {
    case 'c':
    case 'u':
      await searchIndex.upsert('orders', event.after!.id, event.after);
      break;
    case 'd':
      await searchIndex.delete('orders', event.before!.id);
      break;
  }
});

// Usage: Maintain materialized view
cdcProcessor.onTable('order_items', async (event) => {
  const orderId = event.after?.order_id || event.before?.order_id;
  await orderStatsService.recalculate(orderId);
});
```

## CQRS with Eventual Consistency

```typescript
// Command side (write model)
class OrderCommandHandler {
  constructor(
    private orderRepository: OrderRepository,
    private eventStore: EventStore
  ) {}

  async handle(command: PlaceOrderCommand): Promise<string> {
    const order = Order.place(
      command.customerId,
      command.items,
      command.shippingAddress
    );

    // Save to write model
    await this.orderRepository.save(order);

    // Publish events for read model updates
    const events = order.pullDomainEvents();
    for (const event of events) {
      await this.eventStore.append(event);
    }

    return order.id;
  }
}

// Query side (read model)
class OrderQueryService {
  constructor(private readDb: ReadDatabase) {}

  async getOrderSummary(orderId: string): Promise<OrderSummaryDTO> {
    return this.readDb.query(
      'SELECT * FROM order_summary_view WHERE id = $1',
      [orderId]
    );
  }

  async getCustomerOrders(customerId: string): Promise<OrderListDTO[]> {
    return this.readDb.query(
      'SELECT * FROM customer_orders_view WHERE customer_id = $1 ORDER BY created_at DESC',
      [customerId]
    );
  }
}

// Event projector (maintains read models)
class OrderProjector {
  constructor(private readDb: ReadDatabase) {}

  async project(event: DomainEvent): Promise<void> {
    switch (event.constructor.name) {
      case 'OrderPlacedEvent':
        await this.handleOrderPlaced(event as OrderPlacedEvent);
        break;
      case 'OrderShippedEvent':
        await this.handleOrderShipped(event as OrderShippedEvent);
        break;
      case 'OrderDeliveredEvent':
        await this.handleOrderDelivered(event as OrderDeliveredEvent);
        break;
    }
  }

  private async handleOrderPlaced(event: OrderPlacedEvent): Promise<void> {
    await this.readDb.query(
      `INSERT INTO order_summary_view
       (id, customer_id, status, total, item_count, created_at)
       VALUES ($1, $2, $3, $4, $5, $6)`,
      [event.orderId, event.customerId, 'placed',
       event.total, event.items.length, event.occurredOn]
    );

    await this.readDb.query(
      `INSERT INTO customer_orders_view
       (order_id, customer_id, status, total, created_at)
       VALUES ($1, $2, $3, $4, $5)`,
      [event.orderId, event.customerId, 'placed',
       event.total, event.occurredOn]
    );
  }

  private async handleOrderShipped(event: OrderShippedEvent): Promise<void> {
    await this.readDb.query(
      `UPDATE order_summary_view
       SET status = 'shipped', tracking_number = $2, shipped_at = $3
       WHERE id = $1`,
      [event.orderId, event.trackingNumber, event.occurredOn]
    );

    await this.readDb.query(
      `UPDATE customer_orders_view
       SET status = 'shipped'
       WHERE order_id = $1`,
      [event.orderId]
    );
  }
}
```

## Conflict Resolution

```typescript
// Last-Write-Wins (LWW)
interface VersionedEntity {
  id: string;
  version: number;
  timestamp: Date;
  data: any;
}

class LWWConflictResolver {
  resolve(local: VersionedEntity, remote: VersionedEntity): VersionedEntity {
    // Latest timestamp wins
    return local.timestamp > remote.timestamp ? local : remote;
  }
}

// Merge (for compatible changes)
interface MergeableEntity {
  id: string;
  version: number;
  changes: Change[];
}

class MergeConflictResolver {
  resolve(base: MergeableEntity, local: MergeableEntity, remote: MergeableEntity): MergeableEntity {
    const localChanges = this.diffChanges(base.changes, local.changes);
    const remoteChanges = this.diffChanges(base.changes, remote.changes);

    // Check for conflicts
    const conflicts = this.findConflicts(localChanges, remoteChanges);

    if (conflicts.length > 0) {
      throw new MergeConflictError(conflicts);
    }

    // Merge non-conflicting changes
    return {
      id: base.id,
      version: Math.max(local.version, remote.version) + 1,
      changes: [...base.changes, ...localChanges, ...remoteChanges],
    };
  }
}

// CRDT (Conflict-free Replicated Data Type)
class GCounter {
  private counts: Map<string, number> = new Map();

  constructor(private nodeId: string) {}

  increment(amount: number = 1): void {
    const current = this.counts.get(this.nodeId) || 0;
    this.counts.set(this.nodeId, current + amount);
  }

  value(): number {
    return Array.from(this.counts.values()).reduce((a, b) => a + b, 0);
  }

  merge(other: GCounter): void {
    for (const [nodeId, count] of other.counts) {
      const current = this.counts.get(nodeId) || 0;
      this.counts.set(nodeId, Math.max(current, count));
    }
  }

  state(): Map<string, number> {
    return new Map(this.counts);
  }
}

// LWW-Register CRDT
class LWWRegister<T> {
  private value: T;
  private timestamp: number;

  constructor(initialValue: T) {
    this.value = initialValue;
    this.timestamp = Date.now();
  }

  set(value: T): void {
    this.value = value;
    this.timestamp = Date.now();
  }

  get(): T {
    return this.value;
  }

  merge(other: LWWRegister<T>): void {
    if (other.timestamp > this.timestamp) {
      this.value = other.value;
      this.timestamp = other.timestamp;
    }
  }
}
```

## Pattern Selection Guide

| Pattern | Consistency | Performance | Complexity | Use Case |
|---------|-------------|-------------|------------|----------|
| 2PC | Strong | Low | High | Financial transactions |
| Saga | Eventual | High | Medium | Long-running workflows |
| Outbox | Eventual | High | Low | Event publishing |
| CDC | Eventual | Very High | Medium | Data synchronization |
| CRDT | Strong Eventual | High | Medium | Collaborative editing |

## When to Use

- **2PC**: When strong consistency is required and latency is acceptable
- **Saga**: Long-running transactions across services
- **Outbox**: Reliable event publishing with local transactions
- **CDC**: Real-time data synchronization across systems
- **CRDT**: Distributed data with offline support
