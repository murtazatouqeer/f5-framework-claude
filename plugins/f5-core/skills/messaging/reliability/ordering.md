---
name: ordering
description: Maintaining message order in distributed systems
category: messaging/reliability
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Message Ordering

## Overview

Message ordering ensures messages are processed in a specific sequence. Different systems provide different ordering guarantees, and understanding these is crucial for building correct distributed systems.

## Ordering Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **No ordering** | Messages may arrive in any order | Independent events |
| **Per-key ordering** | Messages with same key are ordered | Entity updates |
| **Total ordering** | All messages globally ordered | Event sourcing |
| **Causal ordering** | Related messages maintain causality | Distributed systems |

## No Ordering (Unordered)

```typescript
// Messages can arrive in any order
// Simple, highest throughput

class UnorderedProcessor {
  async process(messages: Message[]): Promise<void> {
    // Process in parallel - order doesn't matter
    await Promise.all(messages.map(msg => this.handle(msg)));
  }

  private async handle(message: Message): Promise<void> {
    // Each message is independent
    await this.doWork(message);
  }
}

// Use cases:
// - Independent operations (sending emails)
// - Aggregations (counting events)
// - Stateless transformations
```

## Per-Key Ordering

Messages with the same key are processed in order, but different keys can be parallel.

### Kafka Partition Ordering

```typescript
import { Kafka, Producer, Consumer, Partitioners } from 'kafkajs';

const producer: Producer = kafka.producer({
  createPartitioner: Partitioners.DefaultPartitioner,
});

// Messages with same key go to same partition
async function sendOrderedByKey(
  topic: string,
  key: string,
  value: any
): Promise<void> {
  await producer.send({
    topic,
    messages: [{
      key,           // Determines partition
      value: JSON.stringify(value),
    }],
  });
}

// Order events for same order ID
await sendOrderedByKey('orders', 'order-123', { status: 'created' });
await sendOrderedByKey('orders', 'order-123', { status: 'paid' });
await sendOrderedByKey('orders', 'order-123', { status: 'shipped' });
// These will be processed in order

// Different orders can be parallel
await sendOrderedByKey('orders', 'order-456', { status: 'created' });
// This may be processed before order-123 events
```

### SQS FIFO Ordering

```typescript
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';

const sqs = new SQSClient({ region: 'us-east-1' });

async function sendFifoMessage(
  queueUrl: string,
  body: any,
  messageGroupId: string, // Messages in same group are ordered
  deduplicationId: string
): Promise<void> {
  await sqs.send(new SendMessageCommand({
    QueueUrl: queueUrl,
    MessageBody: JSON.stringify(body),
    MessageGroupId: messageGroupId,
    MessageDeduplicationId: deduplicationId,
  }));
}

// Same group = ordered
await sendFifoMessage(fifoQueue, { action: 'create' }, 'order-123', 'msg-1');
await sendFifoMessage(fifoQueue, { action: 'update' }, 'order-123', 'msg-2');

// Different groups = parallel
await sendFifoMessage(fifoQueue, { action: 'create' }, 'order-456', 'msg-3');
```

### Custom Key-Based Ordering

```typescript
class KeyOrderedProcessor {
  private locks: Map<string, Promise<void>> = new Map();

  async processOrdered(key: string, message: Message): Promise<void> {
    // Wait for previous message with same key
    const previousLock = this.locks.get(key);

    const currentLock = (async () => {
      if (previousLock) {
        await previousLock;
      }
      await this.handle(message);
    })();

    this.locks.set(key, currentLock);

    try {
      await currentLock;
    } finally {
      // Clean up if this is still the current lock
      if (this.locks.get(key) === currentLock) {
        this.locks.delete(key);
      }
    }
  }

  private async handle(message: Message): Promise<void> {
    // Process message
  }
}

// Concurrent processing maintains per-key order
const processor = new KeyOrderedProcessor();

// These execute in order for key 'A'
processor.processOrdered('A', msg1);
processor.processOrdered('A', msg2);
processor.processOrdered('A', msg3);

// This can execute in parallel with 'A'
processor.processOrdered('B', msg4);
```

## Total Ordering

All messages have a global order.

```typescript
// Sequence number based ordering
interface SequencedMessage {
  sequenceNumber: number;
  data: any;
}

class TotalOrderProcessor {
  private expectedSequence = 1;
  private buffer: Map<number, SequencedMessage> = new Map();

  async process(message: SequencedMessage): Promise<void> {
    if (message.sequenceNumber === this.expectedSequence) {
      // Process in order
      await this.handle(message);
      this.expectedSequence++;

      // Process any buffered messages
      await this.processBuffered();
    } else if (message.sequenceNumber > this.expectedSequence) {
      // Buffer for later
      this.buffer.set(message.sequenceNumber, message);
    }
    // Ignore messages with lower sequence (duplicates)
  }

  private async processBuffered(): Promise<void> {
    while (this.buffer.has(this.expectedSequence)) {
      const message = this.buffer.get(this.expectedSequence)!;
      this.buffer.delete(this.expectedSequence);
      await this.handle(message);
      this.expectedSequence++;
    }
  }

  private async handle(message: SequencedMessage): Promise<void> {
    // Process in guaranteed order
  }
}
```

### Single Partition for Total Order

