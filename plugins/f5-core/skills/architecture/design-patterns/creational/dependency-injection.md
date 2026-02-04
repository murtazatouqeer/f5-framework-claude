---
name: dependency-injection
description: Dependency Injection pattern and IoC containers
category: architecture/design-patterns/creational
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Dependency Injection (DI)

## Overview

Dependency Injection is a technique where dependencies are provided to a
class rather than created by the class itself. It's a specific form of
Inversion of Control (IoC).

## Without DI vs With DI

```typescript
// ❌ Without DI - Tight Coupling
class OrderService {
  private repository = new MySQLOrderRepository();
  private emailService = new SendGridEmailService();
  private paymentGateway = new StripePaymentGateway();

  async createOrder(data: CreateOrderDTO): Promise<Order> {
    const order = await this.repository.save(data);
    await this.emailService.send(data.email, 'Order created');
    await this.paymentGateway.charge(data.total);
    return order;
  }
}

// Problems:
// - Can't switch implementations
// - Can't mock for testing
// - Class knows too much about its dependencies

// ✅ With DI - Loose Coupling
class OrderService {
  constructor(
    private readonly repository: OrderRepository,
    private readonly emailService: EmailService,
    private readonly paymentGateway: PaymentGateway
  ) {}

  async createOrder(data: CreateOrderDTO): Promise<Order> {
    const order = await this.repository.save(data);
    await this.emailService.send(data.email, 'Order created');
    await this.paymentGateway.charge(data.total);
    return order;
  }
}
```

## Types of Injection

### Constructor Injection (Preferred)

```typescript
// Dependencies provided through constructor
class UserService {
  constructor(
    private readonly userRepository: UserRepository,
    private readonly passwordHasher: PasswordHasher,
    private readonly logger: Logger
  ) {}

  async createUser(dto: CreateUserDTO): Promise<User> {
    this.logger.log('Creating user');
    const hashedPassword = await this.passwordHasher.hash(dto.password);
    return this.userRepository.save({ ...dto, password: hashedPassword });
  }
}

// Usage
const userService = new UserService(
  new PostgresUserRepository(db),
  new BcryptPasswordHasher(),
  new ConsoleLogger()
);
```

### Property/Setter Injection

```typescript
// Dependencies set through properties
class NotificationService {
  private logger: Logger;
  private emailClient: EmailClient;

  setLogger(logger: Logger): void {
    this.logger = logger;
  }

  setEmailClient(client: EmailClient): void {
    this.emailClient = client;
  }

  async notify(user: User, message: string): Promise<void> {
    this.logger?.log(`Notifying ${user.email}`);
    await this.emailClient.send(user.email, message);
  }
}

// Usage - dependencies can be changed at runtime
const service = new NotificationService();
service.setLogger(new ConsoleLogger());
service.setEmailClient(new SendGridClient());
```

### Method Injection

```typescript
// Dependencies passed to specific methods
class ReportGenerator {
  generate(
    data: ReportData,
    formatter: ReportFormatter,
    exporter: ReportExporter
  ): Buffer {
    const formatted = formatter.format(data);
    return exporter.export(formatted);
  }
}

// Usage - different formatters for different calls
const generator = new ReportGenerator();

// PDF report
const pdfReport = generator.generate(
  data,
  new HTMLFormatter(),
  new PDFExporter()
);

// Excel report
const excelReport = generator.generate(
  data,
  new TableFormatter(),
  new ExcelExporter()
);
```

## DI Containers

### InversifyJS

```typescript
import { Container, injectable, inject } from 'inversify';

// Define tokens
const TYPES = {
  UserRepository: Symbol.for('UserRepository'),
  PasswordHasher: Symbol.for('PasswordHasher'),
  Logger: Symbol.for('Logger'),
  UserService: Symbol.for('UserService'),
};

// Mark classes as injectable
@injectable()
class PostgresUserRepository implements UserRepository {
  constructor(@inject('Database') private db: Database) {}

  async save(user: User): Promise<User> { /* ... */ }
  async findById(id: string): Promise<User | null> { /* ... */ }
}

@injectable()
class BcryptPasswordHasher implements PasswordHasher {
  async hash(password: string): Promise<string> {
    return bcrypt.hash(password, 10);
  }
}

@injectable()
class UserService {
  constructor(
    @inject(TYPES.UserRepository) private repository: UserRepository,
    @inject(TYPES.PasswordHasher) private hasher: PasswordHasher,
    @inject(TYPES.Logger) private logger: Logger
  ) {}

  async createUser(dto: CreateUserDTO): Promise<User> {
    this.logger.log('Creating user');
    const hashedPassword = await this.hasher.hash(dto.password);
    return this.repository.save({ ...dto, password: hashedPassword });
  }
}

// Configure container
const container = new Container();

container.bind<UserRepository>(TYPES.UserRepository)
  .to(PostgresUserRepository)
  .inSingletonScope();

container.bind<PasswordHasher>(TYPES.PasswordHasher)
  .to(BcryptPasswordHasher);

container.bind<Logger>(TYPES.Logger)
  .to(ConsoleLogger)
  .inSingletonScope();

container.bind<UserService>(TYPES.UserService)
  .to(UserService);

// Resolve dependencies
const userService = container.get<UserService>(TYPES.UserService);
```

### TSyringe

```typescript
import { container, injectable, inject } from 'tsyringe';

@injectable()
class UserRepository {
  async save(user: User): Promise<User> { /* ... */ }
}

@injectable()
class EmailService {
  async send(to: string, message: string): Promise<void> { /* ... */ }
}

@injectable()
class UserService {
  constructor(
    private repository: UserRepository,
    private emailService: EmailService
  ) {}

  async createUser(dto: CreateUserDTO): Promise<User> {
    const user = await this.repository.save(dto);
    await this.emailService.send(user.email, 'Welcome!');
    return user;
  }
}

// Auto-wiring - TSyringe resolves dependencies automatically
const userService = container.resolve(UserService);
```

