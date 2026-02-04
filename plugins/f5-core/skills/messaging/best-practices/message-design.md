---
name: message-design
description: Designing effective message schemas and structures
category: messaging/best-practices
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Message Design

## Overview

Well-designed messages are the foundation of reliable messaging systems. Good message design enables schema evolution, debugging, and interoperability across services.

## Message Structure

### Standard Message Envelope

```typescript
interface MessageEnvelope<T> {
  // Identification
  messageId: string;          // Unique identifier
  correlationId: string;      // Trace through system
  causationId?: string;       // What triggered this message

  // Type information
  messageType: string;        // e.g., 'order.created'
  version: number;            // Schema version

  // Metadata
  timestamp: Date;            // When created
  source: string;             // Originating service
  contentType: string;        // e.g., 'application/json'

  // Payload
  payload: T;                 // The actual data

  // Optional
  headers?: Record<string, string>;
}

// Example
const orderCreatedMessage: MessageEnvelope<OrderCreatedPayload> = {
  messageId: 'msg-abc-123',
  correlationId: 'req-xyz-789',
  causationId: 'cmd-def-456',
  messageType: 'order.created',
  version: 1,
  timestamp: new Date(),
  source: 'order-service',
  contentType: 'application/json',
  payload: {
    orderId: 'order-123',
    customerId: 'cust-456',
    items: [{ productId: 'prod-1', quantity: 2, price: 29.99 }],
    total: 59.98,
  },
};
```

### Event Naming Conventions

```typescript
// Domain events - past tense, describes what happened
type DomainEvents =
  | 'order.created'
  | 'order.paid'
  | 'order.shipped'
  | 'order.delivered'
  | 'order.cancelled'
  | 'payment.received'
  | 'payment.refunded'
  | 'inventory.reserved'
  | 'inventory.released';

// Commands - imperative, describes intent
type Commands =
  | 'order.create'
  | 'order.cancel'
  | 'payment.process'
  | 'payment.refund'
  | 'inventory.reserve';

// Queries - question form
type Queries =
  | 'order.get'
  | 'order.list'
  | 'inventory.check';

// Naming pattern: {domain}.{action}
// Examples:
// - user.registered (event)
// - user.register (command)
// - user.profile.updated (event)
// - user.profile.update (command)
```

## Self-Contained Messages

```typescript
// ❌ Bad: Requires lookup
interface BadOrderCreatedEvent {
  orderId: string;
  // Consumer must fetch order details
}

// ✅ Good: Self-contained
interface GoodOrderCreatedEvent {
  orderId: string;
  customerId: string;
  customerEmail: string;
  items: Array<{
    productId: string;
    productName: string;
    quantity: number;
    unitPrice: number;
    totalPrice: number;
  }>;
  subtotal: number;
  tax: number;
  shippingCost: number;
  total: number;
  shippingAddress: {
    street: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
  createdAt: Date;
}

// Benefits:
// - No external dependencies to process
// - Works even if source service is down
// - Enables event replay
// - Faster processing (no lookups)
```

## Schema Versioning

### Version in Message

```typescript
interface VersionedMessage<T> {
  version: number;
  payload: T;
}

// Version 1
interface OrderCreatedV1 {
  orderId: string;
  total: number;
}

// Version 2 - added field
interface OrderCreatedV2 {
  orderId: string;
  subtotal: number;
  tax: number;
  total: number;
}

// Consumer handles multiple versions
function handleOrderCreated(message: VersionedMessage<any>): void {
  switch (message.version) {
    case 1:
      handleV1(message.payload as OrderCreatedV1);
      break;
    case 2:
      handleV2(message.payload as OrderCreatedV2);
      break;
    default:
      throw new Error(`Unsupported version: ${message.version}`);
  }
}
```

### Schema Registry

```typescript
import { SchemaRegistry, SchemaType } from '@kafkajs/confluent-schema-registry';

const registry = new SchemaRegistry({ host: 'http://localhost:8081' });

// Avro schema with evolution rules
const orderSchema = {
  type: 'record',
  name: 'Order',
  namespace: 'com.example.orders',
  fields: [
    { name: 'orderId', type: 'string' },
    { name: 'customerId', type: 'string' },
    { name: 'total', type: 'double' },
    // New optional field (backward compatible)
    { name: 'discount', type: ['null', 'double'], default: null },
  ],
};

// Register schema
const { id } = await registry.register({
  type: SchemaType.AVRO,
  schema: JSON.stringify(orderSchema),
}, {
  subject: 'orders-value',
});

// Encode message
const encoded = await registry.encode(id, orderData);

// Decode message (handles version automatically)
const decoded = await registry.decode(encoded);
```

## Backward and Forward Compatibility

