---
name: performance-metrics
description: Key performance metrics and measurement techniques
category: performance/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Performance Metrics

## Overview

Understanding and measuring performance metrics is the foundation of optimization.
You can't improve what you don't measure.

## Web Performance Metrics

### Core Web Vitals (Google)

```
┌─────────────────────────────────────────────────────────────┐
│                    Core Web Vitals                          │
├─────────────────┬─────────────────┬─────────────────────────┤
│      LCP        │      FID        │         CLS             │
│  Loading        │  Interactivity  │    Visual Stability     │
├─────────────────┼─────────────────┼─────────────────────────┤
│  Good: < 2.5s   │  Good: < 100ms  │    Good: < 0.1          │
│  Poor: > 4.0s   │  Poor: > 300ms  │    Poor: > 0.25         │
└─────────────────┴─────────────────┴─────────────────────────┘
```

#### Largest Contentful Paint (LCP)

Measures loading performance - when the largest content element becomes visible.

```typescript
// Measure LCP using PerformanceObserver
const observer = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  const lastEntry = entries[entries.length - 1];
  console.log('LCP:', lastEntry.startTime);
});

observer.observe({ type: 'largest-contentful-paint', buffered: true });
```

#### First Input Delay (FID)

Measures interactivity - time from first user interaction to browser response.

```typescript
// Measure FID
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    const fid = entry.processingStart - entry.startTime;
    console.log('FID:', fid);
  }
});

observer.observe({ type: 'first-input', buffered: true });
```

#### Cumulative Layout Shift (CLS)

Measures visual stability - how much content shifts during page load.

```typescript
// Measure CLS
let clsValue = 0;
const observer = new PerformanceObserver((list) => {
  for (const entry of list.getEntries()) {
    if (!entry.hadRecentInput) {
      clsValue += entry.value;
    }
  }
  console.log('CLS:', clsValue);
});

observer.observe({ type: 'layout-shift', buffered: true });
```

### Additional Web Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **TTFB** | Time to First Byte | < 200ms |
| **FCP** | First Contentful Paint | < 1.8s |
| **TTI** | Time to Interactive | < 3.8s |
| **TBT** | Total Blocking Time | < 200ms |
| **SI** | Speed Index | < 3.4s |

## Backend Performance Metrics

### Response Time

```typescript
// Measure API response time
import { performance } from 'perf_hooks';

async function measureResponseTime<T>(
  operation: () => Promise<T>,
  name: string
): Promise<T> {
  const start = performance.now();
  try {
    return await operation();
  } finally {
    const duration = performance.now() - start;
    console.log(`${name}: ${duration.toFixed(2)}ms`);

    // Report to monitoring
    metrics.histogram('api.response_time', duration, { operation: name });
  }
}
```

### Percentiles

```typescript
// Calculate percentiles from measurements
function calculatePercentile(values: number[], percentile: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.ceil((percentile / 100) * sorted.length) - 1;
  return sorted[index];
}

// Usage
const responseTimes = [45, 52, 48, 120, 55, 49, 51, 200, 47, 53];
console.log('P50:', calculatePercentile(responseTimes, 50)); // Median
console.log('P95:', calculatePercentile(responseTimes, 95)); // 95th percentile
console.log('P99:', calculatePercentile(responseTimes, 99)); // 99th percentile
```

### Throughput

```typescript
// Measure requests per second
class ThroughputMeter {
  private requestCount = 0;
  private startTime = Date.now();
  private windowMs = 60000; // 1 minute window

  recordRequest(): void {
    this.requestCount++;

    // Reset window if needed
    if (Date.now() - this.startTime > this.windowMs) {
      this.reset();
    }
  }

  getRequestsPerSecond(): number {
    const elapsedSeconds = (Date.now() - this.startTime) / 1000;
    return this.requestCount / elapsedSeconds;
  }

  private reset(): void {
    this.requestCount = 0;
    this.startTime = Date.now();
  }
}
```

### Error Rate

```typescript
// Track error rate
class ErrorRateTracker {
  private total = 0;
  private errors = 0;

  recordSuccess(): void {
    this.total++;
  }

  recordError(): void {
    this.total++;
    this.errors++;
  }

  getErrorRate(): number {
    return this.total === 0 ? 0 : (this.errors / this.total) * 100;
  }

  reset(): void {
    this.total = 0;
    this.errors = 0;
  }
}
```

## Database Metrics

### Query Performance

```typescript
// Measure query time
async function measureQuery<T>(
  query: () => Promise<T>,
  queryName: string
): Promise<T> {
  const start = performance.now();
  try {
    return await query();
  } finally {
    const duration = performance.now() - start;

    // Log slow queries
    if (duration > 100) {
      console.warn(`Slow query [${queryName}]: ${duration.toFixed(2)}ms`);
    }

    metrics.histogram('db.query_time', duration, { query: queryName });
  }
}
```

### Connection Pool Metrics

```typescript
// Monitor connection pool
interface PoolMetrics {
  totalConnections: number;
  idleConnections: number;
  waitingRequests: number;
  acquireTime: number;
}

function getPoolMetrics(pool: Pool): PoolMetrics {
  return {
    totalConnections: pool.totalCount,
    idleConnections: pool.idleCount,
    waitingRequests: pool.waitingCount,
    acquireTime: pool.acquireTime,
  };
}
```

## Memory Metrics

### Node.js Memory Usage

