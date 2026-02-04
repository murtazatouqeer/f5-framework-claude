---
name: event-driven
description: Event-driven architecture patterns and implementation
category: messaging/events
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Event-Driven Architecture

## Overview

Event-Driven Architecture (EDA) is a software design pattern where the flow of the program is determined by events. Components communicate by producing and reacting to events, enabling loose coupling and scalability.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Event** | Immutable fact that something happened |
| **Producer** | Creates and publishes events |
| **Consumer** | Subscribes to and processes events |
| **Event Bus** | Routes events between producers and consumers |
| **Event Store** | Persists events for replay and audit |

## Event Types

| Type | Timing | Purpose | Example |
|------|--------|---------|---------|
| **Domain Event** | Past tense | Business fact | OrderPlaced |
| **Integration Event** | Past tense | Cross-service | PaymentCompleted |
| **Command** | Imperative | Request action | ProcessPayment |
| **Query** | Present | Request data | GetOrderStatus |

## Basic Implementation

### Event Definition

```typescript
// Base event interface
interface DomainEvent {
  readonly eventId: string;
  readonly eventType: string;
  readonly aggregateId: string;
  readonly aggregateType: string;
  readonly occurredOn: Date;
  readonly version: number;
  readonly metadata: EventMetadata;
}

interface EventMetadata {
  correlationId: string;
  causationId?: string;
  userId?: string;
  timestamp: Date;
}

// Concrete event
class OrderPlacedEvent implements DomainEvent {
  readonly eventType = 'order.placed';
  readonly aggregateType = 'Order';
  readonly version = 1;

  constructor(
    readonly eventId: string,
    readonly aggregateId: string,
    readonly customerId: string,
    readonly items: OrderItem[],
    readonly total: number,
    readonly metadata: EventMetadata,
    readonly occurredOn: Date = new Date()
  ) {}
}

// Event factory
function createEvent<T extends DomainEvent>(
  EventClass: new (...args: any[]) => T,
  data: Omit<T, 'eventId' | 'occurredOn' | 'metadata'>,
  metadata: Partial<EventMetadata> = {}
): T {
  return new EventClass({
    ...data,
    eventId: crypto.randomUUID(),
    occurredOn: new Date(),
    metadata: {
      correlationId: metadata.correlationId || crypto.randomUUID(),
      causationId: metadata.causationId,
      userId: metadata.userId,
      timestamp: new Date(),
    },
  });
}
```

### Event Bus

```typescript
type EventHandler<T extends DomainEvent> = (event: T) => Promise<void>;

class EventBus {
  private handlers: Map<string, EventHandler<any>[]> = new Map();
  private middlewares: EventMiddleware[] = [];

  // Subscribe to event type
  subscribe<T extends DomainEvent>(
    eventType: string,
    handler: EventHandler<T>
  ): () => void {
    const handlers = this.handlers.get(eventType) || [];
    handlers.push(handler);
    this.handlers.set(eventType, handlers);

    // Return unsubscribe function
    return () => {
      const index = handlers.indexOf(handler);
      if (index > -1) handlers.splice(index, 1);
    };
  }

  // Add middleware
  use(middleware: EventMiddleware): void {
    this.middlewares.push(middleware);
  }

  // Publish event
  async publish(event: DomainEvent): Promise<void> {
    // Run through middlewares
    let processedEvent = event;
    for (const middleware of this.middlewares) {
      processedEvent = await middleware(processedEvent);
    }

    const handlers = this.handlers.get(event.eventType) || [];

    // Execute all handlers
    await Promise.all(
      handlers.map(handler =>
        this.executeHandler(handler, processedEvent)
      )
    );
  }

  // Publish multiple events
  async publishAll(events: DomainEvent[]): Promise<void> {
    for (const event of events) {
      await this.publish(event);
    }
  }

  private async executeHandler(
    handler: EventHandler<any>,
    event: DomainEvent
  ): Promise<void> {
    try {
      await handler(event);
    } catch (error) {
      console.error(`Handler failed for ${event.eventType}:`, error);
      // Could implement retry logic or dead letter queue here
      throw error;
    }
  }
}

type EventMiddleware = (event: DomainEvent) => Promise<DomainEvent>;

// Logging middleware
const loggingMiddleware: EventMiddleware = async (event) => {
  console.log(`Event: ${event.eventType}`, {
    eventId: event.eventId,
    aggregateId: event.aggregateId,
  });
  return event;
};
```

### Event Handlers

