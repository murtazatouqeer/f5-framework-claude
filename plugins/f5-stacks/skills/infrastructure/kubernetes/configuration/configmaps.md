---
name: k8s-configmaps
description: Kubernetes ConfigMaps for application configuration
applies_to: kubernetes
---

# Kubernetes ConfigMaps

## Overview

ConfigMaps decouple configuration from container images. They store non-confidential data in key-value pairs.

## Creating ConfigMaps

### From YAML

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
  labels:
    app.kubernetes.io/name: myapp
data:
  # Simple key-value pairs
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"
  CACHE_TTL: "3600"

  # Multi-line configuration files
  app.properties: |
    server.port=8080
    server.host=0.0.0.0
    database.pool.size=10
    database.timeout=30000

  logging.yaml: |
    version: 1
    formatters:
      default:
        format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    handlers:
      console:
        class: logging.StreamHandler
        formatter: default
    root:
      level: INFO
      handlers: [console]
```

### From Files (kubectl)

```bash
# From single file
kubectl create configmap app-config --from-file=app.properties

# From multiple files
kubectl create configmap app-config \
  --from-file=app.properties \
  --from-file=logging.yaml

# From directory
kubectl create configmap app-config --from-file=./config/

# With custom key name
kubectl create configmap app-config \
  --from-file=application.properties=app.properties
```

### From Literals

```bash
kubectl create configmap app-config \
  --from-literal=LOG_LEVEL=info \
  --from-literal=MAX_CONNECTIONS=100 \
  --from-literal=CACHE_TTL=3600
```

### From Env File

```bash
# .env file
# LOG_LEVEL=info
# MAX_CONNECTIONS=100

kubectl create configmap app-config --from-env-file=.env
```

## Using ConfigMaps

### Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: myapp:1.0.0

      # Single key
      env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LOG_LEVEL

        - name: MAX_CONN
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: MAX_CONNECTIONS
              optional: true  # Pod starts even if key missing
```

### All Keys as Environment

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: myapp:1.0.0

      # All keys from ConfigMap
      envFrom:
        - configMapRef:
            name: app-config
            optional: false

        # With prefix
        - configMapRef:
            name: app-config
            prefix: APP_
```

### Volume Mount

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true

  volumes:
    - name: config
      configMap:
        name: app-config
```

### Mount Specific Keys

```yaml
volumes:
  - name: config
    configMap:
      name: app-config
      items:
        - key: app.properties
          path: application.properties
        - key: logging.yaml
          path: log-config.yaml
```

### Mount Single File (SubPath)

```yaml
volumeMounts:
  - name: config
    mountPath: /app/config/settings.yaml
    subPath: settings.yaml
    readOnly: true
```

### Set File Permissions

```yaml
volumes:
  - name: config
    configMap:
      name: app-config
      defaultMode: 0644
      items:
        - key: script.sh
          path: script.sh
          mode: 0755  # Executable
```

## Production ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: myapp
  annotations:
    description: "API service configuration"
data:
  # Application settings
  APP_NAME: "My API"
  APP_ENV: "production"
  LOG_LEVEL: "warn"
  LOG_FORMAT: "json"

  # Server settings
  SERVER_PORT: "3000"
  SERVER_HOST: "0.0.0.0"
  SERVER_TIMEOUT: "30000"

  # Database settings (non-sensitive)
  DB_HOST: "postgres.production.svc.cluster.local"
  DB_PORT: "5432"
  DB_NAME: "myapp"
  DB_POOL_SIZE: "20"

  # Cache settings
  REDIS_HOST: "redis.production.svc.cluster.local"
  REDIS_PORT: "6379"
  CACHE_TTL: "3600"

  # Feature flags
  FEATURE_NEW_UI: "true"
  FEATURE_ANALYTICS: "true"

  # Configuration file
  config.yaml: |
    server:
      port: 3000
      host: 0.0.0.0
      timeout: 30s

    database:
      host: postgres.production.svc.cluster.local
      port: 5432
      name: myapp
      pool:
        size: 20
        timeout: 10s

    cache:
      host: redis.production.svc.cluster.local
      port: 6379
      ttl: 3600

    logging:
      level: warn
      format: json
```

## Deployment with ConfigMap

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
      annotations:
        # Trigger rollout on config change
        checksum/config: "abc123"
    spec:
      containers:
        - name: api
          image: api:1.0.0

          # Environment from ConfigMap
          envFrom:
            - configMapRef:
                name: api-config

          # Specific environment variable
          env:
            - name: CONFIG_PATH
              value: /etc/config/config.yaml

          # Volume mount
          volumeMounts:
            - name: config
              mountPath: /etc/config
              readOnly: true

      volumes:
        - name: config
          configMap:
            name: api-config
            items:
              - key: config.yaml
                path: config.yaml
```

## Immutable ConfigMaps

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: immutable-config
immutable: true  # Cannot be updated
data:
  VERSION: "1.0.0"
  BUILD_DATE: "2024-01-15"
```

Benefits of immutable ConfigMaps:
- Protects from accidental updates
- Improves cluster performance (no watches)
- To update: create new ConfigMap, update Pod reference

## Binary Data

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: binary-config
binaryData:
  # Base64 encoded binary files
  logo.png: iVBORw0KGgoAAAANSUhEUgAA...
  favicon.ico: AAABAA...
data:
  # Regular text data
  config.json: |
    {"key": "value"}
```

## ConfigMap Updates

ConfigMaps mounted as volumes update automatically (kubelet sync period ~1 minute).

```yaml
# Avoid subPath for auto-updates
volumeMounts:
  - name: config
    mountPath: /etc/config
    # subPath: config.yaml  # Disables auto-update!
```

For environment variables, Pod restart is required.

## Commands

```bash
# List ConfigMaps
kubectl get configmaps
kubectl get cm

# Get ConfigMap details
kubectl describe cm app-config

# View ConfigMap data
kubectl get cm app-config -o yaml
kubectl get cm app-config -o jsonpath='{.data.LOG_LEVEL}'

# Edit ConfigMap
kubectl edit cm app-config

# Replace ConfigMap
kubectl replace -f configmap.yaml

# Delete ConfigMap
kubectl delete cm app-config

# Export ConfigMap
kubectl get cm app-config -o yaml > configmap-backup.yaml

# Dry run (generate YAML)
kubectl create configmap app-config \
  --from-file=config.yaml \
  --dry-run=client -o yaml
```

## Best Practices

1. **Use namespaces** to scope ConfigMaps
2. **Use descriptive names** matching application
3. **Add labels** for organization and selection
4. **Separate environments** (dev, staging, prod)
5. **Use immutable** for production configs
6. **Version ConfigMaps** for rollback capability
7. **Don't store secrets** - use Secrets instead
8. **Monitor ConfigMap size** (1MB limit)
9. **Use checksums** to trigger Deployment rollouts
10. **Document configuration** with annotations
