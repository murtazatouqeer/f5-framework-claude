# Design Patterns Reference

## Creational Patterns

### Factory Method

```typescript
// Define creation interface, let subclasses decide which class to instantiate
interface PaymentProcessor {
  process(amount: number): Promise<PaymentResult>;
}

interface PaymentProcessorFactory {
  create(): PaymentProcessor;
}

class StripeProcessorFactory implements PaymentProcessorFactory {
  create(): PaymentProcessor {
    return new StripeProcessor(this.config);
  }
}

class PayPalProcessorFactory implements PaymentProcessorFactory {
  create(): PaymentProcessor {
    return new PayPalProcessor(this.config);
  }
}

// Usage
function getProcessorFactory(type: string): PaymentProcessorFactory {
  switch (type) {
    case 'stripe': return new StripeProcessorFactory();
    case 'paypal': return new PayPalProcessorFactory();
    default: throw new Error(`Unknown payment type: ${type}`);
  }
}
```

### Abstract Factory

```typescript
// Create families of related objects without specifying concrete classes
interface UIFactory {
  createButton(): Button;
  createInput(): Input;
  createModal(): Modal;
}

class MaterialUIFactory implements UIFactory {
  createButton(): Button { return new MaterialButton(); }
  createInput(): Input { return new MaterialInput(); }
  createModal(): Modal { return new MaterialModal(); }
}

class AntDesignFactory implements UIFactory {
  createButton(): Button { return new AntButton(); }
  createInput(): Input { return new AntInput(); }
  createModal(): Modal { return new AntModal(); }
}

// Usage
function createUI(factory: UIFactory) {
  const button = factory.createButton();
  const input = factory.createInput();
  return { button, input };
}
```

### Builder

```typescript
// Separate complex object construction from representation
class QueryBuilder {
  private query: Query = { select: [], from: '', where: [], orderBy: [] };

  select(...columns: string[]): this {
    this.query.select.push(...columns);
    return this;
  }

  from(table: string): this {
    this.query.from = table;
    return this;
  }

  where(condition: string): this {
    this.query.where.push(condition);
    return this;
  }

  orderBy(column: string, direction: 'ASC' | 'DESC' = 'ASC'): this {
    this.query.orderBy.push({ column, direction });
    return this;
  }

  build(): string {
    const select = this.query.select.join(', ');
    const where = this.query.where.length
      ? `WHERE ${this.query.where.join(' AND ')}`
      : '';
    const orderBy = this.query.orderBy.length
      ? `ORDER BY ${this.query.orderBy.map(o => `${o.column} ${o.direction}`).join(', ')}`
      : '';

    return `SELECT ${select} FROM ${this.query.from} ${where} ${orderBy}`.trim();
  }
}

// Usage
const sql = new QueryBuilder()
  .select('id', 'name', 'email')
  .from('users')
  .where('active = true')
  .where('created_at > NOW() - INTERVAL 30 DAY')
  .orderBy('created_at', 'DESC')
  .build();
```

### Singleton

```typescript
// Ensure a class has only one instance with global access point
class ConfigurationManager {
  private static instance: ConfigurationManager;
  private config: Map<string, any> = new Map();

  private constructor() {
    // Load config from environment
    this.loadFromEnvironment();
  }

  static getInstance(): ConfigurationManager {
    if (!ConfigurationManager.instance) {
      ConfigurationManager.instance = new ConfigurationManager();
    }
    return ConfigurationManager.instance;
  }

  get<T>(key: string): T | undefined {
    return this.config.get(key) as T;
  }

  private loadFromEnvironment(): void {
    // Load configuration
  }
}

// Prefer dependency injection over singleton in most cases
// Singleton is appropriate for: configuration, logging, connection pools
```

## Structural Patterns

### Adapter

```typescript
// Convert interface of a class into another interface clients expect
interface ModernPaymentGateway {
  charge(amount: Money, card: CardDetails): Promise<PaymentResult>;
}

// Legacy payment system with different interface
class LegacyPaymentSystem {
  processPayment(cents: number, cardNumber: string, expiry: string, cvv: string): boolean {
    // Legacy implementation
    return true;
  }
}

class LegacyPaymentAdapter implements ModernPaymentGateway {
  constructor(private legacy: LegacyPaymentSystem) {}

  async charge(amount: Money, card: CardDetails): Promise<PaymentResult> {
    const cents = amount.toCents();
    const success = this.legacy.processPayment(
      cents,
      card.number,
      card.expiry,
      card.cvv
    );
    return { success, transactionId: crypto.randomUUID() };
  }
}

// Usage
const gateway: ModernPaymentGateway = new LegacyPaymentAdapter(new LegacyPaymentSystem());
await gateway.charge(Money.create(100, 'USD'), cardDetails);
```

### Decorator

