---
name: elk-stack
description: ELK Stack (Elasticsearch, Logstash, Kibana) setup and configuration
category: devops/logging
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# ELK Stack

## Overview

The ELK Stack (Elasticsearch, Logstash, Kibana) is a popular log management
solution for collecting, processing, storing, and visualizing logs.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ELK Stack Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Applications                                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │  App A   │  │  App B   │  │  App C   │                       │
│  │  (logs)  │  │  (logs)  │  │  (logs)  │                       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                       │
│       │             │             │                              │
│       └─────────────┼─────────────┘                              │
│                     │                                            │
│                     ▼                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Beats / Fluentd                       │   │
│  │  (Log Shippers)                                          │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                      Logstash                            │   │
│  │  (Processing Pipeline)                                   │   │
│  │  ┌─────────┐  ┌─────────────┐  ┌─────────┐             │   │
│  │  │  Input  │→│   Filter    │→│  Output  │             │   │
│  │  │         │  │  (Parse,   │  │         │             │   │
│  │  │         │  │   Enrich)  │  │         │             │   │
│  │  └─────────┘  └─────────────┘  └─────────┘             │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Elasticsearch                          │   │
│  │  (Storage & Search)                                      │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                 │   │
│  │  │ Node 1  │  │ Node 2  │  │ Node 3  │                 │   │
│  │  └─────────┘  └─────────┘  └─────────┘                 │   │
│  └──────────────────────────┬──────────────────────────────┘   │
│                             │                                    │
│                             ▼                                    │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                       Kibana                             │   │
│  │  (Visualization)                                         │   │
│  │  ┌─────────────────────────────────────────────────┐   │   │
│  │  │  Dashboards  │  Discover  │  Alerts  │  Lens   │   │   │
│  │  └─────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Docker Compose Setup

```yaml
# docker-compose.yml
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - elasticsearch-data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
      - "9300:9300"
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:9200 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: logstash
    volumes:
      - ./logstash/pipeline:/usr/share/logstash/pipeline
      - ./logstash/config:/usr/share/logstash/config
    ports:
      - "5044:5044"
      - "5000:5000/tcp"
      - "5000:5000/udp"
      - "9600:9600"
    depends_on:
      elasticsearch:
        condition: service_healthy

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      elasticsearch:
        condition: service_healthy

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: filebeat
    volumes:
      - ./filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - logstash
    user: root

volumes:
  elasticsearch-data:
```

## Elasticsearch Configuration

### Index Template

```json
// PUT _index_template/app-logs
{
  "index_patterns": ["app-logs-*"],
  "priority": 100,
  "template": {
    "settings": {
      "number_of_shards": 3,
      "number_of_replicas": 1,
      "index.lifecycle.name": "app-logs-policy",
      "index.lifecycle.rollover_alias": "app-logs"
    },
    "mappings": {
      "properties": {
        "@timestamp": { "type": "date" },
        "level": { "type": "keyword" },
        "message": { "type": "text" },
        "service": { "type": "keyword" },
        "environment": { "type": "keyword" },
        "host": { "type": "keyword" },
        "correlationId": { "type": "keyword" },
        "requestId": { "type": "keyword" },
        "userId": { "type": "keyword" },
        "http": {
          "properties": {
            "method": { "type": "keyword" },
            "path": { "type": "keyword" },
            "statusCode": { "type": "integer" },
            "duration": { "type": "integer" }
          }
        },
        "error": {
          "properties": {
            "name": { "type": "keyword" },
            "message": { "type": "text" },
            "stack": { "type": "text" }
          }
        }
      }
    }
  }
}
```

### Index Lifecycle Policy

```json
// PUT _ilm/policy/app-logs-policy
{
  "policy": {
    "phases": {
      "hot": {
        "min_age": "0ms",
        "actions": {
          "rollover": {
            "max_primary_shard_size": "50gb",
            "max_age": "1d"
          },
          "set_priority": {
            "priority": 100
          }
        }
      },
      "warm": {
        "min_age": "2d",
        "actions": {
          "shrink": {
            "number_of_shards": 1
          },
          "forcemerge": {
            "max_num_segments": 1
          },
          "set_priority": {
            "priority": 50
          }
        }
      },
      "cold": {
        "min_age": "7d",
        "actions": {
          "set_priority": {
            "priority": 0
          }
        }
      },
      "delete": {
        "min_age": "30d",
        "actions": {
          "delete": {}
        }
      }
    }
  }
}
```

