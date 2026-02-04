---
name: memory-profiling
description: Memory profiling and leak detection for Node.js
category: performance/profiling
applies_to: backend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Memory Profiling

## Overview

Memory profiling identifies memory leaks, excessive allocation, and
inefficient memory usage that can cause application crashes and degraded performance.

## Node.js Memory Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    Node.js Memory Layout                         │
├─────────────────────────────────────────────────────────────────┤
│  RSS (Resident Set Size)                                        │
│  ├── Code Segment                                               │
│  ├── Stack                                                      │
│  └── Heap                                                       │
│      ├── New Space (short-lived objects)                        │
│      │   ├── From Space                                         │
│      │   └── To Space                                           │
│      └── Old Space (long-lived objects)                         │
│          ├── Old Pointer Space                                  │
│          ├── Old Data Space                                     │
│          └── Large Object Space                                 │
├─────────────────────────────────────────────────────────────────┤
│  External Memory (Buffers, ArrayBuffers)                        │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Memory Monitoring

### process.memoryUsage()

```typescript
function logMemoryUsage(): void {
  const usage = process.memoryUsage();

  console.log({
    rss: formatBytes(usage.rss),           // Total memory allocated
    heapTotal: formatBytes(usage.heapTotal), // V8 heap size
    heapUsed: formatBytes(usage.heapUsed),   // V8 heap used
    external: formatBytes(usage.external),   // C++ objects
    arrayBuffers: formatBytes(usage.arrayBuffers), // ArrayBuffers
  });
}

function formatBytes(bytes: number): string {
  return `${(bytes / 1024 / 1024).toFixed(2)} MB`;
}

// Monitor continuously
setInterval(logMemoryUsage, 5000);
```

### V8 Heap Statistics

```typescript
import v8 from 'v8';

function getHeapStatistics(): v8.HeapStatistics {
  return v8.getHeapStatistics();
}

function logHeapStats(): void {
  const stats = getHeapStatistics();

  console.log({
    heapSizeLimit: formatBytes(stats.heap_size_limit),
    totalHeapSize: formatBytes(stats.total_heap_size),
    usedHeapSize: formatBytes(stats.used_heap_size),
    mallocedMemory: formatBytes(stats.malloced_memory),
  });
}

// Heap space breakdown
function getHeapSpaceStats(): v8.HeapSpaceInfo[] {
  return v8.getHeapSpaceStatistics();
}
```

## Heap Snapshots

### Taking Heap Snapshots

```typescript
import v8 from 'v8';
import fs from 'fs';

function takeHeapSnapshot(filename: string): void {
  const snapshotFile = fs.createWriteStream(filename);

  v8.writeHeapSnapshot(filename);
  console.log(`Heap snapshot written to ${filename}`);
}

// Trigger via HTTP endpoint
app.get('/debug/heap-snapshot', (req, res) => {
  const filename = `heap-${Date.now()}.heapsnapshot`;
  takeHeapSnapshot(filename);
  res.json({ filename });
});

// Or via signal
process.on('SIGUSR2', () => {
  const filename = `heap-${Date.now()}.heapsnapshot`;
  takeHeapSnapshot(filename);
});
```

### Analyzing Heap Snapshots

```bash
# Load in Chrome DevTools
1. Open Chrome DevTools
2. Go to Memory tab
3. Load snapshot file
4. Analyze:
   - Summary: Objects by constructor
   - Comparison: Diff between snapshots
   - Containment: Object hierarchy
   - Statistics: Memory distribution
```

### Programmatic Heap Analysis

```typescript
import inspector from 'inspector';
import fs from 'fs';

async function captureHeapProfile(): Promise<void> {
  const session = new inspector.Session();
  session.connect();

  await new Promise<void>((resolve) => {
    session.post('HeapProfiler.enable', () => resolve());
  });

  await new Promise<void>((resolve) => {
    session.post('HeapProfiler.startTrackingHeapObjects', () => resolve());
  });

  // Run operations
  await performOperations();

  const profile = await new Promise<any>((resolve) => {
    session.post('HeapProfiler.stopTrackingHeapObjects', (err, data) => {
      resolve(data);
    });
  });

  session.disconnect();
  fs.writeFileSync('heap-profile.json', JSON.stringify(profile));
}
```

