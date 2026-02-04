---
name: kubectl-basics
description: Essential kubectl commands and usage patterns
applies_to: kubernetes
---

# kubectl Basics

## Configuration

```bash
# View current context
kubectl config current-context

# List all contexts
kubectl config get-contexts

# Switch context
kubectl config use-context my-cluster

# Set default namespace
kubectl config set-context --current --namespace=production

# View kubeconfig
kubectl config view
```

## Basic Commands

### Get Resources

```bash
# List resources
kubectl get pods
kubectl get pods -n production
kubectl get pods --all-namespaces
kubectl get pods -A  # shorthand

# Wide output with more info
kubectl get pods -o wide

# Watch for changes
kubectl get pods -w

# Get specific resource
kubectl get pod my-pod

# Get multiple resource types
kubectl get pods,services,deployments

# Custom columns
kubectl get pods -o custom-columns=NAME:.metadata.name,STATUS:.status.phase

# JSON/YAML output
kubectl get pod my-pod -o yaml
kubectl get pod my-pod -o json

# JSONPath
kubectl get pods -o jsonpath='{.items[*].metadata.name}'
```

### Describe Resources

```bash
# Detailed information
kubectl describe pod my-pod
kubectl describe deployment my-deployment
kubectl describe node my-node

# Events only
kubectl describe pod my-pod | grep -A 20 Events
```

### Create Resources

```bash
# From file
kubectl apply -f manifest.yaml
kubectl apply -f ./manifests/
kubectl apply -f https://example.com/manifest.yaml

# Recursive
kubectl apply -R -f ./manifests/

# Create resource imperatively
kubectl create deployment nginx --image=nginx
kubectl create service clusterip nginx --tcp=80:80
kubectl create configmap my-config --from-literal=key=value
kubectl create secret generic my-secret --from-literal=password=secret

# Dry run (client-side)
kubectl apply -f manifest.yaml --dry-run=client

# Dry run (server-side)
kubectl apply -f manifest.yaml --dry-run=server

# Generate YAML without creating
kubectl create deployment nginx --image=nginx --dry-run=client -o yaml > deployment.yaml
```

### Update Resources

```bash
# Apply changes
kubectl apply -f manifest.yaml

# Edit in-place
kubectl edit deployment my-deployment

# Patch resource
kubectl patch deployment my-deployment -p '{"spec":{"replicas":5}}'

# Replace resource
kubectl replace -f manifest.yaml

# Set image
kubectl set image deployment/my-deployment container=image:tag

# Scale
kubectl scale deployment my-deployment --replicas=5

# Rollout
kubectl rollout status deployment/my-deployment
kubectl rollout history deployment/my-deployment
kubectl rollout undo deployment/my-deployment
kubectl rollout undo deployment/my-deployment --to-revision=2
kubectl rollout restart deployment/my-deployment
```

### Delete Resources

```bash
# Delete by name
kubectl delete pod my-pod

# Delete from file
kubectl delete -f manifest.yaml

# Delete by label
kubectl delete pods -l app=nginx

# Delete all in namespace
kubectl delete pods --all -n my-namespace

# Force delete
kubectl delete pod my-pod --grace-period=0 --force

# Delete namespace (deletes everything in it)
kubectl delete namespace my-namespace
```

## Working with Pods

### Logs

```bash
# Pod logs
kubectl logs my-pod

# Container logs (multi-container pod)
kubectl logs my-pod -c my-container

# Follow logs
kubectl logs -f my-pod

# Previous container logs
kubectl logs my-pod --previous

# Last N lines
kubectl logs my-pod --tail=100

# Since time
kubectl logs my-pod --since=1h

# All pods with label
kubectl logs -l app=nginx
```

### Exec

```bash
# Execute command
kubectl exec my-pod -- ls /app

# Interactive shell
kubectl exec -it my-pod -- /bin/sh
kubectl exec -it my-pod -- /bin/bash

# Specific container
kubectl exec -it my-pod -c my-container -- /bin/sh
```

### Copy Files

```bash
# Copy to pod
kubectl cp ./local-file my-pod:/remote/path

# Copy from pod
kubectl cp my-pod:/remote/file ./local-file

# With container
kubectl cp ./file my-pod:/path -c my-container
```

### Port Forward

```bash
# Forward local port to pod
kubectl port-forward my-pod 8080:80

# Forward to service
kubectl port-forward svc/my-service 8080:80

# Forward to deployment
kubectl port-forward deployment/my-deployment 8080:80

# Listen on all interfaces
kubectl port-forward --address 0.0.0.0 my-pod 8080:80
```

## Labels and Selectors

```bash
# Add label
kubectl label pod my-pod env=production

# Update label
kubectl label pod my-pod env=staging --overwrite

# Remove label
kubectl label pod my-pod env-

# Select by label
kubectl get pods -l app=nginx
kubectl get pods -l 'app in (nginx, apache)'
kubectl get pods -l app=nginx,env=production
kubectl get pods -l 'app!=nginx'
```

## Annotations

```bash
# Add annotation
kubectl annotate pod my-pod description="My pod"

# Update annotation
kubectl annotate pod my-pod description="Updated" --overwrite

# Remove annotation
kubectl annotate pod my-pod description-
```

## Resource Management

```bash
# View resource usage
kubectl top nodes
kubectl top pods
kubectl top pods --containers

# Resource quota
kubectl get resourcequota -n my-namespace
kubectl describe resourcequota -n my-namespace

# Limit ranges
kubectl get limitrange -n my-namespace
```

## Debugging

```bash
# Debug with ephemeral container
kubectl debug my-pod -it --image=busybox

# Debug node
kubectl debug node/my-node -it --image=ubuntu

# Run debug pod
kubectl run debug --rm -it --image=nicolaka/netshoot -- bash

# Check events
kubectl get events --sort-by='.lastTimestamp'
kubectl get events -n my-namespace

# Check API resources
kubectl api-resources
kubectl api-versions

# Explain resource
kubectl explain pod
kubectl explain pod.spec
kubectl explain pod.spec.containers
```

## Useful Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgs='kubectl get services'
alias kgd='kubectl get deployments'
alias kga='kubectl get all'
alias kd='kubectl describe'
alias kl='kubectl logs'
alias ke='kubectl exec -it'
alias kaf='kubectl apply -f'
alias kdf='kubectl delete -f'

# With namespace
alias kn='kubectl -n'
alias kprod='kubectl -n production'
alias kstag='kubectl -n staging'
```

## Plugins (krew)

```bash
# Install krew
# https://krew.sigs.k8s.io/docs/user-guide/setup/install/

# Popular plugins
kubectl krew install ctx      # Context switching
kubectl krew install ns       # Namespace switching
kubectl krew install neat     # Clean up YAML
kubectl krew install tree     # Resource hierarchy
kubectl krew install images   # Show container images

# Usage
kubectl ctx my-cluster
kubectl ns production
kubectl neat get pod my-pod -o yaml
kubectl tree deployment my-deployment
```
