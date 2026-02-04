---
name: monitoring
description: Database monitoring, alerting, and health checks
category: database/operations
applies_to: [postgresql, mysql]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Database Monitoring

## Overview

Effective database monitoring helps identify performance issues, prevent
outages, and optimize resource usage. This guide covers key metrics,
monitoring tools, and alerting strategies.

## Key Metrics

```
┌─────────────────────────────────────────────────────────────────┐
│                    Essential Database Metrics                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Performance Metrics                                             │
│  ├── Query latency (p50, p95, p99)                             │
│  ├── Queries per second (QPS)                                   │
│  ├── Active connections                                         │
│  └── Transaction rate                                           │
│                                                                  │
│  Resource Metrics                                                │
│  ├── CPU utilization                                            │
│  ├── Memory usage (buffer cache hit ratio)                      │
│  ├── Disk I/O (reads, writes, IOPS)                            │
│  └── Disk space usage                                           │
│                                                                  │
│  Availability Metrics                                            │
│  ├── Uptime                                                     │
│  ├── Replication lag                                            │
│  ├── Connection errors                                          │
│  └── Failed queries                                             │
│                                                                  │
│  Efficiency Metrics                                              │
│  ├── Index usage rate                                           │
│  ├── Cache hit ratio                                            │
│  ├── Dead tuples (bloat)                                        │
│  └── Lock contention                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## PostgreSQL Monitoring Queries

### Connection Monitoring

```sql
-- Current connection status
SELECT
  state,
  COUNT(*) as count,
  MAX(EXTRACT(EPOCH FROM (now() - state_change)))::int as max_duration_sec
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY state;

-- Connections by application
SELECT
  application_name,
  COUNT(*) as connections,
  SUM(CASE WHEN state = 'active' THEN 1 ELSE 0 END) as active,
  SUM(CASE WHEN state = 'idle' THEN 1 ELSE 0 END) as idle,
  SUM(CASE WHEN state = 'idle in transaction' THEN 1 ELSE 0 END) as idle_in_txn
FROM pg_stat_activity
WHERE datname = current_database()
GROUP BY application_name
ORDER BY connections DESC;

-- Connection limit status
SELECT
  max_conn,
  used_conn,
  reserved_conn,
  max_conn - used_conn - reserved_conn as available
FROM (
  SELECT
    setting::int as max_conn
  FROM pg_settings
  WHERE name = 'max_connections'
) max_conn,
(
  SELECT
    COUNT(*) as used_conn
  FROM pg_stat_activity
) used_conn,
(
  SELECT
    setting::int as reserved_conn
  FROM pg_settings
  WHERE name = 'superuser_reserved_connections'
) reserved_conn;
```

### Performance Monitoring

```sql
-- Database statistics
SELECT
  datname,
  numbackends as connections,
  xact_commit as commits,
  xact_rollback as rollbacks,
  blks_read,
  blks_hit,
  ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2) as cache_hit_pct,
  tup_returned,
  tup_fetched,
  tup_inserted,
  tup_updated,
  tup_deleted
FROM pg_stat_database
WHERE datname = current_database();

-- Table I/O statistics
SELECT
  schemaname,
  relname as table_name,
  seq_scan,
  seq_tup_read,
  idx_scan,
  idx_tup_fetch,
  n_tup_ins as inserts,
  n_tup_upd as updates,
  n_tup_del as deletes,
  n_live_tup as live_rows,
  n_dead_tup as dead_rows,
  ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct,
  last_vacuum,
  last_autovacuum,
  last_analyze,
  last_autoanalyze
FROM pg_stat_user_tables
ORDER BY n_dead_tup DESC
LIMIT 20;

-- Index efficiency
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan as scans,
  idx_tup_read as tuples_read,
  idx_tup_fetch as tuples_fetched,
  pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC
