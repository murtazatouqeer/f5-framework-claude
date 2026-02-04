---
name: k8s-volumes
description: Kubernetes Volumes for Pod storage
applies_to: kubernetes
---

# Kubernetes Volumes

## Overview

Volumes provide persistent storage for containers. They outlive containers but may be tied to Pod lifecycle.

## Volume Types

### emptyDir

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: shared-data
spec:
  containers:
    - name: writer
      image: busybox
      command: ["sh", "-c", "echo hello > /data/hello.txt && sleep 3600"]
      volumeMounts:
        - name: shared
          mountPath: /data

    - name: reader
      image: busybox
      command: ["sh", "-c", "cat /data/hello.txt && sleep 3600"]
      volumeMounts:
        - name: shared
          mountPath: /data

  volumes:
    - name: shared
      emptyDir: {}
```

### emptyDir with Size Limit

```yaml
volumes:
  - name: cache
    emptyDir:
      sizeLimit: 1Gi

  - name: memory-cache
    emptyDir:
      medium: Memory  # tmpfs
      sizeLimit: 256Mi
```

### hostPath

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: hostpath-example
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: docker-socket
          mountPath: /var/run/docker.sock
        - name: host-logs
          mountPath: /host-logs
          readOnly: true

  volumes:
    - name: docker-socket
      hostPath:
        path: /var/run/docker.sock
        type: Socket

    - name: host-logs
      hostPath:
        path: /var/log
        type: Directory
```

### hostPath Types

```yaml
# Type options:
# ""              - No check (default)
# DirectoryOrCreate - Create if missing
# Directory       - Must exist
# FileOrCreate    - Create if missing
# File            - Must exist
# Socket          - Unix socket must exist
# CharDevice      - Character device must exist
# BlockDevice     - Block device must exist

volumes:
  - name: data
    hostPath:
      path: /data/app
      type: DirectoryOrCreate
```

### ConfigMap Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: configmap-volume
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: config
          mountPath: /etc/config
          readOnly: true

  volumes:
    - name: config
      configMap:
        name: app-config
        # Optional: select specific keys
        items:
          - key: app.properties
            path: application.properties
          - key: log.properties
            path: logging.properties
        # Optional: set permissions
        defaultMode: 0644
```

### Secret Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-volume
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true

  volumes:
    - name: secrets
      secret:
        secretName: app-secrets
        defaultMode: 0400  # Restrictive permissions
        items:
          - key: tls.crt
            path: cert.pem
          - key: tls.key
            path: key.pem
```

### PersistentVolumeClaim

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: pvc-pod
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: data
          mountPath: /data

  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: my-pvc
```

### Projected Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: projected-volume
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: all-in-one
          mountPath: /projected

  volumes:
    - name: all-in-one
      projected:
        sources:
          # ConfigMap
          - configMap:
              name: app-config
              items:
                - key: config.yaml
                  path: config.yaml

          # Secret
          - secret:
              name: app-secrets
              items:
                - key: password
                  path: password

          # Downward API
          - downwardAPI:
              items:
                - path: labels
                  fieldRef:
                    fieldPath: metadata.labels
                - path: cpu-limit
                  resourceFieldRef:
                    containerName: app
                    resource: limits.cpu

          # Service Account Token
          - serviceAccountToken:
              path: token
              expirationSeconds: 3600
              audience: api
```

### Downward API Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: downward-api
  labels:
    app: myapp
    version: v1
  annotations:
    build: "123"
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: podinfo
          mountPath: /etc/podinfo

  volumes:
    - name: podinfo
      downwardAPI:
        items:
          - path: labels
            fieldRef:
              fieldPath: metadata.labels
          - path: annotations
            fieldRef:
              fieldPath: metadata.annotations
          - path: name
            fieldRef:
              fieldPath: metadata.name
          - path: namespace
            fieldRef:
              fieldPath: metadata.namespace
          - path: uid
            fieldRef:
              fieldPath: metadata.uid
```

## SubPath

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: subpath-example
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        # Mount specific subdirectory
        - name: data
          mountPath: /app/config
          subPath: config

        # Mount single file
        - name: data
          mountPath: /app/settings.json
          subPath: settings.json

  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: shared-pvc
```

### SubPathExpr (Variable Expansion)

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: subpath-expr
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
      volumeMounts:
        - name: logs
          mountPath: /var/log/app
          subPathExpr: $(POD_NAME)

  volumes:
    - name: logs
      persistentVolumeClaim:
        claimName: logs-pvc
```

## Volume Mount Options

```yaml
volumeMounts:
  - name: data
    mountPath: /data
    readOnly: true          # Read-only mount
    mountPropagation: None  # None, HostToContainer, Bidirectional
```

## Cloud Provider Volumes

### AWS EBS

```yaml
volumes:
  - name: aws-ebs
    awsElasticBlockStore:
      volumeID: vol-0123456789abcdef0
      fsType: ext4
```

### GCE Persistent Disk

```yaml
volumes:
  - name: gce-pd
    gcePersistentDisk:
      pdName: my-disk
      fsType: ext4
```

### Azure Disk

```yaml
volumes:
  - name: azure-disk
    azureDisk:
      diskName: my-disk
      diskURI: /subscriptions/.../disks/my-disk
      kind: Managed
      fsType: ext4
```

## CSI Volumes

```yaml
volumes:
  - name: csi-volume
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: aws-secrets
```

## Init Container with Volumes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: init-volume
spec:
  initContainers:
    - name: download
      image: busybox
      command: ["wget", "-O", "/data/file.tar.gz", "http://example.com/file.tar.gz"]
      volumeMounts:
        - name: data
          mountPath: /data

  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: data
          mountPath: /data

  volumes:
    - name: data
      emptyDir: {}
```

## Volume Commands

```bash
# List PVs
kubectl get pv

# List PVCs
kubectl get pvc

# Describe volume details
kubectl describe pvc my-pvc

# Check volume in pod
kubectl exec my-pod -- df -h

# Check mounted volumes
kubectl get pod my-pod -o jsonpath='{.spec.volumes[*].name}'

# Debug volume mounts
kubectl describe pod my-pod | grep -A5 Volumes
```

## Best Practices

1. **Use emptyDir** for temporary/cache data
2. **Use PVC** for persistent data needs
3. **Use Secrets** for sensitive data, not ConfigMaps
4. **Set readOnly** when write access not needed
5. **Use subPath** to share volumes between containers
6. **Set sizeLimit** on emptyDir to prevent disk exhaustion
7. **Consider Memory medium** for high-performance temp storage
8. **Use projected volumes** to combine multiple sources
