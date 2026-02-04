---
name: k8s-helm-basics
description: Helm package manager basics and commands
applies_to: kubernetes
---

# Helm Basics

## Overview

Helm is the package manager for Kubernetes. It packages applications into charts that can be installed, upgraded, and rolled back.

## Installation

```bash
# macOS
brew install helm

# Linux (script)
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

# Windows (Chocolatey)
choco install kubernetes-helm

# Verify
helm version
```

## Repository Management

```bash
# Add repository
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add stable https://charts.helm.sh/stable
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts

# List repositories
helm repo list

# Update repositories
helm repo update

# Remove repository
helm repo remove stable

# Search charts
helm search repo nginx
helm search repo postgresql --versions
helm search hub redis  # Search Artifact Hub
```

## Installing Charts

### Basic Install

```bash
# Install from repo
helm install my-release bitnami/postgresql

# Install with custom name and namespace
helm install my-postgres bitnami/postgresql -n database --create-namespace

# Install specific version
helm install my-postgres bitnami/postgresql --version 12.5.0

# Install from local chart
helm install my-app ./mychart

# Install from URL
helm install my-app https://example.com/charts/mychart-0.1.0.tgz
```

### Install with Values

```bash
# From command line
helm install my-postgres bitnami/postgresql \
  --set auth.postgresPassword=secretpassword \
  --set primary.persistence.size=10Gi

# From values file
helm install my-postgres bitnami/postgresql -f values.yaml

# Multiple values files (later overrides earlier)
helm install my-postgres bitnami/postgresql \
  -f values.yaml \
  -f values-production.yaml

# Combined
helm install my-postgres bitnami/postgresql \
  -f values.yaml \
  --set auth.postgresPassword=secretpassword
```

### Dry Run and Debug

```bash
# Dry run - show what would be installed
helm install my-release bitnami/postgresql --dry-run

# Debug - show templates and values
helm install my-release bitnami/postgresql --dry-run --debug

# Template only - render templates locally
helm template my-release bitnami/postgresql
helm template my-release bitnami/postgresql -f values.yaml
```

## Upgrading Releases

```bash
# Upgrade release
helm upgrade my-postgres bitnami/postgresql

# Upgrade with values
helm upgrade my-postgres bitnami/postgresql -f values.yaml

# Install or upgrade (create if not exists)
helm upgrade --install my-postgres bitnami/postgresql

# Force upgrade (recreate resources)
helm upgrade my-postgres bitnami/postgresql --force

# Reset values to chart defaults
helm upgrade my-postgres bitnami/postgresql --reset-values

# Reuse values from previous release
helm upgrade my-postgres bitnami/postgresql --reuse-values

# Wait for resources to be ready
helm upgrade my-postgres bitnami/postgresql --wait --timeout 5m
```

## Managing Releases

### List Releases

```bash
# List releases in current namespace
helm list

# List all namespaces
helm list -A

# List all (including failed, pending)
helm list -a

# List with filter
helm list --filter "postgres"

# Output as JSON/YAML
helm list -o json
helm list -o yaml
```

### Release Information

```bash
# Show release status
helm status my-postgres

# Show release history
helm history my-postgres

# Get release values
helm get values my-postgres
helm get values my-postgres --all  # Include computed values

# Get release manifest
helm get manifest my-postgres

# Get release notes
helm get notes my-postgres

# Get all release info
helm get all my-postgres
```

### Rollback

```bash
# Rollback to previous revision
helm rollback my-postgres

# Rollback to specific revision
helm rollback my-postgres 3

# Dry run rollback
helm rollback my-postgres 3 --dry-run
```

### Uninstall

```bash
# Uninstall release
helm uninstall my-postgres

# Keep history (allows rollback)
helm uninstall my-postgres --keep-history

# Uninstall with namespace
helm uninstall my-postgres -n database
```

## Chart Information

```bash
# Show chart info
helm show chart bitnami/postgresql

# Show default values
helm show values bitnami/postgresql
helm show values bitnami/postgresql > values.yaml

# Show README
helm show readme bitnami/postgresql

# Show all info
helm show all bitnami/postgresql
```

## Working with Charts

### Create Chart

```bash
# Create new chart
helm create mychart

# Chart structure created:
# mychart/
# ├── Chart.yaml
# ├── values.yaml
# ├── charts/
# ├── templates/
# │   ├── deployment.yaml
# │   ├── service.yaml
# │   ├── ingress.yaml
# │   ├── hpa.yaml
# │   ├── serviceaccount.yaml
# │   ├── _helpers.tpl
# │   ├── NOTES.txt
# │   └── tests/
# └── .helmignore
```

### Package Chart

```bash
# Package chart
helm package mychart

# Package with version
helm package mychart --version 1.0.0

# Package to specific directory
helm package mychart -d ./charts
```

### Lint Chart

```bash
# Lint chart
helm lint mychart

# Lint with values
helm lint mychart -f values.yaml

# Strict mode
helm lint mychart --strict
```

## Helm Plugins

```bash
# List plugins
helm plugin list

# Install plugin
helm plugin install https://github.com/databus23/helm-diff

# Useful plugins:
# helm-diff - Show diff before upgrade
# helm-secrets - Manage encrypted secrets
# helm-unittest - Unit testing

# Use helm-diff
helm diff upgrade my-postgres bitnami/postgresql -f values.yaml
```

## Environment Variables

```bash
# Set namespace
export HELM_NAMESPACE=production

# Set kubeconfig
export KUBECONFIG=~/.kube/production-config

# Cache directory
export HELM_CACHE_HOME=~/.helm/cache

# Config directory
export HELM_CONFIG_HOME=~/.helm/config

# Data directory
export HELM_DATA_HOME=~/.helm/data
```

## Common Commands Reference

| Command | Description |
|---------|-------------|
| `helm install` | Install a chart |
| `helm upgrade` | Upgrade a release |
| `helm upgrade --install` | Install or upgrade |
| `helm rollback` | Rollback to previous |
| `helm uninstall` | Remove a release |
| `helm list` | List releases |
| `helm status` | Show release status |
| `helm history` | Show revision history |
| `helm get values` | Get release values |
| `helm get manifest` | Get release manifests |
| `helm show values` | Show chart defaults |
| `helm template` | Render templates locally |
| `helm repo add` | Add chart repository |
| `helm repo update` | Update repositories |
| `helm search repo` | Search repositories |
| `helm create` | Create new chart |
| `helm package` | Package a chart |
| `helm lint` | Validate a chart |

## Best Practices

1. **Always use specific versions** in production
2. **Use `--install` with `upgrade`** for idempotent deploys
3. **Store values files** in version control
4. **Use separate values files** per environment
5. **Dry run before applying** in production
6. **Use `helm diff`** to preview changes
7. **Enable release history** for rollback capability
8. **Use `--wait`** in CI/CD for proper status
9. **Lint charts** before packaging
10. **Pin repository versions** in production
