---
name: monitoring
description: Observability and monitoring for messaging systems
category: messaging/best-practices
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
version: 1.0.0
---

# Messaging Monitoring

## Overview

Effective monitoring ensures messaging systems remain healthy, performant, and reliable. Key areas include queue depth, processing latency, error rates, and consumer health.

## Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| **Queue depth** | Messages waiting | Growing consistently |
| **Processing latency** | Time to process | > SLA |
| **Error rate** | Failed messages % | > 1% |
| **Consumer lag** | Behind latest | Growing |
| **Throughput** | Messages/second | < expected |
| **DLQ size** | Failed messages | > 0 (review needed) |

## Metric Collection

### Queue Metrics

```typescript
interface QueueMetrics {
  queueName: string;
  depth: number;              // Messages waiting
  inFlight: number;           // Being processed
  oldestMessageAge: number;   // Seconds
  messagesPerSecond: number;
  errorRate: number;
}

class QueueMonitor {
  constructor(
    private readonly metricsClient: MetricsClient,
    private readonly queues: Map<string, Queue>
  ) {}

  async collectMetrics(): Promise<QueueMetrics[]> {
    const metrics: QueueMetrics[] = [];

    for (const [name, queue] of this.queues) {
      const stats = await queue.getStats();

      const queueMetrics: QueueMetrics = {
        queueName: name,
        depth: stats.waiting,
        inFlight: stats.active,
        oldestMessageAge: stats.oldestMessageAge,
        messagesPerSecond: stats.throughput,
        errorRate: stats.failedLast5m / (stats.processedLast5m || 1),
      };

      metrics.push(queueMetrics);

      // Send to monitoring system
      this.metricsClient.gauge('queue.depth', queueMetrics.depth, { queue: name });
      this.metricsClient.gauge('queue.in_flight', queueMetrics.inFlight, { queue: name });
      this.metricsClient.gauge('queue.oldest_age', queueMetrics.oldestMessageAge, { queue: name });
      this.metricsClient.gauge('queue.throughput', queueMetrics.messagesPerSecond, { queue: name });
      this.metricsClient.gauge('queue.error_rate', queueMetrics.errorRate, { queue: name });
    }

    return metrics;
  }

  startPeriodicCollection(intervalMs: number = 10000): void {
    setInterval(() => this.collectMetrics(), intervalMs);
  }
}
```

### Processing Metrics

```typescript
class ProcessingMetrics {
  constructor(private readonly metricsClient: MetricsClient) {}

  // Wrap message processing with metrics
  async trackProcessing<T>(
    queueName: string,
    messageType: string,
    processor: () => Promise<T>
  ): Promise<T> {
    const startTime = Date.now();
    const labels = { queue: queueName, type: messageType };

    try {
      const result = await processor();

      // Record success
      this.metricsClient.increment('message.processed', labels);
      this.metricsClient.histogram(
        'message.processing_time',
        Date.now() - startTime,
        labels
      );

      return result;
    } catch (error) {
      // Record failure
      this.metricsClient.increment('message.failed', {
        ...labels,
        error: (error as Error).constructor.name,
      });

      throw error;
    }
  }

  // Consumer health
  recordConsumerHeartbeat(consumerId: string): void {
    this.metricsClient.gauge('consumer.last_heartbeat', Date.now(), {
      consumer: consumerId,
    });
  }

  // Batch metrics
  recordBatch(queueName: string, batchSize: number, duration: number): void {
    this.metricsClient.histogram('batch.size', batchSize, { queue: queueName });
    this.metricsClient.histogram('batch.duration', duration, { queue: queueName });
    this.metricsClient.gauge('batch.rate', batchSize / (duration / 1000), { queue: queueName });
  }
}
```

## Consumer Lag Monitoring

### Kafka Consumer Lag

