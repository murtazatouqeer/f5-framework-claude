---
name: k8s-helm-chart-structure
description: Helm chart structure and Chart.yaml configuration
applies_to: kubernetes
---

# Helm Chart Structure

## Overview

A Helm chart is a collection of files that describe a related set of Kubernetes resources.

## Directory Structure

```
mychart/
├── Chart.yaml          # Chart metadata
├── Chart.lock          # Lock file for dependencies
├── values.yaml         # Default configuration values
├── values.schema.json  # JSON schema for values validation
├── .helmignore         # Patterns to ignore when packaging
├── LICENSE             # License information
├── README.md           # Documentation
├── charts/             # Chart dependencies
├── crds/               # Custom Resource Definitions
└── templates/          # Template files
    ├── NOTES.txt       # Post-install notes
    ├── _helpers.tpl    # Template helpers
    ├── deployment.yaml
    ├── service.yaml
    ├── configmap.yaml
    ├── secret.yaml
    ├── ingress.yaml
    ├── hpa.yaml
    ├── pdb.yaml
    ├── serviceaccount.yaml
    └── tests/          # Test files
        └── test-connection.yaml
```

## Chart.yaml

### Basic Chart.yaml

```yaml
apiVersion: v2
name: myapp
description: A Helm chart for MyApp

# Chart type: application or library
type: application

# Chart version (SemVer)
version: 1.0.0

# App version
appVersion: "2.1.0"
```

### Complete Chart.yaml

```yaml
apiVersion: v2
name: myapp
description: A production-ready Helm chart for MyApp

type: application
version: 1.2.3
appVersion: "3.0.0"

# Keywords for search
keywords:
  - api
  - backend
  - microservice

# Homepage URL
home: https://myapp.example.com

# Source code URLs
sources:
  - https://github.com/example/myapp
  - https://github.com/example/myapp-chart

# Maintainers
maintainers:
  - name: John Doe
    email: john@example.com
    url: https://johndoe.dev
  - name: Jane Smith
    email: jane@example.com

# Icon URL (SVG or PNG)
icon: https://myapp.example.com/logo.png

# Minimum Kubernetes version
kubeVersion: ">=1.25.0-0"

# Annotations
annotations:
  category: Backend
  licenses: Apache-2.0
  artifacthub.io/changes: |
    - Added HPA support
    - Fixed service port configuration
  artifacthub.io/containsSecurityUpdates: "true"

# Dependencies
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
    tags:
      - database

  - name: redis
    version: "17.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
    alias: cache

  - name: common
    version: "2.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    import-values:
      - child: image
        parent: commonImage
```

## values.yaml

### Production values.yaml

```yaml
# Image configuration
image:
  repository: myregistry/myapp
  tag: ""  # Defaults to Chart.appVersion
  pullPolicy: IfNotPresent
  pullSecrets: []

# Replicas
replicaCount: 3

# Service Account
serviceAccount:
  create: true
  name: ""
  annotations: {}
  automountServiceAccountToken: false

# Pod configuration
podAnnotations: {}
podLabels: {}

podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL

# Service
service:
  type: ClusterIP
  port: 80
  targetPort: 8080
  annotations: {}

# Ingress
ingress:
  enabled: false
  className: nginx
  annotations: {}
  hosts:
    - host: myapp.example.com
      paths:
        - path: /
          pathType: Prefix
  tls: []

# Resources
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

# Autoscaling
autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Pod Disruption Budget
podDisruptionBudget:
  enabled: true
  minAvailable: 1

# Probes
livenessProbe:
  httpGet:
    path: /health/live
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /health/ready
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3

# Node selection
nodeSelector: {}
tolerations: []
affinity: {}

# Environment variables
env: []
envFrom: []

# ConfigMap
configMap:
  enabled: true
  data:
    LOG_LEVEL: info
    SERVER_PORT: "8080"

# Secrets
secret:
  enabled: false
  data: {}

# Extra volumes
extraVolumes: []
extraVolumeMounts: []

# Init containers
initContainers: []

# Sidecar containers
sidecars: []

# PostgreSQL dependency
postgresql:
  enabled: true
  auth:
    postgresPassword: ""
    database: myapp
  primary:
    persistence:
      size: 10Gi

# Redis dependency
redis:
  enabled: false
  architecture: standalone
```

