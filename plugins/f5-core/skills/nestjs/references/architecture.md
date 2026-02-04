# NestJS Architecture Patterns

Detailed architecture patterns for enterprise NestJS applications.

## Table of Contents

1. [Modular Architecture](#modular-architecture)
2. [Clean Architecture](#clean-architecture)
3. [Domain-Driven Design](#domain-driven-design)
4. [CQRS Pattern](#cqrs-pattern)
5. [Microservices](#microservices)

---

## Modular Architecture

### Overview

NestJS's module system enables organizing code into cohesive, reusable blocks.

### Module Types

| Type | Purpose | Example |
|------|---------|---------|
| Feature Module | Business feature | UserModule, OrderModule |
| Shared Module | Reusable utilities | DatabaseModule, LoggerModule |
| Core Module | App-wide singletons | ConfigModule, AuthModule |
| Dynamic Module | Runtime configuration | TypeOrmModule.forRoot() |

### Feature Module Structure

```
src/modules/user/
├── user.module.ts           # Module definition
├── user.controller.ts       # HTTP layer
├── user.service.ts          # Business logic
├── user.repository.ts       # Data access (optional)
├── dto/
│   ├── create-user.dto.ts
│   ├── update-user.dto.ts
│   └── user-response.dto.ts
├── entities/
│   └── user.entity.ts
├── interfaces/
│   └── user.interface.ts
├── guards/
│   └── user-owner.guard.ts
└── __tests__/
    ├── user.controller.spec.ts
    └── user.service.spec.ts
```

### Module Best Practices

```typescript
// Good: Feature module with clear boundaries
@Module({
  imports: [
    TypeOrmModule.forFeature([User, UserProfile]),
    SharedModule,
  ],
  controllers: [UserController],
  providers: [
    UserService,
    UserRepository,
    UserMapper,
  ],
  exports: [UserService], // Only export what's needed
})
export class UserModule {}
```

```typescript
// Bad: God module with too many responsibilities
@Module({
  imports: [/* 20+ imports */],
  controllers: [/* 10+ controllers */],
  providers: [/* 30+ providers */],
  exports: [/* everything */],
})
export class AppModule {} // Everything in one module
```

---

## Clean Architecture

### Layer Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  Controllers, DTOs, Guards, Interceptors, Pipes             │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│  Use Cases, Application Services, Commands, Queries         │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                            │
│  Entities, Value Objects, Domain Services, Repositories     │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                       │
│  Database, External APIs, File System, Message Queues       │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/
├── presentation/           # Controllers, DTOs
│   └── http/
│       ├── controllers/
│       ├── dto/
│       └── guards/
├── application/            # Use cases
│   ├── commands/
│   ├── queries/
│   └── services/
├── domain/                 # Business logic
│   ├── entities/
│   ├── value-objects/
│   ├── repositories/      # Interfaces only
│   └── services/
└── infrastructure/         # Implementations
    ├── database/
    │   ├── repositories/  # Repository implementations
    │   └── migrations/
    ├── external/
    └── config/
```

### Implementation Example

```typescript
// domain/entities/user.entity.ts
export class User {
  private constructor(
    public readonly id: string,
    public readonly email: Email,
    public readonly name: string,
    private _status: UserStatus,
  ) {}

  static create(props: CreateUserProps): User {
    // Domain validation
    return new User(uuid(), new Email(props.email), props.name, UserStatus.PENDING);
  }

  activate(): void {
    if (this._status !== UserStatus.PENDING) {
      throw new DomainException('User already activated');
    }
    this._status = UserStatus.ACTIVE;
  }
}

// domain/repositories/user.repository.interface.ts
export interface IUserRepository {
  save(user: User): Promise<void>;
  findById(id: string): Promise<User | null>;
  findByEmail(email: Email): Promise<User | null>;
}

// application/commands/create-user.command.ts
export class CreateUserCommand {
  constructor(
    public readonly email: string,
    public readonly name: string,
  ) {}
}

// application/commands/handlers/create-user.handler.ts
@CommandHandler(CreateUserCommand)
export class CreateUserHandler implements ICommandHandler<CreateUserCommand> {
  constructor(
    @Inject('IUserRepository')
    private readonly userRepository: IUserRepository,
  ) {}

  async execute(command: CreateUserCommand): Promise<string> {
    const existingUser = await this.userRepository.findByEmail(
      new Email(command.email)
    );

    if (existingUser) {
      throw new ConflictException('User already exists');
    }

    const user = User.create({
      email: command.email,
      name: command.name,
    });

    await this.userRepository.save(user);
    return user.id;
  }
}

// infrastructure/database/repositories/user.repository.ts
@Injectable()
export class UserRepository implements IUserRepository {
  constructor(
    @InjectRepository(UserEntity)
    private readonly repo: Repository<UserEntity>,
  ) {}

  async save(user: User): Promise<void> {
    const entity = this.toEntity(user);
    await this.repo.save(entity);
  }

  async findById(id: string): Promise<User | null> {
    const entity = await this.repo.findOne({ where: { id } });
    return entity ? this.toDomain(entity) : null;
  }
}
```

---

## Domain-Driven Design

### Building Blocks

| Concept | Description | NestJS Implementation |
|---------|-------------|----------------------|
| Entity | Object with identity | Class with ID |
| Value Object | Immutable, no identity | Class without ID |
| Aggregate | Cluster of entities | Root entity + children |
| Repository | Collection abstraction | Interface + implementation |
| Domain Service | Stateless domain logic | Injectable service |
| Domain Event | Something that happened | Event class |

### Aggregate Example

```typescript
// domain/aggregates/order.aggregate.ts
export class Order extends AggregateRoot {
  private _items: OrderItem[] = [];
  private _status: OrderStatus;

  constructor(
    public readonly id: string,
    public readonly customerId: string,
  ) {
    super();
    this._status = OrderStatus.DRAFT;
  }

  addItem(productId: string, quantity: number, price: Money): void {
    if (this._status !== OrderStatus.DRAFT) {
      throw new DomainException('Cannot modify confirmed order');
    }

    const existingItem = this._items.find(i => i.productId === productId);
    if (existingItem) {
      existingItem.increaseQuantity(quantity);
    } else {
      this._items.push(new OrderItem(productId, quantity, price));
    }

    this.apply(new OrderItemAddedEvent(this.id, productId, quantity));
  }

  confirm(): void {
    if (this._items.length === 0) {
      throw new DomainException('Cannot confirm empty order');
    }
    this._status = OrderStatus.CONFIRMED;
    this.apply(new OrderConfirmedEvent(this.id, this.total));
  }

  get total(): Money {
    return this._items.reduce(
      (sum, item) => sum.add(item.subtotal),
      Money.zero()
    );
  }
}
```

### Value Object Example

```typescript
// domain/value-objects/money.vo.ts
export class Money {
  private constructor(
    public readonly amount: number,
    public readonly currency: string,
  ) {
    if (amount < 0) {
      throw new DomainException('Amount cannot be negative');
    }
  }

  static create(amount: number, currency: string = 'USD'): Money {
    return new Money(amount, currency);
  }

  static zero(currency: string = 'USD'): Money {
    return new Money(0, currency);
  }

  add(other: Money): Money {
    this.ensureSameCurrency(other);
    return new Money(this.amount + other.amount, this.currency);
  }

  multiply(factor: number): Money {
    return new Money(this.amount * factor, this.currency);
  }

  equals(other: Money): boolean {
    return this.amount === other.amount && this.currency === other.currency;
  }

  private ensureSameCurrency(other: Money): void {
    if (this.currency !== other.currency) {
      throw new DomainException('Currency mismatch');
    }
  }
}
```

---

## CQRS Pattern

### Overview

Command Query Responsibility Segregation separates read and write operations.

### Setup

```bash
npm install @nestjs/cqrs
```

### Structure

```
src/modules/order/
├── commands/
│   ├── create-order.command.ts
│   ├── handlers/
│   │   └── create-order.handler.ts
│   └── index.ts
├── queries/
│   ├── get-order.query.ts
│   ├── handlers/
│   │   └── get-order.handler.ts
│   └── index.ts
├── events/
│   ├── order-created.event.ts
│   └── handlers/
│       └── order-created.handler.ts
└── order.module.ts
```

### Implementation

```typescript
// commands/create-order.command.ts
export class CreateOrderCommand {
  constructor(
    public readonly customerId: string,
    public readonly items: OrderItemDto[],
  ) {}
}

// commands/handlers/create-order.handler.ts
@CommandHandler(CreateOrderCommand)
export class CreateOrderHandler implements ICommandHandler<CreateOrderCommand> {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly eventBus: EventBus,
  ) {}

  async execute(command: CreateOrderCommand): Promise<string> {
    const order = Order.create(command.customerId);

    for (const item of command.items) {
      order.addItem(item.productId, item.quantity, item.price);
    }

    await this.orderRepository.save(order);

    this.eventBus.publish(new OrderCreatedEvent(order.id, order.total));

    return order.id;
  }
}

// queries/get-order.query.ts
export class GetOrderQuery {
  constructor(public readonly orderId: string) {}
}

// queries/handlers/get-order.handler.ts
@QueryHandler(GetOrderQuery)
export class GetOrderHandler implements IQueryHandler<GetOrderQuery> {
  constructor(
    @InjectRepository(OrderReadModel)
    private readonly readRepo: Repository<OrderReadModel>,
  ) {}

  async execute(query: GetOrderQuery): Promise<OrderReadModel> {
    return this.readRepo.findOne({ where: { id: query.orderId } });
  }
}

// Controller usage
@Controller('orders')
export class OrderController {
  constructor(
    private readonly commandBus: CommandBus,
    private readonly queryBus: QueryBus,
  ) {}

  @Post()
  async create(@Body() dto: CreateOrderDto): Promise<{ id: string }> {
    const id = await this.commandBus.execute(
      new CreateOrderCommand(dto.customerId, dto.items)
    );
    return { id };
  }

  @Get(':id')
  async findOne(@Param('id') id: string): Promise<OrderReadModel> {
    return this.queryBus.execute(new GetOrderQuery(id));
  }
}
```

### Event Sourcing Integration

```typescript
// events/order-created.event.ts
export class OrderCreatedEvent {
  constructor(
    public readonly orderId: string,
    public readonly total: Money,
    public readonly occurredAt: Date = new Date(),
  ) {}
}

// events/handlers/order-created.handler.ts
@EventsHandler(OrderCreatedEvent)
export class OrderCreatedHandler implements IEventHandler<OrderCreatedEvent> {
  constructor(
    private readonly notificationService: NotificationService,
    private readonly analyticsService: AnalyticsService,
  ) {}

  async handle(event: OrderCreatedEvent): Promise<void> {
    // Side effects
    await Promise.all([
      this.notificationService.sendOrderConfirmation(event.orderId),
      this.analyticsService.trackOrderCreated(event),
    ]);
  }
}
```

---

## Microservices

### Transport Options

| Transport | Use Case | Package |
|-----------|----------|---------|
| TCP | Internal services | Built-in |
| Redis | Pub/sub, caching | @nestjs/microservices |
| RabbitMQ | Message queue | @nestjs/microservices |
| Kafka | Event streaming | @nestjs/microservices |
| gRPC | High performance | @nestjs/microservices |

### Hybrid Application

```typescript
// main.ts
async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // HTTP
  app.useGlobalPipes(new ValidationPipe());

  // Microservice - TCP
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.TCP,
    options: { port: 3001 },
  });

  // Microservice - RabbitMQ
  app.connectMicroservice<MicroserviceOptions>({
    transport: Transport.RMQ,
    options: {
      urls: ['amqp://localhost:5672'],
      queue: 'orders_queue',
    },
  });

  await app.startAllMicroservices();
  await app.listen(3000);
}
```

### Message Patterns

```typescript
// Event-based (fire and forget)
@EventPattern('user_created')
async handleUserCreated(@Payload() data: UserCreatedEvent) {
  await this.notificationService.sendWelcome(data.email);
}

// Request-response
@MessagePattern({ cmd: 'get_user' })
async getUser(@Payload() data: { id: string }): Promise<User> {
  return this.userService.findOne(data.id);
}

// Client usage
@Injectable()
export class OrderService {
  constructor(
    @Inject('USER_SERVICE') private readonly userClient: ClientProxy,
  ) {}

  async createOrder(userId: string): Promise<Order> {
    // Request-response
    const user = await firstValueFrom(
      this.userClient.send({ cmd: 'get_user' }, { id: userId })
    );

    const order = await this.orderRepository.create({ userId });

    // Event emission
    this.userClient.emit('order_created', { userId, orderId: order.id });

    return order;
  }
}
```

### Service Discovery

```typescript
// Using Consul
@Module({
  imports: [
    ConsulModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        host: config.get('CONSUL_HOST'),
        port: config.get('CONSUL_PORT'),
      }),
      inject: [ConfigService],
    }),
  ],
})
export class AppModule {}

// Register service
@Injectable()
export class ServiceRegistration implements OnModuleInit {
  constructor(private consul: ConsulService) {}

  async onModuleInit() {
    await this.consul.register({
      name: 'order-service',
      address: 'localhost',
      port: 3000,
      check: {
        http: 'http://localhost:3000/health',
        interval: '10s',
      },
    });
  }
}
```

---

## Architecture Decision Guide

| Scenario | Recommended Pattern |
|----------|-------------------|
| Simple CRUD app | Modular Architecture |
| Complex business logic | Clean Architecture |
| Multiple bounded contexts | DDD + Modular |
| High read/write ratio difference | CQRS |
| Event-driven requirements | CQRS + Event Sourcing |
| Multiple teams/services | Microservices |
| Startup/MVP | Simple Modular → evolve |

## F5 Quality Gates Mapping

| Gate | Architecture Deliverable |
|------|-------------------------|
| D3 | Architecture diagram, layer definitions |
| D4 | Module structure, interfaces, patterns |
| G3 | Unit tests for domain logic |
| G4 | Integration tests for use cases |
