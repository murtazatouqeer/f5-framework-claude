# Messaging Fundamentals Reference

## Sync vs Async Communication

### Synchronous (Request/Response)

```
Client ──request──► Service ──response──► Client
         └─────── blocking wait ─────────┘
```

- Client waits for response
- Simple error handling
- Tight coupling
- Timeout management required

### Asynchronous (Message-Based)

```
Producer ──message──► Queue ──message──► Consumer
         └─── immediate return ───┘
```

- No blocking
- Loose coupling
- Better resilience
- Eventually consistent

## Messaging Patterns

### Point-to-Point (Queue)

```
Producer ──► Queue ──► Consumer
              │
              └──► Only ONE consumer receives message
```

Use for: Task distribution, work queues, command processing

### Publish/Subscribe

```
Publisher ──► Topic ──► Subscriber A
                  ├──► Subscriber B
                  └──► Subscriber C
                       All subscribers receive message
```

Use for: Event notifications, broadcasting, notifications

### Request/Reply

```
Requester ──request──► Queue ──► Responder
    ▲                              │
    └─────── Reply Queue ◄─────────┘
```

Use for: RPC over messaging, sync semantics over async

### Fan-Out/Fan-In

```
         ┌──► Worker A ──┐
Producer ─┼──► Worker B ──┼──► Aggregator
         └──► Worker C ──┘
```

Use for: Parallel processing, map-reduce patterns

## Message Types

### Commands

```typescript
// Request an action
interface CreateOrderCommand {
  type: 'CREATE_ORDER';
  payload: {
    userId: string;
    items: OrderItem[];
  };
  metadata: {
    correlationId: string;
    timestamp: Date;
  };
}
```

### Events

```typescript
// Notify something happened
interface OrderCreatedEvent {
  type: 'ORDER_CREATED';
  payload: {
    orderId: string;
    userId: string;
    total: number;
  };
  metadata: {
    eventId: string;
    timestamp: Date;
    version: number;
  };
}
```

### Queries

```typescript
// Request data
interface GetOrderQuery {
  type: 'GET_ORDER';
  payload: {
    orderId: string;
  };
  replyTo: string;
}
```

## Message Structure

```typescript
interface Message<T> {
  // Identity
  id: string;
  type: string;

  // Content
  payload: T;

  // Routing
  destination?: string;
  replyTo?: string;

  // Correlation
  correlationId: string;
  causationId?: string;

  // Metadata
  timestamp: Date;
  version?: number;
  ttl?: number;

  // Headers
  headers: Record<string, string>;
}
```

## Delivery Guarantees

### At-Most-Once

```typescript
// Fire and forget - may lose messages
await queue.add('task', data);
// No acknowledgment
```

- Fastest
- May lose messages
- Use for: Non-critical updates, metrics

### At-Least-Once

```typescript
// Acknowledge after processing
const worker = new Worker('tasks', async (job) => {
  await processJob(job);
  // Auto-acknowledged on success
});
```

- May duplicate messages
- Requires idempotency
- Use for: Most business operations

### Exactly-Once

```typescript
// Transactional processing with deduplication
await db.transaction(async (tx) => {
  // Check if already processed
  const processed = await tx.query(
    'SELECT 1 FROM processed_messages WHERE id = ?',
    [message.id]
  );

  if (processed) return;

  // Process message
  await processMessage(message);

  // Mark as processed
  await tx.query(
    'INSERT INTO processed_messages (id) VALUES (?)',
    [message.id]
  );
});
```

- Most complex
- Highest overhead
- Use for: Financial transactions, critical operations

## Message Ordering

### Per-Partition Ordering

```typescript
// Kafka example - ordered within partition
await producer.send({
  topic: 'orders',
  messages: [{
    key: userId,    // Same key = same partition = ordered
    value: JSON.stringify(order),
  }],
});
```

### FIFO Queues

```typescript
// SQS FIFO example
await sqs.sendMessage({
  QueueUrl: 'https://sqs.../queue.fifo',
  MessageBody: JSON.stringify(data),
  MessageGroupId: orderId,  // Ordered within group
  MessageDeduplicationId: messageId,
});
```

## Error Handling

### Retry with Backoff

```typescript
const retryConfig = {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 1000,  // 1s, 2s, 4s, 8s, 16s
  },
};
```

### Dead Letter Queue

```typescript
// After max retries, move to DLQ
if (job.attemptsMade >= job.opts.attempts) {
  await dlqQueue.add('failed', {
    originalJob: job.data,
    error: err.message,
    failedAt: new Date(),
  });
}
```

### Circuit Breaker

```typescript
const breaker = new CircuitBreaker(sendMessage, {
  timeout: 5000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
});

try {
  await breaker.fire(message);
} catch (err) {
  // Circuit open - queue locally or reject
}
```
