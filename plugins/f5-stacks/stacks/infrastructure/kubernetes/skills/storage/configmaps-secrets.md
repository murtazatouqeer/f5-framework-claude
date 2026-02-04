---
name: k8s-configmaps-secrets-storage
description: Kubernetes ConfigMaps and Secrets as storage volumes
applies_to: kubernetes
---

# ConfigMaps and Secrets as Storage

## Overview

ConfigMaps and Secrets can be mounted as volumes to provide configuration files and sensitive data to containers.

## ConfigMap Volumes

### Create ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: production
data:
  # Simple key-value
  LOG_LEVEL: "info"
  MAX_CONNECTIONS: "100"

  # File content
  app.properties: |
    server.port=8080
    server.host=0.0.0.0
    database.pool.size=10

  nginx.conf: |
    worker_processes auto;
    events {
        worker_connections 1024;
    }
    http {
        server {
            listen 80;
            location / {
                proxy_pass http://backend:3000;
            }
        }
    }
```

### Mount as Volume

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
        - key: nginx.conf
          path: nginx/nginx.conf
```

### Set File Permissions

```yaml
volumes:
  - name: config
    configMap:
      name: app-config
      defaultMode: 0644  # rw-r--r--
      items:
        - key: app.properties
          path: app.properties
          mode: 0600  # Override for specific file
```

### Optional ConfigMap

```yaml
volumes:
  - name: config
    configMap:
      name: app-config
      optional: true  # Pod starts even if ConfigMap missing
```

## Secret Volumes

### Create Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
data:
  # Base64 encoded
  username: YWRtaW4=
  password: cGFzc3dvcmQxMjM=

stringData:
  # Plain text (will be encoded)
  api-key: "sk-1234567890abcdef"

  database.properties: |
    db.host=postgres.production
    db.user=admin
    db.password=secret123
```

### TLS Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTi...
  tls.key: LS0tLS1CRUdJTi...
```

### Mount Secret as Volume

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
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true

  volumes:
    - name: secrets
      secret:
        secretName: app-secrets
        defaultMode: 0400  # r--------
```

### Mount TLS Certificates

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      volumeMounts:
        - name: tls
          mountPath: /etc/nginx/ssl
          readOnly: true

  volumes:
    - name: tls
      secret:
        secretName: tls-secret
        items:
          - key: tls.crt
            path: server.crt
          - key: tls.key
            path: server.key
```

## Projected Volumes (Combined)

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
        - name: all-config
          mountPath: /etc/config
          readOnly: true

  volumes:
    - name: all-config
      projected:
        defaultMode: 0440
        sources:
          # ConfigMap
          - configMap:
              name: app-config
              items:
                - key: app.properties
                  path: app.properties

          # Secret
          - secret:
              name: app-secrets
              items:
                - key: api-key
                  path: api-key

          # Downward API
          - downwardAPI:
              items:
                - path: labels
                  fieldRef:
                    fieldPath: metadata.labels
```

## SubPath for Single Files

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
        # Mount single file without hiding directory
        - name: config
          mountPath: /app/config/settings.yaml
          subPath: settings.yaml

        - name: secrets
          mountPath: /app/.env
          subPath: .env

  volumes:
    - name: config
      configMap:
        name: app-config
    - name: secrets
      secret:
        secretName: app-secrets
```

## Immutable ConfigMaps/Secrets

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: immutable-config
immutable: true  # Cannot be updated after creation
data:
  app.properties: |
    version=1.0.0
    feature.enabled=true
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: immutable-secret
immutable: true
data:
  api-key: c2VjcmV0MTIz
```

## Binary Data

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: binary-config
binaryData:
  # Base64 encoded binary
  logo.png: iVBORw0KGgoAAAANSUhEUgAA...
  cert.der: MIICpDCCAYwCCQC...
data:
  # Regular text
  config.yaml: |
    key: value
```

## Deployment with ConfigMap/Secret

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
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
        checksum/config: "{{ sha256sum .Values.config }}"
    spec:
      containers:
        - name: api
          image: api:1.0.0

          # Environment from ConfigMap
          envFrom:
            - configMapRef:
                name: app-env

          # Environment from Secret
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: db-secrets
                  key: password

          # Volume mounts
          volumeMounts:
            - name: config
              mountPath: /etc/config
              readOnly: true
            - name: secrets
              mountPath: /etc/secrets
              readOnly: true

      volumes:
        - name: config
          configMap:
            name: app-config
        - name: secrets
          secret:
            secretName: app-secrets
            defaultMode: 0400
```

## Auto-Update on Change

ConfigMap/Secret volume updates propagate automatically (with kubelet sync period delay).

```yaml
# For immediate update, use subPath: false and readOnly: true
volumeMounts:
  - name: config
    mountPath: /etc/config
    readOnly: true
    # subPath: config.yaml  # Disables auto-update!

# Watch for changes in application
# inotify or polling recommended
```

## Commands

```bash
# Create ConfigMap from file
kubectl create configmap app-config --from-file=config.yaml

# Create ConfigMap from literal
kubectl create configmap app-config --from-literal=LOG_LEVEL=info

# Create ConfigMap from directory
kubectl create configmap app-config --from-file=./config/

# Create Secret from file
kubectl create secret generic app-secrets --from-file=password.txt

# Create Secret from literal
kubectl create secret generic app-secrets --from-literal=password=secret123

# Create TLS Secret
kubectl create secret tls tls-secret --cert=tls.crt --key=tls.key

# View ConfigMap
kubectl get configmap app-config -o yaml

# View Secret (decoded)
kubectl get secret app-secrets -o jsonpath='{.data.password}' | base64 -d

# Edit ConfigMap
kubectl edit configmap app-config

# Check mounted files
kubectl exec app -- ls -la /etc/config
kubectl exec app -- cat /etc/config/app.properties
```

## Best Practices

1. **Use Secrets for sensitive data**, never ConfigMaps
2. **Set restrictive permissions** (0400 for secrets)
3. **Use immutable** for production configs
4. **Avoid subPath** if you need auto-updates
5. **Use projected volumes** to combine sources
6. **Enable encryption at rest** for Secrets
7. **Rotate secrets regularly** with external managers
8. **Use checksums** to trigger deployment rollouts
9. **Separate environment configs** (dev, staging, prod)
10. **Consider external secret managers** (Vault, AWS Secrets Manager)
