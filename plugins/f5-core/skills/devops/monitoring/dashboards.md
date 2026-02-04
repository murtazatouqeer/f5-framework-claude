---
name: dashboards
description: Dashboard design patterns and visualization best practices
category: devops/monitoring
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Dashboards

## Overview

Dashboards provide visual representation of metrics and system health,
enabling quick identification of issues and trends.

## Dashboard Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dashboard Hierarchy                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Level 1: Executive Overview                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Business KPIs                                         │   │
│  │  • SLO status                                            │   │
│  │  • High-level health                                     │   │
│  │  Audience: Leadership, Stakeholders                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  Level 2: Service Overview                                       │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • RED metrics (Rate, Errors, Duration)                  │   │
│  │  • Service dependencies                                  │   │
│  │  • Resource utilization                                  │   │
│  │  Audience: On-call engineers, Team leads                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  Level 3: Service Details                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Endpoint-level metrics                                │   │
│  │  • Instance-level data                                   │   │
│  │  • Detailed error breakdown                              │   │
│  │  Audience: Service owners, Developers                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  Level 4: Debug/Investigation                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  • Trace exploration                                     │   │
│  │  • Log correlation                                       │   │
│  │  • Detailed diagnostics                                  │   │
│  │  Audience: Developers during incidents                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Dashboard Layout Patterns

### Golden Signals Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Service: API Gateway                              [🟢 Healthy]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │      Request Rate        │  │      Error Rate          │    │
│  │    ████████████████████  │  │         0.2%             │    │
│  │    1,234 req/s           │  │    ████░░░░░░░░░░░░░░░░ │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
│                                                                  │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │       Latency            │  │      Saturation          │    │
│  │  P50: 45ms  P95: 120ms   │  │  CPU: 45%  Memory: 62%   │    │
│  │  P99: 340ms              │  │  Connections: 234/500    │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Request Rate Over Time                  │   │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │   │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Latency Distribution (Heatmap)              │   │
│  │  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │   │
│  │  ▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒   │   │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Grafana Dashboard JSON

### Service Overview Dashboard

```json
{
  "dashboard": {
    "id": null,
    "uid": "api-overview",
    "title": "API Service Overview",
    "tags": ["api", "production", "overview"],
    "timezone": "browser",
    "schemaVersion": 38,
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "templating": {
      "list": [
        {
          "name": "service",
          "type": "query",
          "datasource": "Prometheus",
          "query": "label_values(http_requests_total, service)",
          "refresh": 1,
          "sort": 1
        },
        {
          "name": "environment",
          "type": "custom",
          "options": [
            { "text": "production", "value": "production" },
            { "text": "staging", "value": "staging" }
          ],
          "current": { "text": "production", "value": "production" }
        }
      ]
    },
    "panels": [
      {
        "title": "Service Health",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "up{service=\"$service\"}",
            "legendFormat": "Status"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              { "type": "value", "options": { "1": { "text": "UP", "color": "green" } } },
              { "type": "value", "options": { "0": { "text": "DOWN", "color": "red" } } }
            ]
          }
        }
      },
      {
        "title": "Request Rate",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 6, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"$service\"}[5m]))",
            "legendFormat": "req/s"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      },
      {
        "title": "Error Rate",
        "type": "gauge",
        "gridPos": { "h": 4, "w": 6, "x": 12, "y": 0 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"$service\",status=~\"5..\"}[5m])) / sum(rate(http_requests_total{service=\"$service\"}[5m])) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
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
        "title": "P95 Latency",
        "type": "stat",
        "gridPos": { "h": 4, "w": 6, "x": 18, "y": 0 },
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{service=\"$service\"}[5m])))"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 0.5 },
                { "color": "red", "value": 1 }
              ]
            }
          }
        }
      },
      {
        "title": "Request Rate Over Time",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 4 },
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{service=\"$service\"}[5m]))",
            "legendFormat": "Total"
          },
          {
            "expr": "sum by (status) (rate(http_requests_total{service=\"$service\"}[5m]))",
            "legendFormat": "{{status}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "reqps"
          }
        }
      },
      {
        "title": "Latency Percentiles",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 4 },
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket{service=\"$service\"}[5m])))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{service=\"$service\"}[5m])))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket{service=\"$service\"}[5m])))",
            "legendFormat": "P99"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "s"
          }
        }
      },
      {
        "title": "Request Rate by Endpoint",
        "type": "table",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 12 },
        "targets": [
          {
            "expr": "topk(10, sum by (path) (rate(http_requests_total{service=\"$service\"}[5m])))",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          { "id": "organize", "options": { "renameByName": { "path": "Endpoint", "Value": "Requests/s" } } }
        ]
      },
      {
        "title": "Error Rate by Status Code",
        "type": "piechart",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 12 },
        "targets": [
          {
            "expr": "sum by (status) (rate(http_requests_total{service=\"$service\",status=~\"[45]..\"}[5m]))",
            "legendFormat": "{{status}}"
          }
        ]
      }
    ]
  }
}
```

