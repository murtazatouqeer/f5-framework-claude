---
name: k8s-metrics
description: Kubernetes metrics collection and monitoring
applies_to: kubernetes
---

# Kubernetes Metrics

## Overview

Kubernetes metrics provide visibility into cluster health, resource usage, and application performance through tools like Prometheus and metrics-server.

## Metrics Server

### Installation

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

### Verify Installation

```bash
kubectl get deployment metrics-server -n kube-system
kubectl top nodes
kubectl top pods
```

### Using kubectl top

```bash
# Node metrics
kubectl top nodes
kubectl top node node-1

# Pod metrics
kubectl top pods
kubectl top pods -n production
kubectl top pods --all-namespaces
kubectl top pods -l app=api

# Container metrics
kubectl top pods --containers

# Sort by CPU/Memory
kubectl top pods --sort-by=cpu
kubectl top pods --sort-by=memory
```

## Prometheus

### Installation with Helm

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace
```

### ServiceMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: api-monitor
  namespace: monitoring
  labels:
    release: prometheus
spec:
  selector:
    matchLabels:
      app: api
  namespaceSelector:
    matchNames:
      - production
  endpoints:
    - port: metrics
      interval: 30s
      path: /metrics
      scheme: http
```

### PodMonitor

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PodMonitor
metadata:
  name: api-pods
  namespace: monitoring
spec:
  selector:
    matchLabels:
      app: api
  namespaceSelector:
    matchNames:
      - production
  podMetricsEndpoints:
    - port: metrics
      interval: 30s
      path: /metrics
```

## Application Metrics

### Prometheus Client Example (Node.js)

```javascript
const client = require('prom-client');
const express = require('express');

// Create registry
const register = new client.Registry();

// Add default metrics
client.collectDefaultMetrics({ register });

// Custom counter
const httpRequestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total HTTP requests',
  labelNames: ['method', 'path', 'status'],
  registers: [register]
});

// Custom histogram
const httpRequestDuration = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'HTTP request duration',
  labelNames: ['method', 'path'],
  buckets: [0.1, 0.5, 1, 2, 5],
  registers: [register]
});

// Metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', register.contentType);
  res.send(await register.metrics());
});
```

### Service with Metrics Port

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
  labels:
    app: api
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"
spec:
  selector:
    app: api
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: metrics
      port: 9090
      targetPort: 9090
```

## PrometheusRule

### Alert Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: api-alerts
  namespace: monitoring
  labels:
    release: prometheus
spec:
  groups:
    - name: api-alerts
      rules:
        # High error rate
        - alert: HighErrorRate
          expr: |
            sum(rate(http_requests_total{status=~"5.."}[5m]))
            /
            sum(rate(http_requests_total[5m])) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "High error rate detected"
            description: "Error rate is {{ $value | humanizePercentage }}"

        # High latency
        - alert: HighLatency
          expr: |
            histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
            > 2
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "High latency detected"
            description: "P95 latency is {{ $value }}s"

        # Pod not ready
        - alert: PodNotReady
          expr: |
            kube_pod_status_ready{condition="true"} == 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Pod not ready"
            description: "Pod {{ $labels.pod }} in {{ $labels.namespace }} is not ready"

        # High CPU usage
        - alert: HighCPUUsage
          expr: |
            sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod, namespace)
            /
            sum(kube_pod_container_resource_limits{resource="cpu"}) by (pod, namespace)
            > 0.9
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "High CPU usage"
            description: "Pod {{ $labels.pod }} CPU usage is above 90%"

        # High memory usage
        - alert: HighMemoryUsage
          expr: |
            sum(container_memory_working_set_bytes{container!=""}) by (pod, namespace)
            /
            sum(kube_pod_container_resource_limits{resource="memory"}) by (pod, namespace)
            > 0.9
          for: 10m
          labels:
            severity: warning
          annotations:
            summary: "High memory usage"
            description: "Pod {{ $labels.pod }} memory usage is above 90%"
```

## Grafana Dashboards

### Dashboard ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  api-dashboard.json: |
    {
      "dashboard": {
        "title": "API Dashboard",
        "panels": [
          {
            "title": "Request Rate",
            "type": "graph",
            "targets": [
              {
                "expr": "sum(rate(http_requests_total[5m])) by (status)",
                "legendFormat": "{{status}}"
              }
            ]
          },
          {
            "title": "Latency P95",
            "type": "graph",
            "targets": [
              {
                "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))",
                "legendFormat": "P95"
              }
            ]
          }
        ]
      }
    }
```

## Custom Metrics API

### External Metrics for HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 20
  metrics:
    # Custom metric from Prometheus
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"

    # External metric
    - type: External
      external:
        metric:
          name: queue_messages_ready
          selector:
            matchLabels:
              queue: orders
        target:
          type: AverageValue
          averageValue: "30"
```

### Prometheus Adapter

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: adapter-config
  namespace: monitoring
data:
  config.yaml: |
    rules:
      - seriesQuery: 'http_requests_total{namespace!="",pod!=""}'
        resources:
          overrides:
            namespace: {resource: "namespace"}
            pod: {resource: "pod"}
        name:
          matches: "^(.*)_total$"
          as: "${1}_per_second"
        metricsQuery: 'sum(rate(<<.Series>>{<<.LabelMatchers>>}[2m])) by (<<.GroupBy>>)'
```

## kube-state-metrics

Exposes Kubernetes object metrics:

```bash
# Included in kube-prometheus-stack, or install separately:
helm install kube-state-metrics prometheus-community/kube-state-metrics \
  --namespace monitoring
```

### Common kube-state-metrics

```promql
# Pod status
kube_pod_status_phase{phase="Running"}
kube_pod_status_ready{condition="true"}

# Deployment status
kube_deployment_status_replicas_available
kube_deployment_status_replicas_unavailable

# Resource requests/limits
kube_pod_container_resource_requests{resource="cpu"}
kube_pod_container_resource_limits{resource="memory"}

# Node status
kube_node_status_condition{condition="Ready",status="true"}
```

## Commands

```bash
# Port forward to Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus 9090:9090 -n monitoring

# Port forward to Grafana
kubectl port-forward svc/prometheus-grafana 3000:80 -n monitoring

# Check ServiceMonitors
kubectl get servicemonitors -n monitoring

# Check PrometheusRules
kubectl get prometheusrules -n monitoring

# View Prometheus targets
curl localhost:9090/api/v1/targets

# Query Prometheus
curl 'localhost:9090/api/v1/query?query=up'
```

## Best Practices

1. **Use ServiceMonitor/PodMonitor** for service discovery
2. **Set appropriate scrape intervals** (15-60 seconds)
3. **Add labels** for filtering and aggregation
4. **Use recording rules** for expensive queries
5. **Set up meaningful alerts** with runbooks
6. **Use histograms** for latency metrics
7. **Monitor resource usage** against limits
8. **Create dashboards** for key services
9. **Secure metrics endpoints** in production
10. **Retention and storage** - plan for data volume
