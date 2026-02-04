---
name: k8s-rbac
description: Kubernetes Role-Based Access Control
applies_to: kubernetes
---

# Kubernetes RBAC

## Overview

RBAC (Role-Based Access Control) regulates access to Kubernetes resources based on roles assigned to users or service accounts.

## Core Concepts

| Resource | Scope | Description |
|----------|-------|-------------|
| Role | Namespace | Permissions within a namespace |
| ClusterRole | Cluster | Permissions cluster-wide |
| RoleBinding | Namespace | Binds Role to subjects in namespace |
| ClusterRoleBinding | Cluster | Binds ClusterRole cluster-wide |

## Role

### Basic Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```

### Full CRUD Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployment-manager
  namespace: production
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]

  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/status"]
    verbs: ["get", "list", "watch"]

  - apiGroups: [""]
    resources: ["configmaps", "secrets"]
    verbs: ["get", "list"]
```

### Resource-Specific Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: configmap-updater
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["app-config", "env-config"]  # Specific resources only
    verbs: ["get", "update", "patch"]
```

## ClusterRole

### Cluster-Wide Reader

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: cluster-reader
rules:
  - apiGroups: [""]
    resources: ["nodes", "namespaces", "persistentvolumes"]
    verbs: ["get", "list", "watch"]

  - apiGroups: ["storage.k8s.io"]
    resources: ["storageclasses"]
    verbs: ["get", "list", "watch"]
```

### Aggregated ClusterRole

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring-endpoints
  labels:
    rbac.example.com/aggregate-to-monitoring: "true"
rules:
  - apiGroups: [""]
    resources: ["endpoints", "services", "pods"]
    verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: monitoring
aggregationRule:
  clusterRoleSelectors:
    - matchLabels:
        rbac.example.com/aggregate-to-monitoring: "true"
rules: []  # Rules are auto-filled from aggregation
```

## RoleBinding

### Bind to User

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-pods
  namespace: production
subjects:
  - kind: User
    name: jane
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Bind to Group

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: dev-team-deployments
  namespace: production
subjects:
  - kind: Group
    name: developers
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: deployment-manager
  apiGroup: rbac.authorization.k8s.io
```

### Bind to ServiceAccount

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-pod-reader
  namespace: production
subjects:
  - kind: ServiceAccount
    name: app-service-account
    namespace: production
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### Bind ClusterRole to Namespace

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: read-secrets
  namespace: production
subjects:
  - kind: User
    name: jane
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: secret-reader  # ClusterRole, but only in production namespace
  apiGroup: rbac.authorization.k8s.io
```

## ClusterRoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: cluster-admin-binding
subjects:
  - kind: User
    name: admin@example.com
    apiGroup: rbac.authorization.k8s.io
  - kind: Group
    name: cluster-admins
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
```

## ServiceAccount

### Create ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: production
  labels:
    app: myapp
```

### ServiceAccount with Secrets

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: production
secrets:
  - name: app-service-account-token
imagePullSecrets:
  - name: docker-registry
```

### Use ServiceAccount in Pod

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  serviceAccountName: app-service-account
  automountServiceAccountToken: true  # default: true
  containers:
    - name: app
      image: myapp:1.0.0
```

## Production RBAC Setup

### Developer Role

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer
  namespace: production
rules:
  # Read pods and logs
  - apiGroups: [""]
    resources: ["pods", "pods/log", "pods/status"]
    verbs: ["get", "list", "watch"]

  # Read services and endpoints
  - apiGroups: [""]
    resources: ["services", "endpoints"]
    verbs: ["get", "list", "watch"]

  # Read configmaps
  - apiGroups: [""]
    resources: ["configmaps"]
    verbs: ["get", "list", "watch"]

  # Read deployments
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch"]

  # Port forward
  - apiGroups: [""]
    resources: ["pods/portforward"]
    verbs: ["create"]

  # Exec into pods (optional, careful!)
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]
```

### CI/CD ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: cicd-deployer
  namespace: production

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: cicd-deployer
  namespace: production
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

  - apiGroups: [""]
    resources: ["services", "configmaps"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

  - apiGroups: [""]
    resources: ["secrets"]
    verbs: ["get", "list"]

  - apiGroups: ["networking.k8s.io"]
    resources: ["ingresses"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: cicd-deployer
  namespace: production
subjects:
  - kind: ServiceAccount
    name: cicd-deployer
    namespace: production
roleRef:
  kind: Role
  name: cicd-deployer
  apiGroup: rbac.authorization.k8s.io
```

### Application ServiceAccount

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api-app
  namespace: production

---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: api-app
  namespace: production
rules:
  # Read own configmaps
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["api-config"]
    verbs: ["get", "watch"]

  # Read own secrets
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["api-secrets"]
    verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: api-app
  namespace: production
subjects:
  - kind: ServiceAccount
    name: api-app
    namespace: production
roleRef:
  kind: Role
  name: api-app
  apiGroup: rbac.authorization.k8s.io
```

## Common Verbs

| Verb | Description |
|------|-------------|
| get | Read single resource |
| list | Read multiple resources |
| watch | Watch for changes |
| create | Create new resource |
| update | Replace entire resource |
| patch | Partially update resource |
| delete | Delete single resource |
| deletecollection | Delete multiple resources |

## API Groups

| API Group | Resources |
|-----------|-----------|
| "" (core) | pods, services, configmaps, secrets, namespaces |
| apps | deployments, replicasets, statefulsets, daemonsets |
| batch | jobs, cronjobs |
| networking.k8s.io | ingresses, networkpolicies |
| rbac.authorization.k8s.io | roles, rolebindings, clusterroles |
| storage.k8s.io | storageclasses, volumeattachments |

## Commands

```bash
# List roles
kubectl get roles
kubectl get clusterroles

# Describe role
kubectl describe role pod-reader -n production

# List bindings
kubectl get rolebindings
kubectl get clusterrolebindings

# Check permissions
kubectl auth can-i create pods --namespace production
kubectl auth can-i create pods --namespace production --as jane
kubectl auth can-i create pods --namespace production --as system:serviceaccount:production:app

# List all permissions for user
kubectl auth can-i --list --as jane

# Create role from command
kubectl create role pod-reader --verb=get,list,watch --resource=pods -n production

# Create rolebinding
kubectl create rolebinding read-pods --role=pod-reader --user=jane -n production

# Create serviceaccount
kubectl create serviceaccount myapp -n production
```

## Best Practices

1. **Principle of least privilege** - Grant minimum required permissions
2. **Use Roles over ClusterRoles** when possible
3. **Avoid wildcards** (*) in verbs and resources
4. **Use resourceNames** to limit access to specific resources
5. **Create dedicated ServiceAccounts** per application
6. **Disable automountServiceAccountToken** when not needed
7. **Audit RBAC regularly** for over-permissioned roles
8. **Use Groups** for team-based access management
9. **Separate CI/CD accounts** from admin accounts
10. **Document RBAC policies** for compliance
