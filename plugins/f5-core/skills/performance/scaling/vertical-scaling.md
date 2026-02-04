---
name: vertical-scaling
description: Vertical scaling strategies and optimization techniques
category: performance/scaling
applies_to: backend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Vertical Scaling

## Overview

Vertical scaling (scaling up) increases the capacity of a single server by adding
more CPU, memory, or storage. It's simpler to implement but has physical limits.

## When to Use Vertical Scaling

```
┌─────────────────────────────────────────────────────────────────┐
│               Vertical Scaling Decision Matrix                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✅ Good Fit:                    ❌ Poor Fit:                    │
│  • Database servers              • Stateless web servers         │
│  • In-memory caches              • Event processing              │
│  • Single-threaded apps          • High availability required    │
│  • Legacy applications           • Cost-sensitive workloads      │
│  • Quick fixes                   • Long-term growth              │
│  • Development/staging           • Unpredictable traffic         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## CPU Optimization

### Multi-Threading with Worker Threads

```typescript
import { Worker, isMainThread, parentPort, workerData } from 'worker_threads';
import os from 'os';

// CPU-intensive task in worker
if (!isMainThread) {
  const { data } = workerData;
  const result = heavyComputation(data);
  parentPort?.postMessage(result);
}

// Main thread - utilize all CPU cores
class WorkerPool {
  private workers: Worker[] = [];
  private queue: Array<{
    task: any;
    resolve: (value: any) => void;
    reject: (error: Error) => void;
  }> = [];
  private freeWorkers: Worker[] = [];

  constructor(
    private workerScript: string,
    private poolSize: number = os.cpus().length
  ) {
    for (let i = 0; i < poolSize; i++) {
      this.addWorker();
    }
  }

  private addWorker(): void {
    const worker = new Worker(this.workerScript);

    worker.on('message', (result) => {
      // Return worker to pool
      this.freeWorkers.push(worker);
      this.processQueue();
    });

    worker.on('error', (error) => {
      console.error('Worker error:', error);
      // Replace failed worker
      this.workers = this.workers.filter(w => w !== worker);
      this.addWorker();
    });

    this.workers.push(worker);
    this.freeWorkers.push(worker);
  }

  async execute<T>(data: any): Promise<T> {
    return new Promise((resolve, reject) => {
      this.queue.push({ task: data, resolve, reject });
      this.processQueue();
    });
  }

  private processQueue(): void {
    while (this.queue.length > 0 && this.freeWorkers.length > 0) {
      const worker = this.freeWorkers.pop()!;
      const { task, resolve } = this.queue.shift()!;

      worker.once('message', resolve);
      worker.postMessage(task);
    }
  }

  async shutdown(): Promise<void> {
    await Promise.all(this.workers.map(w => w.terminate()));
  }
}

// Usage
const pool = new WorkerPool('./compute-worker.js', 8);

const results = await Promise.all(
  tasks.map(task => pool.execute(task))
);
```

### Cluster Mode for Multi-Core Utilization

```typescript
import cluster from 'cluster';
import os from 'os';
import express from 'express';

const numCPUs = os.cpus().length;

if (cluster.isPrimary) {
  console.log(`Primary ${process.pid} is running`);
  console.log(`Starting ${numCPUs} workers...`);

  // Fork workers
  for (let i = 0; i < numCPUs; i++) {
    cluster.fork();
  }

  // Handle worker exit
  cluster.on('exit', (worker, code, signal) => {
    console.log(`Worker ${worker.process.pid} died (${signal || code})`);
    // Replace dead worker
    cluster.fork();
  });

  // Graceful shutdown
  process.on('SIGTERM', () => {
    console.log('Shutting down cluster...');
    for (const id in cluster.workers) {
      cluster.workers[id]?.kill();
    }
  });
} else {
  // Workers share the TCP connection
  const app = express();

  app.get('/api/data', async (req, res) => {
    // Request handled by one of the workers
    res.json({ worker: process.pid, data: 'response' });
  });

  app.listen(3000, () => {
    console.log(`Worker ${process.pid} started`);
  });
}
```

## Memory Optimization

### Node.js Memory Management

```typescript
// Increase Node.js heap size
// node --max-old-space-size=8192 app.js

