---
name: event-driven-architecture
description: Event-driven architecture patterns for loosely coupled systems
category: architecture/distributed-systems
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Event-Driven Architecture

## Overview

Event-driven architecture (EDA) is a software design pattern where the flow
of the program is determined by events. It promotes loose coupling, scalability,
and real-time responsiveness.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────┐
│                  EVENT-DRIVEN ARCHITECTURE                   │
│                                                             │
│  ┌─────────┐    Event    ┌─────────┐    Event   ┌─────────┐│
│  │Producer │ ──────────► │ Broker  │ ─────────► │Consumer ││
│  └─────────┘             └─────────┘            └─────────┘│
│                                                             │
│  Producers emit events → Brokers route → Consumers react    │
└─────────────────────────────────────────────────────────────┘
```

## Event Types

```typescript
// Event base class
abstract class Event {
  readonly eventId: string = crypto.randomUUID();
  readonly timestamp: Date = new Date();
  abstract readonly eventType: string;
  abstract readonly version: string;
}

// Domain Event - business fact that happened
class OrderPlacedEvent extends Event {
  readonly eventType = 'order.placed';
  readonly version = '1.0';

  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly items: OrderItem[],
    public readonly total: number
  ) {
    super();
  }
}

// Integration Event - for cross-service communication
class OrderPlacedIntegrationEvent extends Event {
  readonly eventType = 'integration.order.placed';
  readonly version = '1.0';

  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly totalAmount: number,
    public readonly currency: string
  ) {
    super();
  }
}

// Command Event - request to perform action
class ProcessPaymentCommand extends Event {
  readonly eventType = 'command.process.payment';
  readonly version = '1.0';

  constructor(
    public readonly orderId: string,
    public readonly amount: number,
    public readonly paymentMethod: string
  ) {
    super();
  }
}

// Notification Event - inform about state change
class PaymentProcessedNotification extends Event {
  readonly eventType = 'notification.payment.processed';
  readonly version = '1.0';

  constructor(
    public readonly paymentId: string,
    public readonly orderId: string,
    public readonly status: 'success' | 'failed'
  ) {
    super();
  }
}
```

## Event Bus Implementation

```typescript
interface EventHandler<T extends Event = Event> {
  handle(event: T): Promise<void>;
}

interface EventBus {
  publish(event: Event): Promise<void>;
  subscribe<T extends Event>(eventType: string, handler: EventHandler<T>): void;
  unsubscribe(eventType: string, handler: EventHandler): void;
}

// In-memory event bus (for single process)
class InMemoryEventBus implements EventBus {
  private handlers: Map<string, Set<EventHandler>> = new Map();

  async publish(event: Event): Promise<void> {
    const handlers = this.handlers.get(event.eventType) || new Set();

    const promises = Array.from(handlers).map(handler =>
      handler.handle(event).catch(error => {
        console.error(`Handler error for ${event.eventType}:`, error);
      })
    );

    await Promise.all(promises);
  }

  subscribe<T extends Event>(eventType: string, handler: EventHandler<T>): void {
    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler as EventHandler);
  }

  unsubscribe(eventType: string, handler: EventHandler): void {
    this.handlers.get(eventType)?.delete(handler);
  }
}

// Distributed event bus (with message broker)
class DistributedEventBus implements EventBus {
  constructor(
    private broker: MessageBroker,
    private serializer: EventSerializer
  ) {}

  async publish(event: Event): Promise<void> {
    const message = {
      key: event.eventId,
      value: this.serializer.serialize(event),
      headers: {
        'event-type': event.eventType,
        'event-version': event.version,
        'timestamp': event.timestamp.toISOString(),
      },
    };

    await this.broker.publish(event.eventType, message);
  }

  subscribe<T extends Event>(eventType: string, handler: EventHandler<T>): void {
    this.broker.subscribe(eventType, async (message) => {
      const event = this.serializer.deserialize<T>(message.value);
      await handler.handle(event);
    });
  }

  unsubscribe(eventType: string, handler: EventHandler): void {
    this.broker.unsubscribe(eventType);
  }
}
```

## Event Sourcing

```typescript
// Event store interface
interface EventStore {
  append(streamId: string, events: Event[], expectedVersion?: number): Promise<void>;
  getEvents(streamId: string, fromVersion?: number): Promise<StoredEvent[]>;
  getSnapshot(streamId: string): Promise<Snapshot | null>;
  saveSnapshot(snapshot: Snapshot): Promise<void>;
}

