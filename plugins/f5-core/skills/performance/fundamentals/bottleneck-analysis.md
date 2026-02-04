---
name: bottleneck-analysis
description: Techniques for identifying and analyzing performance bottlenecks
category: performance/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Bottleneck Analysis

## Overview

Bottleneck analysis is the systematic process of identifying the limiting factors
in system performance. A bottleneck is any component that limits overall throughput.

## The Bottleneck Principle

```
┌─────────────────────────────────────────────────────────────────┐
│                  System Throughput Chain                        │
├────────┬────────┬────────┬────────┬────────┬────────┬──────────┤
│ Client │  CDN   │  LB    │  App   │  Cache │   DB   │  Result  │
│  100ms │  20ms  │  5ms   │  50ms  │  10ms  │ 200ms  │  385ms   │
└────────┴────────┴────────┴────────┴────────┴────────┴──────────┘
                                               ▲
                                               │
                                         BOTTLENECK
                                     (Database is slowest)
```

**Amdahl's Law**: The speedup of a system is limited by the bottleneck component.

## Types of Bottlenecks

### 1. CPU Bottleneck

**Symptoms:**
- High CPU usage (>80% sustained)
- Long processing times
- Event loop lag in Node.js

**Detection:**

```typescript
import os from 'os';

function detectCpuBottleneck(): boolean {
  const cpus = os.cpus();
  let totalIdle = 0;
  let totalTick = 0;

  for (const cpu of cpus) {
    for (const type in cpu.times) {
      totalTick += cpu.times[type as keyof typeof cpu.times];
    }
    totalIdle += cpu.times.idle;
  }

  const cpuUsage = ((totalTick - totalIdle) / totalTick) * 100;
  return cpuUsage > 80;
}
```

**Solutions:**
- Optimize algorithms (reduce complexity)
- Cache computed results
- Use worker threads for heavy computation
- Scale horizontally

### 2. Memory Bottleneck

**Symptoms:**
- High memory usage
- Frequent garbage collection
- Out of memory errors
- Memory leaks over time

**Detection:**

```typescript
function detectMemoryBottleneck(): {
  isBottleneck: boolean;
  details: NodeJS.MemoryUsage;
} {
  const usage = process.memoryUsage();
  const heapUsedPercent = (usage.heapUsed / usage.heapTotal) * 100;

  return {
    isBottleneck: heapUsedPercent > 85,
    details: usage,
  };
}

// Memory leak detection
class MemoryLeakDetector {
  private samples: number[] = [];
  private maxSamples = 100;

  sample(): void {
    const usage = process.memoryUsage();
    this.samples.push(usage.heapUsed);

    if (this.samples.length > this.maxSamples) {
      this.samples.shift();
    }
  }

  detectLeak(): boolean {
    if (this.samples.length < 10) return false;

    // Check if memory is consistently increasing
    let increases = 0;
    for (let i = 1; i < this.samples.length; i++) {
      if (this.samples[i] > this.samples[i - 1]) {
        increases++;
      }
    }

    // If memory increased 80%+ of the time, likely a leak
    return increases / (this.samples.length - 1) > 0.8;
  }
}
```

**Solutions:**
- Fix memory leaks
- Use streaming for large data
- Implement pagination
- Optimize data structures

### 3. I/O Bottleneck

**Symptoms:**
- Low CPU usage but slow responses
- High I/O wait time
- Disk queue buildup

**Detection:**

```typescript
// Measure I/O latency
async function measureIOLatency(filePath: string): Promise<number> {
  const start = performance.now();
  await fs.promises.readFile(filePath);
  return performance.now() - start;
}

// Network I/O detection
async function detectNetworkBottleneck(url: string): Promise<{
  dnsTime: number;
  connectTime: number;
  ttfb: number;
  downloadTime: number;
}> {
  const timings = {
    dnsTime: 0,
    connectTime: 0,
    ttfb: 0,
    downloadTime: 0,
  };

  const start = performance.now();
  // Measure with fetch API performance timing
  await fetch(url);
  timings.downloadTime = performance.now() - start;

  return timings;
}
```

**Solutions:**
- Use connection pooling
- Implement caching
- Use async I/O
- Batch I/O operations

