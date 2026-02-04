# Web Application Example

A complete example of deploying a web application to Kubernetes with best practices.

## Overview

This example demonstrates:
- Deployment with rolling updates
- Service exposure with ClusterIP
- Ingress with TLS termination
- ConfigMap and Secret management
- Horizontal Pod Autoscaling
- Pod Disruption Budget
- Resource limits and requests
- Health checks (liveness, readiness, startup)
- Security context configuration

## Architecture

```
                    ┌─────────────┐
                    │   Ingress   │
                    │  (NGINX)    │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Service   │
                    │ (ClusterIP) │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐┌─────▼─────┐┌─────▼─────┐
        │  Pod 1    ││  Pod 2    ││  Pod 3    │
        │  (web)    ││  (web)    ││  (web)    │
        └───────────┘└───────────┘└───────────┘
```

## Prerequisites

- Kubernetes cluster 1.26+
- kubectl configured
- Ingress controller installed (nginx-ingress)
- cert-manager (optional, for TLS)

## Quick Start

```bash
# Create namespace
kubectl create namespace web-app

# Apply all manifests
kubectl apply -f . -n web-app

# Verify deployment
kubectl get all -n web-app

# Check ingress
kubectl get ingress -n web-app
```

## Files

| File | Description |
|------|-------------|
| `namespace.yaml` | Namespace with labels |
| `configmap.yaml` | Application configuration |
| `secret.yaml` | Sensitive configuration |
| `deployment.yaml` | Pod specification |
| `service.yaml` | Service exposure |
| `ingress.yaml` | External access |
| `hpa.yaml` | Autoscaling rules |
| `pdb.yaml` | Disruption budget |

## Configuration

### Environment Variables

Set in `configmap.yaml`:
- `APP_ENV`: Environment name
- `LOG_LEVEL`: Logging verbosity
- `LOG_FORMAT`: Log output format

### Secrets

Set in `secret.yaml` (use external secrets in production):
- `DATABASE_URL`: Database connection string
- `API_KEY`: External API credentials

### Scaling

Configure in `hpa.yaml`:
- Min replicas: 2
- Max replicas: 10
- CPU target: 70%
- Memory target: 80%

## Customization

### Change Image

```yaml
# deployment.yaml
spec:
  template:
    spec:
      containers:
        - image: your-registry/your-app:tag
```

### Change Domain

```yaml
# ingress.yaml
spec:
  rules:
    - host: your-domain.com
```

### Adjust Resources

```yaml
# deployment.yaml
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi
```

## Monitoring

```bash
# View logs
kubectl logs -l app.kubernetes.io/name=web-app -n web-app -f

# Check metrics
kubectl top pods -n web-app

# View HPA status
kubectl get hpa -n web-app -w
```

## Troubleshooting

### Pod not starting
```bash
kubectl describe pod -l app.kubernetes.io/name=web-app -n web-app
kubectl logs -l app.kubernetes.io/name=web-app -n web-app --previous
```

### Ingress not working
```bash
kubectl describe ingress web-app -n web-app
kubectl logs -l app.kubernetes.io/name=ingress-nginx -n ingress-nginx
```

## Cleanup

```bash
kubectl delete namespace web-app
```
