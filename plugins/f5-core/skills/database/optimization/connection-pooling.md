---
name: connection-pooling
description: Database connection pooling strategies and configuration
category: database/optimization
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Connection Pooling

## Overview

Connection pooling reuses database connections to avoid the overhead of
creating new connections for each request. Proper pooling is essential
for application scalability and database health.

## Why Connection Pooling

```
┌─────────────────────────────────────────────────────────────────┐
│               Connection Pooling Benefits                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Without Pooling:                                                │
│  Request → Open Connection → Query → Close Connection           │
│            (50-100ms)         (5ms)    (5ms)                    │
│  Total: ~60-110ms per request                                   │
│                                                                  │
│  With Pooling:                                                   │
│  Request → Get Connection → Query → Return Connection           │
│            (0.1ms)          (5ms)    (0.1ms)                    │
│  Total: ~5.2ms per request                                      │
│                                                                  │
│  Benefits:                                                       │
│  ✓ Reduced connection overhead                                  │
│  ✓ Limited total connections to database                        │
│  ✓ Better resource utilization                                  │
│  ✓ Improved application response time                           │
│  ✓ Protection against connection storms                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Pool Configuration

### Basic Pool Parameters

```
┌─────────────────────────────────────────────────────────────────┐
│                  Pool Configuration Parameters                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Minimum Pool Size (min_connections)                            │
│  - Connections kept open even when idle                         │
│  - Set based on baseline traffic                                │
│  - Typical: 2-5 for small apps, 10-20 for larger                │
│                                                                  │
│  Maximum Pool Size (max_connections)                            │
│  - Upper limit on total connections                             │
│  - Set based on database limits and app needs                   │
│  - Typical: 10-50 per application instance                      │
│                                                                  │
│  Connection Timeout (connection_timeout)                        │
│  - How long to wait for a free connection                       │
│  - Fail fast vs queue requests                                  │
│  - Typical: 5-30 seconds                                        │
│                                                                  │
│  Idle Timeout (idle_timeout)                                    │
│  - When to close unused connections                             │
│  - Balance between readiness and resource usage                 │
│  - Typical: 10-30 minutes                                       │
│                                                                  │
│  Max Lifetime (max_lifetime)                                    │
│  - Maximum age of a connection                                  │
│  - Prevents issues with stale connections                       │
│  - Typical: 30-60 minutes                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Sizing Formula

```
Total DB connections needed =
  (Application instances) × (Pool size per instance) +
  (Admin connections) + (Monitoring connections) + (Buffer)

Example:
  4 app servers × 20 connections = 80
  + 5 admin connections
  + 5 monitoring connections
  + 10 buffer
  = 100 total connections needed

PostgreSQL default max_connections = 100
May need to increase or use external pooler
```

## PgBouncer (PostgreSQL)

### Installation

```bash
# Ubuntu/Debian
sudo apt-get install pgbouncer

# macOS
brew install pgbouncer

# Docker
docker run -d --name pgbouncer \
  -e DATABASE_URL="postgres://user:pass@db:5432/mydb" \
  -p 6432:6432 \
  edoburu/pgbouncer
```

### Configuration (pgbouncer.ini)

```ini
[databases]
; Database connection strings
mydb = host=localhost port=5432 dbname=mydb
mydb_readonly = host=replica.example.com port=5432 dbname=mydb

; With connection limit per database
production = host=prod-db.example.com port=5432 dbname=prod pool_size=50

[pgbouncer]
; Listen address and port
listen_addr = 0.0.0.0
listen_port = 6432

; Authentication
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt

; Pool mode (transaction, session, statement)
pool_mode = transaction

; Pool size settings
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3

; Connections
max_client_conn = 1000
max_db_connections = 100

; Timeouts
server_connect_timeout = 15
server_idle_timeout = 600
server_lifetime = 3600
client_idle_timeout = 0

; Logging
log_connections = 1
log_disconnections = 1
log_pooler_errors = 1

; Stats
stats_period = 60
```

### Pool Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                   PgBouncer Pool Modes                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SESSION MODE (pool_mode = session)                             │
│  - Connection assigned for entire client session                │
│  - Supports all PostgreSQL features                             │
│  - Least efficient pooling                                      │
│  - Use when: LISTEN/NOTIFY, prepared statements needed          │
│                                                                  │
│  TRANSACTION MODE (pool_mode = transaction)                     │
│  - Connection assigned per transaction                          │
│  - Most common mode for web applications                        │
│  - Good balance of features and efficiency                      │
│  - Limitations: No session-level features between transactions  │
│                                                                  │
│  STATEMENT MODE (pool_mode = statement)                         │
│  - Connection assigned per statement                            │
│  - Most aggressive pooling                                      │
│  - Very limited: No transactions, no SET commands               │
│  - Use for: Simple read-only queries                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### User Authentication (userlist.txt)