### 4. Database Bottleneck

**Symptoms:**
- Slow query times
- Connection pool exhaustion
- High database CPU/memory
- Lock contention

**Detection:**

```sql
-- PostgreSQL: Find slow queries
SELECT
  query,
  calls,
  mean_time,
  total_time,
  rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 20;

-- Check for lock contention
SELECT
  blocked_locks.pid AS blocked_pid,
  blocking_locks.pid AS blocking_pid,
  blocked_activity.query AS blocked_statement,
  blocking_activity.query AS blocking_statement
FROM pg_catalog.pg_locks blocked_locks
JOIN pg_catalog.pg_stat_activity blocked_activity
  ON blocked_activity.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks blocking_locks
  ON blocking_locks.locktype = blocked_locks.locktype
WHERE NOT blocked_locks.granted;
```

```typescript
// Monitor connection pool
function detectConnectionPoolBottleneck(pool: Pool): {
  isBottleneck: boolean;
  waitingRequests: number;
  utilizationPercent: number;
} {
  const utilization = ((pool.totalCount - pool.idleCount) / pool.totalCount) * 100;

  return {
    isBottleneck: pool.waitingCount > 0 || utilization > 90,
    waitingRequests: pool.waitingCount,
    utilizationPercent: utilization,
  };
}
```

**Solutions:**
- Optimize queries and indexes
- Use read replicas
- Implement caching
- Increase connection pool
- Consider database sharding

### 5. Network Bottleneck

**Symptoms:**
- High latency between services
- Packet loss
- Bandwidth saturation

**Detection:**

```typescript
// Measure inter-service latency
async function measureServiceLatency(
  services: string[]
): Promise<Map<string, number>> {
  const latencies = new Map<string, number>();

  for (const service of services) {
    const start = performance.now();
    try {
      await fetch(`${service}/health`);
      latencies.set(service, performance.now() - start);
    } catch (error) {
      latencies.set(service, -1); // Service unreachable
    }
  }

  return latencies;
}
```

**Solutions:**
- Use CDN for static content
- Implement response compression
- Reduce payload sizes
- Use connection keep-alive
- Consider geographic distribution

## Bottleneck Analysis Process

### Step 1: Establish Baseline

```typescript
interface PerformanceBaseline {
  responseTime: { p50: number; p95: number; p99: number };
  throughput: number;
  errorRate: number;
  resourceUsage: {
    cpu: number;
    memory: number;
    connections: number;
  };
}

async function establishBaseline(): Promise<PerformanceBaseline> {
  // Collect metrics over time (e.g., 1 hour during normal operation)
  const samples = await collectMetricsSamples(3600);

  return {
    responseTime: calculatePercentiles(samples.responseTimes),
    throughput: average(samples.requestsPerSecond),
    errorRate: average(samples.errorRates),
    resourceUsage: {
      cpu: average(samples.cpuUsage),
      memory: average(samples.memoryUsage),
      connections: average(samples.dbConnections),
    },
  };
}
```

### Step 2: Load Testing

```typescript
// Artillery load test configuration
const loadTestConfig = {
  config: {
    target: 'http://localhost:3000',
    phases: [
      { duration: 60, arrivalRate: 10 },  // Warm up
      { duration: 120, arrivalRate: 50 }, // Normal load
      { duration: 120, arrivalRate: 100 }, // Stress test
      { duration: 60, arrivalRate: 200 },  // Peak load
    ],
  },
  scenarios: [
    {
      name: 'User journey',
      flow: [
        { get: { url: '/api/products' } },
        { get: { url: '/api/products/{{ productId }}' } },
        { post: { url: '/api/cart', json: { productId: '{{ productId }}' } } },
      ],
    },
  ],
};
```

### Step 3: Profile and Trace

