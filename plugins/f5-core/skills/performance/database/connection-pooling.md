---
name: connection-pooling
description: Database connection pooling configuration and best practices
category: performance/database
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Connection Pooling

## Overview

Connection pooling maintains a pool of database connections that can be reused,
avoiding the overhead of establishing new connections for each query.

## Why Connection Pooling?

```
Without Pooling:
Request → Create Connection → Query → Close Connection
         ~50-100ms overhead per request

With Pooling:
Request → Get Connection from Pool → Query → Return to Pool
         ~1ms overhead per request
```

### Connection Lifecycle Cost

| Operation | Time |
|-----------|------|
| TCP handshake | 1-10ms |
| SSL handshake | 10-50ms |
| PostgreSQL authentication | 5-20ms |
| **Total new connection** | **16-80ms** |
| Get from pool | <1ms |

## Prisma Connection Pooling

### Configuration

```prisma
// schema.prisma
datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}
```

```bash
# .env - Connection string with pool settings
DATABASE_URL="postgresql://user:pass@localhost:5432/db?connection_limit=20&pool_timeout=30"

# Parameters:
# connection_limit: Max connections in pool (default: num_cpus * 2 + 1)
# pool_timeout: Seconds to wait for available connection (default: 10)
```

### Recommended Pool Sizes

```typescript
// Pool size recommendations
const poolConfig = {
  // Small app (1-2 instances)
  small: {
    connectionLimit: 10,
    poolTimeout: 10,
  },

  // Medium app (3-5 instances)
  medium: {
    connectionLimit: 20,
    poolTimeout: 15,
  },

  // Large app (10+ instances)
  large: {
    connectionLimit: 5, // Per instance, use external pooler
    poolTimeout: 30,
  },
};

// Formula: connections_per_instance = max_db_connections / num_instances
// PostgreSQL default max_connections = 100
// 5 instances → 100 / 5 = 20 connections per instance
```

## External Connection Poolers

### PgBouncer

Most popular PostgreSQL connection pooler.

```ini
# pgbouncer.ini
[databases]
mydb = host=db.example.com port=5432 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

# Pool settings
pool_mode = transaction           # transaction | session | statement
default_pool_size = 20           # connections per user/database
max_client_conn = 1000           # max client connections
min_pool_size = 5                # maintain minimum connections
reserve_pool_size = 5            # extra connections for burst
reserve_pool_timeout = 5         # seconds before using reserve

# Timeouts
server_connect_timeout = 15
server_idle_timeout = 600
server_lifetime = 3600
client_idle_timeout = 0
```

```typescript
// Prisma with PgBouncer
// .env
DATABASE_URL="postgresql://user:pass@pgbouncer:6432/mydb?pgbouncer=true"

// The pgbouncer=true flag tells Prisma to:
// - Not use prepared statements (incompatible with transaction mode)
// - Handle connection differently for compatibility
```

### Pool Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                       Pool Modes                                 │
├──────────────┬──────────────────────────────────────────────────┤
│   Session    │ Connection assigned for entire session           │
│              │ Best for: Temporary tables, SET commands         │
│              │ Efficiency: Low (1 client = 1 server connection) │
├──────────────┼──────────────────────────────────────────────────┤
│ Transaction  │ Connection assigned per transaction              │
│              │ Best for: Most web applications                  │
│              │ Efficiency: High (many clients share connections)│
├──────────────┼──────────────────────────────────────────────────┤
│  Statement   │ Connection returned after each statement         │
│              │ Best for: Simple queries, no multi-statement txn │
│              │ Efficiency: Highest                              │
└──────────────┴──────────────────────────────────────────────────┘
```

## Connection Pool Monitoring

### Metrics to Track

```typescript
// Monitor pool health
interface PoolMetrics {
  totalConnections: number;     // Current connections in pool
  idleConnections: number;      // Available connections
  activeConnections: number;    // In-use connections
  waitingRequests: number;      // Requests waiting for connection
  maxConnections: number;       // Pool size limit
  connectionAcquireTime: number; // Time to get connection (ms)
}

// Alert thresholds
const alertThresholds = {
  connectionUtilization: 90,    // % of pool in use
  waitingRequests: 10,          // Requests queued
  acquireTime: 100,             // ms to get connection
};
```

### PgBouncer Stats

```sql
-- Connect to PgBouncer admin console
psql -h localhost -p 6432 -U pgbouncer pgbouncer

-- Show pool stats
SHOW POOLS;
-- cl_active: active client connections
-- cl_waiting: clients waiting for server
-- sv_active: active server connections
-- sv_idle: idle server connections

-- Show stats
SHOW STATS;
-- total_xact_count: total transactions
-- total_query_count: total queries
-- avg_xact_time: average transaction time
```

### Custom Monitoring

```typescript
// Prisma middleware to track connection usage
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