## Logstash Configuration

### Pipeline Configuration

```ruby
# logstash/pipeline/logstash.conf
input {
  beats {
    port => 5044
  }

  tcp {
    port => 5000
    codec => json_lines
  }
}

filter {
  # Parse JSON logs
  if [message] =~ /^\{/ {
    json {
      source => "message"
      target => "parsed"
    }

    mutate {
      rename => {
        "[parsed][timestamp]" => "@timestamp"
        "[parsed][level]" => "level"
        "[parsed][message]" => "log_message"
        "[parsed][service]" => "service"
        "[parsed][correlationId]" => "correlationId"
        "[parsed][requestId]" => "requestId"
        "[parsed][userId]" => "userId"
      }
    }
  }

  # Parse timestamp
  date {
    match => ["@timestamp", "ISO8601"]
    target => "@timestamp"
  }

  # Normalize log level
  mutate {
    lowercase => ["level"]
  }

  # Geoip lookup for IP addresses
  if [ip] {
    geoip {
      source => "ip"
      target => "geo"
    }
  }

  # User agent parsing
  if [userAgent] {
    useragent {
      source => "userAgent"
      target => "ua"
    }
  }

  # Remove unnecessary fields
  mutate {
    remove_field => ["host", "agent", "ecs", "input", "parsed"]
  }

  # Add environment tag
  mutate {
    add_field => {
      "environment" => "${ENVIRONMENT:production}"
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "app-logs-%{+YYYY.MM.dd}"
    document_id => "%{[@metadata][_id]}"
  }

  # Debug output (comment in production)
  # stdout {
  #   codec => rubydebug
  # }
}
```

### Multi-Pipeline Configuration

```yaml
# logstash/config/pipelines.yml
- pipeline.id: application-logs
  path.config: "/usr/share/logstash/pipeline/app.conf"
  pipeline.workers: 2
  pipeline.batch.size: 125

- pipeline.id: access-logs
  path.config: "/usr/share/logstash/pipeline/access.conf"
  pipeline.workers: 1

- pipeline.id: error-logs
  path.config: "/usr/share/logstash/pipeline/error.conf"
  pipeline.workers: 1
```

## Filebeat Configuration

```yaml
# filebeat/filebeat.yml
filebeat.inputs:
  # Application logs
  - type: log
    enabled: true
    paths:
      - /var/log/app/*.log
    json.keys_under_root: true
    json.add_error_key: true
    json.message_key: message
    fields:
      type: application
    fields_under_root: true

  # Docker container logs
  - type: container
    paths:
      - '/var/lib/docker/containers/*/*.log'
    processors:
      - add_docker_metadata:
          host: "unix:///var/run/docker.sock"

  # Kubernetes logs
  - type: kubernetes
    paths:
      - /var/log/containers/*.log
    processors:
      - add_kubernetes_metadata:
          host: ${NODE_NAME}
          matchers:
            - logs_path:
                logs_path: "/var/log/containers/"

processors:
  - add_host_metadata: ~
  - add_cloud_metadata: ~

  # Drop debug logs in production
  - drop_event:
      when:
        equals:
          level: "debug"

output.logstash:
  hosts: ["logstash:5044"]
  loadbalance: true
  bulk_max_size: 2048

# Output directly to Elasticsearch (alternative)
# output.elasticsearch:
#   hosts: ["elasticsearch:9200"]
#   index: "filebeat-%{[agent.version]}-%{+yyyy.MM.dd}"

logging.level: warning
logging.to_files: true
logging.files:
  path: /var/log/filebeat
  name: filebeat
  keepfiles: 7
```

## Kibana Configuration

### Index Pattern

```json
// Create index pattern via API
POST /api/saved_objects/index-pattern
{
  "attributes": {
    "title": "app-logs-*",
    "timeFieldName": "@timestamp"
  }
}
```

