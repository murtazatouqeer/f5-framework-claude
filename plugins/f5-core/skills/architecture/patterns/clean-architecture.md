---
name: clean-architecture
description: Clean Architecture pattern for maintainable systems
category: architecture/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Clean Architecture

## Overview

Clean Architecture separates concerns into concentric layers,
with dependencies pointing inward toward business logic.

## Layer Structure

```
┌─────────────────────────────────────────────────────┐
│                    Frameworks                        │
│  ┌───────────────────────────────────────────────┐  │
│  │              Interface Adapters                │  │
│  │  ┌─────────────────────────────────────────┐  │  │
│  │  │           Application Layer              │  │  │
│  │  │  ┌───────────────────────────────────┐  │  │  │
│  │  │  │         Domain Layer              │  │  │  │
│  │  │  │    (Entities & Business Rules)    │  │  │  │
│  │  │  └───────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
           Dependencies point INWARD →
```

## Directory Structure

```
src/
├── domain/                    # Innermost - Business Logic
│   ├── entities/
│   │   ├── user.ts
│   │   ├── order.ts
│   │   └── product.ts
│   ├── value-objects/
│   │   ├── email.ts
│   │   ├── money.ts
│   │   └── address.ts
│   ├── repositories/          # Interfaces only!
│   │   ├── user.repository.ts
│   │   └── order.repository.ts
│   ├── services/              # Domain services
│   │   └── pricing.service.ts
│   └── errors/
│       └── domain-errors.ts
│
├── application/               # Use Cases
│   ├── use-cases/
│   │   ├── user/
│   │   │   ├── create-user.ts
│   │   │   ├── get-user.ts
│   │   │   └── update-user.ts
│   │   └── order/
│   │       ├── create-order.ts
│   │       └── process-payment.ts
│   ├── dtos/
│   │   ├── user.dto.ts
│   │   └── order.dto.ts
│   ├── mappers/
│   │   └── user.mapper.ts
│   └── interfaces/            # Ports for external services
│       ├── email.service.ts
│       └── payment.gateway.ts
│
├── infrastructure/            # External Implementations
│   ├── persistence/
│   │   ├── prisma/
│   │   │   ├── user.repository.impl.ts
│   │   │   └── order.repository.impl.ts
│   │   └── typeorm/
│   ├── external-services/
│   │   ├── sendgrid.email.service.ts
│   │   └── stripe.payment.gateway.ts
│   ├── cache/
│   │   └── redis.cache.ts
│   └── config/
│       └── database.config.ts
│
└── presentation/              # Outermost - Delivery
    ├── http/
    │   ├── controllers/
    │   │   ├── user.controller.ts
    │   │   └── order.controller.ts
    │   ├── middlewares/
    │   └── routes/
    ├── graphql/
    │   ├── resolvers/
    │   └── schemas/
    └── cli/
        └── commands/
```

## Implementation Example

### Domain Layer (Entities)

```typescript
// domain/entities/order.ts
import { Money } from '../value-objects/money';
import { OrderStatus } from '../enums/order-status';
import { DomainError } from '../errors/domain-errors';

export class Order {
  private constructor(
    public readonly id: string,
    public readonly customerId: string,
    private _items: OrderItem[],
    private _status: OrderStatus,
    public readonly createdAt: Date
  ) {}

  // Factory method
  static create(customerId: string, items: OrderItem[]): Order {
    if (items.length === 0) {
      throw new DomainError('Order must have at least one item');
    }

    return new Order(
      crypto.randomUUID(),
      customerId,
      items,
      OrderStatus.PENDING,
      new Date()
    );
  }

  // Business logic in entity
  get total(): Money {
    return this._items.reduce(
      (sum, item) => sum.add(item.subtotal),
      Money.zero('USD')
    );
  }

  get status(): OrderStatus {
    return this._status;
  }

  get items(): readonly OrderItem[] {
    return [...this._items];
  }

  addItem(item: OrderItem): void {
    if (this._status !== OrderStatus.PENDING) {
      throw new DomainError('Cannot modify non-pending order');
    }
    this._items.push(item);
  }

  confirm(): void {
    if (this._status !== OrderStatus.PENDING) {
      throw new DomainError('Only pending orders can be confirmed');
    }
    this._status = OrderStatus.CONFIRMED;
  }

  ship(): void {
    if (this._status !== OrderStatus.CONFIRMED) {
      throw new DomainError('Only confirmed orders can be shipped');
    }
    this._status = OrderStatus.SHIPPED;
  }

  cancel(): void {
    if (this._status === OrderStatus.SHIPPED) {
      throw new DomainError('Cannot cancel shipped order');
    }
    this._status = OrderStatus.CANCELLED;
  }
}
```

### Domain Layer (Value Objects)

```typescript
// domain/value-objects/money.ts
export class Money {
  private constructor(
    private readonly _amount: number,
    private readonly _currency: string
  ) {}

  static create(amount: number, currency: string): Money {
    if (amount < 0) {
      throw new DomainError('Amount cannot be negative');
    }
    return new Money(amount, currency);
  }

  static zero(currency: string): Money {
    return new Money(0, currency);
  }

  get amount(): number { return this._amount; }
  get currency(): string { return this._currency; }

  add(other: Money): Money {
    this.ensureSameCurrency(other);
    return new Money(this._amount + other._amount, this._currency);
  }

  multiply(factor: number): Money {
    return new Money(this._amount * factor, this._currency);
  }

  private ensureSameCurrency(other: Money): void {
    if (this._currency !== other._currency) {
      throw new DomainError('Currency mismatch');
    }
  }
}
```

