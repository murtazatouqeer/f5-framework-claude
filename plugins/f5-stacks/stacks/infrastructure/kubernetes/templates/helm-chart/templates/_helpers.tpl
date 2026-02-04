{{/*
Helm Chart Template - _helpers.tpl
F5 Framework - Infrastructure Stack

Common template helpers and functions
*/}}

{{/*
Expand the name of the chart.
*/}}
{{- define "app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this.
If release name contains chart name it will be used as a full name.
*/}}
{{- define "app.fullname" -}}
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
{{- define "app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "app.labels" -}}
helm.sh/chart: {{ include "app.chart" . }}
{{ include "app.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: {{ include "app.name" . }}
f5.io/framework: "true"
{{- end }}

{{/*
Selector labels
*/}}
{{- define "app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "app.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "app.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create image name
*/}}
{{- define "app.image" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
Create image pull secrets
*/}}
{{- define "app.imagePullSecrets" -}}
{{- $pullSecrets := list }}
{{- if .Values.global.imagePullSecrets }}
{{- range .Values.global.imagePullSecrets }}
{{- $pullSecrets = append $pullSecrets . }}
{{- end }}
{{- end }}
{{- if .Values.image.pullSecrets }}
{{- range .Values.image.pullSecrets }}
{{- $pullSecrets = append $pullSecrets . }}
{{- end }}
{{- end }}
{{- if $pullSecrets }}
imagePullSecrets:
{{- range $pullSecrets }}
  - name: {{ . }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create ConfigMap name
*/}}
{{- define "app.configMapName" -}}
{{- printf "%s-config" (include "app.fullname" .) }}
{{- end }}

{{/*
Create Secret name
*/}}
{{- define "app.secretName" -}}
{{- printf "%s-secrets" (include "app.fullname" .) }}
{{- end }}

{{/*
Return the proper storage class name
*/}}
{{- define "app.storageClass" -}}
{{- if .Values.global.storageClass }}
{{- .Values.global.storageClass }}
{{- else if .Values.persistence.storageClass }}
{{- .Values.persistence.storageClass }}
{{- end }}
{{- end }}

{{/*
Pod annotations for checksum (triggers rollout on config change)
*/}}
{{- define "app.checksumAnnotations" -}}
{{- if .Values.configMap.enabled }}
checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
{{- end }}
{{- if .Values.secret.enabled }}
checksum/secret: {{ include (print $.Template.BasePath "/secret.yaml") . | sha256sum }}
{{- end }}
{{- end }}

{{/*
Return true if a TLS secret is needed
*/}}
{{- define "app.ingress.tlsSecretNeeded" -}}
{{- if .Values.ingress.tls }}
{{- range .Values.ingress.tls }}
{{- if not .existingSecret }}
{{- true -}}
{{- end }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate backend for ingress
*/}}
{{- define "app.ingress.backend" -}}
service:
  name: {{ include "app.fullname" . }}
  port:
    number: {{ .Values.service.port }}
{{- end }}

{{/*
Resource requirements
*/}}
{{- define "app.resources" -}}
{{- if .Values.resources }}
resources:
  {{- toYaml .Values.resources | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Security context for pod
*/}}
{{- define "app.podSecurityContext" -}}
{{- if .Values.podSecurityContext }}
securityContext:
  {{- toYaml .Values.podSecurityContext | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Security context for container
*/}}
{{- define "app.securityContext" -}}
{{- if .Values.securityContext }}
securityContext:
  {{- toYaml .Values.securityContext | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Affinity rules
*/}}
{{- define "app.affinity" -}}
{{- if .Values.affinity }}
affinity:
  {{- toYaml .Values.affinity | nindent 2 }}
{{- else }}
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              {{- include "app.selectorLabels" . | nindent 14 }}
          topologyKey: kubernetes.io/hostname
{{- end }}
{{- end }}

{{/*
Tolerations
*/}}
{{- define "app.tolerations" -}}
{{- if .Values.tolerations }}
tolerations:
  {{- toYaml .Values.tolerations | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Node selector
*/}}
{{- define "app.nodeSelector" -}}
{{- if .Values.nodeSelector }}
nodeSelector:
  {{- toYaml .Values.nodeSelector | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Topology spread constraints
*/}}
{{- define "app.topologySpreadConstraints" -}}
{{- if .Values.topologySpreadConstraints }}
topologySpreadConstraints:
  {{- toYaml .Values.topologySpreadConstraints | nindent 2 }}
{{- else }}
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        {{- include "app.selectorLabels" . | nindent 8 }}
{{- end }}
{{- end }}

{{/*
Validate values
*/}}
{{- define "app.validateValues" -}}
{{- if and .Values.autoscaling.enabled (not (ge (int .Values.autoscaling.minReplicas) 1)) }}
{{- fail "autoscaling.minReplicas must be at least 1" }}
{{- end }}
{{- if and .Values.ingress.enabled (not .Values.ingress.hosts) }}
{{- fail "ingress.hosts must be set when ingress is enabled" }}
{{- end }}
{{- end }}
