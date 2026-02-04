---
name: bullmq
description: Premium Node.js job queue built on Redis
category: messaging/queues
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# BullMQ

## Overview

BullMQ is a Node.js message queue and job scheduler built on Redis. It provides robust job processing with features like retries, rate limiting, job prioritization, and delayed jobs.

## Core Concepts

| Concept | Description |
|---------|-------------|
| **Queue** | Named job container |
| **Job** | Unit of work with data |
| **Worker** | Processes jobs from queue |
| **Flow** | Parent-child job relationships |
| **Scheduler** | Handles delayed/repeatable jobs |

## Setup

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

// Create worker
const worker = new Worker('orders', async (job) => {
  console.log('Processing order:', job.data);
  return { processed: true };
}, { connection });

// Enable delayed jobs (required for delays and retries)
const scheduler = new QueueScheduler('orders', { connection });
```

## Adding Jobs

```typescript
// Basic job
await orderQueue.add('process', {
  orderId: '123',
  items: [{ product: 'widget', quantity: 2 }],
});

// With options
await orderQueue.add('process', { orderId: '124' }, {
  // Job identification
  jobId: 'order-124', // Custom ID (prevents duplicates)

  // Timing
  delay: 5000,        // Wait 5 seconds before processing

  // Retry configuration
  attempts: 3,        // Max retry attempts
  backoff: {
    type: 'exponential',
    delay: 1000,      // Initial delay
  },

  // Priority (lower = higher priority)
  priority: 1,

  // Lifecycle
  removeOnComplete: {
    age: 3600,        // Remove after 1 hour
    count: 1000,      // Keep last 1000
  },
  removeOnFail: {
    age: 24 * 3600,   // Keep failed for 24 hours
  },
});

// Bulk add
await orderQueue.addBulk([
  { name: 'process', data: { orderId: '125' } },
  { name: 'process', data: { orderId: '126' } },
  { name: 'process', data: { orderId: '127' } },
]);
```

## Processing Jobs

```typescript
const worker = new Worker('orders', async (job) => {
  // Access job data
  const { orderId, items } = job.data;

  // Update progress
  await job.updateProgress(10);

  // Perform work
  const result = await processOrder(orderId, items);

  await job.updateProgress(100);

  // Return value stored in job.returnvalue
  return result;
}, {
  connection,
  concurrency: 5,              // Process 5 jobs simultaneously
  limiter: {
    max: 100,                  // Max 100 jobs
    duration: 60000,           // Per minute
  },
});

// Event handlers
worker.on('completed', (job, returnvalue) => {
  console.log(`Job ${job.id} completed with:`, returnvalue);
});

worker.on('failed', (job, error) => {
  console.error(`Job ${job?.id} failed:`, error);
});

worker.on('progress', (job, progress) => {
  console.log(`Job ${job.id} progress: ${progress}%`);
});

worker.on('error', (error) => {
  console.error('Worker error:', error);
});
```

## Job Types and Named Processors

```typescript
// Define different job types
const emailQueue = new Queue('emails', { connection });

// Add different job types
await emailQueue.add('welcome', { userId: '123', template: 'welcome' });
await emailQueue.add('receipt', { orderId: '456', email: 'user@example.com' });
await emailQueue.add('reminder', { userId: '789', reminderType: 'cart' });

// Process by job name
const worker = new Worker('emails', async (job) => {
  switch (job.name) {
    case 'welcome':
      return sendWelcomeEmail(job.data);
    case 'receipt':
      return sendReceiptEmail(job.data);
    case 'reminder':
      return sendReminderEmail(job.data);
    default:
      throw new Error(`Unknown job type: ${job.name}`);
  }
}, { connection });
```

## Delayed and Scheduled Jobs

```typescript
// Delayed job
await queue.add('reminder', { userId: '123' }, {
  delay: 24 * 60 * 60 * 1000, // 24 hours
});

// Repeatable jobs (cron)
await queue.add('daily-report', { type: 'sales' }, {
  repeat: {
    pattern: '0 9 * * *', // Every day at 9 AM
    tz: 'America/New_York',
  },
});

// Repeatable jobs (interval)
await queue.add('health-check', {}, {
  repeat: {
    every: 60000, // Every minute
    limit: 100,   // Max 100 times
  },
});

// List repeatable jobs
const repeatableJobs = await queue.getRepeatableJobs();

// Remove repeatable job
await queue.removeRepeatableByKey(repeatableJobs[0].key);
```

## Retry Strategies

```typescript
// Exponential backoff
await queue.add('process', data, {
  attempts: 5,
  backoff: {
    type: 'exponential',
    delay: 1000, // 1s, 2s, 4s, 8s, 16s
  },
});

// Fixed delay
await queue.add('process', data, {
  attempts: 3,
  backoff: {
    type: 'fixed',
    delay: 5000, // Always 5 seconds
  },
});

// Custom backoff in worker
const worker = new Worker('queue', async (job) => {
  try {
    await doWork(job.data);
  } catch (error) {
    if (isRetryable(error)) {
      throw error; // Will retry
    }
    // Move to failed without retry
    throw new UnrecoverableError('Cannot process this job');
  }
}, {
  connection,
  settings: {
    backoffStrategy: (attemptsMade) => {
      // Custom delay calculation
      return Math.min(attemptsMade * 1000, 30000);
    },
  },
});
```

## Job Flows (Parent-Child)

```typescript
import { FlowProducer } from 'bullmq';

