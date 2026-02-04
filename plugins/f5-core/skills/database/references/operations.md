# Database Operations

Replication, backup/recovery, sharding, and monitoring strategies.

## Table of Contents

1. [Replication](#replication)
2. [Backup and Recovery](#backup-and-recovery)
3. [Sharding](#sharding)
4. [Monitoring](#monitoring)
5. [High Availability](#high-availability)

---

## Replication

### Replication Types

```
┌─────────────────────────────────────────────────────────────────┐
│                    Replication Types                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Physical (Streaming) Replication                               │
│  ├── Copies WAL (Write-Ahead Log) records                       │
│  ├── Byte-for-byte copy of database                             │
│  └── Fast, low overhead, same PostgreSQL version                │
│                                                                  │
│  Logical Replication                                             │
│  ├── Copies changes at row level                                │
│  ├── Can replicate specific tables                              │
│  └── Supports different versions/schemas                        │
│                                                                  │
│  Synchronous vs Asynchronous                                    │
│  ├── Sync: Zero data loss, higher latency                       │
│  └── Async: Possible data loss, lower latency                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### PostgreSQL Streaming Replication

```bash
# postgresql.conf on primary
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB
hot_standby = on

# For synchronous replication
synchronous_commit = on
synchronous_standby_names = 'replica1'
```

```sql
-- Create replication user
CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'secure_password';

-- Check replication status
SELECT
  client_addr,
  state,
  sync_state,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes
FROM pg_stat_replication;
```

### Read/Write Splitting

```typescript
import { Pool } from 'pg';

const primaryPool = new Pool({
  host: 'primary.example.com',
  max: 20,
});

const replicaPool = new Pool({
  host: 'replica.example.com',
  max: 50,  // More connections for reads
});

class DatabaseRouter {
  async read(sql: string, params?: any[]) {
    return replicaPool.query(sql, params);
  }

  async write(sql: string, params?: any[]) {
    return primaryPool.query(sql, params);
  }
}
```

---

## Backup and Recovery

### Backup Types

| Type | Description | Use Case |
|------|-------------|----------|
| Full | Complete database copy | Weekly baseline |
| Incremental | Changes since last backup | Daily |
| WAL Archiving | Continuous log shipping | Point-in-time recovery |

### PostgreSQL Backup Commands

```bash
# Logical backup (pg_dump)
pg_dump -Fc -Z 9 -f backup.dump mydb

# Physical backup (pg_basebackup)
pg_basebackup -D /backup/base -Ft -z -P -X stream

# Restore from dump
pg_restore -d mydb backup.dump

# WAL archiving configuration
# postgresql.conf
archive_mode = on
archive_command = 'cp %p /archive/wal/%f'
```

### Automated Backup Script

```bash
#!/bin/bash
set -euo pipefail

DB_NAME="${DB_NAME:-mydb}"
BACKUP_DIR="${BACKUP_DIR:-/backup/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"

mkdir -p "${BACKUP_DIR}"

# Create backup
pg_dump -Fc -Z 9 -f "${BACKUP_FILE}" "${DB_NAME}"

# Verify backup
if pg_restore -l "${BACKUP_FILE}" > /dev/null 2>&1; then
    echo "Backup verified: ${BACKUP_FILE}"
else
    echo "ERROR: Backup verification failed"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# Cleanup old backups
find "${BACKUP_DIR}" -name "${DB_NAME}_*.dump" -mtime +${RETENTION_DAYS} -delete
```

### Point-in-Time Recovery (PITR)

```bash
# 1. Restore base backup
tar -xzf /backup/base/base.tar.gz -C /var/lib/postgresql/15/main/

# 2. Create recovery signal
touch /var/lib/postgresql/15/main/recovery.signal

# 3. Configure recovery
cat >> /var/lib/postgresql/15/main/postgresql.conf << EOF
restore_command = 'cp /archive/wal/%f %p'
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'
EOF

# 4. Start PostgreSQL
sudo systemctl start postgresql
```

### RPO/RTO Planning

| Strategy | RPO | RTO | Cost |
|----------|-----|-----|------|
| Daily pg_dump | 24h | Hours | Low |
| WAL archiving | Minutes | 30min | Medium |
| Streaming replication | Seconds | Minutes | High |

---

## Sharding

### Sharding Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                   Sharding Strategies                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Range-Based Sharding                                            │
│  ├── Data divided by key ranges                                 │
│  ├── Example: users 1-1M on shard1, 1M-2M on shard2             │
│  └── Risk: Hot spots if recent data accessed more               │
│                                                                  │
│  Hash-Based Sharding                                             │
│  ├── Hash function determines shard                             │
│  ├── Example: shard = hash(user_id) % num_shards                │
│  └── Benefit: Even distribution                                 │
│                                                                  │
│  Directory-Based Sharding                                        │
│  ├── Lookup table maps keys to shards                           │
│  └── Most flexible but adds lookup overhead                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### PostgreSQL Table Partitioning

```sql
-- Range partitioning by date
CREATE TABLE orders (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  total DECIMAL(15,2),
  created_at TIMESTAMPTZ NOT NULL
) PARTITION BY RANGE (created_at);

-- Create partitions
CREATE TABLE orders_2024_q1 PARTITION OF orders
  FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders
  FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- Automatic partition creation (pg_partman)
SELECT partman.create_parent(
  'public.orders',
  'created_at',
  'native',
  'monthly'
);
```

### Application-Level Sharding

```typescript
class ShardRouter {
  private shards: Pool[];

  constructor(shardConfigs: ShardConfig[]) {
    this.shards = shardConfigs.map(config => new Pool(config));
  }

  getShardForUser(userId: string): Pool {
    const hash = this.hashUserId(userId);
    const shardIndex = hash % this.shards.length;
    return this.shards[shardIndex];
  }

  private hashUserId(userId: string): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = ((hash << 5) - hash) + userId.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash);
  }

  async queryUser(userId: string, sql: string, params?: any[]) {
    const shard = this.getShardForUser(userId);
    return shard.query(sql, params);
  }
}
```

---

## Monitoring

### Key Metrics

```sql
-- Cache hit ratio (should be > 99%)
SELECT
  ROUND(
    100.0 * SUM(heap_blks_hit) /
    NULLIF(SUM(heap_blks_hit) + SUM(heap_blks_read), 0),
    2
  ) as cache_hit_ratio
FROM pg_statio_user_tables;

-- Active connections
SELECT
  datname,
  state,
  COUNT(*) as connections
FROM pg_stat_activity
GROUP BY datname, state;

-- Table sizes
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname || '.' || tablename)) as total_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname || '.' || tablename) DESC;

