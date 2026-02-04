# Message Queues Reference

## BullMQ (Redis-Based)

### Setup

```typescript
import { Queue, Worker, QueueScheduler } from 'bullmq';
import Redis from 'ioredis';

const connection = new Redis({
  host: 'localhost',
  port: 6379,
  maxRetriesPerRequest: null,
});

// Create queue
const orderQueue = new Queue('orders', { connection });

// Create scheduler (for delayed jobs)
const scheduler = new QueueScheduler('orders', { connection });
```

### Producer

```typescript
// Add job
await orderQueue.add('process-order', {
  orderId: '123',
  items: [{ sku: 'ABC', qty: 2 }],
});

// With options
await orderQueue.add(
  'process-order',
  { orderId: '123' },
  {
    priority: 1,
    delay: 5000,
    attempts: 3,
    backoff: { type: 'exponential', delay: 1000 },
    removeOnComplete: true,
    removeOnFail: false,
  },
);

// Bulk add
await orderQueue.addBulk([
  { name: 'order1', data: { orderId: '1' } },
  { name: 'order2', data: { orderId: '2' } },
]);
```

### Worker

```typescript
const worker = new Worker(
  'orders',
  async (job) => {
    console.log(`Processing ${job.id}`);

    // Update progress
    await job.updateProgress(50);

    // Process order
    const result = await processOrder(job.data);

    // Return result
    return result;
  },
  {
    connection,
    concurrency: 5,
    limiter: {
      max: 100,
      duration: 1000,
    },
  },
);

// Event handlers
worker.on('completed', (job, result) => {
  console.log(`Job ${job.id} completed`, result);
});

worker.on('failed', (job, err) => {
  console.error(`Job ${job.id} failed`, err);
});

worker.on('progress', (job, progress) => {
  console.log(`Job ${job.id} progress: ${progress}%`);
});
```

### Repeatable Jobs

```typescript
// Cron-based
await orderQueue.add(
  'daily-report',
  {},
  {
    repeat: {
      cron: '0 9 * * *', // Every day at 9 AM
    },
  },
);

// Interval-based
await orderQueue.add(
  'health-check',
  {},
  {
    repeat: {
      every: 60000, // Every minute
    },
  },
);
```

## RabbitMQ

### Connection

```typescript
import amqp from 'amqplib';

const connection = await amqp.connect('amqp://localhost');
const channel = await connection.createChannel();

// Create queue
await channel.assertQueue('orders', {
  durable: true,
  arguments: {
    'x-dead-letter-exchange': 'dlx',
    'x-message-ttl': 86400000,
  },
});

// Create exchange
await channel.assertExchange('events', 'topic', { durable: true });
```

### Producer

```typescript
// Direct queue
channel.sendToQueue('orders', Buffer.from(JSON.stringify(order)), {
  persistent: true,
  messageId: uuid(),
  timestamp: Date.now(),
});

// Exchange publish
channel.publish('events', 'order.created', Buffer.from(JSON.stringify(order)), {
  persistent: true,
  messageId: uuid(),
});
```

### Consumer

```typescript
// Consume with manual ack
await channel.consume(
  'orders',
  async (msg) => {
    if (!msg) return;

    try {
      const order = JSON.parse(msg.content.toString());
      await processOrder(order);
      channel.ack(msg);
    } catch (err) {
      // Reject and requeue
      channel.nack(msg, false, true);
    }
  },
  { noAck: false },
);

// Topic subscription
await channel.bindQueue('order-notifications', 'events', 'order.*');
```

## AWS SQS

### Setup

```typescript
import { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand } from '@aws-sdk/client-sqs';

const sqs = new SQSClient({ region: 'us-east-1' });
const queueUrl = 'https://sqs.us-east-1.amazonaws.com/123456789/orders';
```

### Producer

```typescript
// Standard queue
await sqs.send(
  new SendMessageCommand({
    QueueUrl: queueUrl,
    MessageBody: JSON.stringify(order),
    MessageAttributes: {
      OrderType: {
        DataType: 'String',
        StringValue: 'standard',
      },
    },
  }),
);

// FIFO queue
await sqs.send(
  new SendMessageCommand({
    QueueUrl: `${queueUrl}.fifo`,
    MessageBody: JSON.stringify(order),
    MessageGroupId: order.userId, // For ordering
    MessageDeduplicationId: order.id, // For deduplication
  }),
);
```

### Consumer

```typescript
async function pollMessages() {
  while (true) {
    const response = await sqs.send(
      new ReceiveMessageCommand({
        QueueUrl: queueUrl,
        MaxNumberOfMessages: 10,
        WaitTimeSeconds: 20, // Long polling
        VisibilityTimeout: 30,
      }),
    );

    if (response.Messages) {
      for (const message of response.Messages) {
        try {
          await processMessage(JSON.parse(message.Body!));

          // Delete on success
          await sqs.send(
            new DeleteMessageCommand({
              QueueUrl: queueUrl,
              ReceiptHandle: message.ReceiptHandle!,
            }),
          );
        } catch (err) {
          console.error('Failed to process message', err);
          // Message returns to queue after visibility timeout
        }
      }
    }
  }
}
```

## Redis Streams

```typescript
import Redis from 'ioredis';

const redis = new Redis();

// Producer
await redis.xadd('orders', '*', 'data', JSON.stringify(order));

// Consumer group
await redis.xgroup('CREATE', 'orders', 'order-processors', '0', 'MKSTREAM');

// Consumer
async function consumeStream() {
  while (true) {
    const messages = await redis.xreadgroup(
      'GROUP',
      'order-processors',
      'consumer-1',
      'COUNT',
      10,
      'BLOCK',
      5000,
      'STREAMS',
      'orders',
      '>',
    );

    if (messages) {
      for (const [stream, entries] of messages) {
        for (const [id, fields] of entries) {
          try {
            const data = JSON.parse(fields[1]);
            await processOrder(data);
            await redis.xack('orders', 'order-processors', id);
          } catch (err) {
            console.error('Failed to process', err);
          }
        }
      }
    }
  }
}
```

## Queue Comparison

| Feature | BullMQ | RabbitMQ | SQS |
|---------|--------|----------|-----|
| Backend | Redis | Erlang | AWS |
| Priority | ✅ | ✅ | ❌ |
| Delayed | ✅ | ✅ (plugin) | ✅ |
| FIFO | ❌ | ✅ | ✅ (.fifo) |
| Routing | ❌ | ✅ | ❌ |
| Exactly-once | ❌ | ❌ | ✅ (FIFO) |
| Persistence | Redis | Disk | AWS |
