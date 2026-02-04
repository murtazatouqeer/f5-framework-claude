---
name: k8s-deployments
description: Kubernetes Deployments for managing stateless applications
applies_to: kubernetes
---

# Kubernetes Deployments

## Overview

Deployments provide declarative updates for Pods and ReplicaSets. They handle scaling, rolling updates, and rollbacks automatically.

## Basic Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
  labels:
    app: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: myregistry/api:1.0.0
          ports:
            - containerPort: 3000
```

## Production Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/instance: api-production
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/component: backend
    app.kubernetes.io/part-of: myapp
    app.kubernetes.io/managed-by: helm
  annotations:
    kubernetes.io/change-cause: "Deployed version 1.0.0"
spec:
  replicas: 3
  revisionHistoryLimit: 5
  progressDeadlineSeconds: 600

  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1

  selector:
    matchLabels:
      app.kubernetes.io/name: api
      app.kubernetes.io/instance: api-production

  template:
    metadata:
      labels:
        app.kubernetes.io/name: api
        app.kubernetes.io/instance: api-production
        app.kubernetes.io/version: "1.0.0"
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "3000"
        prometheus.io/path: "/metrics"
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000

      serviceAccountName: api-service-account
      automountServiceAccountToken: false

      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app.kubernetes.io/name: api
                topologyKey: kubernetes.io/hostname

      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: api

      containers:
        - name: api
          image: myregistry/api:1.0.0
          imagePullPolicy: IfNotPresent

          ports:
            - containerPort: 3000
              name: http
              protocol: TCP

          env:
            - name: NODE_ENV
              value: "production"

          envFrom:
            - configMapRef:
                name: api-config
            - secretRef:
                name: api-secrets

          resources:
            requests:
              cpu: "100m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"

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

          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL

          volumeMounts:
            - name: tmp
              mountPath: /tmp

      volumes:
        - name: tmp
          emptyDir: {}

      terminationGracePeriodSeconds: 30

      imagePullSecrets:
        - name: registry-credentials
```

## Deployment Strategies

### Rolling Update (Default)

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 25%   # Max pods unavailable during update
      maxSurge: 25%         # Max pods over desired count
```

### Recreate (Downtime)

```yaml
spec:
  strategy:
    type: Recreate  # Delete all, then create new
```

## Blue-Green Deployment

```yaml
# Blue Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-blue
  labels:
    app: api
    version: blue
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
      version: blue
  template:
    metadata:
      labels:
        app: api
        version: blue
    spec:
      containers:
        - name: api
          image: myregistry/api:1.0.0

---
# Green Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-green
  labels:
    app: api
    version: green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
      version: green
  template:
    metadata:
      labels:
        app: api
        version: green
    spec:
      containers:
        - name: api
          image: myregistry/api:2.0.0

---
# Service - switch by changing selector
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
    version: blue  # Change to 'green' for switch
  ports:
    - port: 80
      targetPort: 3000
```

## Canary Deployment

```yaml
# Stable Deployment (90% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-stable
spec:
  replicas: 9
  selector:
    matchLabels:
      app: api
      track: stable
  template:
    metadata:
      labels:
        app: api
        track: stable
    spec:
      containers:
        - name: api
          image: myregistry/api:1.0.0

---
# Canary Deployment (10% traffic)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-canary
spec:
  replicas: 1
  selector:
    matchLabels:
      app: api
      track: canary
  template:
    metadata:
      labels:
        app: api
        track: canary
    spec:
      containers:
        - name: api
          image: myregistry/api:2.0.0

---
# Service routes to both
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api  # Matches both stable and canary
  ports:
    - port: 80
      targetPort: 3000
```

## Deployment Commands

```bash
# Create deployment
kubectl create deployment nginx --image=nginx

# Apply deployment
kubectl apply -f deployment.yaml

# Scale deployment
kubectl scale deployment api --replicas=5

# Update image
kubectl set image deployment/api api=myregistry/api:2.0.0

# Rollout status
kubectl rollout status deployment/api

# Rollout history
kubectl rollout history deployment/api

# Rollout undo
kubectl rollout undo deployment/api
kubectl rollout undo deployment/api --to-revision=2

# Pause/resume rollout
kubectl rollout pause deployment/api
kubectl rollout resume deployment/api

# Restart deployment
kubectl rollout restart deployment/api

# Delete deployment
kubectl delete deployment api
```

## ConfigMap and Secret Reload

```yaml
# Force pod restart on config change
spec:
  template:
    metadata:
      annotations:
        # Change this to trigger rollout
        checksum/config: {{ sha256sum .Values.config }}
```

## Pod Anti-Affinity for HA

```yaml
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          # Prefer different nodes
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: api
                topologyKey: kubernetes.io/hostname

          # Require different zones
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app: api
              topologyKey: topology.kubernetes.io/zone
```

## Topology Spread Constraints

```yaml
spec:
  template:
    spec:
      topologySpreadConstraints:
        # Spread across zones
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: api

        # Spread across nodes
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: api
```
