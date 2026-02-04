---
name: alerting
description: Alerting strategies and Alertmanager configuration
category: devops/monitoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Alerting

## Overview

Effective alerting is crucial for maintaining system reliability. Good alerts
are actionable, meaningful, and minimize noise while catching real issues.

## Alerting Philosophy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Alerting Philosophy                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Good Alerts Are:                                                │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ✅ Actionable - Someone needs to take action            │   │
│  │ ✅ Meaningful - Represents real user impact             │   │
│  │ ✅ Urgent - Requires timely response                    │   │
│  │ ✅ Infrequent - Not constant noise                      │   │
│  │ ✅ Documented - Clear runbook for response              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Bad Alerts Are:                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ❌ Flapping - Constantly firing and resolving           │   │
│  │ ❌ Ignored - Team has learned to dismiss them           │   │
│  │ ❌ Unclear - No guidance on how to respond              │   │
│  │ ❌ Low impact - No actual user consequence              │   │
│  │ ❌ Duplicative - Multiple alerts for same issue         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Alert Severity Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                    Severity Levels                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  P1 - Critical                                                   │
│  ├─ Service completely down                                     │
│  ├─ Data loss occurring                                         │
│  ├─ Security breach detected                                    │
│  └─ Response: Immediate (< 5 min)                               │
│                                                                  │
│  P2 - High                                                       │
│  ├─ Major feature unavailable                                   │
│  ├─ Performance severely degraded                               │
│  ├─ Error rate > 5%                                             │
│  └─ Response: Within 30 minutes                                 │
│                                                                  │
│  P3 - Medium                                                     │
│  ├─ Partial degradation                                         │
│  ├─ Non-critical service issues                                 │
│  ├─ Warning thresholds exceeded                                 │
│  └─ Response: Within 4 hours                                    │
│                                                                  │
│  P4 - Low                                                        │
│  ├─ Informational                                               │
│  ├─ Approaching thresholds                                      │
│  ├─ Non-urgent issues                                           │
│  └─ Response: Next business day                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prometheus Alerting Rules

```yaml
# rules/alerts.yml
groups:
  - name: api-alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m])) /
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: 'High error rate detected'
          description: 'Error rate is {{ $value | humanizePercentage }} (> 5%)'
          runbook_url: 'https://runbooks.example.com/high-error-rate'

      # Slow response time
      - alert: HighLatency
        expr: |
          histogram_quantile(0.95,
            sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
          ) > 1
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: 'High latency detected'
          description: 'P95 latency is {{ $value | humanizeDuration }}'

      # Service down
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: 'Service {{ $labels.job }} is down'
          description: 'Instance {{ $labels.instance }} has been down for > 1 minute'

  - name: infrastructure-alerts
    rules:
      # High CPU usage
      - alert: HighCPUUsage
        expr: |
          100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'High CPU usage on {{ $labels.instance }}'
          description: 'CPU usage is {{ $value | humanize }}%'

      # High memory usage
      - alert: HighMemoryUsage
        expr: |
          (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) /
          node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'High memory usage on {{ $labels.instance }}'
          description: 'Memory usage is {{ $value | humanizePercentage }}'

      # Disk space low
      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} /
           node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'Low disk space on {{ $labels.instance }}'
          description: 'Only {{ $value | humanizePercentage }} disk space remaining'

      # Disk space critical
      - alert: DiskSpaceCritical
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} /
           node_filesystem_size_bytes{mountpoint="/"}) < 0.05
        for: 1m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: 'Critical disk space on {{ $labels.instance }}'
          description: 'Only {{ $value | humanizePercentage }} disk space remaining'

  - name: kubernetes-alerts
    rules:
      # Pod not ready
      - alert: PodNotReady
        expr: |
          kube_pod_status_ready{condition="true"} == 0
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'Pod {{ $labels.pod }} not ready'
          description: 'Pod {{ $labels.namespace }}/{{ $labels.pod }} has been not ready for > 5 minutes'

      # Pod crash looping
      - alert: PodCrashLooping
        expr: |
          rate(kube_pod_container_status_restarts_total[15m]) > 0
        for: 5m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'Pod {{ $labels.pod }} is crash looping'
          description: 'Pod {{ $labels.namespace }}/{{ $labels.pod }} is restarting frequently'

      # Deployment replicas mismatch
      - alert: DeploymentReplicasMismatch
        expr: |
          kube_deployment_spec_replicas != kube_deployment_status_available_replicas
        for: 10m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: 'Deployment {{ $labels.deployment }} replicas mismatch'
          description: 'Deployment {{ $labels.namespace }}/{{ $labels.deployment }} has {{ $value }} unavailable replicas'

  - name: database-alerts
    rules:
      # High connection count
      - alert: DatabaseHighConnections
        expr: |
          pg_stat_activity_count > 80
        for: 5m
        labels:
          severity: warning
          team: database
        annotations:
          summary: 'High database connections'
          description: 'Database has {{ $value }} active connections'

      # Slow queries
      - alert: DatabaseSlowQueries
        expr: |
          rate(pg_stat_statements_seconds_total[5m]) > 1
        for: 5m
        labels:
          severity: warning
          team: database
        annotations:
          summary: 'Slow database queries detected'
          description: 'Query execution time is high: {{ $value | humanizeDuration }}'

      # Replication lag
      - alert: DatabaseReplicationLag
        expr: |
          pg_replication_lag > 30
        for: 5m
        labels:
          severity: warning
          team: database
        annotations:
          summary: 'Database replication lag'
          description: 'Replication lag is {{ $value }} seconds'
```

