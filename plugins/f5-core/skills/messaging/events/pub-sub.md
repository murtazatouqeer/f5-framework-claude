---
name: pub-sub
description: Publish-subscribe messaging patterns
category: messaging/events
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Publish-Subscribe Pattern

## Overview

Publish-Subscribe (Pub/Sub) is a messaging pattern where publishers send messages to topics without knowledge of subscribers. Subscribers express interest in topics and receive relevant messages.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Publisher** | Sends messages to topics |
| **Subscriber** | Receives messages from topics |
| **Topic** | Named channel for messages |
| **Message** | Data sent from publisher to subscribers |
| **Broker** | Routes messages between publishers and subscribers |

## Pattern Comparison

| Pattern | Receivers | Coupling | Use Case |
|---------|-----------|----------|----------|
| Point-to-Point | One | Tight | Task queue |
| Pub/Sub | Many | Loose | Event notification |
| Request-Reply | One | Medium | RPC-style |

## Basic Implementation

```typescript
type MessageHandler<T> = (message: T) => void | Promise<void>;

class PubSub<T = any> {
  private subscribers: Map<string, Set<MessageHandler<T>>> = new Map();

  subscribe(topic: string, handler: MessageHandler<T>): () => void {
    if (!this.subscribers.has(topic)) {
      this.subscribers.set(topic, new Set());
    }

    this.subscribers.get(topic)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.subscribers.get(topic)?.delete(handler);
    };
  }

  async publish(topic: string, message: T): Promise<void> {
    const handlers = this.subscribers.get(topic);

    if (!handlers || handlers.size === 0) {
      return;
    }

    const promises = Array.from(handlers).map(async (handler) => {
      try {
        await handler(message);
      } catch (error) {
        console.error(`Handler error for topic ${topic}:`, error);
      }
    });

    await Promise.all(promises);
  }

  // Pattern-based subscription
  subscribePattern(
    pattern: RegExp,
    handler: (topic: string, message: T) => void | Promise<void>
  ): () => void {
    const wrappedHandler = (message: T, topic: string) => handler(topic, message);

    // Store for cleanup
    const subscriptions: Array<() => void> = [];

    // Subscribe to existing matching topics
    for (const topic of this.subscribers.keys()) {
      if (pattern.test(topic)) {
        subscriptions.push(this.subscribe(topic, (msg) => wrappedHandler(msg, topic)));
      }
    }

    return () => {
      subscriptions.forEach(unsub => unsub());
    };
  }
}

// Usage
const pubsub = new PubSub();

// Subscribe
const unsubscribe = pubsub.subscribe('orders', (message) => {
  console.log('Order received:', message);
});

// Publish
await pubsub.publish('orders', { orderId: '123', total: 99.99 });

// Unsubscribe
unsubscribe();
```

## Redis Pub/Sub

```typescript
import Redis from 'ioredis';

class RedisPubSub {
  private publisher: Redis;
  private subscriber: Redis;
  private handlers: Map<string, Set<(message: any) => void>> = new Map();

  constructor(redisUrl: string = 'redis://localhost:6379') {
    this.publisher = new Redis(redisUrl);
    this.subscriber = new Redis(redisUrl);

    this.subscriber.on('message', (channel, message) => {
      const handlers = this.handlers.get(channel);
      if (handlers) {
        const parsed = JSON.parse(message);
        handlers.forEach(handler => handler(parsed));
      }
    });

    this.subscriber.on('pmessage', (pattern, channel, message) => {
      const handlers = this.handlers.get(pattern);
      if (handlers) {
        const parsed = JSON.parse(message);
        handlers.forEach(handler => handler({ channel, data: parsed }));
      }
    });
  }

  async subscribe(
    channel: string,
    handler: (message: any) => void
  ): Promise<() => Promise<void>> {
    if (!this.handlers.has(channel)) {
      this.handlers.set(channel, new Set());
      await this.subscriber.subscribe(channel);
    }

    this.handlers.get(channel)!.add(handler);

    return async () => {
      const handlers = this.handlers.get(channel);
      handlers?.delete(handler);

      if (handlers?.size === 0) {
        await this.subscriber.unsubscribe(channel);
        this.handlers.delete(channel);
      }
    };
  }

  async psubscribe(
    pattern: string,
    handler: (data: { channel: string; data: any }) => void
  ): Promise<() => Promise<void>> {
    if (!this.handlers.has(pattern)) {
      this.handlers.set(pattern, new Set());
      await this.subscriber.psubscribe(pattern);
    }

    this.handlers.get(pattern)!.add(handler);

    return async () => {
      const handlers = this.handlers.get(pattern);
      handlers?.delete(handler);

      if (handlers?.size === 0) {
        await this.subscriber.punsubscribe(pattern);
        this.handlers.delete(pattern);
      }
    };
  }

  async publish(channel: string, message: any): Promise<number> {
    return this.publisher.publish(channel, JSON.stringify(message));
  }

  async close(): Promise<void> {
    await this.subscriber.quit();
    await this.publisher.quit();
  }
}

// Usage
const pubsub = new RedisPubSub();

// Subscribe to specific channel
await pubsub.subscribe('orders:created', (message) => {
  console.log('New order:', message);
});

// Subscribe to pattern
await pubsub.psubscribe('orders:*', ({ channel, data }) => {
  console.log(`Event on ${channel}:`, data);
});

// Publish
await pubsub.publish('orders:created', { orderId: '123' });
await pubsub.publish('orders:shipped', { orderId: '123' });
```

