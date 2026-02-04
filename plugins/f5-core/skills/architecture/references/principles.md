# Architecture Principles Reference

## SOLID Principles

### Single Responsibility Principle (SRP)

> A class should have only one reason to change.

```typescript
// ❌ Multiple responsibilities
class User {
  save(): void { /* database */ }
  sendEmail(): void { /* email */ }
  generateReport(): string { /* report */ }
}

// ✅ Single responsibility each
class User {
  constructor(public readonly id: string, public name: string, public email: string) {}
}

class UserRepository {
  async save(user: User): Promise<void> { /* database only */ }
}

class UserEmailService {
  async sendWelcomeEmail(user: User): Promise<void> { /* email only */ }
}
```

### Open/Closed Principle (OCP)

> Open for extension, closed for modification.

```typescript
// ❌ Must modify to add payment types
class PaymentProcessor {
  process(type: string, amount: number): void {
    if (type === 'credit_card') { /* ... */ }
    else if (type === 'paypal') { /* ... */ }
    // Must add new else-if for each type
  }
}

// ✅ Open for extension via new implementations
interface PaymentMethod {
  process(amount: number): Promise<PaymentResult>;
}

class CreditCardPayment implements PaymentMethod {
  async process(amount: number): Promise<PaymentResult> { /* ... */ }
}

class PayPalPayment implements PaymentMethod {
  async process(amount: number): Promise<PaymentResult> { /* ... */ }
}

// Add new payment without modifying existing code
class StripePayment implements PaymentMethod {
  async process(amount: number): Promise<PaymentResult> { /* ... */ }
}
```

### Liskov Substitution Principle (LSP)

> Subtypes must be substitutable for their base types.

```typescript
// ❌ Square violates Rectangle behavior
class Rectangle {
  setWidth(width: number): void { this.width = width; }
  setHeight(height: number): void { this.height = height; }
}

class Square extends Rectangle {
  setWidth(width: number): void {
    this.width = width;
    this.height = width; // Violates expected behavior!
  }
}

// ✅ Use interfaces for shared behavior
interface Shape {
  getArea(): number;
}

class Rectangle implements Shape {
  constructor(private width: number, private height: number) {}
  getArea(): number { return this.width * this.height; }
}

class Square implements Shape {
  constructor(private side: number) {}
  getArea(): number { return this.side * this.side; }
}
```

### Interface Segregation Principle (ISP)

> Clients should not depend on interfaces they don't use.

```typescript
// ❌ Fat interface forces unnecessary implementations
interface Worker {
  work(): void;
  eat(): void;
  sleep(): void;
}

class Robot implements Worker {
  work(): void { /* OK */ }
  eat(): void { throw new Error('Robots dont eat'); } // Forced!
  sleep(): void { throw new Error('Robots dont sleep'); } // Forced!
}

// ✅ Segregated interfaces
interface Workable { work(): void; }
interface Eatable { eat(): void; }
interface Sleepable { sleep(): void; }

class Human implements Workable, Eatable, Sleepable {
  work(): void { /* ... */ }
  eat(): void { /* ... */ }
  sleep(): void { /* ... */ }
}

class Robot implements Workable {
  work(): void { /* ... */ }
  // No need for eat() or sleep()
}
```

### Dependency Inversion Principle (DIP)

> Depend on abstractions, not concretions.

```typescript
// ❌ High-level depends on low-level
class UserService {
  private database = new MySQLDatabase(); // Tight coupling!
  createUser(data: UserData): void { this.database.save(data); }
}

// ✅ Both depend on abstraction
interface Database {
  save(data: any): Promise<void>;
  find(query: any): Promise<any>;
}

class MySQLDatabase implements Database { /* ... */ }
class PostgreSQLDatabase implements Database { /* ... */ }

class UserService {
  constructor(private database: Database) {} // Injected!
  async createUser(data: UserData): Promise<void> {
    await this.database.save(data);
  }
}

// Easy to switch implementations
const userService = new UserService(new PostgreSQLDatabase());
```

## Core Design Principles

### DRY (Don't Repeat Yourself)

```typescript
// ❌ Duplicated validation
function createUser(email: string) {
  if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
    throw new Error('Invalid email');
  }
}

function updateEmail(email: string) {
  if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
    throw new Error('Invalid email');
  }
}

// ✅ Single source of truth
class Email {
  private constructor(private readonly value: string) {}

  static create(value: string): Email {
    if (!value.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
      throw new Error('Invalid email');
    }
    return new Email(value.toLowerCase());
  }

  toString(): string { return this.value; }
}
```