```
; Format: "username" "password"
; Password can be plain, md5, or scram-sha-256

; Plain text (not recommended)
"myuser" "plainpassword"

; MD5 hash (postgres format)
"myuser" "md5a1b2c3d4e5f6..."

; Generate MD5 hash:
; echo -n "passwordusername" | md5sum | awk '{print "md5" $1}'
```

### HBA Configuration (pgbouncer_hba.conf)

```
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    all             all             0.0.0.0/0               md5
host    all             all             ::0/0                   md5
local   all             all                                     peer
```

## Application-Level Pooling

### Node.js with pg-pool

```typescript
import { Pool, PoolConfig } from 'pg';

const poolConfig: PoolConfig = {
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,

  // Pool settings
  min: 2,                    // Minimum connections
  max: 20,                   // Maximum connections
  idleTimeoutMillis: 30000,  // Close idle connections after 30s
  connectionTimeoutMillis: 5000, // Fail if can't connect in 5s
  maxUses: 7500,            // Close after 7500 queries

  // Statement timeout
  statement_timeout: 30000,  // 30 second query timeout
};

const pool = new Pool(poolConfig);

// Handle pool errors
pool.on('error', (err, client) => {
  console.error('Unexpected error on idle client', err);
});

// Query with automatic connection management
async function query(text: string, params?: any[]) {
  const start = Date.now();
  const res = await pool.query(text, params);
  const duration = Date.now() - start;
  console.log('Executed query', { text, duration, rows: res.rowCount });
  return res;
}

// Transaction with explicit client
async function transaction<T>(
  callback: (client: any) => Promise<T>
): Promise<T> {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    const result = await callback(client);
    await client.query('COMMIT');
    return result;
  } catch (e) {
    await client.query('ROLLBACK');
    throw e;
  } finally {
    client.release();
  }
}

// Usage
await query('SELECT * FROM users WHERE id = $1', [userId]);

await transaction(async (client) => {
  await client.query('UPDATE accounts SET balance = balance - $1 WHERE id = $2', [amount, fromId]);
  await client.query('UPDATE accounts SET balance = balance + $1 WHERE id = $2', [amount, toId]);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  await pool.end();
  process.exit(0);
});
```

### Python with SQLAlchemy

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Create engine with pool configuration
engine = create_engine(
    "postgresql://user:pass@localhost:5432/mydb",
    poolclass=QueuePool,
    pool_size=5,           # Base pool size
    max_overflow=10,       # Additional connections allowed
    pool_timeout=30,       # Wait time for connection
    pool_recycle=1800,     # Recycle connections after 30 min
    pool_pre_ping=True,    # Test connections before use
)

# Create session factory
Session = sessionmaker(bind=engine)

# Context manager for sessions
from contextlib import contextmanager

@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Usage
with get_session() as session:
    user = session.query(User).filter_by(id=user_id).first()
    user.name = "New Name"
    # Commits automatically

# Monitor pool status
print(f"Pool size: {engine.pool.size()}")
print(f"Checked out: {engine.pool.checkedout()}")
print(f"Overflow: {engine.pool.overflow()}")
```

### Java with HikariCP

```java
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;

public class DatabasePool {
    private static HikariDataSource dataSource;

    static {
        HikariConfig config = new HikariConfig();

        // Connection settings
        config.setJdbcUrl("jdbc:postgresql://localhost:5432/mydb");
        config.setUsername("user");
        config.setPassword("password");

        // Pool settings
        config.setMinimumIdle(5);
        config.setMaximumPoolSize(20);
        config.setIdleTimeout(300000);        // 5 minutes
        config.setMaxLifetime(1800000);       // 30 minutes
        config.setConnectionTimeout(30000);   // 30 seconds
        config.setValidationTimeout(5000);    // 5 seconds

        // Performance settings
        config.addDataSourceProperty("cachePrepStmts", "true");
        config.addDataSourceProperty("prepStmtCacheSize", "250");
        config.addDataSourceProperty("prepStmtCacheSqlLimit", "2048");

        // Metrics
        config.setMetricRegistry(metricRegistry);

        dataSource = new HikariDataSource(config);
    }

    public static Connection getConnection() throws SQLException {
        return dataSource.getConnection();
    }

