---
name: k8s-logging
description: Kubernetes logging strategies and implementations
applies_to: kubernetes
---

# Kubernetes Logging

## Overview

Kubernetes logging involves collecting, aggregating, and analyzing logs from containers, nodes, and cluster components.

## Application Logging

### Logging to stdout/stderr

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      # Application should log to stdout/stderr
      # kubectl logs will capture these
```

### Structured Logging

```json
// Application should output JSON logs
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info",
  "message": "Request processed",
  "service": "api",
  "request_id": "abc-123",
  "duration_ms": 45,
  "status_code": 200
}
```

## kubectl logs

```bash
# View logs
kubectl logs pod-name
kubectl logs pod-name -c container-name

# Follow logs
kubectl logs -f pod-name

# Previous container (after restart)
kubectl logs pod-name --previous

# Tail last N lines
kubectl logs pod-name --tail=100

# Since duration
kubectl logs pod-name --since=1h
kubectl logs pod-name --since-time="2024-01-15T10:00:00Z"

# All containers in pod
kubectl logs pod-name --all-containers=true

# Logs from deployment
kubectl logs deployment/api

# Logs from multiple pods
kubectl logs -l app=api

# Timestamps
kubectl logs pod-name --timestamps=true
```

## Sidecar Logging Pattern

### Sidecar for Log Processing

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-sidecar
spec:
  containers:
    # Main application
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: logs
          mountPath: /var/log/app

    # Sidecar for log shipping
    - name: fluentbit
      image: fluent/fluent-bit:2.2
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true
        - name: fluentbit-config
          mountPath: /fluent-bit/etc/

  volumes:
    - name: logs
      emptyDir: {}
    - name: fluentbit-config
      configMap:
        name: fluentbit-config
```

