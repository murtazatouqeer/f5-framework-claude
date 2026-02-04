---
name: log-aggregation
description: Log aggregation patterns and tools
category: devops/logging
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Log Aggregation

## Overview

Log aggregation is the process of collecting logs from multiple sources,
processing them, and storing them in a centralized location for analysis.

## Aggregation Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Log Aggregation Architecture                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Sources                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐            │   │
│  │  │App │ │App │ │App │ │ DB │ │K8s │ │Infra│            │   │
│  │  │ 1  │ │ 2  │ │ 3  │ │    │ │    │ │    │            │   │
│  │  └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘            │   │
│  └─────┼──────┼──────┼──────┼──────┼──────┼──────────────────┘   │
│        │      │      │      │      │      │                      │
│        └──────┴──────┴──────┼──────┴──────┘                      │
│                             ▼                                     │
│  Collection Layer                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │           Agents (Fluentd/Filebeat/Vector)               │   │
│  │  • Tail files    • Parse formats    • Buffer locally    │   │
│  │  • Add metadata  • Filter/transform  • Ship reliably     │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                     │
│                             ▼                                     │
│  Processing Layer (Optional)                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Kafka / Logstash / Fluentd                  │   │
│  │  • Queue/buffer  • Transform  • Route  • Enrich         │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                     │
│                             ▼                                     │
│  Storage Layer                                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │         Elasticsearch / Loki / ClickHouse                │   │
│  │  • Index  • Store  • Search  • Retain/Archive            │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                     │
│                             ▼                                     │
│  Visualization Layer                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            Kibana / Grafana / Custom UI                  │   │
│  │  • Search  • Dashboards  • Alerts  • Explore             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Fluentd

### Fluentd Configuration

```ruby
# fluent.conf

# Input: Collect from container logs
<source>
  @type tail
  path /var/log/containers/*.log
  pos_file /var/log/fluentd-containers.pos
  tag kubernetes.*
  read_from_head true
  <parse>
    @type json
    time_key time
    time_format %Y-%m-%dT%H:%M:%S.%NZ
  </parse>
</source>

# Input: TCP for direct log shipping
<source>
  @type forward
  port 24224
  bind 0.0.0.0
</source>

# Filter: Parse JSON logs
<filter kubernetes.**>
  @type parser
  key_name log
  reserve_data true
  remove_key_name_field true
  <parse>
    @type json
    json_parser oj
  </parse>
</filter>

# Filter: Add Kubernetes metadata
<filter kubernetes.**>
  @type kubernetes_metadata
  @id filter_kube_metadata
</filter>

# Filter: Exclude health check logs
<filter kubernetes.**>
  @type grep
  <exclude>
    key $.kubernetes.container_name
    pattern /^(fluent|filebeat|prometheus)/
  </exclude>
</filter>

# Match: Output to Elasticsearch
<match kubernetes.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix k8s-logs
  include_timestamp true
  type_name _doc

  <buffer>
    @type file
    path /var/log/fluentd-buffers/kubernetes.buffer
    flush_mode interval
    flush_interval 5s
    flush_thread_count 2
    retry_forever true
    retry_max_interval 30s
    chunk_limit_size 10M
    queue_limit_length 8
    overflow_action block
  </buffer>
</match>

# Match: Send errors to separate index
<match kubernetes.**.error>
  @type elasticsearch
  host elasticsearch
  port 9200
  logstash_format true
  logstash_prefix k8s-errors
</match>
```

### Fluentd Kubernetes DaemonSet

```yaml
# fluentd-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: logging
spec:
  selector:
    matchLabels:
      name: fluentd
  template:
    metadata:
      labels:
        name: fluentd
    spec:
      serviceAccountName: fluentd
      tolerations:
        - key: node-role.kubernetes.io/master
          effect: NoSchedule
      containers:
        - name: fluentd
          image: fluent/fluentd-kubernetes-daemonset:v1.16-debian-elasticsearch8
          env:
            - name: FLUENT_ELASTICSEARCH_HOST
              value: "elasticsearch"
            - name: FLUENT_ELASTICSEARCH_PORT
              value: "9200"
            - name: FLUENT_ELASTICSEARCH_SCHEME
              value: "http"
          resources:
            limits:
              memory: 200Mi
            requests:
              cpu: 100m
              memory: 200Mi
          volumeMounts:
            - name: varlog
              mountPath: /var/log
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
            - name: config
              mountPath: /fluentd/etc/fluent.conf
              subPath: fluent.conf
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
        - name: config
          configMap:
            name: fluentd-config
```

## Grafana Loki

### Loki Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Loki Architecture                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Promtail                             │   │
│  │  (Log collection agent - similar to Prometheus model)    │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                        Loki                              │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │Distributor│  │  Ingester │  │  Querier  │              │   │
│  │  │          │→│           │→│           │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  │                      │                │                  │   │
│  │                      ▼                │                  │   │
│  │              ┌──────────────┐         │                  │   │
│  │              │    Storage    │←────────┘                  │   │
│  │              │  (S3/GCS/FS) │                            │   │
│  │              └──────────────┘                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Grafana                             │   │
│  │  (Visualization and querying)                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Loki Configuration

```yaml
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9096

ingester:
  wal:
    enabled: true
    dir: /loki/wal
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 1h
  max_chunk_age: 1h
  chunk_target_size: 1048576
  chunk_retain_period: 30s
  max_transfer_retries: 0

schema_config:
  configs:
    - from: 2020-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    cache_ttl: 24h
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks

compactor:
  working_directory: /loki/boltdb-shipper-compactor
  shared_store: filesystem

limits_config:
  reject_old_samples: true
  reject_old_samples_max_age: 168h
  ingestion_rate_mb: 10
  ingestion_burst_size_mb: 20
  max_streams_per_user: 10000

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: true
  retention_period: 720h
```

