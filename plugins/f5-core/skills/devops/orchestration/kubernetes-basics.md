---
name: kubernetes-basics
description: Kubernetes fundamentals and core concepts
category: devops/orchestration
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Kubernetes Basics

## Overview

Kubernetes (K8s) is an open-source container orchestration platform that automates
deployment, scaling, and management of containerized applications.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Kubernetes Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Control Plane                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │   │
│  │  │   API    │ │  etcd    │ │Scheduler │ │Controller│   │   │
│  │  │  Server  │ │          │ │          │ │ Manager  │   │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  Worker Nodes                                                    │
│  ┌─────────────────┐  ┌─────────────────┐                       │
│  │  ┌───────────┐  │  │  ┌───────────┐  │                       │
│  │  │  kubelet  │  │  │  │  kubelet  │  │                       │
│  │  └───────────┘  │  │  └───────────┘  │                       │
│  │  ┌───────────┐  │  │  ┌───────────┐  │                       │
│  │  │kube-proxy │  │  │  │kube-proxy │  │                       │
│  │  └───────────┘  │  │  └───────────┘  │                       │
│  │  ┌───────────┐  │  │  ┌───────────┐  │                       │
│  │  │ Container │  │  │  │ Container │  │                       │
│  │  │  Runtime  │  │  │  │  Runtime  │  │                       │
│  │  └───────────┘  │  │  └───────────┘  │                       │
│  │  ┌─────┐┌─────┐ │  │  ┌─────┐┌─────┐ │                       │
│  │  │ Pod ││ Pod │ │  │  │ Pod ││ Pod │ │                       │
│  │  └─────┘└─────┘ │  │  └─────┘└─────┘ │                       │
│  └─────────────────┘  └─────────────────┘                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Core Concepts

### Pod

The smallest deployable unit in Kubernetes.

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-app
  labels:
    app: my-app
    environment: production
spec:
  containers:
    - name: app
      image: my-app:1.0.0
      ports:
        - containerPort: 3000
      resources:
        requests:
          memory: "128Mi"
          cpu: "100m"
        limits:
          memory: "256Mi"
          cpu: "500m"
      env:
        - name: NODE_ENV
          value: "production"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
      livenessProbe:
        httpGet:
          path: /health
          port: 3000
        initialDelaySeconds: 10
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /ready
          port: 3000
        initialDelaySeconds: 5
        periodSeconds: 5
```

### Multi-Container Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi-container
spec:
  containers:
    # Main application
    - name: app
      image: my-app:1.0.0
      ports:
        - containerPort: 3000
      volumeMounts:
        - name: shared-data
          mountPath: /data

    # Sidecar for logging
    - name: log-shipper
      image: fluent-bit:latest
      volumeMounts:
        - name: shared-data
          mountPath: /data

  initContainers:
    # Run before main containers
    - name: init-db
      image: busybox
      command: ['sh', '-c', 'until nc -z db 5432; do sleep 1; done']

  volumes:
    - name: shared-data
      emptyDir: {}
```

### Deployment

Manages ReplicaSets and provides declarative updates.

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: my-app
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "3000"
    spec:
      serviceAccountName: my-app
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
        - name: app
          image: my-app:1.0.0
          imagePullPolicy: Always
          ports:
            - containerPort: 3000
              name: http
          resources:
            requests:
              memory: "128Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
          envFrom:
            - configMapRef:
                name: app-config
            - secretRef:
                name: app-secrets
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 10
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 10"]
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchExpressions:
                    - key: app
                      operator: In
                      values:
                        - my-app
                topologyKey: kubernetes.io/hostname
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: my-app
```

### Service

Exposes Pods and enables network access.

```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: my-app
  labels:
    app: my-app
spec:
  type: ClusterIP
  selector:
    app: my-app
  ports:
    - name: http
      port: 80
      targetPort: 3000
      protocol: TCP

---
# NodePort Service
apiVersion: v1
kind: Service
metadata:
  name: my-app-nodeport
spec:
  type: NodePort
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 3000
      nodePort: 30080

---
# LoadBalancer Service
apiVersion: v1
kind: Service
metadata:
  name: my-app-lb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
spec:
  type: LoadBalancer
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 3000

---
# Headless Service (for StatefulSets)
apiVersion: v1
kind: Service
metadata:
  name: my-app-headless
spec:
  type: ClusterIP
  clusterIP: None
  selector:
    app: my-app
  ports:
    - port: 3000
```

### ConfigMap

Store non-sensitive configuration data.

```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  # Simple key-value
  NODE_ENV: "production"
  LOG_LEVEL: "info"

  # File-like keys
  config.json: |
    {
      "apiUrl": "https://api.example.com",
      "timeout": 30000,
      "features": {
        "caching": true,
        "logging": true
      }
    }

  nginx.conf: |
    server {
      listen 80;
      location / {
        proxy_pass http://localhost:3000;
      }
    }
```

```yaml
# Using ConfigMap
spec:
  containers:
    - name: app
      # As environment variables
      envFrom:
        - configMapRef:
            name: app-config

      # Individual key
      env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef:
              name: app-config
              key: LOG_LEVEL

      # As volume
      volumeMounts:
        - name: config
          mountPath: /app/config

  volumes:
    - name: config
      configMap:
        name: app-config
        items:
          - key: config.json
            path: config.json