// Monitor memory usage
function monitorMemory(): void {
  setInterval(() => {
    const usage = process.memoryUsage();
    console.log({
      heapUsed: `${Math.round(usage.heapUsed / 1024 / 1024)} MB`,
      heapTotal: `${Math.round(usage.heapTotal / 1024 / 1024)} MB`,
      external: `${Math.round(usage.external / 1024 / 1024)} MB`,
      rss: `${Math.round(usage.rss / 1024 / 1024)} MB`,
    });

    // Alert on high memory usage
    const heapPercent = usage.heapUsed / usage.heapTotal * 100;
    if (heapPercent > 85) {
      console.warn(`High heap usage: ${heapPercent.toFixed(1)}%`);
    }
  }, 10000);
}

// Efficient data structures
class MemoryEfficientCache<K, V> {
  private cache: Map<K, V>;
  private maxSize: number;
  private accessOrder: K[] = [];

  constructor(maxSize: number) {
    this.cache = new Map();
    this.maxSize = maxSize;
  }

  get(key: K): V | undefined {
    const value = this.cache.get(key);
    if (value !== undefined) {
      // Move to end (most recently used)
      this.accessOrder = this.accessOrder.filter(k => k !== key);
      this.accessOrder.push(key);
    }
    return value;
  }

  set(key: K, value: V): void {
    if (this.cache.size >= this.maxSize) {
      // Evict least recently used
      const lruKey = this.accessOrder.shift();
      if (lruKey !== undefined) {
        this.cache.delete(lruKey);
      }
    }

    this.cache.set(key, value);
    this.accessOrder.push(key);
  }

  clear(): void {
    this.cache.clear();
    this.accessOrder = [];
  }
}
```

### Buffer Management

```typescript
import { Buffer } from 'buffer';

// Pre-allocate buffers for high-throughput scenarios
class BufferPool {
  private pool: Buffer[] = [];
  private bufferSize: number;
  private poolSize: number;

  constructor(bufferSize: number, poolSize: number) {
    this.bufferSize = bufferSize;
    this.poolSize = poolSize;

    // Pre-allocate buffers
    for (let i = 0; i < poolSize; i++) {
      this.pool.push(Buffer.allocUnsafe(bufferSize));
    }
  }

  acquire(): Buffer {
    if (this.pool.length > 0) {
      return this.pool.pop()!;
    }
    // Allocate new buffer if pool is empty
    return Buffer.allocUnsafe(this.bufferSize);
  }

  release(buffer: Buffer): void {
    if (this.pool.length < this.poolSize) {
      buffer.fill(0); // Clear buffer
      this.pool.push(buffer);
    }
    // Let GC handle excess buffers
  }
}

// Usage for high-throughput I/O
const bufferPool = new BufferPool(64 * 1024, 100); // 64KB buffers

async function processFile(filePath: string): Promise<void> {
  const buffer = bufferPool.acquire();

  try {
    // Use buffer for I/O operations
    const fd = await fs.open(filePath, 'r');
    const { bytesRead } = await fd.read(buffer, 0, buffer.length, 0);
    // Process data...
    await fd.close();
  } finally {
    bufferPool.release(buffer);
  }
}
```

## I/O Optimization

### Async I/O with UV Thread Pool

```typescript
// Increase UV thread pool for I/O-bound applications
// UV_THREADPOOL_SIZE=64 node app.js

import { promises as fs } from 'fs';

// Parallel file operations
async function processFiles(paths: string[]): Promise<string[]> {
  // Limit concurrent operations to prevent overwhelming the system
  const BATCH_SIZE = 20;
  const results: string[] = [];

  for (let i = 0; i < paths.length; i += BATCH_SIZE) {
    const batch = paths.slice(i, i + BATCH_SIZE);
    const batchResults = await Promise.all(
      batch.map(path => fs.readFile(path, 'utf-8'))
    );
    results.push(...batchResults);
  }

  return results;
}

