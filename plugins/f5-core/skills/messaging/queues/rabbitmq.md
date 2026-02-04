---
name: rabbitmq
description: Feature-rich message broker with multiple protocols
category: messaging/queues
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# RabbitMQ

## Overview

RabbitMQ is a robust message broker supporting AMQP, MQTT, and STOMP protocols. It excels at complex routing scenarios with exchanges and queues.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Producer** | Sends messages to exchange |
| **Exchange** | Routes messages to queues |
| **Queue** | Stores messages for consumers |
| **Consumer** | Receives and processes messages |
| **Binding** | Rules connecting exchanges to queues |

## Exchange Types

| Type | Routing | Use Case |
|------|---------|----------|
| **Direct** | Exact routing key match | Task queues |
| **Fanout** | Broadcast to all queues | Notifications |
| **Topic** | Pattern matching | Log routing |
| **Headers** | Header attributes | Complex routing |

## Setup

```typescript
import amqp, { Connection, Channel } from 'amqplib';

class RabbitMQClient {
  private connection: Connection | null = null;
  private channel: Channel | null = null;

  async connect(url: string = 'amqp://localhost'): Promise<void> {
    this.connection = await amqp.connect(url);
    this.channel = await this.connection.createChannel();

    // Handle connection errors
    this.connection.on('error', (err) => {
      console.error('Connection error:', err);
    });

    this.connection.on('close', () => {
      console.log('Connection closed');
    });
  }

  async close(): Promise<void> {
    await this.channel?.close();
    await this.connection?.close();
  }
}
```

## Direct Exchange

```typescript
// Producer
async function sendDirect(
  channel: Channel,
  exchange: string,
  routingKey: string,
  message: object
): Promise<void> {
  await channel.assertExchange(exchange, 'direct', { durable: true });

  channel.publish(
    exchange,
    routingKey,
    Buffer.from(JSON.stringify(message)),
    { persistent: true }
  );
}

// Consumer
async function consumeDirect(
  channel: Channel,
  exchange: string,
  routingKey: string,
  queue: string,
  handler: (msg: object) => Promise<void>
): Promise<void> {
  await channel.assertExchange(exchange, 'direct', { durable: true });
  await channel.assertQueue(queue, { durable: true });
  await channel.bindQueue(queue, exchange, routingKey);

  channel.consume(queue, async (msg) => {
    if (msg) {
      try {
        const content = JSON.parse(msg.content.toString());
        await handler(content);
        channel.ack(msg);
      } catch (error) {
        // Reject and requeue on failure
        channel.nack(msg, false, true);
      }
    }
  });
}

// Usage
await sendDirect(channel, 'orders', 'order.create', {
  orderId: '123',
  items: [{ productId: 'abc', quantity: 2 }],
});
```

## Fanout Exchange

```typescript
// Publisher - broadcasts to all bound queues
async function broadcast(
  channel: Channel,
  exchange: string,
  message: object
): Promise<void> {
  await channel.assertExchange(exchange, 'fanout', { durable: true });

  channel.publish(
    exchange,
    '', // Routing key ignored for fanout
    Buffer.from(JSON.stringify(message))
  );
}

// Multiple subscribers receive the same message
async function subscribeToFanout(
  channel: Channel,
  exchange: string,
  handler: (msg: object) => Promise<void>
): Promise<void> {
  await channel.assertExchange(exchange, 'fanout', { durable: true });

  // Create exclusive queue for this consumer
  const { queue } = await channel.assertQueue('', { exclusive: true });
  await channel.bindQueue(queue, exchange, '');

  channel.consume(queue, async (msg) => {
    if (msg) {
      const content = JSON.parse(msg.content.toString());
      await handler(content);
      channel.ack(msg);
    }
  });
}
```

## Topic Exchange