### Fluent Bit ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentbit-config
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Path              /var/log/app/*.log
        Parser            json
        Tag               app.*
        Refresh_Interval  5

    [OUTPUT]
        Name              es
        Match             *
        Host              elasticsearch
        Port              9200
        Index             app-logs
        Type              _doc

  parsers.conf: |
    [PARSER]
        Name        json
        Format      json
        Time_Key    timestamp
        Time_Format %Y-%m-%dT%H:%M:%S.%LZ
```

## DaemonSet Logging

### Fluent Bit DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit
      tolerations:
        - operator: Exists

      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:2.2
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi

          volumeMounts:
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: varlibdockercontainers
              mountPath: /var/lib/docker/containers
              readOnly: true
            - name: config
              mountPath: /fluent-bit/etc/

      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: varlibdockercontainers
          hostPath:
            path: /var/lib/docker/containers
        - name: config
          configMap:
            name: fluent-bit-config
```

### Node Log Collection Config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf

    [INPUT]
        Name              tail
        Tag               kube.*
        Path              /var/log/containers/*.log
        Parser            docker
        DB                /var/log/flb_kube.db
        Mem_Buf_Limit     50MB
        Skip_Long_Lines   On
        Refresh_Interval  10

    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        K8S-Logging.Parser  On
        K8S-Logging.Exclude On

    [OUTPUT]
        Name              es
        Match             *
        Host              elasticsearch.logging.svc.cluster.local
        Port              9200
        Index             kubernetes-logs
        Logstash_Format   On
        Retry_Limit       False

  parsers.conf: |
    [PARSER]
        Name        docker
        Format      json
        Time_Key    time
        Time_Format %Y-%m-%dT%H:%M:%S.%L
        Time_Keep   On

    [PARSER]
        Name        json
        Format      json
```

## Loki Stack

### Loki Installation

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace logging \
  --create-namespace \
  --set promtail.enabled=true \
  --set grafana.enabled=true
```

### Promtail Config

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: promtail-config
  namespace: logging
data:
  promtail.yaml: |
    server:
      http_listen_port: 9080
      grpc_listen_port: 0

    positions:
      filename: /tmp/positions.yaml

    clients:
      - url: http://loki:3100/loki/api/v1/push

    scrape_configs:
      - job_name: kubernetes-pods
        kubernetes_sd_configs:
          - role: pod
        pipeline_stages:
          - cri: {}
          - json:
              expressions:
                level: level
                msg: message
          - labels:
              level:
        relabel_configs:
          - source_labels:
              - __meta_kubernetes_pod_label_app
            target_label: app
          - source_labels:
              - __meta_kubernetes_namespace
            target_label: namespace
          - source_labels:
              - __meta_kubernetes_pod_name
            target_label: pod
```

## EFK Stack (Elasticsearch, Fluentd, Kibana)

### Elasticsearch StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: elasticsearch
  namespace: logging
spec:
  serviceName: elasticsearch
  replicas: 3
  selector:
    matchLabels:
      app: elasticsearch
  template:
    metadata:
      labels:
        app: elasticsearch
    spec:
      containers:
        - name: elasticsearch
          image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
          ports:
            - containerPort: 9200
            - containerPort: 9300
          env:
            - name: discovery.type
              value: single-node
            - name: ES_JAVA_OPTS
              value: "-Xms512m -Xmx512m"
          volumeMounts:
            - name: data
              mountPath: /usr/share/elasticsearch/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 50Gi
```

## Pod Annotations for Logging

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
  annotations:
    # Fluent Bit annotations
    fluentbit.io/parser: json
    fluentbit.io/exclude: "false"

    # Promtail/Loki annotations
    promtail.io/scrape: "true"

    # Fluentd annotations
    fluentd.org/parser: json
spec:
  containers:
    - name: app
      image: myapp:1.0.0
```

## Log Rotation

### Container Runtime Log Rotation

```yaml
# kubelet config for log rotation
apiVersion: kubelet.config.k8s.io/v1beta1
kind: KubeletConfiguration
containerLogMaxSize: "50Mi"
containerLogMaxFiles: 5
```

### Application Log Rotation

```yaml
# For applications writing to files
apiVersion: v1
kind: ConfigMap
metadata:
  name: logrotate-config
data:
  app: |
    /var/log/app/*.log {
        daily
        rotate 7
        compress
        delaycompress
        missingok
        notifempty
        create 0640 app app
    }
```

## Logging Best Practices

### Application Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: logging-config
data:
  LOG_LEVEL: "info"
  LOG_FORMAT: "json"
  LOG_OUTPUT: "stdout"
```

### Structured Log Format

```yaml
# Recommended log fields
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "info|warn|error|debug",
  "service": "service-name",
  "version": "1.0.0",
  "environment": "production",
  "trace_id": "abc-123-xyz",
  "span_id": "def-456",
  "message": "Human readable message",
  "error": {
    "type": "ValidationError",
    "message": "Invalid input",
    "stack": "..."
  },
  "context": {
    "user_id": "user-123",
    "request_id": "req-456"
  }
}
```

## Commands

```bash
# View pod logs
kubectl logs <pod> -n <namespace>

# Stream logs
kubectl logs -f <pod>

# Logs from all pods with label
kubectl logs -l app=api --all-containers

# Stern (better log tailing)
stern api -n production

# Logs from previous container
kubectl logs <pod> --previous

# Export logs
kubectl logs <pod> > pod-logs.txt
```

## Best Practices

1. **Log to stdout/stderr** - Let Kubernetes handle collection
2. **Use structured logging** - JSON format with consistent fields
3. **Include correlation IDs** - trace_id, request_id
4. **Set appropriate log levels** - Don't log DEBUG in production
5. **Use DaemonSet collectors** - Fluent Bit, Promtail
6. **Configure log rotation** - Prevent disk exhaustion
7. **Add Kubernetes metadata** - namespace, pod, labels
8. **Centralize logs** - Elasticsearch, Loki, CloudWatch
9. **Set up log-based alerts** - Error rate spikes
10. **Secure log access** - RBAC for log viewing
