---
name: k8s-hpa
description: Kubernetes Horizontal Pod Autoscaler
applies_to: kubernetes
---

# Kubernetes Horizontal Pod Autoscaler (HPA)

## Overview

HPA automatically scales the number of Pod replicas based on observed metrics like CPU, memory, or custom metrics.

## Basic HPA (CPU)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: production
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

## Memory-Based HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: production
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
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

## Multi-Metric HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api

  minReplicas: 3
  maxReplicas: 50

  metrics:
    # CPU utilization
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    # Memory utilization
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Pods metric (custom)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"

    # Object metric (external like Ingress)
    - type: Object
      object:
        metric:
          name: requests-per-second
        describedObject:
          apiVersion: networking.k8s.io/v1
          kind: Ingress
          name: api-ingress
        target:
          type: Value
          value: "10k"
```

## Production HPA

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/component: autoscaler
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api

  minReplicas: 3
  maxReplicas: 100

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

  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300  # 5 minutes
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
        - type: Pods
          value: 4
          periodSeconds: 60
      selectPolicy: Min

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

## Scaling Behavior

### Conservative Scale Down

```yaml
behavior:
  scaleDown:
    stabilizationWindowSeconds: 600  # 10 minutes
    policies:
      - type: Percent
        value: 10            # Max 10% per minute
        periodSeconds: 60
    selectPolicy: Min
```

### Aggressive Scale Up

```yaml
behavior:
  scaleUp:
    stabilizationWindowSeconds: 0
    policies:
      - type: Percent
        value: 200           # Double capacity
        periodSeconds: 15
      - type: Pods
        value: 10            # Or add 10 pods
        periodSeconds: 15
    selectPolicy: Max
```

### Disable Scale Down

```yaml
behavior:
  scaleDown:
    selectPolicy: Disabled
```

## Custom Metrics HPA

### Prometheus Adapter

```yaml
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
  maxReplicas: 20

  metrics:
    # Custom metric from Prometheus
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "500"

    # External metric
    - type: External
      external:
        metric:
          name: queue_messages_ready
          selector:
            matchLabels:
              queue: "orders"
        target:
          type: AverageValue
          averageValue: "100"
```

### Container Resource Metrics

```yaml
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
    - type: ContainerResource
      containerResource:
        name: cpu
        container: api
        target:
          type: Utilization
          averageUtilization: 70
```

## Target Types

### Utilization (Percentage)

```yaml
target:
  type: Utilization
  averageUtilization: 70  # 70% of requested resources
```

### AverageValue

```yaml
target:
  type: AverageValue
  averageValue: "100"  # Average per pod
```

### Value (Total)

```yaml
target:
  type: Value
  value: "10000"  # Total across all pods
```

## Deployment Requirements

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3  # Initial replicas (HPA will manage)
  template:
    spec:
      containers:
        - name: api
          image: api:1.0.0
          resources:
            # REQUIRED for HPA to work
            requests:
              cpu: "200m"
              memory: "256Mi"
            limits:
              cpu: "1"
              memory: "1Gi"
```

## HPA with PodDisruptionBudget

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: api
```

## Commands

```bash
# List HPAs
kubectl get hpa
kubectl get hpa -n production

# Describe HPA
kubectl describe hpa api-hpa

# View HPA status
kubectl get hpa api-hpa -o yaml

# Watch HPA
kubectl get hpa -w

# Create HPA from command
kubectl autoscale deployment api --cpu-percent=70 --min=2 --max=10

# Delete HPA
kubectl delete hpa api-hpa

# Check metrics
kubectl top pods
kubectl top nodes
```

## HPA Status

```bash
kubectl describe hpa api-hpa

# Output:
# Name:                     api-hpa
# Namespace:                production
# Reference:                Deployment/api
# Metrics:                  ( current / target )
#   resource cpu:           45% / 70%
#   resource memory:        60% / 80%
# Min replicas:             3
# Max replicas:             100
# Deployment pods:          5 current / 5 desired
# Conditions:
#   AbleToScale    True    ReadyForNewScale   recommended size matches current
#   ScalingActive  True    ValidMetricFound   the HPA was able to calculate a ratio
#   ScalingLimited False   DesiredWithinRange current replica count is within acceptable
```

## Troubleshooting

### HPA Not Scaling

```bash
# Check metrics server
kubectl get deployment metrics-server -n kube-system

# Check HPA events
kubectl describe hpa api-hpa

# Common issues:
# - Missing resource requests in Deployment
# - Metrics server not installed
# - RBAC permissions for metrics
```

### Metrics Not Available

```bash
# Verify metrics API
kubectl get --raw "/apis/metrics.k8s.io/v1beta1/pods"

# Check custom metrics API
kubectl get --raw "/apis/custom.metrics.k8s.io/v1beta1"
```

## Best Practices

1. **Always set resource requests** on containers
2. **Start with CPU-based scaling** before custom metrics
3. **Use conservative scale-down** to prevent thrashing
4. **Set appropriate min/max** based on capacity
5. **Combine with PodDisruptionBudget** for availability
6. **Monitor HPA events** for scaling issues
7. **Use stabilization windows** to smooth scaling
8. **Test scaling behavior** before production
9. **Consider KEDA** for event-driven scaling
10. **Set realistic targets** (70-80% utilization typical)
