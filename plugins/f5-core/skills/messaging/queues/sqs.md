---
name: sqs
description: AWS Simple Queue Service for managed message queuing
category: messaging/queues
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# AWS SQS

## Overview

Amazon Simple Queue Service (SQS) is a fully managed message queuing service. It eliminates the complexity of managing message infrastructure while providing reliability and scalability.

## Queue Types

| Type | Ordering | Throughput | Deduplication |
|------|----------|------------|---------------|
| **Standard** | Best-effort | Unlimited | None |
| **FIFO** | Guaranteed | 3,000 msg/s (batch) | Built-in |

## Setup

```typescript
import {
  SQSClient,
  CreateQueueCommand,
  SendMessageCommand,
  ReceiveMessageCommand,
  DeleteMessageCommand,
  GetQueueUrlCommand,
} from '@aws-sdk/client-sqs';

const sqs = new SQSClient({
  region: process.env.AWS_REGION || 'us-east-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

// Create queue
async function createQueue(name: string, fifo: boolean = false): Promise<string> {
  const queueName = fifo ? `${name}.fifo` : name;

  const command = new CreateQueueCommand({
    QueueName: queueName,
    Attributes: fifo ? {
      FifoQueue: 'true',
      ContentBasedDeduplication: 'true',
    } : {
      VisibilityTimeout: '30',
      MessageRetentionPeriod: '345600', // 4 days
    },
  });

  const response = await sqs.send(command);
  return response.QueueUrl!;
}
```

## Standard Queue

### Sending Messages

```typescript
interface MessageOptions {
  delaySeconds?: number;
  attributes?: Record<string, { DataType: string; StringValue: string }>;
}

async function sendMessage(
  queueUrl: string,
  body: object,
  options: MessageOptions = {}
): Promise<string> {
  const command = new SendMessageCommand({
    QueueUrl: queueUrl,
    MessageBody: JSON.stringify(body),
    DelaySeconds: options.delaySeconds,
    MessageAttributes: options.attributes,
  });

  const response = await sqs.send(command);
  return response.MessageId!;
}

// Batch send (up to 10 messages)
import { SendMessageBatchCommand } from '@aws-sdk/client-sqs';

async function sendMessageBatch(
  queueUrl: string,
  messages: Array<{ id: string; body: object }>
): Promise<void> {
  const command = new SendMessageBatchCommand({
    QueueUrl: queueUrl,
    Entries: messages.map(m => ({
      Id: m.id,
      MessageBody: JSON.stringify(m.body),
    })),
  });

  const response = await sqs.send(command);

  if (response.Failed?.length) {
    console.error('Failed messages:', response.Failed);
    throw new Error(`${response.Failed.length} messages failed`);
  }
}
```

### Receiving Messages

```typescript
interface ReceivedMessage {
  messageId: string;
  receiptHandle: string;
  body: object;
  attributes: Record<string, string>;
}

async function receiveMessages(
  queueUrl: string,
  maxMessages: number = 10,
  waitTimeSeconds: number = 20
): Promise<ReceivedMessage[]> {
  const command = new ReceiveMessageCommand({
    QueueUrl: queueUrl,
    MaxNumberOfMessages: Math.min(maxMessages, 10),
    WaitTimeSeconds: waitTimeSeconds, // Long polling
    VisibilityTimeout: 30,
    AttributeNames: ['All'],
    MessageAttributeNames: ['All'],
  });

  const response = await sqs.send(command);

  return (response.Messages || []).map(m => ({
    messageId: m.MessageId!,
    receiptHandle: m.ReceiptHandle!,
    body: JSON.parse(m.Body!),
    attributes: m.Attributes || {},
  }));
}

// Delete after processing
async function deleteMessage(
  queueUrl: string,
  receiptHandle: string
): Promise<void> {
  const command = new DeleteMessageCommand({
    QueueUrl: queueUrl,
    ReceiptHandle: receiptHandle,
  });

  await sqs.send(command);
}

// Batch delete
import { DeleteMessageBatchCommand } from '@aws-sdk/client-sqs';

async function deleteMessageBatch(
  queueUrl: string,
  messages: Array<{ id: string; receiptHandle: string }>
): Promise<void> {
  const command = new DeleteMessageBatchCommand({
    QueueUrl: queueUrl,
    Entries: messages.map(m => ({
      Id: m.id,
      ReceiptHandle: m.receiptHandle,
    })),
  });

  await sqs.send(command);
}
```

