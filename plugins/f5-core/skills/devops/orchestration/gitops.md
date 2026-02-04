---
name: gitops
description: GitOps practices with ArgoCD and Flux
category: devops/orchestration
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# GitOps

## Overview

GitOps is an operational framework that uses Git as the single source of truth
for declarative infrastructure and applications, enabling automated deployment
through pull-based synchronization.

## GitOps Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                     GitOps Principles                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Declarative                                                  │
│     └─ All system state described declaratively                 │
│                                                                  │
│  2. Versioned and Immutable                                      │
│     └─ Desired state stored in Git (version controlled)         │
│                                                                  │
│  3. Pulled Automatically                                         │
│     └─ Agents pull desired state from Git                       │
│                                                                  │
│  4. Continuously Reconciled                                      │
│     └─ Agents ensure actual state matches desired state         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## GitOps Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitOps Architecture                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                     Git Repository                        │  │
│  │  ┌─────────────────┐  ┌─────────────────┐               │  │
│  │  │   App Repo      │  │   Config Repo   │               │  │
│  │  │  (Source Code)  │  │  (Manifests)    │               │  │
│  │  └────────┬────────┘  └────────┬────────┘               │  │
│  └───────────┼────────────────────┼─────────────────────────┘  │
│              │                    │                             │
│              ▼                    ▼                             │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   CI Pipeline    │    │  GitOps Agent    │                  │
│  │  (Build & Push)  │    │ (ArgoCD/Flux)    │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                             │
│           ▼                       ▼                             │
│  ┌──────────────────┐    ┌──────────────────────────────────┐  │
│  │ Container        │    │      Kubernetes Cluster          │  │
│  │ Registry         │    │  ┌───────────┐ ┌───────────┐    │  │
│  │ ┌──────────────┐ │    │  │    App    │ │    App    │    │  │
│  │ │  my-app:v1   │ │    │  │   v1.2.3  │ │   v1.2.3  │    │  │
│  │ │  my-app:v2   │ │    │  └───────────┘ └───────────┘    │  │
│  │ └──────────────┘ │    └──────────────────────────────────┘  │
│  └──────────────────┘                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
# Application Repository (Code)
app-repo/
├── src/
├── Dockerfile
├── package.json
└── .github/
    └── workflows/
        └── ci.yaml

# Configuration Repository (GitOps)
config-repo/
├── apps/
│   ├── base/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── kustomization.yaml
│   └── overlays/
│       ├── development/
│       │   ├── kustomization.yaml
│       │   └── patches/
│       ├── staging/
│       │   ├── kustomization.yaml
│       │   └── patches/
│       └── production/
│           ├── kustomization.yaml
│           └── patches/
├── infrastructure/
│   ├── cert-manager/
│   ├── nginx-ingress/
│   └── monitoring/
└── clusters/
    ├── development/
    │   ├── apps.yaml
    │   └── infrastructure.yaml
    ├── staging/
    └── production/
```

## ArgoCD

### Installation

```bash
# Create namespace
kubectl create namespace argocd

# Install ArgoCD
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Get initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d

# Port forward to access UI
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Or install via Helm
helm repo add argo https://argoproj.github.io/argo-helm
helm install argocd argo/argo-cd -n argocd --create-namespace
```

### Application CRD

```yaml
# argocd-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/config-repo.git
    targetRevision: main
    path: apps/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
      allowEmpty: false
    syncOptions:
      - Validate=true
      - CreateNamespace=true
      - PrunePropagationPolicy=foreground
      - PruneLast=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
  revisionHistoryLimit: 10
```

### ApplicationSet

```yaml
# applicationset.yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: my-app
  namespace: argocd