```typescript
// Attach additional responsibilities dynamically
interface DataSource {
  read(): string;
  write(data: string): void;
}

class FileDataSource implements DataSource {
  constructor(private filename: string) {}
  read(): string { return fs.readFileSync(this.filename, 'utf-8'); }
  write(data: string): void { fs.writeFileSync(this.filename, data); }
}

// Decorator base
abstract class DataSourceDecorator implements DataSource {
  constructor(protected wrappee: DataSource) {}
  read(): string { return this.wrappee.read(); }
  write(data: string): void { this.wrappee.write(data); }
}

class EncryptionDecorator extends DataSourceDecorator {
  read(): string {
    return this.decrypt(super.read());
  }

  write(data: string): void {
    super.write(this.encrypt(data));
  }

  private encrypt(data: string): string { /* ... */ return data; }
  private decrypt(data: string): string { /* ... */ return data; }
}

class CompressionDecorator extends DataSourceDecorator {
  read(): string {
    return this.decompress(super.read());
  }

  write(data: string): void {
    super.write(this.compress(data));
  }

  private compress(data: string): string { /* ... */ return data; }
  private decompress(data: string): string { /* ... */ return data; }
}

// Usage - decorators can be stacked
let source: DataSource = new FileDataSource('data.txt');
source = new EncryptionDecorator(source);
source = new CompressionDecorator(source);
source.write('sensitive data'); // Compressed then encrypted
```

### Facade

```typescript
// Provide unified interface to a set of interfaces in a subsystem
class OrderFacade {
  constructor(
    private inventory: InventoryService,
    private payment: PaymentService,
    private shipping: ShippingService,
    private notification: NotificationService
  ) {}

  async placeOrder(order: OrderRequest): Promise<OrderResult> {
    // Check inventory
    const available = await this.inventory.checkAvailability(order.items);
    if (!available) {
      return { success: false, error: 'Items not available' };
    }

    // Reserve items
    const reservation = await this.inventory.reserve(order.items);

    try {
      // Process payment
      const payment = await this.payment.charge(order.total, order.paymentMethod);
      if (!payment.success) {
        await this.inventory.cancelReservation(reservation.id);
        return { success: false, error: 'Payment failed' };
      }

      // Confirm reservation
      await this.inventory.confirmReservation(reservation.id);

      // Create shipment
      const shipment = await this.shipping.createShipment(order);

      // Send notification
      await this.notification.sendOrderConfirmation(order, shipment);

      return { success: true, orderId: order.id, shipmentId: shipment.id };
    } catch (error) {
      await this.inventory.cancelReservation(reservation.id);
      throw error;
    }
  }
}

// Usage - simple interface hides complex coordination
const facade = new OrderFacade(inventory, payment, shipping, notification);
await facade.placeOrder(orderRequest);
```

### Repository

```typescript
// Mediates between domain and data mapping layers
interface Repository<T, ID> {
  findById(id: ID): Promise<T | null>;
  findAll(): Promise<T[]>;
  save(entity: T): Promise<void>;
  delete(id: ID): Promise<void>;
}

interface UserRepository extends Repository<User, UserId> {
  findByEmail(email: Email): Promise<User | null>;
  findActiveUsers(): Promise<User[]>;
}

class PostgresUserRepository implements UserRepository {
  constructor(private db: Database) {}

  async findById(id: UserId): Promise<User | null> {
    const row = await this.db.query('SELECT * FROM users WHERE id = $1', [id.value]);
    return row ? UserMapper.toDomain(row) : null;
  }

  async findByEmail(email: Email): Promise<User | null> {
    const row = await this.db.query('SELECT * FROM users WHERE email = $1', [email.value]);
    return row ? UserMapper.toDomain(row) : null;
  }

  async save(user: User): Promise<void> {
    const data = UserMapper.toPersistence(user);
    await this.db.query(
      'INSERT INTO users (id, name, email) VALUES ($1, $2, $3) ON CONFLICT (id) DO UPDATE SET name = $2, email = $3',
      [data.id, data.name, data.email]
    );
  }

  async delete(id: UserId): Promise<void> {
    await this.db.query('DELETE FROM users WHERE id = $1', [id.value]);
  }

  async findActiveUsers(): Promise<User[]> {
    const rows = await this.db.query('SELECT * FROM users WHERE active = true');
    return rows.map(UserMapper.toDomain);
  }
}
```

## Behavioral Patterns

### Strategy

```typescript
// Define family of algorithms, make them interchangeable
interface PricingStrategy {
  calculate(order: Order): Money;
}

class StandardPricing implements PricingStrategy {
  calculate(order: Order): Money {
    return order.items.reduce((sum, item) => sum.add(item.price.multiply(item.quantity)), Money.zero());
  }
}

class MemberPricing implements PricingStrategy {
  constructor(private discountPercent: number) {}

  calculate(order: Order): Money {
    const standard = new StandardPricing().calculate(order);
    return standard.multiply(1 - this.discountPercent / 100);
  }
}

class BulkPricing implements PricingStrategy {
  calculate(order: Order): Money {
    return order.items.reduce((sum, item) => {
      const unitPrice = item.quantity >= 10
        ? item.price.multiply(0.9)  // 10% bulk discount
        : item.price;
      return sum.add(unitPrice.multiply(item.quantity));
    }, Money.zero());
  }
}

// Usage
class OrderService {
  constructor(private pricingStrategy: PricingStrategy) {}

  calculateTotal(order: Order): Money {
    return this.pricingStrategy.calculate(order);
  }
}

const memberService = new OrderService(new MemberPricing(15));
const bulkService = new OrderService(new BulkPricing());
```