```typescript
// Use single partition for strict ordering
const producer = kafka.producer();

await producer.send({
  topic: 'ordered-events',
  messages: [{
    partition: 0, // Always same partition
    value: JSON.stringify(event),
  }],
});

// Consumer reads from single partition
const consumer = kafka.consumer({ groupId: 'ordered-consumer' });
await consumer.run({
  partitionsConsumedConcurrently: 1, // Single consumer
  eachMessage: async ({ message }) => {
    // Guaranteed total order
    await processInOrder(message);
  },
});
```

## Causal Ordering

Related messages maintain their causal relationship.

```typescript
// Vector clock for causal ordering
class VectorClock {
  private clock: Map<string, number> = new Map();

  constructor(private readonly nodeId: string) {
    this.clock.set(nodeId, 0);
  }

  increment(): VectorClock {
    const current = this.clock.get(this.nodeId) || 0;
    this.clock.set(this.nodeId, current + 1);
    return this;
  }

  merge(other: VectorClock): VectorClock {
    for (const [nodeId, time] of other.clock) {
      const current = this.clock.get(nodeId) || 0;
      this.clock.set(nodeId, Math.max(current, time));
    }
    return this;
  }

  happensBefore(other: VectorClock): boolean {
    let atLeastOneLess = false;

    for (const [nodeId, time] of this.clock) {
      const otherTime = other.clock.get(nodeId) || 0;

      if (time > otherTime) {
        return false; // Cannot happen before
      }

      if (time < otherTime) {
        atLeastOneLess = true;
      }
    }

    return atLeastOneLess;
  }

  concurrent(other: VectorClock): boolean {
    return !this.happensBefore(other) && !other.happensBefore(this);
  }
}

interface CausalMessage {
  id: string;
  vectorClock: VectorClock;
  data: any;
}

class CausalOrderProcessor {
  private delivered: Map<string, VectorClock> = new Map();
  private pending: CausalMessage[] = [];

  async receive(message: CausalMessage): Promise<void> {
    this.pending.push(message);
    await this.deliverReady();
  }

  private async deliverReady(): Promise<void> {
    let delivered = true;

    while (delivered) {
      delivered = false;

      for (let i = 0; i < this.pending.length; i++) {
        const message = this.pending[i];

        if (this.canDeliver(message)) {
          this.pending.splice(i, 1);
          await this.deliver(message);
          delivered = true;
          break;
        }
      }
    }
  }

  private canDeliver(message: CausalMessage): boolean {
    // Check if all causal dependencies are satisfied
    for (const [nodeId, clock] of this.delivered) {
      const msgClock = message.vectorClock;
      // Simplified check - real implementation more complex
    }
    return true;
  }

  private async deliver(message: CausalMessage): Promise<void> {
    await this.handle(message);
    this.delivered.set(message.id, message.vectorClock);
  }

  private async handle(message: CausalMessage): Promise<void> {
    // Process in causal order
  }
}
```

## Handling Out-of-Order Messages

```typescript
class OutOfOrderHandler {
  private buffer: Map<string, Message[]> = new Map();
  private lastProcessed: Map<string, number> = new Map();

  async handle(message: OrderedMessage): Promise<void> {
    const key = message.partitionKey;
    const expected = (this.lastProcessed.get(key) || 0) + 1;

    if (message.sequenceNumber === expected) {
      // In order - process
      await this.process(message);
      this.lastProcessed.set(key, message.sequenceNumber);

      // Process buffered
      await this.processBuffered(key);

    } else if (message.sequenceNumber > expected) {
      // Out of order - buffer
      const buffer = this.buffer.get(key) || [];
      buffer.push(message);
      buffer.sort((a, b) => a.sequenceNumber - b.sequenceNumber);
      this.buffer.set(key, buffer);

      // Set timeout for missing messages
      this.scheduleTimeout(key, expected);

    } else {
      // Duplicate - ignore
      console.log(`Duplicate message: ${message.sequenceNumber}`);
    }
  }

  private async processBuffered(key: string): Promise<void> {
    const buffer = this.buffer.get(key) || [];
    let expected = (this.lastProcessed.get(key) || 0) + 1;

    while (buffer.length > 0 && buffer[0].sequenceNumber === expected) {
      const message = buffer.shift()!;
      await this.process(message);
      this.lastProcessed.set(key, message.sequenceNumber);
      expected++;
    }
  }

  private scheduleTimeout(key: string, expected: number): void {
    setTimeout(async () => {
      const current = this.lastProcessed.get(key) || 0;
      if (current < expected) {
        // Gap not filled - skip missing messages
        console.warn(`Skipping missing messages up to ${expected}`);
        this.lastProcessed.set(key, expected - 1);
        await this.processBuffered(key);
      }
    }, 5000);
  }

  private async process(message: OrderedMessage): Promise<void> {
    // Process message
  }
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use per-key ordering** | Balance order and parallelism |
| **Include sequence numbers** | Detect gaps and duplicates |
| **Buffer out-of-order** | Handle network reordering |
| **Set timeouts** | Don't wait forever for missing messages |
| **Partition wisely** | Related messages to same partition |
| **Test with delays** | Verify ordering under latency |

## Ordering Comparison

| System | Guarantee | Mechanism |
|--------|-----------|-----------|
| Kafka | Per-partition | Partition key |
| SQS FIFO | Per-group | Message group ID |
| RabbitMQ | Per-queue | Single queue |
| Redis Streams | Per-stream | Stream ID |
| Kinesis | Per-shard | Partition key |