```typescript
// Distributed tracing with OpenTelemetry
import { trace, context, SpanStatusCode } from '@opentelemetry/api';

const tracer = trace.getTracer('my-service');

async function handleRequest(req: Request): Promise<Response> {
  return tracer.startActiveSpan('handleRequest', async (span) => {
    try {
      // Add attributes for analysis
      span.setAttribute('http.method', req.method);
      span.setAttribute('http.url', req.url);

      // Database operation
      const data = await tracer.startActiveSpan('database.query', async (dbSpan) => {
        const result = await db.query('SELECT * FROM users');
        dbSpan.setAttribute('db.rows', result.length);
        return result;
      });

      // External API call
      await tracer.startActiveSpan('external.api', async (apiSpan) => {
        await fetch('https://api.example.com/data');
        apiSpan.end();
      });

      span.setStatus({ code: SpanStatusCode.OK });
      return new Response(JSON.stringify(data));
    } catch (error) {
      span.setStatus({ code: SpanStatusCode.ERROR, message: error.message });
      throw error;
    } finally {
      span.end();
    }
  });
}
```

### Step 4: Identify Bottleneck

```typescript
// Analyze trace data to find bottleneck
interface TraceAnalysis {
  totalDuration: number;
  spans: {
    name: string;
    duration: number;
    percentage: number;
  }[];
  bottleneck: {
    name: string;
    duration: number;
    percentage: number;
  };
}

function analyzeTrace(spans: Span[]): TraceAnalysis {
  const totalDuration = spans.reduce((sum, s) => sum + s.duration, 0);

  const analyzed = spans.map(span => ({
    name: span.name,
    duration: span.duration,
    percentage: (span.duration / totalDuration) * 100,
  }));

  // Sort by duration descending
  analyzed.sort((a, b) => b.duration - a.duration);

  return {
    totalDuration,
    spans: analyzed,
    bottleneck: analyzed[0], // Longest span is the bottleneck
  };
}
```

### Step 5: Fix and Verify

```typescript
// Before and after comparison
async function verifyOptimization(
  baseline: PerformanceBaseline,
  optimization: string
): Promise<{
  improvement: number;
  successful: boolean;
}> {
  console.log(`Testing optimization: ${optimization}`);

  const current = await establishBaseline();

  const improvement = {
    responseTime: ((baseline.responseTime.p95 - current.responseTime.p95)
      / baseline.responseTime.p95) * 100,
    throughput: ((current.throughput - baseline.throughput)
      / baseline.throughput) * 100,
  };

  return {
    improvement: improvement.responseTime,
    successful: improvement.responseTime > 10, // At least 10% improvement
  };
}
```

## Common Bottleneck Patterns

### Pattern 1: The Synchronous Chain

```
❌ Synchronous (slow):
Request → DB Query 1 → DB Query 2 → External API → Response
         100ms        100ms        200ms
         Total: 400ms

✅ Parallel (fast):
Request → [DB Query 1, DB Query 2, External API] → Response
          [100ms,      100ms,       200ms]
          Total: 200ms (parallel execution)
```

```typescript
// Parallelize independent operations
async function optimizedHandler(req: Request): Promise<Response> {
  const [user, products, recommendations] = await Promise.all([
    getUserData(req.userId),
    getProducts(),
    getRecommendations(req.userId),
  ]);

  return { user, products, recommendations };
}
```

### Pattern 2: N+1 Query Problem

```
❌ N+1 Queries:
SELECT * FROM orders;                    -- 1 query
SELECT * FROM users WHERE id = 1;        -- N queries
SELECT * FROM users WHERE id = 2;
...
Total: 1 + N queries

✅ Optimized:
SELECT * FROM orders;                    -- 1 query
SELECT * FROM users WHERE id IN (1,2,3); -- 1 query
Total: 2 queries
```

### Pattern 3: Unbounded Results

```typescript
// ❌ Bad: Fetching all records
const allUsers = await prisma.user.findMany();

// ✅ Good: Paginated with limits
const users = await prisma.user.findMany({
  take: 100,
  skip: page * 100,
  orderBy: { createdAt: 'desc' },
});
```

## Bottleneck Detection Checklist

- [ ] CPU usage consistently > 80%?
- [ ] Memory usage consistently > 85%?
- [ ] Database query times > 100ms?
- [ ] Connection pool frequently exhausted?
- [ ] High event loop lag (> 100ms)?
- [ ] Significant I/O wait times?
- [ ] Network latency between services?
- [ ] Cache hit rate < 80%?
- [ ] High garbage collection frequency?
- [ ] Lock contention in database?