LIMIT 20;
```

### Query Performance

```sql
-- Slowest queries (requires pg_stat_statements)
SELECT
  LEFT(query, 80) as query_preview,
  calls,
  ROUND(total_exec_time::numeric, 2) as total_ms,
  ROUND(mean_exec_time::numeric, 2) as avg_ms,
  ROUND(stddev_exec_time::numeric, 2) as stddev_ms,
  rows,
  ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2) as cache_hit_pct
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;

-- Currently running queries
SELECT
  pid,
  age(clock_timestamp(), query_start) as duration,
  state,
  query
FROM pg_stat_activity
WHERE state != 'idle'
  AND query NOT LIKE '%pg_stat_activity%'
ORDER BY duration DESC;

-- Blocked queries
SELECT
  blocked.pid as blocked_pid,
  blocked.query as blocked_query,
  blocking.pid as blocking_pid,
  blocking.query as blocking_query
FROM pg_stat_activity blocked
JOIN pg_stat_activity blocking ON blocking.pid = ANY(pg_blocking_pids(blocked.pid))
WHERE cardinality(pg_blocking_pids(blocked.pid)) > 0;
```

### Lock Monitoring

```sql
-- Current locks
SELECT
  locktype,
  relation::regclass,
  mode,
  granted,
  pid,
  (SELECT query FROM pg_stat_activity WHERE pid = l.pid) as query
FROM pg_locks l
WHERE relation IS NOT NULL
ORDER BY relation;

-- Lock waits
SELECT
  l.pid,
  l.mode,
  l.locktype,
  l.relation::regclass,
  a.query,
  age(clock_timestamp(), a.query_start) as duration
FROM pg_locks l
JOIN pg_stat_activity a ON l.pid = a.pid
WHERE NOT l.granted
ORDER BY duration DESC;
```

### Replication Monitoring

```sql
-- Replication status (on primary)
SELECT
  client_addr,
  application_name,
  state,
  sync_state,
  sent_lsn,
  write_lsn,
  flush_lsn,
  replay_lsn,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) as lag_bytes,
  pg_wal_lsn_diff(sent_lsn, replay_lsn) / 1024 / 1024 as lag_mb
FROM pg_stat_replication;

-- Replication slot status
SELECT
  slot_name,
  slot_type,
  database,
  active,
  pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn) / 1024 / 1024 as retained_mb
FROM pg_replication_slots;

-- Lag on replica
SELECT
  CASE
    WHEN pg_last_wal_receive_lsn() = pg_last_wal_replay_lsn() THEN 0
    ELSE EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp())
  END AS lag_seconds;
```

## Prometheus Metrics

### PostgreSQL Exporter Setup

```yaml
# docker-compose.yml
services:
  postgres-exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://user:pass@postgres:5432/mydb?sslmode=disable"
    ports:
      - "9187:9187"
```

### Custom Metrics Query

```yaml
# queries.yaml for postgres_exporter
pg_database:
  query: |
    SELECT
      datname,
      numbackends,
      xact_commit,
      xact_rollback,
      blks_read,
      blks_hit
    FROM pg_stat_database
    WHERE datname NOT IN ('template0', 'template1')
  metrics:
    - datname:
        usage: "LABEL"
        description: "Database name"
    - numbackends:
        usage: "GAUGE"
        description: "Number of backends"
    - xact_commit:
        usage: "COUNTER"
        description: "Transactions committed"
    - xact_rollback:
        usage: "COUNTER"
        description: "Transactions rolled back"
    - blks_read:
        usage: "COUNTER"
        description: "Blocks read from disk"
    - blks_hit:
        usage: "COUNTER"
        description: "Blocks hit in cache"

pg_replication_lag:
  query: |
    SELECT
      COALESCE(
        EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp()),
        0
      ) as lag_seconds
  metrics:
    - lag_seconds:
        usage: "GAUGE"
        description: "Replication lag in seconds"
```

### Grafana Dashboard Queries

```promql
# Connection usage percentage
100 * pg_stat_activity_count / pg_settings_max_connections

