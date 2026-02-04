# Architecture Patterns Reference

## Clean Architecture

### Layer Structure

```
src/
├── domain/                    # Innermost - Business Logic
│   ├── entities/              # Core business objects
│   ├── value-objects/         # Immutable value types
│   ├── repositories/          # Interfaces only!
│   ├── services/              # Domain services
│   └── errors/                # Domain errors
│
├── application/               # Use Cases
│   ├── use-cases/             # Application services
│   ├── dtos/                  # Data transfer objects
│   ├── mappers/               # Entity <-> DTO mapping
│   └── interfaces/            # Ports for external services
│
├── infrastructure/            # External Implementations
│   ├── persistence/           # Database implementations
│   ├── external-services/     # Third-party integrations
│   ├── cache/                 # Caching layer
│   └── config/                # Configuration
│
└── presentation/              # Outermost - Delivery
    ├── http/                  # REST controllers
    ├── graphql/               # GraphQL resolvers
    └── cli/                   # CLI commands
```

### Dependency Rule

```
OUTER layers can depend on INNER layers
INNER layers NEVER depend on OUTER layers

✅ Controller → Use Case → Entity
✅ Repository Impl → Repository Interface
❌ Entity → Repository Implementation
❌ Use Case → Controller
```

### Implementation Example

```typescript
// Domain Entity
export class Order {
  private constructor(
    public readonly id: string,
    private _items: OrderItem[],
    private _status: OrderStatus
  ) {}

  static create(items: OrderItem[]): Order {
    if (items.length === 0) throw new DomainError('Order must have items');
    return new Order(crypto.randomUUID(), items, OrderStatus.PENDING);
  }

  get total(): Money {
    return this._items.reduce((sum, item) => sum.add(item.subtotal), Money.zero());
  }

  confirm(): void {
    if (this._status !== OrderStatus.PENDING) {
      throw new DomainError('Only pending orders can be confirmed');
    }
    this._status = OrderStatus.CONFIRMED;
  }
}

// Domain Repository Interface
export interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: string): Promise<Order | null>;
}

// Application Use Case
export class CreateOrderUseCase {
  constructor(private orderRepository: OrderRepository) {}

  async execute(dto: CreateOrderDTO): Promise<OrderResponseDTO> {
    const items = dto.items.map(i => OrderItem.create(i.productId, i.quantity, i.price));
    const order = Order.create(items);
    await this.orderRepository.save(order);
    return OrderMapper.toDTO(order);
  }
}

// Infrastructure Repository Implementation
export class PrismaOrderRepository implements OrderRepository {
  constructor(private prisma: PrismaClient) {}

  async save(order: Order): Promise<void> {
    await this.prisma.order.create({ data: OrderMapper.toPersistence(order) });
  }

  async findById(id: string): Promise<Order | null> {
    const data = await this.prisma.order.findUnique({ where: { id } });
    return data ? OrderMapper.toDomain(data) : null;
  }
}

// Presentation Controller
@Controller('orders')
export class OrderController {
  constructor(private createOrder: CreateOrderUseCase) {}

  @Post()
  async create(@Body() dto: CreateOrderDTO) {
    return this.createOrder.execute(dto);
  }
}
```

## Domain-Driven Design

### Building Blocks

