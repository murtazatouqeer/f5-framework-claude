---
name: domain-driven-design
description: Domain-Driven Design tactical and strategic patterns
category: architecture/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Domain-Driven Design (DDD)

## Overview

DDD is an approach to software development that centers the
development on programming a domain model with a rich
understanding of the business processes.

## Strategic Design

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
│                 │                 │                         │
└────────┬────────┴────────┬────────┴────────────┬────────────┘
         │                 │                      │
         └────── Events ───┴────── Events ────────┘
```

### Context Mapping Patterns

```typescript
// 1. Shared Kernel - Types shared between contexts
// shared-kernel/types.ts
export type CustomerId = string;
export type ProductId = string;
export type Money = {
  amount: number;
  currency: string;
};

// 2. Anti-Corruption Layer - Translate external concepts
// ordering/infrastructure/acl/inventory-acl.ts
export class InventoryAntiCorruptionLayer {
  constructor(private inventoryClient: InventoryClient) {}

  async getProductForOrdering(productId: string): Promise<Product> {
    // Fetch from Inventory context
    const inventoryProduct = await this.inventoryClient.getProduct(productId);

    // Translate to Ordering context's Product
    return new Product(
      inventoryProduct.id,
      inventoryProduct.name,
      Money.create(inventoryProduct.price, inventoryProduct.currency),
      inventoryProduct.availableQuantity > 0
    );
  }
}

// 3. Published Language - Well-documented API/Events
// events/order-placed.event.ts
export interface OrderPlacedEvent {
  eventType: 'ORDER_PLACED';
  version: '1.0';
  payload: {
    orderId: string;
    customerId: string;
    items: Array<{
      productId: string;
      quantity: number;
      priceAtPurchase: number;
    }>;
    totalAmount: number;
    currency: string;
    placedAt: string;
  };
}
```

## Tactical Design

### Entities

```typescript
// domain/entities/order.ts
import { Entity } from '../base/entity';
import { OrderId } from '../value-objects/order-id';
import { CustomerId } from '../value-objects/customer-id';
import { OrderItem } from './order-item';
import { OrderStatus } from '../enums/order-status';
import { Money } from '../value-objects/money';
import { DomainEvent } from '../events/domain-event';
import { OrderCreatedEvent } from '../events/order-created.event';
import { OrderConfirmedEvent } from '../events/order-confirmed.event';

export class Order extends Entity<OrderId> {
  private _customerId: CustomerId;
  private _items: OrderItem[];
  private _status: OrderStatus;
  private _createdAt: Date;
  private _events: DomainEvent[] = [];

  private constructor(
    id: OrderId,
    customerId: CustomerId,
    items: OrderItem[],
    status: OrderStatus,
    createdAt: Date
  ) {
    super(id);
    this._customerId = customerId;
    this._items = items;
    this._status = status;
    this._createdAt = createdAt;
  }

  // Factory method
  static create(customerId: CustomerId, items: OrderItem[]): Order {
    if (items.length === 0) {
      throw new OrderMustHaveItemsError();
    }

    const order = new Order(
      OrderId.generate(),
      customerId,
      items,
      OrderStatus.PENDING,
      new Date()
    );

    // Raise domain event
    order.addEvent(new OrderCreatedEvent(order.id, customerId, order.total));

    return order;
  }

  // Reconstitute from persistence
  static reconstitute(
    id: OrderId,
    customerId: CustomerId,
    items: OrderItem[],
    status: OrderStatus,
    createdAt: Date
  ): Order {
    return new Order(id, customerId, items, status, createdAt);
  }

  get total(): Money {
    return this._items.reduce(
      (sum, item) => sum.add(item.subtotal),
      Money.zero()
    );
  }

  confirm(): void {
    this.ensureStatus(OrderStatus.PENDING, 'confirm');
    this._status = OrderStatus.CONFIRMED;
    this.addEvent(new OrderConfirmedEvent(this.id));
  }

