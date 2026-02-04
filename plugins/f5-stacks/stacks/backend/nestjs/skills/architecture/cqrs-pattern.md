---
name: nestjs-cqrs-pattern
description: CQRS (Command Query Responsibility Segregation) in NestJS
applies_to: nestjs
category: architecture
---

# CQRS Pattern in NestJS

## Overview

CQRS separates read and write operations into different models.
NestJS provides @nestjs/cqrs package for implementing this pattern.

## When to Use

- Complex domain with different read/write needs
- Event-driven architecture
- Need for audit trail / event sourcing
- High read-to-write ratio
- Different scaling needs for reads vs writes
- Collaborative domains with complex workflows

## Installation

```bash
npm install @nestjs/cqrs
```

## Structure

```
src/modules/orders/
├── commands/
│   ├── handlers/
│   │   ├── create-order.handler.ts
│   │   ├── cancel-order.handler.ts
│   │   └── index.ts
│   └── impl/
│       ├── create-order.command.ts
│       ├── cancel-order.command.ts
│       └── index.ts
├── queries/
│   ├── handlers/
│   │   ├── get-order.handler.ts
│   │   ├── get-orders.handler.ts
│   │   └── index.ts
│   └── impl/
│       ├── get-order.query.ts
│       ├── get-orders.query.ts
│       └── index.ts
├── events/
│   ├── handlers/
│   │   ├── order-created.handler.ts
│   │   └── index.ts
│   └── impl/
│       ├── order-created.event.ts
│       └── index.ts
├── sagas/
│   └── orders.saga.ts
├── dto/
├── entities/
└── orders.module.ts
```

## Implementation

### Commands (Write Operations)

Commands represent intention to change state.

```typescript
// commands/impl/create-order.command.ts
export class CreateOrderCommand {
  constructor(
    public readonly customerId: string,
    public readonly items: CreateOrderItemDto[],
    public readonly shippingAddress: AddressDto,
  ) {}
}

export interface CreateOrderItemDto {
  productId: string;
  quantity: number;
  unitPrice: number;
}

export interface AddressDto {
  street: string;
  city: string;
  postalCode: string;
  country: string;
}

// commands/impl/cancel-order.command.ts
export class CancelOrderCommand {
  constructor(
    public readonly orderId: string,
    public readonly reason: string,
    public readonly cancelledBy: string,
  ) {}
}

// commands/handlers/create-order.handler.ts
import { CommandHandler, ICommandHandler, EventBus } from '@nestjs/cqrs';
import { CreateOrderCommand } from '../impl/create-order.command';
import { OrderRepository } from '../../repositories/order.repository';
import { Order } from '../../domain/order.aggregate';
import { OrderCreatedEvent } from '../../events/impl/order-created.event';

@CommandHandler(CreateOrderCommand)
export class CreateOrderHandler implements ICommandHandler<CreateOrderCommand> {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly eventBus: EventBus,
  ) {}

  async execute(command: CreateOrderCommand): Promise<string> {
    const { customerId, items, shippingAddress } = command;

    // Create order aggregate (domain logic)
    const order = Order.create({
      customerId,
      items: items.map(item => ({
        productId: item.productId,
        quantity: item.quantity,
        unitPrice: item.unitPrice,
      })),
      shippingAddress,
    });

    // Persist
    await this.orderRepository.save(order);

    // Publish domain event
    this.eventBus.publish(
      new OrderCreatedEvent(
        order.id,
        order.customerId,
        order.totalAmount,
        order.items,
        order.createdAt,
      ),
    );

    return order.id;
  }
}

// commands/handlers/cancel-order.handler.ts
import { CommandHandler, ICommandHandler, EventBus } from '@nestjs/cqrs';
import { CancelOrderCommand } from '../impl/cancel-order.command';
import { OrderRepository } from '../../repositories/order.repository';
import { OrderCancelledEvent } from '../../events/impl/order-cancelled.event';
import { NotFoundException, BadRequestException } from '@nestjs/common';

@CommandHandler(CancelOrderCommand)
export class CancelOrderHandler implements ICommandHandler<CancelOrderCommand> {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly eventBus: EventBus,
  ) {}

  async execute(command: CancelOrderCommand): Promise<void> {
    const { orderId, reason, cancelledBy } = command;

    const order = await this.orderRepository.findById(orderId);

    if (!order) {
      throw new NotFoundException(`Order ${orderId} not found`);
    }

    // Domain logic - validates cancellation is allowed
    order.cancel(reason, cancelledBy);

    await this.orderRepository.save(order);

    this.eventBus.publish(
      new OrderCancelledEvent(orderId, reason, cancelledBy, new Date()),
    );
  }
}
```

### Queries (Read Operations)

