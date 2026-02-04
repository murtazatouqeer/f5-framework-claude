---
name: microservices
description: Microservices architecture patterns and best practices
category: architecture/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Microservices Architecture

## Overview

Microservices architecture structures an application as a collection of
loosely coupled, independently deployable services organized around
business capabilities.

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        API Gateway                                │
│              (Routing, Auth, Rate Limiting)                       │
└─────────────┬──────────────┬──────────────┬─────────────────────┘
              │              │              │
    ┌─────────▼──────┐ ┌─────▼──────┐ ┌────▼───────┐
    │ User Service   │ │Order Service│ │Product Svc │
    │                │ │             │ │            │
    │  ┌──────────┐  │ │ ┌────────┐ │ │ ┌────────┐ │
    │  │ User DB  │  │ │ │Order DB│ │ │ │Prod DB │ │
    │  └──────────┘  │ │ └────────┘ │ │ └────────┘ │
    └───────┬────────┘ └─────┬──────┘ └──────┬─────┘
            │                │               │
            └────────────────┼───────────────┘
                             │
              ┌──────────────▼──────────────┐
              │       Message Broker         │
              │   (Events, Async Comm)       │
              └──────────────────────────────┘
```

## Service Design

### Service Structure

```
services/
├── user-service/
│   ├── src/
│   │   ├── domain/
│   │   │   ├── entities/
│   │   │   └── events/
│   │   ├── application/
│   │   │   ├── commands/
│   │   │   └── queries/
│   │   ├── infrastructure/
│   │   │   ├── persistence/
│   │   │   └── messaging/
│   │   └── api/
│   │       ├── http/
│   │       └── grpc/
│   ├── tests/
│   ├── Dockerfile
│   └── package.json
│
├── order-service/
├── product-service/
├── payment-service/
└── notification-service/
```

### Service Implementation

```typescript
// order-service/src/application/commands/create-order.handler.ts
export class CreateOrderHandler {
  constructor(
    private readonly orderRepository: OrderRepository,
    private readonly productClient: ProductServiceClient,
    private readonly eventPublisher: EventPublisher
  ) {}

  async execute(command: CreateOrderCommand): Promise<OrderResult> {
    // 1. Validate products exist via sync call
    const products = await this.productClient.getProducts(
      command.items.map(i => i.productId)
    );

    // 2. Create order
    const order = Order.create(
      command.customerId,
      command.items.map(item => {
        const product = products.find(p => p.id === item.productId);
        return OrderItem.create(product, item.quantity);
      })
    );

    // 3. Save locally
    await this.orderRepository.save(order);

    // 4. Publish event for other services
    await this.eventPublisher.publish(
      new OrderCreatedEvent({
        orderId: order.id,
        customerId: order.customerId,
        items: order.items,
        total: order.total,
      })
    );

    return { orderId: order.id };
  }
}
```

## Communication Patterns

### Synchronous (REST/gRPC)

```typescript
// infrastructure/clients/product.client.ts
export class ProductServiceClient {
  constructor(
    private readonly httpClient: HttpClient,
    private readonly circuitBreaker: CircuitBreaker
  ) {}

  async getProduct(productId: string): Promise<Product> {
    return this.circuitBreaker.execute(async () => {
      const response = await this.httpClient.get(
        `${PRODUCT_SERVICE_URL}/products/${productId}`
      );
      return response.data;
    });
  }

  async checkStock(productId: string, quantity: number): Promise<boolean> {
    return this.circuitBreaker.execute(async () => {
      const response = await this.httpClient.get(
        `${PRODUCT_SERVICE_URL}/products/${productId}/stock`,
        { params: { quantity } }
      );
      return response.data.available;
    });
  }
}

// Using gRPC
// product.proto
syntax = "proto3";
package product;

service ProductService {
  rpc GetProduct (GetProductRequest) returns (Product);
  rpc CheckStock (CheckStockRequest) returns (StockResponse);
}

message GetProductRequest {
  string product_id = 1;
}

message Product {
  string id = 1;
  string name = 2;
  double price = 3;
  int32 stock = 4;
}
```

### Asynchronous (Events/Messages)

```typescript
// infrastructure/messaging/event-publisher.ts
export class RabbitMQEventPublisher implements EventPublisher {
  constructor(private readonly channel: Channel) {}

