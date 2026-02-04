---
name: nestjs-queue-processing
description: Queue and background job processing in NestJS
applies_to: nestjs
category: performance
---

# NestJS Queue Processing

## Setup with Bull

```bash
npm install @nestjs/bull bull
npm install -D @types/bull
```

```typescript
// app.module.ts
import { BullModule } from '@nestjs/bull';

@Module({
  imports: [
    BullModule.forRoot({
      redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: parseInt(process.env.REDIS_PORT, 10) || 6379,
        password: process.env.REDIS_PASSWORD,
      },
      defaultJobOptions: {
        removeOnComplete: true,
        removeOnFail: false,
        attempts: 3,
        backoff: {
          type: 'exponential',
          delay: 1000,
        },
      },
    }),
  ],
})
export class AppModule {}
```

## Basic Queue Setup

```typescript
// modules/email/email.module.ts
import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bull';
import { EmailService } from './email.service';
import { EmailProcessor } from './email.processor';

@Module({
  imports: [
    BullModule.registerQueue({
      name: 'email',
      defaultJobOptions: {
        attempts: 5,
        backoff: {
          type: 'exponential',
          delay: 2000,
        },
      },
    }),
  ],
  providers: [EmailService, EmailProcessor],
  exports: [EmailService],
})
export class EmailModule {}
```

## Job Producers

```typescript
// modules/email/email.service.ts
import { Injectable } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bull';
import { Queue, JobOptions } from 'bull';

export interface SendEmailJob {
  to: string;
  subject: string;
  template: string;
  context: Record<string, any>;
}

@Injectable()
export class EmailService {
  constructor(@InjectQueue('email') private emailQueue: Queue) {}

  async sendEmail(data: SendEmailJob, options?: JobOptions): Promise<string> {
    const job = await this.emailQueue.add('send', data, {
      priority: 1,
      ...options,
    });
    return job.id.toString();
  }

  async sendWelcomeEmail(userId: string, email: string): Promise<string> {
    return this.sendEmail({
      to: email,
      subject: 'Welcome!',
      template: 'welcome',
      context: { userId },
    });
  }

  async sendPasswordResetEmail(
    email: string,
    resetToken: string,
  ): Promise<string> {
    return this.sendEmail(
      {
        to: email,
        subject: 'Password Reset',
        template: 'password-reset',
        context: { resetToken },
      },
      {
        priority: 2, // Higher priority
        attempts: 5,
      },
    );
  }

  async scheduleBulkEmail(
    recipients: string[],
    subject: string,
    template: string,
  ): Promise<void> {
    const jobs = recipients.map((to) => ({
      name: 'send',
      data: { to, subject, template, context: {} },
      opts: { priority: 3 }, // Lower priority for bulk
    }));

    await this.emailQueue.addBulk(jobs);
  }
}
```

## Job Consumers (Processors)

```typescript
// modules/email/email.processor.ts
import {
  Processor,
  Process,
  OnQueueActive,
  OnQueueCompleted,
  OnQueueFailed,
  OnQueueError,
} from '@nestjs/bull';
import { Logger } from '@nestjs/common';
import { Job } from 'bull';
import { SendEmailJob } from './email.service';

@Processor('email')
export class EmailProcessor {
  private readonly logger = new Logger(EmailProcessor.name);

  constructor(private mailService: MailService) {}

  @Process('send')
  async handleSendEmail(job: Job<SendEmailJob>): Promise<void> {
    this.logger.log(`Processing email job ${job.id}`);

    const { to, subject, template, context } = job.data;

    try {
      await this.mailService.send({
        to,
        subject,
        template,
        context,
      });

      this.logger.log(`Email sent to ${to}`);
    } catch (error) {
      this.logger.error(`Failed to send email to ${to}`, error.stack);
      throw error; // Re-throw to trigger retry
    }
  }

  @Process('bulk')
  async handleBulkEmail(job: Job<{ emails: SendEmailJob[] }>): Promise<void> {
    const { emails } = job.data;

    for (let i = 0; i < emails.length; i++) {
      await this.mailService.send(emails[i]);
      await job.progress((i + 1) / emails.length * 100);
    }
  }

  @OnQueueActive()
  onActive(job: Job) {
    this.logger.debug(`Processing job ${job.id} of type ${job.name}`);
  }

  @OnQueueCompleted()
  onCompleted(job: Job, result: any) {
    this.logger.debug(`Job ${job.id} completed`);
  }

  @OnQueueFailed()
  onFailed(job: Job, error: Error) {
    this.logger.error(
      `Job ${job.id} failed: ${error.message}`,
      error.stack,
    );
  }

  @OnQueueError()
  onError(error: Error) {
    this.logger.error(`Queue error: ${error.message}`, error.stack);
  }
}
```