### KISS (Keep It Simple, Stupid)

```typescript
// ❌ Over-engineered
class UserManagerFactoryBuilderImpl implements IUserManagerFactoryBuilder {
  private builderConfig: BuilderConfiguration;
  private factoryStrategy: FactoryStrategy;
  // ... 200 lines of abstraction

  createUserManager(): IUserManager {
    return new UserManagerImpl(this.builderConfig);
  }
}

// ✅ Simple and direct
class UserService {
  constructor(private repository: UserRepository) {}

  async getUser(id: string): Promise<User | null> {
    return this.repository.findById(id);
  }

  async createUser(data: CreateUserData): Promise<User> {
    const user = User.create(data);
    await this.repository.save(user);
    return user;
  }
}
```

### YAGNI (You Aren't Gonna Need It)

```typescript
// ❌ Speculative features
interface User {
  id: string;
  name: string;
  email: string;
  futureFeatureFlag: boolean;        // "We might need this"
  legacySystemId: string;            // "Just in case"
  analyticsMetadata: Record<string, any>; // "Could be useful"
}

// ✅ Only what's needed now
interface User {
  id: string;
  name: string;
  email: string;
}
```

### Separation of Concerns

```typescript
// ❌ Mixed concerns
class OrderController {
  async createOrder(req: Request) {
    // Validation
    if (!req.body.items?.length) throw new Error('Items required');

    // Business logic
    const total = req.body.items.reduce((sum, i) => sum + i.price * i.qty, 0);

    // Persistence
    const order = await db.query('INSERT INTO orders...');

    // Notification
    await emailService.send(order.customerEmail, 'Order confirmed');

    return order;
  }
}

// ✅ Separated concerns
// Controller - HTTP handling only
class OrderController {
  constructor(private createOrderUseCase: CreateOrderUseCase) {}

  async createOrder(req: Request, res: Response) {
    const dto = CreateOrderDTO.fromRequest(req);
    const result = await this.createOrderUseCase.execute(dto);
    return res.status(201).json(result);
  }
}

// Use case - business logic
class CreateOrderUseCase {
  constructor(
    private orderRepository: OrderRepository,
    private notificationService: NotificationService
  ) {}

  async execute(dto: CreateOrderDTO): Promise<OrderResponse> {
    const order = Order.create(dto.items);
    await this.orderRepository.save(order);
    await this.notificationService.notifyOrderCreated(order);
    return OrderMapper.toResponse(order);
  }
}

// Repository - persistence
class OrderRepository {
  async save(order: Order): Promise<void> { /* database only */ }
}

// Service - notifications
class NotificationService {
  async notifyOrderCreated(order: Order): Promise<void> { /* email only */ }
}
```

## Dependency Inversion in Practice

### Constructor Injection

```typescript
// Preferred - explicit dependencies
class OrderService {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly paymentGateway: PaymentGateway,
    private readonly emailService: EmailService
  ) {}
}
```

### Interface-Based Dependencies

```typescript
// Domain layer defines interface
interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
}

// Infrastructure implements interface
class PostgresOrderRepository implements OrderRepository {
  constructor(private db: Database) {}

  async save(order: Order): Promise<void> {
    const data = OrderMapper.toPersistence(order);
    await this.db.query('INSERT INTO orders...', data);
  }

  async findById(id: OrderId): Promise<Order | null> {
    const row = await this.db.query('SELECT * FROM orders WHERE id = $1', [id.value]);
    return row ? OrderMapper.toDomain(row) : null;
  }
}
```

### Dependency Injection Container

```typescript
// Container configuration
const container = new Container();

// Bind interfaces to implementations
container.bind<OrderRepository>('OrderRepository').to(PostgresOrderRepository);
container.bind<PaymentGateway>('PaymentGateway').to(StripePaymentGateway);
container.bind<EmailService>('EmailService').to(SendGridEmailService);

// Resolve with dependencies
const orderService = container.resolve(OrderService);
```

## Common Violations

| Principle | Violation Sign | Fix |
|-----------|----------------|-----|
| SRP | Class has "and" in name | Split into focused classes |
| OCP | Switch/if on type | Use polymorphism |
| LSP | Override throws NotImplemented | Use composition over inheritance |
| ISP | Implements unused methods | Split interface |
| DIP | `new` inside class | Inject dependency |
| DRY | Copy-paste code | Extract to function/class |
| KISS | "Future-proofing" | Build only what's needed |
