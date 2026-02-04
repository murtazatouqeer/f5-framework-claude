---
name: cqrs-event-sourcing
description: Command Query Responsibility Segregation and Event Sourcing patterns
category: architecture/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CQRS & Event Sourcing

## Overview

CQRS separates read and write operations into different models.
Event Sourcing stores state as a sequence of events rather than current state.

## CQRS Pattern

```
Traditional CRUD:
┌──────────────────────────────────────┐
│              Application             │
│    ┌──────────────────────────┐     │
│    │      Single Model        │     │
│    │   (Read + Write)         │     │
│    └────────────┬─────────────┘     │
│                 │                    │
│    ┌────────────▼─────────────┐     │
│    │       Database           │     │
│    └──────────────────────────┘     │
└──────────────────────────────────────┘

CQRS:
┌──────────────────────────────────────────────────┐
│                   Application                     │
│  ┌─────────────────┐    ┌─────────────────────┐  │
│  │  Command Side   │    │    Query Side       │  │
│  │  (Write Model)  │    │   (Read Model)      │  │
│  └────────┬────────┘    └──────────┬──────────┘  │
│           │                        │             │
│  ┌────────▼────────┐    ┌──────────▼──────────┐  │
│  │  Write Database │───►│   Read Database     │  │
│  │  (Normalized)   │sync│  (Denormalized)     │  │
│  └─────────────────┘    └─────────────────────┘  │
└──────────────────────────────────────────────────┘
```

## Directory Structure

```
src/
├── application/
│   ├── commands/                  # Write side
│   │   ├── handlers/
│   │   │   ├── create-order.handler.ts
│   │   │   └── cancel-order.handler.ts
│   │   └── create-order.command.ts
│   │
│   └── queries/                   # Read side
│       ├── handlers/
│       │   ├── get-order.handler.ts
│       │   └── list-orders.handler.ts
│       └── get-order.query.ts
│
├── domain/
│   ├── aggregates/
│   │   └── order.aggregate.ts
│   ├── events/
│   │   ├── order-created.event.ts
│   │   └── order-cancelled.event.ts
│   └── repositories/
│       └── order.repository.ts
│
├── infrastructure/
│   ├── persistence/
│   │   ├── write/                 # Write model storage
│   │   │   └── event-store.ts
│   │   └── read/                  # Read model storage
│   │       └── order-read.repository.ts
│   └── projections/
│       └── order.projection.ts
│
└── read-models/
    └── order.read-model.ts
```

## CQRS Implementation

### Commands

```typescript
// application/commands/create-order.command.ts
export class CreateOrderCommand {
  constructor(
    public readonly customerId: string,
    public readonly items: Array<{
      productId: string;
      quantity: number;
    }>
  ) {}
}

// application/commands/handlers/create-order.handler.ts
export class CreateOrderHandler {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly eventPublisher: EventPublisher
  ) {}

  async execute(command: CreateOrderCommand): Promise<string> {
    // Create aggregate
    const order = Order.create(
      this.orderRepository.nextId(),
      command.customerId,
      command.items
    );

    // Save to write model
    await this.orderRepository.save(order);

    // Publish events for read model sync
    const events = order.pullDomainEvents();
    await this.eventPublisher.publishAll(events);

    return order.id;
  }
}
```

### Queries

```typescript
// application/queries/get-order.query.ts
export class GetOrderQuery {
  constructor(public readonly orderId: string) {}
}

// application/queries/handlers/get-order.handler.ts
export class GetOrderHandler {
  constructor(
    private readonly orderReadRepository: OrderReadRepository
  ) {}

  async execute(query: GetOrderQuery): Promise<OrderReadModel | null> {
    // Query from read model (optimized for reads)
    return this.orderReadRepository.findById(query.orderId);
  }
}

// read-models/order.read-model.ts
export interface OrderReadModel {
  id: string;
  customerId: string;
  customerName: string;  // Denormalized
  customerEmail: string; // Denormalized
  items: Array<{
    productId: string;
    productName: string;  // Denormalized
    quantity: number;
    unitPrice: number;
    subtotal: number;
  }>;
  total: number;
  status: string;
  statusLabel: string;   // Computed
  createdAt: string;
  updatedAt: string;
}
```

### Projections (Read Model Sync)

