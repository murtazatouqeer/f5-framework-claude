---
name: k8s-helm-dependencies
description: Helm chart dependencies and subcharts
applies_to: kubernetes
---

# Helm Chart Dependencies

## Overview

Helm charts can depend on other charts. Dependencies are defined in Chart.yaml and managed with `helm dependency` commands.

## Defining Dependencies

### Basic Dependencies

```yaml
# Chart.yaml
apiVersion: v2
name: myapp
version: 1.0.0

dependencies:
  - name: postgresql
    version: "12.5.0"
    repository: "https://charts.bitnami.com/bitnami"

  - name: redis
    version: "17.11.0"
    repository: "https://charts.bitnami.com/bitnami"
```

### Version Ranges

```yaml
dependencies:
  # Exact version
  - name: postgresql
    version: "12.5.0"
    repository: "https://charts.bitnami.com/bitnami"

  # Patch range (12.5.x)
  - name: postgresql
    version: "~12.5.0"
    repository: "https://charts.bitnami.com/bitnami"

  # Minor range (12.x.x)
  - name: postgresql
    version: "^12.0.0"
    repository: "https://charts.bitnami.com/bitnami"

  # Range
  - name: postgresql
    version: ">=12.0.0 <13.0.0"
    repository: "https://charts.bitnami.com/bitnami"
```

### Conditional Dependencies

```yaml
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled

  - name: redis
    version: "17.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
```

```yaml
# values.yaml
postgresql:
  enabled: true

redis:
  enabled: false
```

### Tagged Dependencies

```yaml
# Chart.yaml
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    tags:
      - database

  - name: mysql
    version: "9.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    tags:
      - database

  - name: redis
    version: "17.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    tags:
      - cache
```

```yaml
# values.yaml
tags:
  database: true
  cache: false
```

### Alias Dependencies

```yaml
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    alias: primary-db

  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    alias: replica-db
```

```yaml
# values.yaml
primary-db:
  auth:
    database: primary

replica-db:
  auth:
    database: replica
```

## Local Dependencies

### File Path

```yaml
dependencies:
  - name: common
    version: "1.0.0"
    repository: "file://../common"

  - name: shared-lib
    version: "2.0.0"
    repository: "file://./charts/shared-lib"
```

### OCI Registry

```yaml
dependencies:
  - name: mylib
    version: "1.0.0"
    repository: "oci://myregistry.azurecr.io/helm"
```

## Configuring Dependencies

### Pass Values to Dependencies

```yaml
# values.yaml
postgresql:
  auth:
    postgresPassword: "secretpassword"
    database: "myapp"
  primary:
    persistence:
      enabled: true
      size: 10Gi
  metrics:
    enabled: true

redis:
  architecture: standalone
  auth:
    enabled: true
    password: "redispassword"
```

### Import Values from Dependencies

```yaml
# Chart.yaml
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    import-values:
      - data
```

```yaml
# Advanced import
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    import-values:
      - child: auth
        parent: database

      - child: primary.service
        parent: databaseService
```

### Global Values

```yaml
# values.yaml
global:
  imageRegistry: myregistry.example.com
  imagePullSecrets:
    - myregistrykey
  storageClass: fast-ssd

postgresql:
  # Will use global.imageRegistry
```

## Managing Dependencies

### Commands

```bash
# Update dependencies (download to charts/)
helm dependency update myapp

# List dependencies
helm dependency list myapp

# Build dependencies from lock file
helm dependency build myapp

# Verify Chart.lock exists
cat myapp/Chart.lock
```

### Chart.lock

```yaml
# Chart.lock (auto-generated)
dependencies:
  - name: postgresql
    repository: https://charts.bitnami.com/bitnami
    version: 12.5.0
  - name: redis
    repository: https://charts.bitnami.com/bitnami
    version: 17.11.0
digest: sha256:abc123...
generated: "2024-01-15T10:00:00.000000000Z"
```

## Accessing Dependency Values in Templates

```yaml
# Access postgresql subchart values
{{ .Values.postgresql.auth.database }}
{{ .Values.postgresql.primary.service.port }}

# Access aliased dependency
{{ .Values.primary-db.auth.database }}

# Check if dependency is enabled
{{- if .Values.postgresql.enabled }}
DATABASE_HOST: {{ .Release.Name }}-postgresql
{{- end }}
```

## Override Dependency Templates

### Create Override Template

```yaml
# templates/postgresql/configmap.yaml
# This overrides the postgresql chart's configmap
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-postgresql-custom
data:
  custom-config: "value"
```

### Disable Dependency Resource

```yaml
# values.yaml
postgresql:
  # Disable built-in service
  primary:
    service:
      type: ClusterIP

  # Create external secret instead of built-in
  auth:
    existingSecret: my-external-secret
```

## Subchart Condition Examples

### Database Selection

```yaml
# Chart.yaml
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled

  - name: mysql
    version: "9.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: mysql.enabled

  - name: mongodb
    version: "13.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: mongodb.enabled
```

```yaml
# values.yaml (use PostgreSQL)
postgresql:
  enabled: true
mysql:
  enabled: false
mongodb:
  enabled: false
```

### Environment-Based

```yaml
# values-dev.yaml
postgresql:
  enabled: true
  primary:
    persistence:
      enabled: false

# values-prod.yaml
postgresql:
  enabled: true
  primary:
    persistence:
      enabled: true
      size: 100Gi
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
```

## Library Charts

### Define Library Chart

```yaml
# common/Chart.yaml
apiVersion: v2
name: common
type: library
version: 1.0.0
```

```yaml
# common/templates/_labels.tpl
{{- define "common.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
```

### Use Library Chart

```yaml
# myapp/Chart.yaml
dependencies:
  - name: common
    version: "1.x.x"
    repository: "file://../common"
```

```yaml
# myapp/templates/deployment.yaml
metadata:
  labels:
    {{- include "common.labels" . | nindent 4 }}
```

## Best Practices

1. **Pin versions** in production (exact or patch range)
2. **Use Chart.lock** for reproducible builds
3. **Prefer conditions** over tags for single dependencies
4. **Use aliases** when needing multiple instances
5. **Test dependency updates** in staging first
6. **Keep dependencies minimal** - only what's needed
7. **Document dependency configuration** in README
8. **Use global values** for shared configuration
9. **Version library charts** carefully
10. **Review dependency security** updates regularly

## Commands Reference

| Command | Description |
|---------|-------------|
| `helm dependency update` | Download dependencies |
| `helm dependency build` | Build from Chart.lock |
| `helm dependency list` | List dependencies |
| `helm search repo <dep>` | Find dependency versions |
| `helm show values <repo/chart>` | See dependency values |
