---
name: api-resources
description: Kubernetes API resources and versions
applies_to: kubernetes
---

# Kubernetes API Resources

## Discovering API Resources

```bash
# List all API resources
kubectl api-resources

# List with API group
kubectl api-resources --api-group=apps

# List namespaced resources
kubectl api-resources --namespaced=true

# List cluster-scoped resources
kubectl api-resources --namespaced=false

# List with specific verbs
kubectl api-resources --verbs=list,get

# List API versions
kubectl api-versions
```

## Core API Resources (v1)

```bash
# /api/v1 - Core API (no group)
kubectl api-resources --api-group=""
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| Pod | po | Yes | Smallest deployable unit |
| Service | svc | Yes | Network abstraction |
| ConfigMap | cm | Yes | Configuration data |
| Secret | - | Yes | Sensitive data |
| PersistentVolume | pv | No | Cluster storage |
| PersistentVolumeClaim | pvc | Yes | Storage request |
| Namespace | ns | No | Virtual cluster |
| Node | no | No | Cluster node |
| ServiceAccount | sa | Yes | Pod identity |
| Endpoints | ep | Yes | Service endpoints |
| Event | ev | Yes | Cluster events |
| LimitRange | limits | Yes | Resource defaults |
| ResourceQuota | quota | Yes | Resource limits |

## Apps API Resources (apps/v1)

```bash
# /apis/apps/v1
kubectl api-resources --api-group=apps
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| Deployment | deploy | Yes | Stateless workloads |
| ReplicaSet | rs | Yes | Pod replicas |
| StatefulSet | sts | Yes | Stateful workloads |
| DaemonSet | ds | Yes | One pod per node |
| ControllerRevision | - | Yes | Revision history |

## Batch API Resources (batch/v1)

```bash
# /apis/batch/v1
kubectl api-resources --api-group=batch
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| Job | - | Yes | Run to completion |
| CronJob | cj | Yes | Scheduled jobs |

## Networking API Resources (networking.k8s.io/v1)

```bash
# /apis/networking.k8s.io/v1
kubectl api-resources --api-group=networking.k8s.io
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| Ingress | ing | Yes | HTTP/HTTPS routing |
| IngressClass | - | No | Ingress controller class |
| NetworkPolicy | netpol | Yes | Network rules |

## Autoscaling API Resources (autoscaling/v2)

```bash
# /apis/autoscaling/v2
kubectl api-resources --api-group=autoscaling
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| HorizontalPodAutoscaler | hpa | Yes | Pod autoscaling |

## RBAC API Resources (rbac.authorization.k8s.io/v1)

```bash
# /apis/rbac.authorization.k8s.io/v1
kubectl api-resources --api-group=rbac.authorization.k8s.io
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| Role | - | Yes | Namespace permissions |
| ClusterRole | - | No | Cluster permissions |
| RoleBinding | - | Yes | Namespace role binding |
| ClusterRoleBinding | - | No | Cluster role binding |

## Storage API Resources (storage.k8s.io/v1)

```bash
# /apis/storage.k8s.io/v1
kubectl api-resources --api-group=storage.k8s.io
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| StorageClass | sc | No | Storage provisioner |
| VolumeAttachment | - | No | Volume attachment |
| CSIDriver | - | No | CSI driver info |
| CSINode | - | No | CSI node info |

## Policy API Resources (policy/v1)

```bash
# /apis/policy/v1
kubectl api-resources --api-group=policy
```

| Kind | Short | Namespaced | Description |
|------|-------|------------|-------------|
| PodDisruptionBudget | pdb | Yes | Disruption limits |

## Explaining Resources

```bash
# Get resource documentation
kubectl explain pods
kubectl explain pods.spec
kubectl explain pods.spec.containers
kubectl explain pods.spec.containers.resources

# With API version
kubectl explain pods --api-version=v1

# Recursive explanation
kubectl explain pods --recursive

# Output as JSON schema
kubectl explain pods --output=plaintext-openapiv2
```

## Resource Shortcuts

```bash
# Common shortcuts
po    = pods
svc   = services
deploy = deployments
ds    = daemonsets
sts   = statefulsets
rs    = replicasets
cm    = configmaps
pv    = persistentvolumes
pvc   = persistentvolumeclaims
ns    = namespaces
no    = nodes
ing   = ingresses
netpol = networkpolicies
sa    = serviceaccounts
hpa   = horizontalpodautoscalers
pdb   = poddisruptionbudgets
sc    = storageclasses
cj    = cronjobs
ev    = events
ep    = endpoints
limits = limitranges
quota = resourcequotas
```

## API Versions

### Stability Levels

| Level | Description | Example |
|-------|-------------|---------|
| alpha | Experimental, may change | v1alpha1 |
| beta | Well-tested, may change | v1beta1 |
| stable | Production-ready | v1 |

### Version Migration

```yaml
# Check deprecated APIs
kubectl get --raw /apis/apps/v1beta1 2>&1 | grep -i deprecated

# Common migrations:
# extensions/v1beta1 → networking.k8s.io/v1 (Ingress)
# policy/v1beta1 → policy/v1 (PodDisruptionBudget)
# autoscaling/v2beta2 → autoscaling/v2 (HPA)
```

## Custom Resource Definitions

```bash
# List CRDs
kubectl get crds

# Describe CRD
kubectl describe crd mycrd.example.com

# List custom resources
kubectl get mycrd.example.com
```

### CRD Example

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: myresources.example.com
spec:
  group: example.com
  names:
    kind: MyResource
    plural: myresources
    singular: myresource
    shortNames:
      - mr
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                replicas:
                  type: integer
                image:
                  type: string
```

## Server-Side Apply

```bash
# Apply with server-side apply
kubectl apply -f manifest.yaml --server-side

# Force conflicts
kubectl apply -f manifest.yaml --server-side --force-conflicts

# View field managers
kubectl get pod my-pod -o yaml | grep -A 5 managedFields
```
