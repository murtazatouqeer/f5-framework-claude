---
name: metrics-fundamentals
description: Core concepts and best practices for application metrics
category: devops/monitoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Metrics Fundamentals

## Overview

Metrics are numerical measurements collected over time that help you understand
the behavior and performance of your systems.

## Four Golden Signals

```
┌─────────────────────────────────────────────────────────────────┐
│                    Four Golden Signals                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │    LATENCY      │  │    TRAFFIC      │                       │
│  │                 │  │                 │                       │
│  │  Time to serve  │  │  Demand on      │                       │
│  │  a request      │  │  your system    │                       │
│  │                 │  │                 │                       │
│  │  • p50, p95, p99│  │  • Requests/sec │                       │
│  │  • Success vs   │  │  • Sessions     │                       │
│  │    error latency│  │  • Throughput   │                       │
│  └─────────────────┘  └─────────────────┘                       │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │    ERRORS       │  │   SATURATION    │                       │
│  │                 │  │                 │                       │
│  │  Rate of failed │  │  How full your  │                       │
│  │  requests       │  │  service is     │                       │
│  │                 │  │                 │                       │
│  │  • Error rate   │  │  • CPU usage    │                       │
│  │  • Error types  │  │  • Memory usage │                       │
│  │  • HTTP 5xx     │  │  • Queue depth  │                       │
│  └─────────────────┘  └─────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Metric Types

### Counter

Cumulative metric that only increases or resets to zero.

```typescript
// Use for: request counts, errors, completed tasks
import { Counter } from 'prom-client';

const httpRequestsTotal = new Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'path', 'status'],
});

// Increment
httpRequestsTotal.inc();
httpRequestsTotal.inc({ method: 'GET', path: '/api/users', status: '200' });
httpRequestsTotal.inc({ method: 'POST', path: '/api/users', status: '201' }, 1);
```

### Gauge

Metric that can go up or down.

```typescript
// Use for: temperature, memory usage, queue size, active connections
import { Gauge } from 'prom-client';

const activeConnections = new Gauge({
  name: 'active_connections',
  help: 'Number of active connections',
  labelNames: ['type'],
});

// Set, increment, decrement
activeConnections.set(100);
activeConnections.inc();
activeConnections.inc(5);
activeConnections.dec();
activeConnections.dec(3);

// Memory usage
const memoryUsageGauge = new Gauge({
  name: 'nodejs_memory_usage_bytes',
  help: 'Memory usage in bytes',
  labelNames: ['type'],
  collect() {
    const usage = process.memoryUsage();
    this.set({ type: 'heapUsed' }, usage.heapUsed);
    this.set({ type: 'heapTotal' }, usage.heapTotal);
    this.set({ type: 'rss' }, usage.rss);
  },
});
```

### Histogram

Samples observations and counts them in configurable buckets.

```typescript
// Use for: request duration, response sizes
import { Histogram } from 'prom-client';

const httpRequestDuration = new Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration in seconds',
  labelNames: ['method', 'path', 'status'],
  buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10],
});

// Observe
const timer = httpRequestDuration.startTimer();
// ... do work ...
timer({ method: 'GET', path: '/api/users', status: '200' });

// Or manual observation
httpRequestDuration.observe({ method: 'GET', path: '/api/users', status: '200' }, 0.5);
```

### Summary

Similar to histogram but calculates quantiles on the client side.

```typescript
// Use for: request duration when precise quantiles needed
import { Summary } from 'prom-client';

const httpRequestDurationSummary = new Summary({
  name: 'http_request_duration_summary_seconds',
  help: 'HTTP request duration summary',
  labelNames: ['method', 'path'],
  percentiles: [0.5, 0.9, 0.95, 0.99],
  maxAgeSeconds: 600,
  ageBuckets: 5,
});

// Observe
const end = httpRequestDurationSummary.startTimer();
// ... do work ...
end({ method: 'GET', path: '/api/users' });
```

## Naming Conventions

```yaml
# Metric Naming Best Practices
format: <namespace>_<name>_<unit>

examples:
  # Counters (use _total suffix)
  - http_requests_total
  - database_queries_total
  - cache_hits_total
  - errors_total

  # Gauges
  - temperature_celsius
  - memory_usage_bytes
  - queue_length
  - active_connections

  # Histograms/Summaries (use appropriate unit suffix)
  - http_request_duration_seconds
  - request_size_bytes
  - response_size_bytes

units:
  - seconds (for time durations)
  - bytes (for data sizes)
  - total (for counters)
  - ratio (for percentages as 0-1)
```

## Labels

```typescript
// Good label usage
const httpRequests = new Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status', 'service'],
});

