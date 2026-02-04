---
name: kafka
description: Apache Kafka distributed event streaming platform
category: messaging/events
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Apache Kafka

## Overview

Apache Kafka is a distributed event streaming platform designed for high-throughput, fault-tolerant, real-time data pipelines. It stores streams of records in a fault-tolerant, durable way.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Topic** | Named stream of records |
| **Partition** | Ordered, immutable sequence within topic |
| **Producer** | Publishes records to topics |
| **Consumer** | Reads records from topics |
| **Consumer Group** | Coordinates consumers for parallel processing |
| **Broker** | Kafka server storing data |
| **Offset** | Position of record in partition |

## Architecture

```
Producer → Topic (Partitions) → Consumer Group
              ├─ Partition 0 ─→ Consumer 1
              ├─ Partition 1 ─→ Consumer 2
              └─ Partition 2 ─→ Consumer 3
```

## Setup with KafkaJS

```typescript
import { Kafka, Producer, Consumer, EachMessagePayload } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'my-app',
  brokers: ['localhost:9092', 'localhost:9093'],
  ssl: process.env.NODE_ENV === 'production',
  sasl: process.env.NODE_ENV === 'production' ? {
    mechanism: 'plain',
    username: process.env.KAFKA_USERNAME!,
    password: process.env.KAFKA_PASSWORD!,
  } : undefined,
  retry: {
    initialRetryTime: 100,
    retries: 8,
  },
});

// Admin client for topic management
const admin = kafka.admin();
await admin.connect();

await admin.createTopics({
  topics: [
    {
      topic: 'orders',
      numPartitions: 3,
      replicationFactor: 2,
    },
  ],
});

await admin.disconnect();
```

## Producer

```typescript
class KafkaProducer {
  private producer: Producer;

  constructor(kafka: Kafka) {
    this.producer = kafka.producer({
      allowAutoTopicCreation: false,
      transactionTimeout: 30000,
    });
  }

  async connect(): Promise<void> {
    await this.producer.connect();
  }

  async disconnect(): Promise<void> {
    await this.producer.disconnect();
  }

  // Send single message
  async send(
    topic: string,
    message: object,
    key?: string
  ): Promise<void> {
    await this.producer.send({
      topic,
      messages: [{
        key: key || null,
        value: JSON.stringify(message),
        headers: {
          'content-type': 'application/json',
          'timestamp': Date.now().toString(),
        },
      }],
    });
  }

  // Send batch
  async sendBatch(
    topic: string,
    messages: Array<{ key?: string; value: object }>
  ): Promise<void> {
    await this.producer.send({
      topic,
      messages: messages.map(m => ({
        key: m.key || null,
        value: JSON.stringify(m.value),
      })),
    });
  }

  // Send to specific partition
  async sendToPartition(
    topic: string,
    partition: number,
    message: object
  ): Promise<void> {
    await this.producer.send({
      topic,
      messages: [{
        partition,
        value: JSON.stringify(message),
      }],
    });
  }
}

// Usage
const producer = new KafkaProducer(kafka);
await producer.connect();

// Key determines partition (same key = same partition = ordering)
await producer.send('orders', { orderId: '123', status: 'created' }, 'order-123');
await producer.send('orders', { orderId: '123', status: 'paid' }, 'order-123');
```

## Consumer

