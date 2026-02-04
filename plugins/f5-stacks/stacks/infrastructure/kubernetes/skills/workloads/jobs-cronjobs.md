---
name: k8s-jobs-cronjobs
description: Kubernetes Jobs and CronJobs for batch workloads
applies_to: kubernetes
---

# Kubernetes Jobs and CronJobs

## Jobs

Jobs create Pods that run to completion. Use for batch processing, one-time tasks, and migrations.

### Basic Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: production
spec:
  template:
    spec:
      containers:
        - name: migration
          image: myapp:1.0.0
          command: ["npm", "run", "migrate"]
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secrets
                  key: url
      restartPolicy: Never
  backoffLimit: 4
```

### Production Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: data-export
  namespace: production
  labels:
    app.kubernetes.io/name: data-export
    app.kubernetes.io/component: batch
spec:
  # Completion settings
  completions: 1           # Number of successful completions
  parallelism: 1           # Number of parallel pods
  backoffLimit: 3          # Retries before marking failed
  activeDeadlineSeconds: 3600  # Max time (1 hour)
  ttlSecondsAfterFinished: 86400  # Cleanup after 24 hours

  template:
    metadata:
      labels:
        app.kubernetes.io/name: data-export
    spec:
      restartPolicy: Never

      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000

      serviceAccountName: data-export

      containers:
        - name: export
          image: myregistry/data-export:1.0.0

          command:
            - /bin/sh
            - -c
            - |
              echo "Starting export..."
              python export.py --output /data/export.csv
              echo "Export complete"

          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secrets
                  key: url
            - name: S3_BUCKET
              value: "my-exports"

          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"

          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true

          volumeMounts:
            - name: data
              mountPath: /data
            - name: tmp
              mountPath: /tmp

      volumes:
        - name: data
          emptyDir:
            sizeLimit: 10Gi
        - name: tmp
          emptyDir: {}
```

### Parallel Job

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: parallel-processor
spec:
  completions: 10    # Total work items
  parallelism: 3     # Run 3 pods at a time

  template:
    spec:
      containers:
        - name: processor
          image: myprocessor:1.0.0
          env:
            - name: JOB_COMPLETION_INDEX
              valueFrom:
                fieldRef:
                  fieldPath: metadata.annotations['batch.kubernetes.io/job-completion-index']
      restartPolicy: Never
```

### Indexed Job (Work Queue)

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: indexed-job
spec:
  completions: 5
  parallelism: 5
  completionMode: Indexed  # Each pod gets unique index

  template:
    spec:
      containers:
        - name: worker
          image: worker:1.0.0
          command:
            - process-work
            - --index=$(JOB_COMPLETION_INDEX)
          env:
            - name: JOB_COMPLETION_INDEX
              valueFrom:
                fieldRef:
                  fieldPath: metadata.annotations['batch.kubernetes.io/job-completion-index']
      restartPolicy: Never
```

## CronJobs

CronJobs create Jobs on a schedule.

### Basic CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
  namespace: production
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: backup-tool:1.0.0
              command: ["/bin/sh", "-c", "backup.sh"]
          restartPolicy: OnFailure
