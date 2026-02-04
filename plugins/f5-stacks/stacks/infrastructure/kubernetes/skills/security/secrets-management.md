---
name: k8s-secrets-management
description: Kubernetes Secrets Management and External Secret Stores
applies_to: kubernetes
---

# Kubernetes Secrets Management

## Overview

Best practices for managing secrets in Kubernetes, including native Secrets, external secret managers, and encryption.

## Native Kubernetes Secrets

### Limitations

- Base64 encoded (not encrypted) by default
- Stored in etcd
- Visible to anyone with RBAC access
- No automatic rotation
- No audit trail

### Enable Encryption at Rest

```yaml
# /etc/kubernetes/encryption-config.yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-32-byte-key>
      - identity: {}  # Fallback for reading unencrypted
```

```bash
# Apply to API server
kube-apiserver --encryption-provider-config=/etc/kubernetes/encryption-config.yaml

# Verify encryption
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

## External Secrets Operator

### Installation

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace
```

### ClusterSecretStore

```yaml
# AWS Secrets Manager
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: aws-secrets-manager
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets

---
# HashiCorp Vault
apiVersion: external-secrets.io/v1beta1
kind: ClusterSecretStore
metadata:
  name: vault
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "external-secrets"
          serviceAccountRef:
            name: external-secrets
            namespace: external-secrets
```

### ExternalSecret

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  refreshInterval: 1h

  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secrets-manager

  target:
    name: app-secrets
    creationPolicy: Owner

  data:
    - secretKey: DB_PASSWORD
      remoteRef:
        key: prod/myapp/database
        property: password

    - secretKey: API_KEY
      remoteRef:
        key: prod/myapp/api
        property: key

  dataFrom:
    - extract:
        key: prod/myapp/config
```

### ExternalSecret for Vault

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: vault-secrets
  namespace: production
spec:
  refreshInterval: 30m

  secretStoreRef:
    kind: ClusterSecretStore
    name: vault

  target:
    name: app-secrets

  data:
    - secretKey: database-password
      remoteRef:
        key: secret/data/production/database
        property: password

    - secretKey: api-key
      remoteRef:
        key: secret/data/production/api
        property: key
```

## Sealed Secrets

### Installation

```bash
# Install controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/controller.yaml

# Install kubeseal CLI
brew install kubeseal
```

### Create Sealed Secret

```bash
# Create regular secret YAML
kubectl create secret generic app-secrets \
  --from-literal=password=supersecret \
  --dry-run=client -o yaml > secret.yaml

# Seal it
kubeseal --format yaml < secret.yaml > sealed-secret.yaml

# Apply sealed secret
kubectl apply -f sealed-secret.yaml
```

### Sealed Secret Resource

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: app-secrets
  namespace: production
spec:
  encryptedData:
    password: AgBy3i4OJSWK+...encrypted...
  template:
    metadata:
      name: app-secrets
      namespace: production
    type: Opaque
```

### Scoped Secrets

```bash
# Namespace-scoped (default)
kubeseal --scope namespace-wide < secret.yaml > sealed-secret.yaml

# Cluster-scoped
kubeseal --scope cluster-wide < secret.yaml > sealed-secret.yaml

# Strict (exact name + namespace)
kubeseal --scope strict < secret.yaml > sealed-secret.yaml
```

## HashiCorp Vault Agent Injector

### Installation

```bash
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install vault hashicorp/vault \
  --set "injector.enabled=true" \
  --set "server.enabled=false"
```

### Pod Annotations

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
  annotations:
    vault.hashicorp.com/agent-inject: "true"
    vault.hashicorp.com/role: "app"
    vault.hashicorp.com/agent-inject-secret-database.txt: "secret/data/production/database"
    vault.hashicorp.com/agent-inject-template-database.txt: |
      {{- with secret "secret/data/production/database" -}}
      postgresql://{{ .Data.data.username }}:{{ .Data.data.password }}@postgres:5432/mydb
      {{- end }}
spec:
  serviceAccountName: app
  containers:
    - name: app
      image: myapp:1.0.0
      # Secret available at /vault/secrets/database.txt
```

## AWS Secrets Store CSI Driver

### Installation

```bash
helm repo add secrets-store-csi-driver https://kubernetes-sigs.github.io/secrets-store-csi-driver/charts
helm install csi-secrets-store secrets-store-csi-driver/secrets-store-csi-driver \
  --namespace kube-system

# AWS provider
kubectl apply -f https://raw.githubusercontent.com/aws/secrets-store-csi-driver-provider-aws/main/deployment/aws-provider-installer.yaml
```

### SecretProviderClass

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: aws-secrets
  namespace: production
spec:
  provider: aws
  parameters:
    objects: |
      - objectName: "prod/myapp/database"
        objectType: "secretsmanager"
        jmesPath:
          - path: username
            objectAlias: db_username
          - path: password
            objectAlias: db_password

  secretObjects:
    - secretName: db-credentials
      type: Opaque
      data:
        - objectName: db_username
          key: username
        - objectName: db_password
          key: password
```

### Pod Using CSI

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  serviceAccountName: app
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: secrets
          mountPath: /mnt/secrets
          readOnly: true
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password

  volumes:
    - name: secrets
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: aws-secrets
```

## Secret Rotation

### External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: rotating-secret
spec:
  refreshInterval: 15m  # Check every 15 minutes
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secrets-manager
  target:
    name: app-secrets
  data:
    - secretKey: api-key
      remoteRef:
        key: prod/myapp/api-key
```

### Reloader for Deployment Updates

```bash
# Install Reloader
kubectl apply -f https://raw.githubusercontent.com/stakater/Reloader/master/deployments/kubernetes/reloader.yaml
```

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  annotations:
    reloader.stakater.com/auto: "true"
    # Or specific:
    # secret.reloader.stakater.com/reload: "app-secrets"
spec:
  template:
    spec:
      containers:
        - name: api
          envFrom:
            - secretRef:
                name: app-secrets
```

## RBAC for Secrets

### Restrict Secret Access

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
  namespace: production
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["app-secrets"]  # Only specific secrets
    verbs: ["get"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-secret-access
  namespace: production
subjects:
  - kind: ServiceAccount
    name: app
    namespace: production
roleRef:
  kind: Role
  name: secret-reader
  apiGroup: rbac.authorization.k8s.io
```

## Commands

```bash
# List secrets
kubectl get secrets -n production

# Decode secret
kubectl get secret app-secrets -o jsonpath='{.data.password}' | base64 -d

# Create secret
kubectl create secret generic app-secrets \
  --from-literal=password=secret123

# Update secret
kubectl create secret generic app-secrets \
  --from-literal=password=newsecret \
  --dry-run=client -o yaml | kubectl apply -f -

# Check external secrets
kubectl get externalsecrets -n production
kubectl describe externalsecret app-secrets

# Check sealed secrets
kubectl get sealedsecrets -n production
```

## Best Practices

1. **Use external secret managers** (Vault, AWS SM, etc.) in production
2. **Enable encryption at rest** for native secrets
3. **Use Sealed Secrets** for GitOps workflows
4. **Implement automatic rotation** with External Secrets Operator
5. **Apply least-privilege RBAC** for secret access
6. **Avoid secrets in environment variables** when possible (use files)
7. **Use service accounts** with IAM roles (IRSA, Workload Identity)
8. **Audit secret access** with Kubernetes audit logging
9. **Never commit secrets** to version control
10. **Rotate secrets regularly** and after incidents
