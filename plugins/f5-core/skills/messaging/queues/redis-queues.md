---
name: redis-queues
description: Lightweight Redis-based message queues
category: messaging/queues
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Redis Queues

## Overview

Redis provides simple, high-performance messaging through Lists, Pub/Sub, and Streams. Ideal for lightweight queuing needs without dedicated message broker infrastructure.

## Redis Data Structures for Messaging

| Structure | Pattern | Use Case |
|-----------|---------|----------|
| **Lists** | FIFO queue | Task distribution |
| **Pub/Sub** | Broadcast | Real-time notifications |
| **Streams** | Event log | Event sourcing |
| **Sorted Sets** | Priority queue | Scheduled tasks |

## List-Based Queues

### Basic Queue Operations

```typescript
import Redis from 'ioredis';

class RedisQueue {
  private redis: Redis;

  constructor(redisUrl: string = 'redis://localhost:6379') {
    this.redis = new Redis(redisUrl);
  }

  // Add to queue (LPUSH for FIFO with BRPOP)
  async enqueue(queue: string, message: object): Promise<void> {
    await this.redis.lpush(queue, JSON.stringify(message));
  }

  // Remove from queue (blocking)
  async dequeue(queue: string, timeout: number = 0): Promise<object | null> {
    const result = await this.redis.brpop(queue, timeout);

    if (result) {
      return JSON.parse(result[1]);
    }

    return null;
  }

  // Peek without removing
  async peek(queue: string): Promise<object | null> {
    const result = await this.redis.lindex(queue, -1);
    return result ? JSON.parse(result) : null;
  }

  // Get queue length
  async length(queue: string): Promise<number> {
    return this.redis.llen(queue);
  }
}
```

### Reliable Queue with Acknowledgment

```typescript
class ReliableQueue {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  async enqueue(queue: string, message: object): Promise<string> {
    const messageId = `msg:${Date.now()}:${Math.random().toString(36).substr(2, 9)}`;
    const payload = JSON.stringify({ id: messageId, data: message });

    await this.redis.lpush(queue, payload);
    return messageId;
  }

  // Move to processing queue atomically
  async dequeue(
    queue: string,
    processingQueue: string,
    timeout: number = 0
  ): Promise<{ id: string; data: object } | null> {
    const result = await this.redis.brpoplpush(queue, processingQueue, timeout);

    if (result) {
      return JSON.parse(result);
    }

    return null;
  }

  // Acknowledge completion
  async ack(processingQueue: string, messageId: string): Promise<void> {
    // Remove from processing queue
    const messages = await this.redis.lrange(processingQueue, 0, -1);

    for (const msg of messages) {
      const parsed = JSON.parse(msg);
      if (parsed.id === messageId) {
        await this.redis.lrem(processingQueue, 1, msg);
        break;
      }
    }
  }

  // Return failed message to main queue
  async nack(
    processingQueue: string,
    queue: string,
    messageId: string
  ): Promise<void> {
    const messages = await this.redis.lrange(processingQueue, 0, -1);

    for (const msg of messages) {
      const parsed = JSON.parse(msg);
      if (parsed.id === messageId) {
        await this.redis.lrem(processingQueue, 1, msg);
        await this.redis.rpush(queue, msg); // Add back to end
        break;
      }
    }
  }

  // Requeue stuck messages (heartbeat timeout)
  async recoverStuck(
    processingQueue: string,
    queue: string,
    maxAge: number = 30000
  ): Promise<number> {
    const now = Date.now();
    const messages = await this.redis.lrange(processingQueue, 0, -1);
    let recovered = 0;

    for (const msg of messages) {
      const parsed = JSON.parse(msg);
      const messageTime = parseInt(parsed.id.split(':')[1]);

      if (now - messageTime > maxAge) {
        await this.redis.lrem(processingQueue, 1, msg);
        await this.redis.rpush(queue, msg);
        recovered++;
      }
    }

    return recovered;
  }
}
```

## Redis Pub/Sub

### Basic Pub/Sub

