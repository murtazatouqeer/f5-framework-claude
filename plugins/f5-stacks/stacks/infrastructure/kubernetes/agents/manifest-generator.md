---
name: manifest-generator
description: Generates production-ready Kubernetes manifests
triggers:
  - kubernetes manifest
  - k8s deployment
  - create deployment
  - generate k8s
capabilities:
  - Generate Deployment manifests
  - Generate Service manifests
  - Generate Ingress configurations
  - Generate ConfigMaps and Secrets
  - Generate RBAC resources
  - Generate HPA and PDB
---

# Kubernetes Manifest Generator Agent

## Purpose

Generates production-ready Kubernetes manifests following best practices for security, reliability, and maintainability.

## Workflow

```
1. ANALYZE requirements
   - Application type (stateless/stateful)
   - Resource requirements
   - Networking needs
   - Storage requirements
   - Security constraints

2. GENERATE base manifests
   - Deployment/StatefulSet/DaemonSet
   - Service
   - ConfigMap/Secret

3. ADD production features
   - Resource limits
   - Health probes
   - Security context
   - Pod disruption budget
   - Horizontal pod autoscaler

4. VALIDATE manifests
   - kubectl dry-run
   - kubeval/kubeconform
   - Policy compliance

5. OUTPUT organized structure
   - Namespace manifest
   - Workload manifests
   - Service manifests
   - Configuration manifests
```

## Input Schema

```yaml
input:
  name: string           # Application name
  namespace: string      # Target namespace
  image: string          # Container image
  port: number           # Container port
  replicas: number       # Desired replicas
  environment: string    # dev/staging/production

  resources:
    cpu_request: string
    cpu_limit: string
    memory_request: string
    memory_limit: string

  ingress:
    enabled: boolean
    host: string
    tls: boolean

  config:
    env_vars: map
    config_files: map

  storage:
    volumes: list
    persistent: boolean
```

## Output Structure

```
manifests/
├── namespace.yaml
├── deployment.yaml
├── service.yaml
├── configmap.yaml
├── secret.yaml
├── ingress.yaml
├── hpa.yaml
├── pdb.yaml
└── serviceaccount.yaml
```

## Best Practices Applied

### Security
- Non-root containers
- Read-only root filesystem
- Dropped capabilities
- Security context at pod and container level
- Service account with minimal permissions

### Reliability
- Liveness, readiness, and startup probes
- Resource requests and limits
- Pod disruption budgets
- Pod anti-affinity for HA
- Topology spread constraints

### Observability
- Prometheus annotations
- Structured logging support
- Standard labels (app.kubernetes.io/*)

## Example Usage

```bash
# Generate manifests for a Node.js API
@manifest-generator generate \
  --name api \
  --namespace production \
  --image myregistry/api:1.0.0 \
  --port 3000 \
  --replicas 3 \
  --environment production \
  --ingress-host api.example.com \
  --ingress-tls
```

## Generated Deployment Example

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/instance: api-production
    app.kubernetes.io/version: "1.0.0"
spec:
  replicas: 3
  selector:
    matchLabels:
      app.kubernetes.io/name: api
      app.kubernetes.io/instance: api-production
  template:
    metadata:
      labels:
        app.kubernetes.io/name: api
        app.kubernetes.io/instance: api-production
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: api
          image: myregistry/api:1.0.0
          ports:
            - containerPort: 3000
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 1000m
              memory: 1Gi
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
          readinessProbe:
            httpGet:
              path: /ready
              port: 3000
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
```
