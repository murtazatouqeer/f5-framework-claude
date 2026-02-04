---
name: hexagonal-architecture
description: Ports and Adapters pattern for flexible system boundaries
category: architecture/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Hexagonal Architecture (Ports & Adapters)

## Overview

Hexagonal Architecture, also known as Ports and Adapters, isolates the
application core from external concerns through well-defined interfaces.

## Core Concepts

```
                    Driving Adapters (Primary)
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ▼              ▼              ▼
       ┌─────────┐   ┌─────────┐   ┌─────────┐
       │  HTTP   │   │  CLI    │   │  Events │
       │ Adapter │   │ Adapter │   │ Adapter │
       └────┬────┘   └────┬────┘   └────┬────┘
            │             │             │
            └──────┬──────┴──────┬──────┘
                   │             │
              ┌────▼─────────────▼────┐
              │    Driving Ports      │
              │    (Input Ports)      │
              ├───────────────────────┤
              │                       │
              │    APPLICATION        │
              │       CORE            │
              │    (Domain Logic)     │
              │                       │
              ├───────────────────────┤
              │    Driven Ports       │
              │   (Output Ports)      │
              └────┬─────────────┬────┘
                   │             │
            ┌──────┴──────┬──────┴──────┐
            │             │             │
       ┌────▼────┐   ┌────▼────┐   ┌────▼────┐
       │Database │   │  Email  │   │ Payment │
       │ Adapter │   │ Adapter │   │ Adapter │
       └─────────┘   └─────────┘   └─────────┘
            │              │              │
            ▼              ▼              ▼
                  Driven Adapters (Secondary)
```

## Directory Structure

```
src/
├── core/                          # Application Core
│   ├── domain/
│   │   ├── entities/
│   │   │   └── order.ts
│   │   ├── value-objects/
│   │   │   └── money.ts
│   │   └── services/
│   │       └── pricing.service.ts
│   │
│   ├── ports/
│   │   ├── driving/               # Input ports (use cases)
│   │   │   ├── create-order.port.ts
│   │   │   ├── get-order.port.ts
│   │   │   └── cancel-order.port.ts
│   │   │
│   │   └── driven/                # Output ports (interfaces)
│   │       ├── order.repository.port.ts
│   │       ├── payment.gateway.port.ts
│   │       ├── notification.port.ts
│   │       └── event-publisher.port.ts
│   │
│   └── application/               # Use case implementations
│       ├── create-order.service.ts
│       ├── get-order.service.ts
│       └── cancel-order.service.ts
│
└── adapters/                      # All adapters
    ├── driving/                   # Primary adapters (input)
    │   ├── http/
    │   │   ├── controllers/
    │   │   │   └── order.controller.ts
    │   │   └── middlewares/
    │   ├── graphql/
    │   │   └── resolvers/
    │   ├── cli/
    │   │   └── commands/
    │   └── events/
    │       └── order-event.handler.ts
    │
    └── driven/                    # Secondary adapters (output)
        ├── persistence/
        │   ├── postgres/
        │   │   └── order.repository.ts
        │   └── mongodb/
        │       └── order.repository.ts
        ├── payment/
        │   ├── stripe.adapter.ts
        │   └── paypal.adapter.ts
        ├── notification/
        │   ├── email.adapter.ts
        │   └── sms.adapter.ts
        └── messaging/
            └── rabbitmq.publisher.ts
```

## Implementation

### Driving Port (Input Port)

```typescript
// core/ports/driving/create-order.port.ts
export interface CreateOrderPort {
  execute(command: CreateOrderCommand): Promise<OrderResult>;
}

export interface CreateOrderCommand {
  customerId: string;
  items: Array<{
    productId: string;
    quantity: number;
  }>;
  shippingAddress: Address;
}

export interface OrderResult {
  orderId: string;
  total: number;
  status: string;
}
```

### Driven Port (Output Port)

```typescript
// core/ports/driven/order.repository.port.ts
import { Order } from '../../domain/entities/order';

export interface OrderRepositoryPort {
  save(order: Order): Promise<void>;
  findById(id: string): Promise<Order | null>;
  findByCustomerId(customerId: string): Promise<Order[]>;
  nextId(): string;
}

// core/ports/driven/payment.gateway.port.ts
export interface PaymentGatewayPort {
  charge(params: ChargeParams): Promise<ChargeResult>;
  refund(chargeId: string, amount?: number): Promise<RefundResult>;
}

export interface ChargeParams {
  amount: number;
  currency: string;
  customerId: string;
  description?: string;
}

export interface ChargeResult {
  chargeId: string;
  status: 'succeeded' | 'pending' | 'failed';
  amount: number;
}
```

### Application Service (Use Case Implementation)