```

### Secret

Store sensitive data.

```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  # Base64 encoded
  database-url: cG9zdGdyZXM6Ly91c2VyOnBhc3NAaG9zdC9kYg==
  api-key: c2VjcmV0LWFwaS1rZXk=

---
# String data (automatically encoded)
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets-string
type: Opaque
stringData:
  database-url: "postgres://user:pass@host/db"
  api-key: "secret-api-key"

---
# Docker registry secret
apiVersion: v1
kind: Secret
metadata:
  name: registry-credentials
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: <base64-encoded-docker-config>

---
# TLS Secret
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: <base64-encoded-cert>
  tls.key: <base64-encoded-key>
```

### Ingress

HTTP/HTTPS routing to services.

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
spec:
  tls:
    - hosts:
        - api.example.com
        - app.example.com
      secretName: example-tls
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api-service
                port:
                  number: 80

    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: frontend-service
                port:
                  number: 80
```

### Namespace

Logical isolation of resources.

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    env: production
    team: platform

---
# Resource Quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: 20Gi
    limits.cpu: "20"
    limits.memory: 40Gi
    pods: "50"
    services: "20"

---
# Limit Range
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
spec:
  limits:
    - default:
        cpu: "500m"
        memory: "256Mi"
      defaultRequest:
        cpu: "100m"
        memory: "128Mi"
      type: Container
```

### StatefulSet

For stateful applications.

```yaml
# statefulset.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
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
          image: postgres:15
          ports:
            - containerPort: 5432
              name: postgres
          env:
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: postgres-secrets
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
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
            storage: 10Gi
```

### PersistentVolume

Storage abstraction.

```yaml
# persistent-volume.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-fast-ssd
spec:
  capacity:
    storage: 100Gi
  volumeMode: Filesystem
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  storageClassName: fast-ssd
  csi:
    driver: ebs.csi.aws.com
    volumeHandle: vol-0abc123

---
# Storage Class
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  fsType: ext4
  encrypted: "true"
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer

---
# Persistent Volume Claim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-data
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: fast-ssd
  resources:
    requests:
      storage: 10Gi
```

### HorizontalPodAutoscaler

Automatic scaling based on metrics.

```yaml
# hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
    - type: Pods
      pods:
        metric:
          name: requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```

## Essential Commands

```bash
# Cluster Info
kubectl cluster-info
kubectl get nodes
kubectl get namespaces

# Create/Apply Resources
kubectl apply -f deployment.yaml
kubectl apply -f . --recursive
kubectl create namespace staging

# Get Resources
kubectl get pods
kubectl get pods -o wide
kubectl get all -n production
kubectl get pods -l app=my-app

# Describe Resources
kubectl describe pod my-app-xyz
kubectl describe deployment my-app
kubectl describe node worker-1

# Logs
kubectl logs my-app-xyz
kubectl logs -f my-app-xyz           # Follow
kubectl logs my-app-xyz -c sidecar   # Specific container
kubectl logs -l app=my-app --all-containers

# Exec into Pod
kubectl exec -it my-app-xyz -- /bin/sh
kubectl exec my-app-xyz -- cat /app/config.json

# Port Forward
kubectl port-forward pod/my-app-xyz 8080:3000
kubectl port-forward svc/my-app 8080:80

# Scaling
kubectl scale deployment my-app --replicas=5
kubectl autoscale deployment my-app --min=2 --max=10 --cpu-percent=80

# Rolling Update
kubectl set image deployment/my-app app=my-app:2.0.0
kubectl rollout status deployment/my-app
kubectl rollout history deployment/my-app
kubectl rollout undo deployment/my-app

# Delete Resources
kubectl delete pod my-app-xyz
kubectl delete -f deployment.yaml
kubectl delete deployment my-app

# Debugging
kubectl get events --sort-by=.metadata.creationTimestamp
kubectl top pods
kubectl top nodes
```

## Network Policies

Control Pod-to-Pod communication.

```yaml
# network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow from frontend
    - from:
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 3000
    # Allow from ingress controller
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 3000
  egress:
    # Allow to database
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    # Allow DNS
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

## RBAC (Role-Based Access Control)

```yaml
# rbac.yaml
# Service Account
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app
  namespace: production

---
# Role (namespace-scoped)
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get"]

---
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
  - kind: ServiceAccount
    name: my-app
    namespace: production
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io

---
# ClusterRole (cluster-scoped)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: node-reader
rules:
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["get", "list", "watch"]

---
# ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: read-nodes
subjects:
  - kind: ServiceAccount
    name: my-app
    namespace: production
roleRef:
  kind: ClusterRole
  name: node-reader
  apiGroup: rbac.authorization.k8s.io
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Kubernetes Best Practices                       │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Always set resource requests and limits                       │
│ ☐ Use namespaces for isolation                                  │
│ ☐ Implement health checks (liveness & readiness)                │
│ ☐ Use ConfigMaps and Secrets for configuration                  │
│ ☐ Avoid using :latest tag                                       │
│ ☐ Run as non-root user                                          │
│ ☐ Use Pod Disruption Budgets                                    │
│ ☐ Implement Network Policies                                    │
│ ☐ Use RBAC for access control                                   │
│ ☐ Set up HPA for auto-scaling                                   │
│ ☐ Use PodAntiAffinity for high availability                     │
│ ☐ Implement graceful shutdown                                   │
└─────────────────────────────────────────────────────────────────┘
```