```typescript
// Value Object - Immutable, identity by value
export class Money {
  private constructor(
    private readonly _amount: number,
    private readonly _currency: string
  ) {}

  static create(amount: number, currency: string): Money {
    if (amount < 0) throw new Error('Amount cannot be negative');
    return new Money(amount, currency);
  }

  add(other: Money): Money {
    this.ensureSameCurrency(other);
    return new Money(this._amount + other._amount, this._currency);
  }

  equals(other: Money): boolean {
    return this._amount === other._amount && this._currency === other._currency;
  }
}

// Entity - Identity + lifecycle
export class Order extends Entity<OrderId> {
  private _items: OrderItem[] = [];
  private _status: OrderStatus;

  // Aggregate root controls access to items
  get items(): readonly OrderItem[] { return [...this._items]; }

  addItem(productId: ProductId, quantity: number, price: Money): void {
    if (this._status !== OrderStatus.DRAFT) {
      throw new DomainError('Cannot modify non-draft order');
    }
    this._items.push(OrderItem.create(productId, quantity, price));
  }
}

// Domain Event
export class OrderCreatedEvent implements DomainEvent {
  readonly occurredOn = new Date();
  readonly eventType = 'ORDER_CREATED';

  constructor(
    public readonly orderId: OrderId,
    public readonly customerId: CustomerId,
    public readonly total: Money
  ) {}
}

// Domain Service - Cross-entity logic
export class PricingService {
  constructor(private discountPolicies: DiscountPolicy[]) {}

  calculateFinalPrice(order: Order, customer: Customer): Money {
    let price = order.total;
    for (const policy of this.discountPolicies) {
      if (policy.isApplicable(order, customer)) {
        price = policy.apply(price);
      }
    }
    return price;
  }
}
```

### Bounded Contexts

```
┌─────────────────────────────────────────────────────────────┐
│                      E-Commerce System                       │
├─────────────────┬─────────────────┬─────────────────────────┤
│   Ordering BC   │   Shipping BC   │    Inventory BC         │
│                 │                 │                         │
│  • Order        │  • Shipment     │  • Product              │
│  • OrderItem    │  • Carrier      │  • Stock                │
│  • Customer     │  • Address      │  • Warehouse            │
│    (snapshot)   │  • Package      │  • Location             │
└────────┬────────┴────────┬────────┴────────────┬────────────┘
         └────── Events ───┴────── Events ────────┘
```

### Anti-Corruption Layer

```typescript
// Translate between bounded contexts
export class InventoryACL {
  constructor(private inventoryClient: InventoryClient) {}

  async getProductForOrdering(productId: string): Promise<OrderingProduct> {
    const inventoryProduct = await this.inventoryClient.getProduct(productId);

    // Translate to Ordering context's concept
    return new OrderingProduct(
      inventoryProduct.id,
      inventoryProduct.name,
      Money.create(inventoryProduct.price, inventoryProduct.currency),
      inventoryProduct.availableQuantity > 0
    );
  }
}
```

## CQRS + Event Sourcing

### CQRS Pattern

```typescript
// Command side - writes
interface CommandHandler<T> {
  execute(command: T): Promise<void>;
}

class CreateOrderHandler implements CommandHandler<CreateOrderCommand> {
  constructor(private orderRepository: OrderRepository) {}

  async execute(command: CreateOrderCommand): Promise<void> {
    const order = Order.create(command.customerId, command.items);
    await this.orderRepository.save(order);
  }
}

// Query side - reads
interface QueryHandler<T, R> {
  execute(query: T): Promise<R>;
}

class GetOrderDetailsHandler implements QueryHandler<GetOrderDetailsQuery, OrderDetails> {
  constructor(private readDb: ReadDatabase) {}

  async execute(query: GetOrderDetailsQuery): Promise<OrderDetails> {
    return this.readDb.query('SELECT * FROM order_details_view WHERE id = $1', [query.orderId]);
  }
}
```

### Event Sourcing

```typescript
// Store events as source of truth
interface DomainEvent {
  eventType: string;
  occurredOn: Date;
  aggregateId: string;
}

class Order extends EventSourcedAggregate {
  private status: OrderStatus;
  private items: OrderItem[] = [];

  static create(customerId: string, items: OrderItem[]): Order {
    const order = new Order();
    order.apply(new OrderCreatedEvent(crypto.randomUUID(), customerId, items));
    return order;
  }

  confirm(): void {
    if (this.status !== OrderStatus.PENDING) {
      throw new Error('Cannot confirm non-pending order');
    }
    this.apply(new OrderConfirmedEvent(this.id));
  }

  // Apply events to rebuild state
  protected when(event: DomainEvent): void {
    if (event instanceof OrderCreatedEvent) {
      this.id = event.orderId;
      this.items = event.items;
      this.status = OrderStatus.PENDING;
    } else if (event instanceof OrderConfirmedEvent) {
      this.status = OrderStatus.CONFIRMED;
    }
  }
}

// Event store
interface EventStore {
  save(events: DomainEvent[]): Promise<void>;
  getEvents(aggregateId: string): Promise<DomainEvent[]>;
}

// Rebuild aggregate from events
async function loadOrder(id: string, eventStore: EventStore): Promise<Order> {
  const events = await eventStore.getEvents(id);
  const order = new Order();
  for (const event of events) {
    order.applyFromHistory(event);
  }
  return order;
}
```