spec:
  generators:
    # Generate for each cluster
    - clusters:
        selector:
          matchLabels:
            environment: production
    # Or for each directory
    - git:
        repoURL: https://github.com/myorg/config-repo.git
        revision: main
        directories:
          - path: apps/*
    # Or from list
    - list:
        elements:
          - cluster: development
            url: https://dev-cluster.example.com
            namespace: dev
          - cluster: staging
            url: https://staging-cluster.example.com
            namespace: staging
          - cluster: production
            url: https://prod-cluster.example.com
            namespace: prod
  template:
    metadata:
      name: '{{cluster}}-my-app'
    spec:
      project: default
      source:
        repoURL: https://github.com/myorg/config-repo.git
        targetRevision: main
        path: 'apps/overlays/{{cluster}}'
      destination:
        server: '{{url}}'
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
```

### ArgoCD Project

```yaml
# argocd-project.yaml
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
  namespace: argocd
spec:
  description: Production environment project
  sourceRepos:
    - 'https://github.com/myorg/*'
  destinations:
    - namespace: production
      server: https://kubernetes.default.svc
    - namespace: production-*
      server: https://kubernetes.default.svc
  clusterResourceWhitelist:
    - group: ''
      kind: Namespace
  namespaceResourceBlacklist:
    - group: ''
      kind: ResourceQuota
    - group: ''
      kind: LimitRange
  roles:
    - name: developer
      description: Developer access
      policies:
        - p, proj:production:developer, applications, get, production/*, allow
        - p, proj:production:developer, applications, sync, production/*, allow
      groups:
        - developers
```

### Helm Application

```yaml
# helm-application.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: my-app-helm
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/myorg/helm-charts.git
    targetRevision: main
    path: charts/my-app
    helm:
      releaseName: my-app
      valueFiles:
        - values.yaml
        - values-production.yaml
      values: |
        replicaCount: 3
        image:
          tag: 1.2.3
      parameters:
        - name: image.repository
          value: my-registry.com/my-app
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Flux CD

### Installation

```bash
# Install Flux CLI
curl -s https://fluxcd.io/install.sh | sudo bash

# Bootstrap Flux with GitHub
flux bootstrap github \
  --owner=myorg \
  --repository=fleet-infra \
  --branch=main \
  --path=clusters/production \
  --personal

# Check installation
flux check
```

### GitRepository Source

```yaml
# git-repository.yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/myorg/config-repo
  ref:
    branch: main
  secretRef:
    name: github-credentials
```

### Kustomization

```yaml
# kustomization.yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: my-app
  namespace: flux-system
spec:
  interval: 10m
  targetNamespace: production
  sourceRef:
    kind: GitRepository
    name: my-app
  path: ./apps/overlays/production
  prune: true
  timeout: 2m
  validation: client
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: my-app
      namespace: production
  postBuild:
    substitute:
      cluster_env: production
    substituteFrom:
      - kind: ConfigMap
        name: cluster-vars
```

### HelmRelease

```yaml
# helm-release.yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: my-app
  namespace: production
spec:
  interval: 5m
  chart:
    spec:
      chart: my-app
      version: '1.x.x'
      sourceRef:
        kind: HelmRepository
        name: my-charts
        namespace: flux-system
      interval: 1m
  values:
    replicaCount: 3
    image:
      repository: my-registry.com/my-app
      tag: 1.2.3
  valuesFrom:
    - kind: ConfigMap
      name: my-app-values
      valuesKey: values.yaml
    - kind: Secret
      name: my-app-secrets
      valuesKey: secrets.yaml
  upgrade:
    remediation:
      retries: 3
  rollback:
    cleanupOnFail: true
```

### Image Automation

```yaml
# image-repository.yaml
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageRepository
metadata:
  name: my-app
  namespace: flux-system
spec:
  image: my-registry.com/my-app
  interval: 1m
  secretRef:
    name: registry-credentials

---
# image-policy.yaml
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImagePolicy
metadata:
  name: my-app
  namespace: flux-system
spec:
  imageRepositoryRef:
    name: my-app
  policy:
    semver:
      range: '>=1.0.0 <2.0.0'
    # Or alphabetical
    # alphabetical:
    #   order: asc
    # Or numerical
    # numerical:
    #   order: asc

---
# image-update-automation.yaml
apiVersion: image.toolkit.fluxcd.io/v1beta1
kind: ImageUpdateAutomation
metadata:
  name: flux-system
  namespace: flux-system
spec:
  interval: 1m
  sourceRef:
    kind: GitRepository
    name: flux-system
  git:
    checkout:
      ref:
        branch: main
    commit:
      author:
        email: flux@example.com
        name: Flux
      messageTemplate: |
        Automated image update

        Automation: {{ .AutomationObject }}

        Files:
        {{ range $filename, $_ := .Updated.Files -}}
        - {{ $filename }}
        {{ end -}}

        Objects:
        {{ range $resource, $_ := .Updated.Objects -}}
        - {{ $resource.Kind }} {{ $resource.Name }}
        {{ end -}}
    push:
      branch: main
  update:
    path: ./clusters/production
    strategy: Setters
```

### Deployment with Image Marker

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      containers:
        - name: app
          image: my-registry.com/my-app:1.2.3 # {"$imagepolicy": "flux-system:my-app"}
```

## Kustomize for GitOps

### Base Configuration

```yaml
# apps/base/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
  - configmap.yaml

commonLabels:
  app.kubernetes.io/name: my-app
  app.kubernetes.io/managed-by: kustomize
```

### Environment Overlay

```yaml
# apps/overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: production

resources:
  - ../../base
  - ingress.yaml
  - hpa.yaml

patches:
  - path: patches/deployment.yaml
  - path: patches/configmap.yaml

images:
  - name: my-app
    newName: my-registry.com/my-app
    newTag: 1.2.3

replicas:
  - name: my-app
    count: 3

configMapGenerator:
  - name: my-app-config
    behavior: merge
    literals:
      - NODE_ENV=production
      - LOG_LEVEL=warn

secretGenerator:
  - name: my-app-secrets
    type: Opaque
    literals:
      - API_KEY=prod-secret
```

### Patch Example

```yaml
# apps/overlays/production/patches/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 5
  template:
    spec:
      containers:
        - name: app
          resources:
            limits:
              cpu: 1000m
              memory: 512Mi
            requests:
              cpu: 200m
              memory: 256Mi
```

## CI/CD Integration

### GitHub Actions with ArgoCD

```yaml
# .github/workflows/deploy.yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build and push image
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: my-registry.com/my-app:${{ github.sha }}

  update-manifest:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Checkout config repo
        uses: actions/checkout@v4
        with:
          repository: myorg/config-repo
          token: ${{ secrets.CONFIG_REPO_TOKEN }}

      - name: Update image tag
        run: |
          cd apps/overlays/production
          kustomize edit set image my-app=my-registry.com/my-app:${{ github.sha }}

      - name: Commit and push
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add .
          git commit -m "Update my-app to ${{ github.sha }}"
          git push

  sync-argocd:
    needs: update-manifest
    runs-on: ubuntu-latest
    steps:
      - name: Sync ArgoCD
        uses: clowdhaus/argo-cd-action@v1
        with:
          command: app sync my-app
          options: --grpc-web
        env:
          ARGOCD_SERVER: argocd.example.com
          ARGOCD_AUTH_TOKEN: ${{ secrets.ARGOCD_TOKEN }}
```

## Progressive Delivery

### Argo Rollouts

```yaml
# rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-app
spec:
  replicas: 5
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-registry.com/my-app:1.2.3
  strategy:
    canary:
      canaryService: my-app-canary
      stableService: my-app-stable
      trafficRouting:
        istio:
          virtualService:
            name: my-app
            routes:
              - primary
      steps:
        - setWeight: 10
        - pause: { duration: 5m }
        - setWeight: 30
        - pause: { duration: 5m }
        - setWeight: 50
        - pause: { duration: 5m }
        - setWeight: 100
      analysis:
        templates:
          - templateName: success-rate
        startingStep: 1
        args:
          - name: service-name
            value: my-app-canary

---
# analysis-template.yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service-name
  metrics:
    - name: success-rate
      interval: 1m
      successCondition: result[0] >= 0.95
      provider:
        prometheus:
          address: http://prometheus:9090
          query: |
            sum(rate(http_requests_total{service="{{args.service-name}}",status=~"2.*"}[5m])) /
            sum(rate(http_requests_total{service="{{args.service-name}}"}[5m]))
```

### Flagger

```yaml
# flagger-canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: my-app
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  progressDeadlineSeconds: 60
  service:
    port: 80
    targetPort: 3000
    gateways:
      - public-gateway.istio-system.svc.cluster.local
    hosts:
      - api.example.com
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
      - name: request-success-rate
        thresholdRange:
          min: 99
        interval: 1m
      - name: request-duration
        thresholdRange:
          max: 500
        interval: 1m
    webhooks:
      - name: load-test
        url: http://loadtester.test/
        timeout: 5s
        metadata:
          cmd: "hey -z 1m -q 10 http://my-app-canary.production/"
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitOps Best Practices                         │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Separate app code repo from config repo                       │
│ ☐ Use Kustomize or Helm for environment differences             │
│ ☐ Enable automated sync with self-heal                          │
│ ☐ Implement proper RBAC for GitOps tools                        │
│ ☐ Use sealed secrets or external secrets operator               │
│ ☐ Set up health checks for applications                         │
│ ☐ Configure notification alerts                                 │
│ ☐ Implement progressive delivery for production                 │
│ ☐ Use ApplicationSets for multi-cluster                         │
│ ☐ Enable image automation for staging                           │
│ ☐ Protect main branch with required reviews                     │
│ ☐ Keep sync intervals appropriate (not too aggressive)          │
└─────────────────────────────────────────────────────────────────┘
```