### NestJS DI

```typescript
import { Module, Injectable, Inject } from '@nestjs/common';

@Injectable()
class UserRepository {
  async save(user: User): Promise<User> { /* ... */ }
}

@Injectable()
class UserService {
  constructor(
    private readonly userRepository: UserRepository,
    @Inject('CONFIG') private readonly config: AppConfig
  ) {}

  async createUser(dto: CreateUserDTO): Promise<User> {
    return this.userRepository.save(dto);
  }
}

@Module({
  providers: [
    UserRepository,
    UserService,
    {
      provide: 'CONFIG',
      useValue: { apiUrl: 'https://api.example.com' },
    },
  ],
  exports: [UserService],
})
class UserModule {}
```

## Scopes

```typescript
// Singleton - one instance for entire application
container.bind(Logger).to(ConsoleLogger).inSingletonScope();

// Transient - new instance for each resolution (default)
container.bind(RequestValidator).to(RequestValidator).inTransientScope();

// Request - one instance per request (web applications)
container.bind(RequestContext).to(RequestContext).inRequestScope();

// Custom scope
const workspaceScope = new ContainerScope();
container.bind(WorkspaceService).to(WorkspaceService).inScope(workspaceScope);
```

## Factory Pattern with DI

```typescript
// When you need runtime decisions
interface PaymentGatewayFactory {
  create(type: PaymentType): PaymentGateway;
}

@injectable()
class DefaultPaymentGatewayFactory implements PaymentGatewayFactory {
  constructor(
    @inject('StripeGateway') private stripe: PaymentGateway,
    @inject('PayPalGateway') private paypal: PaymentGateway
  ) {}

  create(type: PaymentType): PaymentGateway {
    switch (type) {
      case 'stripe': return this.stripe;
      case 'paypal': return this.paypal;
      default: throw new Error(`Unknown payment type: ${type}`);
    }
  }
}

@injectable()
class OrderService {
  constructor(
    private readonly gatewayFactory: PaymentGatewayFactory
  ) {}

  async processPayment(order: Order): Promise<void> {
    const gateway = this.gatewayFactory.create(order.paymentType);
    await gateway.charge(order.total);
  }
}
```

## Testing with DI

```typescript
describe('UserService', () => {
  let userService: UserService;
  let mockRepository: jest.Mocked<UserRepository>;
  let mockHasher: jest.Mocked<PasswordHasher>;
  let mockLogger: jest.Mocked<Logger>;

  beforeEach(() => {
    // Create mocks
    mockRepository = {
      save: jest.fn(),
      findById: jest.fn(),
      findByEmail: jest.fn(),
    };

    mockHasher = {
      hash: jest.fn(),
      verify: jest.fn(),
    };

    mockLogger = {
      log: jest.fn(),
      error: jest.fn(),
    };

    // Inject mocks
    userService = new UserService(mockRepository, mockHasher, mockLogger);
  });

  it('should hash password before saving', async () => {
    const dto = { email: 'test@example.com', password: 'secret' };
    mockHasher.hash.mockResolvedValue('hashed_secret');
    mockRepository.save.mockResolvedValue({ id: '1', ...dto, password: 'hashed_secret' });

    await userService.createUser(dto);

    expect(mockHasher.hash).toHaveBeenCalledWith('secret');
    expect(mockRepository.save).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'hashed_secret',
    });
  });

  it('should log user creation', async () => {
    mockHasher.hash.mockResolvedValue('hashed');
    mockRepository.save.mockResolvedValue({ id: '1' } as User);

    await userService.createUser({ email: 'test@example.com', password: 'secret' });

    expect(mockLogger.log).toHaveBeenCalledWith('Creating user');
  });
});
```

## Best Practices

### 1. Depend on Abstractions

```typescript
// ❌ Depending on concrete class
class OrderService {
  constructor(private repo: PostgresOrderRepository) {}
}

// ✅ Depending on interface
class OrderService {
  constructor(private repo: OrderRepository) {}
}
```

### 2. Constructor Injection for Required Dependencies

```typescript
// ✅ Required dependencies in constructor
class UserService {
  constructor(
    private readonly repository: UserRepository,  // Required
    private readonly logger: Logger               // Required
  ) {}
}
```

### 3. Optional Dependencies with Defaults

```typescript
// ✅ Optional dependencies with sensible defaults
class CacheService {
  constructor(
    private readonly store: CacheStore,
    private readonly options: CacheOptions = { ttl: 3600 }
  ) {}
}
```

### 4. Avoid Service Locator Anti-Pattern

```typescript
// ❌ Service Locator - hides dependencies
class OrderService {
  process(order: Order): void {
    const repository = ServiceLocator.get<OrderRepository>('OrderRepository');
    const logger = ServiceLocator.get<Logger>('Logger');
    // ...
  }
}

// ✅ Explicit dependencies
class OrderService {
  constructor(
    private readonly repository: OrderRepository,
    private readonly logger: Logger
  ) {}

  process(order: Order): void {
    // Dependencies are explicit
  }
}
```

## Summary

| Benefit | Description |
|---------|-------------|
| Testability | Easy to mock dependencies |
| Flexibility | Swap implementations without code changes |
| Maintainability | Clear dependency graph |
| Reusability | Components work with any implementation |
| Separation | Classes focus on their responsibility |
