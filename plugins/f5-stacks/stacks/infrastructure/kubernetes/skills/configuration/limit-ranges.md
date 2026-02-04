---
name: k8s-limit-ranges
description: Kubernetes LimitRanges for container resource constraints
applies_to: kubernetes
---

# Kubernetes LimitRanges

## Overview

LimitRanges constrain resource allocations for Pods and containers in a namespace. They set defaults, minimums, and maximums.

## Basic LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
  namespace: production
spec:
  limits:
    - type: Container
      default:
        cpu: "500m"
        memory: "512Mi"
      defaultRequest:
        cpu: "100m"
        memory: "128Mi"
      min:
        cpu: "50m"
        memory: "64Mi"
      max:
        cpu: "2"
        memory: "4Gi"
```

## Container Limits

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: container-limits
  namespace: production
spec:
  limits:
    - type: Container

      # Default limits (applied if not specified)
      default:
        cpu: "1"
        memory: "1Gi"
        ephemeral-storage: "2Gi"

      # Default requests (applied if not specified)
      defaultRequest:
        cpu: "200m"
        memory: "256Mi"
        ephemeral-storage: "1Gi"

      # Minimum allowed
      min:
        cpu: "50m"
        memory: "64Mi"
        ephemeral-storage: "100Mi"

      # Maximum allowed
      max:
        cpu: "4"
        memory: "8Gi"
        ephemeral-storage: "10Gi"

      # Max ratio of limits to requests
      maxLimitRequestRatio:
        cpu: "10"
        memory: "4"
```

## Pod Limits

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: pod-limits
  namespace: production
spec:
  limits:
    - type: Pod
      min:
        cpu: "100m"
        memory: "128Mi"
      max:
        cpu: "16"
        memory: "32Gi"
```

## PVC Limits

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: storage-limits
  namespace: production
spec:
  limits:
    - type: PersistentVolumeClaim
      min:
        storage: "1Gi"
      max:
        storage: "100Gi"
```

## Production LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: production-limits
  namespace: production
  labels:
    app.kubernetes.io/name: limitrange
    app.kubernetes.io/component: resource-management
spec:
  limits:
    # Container limits
    - type: Container
      default:
        cpu: "500m"
        memory: "512Mi"
        ephemeral-storage: "1Gi"
      defaultRequest:
        cpu: "100m"
        memory: "128Mi"
        ephemeral-storage: "500Mi"
      min:
        cpu: "25m"
        memory: "32Mi"
      max:
        cpu: "4"
        memory: "8Gi"
        ephemeral-storage: "10Gi"
      maxLimitRequestRatio:
        cpu: "10"
        memory: "4"

    # Pod limits (aggregate)
    - type: Pod
      max:
        cpu: "8"
        memory: "16Gi"

    # PVC limits
    - type: PersistentVolumeClaim
      min:
        storage: "1Gi"
      max:
        storage: "500Gi"
```

## Development LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: dev-limits
  namespace: development
spec:
  limits:
    - type: Container
      default:
        cpu: "200m"
        memory: "256Mi"
      defaultRequest:
        cpu: "50m"
        memory: "64Mi"
      min:
        cpu: "10m"
        memory: "16Mi"
      max:
        cpu: "1"
        memory: "2Gi"
      maxLimitRequestRatio:
        cpu: "20"
        memory: "8"

    - type: PersistentVolumeClaim
      min:
        storage: "100Mi"
      max:
        storage: "10Gi"
```

## Batch Job LimitRange

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: batch-limits
  namespace: batch-jobs
spec:
  limits:
    - type: Container
      default:
        cpu: "2"
        memory: "4Gi"
      defaultRequest:
        cpu: "500m"
        memory: "1Gi"
      min:
        cpu: "100m"
        memory: "256Mi"
      max:
        cpu: "8"
        memory: "32Gi"
```

## How LimitRanges Work

### Default Application

```yaml
# Pod without resources specified
apiVersion: v1
kind: Pod
metadata:
  name: no-resources
spec:
  containers:
    - name: app
      image: nginx

# After LimitRange applied:
# resources:
#   requests:
#     cpu: 100m       # from defaultRequest
#     memory: 128Mi   # from defaultRequest
#   limits:
#     cpu: 500m       # from default
#     memory: 512Mi   # from default
```

### Validation

```yaml
# This Pod would be rejected (exceeds max)
apiVersion: v1
kind: Pod
metadata:
  name: too-big
