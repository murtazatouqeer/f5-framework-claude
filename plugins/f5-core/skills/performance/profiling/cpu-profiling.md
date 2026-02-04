---
name: cpu-profiling
description: CPU profiling techniques for Node.js applications
category: performance/profiling
applies_to: backend
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# CPU Profiling

## Overview

CPU profiling identifies code that consumes excessive CPU time,
helping optimize computation-heavy operations.

## Node.js Built-in Profiler

### V8 CPU Profiler

```bash
# Start Node.js with profiler enabled
node --prof app.js

# Generate human-readable output
node --prof-process isolate-*.log > processed.txt
```

### Inspector Protocol

```typescript
import inspector from 'inspector';
import fs from 'fs';

// Start CPU profiling
const session = new inspector.Session();
session.connect();

session.post('Profiler.enable', () => {
  session.post('Profiler.start', () => {
    // Run code to profile
    runExpensiveOperation();

    // Stop and save profile
    session.post('Profiler.stop', (err, { profile }) => {
      if (err) throw err;

      fs.writeFileSync(
        'cpu-profile.cpuprofile',
        JSON.stringify(profile)
      );
      console.log('Profile saved');
    });
  });
});

// Load in Chrome DevTools: chrome://inspect
```

### Programmatic Profiling

```typescript
import { performance, PerformanceObserver } from 'perf_hooks';

// Mark important operations
function profiledFunction() {
  performance.mark('start-operation');

  // Expensive operation
  heavyComputation();

  performance.mark('end-operation');
  performance.measure('operation', 'start-operation', 'end-operation');
}

// Observe measurements
const obs = new PerformanceObserver((list) => {
  const entries = list.getEntries();
  entries.forEach((entry) => {
    console.log(`${entry.name}: ${entry.duration.toFixed(2)}ms`);
  });
});

obs.observe({ entryTypes: ['measure'] });
```

## 0x - Flamegraph Generator

```bash
# Install 0x
npm install -g 0x

# Generate flamegraph
0x app.js

# With specific duration
0x --collect-only -D 30000 app.js  # 30 seconds
0x --visualize-only /path/to/profile.json

# Output: flamegraph-*.html
```

### Interpreting Flamegraphs

```
┌─────────────────────────────────────────────────────────────────┐
│                        main                                      │
├─────────────────────────────────────────────────────────────────┤
│          │                handleRequest                          │
│          ├───────────────────────────────────────────────────────┤
│          │    │         processData (40%)                        │
│          │    ├───────────────────────────────────────────────────┤
│          │    │  parseJSON │  transform  │    validate           │
│          │    │   (15%)    │   (20%)     │     (5%)              │
└──────────┴────┴────────────┴─────────────┴───────────────────────┘

Width = Time spent in function
Height = Call stack depth
Look for wide bars = optimization targets
```

## Clinic.js

```bash
# Install Clinic.js
npm install -g clinic

# Detect various issues
clinic doctor -- node app.js
clinic flame -- node app.js  # CPU flamegraph
clinic bubbleprof -- node app.js  # Async operations
clinic heapprofiler -- node app.js  # Memory

# Under load
clinic doctor --autocannon [OPTIONS] -- node app.js
```

### Clinic Doctor Output

```
┌───────────────────────────────────────────────────────────────┐
│ Detected issue: I/O bottleneck                                │
├───────────────────────────────────────────────────────────────┤
│ CPU: ████░░░░░░  40%    (low CPU, high I/O wait)             │
│ Event Loop: ████████░░  80% blocked                          │
│ Memory: ███░░░░░░░  30%                                      │
├───────────────────────────────────────────────────────────────┤
│ Recommendation: Optimize database queries or use caching     │
└───────────────────────────────────────────────────────────────┘
```

## Chrome DevTools Profiling

### Connect to Node.js

```bash
# Start with inspect flag
node --inspect app.js

# Or break immediately
node --inspect-brk app.js
```

### Profile in DevTools

1. Open `chrome://inspect`
2. Click "Open dedicated DevTools for Node"
3. Go to "Performance" tab
4. Click "Record"
5. Perform operations
6. Click "Stop"
7. Analyze timeline

## Common CPU Issues

### Blocking Event Loop

```typescript
// ❌ Bad - blocks event loop
function processSync(data: any[]) {
  return data.map((item) => expensiveOperation(item));
}

// ✅ Good - yield to event loop
async function processAsync(data: any[]) {
  const results = [];
  for (const item of data) {
    results.push(expensiveOperation(item));

    // Yield every 100 items
    if (results.length % 100 === 0) {
      await new Promise((resolve) => setImmediate(resolve));
    }
  }
  return results;
}
```

### Inefficient Loops