```typescript
// core/application/create-order.service.ts
import { CreateOrderPort, CreateOrderCommand, OrderResult } from '../ports/driving/create-order.port';
import { OrderRepositoryPort } from '../ports/driven/order.repository.port';
import { ProductRepositoryPort } from '../ports/driven/product.repository.port';
import { PaymentGatewayPort } from '../ports/driven/payment.gateway.port';
import { EventPublisherPort } from '../ports/driven/event-publisher.port';
import { Order } from '../domain/entities/order';
import { OrderItem } from '../domain/entities/order-item';

export class CreateOrderService implements CreateOrderPort {
  constructor(
    private readonly orderRepository: OrderRepositoryPort,
    private readonly productRepository: ProductRepositoryPort,
    private readonly paymentGateway: PaymentGatewayPort,
    private readonly eventPublisher: EventPublisherPort
  ) {}

  async execute(command: CreateOrderCommand): Promise<OrderResult> {
    // 1. Fetch products and validate
    const products = await Promise.all(
      command.items.map(item =>
        this.productRepository.findById(item.productId)
      )
    );

    // 2. Create domain entity
    const orderItems = command.items.map((item, index) => {
      const product = products[index];
      if (!product) throw new ProductNotFoundError(item.productId);
      return OrderItem.create(product, item.quantity);
    });

    const order = Order.create(
      this.orderRepository.nextId(),
      command.customerId,
      orderItems,
      command.shippingAddress
    );

    // 3. Process payment
    const paymentResult = await this.paymentGateway.charge({
      amount: order.total.amount,
      currency: order.total.currency,
      customerId: command.customerId,
      description: `Order ${order.id}`,
    });

    if (paymentResult.status === 'failed') {
      throw new PaymentFailedError(paymentResult);
    }

    order.markAsPaid(paymentResult.chargeId);

    // 4. Persist
    await this.orderRepository.save(order);

    // 5. Publish events
    await this.eventPublisher.publish({
      type: 'ORDER_CREATED',
      payload: {
        orderId: order.id,
        customerId: order.customerId,
        total: order.total.amount,
      },
    });

    return {
      orderId: order.id,
      total: order.total.amount,
      status: order.status,
    };
  }
}
```

### Driving Adapter (HTTP Controller)

```typescript
// adapters/driving/http/controllers/order.controller.ts
import { Controller, Post, Get, Body, Param, Inject } from '@nestjs/common';
import { CreateOrderPort } from '@/core/ports/driving/create-order.port';
import { GetOrderPort } from '@/core/ports/driving/get-order.port';
import { CreateOrderRequest, OrderResponse } from './dtos';

@Controller('orders')
export class OrderController {
  constructor(
    @Inject('CreateOrderPort') private readonly createOrder: CreateOrderPort,
    @Inject('GetOrderPort') private readonly getOrder: GetOrderPort
  ) {}

  @Post()
  async create(@Body() request: CreateOrderRequest): Promise<OrderResponse> {
    // Transform HTTP request to port command
    const command = {
      customerId: request.customer_id,
      items: request.items.map(item => ({
        productId: item.product_id,
        quantity: item.quantity,
      })),
      shippingAddress: {
        street: request.shipping.street,
        city: request.shipping.city,
        zipCode: request.shipping.zip_code,
        country: request.shipping.country,
      },
    };

    const result = await this.createOrder.execute(command);

    // Transform port result to HTTP response
    return {
      order_id: result.orderId,
      total: result.total,
      status: result.status,
    };
  }

  @Get(':id')
  async findOne(@Param('id') id: string): Promise<OrderResponse> {
    const result = await this.getOrder.execute({ orderId: id });
    return {
      order_id: result.orderId,
      total: result.total,
      status: result.status,
    };
  }
}
```

### Driven Adapter (Repository)

