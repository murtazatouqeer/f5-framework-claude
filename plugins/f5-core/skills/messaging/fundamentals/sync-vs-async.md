---
name: sync-vs-async
description: When to use synchronous vs asynchronous communication
category: messaging/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Sync vs Async Communication

## Overview

Choosing between synchronous and asynchronous communication is a fundamental architectural decision that impacts system behavior, reliability, and complexity.

## Comparison

| Aspect | Synchronous | Asynchronous |
|--------|-------------|--------------|
| Coupling | Temporal coupling | Decoupled |
| Response | Immediate | Eventual |
| Failure handling | Cascading failures | Isolated failures |
| Complexity | Lower | Higher |
| Debugging | Easier | Harder |
| Scalability | Limited | Better |

## Synchronous Communication

### Characteristics

```
Client ──request──► Service ──response──► Client
        ◄─────── waits ───────►
```

```typescript
// HTTP Request (Synchronous)
async function createOrder(orderData: OrderData): Promise<Order> {
  // Call inventory service
  const inventory = await inventoryService.check(orderData.items);

  // Call payment service
  const payment = await paymentService.charge(orderData.payment);

  // Call shipping service
  const shipping = await shippingService.calculate(orderData.address);

  // Create order
  return orderRepository.save({
    ...orderData,
    inventory,
    payment,
    shipping,
  });
}
```

### Advantages

- Simple to understand and implement
- Immediate feedback
- Easy debugging with stack traces
- Request-response is intuitive

### Disadvantages

- Temporal coupling (both must be available)
- Cascading failures
- Limited scalability
- Long request times with many dependencies

### When to Use

- Real-time response required
- Simple operations
- Few downstream dependencies
- Strong consistency needed
- User-facing APIs needing immediate feedback

## Asynchronous Communication

### Characteristics

```
Producer ──message──► Queue ──message──► Consumer
           └── continues ──►
```

```typescript
// Message Queue (Asynchronous)
async function createOrder(orderData: OrderData): Promise<string> {
  const orderId = generateOrderId();

  // Save initial order
  await orderRepository.save({
    id: orderId,
    status: 'pending',
    ...orderData,
  });

  // Publish event - other services react independently
  await eventBus.publish('order.created', {
    orderId,
    items: orderData.items,
    customerId: orderData.customerId,
  });

  return orderId; // Return immediately
}

// Inventory Service (separate process)
eventBus.subscribe('order.created', async (event) => {
  await inventoryService.reserve(event.orderId, event.items);
});

// Payment Service (separate process)
eventBus.subscribe('order.created', async (event) => {
  await paymentService.initiate(event.orderId);
});
```

### Advantages

- Decoupled services
- Better fault isolation
- Improved scalability
- Load leveling
- Natural retry mechanism

### Disadvantages

- Increased complexity
- Eventual consistency
- Harder to debug
- Requires infrastructure (message broker)
- No immediate response

### When to Use

- Long-running operations
- Multiple downstream services
- Fire-and-forget scenarios
- Workload needs buffering
- Services need to scale independently

## Hybrid Approaches

### Command Query Responsibility Segregation (CQRS)

```typescript
// Commands are async
class CreateOrderHandler {
  async handle(command: CreateOrderCommand): Promise<void> {
    const order = Order.create(command);
    await this.orderRepository.save(order);

    // Publish event for projections
    await this.eventBus.publish(new OrderCreatedEvent(order));
  }
}

// Queries are sync
class OrderQueryService {
  async getOrder(orderId: string): Promise<OrderView> {
    return this.readDatabase.findOrder(orderId);
  }
}
```

### Sync API with Async Backend

```typescript
// Controller: Sync HTTP API
@Post('/orders')
async createOrder(@Body() dto: CreateOrderDto): Promise<OrderResponse> {
  // Validate synchronously
  await this.validator.validate(dto);

  // Enqueue for async processing
  const orderId = await this.orderQueue.add('create', dto);

  // Return immediately with pending status
  return {
    orderId,
    status: 'processing',
    statusUrl: `/orders/${orderId}/status`,
  };
}

// Background worker: Async processing
orderQueue.process('create', async (job) => {
  // Heavy processing happens here
  await processOrder(job.data);
});
```

### Async with Webhook Callback

```typescript
// Initial request
async function requestPayment(payment: PaymentRequest): Promise<string> {
  const transactionId = await paymentGateway.initiate({
    ...payment,
    callbackUrl: `${config.baseUrl}/webhooks/payment`,
  });

  return transactionId;
}

// Webhook handler receives result
@Post('/webhooks/payment')
async handlePaymentWebhook(@Body() payload: PaymentWebhook): Promise<void> {
  const order = await orderRepository.findByTransactionId(payload.transactionId);

  if (payload.status === 'success') {
    await order.markPaid();
  } else {
    await order.markPaymentFailed(payload.error);
  }

  await orderRepository.save(order);
}
```

## Decision Framework

```
Need immediate response?
├── Yes → Is operation fast (<100ms)?
│   ├── Yes → Synchronous
│   └── No → Sync API + Async backend
└── No → Is order important?
    ├── Yes → Message queue with ordering
    └── No → Pub/Sub events
```

### Questions to Ask

1. **Does the caller need the result immediately?**
   - Yes → Sync or sync with polling
   - No → Async is fine

2. **Can the operation fail partially?**
   - Yes → Consider saga pattern
   - No → Simple sync/async

3. **How many downstream services?**
   - 0-2 → Sync may be fine
   - 3+ → Consider async

4. **What's the acceptable latency?**
   - < 100ms → Sync required
   - > 1s acceptable → Async beneficial

5. **Do services need to scale independently?**
   - Yes → Async required
   - No → Sync may be simpler

## Mixing Patterns

### Read Sync, Write Async

```typescript
class OrderService {
  // Reads are synchronous for immediate response
  async getOrder(id: string): Promise<Order> {
    return this.orderRepository.findById(id);
  }

  // Writes are async for reliability
  async createOrder(data: CreateOrderDto): Promise<string> {
    const orderId = uuid();
    await this.queue.add('create-order', { orderId, ...data });
    return orderId;
  }
}
```

### Sync with Async Fallback

```typescript
async function getProductRecommendations(userId: string): Promise<Product[]> {
  try {
    // Try sync call with timeout
    return await withTimeout(
      recommendationService.getForUser(userId),
      500 // 500ms timeout
    );
  } catch (error) {
    // Fall back to cached/default recommendations
    return cachedRecommendations.getDefault();
  }
}
```

## Performance Comparison

| Scenario | Sync Time | Async Time | Notes |
|----------|-----------|------------|-------|
| 1 downstream call | 100ms | 10ms + eventual | Async faster response |
| 3 sequential calls | 300ms | 10ms + eventual | Async much faster |
| Under heavy load | Timeouts | Queued | Async handles better |
| Service down | Immediate failure | Retry later | Async more resilient |
