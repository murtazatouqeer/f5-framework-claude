---
name: async-processing
description: Async processing patterns for API performance
category: performance/api
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Async Processing

## Overview

Async processing offloads time-consuming tasks from the request/response cycle,
improving API responsiveness and user experience.

## When to Use Async Processing

| Scenario | Sync | Async |
|----------|------|-------|
| Response time < 200ms | ✅ | - |
| Response time 200ms-2s | Consider | ✅ |
| Response time > 2s | - | ✅ |
| External API calls | ✅ | ✅ |
| File processing | - | ✅ |
| Email/notification | - | ✅ |
| Report generation | - | ✅ |

## Pattern 1: Fire and Forget

For tasks where the result isn't needed immediately.

```typescript
// Email sending - don't wait for completion
app.post('/api/users', async (req, res) => {
  const user = await prisma.user.create({ data: req.body });

  // Fire and forget - don't await
  sendWelcomeEmail(user.email).catch(console.error);

  // Return immediately
  res.status(201).json(user);
});

async function sendWelcomeEmail(email: string): Promise<void> {
  // This runs after response is sent
  await emailService.send({
    to: email,
    template: 'welcome',
  });
}
```

## Pattern 2: Job Queue

For reliable async processing with retries.

### BullMQ Implementation

```typescript
import { Queue, Worker, Job } from 'bullmq';
import { Redis } from 'ioredis';

const connection = new Redis({
  host: process.env.REDIS_HOST,
  port: 6379,
});

// Create queue
const emailQueue = new Queue('email', { connection });

// API endpoint - add job to queue
app.post('/api/orders', async (req, res) => {
  const order = await prisma.order.create({ data: req.body });

  // Add job to queue
  await emailQueue.add('order-confirmation', {
    orderId: order.id,
    userEmail: req.user.email,
  }, {
    attempts: 3,
    backoff: { type: 'exponential', delay: 1000 },
  });

  res.status(201).json(order);
});

// Worker - process jobs
const worker = new Worker('email', async (job: Job) => {
  const { orderId, userEmail } = job.data;

  const order = await prisma.order.findUnique({
    where: { id: orderId },
    include: { items: { include: { product: true } } },
  });

  await emailService.send({
    to: userEmail,
    template: 'order-confirmation',
    data: { order },
  });

  return { sent: true };
}, { connection });

worker.on('completed', (job) => {
  console.log(`Job ${job.id} completed`);
});

worker.on('failed', (job, err) => {
  console.error(`Job ${job?.id} failed:`, err);
});
```

### Job Types

```typescript
// Different queues for different priorities
const queues = {
  critical: new Queue('critical', {
    connection,
    defaultJobOptions: { priority: 1, attempts: 5 },
  }),
  normal: new Queue('normal', {
    connection,
    defaultJobOptions: { priority: 5, attempts: 3 },
  }),
  low: new Queue('low', {
    connection,
    defaultJobOptions: { priority: 10, attempts: 1 },
  }),
};

// Scheduled jobs
await queues.normal.add('daily-report', {}, {
  repeat: { cron: '0 8 * * *' }, // Daily at 8am
});

// Delayed jobs
await queues.normal.add('reminder', { userId: '123' }, {
  delay: 24 * 60 * 60 * 1000, // 24 hours from now
});

// Rate-limited jobs
await queues.normal.add('api-sync', {}, {
  rateLimiter: {
    max: 10,
    duration: 1000, // 10 per second
  },
});
```

## Pattern 3: Polling Status

For long-running tasks where client needs result.

```typescript
interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  result?: any;
  error?: string;
  createdAt: Date;
  updatedAt: Date;
}

// Start job
app.post('/api/reports', async (req, res) => {
  const jobId = crypto.randomUUID();

  // Store initial status
  await redis.set(`job:${jobId}`, JSON.stringify({
    id: jobId,
    status: 'pending',
    createdAt: new Date(),
    updatedAt: new Date(),
  }), 'EX', 86400);

  // Add to queue
  await reportQueue.add('generate', {
    jobId,
    params: req.body,
  });

  // Return job ID for polling
  res.status(202).json({
    jobId,
    statusUrl: `/api/reports/${jobId}/status`,
  });
});

// Check status
app.get('/api/reports/:jobId/status', async (req, res) => {
  const status = await redis.get(`job:${req.params.jobId}`);

  if (!status) {
    return res.status(404).json({ error: 'Job not found' });
  }

  res.json(JSON.parse(status));
});

// Worker updates status
const worker = new Worker('reports', async (job) => {
  const { jobId, params } = job.data;

  // Update to processing
  await updateJobStatus(jobId, { status: 'processing', progress: 0 });

  try {
    // Generate report with progress updates
    const report = await generateReport(params, async (progress) => {
      await updateJobStatus(jobId, { progress });
    });

    // Update to completed
    await updateJobStatus(jobId, {
      status: 'completed',
      progress: 100,
      result: { reportUrl: report.url },
    });

    return report;
  } catch (error) {
    await updateJobStatus(jobId, {
      status: 'failed',
      error: error.message,
    });
    throw error;
  }
}, { connection });

async function updateJobStatus(jobId: string, updates: Partial<JobStatus>): Promise<void> {
  const current = await redis.get(`job:${jobId}`);
  if (current) {
    const status = JSON.parse(current);
    await redis.set(`job:${jobId}`, JSON.stringify({
      ...status,
      ...updates,
      updatedAt: new Date(),
    }), 'EX', 86400);
  }
}
```

## Pattern 4: Webhooks

Notify clients when async work completes.