```typescript
class RedisPubSub {
  private publisher: Redis;
  private subscriber: Redis;
  private handlers: Map<string, ((message: object) => void)[]> = new Map();

  constructor(redisUrl: string = 'redis://localhost:6379') {
    this.publisher = new Redis(redisUrl);
    this.subscriber = new Redis(redisUrl);

    this.subscriber.on('message', (channel, message) => {
      const handlers = this.handlers.get(channel) || [];
      const data = JSON.parse(message);

      handlers.forEach(handler => handler(data));
    });
  }

  async publish(channel: string, message: object): Promise<void> {
    await this.publisher.publish(channel, JSON.stringify(message));
  }

  async subscribe(
    channel: string,
    handler: (message: object) => void
  ): Promise<void> {
    if (!this.handlers.has(channel)) {
      this.handlers.set(channel, []);
      await this.subscriber.subscribe(channel);
    }

    this.handlers.get(channel)!.push(handler);
  }

  async unsubscribe(channel: string): Promise<void> {
    await this.subscriber.unsubscribe(channel);
    this.handlers.delete(channel);
  }

  // Pattern subscription
  async psubscribe(
    pattern: string,
    handler: (channel: string, message: object) => void
  ): Promise<void> {
    this.subscriber.on('pmessage', (pat, channel, message) => {
      if (pat === pattern) {
        handler(channel, JSON.parse(message));
      }
    });

    await this.subscriber.psubscribe(pattern);
  }
}

// Usage
const pubsub = new RedisPubSub();

await pubsub.subscribe('orders', (message) => {
  console.log('Received order:', message);
});

await pubsub.psubscribe('events:*', (channel, message) => {
  console.log(`Event on ${channel}:`, message);
});

await pubsub.publish('orders', { orderId: '123', total: 99.99 });
await pubsub.publish('events:user:created', { userId: 'abc' });
```

### Pub/Sub Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Fire-and-forget | No persistence | Use Streams for durability |
| No acknowledgment | Lost messages | Combine with List queues |
| Subscriber must be online | Miss messages | Use Streams with consumer groups |

## Redis Streams

### Stream Basics

```typescript
class RedisStreamProducer {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  async add(
    stream: string,
    data: Record<string, string>,
    maxLen?: number
  ): Promise<string> {
    const args: (string | number)[] = [stream];

    if (maxLen) {
      args.push('MAXLEN', '~', maxLen);
    }

    args.push('*'); // Auto-generate ID

    for (const [key, value] of Object.entries(data)) {
      args.push(key, value);
    }

    return this.redis.xadd(...args);
  }
}

class RedisStreamConsumer {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  // Read new entries
  async read(
    stream: string,
    lastId: string = '$', // '$' = only new, '0' = from beginning
    count: number = 10,
    block: number = 0 // 0 = non-blocking
  ): Promise<Array<{ id: string; data: Record<string, string> }>> {
    const result = await this.redis.xread(
      'COUNT', count,
      'BLOCK', block,
      'STREAMS', stream, lastId
    );

    if (!result) return [];

    return result[0][1].map(([id, fields]) => ({
      id,
      data: this.fieldsToObject(fields),
    }));
  }

  private fieldsToObject(fields: string[]): Record<string, string> {
    const obj: Record<string, string> = {};
    for (let i = 0; i < fields.length; i += 2) {
      obj[fields[i]] = fields[i + 1];
    }
    return obj;
  }
}
```

### Consumer Groups

```typescript
class StreamConsumerGroup {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  // Create consumer group
  async createGroup(
    stream: string,
    group: string,
    startId: string = '$'
  ): Promise<void> {
    try {
      await this.redis.xgroup('CREATE', stream, group, startId, 'MKSTREAM');
    } catch (error: any) {
      // Group already exists
      if (!error.message.includes('BUSYGROUP')) {
        throw error;
      }
    }
  }

  // Read as consumer in group
  async readGroup(
    stream: string,
    group: string,
    consumer: string,
    count: number = 10,
    block: number = 0
  ): Promise<Array<{ id: string; data: Record<string, string> }>> {
    const result = await this.redis.xreadgroup(
      'GROUP', group, consumer,
      'COUNT', count,
      'BLOCK', block,
      'STREAMS', stream, '>'  // '>' = only new messages
    );

    if (!result) return [];

    return result[0][1].map(([id, fields]) => ({
      id,
      data: this.fieldsToObject(fields),
    }));
  }

  // Acknowledge message
  async ack(stream: string, group: string, messageId: string): Promise<void> {
    await this.redis.xack(stream, group, messageId);
  }

  // Claim pending messages (for recovery)
  async claimPending(
    stream: string,
    group: string,
    consumer: string,
    minIdleTime: number = 30000,
    count: number = 10
  ): Promise<Array<{ id: string; data: Record<string, string> }>> {
    // Get pending entries
    const pending = await this.redis.xpending(
      stream, group, '-', '+', count
    );

    if (!pending.length) return [];

    const ids = pending
      .filter(([id, owner, idle]) => idle > minIdleTime)
      .map(([id]) => id);

    if (!ids.length) return [];

    const result = await this.redis.xclaim(
      stream, group, consumer, minIdleTime, ...ids
    );

    return result.map(([id, fields]) => ({
      id,
      data: this.fieldsToObject(fields),
    }));
  }

  private fieldsToObject(fields: string[]): Record<string, string> {
    const obj: Record<string, string> = {};
    for (let i = 0; i < fields.length; i += 2) {
      obj[fields[i]] = fields[i + 1];
    }
    return obj;
  }
}

// Usage
const group = new StreamConsumerGroup(redis);
await group.createGroup('orders', 'order-processors');

// Worker loop
async function worker(consumerId: string) {
  while (true) {
    // First, claim any stuck messages
    const stuck = await group.claimPending('orders', 'order-processors', consumerId);
    for (const msg of stuck) {
      await processMessage(msg);
      await group.ack('orders', 'order-processors', msg.id);
    }

    // Then read new messages
    const messages = await group.readGroup(
      'orders', 'order-processors', consumerId, 10, 5000
    );

    for (const msg of messages) {
      await processMessage(msg);
      await group.ack('orders', 'order-processors', msg.id);
    }
  }
}
```

