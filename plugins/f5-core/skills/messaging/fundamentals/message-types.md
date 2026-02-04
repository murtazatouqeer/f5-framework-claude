---
name: message-types
description: Commands, events, and queries in messaging systems
category: messaging/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Message Types

## Overview

Different message types serve different purposes. Understanding when to use each type is crucial for clean architecture.

## Three Main Types

| Type | Intent | Naming | Response |
|------|--------|--------|----------|
| **Command** | Request action | Imperative verb | Optional/Ack |
| **Event** | Notify of fact | Past tense | None |
| **Query** | Request data | Question form | Required |

## Commands

Commands request that something be done. They represent intent.

### Characteristics

- Imperative naming: `CreateOrder`, `SendEmail`, `CancelSubscription`
- Directed to specific handler
- Can be rejected
- Usually expect acknowledgment
- Modify state

### Implementation

```typescript
// Command definition
interface Command {
  readonly commandId: string;
  readonly timestamp: Date;
  readonly correlationId?: string;
}

interface CreateOrderCommand extends Command {
  readonly customerId: string;
  readonly items: OrderItem[];
  readonly shippingAddress: Address;
}

interface CancelOrderCommand extends Command {
  readonly orderId: string;
  readonly reason: string;
}

// Command handler
interface CommandHandler<T extends Command> {
  handle(command: T): Promise<void>;
}

class CreateOrderHandler implements CommandHandler<CreateOrderCommand> {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly eventPublisher: EventPublisher
  ) {}

  async handle(command: CreateOrderCommand): Promise<void> {
    // Validate
    if (!command.items.length) {
      throw new ValidationError('Order must have items');
    }

    // Create aggregate
    const order = Order.create({
      customerId: command.customerId,
      items: command.items,
      shippingAddress: command.shippingAddress,
    });

    // Persist
    await this.orderRepository.save(order);

    // Publish resulting events
    await this.eventPublisher.publish(order.pullEvents());
  }
}
```

### Command Bus

```typescript
// Command bus pattern
class CommandBus {
  private handlers: Map<string, CommandHandler<any>> = new Map();

  register<T extends Command>(
    commandType: string,
    handler: CommandHandler<T>
  ): void {
    this.handlers.set(commandType, handler);
  }

  async dispatch<T extends Command>(command: T): Promise<void> {
    const handler = this.handlers.get(command.constructor.name);

    if (!handler) {
      throw new Error(`No handler for ${command.constructor.name}`);
    }

    await handler.handle(command);
  }
}

// Usage
const commandBus = new CommandBus();
commandBus.register('CreateOrderCommand', new CreateOrderHandler(...));

await commandBus.dispatch(new CreateOrderCommand({
  customerId: 'cust-123',
  items: [{ productId: 'prod-1', quantity: 2 }],
  shippingAddress: address,
}));
```

## Events

Events notify that something happened. They are facts.

### Characteristics

- Past tense naming: `OrderCreated`, `PaymentReceived`, `UserRegistered`
- Broadcast to multiple subscribers
- Cannot be rejected (already happened)
- No response expected
- Immutable

### Implementation

```typescript
// Event definition
interface DomainEvent {
  readonly eventId: string;
  readonly eventType: string;
  readonly occurredOn: Date;
  readonly aggregateId: string;
  readonly version: number;
}

class OrderCreatedEvent implements DomainEvent {
  readonly eventType = 'order.created';
  readonly eventId: string;
  readonly occurredOn: Date;
  readonly version = 1;

  constructor(
    readonly aggregateId: string,
    readonly customerId: string,
    readonly items: OrderItem[],
    readonly total: number
  ) {
    this.eventId = crypto.randomUUID();
    this.occurredOn = new Date();
  }
}

class OrderShippedEvent implements DomainEvent {
  readonly eventType = 'order.shipped';
  readonly eventId: string;
  readonly occurredOn: Date;
  readonly version = 1;

  constructor(
    readonly aggregateId: string,
    readonly trackingNumber: string,
    readonly carrier: string,
    readonly estimatedDelivery: Date
  ) {
    this.eventId = crypto.randomUUID();
    this.occurredOn = new Date();
  }
}
```

### Event Handlers

```typescript
// Multiple handlers for same event
interface EventHandler<T extends DomainEvent> {
  handle(event: T): Promise<void>;
}

// Handler 1: Send confirmation email
class SendOrderConfirmationHandler implements EventHandler<OrderCreatedEvent> {
  async handle(event: OrderCreatedEvent): Promise<void> {
    await this.emailService.sendOrderConfirmation(
      event.customerId,
      event.aggregateId
    );
  }
}

// Handler 2: Update inventory
class ReserveInventoryHandler implements EventHandler<OrderCreatedEvent> {
  async handle(event: OrderCreatedEvent): Promise<void> {
    for (const item of event.items) {
      await this.inventoryService.reserve(item.productId, item.quantity);
    }
  }
}

// Handler 3: Track analytics
class TrackOrderAnalyticsHandler implements EventHandler<OrderCreatedEvent> {
  async handle(event: OrderCreatedEvent): Promise<void> {
    await this.analytics.track('order_created', {
      orderId: event.aggregateId,
      total: event.total,
      itemCount: event.items.length,
    });
  }
}
```