## Scheduled Jobs

```typescript
// modules/tasks/tasks.module.ts
import { Module } from '@nestjs/common';
import { BullModule } from '@nestjs/bull';
import { ScheduleModule } from '@nestjs/schedule';
import { TasksService } from './tasks.service';
import { TasksProcessor } from './tasks.processor';

@Module({
  imports: [
    ScheduleModule.forRoot(),
    BullModule.registerQueue({ name: 'tasks' }),
  ],
  providers: [TasksService, TasksProcessor],
})
export class TasksModule {}

// modules/tasks/tasks.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { Cron, CronExpression } from '@nestjs/schedule';
import { InjectQueue } from '@nestjs/bull';
import { Queue } from 'bull';

@Injectable()
export class TasksService {
  private readonly logger = new Logger(TasksService.name);

  constructor(@InjectQueue('tasks') private tasksQueue: Queue) {}

  // Run daily at midnight
  @Cron(CronExpression.EVERY_DAY_AT_MIDNIGHT)
  async handleDailyCleanup() {
    this.logger.log('Scheduling daily cleanup job');
    await this.tasksQueue.add('cleanup', {
      type: 'daily',
      timestamp: new Date(),
    });
  }

  // Run every hour
  @Cron(CronExpression.EVERY_HOUR)
  async handleHourlySync() {
    this.logger.log('Scheduling hourly sync job');
    await this.tasksQueue.add('sync', {
      type: 'hourly',
      timestamp: new Date(),
    });
  }

  // Run every 5 minutes
  @Cron('*/5 * * * *')
  async handleHealthCheck() {
    await this.tasksQueue.add('health-check', {}, { priority: 1 });
  }
}
```

## Delayed Jobs

```typescript
// modules/notifications/notifications.service.ts
import { Injectable } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bull';
import { Queue } from 'bull';

@Injectable()
export class NotificationsService {
  constructor(
    @InjectQueue('notifications') private notificationsQueue: Queue,
  ) {}

  async scheduleReminder(
    userId: string,
    message: string,
    delayMs: number,
  ): Promise<string> {
    const job = await this.notificationsQueue.add(
      'reminder',
      { userId, message },
      {
        delay: delayMs,
        jobId: `reminder-${userId}-${Date.now()}`, // Unique ID
      },
    );
    return job.id.toString();
  }

  async scheduleFollowUp(
    userId: string,
    data: any,
    scheduledTime: Date,
  ): Promise<string> {
    const delay = scheduledTime.getTime() - Date.now();

    const job = await this.notificationsQueue.add(
      'follow-up',
      { userId, ...data },
      {
        delay: Math.max(0, delay),
        attempts: 1, // No retry for scheduled notifications
      },
    );
    return job.id.toString();
  }

  async cancelScheduledJob(jobId: string): Promise<boolean> {
    const job = await this.notificationsQueue.getJob(jobId);
    if (job) {
      await job.remove();
      return true;
    }
    return false;
  }
}
```

## Job Priorities

```typescript
// common/queues/priority-queue.service.ts
import { Injectable } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bull';
import { Queue } from 'bull';

export enum JobPriority {
  CRITICAL = 1,
  HIGH = 2,
  NORMAL = 3,
  LOW = 4,
  BULK = 5,
}

@Injectable()
export class PriorityQueueService {
  constructor(@InjectQueue('priority') private queue: Queue) {}

  async addCriticalJob(name: string, data: any): Promise<string> {
    const job = await this.queue.add(name, data, {
      priority: JobPriority.CRITICAL,
      attempts: 5,
    });
    return job.id.toString();
  }

  async addHighPriorityJob(name: string, data: any): Promise<string> {
    const job = await this.queue.add(name, data, {
      priority: JobPriority.HIGH,
      attempts: 3,
    });
    return job.id.toString();
  }

  async addNormalJob(name: string, data: any): Promise<string> {
    const job = await this.queue.add(name, data, {
      priority: JobPriority.NORMAL,
    });
    return job.id.toString();
  }

  async addBulkJobs(
    jobs: Array<{ name: string; data: any }>,
  ): Promise<void> {
    const bulkJobs = jobs.map((job) => ({
      name: job.name,
      data: job.data,
      opts: { priority: JobPriority.BULK },
    }));

    await this.queue.addBulk(bulkJobs);
  }
}
```

