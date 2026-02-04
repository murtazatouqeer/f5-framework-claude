---
name: service-mesh
description: Service mesh patterns with Istio and Linkerd
category: devops/orchestration
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Service Mesh

## Overview

A service mesh is a dedicated infrastructure layer for handling service-to-service
communication, providing traffic management, security, and observability.

## Service Mesh Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Service Mesh Architecture                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Control Plane                         │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐              │   │
│  │  │  Pilot   │  │  Citadel │  │  Galley  │              │   │
│  │  │(Traffic) │  │(Security)│  │ (Config) │              │   │
│  │  └──────────┘  └──────────┘  └──────────┘              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                   │
│                              ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Data Plane                           │   │
│  │                                                          │   │
│  │  ┌─────────────────┐     ┌─────────────────┐           │   │
│  │  │    Service A    │     │    Service B    │           │   │
│  │  │  ┌───────────┐  │     │  ┌───────────┐  │           │   │
│  │  │  │    App    │  │     │  │    App    │  │           │   │
│  │  │  └───────────┘  │     │  └───────────┘  │           │   │
│  │  │  ┌───────────┐  │ mTLS│  ┌───────────┐  │           │   │
│  │  │  │  Sidecar  │◄─┼─────┼─▶│  Sidecar  │  │           │   │
│  │  │  │  (Envoy)  │  │     │  │  (Envoy)  │  │           │   │
│  │  │  └───────────┘  │     │  └───────────┘  │           │   │
│  │  └─────────────────┘     └─────────────────┘           │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Istio Installation

```bash
# Download Istio
curl -L https://istio.io/downloadIstio | sh -

# Install with default profile
istioctl install --set profile=default -y

# Install with demo profile (includes more features)
istioctl install --set profile=demo -y

# Enable sidecar injection for namespace
kubectl label namespace default istio-injection=enabled
```

### Istio Profiles

```yaml
# istio-config.yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-config
spec:
  profile: default
  meshConfig:
    accessLogFile: /dev/stdout
    enableTracing: true
    defaultConfig:
      tracing:
        sampling: 100.0
  components:
    ingressGateways:
      - name: istio-ingressgateway
        enabled: true
        k8s:
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: 500m
              memory: 256Mi
    egressGateways:
      - name: istio-egressgateway
        enabled: true
  values:
    global:
      proxy:
        resources:
          requests:
            cpu: 50m
            memory: 64Mi
          limits:
            cpu: 200m
            memory: 128Mi
```

## Traffic Management

### Virtual Service

```yaml
# virtual-service.yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
    - my-app
    - api.example.com
  gateways:
    - my-gateway
    - mesh  # Internal traffic
  http:
    # Route based on headers
    - match:
        - headers:
            x-version:
              exact: "v2"
      route:
        - destination:
            host: my-app
            subset: v2

    # Route based on URI
    - match:
        - uri:
            prefix: /api/v2
      rewrite:
        uri: /api
      route:
        - destination:
            host: my-app
            subset: v2

    # Traffic splitting (Canary)
    - route:
        - destination:
            host: my-app
            subset: v1
          weight: 90
        - destination:
            host: my-app
            subset: v2
          weight: 10

    # Fault injection (testing)
    - match:
        - headers:
            x-test-fault:
              exact: "true"
      fault:
        delay:
          percentage:
            value: 100
          fixedDelay: 5s
        abort:
          percentage:
            value: 10
          httpStatus: 503
      route:
        - destination:
            host: my-app
            subset: v1

    # Timeout and retries
    - route:
        - destination:
            host: my-app
            subset: v1
      timeout: 30s
      retries:
        attempts: 3
        perTryTimeout: 10s
        retryOn: 5xx,reset,connect-failure
```

### Destination Rule

```yaml
# destination-rule.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: my-app
spec:
  host: my-app
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        h2UpgradePolicy: UPGRADE
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
    loadBalancer:
      simple: ROUND_ROBIN
      # Or consistent hashing
      # consistentHash:
      #   httpHeaderName: x-user-id
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
  subsets:
    - name: v1
      labels:
        version: v1
      trafficPolicy:
        connectionPool:
          http:
            http1MaxPendingRequests: 50
    - name: v2
      labels:
        version: v2
```

### Gateway

```yaml
# gateway.yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: my-gateway
spec:
  selector:
    istio: ingressgateway
  servers:
    - port:
        number: 80
        name: http
        protocol: HTTP
      hosts:
        - "*.example.com"
      tls:
        httpsRedirect: true
    - port:
        number: 443
        name: https
        protocol: HTTPS
      hosts:
        - "*.example.com"
      tls:
        mode: SIMPLE
        credentialName: example-tls
```

## Security

### mTLS Configuration

```yaml
# peer-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # STRICT, PERMISSIVE, or DISABLE

---
# Namespace-wide strict mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
```

### Authorization Policy

```yaml
# authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: api-authorization
  namespace: production
spec:
  selector:
    matchLabels:
      app: my-app
  action: ALLOW
  rules:
    # Allow from specific service
    - from:
        - source:
            principals:
              - "cluster.local/ns/production/sa/frontend"
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/*"]

    # Allow from specific namespace
    - from:
        - source:
            namespaces: ["monitoring"]
      to:
        - operation:
            methods: ["GET"]
            paths: ["/health", "/metrics"]

    # Allow with JWT claims
    - from:
        - source:
            requestPrincipals: ["*"]
      when:
        - key: request.auth.claims[role]
          values: ["admin"]

---
# Deny all by default
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  {}  # Empty spec denies all
```

### Request Authentication (JWT)

```yaml
# request-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: my-app
  jwtRules:
    - issuer: "https://auth.example.com"
      jwksUri: "https://auth.example.com/.well-known/jwks.json"
      audiences:
        - "api.example.com"
      forwardOriginalToken: true
      outputPayloadToHeader: x-jwt-payload
```