## Microservices

### Service Structure

```
services/
├── order-service/
│   ├── src/
│   │   ├── domain/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── api/
│   ├── Dockerfile
│   └── package.json
├── inventory-service/
├── payment-service/
└── notification-service/
```

### Inter-Service Communication

```typescript
// Synchronous - REST/gRPC client
class ProductServiceClient {
  constructor(
    private http: HttpClient,
    private circuitBreaker: CircuitBreaker
  ) {}

  async getProduct(id: string): Promise<Product> {
    return this.circuitBreaker.execute(() =>
      this.http.get(`${PRODUCT_SERVICE_URL}/products/${id}`)
    );
  }
}

// Asynchronous - Events
class OrderEventPublisher {
  constructor(private messageBroker: MessageBroker) {}

  async publishOrderCreated(order: Order): Promise<void> {
    await this.messageBroker.publish('order.created', {
      orderId: order.id,
      customerId: order.customerId,
      items: order.items,
      total: order.total,
    });
  }
}

// Event consumer
class OrderEventsConsumer {
  constructor(private notificationService: NotificationService) {}

  @Subscribe('order.created')
  async onOrderCreated(event: OrderCreatedEvent): Promise<void> {
    await this.notificationService.sendOrderConfirmation(event);
  }
}
```

### Saga Pattern (Distributed Transactions)

```typescript
class CreateOrderSaga {
  private steps: SagaStep[] = [
    {
      name: 'reserve_inventory',
      execute: async (ctx) => {
        ctx.reservationId = await this.inventory.reserve(ctx.items);
      },
      compensate: async (ctx) => {
        await this.inventory.cancelReservation(ctx.reservationId);
      },
    },
    {
      name: 'process_payment',
      execute: async (ctx) => {
        ctx.paymentId = await this.payment.charge(ctx.customerId, ctx.total);
      },
      compensate: async (ctx) => {
        await this.payment.refund(ctx.paymentId);
      },
    },
    {
      name: 'confirm_order',
      execute: async (ctx) => {
        await this.orderRepo.confirm(ctx.orderId);
      },
      compensate: async (ctx) => {
        await this.orderRepo.cancel(ctx.orderId);
      },
    },
  ];

  async execute(command: CreateOrderCommand): Promise<SagaResult> {
    const context = { ...command };
    const completedSteps: SagaStep[] = [];

    try {
      for (const step of this.steps) {
        await step.execute(context);
        completedSteps.push(step);
      }
      return { success: true };
    } catch (error) {
      // Compensate in reverse order
      for (const step of completedSteps.reverse()) {
        await step.compensate(context).catch(console.error);
      }
      return { success: false, error: error.message };
    }
  }
}
```

### API Gateway

```typescript
const routes: RouteConfig[] = [
  {
    path: '/api/users/**',
    service: 'user-service',
    middleware: ['auth', 'rateLimit'],
  },
  {
    path: '/api/orders/**',
    service: 'order-service',
    middleware: ['auth', 'rateLimit'],
  },
  {
    path: '/api/products/**',
    service: 'product-service',
    middleware: ['rateLimit'], // Public access
  },
];
```

## Pattern Selection Guide

| Scenario | Recommended Pattern |
|----------|-------------------|
| Simple CRUD app | Layered Architecture |
| Complex business rules | Clean/Hexagonal + DDD |
| Large team (10+ devs) | Microservices |
| High read/write asymmetry | CQRS |
| Audit requirements | Event Sourcing |
| Async workflows | Event-Driven Architecture |
| Medium complexity, single team | Modular Monolith |
