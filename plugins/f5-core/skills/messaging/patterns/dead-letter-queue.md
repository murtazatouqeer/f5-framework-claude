---
name: dead-letter-queue
description: Handling failed messages with dead letter queues
category: messaging/patterns
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Dead Letter Queue

## Overview

A Dead Letter Queue (DLQ) captures messages that cannot be processed successfully. It provides a mechanism to isolate problematic messages for analysis and reprocessing without blocking the main queue.

## Why Use DLQ

| Scenario | Without DLQ | With DLQ |
|----------|-------------|----------|
| Poison message | Blocks queue | Isolated for review |
| Processing failure | Infinite retries | Captured after max retries |
| Schema mismatch | Consumer crashes | Message preserved |
| Debugging | Lost context | Full message available |

## Basic Implementation

```typescript
interface Message {
  id: string;
  body: any;
  attributes: Record<string, string>;
  retryCount: number;
  originalQueue: string;
  error?: string;
  failedAt?: Date;
}

class DeadLetterQueue {
  private messages: Message[] = [];

  async add(message: Message, error: Error): Promise<void> {
    const dlqMessage: Message = {
      ...message,
      error: error.message,
      failedAt: new Date(),
    };

    this.messages.push(dlqMessage);

    console.log(`Message ${message.id} moved to DLQ: ${error.message}`);
  }

  async getAll(): Promise<Message[]> {
    return [...this.messages];
  }

  async getByOriginalQueue(queue: string): Promise<Message[]> {
    return this.messages.filter(m => m.originalQueue === queue);
  }

  async remove(messageId: string): Promise<boolean> {
    const index = this.messages.findIndex(m => m.id === messageId);

    if (index !== -1) {
      this.messages.splice(index, 1);
      return true;
    }

    return false;
  }

  async requeue(messageId: string, targetQueue: Queue): Promise<boolean> {
    const message = this.messages.find(m => m.id === messageId);

    if (!message) return false;

    // Reset retry count
    const requeuedMessage = {
      ...message,
      retryCount: 0,
      error: undefined,
      failedAt: undefined,
    };

    await targetQueue.add(requeuedMessage);
    await this.remove(messageId);

    return true;
  }

  async requeueAll(targetQueue: Queue): Promise<number> {
    const count = this.messages.length;

    for (const message of [...this.messages]) {
      await this.requeue(message.id, targetQueue);
    }

    return count;
  }
}
```

## Queue Processor with DLQ

```typescript
interface ProcessorOptions {
  maxRetries: number;
  retryDelay: number;
}

class QueueProcessor {
  constructor(
    private readonly queue: Queue,
    private readonly dlq: DeadLetterQueue,
    private readonly options: ProcessorOptions
  ) {}

  async process(handler: (message: Message) => Promise<void>): Promise<void> {
    while (true) {
      const message = await this.queue.receive();

      if (!message) {
        await this.sleep(1000);
        continue;
      }

      try {
        await handler(message);
        await this.queue.ack(message);
      } catch (error) {
        await this.handleFailure(message, error as Error);
      }
    }
  }

  private async handleFailure(message: Message, error: Error): Promise<void> {
    message.retryCount = (message.retryCount || 0) + 1;

    if (message.retryCount >= this.options.maxRetries) {
      // Move to DLQ
      await this.dlq.add(message, error);
      await this.queue.ack(message); // Remove from main queue
    } else {
      // Retry with delay
      await this.sleep(this.options.retryDelay * message.retryCount);
      await this.queue.nack(message); // Return to queue
    }
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

## RabbitMQ DLQ

```typescript
import amqp, { Channel } from 'amqplib';

async function setupDLQ(channel: Channel): Promise<void> {
  // Create DLX (Dead Letter Exchange)
  await channel.assertExchange('dlx', 'direct', { durable: true });

  // Create DLQ
  await channel.assertQueue('orders-dlq', {
    durable: true,
  });

  // Bind DLQ to DLX
  await channel.bindQueue('orders-dlq', 'dlx', 'orders');

  // Create main queue with DLX configuration
  await channel.assertQueue('orders', {
    durable: true,
    arguments: {
      'x-dead-letter-exchange': 'dlx',
      'x-dead-letter-routing-key': 'orders',
      'x-message-ttl': 60000, // Optional: messages expire after 60s
    },
  });
}

// Messages go to DLQ when:
// 1. Rejected without requeue: channel.nack(msg, false, false)
// 2. TTL expires
// 3. Queue length limit exceeded