```typescript
// Get memory usage
function getMemoryUsage(): NodeJS.MemoryUsage & { percentUsed: number } {
  const usage = process.memoryUsage();
  const totalMemory = require('os').totalmem();

  return {
    ...usage,
    percentUsed: (usage.heapUsed / totalMemory) * 100,
  };
}

// Monitor memory
setInterval(() => {
  const memory = getMemoryUsage();

  if (memory.percentUsed > 80) {
    console.warn('High memory usage:', memory.percentUsed.toFixed(2) + '%');
  }

  metrics.gauge('memory.heap_used', memory.heapUsed);
  metrics.gauge('memory.heap_total', memory.heapTotal);
  metrics.gauge('memory.rss', memory.rss);
}, 30000);
```

### Garbage Collection Metrics

```typescript
// Monitor GC (requires --expose-gc flag)
import v8 from 'v8';

function getHeapStatistics() {
  const stats = v8.getHeapStatistics();
  return {
    totalHeapSize: stats.total_heap_size,
    usedHeapSize: stats.used_heap_size,
    heapSizeLimit: stats.heap_size_limit,
    mallocedMemory: stats.malloced_memory,
    peakMallocedMemory: stats.peak_malloced_memory,
  };
}
```

## CPU Metrics

### CPU Usage

```typescript
// Get CPU usage
import os from 'os';

function getCpuUsage(): number {
  const cpus = os.cpus();
  let totalIdle = 0;
  let totalTick = 0;

  for (const cpu of cpus) {
    for (const type in cpu.times) {
      totalTick += cpu.times[type as keyof typeof cpu.times];
    }
    totalIdle += cpu.times.idle;
  }

  return ((totalTick - totalIdle) / totalTick) * 100;
}
```

### Event Loop Lag

```typescript
// Measure event loop lag
function measureEventLoopLag(): Promise<number> {
  const start = process.hrtime.bigint();
  return new Promise((resolve) => {
    setImmediate(() => {
      const lag = Number(process.hrtime.bigint() - start) / 1e6; // ms
      resolve(lag);
    });
  });
}

// Monitor continuously
setInterval(async () => {
  const lag = await measureEventLoopLag();
  if (lag > 100) {
    console.warn('Event loop lag:', lag.toFixed(2), 'ms');
  }
  metrics.gauge('event_loop.lag', lag);
}, 1000);
```

## Metric Collection Framework

```typescript
// Centralized metrics collection
class MetricsCollector {
  private histograms: Map<string, number[]> = new Map();
  private gauges: Map<string, number> = new Map();
  private counters: Map<string, number> = new Map();

  histogram(name: string, value: number, tags?: Record<string, string>): void {
    const key = this.buildKey(name, tags);
    if (!this.histograms.has(key)) {
      this.histograms.set(key, []);
    }
    this.histograms.get(key)!.push(value);
  }

  gauge(name: string, value: number, tags?: Record<string, string>): void {
    const key = this.buildKey(name, tags);
    this.gauges.set(key, value);
  }

  counter(name: string, increment: number = 1, tags?: Record<string, string>): void {
    const key = this.buildKey(name, tags);
    const current = this.counters.get(key) || 0;
    this.counters.set(key, current + increment);
  }

  getStats(name: string): {
    min: number;
    max: number;
    avg: number;
    p50: number;
    p95: number;
    p99: number;
  } | null {
    const values = this.histograms.get(name);
    if (!values || values.length === 0) return null;

    const sorted = [...values].sort((a, b) => a - b);
    const sum = sorted.reduce((a, b) => a + b, 0);

    return {
      min: sorted[0],
      max: sorted[sorted.length - 1],
      avg: sum / sorted.length,
      p50: this.percentile(sorted, 50),
      p95: this.percentile(sorted, 95),
      p99: this.percentile(sorted, 99),
    };
  }

  private buildKey(name: string, tags?: Record<string, string>): string {
    if (!tags) return name;
    const tagStr = Object.entries(tags)
      .map(([k, v]) => `${k}=${v}`)
      .join(',');
    return `${name}{${tagStr}}`;
  }

  private percentile(sorted: number[], p: number): number {
    const index = Math.ceil((p / 100) * sorted.length) - 1;
    return sorted[Math.max(0, index)];
  }
}

export const metrics = new MetricsCollector();
```

## SLA/SLO Targets

```typescript
// Define SLOs
const SLO = {
  api: {
    availability: 99.9, // 99.9% uptime
    responseTime: {
      p50: 100, // 100ms
      p95: 200, // 200ms
      p99: 500, // 500ms
    },
    errorRate: 0.1, // 0.1%
  },
  database: {
    queryTime: {
      p50: 20,
      p95: 50,
      p99: 100,
    },
  },
  web: {
    lcp: 2500, // 2.5s
    fid: 100,  // 100ms
    cls: 0.1,
  },
};

// Check SLO compliance
function checkSLOCompliance(
  metric: string,
  value: number,
  threshold: number
): boolean {
  const compliant = value <= threshold;
  if (!compliant) {
    console.warn(`SLO violation: ${metric} = ${value}, threshold = ${threshold}`);
  }
  return compliant;
}
```

## Best Practices

1. **Measure before optimizing** - Don't guess where bottlenecks are
2. **Use percentiles, not averages** - P95/P99 show real user experience
3. **Set clear targets** - Define SLOs before development
4. **Monitor continuously** - Performance can degrade over time
5. **Automate alerts** - Know immediately when SLOs are violated
6. **Track trends** - Look for gradual degradation patterns
