---
name: k8s-services
description: Kubernetes Services for network abstraction
applies_to: kubernetes
---

# Kubernetes Services

## Overview

Services provide stable network endpoints for Pods. They abstract Pod IP addresses and enable load balancing.

## Service Types

### ClusterIP (Default)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
spec:
  type: ClusterIP
  selector:
    app: api
  ports:
    - name: http
      port: 80
      targetPort: 3000
      protocol: TCP
```

### NodePort

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-nodeport
spec:
  type: NodePort
  selector:
    app: api
  ports:
    - port: 80
      targetPort: 3000
      nodePort: 30080  # 30000-32767
```

### LoadBalancer

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-lb
  annotations:
    # AWS annotations
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
spec:
  type: LoadBalancer
  selector:
    app: api
  ports:
    - port: 80
      targetPort: 3000
```

### ExternalName

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-db
spec:
  type: ExternalName
  externalName: db.example.com
```

### Headless Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: db-headless
spec:
  type: ClusterIP
  clusterIP: None  # Headless
  selector:
    app: database
  ports:
    - port: 5432
```

## Production Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/component: backend
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "3000"
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: api
    app.kubernetes.io/instance: api-production
  ports:
    - name: http
      port: 80
      targetPort: http
      protocol: TCP
    - name: grpc
      port: 9090
      targetPort: grpc
      protocol: TCP
  sessionAffinity: None  # or ClientIP
```

## Multi-Port Service

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
    - name: http
      port: 80
      targetPort: 3000
    - name: https
      port: 443
      targetPort: 3443
    - name: metrics
      port: 9090
      targetPort: 9090
```

## Session Affinity

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
    - port: 80
      targetPort: 3000
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours
```

## External Traffic Policy

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  type: LoadBalancer
  externalTrafficPolicy: Local  # or Cluster (default)
  selector:
    app: api
  ports:
    - port: 80
```

## Internal Traffic Policy

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  internalTrafficPolicy: Local  # or Cluster (default)
  selector:
    app: api
  ports:
    - port: 80
```

## Service with External IPs

```yaml
apiVersion: v1
kind: Service
metadata:
  name: api
spec:
  selector:
    app: api
  ports:
    - port: 80
  externalIPs:
    - 192.168.1.100
```

## Endpoints

```yaml
# Manual endpoints (no selector)
apiVersion: v1
kind: Service
metadata:
  name: external-service
spec:
  ports:
    - port: 80

---
apiVersion: v1
kind: Endpoints
metadata:
  name: external-service
subsets:
  - addresses:
      - ip: 10.0.0.1
      - ip: 10.0.0.2
    ports:
      - port: 8080
```

## EndpointSlices (Kubernetes 1.21+)

```yaml
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: api-abc12
  labels:
    kubernetes.io/service-name: api
addressType: IPv4
ports:
  - name: http
    port: 3000
    protocol: TCP
endpoints:
  - addresses:
      - "10.1.1.1"
    conditions:
      ready: true
      serving: true
      terminating: false
    nodeName: node-1
```

## Cloud Provider Annotations

### AWS

```yaml
metadata:
  annotations:
    # Network Load Balancer
    service.beta.kubernetes.io/aws-load-balancer-type: nlb
    service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: ip

    # Classic Load Balancer
    service.beta.kubernetes.io/aws-load-balancer-backend-protocol: http
    service.beta.kubernetes.io/aws-load-balancer-ssl-cert: arn:aws:acm:...
    service.beta.kubernetes.io/aws-load-balancer-ssl-ports: "443"
```

### GCP

```yaml
metadata:
  annotations:
    cloud.google.com/load-balancer-type: Internal
    networking.gke.io/load-balancer-type: Internal
```

### Azure

```yaml
metadata:
  annotations:
    service.beta.kubernetes.io/azure-load-balancer-internal: "true"
```

## Service DNS

```
# Service DNS format
<service-name>.<namespace>.svc.cluster.local

# Examples
api.production.svc.cluster.local
api.production.svc
api.production
api  # within same namespace

# Headless service
# Returns all pod IPs
db-headless.production.svc.cluster.local

# StatefulSet pod DNS
postgres-0.postgres-headless.production.svc.cluster.local
```

## Service Commands

```bash
# Create service
kubectl expose deployment api --port=80 --target-port=3000

# List services
kubectl get services
kubectl get svc

# Describe service
kubectl describe svc api

# Get endpoints
kubectl get endpoints api

# Get EndpointSlices
kubectl get endpointslices -l kubernetes.io/service-name=api

# Port forward to service
kubectl port-forward svc/api 8080:80

# Delete service
kubectl delete svc api
```

## Debugging Services

```bash
# Test DNS
kubectl run test --rm -it --image=busybox -- nslookup api.production

# Test connectivity
kubectl run test --rm -it --image=busybox -- wget -qO- http://api:80

# Check endpoints
kubectl get endpoints api

# Describe for events
kubectl describe svc api
```
