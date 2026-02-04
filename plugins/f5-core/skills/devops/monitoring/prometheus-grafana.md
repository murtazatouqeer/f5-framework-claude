---
name: prometheus-grafana
description: Prometheus metrics collection and Grafana visualization
category: devops/monitoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Prometheus and Grafana

## Overview

Prometheus is an open-source monitoring system with a time-series database,
while Grafana provides visualization and alerting capabilities.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│               Prometheus + Grafana Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Applications                             │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                 │ │
│  │  │  App A   │  │  App B   │  │  App C   │                 │ │
│  │  │ /metrics │  │ /metrics │  │ /metrics │                 │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘                 │ │
│  └───────┼─────────────┼─────────────┼─────────────────────────┘ │
│          │             │             │                           │
│          └─────────────┼─────────────┘                           │
│                        │ scrape                                  │
│                        ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Prometheus                               │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │   Scraper    │  │    TSDB      │  │    Rules     │     │ │
│  │  │              │  │              │  │   Engine     │     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  │                           │                │               │ │
│  │                           │                │               │ │
│  └───────────────────────────┼────────────────┼───────────────┘ │
│                              │                │                  │
│          ┌───────────────────┘                │                  │
│          │                                    ▼                  │
│          ▼                        ┌──────────────────┐          │
│  ┌──────────────────┐            │  Alertmanager    │          │
│  │     Grafana      │            │  ┌────────────┐  │          │
│  │  ┌────────────┐  │            │  │   Routes   │  │          │
│  │  │ Dashboards │  │            │  │  Silences  │  │          │
│  │  │   Alerts   │  │            │  │  Inhibits  │  │          │
│  │  └────────────┘  │            │  └────────────┘  │          │
│  └──────────────────┘            └──────────────────┘          │
│                                           │                     │
│                                           ▼                     │
│                               ┌──────────────────────┐         │
│                               │ Slack / Email / PD   │         │
│                               └──────────────────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prometheus Installation

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:v2.47.0
    container_name: prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./prometheus/rules:/etc/prometheus/rules
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-lifecycle'
      - '--web.enable-admin-api'
    ports:
      - '9090:9090'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:10.1.0
    container_name: grafana
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - '3000:3000'
    depends_on:
      - prometheus
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:v0.26.0
    container_name: alertmanager
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
    ports:
      - '9093:9093'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

### Kubernetes with Helm

```bash
# Add Helm repository
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install kube-prometheus-stack (includes Prometheus, Grafana, Alertmanager)
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f values.yaml
```

```yaml
# values.yaml
prometheus:
  prometheusSpec:
    retention: 15d
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: fast-ssd
          accessModes: ['ReadWriteOnce']
          resources:
            requests:
              storage: 50Gi
    resources:
      requests:
        memory: 2Gi
        cpu: 500m
      limits:
        memory: 4Gi
        cpu: 2000m

grafana:
  adminPassword: ${GRAFANA_PASSWORD}
  persistence:
    enabled: true
    size: 10Gi
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: 'default'
          orgId: 1
          folder: ''
          type: file
          disableDeletion: false
          editable: true
          options:
            path: /var/lib/grafana/dashboards/default

alertmanager:
  config:
    global:
      slack_api_url: ${SLACK_WEBHOOK_URL}
    route:
      group_by: ['alertname', 'cluster', 'service']
      group_wait: 30s
      group_interval: 5m
      repeat_interval: 4h
      receiver: 'slack-notifications'
    receivers:
      - name: 'slack-notifications'
        slack_configs:
          - channel: '#alerts'
            send_resolved: true
```

## Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: production
    region: us-east-1

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Application endpoints
  - job_name: 'api'
    metrics_path: /metrics
    static_configs:
      - targets: ['api:3000']
        labels:
          service: api
          env: production

  # Kubernetes service discovery
  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels:
          [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
        target_label: __address__
      - source_labels: [__meta_kubernetes_namespace]
        action: replace
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        action: replace
        target_label: pod
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: replace
        target_label: app

  # Node Exporter
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']

  # Blackbox Exporter (probing)
  - job_name: 'blackbox'
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - https://api.example.com/health
          - https://app.example.com
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

## PromQL Queries

### Basic Queries

```promql
# Instant vector (current value)
http_requests_total

# Range vector (values over time)
http_requests_total[5m]

# With labels
http_requests_total{method="GET", status="200"}

# Label matching
http_requests_total{status=~"2.."}    # Regex match
http_requests_total{status!="500"}    # Not equal
http_requests_total{status=~"4..|5.."} # Multiple patterns
```

### Rate and Aggregations

```promql
# Request rate per second (5 minute window)
rate(http_requests_total[5m])

# Increase over time period
increase(http_requests_total[1h])

# Sum by label
sum by (method) (rate(http_requests_total[5m]))

# Average
avg(rate(http_requests_total[5m]))

# Percentiles from histogram
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# P99 grouped by service
histogram_quantile(0.99,
  sum by (service, le) (
    rate(http_request_duration_seconds_bucket[5m])
  )
)
```

### Common Patterns

```promql
# Error rate percentage
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) * 100

# Availability (success rate)
sum(rate(http_requests_total{status!~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) * 100

# Request rate by status
sum by (status) (rate(http_requests_total[5m]))

# Memory usage percentage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) /
node_memory_MemTotal_bytes * 100

# CPU usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# Disk usage percentage
100 - ((node_filesystem_avail_bytes{mountpoint="/"} /
        node_filesystem_size_bytes{mountpoint="/"}) * 100)

# Saturation (load average per CPU)
node_load1 / count(node_cpu_seconds_total{mode="idle"}) without (cpu, mode)

# Top 5 by requests
topk(5, sum by (path) (rate(http_requests_total[5m])))

# Increase in errors over last hour
increase(http_requests_total{status=~"5.."}[1h])
```

### Alerting Queries

```promql
# High error rate (>5%)
sum(rate(http_requests_total{status=~"5.."}[5m])) /
sum(rate(http_requests_total[5m])) > 0.05

# Slow response time (P95 > 1s)
histogram_quantile(0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
) > 1

# High memory usage (>85%)
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) /
node_memory_MemTotal_bytes > 0.85

# Instance down
up == 0

# Pending pods
kube_pod_status_phase{phase="Pending"} > 0
```

## Recording Rules

```yaml
# rules/recording.yml
groups:
  - name: api-rules
    interval: 30s
    rules:
      # Request rate
      - record: job:http_requests:rate5m
        expr: sum by (job) (rate(http_requests_total[5m]))

      # Error rate
      - record: job:http_requests:error_rate5m
        expr: |
          sum by (job) (rate(http_requests_total{status=~"5.."}[5m])) /
          sum by (job) (rate(http_requests_total[5m]))

      # Latency percentiles
      - record: job:http_request_duration_seconds:p50
        expr: |
          histogram_quantile(0.50,
            sum by (job, le) (rate(http_request_duration_seconds_bucket[5m]))
          )

      - record: job:http_request_duration_seconds:p95
        expr: |
          histogram_quantile(0.95,
            sum by (job, le) (rate(http_request_duration_seconds_bucket[5m]))
          )

      - record: job:http_request_duration_seconds:p99
        expr: |
          histogram_quantile(0.99,
            sum by (job, le) (rate(http_request_duration_seconds_bucket[5m]))
          )
```

## Grafana Dashboards

### Dashboard JSON

```json
{
  "dashboard": {
    "title": "API Overview",
    "uid": "api-overview",
    "tags": ["api", "production"],
    "timezone": "browser",
    "refresh": "30s",
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m]))",
            "legendFormat": "Total"
          },
          {
            "expr": "sum by (status) (rate(http_requests_total[5m]))",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "gauge",
        "gridPos": { "h": 8, "w": 6, "x": 12, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{status=~\"5..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 1 },
                { "color": "red", "value": 5 }
              ]
            }
          }
        }
      },
      {
        "title": "Latency P95",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))",
            "legendFormat": "P99"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      }
    ]
  }
}
```

### Grafana Provisioning

```yaml
# grafana/provisioning/datasources/datasources.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    editable: false
```

```yaml
# grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1
providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    options:
      path: /var/lib/grafana/dashboards
```

## ServiceMonitor (Kubernetes)

```yaml
# servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: my-app
  namespace: production
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: my-app
  namespaceSelector:
    matchNames:
      - production
  endpoints:
    - port: http
      path: /metrics
      interval: 15s
      scrapeTimeout: 10s
      honorLabels: true
      relabelings:
        - sourceLabels: [__meta_kubernetes_pod_name]
          targetLabel: pod
        - sourceLabels: [__meta_kubernetes_namespace]
          targetLabel: namespace
```

## PodMonitor (Kubernetes)

```yaml
# podmonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: my-app
  namespace: production
spec:
  selector:
    matchLabels:
      app: my-app
  namespaceSelector:
    matchNames:
      - production
  podMetricsEndpoints:
    - port: metrics
      path: /metrics
      interval: 15s
```

## Exporters

### Node Exporter

```yaml
# docker-compose node-exporter
node-exporter:
  image: prom/node-exporter:v1.6.1
  container_name: node-exporter
  volumes:
    - /proc:/host/proc:ro
    - /sys:/host/sys:ro
    - /:/rootfs:ro
  command:
    - '--path.procfs=/host/proc'
    - '--path.sysfs=/host/sys'
    - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
  ports:
    - '9100:9100'
```

### Blackbox Exporter

```yaml
# blackbox-exporter.yml
modules:
  http_2xx:
    prober: http
    timeout: 5s
    http:
      valid_http_versions: ['HTTP/1.1', 'HTTP/2.0']
      valid_status_codes: []
      method: GET
      follow_redirects: true
      fail_if_ssl: false
      fail_if_not_ssl: true
      tls_config:
        insecure_skip_verify: false

  http_post_2xx:
    prober: http
    timeout: 5s
    http:
      method: POST
      headers:
        Content-Type: application/json

  tcp_connect:
    prober: tcp
    timeout: 5s

  icmp:
    prober: icmp
    timeout: 5s
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Prometheus + Grafana Best Practices                 │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use recording rules for expensive queries                     │
│ ☐ Set appropriate retention period (15-30 days typical)         │
│ ☐ Use relabeling to reduce cardinality                          │
│ ☐ Organize dashboards by service/team                           │
│ ☐ Create standard dashboard templates                           │
│ ☐ Use variables in Grafana for filtering                        │
│ ☐ Set up alerting in Alertmanager (not Grafana)                │
│ ☐ Configure proper resource limits                              │
│ ☐ Use federation for large deployments                          │
│ ☐ Implement backup for Prometheus TSDB                          │
│ ☐ Use ServiceMonitor/PodMonitor in Kubernetes                   │
│ ☐ Monitor Prometheus itself                                     │
└─────────────────────────────────────────────────────────────────┘
```
