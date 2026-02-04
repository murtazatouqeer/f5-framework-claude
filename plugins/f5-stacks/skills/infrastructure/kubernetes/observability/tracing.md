---
name: k8s-tracing
description: Kubernetes distributed tracing with OpenTelemetry and Jaeger
applies_to: kubernetes
---

# Kubernetes Distributed Tracing

## Overview

Distributed tracing tracks requests across microservices, providing visibility into request flow, latency, and errors.

## OpenTelemetry

### OpenTelemetry Collector

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
    spec:
      containers:
        - name: otel-collector
          image: otel/opentelemetry-collector-contrib:0.91.0
          ports:
            - containerPort: 4317  # OTLP gRPC
            - containerPort: 4318  # OTLP HTTP
            - containerPort: 9411  # Zipkin
            - containerPort: 14268 # Jaeger
          volumeMounts:
            - name: config
              mountPath: /etc/otelcol-contrib

      volumes:
        - name: config
          configMap:
            name: otel-collector-config

---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
  namespace: observability
spec:
  selector:
    app: otel-collector
  ports:
    - name: otlp-grpc
      port: 4317
    - name: otlp-http
      port: 4318
    - name: zipkin
      port: 9411
    - name: jaeger
      port: 14268
```

### Collector Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: observability
data:
  config.yaml: |
    receivers:
      otlp:
        protocols:
          grpc:
            endpoint: 0.0.0.0:4317
          http:
            endpoint: 0.0.0.0:4318

      zipkin:
        endpoint: 0.0.0.0:9411

      jaeger:
        protocols:
          thrift_http:
            endpoint: 0.0.0.0:14268

    processors:
      batch:
        timeout: 1s
        send_batch_size: 1024

      memory_limiter:
        check_interval: 1s
        limit_mib: 1000
        spike_limit_mib: 200

      resource:
        attributes:
          - key: environment
            value: production
            action: upsert

    exporters:
      jaeger:
        endpoint: jaeger-collector:14250
        tls:
          insecure: true

      otlp:
        endpoint: tempo:4317
        tls:
          insecure: true

      logging:
        loglevel: debug

    extensions:
      health_check:
      pprof:
      zpages:

    service:
      extensions: [health_check, pprof, zpages]
      pipelines:
        traces:
          receivers: [otlp, zipkin, jaeger]
          processors: [memory_limiter, batch, resource]
          exporters: [jaeger, logging]
```

## Jaeger

### Jaeger Installation

```bash
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger \
  --namespace observability \
  --create-namespace \
  --set provisionDataStore.cassandra=false \
  --set allInOne.enabled=true \
  --set storage.type=memory
```

### Jaeger All-in-One

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: jaeger
  namespace: observability
spec:
  replicas: 1
  selector:
    matchLabels:
      app: jaeger
  template:
    metadata:
      labels:
        app: jaeger
    spec:
      containers:
        - name: jaeger
          image: jaegertracing/all-in-one:1.52
          ports:
            - containerPort: 5775   # UDP agent zipkin.thrift
            - containerPort: 6831   # UDP agent jaeger.thrift
            - containerPort: 6832   # UDP agent jaeger.thrift
            - containerPort: 5778   # HTTP config
            - containerPort: 16686  # HTTP UI
            - containerPort: 14268  # HTTP collector
            - containerPort: 14250  # gRPC collector
            - containerPort: 9411   # HTTP zipkin
          env:
            - name: COLLECTOR_ZIPKIN_HOST_PORT
              value: ":9411"
          resources:
            requests:
              cpu: 100m
              memory: 256Mi
            limits:
              cpu: 500m
              memory: 1Gi

---
apiVersion: v1
kind: Service
metadata:
  name: jaeger
  namespace: observability
spec:
  selector:
    app: jaeger
  ports:
    - name: ui
      port: 16686
    - name: collector-http
      port: 14268
    - name: collector-grpc
      port: 14250
```

## Application Instrumentation

### Node.js with OpenTelemetry

```javascript
// tracing.js
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-grpc');
const { Resource } = require('@opentelemetry/resources');
const { SemanticResourceAttributes } = require('@opentelemetry/semantic-conventions');