spec:
  containers:
    - name: app
      image: nginx
      resources:
        requests:
          cpu: "10"      # Exceeds max of 4
          memory: "100Gi" # Exceeds max of 8Gi
```

### Ratio Enforcement

```yaml
# With maxLimitRequestRatio cpu: "10"
# This is valid:
resources:
  requests:
    cpu: "100m"
  limits:
    cpu: "1"  # ratio 10:1

# This would be rejected:
resources:
  requests:
    cpu: "100m"
  limits:
    cpu: "2"  # ratio 20:1 exceeds max
```

## Multi-Container Pod Behavior

```yaml
# Pod with multiple containers
apiVersion: v1
kind: Pod
metadata:
  name: multi-container
spec:
  containers:
    - name: app
      image: myapp
      resources:
        requests:
          cpu: "200m"
          memory: "256Mi"

    - name: sidecar
      image: sidecar
      # Gets defaults from LimitRange:
      # requests.cpu: 100m
      # requests.memory: 128Mi
      # limits.cpu: 500m
      # limits.memory: 512Mi
```

## Combined with ResourceQuota

```yaml
# LimitRange ensures defaults
apiVersion: v1
kind: LimitRange
metadata:
  name: limits
  namespace: production
spec:
  limits:
    - type: Container
      defaultRequest:
        cpu: "100m"
        memory: "128Mi"
      default:
        cpu: "500m"
        memory: "512Mi"

---
# ResourceQuota enforces totals
apiVersion: v1
kind: ResourceQuota
metadata:
  name: quota
  namespace: production
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
```

## Commands

```bash
# List LimitRanges
kubectl get limitrange
kubectl get limits
kubectl get limits -n production

# Describe LimitRange
kubectl describe limitrange resource-limits -n production

# Create LimitRange
kubectl apply -f limitrange.yaml

# Edit LimitRange
kubectl edit limitrange resource-limits -n production

# Delete LimitRange
kubectl delete limitrange resource-limits -n production

# View in all namespaces
kubectl get limitrange --all-namespaces
```

## Viewing Applied Limits

```bash
# Describe shows all constraints
kubectl describe limits resource-limits -n production

# Output:
# Type        Resource  Min   Max   Default Request  Default Limit  Max Limit/Request Ratio
# ----        --------  ---   ---   ---------------  -------------  -----------------------
# Container   cpu       50m   4     100m             500m           10
# Container   memory    64Mi  8Gi   128Mi            512Mi          4
# Pod         cpu       100m  8     -                -              -
# Pod         memory    128Mi 16Gi  -                -              -
# PVC         storage   1Gi   500Gi -                -              -
```

## Best Practices

1. **Always set LimitRanges** in production namespaces
2. **Set reasonable defaults** for your workloads
3. **Use with ResourceQuota** for complete resource control
4. **Set maxLimitRequestRatio** to prevent resource hogging
5. **Keep min values low** to allow small test containers
6. **Set PVC limits** to prevent storage exhaustion
7. **Document limits** for development teams
8. **Test limits** before applying to production
9. **Monitor pod creation failures** due to limit violations
10. **Adjust based on workload patterns** over time

## Common Patterns

### Strict Production

```yaml
spec:
  limits:
    - type: Container
      default:
        cpu: "500m"
        memory: "512Mi"
      defaultRequest:
        cpu: "250m"
        memory: "256Mi"
      min:
        cpu: "100m"
        memory: "128Mi"
      max:
        cpu: "2"
        memory: "4Gi"
      maxLimitRequestRatio:
        cpu: "4"
        memory: "2"
```

### Flexible Development

```yaml
spec:
  limits:
    - type: Container
      default:
        cpu: "200m"
        memory: "256Mi"
      defaultRequest:
        cpu: "50m"
        memory: "64Mi"
      min:
        cpu: "10m"
        memory: "16Mi"
      max:
        cpu: "4"
        memory: "8Gi"
      maxLimitRequestRatio:
        cpu: "20"
        memory: "10"
```

### Memory-Intensive Workloads

```yaml
spec:
  limits:
    - type: Container
      default:
        cpu: "500m"
        memory: "2Gi"
      defaultRequest:
        cpu: "100m"
        memory: "1Gi"
      max:
        cpu: "4"
        memory: "32Gi"
```