async function processWithDLQ(channel: Channel): Promise<void> {
  await setupDLQ(channel);

  channel.consume('orders', async (msg) => {
    if (!msg) return;

    try {
      const content = JSON.parse(msg.content.toString());
      await processOrder(content);
      channel.ack(msg);
    } catch (error) {
      const retryCount = (msg.properties.headers?.['x-retry-count'] || 0) + 1;

      if (retryCount >= 3) {
        // Reject without requeue - goes to DLQ
        channel.nack(msg, false, false);
      } else {
        // Republish with retry count
        channel.publish('', 'orders', msg.content, {
          headers: { 'x-retry-count': retryCount },
        });
        channel.ack(msg);
      }
    }
  });
}
```

## AWS SQS DLQ

```typescript
import {
  SQSClient,
  CreateQueueCommand,
  SetQueueAttributesCommand,
  ReceiveMessageCommand,
  DeleteMessageCommand,
} from '@aws-sdk/client-sqs';

const sqs = new SQSClient({ region: 'us-east-1' });

async function setupSQSDLQ(): Promise<{ mainQueueUrl: string; dlqUrl: string }> {
  // Create DLQ
  const dlqResponse = await sqs.send(new CreateQueueCommand({
    QueueName: 'orders-dlq',
  }));
  const dlqUrl = dlqResponse.QueueUrl!;

  // Get DLQ ARN
  const dlqArn = `arn:aws:sqs:us-east-1:${process.env.AWS_ACCOUNT}:orders-dlq`;

  // Create main queue
  const mainResponse = await sqs.send(new CreateQueueCommand({
    QueueName: 'orders',
  }));
  const mainQueueUrl = mainResponse.QueueUrl!;

  // Configure redrive policy
  await sqs.send(new SetQueueAttributesCommand({
    QueueUrl: mainQueueUrl,
    Attributes: {
      RedrivePolicy: JSON.stringify({
        deadLetterTargetArn: dlqArn,
        maxReceiveCount: 3, // Move to DLQ after 3 failed receives
      }),
    },
  }));

  return { mainQueueUrl, dlqUrl };
}

// Process DLQ messages
async function processDLQ(dlqUrl: string): Promise<void> {
  const response = await sqs.send(new ReceiveMessageCommand({
    QueueUrl: dlqUrl,
    MaxNumberOfMessages: 10,
    AttributeNames: ['All'],
    MessageAttributeNames: ['All'],
  }));

  for (const message of response.Messages || []) {
    console.log('DLQ Message:', {
      messageId: message.MessageId,
      body: message.Body,
      receiveCount: message.Attributes?.ApproximateReceiveCount,
      firstReceived: message.Attributes?.ApproximateFirstReceiveTimestamp,
    });

    // Analyze and decide what to do
    const decision = await analyzeFailedMessage(message);

    if (decision === 'reprocess') {
      // Send back to main queue
      await reprocessMessage(message);
    } else if (decision === 'archive') {
      // Archive for later analysis
      await archiveMessage(message);
    }

    // Delete from DLQ
    await sqs.send(new DeleteMessageCommand({
      QueueUrl: dlqUrl,
      ReceiptHandle: message.ReceiptHandle!,
    }));
  }
}
```

## BullMQ DLQ

```typescript
import { Queue, Worker, Job } from 'bullmq';

// BullMQ automatically handles failed jobs
const orderQueue = new Queue('orders', {
  connection: { host: 'localhost', port: 6379 },
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential',
      delay: 1000,
    },
    removeOnComplete: {
      age: 3600,      // Keep completed for 1 hour
      count: 1000,    // Keep last 1000
    },
    removeOnFail: {
      age: 24 * 3600, // Keep failed for 24 hours
    },
  },
});

const worker = new Worker('orders', async (job: Job) => {
  // Process job
  await processOrder(job.data);
}, {
  connection: { host: 'localhost', port: 6379 },
});

worker.on('failed', async (job, error) => {
  if (job && job.attemptsMade >= job.opts.attempts!) {
    console.log(`Job ${job.id} moved to failed (DLQ equivalent)`);

    // Optionally move to separate DLQ
    await dlqQueue.add('failed-order', {
      originalJob: job.data,
      error: error.message,
      attempts: job.attemptsMade,
      failedAt: new Date(),
    });
  }
});

// Get failed jobs (BullMQ's built-in DLQ)
async function getFailedJobs(): Promise<Job[]> {
  return orderQueue.getFailed(0, 100);
}

// Retry failed job
async function retryFailedJob(jobId: string): Promise<void> {
  const job = await orderQueue.getJob(jobId);
  if (job) {
    await job.retry();
  }
}