  ship(trackingNumber: string): void {
    this.ensureStatus(OrderStatus.CONFIRMED, 'ship');
    this._status = OrderStatus.SHIPPED;
    this.addEvent(new OrderShippedEvent(this.id, trackingNumber));
  }

  cancel(reason: string): void {
    if (this._status === OrderStatus.SHIPPED) {
      throw new CannotCancelShippedOrderError();
    }
    this._status = OrderStatus.CANCELLED;
    this.addEvent(new OrderCancelledEvent(this.id, reason));
  }

  private ensureStatus(expected: OrderStatus, action: string): void {
    if (this._status !== expected) {
      throw new InvalidOrderStateError(action, this._status, expected);
    }
  }

  private addEvent(event: DomainEvent): void {
    this._events.push(event);
  }

  pullEvents(): DomainEvent[] {
    const events = [...this._events];
    this._events = [];
    return events;
  }
}
```

### Value Objects

```typescript
// domain/value-objects/money.ts
export class Money {
  private constructor(
    private readonly _amount: number,
    private readonly _currency: string
  ) {
    if (_amount < 0) {
      throw new InvalidMoneyError('Amount cannot be negative');
    }
  }

  static create(amount: number, currency: string = 'USD'): Money {
    return new Money(amount, currency);
  }

  static zero(currency: string = 'USD'): Money {
    return new Money(0, currency);
  }

  get amount(): number { return this._amount; }
  get currency(): string { return this._currency; }

  add(other: Money): Money {
    this.ensureSameCurrency(other);
    return new Money(this._amount + other._amount, this._currency);
  }

  subtract(other: Money): Money {
    this.ensureSameCurrency(other);
    return new Money(this._amount - other._amount, this._currency);
  }

  multiply(factor: number): Money {
    return new Money(this._amount * factor, this._currency);
  }

  equals(other: Money): boolean {
    return this._amount === other._amount && this._currency === other._currency;
  }

  private ensureSameCurrency(other: Money): void {
    if (this._currency !== other._currency) {
      throw new CurrencyMismatchError(this._currency, other._currency);
    }
  }

  toString(): string {
    return `${this._currency} ${this._amount.toFixed(2)}`;
  }
}

// domain/value-objects/email.ts
export class Email {
  private constructor(private readonly _value: string) {}

  static create(value: string): Email {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      throw new InvalidEmailError(value);
    }
    return new Email(value.toLowerCase());
  }

  get value(): string { return this._value; }

  get domain(): string {
    return this._value.split('@')[1];
  }

  equals(other: Email): boolean {
    return this._value === other._value;
  }

  toString(): string { return this._value; }
}

// domain/value-objects/address.ts
export class Address {
  private constructor(
    public readonly street: string,
    public readonly city: string,
    public readonly state: string,
    public readonly zipCode: string,
    public readonly country: string
  ) {}

  static create(props: AddressProps): Address {
    // Validation
    if (!props.street?.trim()) throw new InvalidAddressError('Street is required');
    if (!props.city?.trim()) throw new InvalidAddressError('City is required');
    if (!props.zipCode?.trim()) throw new InvalidAddressError('Zip code is required');
    if (!props.country?.trim()) throw new InvalidAddressError('Country is required');

    return new Address(
      props.street.trim(),
      props.city.trim(),
      props.state?.trim() || '',
      props.zipCode.trim(),
      props.country.trim()
    );
  }

  equals(other: Address): boolean {
    return (
      this.street === other.street &&
      this.city === other.city &&
      this.state === other.state &&
      this.zipCode === other.zipCode &&
      this.country === other.country
    );
  }

  format(): string {
    return `${this.street}, ${this.city}, ${this.state} ${this.zipCode}, ${this.country}`;
  }
}
```

### Aggregates

```typescript
// domain/aggregates/order.aggregate.ts
// Order is the Aggregate Root
// OrderItem is an Entity within the aggregate
// Order controls all access to OrderItems

export class Order {
  private _items: OrderItem[] = [];