```typescript
// infrastructure/projections/order.projection.ts
export class OrderProjection {
  constructor(
    private readonly readDb: ReadDatabase
  ) {}

  @OnEvent('OrderCreated')
  async onOrderCreated(event: OrderCreatedEvent): Promise<void> {
    // Fetch additional data for denormalization
    const customer = await this.customerService.findById(event.customerId);
    const products = await Promise.all(
      event.items.map(item => this.productService.findById(item.productId))
    );

    // Build read model
    const readModel: OrderReadModel = {
      id: event.orderId,
      customerId: event.customerId,
      customerName: customer.name,
      customerEmail: customer.email,
      items: event.items.map((item, index) => ({
        productId: item.productId,
        productName: products[index].name,
        quantity: item.quantity,
        unitPrice: products[index].price,
        subtotal: item.quantity * products[index].price,
      })),
      total: event.total,
      status: 'pending',
      statusLabel: 'Pending',
      createdAt: event.occurredAt.toISOString(),
      updatedAt: event.occurredAt.toISOString(),
    };

    await this.readDb.orders.insert(readModel);
  }

  @OnEvent('OrderConfirmed')
  async onOrderConfirmed(event: OrderConfirmedEvent): Promise<void> {
    await this.readDb.orders.update(
      { id: event.orderId },
      {
        status: 'confirmed',
        statusLabel: 'Confirmed',
        updatedAt: event.occurredAt.toISOString(),
      }
    );
  }

  @OnEvent('OrderShipped')
  async onOrderShipped(event: OrderShippedEvent): Promise<void> {
    await this.readDb.orders.update(
      { id: event.orderId },
      {
        status: 'shipped',
        statusLabel: `Shipped - ${event.trackingNumber}`,
        trackingNumber: event.trackingNumber,
        updatedAt: event.occurredAt.toISOString(),
      }
    );
  }
}
```

## Event Sourcing

```
Traditional State Storage:
┌─────────────┐
│ Orders      │
├─────────────┤
│ id: 1       │
│ status: paid│  ← Only current state
│ total: 100  │
└─────────────┘

Event Sourcing:
┌────────────────────────────────────────────────────┐
│ Events                                             │
├────────────────────────────────────────────────────┤
│ 1. OrderCreated { id: 1, items: [...] }           │
│ 2. OrderItemAdded { orderId: 1, productId: 5 }    │
│ 3. OrderConfirmed { orderId: 1 }                  │
│ 4. PaymentReceived { orderId: 1, amount: 100 }    │
└────────────────────────────────────────────────────┘
         │
         ▼
    Replay events to get current state
```

### Event Store

```typescript
// infrastructure/persistence/write/event-store.ts
export interface StoredEvent {
  id: string;
  aggregateId: string;
  aggregateType: string;
  eventType: string;
  eventData: any;
  metadata: {
    userId?: string;
    correlationId?: string;
    causationId?: string;
  };
  version: number;
  occurredAt: Date;
}

export class EventStore {
  constructor(private readonly db: Database) {}

  async append(
    aggregateId: string,
    events: DomainEvent[],
    expectedVersion: number
  ): Promise<void> {
    const connection = await this.db.getConnection();

    try {
      await connection.beginTransaction();

      // Optimistic concurrency check
      const currentVersion = await this.getCurrentVersion(aggregateId);
      if (currentVersion !== expectedVersion) {
        throw new ConcurrencyError(
          `Expected version ${expectedVersion}, but found ${currentVersion}`
        );
      }

      // Append events
      for (let i = 0; i < events.length; i++) {
        const event = events[i];
        await connection.query(
          `INSERT INTO event_store
           (id, aggregate_id, aggregate_type, event_type, event_data, version, occurred_at)
           VALUES ($1, $2, $3, $4, $5, $6, $7)`,
          [
            crypto.randomUUID(),
            aggregateId,
            event.aggregateType,
            event.eventType,
            JSON.stringify(event.data),
            expectedVersion + i + 1,
            new Date(),
          ]
        );
      }

      await connection.commit();
    } catch (error) {
      await connection.rollback();
      throw error;
    }
  }

  async getEvents(aggregateId: string): Promise<StoredEvent[]> {
    const result = await this.db.query(
      `SELECT * FROM event_store
       WHERE aggregate_id = $1
       ORDER BY version ASC`,
      [aggregateId]
    );
    return result.rows;
  }

  private async getCurrentVersion(aggregateId: string): Promise<number> {
    const result = await this.db.query(
      `SELECT COALESCE(MAX(version), 0) as version
       FROM event_store
       WHERE aggregate_id = $1`,
      [aggregateId]
    );
    return result.rows[0].version;
  }
}
```

### Event-Sourced Aggregate