### Infrastructure Dashboard

```json
{
  "dashboard": {
    "title": "Infrastructure Overview",
    "uid": "infra-overview",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 8, "x": 0, "y": 0 },
        "targets": [
          {
            "expr": "100 - (avg by (instance) (rate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100
          }
        }
      },
      {
        "title": "Memory Usage",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 8, "x": 8, "y": 0 },
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100
          }
        }
      },
      {
        "title": "Disk Usage",
        "type": "bargauge",
        "gridPos": { "h": 8, "w": 8, "x": 16, "y": 0 },
        "targets": [
          {
            "expr": "(node_filesystem_size_bytes{mountpoint=\"/\"} - node_filesystem_avail_bytes{mountpoint=\"/\"}) / node_filesystem_size_bytes{mountpoint=\"/\"} * 100",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "steps": [
                { "color": "green", "value": null },
                { "color": "yellow", "value": 70 },
                { "color": "red", "value": 90 }
              ]
            }
          }
        }
      },
      {
        "title": "Network Traffic",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 0, "y": 8 },
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total{device!=\"lo\"}[5m])",
            "legendFormat": "{{instance}} - Receive"
          },
          {
            "expr": "rate(node_network_transmit_bytes_total{device!=\"lo\"}[5m])",
            "legendFormat": "{{instance}} - Transmit"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "Bps"
          }
        }
      },
      {
        "title": "Disk I/O",
        "type": "timeseries",
        "gridPos": { "h": 8, "w": 12, "x": 12, "y": 8 },
        "targets": [
          {
            "expr": "rate(node_disk_read_bytes_total[5m])",
            "legendFormat": "{{instance}} - Read"
          },
          {
            "expr": "rate(node_disk_written_bytes_total[5m])",
            "legendFormat": "{{instance}} - Write"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "Bps"
          }
        }
      }
    ]
  }
}
```

## Grafana Variables

```json
{
  "templating": {
    "list": [
      {
        "name": "datasource",
        "type": "datasource",
        "query": "prometheus"
      },
      {
        "name": "cluster",
        "type": "query",
        "datasource": "$datasource",
        "query": "label_values(up, cluster)",
        "refresh": 1,
        "sort": 1
      },
      {
        "name": "namespace",
        "type": "query",
        "datasource": "$datasource",
        "query": "label_values(kube_pod_info{cluster=\"$cluster\"}, namespace)",
        "refresh": 1,
        "sort": 1,
        "multi": true,
        "includeAll": true
      },
      {
        "name": "service",
        "type": "query",
        "datasource": "$datasource",
        "query": "label_values(http_requests_total{namespace=~\"$namespace\"}, service)",
        "refresh": 2,
        "sort": 1
      },
      {
        "name": "interval",
        "type": "interval",
        "options": [
          { "text": "1m", "value": "1m" },
          { "text": "5m", "value": "5m" },
          { "text": "10m", "value": "10m" },
          { "text": "30m", "value": "30m" },
          { "text": "1h", "value": "1h" }
        ],
        "current": { "text": "5m", "value": "5m" }
      }
    ]
  }
}
```

## Panel Types

### Time Series