  // All access to items goes through the aggregate root
  get items(): readonly OrderItem[] {
    return [...this._items];
  }

  addItem(productId: ProductId, quantity: number, price: Money): void {
    // Validate at aggregate level
    if (this._status !== OrderStatus.DRAFT) {
      throw new CannotModifyNonDraftOrderError();
    }

    // Check if item already exists
    const existingItem = this._items.find(i => i.productId.equals(productId));
    if (existingItem) {
      existingItem.increaseQuantity(quantity);
    } else {
      this._items.push(OrderItem.create(productId, quantity, price));
    }

    // Invariant: order total must not exceed limit
    if (this.total.amount > MAX_ORDER_TOTAL) {
      throw new OrderTotalExceedsLimitError();
    }
  }

  removeItem(productId: ProductId): void {
    if (this._status !== OrderStatus.DRAFT) {
      throw new CannotModifyNonDraftOrderError();
    }

    const index = this._items.findIndex(i => i.productId.equals(productId));
    if (index === -1) {
      throw new ItemNotInOrderError(productId);
    }

    this._items.splice(index, 1);
  }
}
```

### Domain Services

```typescript
// domain/services/pricing.service.ts
import { Order } from '../entities/order';
import { Customer } from '../entities/customer';
import { Money } from '../value-objects/money';
import { DiscountPolicy } from '../policies/discount-policy';

// Domain service - stateless operations that don't belong to a single entity
export class PricingService {
  constructor(private readonly discountPolicies: DiscountPolicy[]) {}

  calculateFinalPrice(order: Order, customer: Customer): Money {
    let price = order.total;

    // Apply all applicable discounts
    for (const policy of this.discountPolicies) {
      if (policy.isApplicable(order, customer)) {
        price = policy.apply(price, order, customer);
      }
    }

    return price;
  }
}

// domain/policies/discount-policy.ts
export interface DiscountPolicy {
  isApplicable(order: Order, customer: Customer): boolean;
  apply(price: Money, order: Order, customer: Customer): Money;
}

export class VIPDiscountPolicy implements DiscountPolicy {
  isApplicable(order: Order, customer: Customer): boolean {
    return customer.isVIP;
  }

  apply(price: Money, order: Order, customer: Customer): Money {
    return price.multiply(0.9); // 10% discount
  }
}

export class BulkOrderDiscountPolicy implements DiscountPolicy {
  isApplicable(order: Order, customer: Customer): boolean {
    return order.itemCount > 10;
  }

  apply(price: Money, order: Order, customer: Customer): Money {
    return price.multiply(0.95); // 5% discount
  }
}

export class FirstOrderDiscountPolicy implements DiscountPolicy {
  constructor(private orderRepository: OrderRepository) {}

  isApplicable(order: Order, customer: Customer): boolean {
    return customer.orderCount === 0;
  }

  apply(price: Money, order: Order, customer: Customer): Money {
    return price.multiply(0.85); // 15% discount for first order
  }
}
```

### Domain Events

```typescript
// domain/events/order-created.event.ts
import { DomainEvent } from './domain-event';
import { OrderId } from '../value-objects/order-id';
import { CustomerId } from '../value-objects/customer-id';
import { Money } from '../value-objects/money';

export class OrderCreatedEvent implements DomainEvent {
  readonly occurredOn: Date;
  readonly eventType = 'ORDER_CREATED';

  constructor(
    public readonly orderId: OrderId,
    public readonly customerId: CustomerId,
    public readonly total: Money
  ) {
    this.occurredOn = new Date();
  }
}

// application/event-handlers/order-created.handler.ts
export class OrderCreatedHandler {
  constructor(
    private readonly emailService: EmailService,
    private readonly inventoryService: InventoryService,
    private readonly analyticsService: AnalyticsService
  ) {}

