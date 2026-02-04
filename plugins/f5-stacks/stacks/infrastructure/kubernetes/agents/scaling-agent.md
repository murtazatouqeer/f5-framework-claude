---
name: scaling-agent
description: Designs and implements Kubernetes scaling strategies
triggers:
  - k8s scaling
  - autoscaling
  - hpa
  - vpa
  - cluster autoscaler
capabilities:
  - Horizontal Pod Autoscaler design
  - Vertical Pod Autoscaler configuration
  - Cluster autoscaler setup
  - Scaling strategy recommendations
  - Performance optimization
---

# Kubernetes Scaling Agent

## Purpose

Designs and implements optimal scaling strategies for Kubernetes workloads based on application characteristics and requirements.

## Workflow

```
1. ANALYZE workload characteristics
   - CPU/memory patterns
   - Traffic patterns
   - Latency requirements
   - Cost constraints

2. DESIGN scaling strategy
   - HPA for horizontal scaling
   - VPA for vertical scaling
   - Cluster autoscaler for nodes
   - KEDA for event-driven scaling

3. CONFIGURE metrics
   - CPU/memory utilization
   - Custom metrics
   - External metrics

4. IMPLEMENT safeguards
   - Min/max replicas
   - Scaling policies
   - Pod disruption budgets

5. VALIDATE and tune
   - Load testing
   - Metric analysis
   - Fine-tuning thresholds
```

## Scaling Strategies

### Horizontal Pod Autoscaler (HPA)

```yaml
# HPA with multiple metrics
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
  maxReplicas: 20

  metrics:
    # CPU-based scaling
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70

    # Memory-based scaling
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80

    # Custom metric (requests per second)
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: 1000

  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
        - type: Pods
          value: 2
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

### Vertical Pod Autoscaler (VPA)

```yaml
# VPA for automatic resource adjustment
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
    updateMode: Auto  # Off, Initial, Recreate, Auto

  resourcePolicy:
    containerPolicies:
      - containerName: api
        minAllowed:
          cpu: 100m
          memory: 256Mi
        maxAllowed:
          cpu: 4
          memory: 8Gi
        controlledResources: ["cpu", "memory"]
        controlledValues: RequestsAndLimits
```

### KEDA (Event-Driven Autoscaling)

```yaml
# KEDA ScaledObject for event-driven scaling
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: api-scaledobject
  namespace: production
spec:
  scaleTargetRef:
    name: api

  minReplicaCount: 1
  maxReplicaCount: 50
  pollingInterval: 15
  cooldownPeriod: 300

  triggers:
    # Scale based on RabbitMQ queue length
    - type: rabbitmq
      metadata:
        queueName: tasks
        host: amqp://rabbitmq.default.svc.cluster.local
        queueLength: "50"

    # Scale based on Prometheus metric
    - type: prometheus
      metadata:
        serverAddress: http://prometheus:9090
        metricName: http_requests_total
        threshold: "100"
        query: sum(rate(http_requests_total{service="api"}[2m]))
```

### Cluster Autoscaler

```yaml
# Cluster Autoscaler configuration (EKS example)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
spec:
  template:
    spec:
      containers:
        - name: cluster-autoscaler
          image: k8s.gcr.io/autoscaling/cluster-autoscaler:v1.29.0
          command:
            - ./cluster-autoscaler
            - --v=4
            - --stderrthreshold=info
            - --cloud-provider=aws
            - --skip-nodes-with-local-storage=false
            - --expander=least-waste
            - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/my-cluster
            - --balance-similar-node-groups
            - --scale-down-enabled=true
            - --scale-down-delay-after-add=10m
            - --scale-down-unneeded-time=10m
```

## Pod Disruption Budget

```yaml
# Ensure minimum availability during scaling/updates
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api-pdb
  namespace: production
spec:
  minAvailable: 2      # or use maxUnavailable
  selector:
    matchLabels:
      app: api
```

## Scaling Best Practices

### Right-sizing Resources
```yaml
# Start with conservative limits, adjust with VPA recommendations
resources:
  requests:
    cpu: 100m      # Start low
    memory: 256Mi
  limits:
    cpu: 1000m     # Allow burst
    memory: 1Gi    # Hard limit
```

### Scaling Policies
```yaml
# Prevent flapping with stabilization windows
behavior:
  scaleDown:
    stabilizationWindowSeconds: 300  # Wait 5 min before scaling down
  scaleUp:
    stabilizationWindowSeconds: 0    # Scale up immediately
```

### Cost Optimization
```yaml
# Use spot/preemptible nodes with proper handling
spec:
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          preference:
            matchExpressions:
              - key: node.kubernetes.io/lifecycle
                operator: In
                values:
                  - spot
  tolerations:
    - key: "kubernetes.io/preemptible"
      operator: "Equal"
      value: "true"
      effect: "NoSchedule"
```

## Monitoring Scaling

```bash
# Watch HPA status
kubectl get hpa -w

# Check HPA events
kubectl describe hpa <name>

# View current metrics
kubectl top pods

# Check VPA recommendations
kubectl describe vpa <name>
```
