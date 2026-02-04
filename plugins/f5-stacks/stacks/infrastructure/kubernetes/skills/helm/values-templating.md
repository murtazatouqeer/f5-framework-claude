---
name: k8s-helm-templating
description: Helm templating with Go templates and Sprig functions
applies_to: kubernetes
---

# Helm Values and Templating

## Template Basics

### Accessing Values

```yaml
# values.yaml
image:
  repository: myapp
  tag: "1.0.0"
replicaCount: 3

# template
image: {{ .Values.image.repository }}:{{ .Values.image.tag }}
replicas: {{ .Values.replicaCount }}
```

### Built-in Objects

```yaml
# Release information
{{ .Release.Name }}        # Release name
{{ .Release.Namespace }}   # Release namespace
{{ .Release.IsUpgrade }}   # Is this an upgrade
{{ .Release.IsInstall }}   # Is this a new install
{{ .Release.Revision }}    # Revision number
{{ .Release.Service }}     # Rendering engine (always "Helm")

# Chart information
{{ .Chart.Name }}          # Chart name
{{ .Chart.Version }}       # Chart version
{{ .Chart.AppVersion }}    # App version
{{ .Chart.Description }}   # Chart description

# Template information
{{ .Template.Name }}       # Current template path
{{ .Template.BasePath }}   # Templates directory

# Capabilities
{{ .Capabilities.KubeVersion }}
{{ .Capabilities.APIVersions.Has "networking.k8s.io/v1" }}
```

## Control Structures

### Conditionals

```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
# ...
{{- end }}

{{- if and .Values.service.enabled (eq .Values.service.type "LoadBalancer") }}
# LoadBalancer service configuration
{{- end }}

{{- if or .Values.configMap.enabled .Values.secret.enabled }}
# Configuration exists
{{- end }}

{{- if not .Values.autoscaling.enabled }}
replicas: {{ .Values.replicaCount }}
{{- end }}

# if-else
{{- if .Values.persistence.enabled }}
  persistentVolumeClaim:
    claimName: {{ .Values.persistence.existingClaim | default (include "myapp.fullname" .) }}
{{- else }}
  emptyDir: {}
{{- end }}
```

### Loops

```yaml
# Range over list
{{- range .Values.ingress.hosts }}
- host: {{ .host }}
  http:
    paths:
    {{- range .paths }}
    - path: {{ .path }}
      pathType: {{ .pathType }}
    {{- end }}
{{- end }}

# Range over map
{{- range $key, $value := .Values.env }}
- name: {{ $key }}
  value: {{ $value | quote }}
{{- end }}

# Range with index
{{- range $index, $host := .Values.ingress.hosts }}
# Host {{ $index }}: {{ $host.host }}
{{- end }}
```

### With (Scope Change)

```yaml
{{- with .Values.nodeSelector }}
nodeSelector:
  {{- toYaml . | nindent 2 }}
{{- end }}

# With and else
{{- with .Values.affinity }}
affinity:
  {{- toYaml . | nindent 2 }}
{{- else }}
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          topologyKey: kubernetes.io/hostname
{{- end }}
```

## Functions

### String Functions

```yaml
# Quote
value: {{ .Values.password | quote }}
# Output: value: "mypassword"

# Upper/Lower
value: {{ .Values.name | upper }}
value: {{ .Values.name | lower }}

# Trim
value: {{ .Values.name | trim }}
value: {{ .Values.name | trimPrefix "prefix-" }}
value: {{ .Values.name | trimSuffix "-suffix" }}

# Replace
value: {{ .Values.name | replace "-" "_" }}

# Contains/HasPrefix/HasSuffix
{{- if contains "postgresql" .Values.database.type }}
{{- if hasPrefix "prod-" .Values.environment }}
{{- if hasSuffix ".com" .Values.domain }}

# Substring
value: {{ substr 0 5 .Values.name }}

# Default
value: {{ .Values.name | default "default-name" }}

# Required (fail if empty)
value: {{ required "A valid name is required!" .Values.name }}
```

