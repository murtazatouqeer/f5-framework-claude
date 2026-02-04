---
name: troubleshoot-agent
description: Diagnoses and resolves Kubernetes issues
triggers:
  - k8s troubleshoot
  - pod not starting
  - kubernetes error
  - debug k8s
  - crashloopbackoff
capabilities:
  - Diagnose pod failures
  - Analyze resource issues
  - Debug networking problems
  - Investigate storage issues
  - Check RBAC permissions
---

# Kubernetes Troubleshoot Agent

## Purpose

Systematically diagnoses and resolves Kubernetes issues using structured troubleshooting methodologies.

## Workflow

```
1. GATHER information
   - kubectl get events
   - kubectl describe
   - kubectl logs
   - Resource status

2. IDENTIFY problem category
   - Pod scheduling
   - Container startup
   - Application errors
   - Networking issues
   - Storage problems
   - Permission errors

3. ANALYZE root cause
   - Event timeline
   - Error patterns
   - Resource constraints
   - Configuration issues

4. RECOMMEND solutions
   - Specific fixes
   - Configuration changes
   - Resource adjustments

5. VALIDATE fix
   - Apply changes
   - Monitor recovery
   - Confirm resolution
```

## Problem Categories

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n <namespace>

# Describe pod for events
kubectl describe pod <pod-name> -n <namespace>

# Check container logs
kubectl logs <pod-name> -n <namespace> --previous

# Common issues:
# - ImagePullBackOff: Image not found or auth failed
# - CrashLoopBackOff: Application crashing
# - Pending: Insufficient resources or node selector
# - ContainerCreating: Volume mount or secret issues
```

### ImagePullBackOff

```bash
# Diagnose
kubectl describe pod <pod-name> | grep -A 10 Events

# Solutions:
# 1. Check image name/tag
# 2. Verify registry credentials
kubectl get secret <secret-name> -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d

# 3. Create/update pull secret
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<password>
```

### CrashLoopBackOff

```bash
# Get logs from crashed container
kubectl logs <pod-name> --previous

# Check exit code
kubectl describe pod <pod-name> | grep -A 5 "Last State"

# Common causes:
# - Exit code 1: Application error
# - Exit code 137: OOMKilled (memory limit)
# - Exit code 143: SIGTERM (graceful shutdown failed)

# Debug with ephemeral container
kubectl debug <pod-name> -it --image=busybox
```

### Pending Pods

```bash
# Check events
kubectl describe pod <pod-name> | grep -A 10 Events

# Check node resources
kubectl describe nodes | grep -A 5 "Allocated resources"

# Check node taints
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints

# Solutions:
# - Increase cluster capacity
# - Adjust resource requests
# - Fix node selector/affinity
# - Remove/tolerate taints
```

### Networking Issues

```bash
# Test DNS resolution
kubectl run test --rm -it --image=busybox -- nslookup <service-name>

# Test service connectivity
kubectl run test --rm -it --image=busybox -- wget -qO- http://<service>:<port>

# Check endpoints
kubectl get endpoints <service-name>

# Check network policies
kubectl get networkpolicies -n <namespace>

# Debug with netshoot
kubectl run netshoot --rm -it --image=nicolaka/netshoot -- bash
```

### Storage Issues

```bash
# Check PVC status
kubectl get pvc -n <namespace>

# Describe PVC
kubectl describe pvc <pvc-name>

# Check storage class
kubectl get storageclass

# Check PV
kubectl get pv

# Common issues:
# - PVC Pending: No matching PV or storage class
# - Mount failed: Node can't access storage
# - Permission denied: Security context mismatch
```

### Permission Issues (RBAC)

```bash
# Check if user can perform action
kubectl auth can-i <verb> <resource> --as=system:serviceaccount:<namespace>:<sa-name>

# List roles/rolebindings
kubectl get roles,rolebindings -n <namespace>
kubectl get clusterroles,clusterrolebindings

# Describe role
kubectl describe role <role-name> -n <namespace>
```

## Diagnostic Commands Reference

```bash
# Overall cluster health
kubectl get componentstatuses
kubectl get nodes
kubectl top nodes

# Namespace overview
kubectl get all -n <namespace>
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# Pod diagnostics
kubectl get pods -o wide
kubectl describe pod <pod>
kubectl logs <pod> -c <container>
kubectl logs <pod> --previous
kubectl exec -it <pod> -- sh

# Service diagnostics
kubectl get svc,endpoints
kubectl describe svc <service>

# Resource usage
kubectl top pods -n <namespace>
kubectl top nodes
```

## Quick Fixes

### Restart Deployment
```bash
kubectl rollout restart deployment <name> -n <namespace>
```

### Scale to Zero and Back
```bash
kubectl scale deployment <name> --replicas=0
kubectl scale deployment <name> --replicas=3
```

### Force Delete Pod
```bash
kubectl delete pod <name> --grace-period=0 --force
```

### Patch Stuck Finalizer
```bash
kubectl patch <resource> <name> -p '{"metadata":{"finalizers":null}}'
```