Queries retrieve data without modifying state.

```typescript
// queries/impl/get-order.query.ts
export class GetOrderQuery {
  constructor(public readonly orderId: string) {}
}

// queries/impl/get-orders.query.ts
export class GetOrdersQuery {
  constructor(
    public readonly customerId?: string,
    public readonly status?: string,
    public readonly page: number = 1,
    public readonly limit: number = 10,
  ) {}
}

// queries/handlers/get-order.handler.ts
import { IQueryHandler, QueryHandler } from '@nestjs/cqrs';
import { GetOrderQuery } from '../impl/get-order.query';
import { OrderReadRepository } from '../../repositories/order-read.repository';
import { OrderDto } from '../../dto/order.dto';
import { NotFoundException } from '@nestjs/common';

@QueryHandler(GetOrderQuery)
export class GetOrderHandler implements IQueryHandler<GetOrderQuery> {
  constructor(private readonly orderReadRepo: OrderReadRepository) {}

  async execute(query: GetOrderQuery): Promise<OrderDto> {
    const order = await this.orderReadRepo.findById(query.orderId);

    if (!order) {
      throw new NotFoundException(`Order ${query.orderId} not found`);
    }

    return order;
  }
}

// queries/handlers/get-orders.handler.ts
import { IQueryHandler, QueryHandler } from '@nestjs/cqrs';
import { GetOrdersQuery } from '../impl/get-orders.query';
import { OrderReadRepository } from '../../repositories/order-read.repository';
import { PaginatedOrdersDto } from '../../dto/paginated-orders.dto';

@QueryHandler(GetOrdersQuery)
export class GetOrdersHandler implements IQueryHandler<GetOrdersQuery> {
  constructor(private readonly orderReadRepo: OrderReadRepository) {}

  async execute(query: GetOrdersQuery): Promise<PaginatedOrdersDto> {
    const { customerId, status, page, limit } = query;

    const [orders, total] = await this.orderReadRepo.findMany({
      customerId,
      status,
      skip: (page - 1) * limit,
      take: limit,
    });

    return {
      items: orders,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }
}
```

### Events

Events represent facts that happened.

```typescript
// events/impl/order-created.event.ts
export class OrderCreatedEvent {
  constructor(
    public readonly orderId: string,
    public readonly customerId: string,
    public readonly totalAmount: number,
    public readonly items: OrderItemSnapshot[],
    public readonly createdAt: Date,
  ) {}
}

export interface OrderItemSnapshot {
  productId: string;
  productName: string;
  quantity: number;
  unitPrice: number;
}

// events/impl/order-cancelled.event.ts
export class OrderCancelledEvent {
  constructor(
    public readonly orderId: string,
    public readonly reason: string,
    public readonly cancelledBy: string,
    public readonly cancelledAt: Date,
  ) {}
}

// events/handlers/order-created.handler.ts
import { EventsHandler, IEventHandler } from '@nestjs/cqrs';
import { OrderCreatedEvent } from '../impl/order-created.event';
import { NotificationService } from '../../../notifications/notification.service';
import { InventoryService } from '../../../inventory/inventory.service';
import { AnalyticsService } from '../../../analytics/analytics.service';

@EventsHandler(OrderCreatedEvent)
export class OrderCreatedHandler implements IEventHandler<OrderCreatedEvent> {
  constructor(
    private readonly notificationService: NotificationService,
    private readonly inventoryService: InventoryService,
    private readonly analyticsService: AnalyticsService,
  ) {}

  async handle(event: OrderCreatedEvent): Promise<void> {
    // These can run in parallel
    await Promise.all([
      // Send confirmation email
      this.notificationService.sendOrderConfirmation(
        event.orderId,
        event.customerId,
      ),

      // Reserve inventory
      this.inventoryService.reserveItems(
        event.orderId,
        event.items.map(item => ({
          productId: item.productId,
          quantity: item.quantity,
        })),
      ),

      // Track analytics
      this.analyticsService.trackOrderCreated({
        orderId: event.orderId,
        customerId: event.customerId,
        totalAmount: event.totalAmount,
        itemCount: event.items.length,
      }),
    ]);
  }
}

// events/handlers/order-cancelled.handler.ts
@EventsHandler(OrderCancelledEvent)
export class OrderCancelledHandler implements IEventHandler<OrderCancelledEvent> {
  constructor(
    private readonly notificationService: NotificationService,
    private readonly inventoryService: InventoryService,
    private readonly refundService: RefundService,
  ) {}

  async handle(event: OrderCancelledEvent): Promise<void> {
    await Promise.all([
      this.notificationService.sendCancellationNotice(event.orderId),
      this.inventoryService.releaseReservation(event.orderId),
      this.refundService.initiateRefund(event.orderId),
    ]);
  }
}
```