```typescript
// Pattern-based routing
// Patterns: * (one word), # (zero or more words)

async function publishTopic(
  channel: Channel,
  exchange: string,
  routingKey: string, // e.g., 'order.created.usa'
  message: object
): Promise<void> {
  await channel.assertExchange(exchange, 'topic', { durable: true });

  channel.publish(
    exchange,
    routingKey,
    Buffer.from(JSON.stringify(message))
  );
}

async function subscribeTopic(
  channel: Channel,
  exchange: string,
  pattern: string, // e.g., 'order.*.usa', 'order.#'
  queue: string,
  handler: (msg: object, routingKey: string) => Promise<void>
): Promise<void> {
  await channel.assertExchange(exchange, 'topic', { durable: true });
  await channel.assertQueue(queue, { durable: true });
  await channel.bindQueue(queue, exchange, pattern);

  channel.consume(queue, async (msg) => {
    if (msg) {
      const content = JSON.parse(msg.content.toString());
      await handler(content, msg.fields.routingKey);
      channel.ack(msg);
    }
  });
}

// Examples
// 'order.created.usa' matches: 'order.*.usa', 'order.#', '#'
// 'order.shipped.eu' matches: 'order.shipped.*', 'order.#'
```

## Work Queues (Competing Consumers)

```typescript
// Distribute tasks among workers
async function createWorkQueue(
  channel: Channel,
  queue: string
): Promise<void> {
  await channel.assertQueue(queue, {
    durable: true,
  });

  // Fair dispatch - don't give more than 1 task at a time
  channel.prefetch(1);
}

async function addTask(
  channel: Channel,
  queue: string,
  task: object
): Promise<void> {
  channel.sendToQueue(
    queue,
    Buffer.from(JSON.stringify(task)),
    { persistent: true }
  );
}

async function processTask(
  channel: Channel,
  queue: string,
  worker: (task: object) => Promise<void>
): Promise<void> {
  channel.consume(queue, async (msg) => {
    if (msg) {
      const task = JSON.parse(msg.content.toString());

      try {
        await worker(task);
        channel.ack(msg);
      } catch (error) {
        // Dead letter on repeated failures
        channel.nack(msg, false, false);
      }
    }
  });
}
```

## Request-Reply (RPC)

```typescript
import { v4 as uuid } from 'uuid';

class RpcClient {
  private responseQueue: string = '';
  private correlationMap: Map<string, {
    resolve: (value: any) => void;
    reject: (error: Error) => void;
  }> = new Map();

  async setup(channel: Channel): Promise<void> {
    // Create exclusive reply queue
    const { queue } = await channel.assertQueue('', { exclusive: true });
    this.responseQueue = queue;

    // Listen for responses
    channel.consume(queue, (msg) => {
      if (msg) {
        const correlationId = msg.properties.correlationId;
        const pending = this.correlationMap.get(correlationId);

        if (pending) {
          const response = JSON.parse(msg.content.toString());
          pending.resolve(response);
          this.correlationMap.delete(correlationId);
        }

        channel.ack(msg);
      }
    });
  }

  async call(
    channel: Channel,
    queue: string,
    request: object,
    timeout: number = 5000
  ): Promise<any> {
    const correlationId = uuid();

    return new Promise((resolve, reject) => {
      // Set timeout
      const timer = setTimeout(() => {
        this.correlationMap.delete(correlationId);
        reject(new Error('RPC timeout'));
      }, timeout);

      this.correlationMap.set(correlationId, {
        resolve: (value) => {
          clearTimeout(timer);
          resolve(value);
        },
        reject,
      });

      channel.sendToQueue(queue, Buffer.from(JSON.stringify(request)), {
        correlationId,
        replyTo: this.responseQueue,
      });
    });
  }
}

// RPC Server
async function createRpcServer(
  channel: Channel,
  queue: string,
  handler: (request: object) => Promise<object>
): Promise<void> {
  await channel.assertQueue(queue, { durable: true });
  channel.prefetch(1);

  channel.consume(queue, async (msg) => {
    if (msg) {
      const request = JSON.parse(msg.content.toString());

      try {
        const response = await handler(request);

        channel.sendToQueue(
          msg.properties.replyTo,
          Buffer.from(JSON.stringify(response)),
          { correlationId: msg.properties.correlationId }
        );
      } catch (error) {
        channel.sendToQueue(
          msg.properties.replyTo,
          Buffer.from(JSON.stringify({ error: error.message })),
          { correlationId: msg.properties.correlationId }
        );
      }

      channel.ack(msg);
    }
  });
}
```