```json
{
  "title": "Request Rate",
  "type": "timeseries",
  "options": {
    "legend": {
      "displayMode": "table",
      "placement": "bottom",
      "calcs": ["mean", "max", "last"]
    },
    "tooltip": {
      "mode": "multi",
      "sort": "desc"
    }
  },
  "fieldConfig": {
    "defaults": {
      "custom": {
        "drawStyle": "line",
        "lineInterpolation": "smooth",
        "fillOpacity": 10,
        "pointSize": 5,
        "showPoints": "never"
      }
    }
  }
}
```

### Heatmap

```json
{
  "title": "Latency Heatmap",
  "type": "heatmap",
  "targets": [
    {
      "expr": "sum by (le) (rate(http_request_duration_seconds_bucket[5m]))",
      "format": "heatmap"
    }
  ],
  "options": {
    "calculate": false,
    "cellGap": 1,
    "color": {
      "scheme": "Spectral"
    },
    "yAxis": {
      "unit": "s"
    }
  }
}
```

### Stat Panel

```json
{
  "title": "Current Error Rate",
  "type": "stat",
  "options": {
    "reduceOptions": {
      "calcs": ["lastNotNull"]
    },
    "colorMode": "background",
    "graphMode": "area",
    "justifyMode": "auto",
    "textMode": "auto"
  },
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
}
```

## Dashboard Annotations

```json
{
  "annotations": {
    "list": [
      {
        "name": "Deployments",
        "datasource": "Prometheus",
        "enable": true,
        "expr": "changes(deployment_info[1m]) > 0",
        "iconColor": "blue",
        "tagKeys": "version",
        "textFormat": "Deployed {{version}}"
      },
      {
        "name": "Alerts",
        "datasource": "-- Grafana --",
        "enable": true,
        "type": "alert"
      },
      {
        "name": "Incidents",
        "datasource": "Loki",
        "enable": true,
        "expr": "{app=\"incident-tracker\"} |= \"incident\"",
        "iconColor": "red"
      }
    ]
  }
}
```

## Dashboard as Code

### Grafonnet (Jsonnet)

```jsonnet
// dashboard.jsonnet
local grafana = import 'grafonnet/grafana.libsonnet';
local dashboard = grafana.dashboard;
local row = grafana.row;
local prometheus = grafana.prometheus;
local graphPanel = grafana.graphPanel;
local statPanel = grafana.statPanel;

dashboard.new(
  'API Overview',
  schemaVersion=38,
  tags=['api', 'production'],
  time_from='now-1h',
  refresh='30s',
)
.addTemplate(
  grafana.template.datasource(
    'datasource',
    'prometheus',
    'Prometheus',
  )
)
.addTemplate(
  grafana.template.query(
    'service',
    'label_values(http_requests_total, service)',
    datasource='$datasource',
    refresh='load',
  )
)
.addPanel(
  statPanel.new(
    'Request Rate',
    datasource='$datasource',
    unit='reqps',
  ).addTarget(
    prometheus.target(
      'sum(rate(http_requests_total{service="$service"}[5m]))',
      legendFormat='req/s',
    )
  ),
  gridPos={ h: 4, w: 6, x: 0, y: 0 }
)
.addPanel(
  graphPanel.new(
    'Request Rate Over Time',
    datasource='$datasource',
    format='reqps',
  ).addTarget(
    prometheus.target(
      'sum by (status) (rate(http_requests_total{service="$service"}[5m]))',
      legendFormat='{{status}}',
    )
  ),
  gridPos={ h: 8, w: 12, x: 0, y: 4 }
)
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Dashboard Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Follow the dashboard hierarchy (overview → detail)            │
│ ☐ Put most important metrics at the top                         │
│ ☐ Use consistent time ranges across panels                      │
│ ☐ Add meaningful thresholds and colors                          │
│ ☐ Include dashboard variables for filtering                     │
│ ☐ Add annotations for deployments and incidents                 │
│ ☐ Use appropriate visualization types                           │
│ ☐ Include legends with useful statistics                        │
│ ☐ Add links to related dashboards                               │
│ ☐ Version control dashboards as code                            │
│ ☐ Document dashboard purpose and audience                       │
│ ☐ Keep dashboards focused (avoid too many panels)               │
└─────────────────────────────────────────────────────────────────┘
```