## Rate Limiting Jobs

```typescript
// modules/api-sync/api-sync.processor.ts
import { Processor, Process } from '@nestjs/bull';
import { Job, Queue } from 'bull';

@Processor('api-sync')
export class ApiSyncProcessor {
  constructor(@InjectQueue('api-sync') private queue: Queue) {}

  @Process({
    name: 'sync',
    concurrency: 1, // Process one at a time
  })
  async handleSync(job: Job) {
    // Rate limited API calls
    await this.syncWithApi(job.data);
  }
}

// Rate limiting configuration
BullModule.registerQueue({
  name: 'api-sync',
  limiter: {
    max: 10,        // Maximum 10 jobs
    duration: 1000, // Per second
  },
});
```

## Job Progress Tracking

```typescript
// modules/import/import.processor.ts
import { Processor, Process } from '@nestjs/bull';
import { Job } from 'bull';

@Processor('import')
export class ImportProcessor {
  @Process('csv')
  async handleCsvImport(job: Job<{ fileUrl: string; userId: string }>) {
    const { fileUrl, userId } = job.data;

    // Download and parse CSV
    const rows = await this.downloadAndParse(fileUrl);
    const total = rows.length;

    for (let i = 0; i < total; i++) {
      await this.processRow(rows[i]);

      // Update progress
      const progress = Math.round(((i + 1) / total) * 100);
      await job.progress(progress);

      // Add log
      await job.log(`Processed row ${i + 1} of ${total}`);
    }

    return { processed: total };
  }
}

// Check job progress
async getJobProgress(jobId: string): Promise<number> {
  const job = await this.importQueue.getJob(jobId);
  return job ? job.progress() : 0;
}
```

## Queue Events and Monitoring

```typescript
// common/queues/queue-monitor.service.ts
import { Injectable, OnModuleInit } from '@nestjs/common';
import { InjectQueue } from '@nestjs/bull';
import { Queue, QueueEvents } from 'bull';

@Injectable()
export class QueueMonitorService implements OnModuleInit {
  private queueEvents: QueueEvents;

  constructor(@InjectQueue('email') private emailQueue: Queue) {}

  async onModuleInit() {
    this.queueEvents = new QueueEvents('email');

    this.queueEvents.on('completed', ({ jobId, returnvalue }) => {
      console.log(`Job ${jobId} completed with result:`, returnvalue);
    });

    this.queueEvents.on('failed', ({ jobId, failedReason }) => {
      console.error(`Job ${jobId} failed:`, failedReason);
    });

    this.queueEvents.on('progress', ({ jobId, data }) => {
      console.log(`Job ${jobId} progress:`, data);
    });
  }

  async getQueueStats(): Promise<QueueStats> {
    const [waiting, active, completed, failed, delayed] = await Promise.all([
      this.emailQueue.getWaitingCount(),
      this.emailQueue.getActiveCount(),
      this.emailQueue.getCompletedCount(),
      this.emailQueue.getFailedCount(),
      this.emailQueue.getDelayedCount(),
    ]);

    return { waiting, active, completed, failed, delayed };
  }

  async getFailedJobs(limit = 10): Promise<any[]> {
    const jobs = await this.emailQueue.getFailed(0, limit - 1);
    return jobs.map((job) => ({
      id: job.id,
      data: job.data,
      failedReason: job.failedReason,
      attemptsMade: job.attemptsMade,
      timestamp: job.timestamp,
    }));
  }

  async retryFailedJob(jobId: string): Promise<void> {
    const job = await this.emailQueue.getJob(jobId);
    if (job) {
      await job.retry();
    }
  }

  async retryAllFailed(): Promise<number> {
    const failed = await this.emailQueue.getFailed();
    await Promise.all(failed.map((job) => job.retry()));
    return failed.length;
  }

  async cleanQueue(): Promise<void> {
    await this.emailQueue.clean(0, 'completed');
    await this.emailQueue.clean(0, 'failed');
  }
}

interface QueueStats {
  waiting: number;
  active: number;
  completed: number;
  failed: number;
  delayed: number;
}
```