## Memory Leak Detection

### Common Leak Patterns

```typescript
// ❌ Leak: Growing array
class LeakyCache {
  private cache: any[] = [];

  add(item: any): void {
    this.cache.push(item); // Never removed
  }
}

// ✅ Fix: Bounded cache with eviction
class BoundedCache {
  private cache: Map<string, any> = new Map();
  private maxSize = 1000;

  set(key: string, value: any): void {
    if (this.cache.size >= this.maxSize) {
      const oldestKey = this.cache.keys().next().value;
      this.cache.delete(oldestKey);
    }
    this.cache.set(key, value);
  }
}

// ❌ Leak: Event listener not removed
class LeakyComponent {
  constructor() {
    eventEmitter.on('data', this.handleData);
  }

  handleData = (data: any) => {
    // Process data
  };
}

// ✅ Fix: Clean up listeners
class CleanComponent {
  constructor() {
    eventEmitter.on('data', this.handleData);
  }

  handleData = (data: any) => {
    // Process data
  };

  destroy(): void {
    eventEmitter.off('data', this.handleData);
  }
}

// ❌ Leak: Closure holding reference
function createLeak() {
  const largeData = new Array(1000000).fill('x');

  return () => {
    // largeData is never garbage collected
    console.log(largeData.length);
  };
}

// ✅ Fix: Clear reference when done
function createNoLeak() {
  let largeData: string[] | null = new Array(1000000).fill('x');

  return () => {
    if (largeData) {
      console.log(largeData.length);
      largeData = null; // Allow GC
    }
  };
}
```

### Memory Leak Detection Tool

```typescript
// Simple leak detector
class LeakDetector {
  private samples: number[] = [];
  private sampleInterval: NodeJS.Timeout | null = null;

  start(intervalMs: number = 10000, maxSamples: number = 60): void {
    this.sampleInterval = setInterval(() => {
      const usage = process.memoryUsage();
      this.samples.push(usage.heapUsed);

      if (this.samples.length > maxSamples) {
        this.samples.shift();
      }

      this.analyze();
    }, intervalMs);
  }

  stop(): void {
    if (this.sampleInterval) {
      clearInterval(this.sampleInterval);
    }
  }

  private analyze(): void {
    if (this.samples.length < 10) return;

    // Check for consistent growth
    let increases = 0;
    for (let i = 1; i < this.samples.length; i++) {
      if (this.samples[i] > this.samples[i - 1] * 1.01) {
        increases++;
      }
    }

    const growthRate = increases / (this.samples.length - 1);

    if (growthRate > 0.8) {
      console.warn('Potential memory leak detected!', {
        growthRate: `${(growthRate * 100).toFixed(0)}%`,
        currentHeap: formatBytes(this.samples[this.samples.length - 1]),
        startHeap: formatBytes(this.samples[0]),
      });
    }
  }
}
```

## Garbage Collection Monitoring

### GC Tracing

```bash
# Start with GC tracing
node --trace-gc app.js

# Expose GC for manual triggering
node --expose-gc app.js
```

```typescript
// Manual GC trigger (requires --expose-gc)
declare const global: typeof globalThis & { gc?: () => void };

function forceGC(): void {
  if (global.gc) {
    global.gc();
    console.log('Garbage collection triggered');
  } else {
    console.warn('GC not exposed. Run with --expose-gc');
  }
}
```

### GC Performance Observer

```typescript
import { PerformanceObserver } from 'perf_hooks';

const gcObserver = new PerformanceObserver((list) => {
  const entries = list.getEntries();

  for (const entry of entries) {
    if (entry.entryType === 'gc') {
      console.log({
        type: entry.name, // minor, major, incremental, weakcb
        duration: entry.duration,
        startTime: entry.startTime,
      });

      // Alert on long GC pauses
      if (entry.duration > 100) {
        console.warn(`Long GC pause: ${entry.duration}ms`);
      }
    }
  }
});

gcObserver.observe({ entryTypes: ['gc'] });
```

## Clinic.js Heap Profiler

