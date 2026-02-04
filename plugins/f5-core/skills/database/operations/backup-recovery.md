---
name: backup-recovery
description: Database backup strategies and recovery procedures
category: database/operations
applies_to: [postgresql, mysql, sql-server]
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Backup and Recovery

## Overview

A robust backup strategy protects against data loss from hardware failures,
software bugs, human errors, and security incidents. Recovery procedures
must be regularly tested to ensure they work when needed.

## Backup Types

```
┌─────────────────────────────────────────────────────────────────┐
│                     Backup Types Overview                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Full Backup                                                     │
│  ├── Complete copy of entire database                           │
│  ├── Largest size, longest time                                 │
│  └── Independent restore (no other backups needed)              │
│                                                                  │
│  Incremental Backup                                              │
│  ├── Only changes since last backup (any type)                  │
│  ├── Smallest size, fastest backup                              │
│  └── Requires full + all incrementals to restore                │
│                                                                  │
│  Differential Backup                                             │
│  ├── Changes since last full backup                             │
│  ├── Medium size, grows over time                               │
│  └── Requires only full + latest differential                   │
│                                                                  │
│  Continuous/WAL Archiving                                        │
│  ├── Transaction log shipping                                   │
│  ├── Point-in-time recovery possible                            │
│  └── Minimal data loss (seconds to minutes)                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## PostgreSQL Backup Methods

### pg_dump (Logical Backup)

```bash
# Full database dump (custom format - recommended)
pg_dump -Fc -Z 9 -f backup.dump mydb

# Full database dump (plain SQL)
pg_dump -f backup.sql mydb

# Schema only
pg_dump --schema-only -f schema.sql mydb

# Data only
pg_dump --data-only -f data.sql mydb

# Specific tables
pg_dump -t users -t orders -f subset.dump mydb

# Exclude tables
pg_dump --exclude-table=logs --exclude-table=audit -f backup.dump mydb

# With compression
pg_dump mydb | gzip > backup.sql.gz

# Parallel dump (multiple jobs)
pg_dump -Fd -j 4 -f backup_dir mydb
```

### pg_dumpall (All Databases)

```bash
# All databases including roles
pg_dumpall -f all_databases.sql

# Globals only (roles, tablespaces)
pg_dumpall --globals-only -f globals.sql

# Roles only
pg_dumpall --roles-only -f roles.sql
```

### pg_basebackup (Physical Backup)

```bash
# Full physical backup
pg_basebackup -D /backup/base -Ft -z -P

# With WAL streaming
pg_basebackup -D /backup/base -Ft -z -P -X stream

# To a different host
pg_basebackup -h primary.example.com -D /backup/base -Ft -z -P -X stream

# With slot (prevents WAL deletion)
pg_basebackup -D /backup/base -S backup_slot -X stream
```

### WAL Archiving (Continuous)

```bash
# postgresql.conf
archive_mode = on
archive_command = 'cp %p /archive/wal/%f'
# Or with compression:
archive_command = 'gzip < %p > /archive/wal/%f.gz'

# Create replication slot for backup
SELECT pg_create_physical_replication_slot('backup_slot');

# Archive to S3
archive_command = 'aws s3 cp %p s3://mybucket/wal/%f'
```

## Automated Backup Script

```bash
#!/bin/bash
# backup_postgres.sh - Automated PostgreSQL backup

set -euo pipefail

# Configuration
DB_NAME="${DB_NAME:-mydb}"
BACKUP_DIR="${BACKUP_DIR:-/backup/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
S3_BUCKET="${S3_BUCKET:-}"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# Create backup
echo "Starting backup of ${DB_NAME}..."
pg_dump -Fc -Z 9 -f "${BACKUP_FILE}" "${DB_NAME}"

# Verify backup
if pg_restore -l "${BACKUP_FILE}" > /dev/null 2>&1; then
    echo "Backup verified successfully"
    BACKUP_SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "Backup size: ${BACKUP_SIZE}"
else
    echo "ERROR: Backup verification failed"
    rm -f "${BACKUP_FILE}"
    exit 1