```typescript
// Register webhook
app.post('/api/exports', async (req, res) => {
  const { data, webhookUrl } = req.body;
  const jobId = crypto.randomUUID();

  await exportQueue.add('export', {
    jobId,
    data,
    webhookUrl,
  });

  res.status(202).json({ jobId });
});

// Worker sends webhook on completion
const worker = new Worker('exports', async (job) => {
  const { jobId, data, webhookUrl } = job.data;

  const result = await processExport(data);

  // Send webhook notification
  if (webhookUrl) {
    await sendWebhook(webhookUrl, {
      event: 'export.completed',
      jobId,
      result,
      timestamp: new Date().toISOString(),
    });
  }

  return result;
}, { connection });

async function sendWebhook(
  url: string,
  payload: any,
  retries: number = 3
): Promise<void> {
  for (let attempt = 0; attempt < retries; attempt++) {
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Webhook-Signature': generateSignature(payload),
        },
        body: JSON.stringify(payload),
      });

      if (response.ok) return;

      if (response.status >= 400 && response.status < 500) {
        // Client error, don't retry
        console.error(`Webhook failed: ${response.status}`);
        return;
      }
    } catch (error) {
      console.error(`Webhook attempt ${attempt + 1} failed:`, error);
    }

    // Exponential backoff
    await sleep(1000 * Math.pow(2, attempt));
  }
}
```

## Pattern 5: Server-Sent Events (SSE)

Real-time progress updates without polling.

```typescript
// SSE endpoint for job progress
app.get('/api/jobs/:jobId/progress', async (req, res) => {
  const { jobId } = req.params;

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');

  // Subscribe to job updates
  const subscriber = new Redis(process.env.REDIS_URL);
  await subscriber.subscribe(`job:${jobId}:updates`);

  subscriber.on('message', (channel, message) => {
    const data = JSON.parse(message);
    res.write(`data: ${JSON.stringify(data)}\n\n`);

    if (data.status === 'completed' || data.status === 'failed') {
      subscriber.unsubscribe();
      subscriber.quit();
      res.end();
    }
  });

  // Handle client disconnect
  req.on('close', () => {
    subscriber.unsubscribe();
    subscriber.quit();
  });

  // Send initial status
  const status = await redis.get(`job:${jobId}`);
  if (status) {
    res.write(`data: ${status}\n\n`);
  }
});

// Worker publishes updates
async function publishJobUpdate(jobId: string, update: any): Promise<void> {
  await redis.publish(`job:${jobId}:updates`, JSON.stringify(update));
}
```

## Pattern 6: Background Workers

For continuous background processing.

```typescript
// Background worker for data sync
class DataSyncWorker {
  private running = false;
  private interval: NodeJS.Timeout | null = null;

  start(intervalMs: number = 60000): void {
    if (this.running) return;

    this.running = true;
    this.interval = setInterval(() => this.sync(), intervalMs);

    // Run immediately
    this.sync();

    console.log('Data sync worker started');
  }

  stop(): void {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
    }
    this.running = false;
    console.log('Data sync worker stopped');
  }

  private async sync(): Promise<void> {
    if (!this.running) return;

    try {
      // Get pending sync items
      const items = await prisma.syncQueue.findMany({
        where: { status: 'pending' },
        take: 100,
      });

      for (const item of items) {
        try {
          await this.processItem(item);
          await prisma.syncQueue.update({
            where: { id: item.id },
            data: { status: 'completed', completedAt: new Date() },
          });
        } catch (error) {
          await prisma.syncQueue.update({
            where: { id: item.id },
            data: {
              status: 'failed',
              error: error.message,
              retries: { increment: 1 },
            },
          });
        }
      }
    } catch (error) {
      console.error('Sync error:', error);
    }
  }

  private async processItem(item: SyncQueueItem): Promise<void> {
    // Process sync item
    await externalApi.sync(item.data);
  }
}

// Start worker on app init
const syncWorker = new DataSyncWorker();
syncWorker.start();

// Graceful shutdown
process.on('SIGTERM', () => {
  syncWorker.stop();
});
```

## Error Handling & Retries

```typescript
// Retry configuration
const retryConfig = {
  attempts: 3,
  backoff: {
    type: 'exponential' as const,
    delay: 1000, // Start with 1 second
  },
};

// Dead letter queue for failed jobs
const deadLetterQueue = new Queue('dead-letter', { connection });

const worker = new Worker('tasks', async (job) => {
  try {
    return await processTask(job.data);
  } catch (error) {
    if (job.attemptsMade >= retryConfig.attempts - 1) {
      // Max retries reached, move to dead letter queue
      await deadLetterQueue.add('failed-task', {
        originalJob: job.data,
        error: error.message,
        attempts: job.attemptsMade + 1,
        failedAt: new Date(),
      });
    }
    throw error;
  }
}, {
  connection,
  ...retryConfig,
});

// Monitor dead letter queue
const dlqWorker = new Worker('dead-letter', async (job) => {
  // Log, alert, or attempt manual recovery
  console.error('Dead letter job:', job.data);
  await alertService.notify(`Job failed: ${job.data.originalJob.type}`);
}, { connection });
```

## Best Practices

1. **Use queues for reliability** - Don't fire-and-forget critical tasks
2. **Implement idempotency** - Jobs may be retried
3. **Set appropriate timeouts** - Prevent hung jobs
4. **Monitor queue depth** - Alert on backlog
5. **Use dead letter queues** - Handle permanent failures
6. **Provide status endpoints** - Let clients check progress
7. **Implement graceful shutdown** - Finish current jobs
8. **Log comprehensively** - Debug async issues
