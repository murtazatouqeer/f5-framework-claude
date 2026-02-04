---
name: helm-charts
description: Helm package manager for Kubernetes applications
category: devops/orchestration
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Helm Charts

## Overview

Helm is the package manager for Kubernetes, providing a way to define, install,
and upgrade complex Kubernetes applications using charts.

## Helm Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Helm Architecture                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Developer                    Kubernetes Cluster                 │
│  ┌─────────────┐              ┌─────────────────────────────┐   │
│  │             │              │                             │   │
│  │  Chart      │    helm      │   ┌─────────────────────┐   │   │
│  │  Repository │   install    │   │    Release          │   │   │
│  │             │  ─────────▶  │   │  ┌───────────────┐  │   │   │
│  │  ┌───────┐  │              │   │  │  Deployment   │  │   │   │
│  │  │ Chart │  │              │   │  │  Service      │  │   │   │
│  │  │.tgz   │  │              │   │  │  ConfigMap    │  │   │   │
│  │  └───────┘  │              │   │  │  Secret       │  │   │   │
│  │             │              │   │  └───────────────┘  │   │   │
│  └─────────────┘              │   └─────────────────────┘   │   │
│                               │                             │   │
│  ┌─────────────┐              │   Release History           │   │
│  │  values.    │              │   ┌─────────────────────┐   │   │
│  │  yaml       │              │   │ v1 │ v2 │ v3 │ ... │   │   │
│  └─────────────┘              │   └─────────────────────┘   │   │
│                               └─────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Chart Structure

```
my-app/
├── Chart.yaml           # Chart metadata
├── values.yaml          # Default configuration values
├── values.schema.json   # JSON Schema for values validation
├── charts/              # Chart dependencies
├── crds/                # Custom Resource Definitions
├── templates/           # Kubernetes manifest templates
│   ├── NOTES.txt        # Post-install notes
│   ├── _helpers.tpl     # Template helpers
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── configmap.yaml
│   ├── secret.yaml
│   ├── ingress.yaml
│   ├── hpa.yaml
│   └── serviceaccount.yaml
└── .helmignore          # Files to ignore when packaging
```

## Chart.yaml

```yaml
# Chart.yaml
apiVersion: v2
name: my-app
description: A Helm chart for My Application
type: application
version: 1.0.0
appVersion: "2.5.0"

# Dependencies
dependencies:
  - name: postgresql
    version: "12.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: postgresql.enabled
  - name: redis
    version: "17.x.x"
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled

# Maintainers
maintainers:
  - name: Platform Team
    email: platform@example.com

# Keywords for search
keywords:
  - api
  - nodejs
  - backend

# Annotations
annotations:
  artifacthub.io/changes: |
    - kind: added
      description: Added HPA support
    - kind: fixed
      description: Fixed ingress configuration
```

## values.yaml

```yaml
# values.yaml
# Application configuration
replicaCount: 3

image:
  repository: my-registry.com/my-app
  pullPolicy: IfNotPresent
  tag: ""  # Defaults to appVersion

imagePullSecrets:
  - name: registry-credentials

nameOverride: ""
fullnameOverride: ""

# Service Account
serviceAccount:
  create: true
  annotations: {}
  name: ""

# Pod configuration
podAnnotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "3000"

podSecurityContext:
  fsGroup: 1000

securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false

# Service
service:
  type: ClusterIP
  port: 80
  targetPort: 3000

# Ingress
ingress:
  enabled: true
  className: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: api-tls
      hosts:
        - api.example.com

# Resources
resources:
  limits:
    cpu: 500m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

# Autoscaling
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Node selection
nodeSelector: {}

tolerations: []

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app.kubernetes.io/name
                operator: In
                values:
                  - my-app
          topologyKey: kubernetes.io/hostname

# Application configuration
config:
  nodeEnv: production
  logLevel: info
  apiTimeout: 30000

# Secrets (use external secrets in production)
secrets:
  databaseUrl: ""
  jwtSecret: ""

# Health checks
healthCheck:
  liveness:
    path: /health
    initialDelaySeconds: 10
    periodSeconds: 10
  readiness:
    path: /ready
    initialDelaySeconds: 5
    periodSeconds: 5

# Dependencies
postgresql:
  enabled: true
  auth:
    database: myapp
    username: myapp

redis:
  enabled: true
  architecture: standalone
```

## Template Files

### _helpers.tpl

