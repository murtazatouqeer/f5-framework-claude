# Reliability Reference

## SRE Fundamentals

### Service Level Indicators (SLIs)

| SLI | Description | Calculation |
|-----|-------------|-------------|
| Availability | % of successful requests | (successful / total) × 100 |
| Latency | Response time percentile | p50, p95, p99 |
| Throughput | Requests per second | count / time |
| Error Rate | % of failed requests | (errors / total) × 100 |

### Service Level Objectives (SLOs)

```yaml
# SLO definition
service: api
slos:
  - name: availability
    target: 99.9%
    window: 30d

  - name: latency_p99
    target: 200ms
    window: 30d

  - name: error_rate
    target: 0.1%
    window: 30d
```

### Error Budget

```
Error Budget = 1 - SLO Target

For 99.9% availability over 30 days:
- Error budget = 0.1% = 43.2 minutes downtime allowed
- Monthly budget: 30 days × 24 hours × 60 min × 0.001 = 43.2 min
```

## Incident Management

### Severity Levels

| Level | Impact | Response |
|-------|--------|----------|
| P1 | Service down | Immediate (24/7) |
| P2 | Major degradation | < 1 hour |
| P3 | Minor impact | < 4 hours |
| P4 | Low impact | Next business day |

### Incident Response

```markdown
## Incident Template

### Summary
[Brief description of the incident]

### Timeline
- HH:MM - Issue detected
- HH:MM - Investigation started
- HH:MM - Root cause identified
- HH:MM - Fix deployed
- HH:MM - Service restored

### Impact
- Duration: X hours
- Users affected: X
- Revenue impact: $X

### Root Cause
[Technical explanation]

### Resolution
[What fixed the issue]

### Action Items
- [ ] Implement monitoring for X
- [ ] Add circuit breaker to Y
- [ ] Update runbook for Z
```

### On-Call Rotation

```yaml
# PagerDuty schedule example
schedule:
  name: "API On-Call"
  rotation_type: weekly
  users:
    - alice@example.com
    - bob@example.com
    - carol@example.com
  escalation_policy:
    - delay: 5m
      target: primary_on_call
    - delay: 15m
      target: secondary_on_call
    - delay: 30m
      target: engineering_manager
```

## Disaster Recovery

### RPO and RTO

| Metric | Definition | Example |
|--------|------------|---------|
| RPO | Recovery Point Objective (data loss tolerance) | 1 hour |
| RTO | Recovery Time Objective (downtime tolerance) | 4 hours |

### Backup Strategies

```bash
# PostgreSQL backup
pg_dump -h localhost -U postgres -d mydb > backup.sql
pg_dump -Fc -h localhost -U postgres -d mydb > backup.dump

# Restore
pg_restore -h localhost -U postgres -d mydb backup.dump

# Automated S3 backup
#!/bin/bash
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -Fc $DATABASE_URL | aws s3 cp - s3://backups/db/${TIMESTAMP}.dump

# Keep last 30 days
aws s3 ls s3://backups/db/ | while read -r line; do
  createDate=$(echo $line | awk '{print $1}')
  if [[ $(date -d "$createDate" +%s) -lt $(date -d "30 days ago" +%s) ]]; then
    fileName=$(echo $line | awk '{print $4}')
    aws s3 rm s3://backups/db/$fileName
  fi
done
```

### Multi-Region Setup

```yaml
# Kubernetes multi-cluster
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: global-ingress
  annotations:
    kubernetes.io/ingress.global-static-ip-name: "global-ip"
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 80
```

## Chaos Engineering

### Principles

1. Define steady state
2. Hypothesize about impact
3. Introduce real-world events
4. Minimize blast radius
5. Run experiments in production

### Chaos Mesh (Kubernetes)

```yaml
# Pod kill experiment
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: pod-kill-example
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces:
      - production
    labelSelectors:
      app: api
  scheduler:
    cron: "@every 1h"
---
# Network delay experiment
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: network-delay
spec:
  action: delay
  mode: all
  selector:
    namespaces:
      - production
    labelSelectors:
      app: api
  delay:
    latency: "200ms"
    jitter: "50ms"
  duration: "5m"
```

### Litmus Chaos

```yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: api-chaos
spec:
  appinfo:
    appns: production
    applabel: "app=api"
  chaosServiceAccount: litmus-admin
  experiments:
    - name: pod-delete
      spec:
        components:
          env:
            - name: TOTAL_CHAOS_DURATION
              value: "30"
            - name: CHAOS_INTERVAL
              value: "10"
```

## Runbooks

### Service Restart

```markdown
## API Service Restart

### Symptoms
- High error rate
- Memory exhaustion
- Unresponsive health checks

### Steps
1. Check current status
   ```bash
   kubectl get pods -l app=api
   kubectl top pods -l app=api
   ```

2. Capture logs for analysis
   ```bash
   kubectl logs deployment/api --tail=1000 > /tmp/api-logs.txt
   ```

3. Rolling restart
   ```bash
   kubectl rollout restart deployment/api
   kubectl rollout status deployment/api
   ```

4. Verify recovery
   ```bash
   curl -s https://api.example.com/health
   ```

### Escalation
If service doesn't recover within 5 minutes:
- Page secondary on-call
- Consider rollback to previous version
```

### Database Failover

```markdown
## Database Failover Procedure

### When to Use
- Primary database unresponsive
- Replication lag > 1 minute
- Datacenter outage

### Steps
1. Verify primary is unreachable
   ```bash
   psql -h primary.db.com -c "SELECT 1"
   ```

2. Promote replica to primary
   ```bash
   # AWS RDS
   aws rds promote-read-replica --db-instance-identifier replica-1

   # PostgreSQL
   pg_ctl promote -D /var/lib/postgresql/data
   ```

3. Update connection strings
   ```bash
   kubectl set env deployment/api DATABASE_URL=postgresql://replica.db.com/app
   ```

4. Verify application connectivity
   ```bash
   kubectl logs -f deployment/api | grep -i database
   ```

### Post-Failover
- Update DNS records
- Create new replica from new primary
- Update monitoring dashboards
```