# Cache hit ratio
100 * rate(pg_stat_database_blks_hit[5m]) /
(rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m]))

# Transactions per second
rate(pg_stat_database_xact_commit[1m]) + rate(pg_stat_database_xact_rollback[1m])

# Replication lag
pg_replication_lag_seconds

# Dead tuple percentage
100 * pg_stat_user_tables_n_dead_tup /
(pg_stat_user_tables_n_live_tup + pg_stat_user_tables_n_dead_tup)

# Disk space usage
pg_database_size_bytes

# Query duration (95th percentile)
histogram_quantile(0.95, rate(pg_stat_statements_seconds_bucket[5m]))
```

## Alerting Rules

### Prometheus Alert Rules

```yaml
# alerts.yml
groups:
  - name: postgres
    rules:
      - alert: PostgresDown
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PostgreSQL is down"
          description: "PostgreSQL instance {{ $labels.instance }} is down"

      - alert: HighConnectionUsage
        expr: |
          100 * pg_stat_activity_count / pg_settings_max_connections > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High connection usage"
          description: "Connection usage is {{ $value }}%"

      - alert: LowCacheHitRatio
        expr: |
          100 * rate(pg_stat_database_blks_hit[5m]) /
          (rate(pg_stat_database_blks_hit[5m]) + rate(pg_stat_database_blks_read[5m])) < 95
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "Low cache hit ratio"
          description: "Cache hit ratio is {{ $value }}%"

      - alert: HighReplicationLag
        expr: pg_replication_lag_seconds > 30
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High replication lag"
          description: "Replication lag is {{ $value }} seconds"

      - alert: CriticalReplicationLag
        expr: pg_replication_lag_seconds > 300
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Critical replication lag"
          description: "Replication lag is {{ $value }} seconds"

      - alert: HighDeadTuples
        expr: |
          100 * pg_stat_user_tables_n_dead_tup /
          (pg_stat_user_tables_n_live_tup + pg_stat_user_tables_n_dead_tup) > 10
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "High dead tuple percentage"
          description: "Table {{ $labels.relname }} has {{ $value }}% dead tuples"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/var/lib/postgresql"} /
           node_filesystem_size_bytes{mountpoint="/var/lib/postgresql"}) * 100 < 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Low disk space"
          description: "Only {{ $value }}% disk space remaining"

      - alert: SlowQueries
        expr: |
          rate(pg_stat_statements_seconds_sum[5m]) /
          rate(pg_stat_statements_calls[5m]) > 1
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Slow average query time"
          description: "Average query time is {{ $value }} seconds"

      - alert: HighRollbackRate
        expr: |
          100 * rate(pg_stat_database_xact_rollback[5m]) /
          (rate(pg_stat_database_xact_commit[5m]) + rate(pg_stat_database_xact_rollback[5m])) > 5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High rollback rate"
          description: "Rollback rate is {{ $value }}%"
```

## Health Check Script

```bash
#!/bin/bash
# db_health_check.sh

set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-mydb}"
DB_USER="${DB_USER:-postgres}"

# Check connection
check_connection() {
    if pg_isready -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" > /dev/null 2>&1; then
        echo "✓ Connection: OK"
        return 0
    else
        echo "✗ Connection: FAILED"
        return 1
    fi
}