    // Usage with try-with-resources
    public User getUser(String id) throws SQLException {
        String sql = "SELECT * FROM users WHERE id = ?";
        try (Connection conn = getConnection();
             PreparedStatement ps = conn.prepareStatement(sql)) {
            ps.setString(1, id);
            try (ResultSet rs = ps.executeQuery()) {
                if (rs.next()) {
                    return mapUser(rs);
                }
            }
        }
        return null;
    }
}
```

## Monitoring Connection Pools

### PostgreSQL Connection Stats

```sql
-- Current connections by state
SELECT
  state,
  COUNT(*) as count,
  MAX(EXTRACT(EPOCH FROM (NOW() - state_change))) as max_duration_seconds
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;

-- Connections by application
SELECT
  application_name,
  COUNT(*) as connections,
  SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active,
  SUM(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY application_name;

-- Waiting connections
SELECT
  COUNT(*) as waiting_connections
FROM pg_stat_activity
WHERE wait_event_type IS NOT NULL
  AND state = 'active';

-- Connection age distribution
SELECT
  CASE
    WHEN EXTRACT(EPOCH FROM (NOW() - backend_start)) < 60 THEN '< 1 min'
    WHEN EXTRACT(EPOCH FROM (NOW() - backend_start)) < 300 THEN '1-5 min'
    WHEN EXTRACT(EPOCH FROM (NOW() - backend_start)) < 1800 THEN '5-30 min'
    ELSE '> 30 min'
  END as age_bucket,
  COUNT(*) as count
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY 1
ORDER BY 1;
```

### PgBouncer Stats

```sql
-- Connect to PgBouncer admin console
-- psql -p 6432 -U pgbouncer pgbouncer

-- Pool statistics
SHOW POOLS;
/*
 database |   user   | cl_active | cl_waiting | sv_active | sv_idle | sv_used | sv_tested | sv_login | maxwait
----------+----------+-----------+------------+-----------+---------+---------+-----------+----------+---------
 mydb     | myuser   |         5 |          0 |         3 |       2 |       0 |         0 |        0 |       0
*/

-- Client statistics
SHOW CLIENTS;

-- Server connections
SHOW SERVERS;

-- Overall stats
SHOW STATS;

-- Configuration
SHOW CONFIG;

-- Memory usage
SHOW MEM;
```

### Application Metrics

```typescript
// Node.js pool monitoring
import { Pool } from 'pg';
import { register, Gauge } from 'prom-client';

const pool = new Pool(config);

// Create Prometheus metrics
const poolTotal = new Gauge({
  name: 'pg_pool_connections_total',
  help: 'Total connections in pool'
});

const poolIdle = new Gauge({
  name: 'pg_pool_connections_idle',
  help: 'Idle connections in pool'
});

const poolWaiting = new Gauge({
  name: 'pg_pool_waiting_count',
  help: 'Clients waiting for connection'
});

// Update metrics periodically
setInterval(() => {
  poolTotal.set(pool.totalCount);
  poolIdle.set(pool.idleCount);
  poolWaiting.set(pool.waitingCount);
}, 5000);

// Log pool events
pool.on('connect', () => console.log('Pool: connection created'));
pool.on('acquire', () => console.log('Pool: connection acquired'));
pool.on('release', () => console.log('Pool: connection released'));
pool.on('remove', () => console.log('Pool: connection removed'));
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Connection Pooling Best Practices                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Right-size your pool                                        │
│     - Too small: Requests queue up                              │
│     - Too large: Database overwhelmed                           │
│     - Start with (CPU cores * 2) + disk spindles                │
│                                                                  │
│  2. Always release connections                                  │
│     - Use try/finally or connection managers                    │
│     - Set appropriate timeouts                                  │
│                                                                  │
│  3. Use transactions appropriately                              │
│     - Don't hold connections during I/O                         │
│     - Keep transactions short                                   │
│                                                                  │
│  4. Monitor pool health                                         │
│     - Track active/idle/waiting connections                     │
│     - Alert on pool exhaustion                                  │
│                                                                  │
│  5. Configure connection lifetime                               │
│     - Prevent stale connections                                 │
│     - Work with database's idle timeout                         │
│                                                                  │
│  6. Use external pooler for high scale                          │
│     - PgBouncer for PostgreSQL                                  │
│     - ProxySQL for MySQL                                        │
│                                                                  │
│  7. Handle connection failures gracefully                       │
│     - Retry with backoff                                        │
│     - Circuit breaker pattern                                   │
│                                                                  │
│  8. Test pool behavior under load                               │
│     - Verify timeout handling                                   │
│     - Check pool exhaustion behavior                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Pool exhaustion | Timeouts, slow responses | Increase pool size or optimize queries |
| Connection leaks | Growing connections | Check for unreleased connections |
| Stale connections | Random errors | Enable health checks, reduce max lifetime |
| Too many connections | Database errors | Use external pooler, reduce pool size |
| Slow connection creation | Initial request latency | Set minimum pool size |
