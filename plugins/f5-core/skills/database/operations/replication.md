---
name: replication
description: Database replication strategies and configuration
category: database/operations
applies_to: [postgresql, mysql]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Database Replication

## Overview

Replication copies data from one database server (primary) to one or more
other servers (replicas). It provides high availability, read scaling,
and disaster recovery capabilities.

## Replication Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    Replication Types                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Physical (Streaming) Replication                               │
│  ├── Copies WAL (Write-Ahead Log) records                       │
│  ├── Byte-for-byte copy of database                             │
│  ├── Fast, low overhead                                         │
│  └── Limited to same PostgreSQL version                         │
│                                                                  │
│  Logical Replication                                             │
│  ├── Copies changes at row level                                │
│  ├── Can replicate specific tables                              │
│  ├── Supports different versions/schemas                        │
│  └── Higher overhead than physical                              │
│                                                                  │
│  Synchronous vs Asynchronous                                    │
│  ├── Sync: Primary waits for replica confirmation               │
│  │   └── Zero data loss, higher latency                         │
│  └── Async: Primary doesn't wait                                │
│      └── Possible data loss, lower latency                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## PostgreSQL Streaming Replication

### Primary Server Configuration

```bash
# postgresql.conf on primary
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB
hot_standby = on

# For synchronous replication (optional)
synchronous_commit = on
synchronous_standby_names = 'replica1'
```

```bash
# pg_hba.conf - Allow replication connections
# TYPE  DATABASE        USER            ADDRESS                 METHOD
host    replication     replicator      10.0.0.0/8              scram-sha-256
host    replication     replicator      replica.example.com     scram-sha-256
```

```sql
-- Create replication user
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_password';
```

### Replica Server Setup

```bash
# Stop PostgreSQL on replica
sudo systemctl stop postgresql

# Clear data directory
rm -rf /var/lib/postgresql/15/main/*

# Take base backup from primary
pg_basebackup -h primary.example.com -U replicator -D /var/lib/postgresql/15/main -Fp -Xs -P -R

# The -R flag creates standby.signal and postgresql.auto.conf with connection info

# Start replica
sudo systemctl start postgresql
```

### Verify Replication

```sql
-- On primary: Check replication status
SELECT
  client_addr,
  state,
  sent_lsn,
  write_lsn,
  flush_lsn,
  replay_lsn,
  sync_state,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes
FROM pg_stat_replication;

-- On replica: Check if in recovery mode
SELECT pg_is_in_recovery();  -- Should return 't'

-- Check replay lag
SELECT
  now() - pg_last_xact_replay_timestamp() AS replay_lag;
```

## Logical Replication

### Publisher (Source)

```sql
-- postgresql.conf
wal_level = logical
max_replication_slots = 10
max_wal_senders = 10

-- Create publication for specific tables
CREATE PUBLICATION my_publication FOR TABLE users, orders, products;

-- Or all tables
CREATE PUBLICATION all_tables FOR ALL TABLES;

-- Add/remove tables
ALTER PUBLICATION my_publication ADD TABLE new_table;
ALTER PUBLICATION my_publication DROP TABLE old_table;
```

### Subscriber (Destination)

```sql
-- Create subscription
CREATE SUBSCRIPTION my_subscription
  CONNECTION 'host=publisher.example.com dbname=mydb user=replicator password=pass'
  PUBLICATION my_publication;

-- Check subscription status
SELECT * FROM pg_stat_subscription;

-- Manage subscription
ALTER SUBSCRIPTION my_subscription DISABLE;
ALTER SUBSCRIPTION my_subscription ENABLE;
ALTER SUBSCRIPTION my_subscription REFRESH PUBLICATION;
DROP SUBSCRIPTION my_subscription;
```

### Use Cases for Logical Replication