```yaml
# templates/_helpers.tpl
{{/*
Expand the name of the chart.
*/}}
{{- define "my-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "my-app.fullname" -}}
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
Create chart name and version as used by the chart label.
*/}}
{{- define "my-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "my-app.labels" -}}
helm.sh/chart: {{ include "my-app.chart" . }}
{{ include "my-app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "my-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "my-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "my-app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "my-app.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "my-app.databaseUrl" -}}
{{- if .Values.postgresql.enabled }}
{{- printf "postgresql://%s:%s@%s-postgresql:5432/%s" .Values.postgresql.auth.username .Values.postgresql.auth.password (include "my-app.fullname" .) .Values.postgresql.auth.database }}
{{- else }}
{{- .Values.secrets.databaseUrl }}
{{- end }}
{{- end }}
```

### deployment.yaml

```yaml
# templates/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "my-app.selectorLabels" . | nindent 6 }}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
        {{- with .Values.podAnnotations }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
      labels:
        {{- include "my-app.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "my-app.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.targetPort }}
              protocol: TCP
          envFrom:
            - configMapRef:
                name: {{ include "my-app.fullname" . }}
            - secretRef:
                name: {{ include "my-app.fullname" . }}
          livenessProbe:
            httpGet:
              path: {{ .Values.healthCheck.liveness.path }}
              port: http
            initialDelaySeconds: {{ .Values.healthCheck.liveness.initialDelaySeconds }}
            periodSeconds: {{ .Values.healthCheck.liveness.periodSeconds }}
          readinessProbe:
            httpGet:
              path: {{ .Values.healthCheck.readiness.path }}
              port: http
            initialDelaySeconds: {{ .Values.healthCheck.readiness.initialDelaySeconds }}
            periodSeconds: {{ .Values.healthCheck.readiness.periodSeconds }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          volumeMounts:
            - name: tmp
              mountPath: /tmp
      volumes:
        - name: tmp
          emptyDir: {}
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.affinity }}
      affinity:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      {{- with .Values.tolerations }}
      tolerations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
```

### service.yaml

```yaml
# templates/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "my-app.selectorLabels" . | nindent 4 }}
```

### ingress.yaml

```yaml
# templates/ingress.yaml
{{- if .Values.ingress.enabled -}}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
  {{- with .Values.ingress.annotations }}
  annotations:
    {{- toYaml . | nindent 4 }}
  {{- end }}
spec:
  {{- if .Values.ingress.className }}
  ingressClassName: {{ .Values.ingress.className }}
  {{- end }}
  {{- if .Values.ingress.tls }}
  tls:
    {{- range .Values.ingress.tls }}
    - hosts:
        {{- range .hosts }}
        - {{ . | quote }}
        {{- end }}
      secretName: {{ .secretName }}
    {{- end }}
  {{- end }}
  rules:
    {{- range .Values.ingress.hosts }}
    - host: {{ .host | quote }}
      http:
        paths:
          {{- range .paths }}
          - path: {{ .path }}
            pathType: {{ .pathType }}
            backend:
              service:
                name: {{ include "my-app.fullname" $ }}
                port:
                  number: {{ $.Values.service.port }}
          {{- end }}
    {{- end }}
{{- end }}
```

### configmap.yaml

```yaml
# templates/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
data:
  NODE_ENV: {{ .Values.config.nodeEnv | quote }}
  LOG_LEVEL: {{ .Values.config.logLevel | quote }}
  API_TIMEOUT: {{ .Values.config.apiTimeout | quote }}
  {{- if .Values.redis.enabled }}
  REDIS_HOST: {{ include "my-app.fullname" . }}-redis-master
  REDIS_PORT: "6379"
  {{- end }}
```

### secret.yaml

```yaml
# templates/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
type: Opaque
data:
  DATABASE_URL: {{ include "my-app.databaseUrl" . | b64enc | quote }}
  JWT_SECRET: {{ .Values.secrets.jwtSecret | b64enc | quote }}
```

### hpa.yaml

```yaml
# templates/hpa.yaml
{{- if .Values.autoscaling.enabled }}
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "my-app.fullname" . }}
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "my-app.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
```

## Essential Commands