### Promtail Configuration

```yaml
# promtail-config.yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  # Kubernetes pod logs
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    pipeline_stages:
      - cri: {}
      - json:
          expressions:
            level: level
            message: message
            timestamp: timestamp
      - labels:
          level:
      - timestamp:
          source: timestamp
          format: RFC3339Nano
    relabel_configs:
      - source_labels:
          - __meta_kubernetes_pod_controller_name
        regex: ([0-9a-z-.]+?)(-[0-9a-f]{8,10})?
        action: replace
        target_label: __tmp_controller_name
      - source_labels:
          - __meta_kubernetes_pod_label_app_kubernetes_io_name
          - __meta_kubernetes_pod_label_app
          - __tmp_controller_name
          - __meta_kubernetes_pod_name
        regex: ^;*([^;]+)(;.*)?$
        action: replace
        target_label: app
      - source_labels:
          - __meta_kubernetes_pod_node_name
        action: replace
        target_label: node_name
      - source_labels:
          - __meta_kubernetes_namespace
        action: replace
        target_label: namespace
      - source_labels:
          - __meta_kubernetes_pod_name
        action: replace
        target_label: pod
      - source_labels:
          - __meta_kubernetes_pod_container_name
        action: replace
        target_label: container

  # Static file logs
  - job_name: system
    static_configs:
      - targets:
          - localhost
        labels:
          job: varlogs
          __path__: /var/log/*log
```

### LogQL Queries

```logql
# Basic queries
{app="api-gateway"}
{namespace="production", container="app"}

# Filter by content
{app="api-gateway"} |= "error"
{app="api-gateway"} !~ "health"

# JSON parsing
{app="api-gateway"} | json | level="error"
{app="api-gateway"} | json | duration > 1000

# Line format
{app="api-gateway"} | json | line_format "{{.level}} - {{.message}}"

# Metrics from logs
count_over_time({app="api-gateway"} |= "error" [5m])
rate({app="api-gateway"} |= "error" [5m])
sum by (level) (count_over_time({app="api-gateway"} | json [1h]))

# Top errors
topk(10, sum by (error) (count_over_time({app="api-gateway"} | json | error!="" [1h])))
```

## Vector

### Vector Configuration

```toml
# vector.toml

# Sources
[sources.kubernetes_logs]
type = "kubernetes_logs"
self_node_name = "${VECTOR_SELF_NODE_NAME}"

[sources.app_logs]
type = "file"
include = ["/var/log/app/*.log"]
read_from = "beginning"

# Transforms
[transforms.parse_json]
type = "remap"
inputs = ["kubernetes_logs", "app_logs"]
source = '''
. = parse_json!(.message)
.timestamp = to_timestamp!(.timestamp)
'''

[transforms.add_metadata]
type = "remap"
inputs = ["parse_json"]
source = '''
.environment = get_env_var!("ENVIRONMENT")
.cluster = get_env_var!("CLUSTER_NAME")
'''

[transforms.filter_debug]
type = "filter"
inputs = ["add_metadata"]
condition = '.level != "debug"'

[transforms.sample]
type = "sample"
inputs = ["filter_debug"]
rate = 10  # Keep 1 in 10 logs
exclude = '.level == "error"'  # Don't sample errors

# Sinks
[sinks.elasticsearch]
type = "elasticsearch"
inputs = ["sample"]
endpoints = ["http://elasticsearch:9200"]
bulk.index = "logs-%Y.%m.%d"

[sinks.loki]
type = "loki"
inputs = ["sample"]
endpoint = "http://loki:3100"
labels.app = "{{ app }}"
labels.environment = "{{ environment }}"

[sinks.console]
type = "console"
inputs = ["sample"]
encoding.codec = "json"
```

## Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                  Log Aggregation Tool Comparison                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tool         │ Best For              │ Storage        │ Query │
│  ─────────────┼───────────────────────┼────────────────┼───────│
│  ELK Stack    │ Full-text search      │ Elasticsearch  │ KQL   │
│               │ Complex analysis      │ (expensive)    │       │
│               │                       │                │       │
│  Loki         │ Kubernetes-native     │ Object storage │ LogQL │
│               │ Cost-effective        │ (cheap)        │       │
│               │                       │                │       │
│  Fluentd      │ Data collection       │ N/A (shipper)  │ N/A   │
│               │ Multi-destination     │                │       │
│               │                       │                │       │
│  Vector       │ High performance      │ N/A (shipper)  │ VRL   │
│               │ Observability pipeline│                │       │
│               │                       │                │       │
│  CloudWatch   │ AWS-native            │ AWS            │ Logs  │
│  Logs         │ Easy setup            │                │Insights│
│               │                       │                │       │
│  Datadog      │ APM integration       │ Managed        │ Custom│
│               │ Enterprise support    │                │       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                Log Aggregation Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use structured logging (JSON) for better parsing              │
│ ☐ Add labels for efficient filtering (service, env, pod)        │
│ ☐ Implement log sampling for high-volume services               │
│ ☐ Set up log retention and rotation policies                    │
│ ☐ Use buffers to handle spikes                                  │
│ ☐ Monitor the logging pipeline itself                           │
│ ☐ Configure alerts for log pipeline failures                    │
│ ☐ Implement log correlation with trace IDs                      │
│ ☐ Filter sensitive data at collection time                      │
│ ☐ Use appropriate storage tier (hot/warm/cold)                  │
│ ☐ Test log queries for performance                              │
│ ☐ Document log schemas and query patterns                       │
└─────────────────────────────────────────────────────────────────┘
```
