---
name: helm-chart-generator
description: Generates production-ready Helm charts
triggers:
  - helm chart
  - create chart
  - generate helm
  - package kubernetes
capabilities:
  - Generate Helm chart structure
  - Create values.yaml with defaults
  - Generate templates with helpers
  - Add chart dependencies
  - Create values schemas
---

# Helm Chart Generator Agent

## Purpose

Generates production-ready Helm charts with proper templating, documentation, and best practices.

## Workflow

```
1. ANALYZE application requirements
   - Identify resources needed
   - Determine configurable values
   - Plan dependencies

2. SCAFFOLD chart structure
   - Chart.yaml
   - values.yaml
   - templates/
   - helpers

3. CREATE templates
   - Deployment/StatefulSet
   - Service
   - Ingress
   - ConfigMap/Secret
   - ServiceAccount
   - HPA/PDB

4. IMPLEMENT helpers
   - Name generation
   - Label generation
   - Image reference
   - Resource helpers

5. ADD documentation
   - README.md
   - values.schema.json
   - NOTES.txt

6. VALIDATE chart
   - helm lint
   - helm template
   - kubeval
```

## Input Schema

```yaml
input:
  chart_name: string
  description: string
  app_version: string

  maintainers:
    - name: string
      email: string

  dependencies:
    - name: string
      version: string
      repository: string
      condition: string

  values:
    replicas: number
    image:
      repository: string
      tag: string
    resources: object
    ingress: object
    autoscaling: object
```

## Output Structure

```
mychart/
├── Chart.yaml
├── Chart.lock
├── values.yaml
├── values.schema.json
├── README.md
├── .helmignore
├── templates/
│   ├── NOTES.txt
│   ├── _helpers.tpl
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── serviceaccount.yaml
│   ├── hpa.yaml
│   ├── pdb.yaml
│   └── tests/
│       └── test-connection.yaml
└── charts/
```

## Best Practices Applied

### Templating
- Consistent naming with helpers
- Proper indentation with nindent
- Conditional rendering
- Default values
- Type coercion

### Values Design
- Logical grouping
- Sensible defaults
- Environment-specific overrides
- Schema validation

### Security
- ServiceAccount creation
- RBAC resources
- Pod security context defaults
- Secret management

## Example Usage

```bash
# Generate a new Helm chart
@helm-chart-generator create \
  --name myapp \
  --description "My Application" \
  --app-version 1.0.0 \
  --with-postgresql \
  --with-redis \
  --with-ingress

# Generate from existing manifests
@helm-chart-generator from-manifests \
  --source ./manifests \
  --chart-name myapp
```

## Generated Chart.yaml Example

```yaml
apiVersion: v2
name: myapp
description: A Helm chart for MyApp
type: application
version: 0.1.0
appVersion: "1.0.0"

keywords:
  - api
  - microservice

maintainers:
  - name: DevOps Team
    email: devops@example.com

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

## Generated values.yaml Example

```yaml
replicaCount: 3

image:
  repository: myregistry/myapp
  tag: ""
  pullPolicy: IfNotPresent

serviceAccount:
  create: true
  annotations: {}
  name: ""

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: false
  className: nginx
  annotations: {}
  hosts:
    - host: chart-example.local
      paths:
        - path: /
          pathType: Prefix
  tls: []

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 1000m
    memory: 1Gi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70

postgresql:
  enabled: true
  auth:
    database: myapp

redis:
  enabled: false
```

## Template Helpers Generated

```yaml
{{/*
Expand the name of the chart.
*/}}
{{- define "myapp.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "myapp.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "myapp.labels" -}}
helm.sh/chart: {{ include "myapp.chart" . }}
{{ include "myapp.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}
```