interface StoredEvent {
  eventId: string;
  streamId: string;
  version: number;
  eventType: string;
  data: any;
  metadata: EventMetadata;
  timestamp: Date;
}

interface Snapshot {
  streamId: string;
  version: number;
  state: any;
  timestamp: Date;
}

// PostgreSQL event store implementation
class PostgresEventStore implements EventStore {
  constructor(private db: Database) {}

  async append(streamId: string, events: Event[], expectedVersion?: number): Promise<void> {
    await this.db.transaction(async (trx) => {
      // Optimistic concurrency check
      if (expectedVersion !== undefined) {
        const currentVersion = await this.getCurrentVersion(streamId, trx);
        if (currentVersion !== expectedVersion) {
          throw new ConcurrencyError(
            `Expected version ${expectedVersion}, but current is ${currentVersion}`
          );
        }
      }

      let version = expectedVersion ?? await this.getCurrentVersion(streamId, trx);

      for (const event of events) {
        version++;
        await trx.query(
          `INSERT INTO events (event_id, stream_id, version, event_type, data, metadata, timestamp)
           VALUES ($1, $2, $3, $4, $5, $6, $7)`,
          [event.eventId, streamId, version, event.eventType,
           JSON.stringify(event), JSON.stringify({ version: event.version }), event.timestamp]
        );
      }
    });
  }

  async getEvents(streamId: string, fromVersion: number = 0): Promise<StoredEvent[]> {
    const rows = await this.db.query(
      `SELECT * FROM events WHERE stream_id = $1 AND version > $2 ORDER BY version ASC`,
      [streamId, fromVersion]
    );
    return rows.map(this.mapToStoredEvent);
  }

  async getSnapshot(streamId: string): Promise<Snapshot | null> {
    const row = await this.db.queryOne(
      `SELECT * FROM snapshots WHERE stream_id = $1 ORDER BY version DESC LIMIT 1`,
      [streamId]
    );
    return row ? this.mapToSnapshot(row) : null;
  }

  async saveSnapshot(snapshot: Snapshot): Promise<void> {
    await this.db.query(
      `INSERT INTO snapshots (stream_id, version, state, timestamp)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (stream_id, version) DO UPDATE SET state = $3, timestamp = $4`,
      [snapshot.streamId, snapshot.version, JSON.stringify(snapshot.state), snapshot.timestamp]
    );
  }

  private async getCurrentVersion(streamId: string, trx: Transaction): Promise<number> {
    const result = await trx.queryOne<{ version: number }>(
      `SELECT MAX(version) as version FROM events WHERE stream_id = $1`,
      [streamId]
    );
    return result?.version ?? 0;
  }
}

// Event-sourced aggregate
abstract class EventSourcedAggregate {
  private uncommittedEvents: Event[] = [];
  protected version: number = 0;

  abstract get id(): string;

  protected apply(event: Event): void {
    this.when(event);
    this.version++;
    this.uncommittedEvents.push(event);
  }

  protected abstract when(event: Event): void;

  loadFromHistory(events: StoredEvent[]): void {
    for (const storedEvent of events) {
      this.when(storedEvent.data);
      this.version = storedEvent.version;
    }
  }

  loadFromSnapshot(snapshot: Snapshot, events: StoredEvent[]): void {
    Object.assign(this, snapshot.state);
    this.version = snapshot.version;
    this.loadFromHistory(events);
  }

  getUncommittedEvents(): Event[] {
    return [...this.uncommittedEvents];
  }

  clearUncommittedEvents(): void {
    this.uncommittedEvents = [];
  }

  getSnapshot(): any {
    return { ...this };
  }
}

// Order aggregate with event sourcing
class Order extends EventSourcedAggregate {
  private _id: string = '';
  private customerId: string = '';
  private items: OrderItem[] = [];
  private status: OrderStatus = 'draft';
  private total: number = 0;

  get id(): string {
    return this._id;
  }