// Guidelines for labels:
// ✅ DO: Use labels with low cardinality
// ✅ DO: method: GET, POST, PUT, DELETE
// ✅ DO: status: 200, 201, 400, 500
// ✅ DO: environment: production, staging

// ❌ DON'T: Use high cardinality labels
// ❌ DON'T: user_id (millions of unique values)
// ❌ DON'T: request_id (unique per request)
// ❌ DON'T: timestamp (constantly changing)

// Path normalization to reduce cardinality
function normalizePath(path: string): string {
  return path
    .replace(/\/users\/\d+/, '/users/:id')
    .replace(/\/orders\/[a-f0-9-]+/, '/orders/:id')
    .replace(/\?.*$/, '');
}
```

## Application Metrics Setup

### Express.js with prom-client

```typescript
// metrics.ts
import express from 'express';
import client from 'prom-client';

// Create registry
const register = new client.Registry();

// Add default metrics (Node.js metrics)
client.collectDefaultMetrics({ register });

// Custom metrics
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.001, 0.005, 0.015, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 1, 2, 5],
  registers: [register],
});

const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
  registers: [register],
});

const httpActiveRequests = new client.Gauge({
  name: 'http_active_requests',
  help: 'Number of active HTTP requests',
  registers: [register],
});

// Middleware
export function metricsMiddleware(
  req: express.Request,
  res: express.Response,
  next: express.NextFunction
) {
  const start = process.hrtime();
  httpActiveRequests.inc();

  res.on('finish', () => {
    const [seconds, nanoseconds] = process.hrtime(start);
    const duration = seconds + nanoseconds / 1e9;
    const route = req.route?.path || req.path;

    httpRequestDuration.observe(
      {
        method: req.method,
        route: normalizePath(route),
        status_code: res.statusCode.toString(),
      },
      duration
    );

    httpRequestsTotal.inc({
      method: req.method,
      route: normalizePath(route),
      status_code: res.statusCode.toString(),
    });

    httpActiveRequests.dec();
  });

  next();
}

// Metrics endpoint
export function metricsEndpoint(app: express.Application) {
  app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
  });
}
```

### NestJS with Prometheus

```typescript
// prometheus.module.ts
import { Module, Global } from '@nestjs/common';
import { PrometheusModule } from '@willsoto/nestjs-prometheus';
import { makeCounterProvider, makeHistogramProvider } from '@willsoto/nestjs-prometheus';

@Global()
@Module({
  imports: [
    PrometheusModule.register({
      defaultMetrics: {
        enabled: true,
      },
      path: '/metrics',
    }),
  ],
  providers: [
    makeCounterProvider({
      name: 'http_requests_total',
      help: 'Total number of HTTP requests',
      labelNames: ['method', 'path', 'status'],
    }),
    makeHistogramProvider({
      name: 'http_request_duration_seconds',
      help: 'HTTP request duration in seconds',
      labelNames: ['method', 'path', 'status'],
      buckets: [0.001, 0.005, 0.015, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 1, 2, 5],
    }),
  ],
  exports: [PrometheusModule],
})
export class MetricsModule {}

// metrics.interceptor.ts
import { Injectable, NestInterceptor, ExecutionContext, CallHandler } from '@nestjs/common';
import { Observable } from 'rxjs';
import { tap } from 'rxjs/operators';
import { InjectMetric } from '@willsoto/nestjs-prometheus';
import { Counter, Histogram } from 'prom-client';

@Injectable()
export class MetricsInterceptor implements NestInterceptor {
  constructor(
    @InjectMetric('http_requests_total') private readonly counter: Counter<string>,
    @InjectMetric('http_request_duration_seconds') private readonly histogram: Histogram<string>
  ) {}

  intercept(context: ExecutionContext, next: CallHandler): Observable<any> {
    const request = context.switchToHttp().getRequest();
    const response = context.switchToHttp().getResponse();
    const end = this.histogram.startTimer();

    return next.handle().pipe(
      tap(() => {
        const labels = {
          method: request.method,
          path: request.route?.path || request.path,
          status: response.statusCode.toString(),
        };
        this.counter.inc(labels);
        end(labels);
      })
    );
  }
}
```

## Business Metrics

```typescript
// business-metrics.ts
import { Counter, Gauge, Histogram } from 'prom-client';

// Order metrics
const ordersTotal = new Counter({
  name: 'orders_total',
  help: 'Total number of orders',
  labelNames: ['status', 'payment_method', 'region'],
});

const orderValueTotal = new Counter({
  name: 'order_value_total',
  help: 'Total value of orders',
  labelNames: ['currency'],
});

const orderProcessingDuration = new Histogram({
  name: 'order_processing_duration_seconds',
  help: 'Time to process an order',
  labelNames: ['type'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60],
});