## Observability

### Telemetry Configuration

```yaml
# telemetry.yaml
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: mesh-default
  namespace: istio-system
spec:
  accessLogging:
    - providers:
        - name: envoy
  tracing:
    - providers:
        - name: "jaeger"
      randomSamplingPercentage: 100.0
  metrics:
    - providers:
        - name: prometheus
```

### Service Entry (External Services)

```yaml
# service-entry.yaml
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-api
spec:
  hosts:
    - api.external.com
  location: MESH_EXTERNAL
  ports:
    - number: 443
      name: https
      protocol: HTTPS
  resolution: DNS

---
# With egress gateway
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-db
spec:
  hosts:
    - db.external.com
  location: MESH_EXTERNAL
  ports:
    - number: 5432
      name: tcp
      protocol: TCP
  resolution: DNS
  endpoints:
    - address: 203.0.113.10
```

## Canary Deployment with Istio

```yaml
# canary-deployment.yaml
# Deployment v1
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-v1
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
      version: v1
  template:
    metadata:
      labels:
        app: my-app
        version: v1
    spec:
      containers:
        - name: app
          image: my-app:1.0.0

---
# Deployment v2 (Canary)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app-v2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: my-app
      version: v2
  template:
    metadata:
      labels:
        app: my-app
        version: v2
    spec:
      containers:
        - name: app
          image: my-app:2.0.0

---
# Service
apiVersion: v1
kind: Service
metadata:
  name: my-app
spec:
  selector:
    app: my-app
  ports:
    - port: 80
      targetPort: 3000

---
# Destination Rule
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: my-app
spec:
  host: my-app
  subsets:
    - name: v1
      labels:
        version: v1
    - name: v2
      labels:
        version: v2

---
# Virtual Service - 90/10 split
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
    - my-app
  http:
    - route:
        - destination:
            host: my-app
            subset: v1
          weight: 90
        - destination:
            host: my-app
            subset: v2
          weight: 10
```

## Circuit Breaker Pattern

```yaml
# circuit-breaker.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: my-app-circuit-breaker
spec:
  host: my-app
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
    outlierDetection:
      # Eject hosts with errors
      consecutive5xxErrors: 5
      consecutiveGatewayErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 50
```

## Rate Limiting

```yaml
# rate-limit.yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: rate-limit
  namespace: istio-system
spec:
  workloadSelector:
    labels:
      istio: ingressgateway
  configPatches:
    - applyTo: HTTP_FILTER
      match:
        context: GATEWAY
        listener:
          filterChain:
            filter:
              name: "envoy.filters.network.http_connection_manager"
      patch:
        operation: INSERT_BEFORE
        value:
          name: envoy.filters.http.local_ratelimit
          typed_config:
            "@type": type.googleapis.com/udpa.type.v1.TypedStruct
            type_url: type.googleapis.com/envoy.extensions.filters.http.local_ratelimit.v3.LocalRateLimit
            value:
              stat_prefix: http_local_rate_limiter
              token_bucket:
                max_tokens: 100
                tokens_per_fill: 100
                fill_interval: 60s
              filter_enabled:
                runtime_key: local_rate_limit_enabled
                default_value:
                  numerator: 100
                  denominator: HUNDRED
              filter_enforced:
                runtime_key: local_rate_limit_enforced
                default_value:
                  numerator: 100
                  denominator: HUNDRED
```

## Linkerd Alternative

```bash
# Install Linkerd
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh

# Check cluster
linkerd check --pre

# Install
linkerd install --crds | kubectl apply -f -
linkerd install | kubectl apply -f -

# Inject sidecar
kubectl get deploy -o yaml | linkerd inject - | kubectl apply -f -

# Or annotate namespace
kubectl annotate namespace default linkerd.io/inject=enabled
```

### Linkerd Service Profile

```yaml
# service-profile.yaml
apiVersion: linkerd.io/v1alpha2
kind: ServiceProfile
metadata:
  name: my-app.production.svc.cluster.local
  namespace: production
spec:
  routes:
    - name: GET /api/users
      condition:
        method: GET
        pathRegex: /api/users
      responseClasses:
        - condition:
            status:
              min: 500
              max: 599
          isFailure: true
      timeout: 30s
      retries:
        retryBudget:
          retryRatio: 0.2
          minRetriesPerSecond: 10
          ttl: 10s
```

## Debugging Service Mesh

```bash
# Istio debugging
istioctl analyze
istioctl proxy-status
istioctl proxy-config cluster <pod-name>
istioctl proxy-config route <pod-name>
istioctl proxy-config endpoints <pod-name>

# View Envoy config
kubectl exec <pod-name> -c istio-proxy -- pilot-agent request GET config_dump

# Check mTLS status
istioctl authn tls-check <pod-name>

# Kiali dashboard
istioctl dashboard kiali

# Jaeger tracing
istioctl dashboard jaeger

# Grafana metrics
istioctl dashboard grafana
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                  Service Mesh Best Practices                     │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Start with permissive mTLS, then migrate to strict            │
│ ☐ Use authorization policies for zero-trust                     │
│ ☐ Configure circuit breakers for all services                   │
│ ☐ Set appropriate timeouts and retries                          │
│ ☐ Enable distributed tracing                                    │
│ ☐ Monitor sidecar resource usage                                │
│ ☐ Use service entries for external services                     │
│ ☐ Test fault injection before production                        │
│ ☐ Implement gradual traffic shifting for deployments            │
│ ☐ Keep control plane highly available                           │
│ ☐ Monitor mesh performance overhead                             │
│ ☐ Use canary deployments with traffic splitting                 │
└─────────────────────────────────────────────────────────────────┘
```
