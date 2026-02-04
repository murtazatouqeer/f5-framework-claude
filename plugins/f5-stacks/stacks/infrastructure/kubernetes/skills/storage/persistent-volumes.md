---
name: k8s-persistent-volumes
description: Kubernetes PersistentVolumes and PersistentVolumeClaims
applies_to: kubernetes
---

# Kubernetes PersistentVolumes

## Overview

PersistentVolumes (PV) and PersistentVolumeClaims (PVC) provide an API for storage that abstracts implementation details.

## PersistentVolume

### Basic PV

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-data
  labels:
    type: local
    environment: production
spec:
  capacity:
    storage: 10Gi

  accessModes:
    - ReadWriteOnce

  persistentVolumeReclaimPolicy: Retain

  storageClassName: manual

  hostPath:
    path: /mnt/data
```

### NFS PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-nfs
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteMany
  persistentVolumeReclaimPolicy: Retain
  storageClassName: nfs
  mountOptions:
    - hard
    - nfsvers=4.1
  nfs:
    server: nfs-server.example.com
    path: /exports/data
```

### AWS EBS PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-aws-ebs
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: gp3
  awsElasticBlockStore:
    volumeID: vol-0123456789abcdef0
    fsType: ext4
  nodeAffinity:
    required:
      nodeSelectorTerms:
        - matchExpressions:
            - key: topology.kubernetes.io/zone
              operator: In
              values:
                - us-east-1a
```

### GCE PD PersistentVolume

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-gce-pd
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Delete
  storageClassName: standard
  gcePersistentDisk:
    pdName: my-data-disk
    fsType: ext4
```

## Access Modes

| Mode | Abbreviation | Description |
|------|--------------|-------------|
| ReadWriteOnce | RWO | Single node read/write |
| ReadOnlyMany | ROX | Many nodes read-only |
| ReadWriteMany | RWX | Many nodes read/write |
| ReadWriteOncePod | RWOP | Single pod read/write |

```yaml
spec:
  accessModes:
    - ReadWriteOnce
    # - ReadOnlyMany
    # - ReadWriteMany
    # - ReadWriteOncePod
```

## Reclaim Policies

```yaml
spec:
  # Retain - Manual cleanup required
  persistentVolumeReclaimPolicy: Retain

  # Delete - Automatically delete storage
  persistentVolumeReclaimPolicy: Delete

  # Recycle - Basic scrub (deprecated)
  persistentVolumeReclaimPolicy: Recycle
```

## PersistentVolumeClaim

### Basic PVC

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
  namespace: production
spec:
  accessModes:
    - ReadWriteOnce

  resources:
    requests:
      storage: 10Gi

  storageClassName: standard
```

### PVC with Selector

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: ""  # Empty for manual binding
  selector:
    matchLabels:
      type: local
      environment: production
    matchExpressions:
      - key: tier
        operator: In
        values:
          - fast
          - ssd
```

### PVC with Volume Mode

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: block-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: fast-ssd
  volumeMode: Block  # or Filesystem (default)
```

## Using PVC in Pods

### Single Container

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
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
        claimName: data-pvc
```

### Block Volume

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: block-pod
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeDevices:
        - name: data
          devicePath: /dev/xvda

  volumes:
    - name: data
      persistentVolumeClaim:
        claimName: block-pvc
```

## StatefulSet with PVC Template

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
spec:
  serviceName: postgres
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
          volumeMounts:
            - name: data
              mountPath: /var/lib/postgresql/data

  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes:
          - ReadWriteOnce
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
```

## Volume Expansion

### Enable in StorageClass

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: expandable
provisioner: kubernetes.io/aws-ebs
allowVolumeExpansion: true
```

### Expand PVC

```yaml
# Update PVC with larger size
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Gi  # Increased from 10Gi
  storageClassName: expandable
```

```bash
# Expand via kubectl
kubectl patch pvc data-pvc -p '{"spec":{"resources":{"requests":{"storage":"50Gi"}}}}'
```

## Volume Cloning

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: cloned-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
  dataSource:
    kind: PersistentVolumeClaim
    name: source-pvc
```

## Volume Snapshots

### VolumeSnapshotClass

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshotClass
metadata:
  name: csi-snapclass
driver: ebs.csi.aws.com
deletionPolicy: Delete
```

### Create Snapshot

```yaml
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: data-snapshot
spec:
  volumeSnapshotClassName: csi-snapclass
  source:
    persistentVolumeClaimName: data-pvc
```

### Restore from Snapshot

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: restored-pvc
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
  dataSource:
    name: data-snapshot
    kind: VolumeSnapshot
    apiGroup: snapshot.storage.k8s.io
```

## PV/PVC Lifecycle

```
PV States:
Available → Bound → Released → (Retained/Deleted)

PVC States:
Pending → Bound → (Lost if PV deleted)
```

## PV/PVC Commands

```bash
# List PersistentVolumes
kubectl get pv
kubectl get pv -o wide

# List PersistentVolumeClaims
kubectl get pvc
kubectl get pvc -n production

# Describe PV/PVC
kubectl describe pv pv-data
kubectl describe pvc data-pvc

# Check binding
kubectl get pvc data-pvc -o jsonpath='{.spec.volumeName}'

# Delete PVC
kubectl delete pvc data-pvc

# Patch reclaim policy
kubectl patch pv pv-data -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'

# Check storage capacity
kubectl get pv -o custom-columns=NAME:.metadata.name,CAPACITY:.spec.capacity.storage,STATUS:.status.phase

# Watch PVC status
kubectl get pvc -w

# Get events
kubectl get events --field-selector involvedObject.kind=PersistentVolumeClaim
```

## Troubleshooting

### PVC Stuck in Pending

```bash
# Check events
kubectl describe pvc my-pvc

# Common causes:
# - No matching PV available
# - StorageClass not found
# - Insufficient storage capacity
# - Volume affinity mismatch
```

### PV Stuck in Released

```bash
# Remove claimRef to make Available again
kubectl patch pv pv-data -p '{"spec":{"claimRef":null}}'
```

### Data Migration

```bash
# Create job to copy data between PVCs
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: pvc-migration
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: busybox
          command: ["sh", "-c", "cp -av /source/* /dest/"]
          volumeMounts:
            - name: source
              mountPath: /source
            - name: dest
              mountPath: /dest
      volumes:
        - name: source
          persistentVolumeClaim:
            claimName: old-pvc
        - name: dest
          persistentVolumeClaim:
            claimName: new-pvc
      restartPolicy: Never
EOF
```

## Best Practices

1. **Use StorageClasses** for dynamic provisioning
2. **Set appropriate reclaim policy** (Retain for important data)
3. **Use volume snapshots** for backups
4. **Enable volume expansion** for growth
5. **Use ReadWriteOncePod** for exclusive access
6. **Monitor storage capacity** and set alerts
7. **Use labels** for PV selection
8. **Consider topology constraints** for cloud volumes