### Sagas (Process Managers)

Sagas orchestrate complex workflows across multiple aggregates.

```typescript
// sagas/orders.saga.ts
import { Injectable } from '@nestjs/common';
import { Saga, ICommand, ofType } from '@nestjs/cqrs';
import { Observable, map, filter, delay } from 'rxjs';
import { OrderCreatedEvent } from '../events/impl/order-created.event';
import { PaymentCompletedEvent } from '../../payments/events/payment-completed.event';
import { PaymentFailedEvent } from '../../payments/events/payment-failed.event';
import { ProcessPaymentCommand } from '../../payments/commands/process-payment.command';
import { ShipOrderCommand } from '../commands/impl/ship-order.command';
import { CancelOrderCommand } from '../commands/impl/cancel-order.command';

@Injectable()
export class OrdersSaga {
  // When order created, initiate payment
  @Saga()
  orderCreated = (events$: Observable<any>): Observable<ICommand> => {
    return events$.pipe(
      ofType(OrderCreatedEvent),
      map((event) => {
        return new ProcessPaymentCommand(
          event.orderId,
          event.customerId,
          event.totalAmount,
        );
      }),
    );
  };

  // When payment completed, ship order
  @Saga()
  paymentCompleted = (events$: Observable<any>): Observable<ICommand> => {
    return events$.pipe(
      ofType(PaymentCompletedEvent),
      delay(1000), // Small delay to ensure order is updated
      map((event) => {
        return new ShipOrderCommand(event.orderId);
      }),
    );
  };

  // When payment failed, cancel order
  @Saga()
  paymentFailed = (events$: Observable<any>): Observable<ICommand> => {
    return events$.pipe(
      ofType(PaymentFailedEvent),
      map((event) => {
        return new CancelOrderCommand(
          event.orderId,
          `Payment failed: ${event.reason}`,
          'system',
        );
      }),
    );
  };
}
```

### Domain Aggregate (For Complex Business Logic)

```typescript
// domain/order.aggregate.ts
import { AggregateRoot } from '@nestjs/cqrs';
import { OrderCreatedEvent } from '../events/impl/order-created.event';
import { OrderCancelledEvent } from '../events/impl/order-cancelled.event';

export enum OrderStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  PAID = 'paid',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
}

export class Order extends AggregateRoot {
  public id: string;
  public customerId: string;
  public items: OrderItem[];
  public shippingAddress: Address;
  public status: OrderStatus;
  public totalAmount: number;
  public createdAt: Date;
  public updatedAt: Date;

  static create(props: CreateOrderProps): Order {
    const order = new Order();
    order.id = generateId();
    order.customerId = props.customerId;
    order.items = props.items.map(item => new OrderItem(item));
    order.shippingAddress = new Address(props.shippingAddress);
    order.status = OrderStatus.PENDING;
    order.totalAmount = order.calculateTotal();
    order.createdAt = new Date();
    order.updatedAt = new Date();

    // Apply event (for event sourcing compatibility)
    order.apply(
      new OrderCreatedEvent(
        order.id,
        order.customerId,
        order.totalAmount,
        order.items.map(i => i.toSnapshot()),
        order.createdAt,
      ),
    );

    return order;
  }

  cancel(reason: string, cancelledBy: string): void {
    if (this.status === OrderStatus.SHIPPED) {
      throw new Error('Cannot cancel shipped order');
    }

    if (this.status === OrderStatus.DELIVERED) {
      throw new Error('Cannot cancel delivered order');
    }

    if (this.status === OrderStatus.CANCELLED) {
      throw new Error('Order is already cancelled');
    }

    this.status = OrderStatus.CANCELLED;
    this.updatedAt = new Date();

    this.apply(
      new OrderCancelledEvent(this.id, reason, cancelledBy, new Date()),
    );
  }

  confirm(): void {
    if (this.status !== OrderStatus.PENDING) {
      throw new Error('Can only confirm pending orders');
    }
    this.status = OrderStatus.CONFIRMED;
    this.updatedAt = new Date();
  }

  markPaid(): void {
    if (this.status !== OrderStatus.CONFIRMED) {
      throw new Error('Can only mark confirmed orders as paid');
    }
    this.status = OrderStatus.PAID;
    this.updatedAt = new Date();
  }

  ship(): void {
    if (this.status !== OrderStatus.PAID) {
      throw new Error('Can only ship paid orders');
    }
    this.status = OrderStatus.SHIPPED;
    this.updatedAt = new Date();
  }

  private calculateTotal(): number {
    return this.items.reduce(
      (sum, item) => sum + item.quantity * item.unitPrice,
      0,
    );
  }
}
```

