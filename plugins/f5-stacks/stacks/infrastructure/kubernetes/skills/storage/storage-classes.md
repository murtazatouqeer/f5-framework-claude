---
name: k8s-storage-classes
description: Kubernetes StorageClasses for dynamic provisioning
applies_to: kubernetes
---

# Kubernetes StorageClasses

## Overview

StorageClasses enable dynamic provisioning of PersistentVolumes. They define the provisioner, parameters, and reclaim policy for dynamically created volumes.

## Basic StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
  annotations:
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: kubernetes.io/aws-ebs
parameters:
  type: gp3
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

## AWS EBS StorageClasses

### GP3 (General Purpose SSD)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
  iops: "3000"
  throughput: "125"
  encrypted: "true"
  kmsKeyId: "arn:aws:kms:us-east-1:123456789:key/abc-123"
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### IO1/IO2 (Provisioned IOPS)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: io2-high-iops
provisioner: ebs.csi.aws.com
parameters:
  type: io2
  iopsPerGB: "50"
  encrypted: "true"
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### ST1 (Throughput Optimized HDD)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: st1-throughput
provisioner: ebs.csi.aws.com
parameters:
  type: st1
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

## GCP StorageClasses

### Standard PD

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-standard
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### SSD PD

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: ssd
provisioner: pd.csi.storage.gke.io
parameters:
  type: pd-ssd
  replication-type: regional-pd
reclaimPolicy: Retain
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

## Azure StorageClasses

### Azure Disk

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_LRS
  cachingMode: ReadOnly
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: WaitForFirstConsumer
```

### Azure Files

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: azure-file
provisioner: file.csi.azure.com
parameters:
  skuName: Standard_LRS
reclaimPolicy: Delete
allowVolumeExpansion: true
volumeBindingMode: Immediate
mountOptions:
  - dir_mode=0777
  - file_mode=0777
```

## NFS StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /exports
reclaimPolicy: Delete
volumeBindingMode: Immediate
mountOptions:
  - hard
  - nfsvers=4.1
```

## Local StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
```

### Local PV for Local StorageClass

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: local-pv-node1
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: local-storage
  local:
    path: /mnt/disks/ssd1
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: kubernetes.io/hostname
              operator: In
              values:
                - node1
```

## Volume Binding Modes

```yaml
# WaitForFirstConsumer - Bind when Pod scheduled
# Delays binding until Pod is scheduled
# Better for topology-aware storage
volumeBindingMode: WaitForFirstConsumer

# Immediate - Bind immediately
# Binds as soon as PVC created
# May cause scheduling issues in multi-zone
volumeBindingMode: Immediate
```

## Allowed Topologies

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: zone-aware
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
volumeBindingMode: WaitForFirstConsumer
allowedTopologies:
  - matchLabelExpressions:
      - key: topology.kubernetes.io/zone
        values:
          - us-east-1a
          - us-east-1b
```

## Mount Options

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: nfs-mount-options
provisioner: nfs.csi.k8s.io
parameters:
  server: nfs-server.example.com
  share: /exports
mountOptions:
  - hard
  - nfsvers=4.1
  - rsize=1048576
  - wsize=1048576
  - timeo=600
  - retrans=2
```

## Reclaim Policies

```yaml
# Delete - Delete volume when PVC deleted
reclaimPolicy: Delete

# Retain - Keep volume for manual cleanup
reclaimPolicy: Retain
```

## Default StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: standard
  annotations:
    # Set as default
    storageclass.kubernetes.io/is-default-class: "true"
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
```

```bash
# Set default via kubectl
kubectl patch storageclass standard -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# Remove default
kubectl patch storageclass old-default -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"false"}}}'
```

## Using StorageClass in PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fast-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: gp3  # Reference StorageClass
```

### Use Default StorageClass

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: default-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  # Omit storageClassName to use default
```

### Disable Dynamic Provisioning

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: manual-binding
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: ""  # Empty string disables dynamic provisioning
```

## CSI Driver StorageClasses

### Secrets Store CSI

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: secrets-store
provisioner: secrets-store.csi.k8s.io
```

### EFS CSI (AWS)

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: efs
provisioner: efs.csi.aws.com
parameters:
  provisioningMode: efs-ap
  fileSystemId: fs-123456
  directoryPerms: "700"
  gidRangeStart: "1000"
  gidRangeEnd: "2000"
  basePath: "/dynamic_provisioning"
```

### Longhorn

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: longhorn
provisioner: driver.longhorn.io
parameters:
  numberOfReplicas: "3"
  staleReplicaTimeout: "2880"
  fromBackup: ""
reclaimPolicy: Delete
allowVolumeExpansion: true
```

## StorageClass Commands

```bash
# List StorageClasses
kubectl get storageclass
kubectl get sc

# Describe StorageClass
kubectl describe sc gp3

# Get default StorageClass
kubectl get sc -o jsonpath='{.items[?(@.metadata.annotations.storageclass\.kubernetes\.io/is-default-class=="true")].metadata.name}'

# Check provisioner
kubectl get sc -o custom-columns=NAME:.metadata.name,PROVISIONER:.provisioner

# Delete StorageClass
kubectl delete sc old-class
```

## Best Practices

1. **Set a default StorageClass** for convenience
2. **Use WaitForFirstConsumer** for topology-aware storage
3. **Enable volume expansion** for flexibility
4. **Use appropriate reclaim policy** (Retain for production data)
5. **Configure encryption** for sensitive data
6. **Set IOPS/throughput** based on workload requirements
7. **Use topology constraints** for multi-zone clusters
8. **Monitor provisioner health** and capacity