  static create(customerId: string, items: OrderItem[]): Order {
    const order = new Order();
    order.apply(new OrderCreatedEvent(
      crypto.randomUUID(),
      customerId,
      items,
      items.reduce((sum, item) => sum + item.price * item.quantity, 0)
    ));
    return order;
  }

  place(): void {
    if (this.status !== 'draft') {
      throw new InvalidOperationError('Only draft orders can be placed');
    }
    this.apply(new OrderPlacedEvent(this._id, this.customerId, this.items, this.total));
  }

  ship(trackingNumber: string): void {
    if (this.status !== 'placed') {
      throw new InvalidOperationError('Only placed orders can be shipped');
    }
    this.apply(new OrderShippedEvent(this._id, trackingNumber));
  }

  protected when(event: Event): void {
    switch (event.constructor.name) {
      case 'OrderCreatedEvent':
        const created = event as OrderCreatedEvent;
        this._id = created.orderId;
        this.customerId = created.customerId;
        this.items = created.items;
        this.total = created.total;
        this.status = 'draft';
        break;

      case 'OrderPlacedEvent':
        this.status = 'placed';
        break;

      case 'OrderShippedEvent':
        this.status = 'shipped';
        break;
    }
  }
}

// Repository using event store
class EventSourcedOrderRepository {
  constructor(
    private eventStore: EventStore,
    private snapshotFrequency: number = 100
  ) {}

  async save(order: Order): Promise<void> {
    const events = order.getUncommittedEvents();
    await this.eventStore.append(`order-${order.id}`, events, order.version - events.length);
    order.clearUncommittedEvents();

    // Create snapshot periodically
    if (order.version % this.snapshotFrequency === 0) {
      await this.eventStore.saveSnapshot({
        streamId: `order-${order.id}`,
        version: order.version,
        state: order.getSnapshot(),
        timestamp: new Date(),
      });
    }
  }

  async getById(orderId: string): Promise<Order | null> {
    const streamId = `order-${orderId}`;
    const snapshot = await this.eventStore.getSnapshot(streamId);
    const order = new Order();

    if (snapshot) {
      const events = await this.eventStore.getEvents(streamId, snapshot.version);
      order.loadFromSnapshot(snapshot, events);
    } else {
      const events = await this.eventStore.getEvents(streamId);
      if (events.length === 0) return null;
      order.loadFromHistory(events);
    }

    return order;
  }
}
```

## Event Handlers and Projections

```typescript
// Event handler decorator pattern
abstract class EventHandler<T extends Event = Event> {
  abstract readonly eventType: string;
  abstract handle(event: T): Promise<void>;
}

// Order read model projection
class OrderReadModelProjection extends EventHandler<OrderPlacedEvent> {
  readonly eventType = 'order.placed';

  constructor(private readDb: Database) {}

  async handle(event: OrderPlacedEvent): Promise<void> {
    await this.readDb.query(
      `INSERT INTO order_read_model (id, customer_id, status, total, item_count, created_at)
       VALUES ($1, $2, $3, $4, $5, $6)
       ON CONFLICT (id) DO UPDATE SET status = $3`,
      [event.orderId, event.customerId, 'placed', event.total, event.items.length, event.timestamp]
    );
  }
}

// Notification handler
class OrderNotificationHandler extends EventHandler<OrderPlacedEvent> {
  readonly eventType = 'order.placed';

  constructor(
    private notificationService: NotificationService,
    private customerService: CustomerService
  ) {}

  async handle(event: OrderPlacedEvent): Promise<void> {
    const customer = await this.customerService.getById(event.customerId);

    await this.notificationService.send({
      to: customer.email,
      template: 'order-confirmation',
      data: {
        orderId: event.orderId,
        total: event.total,
        items: event.items,
      },
    });
  }
}

// Analytics handler
class OrderAnalyticsHandler extends EventHandler<OrderPlacedEvent> {
  readonly eventType = 'order.placed';

  constructor(private analyticsService: AnalyticsService) {}

  async handle(event: OrderPlacedEvent): Promise<void> {
    await this.analyticsService.track('order_placed', {
      orderId: event.orderId,
      customerId: event.customerId,
      total: event.total,
      itemCount: event.items.length,
      timestamp: event.timestamp,
    });
  }
}

// Handler registry
class EventHandlerRegistry {
  private handlers: Map<string, EventHandler[]> = new Map();