  async publish(event: DomainEvent): Promise<void> {
    const exchange = 'domain_events';
    const routingKey = event.eventType;

    await this.channel.publish(
      exchange,
      routingKey,
      Buffer.from(JSON.stringify({
        eventId: crypto.randomUUID(),
        eventType: event.eventType,
        occurredAt: new Date().toISOString(),
        payload: event.payload,
      })),
      { persistent: true }
    );
  }
}

// Event consumer in another service
// notification-service/src/infrastructure/messaging/order-events.consumer.ts
export class OrderEventsConsumer {
  constructor(private readonly notificationService: NotificationService) {}

  @Subscribe('order.created')
  async onOrderCreated(event: OrderCreatedEvent): Promise<void> {
    await this.notificationService.sendOrderConfirmation(
      event.payload.customerId,
      event.payload.orderId
    );
  }

  @Subscribe('order.shipped')
  async onOrderShipped(event: OrderShippedEvent): Promise<void> {
    await this.notificationService.sendShippingNotification(
      event.payload.customerId,
      event.payload.trackingNumber
    );
  }
}
```

## Saga Pattern (Distributed Transactions)

```typescript
// Choreography-based Saga
// order-service publishes events, other services react

// OrderCreated → PaymentService charges → PaymentCompleted
// PaymentCompleted → InventoryService reserves → InventoryReserved
// InventoryReserved → OrderService confirms → OrderConfirmed

// Compensation on failure:
// PaymentFailed → OrderService cancels → OrderCancelled
// InventoryFailed → PaymentService refunds → PaymentRefunded

// Orchestration-based Saga
export class CreateOrderSaga {
  private readonly steps: SagaStep[] = [
    {
      name: 'reserve_inventory',
      execute: async (ctx) => {
        const result = await this.inventoryClient.reserve(ctx.items);
        ctx.reservationId = result.reservationId;
      },
      compensate: async (ctx) => {
        await this.inventoryClient.cancelReservation(ctx.reservationId);
      },
    },
    {
      name: 'process_payment',
      execute: async (ctx) => {
        const result = await this.paymentClient.charge({
          customerId: ctx.customerId,
          amount: ctx.total,
        });
        ctx.paymentId = result.paymentId;
      },
      compensate: async (ctx) => {
        await this.paymentClient.refund(ctx.paymentId);
      },
    },
    {
      name: 'confirm_order',
      execute: async (ctx) => {
        await this.orderRepository.confirm(ctx.orderId);
      },
      compensate: async (ctx) => {
        await this.orderRepository.cancel(ctx.orderId);
      },
    },
  ];

  async execute(command: CreateOrderCommand): Promise<SagaResult> {
    const context: SagaContext = {
      orderId: command.orderId,
      customerId: command.customerId,
      items: command.items,
      total: command.total,
    };

    const completedSteps: SagaStep[] = [];

    try {
      for (const step of this.steps) {
        await step.execute(context);
        completedSteps.push(step);
      }
      return { success: true, orderId: context.orderId };
    } catch (error) {
      // Compensate in reverse order
      for (const step of completedSteps.reverse()) {
        try {
          await step.compensate(context);
        } catch (compensationError) {
          // Log and continue compensation
          console.error(`Compensation failed for ${step.name}`, compensationError);
        }
      }
      return { success: false, error: error.message };
    }
  }
}
```

## API Gateway

```typescript
// gateway/src/routes.ts
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
    middleware: ['rateLimit'],  // Public access
  },
];

// gateway/src/middleware/auth.ts
export const authMiddleware: Middleware = async (req, res, next) => {
  const token = req.headers.authorization?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }

  try {
    const payload = await verifyToken(token);
    req.user = payload;
    next();
  } catch {
    return res.status(401).json({ error: 'Invalid token' });
  }
};

// gateway/src/middleware/rate-limit.ts
export const rateLimitMiddleware = rateLimit({
  windowMs: 60 * 1000,  // 1 minute
  max: 100,  // 100 requests per minute
  keyGenerator: (req) => req.user?.id || req.ip,
});
```

## Service Discovery

```typescript
// Using Consul for service discovery
export class ConsulServiceDiscovery implements ServiceDiscovery {
  private consul: Consul;

  async register(service: ServiceInfo): Promise<void> {
    await this.consul.agent.service.register({
      name: service.name,
      id: service.instanceId,
      address: service.host,
      port: service.port,
      check: {
        http: `http://${service.host}:${service.port}/health`,
        interval: '10s',
        timeout: '5s',
      },
    });
  }