// Retry all failed jobs
async function retryAllFailed(): Promise<number> {
  const failed = await orderQueue.getFailed();
  let count = 0;

  for (const job of failed) {
    await job.retry();
    count++;
  }

  return count;
}
```

## DLQ Analysis Dashboard

```typescript
interface DLQStats {
  total: number;
  byQueue: Record<string, number>;
  byError: Record<string, number>;
  byHour: Record<string, number>;
}

class DLQAnalyzer {
  constructor(private readonly dlq: DeadLetterQueue) {}

  async getStats(): Promise<DLQStats> {
    const messages = await this.dlq.getAll();

    const stats: DLQStats = {
      total: messages.length,
      byQueue: {},
      byError: {},
      byHour: {},
    };

    for (const msg of messages) {
      // By queue
      stats.byQueue[msg.originalQueue] = (stats.byQueue[msg.originalQueue] || 0) + 1;

      // By error
      const errorKey = this.categorizeError(msg.error || 'unknown');
      stats.byError[errorKey] = (stats.byError[errorKey] || 0) + 1;

      // By hour
      if (msg.failedAt) {
        const hour = msg.failedAt.toISOString().slice(0, 13);
        stats.byHour[hour] = (stats.byHour[hour] || 0) + 1;
      }
    }

    return stats;
  }

  private categorizeError(error: string): string {
    if (error.includes('timeout')) return 'timeout';
    if (error.includes('connection')) return 'connection';
    if (error.includes('validation')) return 'validation';
    if (error.includes('not found')) return 'not_found';
    return 'other';
  }

  async findPatterns(): Promise<{
    recurringErrors: string[];
    peakHours: string[];
    problematicQueues: string[];
  }> {
    const stats = await this.getStats();

    return {
      recurringErrors: Object.entries(stats.byError)
        .filter(([_, count]) => count > 10)
        .map(([error]) => error),

      peakHours: Object.entries(stats.byHour)
        .sort(([_, a], [__, b]) => b - a)
        .slice(0, 5)
        .map(([hour]) => hour),

      problematicQueues: Object.entries(stats.byQueue)
        .filter(([_, count]) => count > 5)
        .map(([queue]) => queue),
    };
  }
}
```

## Automated DLQ Processing

```typescript
class DLQProcessor {
  constructor(
    private readonly dlq: DeadLetterQueue,
    private readonly mainQueue: Queue,
    private readonly rules: ProcessingRule[]
  ) {}

  async processAutomatically(): Promise<ProcessingResult> {
    const messages = await this.dlq.getAll();
    const result: ProcessingResult = {
      requeued: 0,
      archived: 0,
      deleted: 0,
      manual: 0,
    };

    for (const message of messages) {
      const action = this.determineAction(message);

      switch (action) {
        case 'requeue':
          await this.dlq.requeue(message.id, this.mainQueue);
          result.requeued++;
          break;

        case 'archive':
          await this.archiveMessage(message);
          await this.dlq.remove(message.id);
          result.archived++;
          break;

        case 'delete':
          await this.dlq.remove(message.id);
          result.deleted++;
          break;

        case 'manual':
          result.manual++;
          break;
      }
    }

    return result;
  }

  private determineAction(message: Message): 'requeue' | 'archive' | 'delete' | 'manual' {
    for (const rule of this.rules) {
      if (rule.matches(message)) {
        return rule.action;
      }
    }
    return 'manual';
  }

  private async archiveMessage(message: Message): Promise<void> {
    // Store in archive (S3, database, etc.)
  }
}

interface ProcessingRule {
  matches: (message: Message) => boolean;
  action: 'requeue' | 'archive' | 'delete' | 'manual';
}

// Example rules
const rules: ProcessingRule[] = [
  {
    // Requeue temporary failures
    matches: (msg) => msg.error?.includes('timeout') || false,
    action: 'requeue',
  },
  {
    // Delete old messages
    matches: (msg) => {
      const age = Date.now() - (msg.failedAt?.getTime() || 0);
      return age > 7 * 24 * 60 * 60 * 1000; // 7 days
    },
    action: 'delete',
  },
  {
    // Archive validation errors
    matches: (msg) => msg.error?.includes('validation') || false,
    action: 'archive',
  },
];
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Monitor DLQ size** | Alert on growth |
| **Preserve context** | Include original headers and metadata |
| **Set retention** | Auto-delete old messages |
| **Analyze patterns** | Find root causes |
| **Automate processing** | Rules-based requeue/archive |
| **Manual review workflow** | UI for unknown errors |