```bash
# Install Clinic.js
npm install -g clinic

# Run heap profiler
clinic heapprofiler -- node app.js

# Generate report
# Output: .clinic/*.html
```

## Memory Optimization Strategies

### Object Pooling

```typescript
// Object pool for frequently created/destroyed objects
class ObjectPool<T> {
  private pool: T[] = [];
  private factory: () => T;
  private reset: (obj: T) => void;

  constructor(
    factory: () => T,
    reset: (obj: T) => void,
    initialSize: number = 10
  ) {
    this.factory = factory;
    this.reset = reset;

    // Pre-populate pool
    for (let i = 0; i < initialSize; i++) {
      this.pool.push(factory());
    }
  }

  acquire(): T {
    return this.pool.pop() || this.factory();
  }

  release(obj: T): void {
    this.reset(obj);
    this.pool.push(obj);
  }
}

// Usage
interface PooledRequest {
  url: string;
  headers: Record<string, string>;
  body: any;
}

const requestPool = new ObjectPool<PooledRequest>(
  () => ({ url: '', headers: {}, body: null }),
  (req) => {
    req.url = '';
    req.headers = {};
    req.body = null;
  }
);

// Acquire from pool
const request = requestPool.acquire();
request.url = '/api/data';

// Release back to pool when done
requestPool.release(request);
```

### Streaming Large Data

```typescript
import { createReadStream, createWriteStream } from 'fs';
import { pipeline } from 'stream/promises';
import { Transform } from 'stream';

// ❌ Bad - loads entire file into memory
async function processFileBad(path: string): Promise<void> {
  const data = await fs.promises.readFile(path, 'utf-8');
  const processed = processData(data);
  await fs.promises.writeFile('output.txt', processed);
}

// ✅ Good - streams data
async function processFileGood(inputPath: string, outputPath: string): Promise<void> {
  const processTransform = new Transform({
    transform(chunk, encoding, callback) {
      const processed = processChunk(chunk.toString());
      callback(null, processed);
    },
  });

  await pipeline(
    createReadStream(inputPath),
    processTransform,
    createWriteStream(outputPath)
  );
}
```

### WeakMap and WeakSet

```typescript
// Use WeakMap for object metadata that shouldn't prevent GC
const objectMetadata = new WeakMap<object, { created: Date; accessed: Date }>();

function trackObject(obj: object): void {
  objectMetadata.set(obj, {
    created: new Date(),
    accessed: new Date(),
  });
}

function accessObject(obj: object): void {
  const metadata = objectMetadata.get(obj);
  if (metadata) {
    metadata.accessed = new Date();
  }
}

// When obj is garbage collected, its entry in WeakMap is also removed
```

## Memory Budget Alerts

```typescript
// Alert when approaching memory limits
class MemoryMonitor {
  private thresholdPercent = 80;
  private checkInterval: NodeJS.Timeout | null = null;

  start(intervalMs: number = 30000): void {
    this.checkInterval = setInterval(() => this.check(), intervalMs);
  }

  stop(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
    }
  }

  private check(): void {
    const usage = process.memoryUsage();
    const stats = v8.getHeapStatistics();

    const usedPercent = (stats.used_heap_size / stats.heap_size_limit) * 100;

    if (usedPercent > this.thresholdPercent) {
      console.error('Memory threshold exceeded!', {
        usedPercent: `${usedPercent.toFixed(1)}%`,
        heapUsed: formatBytes(usage.heapUsed),
        heapLimit: formatBytes(stats.heap_size_limit),
      });

      // Optionally trigger GC or alert
      this.handleMemoryPressure();
    }
  }

  private handleMemoryPressure(): void {
    // Clear caches
    // Alert monitoring
    // Trigger GC if available
  }
}
```

## Best Practices

1. **Monitor memory continuously** - Track trends over time
2. **Take regular heap snapshots** - Compare to find leaks
3. **Clean up event listeners** - Remove when component is destroyed
4. **Use WeakMap/WeakSet** - For metadata on objects
5. **Stream large data** - Don't load into memory
6. **Set memory limits** - Crash early rather than slowly degrade
7. **Profile in production** - Dev may mask leaks
8. **Implement object pooling** - For frequently allocated objects