```

### Production CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: db-backup
  namespace: production
  labels:
    app.kubernetes.io/name: db-backup
    app.kubernetes.io/component: backup
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  timeZone: "America/New_York"

  # Concurrency policy
  concurrencyPolicy: Forbid  # Allow, Forbid, Replace

  # Scheduling settings
  startingDeadlineSeconds: 300  # Must start within 5 minutes

  # History
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 3

  # Suspend
  suspend: false

  jobTemplate:
    metadata:
      labels:
        app.kubernetes.io/name: db-backup
    spec:
      activeDeadlineSeconds: 7200  # 2 hours max
      backoffLimit: 2
      ttlSecondsAfterFinished: 86400

      template:
        metadata:
          labels:
            app.kubernetes.io/name: db-backup
        spec:
          restartPolicy: OnFailure

          securityContext:
            runAsNonRoot: true
            runAsUser: 1000

          serviceAccountName: db-backup

          containers:
            - name: backup
              image: myregistry/db-backup:1.0.0

              command:
                - /bin/sh
                - -c
                - |
                  set -e
                  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                  pg_dump $DATABASE_URL | gzip > /backup/db_$TIMESTAMP.sql.gz
                  aws s3 cp /backup/db_$TIMESTAMP.sql.gz s3://$S3_BUCKET/backups/
                  echo "Backup completed: db_$TIMESTAMP.sql.gz"

              env:
                - name: DATABASE_URL
                  valueFrom:
                    secretKeyRef:
                      name: db-secrets
                      key: url
                - name: S3_BUCKET
                  value: "my-backups"
                - name: AWS_ACCESS_KEY_ID
                  valueFrom:
                    secretKeyRef:
                      name: aws-credentials
                      key: access-key
                - name: AWS_SECRET_ACCESS_KEY
                  valueFrom:
                    secretKeyRef:
                      name: aws-credentials
                      key: secret-key

              resources:
                requests:
                  cpu: "500m"
                  memory: "512Mi"
                limits:
                  cpu: "1000m"
                  memory: "2Gi"

              volumeMounts:
                - name: backup
                  mountPath: /backup

          volumes:
            - name: backup
              emptyDir:
                sizeLimit: 5Gi
```

## Cron Schedule Syntax

```
# ┌───────────── minute (0 - 59)
# │ ┌───────────── hour (0 - 23)
# │ │ ┌───────────── day of the month (1 - 31)
# │ │ │ ┌───────────── month (1 - 12)
# │ │ │ │ ┌───────────── day of the week (0 - 6)
# │ │ │ │ │
# * * * * *

# Examples:
"0 * * * *"      # Every hour
"*/15 * * * *"   # Every 15 minutes
"0 0 * * *"      # Daily at midnight
"0 2 * * *"      # Daily at 2 AM
"0 0 * * 0"      # Weekly on Sunday
"0 0 1 * *"      # Monthly on 1st
"0 0 1 1 *"      # Yearly on Jan 1
"0 9-17 * * 1-5" # Weekdays 9-5
```

## Concurrency Policies

```yaml
spec:
  # Allow - Multiple jobs can run concurrently (default)
  concurrencyPolicy: Allow

  # Forbid - Skip if previous still running
  concurrencyPolicy: Forbid

  # Replace - Cancel previous and start new
  concurrencyPolicy: Replace
```

## Job/CronJob Commands

```bash
# Create Job
kubectl apply -f job.yaml

# List Jobs
kubectl get jobs
kubectl get jobs -o wide

# Watch Job
kubectl get jobs -w

# Describe Job
kubectl describe job db-migration

# Get Job pods
kubectl get pods -l job-name=db-migration

# View logs
kubectl logs job/db-migration

# Delete Job
kubectl delete job db-migration

# Delete completed Jobs
kubectl delete jobs --field-selector status.successful=1

# CronJob commands
kubectl get cronjobs
kubectl describe cronjob backup

# Manually trigger CronJob
kubectl create job --from=cronjob/backup manual-backup

# Suspend CronJob
kubectl patch cronjob backup -p '{"spec":{"suspend":true}}'

# Delete CronJob
kubectl delete cronjob backup
```

## Best Practices

1. **Set activeDeadlineSeconds** - Prevent runaway jobs
2. **Configure backoffLimit** - Control retry behavior
3. **Use ttlSecondsAfterFinished** - Auto cleanup completed jobs
4. **Set resource limits** - Batch jobs can be resource intensive
5. **Use concurrencyPolicy: Forbid** - For jobs that can't overlap
6. **Configure startingDeadlineSeconds** - Handle missed schedules
7. **Monitor failed jobs** - Set up alerting
8. **Use timeZone** - For predictable scheduling
