# Microservices Example

A complete example of deploying a microservices architecture to Kubernetes.

## Overview

This example demonstrates:
- Multiple services communicating via internal DNS
- API Gateway pattern with Ingress
- Service-to-service authentication
- Distributed configuration
- Service mesh readiness
- Network policies for service isolation
- Centralized logging and tracing

## Architecture

```
                         ┌─────────────────┐
                         │    Ingress      │
                         │  (API Gateway)  │
                         └────────┬────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                   │
       ┌──────▼──────┐    ┌───────▼──────┐    ┌──────▼──────┐
       │   API       │    │   Users      │    │   Orders    │
       │   Service   │────│   Service    │────│   Service   │
       └──────┬──────┘    └───────┬──────┘    └──────┬──────┘
              │                   │                   │
              │           ┌───────▼──────┐           │
              │           │   Auth       │           │
              └───────────│   Service    │───────────┘
                          └───────┬──────┘
                                  │
                          ┌───────▼──────┐
                          │   Database   │
                          │  (External)  │
                          └──────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api-gateway | 8080 | Entry point, routing |
| users-service | 8081 | User management |
| orders-service | 8082 | Order processing |
| auth-service | 8083 | Authentication |

## Prerequisites

- Kubernetes cluster 1.26+
- kubectl configured
- Ingress controller installed
- Network policies enabled

## Quick Start

```bash
# Create namespace
kubectl create namespace microservices

# Apply all manifests
kubectl apply -f . -n microservices

# Verify services
kubectl get all -n microservices

# Test internal communication
kubectl exec -it deploy/api-gateway -n microservices -- \
  curl http://users-service:8081/health
```

## Service Discovery

Services communicate using Kubernetes DNS:
- `users-service.microservices.svc.cluster.local`
- `orders-service.microservices.svc.cluster.local`
- Short form within namespace: `users-service`

## Network Policies

Default deny all ingress, explicit allow rules:
- API Gateway → All services
- Users Service → Auth Service
- Orders Service → Users Service, Auth Service

## Configuration

### Shared Configuration

Use ConfigMaps for shared settings:
```bash
kubectl create configmap shared-config \
  --from-literal=LOG_LEVEL=info \
  -n microservices
```

### Service-Specific Secrets

Each service has dedicated secrets:
```bash
kubectl create secret generic users-secrets \
  --from-literal=DB_PASSWORD=secret \
  -n microservices
```

## Monitoring

### Distributed Tracing

Services propagate trace headers:
- `X-Request-ID`
- `X-B3-TraceId`
- `X-B3-SpanId`

### Metrics

Each service exposes `/metrics` for Prometheus scraping.

## Cleanup

```bash
kubectl delete namespace microservices
```