```
┌─────────────────────────────────────────────────────────────────┐
│              Logical Replication Use Cases                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Selective Replication                                       │
│     - Replicate only specific tables                            │
│     - Filter rows with WHERE clause                             │
│                                                                  │
│  2. Version Upgrades                                             │
│     - Replicate to newer PostgreSQL version                     │
│     - Minimal downtime migration                                │
│                                                                  │
│  3. Multi-Master (with extensions)                              │
│     - BDR (Bi-Directional Replication)                          │
│     - Conflict resolution required                              │
│                                                                  │
│  4. Data Consolidation                                          │
│     - Merge data from multiple sources                          │
│     - Central reporting database                                │
│                                                                  │
│  5. Different Indexes/Schemas                                   │
│     - Replica can have different indexes                        │
│     - Optimized for specific workloads                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## High Availability Setup

### With Patroni (Recommended)

```yaml
# patroni.yml
scope: postgres-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008
  connect_address: node1.example.com:8008

etcd:
  hosts:
    - etcd1.example.com:2379
    - etcd2.example.com:2379
    - etcd3.example.com:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        wal_level: replica
        hot_standby: on
        max_wal_senders: 10
        max_replication_slots: 10

  initdb:
    - encoding: UTF8
    - data-checksums

postgresql:
  listen: 0.0.0.0:5432
  connect_address: node1.example.com:5432
  data_dir: /var/lib/postgresql/15/main
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: repl_password
    superuser:
      username: postgres
      password: postgres_password

tags:
  nofailover: false
  noloadbalance: false
  clonefrom: false
```

```bash
# Start Patroni
patroni /etc/patroni/patroni.yml

# Check cluster status
patronictl -c /etc/patroni/patroni.yml list

# Manual failover
patronictl -c /etc/patroni/patroni.yml switchover
```

### With pg_auto_failover

```bash
# Initialize monitor node
pg_autoctl create monitor \
  --pgdata /var/lib/pgsql/monitor \
  --pgport 5000 \
  --hostname monitor.example.com

# Initialize primary
pg_autoctl create postgres \
  --pgdata /var/lib/pgsql/primary \
  --pgport 5432 \
  --hostname primary.example.com \
  --monitor postgres://monitor.example.com:5000/pg_auto_failover

# Initialize secondary
pg_autoctl create postgres \
  --pgdata /var/lib/pgsql/secondary \
  --pgport 5432 \
  --hostname secondary.example.com \
  --monitor postgres://monitor.example.com:5000/pg_auto_failover

# Check status
pg_autoctl show state
```

## Read Replica Load Balancing

### Application-Level Routing

```typescript
// TypeScript example with read/write splitting
import { Pool } from 'pg';

const primaryPool = new Pool({
  host: 'primary.example.com',
  database: 'mydb',
  max: 20,
});

const replicaPool = new Pool({
  host: 'replica.example.com',
  database: 'mydb',
  max: 50,  // More connections for reads
});

class DatabaseRouter {
  async query(sql: string, params?: any[]) {
    // Route based on query type
    if (this.isReadOnlyQuery(sql)) {
      return replicaPool.query(sql, params);
    }
    return primaryPool.query(sql, params);
  }

  private isReadOnlyQuery(sql: string): boolean {
    const normalized = sql.trim().toUpperCase();
    return normalized.startsWith('SELECT') &&
           !normalized.includes('FOR UPDATE') &&
           !normalized.includes('FOR SHARE');
  }

  // Explicit methods for clarity
  async read(sql: string, params?: any[]) {
    return replicaPool.query(sql, params);
  }

  async write(sql: string, params?: any[]) {
    return primaryPool.query(sql, params);
  }
}
```

### HAProxy Configuration

```
# haproxy.cfg
global
    maxconn 1000

defaults
    mode tcp
    timeout connect 10s
    timeout client 30s
    timeout server 30s

# Write traffic to primary
frontend pg_write
    bind *:5432
    default_backend pg_primary

backend pg_primary
    option httpchk GET /primary
    http-check expect status 200
    server primary primary.example.com:5432 check port 8008

# Read traffic to replicas
frontend pg_read
    bind *:5433
    default_backend pg_replicas

