---
name: k8s-pod-security
description: Kubernetes Pod Security Standards and Admission
applies_to: kubernetes
---

# Kubernetes Pod Security

## Overview

Pod Security Standards define three policies (Privileged, Baseline, Restricted) that cover the security spectrum. Pod Security Admission enforces these standards at the namespace level.

## Pod Security Standards

### Privileged

No restrictions. Use for system-level workloads like CNI, storage drivers.

### Baseline

Minimally restrictive, prevents known privilege escalations.

**Restrictions:**
- No privileged containers
- No hostNetwork, hostPID, hostIPC
- Limited hostPorts
- Restricted volume types
- No privilege escalation

### Restricted

Heavily restricted, follows security best practices.

**Additional restrictions:**
- Must run as non-root
- Seccomp profile required
- All capabilities dropped
- Read-only root filesystem (recommended)

## Pod Security Admission

### Namespace Labels

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce - Block non-compliant pods
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest

    # Warn - Allow but warn
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest

    # Audit - Log violations
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

### Different Modes

```yaml
# Development namespace - Baseline enforced, Restricted warned
apiVersion: v1
kind: Namespace
metadata:
  name: development
  labels:
    pod-security.kubernetes.io/enforce: baseline
    pod-security.kubernetes.io/warn: restricted

---
# Production namespace - Restricted enforced
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted

---
# System namespace - Privileged (for CNI, etc.)
apiVersion: v1
kind: Namespace
metadata:
  name: kube-system
  labels:
    pod-security.kubernetes.io/enforce: privileged
```

## Restricted Pod Example

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
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
        runAsNonRoot: true
        runAsUser: 1000
        capabilities:
          drop:
            - ALL

      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/cache

  volumes:
    - name: tmp
      emptyDir: {}
    - name: cache
      emptyDir: {}
```

## Deployment with Security Context

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      # Pod-level security context
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        runAsGroup: 1000
        fsGroup: 1000
        seccompProfile:
          type: RuntimeDefault

      serviceAccountName: api
      automountServiceAccountToken: false

      containers:
        - name: api
          image: api:1.0.0

          # Container-level security context
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL

          ports:
            - containerPort: 8080
              name: http

          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 512Mi

          volumeMounts:
            - name: tmp
              mountPath: /tmp
            - name: data
              mountPath: /data

      volumes:
        - name: tmp
          emptyDir: {}
        - name: data
          emptyDir: {}
```

## Security Context Options

### Pod Level

```yaml
spec:
  securityContext:
    # User/Group
    runAsUser: 1000
    runAsGroup: 1000
    runAsNonRoot: true
    fsGroup: 1000
    fsGroupChangePolicy: "OnRootMismatch"

    # Supplemental groups
    supplementalGroups: [1000, 2000]

    # Sysctls
    sysctls:
      - name: net.core.somaxconn
        value: "1024"

    # Seccomp
    seccompProfile:
      type: RuntimeDefault  # or Localhost, Unconfined

    # SELinux
    seLinuxOptions:
      level: "s0:c123,c456"

    # Windows options
    windowsOptions:
      runAsUserName: "ContainerUser"
```

### Container Level

```yaml
containers:
  - name: app
    securityContext:
      # Privileges
      privileged: false
      allowPrivilegeEscalation: false

      # User
      runAsUser: 1000
      runAsGroup: 1000
      runAsNonRoot: true

      # Filesystem
      readOnlyRootFilesystem: true

      # Capabilities
      capabilities:
        drop:
          - ALL
        add:
          - NET_BIND_SERVICE  # If needed

      # Seccomp (can override pod level)
      seccompProfile:
        type: RuntimeDefault

      # SELinux
      seLinuxOptions:
        level: "s0:c123,c456"

      # Proc mount
      procMount: Default  # or Unmasked
```

## Capabilities

### Drop All (Recommended)

```yaml
securityContext:
  capabilities:
    drop:
      - ALL
```

### Add Specific Capabilities

```yaml
securityContext:
  capabilities:
    drop:
      - ALL
    add:
      - NET_BIND_SERVICE  # Bind to ports < 1024
      - CHOWN             # Change file ownership
      - SETUID            # Set user ID
      - SETGID            # Set group ID
```

### Common Capabilities

| Capability | Use Case |
|------------|----------|
| NET_BIND_SERVICE | Bind to privileged ports |
| NET_RAW | Raw socket access |
| SYS_ADMIN | Mount, namespaces (dangerous) |
| SYS_PTRACE | Process tracing |
| CHOWN | Change file ownership |
| DAC_OVERRIDE | Bypass file permissions |

## Seccomp Profiles

### Runtime Default

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

### Custom Profile

```yaml
securityContext:
  seccompProfile:
    type: Localhost
    localhostProfile: profiles/audit.json
```

### Profile Example

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "exit", "exit_group"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

## AppArmor

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
  annotations:
    container.apparmor.security.beta.kubernetes.io/app: runtime/default
spec:
  containers:
    - name: app
      image: myapp:1.0.0
```

## Commands

```bash
# Check namespace labels
kubectl get namespace production -o yaml | grep pod-security

# Label namespace
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted \
  pod-security.kubernetes.io/warn=restricted

# Dry run pod creation
kubectl apply -f pod.yaml --dry-run=server

# Check if pod would be admitted
kubectl auth can-i create pods --as=system:serviceaccount:production:default

# View security context
kubectl get pod secure-app -o jsonpath='{.spec.securityContext}'
```

## Migration to Pod Security Standards

### Step 1: Audit Current State

```bash
# Add audit label first
kubectl label namespace production \
  pod-security.kubernetes.io/audit=restricted \
  pod-security.kubernetes.io/warn=restricted

# Check audit logs
kubectl logs -n kube-system -l component=kube-apiserver | grep "pod-security"
```

### Step 2: Fix Violations

Update Deployments to comply with restricted standard.

### Step 3: Enforce

```bash
kubectl label namespace production \
  pod-security.kubernetes.io/enforce=restricted
```

## Best Practices

1. **Start with restricted** and only relax when needed
2. **Use warn/audit modes** to discover issues before enforcing
3. **Run as non-root** (runAsNonRoot: true)
4. **Drop all capabilities** and add back only what's needed
5. **Use read-only root filesystem** with emptyDir for writes
6. **Enable seccomp** with RuntimeDefault profile
7. **Disable service account token mounting** when not needed
8. **Set resource limits** to prevent DoS
9. **Use dedicated service accounts** per application
10. **Regularly audit** pod security settings
