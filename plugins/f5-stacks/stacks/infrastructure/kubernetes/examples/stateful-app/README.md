# Stateful Application Example

A complete example of deploying a stateful application to Kubernetes using StatefulSet.

## Overview

This example demonstrates:
- StatefulSet with ordered deployment
- Persistent storage with PersistentVolumeClaims
- Headless Service for stable network identity
- Init containers for initialization
- Ordered rolling updates
- Pod management policies
- Volume snapshots and backup strategies

## Architecture

```
                    ┌─────────────┐
                    │   Service   │
                    │  (Regular)  │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼─────┐┌─────▼─────┐┌─────▼─────┐
        │   db-0    ││   db-1    ││   db-2    │
        │  (leader) ││ (replica) ││ (replica) │
        └─────┬─────┘└─────┬─────┘└─────┬─────┘
              │            │            │
        ┌─────▼─────┐┌─────▼─────┐┌─────▼─────┐
        │   PVC-0   ││   PVC-1   ││   PVC-2   │
        │   10Gi    ││   10Gi    ││   10Gi    │
        └───────────┘└───────────┘└───────────┘

    Headless Service: db-0.db-headless.stateful-app.svc.cluster.local
                      db-1.db-headless.stateful-app.svc.cluster.local
                      db-2.db-headless.stateful-app.svc.cluster.local
```

## Use Cases

- Databases (PostgreSQL, MySQL, MongoDB)
- Message queues (Kafka, RabbitMQ)
- Cache clusters (Redis Cluster)
- Distributed systems (ZooKeeper, etcd)
- Search engines (Elasticsearch)

## Prerequisites

- Kubernetes cluster 1.26+
- StorageClass with dynamic provisioning
- kubectl configured

## Quick Start

```bash
# Create namespace
kubectl create namespace stateful-app

# Apply all manifests
kubectl apply -f . -n stateful-app

# Wait for StatefulSet to be ready
kubectl rollout status statefulset/db -n stateful-app

# Verify pods (ordered naming: db-0, db-1, db-2)
kubectl get pods -n stateful-app -l app.kubernetes.io/name=db

# Check PersistentVolumeClaims
kubectl get pvc -n stateful-app
```

## Pod Identity

Each pod has a stable identity:
- **Network**: `<pod-name>.<headless-service>.<namespace>.svc.cluster.local`
- **Storage**: Dedicated PVC that survives pod restart
- **Ordinal**: Predictable index (0, 1, 2, ...)

## Scaling

```bash
# Scale up (new pods created in order)
kubectl scale statefulset db --replicas=5 -n stateful-app

# Scale down (pods deleted in reverse order)
kubectl scale statefulset db --replicas=3 -n stateful-app
```

## Updates

```bash
# Rolling update (reverse order by default)
kubectl set image statefulset/db db=postgres:16 -n stateful-app

# Check update status
kubectl rollout status statefulset/db -n stateful-app

# Rollback
kubectl rollout undo statefulset/db -n stateful-app
```

## Backup

```bash
# Create volume snapshot
kubectl apply -f volume-snapshot.yaml -n stateful-app

# List snapshots
kubectl get volumesnapshots -n stateful-app
```

## Files

| File | Description |
|------|-------------|
| `namespace.yaml` | Namespace configuration |
| `statefulset.yaml` | StatefulSet with volume claims |
| `service.yaml` | Regular and headless services |
| `configmap.yaml` | Database configuration |
| `secret.yaml` | Credentials (use external in prod) |
| `pdb.yaml` | Pod disruption budget |
| `backup-cronjob.yaml` | Automated backup job |

## Cleanup

```bash
# Delete StatefulSet (PVCs are retained)
kubectl delete statefulset db -n stateful-app

# Delete PVCs manually if needed
kubectl delete pvc -l app.kubernetes.io/name=db -n stateful-app

# Delete namespace
kubectl delete namespace stateful-app
```