backend pg_replicas
    balance roundrobin
    option httpchk GET /replica
    http-check expect status 200
    server replica1 replica1.example.com:5432 check port 8008
    server replica2 replica2.example.com:5432 check port 8008
```

### PgBouncer with Multiple Pools

```ini
# pgbouncer.ini
[databases]
# Write pool - connects to primary
mydb_write = host=primary.example.com port=5432 dbname=mydb

# Read pool - connects to replicas via HAProxy
mydb_read = host=haproxy.example.com port=5433 dbname=mydb

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
```

## Monitoring Replication

### Replication Lag Monitoring

```sql
-- On primary: Check all replicas
SELECT
  client_addr,
  application_name,
  state,
  sync_state,
  pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) as lag_bytes,
  pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) / 1024 / 1024 as lag_mb
FROM pg_stat_replication;

-- On replica: Check local lag
SELECT
  CASE
    WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() THEN 0
    ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
  END AS lag_seconds;

-- Detailed replication info
SELECT
  slot_name,
  plugin,
  slot_type,
  database,
  active,
  pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) as retained_bytes
FROM pg_replication_slots;
```

### Alerting Script

```bash
#!/bin/bash
# check_replication_lag.sh

MAX_LAG_SECONDS=60
MAX_LAG_BYTES=$((100 * 1024 * 1024))  # 100MB

# Check lag on replica
LAG_SECONDS=$(psql -t -c "
  SELECT COALESCE(
    EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())::int,
    0
  );
")

if [ "$LAG_SECONDS" -gt "$MAX_LAG_SECONDS" ]; then
    echo "CRITICAL: Replication lag is ${LAG_SECONDS} seconds"
    # Send alert
    exit 2
fi

echo "OK: Replication lag is ${LAG_SECONDS} seconds"
exit 0
```

## Failover Procedures

### Manual Failover

```sql
-- On new primary (former replica):

-- 1. Promote replica to primary
SELECT pg_promote();

-- Or via command line:
-- pg_ctl promote -D /var/lib/postgresql/15/main

-- 2. Verify promotion
SELECT pg_is_in_recovery();  -- Should return 'f'

-- 3. Update application connection strings

-- 4. Optionally rebuild old primary as replica
```

### Preventing Split-Brain

```sql
-- postgresql.conf settings for synchronous replication
synchronous_commit = remote_apply  -- Strongest guarantee
synchronous_standby_names = 'FIRST 1 (replica1, replica2)'

-- With multiple sync replicas (quorum)
synchronous_standby_names = 'ANY 2 (replica1, replica2, replica3)'
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Replication Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Monitor Replication Lag                                     │
│     - Alert on high lag                                         │
│     - Track lag trends                                          │
│                                                                  │
│  2. Use Replication Slots                                       │
│     - Prevent WAL deletion before replay                        │
│     - Monitor slot lag to prevent disk fill                     │
│                                                                  │
│  3. Test Failover Regularly                                     │
│     - Scheduled failover tests                                  │
│     - Document procedure                                        │
│                                                                  │
│  4. Use Connection Pooling                                      │
│     - PgBouncer or similar                                      │
│     - Separate pools for primary/replicas                       │
│                                                                  │
│  5. Consider Synchronous for Critical Data                      │
│     - Higher latency but zero data loss                         │
│     - Use quorum for availability                               │
│                                                                  │
│  6. Separate Read/Write Traffic                                 │
│     - Scale reads with replicas                                 │
│     - Be aware of replication lag for reads                     │
│                                                                  │
│  7. Use HA Solution                                             │
│     - Patroni, pg_auto_failover, or similar                     │
│     - Automated failover reduces downtime                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Replication Comparison

| Feature | Streaming | Logical |
|---------|-----------|---------|
| Overhead | Low | Medium |
| Granularity | Full database | Tables |
| Cross-version | No | Yes |
| Different schema | No | Yes |
| Failover | Yes | Manual |
| Read scaling | Yes | Yes |
| Setup complexity | Low | Medium |