## Event Emitter Pattern

```typescript
import { EventEmitter } from 'events';

class TypedEventEmitter<Events extends Record<string, any>> {
  private emitter = new EventEmitter();

  on<K extends keyof Events>(
    event: K,
    listener: (data: Events[K]) => void
  ): this {
    this.emitter.on(event as string, listener);
    return this;
  }

  once<K extends keyof Events>(
    event: K,
    listener: (data: Events[K]) => void
  ): this {
    this.emitter.once(event as string, listener);
    return this;
  }

  off<K extends keyof Events>(
    event: K,
    listener: (data: Events[K]) => void
  ): this {
    this.emitter.off(event as string, listener);
    return this;
  }

  emit<K extends keyof Events>(event: K, data: Events[K]): boolean {
    return this.emitter.emit(event as string, data);
  }

  removeAllListeners<K extends keyof Events>(event?: K): this {
    this.emitter.removeAllListeners(event as string);
    return this;
  }
}

// Define event types
interface OrderEvents {
  'order:created': { orderId: string; customerId: string };
  'order:paid': { orderId: string; amount: number };
  'order:shipped': { orderId: string; trackingNumber: string };
}

// Usage
const orderEvents = new TypedEventEmitter<OrderEvents>();

orderEvents.on('order:created', (data) => {
  console.log('Order created:', data.orderId); // TypeScript knows the type
});

orderEvents.emit('order:created', {
  orderId: '123',
  customerId: 'cust-456',
});
```

## Topic Hierarchy

```typescript
class HierarchicalPubSub {
  private subscribers: Map<string, Set<(topic: string, message: any) => void>> = new Map();

  subscribe(
    topicPattern: string,
    handler: (topic: string, message: any) => void
  ): () => void {
    if (!this.subscribers.has(topicPattern)) {
      this.subscribers.set(topicPattern, new Set());
    }

    this.subscribers.get(topicPattern)!.add(handler);

    return () => {
      this.subscribers.get(topicPattern)?.delete(handler);
    };
  }

  async publish(topic: string, message: any): Promise<void> {
    // Find all matching subscriptions
    for (const [pattern, handlers] of this.subscribers.entries()) {
      if (this.matches(topic, pattern)) {
        for (const handler of handlers) {
          try {
            await handler(topic, message);
          } catch (error) {
            console.error('Handler error:', error);
          }
        }
      }
    }
  }

  private matches(topic: string, pattern: string): boolean {
    // Support wildcards: * (single level), # (multi-level)
    const topicParts = topic.split('/');
    const patternParts = pattern.split('/');

    let ti = 0;
    let pi = 0;

    while (ti < topicParts.length && pi < patternParts.length) {
      if (patternParts[pi] === '#') {
        return true; // # matches everything remaining
      }

      if (patternParts[pi] === '*' || patternParts[pi] === topicParts[ti]) {
        ti++;
        pi++;
      } else {
        return false;
      }
    }

    return ti === topicParts.length && pi === patternParts.length;
  }
}

// Usage
const pubsub = new HierarchicalPubSub();

// Subscribe to specific topic
pubsub.subscribe('orders/created', (topic, message) => {
  console.log('New order:', message);
});

// Subscribe to all order events
pubsub.subscribe('orders/*', (topic, message) => {
  console.log(`Order event ${topic}:`, message);
});

// Subscribe to all events
pubsub.subscribe('#', (topic, message) => {
  console.log(`Any event ${topic}:`, message);
});

// Publish
await pubsub.publish('orders/created', { orderId: '123' });
await pubsub.publish('orders/shipped', { orderId: '123' });
await pubsub.publish('payments/received', { paymentId: '456' });
```

## Durable Subscriptions