### Module Setup

```typescript
// orders.module.ts
import { Module } from '@nestjs/common';
import { CqrsModule } from '@nestjs/cqrs';
import { TypeOrmModule } from '@nestjs/typeorm';

// Controllers
import { OrdersController } from './orders.controller';

// Command Handlers
import { CreateOrderHandler } from './commands/handlers/create-order.handler';
import { CancelOrderHandler } from './commands/handlers/cancel-order.handler';

// Query Handlers
import { GetOrderHandler } from './queries/handlers/get-order.handler';
import { GetOrdersHandler } from './queries/handlers/get-orders.handler';

// Event Handlers
import { OrderCreatedHandler } from './events/handlers/order-created.handler';
import { OrderCancelledHandler } from './events/handlers/order-cancelled.handler';

// Sagas
import { OrdersSaga } from './sagas/orders.saga';

// Repositories
import { OrderRepository } from './repositories/order.repository';
import { OrderReadRepository } from './repositories/order-read.repository';

// Entities
import { OrderEntity } from './entities/order.entity';
import { OrderItemEntity } from './entities/order-item.entity';

const CommandHandlers = [CreateOrderHandler, CancelOrderHandler];
const QueryHandlers = [GetOrderHandler, GetOrdersHandler];
const EventHandlers = [OrderCreatedHandler, OrderCancelledHandler];
const Sagas = [OrdersSaga];

@Module({
  imports: [
    CqrsModule,
    TypeOrmModule.forFeature([OrderEntity, OrderItemEntity]),
  ],
  controllers: [OrdersController],
  providers: [
    ...CommandHandlers,
    ...QueryHandlers,
    ...EventHandlers,
    ...Sagas,
    OrderRepository,
    OrderReadRepository,
  ],
  exports: [OrderRepository],
})
export class OrdersModule {}
```

### Controller Usage

```typescript
// orders.controller.ts
import { Controller, Post, Get, Patch, Body, Param, Query } from '@nestjs/common';
import { CommandBus, QueryBus } from '@nestjs/cqrs';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { CreateOrderCommand } from './commands/impl/create-order.command';
import { CancelOrderCommand } from './commands/impl/cancel-order.command';
import { GetOrderQuery } from './queries/impl/get-order.query';
import { GetOrdersQuery } from './queries/impl/get-orders.query';
import { CreateOrderDto } from './dto/create-order.dto';
import { CancelOrderDto } from './dto/cancel-order.dto';
import { OrderQueryDto } from './dto/order-query.dto';

@ApiTags('Orders')
@Controller('orders')
export class OrdersController {
  constructor(
    private readonly commandBus: CommandBus,
    private readonly queryBus: QueryBus,
  ) {}

  @Post()
  @ApiOperation({ summary: 'Create order' })
  async createOrder(@Body() dto: CreateOrderDto): Promise<{ id: string }> {
    const orderId = await this.commandBus.execute(
      new CreateOrderCommand(
        dto.customerId,
        dto.items,
        dto.shippingAddress,
      ),
    );
    return { id: orderId };
  }

  @Get()
  @ApiOperation({ summary: 'Get orders' })
  async getOrders(@Query() query: OrderQueryDto) {
    return this.queryBus.execute(
      new GetOrdersQuery(
        query.customerId,
        query.status,
        query.page,
        query.limit,
      ),
    );
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get order by ID' })
  async getOrder(@Param('id') id: string) {
    return this.queryBus.execute(new GetOrderQuery(id));
  }

  @Patch(':id/cancel')
  @ApiOperation({ summary: 'Cancel order' })
  async cancelOrder(
    @Param('id') id: string,
    @Body() dto: CancelOrderDto,
  ): Promise<void> {
    await this.commandBus.execute(
      new CancelOrderCommand(id, dto.reason, dto.cancelledBy),
    );
  }
}
```

## Best Practices

1. **Commands return minimal data** (usually just ID or void)
2. **Queries return DTOs**, not domain entities
3. **Events are immutable facts** that happened
4. **Sagas handle cross-aggregate workflows**
5. **Keep read models eventually consistent**
6. **Name commands as imperative** (CreateOrder, CancelOrder)
7. **Name events as past tense** (OrderCreated, OrderCancelled)
8. **One handler per command/query/event**

## Checklist

- [ ] Commands named as verbs (CreateOrder, CancelOrder)
- [ ] Queries named as questions (GetOrder, FindOrders)
- [ ] Events named as past tense (OrderCreated, OrderCancelled)
- [ ] Handlers are single responsibility
- [ ] Read/write models separated if needed
- [ ] Sagas for cross-aggregate coordination
- [ ] Events are immutable
- [ ] Commands validate input