```typescript
// Single responsibility handlers
class OrderPlacedHandler {
  constructor(
    private readonly inventoryService: InventoryService,
    private readonly emailService: EmailService,
    private readonly analyticsService: AnalyticsService
  ) {}

  async handle(event: OrderPlacedEvent): Promise<void> {
    // Each handler does one thing
    await this.reserveInventory(event);
  }

  private async reserveInventory(event: OrderPlacedEvent): Promise<void> {
    for (const item of event.items) {
      await this.inventoryService.reserve(item.productId, item.quantity);
    }
  }
}

// Handler registration
const eventBus = new EventBus();

const orderPlacedHandler = new OrderPlacedHandler(
  inventoryService,
  emailService,
  analyticsService
);

eventBus.subscribe('order.placed', (event) =>
  orderPlacedHandler.handle(event)
);
```

## Event Store

```typescript
interface StoredEvent {
  eventId: string;
  eventType: string;
  aggregateId: string;
  aggregateType: string;
  version: number;
  payload: string;
  metadata: string;
  occurredOn: Date;
  createdAt: Date;
}

class EventStore {
  constructor(private readonly db: Database) {}

  async append(event: DomainEvent): Promise<void> {
    await this.db.query(`
      INSERT INTO events (
        event_id, event_type, aggregate_id, aggregate_type,
        version, payload, metadata, occurred_on
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    `, [
      event.eventId,
      event.eventType,
      event.aggregateId,
      event.aggregateType,
      event.version,
      JSON.stringify(event),
      JSON.stringify(event.metadata),
      event.occurredOn,
    ]);
  }

  async getByAggregateId(aggregateId: string): Promise<DomainEvent[]> {
    const rows = await this.db.query(`
      SELECT * FROM events
      WHERE aggregate_id = $1
      ORDER BY occurred_on ASC
    `, [aggregateId]);

    return rows.map(row => JSON.parse(row.payload));
  }

  async getByEventType(
    eventType: string,
    since?: Date
  ): Promise<DomainEvent[]> {
    const query = since
      ? `SELECT * FROM events WHERE event_type = $1 AND occurred_on > $2 ORDER BY occurred_on`
      : `SELECT * FROM events WHERE event_type = $1 ORDER BY occurred_on`;

    const params = since ? [eventType, since] : [eventType];
    const rows = await this.db.query(query, params);

    return rows.map(row => JSON.parse(row.payload));
  }

  async getAllSince(position: number, limit: number = 100): Promise<{
    events: DomainEvent[];
    nextPosition: number;
  }> {
    const rows = await this.db.query(`
      SELECT * FROM events
      WHERE id > $1
      ORDER BY id
      LIMIT $2
    `, [position, limit]);

    const events = rows.map(row => JSON.parse(row.payload));
    const nextPosition = rows.length > 0 ? rows[rows.length - 1].id : position;

    return { events, nextPosition };
  }
}
```

## Aggregate with Events

```typescript
abstract class AggregateRoot {
  private _uncommittedEvents: DomainEvent[] = [];
  protected version: number = 0;

  get uncommittedEvents(): DomainEvent[] {
    return [...this._uncommittedEvents];
  }

  clearUncommittedEvents(): void {
    this._uncommittedEvents = [];
  }

  protected addEvent(event: DomainEvent): void {
    this._uncommittedEvents.push(event);
    this.apply(event);
  }

  protected abstract apply(event: DomainEvent): void;

  static rehydrate<T extends AggregateRoot>(
    aggregate: T,
    events: DomainEvent[]
  ): T {
    for (const event of events) {
      aggregate.apply(event);
      aggregate.version++;
    }
    return aggregate;
  }
}

class Order extends AggregateRoot {
  private _id!: string;
  private _status!: OrderStatus;
  private _items: OrderItem[] = [];
  private _total!: number;

  get id(): string { return this._id; }
  get status(): OrderStatus { return this._status; }

  static create(
    orderId: string,
    customerId: string,
    items: OrderItem[]
  ): Order {
    const order = new Order();
    const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

    order.addEvent(new OrderPlacedEvent(
      crypto.randomUUID(),
      orderId,
      customerId,
      items,
      total,
      { correlationId: crypto.randomUUID(), timestamp: new Date() }
    ));

    return order;
  }

  ship(trackingNumber: string): void {
    if (this._status !== 'confirmed') {
      throw new Error('Order must be confirmed before shipping');
    }

    this.addEvent(new OrderShippedEvent(
      crypto.randomUUID(),
      this._id,
      trackingNumber,
      { correlationId: crypto.randomUUID(), timestamp: new Date() }
    ));
  }

  protected apply(event: DomainEvent): void {
    switch (event.eventType) {
      case 'order.placed':
        this.applyOrderPlaced(event as OrderPlacedEvent);
        break;
      case 'order.shipped':
        this.applyOrderShipped(event as OrderShippedEvent);
        break;
    }
  }

  private applyOrderPlaced(event: OrderPlacedEvent): void {
    this._id = event.aggregateId;
    this._status = 'placed';
    this._items = event.items;
    this._total = event.total;
  }

  private applyOrderShipped(event: OrderShippedEvent): void {
    this._status = 'shipped';
  }
}
```

## Event Repository

```typescript
class EventSourcedRepository<T extends AggregateRoot> {
  constructor(
    private readonly eventStore: EventStore,
    private readonly eventBus: EventBus,
    private readonly factory: () => T
  ) {}

  async save(aggregate: T): Promise<void> {
    const events = aggregate.uncommittedEvents;

    // Persist events
    for (const event of events) {
      await this.eventStore.append(event);
    }

    // Publish events
    await this.eventBus.publishAll(events);

    // Clear uncommitted events
    aggregate.clearUncommittedEvents();
  }

  async getById(id: string): Promise<T | null> {
    const events = await this.eventStore.getByAggregateId(id);

    if (events.length === 0) {
      return null;
    }

    const aggregate = this.factory();
    return AggregateRoot.rehydrate(aggregate, events) as T;
  }
}

// Usage
const orderRepository = new EventSourcedRepository<Order>(
  eventStore,
  eventBus,
  () => new Order()
);

// Create and save order
const order = Order.create('order-123', 'customer-456', items);
await orderRepository.save(order);

// Load order
const loaded = await orderRepository.getById('order-123');
```

## Projections

```typescript
// Read model projection
class OrderProjection {
  constructor(private readonly db: Database) {}

  async handle(event: DomainEvent): Promise<void> {
    switch (event.eventType) {
      case 'order.placed':
        await this.handleOrderPlaced(event as OrderPlacedEvent);
        break;
      case 'order.shipped':
        await this.handleOrderShipped(event as OrderShippedEvent);
        break;
    }
  }

  private async handleOrderPlaced(event: OrderPlacedEvent): Promise<void> {
    await this.db.query(`
      INSERT INTO order_views (id, customer_id, status, total, created_at)
      VALUES ($1, $2, $3, $4, $5)
    `, [event.aggregateId, event.customerId, 'placed', event.total, event.occurredOn]);
  }

  private async handleOrderShipped(event: OrderShippedEvent): Promise<void> {
    await this.db.query(`
      UPDATE order_views SET status = $1, shipped_at = $2 WHERE id = $3
    `, ['shipped', event.occurredOn, event.aggregateId]);
  }
}

// Projection runner (catches up and stays current)
class ProjectionRunner {
  private position: number = 0;

  constructor(
    private readonly eventStore: EventStore,
    private readonly projection: OrderProjection
  ) {}

  async start(): Promise<void> {
    // Catch up with historical events
    await this.catchUp();

    // Subscribe to new events
    // (In production, use a message broker for real-time updates)
    setInterval(() => this.catchUp(), 1000);
  }

  private async catchUp(): Promise<void> {
    while (true) {
      const { events, nextPosition } = await this.eventStore.getAllSince(
        this.position,
        100
      );

      if (events.length === 0) break;

      for (const event of events) {
        await this.projection.handle(event);
      }

      this.position = nextPosition;
    }
  }
}
```

## Benefits and Trade-offs

| Benefit | Trade-off |
|---------|-----------|
| Loose coupling | Increased complexity |
| Scalability | Eventual consistency |
| Audit trail | Debugging difficulty |
| Temporal queries | Learning curve |
| Flexibility | Infrastructure needs |

## When to Use

### Good Fit
- Complex business domains
- Multiple bounded contexts
- Audit requirements
- Temporal queries needed
- High scalability needs

### Poor Fit
- Simple CRUD operations
- Strong consistency required
- Small, simple systems
- Team inexperienced with EDA

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Immutable events** | Never modify published events |
| **Event versioning** | Include version in event schema |
| **Idempotent handlers** | Handle duplicate events gracefully |
| **Correlation IDs** | Track event chains |
| **Small events** | Include only necessary data |
| **Event naming** | Use past tense, domain language |
