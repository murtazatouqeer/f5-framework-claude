---
name: k8s-pods
description: Kubernetes Pods - smallest deployable units
applies_to: kubernetes
---

# Kubernetes Pods

## Overview

A Pod is the smallest deployable unit in Kubernetes. It represents a single instance of a running process and can contain one or more containers.

## Basic Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  namespace: default
  labels:
    app: nginx
    environment: production
spec:
  containers:
    - name: nginx
      image: nginx:1.25
      ports:
        - containerPort: 80
          name: http
```

## Production Pod with All Features

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/instance: api-production
    app.kubernetes.io/version: "1.0.0"
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "3000"
spec:
  # Security context for pod
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault

  # Service account
  serviceAccountName: api-service-account
  automountServiceAccountToken: false

  # DNS configuration
  dnsPolicy: ClusterFirst
  dnsConfig:
    options:
      - name: ndots
        value: "2"

  # Init containers
  initContainers:
    - name: init-db
      image: busybox:1.36
      command: ['sh', '-c', 'until nc -z db 5432; do sleep 2; done']

  # Main containers
  containers:
    - name: api
      image: myregistry/api:1.0.0
      imagePullPolicy: IfNotPresent

      # Ports
      ports:
        - containerPort: 3000
          name: http
          protocol: TCP

      # Environment variables
      env:
        - name: NODE_ENV
          value: "production"
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: database-password

      # Environment from ConfigMap/Secret
      envFrom:
        - configMapRef:
            name: api-config
        - secretRef:
            name: api-secrets

      # Resources
      resources:
        requests:
          cpu: "100m"
          memory: "256Mi"
        limits:
          cpu: "1000m"
          memory: "1Gi"

      # Probes
      startupProbe:
        httpGet:
          path: /health
          port: http
        failureThreshold: 30
        periodSeconds: 10

      livenessProbe:
        httpGet:
          path: /health
          port: http
        initialDelaySeconds: 0
        periodSeconds: 15
        timeoutSeconds: 5
        failureThreshold: 3

      readinessProbe:
        httpGet:
          path: /ready
          port: http
        initialDelaySeconds: 0
        periodSeconds: 5
        timeoutSeconds: 3
        failureThreshold: 3

      # Lifecycle hooks
      lifecycle:
        postStart:
          exec:
            command: ["/bin/sh", "-c", "echo 'Pod started'"]
        preStop:
          exec:
            command: ["/bin/sh", "-c", "sleep 10"]

      # Security context for container
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL

      # Volume mounts
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: config
          mountPath: /app/config
          readOnly: true

  # Volumes
  volumes:
    - name: tmp
      emptyDir: {}
    - name: config
      configMap:
        name: api-config

  # Termination
  terminationGracePeriodSeconds: 30

  # Image pull secrets
  imagePullSecrets:
    - name: registry-credentials

  # Node selection
  nodeSelector:
    kubernetes.io/os: linux

  # Tolerations
  tolerations:
    - key: "dedicated"
      operator: "Equal"
      value: "api"
      effect: "NoSchedule"

  # Affinity
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: node-type
                operator: In
                values:
                  - compute

  # Restart policy
  restartPolicy: Always
```

## Multi-Container Patterns

### Sidecar Pattern

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
      ports:
        - containerPort: 8080
      volumeMounts:
        - name: logs
          mountPath: /var/log/app

    # Sidecar for log shipping
    - name: log-shipper
      image: fluent/fluent-bit
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          readOnly: true

  volumes:
    - name: logs
      emptyDir: {}
```

### Ambassador Pattern

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-ambassador
spec:
  containers:
    # Main application
    - name: app
      image: myapp:1.0.0
      env:
        - name: DATABASE_URL
          value: "localhost:5432"

    # Ambassador proxy to database
    - name: db-proxy
      image: cloudsql-proxy
      args:
        - "-instances=project:region:instance=tcp:5432"
```

### Adapter Pattern

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-adapter
spec:
  containers:
    # Main application (non-standard metrics)
    - name: app
      image: legacy-app:1.0.0
      ports:
        - containerPort: 8080

    # Adapter for Prometheus metrics
    - name: metrics-adapter
      image: metrics-adapter:1.0.0
      ports:
        - containerPort: 9090
          name: metrics
```

## Init Containers

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-init
spec:
  initContainers:
    # Wait for database
    - name: wait-for-db
      image: busybox:1.36
      command: ['sh', '-c', 'until nc -z db-service 5432; do sleep 2; done']

    # Run migrations
    - name: run-migrations
      image: myapp:1.0.0
      command: ['npm', 'run', 'migrate']
      env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secrets
              key: url

    # Download config
    - name: download-config
      image: curlimages/curl
      command: ['sh', '-c', 'curl -o /config/app.json $CONFIG_URL']
      volumeMounts:
        - name: config
          mountPath: /config

  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: config
          mountPath: /app/config

  volumes:
    - name: config
      emptyDir: {}
```

## Probes

### HTTP Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8080
    httpHeaders:
      - name: Custom-Header
        value: probe
  initialDelaySeconds: 15
  periodSeconds: 20
  timeoutSeconds: 5
  failureThreshold: 3
```

### TCP Probe

```yaml
readinessProbe:
  tcpSocket:
    port: 5432
  initialDelaySeconds: 5
  periodSeconds: 10
```

### Exec Probe

```yaml
livenessProbe:
  exec:
    command:
      - cat
      - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

### gRPC Probe

```yaml
livenessProbe:
  grpc:
    port: 50051
    service: health
  initialDelaySeconds: 5
  periodSeconds: 10
```

## Resource Management

```yaml
resources:
  requests:
    cpu: "100m"        # 0.1 CPU cores
    memory: "256Mi"    # 256 MiB
    ephemeral-storage: "1Gi"
  limits:
    cpu: "1000m"       # 1 CPU core
    memory: "1Gi"      # 1 GiB
    ephemeral-storage: "2Gi"
```

## Pod Commands

```bash
# Create pod
kubectl run nginx --image=nginx

# List pods
kubectl get pods
kubectl get pods -o wide

# Describe pod
kubectl describe pod nginx

# Pod logs
kubectl logs nginx
kubectl logs nginx -f
kubectl logs nginx --previous

# Execute in pod
kubectl exec -it nginx -- /bin/bash

# Port forward
kubectl port-forward nginx 8080:80

# Copy files
kubectl cp ./file nginx:/path/file

# Delete pod
kubectl delete pod nginx
```