// User metrics
const activeUsers = new Gauge({
  name: 'active_users',
  help: 'Number of active users',
  labelNames: ['plan'],
});

const userRegistrations = new Counter({
  name: 'user_registrations_total',
  help: 'Total user registrations',
  labelNames: ['source', 'plan'],
});

// Usage in service
class OrderService {
  async createOrder(order: Order) {
    const timer = orderProcessingDuration.startTimer({ type: order.type });

    try {
      const result = await this.processOrder(order);

      ordersTotal.inc({
        status: 'completed',
        payment_method: order.paymentMethod,
        region: order.region,
      });

      orderValueTotal.inc({ currency: order.currency }, order.total);

      return result;
    } catch (error) {
      ordersTotal.inc({
        status: 'failed',
        payment_method: order.paymentMethod,
        region: order.region,
      });
      throw error;
    } finally {
      timer();
    }
  }
}
```

## Infrastructure Metrics

```typescript
// infrastructure-metrics.ts
import { Gauge } from 'prom-client';
import os from 'os';

// System metrics
const systemCpuUsage = new Gauge({
  name: 'system_cpu_usage_percent',
  help: 'System CPU usage percentage',
  collect() {
    const cpus = os.cpus();
    const totalIdle = cpus.reduce((acc, cpu) => acc + cpu.times.idle, 0);
    const totalTick = cpus.reduce(
      (acc, cpu) =>
        acc + cpu.times.user + cpu.times.nice + cpu.times.sys + cpu.times.idle + cpu.times.irq,
      0
    );
    const usage = ((1 - totalIdle / totalTick) * 100).toFixed(2);
    this.set(parseFloat(usage));
  },
});

const systemMemoryUsage = new Gauge({
  name: 'system_memory_usage_bytes',
  help: 'System memory usage',
  labelNames: ['type'],
  collect() {
    const total = os.totalmem();
    const free = os.freemem();
    const used = total - free;
    this.set({ type: 'total' }, total);
    this.set({ type: 'free' }, free);
    this.set({ type: 'used' }, used);
  },
});

// Database metrics
const dbPoolSize = new Gauge({
  name: 'database_pool_size',
  help: 'Database connection pool size',
  labelNames: ['state'],
});

const dbQueryDuration = new Histogram({
  name: 'database_query_duration_seconds',
  help: 'Database query duration',
  labelNames: ['operation', 'table'],
  buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
});

// Cache metrics
const cacheHits = new Counter({
  name: 'cache_hits_total',
  help: 'Cache hit count',
  labelNames: ['cache_name'],
});

const cacheMisses = new Counter({
  name: 'cache_misses_total',
  help: 'Cache miss count',
  labelNames: ['cache_name'],
});
```

## RED Method

```
┌─────────────────────────────────────────────────────────────────┐
│                    RED Method (Request-focused)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  R - Rate                                                        │
│      Requests per second                                         │
│      rate(http_requests_total[5m])                              │
│                                                                  │
│  E - Errors                                                      │
│      Number of failed requests per second                        │
│      rate(http_requests_total{status=~"5.."}[5m])               │
│                                                                  │
│  D - Duration                                                    │
│      Distribution of request latencies                           │
│      histogram_quantile(0.99, http_request_duration_seconds)    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## USE Method

```
┌─────────────────────────────────────────────────────────────────┐
│                    USE Method (Resource-focused)                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  U - Utilization                                                 │
│      % time resource is busy                                     │
│      avg(rate(node_cpu_seconds_total{mode!="idle"}[5m]))        │
│                                                                  │
│  S - Saturation                                                  │
│      Amount of work queued                                       │
│      node_load1 / count(node_cpu_seconds_total{mode="idle"})    │
│                                                                  │
│  E - Errors                                                      │
│      Count of error events                                       │
│      rate(node_disk_io_time_weighted_seconds_total[5m])         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Metrics Best Practices                          │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use consistent naming conventions                              │
│ ☐ Keep label cardinality low (<1000 unique combinations)        │
│ ☐ Choose appropriate metric types                                │
│ ☐ Include units in metric names                                  │
│ ☐ Add meaningful help text                                       │
│ ☐ Expose metrics on /metrics endpoint                            │
│ ☐ Include both technical and business metrics                    │
│ ☐ Use histograms for latency (not summaries)                    │
│ ☐ Monitor the Four Golden Signals                                │
│ ☐ Set up recording rules for complex queries                     │
│ ☐ Document metric meanings                                       │
│ ☐ Avoid metrics that change with every request (high churn)      │
└─────────────────────────────────────────────────────────────────┘
```