```typescript
interface DurableSubscription {
  id: string;
  topic: string;
  lastPosition: number;
  createdAt: Date;
}

class DurablePubSub {
  private messages: Array<{ id: number; topic: string; data: any; timestamp: Date }> = [];
  private subscriptions: Map<string, DurableSubscription> = new Map();
  private handlers: Map<string, (message: any) => Promise<void>> = new Map();
  private nextId = 1;

  async publish(topic: string, data: any): Promise<number> {
    const id = this.nextId++;
    this.messages.push({ id, topic, data, timestamp: new Date() });

    // Notify active subscribers
    for (const [subId, subscription] of this.subscriptions.entries()) {
      if (this.topicMatches(topic, subscription.topic)) {
        const handler = this.handlers.get(subId);
        if (handler) {
          await handler({ id, topic, data });
          subscription.lastPosition = id;
        }
      }
    }

    return id;
  }

  createSubscription(id: string, topic: string, fromPosition: number = 0): void {
    this.subscriptions.set(id, {
      id,
      topic,
      lastPosition: fromPosition,
      createdAt: new Date(),
    });
  }

  async subscribe(
    subscriptionId: string,
    handler: (message: any) => Promise<void>
  ): Promise<void> {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) {
      throw new Error(`Subscription ${subscriptionId} not found`);
    }

    this.handlers.set(subscriptionId, handler);

    // Deliver missed messages
    const missedMessages = this.messages.filter(
      m => m.id > subscription.lastPosition &&
           this.topicMatches(m.topic, subscription.topic)
    );

    for (const message of missedMessages) {
      await handler(message);
      subscription.lastPosition = message.id;
    }
  }

  unsubscribe(subscriptionId: string): void {
    this.handlers.delete(subscriptionId);
    // Keep subscription for reconnection
  }

  private topicMatches(topic: string, pattern: string): boolean {
    return topic === pattern || pattern === '*';
  }
}

// Usage
const pubsub = new DurablePubSub();

// Create durable subscription
pubsub.createSubscription('order-processor', 'orders', 0);

// Connect (will receive missed messages)
await pubsub.subscribe('order-processor', async (message) => {
  console.log('Processing:', message);
  await processOrder(message.data);
});

// Publish while connected
await pubsub.publish('orders', { orderId: '123' });

// Disconnect
pubsub.unsubscribe('order-processor');

// Messages published while disconnected
await pubsub.publish('orders', { orderId: '124' });
await pubsub.publish('orders', { orderId: '125' });

// Reconnect - will receive missed messages
await pubsub.subscribe('order-processor', async (message) => {
  console.log('Processing after reconnect:', message);
});
```

## Fan-Out Pattern

```typescript
class FanOutPubSub {
  private queues: Map<string, any[]> = new Map();
  private consumers: Map<string, Map<string, (message: any) => Promise<void>>> = new Map();

  // Create queue for subscriber
  createQueue(topic: string, consumerId: string): void {
    const key = `${topic}:${consumerId}`;
    this.queues.set(key, []);

    if (!this.consumers.has(topic)) {
      this.consumers.set(topic, new Map());
    }
  }

  // Publish copies to all subscriber queues
  async publish(topic: string, message: any): Promise<void> {
    const subscribers = this.consumers.get(topic);
    if (!subscribers) return;

    for (const consumerId of subscribers.keys()) {
      const key = `${topic}:${consumerId}`;
      const queue = this.queues.get(key);
      queue?.push({ ...message, timestamp: new Date() });

      // Notify if consumer is active
      const handler = subscribers.get(consumerId);
      if (handler) {
        const msg = queue?.shift();
        if (msg) {
          await handler(msg);
        }
      }
    }
  }

  // Start consuming
  async consume(
    topic: string,
    consumerId: string,
    handler: (message: any) => Promise<void>
  ): Promise<void> {
    const subscribers = this.consumers.get(topic);
    if (!subscribers) {
      throw new Error(`Topic ${topic} not found for consumer ${consumerId}`);
    }

    subscribers.set(consumerId, handler);

    // Process queued messages
    const key = `${topic}:${consumerId}`;
    const queue = this.queues.get(key);

    while (queue && queue.length > 0) {
      const message = queue.shift();
      await handler(message);
    }
  }
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Handle failures** | Don't let one subscriber break others |
| **Use dead letter** | Capture failed messages |
| **Implement backpressure** | Slow publishers when subscribers lag |
| **Monitor lag** | Track subscriber positions |
| **Idempotent handlers** | Handle duplicate deliveries |
| **Async handlers** | Non-blocking message processing |

## When to Use Pub/Sub

### Good Fit
- Event notification
- Decoupled systems
- Multiple consumers
- Broadcast scenarios
- Real-time updates

### Poor Fit
- Request-response needed
- Guaranteed delivery required
- Message ordering critical
- Transaction support needed
