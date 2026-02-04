---
name: apm-tools
description: Application Performance Monitoring tools and setup
category: performance/profiling
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# APM Tools

## Overview

Application Performance Monitoring (APM) tools provide visibility into
application health, performance bottlenecks, and error tracking in production.

## Popular APM Solutions

| Tool | Strengths | Best For |
|------|-----------|----------|
| Datadog | Full stack, infrastructure | Enterprise |
| New Relic | Deep instrumentation | Complex apps |
| Dynatrace | AI-powered, auto-discovery | Large scale |
| Sentry | Error tracking, replay | Error focus |
| Elastic APM | Open source, ELK integration | Self-hosted |
| Grafana/Tempo | Open source, distributed tracing | Cost-conscious |

## OpenTelemetry Setup

### Installation

```bash
npm install @opentelemetry/api \
  @opentelemetry/sdk-node \
  @opentelemetry/auto-instrumentations-node \
  @opentelemetry/exporter-trace-otlp-http \
  @opentelemetry/exporter-metrics-otlp-http
```

### Configuration

```typescript
// tracing.ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'my-api',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: process.env.NODE_ENV,
  }),

  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/traces',
  }),

  metricReader: new PeriodicExportingMetricReader({
    exporter: new OTLPMetricExporter({
      url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://localhost:4318/v1/metrics',
    }),
    exportIntervalMillis: 60000,
  }),

  instrumentations: [
    getNodeAutoInstrumentations({
      '@opentelemetry/instrumentation-http': {
        ignoreIncomingRequestHook: (req) => req.url === '/health',
      },
      '@opentelemetry/instrumentation-express': {},
      '@opentelemetry/instrumentation-pg': {},
      '@opentelemetry/instrumentation-redis': {},
    }),
  ],
});

sdk.start();

// Graceful shutdown
process.on('SIGTERM', () => {
  sdk.shutdown().then(() => process.exit(0));
});

export { sdk };
```

### Custom Spans

```typescript
import { trace, SpanStatusCode, context } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

async function processOrder(orderId: string): Promise<Order> {
  return tracer.startActiveSpan('processOrder', async (span) => {
    try {
      // Add attributes
      span.setAttribute('order.id', orderId);

      // Child span for database operation
      const order = await tracer.startActiveSpan('db.fetchOrder', async (dbSpan) => {
        const result = await prisma.order.findUnique({ where: { id: orderId } });
        dbSpan.setAttribute('db.rows', result ? 1 : 0);
        return result;
      });

      if (!order) {
        span.setStatus({ code: SpanStatusCode.ERROR, message: 'Order not found' });
        throw new Error('Order not found');
      }

      // Child span for external API
      await tracer.startActiveSpan('payment.process', async (paymentSpan) => {
        paymentSpan.setAttribute('payment.provider', 'stripe');
        await paymentService.processPayment(order);
      });

      span.setStatus({ code: SpanStatusCode.OK });
      return order;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR, message: (error as Error).message });
      throw error;
    } finally {
      span.end();
    }
  });
}
```

### Custom Metrics

```typescript
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('my-service');

// Counter
const requestCounter = meter.createCounter('http_requests_total', {
  description: 'Total HTTP requests',
});

// Histogram
const responseTime = meter.createHistogram('http_response_time_ms', {
  description: 'HTTP response time in milliseconds',
});

// Gauge (via observable)
const activeConnections = meter.createObservableGauge('db_connections_active', {
  description: 'Active database connections',
});

activeConnections.addCallback((result) => {
  result.observe(pool.activeCount, { database: 'primary' });
});

// Usage in middleware
app.use((req, res, next) => {
  const start = Date.now();

  res.on('finish', () => {
    requestCounter.add(1, {
      method: req.method,
      path: req.route?.path || 'unknown',
      status: res.statusCode.toString(),
    });

    responseTime.record(Date.now() - start, {
      method: req.method,
      path: req.route?.path || 'unknown',
    });
  });

  next();
});
```

## Datadog Integration

```typescript
// Datadog tracer setup
import tracer from 'dd-trace';

tracer.init({
  service: 'my-api',
  env: process.env.NODE_ENV,
  version: process.env.APP_VERSION,
  logInjection: true,
  runtimeMetrics: true,
  profiling: true,
});

// Custom spans
const span = tracer.startSpan('custom.operation');
span.setTag('user.id', userId);
span.setTag('order.total', orderTotal);
span.finish();

// Wrap functions
const wrappedFunction = tracer.wrap('operation.name', originalFunction);

// Custom metrics
const { dogstatsd } = require('dd-trace');

dogstatsd.increment('page.views', 1, ['page:home']);
dogstatsd.histogram('api.response_time', responseTime, ['endpoint:/users']);
dogstatsd.gauge('queue.size', queueSize);
```