const sdk = new NodeSDK({
  resource: new Resource({
    [SemanticResourceAttributes.SERVICE_NAME]: 'my-service',
    [SemanticResourceAttributes.SERVICE_VERSION]: '1.0.0',
    [SemanticResourceAttributes.DEPLOYMENT_ENVIRONMENT]: 'production',
  }),
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT || 'http://otel-collector:4317',
  }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();

process.on('SIGTERM', () => {
  sdk.shutdown().then(() => process.exit(0));
});
```

### Python with OpenTelemetry

```python
# tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME

resource = Resource(attributes={
    SERVICE_NAME: "my-service"
})

provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint="otel-collector:4317", insecure=True)
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

# Usage
with tracer.start_as_current_span("my-operation") as span:
    span.set_attribute("key", "value")
    # do work
```

## Kubernetes Deployment with Tracing

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
      containers:
        - name: api
          image: api:1.0.0
          ports:
            - containerPort: 8080
          env:
            # OpenTelemetry configuration
            - name: OTEL_SERVICE_NAME
              value: "api"
            - name: OTEL_EXPORTER_OTLP_ENDPOINT
              value: "http://otel-collector.observability:4317"
            - name: OTEL_EXPORTER_OTLP_PROTOCOL
              value: "grpc"
            - name: OTEL_RESOURCE_ATTRIBUTES
              value: "service.namespace=production,service.version=1.0.0"
            - name: OTEL_TRACES_SAMPLER
              value: "parentbased_traceidratio"
            - name: OTEL_TRACES_SAMPLER_ARG
              value: "0.1"  # 10% sampling

            # Inject pod metadata
            - name: OTEL_RESOURCE_ATTRIBUTES_POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: OTEL_RESOURCE_ATTRIBUTES_NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
```

## Sampling Strategies

### Always On

```yaml
env:
  - name: OTEL_TRACES_SAMPLER
    value: "always_on"
```

### Probability Sampling

```yaml
env:
  - name: OTEL_TRACES_SAMPLER
    value: "traceidratio"
  - name: OTEL_TRACES_SAMPLER_ARG
    value: "0.1"  # 10%
```

### Parent-Based Sampling

```yaml
env:
  - name: OTEL_TRACES_SAMPLER
    value: "parentbased_traceidratio"
  - name: OTEL_TRACES_SAMPLER_ARG
    value: "0.1"
```

## Context Propagation

### W3C Trace Context

```yaml
env:
  - name: OTEL_PROPAGATORS
    value: "tracecontext,baggage"
```

### Headers

```
traceparent: 00-0af7651916cd43dd8448eb211c80319c-b7ad6b7169203331-01
tracestate: congo=t61rcWkgMzE
```

## Service Mesh Integration

### Istio Tracing

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    enableTracing: true
    defaultConfig:
      tracing:
        sampling: 10.0  # 10%
        zipkin:
          address: jaeger-collector.observability:9411
```

### Linkerd Tracing

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: linkerd-config
  namespace: linkerd
data:
  values: |
    tracing:
      enabled: true
      collector:
        jaeger:
          addr: jaeger-collector.observability:9411
```

## Tempo (Grafana)

### Tempo Installation

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm install tempo grafana/tempo \
  --namespace observability
```

### Tempo Configuration

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: tempo-config
  namespace: observability
data:
  tempo.yaml: |
    server:
      http_listen_port: 3200

    distributor:
      receivers:
        otlp:
          protocols:
            grpc:
            http:
        jaeger:
          protocols:
            thrift_http:
        zipkin:

    ingester:
      trace_idle_period: 10s
      max_block_bytes: 1_000_000
      max_block_duration: 5m

    compactor:
      compaction:
        compaction_window: 1h
        max_block_bytes: 100_000_000
        block_retention: 1h

    storage:
      trace:
        backend: local
        local:
          path: /tmp/tempo/blocks
```

## Commands

```bash
# Port forward Jaeger UI
kubectl port-forward svc/jaeger 16686:16686 -n observability

# Port forward Tempo
kubectl port-forward svc/tempo 3200:3200 -n observability

# Check collector logs
kubectl logs -l app=otel-collector -n observability

# Verify traces are being collected
curl http://localhost:16686/api/services
```

## Best Practices

1. **Use OpenTelemetry** for vendor-neutral instrumentation
2. **Implement sampling** in production (1-10%)
3. **Propagate context** across service boundaries
4. **Add meaningful span attributes** (user_id, request_id)
5. **Set appropriate span names** - use operation names
6. **Record errors** with error attributes
7. **Use baggage** for cross-cutting concerns
8. **Correlate with logs and metrics** via trace_id
9. **Set up retention policies** for trace storage
10. **Create trace-based alerts** for latency/errors
