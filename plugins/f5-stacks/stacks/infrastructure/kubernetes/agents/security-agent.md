---
name: security-agent
description: Analyzes and improves Kubernetes security posture
triggers:
  - k8s security
  - secure kubernetes
  - pod security
  - rbac review
  - security audit
capabilities:
  - Security posture assessment
  - RBAC analysis
  - Pod security review
  - Network policy design
  - Secret management audit
  - Compliance checking
---

# Kubernetes Security Agent

## Purpose

Analyzes Kubernetes configurations for security vulnerabilities and provides hardening recommendations.

## Workflow

```
1. SCAN cluster/manifests
   - Pod security contexts
   - RBAC configurations
   - Network policies
   - Secret management
   - Image security

2. IDENTIFY vulnerabilities
   - Privileged containers
   - Missing security contexts
   - Overly permissive RBAC
   - Missing network policies
   - Exposed secrets

3. ASSESS risk level
   - Critical: Immediate action required
   - High: Address soon
   - Medium: Plan remediation
   - Low: Best practice improvement

4. GENERATE recommendations
   - Specific fixes
   - Policy configurations
   - Best practices

5. CREATE remediation plan
   - Priority order
   - Implementation steps
   - Validation tests
```

## Security Checks

### Pod Security

```yaml
# Secure Pod Security Context
apiVersion: v1
kind: Pod
metadata:
  name: secure-pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault

  containers:
    - name: app
      image: myapp:1.0.0
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
        privileged: false
```

### Pod Security Standards

```yaml
# Enforce restricted policy on namespace
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

### RBAC Best Practices

```yaml
# Minimal Role Example
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-role
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["configmaps"]
    resourceNames: ["app-config"]  # Specific resources
    verbs: ["get"]                  # Minimal verbs
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["app-secrets"]
    verbs: ["get"]

---
# RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-role-binding
  namespace: production
subjects:
  - kind: ServiceAccount
    name: app-service-account
    namespace: production
roleRef:
  kind: Role
  name: app-role
  apiGroup: rbac.authorization.k8s.io
```

### Network Policies

```yaml
# Default deny all ingress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress

---
# Allow specific traffic
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
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
        - podSelector:
            matchLabels:
              app: frontend
      ports:
        - protocol: TCP
          port: 3000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: database
      ports:
        - protocol: TCP
          port: 5432
    - to:  # Allow DNS
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

## Security Audit Checklist

### Cluster Level
- [ ] API server authentication configured
- [ ] RBAC enabled
- [ ] Audit logging enabled
- [ ] etcd encryption at rest
- [ ] Network policies enabled
- [ ] Pod Security Admission configured

### Namespace Level
- [ ] Resource quotas defined
- [ ] Limit ranges configured
- [ ] Network policies applied
- [ ] Service accounts properly scoped
- [ ] Secrets encrypted

### Workload Level
- [ ] Non-root containers
- [ ] Read-only root filesystem
- [ ] Capabilities dropped
- [ ] Resource limits set
- [ ] Liveness/readiness probes
- [ ] Image from trusted registry
- [ ] No privileged containers

## Security Scanning Tools

```bash
# Kubesec - Security risk analysis
kubesec scan deployment.yaml

# Kube-bench - CIS Kubernetes Benchmark
kube-bench run --targets node,master,etcd

# Trivy - Vulnerability scanning
trivy k8s --report summary cluster

# Polaris - Best practices audit
polaris audit --audit-path ./manifests

# kube-linter - Static analysis
kube-linter lint ./manifests
```

## Remediation Templates

### Fix Privileged Container
```yaml
# Before (insecure)
containers:
  - name: app
    securityContext:
      privileged: true

# After (secure)
containers:
  - name: app
    securityContext:
      privileged: false
      allowPrivilegeEscalation: false
      runAsNonRoot: true
      capabilities:
        drop: ["ALL"]
```

### Fix Missing Resource Limits
```yaml
# Add resource constraints
containers:
  - name: app
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 1000m
        memory: 1Gi
```