  async handle(event: OrderCreatedEvent): Promise<void> {
    // Handle in parallel where possible
    await Promise.all([
      this.emailService.sendOrderConfirmation(event.customerId, event.orderId),
      this.inventoryService.reserveItems(event.orderId),
      this.analyticsService.trackOrderCreated(event),
    ]);
  }
}
```

### Repository Pattern

```typescript
// domain/repositories/order.repository.ts
import { Order } from '../entities/order';
import { OrderId } from '../value-objects/order-id';
import { CustomerId } from '../value-objects/customer-id';

// Repository interface in domain layer
export interface OrderRepository {
  nextId(): OrderId;
  save(order: Order): Promise<void>;
  findById(id: OrderId): Promise<Order | null>;
  findByCustomerId(customerId: CustomerId): Promise<Order[]>;
}

// infrastructure/persistence/order.repository.impl.ts
export class PostgresOrderRepository implements OrderRepository {
  constructor(private readonly db: Database) {}

  nextId(): OrderId {
    return OrderId.generate();
  }

  async save(order: Order): Promise<void> {
    // Use unit of work pattern for consistency
    const connection = await this.db.getConnection();
    try {
      await connection.beginTransaction();

      await connection.query(
        `INSERT INTO orders (id, customer_id, status, created_at)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (id) DO UPDATE SET status = $3`,
        [order.id.value, order.customerId.value, order.status, order.createdAt]
      );

      for (const item of order.items) {
        await connection.query(
          `INSERT INTO order_items (id, order_id, product_id, quantity, price)
           VALUES ($1, $2, $3, $4, $5)
           ON CONFLICT (id) DO NOTHING`,
          [item.id, order.id.value, item.productId.value, item.quantity, item.price.amount]
        );
      }

      await connection.commit();
    } catch (error) {
      await connection.rollback();
      throw error;
    }
  }

  async findById(id: OrderId): Promise<Order | null> {
    const orderRow = await this.db.query(
      'SELECT * FROM orders WHERE id = $1',
      [id.value]
    );

    if (!orderRow) return null;

    const itemRows = await this.db.query(
      'SELECT * FROM order_items WHERE order_id = $1',
      [id.value]
    );

    return OrderMapper.toDomain(orderRow, itemRows);
  }
}
```

### Specification Pattern

```typescript
// domain/specifications/order.specification.ts
export interface Specification<T> {
  isSatisfiedBy(entity: T): boolean;
  and(other: Specification<T>): Specification<T>;
  or(other: Specification<T>): Specification<T>;
  not(): Specification<T>;
}

abstract class CompositeSpecification<T> implements Specification<T> {
  abstract isSatisfiedBy(entity: T): boolean;

  and(other: Specification<T>): Specification<T> {
    return new AndSpecification(this, other);
  }

  or(other: Specification<T>): Specification<T> {
    return new OrSpecification(this, other);
  }

  not(): Specification<T> {
    return new NotSpecification(this);
  }
}

// Concrete specifications
export class OrderPendingSpecification extends CompositeSpecification<Order> {
  isSatisfiedBy(order: Order): boolean {
    return order.status === OrderStatus.PENDING;
  }
}

export class OrderTotalAboveSpecification extends CompositeSpecification<Order> {
  constructor(private readonly threshold: Money) {
    super();
  }

  isSatisfiedBy(order: Order): boolean {
    return order.total.amount >= this.threshold.amount;
  }
}

// Usage
const spec = new OrderPendingSpecification()
  .and(new OrderTotalAboveSpecification(Money.create(100)));

const eligibleOrders = orders.filter(order => spec.isSatisfiedBy(order));
```

## Summary

| Concept | Purpose | Example |
|---------|---------|---------|
| Entity | Identity + Lifecycle | Order, User |
| Value Object | Immutable, no identity | Money, Email |
| Aggregate | Consistency boundary | Order + OrderItems |
| Domain Service | Cross-entity logic | PricingService |
| Domain Event | Notify state changes | OrderCreated |
| Repository | Persistence abstraction | OrderRepository |
| Factory | Complex creation | Order.create() |
| Specification | Business rules as objects | OrderPendingSpec |