```typescript
import { Kafka, Admin } from 'kafkajs';

class KafkaLagMonitor {
  private admin: Admin;

  constructor(kafka: Kafka) {
    this.admin = kafka.admin();
  }

  async getLag(groupId: string, topics: string[]): Promise<Map<string, number>> {
    await this.admin.connect();

    const lag = new Map<string, number>();

    for (const topic of topics) {
      // Get consumer group offsets
      const consumerOffsets = await this.admin.fetchOffsets({
        groupId,
        topics: [topic],
      });

      // Get topic high watermarks
      const topicOffsets = await this.admin.fetchTopicOffsets(topic);

      let totalLag = 0;

      for (const partition of consumerOffsets[0].partitions) {
        const highWatermark = topicOffsets.find(
          t => t.partition === partition.partition
        );

        if (highWatermark) {
          const partitionLag = BigInt(highWatermark.high) - BigInt(partition.offset);
          totalLag += Number(partitionLag);
        }
      }

      lag.set(topic, totalLag);
    }

    await this.admin.disconnect();
    return lag;
  }

  async monitorLag(
    groupId: string,
    topics: string[],
    alertThreshold: number,
    intervalMs: number = 30000
  ): Promise<void> {
    setInterval(async () => {
      const lag = await this.getLag(groupId, topics);

      for (const [topic, lagValue] of lag) {
        console.log(`Consumer lag for ${topic}: ${lagValue}`);

        if (lagValue > alertThreshold) {
          await this.alertService.warn('High consumer lag', {
            groupId,
            topic,
            lag: lagValue,
            threshold: alertThreshold,
          });
        }
      }
    }, intervalMs);
  }
}
```

## Health Checks

```typescript
interface HealthStatus {
  healthy: boolean;
  checks: {
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message?: string;
    latency?: number;
  }[];
}

class MessagingHealthCheck {
  async check(): Promise<HealthStatus> {
    const checks = await Promise.all([
      this.checkBrokerConnection(),
      this.checkQueueDepth(),
      this.checkConsumerLag(),
      this.checkDLQSize(),
      this.checkProcessingRate(),
    ]);

    return {
      healthy: checks.every(c => c.status !== 'fail'),
      checks,
    };
  }

  private async checkBrokerConnection(): Promise<HealthStatus['checks'][0]> {
    const start = Date.now();

    try {
      await this.broker.ping();
      return {
        name: 'broker_connection',
        status: 'pass',
        latency: Date.now() - start,
      };
    } catch (error) {
      return {
        name: 'broker_connection',
        status: 'fail',
        message: (error as Error).message,
      };
    }
  }

  private async checkQueueDepth(): Promise<HealthStatus['checks'][0]> {
    const depth = await this.queue.getDepth();
    const threshold = 10000;

    return {
      name: 'queue_depth',
      status: depth > threshold ? 'warn' : 'pass',
      message: `Depth: ${depth}`,
    };
  }

  private async checkConsumerLag(): Promise<HealthStatus['checks'][0]> {
    const lag = await this.getLag();
    const threshold = 1000;

    return {
      name: 'consumer_lag',
      status: lag > threshold ? 'fail' : 'pass',
      message: `Lag: ${lag}`,
    };
  }

  private async checkDLQSize(): Promise<HealthStatus['checks'][0]> {
    const size = await this.dlq.getSize();

    return {
      name: 'dlq_size',
      status: size > 0 ? 'warn' : 'pass',
      message: `DLQ has ${size} messages`,
    };
  }

  private async checkProcessingRate(): Promise<HealthStatus['checks'][0]> {
    const rate = await this.getProcessingRate();
    const minRate = 10; // messages per second

    return {
      name: 'processing_rate',
      status: rate < minRate ? 'warn' : 'pass',
      message: `Rate: ${rate}/s`,
    };
  }
}

// Express health endpoint
app.get('/health', async (req, res) => {
  const health = await healthCheck.check();
  res.status(health.healthy ? 200 : 503).json(health);
});
```

## Alerting Rules

