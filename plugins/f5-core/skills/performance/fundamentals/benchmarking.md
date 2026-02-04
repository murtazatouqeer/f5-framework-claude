---
name: benchmarking
description: Performance benchmarking methodologies and tools
category: performance/fundamentals
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Benchmarking

## Overview

Benchmarking is the process of measuring and comparing system performance
against defined standards or competing implementations.

## Benchmarking Principles

### 1. Reproducibility

```typescript
// Ensure consistent test environment
interface BenchmarkEnvironment {
  nodeVersion: string;
  platform: string;
  cpuModel: string;
  cpuCores: number;
  totalMemory: number;
  timestamp: string;
}

function captureEnvironment(): BenchmarkEnvironment {
  return {
    nodeVersion: process.version,
    platform: process.platform,
    cpuModel: os.cpus()[0].model,
    cpuCores: os.cpus().length,
    totalMemory: os.totalmem(),
    timestamp: new Date().toISOString(),
  };
}
```

### 2. Statistical Significance

```typescript
// Run multiple iterations for statistical validity
interface BenchmarkResult {
  name: string;
  iterations: number;
  mean: number;
  stdDev: number;
  min: number;
  max: number;
  p50: number;
  p95: number;
  p99: number;
  opsPerSecond: number;
}

function calculateStats(measurements: number[]): Omit<BenchmarkResult, 'name' | 'opsPerSecond'> {
  const sorted = [...measurements].sort((a, b) => a - b);
  const sum = sorted.reduce((a, b) => a + b, 0);
  const mean = sum / sorted.length;

  const squaredDiffs = sorted.map(v => Math.pow(v - mean, 2));
  const variance = squaredDiffs.reduce((a, b) => a + b, 0) / sorted.length;
  const stdDev = Math.sqrt(variance);

  return {
    iterations: sorted.length,
    mean,
    stdDev,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    p50: percentile(sorted, 50),
    p95: percentile(sorted, 95),
    p99: percentile(sorted, 99),
  };
}
```

### 3. Warm-up Period

```typescript
// Warm up before measuring
async function benchmark(
  name: string,
  fn: () => Promise<void>,
  options: { warmupIterations?: number; iterations?: number } = {}
): Promise<BenchmarkResult> {
  const { warmupIterations = 100, iterations = 1000 } = options;

  // Warm-up phase (results discarded)
  console.log(`Warming up ${name}...`);
  for (let i = 0; i < warmupIterations; i++) {
    await fn();
  }

  // Force garbage collection if available
  if (global.gc) {
    global.gc();
  }

  // Measurement phase
  console.log(`Benchmarking ${name}...`);
  const measurements: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await fn();
    measurements.push(performance.now() - start);
  }

  const stats = calculateStats(measurements);

  return {
    name,
    ...stats,
    opsPerSecond: 1000 / stats.mean,
  };
}
```

## Micro-Benchmarking

### Code-Level Performance

```typescript
// Benchmark different implementations
async function compareSolutions() {
  const data = Array.from({ length: 10000 }, () => Math.random());

  // Solution A: for loop
  const resultA = await benchmark('for-loop', async () => {
    let sum = 0;
    for (let i = 0; i < data.length; i++) {
      sum += data[i];
    }
  });

  // Solution B: reduce
  const resultB = await benchmark('reduce', async () => {
    data.reduce((a, b) => a + b, 0);
  });

  // Solution C: forEach
  const resultC = await benchmark('forEach', async () => {
    let sum = 0;
    data.forEach(v => { sum += v; });
  });

  console.table([resultA, resultB, resultC]);
}
```

### Comparing Algorithms

```typescript
// Benchmark sorting algorithms
function benchmarkSorting() {
  const createData = () => Array.from({ length: 1000 }, () => Math.random());

  return Promise.all([
    benchmark('native-sort', async () => {
      const arr = createData();
      arr.sort((a, b) => a - b);
    }),
    benchmark('quicksort', async () => {
      const arr = createData();
      quicksort(arr);
    }),
    benchmark('mergesort', async () => {
      const arr = createData();
      mergesort(arr);
    }),
  ]);
}
```

## API Benchmarking

### Using Artillery

```yaml
# artillery.yml
config:
  target: "http://localhost:3000"
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Warm up"
    - duration: 120
      arrivalRate: 50
      name: "Steady state"
    - duration: 60
      arrivalRate: 100
      name: "Stress test"
  plugins:
    expect: {}
  defaults:
    headers:
      Authorization: "Bearer {{ $processEnvironment.API_TOKEN }}"

scenarios:
  - name: "API Benchmark"
    flow:
      - get:
          url: "/api/users"
          expect:
            - statusCode: 200
            - hasProperty: "data"
      - think: 1
      - post:
          url: "/api/users"
          json:
            name: "Test User"
            email: "test@example.com"
          expect:
            - statusCode: 201
```