  async discover(serviceName: string): Promise<ServiceInstance[]> {
    const result = await this.consul.health.service({
      service: serviceName,
      passing: true,  // Only healthy instances
    });

    return result.map(entry => ({
      id: entry.Service.ID,
      host: entry.Service.Address,
      port: entry.Service.Port,
    }));
  }

  async deregister(instanceId: string): Promise<void> {
    await this.consul.agent.service.deregister(instanceId);
  }
}
```

## Circuit Breaker Pattern

```typescript
// infrastructure/resilience/circuit-breaker.ts
export class CircuitBreaker {
  private state: 'CLOSED' | 'OPEN' | 'HALF_OPEN' = 'CLOSED';
  private failures = 0;
  private lastFailure: Date | null = null;

  constructor(
    private readonly options: {
      failureThreshold: number;
      resetTimeout: number;
      monitoringPeriod: number;
    }
  ) {}

  async execute<T>(operation: () => Promise<T>): Promise<T> {
    if (this.state === 'OPEN') {
      if (this.shouldAttemptReset()) {
        this.state = 'HALF_OPEN';
      } else {
        throw new CircuitOpenError();
      }
    }

    try {
      const result = await operation();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = 'CLOSED';
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailure = new Date();

    if (this.failures >= this.options.failureThreshold) {
      this.state = 'OPEN';
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailure) return true;
    const elapsed = Date.now() - this.lastFailure.getTime();
    return elapsed >= this.options.resetTimeout;
  }
}

// Usage
const circuitBreaker = new CircuitBreaker({
  failureThreshold: 5,
  resetTimeout: 30000,  // 30 seconds
  monitoringPeriod: 60000,
});

const product = await circuitBreaker.execute(() =>
  productClient.getProduct(productId)
);
```

## Distributed Tracing

```typescript
// infrastructure/tracing/tracer.ts
import { trace, SpanStatusCode } from '@opentelemetry/api';

export function traced(spanName: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const tracer = trace.getTracer('order-service');
      return tracer.startActiveSpan(spanName, async (span) => {
        try {
          const result = await originalMethod.apply(this, args);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error) {
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: error.message,
          });
          span.recordException(error);
          throw error;
        } finally {
          span.end();
        }
      });
    };
  };
}

// Usage
export class OrderService {
  @traced('CreateOrder')
  async createOrder(dto: CreateOrderDTO): Promise<Order> {
    // Method implementation
  }
}
```

## Data Patterns

### Database per Service

```
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  User Service   │  │  Order Service  │  │ Product Service │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
    ┌────▼────┐          ┌────▼────┐          ┌────▼────┐
    │ User DB │          │Order DB │          │Prod DB  │
    │(Postgres)│          │(MongoDB)│          │(Postgres)│
    └─────────┘          └─────────┘          └─────────┘
```

### API Composition

```typescript
// gateway/src/composition/order-details.ts
export class OrderDetailsComposer {
  constructor(
    private readonly orderClient: OrderServiceClient,
    private readonly userClient: UserServiceClient,
    private readonly productClient: ProductServiceClient
  ) {}

  async getOrderDetails(orderId: string): Promise<OrderDetailsView> {
    const order = await this.orderClient.getOrder(orderId);

    // Parallel fetches
    const [customer, products] = await Promise.all([
      this.userClient.getUser(order.customerId),
      this.productClient.getProducts(order.items.map(i => i.productId)),
    ]);

    return {
      orderId: order.id,
      status: order.status,
      customer: {
        id: customer.id,
        name: customer.name,
        email: customer.email,
      },
      items: order.items.map(item => {
        const product = products.find(p => p.id === item.productId);
        return {
          productId: item.productId,
          productName: product?.name,
          quantity: item.quantity,
          unitPrice: item.price,
        };
      }),
      total: order.total,
      createdAt: order.createdAt,
    };
  }
}
```

## When to Use Microservices

### Good Fit
- Large, complex domains
- Multiple teams working independently
- Different scaling requirements per component
- Polyglot persistence needs
- Frequent deployments needed

### When NOT to Use
- Small teams / small applications
- Unclear domain boundaries
- Tight latency requirements
- Limited DevOps capabilities
- Early-stage startups (usually)