```typescript
interface AlertRule {
  name: string;
  metric: string;
  condition: 'gt' | 'lt' | 'eq';
  threshold: number;
  duration: string;
  severity: 'info' | 'warning' | 'critical';
  action: 'email' | 'slack' | 'page';
}

const alertRules: AlertRule[] = [
  {
    name: 'High queue depth',
    metric: 'queue.depth',
    condition: 'gt',
    threshold: 10000,
    duration: '5m',
    severity: 'warning',
    action: 'slack',
  },
  {
    name: 'Consumer lag critical',
    metric: 'consumer.lag',
    condition: 'gt',
    threshold: 100000,
    duration: '5m',
    severity: 'critical',
    action: 'page',
  },
  {
    name: 'High error rate',
    metric: 'message.error_rate',
    condition: 'gt',
    threshold: 0.05,
    duration: '5m',
    severity: 'critical',
    action: 'page',
  },
  {
    name: 'DLQ not empty',
    metric: 'dlq.size',
    condition: 'gt',
    threshold: 0,
    duration: '1m',
    severity: 'warning',
    action: 'slack',
  },
  {
    name: 'No messages processed',
    metric: 'message.processed.rate',
    condition: 'lt',
    threshold: 1,
    duration: '10m',
    severity: 'warning',
    action: 'slack',
  },
  {
    name: 'Consumer down',
    metric: 'consumer.count',
    condition: 'lt',
    threshold: 1,
    duration: '1m',
    severity: 'critical',
    action: 'page',
  },
];
```

## Dashboard Panels

```typescript
// Grafana dashboard configuration
const dashboardConfig = {
  title: 'Messaging System Overview',
  panels: [
    {
      title: 'Queue Depth',
      type: 'timeseries',
      query: 'queue_depth{queue=~"$queue"}',
      thresholds: [
        { value: 5000, color: 'yellow' },
        { value: 10000, color: 'red' },
      ],
    },
    {
      title: 'Processing Rate',
      type: 'timeseries',
      query: 'rate(messages_processed_total[1m])',
    },
    {
      title: 'Error Rate',
      type: 'gauge',
      query: 'sum(rate(messages_failed_total[5m])) / sum(rate(messages_processed_total[5m]))',
      max: 0.1,
      thresholds: [
        { value: 0.01, color: 'green' },
        { value: 0.05, color: 'yellow' },
        { value: 0.1, color: 'red' },
      ],
    },
    {
      title: 'Consumer Lag',
      type: 'timeseries',
      query: 'consumer_lag{group=~"$group"}',
    },
    {
      title: 'Processing Latency (p99)',
      type: 'timeseries',
      query: 'histogram_quantile(0.99, rate(processing_time_bucket[5m]))',
    },
    {
      title: 'DLQ Size',
      type: 'stat',
      query: 'dlq_size',
      color: 'red',
    },
  ],
};
```

## Distributed Tracing

```typescript
import { trace, context, SpanKind } from '@opentelemetry/api';

class TracedMessageProcessor {
  private tracer = trace.getTracer('messaging-service');

  async processWithTracing(message: Message): Promise<void> {
    // Extract context from message headers
    const parentContext = this.extractContext(message);

    // Create span for processing
    const span = this.tracer.startSpan(
      `process ${message.type}`,
      {
        kind: SpanKind.CONSUMER,
        attributes: {
          'messaging.system': 'rabbitmq',
          'messaging.destination': message.queue,
          'messaging.message_id': message.id,
          'messaging.correlation_id': message.correlationId,
        },
      },
      parentContext
    );

    try {
      await context.with(trace.setSpan(context.active(), span), async () => {
        await this.handler(message);
      });

      span.setStatus({ code: 0 }); // OK
    } catch (error) {
      span.setStatus({
        code: 2, // ERROR
        message: (error as Error).message,
      });
      span.recordException(error as Error);
      throw error;
    } finally {
      span.end();
    }
  }

  private extractContext(message: Message): any {
    // Extract trace context from message headers
    return propagation.extract(context.active(), message.headers);
  }
}
```

## Best Practices

| Practice | Implementation |
|----------|----------------|
| **Monitor queue depth** | Alert on growth trends |
| **Track consumer lag** | Ensure consumers keep up |
| **Measure latency** | End-to-end message time |
| **Watch error rates** | Catch issues early |
| **Check DLQ regularly** | Review failed messages |
| **Use distributed tracing** | Follow message flow |
| **Set SLOs** | Define acceptable thresholds |
| **Automate alerts** | Page on critical issues |