## Alertmanager Configuration

```yaml
# alertmanager.yml
global:
  # Default SMTP settings
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: '${SMTP_PASSWORD}'

  # Slack settings
  slack_api_url: '${SLACK_WEBHOOK_URL}'

  # PagerDuty settings
  pagerduty_url: 'https://events.pagerduty.com/v2/enqueue'

  # Resolve timeout
  resolve_timeout: 5m

# Templates
templates:
  - '/etc/alertmanager/templates/*.tmpl'

# Routing tree
route:
  # Default receiver
  receiver: 'slack-default'

  # Group by these labels
  group_by: ['alertname', 'cluster', 'service']

  # Wait before sending grouped alerts
  group_wait: 30s

  # Wait before sending new alerts for group
  group_interval: 5m

  # Wait before re-sending
  repeat_interval: 4h

  # Child routes
  routes:
    # Critical alerts -> PagerDuty + Slack
    - match:
        severity: critical
      receiver: 'pagerduty-critical'
      continue: true
      routes:
        - match:
            team: backend
          receiver: 'slack-backend-critical'
        - match:
            team: platform
          receiver: 'slack-platform-critical'

    # High severity -> Slack with shorter repeat
    - match:
        severity: high
      receiver: 'slack-high'
      repeat_interval: 1h

    # Warning -> Slack
    - match:
        severity: warning
      receiver: 'slack-warnings'
      repeat_interval: 4h

    # Team-specific routing
    - match:
        team: backend
      receiver: 'slack-backend'
    - match:
        team: platform
      receiver: 'slack-platform'
    - match:
        team: database
      receiver: 'slack-database'

# Inhibition rules
inhibit_rules:
  # If critical, inhibit warnings
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'cluster', 'service']

  # If service is down, inhibit other alerts for that service
  - source_match:
      alertname: 'ServiceDown'
    target_match_re:
      alertname: '.+'
    equal: ['service']

# Receivers
receivers:
  - name: 'slack-default'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
        title: '{{ template "slack.title" . }}'
        text: '{{ template "slack.text" . }}'
        actions:
          - type: button
            text: 'Runbook'
            url: '{{ (index .Alerts 0).Annotations.runbook_url }}'
          - type: button
            text: 'Dashboard'
            url: 'https://grafana.example.com/d/overview'

  - name: 'slack-backend'
    slack_configs:
      - channel: '#backend-alerts'
        send_resolved: true

  - name: 'slack-backend-critical'
    slack_configs:
      - channel: '#backend-critical'
        send_resolved: true
        color: '{{ if eq .Status "firing" }}danger{{ else }}good{{ end }}'

  - name: 'slack-platform'
    slack_configs:
      - channel: '#platform-alerts'
        send_resolved: true

  - name: 'slack-platform-critical'
    slack_configs:
      - channel: '#platform-critical'
        send_resolved: true

  - name: 'slack-database'
    slack_configs:
      - channel: '#database-alerts'
        send_resolved: true

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#warnings'
        send_resolved: true

  - name: 'slack-high'
    slack_configs:
      - channel: '#alerts-high'
        send_resolved: true

  - name: 'pagerduty-critical'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_SERVICE_KEY}'
        severity: critical
        description: '{{ template "pagerduty.description" . }}'
        details:
          firing: '{{ template "pagerduty.firing" . }}'
          num_firing: '{{ .Alerts.Firing | len }}'
          num_resolved: '{{ .Alerts.Resolved | len }}'

  - name: 'email-critical'
    email_configs:
      - to: 'oncall@example.com'
        send_resolved: true
        html: '{{ template "email.html" . }}'
```

## Alert Templates

