---
name: k8s-cluster-autoscaler
description: Kubernetes Cluster Autoscaler for node scaling
applies_to: kubernetes
---

# Kubernetes Cluster Autoscaler

## Overview

Cluster Autoscaler automatically adjusts the size of your cluster by adding or removing nodes based on pending pods and node utilization.

## AWS EKS Cluster Autoscaler

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:DescribeAutoScalingGroups",
        "autoscaling:DescribeAutoScalingInstances",
        "autoscaling:DescribeLaunchConfigurations",
        "autoscaling:DescribeScalingActivities",
        "autoscaling:DescribeTags",
        "ec2:DescribeImages",
        "ec2:DescribeInstanceTypes",
        "ec2:DescribeLaunchTemplateVersions",
        "ec2:GetInstanceTypesFromInstanceRequirements",
        "eks:DescribeNodegroup"
      ],
      "Resource": ["*"]
    },
    {
      "Effect": "Allow",
      "Action": [
        "autoscaling:SetDesiredCapacity",
        "autoscaling:TerminateInstanceInAutoScalingGroup"
      ],
      "Resource": ["*"],
      "Condition": {
        "StringEquals": {
          "aws:ResourceTag/k8s.io/cluster-autoscaler/enabled": "true",
          "aws:ResourceTag/k8s.io/cluster-autoscaler/my-cluster": "owned"
        }
      }
    }
  ]
}
```

### EKS Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  labels:
    app: cluster-autoscaler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: cluster-autoscaler
  template:
    metadata:
      labels:
        app: cluster-autoscaler
    spec:
      serviceAccountName: cluster-autoscaler
      priorityClassName: system-cluster-critical

      containers:
        - name: cluster-autoscaler
          image: registry.k8s.io/autoscaling/cluster-autoscaler:v1.29.0

          command:
            - ./cluster-autoscaler
            - --v=4
            - --stderrthreshold=info
            - --cloud-provider=aws
            - --skip-nodes-with-local-storage=false
            - --expander=least-waste
            - --node-group-auto-discovery=asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/my-cluster
            - --balance-similar-node-groups
            - --skip-nodes-with-system-pods=false
            - --scale-down-enabled=true
            - --scale-down-delay-after-add=10m
            - --scale-down-unneeded-time=10m
            - --scale-down-utilization-threshold=0.5

          resources:
            requests:
              cpu: 100m
              memory: 600Mi
            limits:
              cpu: 100m
              memory: 600Mi

          volumeMounts:
            - name: ssl-certs
              mountPath: /etc/ssl/certs/ca-certificates.crt
              readOnly: true

      volumes:
        - name: ssl-certs
          hostPath:
            path: /etc/ssl/certs/ca-bundle.crt

      nodeSelector:
        kubernetes.io/os: linux

      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
```

### Service Account

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cluster-autoscaler
  namespace: kube-system
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/cluster-autoscaler

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-autoscaler
rules:
  - apiGroups: [""]
    resources: ["events", "endpoints"]
    verbs: ["create", "patch"]
  - apiGroups: [""]
    resources: ["pods/eviction"]
    verbs: ["create"]
  - apiGroups: [""]
    resources: ["pods/status"]
    verbs: ["update"]
  - apiGroups: [""]
    resources: ["endpoints"]
    resourceNames: ["cluster-autoscaler"]
    verbs: ["get", "update"]
  - apiGroups: [""]
    resources: ["nodes"]
    verbs: ["watch", "list", "get", "update"]
  - apiGroups: [""]
    resources: ["namespaces", "pods", "services", "replicationcontrollers", "persistentvolumeclaims", "persistentvolumes"]
    verbs: ["watch", "list", "get"]
  - apiGroups: ["extensions"]
    resources: ["replicasets", "daemonsets"]
    verbs: ["watch", "list", "get"]
  - apiGroups: ["policy"]
    resources: ["poddisruptionbudgets"]
    verbs: ["watch", "list"]
  - apiGroups: ["apps"]
    resources: ["statefulsets", "replicasets", "daemonsets"]
    verbs: ["watch", "list", "get"]
  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses", "csinodes", "csidrivers", "csistoragecapacities"]
    verbs: ["watch", "list", "get"]
  - apiGroups: ["batch", "extensions"]
    resources: ["jobs"]
    verbs: ["get", "list", "watch", "patch"]
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    verbs: ["create"]
  - apiGroups: ["coordination.k8s.io"]
    resources: ["leases"]
    resourceNames: ["cluster-autoscaler"]
    verbs: ["get", "update"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-autoscaler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-autoscaler
subjects:
  - kind: ServiceAccount
    name: cluster-autoscaler
    namespace: kube-system
```

## GKE Cluster Autoscaler

GKE has built-in autoscaling. Enable via:

```bash
# Enable autoscaling on node pool
gcloud container clusters update my-cluster \
  --enable-autoscaling \
  --min-nodes=1 \
  --max-nodes=10 \
  --node-pool=default-pool
```

```yaml
# Or via Terraform
resource "google_container_node_pool" "primary" {
  cluster = google_container_cluster.primary.name

  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }
}
```

## AKS Cluster Autoscaler

```bash
# Enable autoscaler on AKS
az aks update \
  --resource-group myResourceGroup \
  --name myAKSCluster \
  --enable-cluster-autoscaler \
  --min-count 1 \
  --max-count 10
