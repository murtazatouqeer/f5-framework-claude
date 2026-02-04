---
name: k8s-statefulsets
description: Kubernetes StatefulSets for stateful applications
applies_to: kubernetes
---

# Kubernetes StatefulSets

## Overview

StatefulSets manage stateful applications with:
- Stable, unique network identifiers
- Stable, persistent storage
- Ordered, graceful deployment and scaling
- Ordered, automated rolling updates

## Basic StatefulSet

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: production
spec:
  serviceName: postgres-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
          ports:
            - containerPort: 5432
              name: postgres
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: password
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
```

## Production StatefulSet (PostgreSQL HA)

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: production
  labels:
    app.kubernetes.io/name: postgres
    app.kubernetes.io/instance: postgres-production
spec:
  serviceName: postgres-headless
  replicas: 3
  podManagementPolicy: OrderedReady  # or Parallel
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0  # For canary updates

  selector:
    matchLabels:
      app.kubernetes.io/name: postgres
      app.kubernetes.io/instance: postgres-production

  template:
    metadata:
      labels:
        app.kubernetes.io/name: postgres
        app.kubernetes.io/instance: postgres-production
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9187"
    spec:
      securityContext:
        runAsUser: 999
        runAsGroup: 999
        fsGroup: 999

      serviceAccountName: postgres

      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            - labelSelector:
                matchLabels:
                  app.kubernetes.io/name: postgres
              topologyKey: kubernetes.io/hostname

      initContainers:
        - name: init-permissions
          image: busybox:1.36
          command: ['sh', '-c', 'chown -R 999:999 /var/lib/postgresql/data']
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
          securityContext:
            runAsUser: 0

      containers:
        - name: postgres
          image: postgres:16-alpine
          imagePullPolicy: IfNotPresent

          ports:
            - containerPort: 5432
              name: postgres

          env:
            - name: POSTGRES_USER
              value: "postgres"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: password
            - name: POSTGRES_DB
              value: "app"
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name

          resources:
            requests:
              cpu: "500m"
              memory: "1Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"

          livenessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - postgres
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 6

          readinessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - postgres
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3

          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data
            - name: config
              mountPath: /etc/postgresql/conf.d

        # Metrics exporter sidecar
        - name: metrics
          image: prometheuscommunity/postgres-exporter:v0.15.0
          ports:
            - containerPort: 9187
              name: metrics
          env:
            - name: DATA_SOURCE_NAME
              value: "postgresql://postgres:$(POSTGRES_PASSWORD)@localhost:5432/postgres?sslmode=disable"
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: password
          resources:
            requests:
              cpu: "50m"
              memory: "64Mi"
            limits:
              cpu: "100m"
              memory: "128Mi"

      volumes:
        - name: config
          configMap:
            name: postgres-config

      terminationGracePeriodSeconds: 120

  volumeClaimTemplates:
    - metadata:
        name: data
        labels:
          app.kubernetes.io/name: postgres
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
```

## Headless Service

```yaml
# Required for StatefulSet DNS
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: production
  labels:
    app.kubernetes.io/name: postgres
spec:
  type: ClusterIP
  clusterIP: None  # Headless
  selector:
    app.kubernetes.io/name: postgres
  ports:
    - port: 5432
      targetPort: postgres
      name: postgres

---
# Client service (load balanced)
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: production
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: postgres
  ports:
    - port: 5432
      targetPort: postgres
```

## DNS Names

```
# Individual pods
postgres-0.postgres-headless.production.svc.cluster.local
postgres-1.postgres-headless.production.svc.cluster.local
postgres-2.postgres-headless.production.svc.cluster.local

# Headless service (returns all pod IPs)
postgres-headless.production.svc.cluster.local

# Client service (load balanced)
postgres.production.svc.cluster.local
```

## Update Strategies

### Rolling Update

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0  # Update all pods
```

### Partitioned Update (Canary)

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 2  # Only update pods with ordinal >= 2
```

### OnDelete

```yaml
spec:
  updateStrategy:
    type: OnDelete  # Manual deletion required
```

## Pod Management Policy

```yaml
spec:
  # OrderedReady (default) - Sequential creation/deletion
  podManagementPolicy: OrderedReady

  # Parallel - All pods created/deleted simultaneously
  podManagementPolicy: Parallel
```

## StatefulSet Commands

```bash
# Create StatefulSet
kubectl apply -f statefulset.yaml

# Scale StatefulSet
kubectl scale statefulset postgres --replicas=5

# Patch update strategy
kubectl patch statefulset postgres -p '{"spec":{"updateStrategy":{"type":"RollingUpdate","rollingUpdate":{"partition":2}}}}'

# Rollout status
kubectl rollout status statefulset/postgres

# Delete StatefulSet (keeps PVCs)
kubectl delete statefulset postgres

# Delete with PVCs
kubectl delete statefulset postgres --cascade=orphan
kubectl delete pvc -l app=postgres
```

## Redis Cluster Example

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis
spec:
  serviceName: redis-headless
  replicas: 6
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          command:
            - redis-server
            - /etc/redis/redis.conf
            - --cluster-enabled
            - "yes"
            - --cluster-config-file
            - /data/nodes.conf
          ports:
            - containerPort: 6379
              name: client
            - containerPort: 16379
              name: gossip
          volumeMounts:
            - name: data
              mountPath: /data
            - name: config
              mountPath: /etc/redis
      volumes:
        - name: config
          configMap:
            name: redis-config
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        resources:
          requests:
            storage: 10Gi
```

## Best Practices

1. **Always use headless service** for stable network identity
2. **Set appropriate termination grace period** for graceful shutdown
3. **Use pod anti-affinity** for high availability
4. **Configure proper storage class** with appropriate performance
5. **Implement health checks** specific to your database
6. **Use init containers** for data initialization
7. **Consider backup solutions** for persistent data
