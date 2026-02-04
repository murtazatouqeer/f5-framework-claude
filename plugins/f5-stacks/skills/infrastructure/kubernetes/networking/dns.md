---
name: k8s-dns
description: Kubernetes DNS and service discovery
applies_to: kubernetes
---

# Kubernetes DNS

## DNS Overview

CoreDNS is the default DNS server in Kubernetes. It provides service discovery and name resolution.

## DNS Record Types

### Service DNS

```
# ClusterIP Service
<service>.<namespace>.svc.cluster.local

# Examples
api.production.svc.cluster.local
api.production.svc
api.production
api  # Same namespace

# Resolves to: ClusterIP address
```

### Headless Service DNS

```
# Headless Service (clusterIP: None)
<service>.<namespace>.svc.cluster.local

# Resolves to: All Pod IPs (A records)

# Individual Pod DNS
<pod-name>.<service>.<namespace>.svc.cluster.local

# StatefulSet Pod DNS
postgres-0.postgres-headless.production.svc.cluster.local
postgres-1.postgres-headless.production.svc.cluster.local
```

### Pod DNS

```
# Pod A record (when hostname/subdomain set)
<hostname>.<subdomain>.<namespace>.svc.cluster.local

# Pod IP-based record
<pod-ip-dashed>.<namespace>.pod.cluster.local
10-1-2-3.production.pod.cluster.local
```

## DNS Configuration

### CoreDNS ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns
  namespace: kube-system
data:
  Corefile: |
    .:53 {
        errors
        health {
           lameduck 5s
        }
        ready
        kubernetes cluster.local in-addr.arpa ip6.arpa {
           pods insecure
           fallthrough in-addr.arpa ip6.arpa
           ttl 30
        }
        prometheus :9153
        forward . /etc/resolv.conf {
           max_concurrent 1000
        }
        cache 30
        loop
        reload
        loadbalance
    }
```

### Custom DNS Entries

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: coredns-custom
  namespace: kube-system
data:
  custom.server: |
    example.com:53 {
        forward . 10.0.0.1
    }
  custom.override: |
    hosts {
        10.0.0.100 custom.example.com
        fallthrough
    }
```

## Pod DNS Configuration

### dnsPolicy Options

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  # Default - inherit from node
  dnsPolicy: Default

  # ClusterFirst (default for pods)
  dnsPolicy: ClusterFirst

  # ClusterFirstWithHostNet
  dnsPolicy: ClusterFirstWithHostNet
  hostNetwork: true

  # None - custom DNS config required
  dnsPolicy: None
```

### Custom DNS Config

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  dnsPolicy: None
  dnsConfig:
    nameservers:
      - 10.0.0.1
      - 8.8.8.8
    searches:
      - production.svc.cluster.local
      - svc.cluster.local
      - cluster.local
    options:
      - name: ndots
        value: "2"
      - name: edns0
```

### Optimize DNS Resolution

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: api
spec:
  dnsConfig:
    options:
      # Reduce DNS lookups for FQDNs
      - name: ndots
        value: "2"
      # Enable EDNS for larger responses
      - name: edns0
      # Single request mode
      - name: single-request-reopen
```

## ExternalName Service

```yaml
# Map internal name to external DNS
apiVersion: v1
kind: Service
metadata:
  name: external-db
  namespace: production
spec:
  type: ExternalName
  externalName: db.external-provider.com

# Usage: external-db.production.svc.cluster.local
# Resolves to: CNAME db.external-provider.com
```

## Headless Service for StatefulSets

```yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-headless
  namespace: production
spec:
  clusterIP: None
  selector:
    app: postgres
  ports:
    - port: 5432

---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres-headless
  replicas: 3
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: postgres:16
```

## DNS Debugging

```bash
# Check CoreDNS pods
kubectl get pods -n kube-system -l k8s-app=kube-dns

# View CoreDNS logs
kubectl logs -n kube-system -l k8s-app=kube-dns

# Test DNS resolution
kubectl run test-dns --rm -it --image=busybox:1.36 -- nslookup api.production

# Detailed DNS test
kubectl run test-dns --rm -it --image=nicolaka/netshoot -- bash
# Inside pod:
nslookup api.production.svc.cluster.local
dig api.production.svc.cluster.local
host api.production.svc.cluster.local

# Check /etc/resolv.conf
kubectl exec -it my-pod -- cat /etc/resolv.conf
```

## DNS Troubleshooting

### Common Issues

```bash
# Issue: DNS resolution slow
# Solution: Reduce ndots value
dnsConfig:
  options:
    - name: ndots
      value: "2"

# Issue: External DNS not resolving
# Check: CoreDNS forward configuration
kubectl get configmap coredns -n kube-system -o yaml

# Issue: Pod can't resolve services
# Check: DNS Policy and search domains
kubectl exec my-pod -- cat /etc/resolv.conf
```

### DNS Policy Comparison

| Policy | Use Case | DNS Server |
|--------|----------|------------|
| ClusterFirst | Default for pods | CoreDNS first, then upstream |
| Default | hostNetwork pods | Node's resolv.conf |
| None | Custom DNS setup | dnsConfig only |
| ClusterFirstWithHostNet | hostNetwork with cluster DNS | CoreDNS first |

## DNS Metrics

```yaml
# CoreDNS exposes Prometheus metrics
# :9153/metrics

# Key metrics:
# coredns_dns_requests_total
# coredns_dns_responses_total
# coredns_dns_request_duration_seconds
# coredns_cache_hits_total
# coredns_cache_misses_total
```

## Best Practices

1. **Use short names** when possible within same namespace
2. **Set appropriate ndots** to reduce DNS queries
3. **Use headless services** for stateful applications
4. **Monitor CoreDNS** for performance and errors
5. **Configure proper resource limits** for CoreDNS pods
6. **Use ExternalName** for external service references
7. **Consider DNS caching** at application level for performance