## Sentry Integration

```typescript
import * as Sentry from '@sentry/node';
import { ProfilingIntegration } from '@sentry/profiling-node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.APP_VERSION,

  integrations: [
    new Sentry.Integrations.Http({ tracing: true }),
    new Sentry.Integrations.Express({ app }),
    new Sentry.Integrations.Prisma({ client: prisma }),
    new ProfilingIntegration(),
  ],

  tracesSampleRate: 1.0,
  profilesSampleRate: 1.0,

  beforeSend(event) {
    // Sanitize sensitive data
    if (event.request?.headers) {
      delete event.request.headers['authorization'];
    }
    return event;
  },
});

// Express integration
app.use(Sentry.Handlers.requestHandler());
app.use(Sentry.Handlers.tracingHandler());

// Routes...

app.use(Sentry.Handlers.errorHandler());

// Manual error capture
try {
  riskyOperation();
} catch (error) {
  Sentry.captureException(error, {
    tags: { component: 'payment' },
    extra: { orderId },
  });
}

// Custom transaction
const transaction = Sentry.startTransaction({
  name: 'Process Order',
  op: 'task',
});

Sentry.configureScope((scope) => {
  scope.setSpan(transaction);
});

// Child span
const span = transaction.startChild({
  op: 'db.query',
  description: 'SELECT * FROM orders',
});
// ... operation
span.finish();

transaction.finish();
```

## Grafana Stack (Prometheus + Loki + Tempo)

### Prometheus Metrics

```typescript
import promClient from 'prom-client';

// Default metrics (CPU, memory, etc.)
promClient.collectDefaultMetrics();

// Custom metrics
const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status'],
  buckets: [0.1, 0.3, 0.5, 0.7, 1, 3, 5, 7, 10],
});

const activeRequests = new promClient.Gauge({
  name: 'http_requests_active',
  help: 'Number of active HTTP requests',
});

// Middleware
app.use((req, res, next) => {
  activeRequests.inc();
  const end = httpRequestDuration.startTimer();

  res.on('finish', () => {
    activeRequests.dec();
    end({
      method: req.method,
      route: req.route?.path || 'unknown',
      status: res.statusCode,
    });
  });

  next();
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', promClient.register.contentType);
  res.end(await promClient.register.metrics());
});
```

### Structured Logging for Loki

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
  // Structured output for Loki
  transport: {
    target: 'pino-pretty', // or pino-loki for direct push
    options: {
      colorize: process.env.NODE_ENV !== 'production',
    },
  },
});

// Usage with context
const requestLogger = logger.child({
  requestId: req.id,
  userId: req.user?.id,
  path: req.path,
});

requestLogger.info({ duration: 150 }, 'Request completed');
requestLogger.error({ err, orderId }, 'Order processing failed');
```

## Dashboard Examples

### Key Metrics to Track

```yaml
# Essential APM Dashboards

request_metrics:
  - Request rate (req/s)
  - Error rate (%)
  - Response time percentiles (p50, p95, p99)
  - Active requests

infrastructure:
  - CPU usage
  - Memory usage
  - Disk I/O
  - Network I/O

database:
  - Query duration percentiles
  - Connection pool utilization
  - Slow query count
  - Error rate

business:
  - Orders per minute
  - Revenue per hour
  - User signups
  - Cart abandonment rate
```

### Grafana Dashboard JSON

```json
{
  "panels": [
    {
      "title": "Request Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(http_requests_total[5m])",
          "legendFormat": "{{method}} {{route}}"
        }
      ]
    },
    {
      "title": "Response Time P95",
      "type": "graph",
      "targets": [
        {
          "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
          "legendFormat": "P95"
        }
      ]
    },
    {
      "title": "Error Rate",
      "type": "graph",
      "targets": [
        {
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
          "legendFormat": "Error %"
        }
      ]
    }
  ]
}
```

## Alerting Rules

```yaml
# Prometheus alerting rules
groups:
  - name: api-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: SlowResponses
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow response times"
          description: "P95 response time is {{ $value }}s"

      - alert: HighMemoryUsage
        expr: process_resident_memory_bytes / node_memory_MemTotal_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
```

## Best Practices

1. **Instrument early** - Add tracing from project start
2. **Use standard conventions** - OpenTelemetry semantic conventions
3. **Sample appropriately** - 100% sampling in dev, lower in prod
4. **Set meaningful alerts** - Avoid alert fatigue
5. **Correlate traces and logs** - Use trace IDs in logs
6. **Track business metrics** - Not just technical metrics
7. **Review dashboards regularly** - Remove unused panels
8. **Document runbooks** - What to do when alerts fire