### Event Bus

```typescript
// Event bus with multiple subscribers
class EventBus {
  private handlers: Map<string, EventHandler<any>[]> = new Map();

  subscribe<T extends DomainEvent>(
    eventType: string,
    handler: EventHandler<T>
  ): void {
    const handlers = this.handlers.get(eventType) || [];
    handlers.push(handler);
    this.handlers.set(eventType, handlers);
  }

  async publish(event: DomainEvent): Promise<void> {
    const handlers = this.handlers.get(event.eventType) || [];

    // Execute all handlers (parallel or sequential)
    await Promise.all(handlers.map(h => h.handle(event)));
  }
}
```

## Queries

Queries request information without modifying state.

### Characteristics

- Question form naming: `GetOrder`, `FindUserByEmail`, `ListProducts`
- Directed to specific handler
- Always return data
- No side effects (read-only)

### Implementation

```typescript
// Query definition
interface Query<TResult> {
  readonly queryId: string;
}

interface GetOrderQuery extends Query<OrderDto> {
  readonly orderId: string;
}

interface ListOrdersQuery extends Query<OrderDto[]> {
  readonly customerId: string;
  readonly status?: OrderStatus;
  readonly page: number;
  readonly limit: number;
}

// Query handler
interface QueryHandler<TQuery extends Query<TResult>, TResult> {
  handle(query: TQuery): Promise<TResult>;
}

class GetOrderHandler implements QueryHandler<GetOrderQuery, OrderDto> {
  constructor(private readonly readDb: ReadDatabase) {}

  async handle(query: GetOrderQuery): Promise<OrderDto> {
    const order = await this.readDb.orders.findById(query.orderId);

    if (!order) {
      throw new NotFoundError(`Order ${query.orderId} not found`);
    }

    return order;
  }
}
```

### Query Bus

```typescript
// Query bus pattern
class QueryBus {
  private handlers: Map<string, QueryHandler<any, any>> = new Map();

  register<TQuery extends Query<TResult>, TResult>(
    queryType: string,
    handler: QueryHandler<TQuery, TResult>
  ): void {
    this.handlers.set(queryType, handler);
  }

  async execute<TResult>(query: Query<TResult>): Promise<TResult> {
    const handler = this.handlers.get(query.constructor.name);

    if (!handler) {
      throw new Error(`No handler for ${query.constructor.name}`);
    }

    return handler.handle(query);
  }
}

// Usage
const order = await queryBus.execute(new GetOrderQuery({
  orderId: 'ord-123',
}));
```

## Comparison Table

| Aspect | Command | Event | Query |
|--------|---------|-------|-------|
| Purpose | Request action | Notify fact | Request data |
| Naming | `CreateOrder` | `OrderCreated` | `GetOrder` |
| Direction | Sender → Handler | Publisher → Subscribers | Sender → Handler |
| Handlers | One | Many | One |
| Response | Ack/Error | None | Data |
| Modifies state | Yes | No (already happened) | No |
| Can reject | Yes | No | N/A |

## Message Design Principles

### 1. Self-Contained

```typescript
// ❌ Bad: Requires external lookup
interface OrderCreatedEvent {
  orderId: string;
  // Consumer must fetch order details
}

// ✅ Good: Contains necessary data
interface OrderCreatedEvent {
  orderId: string;
  customerId: string;
  items: { productId: string; quantity: number; price: number }[];
  total: number;
  createdAt: Date;
}
```

### 2. Versioned

```typescript
interface OrderCreatedEventV1 {
  version: 1;
  orderId: string;
  total: number;
}

interface OrderCreatedEventV2 {
  version: 2;
  orderId: string;
  subtotal: number;  // Renamed
  tax: number;       // Added
  total: number;
}

// Consumer handles both versions
function handleOrderCreated(event: OrderCreatedEventV1 | OrderCreatedEventV2) {
  if (event.version === 1) {
    // Handle v1
  } else {
    // Handle v2
  }
}
```

### 3. Immutable

```typescript
// Events are facts - never modify them
class OrderCreatedEvent {
  constructor(
    readonly orderId: string,
    readonly customerId: string,
    readonly total: number,
    readonly createdAt: Date = new Date()
  ) {
    Object.freeze(this);
  }
}
```