# Check replication lag
check_replication() {
    lag=$(psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -t -c "
        SELECT COALESCE(
            EXTRACT(EPOCH FROM now() - pg_last_xact_replay_timestamp()),
            0
        )::int;
    " 2>/dev/null || echo "N/A")

    if [[ "$lag" == "N/A" ]]; then
        echo "✓ Replication: Primary or not configured"
    elif [[ "$lag" -lt 30 ]]; then
        echo "✓ Replication lag: ${lag}s"
    elif [[ "$lag" -lt 300 ]]; then
        echo "⚠ Replication lag: ${lag}s (warning)"
    else
        echo "✗ Replication lag: ${lag}s (critical)"
        return 1
    fi
}

# Check connections
check_connections() {
    result=$(psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -t -c "
        SELECT
            COUNT(*) as used,
            setting::int as max
        FROM pg_stat_activity, pg_settings
        WHERE name = 'max_connections'
        GROUP BY setting;
    " 2>/dev/null)

    used=$(echo "$result" | awk '{print $1}')
    max=$(echo "$result" | awk '{print $3}')
    pct=$((100 * used / max))

    if [[ "$pct" -lt 80 ]]; then
        echo "✓ Connections: ${used}/${max} (${pct}%)"
    elif [[ "$pct" -lt 95 ]]; then
        echo "⚠ Connections: ${used}/${max} (${pct}%) (warning)"
    else
        echo "✗ Connections: ${used}/${max} (${pct}%) (critical)"
        return 1
    fi
}

# Check cache hit ratio
check_cache() {
    ratio=$(psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -t -c "
        SELECT ROUND(100.0 * blks_hit / NULLIF(blks_hit + blks_read, 0), 2)
        FROM pg_stat_database
        WHERE datname = current_database();
    " 2>/dev/null | xargs)

    if [[ -z "$ratio" ]] || [[ "$ratio" == "" ]]; then
        echo "✓ Cache hit ratio: N/A (no reads yet)"
    elif (( $(echo "$ratio > 95" | bc -l) )); then
        echo "✓ Cache hit ratio: ${ratio}%"
    elif (( $(echo "$ratio > 90" | bc -l) )); then
        echo "⚠ Cache hit ratio: ${ratio}% (warning)"
    else
        echo "✗ Cache hit ratio: ${ratio}% (critical)"
        return 1
    fi
}

# Check disk space
check_disk() {
    size=$(psql -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -U "$DB_USER" -t -c "
        SELECT pg_size_pretty(pg_database_size(current_database()));
    " 2>/dev/null | xargs)

    echo "ℹ Database size: ${size}"
}

# Run all checks
echo "=== PostgreSQL Health Check ==="
echo "Host: $DB_HOST:$DB_PORT"
echo "Database: $DB_NAME"
echo ""

failed=0

check_connection || failed=1
check_replication || failed=1
check_connections || failed=1
check_cache || failed=1
check_disk

echo ""
if [[ $failed -eq 0 ]]; then
    echo "Overall status: HEALTHY"
    exit 0
else
    echo "Overall status: UNHEALTHY"
    exit 1
fi
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│               Monitoring Best Practices                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Monitor What Matters                                        │
│     - Focus on user-impacting metrics                           │
│     - Avoid alert fatigue                                       │
│                                                                  │
│  2. Set Meaningful Thresholds                                   │
│     - Base on historical data                                   │
│     - Adjust over time                                          │
│                                                                  │
│  3. Use Multiple Alert Severities                               │
│     - Warning: Needs attention soon                             │
│     - Critical: Needs immediate action                          │
│                                                                  │
│  4. Include Context in Alerts                                   │
│     - What's wrong                                              │
│     - Current value vs threshold                                │
│     - Link to runbook                                           │
│                                                                  │
│  5. Monitor Trends, Not Just Thresholds                         │
│     - Disk space growth rate                                    │
│     - Query latency trends                                      │
│                                                                  │
│  6. Test Your Monitoring                                        │
│     - Verify alerts fire correctly                              │
│     - Test alert routing                                        │
│                                                                  │
│  7. Document Everything                                         │
│     - What each metric means                                    │
│     - What to do when alert fires                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Alert Thresholds Summary

| Metric | Warning | Critical |
|--------|---------|----------|
| Connection usage | > 80% | > 95% |
| Cache hit ratio | < 95% | < 90% |
| Replication lag | > 30s | > 300s |
| Dead tuples | > 10% | > 20% |
| Disk space | < 20% free | < 10% free |
| Rollback rate | > 5% | > 10% |
| Query latency (p99) | > 1s | > 5s |