```

## Expander Strategies

### Least Waste

```yaml
command:
  - --expander=least-waste
# Selects node group that will have least idle resources
```

### Random

```yaml
command:
  - --expander=random
# Randomly selects from suitable node groups
```

### Most Pods

```yaml
command:
  - --expander=most-pods
# Selects node group that can schedule most pods
```

### Priority

```yaml
command:
  - --expander=priority
```

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    10:
      - .*spot.*
    50:
      - .*on-demand.*
```

## Scale Down Configuration

```yaml
command:
  # Enable scale down
  - --scale-down-enabled=true

  # Wait time after scale up before considering scale down
  - --scale-down-delay-after-add=10m

  # Wait time after node deletion before considering more deletions
  - --scale-down-delay-after-delete=10s

  # Wait time after scale down failure
  - --scale-down-delay-after-failure=3m

  # Node is considered for removal if utilization below this
  - --scale-down-utilization-threshold=0.5

  # How long node should be unneeded before removal
  - --scale-down-unneeded-time=10m

  # Don't scale down nodes with local storage
  - --skip-nodes-with-local-storage=false

  # Don't scale down nodes with system pods
  - --skip-nodes-with-system-pods=false
```

## Preventing Scale Down

### Pod Annotations

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: important-pod
  annotations:
    cluster-autoscaler.kubernetes.io/safe-to-evict: "false"
```

### Node Annotations

```yaml
kubectl annotate node my-node cluster-autoscaler.kubernetes.io/scale-down-disabled=true
```

## Priority-Based Scaling

### Priority Classes

```yaml
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "High priority workloads"

---
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: low-priority
value: 100
globalDefault: false
preemptionPolicy: Never
description: "Low priority, can be preempted"
```

### Use in Pods

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: high-priority-pod
spec:
  priorityClassName: high-priority
  containers:
    - name: app
      image: myapp:1.0.0
```

## Node Taints for Scaling

```yaml
# Node group for specific workloads
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gpu-workload
spec:
  template:
    spec:
      tolerations:
        - key: "nvidia.com/gpu"
          operator: "Equal"
          value: "true"
          effect: "NoSchedule"
      nodeSelector:
        node.kubernetes.io/instance-type: p3.2xlarge
```

## Commands

```bash
# Check cluster autoscaler logs
kubectl logs -f deployment/cluster-autoscaler -n kube-system

# View autoscaler status
kubectl get configmap cluster-autoscaler-status -n kube-system -o yaml

# Check node groups
kubectl get nodes -o custom-columns=NAME:.metadata.name,INSTANCE-TYPE:.metadata.labels.'node\.kubernetes\.io/instance-type'

# View pending pods
kubectl get pods --field-selector=status.phase=Pending

# Check autoscaler events
kubectl get events -n kube-system --field-selector source=cluster-autoscaler
```

## Troubleshooting

### Pods Not Triggering Scale Up

```bash
# Check if pod has appropriate requests
kubectl get pod pending-pod -o yaml | grep -A 10 resources

# Common issues:
# - Pod has nodeSelector/affinity that doesn't match any node group
# - Pod requests more resources than any node type provides
# - Pod has tolerations that don't match any node group taints
```

### Nodes Not Scaling Down

```bash
# Check for pods preventing scale down
kubectl get pods --all-namespaces -o wide | grep <node-name>

# Check for annotations
kubectl get node <node-name> -o yaml | grep safe-to-evict

# Common blockers:
# - Pods with local storage
# - Pods with restrictive PDBs
# - Pods without controller (bare pods)
# - System pods
```

## Best Practices

1. **Set appropriate min/max** for node groups
2. **Use priority expander** for cost optimization (spot first)
3. **Configure PodDisruptionBudgets** for graceful scale down
4. **Set resource requests** on all pods
5. **Use multiple node groups** for different workload types
6. **Monitor cluster autoscaler** logs and events
7. **Test scale-up time** for capacity planning
8. **Use pod priorities** for critical workloads
9. **Configure appropriate delays** to prevent thrashing
10. **Label node groups** for expander strategies