const flowProducer = new FlowProducer({ connection });

// Create flow with dependencies
const flow = await flowProducer.add({
  name: 'complete-order',
  queueName: 'orders',
  data: { orderId: '123' },
  children: [
    {
      name: 'charge-payment',
      queueName: 'payments',
      data: { amount: 99.99 },
    },
    {
      name: 'reserve-inventory',
      queueName: 'inventory',
      data: { items: [{ sku: 'ABC', qty: 2 }] },
    },
    {
      name: 'send-confirmation',
      queueName: 'emails',
      data: { template: 'order-confirmed' },
      children: [
        {
          name: 'charge-payment', // Must complete first
          queueName: 'payments',
          data: { amount: 99.99 },
        },
      ],
    },
  ],
});

// Parent job waits for all children
// Children can have their own children (nested flows)
```

## Rate Limiting

```typescript
// Global rate limit
const worker = new Worker('api-calls', processor, {
  connection,
  limiter: {
    max: 10,       // 10 jobs
    duration: 1000, // Per second
  },
});

// Group rate limiting
const worker = new Worker('user-requests', processor, {
  connection,
  limiter: {
    max: 5,
    duration: 1000,
    groupKey: 'userId', // Rate limit per user
  },
});

// Add job with group key
await queue.add('request', { userId: 'user-123', action: 'fetch' });
```

## Queue Events

```typescript
import { QueueEvents } from 'bullmq';

const queueEvents = new QueueEvents('orders', { connection });

queueEvents.on('completed', ({ jobId, returnvalue }) => {
  console.log(`Job ${jobId} completed:`, returnvalue);
});

queueEvents.on('failed', ({ jobId, failedReason }) => {
  console.error(`Job ${jobId} failed:`, failedReason);
});

queueEvents.on('progress', ({ jobId, data }) => {
  console.log(`Job ${jobId} progress:`, data);
});

queueEvents.on('waiting', ({ jobId }) => {
  console.log(`Job ${jobId} is waiting`);
});

queueEvents.on('active', ({ jobId }) => {
  console.log(`Job ${jobId} is active`);
});

queueEvents.on('delayed', ({ jobId, delay }) => {
  console.log(`Job ${jobId} delayed for ${delay}ms`);
});
```

## Queue Management

```typescript
// Get queue state
const waiting = await queue.getWaitingCount();
const active = await queue.getActiveCount();
const completed = await queue.getCompletedCount();
const failed = await queue.getFailedCount();
const delayed = await queue.getDelayedCount();

// Get jobs
const waitingJobs = await queue.getWaiting(0, 10);
const failedJobs = await queue.getFailed(0, 10);

// Get specific job
const job = await queue.getJob('job-id');

// Retry failed job
await job.retry();

// Remove job
await job.remove();

// Pause/resume queue
await queue.pause();
await queue.resume();

// Drain queue (remove all jobs)
await queue.drain();

// Obliterate queue (remove everything including history)
await queue.obliterate({ force: true });
```

## Graceful Shutdown

```typescript
async function shutdown(): Promise<void> {
  console.log('Shutting down...');

  // Stop accepting new jobs
  await worker.pause();

  // Wait for current jobs to complete (with timeout)
  await worker.close();

  // Close queue
  await queue.close();

  // Close scheduler
  await scheduler.close();

  // Close Redis connection
  await connection.quit();

  console.log('Shutdown complete');
}

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);
```

## Sandboxed Processors

```typescript
// Run processor in separate process (isolation)
const worker = new Worker('heavy-tasks',
  path.join(__dirname, 'processor.js'), // Path to processor file
  {
    connection,
    useWorkerThreads: true, // Use worker threads instead of child processes
  }
);

// processor.js
module.exports = async (job) => {
  // Heavy computation isolated from main process
  const result = await heavyComputation(job.data);
  return result;
};
```

## Monitoring with Bull Board

```typescript
import { createBullBoard } from '@bull-board/api';
import { BullMQAdapter } from '@bull-board/api/bullMQAdapter';
import { ExpressAdapter } from '@bull-board/express';
import express from 'express';

const serverAdapter = new ExpressAdapter();

createBullBoard({
  queues: [
    new BullMQAdapter(orderQueue),
    new BullMQAdapter(emailQueue),
    new BullMQAdapter(paymentQueue),
  ],
  serverAdapter,
});

const app = express();
serverAdapter.setBasePath('/admin/queues');
app.use('/admin/queues', serverAdapter.getRouter());

app.listen(3000, () => {
  console.log('Bull Board available at http://localhost:3000/admin/queues');
});
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use job IDs** | Prevent duplicate processing |
| **Set removeOnComplete** | Prevent Redis memory growth |
| **Configure retries** | Handle transient failures |
| **Use concurrency** | Match to available resources |
| **Implement graceful shutdown** | Complete active jobs before exit |
| **Monitor queue metrics** | Track depth, latency, failure rate |
| **Use named processors** | Organize job types logically |

## Comparison with Bull

| Feature | BullMQ | Bull (v3) |
|---------|--------|-----------|
| Job flows | ✅ | ❌ |
| Group rate limiting | ✅ | ❌ |
| Worker threads | ✅ | ❌ |
| TypeScript | Native | Via @types |
| Maintenance | Active | Maintenance only |
| Redis | 6+ | 2.8+ |