### Consumer Pattern

```typescript
class SQSConsumer {
  private running = false;
  private queueUrl: string;
  private handler: (message: ReceivedMessage) => Promise<void>;

  constructor(
    queueUrl: string,
    handler: (message: ReceivedMessage) => Promise<void>
  ) {
    this.queueUrl = queueUrl;
    this.handler = handler;
  }

  async start(): Promise<void> {
    this.running = true;

    while (this.running) {
      try {
        const messages = await receiveMessages(this.queueUrl, 10, 20);

        await Promise.all(messages.map(async (message) => {
          try {
            await this.handler(message);
            await deleteMessage(this.queueUrl, message.receiptHandle);
          } catch (error) {
            console.error('Handler error:', error);
            // Message will return to queue after visibility timeout
          }
        }));
      } catch (error) {
        console.error('Polling error:', error);
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }

  stop(): void {
    this.running = false;
  }
}

// Usage
const consumer = new SQSConsumer(queueUrl, async (message) => {
  console.log('Processing:', message.body);
  await processOrder(message.body);
});

consumer.start();
```

## FIFO Queue

```typescript
// FIFO requires message group ID and deduplication ID
async function sendFifoMessage(
  queueUrl: string,
  body: object,
  messageGroupId: string,
  deduplicationId?: string
): Promise<string> {
  const command = new SendMessageCommand({
    QueueUrl: queueUrl,
    MessageBody: JSON.stringify(body),
    MessageGroupId: messageGroupId,
    // If ContentBasedDeduplication is disabled:
    MessageDeduplicationId: deduplicationId || crypto.randomUUID(),
  });

  const response = await sqs.send(command);
  return response.MessageId!;
}

// Messages with same group ID are processed in order
await sendFifoMessage(fifoQueueUrl, { action: 'create' }, 'order-123');
await sendFifoMessage(fifoQueueUrl, { action: 'update' }, 'order-123');
await sendFifoMessage(fifoQueueUrl, { action: 'ship' }, 'order-123');

// Different groups can be processed in parallel
await sendFifoMessage(fifoQueueUrl, { action: 'create' }, 'order-456');
```

## Dead Letter Queue

```typescript
import { SetQueueAttributesCommand } from '@aws-sdk/client-sqs';

async function setupDeadLetterQueue(
  sourceQueueUrl: string,
  dlqArn: string,
  maxReceiveCount: number = 3
): Promise<void> {
  const command = new SetQueueAttributesCommand({
    QueueUrl: sourceQueueUrl,
    Attributes: {
      RedrivePolicy: JSON.stringify({
        deadLetterTargetArn: dlqArn,
        maxReceiveCount: maxReceiveCount,
      }),
    },
  });

  await sqs.send(command);
}

// Process DLQ messages
async function processDLQ(dlqUrl: string): Promise<void> {
  const messages = await receiveMessages(dlqUrl, 10, 0);

  for (const message of messages) {
    console.log('DLQ message:', message.body);
    console.log('Receive count:', message.attributes.ApproximateReceiveCount);

    // Analyze, fix, or archive
    await archiveFailedMessage(message);
    await deleteMessage(dlqUrl, message.receiptHandle);
  }
}
```

## Visibility Timeout

```typescript
import { ChangeMessageVisibilityCommand } from '@aws-sdk/client-sqs';

// Extend visibility timeout for long-running tasks
async function extendVisibility(
  queueUrl: string,
  receiptHandle: string,
  timeoutSeconds: number
): Promise<void> {
  const command = new ChangeMessageVisibilityCommand({
    QueueUrl: queueUrl,
    ReceiptHandle: receiptHandle,
    VisibilityTimeout: timeoutSeconds,
  });

  await sqs.send(command);
}

// Usage in long task
async function processLongTask(
  queueUrl: string,
  message: ReceivedMessage
): Promise<void> {
  const heartbeatInterval = setInterval(async () => {
    await extendVisibility(queueUrl, message.receiptHandle, 30);
  }, 15000); // Extend every 15 seconds

  try {
    await performLongRunningTask(message.body);
  } finally {
    clearInterval(heartbeatInterval);
  }
}
```