```typescript
// adapters/driven/persistence/postgres/order.repository.ts
import { Injectable } from '@nestjs/common';
import { Pool } from 'pg';
import { OrderRepositoryPort } from '@/core/ports/driven/order.repository.port';
import { Order } from '@/core/domain/entities/order';
import { OrderMapper } from './mappers/order.mapper';

@Injectable()
export class PostgresOrderRepository implements OrderRepositoryPort {
  constructor(private readonly pool: Pool) {}

  async save(order: Order): Promise<void> {
    const data = OrderMapper.toPersistence(order);

    await this.pool.query(
      `INSERT INTO orders (id, customer_id, status, total_amount, total_currency, created_at)
       VALUES ($1, $2, $3, $4, $5, $6)
       ON CONFLICT (id) DO UPDATE SET
         status = $3,
         total_amount = $4,
         updated_at = NOW()`,
      [data.id, data.customerId, data.status, data.totalAmount, data.totalCurrency, data.createdAt]
    );

    // Save order items
    for (const item of data.items) {
      await this.pool.query(
        `INSERT INTO order_items (id, order_id, product_id, quantity, price)
         VALUES ($1, $2, $3, $4, $5)
         ON CONFLICT (id) DO NOTHING`,
        [item.id, data.id, item.productId, item.quantity, item.price]
      );
    }
  }

  async findById(id: string): Promise<Order | null> {
    const orderResult = await this.pool.query(
      'SELECT * FROM orders WHERE id = $1',
      [id]
    );

    if (orderResult.rows.length === 0) return null;

    const itemsResult = await this.pool.query(
      'SELECT * FROM order_items WHERE order_id = $1',
      [id]
    );

    return OrderMapper.toDomain(orderResult.rows[0], itemsResult.rows);
  }

  async findByCustomerId(customerId: string): Promise<Order[]> {
    const result = await this.pool.query(
      `SELECT o.*, json_agg(oi.*) as items
       FROM orders o
       LEFT JOIN order_items oi ON o.id = oi.order_id
       WHERE o.customer_id = $1
       GROUP BY o.id
       ORDER BY o.created_at DESC`,
      [customerId]
    );

    return result.rows.map(row => OrderMapper.toDomain(row, row.items));
  }

  nextId(): string {
    return crypto.randomUUID();
  }
}
```

### Driven Adapter (Payment Gateway)

```typescript
// adapters/driven/payment/stripe.adapter.ts
import Stripe from 'stripe';
import { PaymentGatewayPort, ChargeParams, ChargeResult } from '@/core/ports/driven/payment.gateway.port';

export class StripePaymentAdapter implements PaymentGatewayPort {
  private stripe: Stripe;

  constructor(apiKey: string) {
    this.stripe = new Stripe(apiKey, { apiVersion: '2023-10-16' });
  }

  async charge(params: ChargeParams): Promise<ChargeResult> {
    try {
      const paymentIntent = await this.stripe.paymentIntents.create({
        amount: Math.round(params.amount * 100), // Convert to cents
        currency: params.currency.toLowerCase(),
        customer: params.customerId,
        description: params.description,
        confirm: true,
        automatic_payment_methods: {
          enabled: true,
          allow_redirects: 'never',
        },
      });

      return {
        chargeId: paymentIntent.id,
        status: paymentIntent.status === 'succeeded' ? 'succeeded' : 'pending',
        amount: params.amount,
      };
    } catch (error) {
      return {
        chargeId: '',
        status: 'failed',
        amount: params.amount,
      };
    }
  }

  async refund(chargeId: string, amount?: number): Promise<RefundResult> {
    const refund = await this.stripe.refunds.create({
      payment_intent: chargeId,
      amount: amount ? Math.round(amount * 100) : undefined,
    });

    return {
      refundId: refund.id,
      status: refund.status === 'succeeded' ? 'succeeded' : 'failed',
      amount: refund.amount / 100,
    };
  }
}
```

## Wiring It Together

```typescript
// adapters/config/dependency-injection.ts
import { Module } from '@nestjs/common';

// Ports
import { CreateOrderPort } from '@/core/ports/driving/create-order.port';
import { OrderRepositoryPort } from '@/core/ports/driven/order.repository.port';
import { PaymentGatewayPort } from '@/core/ports/driven/payment.gateway.port';

// Application services
import { CreateOrderService } from '@/core/application/create-order.service';

// Adapters
import { PostgresOrderRepository } from '@/adapters/driven/persistence/postgres/order.repository';
import { StripePaymentAdapter } from '@/adapters/driven/payment/stripe.adapter';
import { OrderController } from '@/adapters/driving/http/controllers/order.controller';

@Module({
  controllers: [OrderController],
  providers: [
    // Driven adapters
    {
      provide: 'OrderRepositoryPort',
      useClass: PostgresOrderRepository,
    },
    {
      provide: 'PaymentGatewayPort',
      useFactory: () => new StripePaymentAdapter(process.env.STRIPE_KEY!),
    },

    // Driving ports (use cases)
    {
      provide: 'CreateOrderPort',
      useFactory: (orderRepo, paymentGateway) =>
        new CreateOrderService(orderRepo, paymentGateway),
      inject: ['OrderRepositoryPort', 'PaymentGatewayPort'],
    },
  ],
})
export class OrderModule {}
```

## Key Differences from Clean Architecture

| Aspect | Clean Architecture | Hexagonal |
|--------|-------------------|-----------|
| Focus | Layers | Ports & Adapters |
| Terminology | Use Cases | Driving/Driven Ports |
| Structure | Concentric circles | Hexagon with adapters |
| Emphasis | Dependency direction | System boundaries |

## Benefits

| Benefit | Description |
|---------|-------------|
| Testability | Core can be tested without adapters |
| Flexibility | Swap adapters without changing core |
| Clarity | Clear system boundaries |
| Independence | Framework/infrastructure agnostic |