### Domain Layer (Repository Interface)

```typescript
// domain/repositories/order.repository.ts
import { Order } from '../entities/order';

// Interface only - no implementation details!
export interface OrderRepository {
  save(order: Order): Promise<void>;
  findById(id: string): Promise<Order | null>;
  findByCustomerId(customerId: string): Promise<Order[]>;
  delete(id: string): Promise<void>;
}
```

### Application Layer (Use Case)

```typescript
// application/use-cases/order/create-order.ts
import { Order, OrderItem } from '@/domain/entities/order';
import { OrderRepository } from '@/domain/repositories/order.repository';
import { ProductRepository } from '@/domain/repositories/product.repository';
import { EventPublisher } from '@/application/interfaces/event-publisher';
import { CreateOrderDTO, OrderResponseDTO } from '@/application/dtos/order.dto';
import { OrderMapper } from '@/application/mappers/order.mapper';

export class CreateOrderUseCase {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly productRepository: ProductRepository,
    private readonly eventPublisher: EventPublisher
  ) {}

  async execute(dto: CreateOrderDTO): Promise<OrderResponseDTO> {
    // 1. Validate products exist and have stock
    const orderItems = await Promise.all(
      dto.items.map(async (item) => {
        const product = await this.productRepository.findById(item.productId);
        if (!product) {
          throw new Error(`Product ${item.productId} not found`);
        }
        if (!product.hasStock(item.quantity)) {
          throw new Error(`Insufficient stock for ${product.name}`);
        }
        return OrderItem.create(product, item.quantity);
      })
    );

    // 2. Create order (domain logic)
    const order = Order.create(dto.customerId, orderItems);

    // 3. Persist
    await this.orderRepository.save(order);

    // 4. Publish event
    await this.eventPublisher.publish({
      type: 'ORDER_CREATED',
      payload: { orderId: order.id, customerId: order.customerId }
    });

    // 5. Return DTO (not entity!)
    return OrderMapper.toDTO(order);
  }
}
```

### Infrastructure Layer (Repository Implementation)

```typescript
// infrastructure/persistence/prisma/order.repository.impl.ts
import { PrismaClient } from '@prisma/client';
import { Order } from '@/domain/entities/order';
import { OrderRepository } from '@/domain/repositories/order.repository';
import { OrderMapper } from './mappers/order.mapper';

export class PrismaOrderRepository implements OrderRepository {
  constructor(private readonly prisma: PrismaClient) {}

  async save(order: Order): Promise<void> {
    const data = OrderMapper.toPersistence(order);

    await this.prisma.order.upsert({
      where: { id: order.id },
      create: data,
      update: data,
    });
  }

  async findById(id: string): Promise<Order | null> {
    const record = await this.prisma.order.findUnique({
      where: { id },
      include: { items: true },
    });

    return record ? OrderMapper.toDomain(record) : null;
  }

  async findByCustomerId(customerId: string): Promise<Order[]> {
    const records = await this.prisma.order.findMany({
      where: { customerId },
      include: { items: true },
      orderBy: { createdAt: 'desc' },
    });

    return records.map(OrderMapper.toDomain);
  }

  async delete(id: string): Promise<void> {
    await this.prisma.order.delete({ where: { id } });
  }
}
```

### Presentation Layer (Controller)

```typescript
// presentation/http/controllers/order.controller.ts
import { Controller, Post, Get, Body, Param } from '@nestjs/common';
import { CreateOrderUseCase } from '@/application/use-cases/order/create-order';
import { GetOrderUseCase } from '@/application/use-cases/order/get-order';
import { CreateOrderDTO } from '@/application/dtos/order.dto';

@Controller('orders')
export class OrderController {
  constructor(
    private readonly createOrder: CreateOrderUseCase,
    private readonly getOrder: GetOrderUseCase
  ) {}

  @Post()
  async create(@Body() dto: CreateOrderDTO) {
    return this.createOrder.execute(dto);
  }

  @Get(':id')
  async findOne(@Param('id') id: string) {
    return this.getOrder.execute(id);
  }
}
```

## Dependency Injection Setup

```typescript
// infrastructure/di/container.ts
import { Container } from 'inversify';
import { OrderRepository } from '@/domain/repositories/order.repository';
import { PrismaOrderRepository } from '@/infrastructure/persistence/prisma/order.repository.impl';
import { CreateOrderUseCase } from '@/application/use-cases/order/create-order';

const container = new Container();

// Bind interfaces to implementations
container.bind<OrderRepository>('OrderRepository').to(PrismaOrderRepository);
container.bind<CreateOrderUseCase>(CreateOrderUseCase).toSelf();

export { container };
```

## The Dependency Rule

```
OUTER layers can depend on INNER layers
INNER layers NEVER depend on OUTER layers

✅ Controller → Use Case → Entity
✅ Repository Impl → Repository Interface
❌ Entity → Repository Implementation
❌ Use Case → Controller
```

## Benefits

| Benefit | Description |
|---------|-------------|
| Testability | Business logic easily unit tested |
| Flexibility | Swap implementations without affecting core |
| Maintainability | Clear separation of concerns |
| Independence | Framework/database agnostic core |

## Rules Summary

1. **Dependencies point inward** - Outer layers depend on inner, never reverse
2. **Domain has no dependencies** - Pure business logic only
3. **Use interfaces at boundaries** - Define contracts in inner layers
4. **DTOs cross boundaries** - Never expose domain entities
5. **Framework code in outer layers** - Keep frameworks out of domain