```typescript
// ❌ Bad - O(n²) nested loops
function findDuplicates(items: string[]): string[] {
  const duplicates: string[] = [];
  for (let i = 0; i < items.length; i++) {
    for (let j = i + 1; j < items.length; j++) {
      if (items[i] === items[j] && !duplicates.includes(items[i])) {
        duplicates.push(items[i]);
      }
    }
  }
  return duplicates;
}

// ✅ Good - O(n) with Set
function findDuplicates(items: string[]): string[] {
  const seen = new Set<string>();
  const duplicates = new Set<string>();

  for (const item of items) {
    if (seen.has(item)) {
      duplicates.add(item);
    }
    seen.add(item);
  }

  return Array.from(duplicates);
}
```

### JSON Serialization

```typescript
// ❌ Bad - repeated serialization
function log(data: any) {
  console.log('Data:', JSON.stringify(data));
  metrics.record(JSON.stringify(data));
  audit.log(JSON.stringify(data));
}

// ✅ Good - serialize once
function log(data: any) {
  const serialized = JSON.stringify(data);
  console.log('Data:', serialized);
  metrics.record(serialized);
  audit.log(serialized);
}

// ✅ Better - lazy serialization
function log(data: any) {
  const lazySerialize = () => JSON.stringify(data);

  if (config.logLevel === 'debug') {
    console.log('Data:', lazySerialize());
  }
  metrics.record(lazySerialize);
}
```

### Regular Expressions

```typescript
// ❌ Bad - catastrophic backtracking
const badRegex = /^(a+)+$/;
badRegex.test('aaaaaaaaaaaaaaaaaaaaaaaaaaaa!'); // Takes forever

// ✅ Good - atomic grouping or simpler pattern
const goodRegex = /^a+$/;
```

## Event Loop Monitoring

```typescript
// Monitor event loop lag
function monitorEventLoop(threshold: number = 100): void {
  let lastCheck = Date.now();

  setInterval(() => {
    const now = Date.now();
    const lag = now - lastCheck - 1000; // Expected interval is 1000ms

    if (lag > threshold) {
      console.warn(`Event loop lag: ${lag}ms`);
    }

    lastCheck = now;
  }, 1000);
}

// Using perf_hooks
import { monitorEventLoopDelay } from 'perf_hooks';

const histogram = monitorEventLoopDelay({ resolution: 20 });
histogram.enable();

setInterval(() => {
  console.log({
    min: histogram.min,
    max: histogram.max,
    mean: histogram.mean,
    percentile99: histogram.percentile(99),
  });
  histogram.reset();
}, 5000);
```

## Worker Threads for CPU-Intensive Tasks

```typescript
// worker.ts
import { parentPort, workerData } from 'worker_threads';

function heavyComputation(data: number[]): number {
  return data.reduce((sum, n) => sum + Math.sqrt(n), 0);
}

if (parentPort) {
  const result = heavyComputation(workerData);
  parentPort.postMessage(result);
}

// main.ts
import { Worker } from 'worker_threads';

async function runInWorker(data: number[]): Promise<number> {
  return new Promise((resolve, reject) => {
    const worker = new Worker('./worker.ts', {
      workerData: data,
    });

    worker.on('message', resolve);
    worker.on('error', reject);
    worker.on('exit', (code) => {
      if (code !== 0) {
        reject(new Error(`Worker exited with code ${code}`));
      }
    });
  });
}

// Worker pool for multiple tasks
import Piscina from 'piscina';

const pool = new Piscina({
  filename: './worker.ts',
  maxThreads: 4,
});

const results = await Promise.all(
  chunks.map((chunk) => pool.run(chunk))
);
```

## Profiling Middleware

```typescript
// Express middleware for request profiling
import { performance } from 'perf_hooks';

function profilingMiddleware() {
  return (req: Request, res: Response, next: NextFunction) => {
    const start = performance.now();

    res.on('finish', () => {
      const duration = performance.now() - start;

      if (duration > 1000) {
        console.warn(`Slow request: ${req.method} ${req.path} - ${duration.toFixed(2)}ms`);
      }

      metrics.histogram('http_request_duration', duration, {
        method: req.method,
        path: req.route?.path || 'unknown',
        status: res.statusCode,
      });
    });

    next();
  };
}
```

## Best Practices

1. **Profile in production-like environment** - Dev builds behave differently
2. **Use flamegraphs for visualization** - Easier to spot issues
3. **Monitor event loop lag** - Detect blocking code
4. **Offload CPU work to workers** - Keep main thread responsive
5. **Cache computation results** - Avoid redundant work
6. **Profile under load** - Issues often appear at scale
7. **Compare before/after** - Validate optimizations
8. **Set performance budgets** - Alert on regressions