## Priority Queue with Sorted Sets

```typescript
class PriorityQueue {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  // Add with priority (lower score = higher priority)
  async add(
    queue: string,
    message: object,
    priority: number = 0
  ): Promise<void> {
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const payload = JSON.stringify({ id, data: message });

    await this.redis.zadd(queue, priority, payload);
  }

  // Get highest priority item
  async pop(queue: string): Promise<object | null> {
    // Atomic pop of lowest score
    const result = await this.redis.zpopmin(queue);

    if (result.length) {
      return JSON.parse(result[0]).data;
    }

    return null;
  }

  // Peek without removing
  async peek(queue: string, count: number = 1): Promise<object[]> {
    const results = await this.redis.zrange(queue, 0, count - 1);
    return results.map(r => JSON.parse(r).data);
  }

  // Get queue length
  async length(queue: string): Promise<number> {
    return this.redis.zcard(queue);
  }
}

// Usage
const pq = new PriorityQueue(redis);

await pq.add('tasks', { task: 'low-priority' }, 10);
await pq.add('tasks', { task: 'high-priority' }, 1);
await pq.add('tasks', { task: 'medium-priority' }, 5);

const next = await pq.pop('tasks'); // { task: 'high-priority' }
```

## Delayed Queue

```typescript
class DelayedQueue {
  private redis: Redis;

  constructor(redis: Redis) {
    this.redis = redis;
  }

  // Schedule message for future delivery
  async schedule(
    queue: string,
    message: object,
    delayMs: number
  ): Promise<void> {
    const executeAt = Date.now() + delayMs;
    const payload = JSON.stringify(message);

    await this.redis.zadd(`${queue}:delayed`, executeAt, payload);
  }

  // Move due messages to main queue
  async processDue(queue: string): Promise<number> {
    const now = Date.now();
    const delayedQueue = `${queue}:delayed`;

    // Get due messages
    const due = await this.redis.zrangebyscore(delayedQueue, 0, now);

    if (!due.length) return 0;

    // Move to main queue atomically
    const pipeline = this.redis.pipeline();

    for (const msg of due) {
      pipeline.lpush(queue, msg);
      pipeline.zrem(delayedQueue, msg);
    }

    await pipeline.exec();
    return due.length;
  }

  // Start scheduler
  startScheduler(queue: string, intervalMs: number = 1000): NodeJS.Timer {
    return setInterval(async () => {
      const moved = await this.processDue(queue);
      if (moved > 0) {
        console.log(`Moved ${moved} messages to ${queue}`);
      }
    }, intervalMs);
  }
}

// Usage
const delayed = new DelayedQueue(redis);

// Schedule for 5 minutes later
await delayed.schedule('notifications', {
  type: 'reminder',
  userId: 'abc',
}, 5 * 60 * 1000);

// Start scheduler
delayed.startScheduler('notifications');
```

## Comparison

| Feature | Lists | Pub/Sub | Streams |
|---------|-------|---------|---------|
| Persistence | Yes | No | Yes |
| Consumer Groups | Manual | No | Yes |
| Replay | Limited | No | Yes |
| Ordering | FIFO | None | By ID |
| Acknowledgment | Manual | No | Built-in |
| Use Case | Simple queues | Real-time | Event log |

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use Streams for durability** | When message loss is unacceptable |
| **Implement heartbeat** | Recover stuck messages in processing |
| **Set MAXLEN on Streams** | Prevent unbounded growth |
| **Use pipeline** | Batch operations for efficiency |
| **Monitor memory** | Redis is in-memory, set maxmemory |