fi

# Upload to S3 if configured
if [[ -n "${S3_BUCKET}" ]]; then
    echo "Uploading to S3..."
    aws s3 cp "${BACKUP_FILE}" "s3://${S3_BUCKET}/postgres/${DB_NAME}/"
fi

# Cleanup old backups
echo "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_DIR}" -name "${DB_NAME}_*.dump" -mtime +${RETENTION_DAYS} -delete

# Log completion
echo "Backup completed: ${BACKUP_FILE}"

# Send notification (optional)
# curl -X POST -d "PostgreSQL backup completed: ${BACKUP_FILE}" $WEBHOOK_URL
```

### Cron Schedule

```bash
# Daily backup at 2 AM
0 2 * * * /scripts/backup_postgres.sh >> /var/log/backup.log 2>&1

# Hourly WAL backup
0 * * * * /scripts/archive_wal.sh >> /var/log/wal_archive.log 2>&1

# Weekly full backup (Sunday 1 AM)
0 1 * * 0 /scripts/full_backup.sh >> /var/log/full_backup.log 2>&1
```

## Recovery Procedures

### Restore from pg_dump

```bash
# Restore custom format (recommended)
pg_restore -d mydb backup.dump

# Create database and restore
pg_restore -C -d postgres backup.dump

# Restore specific tables
pg_restore -t users -t orders -d mydb backup.dump

# Schema only
pg_restore --schema-only -d mydb backup.dump

# Data only (table must exist)
pg_restore --data-only -d mydb backup.dump

# Restore with parallelism
pg_restore -j 4 -d mydb backup.dump

# Restore plain SQL
psql -d mydb -f backup.sql

# With verbose output
pg_restore -v -d mydb backup.dump 2>&1 | tee restore.log
```

### Point-in-Time Recovery (PITR)

```bash
# 1. Stop PostgreSQL
sudo systemctl stop postgresql