```typescript
// domain/aggregates/order.aggregate.ts
export abstract class EventSourcedAggregate {
  private _uncommittedEvents: DomainEvent[] = [];
  private _version: number = 0;

  get version(): number {
    return this._version;
  }

  get uncommittedEvents(): DomainEvent[] {
    return [...this._uncommittedEvents];
  }

  clearUncommittedEvents(): void {
    this._uncommittedEvents = [];
  }

  protected apply(event: DomainEvent): void {
    this.applyEvent(event);
    this._uncommittedEvents.push(event);
    this._version++;
  }

  protected abstract applyEvent(event: DomainEvent): void;

  // Reconstitute from events
  static loadFromHistory<T extends EventSourcedAggregate>(
    this: new () => T,
    events: DomainEvent[]
  ): T {
    const aggregate = new this();
    for (const event of events) {
      aggregate.applyEvent(event);
      aggregate._version++;
    }
    return aggregate;
  }
}

export class Order extends EventSourcedAggregate {
  private _id: string;
  private _customerId: string;
  private _items: OrderItem[] = [];
  private _status: OrderStatus;

  get id(): string { return this._id; }
  get status(): OrderStatus { return this._status; }

  // Command methods apply events
  static create(id: string, customerId: string, items: CreateOrderItem[]): Order {
    const order = new Order();
    order.apply(new OrderCreatedEvent(id, customerId, items));
    return order;
  }

  confirm(): void {
    if (this._status !== OrderStatus.PENDING) {
      throw new InvalidOrderStateError('Only pending orders can be confirmed');
    }
    this.apply(new OrderConfirmedEvent(this._id));
  }

  addItem(productId: string, quantity: number, price: number): void {
    if (this._status !== OrderStatus.PENDING) {
      throw new InvalidOrderStateError('Cannot add items to non-pending order');
    }
    this.apply(new OrderItemAddedEvent(this._id, productId, quantity, price));
  }

  // Event handlers update state
  protected applyEvent(event: DomainEvent): void {
    switch (event.eventType) {
      case 'OrderCreated':
        this.applyOrderCreated(event as OrderCreatedEvent);
        break;
      case 'OrderConfirmed':
        this.applyOrderConfirmed(event as OrderConfirmedEvent);
        break;
      case 'OrderItemAdded':
        this.applyOrderItemAdded(event as OrderItemAddedEvent);
        break;
      // ... other events
    }
  }

  private applyOrderCreated(event: OrderCreatedEvent): void {
    this._id = event.orderId;
    this._customerId = event.customerId;
    this._items = event.items.map(i =>
      new OrderItem(i.productId, i.quantity, i.price)
    );
    this._status = OrderStatus.PENDING;
  }

  private applyOrderConfirmed(event: OrderConfirmedEvent): void {
    this._status = OrderStatus.CONFIRMED;
  }

  private applyOrderItemAdded(event: OrderItemAddedEvent): void {
    this._items.push(new OrderItem(
      event.productId,
      event.quantity,
      event.price
    ));
  }
}
```

### Event-Sourced Repository

```typescript
// infrastructure/persistence/order.repository.impl.ts
export class EventSourcedOrderRepository implements OrderRepository {
  constructor(
    private readonly eventStore: EventStore,
    private readonly eventPublisher: EventPublisher
  ) {}

  async save(order: Order): Promise<void> {
    const events = order.uncommittedEvents;
    if (events.length === 0) return;

    // Append to event store
    await this.eventStore.append(
      order.id,
      events,
      order.version - events.length  // Expected version before new events
    );

    // Publish events for projections
    for (const event of events) {
      await this.eventPublisher.publish(event);
    }

    order.clearUncommittedEvents();
  }

  async findById(id: string): Promise<Order | null> {
    const events = await this.eventStore.getEvents(id);
    if (events.length === 0) return null;

    // Reconstitute aggregate from events
    const domainEvents = events.map(e => this.deserializeEvent(e));
    return Order.loadFromHistory(domainEvents);
  }

  private deserializeEvent(stored: StoredEvent): DomainEvent {
    // Map stored event to domain event
    const EventClass = EVENT_MAP[stored.eventType];
    return new EventClass(stored.eventData);
  }
}
```

## Snapshots (Performance Optimization)

```typescript
// For aggregates with many events, periodically save snapshots
export class SnapshotStore {
  constructor(private readonly db: Database) {}

  async saveSnapshot(aggregateId: string, state: any, version: number): Promise<void> {
    await this.db.query(
      `INSERT INTO snapshots (aggregate_id, state, version, created_at)
       VALUES ($1, $2, $3, NOW())
       ON CONFLICT (aggregate_id) DO UPDATE SET
         state = $2, version = $3, created_at = NOW()`,
      [aggregateId, JSON.stringify(state), version]
    );
  }

  async getLatestSnapshot(aggregateId: string): Promise<Snapshot | null> {
    const result = await this.db.query(
      'SELECT * FROM snapshots WHERE aggregate_id = $1',
      [aggregateId]
    );
    return result.rows[0] || null;
  }
}

// Modified repository with snapshots
export class EventSourcedOrderRepository implements OrderRepository {
  async findById(id: string): Promise<Order | null> {
    // Try to get snapshot first
    const snapshot = await this.snapshotStore.getLatestSnapshot(id);

    // Get events after snapshot (or all events if no snapshot)
    const events = await this.eventStore.getEventsAfterVersion(
      id,
      snapshot?.version ?? 0
    );

    if (!snapshot && events.length === 0) return null;

    // Reconstitute from snapshot + events
    const order = snapshot
      ? Order.fromSnapshot(snapshot.state)
      : new Order();

    const domainEvents = events.map(e => this.deserializeEvent(e));
    for (const event of domainEvents) {
      order.applyEvent(event);
    }

    // Take snapshot if many events since last snapshot
    if (events.length > SNAPSHOT_THRESHOLD) {
      await this.snapshotStore.saveSnapshot(id, order.toSnapshot(), order.version);
    }

    return order;
  }
}
```

## When to Use

### CQRS Benefits
- Different read/write scaling
- Optimized read models
- Complex domain logic separation
- Eventual consistency acceptable

### Event Sourcing Benefits
- Complete audit trail
- Temporal queries (state at any point)
- Event replay for debugging
- Rebuild read models from events

### When NOT to Use
- Simple CRUD applications
- Strong consistency required everywhere
- Small, simple domains
- Team unfamiliar with patterns