```bash
# Run benchmark
artillery run artillery.yml --output results.json

# Generate report
artillery report results.json --output report.html
```

### Using k6

```javascript
// k6-benchmark.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  stages: [
    { duration: '1m', target: 10 },   // Ramp up
    { duration: '3m', target: 50 },   // Steady state
    { duration: '1m', target: 100 },  // Stress
    { duration: '1m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<500'],
    errors: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://localhost:3000/api/users');

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 200ms': (r) => r.timings.duration < 200,
  });

  errorRate.add(res.status !== 200);
  responseTime.add(res.timings.duration);

  sleep(1);
}
```

```bash
# Run k6 benchmark
k6 run k6-benchmark.js

# With HTML report
k6 run k6-benchmark.js --out json=results.json
```

### Custom HTTP Benchmarking

```typescript
// Custom benchmarking tool
import { performance } from 'perf_hooks';

interface HttpBenchmarkConfig {
  url: string;
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  headers?: Record<string, string>;
  body?: any;
  concurrency: number;
  totalRequests: number;
}

interface HttpBenchmarkResult {
  totalRequests: number;
  successfulRequests: number;
  failedRequests: number;
  totalTime: number;
  requestsPerSecond: number;
  latency: {
    min: number;
    max: number;
    mean: number;
    p50: number;
    p95: number;
    p99: number;
  };
}

async function httpBenchmark(config: HttpBenchmarkConfig): Promise<HttpBenchmarkResult> {
  const { url, method, headers, body, concurrency, totalRequests } = config;

  const latencies: number[] = [];
  let successCount = 0;
  let failCount = 0;

  const startTime = performance.now();

  // Create request batches
  const batches = Math.ceil(totalRequests / concurrency);

  for (let batch = 0; batch < batches; batch++) {
    const batchSize = Math.min(concurrency, totalRequests - batch * concurrency);

    const promises = Array.from({ length: batchSize }, async () => {
      const reqStart = performance.now();

      try {
        const res = await fetch(url, {
          method,
          headers,
          body: body ? JSON.stringify(body) : undefined,
        });

        latencies.push(performance.now() - reqStart);

        if (res.ok) {
          successCount++;
        } else {
          failCount++;
        }
      } catch (error) {
        latencies.push(performance.now() - reqStart);
        failCount++;
      }
    });

    await Promise.all(promises);
  }

  const totalTime = performance.now() - startTime;
  const sortedLatencies = [...latencies].sort((a, b) => a - b);

  return {
    totalRequests,
    successfulRequests: successCount,
    failedRequests: failCount,
    totalTime,
    requestsPerSecond: (totalRequests / totalTime) * 1000,
    latency: {
      min: sortedLatencies[0],
      max: sortedLatencies[sortedLatencies.length - 1],
      mean: latencies.reduce((a, b) => a + b, 0) / latencies.length,
      p50: percentile(sortedLatencies, 50),
      p95: percentile(sortedLatencies, 95),
      p99: percentile(sortedLatencies, 99),
    },
  };
}

// Usage
const result = await httpBenchmark({
  url: 'http://localhost:3000/api/users',
  method: 'GET',
  concurrency: 10,
  totalRequests: 1000,
});

console.log('Benchmark Results:');
console.log(`  Total Requests: ${result.totalRequests}`);
console.log(`  Successful: ${result.successfulRequests}`);
console.log(`  Failed: ${result.failedRequests}`);
console.log(`  RPS: ${result.requestsPerSecond.toFixed(2)}`);
console.log(`  Latency P95: ${result.latency.p95.toFixed(2)}ms`);
```

## Database Benchmarking

### Query Performance

```typescript
// Benchmark database queries
async function benchmarkQueries() {
  const results = await Promise.all([
    benchmark('simple-select', async () => {
      await prisma.user.findMany({ take: 100 });
    }),

    benchmark('join-query', async () => {
      await prisma.user.findMany({
        take: 100,
        include: { orders: true },
      });
    }),

    benchmark('aggregate', async () => {
      await prisma.order.aggregate({
        _sum: { total: true },
        _count: true,
      });
    }),

    benchmark('complex-filter', async () => {
      await prisma.user.findMany({
        where: {
          AND: [
            { status: 'active' },
            { createdAt: { gte: new Date('2024-01-01') } },
            { orders: { some: { total: { gt: 100 } } } },
          ],
        },
        take: 100,
      });
    }),
  ]);

  console.table(results);
}
```

