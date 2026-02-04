---
name: k8s-resource-quotas
description: Kubernetes ResourceQuotas for namespace resource limits
applies_to: kubernetes
---

# Kubernetes ResourceQuotas

## Overview

ResourceQuotas constrain aggregate resource consumption per namespace. They limit the quantity of objects and total compute resources.

## Basic ResourceQuota

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: production
spec:
  hard:
    # Compute resources
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi

    # Object counts
    pods: "50"
    services: "10"
    secrets: "20"
    configmaps: "20"
```

## Compute Resource Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-resources
  namespace: production
spec:
  hard:
    # CPU
    requests.cpu: "100"        # Total CPU requests
    limits.cpu: "200"          # Total CPU limits

    # Memory
    requests.memory: 200Gi     # Total memory requests
    limits.memory: 400Gi       # Total memory limits

    # Ephemeral storage
    requests.ephemeral-storage: 500Gi
    limits.ephemeral-storage: 1Ti

    # GPU (if available)
    requests.nvidia.com/gpu: "4"
```

## Object Count Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-counts
  namespace: production
spec:
  hard:
    # Core objects
    pods: "100"
    services: "20"
    replicationcontrollers: "10"
    resourcequotas: "5"
    secrets: "50"
    configmaps: "50"
    persistentvolumeclaims: "20"

    # Workloads
    count/deployments.apps: "20"
    count/replicasets.apps: "50"
    count/statefulsets.apps: "10"
    count/jobs.batch: "30"
    count/cronjobs.batch: "10"

    # Networking
    count/services: "20"
    count/ingresses.networking.k8s.io: "10"

    # Services by type
    services.loadbalancers: "2"
    services.nodeports: "5"
```

## Storage Quotas

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: production
spec:
  hard:
    # Total storage requests
    requests.storage: 500Gi

    # PVC count
    persistentvolumeclaims: "20"

    # Per StorageClass limits
    gp3.storageclass.storage.k8s.io/requests.storage: 200Gi
    gp3.storageclass.storage.k8s.io/persistentvolumeclaims: "10"

    ssd.storageclass.storage.k8s.io/requests.storage: 100Gi
    ssd.storageclass.storage.k8s.io/persistentvolumeclaims: "5"
```

## Scoped ResourceQuotas

### By Priority Class

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: high-priority-quota
  namespace: production
spec:
  hard:
    pods: "10"
    requests.cpu: "20"
    requests.memory: 40Gi
  scopeSelector:
    matchExpressions:
      - scopeName: PriorityClass
        operator: In
        values:
          - high
```

### By Pod Quality of Service

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: best-effort-quota
  namespace: production
spec:
  hard:
    pods: "20"
  scopes:
    - BestEffort

---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: not-best-effort-quota
  namespace: production
spec:
  hard:
    pods: "50"
    requests.cpu: "50"
    requests.memory: 100Gi
  scopes:
    - NotBestEffort
```

### By Terminating/Non-Terminating

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: terminating-quota
  namespace: production
spec:
  hard:
    pods: "100"
    requests.cpu: "50"
  scopes:
    - Terminating  # Pods with activeDeadlineSeconds

---
apiVersion: v1
kind: ResourceQuota
metadata:
  name: not-terminating-quota
  namespace: production
spec:
  hard:
    pods: "50"
    requests.cpu: "100"
  scopes:
    - NotTerminating  # Long-running pods
```

## Production ResourceQuota Set

```yaml
# Compute quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: production
  labels:
    app.kubernetes.io/name: quota
    app.kubernetes.io/component: resource-management
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    requests.ephemeral-storage: 100Gi

---
# Object count quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-quota
  namespace: production
spec:
  hard:
    pods: "200"
    services: "50"
    secrets: "100"
    configmaps: "100"
    persistentvolumeclaims: "50"
    count/deployments.apps: "50"
    count/statefulsets.apps: "20"
    count/jobs.batch: "100"
    count/cronjobs.batch: "20"
    services.loadbalancers: "5"
    services.nodeports: "10"

---
# Storage quota
apiVersion: v1
kind: ResourceQuota
metadata:
  name: storage-quota
  namespace: production
spec:
  hard:
    requests.storage: 1Ti
    persistentvolumeclaims: "50"
    gp3.storageclass.storage.k8s.io/requests.storage: 500Gi
```

## Team-Based Quotas

### Development Team

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: dev-team-quota
  namespace: team-dev
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    pods: "50"
    services: "20"
    persistentvolumeclaims: "10"
    requests.storage: 100Gi
```

### Production Team

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: prod-team-quota
  namespace: team-prod
spec:
  hard:
    requests.cpu: "100"
    requests.memory: 200Gi
    limits.cpu: "200"
    limits.memory: 400Gi
    pods: "200"
    services: "50"
    persistentvolumeclaims: "50"
    requests.storage: 500Gi
```

## Quota Status

```bash
# View quota status
kubectl get resourcequota -n production

# Detailed status
kubectl describe resourcequota compute-quota -n production

# Output:
# Name:            compute-quota
# Namespace:       production
# Resource         Used    Hard
# --------         ----    ----
# limits.cpu       15      40
# limits.memory    30Gi    80Gi
# requests.cpu     10      20
# requests.memory  20Gi    40Gi
```

## Cross-Namespace Quotas (ClusterResourceQuota)

```yaml
# OpenShift ClusterResourceQuota
apiVersion: quota.openshift.io/v1
kind: ClusterResourceQuota
metadata:
  name: team-quota
spec:
  quota:
    hard:
      requests.cpu: "100"
      requests.memory: 200Gi
  selector:
    labels:
      matchLabels:
        team: backend
```

## Commands

```bash
# List ResourceQuotas
kubectl get resourcequota
kubectl get quota
kubectl get quota -n production

# Describe ResourceQuota
kubectl describe quota compute-quota -n production

# Create ResourceQuota
kubectl apply -f resourcequota.yaml

# Edit ResourceQuota
kubectl edit quota compute-quota -n production

# Delete ResourceQuota
kubectl delete quota compute-quota -n production

# View all quotas in all namespaces
kubectl get quota --all-namespaces

# Check resource usage vs quota
kubectl get quota -n production -o yaml
```

## Enforcement Behavior

When a ResourceQuota exists in a namespace:

1. **Pod creation fails** if it would exceed quota
2. **Requests/limits required** for compute resources (unless LimitRange sets defaults)
3. **Objects fail to create** if count exceeds quota
4. **PVC creation fails** if storage exceeds quota

## Best Practices

1. **Set quotas on all namespaces** to prevent resource exhaustion
2. **Use LimitRanges** with ResourceQuotas to set defaults
3. **Monitor quota usage** and set alerts before hitting limits
4. **Size quotas appropriately** based on team needs
5. **Use scoped quotas** for fine-grained control
6. **Include storage quotas** to prevent disk exhaustion
7. **Limit LoadBalancer services** (cloud cost control)
8. **Review and adjust** quotas periodically
9. **Document quota policies** for teams
10. **Test quota limits** in staging before production