## Dead Letter Exchange

```typescript
async function setupDeadLetterQueue(channel: Channel): Promise<void> {
  // Dead letter exchange
  await channel.assertExchange('dlx', 'direct', { durable: true });
  await channel.assertQueue('dead-letters', { durable: true });
  await channel.bindQueue('dead-letters', 'dlx', 'dead');

  // Main queue with DLX configuration
  await channel.assertQueue('tasks', {
    durable: true,
    arguments: {
      'x-dead-letter-exchange': 'dlx',
      'x-dead-letter-routing-key': 'dead',
      'x-message-ttl': 60000, // 60 seconds TTL
    },
  });
}

// Messages go to DLX when:
// - Rejected without requeue (nack with requeue=false)
// - TTL expires
// - Queue length limit exceeded
```

## Message Properties

```typescript
channel.publish(exchange, routingKey, content, {
  // Delivery mode
  persistent: true,        // Survives broker restart

  // Routing
  correlationId: 'abc123', // Request-response matching
  replyTo: 'reply-queue',  // Response queue

  // Content
  contentType: 'application/json',
  contentEncoding: 'utf-8',

  // Expiration
  expiration: '60000',     // Message TTL in ms

  // Metadata
  messageId: 'msg-001',
  timestamp: Date.now(),
  type: 'order.created',
  appId: 'order-service',

  // Custom headers
  headers: {
    'x-retry-count': 0,
    'x-source': 'api',
  },
});
```

## Connection Management

```typescript
class RabbitMQConnectionManager {
  private connection: Connection | null = null;
  private channel: Channel | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;

  async connect(url: string): Promise<void> {
    try {
      this.connection = await amqp.connect(url);
      this.channel = await this.connection.createChannel();
      this.reconnectAttempts = 0;

      this.connection.on('error', this.handleError.bind(this));
      this.connection.on('close', this.handleClose.bind(this));

      console.log('Connected to RabbitMQ');
    } catch (error) {
      console.error('Connection failed:', error);
      await this.reconnect(url);
    }
  }

  private async handleError(error: Error): Promise<void> {
    console.error('RabbitMQ error:', error);
  }

  private async handleClose(): Promise<void> {
    console.log('Connection closed, attempting reconnect...');
    await this.reconnect(process.env.RABBITMQ_URL || 'amqp://localhost');
  }

  private async reconnect(url: string): Promise<void> {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      throw new Error('Max reconnection attempts reached');
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);

    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    await new Promise(resolve => setTimeout(resolve, delay));
    await this.connect(url);
  }

  getChannel(): Channel {
    if (!this.channel) {
      throw new Error('Not connected');
    }
    return this.channel;
  }
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Acknowledge properly** | Only ack after successful processing |
| **Use prefetch** | Limit unacked messages per consumer |
| **Handle errors** | Implement DLX for failed messages |
| **Monitor queues** | Track queue depth and consumer count |
| **Persist messages** | Use durable queues and persistent delivery |
| **Connection pooling** | Reuse connections, create channels |

## Comparison with Others

| Feature | RabbitMQ | Kafka | Redis |
|---------|----------|-------|-------|
| Protocol | AMQP | Custom | RESP |
| Routing | Flexible | Partition | Simple |
| Replay | No | Yes | No |
| Ordering | Per-queue | Per-partition | Per-queue |
| Use Case | Complex routing | Event streaming | Simple queues |