```bash
# Repository Management
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
helm repo list
helm search repo postgresql

# Chart Management
helm create my-app                    # Create new chart
helm dependency update                # Download dependencies
helm dependency build                 # Build dependencies
helm package my-app                   # Package chart

# Installation
helm install my-release ./my-app
helm install my-release ./my-app -f values-prod.yaml
helm install my-release ./my-app --set image.tag=2.0.0
helm install my-release ./my-app -n production --create-namespace

# Upgrade
helm upgrade my-release ./my-app
helm upgrade my-release ./my-app --install  # Install if not exists
helm upgrade my-release ./my-app --atomic   # Rollback on failure
helm upgrade my-release ./my-app --wait     # Wait for completion

# Rollback
helm rollback my-release
helm rollback my-release 1           # Rollback to revision 1

# Status and History
helm list
helm list -n production
helm status my-release
helm history my-release

# Debugging
helm template my-release ./my-app    # Render templates locally
helm lint ./my-app                   # Lint chart
helm get manifest my-release         # Get deployed manifests
helm get values my-release           # Get deployed values
helm diff upgrade my-release ./my-app  # Show changes (requires plugin)

# Uninstall
helm uninstall my-release
helm uninstall my-release --keep-history
```

## Values Override Strategies

```yaml
# values-dev.yaml
replicaCount: 1

ingress:
  enabled: false

resources:
  limits:
    cpu: 200m
    memory: 128Mi

autoscaling:
  enabled: false

postgresql:
  enabled: true
  auth:
    password: dev-password

---
# values-staging.yaml
replicaCount: 2

ingress:
  enabled: true
  hosts:
    - host: api.staging.example.com
      paths:
        - path: /
          pathType: Prefix

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5

---
# values-prod.yaml
replicaCount: 3

ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "100"
  hosts:
    - host: api.example.com
      paths:
        - path: /
          pathType: Prefix

resources:
  limits:
    cpu: 1000m
    memory: 512Mi
  requests:
    cpu: 200m
    memory: 256Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
```

```bash
# Using override files
helm install my-release ./my-app -f values-prod.yaml

# Multiple override files (later files take precedence)
helm install my-release ./my-app \
  -f values.yaml \
  -f values-prod.yaml \
  -f values-secrets.yaml

# Command-line overrides
helm install my-release ./my-app \
  --set image.tag=2.0.0 \
  --set replicaCount=5

# Combined
helm install my-release ./my-app \
  -f values-prod.yaml \
  --set image.tag=2.0.0
```

## Hooks

```yaml
# templates/job-migration.yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: {{ include "my-app.fullname" . }}-migration
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": pre-upgrade,pre-install
    "helm.sh/hook-weight": "-5"
    "helm.sh/hook-delete-policy": before-hook-creation,hook-succeeded
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migration
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          command: ["npm", "run", "db:migrate"]
          envFrom:
            - secretRef:
                name: {{ include "my-app.fullname" . }}
```

Hook Types:
- `pre-install`: Before resources are created
- `post-install`: After resources are created
- `pre-delete`: Before resources are deleted
- `post-delete`: After resources are deleted
- `pre-upgrade`: Before upgrade
- `post-upgrade`: After upgrade
- `pre-rollback`: Before rollback
- `post-rollback`: After rollback

## Testing

```yaml
# templates/tests/test-connection.yaml
apiVersion: v1
kind: Pod
metadata:
  name: "{{ include "my-app.fullname" . }}-test-connection"
  labels:
    {{- include "my-app.labels" . | nindent 4 }}
  annotations:
    "helm.sh/hook": test
spec:
  containers:
    - name: wget
      image: busybox
      command: ['wget']
      args: ['{{ include "my-app.fullname" . }}:{{ .Values.service.port }}/health']
  restartPolicy: Never
```

```bash
# Run tests
helm test my-release
helm test my-release --logs
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                    Helm Best Practices                           │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use semantic versioning for chart versions                    │
│ ☐ Document all values in values.yaml                            │
│ ☐ Use values.schema.json for validation                         │
│ ☐ Include NOTES.txt for post-install instructions               │
│ ☐ Use _helpers.tpl for reusable templates                       │
│ ☐ Add checksum annotations to trigger pod restart               │
│ ☐ Use hooks for migrations and setup                            │
│ ☐ Include helm tests                                            │
│ ☐ Separate values files per environment                         │
│ ☐ Use --atomic for production upgrades                          │
│ ☐ Lint charts before publishing                                 │
│ ☐ Sign charts for verification                                  │
└─────────────────────────────────────────────────────────────────┘
```