## Message Attributes

```typescript
async function sendWithAttributes(
  queueUrl: string,
  body: object,
  attributes: Record<string, string | number>
): Promise<void> {
  const messageAttributes: Record<string, any> = {};

  for (const [key, value] of Object.entries(attributes)) {
    messageAttributes[key] = {
      DataType: typeof value === 'number' ? 'Number' : 'String',
      StringValue: String(value),
    };
  }

  const command = new SendMessageCommand({
    QueueUrl: queueUrl,
    MessageBody: JSON.stringify(body),
    MessageAttributes: messageAttributes,
  });

  await sqs.send(command);
}

// Usage
await sendWithAttributes(queueUrl,
  { orderId: '123' },
  {
    priority: 'high',
    retryCount: 0,
    source: 'api',
  }
);
```

## Lambda Integration

```typescript
// Lambda handler for SQS trigger
import { SQSEvent, SQSHandler, SQSBatchResponse } from 'aws-lambda';

export const handler: SQSHandler = async (event: SQSEvent): Promise<SQSBatchResponse> => {
  const batchItemFailures: { itemIdentifier: string }[] = [];

  for (const record of event.Records) {
    try {
      const body = JSON.parse(record.body);
      await processMessage(body);
    } catch (error) {
      console.error('Failed to process:', record.messageId, error);
      batchItemFailures.push({ itemIdentifier: record.messageId });
    }
  }

  // Return failed items for retry
  return { batchItemFailures };
};

// Enable partial batch response in Lambda config:
// FunctionResponseTypes: ["ReportBatchItemFailures"]
```

## Monitoring

```typescript
import {
  CloudWatchClient,
  GetMetricDataCommand
} from '@aws-sdk/client-cloudwatch';

const cloudwatch = new CloudWatchClient({ region: 'us-east-1' });

async function getQueueMetrics(queueName: string): Promise<{
  messagesVisible: number;
  messagesInFlight: number;
  oldestMessage: number;
}> {
  const now = new Date();
  const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

  const command = new GetMetricDataCommand({
    MetricDataQueries: [
      {
        Id: 'visible',
        MetricStat: {
          Metric: {
            Namespace: 'AWS/SQS',
            MetricName: 'ApproximateNumberOfMessagesVisible',
            Dimensions: [{ Name: 'QueueName', Value: queueName }],
          },
          Period: 60,
          Stat: 'Average',
        },
      },
      {
        Id: 'inflight',
        MetricStat: {
          Metric: {
            Namespace: 'AWS/SQS',
            MetricName: 'ApproximateNumberOfMessagesNotVisible',
            Dimensions: [{ Name: 'QueueName', Value: queueName }],
          },
          Period: 60,
          Stat: 'Average',
        },
      },
      {
        Id: 'oldest',
        MetricStat: {
          Metric: {
            Namespace: 'AWS/SQS',
            MetricName: 'ApproximateAgeOfOldestMessage',
            Dimensions: [{ Name: 'QueueName', Value: queueName }],
          },
          Period: 60,
          Stat: 'Maximum',
        },
      },
    ],
    StartTime: fiveMinutesAgo,
    EndTime: now,
  });

  const response = await cloudwatch.send(command);

  return {
    messagesVisible: response.MetricDataResults?.[0]?.Values?.[0] || 0,
    messagesInFlight: response.MetricDataResults?.[1]?.Values?.[0] || 0,
    oldestMessage: response.MetricDataResults?.[2]?.Values?.[0] || 0,
  };
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Use long polling** | WaitTimeSeconds: 20 |
| **Batch operations** | Send/receive/delete in batches |
| **Set appropriate timeout** | VisibilityTimeout > processing time |
| **Implement DLQ** | Catch poison messages |
| **Use FIFO when needed** | For strict ordering requirements |
| **Monitor queue depth** | Alert on backlog growth |

## Comparison

| Feature | SQS Standard | SQS FIFO | SNS |
|---------|--------------|----------|-----|
| Ordering | Best-effort | Guaranteed | None |
| Duplicates | Possible | Prevented | Possible |
| Throughput | Unlimited | 3,000/s | Unlimited |
| Pattern | Queue | Queue | Pub/Sub |
| Persistence | Yes | Yes | No |