```yaml
# templates/slack.tmpl
{{ define "slack.title" }}
[{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ end }}] {{ .CommonLabels.alertname }}
{{ end }}

{{ define "slack.text" }}
{{ range .Alerts }}
*Alert:* {{ .Annotations.summary }}
*Description:* {{ .Annotations.description }}
*Severity:* {{ .Labels.severity }}
*Service:* {{ .Labels.service }}
{{ if .Labels.instance }}*Instance:* {{ .Labels.instance }}{{ end }}
{{ end }}
{{ end }}

# templates/pagerduty.tmpl
{{ define "pagerduty.description" }}
{{ .CommonLabels.alertname }}: {{ .CommonAnnotations.summary }}
{{ end }}

{{ define "pagerduty.firing" }}
{{ range .Alerts.Firing }}
- {{ .Annotations.description }}
{{ end }}
{{ end }}
```

## SLO-Based Alerts

```yaml
# rules/slo-alerts.yml
groups:
  - name: slo-alerts
    rules:
      # Error budget burn rate (fast burn)
      - alert: ErrorBudgetFastBurn
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[1h])) /
            sum(rate(http_requests_total[1h]))
          ) > (14.4 * (1 - 0.999))  # 14.4x burn rate
        for: 2m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: 'Error budget burning too fast'
          description: 'At current rate, error budget will be exhausted in < 1 hour'

      # Error budget burn rate (slow burn)
      - alert: ErrorBudgetSlowBurn
        expr: |
          (
            sum(rate(http_requests_total{status=~"5.."}[6h])) /
            sum(rate(http_requests_total[6h]))
          ) > (6 * (1 - 0.999))  # 6x burn rate
        for: 30m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: 'Error budget burning faster than sustainable'
          description: 'At current rate, error budget will be exhausted before end of period'

      # Availability SLO breach
      - alert: AvailabilitySLOBreach
        expr: |
          (
            sum(rate(http_requests_total{status!~"5.."}[30d])) /
            sum(rate(http_requests_total[30d]))
          ) < 0.999
        for: 5m
        labels:
          severity: critical
          team: backend
        annotations:
          summary: 'Availability SLO breached'
          description: 'Current 30-day availability is {{ $value | humanizePercentage }}, below 99.9% SLO'

      # Latency SLO breach
      - alert: LatencySLOBreach
        expr: |
          (
            sum(rate(http_request_duration_seconds_bucket{le="0.3"}[30d])) /
            sum(rate(http_request_duration_seconds_count[30d]))
          ) < 0.95
        for: 5m
        labels:
          severity: warning
          team: backend
        annotations:
          summary: 'Latency SLO breached'
          description: 'Less than 95% of requests completing within 300ms SLO'
```

## Silences and Maintenance

```bash
# Create silence via amtool
amtool silence add alertname="HighCPUUsage" instance="worker-1" \
  --author="admin@example.com" \
  --comment="Scheduled maintenance" \
  --duration="2h"

# List active silences
amtool silence query

# Expire a silence
amtool silence expire <silence-id>

# Create silence via API
curl -X POST http://alertmanager:9093/api/v2/silences \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [
      {"name": "alertname", "value": "HighCPUUsage", "isRegex": false},
      {"name": "instance", "value": "worker-1", "isRegex": false}
    ],
    "startsAt": "2024-01-15T00:00:00Z",
    "endsAt": "2024-01-15T02:00:00Z",
    "createdBy": "admin@example.com",
    "comment": "Scheduled maintenance"
  }'
```

## Alert Testing

```yaml
# test-alerts.yml
rule_files:
  - rules/*.yml

evaluation_interval: 1m

tests:
  - interval: 1m
    input_series:
      - series: 'http_requests_total{status="200"}'
        values: '0+100x10'
      - series: 'http_requests_total{status="500"}'
        values: '0+10x10'

    alert_rule_test:
      - eval_time: 10m
        alertname: HighErrorRate
        exp_alerts:
          - exp_labels:
              severity: critical
              team: backend
            exp_annotations:
              summary: 'High error rate detected'
```

```bash
# Run alert tests
promtool test rules test-alerts.yml
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   Alerting Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Alert on symptoms, not causes                                  │
│ ☐ Ensure all alerts are actionable                              │
│ ☐ Include runbook URLs in annotations                           │
│ ☐ Use appropriate severity levels                               │
│ ☐ Set proper for durations to avoid flapping                    │
│ ☐ Group related alerts together                                 │
│ ☐ Configure inhibition rules                                    │
│ ☐ Route critical alerts to PagerDuty/on-call                    │
│ ☐ Use SLO-based alerts for user-facing services                 │
│ ☐ Regularly review and prune unused alerts                      │
│ ☐ Test alerts in staging before production                      │
│ ☐ Document response procedures                                  │
└─────────────────────────────────────────────────────────────────┘
```
