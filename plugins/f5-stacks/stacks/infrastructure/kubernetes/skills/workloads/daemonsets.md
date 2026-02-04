---
name: k8s-daemonsets
description: Kubernetes DaemonSets for node-level workloads
applies_to: kubernetes
---

# Kubernetes DaemonSets

## Overview

DaemonSets ensure that all (or some) nodes run a copy of a Pod. Use cases include:
- Log collection (Fluentd, Filebeat)
- Node monitoring (Node Exporter, Datadog Agent)
- Cluster storage (Ceph, GlusterFS)
- Network plugins (Calico, Cilium)

## Basic DaemonSet

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
  namespace: kube-system
  labels:
    app: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
        - name: fluentd
          image: fluent/fluentd:v1.16
          resources:
            limits:
              memory: 200Mi
            requests:
              cpu: 100m
              memory: 200Mi
          volumeMounts:
            - name: varlog
              mountPath: /var/log
            - name: containers
              mountPath: /var/lib/docker/containers
              readOnly: true
      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: containers
          hostPath:
            path: /var/lib/docker/containers
```

## Production DaemonSet (Node Exporter)

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: node-exporter
  namespace: monitoring
  labels:
    app.kubernetes.io/name: node-exporter
    app.kubernetes.io/component: metrics
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: node-exporter

  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1

  template:
    metadata:
      labels:
        app.kubernetes.io/name: node-exporter
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "9100"
    spec:
      hostPID: true
      hostNetwork: true

      serviceAccountName: node-exporter

      securityContext:
        runAsUser: 65534
        runAsGroup: 65534
        runAsNonRoot: true

      tolerations:
        # Run on all nodes including masters
        - operator: Exists

      containers:
        - name: node-exporter
          image: prom/node-exporter:v1.7.0

          args:
            - --path.procfs=/host/proc
            - --path.sysfs=/host/sys
            - --path.rootfs=/host/root
            - --collector.filesystem.mount-points-exclude=^/(dev|proc|sys|var/lib/docker/.+|var/lib/kubelet/.+)($|/)
            - --collector.filesystem.fs-types-exclude=^(autofs|binfmt_misc|cgroup|configfs|debugfs|devpts|devtmpfs|fusectl|hugetlbfs|mqueue|overlay|proc|procfs|pstore|rpc_pipefs|securityfs|squashfs|sysfs|tracefs)$

          ports:
            - containerPort: 9100
              hostPort: 9100
              name: metrics
              protocol: TCP

          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 250m
              memory: 128Mi

          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop:
                - ALL
              add:
                - SYS_TIME

          volumeMounts:
            - name: proc
              mountPath: /host/proc
              readOnly: true
            - name: sys
              mountPath: /host/sys
              readOnly: true
            - name: root
              mountPath: /host/root
              readOnly: true
              mountPropagation: HostToContainer

      volumes:
        - name: proc
          hostPath:
            path: /proc
        - name: sys
          hostPath:
            path: /sys
        - name: root
          hostPath:
            path: /
```

## Fluent Bit Log Collector

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: logging
  labels:
    app: fluent-bit
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      serviceAccountName: fluent-bit

      tolerations:
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
        - key: node-role.kubernetes.io/master
          operator: Exists
          effect: NoSchedule

      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:2.2

          ports:
            - containerPort: 2020
              name: http

          env:
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName

          resources:
            requests:
              cpu: 50m
              memory: 64Mi
            limits:
              cpu: 200m
              memory: 256Mi

          volumeMounts:
            - name: varlog
              mountPath: /var/log
              readOnly: true
            - name: containers
              mountPath: /var/lib/docker/containers
              readOnly: true
            - name: config
              mountPath: /fluent-bit/etc
            - name: machine-id
              mountPath: /etc/machine-id
              readOnly: true

      volumes:
        - name: varlog
          hostPath:
            path: /var/log
        - name: containers
          hostPath:
            path: /var/lib/docker/containers
        - name: config
          configMap:
            name: fluent-bit-config
        - name: machine-id
          hostPath:
            path: /etc/machine-id
            type: File
```

## Node Selection

### Run on Specific Nodes

```yaml
spec:
  template:
    spec:
      nodeSelector:
        node-type: worker
```

### Using Affinity

```yaml
spec:
  template:
    spec:
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: kubernetes.io/os
                    operator: In
                    values:
                      - linux
                  - key: node-type
                    operator: NotIn
                    values:
                      - gpu
```

### Tolerations for All Nodes

```yaml
spec:
  template:
    spec:
      tolerations:
        # Run on all nodes
        - operator: Exists

        # Or specific tolerations
        - key: node-role.kubernetes.io/control-plane
          operator: Exists
          effect: NoSchedule
        - key: node.kubernetes.io/not-ready
          operator: Exists
          effect: NoExecute
```

## Update Strategies

### Rolling Update

```yaml
spec:
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1  # Or percentage like "10%"
```

### OnDelete

```yaml
spec:
  updateStrategy:
    type: OnDelete  # Manual deletion triggers update
```

## Priority and Preemption

```yaml
spec:
  template:
    spec:
      priorityClassName: system-node-critical
```

## DaemonSet Commands

```bash
# Create DaemonSet
kubectl apply -f daemonset.yaml

# List DaemonSets
kubectl get daemonsets -n kube-system

# Describe DaemonSet
kubectl describe daemonset fluentd -n kube-system

# Rollout status
kubectl rollout status daemonset/fluentd -n kube-system

# Update image
kubectl set image daemonset/fluentd fluentd=fluent/fluentd:v1.17 -n kube-system

# Rollout history
kubectl rollout history daemonset/fluentd -n kube-system

# Rollback
kubectl rollout undo daemonset/fluentd -n kube-system

# Delete DaemonSet
kubectl delete daemonset fluentd -n kube-system
```

## Host Access Patterns

### Host Network

```yaml
spec:
  template:
    spec:
      hostNetwork: true
      dnsPolicy: ClusterFirstWithHostNet
```

### Host PID/IPC

```yaml
spec:
  template:
    spec:
      hostPID: true   # Access host processes
      hostIPC: true   # Access host IPC namespace
```

### Host Volumes

```yaml
volumes:
  - name: host-root
    hostPath:
      path: /
      type: Directory
  - name: host-proc
    hostPath:
      path: /proc
      type: Directory
  - name: host-sys
    hostPath:
      path: /sys
      type: Directory
```

## Best Practices

1. **Use resource limits** - DaemonSets run on every node
2. **Configure tolerations** - To run on all node types
3. **Use priority classes** - For critical system components
4. **Minimize host access** - Only what's necessary
5. **Configure proper update strategy** - RollingUpdate with maxUnavailable
6. **Use node selectors** - When not needed on all nodes
7. **Mount host paths read-only** - When possible
