---
name: k8s-architecture
description: Kubernetes cluster architecture and components
applies_to: kubernetes
---

# Kubernetes Architecture

## Cluster Components

### Control Plane

```
┌──────────────────────────────────────────────────────────────┐
│                       CONTROL PLANE                          │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ API Server  │  │  Scheduler  │  │ Controller Manager  │  │
│  │   (kube-    │  │   (kube-    │  │    (kube-           │  │
│  │  apiserver) │  │  scheduler) │  │  controller-manager)│  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┴─────────────────────┘             │
│                          │                                   │
│                   ┌──────┴──────┐                           │
│                   │    etcd     │                           │
│                   │ (key-value) │                           │
│                   └─────────────┘                           │
└──────────────────────────────────────────────────────────────┘
```

#### kube-apiserver
- Entry point for all REST commands
- Validates and processes API requests
- Gateway to etcd

#### etcd
- Consistent and highly-available key-value store
- Stores all cluster data
- Single source of truth

#### kube-scheduler
- Watches for newly created Pods
- Assigns Pods to nodes based on:
  - Resource requirements
  - Affinity/anti-affinity
  - Taints/tolerations
  - Data locality

#### kube-controller-manager
- Runs controller processes:
  - Node Controller
  - Replication Controller
  - Endpoints Controller
  - ServiceAccount Controller

### Worker Nodes

```
┌──────────────────────────────────────────────────────────────┐
│                        WORKER NODE                           │
├──────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   kubelet   │  │ kube-proxy  │  │ Container Runtime   │  │
│  │             │  │             │  │ (containerd/CRI-O)  │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┴─────────────────────┘             │
│                          │                                   │
│    ┌─────────────────────┴─────────────────────┐            │
│    │                  PODS                      │            │
│    │  ┌─────────┐  ┌─────────┐  ┌─────────┐   │            │
│    │  │Container│  │Container│  │Container│   │            │
│    │  └─────────┘  └─────────┘  └─────────┘   │            │
│    └────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

#### kubelet
- Node agent running on each node
- Ensures containers are running in Pods
- Reports node and pod status to control plane

#### kube-proxy
- Network proxy on each node
- Maintains network rules
- Handles service abstraction

#### Container Runtime
- Runs containers (containerd, CRI-O)
- Implements Container Runtime Interface (CRI)

## Kubernetes Objects

### Core Objects

```yaml
# Namespace - Virtual cluster
apiVersion: v1
kind: Namespace
metadata:
  name: production

---
# Pod - Smallest deployable unit
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  namespace: production
spec:
  containers:
    - name: nginx
      image: nginx:1.25

---
# Service - Network abstraction
apiVersion: v1
kind: Service
metadata:
  name: nginx-service
spec:
  selector:
    app: nginx
  ports:
    - port: 80
      targetPort: 80
```

### Workload Objects

| Object | Purpose | Use Case |
|--------|---------|----------|
| Deployment | Stateless apps | Web servers, APIs |
| StatefulSet | Stateful apps | Databases, caches |
| DaemonSet | One per node | Logging, monitoring |
| Job | Run to completion | Batch processing |
| CronJob | Scheduled jobs | Periodic tasks |

### Configuration Objects

| Object | Purpose | Use Case |
|--------|---------|----------|
| ConfigMap | Non-sensitive config | App settings |
| Secret | Sensitive data | Passwords, tokens |
| ResourceQuota | Limit resources | Namespace limits |
| LimitRange | Default limits | Container defaults |

### Storage Objects

| Object | Purpose | Use Case |
|--------|---------|----------|
| PersistentVolume | Cluster storage | Storage provisioning |
| PersistentVolumeClaim | Storage request | App storage needs |
| StorageClass | Dynamic provisioning | Storage tiers |

## API Groups

```bash
# Core API (legacy)
/api/v1
  - pods
  - services
  - configmaps
  - secrets
  - namespaces

# Named API groups
/apis/apps/v1
  - deployments
  - statefulsets
  - daemonsets
  - replicasets

/apis/batch/v1
  - jobs
  - cronjobs

/apis/networking.k8s.io/v1
  - ingresses
  - networkpolicies

/apis/autoscaling/v2
  - horizontalpodautoscalers
```

## Resource Hierarchy

```
Cluster
├── Namespace: kube-system (system components)
├── Namespace: default
├── Namespace: production
│   ├── Deployment: api
│   │   └── ReplicaSet: api-5d8f9b7c6
│   │       ├── Pod: api-5d8f9b7c6-abc12
│   │       ├── Pod: api-5d8f9b7c6-def34
│   │       └── Pod: api-5d8f9b7c6-ghi56
│   ├── Service: api
│   ├── ConfigMap: api-config
│   ├── Secret: api-secrets
│   └── Ingress: api-ingress
└── Namespace: staging
```

## Labels and Selectors

```yaml
# Recommended labels
metadata:
  labels:
    app.kubernetes.io/name: myapp
    app.kubernetes.io/instance: myapp-production
    app.kubernetes.io/version: "1.0.0"
    app.kubernetes.io/component: api
    app.kubernetes.io/part-of: myplatform
    app.kubernetes.io/managed-by: helm
```

## Networking Model

- Every Pod gets its own IP address
- Pods can communicate without NAT
- Nodes can communicate with all Pods without NAT
- The IP a Pod sees itself as is the same IP others see it as

```
┌─────────────────────────────────────────────────────────────┐
│                     Cluster Network                          │
│  ┌──────────────────┐          ┌──────────────────┐        │
│  │     Node 1       │          │     Node 2       │        │
│  │  ┌─────┐ ┌─────┐ │          │  ┌─────┐ ┌─────┐│        │
│  │  │Pod A│ │Pod B│ │ ◄──────► │  │Pod C│ │Pod D││        │
│  │  │10.1 │ │10.2 │ │          │  │10.3 │ │10.4 ││        │
│  │  └─────┘ └─────┘ │          │  └─────┘ └─────┘│        │
│  └──────────────────┘          └──────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```
