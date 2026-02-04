---
name: k8s-vpa
description: Kubernetes Vertical Pod Autoscaler
applies_to: kubernetes
---

# Kubernetes Vertical Pod Autoscaler (VPA)

## Overview

VPA automatically adjusts CPU and memory requests/limits for containers based on historical usage. It helps right-size workloads.

## Installation

```bash
# Clone VPA repository
git clone https://github.com/kubernetes/autoscaler.git
cd autoscaler/vertical-pod-autoscaler

# Install VPA
./hack/vpa-up.sh

# Verify installation
kubectl get pods -n kube-system | grep vpa
```

## Basic VPA

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api

  updatePolicy:
    updateMode: "Auto"
```

## Update Modes

### Auto Mode

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  updatePolicy:
    updateMode: "Auto"  # Automatically restarts pods with new resources
```

### Recreate Mode

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  updatePolicy:
    updateMode: "Recreate"  # Only updates on pod recreation
```

### Initial Mode

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  updatePolicy:
    updateMode: "Initial"  # Only sets resources at pod creation
```

### Off Mode (Recommendation Only)

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  updatePolicy:
    updateMode: "Off"  # Only provides recommendations, no changes
```

## Resource Policies

### Container-Specific Policies

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api

  updatePolicy:
    updateMode: "Auto"

  resourcePolicy:
    containerPolicies:
      - containerName: api
        minAllowed:
          cpu: "100m"
          memory: "128Mi"
        maxAllowed:
          cpu: "4"
          memory: "8Gi"
        controlledResources:
          - cpu
          - memory
        controlledValues: RequestsAndLimits

      - containerName: sidecar
        mode: "Off"  # Don't adjust this container
```

### Controlled Values

```yaml
resourcePolicy:
  containerPolicies:
    - containerName: api
      # RequestsOnly - Only adjust requests, keep limits ratio
      # RequestsAndLimits - Adjust both
      controlledValues: RequestsAndLimits
```

## Production VPA

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/component: autoscaler
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api

  updatePolicy:
    updateMode: "Auto"
    minReplicas: 2  # Don't evict if below this

  resourcePolicy:
    containerPolicies:
      - containerName: api
        minAllowed:
          cpu: "200m"
          memory: "256Mi"
        maxAllowed:
          cpu: "4"
          memory: "8Gi"
        controlledResources:
          - cpu
          - memory
        controlledValues: RequestsAndLimits

      - containerName: istio-proxy
        mode: "Off"  # Don't touch sidecar

  recommenders:
    - name: default
```

## VPA with Multiple Containers

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: multi-container-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app

  updatePolicy:
    updateMode: "Auto"

  resourcePolicy:
    containerPolicies:
      - containerName: app
        minAllowed:
          cpu: "100m"
          memory: "128Mi"
        maxAllowed:
          cpu: "2"
          memory: "4Gi"

      - containerName: nginx
        minAllowed:
          cpu: "50m"
          memory: "64Mi"
        maxAllowed:
          cpu: "500m"
          memory: "512Mi"

      - containerName: fluentd
        mode: "Off"  # Exclude from VPA
```

## VPA for StatefulSet

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: postgres-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: StatefulSet
    name: postgres

  updatePolicy:
    updateMode: "Initial"  # Only at creation to avoid restarts
    minReplicas: 1

  resourcePolicy:
    containerPolicies:
      - containerName: postgres
        minAllowed:
          cpu: "500m"
          memory: "1Gi"
        maxAllowed:
          cpu: "4"
          memory: "16Gi"
```

## VPA for CronJob

```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: backup-vpa
spec:
  targetRef:
    apiVersion: batch/v1
    kind: CronJob
    name: backup

  updatePolicy:
    updateMode: "Auto"

  resourcePolicy:
    containerPolicies:
      - containerName: backup
        minAllowed:
          cpu: "100m"
          memory: "256Mi"
        maxAllowed:
          cpu: "2"
          memory: "4Gi"
```

## Viewing VPA Status

```bash
# Get VPA status
kubectl get vpa api-vpa -o yaml

# Output includes recommendations:
# status:
#   conditions:
#   - type: RecommendationProvided
#     status: "True"
#   recommendation:
#     containerRecommendations:
#     - containerName: api
#       lowerBound:
#         cpu: "100m"
#         memory: "262144k"
#       target:
#         cpu: "250m"
#         memory: "524288k"
#       uncappedTarget:
#         cpu: "250m"
#         memory: "524288k"
#       upperBound:
#         cpu: "500m"
#         memory: "1048576k"
```

## Commands

```bash
# List VPAs
kubectl get vpa
kubectl get vpa -n production

# Describe VPA
kubectl describe vpa api-vpa

# Get recommendations
kubectl get vpa api-vpa -o jsonpath='{.status.recommendation}'

# Watch VPA
kubectl get vpa -w

# Delete VPA
kubectl delete vpa api-vpa
```

## VPA Components

```bash
# VPA consists of 3 components:
# 1. Recommender - Monitors resources and provides recommendations
# 2. Updater - Evicts pods needing updates
# 3. Admission Controller - Sets resources on new pods

kubectl get pods -n kube-system | grep vpa
# vpa-recommender-xxx
# vpa-updater-xxx
# vpa-admission-controller-xxx
```

## VPA vs HPA

| Feature | VPA | HPA |
|---------|-----|-----|
| Scales | CPU/Memory per pod | Number of pods |
| Updates | Restarts pods | Adds/removes pods |
| Use case | Right-sizing | Load handling |
| Metrics | Historical usage | Current metrics |

### Using VPA and HPA Together

```yaml
# VPA for vertical scaling (OFF mode recommended with HPA)
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: api-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  updatePolicy:
    updateMode: "Off"  # Recommendation only when using HPA
  resourcePolicy:
    containerPolicies:
      - containerName: api
        controlledResources:
          - memory  # Only control memory, let HPA use CPU

---
# HPA for horizontal scaling
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

## Best Practices

1. **Start with Off mode** to observe recommendations
2. **Set reasonable min/max** to prevent extreme values
3. **Exclude sidecar containers** from VPA
4. **Use Initial mode** for stateful workloads
5. **Don't use Auto mode with HPA on same resource**
6. **Monitor pod evictions** during VPA updates
7. **Set minReplicas** to maintain availability
8. **Test in staging** before production
9. **Review recommendations** before enabling Auto
10. **Use PodDisruptionBudget** with VPA Auto mode