```typescript
// Backward compatible changes (safe):
// - Add optional fields with defaults
// - Add new enum values at end
// - Widen numeric types (int → long)

// Forward compatible changes (safe):
// - Remove optional fields
// - Ignore unknown fields

// Breaking changes (avoid):
// - Remove required fields
// - Change field types
// - Rename fields

// Strategy: Always add, never remove or change
interface OrderV1 {
  orderId: string;
  amount: number;
}

// V2: Add field, keep old
interface OrderV2 {
  orderId: string;
  amount: number;      // Keep for backward compatibility
  subtotal?: number;   // New optional field
  tax?: number;        // New optional field
  total?: number;      // New calculated field
}

// Consumer handles both
function processOrder(order: OrderV1 | OrderV2): void {
  const total = 'total' in order && order.total
    ? order.total
    : order.amount; // Fallback to v1 field
}
```

## Message Size Optimization

```typescript
// Large messages - use references
interface LargePayloadMessage {
  messageId: string;
  payloadType: 'inline' | 'reference';

  // For small payloads
  payload?: any;

  // For large payloads
  payloadRef?: {
    bucket: string;
    key: string;
    size: number;
    checksum: string;
  };
}

// Producer
async function sendMessage(data: any): Promise<void> {
  const serialized = JSON.stringify(data);

  if (serialized.length > 256 * 1024) { // 256KB threshold
    // Store in S3
    const key = `messages/${crypto.randomUUID()}.json`;
    await s3.putObject({
      Bucket: 'message-payloads',
      Key: key,
      Body: serialized,
    });

    await queue.send({
      messageId: crypto.randomUUID(),
      payloadType: 'reference',
      payloadRef: {
        bucket: 'message-payloads',
        key,
        size: serialized.length,
        checksum: md5(serialized),
      },
    });
  } else {
    await queue.send({
      messageId: crypto.randomUUID(),
      payloadType: 'inline',
      payload: data,
    });
  }
}

// Consumer
async function receiveMessage(message: LargePayloadMessage): Promise<any> {
  if (message.payloadType === 'inline') {
    return message.payload;
  }

  const response = await s3.getObject({
    Bucket: message.payloadRef!.bucket,
    Key: message.payloadRef!.key,
  });

  return JSON.parse(await response.Body.transformToString());
}
```

## Message Validation

```typescript
import { z } from 'zod';

// Define schema
const OrderCreatedSchema = z.object({
  orderId: z.string().uuid(),
  customerId: z.string().uuid(),
  items: z.array(z.object({
    productId: z.string(),
    quantity: z.number().int().positive(),
    price: z.number().positive(),
  })).min(1),
  total: z.number().positive(),
  createdAt: z.string().datetime(),
});

type OrderCreated = z.infer<typeof OrderCreatedSchema>;

// Validate on produce
async function publishOrderCreated(data: unknown): Promise<void> {
  const validated = OrderCreatedSchema.parse(data);
  await eventBus.publish('order.created', validated);
}

// Validate on consume
async function handleOrderCreated(message: unknown): Promise<void> {
  const result = OrderCreatedSchema.safeParse(message);

  if (!result.success) {
    console.error('Invalid message:', result.error);
    // Move to DLQ or handle error
    return;
  }

  await processOrder(result.data);
}
```

## Correlation and Tracing

```typescript
interface TracingContext {
  traceId: string;       // Unique trace identifier
  spanId: string;        // Current span
  parentSpanId?: string; // Parent span
  baggage?: Record<string, string>;
}

class MessageTracer {
  // Create new trace
  startTrace(): TracingContext {
    return {
      traceId: crypto.randomUUID(),
      spanId: crypto.randomUUID(),
    };
  }

  // Continue existing trace
  continueTrace(context: TracingContext): TracingContext {
    return {
      traceId: context.traceId,
      spanId: crypto.randomUUID(),
      parentSpanId: context.spanId,
      baggage: context.baggage,
    };
  }

  // Extract from message
  extractContext(message: MessageEnvelope<any>): TracingContext {
    return {
      traceId: message.correlationId,
      spanId: message.headers?.['x-span-id'] || crypto.randomUUID(),
      parentSpanId: message.headers?.['x-parent-span-id'],
    };
  }

  // Inject into message
  injectContext(
    message: MessageEnvelope<any>,
    context: TracingContext
  ): MessageEnvelope<any> {
    return {
      ...message,
      correlationId: context.traceId,
      headers: {
        ...message.headers,
        'x-span-id': context.spanId,
        'x-parent-span-id': context.parentSpanId,
      },
    };
  }
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Include message ID** | Enable deduplication |
| **Use correlation IDs** | Trace across services |
| **Version schemas** | Support evolution |
| **Self-contained data** | No external lookups |
| **Validate messages** | Catch errors early |
| **Keep messages small** | Use references for large data |
| **Meaningful names** | Clear event/command naming |
| **Document schemas** | Enable consumer development |

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Chatty messages | High overhead | Batch or aggregate |
| God messages | Too complex | Split by concern |
| Undocumented | Hard to consume | Schema registry |
| No versioning | Breaking changes | Always version |
| External refs only | Coupling | Include essential data |