  register(handler: EventHandler): void {
    const handlers = this.handlers.get(handler.eventType) || [];
    handlers.push(handler);
    this.handlers.set(handler.eventType, handlers);
  }

  async dispatch(event: Event): Promise<void> {
    const handlers = this.handlers.get(event.eventType) || [];

    await Promise.all(handlers.map(handler =>
      handler.handle(event).catch(error => {
        console.error(`Handler error for ${event.eventType}:`, error);
        // Consider dead letter queue for failed events
      })
    ));
  }
}
```

## Event Schema Evolution

```typescript
// Event versioning with upcasting
interface EventUpcaster<T extends Event> {
  fromVersion: string;
  toVersion: string;
  upcast(event: any): T;
}

class EventUpcasterChain {
  private upcasters: Map<string, EventUpcaster<any>[]> = new Map();

  register<T extends Event>(upcaster: EventUpcaster<T>): void {
    const key = `${upcaster.fromVersion}->${upcaster.toVersion}`;
    const chain = this.upcasters.get(upcaster.fromVersion) || [];
    chain.push(upcaster);
    this.upcasters.set(upcaster.fromVersion, chain);
  }

  upcast<T extends Event>(event: any, targetVersion: string): T {
    let current = event;
    let currentVersion = event.version;

    while (currentVersion !== targetVersion) {
      const upcasters = this.upcasters.get(currentVersion);
      if (!upcasters || upcasters.length === 0) {
        throw new Error(`No upcaster found for version ${currentVersion}`);
      }

      const upcaster = upcasters[0];
      current = upcaster.upcast(current);
      currentVersion = upcaster.toVersion;
    }

    return current as T;
  }
}

// Example: Order event evolution
// V1: OrderPlacedEvent with items as array of strings
// V2: OrderPlacedEvent with items as array of OrderItem objects

class OrderPlacedEventV1ToV2Upcaster implements EventUpcaster<OrderPlacedEvent> {
  fromVersion = '1.0';
  toVersion = '2.0';

  upcast(event: any): OrderPlacedEvent {
    return new OrderPlacedEvent(
      event.orderId,
      event.customerId,
      event.items.map((itemId: string) => ({
        productId: itemId,
        quantity: 1,
        price: 0, // Unknown, would need lookup
      })),
      event.total
    );
  }
}

// Schema registry for event validation
class EventSchemaRegistry {
  private schemas: Map<string, JsonSchema> = new Map();

  register(eventType: string, version: string, schema: JsonSchema): void {
    this.schemas.set(`${eventType}:${version}`, schema);
  }

  validate(event: Event): ValidationResult {
    const schema = this.schemas.get(`${event.eventType}:${event.version}`);
    if (!schema) {
      return { valid: false, errors: ['Schema not found'] };
    }
    return this.validateAgainstSchema(event, schema);
  }
}
```

## Dead Letter Queue

```typescript
// Dead letter handling for failed events
interface DeadLetterEntry {
  id: string;
  event: Event;
  error: string;
  attempts: number;
  firstFailure: Date;
  lastFailure: Date;
  handler: string;
}

class DeadLetterQueue {
  constructor(private storage: DeadLetterStorage) {}

  async add(event: Event, error: Error, handler: string): Promise<void> {
    const existing = await this.storage.findByEventId(event.eventId);

    if (existing) {
      existing.attempts++;
      existing.lastFailure = new Date();
      existing.error = error.message;
      await this.storage.update(existing);
    } else {
      await this.storage.create({
        id: crypto.randomUUID(),
        event,
        error: error.message,
        attempts: 1,
        firstFailure: new Date(),
        lastFailure: new Date(),
        handler,
      });
    }
  }

  async retry(entryId: string): Promise<void> {
    const entry = await this.storage.findById(entryId);
    if (!entry) throw new Error('Entry not found');

    try {
      await this.eventBus.publish(entry.event);
      await this.storage.delete(entryId);
    } catch (error) {
      entry.attempts++;
      entry.lastFailure = new Date();
      entry.error = error.message;
      await this.storage.update(entry);
      throw error;
    }
  }

  async getEntries(options: { limit?: number; offset?: number }): Promise<DeadLetterEntry[]> {
    return this.storage.findAll(options);
  }
}