// Optimized streaming for large files
import { createReadStream, createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';
import { Transform } from 'stream';

async function processLargeFile(
  inputPath: string,
  outputPath: string,
  transform: (chunk: Buffer) => Buffer
): Promise<void> {
  const input = createReadStream(inputPath, {
    highWaterMark: 1024 * 1024, // 1MB chunks
  });

  const transformer = new Transform({
    transform(chunk, encoding, callback) {
      try {
        const result = transform(chunk);
        callback(null, result);
      } catch (error) {
        callback(error as Error);
      }
    },
  });

  const output = createWriteStream(outputPath, {
    highWaterMark: 1024 * 1024,
  });

  await pipeline(input, transformer, output);
}
```

### Connection Keep-Alive

```typescript
import http from 'http';
import https from 'https';

// Reuse connections for HTTP clients
const httpAgent = new http.Agent({
  keepAlive: true,
  keepAliveMsecs: 30000,
  maxSockets: 100,
  maxFreeSockets: 10,
});

const httpsAgent = new https.Agent({
  keepAlive: true,
  keepAliveMsecs: 30000,
  maxSockets: 100,
  maxFreeSockets: 10,
});

// Use with fetch or axios
import axios from 'axios';

const client = axios.create({
  httpAgent,
  httpsAgent,
  timeout: 30000,
});

// Server-side keep-alive
const server = http.createServer(app);
server.keepAliveTimeout = 65000; // Slightly higher than ALB timeout
server.headersTimeout = 66000;
```

## Database Vertical Scaling

### Connection Pool Tuning

```typescript
import { Pool } from 'pg';

// Calculate optimal pool size based on server resources
// Formula: connections = (core_count * 2) + effective_spindle_count
// For SSD, effective_spindle_count ≈ 0
const CORE_COUNT = 8;
const POOL_SIZE = CORE_COUNT * 2 + 1;

const pool = new Pool({
  host: process.env.DB_HOST,
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  max: POOL_SIZE,
  min: Math.floor(POOL_SIZE / 2),
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
  // Statement timeout to prevent long-running queries
  statement_timeout: 30000,
});

// Monitor pool metrics
pool.on('connect', () => {
  console.log('New connection established');
});

pool.on('error', (err) => {
  console.error('Pool error:', err);
});

// Periodic pool stats
setInterval(async () => {
  console.log({
    totalCount: pool.totalCount,
    idleCount: pool.idleCount,
    waitingCount: pool.waitingCount,
  });
}, 10000);
```

### PostgreSQL Configuration for Vertical Scaling

```sql
-- postgresql.conf optimizations for large server (64GB RAM, 16 cores)

-- Memory settings
shared_buffers = 16GB                -- 25% of RAM
effective_cache_size = 48GB          -- 75% of RAM
work_mem = 256MB                     -- Per-operation memory
maintenance_work_mem = 2GB           -- For VACUUM, INDEX creation
wal_buffers = 64MB

-- CPU settings
max_worker_processes = 16            -- Match core count
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
max_parallel_maintenance_workers = 4

-- Connection settings
max_connections = 200
superuser_reserved_connections = 3

-- Query planner
random_page_cost = 1.1               -- For SSD storage
effective_io_concurrency = 200       -- For SSD storage
default_statistics_target = 200      -- More accurate query planning

-- WAL settings
wal_level = replica
max_wal_senders = 3
checkpoint_completion_target = 0.9
checkpoint_timeout = 15min
```

## Application-Level Caching

### In-Memory Caching

```typescript
import NodeCache from 'node-cache';

// Optimized local cache for frequently accessed data
const cache = new NodeCache({
  stdTTL: 600,           // 10 minutes default TTL
  checkperiod: 120,      // Check for expired keys every 2 minutes
  useClones: false,      // Don't clone objects (faster but mutable)
  maxKeys: 10000,        // Limit cache size
});

class CacheService {
  async getOrSet<T>(
    key: string,
    factory: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cached = cache.get<T>(key);
    if (cached !== undefined) {
      return cached;
    }

    const value = await factory();
    cache.set(key, value, ttl);
    return value;
  }

  invalidate(pattern: string): void {
    const keys = cache.keys();
    const regex = new RegExp(pattern);

    keys.forEach(key => {
      if (regex.test(key)) {
        cache.del(key);
      }
    });
  }

  getStats(): NodeCache.Stats {
    return cache.getStats();
  }
}

// Usage
const cacheService = new CacheService();

const user = await cacheService.getOrSet(
  `user:${userId}`,
  () => db.user.findUnique({ where: { id: userId } }),
  300 // 5 minutes TTL
);
```

### Memoization for Expensive Computations

```typescript
// Generic memoization with configurable cache
function memoize<TArgs extends any[], TResult>(
  fn: (...args: TArgs) => TResult,
  options: {
    maxSize?: number;
    ttl?: number;
    keyFn?: (...args: TArgs) => string;
  } = {}
): (...args: TArgs) => TResult {
  const { maxSize = 100, ttl = 60000, keyFn } = options;
  const cache = new Map<string, { value: TResult; expiry: number }>();
  const accessOrder: string[] = [];

  return function (...args: TArgs): TResult {
    const key = keyFn ? keyFn(...args) : JSON.stringify(args);
    const cached = cache.get(key);

    if (cached && cached.expiry > Date.now()) {
      // Move to end of access order
      const idx = accessOrder.indexOf(key);
      if (idx > -1) accessOrder.splice(idx, 1);
      accessOrder.push(key);
      return cached.value;
    }

    // Evict if necessary
    while (cache.size >= maxSize) {
      const lruKey = accessOrder.shift();
      if (lruKey) cache.delete(lruKey);
    }

    const result = fn(...args);
    cache.set(key, { value: result, expiry: Date.now() + ttl });
    accessOrder.push(key);

    return result;
  };
}

// Usage
const expensiveCalculation = memoize(
  (userId: string, data: any) => {
    // CPU-intensive computation
    return computeResult(userId, data);
  },
  { maxSize: 1000, ttl: 300000 }
);
```

## Monitoring and Alerting

```typescript
import os from 'os';
import v8 from 'v8';

interface SystemMetrics {
  cpu: {
    usage: number;
    cores: number;
    loadAvg: number[];
  };
  memory: {
    total: number;
    used: number;
    free: number;
    heapUsed: number;
    heapTotal: number;
  };
  uptime: number;
}

function collectSystemMetrics(): SystemMetrics {
  const cpus = os.cpus();
  const memUsage = process.memoryUsage();
  const heapStats = v8.getHeapStatistics();

  // Calculate CPU usage
  let totalIdle = 0;
  let totalTick = 0;
  cpus.forEach(cpu => {
    for (const type in cpu.times) {
      totalTick += cpu.times[type as keyof typeof cpu.times];
    }
    totalIdle += cpu.times.idle;
  });
  const cpuUsage = 100 - (totalIdle / totalTick * 100);

  return {
    cpu: {
      usage: cpuUsage,
      cores: cpus.length,
      loadAvg: os.loadavg(),
    },
    memory: {
      total: os.totalmem(),
      used: os.totalmem() - os.freemem(),
      free: os.freemem(),
      heapUsed: memUsage.heapUsed,
      heapTotal: heapStats.heap_size_limit,
    },
    uptime: process.uptime(),
  };
}

// Alert thresholds for vertical scaling decisions
function checkScalingTriggers(metrics: SystemMetrics): string[] {
  const alerts: string[] = [];

  if (metrics.cpu.usage > 80) {
    alerts.push(`High CPU usage: ${metrics.cpu.usage.toFixed(1)}%`);
  }

  if (metrics.cpu.loadAvg[0] > metrics.cpu.cores * 0.7) {
    alerts.push(`High load average: ${metrics.cpu.loadAvg[0].toFixed(2)}`);
  }

  const memoryPercent = metrics.memory.used / metrics.memory.total * 100;
  if (memoryPercent > 85) {
    alerts.push(`High memory usage: ${memoryPercent.toFixed(1)}%`);
  }

  const heapPercent = metrics.memory.heapUsed / metrics.memory.heapTotal * 100;
  if (heapPercent > 80) {
    alerts.push(`High heap usage: ${heapPercent.toFixed(1)}%`);
  }

  return alerts;
}
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Vertical Scaling Checklist                          │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Profile application to identify bottlenecks                   │
│ ☐ Optimize code before adding resources                         │
│ ☐ Use worker threads for CPU-intensive tasks                    │
│ ☐ Tune memory allocation (--max-old-space-size)                 │
│ ☐ Increase UV_THREADPOOL_SIZE for I/O-bound apps                │
│ ☐ Configure database connection pools appropriately             │
│ ☐ Implement application-level caching                           │
│ ☐ Monitor resource utilization continuously                     │
│ ☐ Set up alerts for scaling triggers                            │
│ ☐ Plan for eventual horizontal scaling migration                │
│ ☐ Document resource requirements and limits                     │
│ ☐ Test application behavior under resource constraints          │
└─────────────────────────────────────────────────────────────────┘
```

## Vertical vs Horizontal Decision

| Factor | Vertical | Horizontal |
|--------|----------|------------|
| Complexity | Low | High |
| Cost (short-term) | Low | Higher |
| Cost (long-term) | Higher | Lower |
| Downtime for scaling | Yes | No |
| Maximum capacity | Limited | Unlimited |
| Fault tolerance | Poor | Good |
| Database scaling | Preferred | Complex |
| Stateless apps | Possible | Preferred |