### Dashboard Query Examples

```
# KQL (Kibana Query Language)

# Find all errors
level: error

# Find errors for specific service
level: error AND service: "api-gateway"

# Find requests with high latency
http.duration > 1000

# Find 5xx errors
http.statusCode >= 500

# Find by correlation ID
correlationId: "123-456-789"

# Find by user
userId: "user-123" AND level: (error OR warn)

# Find authentication failures
message: "authentication failed" OR message: "login failed"

# Time range queries (use with time picker)
@timestamp >= "2024-01-15" AND @timestamp < "2024-01-16"
```

### Saved Search

```json
{
  "attributes": {
    "title": "Error Logs",
    "description": "All error level logs",
    "columns": ["@timestamp", "service", "message", "error.message"],
    "sort": [["@timestamp", "desc"]],
    "kibanaSavedObjectMeta": {
      "searchSourceJSON": {
        "index": "app-logs-*",
        "query": {
          "query": "level: error",
          "language": "kuery"
        },
        "filter": []
      }
    }
  }
}
```

## Kubernetes Deployment

```yaml
# elasticsearch.yaml
apiVersion: elasticsearch.k8s.elastic.co/v1
kind: Elasticsearch
metadata:
  name: logs
  namespace: logging
spec:
  version: 8.11.0
  nodeSets:
    - name: default
      count: 3
      config:
        node.store.allow_mmap: false
      volumeClaimTemplates:
        - metadata:
            name: elasticsearch-data
          spec:
            accessModes:
              - ReadWriteOnce
            resources:
              requests:
                storage: 100Gi
            storageClassName: fast-ssd
      podTemplate:
        spec:
          containers:
            - name: elasticsearch
              resources:
                requests:
                  memory: 4Gi
                  cpu: 2
                limits:
                  memory: 4Gi

---
# kibana.yaml
apiVersion: kibana.k8s.elastic.co/v1
kind: Kibana
metadata:
  name: logs
  namespace: logging
spec:
  version: 8.11.0
  count: 1
  elasticsearchRef:
    name: logs
  podTemplate:
    spec:
      containers:
        - name: kibana
          resources:
            requests:
              memory: 1Gi
              cpu: 500m
            limits:
              memory: 2Gi

---
# filebeat.yaml
apiVersion: beat.k8s.elastic.co/v1beta1
kind: Beat
metadata:
  name: filebeat
  namespace: logging
spec:
  type: filebeat
  version: 8.11.0
  elasticsearchRef:
    name: logs
  config:
    filebeat.autodiscover:
      providers:
        - type: kubernetes
          node: ${NODE_NAME}
          hints.enabled: true
          hints.default_config:
            type: container
            paths:
              - /var/log/containers/*${data.kubernetes.container.id}.log
    processors:
      - add_kubernetes_metadata:
          host: ${NODE_NAME}
  daemonSet:
    podTemplate:
      spec:
        serviceAccountName: filebeat
        automountServiceAccountToken: true
        dnsPolicy: ClusterFirstWithHostNet
        hostNetwork: true
        containers:
          - name: filebeat
            volumeMounts:
              - name: varlogcontainers
                mountPath: /var/log/containers
              - name: varlogpods
                mountPath: /var/log/pods
        volumes:
          - name: varlogcontainers
            hostPath:
              path: /var/log/containers
          - name: varlogpods
            hostPath:
              path: /var/log/pods
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                   ELK Stack Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use ILM for automatic index management                        │
│ ☐ Set appropriate shard count based on data volume              │
│ ☐ Configure proper resource limits for each component           │
│ ☐ Use dedicated hot/warm/cold nodes for large deployments       │
│ ☐ Enable security features (authentication, TLS)                │
│ ☐ Set up monitoring for the ELK stack itself                    │
│ ☐ Use index templates for consistent mappings                   │
│ ☐ Implement log retention policies                              │
│ ☐ Use Beats for lightweight log shipping                        │
│ ☐ Create useful Kibana dashboards and saved searches            │
│ ☐ Set up alerts for critical log patterns                       │
│ ☐ Regular backup of Elasticsearch indices                       │
└─────────────────────────────────────────────────────────────────┘
```