# 2. Clear data directory
rm -rf /var/lib/postgresql/15/main/*

# 3. Restore base backup
tar -xzf /backup/base/base.tar.gz -C /var/lib/postgresql/15/main/
tar -xzf /backup/base/pg_wal.tar.gz -C /var/lib/postgresql/15/main/pg_wal/

# 4. Create recovery signal and configure recovery
touch /var/lib/postgresql/15/main/recovery.signal

# 5. Configure postgresql.conf for recovery
cat >> /var/lib/postgresql/15/main/postgresql.conf << EOF
restore_command = 'cp /archive/wal/%f %p'
recovery_target_time = '2024-01-15 14:30:00'
recovery_target_action = 'promote'
EOF

# 6. Start PostgreSQL
sudo systemctl start postgresql

# 7. Check recovery status
psql -c "SELECT pg_is_in_recovery();"
# Returns 't' during recovery, 'f' when complete
```

### Recovery Configuration Options

```sql
-- postgresql.conf recovery options

-- Restore command (required for PITR)
restore_command = 'cp /archive/wal/%f %p'

-- Recovery targets (use ONE of these)
recovery_target_time = '2024-01-15 14:30:00 UTC'
recovery_target_xid = '1234567'
recovery_target_name = 'before_migration'
recovery_target_lsn = '0/1234567'
recovery_target = 'immediate'  -- First consistent point

-- What to do after reaching target
recovery_target_action = 'pause'    -- Pause for inspection
recovery_target_action = 'promote'  -- Become primary
recovery_target_action = 'shutdown' -- Shutdown cleanly

-- Timeline selection
recovery_target_timeline = 'latest'

-- Create named recovery point
SELECT pg_create_restore_point('before_migration');
```

## Disaster Recovery

### RPO and RTO

```
┌─────────────────────────────────────────────────────────────────┐
│                    Recovery Objectives                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  RPO (Recovery Point Objective)                                 │
│  ├── How much data loss is acceptable?                          │
│  ├── Daily backups: RPO = 24 hours                              │
│  ├── Hourly backups: RPO = 1 hour                               │
│  └── Continuous WAL: RPO = seconds                              │
│                                                                  │
│  RTO (Recovery Time Objective)                                  │
│  ├── How quickly must we recover?                               │
│  ├── Cold standby: RTO = hours                                  │
│  ├── Warm standby: RTO = minutes                                │
│  └── Hot standby: RTO = seconds                                 │
│                                                                  │
│  Example Requirements:                                           │
│  ├── E-commerce: RPO < 5 min, RTO < 15 min                     │
│  ├── Banking: RPO = 0, RTO < 1 min                             │
│  └── Blog: RPO < 24h, RTO < 4h                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Disaster Recovery Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│              Disaster Recovery Checklist                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Before Disaster:                                                │
│  □ Document backup procedures                                   │
│  □ Test restore procedures monthly                              │
│  □ Verify backup integrity                                      │
│  □ Store backups offsite/different region                       │
│  □ Document connection strings and credentials                  │
│  □ Maintain runbook for recovery                                │
│                                                                  │
│  During Recovery:                                                │
│  □ Assess the situation and scope                               │
│  □ Notify stakeholders                                          │
│  □ Choose recovery strategy based on RTO/RPO                    │
│  □ Execute recovery procedure                                   │
│  □ Verify data integrity                                        │
│  □ Test application connectivity                                │
│                                                                  │
│  After Recovery:                                                 │
│  □ Document what happened                                       │
│  □ Conduct post-mortem                                          │
│  □ Update procedures if needed                                  │
│  □ Resume normal backup schedule                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Backup Verification

```bash
#!/bin/bash
# verify_backup.sh - Test backup restoration

set -euo pipefail

BACKUP_FILE=$1
TEST_DB="backup_test_$(date +%s)"

echo "Creating test database..."
createdb "${TEST_DB}"

echo "Restoring backup..."
pg_restore -d "${TEST_DB}" "${BACKUP_FILE}"

echo "Running verification queries..."
psql -d "${TEST_DB}" << 'EOF'
-- Check table counts
SELECT
  schemaname,
  tablename,
  n_live_tup as row_count
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- Verify critical tables exist
SELECT EXISTS (SELECT 1 FROM users LIMIT 1) as users_exist;
SELECT EXISTS (SELECT 1 FROM orders LIMIT 1) as orders_exist;

-- Check data integrity
SELECT COUNT(*) as orphan_orders
FROM orders o
LEFT JOIN users u ON o.user_id = u.id
WHERE u.id IS NULL;
EOF

echo "Cleaning up test database..."
dropdb "${TEST_DB}"

echo "Backup verification complete!"
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                 Backup Best Practices                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Follow 3-2-1 Rule                                           │
│     - 3 copies of data                                          │
│     - 2 different storage types                                 │
│     - 1 offsite location                                        │
│                                                                  │
│  2. Automate Everything                                         │
│     - Scheduled backups                                         │
│     - Automated verification                                    │
│     - Alerting on failures                                      │
│                                                                  │
│  3. Test Restores Regularly                                     │
│     - Monthly restore tests                                     │
│     - Time the restore process                                  │
│     - Document any issues                                       │
│                                                                  │
│  4. Monitor Backup Health                                       │
│     - Backup completion                                         │
│     - Backup size trends                                        │
│     - WAL archiving status                                      │
│                                                                  │
│  5. Secure Your Backups                                         │
│     - Encrypt at rest                                           │
│     - Encrypt in transit                                        │
│     - Control access                                            │
│                                                                  │
│  6. Document Everything                                         │
│     - Backup schedule                                           │
│     - Restore procedures                                        │
│     - Contact information                                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Backup Strategy Matrix

| Strategy | RPO | RTO | Cost | Complexity |
|----------|-----|-----|------|------------|
| Daily pg_dump | 24h | Hours | Low | Low |
| Daily + hourly diff | 1h | Hours | Low | Medium |
| WAL archiving | Minutes | 30min | Medium | Medium |
| Streaming replication | Seconds | Minutes | High | High |
| Multi-region replication | Seconds | Minutes | Very High | Very High |