## values.schema.json

```json
{
  "$schema": "https://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["image", "service"],
  "properties": {
    "replicaCount": {
      "type": "integer",
      "minimum": 1,
      "default": 1
    },
    "image": {
      "type": "object",
      "required": ["repository"],
      "properties": {
        "repository": {
          "type": "string"
        },
        "tag": {
          "type": "string"
        },
        "pullPolicy": {
          "type": "string",
          "enum": ["Always", "IfNotPresent", "Never"],
          "default": "IfNotPresent"
        }
      }
    },
    "service": {
      "type": "object",
      "required": ["port"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["ClusterIP", "NodePort", "LoadBalancer"],
          "default": "ClusterIP"
        },
        "port": {
          "type": "integer",
          "minimum": 1,
          "maximum": 65535
        }
      }
    },
    "ingress": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false
        },
        "hosts": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["host"],
            "properties": {
              "host": {
                "type": "string",
                "format": "hostname"
              }
            }
          }
        }
      }
    }
  }
}
```

## .helmignore

```
# Patterns to ignore when building packages

# VCS
.git/
.gitignore
.bzr/
.bzrignore
.hg/
.hgignore
.svn/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Build artifacts
*.tgz
*.tar.gz

# Testing
tests/
*.test.yaml

# Documentation
*.md
!README.md
docs/

# CI/CD
.github/
.gitlab-ci.yml
.circleci/
Jenkinsfile
.travis.yml

# Development
Makefile
Taskfile.yaml
.envrc
.tool-versions
```

## NOTES.txt

```
{{- $fullName := include "myapp.fullname" . -}}

Thank you for installing {{ .Chart.Name }}!

Your release is named {{ .Release.Name }}.

{{- if .Values.ingress.enabled }}
Application URL:
{{- range $host := .Values.ingress.hosts }}
  http{{ if $.Values.ingress.tls }}s{{ end }}://{{ $host.host }}
{{- end }}
{{- else if contains "NodePort" .Values.service.type }}
Get the application URL by running:
  export NODE_PORT=$(kubectl get --namespace {{ .Release.Namespace }} -o jsonpath="{.spec.ports[0].nodePort}" services {{ $fullName }})
  export NODE_IP=$(kubectl get nodes --namespace {{ .Release.Namespace }} -o jsonpath="{.items[0].status.addresses[0].address}")
  echo http://$NODE_IP:$NODE_PORT
{{- else if contains "LoadBalancer" .Values.service.type }}
Get the application URL by running:
  NOTE: It may take a few minutes for the LoadBalancer IP to be available.
  kubectl get svc --namespace {{ .Release.Namespace }} {{ $fullName }} -w
{{- else if contains "ClusterIP" .Values.service.type }}
Get the application URL by running:
  kubectl port-forward --namespace {{ .Release.Namespace }} svc/{{ $fullName }} 8080:{{ .Values.service.port }}
  echo "Visit http://127.0.0.1:8080"
{{- end }}

To check the status:
  kubectl get pods -l "app.kubernetes.io/name={{ include "myapp.name" . }},app.kubernetes.io/instance={{ .Release.Name }}" -n {{ .Release.Namespace }}
```

## Library Charts

### Library Chart.yaml

```yaml
apiVersion: v2
name: common
description: Common templates for Helm charts
type: library
version: 1.0.0
```

### Using Library Chart

```yaml
# In dependent chart's Chart.yaml
dependencies:
  - name: common
    version: "1.x.x"
    repository: "file://../common"
```

## Commands

```bash
# Create new chart
helm create myapp

# Validate chart structure
helm lint myapp

# Package chart
helm package myapp

# Update dependencies
helm dependency update myapp

# List dependencies
helm dependency list myapp
```

## Best Practices

1. **Use semantic versioning** for chart versions
2. **Separate appVersion** from chart version
3. **Document values** with comments
4. **Use JSON schema** for values validation
5. **Pin dependency versions** with Chart.lock
6. **Include helpful NOTES.txt** for users
7. **Provide sensible defaults** in values.yaml
8. **Use conditions** for optional dependencies
9. **Keep charts focused** on single application
10. **Include comprehensive README.md**