### Observer

```typescript
// Define one-to-many dependency between objects
interface Observer<T> {
  update(event: T): void;
}

interface Subject<T> {
  subscribe(observer: Observer<T>): void;
  unsubscribe(observer: Observer<T>): void;
  notify(event: T): void;
}

class EventEmitter<T> implements Subject<T> {
  private observers: Set<Observer<T>> = new Set();

  subscribe(observer: Observer<T>): void {
    this.observers.add(observer);
  }

  unsubscribe(observer: Observer<T>): void {
    this.observers.delete(observer);
  }

  notify(event: T): void {
    this.observers.forEach(observer => observer.update(event));
  }
}

// Domain event publisher
class OrderEventPublisher extends EventEmitter<OrderEvent> {
  orderCreated(order: Order): void {
    this.notify({ type: 'ORDER_CREATED', payload: order });
  }

  orderShipped(order: Order, tracking: string): void {
    this.notify({ type: 'ORDER_SHIPPED', payload: { order, tracking } });
  }
}

// Observers
class InventoryObserver implements Observer<OrderEvent> {
  update(event: OrderEvent): void {
    if (event.type === 'ORDER_CREATED') {
      this.updateInventory(event.payload);
    }
  }
}

class NotificationObserver implements Observer<OrderEvent> {
  update(event: OrderEvent): void {
    if (event.type === 'ORDER_SHIPPED') {
      this.sendShippingNotification(event.payload);
    }
  }
}
```

### Command

```typescript
// Encapsulate request as object, enabling undo/redo and queuing
interface Command {
  execute(): Promise<void>;
  undo(): Promise<void>;
}

class AddItemCommand implements Command {
  private previousQuantity: number = 0;

  constructor(
    private cart: ShoppingCart,
    private productId: string,
    private quantity: number
  ) {}

  async execute(): Promise<void> {
    const existing = this.cart.findItem(this.productId);
    this.previousQuantity = existing?.quantity || 0;
    this.cart.addItem(this.productId, this.quantity);
  }

  async undo(): Promise<void> {
    if (this.previousQuantity === 0) {
      this.cart.removeItem(this.productId);
    } else {
      this.cart.setItemQuantity(this.productId, this.previousQuantity);
    }
  }
}

class CommandHistory {
  private history: Command[] = [];
  private position: number = -1;

  async execute(command: Command): Promise<void> {
    // Remove any commands after current position (for redo)
    this.history = this.history.slice(0, this.position + 1);
    await command.execute();
    this.history.push(command);
    this.position++;
  }

  async undo(): Promise<void> {
    if (this.position >= 0) {
      await this.history[this.position].undo();
      this.position--;
    }
  }

  async redo(): Promise<void> {
    if (this.position < this.history.length - 1) {
      this.position++;
      await this.history[this.position].execute();
    }
  }
}
```

### State

```typescript
// Allow object to alter behavior when internal state changes
interface OrderState {
  proceed(order: Order): void;
  cancel(order: Order): void;
  ship(order: Order): void;
}

class PendingState implements OrderState {
  proceed(order: Order): void {
    order.setState(new ConfirmedState());
  }

  cancel(order: Order): void {
    order.setState(new CancelledState());
  }

  ship(order: Order): void {
    throw new Error('Cannot ship pending order');
  }
}

class ConfirmedState implements OrderState {
  proceed(order: Order): void {
    order.setState(new ProcessingState());
  }

  cancel(order: Order): void {
    order.setState(new CancelledState());
  }

  ship(order: Order): void {
    throw new Error('Order must be processed before shipping');
  }
}

class ProcessingState implements OrderState {
  proceed(order: Order): void {
    throw new Error('Use ship() to proceed from processing');
  }

  cancel(order: Order): void {
    throw new Error('Cannot cancel order in processing');
  }

  ship(order: Order): void {
    order.setState(new ShippedState());
  }
}

class Order {
  private state: OrderState = new PendingState();

  setState(state: OrderState): void {
    this.state = state;
  }

  proceed(): void { this.state.proceed(this); }
  cancel(): void { this.state.cancel(this); }
  ship(): void { this.state.ship(this); }
}
```

## Pattern Selection Guide

| Need | Pattern | Example |
|------|---------|---------|
| Create objects without specifying class | Factory Method | Payment processor creation |
| Create families of related objects | Abstract Factory | UI component libraries |
| Complex object construction | Builder | SQL query builder |
| Single instance with global access | Singleton | Configuration manager |
| Convert incompatible interfaces | Adapter | Legacy system integration |
| Add behavior dynamically | Decorator | Logging, caching, encryption |
| Simplify complex subsystem | Facade | Order processing workflow |
| Persistence abstraction | Repository | Data access layer |
| Interchangeable algorithms | Strategy | Pricing, sorting, validation |
| Notify on state changes | Observer | Event-driven systems |
| Encapsulate operations | Command | Undo/redo, task queues |
| Behavior varies by state | State | Workflow, order status |