// Resilient event handler with DLQ
class ResilientEventHandler<T extends Event> {
  constructor(
    private handler: EventHandler<T>,
    private dlq: DeadLetterQueue,
    private maxRetries: number = 3
  ) {}

  async handle(event: T): Promise<void> {
    try {
      await this.handler.handle(event);
    } catch (error) {
      if (this.shouldRetry(error)) {
        throw error; // Let broker retry
      } else {
        await this.dlq.add(event, error, this.handler.constructor.name);
      }
    }
  }

  private shouldRetry(error: Error): boolean {
    // Transient errors should be retried
    return error.name === 'NetworkError' || error.name === 'TimeoutError';
  }
}
```

## Event Choreography vs Orchestration

```typescript
// Choreography: Services react to events independently
// No central coordinator

// Orchestration: Central coordinator manages workflow
class OrderWorkflowOrchestrator {
  constructor(
    private eventBus: EventBus,
    private workflowStore: WorkflowStore
  ) {
    this.setupEventHandlers();
  }

  private setupEventHandlers(): void {
    this.eventBus.subscribe('order.created', this.handleOrderCreated.bind(this));
    this.eventBus.subscribe('payment.completed', this.handlePaymentCompleted.bind(this));
    this.eventBus.subscribe('payment.failed', this.handlePaymentFailed.bind(this));
    this.eventBus.subscribe('inventory.reserved', this.handleInventoryReserved.bind(this));
    this.eventBus.subscribe('inventory.failed', this.handleInventoryFailed.bind(this));
  }

  async handleOrderCreated(event: OrderCreatedEvent): Promise<void> {
    // Create workflow instance
    const workflow = await this.workflowStore.create({
      orderId: event.orderId,
      status: 'pending_payment',
      steps: [
        { name: 'payment', status: 'pending' },
        { name: 'inventory', status: 'pending' },
        { name: 'shipping', status: 'pending' },
      ],
    });

    // Command payment service
    await this.eventBus.publish(new ProcessPaymentCommand(
      event.orderId,
      event.total,
      'credit_card'
    ));
  }

  async handlePaymentCompleted(event: PaymentCompletedEvent): Promise<void> {
    const workflow = await this.workflowStore.findByOrderId(event.orderId);

    workflow.updateStep('payment', 'completed');
    workflow.status = 'pending_inventory';
    await this.workflowStore.update(workflow);

    // Command inventory service
    await this.eventBus.publish(new ReserveInventoryCommand(
      event.orderId,
      workflow.items
    ));
  }

  async handlePaymentFailed(event: PaymentFailedEvent): Promise<void> {
    const workflow = await this.workflowStore.findByOrderId(event.orderId);

    workflow.updateStep('payment', 'failed');
    workflow.status = 'failed';
    await this.workflowStore.update(workflow);

    // Compensating action
    await this.eventBus.publish(new CancelOrderCommand(event.orderId, 'Payment failed'));
  }

  async handleInventoryReserved(event: InventoryReservedEvent): Promise<void> {
    const workflow = await this.workflowStore.findByOrderId(event.orderId);

    workflow.updateStep('inventory', 'completed');
    workflow.status = 'ready_for_shipping';
    await this.workflowStore.update(workflow);

    // Command shipping service
    await this.eventBus.publish(new CreateShipmentCommand(
      event.orderId,
      workflow.shippingAddress
    ));
  }

  async handleInventoryFailed(event: InventoryFailedEvent): Promise<void> {
    const workflow = await this.workflowStore.findByOrderId(event.orderId);

    workflow.updateStep('inventory', 'failed');
    workflow.status = 'compensating';
    await this.workflowStore.update(workflow);

    // Compensating actions
    await this.eventBus.publish(new RefundPaymentCommand(event.orderId));
    await this.eventBus.publish(new CancelOrderCommand(event.orderId, 'Inventory unavailable'));
  }
}
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Loose Coupling | Services communicate through events, not direct calls |
| Scalability | Easy to add new consumers without changing producers |
| Resilience | Async processing handles temporary failures |
| Audit Trail | Events provide complete history of state changes |
| Real-time | Immediate reaction to business events |

## When to Use

- Microservices needing loose coupling
- Real-time analytics and notifications
- Audit logging requirements
- Complex business workflows
- Event sourcing for complete state history