```typescript
class KafkaConsumer {
  private consumer: Consumer;
  private handlers: Map<string, (message: any) => Promise<void>> = new Map();

  constructor(kafka: Kafka, groupId: string) {
    this.consumer = kafka.consumer({
      groupId,
      sessionTimeout: 30000,
      heartbeatInterval: 3000,
      maxBytesPerPartition: 1048576, // 1MB
      retry: {
        retries: 5,
      },
    });
  }

  async connect(): Promise<void> {
    await this.consumer.connect();
  }

  async disconnect(): Promise<void> {
    await this.consumer.disconnect();
  }

  async subscribe(topics: string[]): Promise<void> {
    for (const topic of topics) {
      await this.consumer.subscribe({
        topic,
        fromBeginning: false, // Start from latest offset
      });
    }
  }

  // Register handler for topic
  onMessage(topic: string, handler: (message: any) => Promise<void>): void {
    this.handlers.set(topic, handler);
  }

  async start(): Promise<void> {
    await this.consumer.run({
      eachMessage: async ({ topic, partition, message }: EachMessagePayload) => {
        const handler = this.handlers.get(topic);

        if (handler && message.value) {
          try {
            const value = JSON.parse(message.value.toString());
            await handler(value);
          } catch (error) {
            console.error('Message processing failed:', error);
            // Handle error (retry, dead letter, etc.)
          }
        }
      },
    });
  }
}

// Usage
const consumer = new KafkaConsumer(kafka, 'order-service');
await consumer.connect();
await consumer.subscribe(['orders', 'payments']);

consumer.onMessage('orders', async (message) => {
  console.log('Order event:', message);
  await processOrder(message);
});

consumer.onMessage('payments', async (message) => {
  console.log('Payment event:', message);
  await processPayment(message);
});

await consumer.start();
```

## Consumer Groups

```typescript
// Multiple consumers in same group share partitions
// Partition 0 → Consumer A
// Partition 1 → Consumer B
// Partition 2 → Consumer A

// When consumer C joins:
// Partition 0 → Consumer A
// Partition 1 → Consumer B
// Partition 2 → Consumer C

// Handle rebalancing
consumer.on('consumer.rebalancing', async () => {
  console.log('Rebalancing started');
  // Commit any pending work before rebalance
});

consumer.on('consumer.group_join', async ({ payload }) => {
  console.log('Joined group:', payload.groupId);
  console.log('Assigned partitions:', payload.memberAssignment);
});
```

## Batch Processing

```typescript
await consumer.run({
  eachBatch: async ({
    batch,
    resolveOffset,
    heartbeat,
    commitOffsetsIfNecessary,
    isRunning,
    isStale,
  }) => {
    for (const message of batch.messages) {
      if (!isRunning() || isStale()) break;

      try {
        const value = JSON.parse(message.value?.toString() || '{}');
        await processMessage(value);

        // Mark as processed
        resolveOffset(message.offset);

        // Keep connection alive for long batches
        await heartbeat();
      } catch (error) {
        console.error('Batch message failed:', error);
        // Don't resolve offset - will be reprocessed
        break;
      }
    }

    // Commit processed offsets
    await commitOffsetsIfNecessary();
  },
  autoCommit: false, // Manual commit control
});
```

## Exactly-Once Semantics

```typescript
// Idempotent producer (prevents duplicates)
const producer = kafka.producer({
  idempotent: true,
  maxInFlightRequests: 5,
});

// Transactional producer
const transactionalProducer = kafka.producer({
  idempotent: true,
  transactionalId: 'my-transactional-id',
  maxInFlightRequests: 1,
});

await transactionalProducer.connect();

// Transaction example
const transaction = await transactionalProducer.transaction();

try {
  await transaction.send({
    topic: 'orders',
    messages: [{ value: JSON.stringify({ orderId: '123' }) }],
  });

  await transaction.send({
    topic: 'inventory',
    messages: [{ value: JSON.stringify({ action: 'reserve' }) }],
  });

  // Commit consumer offsets in same transaction
  await transaction.sendOffsets({
    consumerGroupId: 'my-group',
    topics: [{
      topic: 'input-topic',
      partitions: [{ partition: 0, offset: '100' }],
    }],
  });

  await transaction.commit();
} catch (error) {
  await transaction.abort();
  throw error;
}
```

## Offset Management

```typescript
// Manual offset commit
await consumer.run({
  autoCommit: false,
  eachMessage: async ({ topic, partition, message }) => {
    await processMessage(message);

    // Commit after processing
    await consumer.commitOffsets([{
      topic,
      partition,
      offset: (BigInt(message.offset) + 1n).toString(),
    }]);
  },
});

// Seek to specific offset
await consumer.seek({
  topic: 'orders',
  partition: 0,
  offset: '1000', // Start from offset 1000
});

// Reset to beginning
admin.resetOffsets({
  groupId: 'my-group',
  topic: 'orders',
  earliest: true,
});
```