### Type Conversion

```yaml
# toString
value: {{ .Values.port | toString }}

# toInt
value: {{ .Values.replicas | int }}

# toBool
value: {{ .Values.enabled | toString | lower }}

# toJson/toYaml
annotations:
  config: {{ .Values.config | toJson | quote }}

# fromJson/fromYaml
{{- $config := .Values.configJson | fromJson }}
```

### List Functions

```yaml
# First/Last
value: {{ first .Values.hosts }}
value: {{ last .Values.hosts }}

# Initial/Rest
{{- range initial .Values.hosts }}
{{- range rest .Values.hosts }}

# Append/Prepend
{{- $list := append .Values.hosts "new-host" }}

# Concat
{{- $combined := concat .Values.list1 .Values.list2 }}

# Has (contains)
{{- if has "value" .Values.list }}

# Without (remove)
{{- $filtered := without .Values.list "remove-this" }}

# Uniq
{{- $unique := uniq .Values.list }}

# Compact (remove empty)
{{- $cleaned := compact .Values.list }}
```

### Dictionary Functions

```yaml
# dict - Create dictionary
{{- $labels := dict "app" .Values.name "version" .Values.version }}

# get - Get value
value: {{ get .Values.config "key" }}

# set - Set value (modifies in place)
{{- $_ := set .Values.config "newKey" "newValue" }}

# merge - Merge dictionaries
{{- $merged := merge .Values.defaults .Values.overrides }}

# keys/values
{{- range keys .Values.env }}
{{- range values .Values.env }}

# pick - Select keys
{{- $subset := pick .Values.config "key1" "key2" }}

# omit - Remove keys
{{- $filtered := omit .Values.config "secretKey" }}
```

### Flow Control

```yaml
# fail - Stop with error
{{- if not .Values.required }}
{{- fail "required value is missing" }}
{{- end }}

# print/printf
{{- printf "%s-%s" .Release.Name .Values.suffix }}

# tpl - Evaluate string as template
annotations:
  description: {{ tpl .Values.description . }}
```

## Template Helpers (_helpers.tpl)

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
Create chart name and version as used by the chart label.
*/}}
{{- define "myapp.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "myapp.labels" -}}
helm.sh/chart: {{ include "myapp.chart" . }}
{{ include "myapp.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "myapp.selectorLabels" -}}
app.kubernetes.io/name: {{ include "myapp.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Service account name
*/}}
{{- define "myapp.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "myapp.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Image name
*/}}
{{- define "myapp.image" -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion }}
{{- printf "%s:%s" .Values.image.repository $tag }}
{{- end }}
```

## Using Named Templates

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "myapp.fullname" . }}
  labels:
    {{- include "myapp.labels" . | nindent 4 }}
spec:
  selector:
    matchLabels:
      {{- include "myapp.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "myapp.selectorLabels" . | nindent 8 }}
    spec:
      serviceAccountName: {{ include "myapp.serviceAccountName" . }}
      containers:
        - name: {{ .Chart.Name }}
          image: {{ include "myapp.image" . }}
```

## Whitespace Control

```yaml
# Remove leading whitespace
{{- .Values.name }}

# Remove trailing whitespace
{{ .Values.name -}}

# Remove both
{{- .Values.name -}}

# nindent - Add newline and indent
labels:
  {{- include "myapp.labels" . | nindent 2 }}

# indent - Just indent (no newline)
{{ .Values.config | indent 4 }}
```

## Best Practices

1. **Use helpers** for repeated patterns
2. **Quote string values** with `quote`
3. **Use `required`** for mandatory values
4. **Provide `default`** values
5. **Control whitespace** carefully with `-`
6. **Use `nindent`** for proper YAML formatting
7. **Validate with `helm template`**
8. **Keep templates readable** with comments
9. **Use `toYaml`** for complex nested values
10. **Test edge cases** with different values