-- Replication lag
SELECT
  client_addr,
  pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) / 1024 / 1024 as lag_mb
FROM pg_stat_replication;

-- Dead tuples (need VACUUM)
SELECT
  relname,
  n_dead_tup,
  n_live_tup,
  ROUND(100 * n_dead_tup::numeric / NULLIF(n_live_tup, 0), 2) as dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC;
```

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Cache hit ratio | < 99% | < 95% |
| Replication lag | > 60s | > 300s |
| Connection usage | > 80% | > 95% |
| Disk usage | > 80% | > 90% |
| Dead tuple ratio | > 10% | > 20% |

### Prometheus Metrics (postgres_exporter)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']

# Alert rules
groups:
  - name: postgres
    rules:
      - alert: HighReplicationLag
        expr: pg_replication_lag > 60
        for: 5m
        labels:
          severity: warning

      - alert: LowCacheHitRatio
        expr: pg_stat_database_blks_hit / (pg_stat_database_blks_hit + pg_stat_database_blks_read) < 0.99
        for: 10m
        labels:
          severity: warning
```

---

## High Availability

### HA Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    High Availability Setup                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    HAProxy/PgBouncer    ┌─────────────┐        │
│  │  App Server │───────────────────────▶│   Primary   │        │
│  └─────────────┘         │               └─────────────┘        │
│                          │                     │                 │
│                          │               Streaming               │
│                          │               Replication             │
│                          │                     │                 │
│                          │               ┌─────────────┐        │
│                          └─────────────▶│   Replica   │        │
│                           (reads only)   └─────────────┘        │
│                                                                  │
│  Patroni/pg_auto_failover manages automatic failover            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Patroni Configuration

```yaml
# patroni.yml
scope: postgres-cluster
name: node1

restapi:
  listen: 0.0.0.0:8008

etcd:
  hosts:
    - etcd1.example.com:2379
    - etcd2.example.com:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        wal_level: replica
        hot_standby: on
        max_wal_senders: 10

postgresql:
  listen: 0.0.0.0:5432
  connect_address: node1.example.com:5432
  data_dir: /var/lib/postgresql/15/main
```

### HAProxy Configuration

```
# haproxy.cfg
frontend pg_write
    bind *:5432
    default_backend pg_primary

backend pg_primary
    option httpchk GET /primary
    http-check expect status 200
    server primary primary.example.com:5432 check port 8008

frontend pg_read
    bind *:5433
    default_backend pg_replicas

backend pg_replicas
    balance roundrobin
    option httpchk GET /replica
    server replica1 replica1.example.com:5432 check port 8008
    server replica2 replica2.example.com:5432 check port 8008
```

---

## Operations Checklist

| Area | Check | Status |
|------|-------|--------|
| **Backup** | Daily backups running | ☐ |
| | Backup verification automated | ☐ |
| | PITR tested monthly | ☐ |
| | Offsite backup copies | ☐ |
| **Replication** | Replication lag monitored | ☐ |
| | Failover tested quarterly | ☐ |
| | Read replicas load balanced | ☐ |
| **Monitoring** | Cache hit ratio > 99% | ☐ |
| | Slow query logging enabled | ☐ |
| | Disk space alerts configured | ☐ |
| | Connection pool sized correctly | ☐ |
| **Maintenance** | VACUUM scheduled | ☐ |
| | Index maintenance planned | ☐ |
| | Stats collection enabled | ☐ |