## Queue Admin UI

```typescript
// main.ts - Bull Board integration
import { createBullBoard } from '@bull-board/api';
import { BullAdapter } from '@bull-board/api/bullAdapter';
import { ExpressAdapter } from '@bull-board/express';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Get queues
  const emailQueue = app.get<Queue>('BullQueue_email');
  const tasksQueue = app.get<Queue>('BullQueue_tasks');

  // Setup Bull Board
  const serverAdapter = new ExpressAdapter();
  serverAdapter.setBasePath('/admin/queues');

  createBullBoard({
    queues: [
      new BullAdapter(emailQueue),
      new BullAdapter(tasksQueue),
    ],
    serverAdapter,
  });

  app.use('/admin/queues', serverAdapter.getRouter());

  await app.listen(3000);
}
```

## Error Handling and Retries

```typescript
// modules/orders/orders.processor.ts
import { Processor, Process } from '@nestjs/bull';
import { Job } from 'bull';

@Processor('orders')
export class OrdersProcessor {
  @Process('process-payment')
  async handlePayment(job: Job) {
    try {
      const result = await this.processPayment(job.data);
      return result;
    } catch (error) {
      // Custom retry logic
      if (this.isRetryable(error)) {
        throw error; // Will trigger retry
      }

      // Non-retryable error - fail permanently
      await job.moveToFailed({ message: error.message }, true);
      return;
    }
  }

  private isRetryable(error: Error): boolean {
    // Retry on network errors, rate limits
    const retryableErrors = ['ETIMEDOUT', 'ECONNRESET', 'RATE_LIMIT'];
    return retryableErrors.some((e) => error.message.includes(e));
  }
}

// Custom backoff strategy
BullModule.registerQueue({
  name: 'orders',
  defaultJobOptions: {
    attempts: 5,
    backoff: {
      type: 'custom',
    },
  },
  settings: {
    backoffStrategies: {
      custom: (attemptsMade: number) => {
        // Exponential backoff with jitter
        const base = 1000;
        const exponential = Math.pow(2, attemptsMade) * base;
        const jitter = Math.random() * 1000;
        return exponential + jitter;
      },
    },
  },
});
```

## Testing Queues

```typescript
// test/email.processor.spec.ts
import { Test, TestingModule } from '@nestjs/testing';
import { getQueueToken } from '@nestjs/bull';
import { EmailProcessor } from './email.processor';

describe('EmailProcessor', () => {
  let processor: EmailProcessor;
  let mockMailService: jest.Mocked<MailService>;

  beforeEach(async () => {
    mockMailService = {
      send: jest.fn().mockResolvedValue(true),
    } as any;

    const module: TestingModule = await Test.createTestingModule({
      providers: [
        EmailProcessor,
        { provide: MailService, useValue: mockMailService },
      ],
    }).compile();

    processor = module.get<EmailProcessor>(EmailProcessor);
  });

  it('should process email job', async () => {
    const job = {
      id: '1',
      data: {
        to: 'test@example.com',
        subject: 'Test',
        template: 'welcome',
        context: {},
      },
      progress: jest.fn(),
    } as any;

    await processor.handleSendEmail(job);

    expect(mockMailService.send).toHaveBeenCalledWith(job.data);
  });

  it('should throw on failure for retry', async () => {
    mockMailService.send.mockRejectedValue(new Error('Send failed'));

    const job = {
      id: '1',
      data: { to: 'test@example.com' },
    } as any;

    await expect(processor.handleSendEmail(job)).rejects.toThrow('Send failed');
  });
});
```

## Best Practices

1. **Idempotent jobs**: Design jobs that can be safely retried
2. **Small payloads**: Store large data externally, pass references
3. **Proper error handling**: Distinguish retryable vs permanent failures
4. **Monitor queues**: Track depth, processing time, failure rates
5. **Clean up**: Remove completed/failed jobs periodically
6. **Rate limiting**: Protect external services from overload

## Checklist

- [ ] Redis configured for Bull
- [ ] Queue modules created
- [ ] Processors implemented with error handling
- [ ] Retry strategies configured
- [ ] Job priorities defined
- [ ] Progress tracking implemented
- [ ] Queue monitoring/admin UI
- [ ] Scheduled jobs configured
- [ ] Queue tests written