// Track query timing
prisma.$use(async (params, next) => {
  const start = performance.now();
  const result = await next(params);
  const duration = performance.now() - start;

  metrics.histogram('db.query.duration', duration, {
    model: params.model,
    action: params.action,
  });

  return result;
});

// Health check endpoint
app.get('/health/db', async (req, res) => {
  const start = performance.now();

  try {
    await prisma.$queryRaw`SELECT 1`;
    const latency = performance.now() - start;

    res.json({
      status: 'healthy',
      latency: `${latency.toFixed(2)}ms`,
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      error: error.message,
    });
  }
});
```

## Connection Pool Sizing

### Formula

```typescript
// Calculate optimal pool size
function calculatePoolSize(config: {
  maxDbConnections: number;
  numInstances: number;
  safetyMargin: number;       // Usually 0.8-0.9
  minConnectionsPerInstance: number;
}): number {
  const { maxDbConnections, numInstances, safetyMargin, minConnectionsPerInstance } = config;

  const maxPerInstance = Math.floor(
    (maxDbConnections * safetyMargin) / numInstances
  );

  return Math.max(minConnectionsPerInstance, maxPerInstance);
}

// Example
const poolSize = calculatePoolSize({
  maxDbConnections: 100,  // PostgreSQL max_connections
  numInstances: 5,        // App instances
  safetyMargin: 0.8,      // Keep 20% for admin/monitoring
  minConnectionsPerInstance: 5,
});
// Result: 16 connections per instance
```

### PostgreSQL Configuration

```sql
-- Check current settings
SHOW max_connections;           -- Default: 100
SHOW shared_buffers;            -- Memory for caching
SHOW work_mem;                  -- Memory per operation

-- Recommended settings for connection pooling
-- postgresql.conf
max_connections = 200           -- Higher with external pooler
shared_buffers = 256MB          -- 25% of RAM for dedicated server
work_mem = 16MB                 -- Per operation memory
```

## Serverless Considerations

### Prisma with Serverless

```typescript
// For serverless (AWS Lambda, Vercel)
// Use external pooler or Prisma Accelerate

// Option 1: PgBouncer
DATABASE_URL="postgresql://user:pass@pgbouncer:6432/db?pgbouncer=true"

// Option 2: Prisma Accelerate
DATABASE_URL="prisma://accelerate.prisma-data.net/?api_key=..."

// Option 3: Connection string with lower limits
DATABASE_URL="postgresql://user:pass@db:5432/db?connection_limit=1"
// Single connection per Lambda instance
```

### Cold Start Optimization

```typescript
// Reuse Prisma client across invocations
import { PrismaClient } from '@prisma/client';

// Declare outside handler
const prisma = global.prisma || new PrismaClient();

if (process.env.NODE_ENV !== 'production') {
  global.prisma = prisma;
}

export async function handler(event: any) {
  // Prisma client is reused across warm invocations
  const result = await prisma.user.findMany();
  return result;
}

// Clean shutdown for graceful termination
process.on('beforeExit', async () => {
  await prisma.$disconnect();
});
```

## Troubleshooting

### Connection Exhaustion

```typescript
// Symptoms: "Connection pool exhausted" errors

// Solutions:
// 1. Increase pool size
DATABASE_URL="...?connection_limit=30"

// 2. Reduce connection usage
// Use transactions wisely
await prisma.$transaction(async (tx) => {
  // All queries use same connection
  await tx.user.create({ data });
  await tx.order.create({ data });
});

// 3. Add timeout handling
DATABASE_URL="...?connection_limit=20&pool_timeout=30"

// 4. Check for connection leaks
// Ensure all queries complete or timeout
```

### Connection Leaks

```typescript
// Detect leaks with monitoring
let activeQueries = 0;

prisma.$use(async (params, next) => {
  activeQueries++;
  console.log(`Active queries: ${activeQueries}`);

  try {
    return await next(params);
  } finally {
    activeQueries--;
  }
});

// If activeQueries keeps growing, you have a leak
```

### Slow Connection Acquisition

```typescript
// Monitor connection wait time
const acquireStart = performance.now();
await prisma.$queryRaw`SELECT 1`;
const acquireTime = performance.now() - acquireStart;

if (acquireTime > 100) {
  console.warn(`Slow connection acquisition: ${acquireTime}ms`);
  // Consider:
  // - Increasing pool size
  // - Reducing query duration
  // - Using external pooler
}
```

## Best Practices

1. **Size pools appropriately** - Not too small (queuing) or large (resource waste)
2. **Use external pooler for serverless** - PgBouncer or Prisma Accelerate
3. **Monitor pool metrics** - Track utilization and wait times
4. **Handle timeouts gracefully** - Don't let requests hang forever
5. **Clean up connections** - Proper shutdown handling
6. **Consider pool mode** - Transaction mode for web apps
7. **Test under load** - Verify pool handles expected concurrency
8. **Set up alerts** - Know when pool is exhausted