## Stream Processing

```typescript
// Simple stream processor
class StreamProcessor {
  constructor(
    private readonly kafka: Kafka,
    private readonly inputTopic: string,
    private readonly outputTopic: string
  ) {}

  async start(): Promise<void> {
    const consumer = this.kafka.consumer({ groupId: 'stream-processor' });
    const producer = this.kafka.producer();

    await consumer.connect();
    await producer.connect();
    await consumer.subscribe({ topic: this.inputTopic });

    await consumer.run({
      eachMessage: async ({ message }) => {
        if (!message.value) return;

        const input = JSON.parse(message.value.toString());
        const output = await this.transform(input);

        await producer.send({
          topic: this.outputTopic,
          messages: [{
            key: message.key,
            value: JSON.stringify(output),
          }],
        });
      },
    });
  }

  private async transform(input: any): Promise<any> {
    // Transform logic
    return {
      ...input,
      processed: true,
      processedAt: new Date().toISOString(),
    };
  }
}
```

## Schema Registry

```typescript
import { SchemaRegistry, SchemaType } from '@kafkajs/confluent-schema-registry';

const registry = new SchemaRegistry({
  host: 'http://localhost:8081',
});

// Register schema
const schema = {
  type: 'record',
  name: 'Order',
  fields: [
    { name: 'orderId', type: 'string' },
    { name: 'customerId', type: 'string' },
    { name: 'total', type: 'double' },
  ],
};

const { id: schemaId } = await registry.register({
  type: SchemaType.AVRO,
  schema: JSON.stringify(schema),
}, { subject: 'orders-value' });

// Produce with schema
const encodedValue = await registry.encode(schemaId, {
  orderId: '123',
  customerId: 'cust-456',
  total: 99.99,
});

await producer.send({
  topic: 'orders',
  messages: [{ value: encodedValue }],
});

// Consume with schema
await consumer.run({
  eachMessage: async ({ message }) => {
    const decoded = await registry.decode(message.value);
    console.log('Order:', decoded);
  },
});
```

## Monitoring

```typescript
// Producer metrics
producer.on('producer.network.request', (event) => {
  console.log('Request:', {
    broker: event.payload.broker,
    duration: event.payload.duration,
    size: event.payload.size,
  });
});

// Consumer metrics
consumer.on('consumer.fetch', (event) => {
  console.log('Fetch:', {
    numberOfBatches: event.payload.numberOfBatches,
    duration: event.payload.duration,
  });
});

consumer.on('consumer.commit_offsets', (event) => {
  console.log('Committed:', event.payload.topics);
});

// Lag monitoring
const admin = kafka.admin();
const offsets = await admin.fetchOffsets({
  groupId: 'my-group',
  topics: ['orders'],
});

const topicOffsets = await admin.fetchTopicOffsets('orders');

// Calculate lag per partition
for (const partition of offsets[0].partitions) {
  const topicOffset = topicOffsets.find(t => t.partition === partition.partition);
  const lag = BigInt(topicOffset?.high || 0) - BigInt(partition.offset);
  console.log(`Partition ${partition.partition} lag: ${lag}`);
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use keys for ordering** | Same key → same partition → ordered |
| **Right partition count** | Match consumer count, plan for growth |
| **Idempotent consumers** | Handle duplicate deliveries |
| **Monitor lag** | Alert on growing consumer lag |
| **Use compression** | gzip, snappy, or lz4 for throughput |
| **Set retention** | Based on replay and storage needs |

## Comparison

| Feature | Kafka | RabbitMQ | SQS |
|---------|-------|----------|-----|
| Model | Log | Queue | Queue |
| Ordering | Per-partition | Per-queue | FIFO only |
| Replay | Yes | No | No |
| Retention | Configurable | Until consumed | 14 days |
| Throughput | Very high | High | High |
| Complexity | High | Medium | Low |