### Connection Pool Benchmark

```typescript
// Test connection pool under load
async function benchmarkConnectionPool() {
  const concurrencyLevels = [1, 5, 10, 20, 50, 100];
  const results: any[] = [];

  for (const concurrency of concurrencyLevels) {
    const start = performance.now();
    const errors: number[] = [];

    const queries = Array.from({ length: concurrency }, async () => {
      try {
        await prisma.$queryRaw`SELECT 1`;
      } catch (error) {
        errors.push(1);
      }
    });

    await Promise.all(queries);

    results.push({
      concurrency,
      duration: performance.now() - start,
      errors: errors.length,
      throughput: (concurrency / ((performance.now() - start) / 1000)).toFixed(2),
    });
  }

  console.table(results);
}
```

## Comparative Benchmarking

### A/B Testing Performance

```typescript
// Compare two implementations
async function abTest(
  nameA: string,
  implA: () => Promise<any>,
  nameB: string,
  implB: () => Promise<any>,
  iterations: number = 1000
): Promise<{
  winner: string;
  improvement: number;
  results: { a: BenchmarkResult; b: BenchmarkResult };
}> {
  const resultA = await benchmark(nameA, implA, { iterations });
  const resultB = await benchmark(nameB, implB, { iterations });

  const improvement = ((resultA.mean - resultB.mean) / resultA.mean) * 100;

  return {
    winner: resultB.mean < resultA.mean ? nameB : nameA,
    improvement: Math.abs(improvement),
    results: { a: resultA, b: resultB },
  };
}

// Usage
const comparison = await abTest(
  'string-concat',
  async () => {
    let result = '';
    for (let i = 0; i < 1000; i++) {
      result += 'a';
    }
  },
  'array-join',
  async () => {
    const parts: string[] = [];
    for (let i = 0; i < 1000; i++) {
      parts.push('a');
    }
    parts.join('');
  }
);

console.log(`Winner: ${comparison.winner} (${comparison.improvement.toFixed(2)}% faster)`);
```

## Benchmark Reporting

### Generate Report

```typescript
interface BenchmarkReport {
  environment: BenchmarkEnvironment;
  timestamp: string;
  results: BenchmarkResult[];
  summary: {
    totalBenchmarks: number;
    fastestBenchmark: string;
    slowestBenchmark: string;
  };
}

function generateReport(results: BenchmarkResult[]): BenchmarkReport {
  const sorted = [...results].sort((a, b) => a.mean - b.mean);

  return {
    environment: captureEnvironment(),
    timestamp: new Date().toISOString(),
    results,
    summary: {
      totalBenchmarks: results.length,
      fastestBenchmark: sorted[0].name,
      slowestBenchmark: sorted[sorted.length - 1].name,
    },
  };
}

// Output as markdown
function reportToMarkdown(report: BenchmarkReport): string {
  let md = `# Benchmark Report\n\n`;
  md += `**Date:** ${report.timestamp}\n\n`;

  md += `## Environment\n\n`;
  md += `- Node.js: ${report.environment.nodeVersion}\n`;
  md += `- Platform: ${report.environment.platform}\n`;
  md += `- CPU: ${report.environment.cpuModel}\n`;
  md += `- Cores: ${report.environment.cpuCores}\n\n`;

  md += `## Results\n\n`;
  md += `| Name | Mean (ms) | P95 (ms) | Ops/sec |\n`;
  md += `|------|-----------|----------|--------|\n`;

  for (const result of report.results) {
    md += `| ${result.name} | ${result.mean.toFixed(2)} | ${result.p95.toFixed(2)} | ${result.opsPerSecond.toFixed(0)} |\n`;
  }

  md += `\n## Summary\n\n`;
  md += `- Fastest: **${report.summary.fastestBenchmark}**\n`;
  md += `- Slowest: **${report.summary.slowestBenchmark}**\n`;

  return md;
}
```

## Best Practices

1. **Isolate benchmarks** - Run on dedicated machines without other workloads
2. **Warm up first** - Allow JIT compilation and cache warming
3. **Multiple iterations** - Statistical significance requires many samples
4. **Control variables** - Change one thing at a time
5. **Document environment** - Record hardware, OS, runtime versions
6. **Compare apples to apples** - Use same conditions for comparisons
7. **Measure what matters** - Focus on realistic workloads
8. **Watch for outliers** - Use percentiles, not just averages
