---
name: k8s-secrets
description: Kubernetes Secrets for sensitive data management
applies_to: kubernetes
---

# Kubernetes Secrets

## Overview

Secrets store sensitive data such as passwords, tokens, and keys. They're base64 encoded (not encrypted by default) and can be encrypted at rest.

## Secret Types

| Type | Description |
|------|-------------|
| `Opaque` | Arbitrary user-defined data (default) |
| `kubernetes.io/tls` | TLS certificate and key |
| `kubernetes.io/dockerconfigjson` | Docker registry credentials |
| `kubernetes.io/basic-auth` | Basic authentication credentials |
| `kubernetes.io/ssh-auth` | SSH private key |
| `kubernetes.io/service-account-token` | Service account token |

## Creating Secrets

### Opaque Secret (YAML)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: production
type: Opaque
data:
  # Base64 encoded values
  username: YWRtaW4=          # admin
  password: cGFzc3dvcmQxMjM=  # password123

stringData:
  # Plain text (auto-encoded)
  api-key: "sk-1234567890abcdef"
  connection-string: "postgresql://user:pass@host:5432/db"
```

### From kubectl

```bash
# From literals
kubectl create secret generic app-secrets \
  --from-literal=username=admin \
  --from-literal=password=secret123

# From files
kubectl create secret generic app-secrets \
  --from-file=username=./username.txt \
  --from-file=password=./password.txt

# From env file
kubectl create secret generic app-secrets \
  --from-env-file=.env.secrets
```

### TLS Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tls-secret
type: kubernetes.io/tls
data:
  tls.crt: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0t...
  tls.key: LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0t...
```

```bash
kubectl create secret tls tls-secret \
  --cert=path/to/tls.crt \
  --key=path/to/tls.key
```

### Docker Registry Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: docker-registry
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: eyJhdXRocyI6ey...
```

```bash
kubectl create secret docker-registry docker-registry \
  --docker-server=registry.example.com \
  --docker-username=myuser \
  --docker-password=mypassword \
  --docker-email=user@example.com
```

### Basic Auth Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: basic-auth
type: kubernetes.io/basic-auth
stringData:
  username: admin
  password: secret123
```

### SSH Auth Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ssh-key
type: kubernetes.io/ssh-auth
data:
  ssh-privatekey: LS0tLS1CRUdJTiBPUEVOU1...
```

```bash
kubectl create secret generic ssh-key \
  --from-file=ssh-privatekey=~/.ssh/id_rsa
```

## Using Secrets

### Environment Variables

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: myapp:1.0.0

      # Single key
      env:
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: password

        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: api-key
              optional: true
```

### All Keys as Environment

```yaml
envFrom:
  - secretRef:
      name: app-secrets
      optional: false

  # With prefix
  - secretRef:
      name: app-secrets
      prefix: SECRET_
```

### Volume Mount

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: myapp:1.0.0
      volumeMounts:
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true

  volumes:
    - name: secrets
      secret:
        secretName: app-secrets
        defaultMode: 0400  # r--------
```

### Mount Specific Keys

```yaml
volumes:
  - name: secrets
    secret:
      secretName: app-secrets
      items:
        - key: tls.crt
          path: cert.pem
        - key: tls.key
          path: key.pem
          mode: 0400
```

### Mount Single File

```yaml
volumeMounts:
  - name: secrets
    mountPath: /app/.env
    subPath: .env
    readOnly: true
```

## Production Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: production
  labels:
    app.kubernetes.io/name: api
    app.kubernetes.io/component: backend
  annotations:
    description: "API service secrets"
type: Opaque
stringData:
  # Database credentials
  DB_USERNAME: "api_user"
  DB_PASSWORD: "super-secret-password"

  # API keys
  JWT_SECRET: "jwt-signing-key-here"
  ENCRYPTION_KEY: "32-byte-encryption-key"

  # External service credentials
  AWS_ACCESS_KEY_ID: "AKIAIOSFODNN7EXAMPLE"
  AWS_SECRET_ACCESS_KEY: "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

  # OAuth credentials
  OAUTH_CLIENT_ID: "client-id"
  OAUTH_CLIENT_SECRET: "client-secret"
```

## Deployment with Secrets

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: api:1.0.0

          env:
            # From Secret
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: DB_PASSWORD

            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: api-secrets
                  key: JWT_SECRET

          volumeMounts:
            - name: secrets
              mountPath: /etc/secrets
              readOnly: true

      volumes:
        - name: secrets
          secret:
            secretName: api-secrets
            defaultMode: 0400

      # Pull from private registry
      imagePullSecrets:
        - name: docker-registry
```

## Image Pull Secrets

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
    - name: app
      image: registry.example.com/myapp:1.0.0

  imagePullSecrets:
    - name: docker-registry
```

### Default Image Pull Secret

```bash
# Add to service account
kubectl patch serviceaccount default \
  -p '{"imagePullSecrets": [{"name": "docker-registry"}]}'
```

## Immutable Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: immutable-secret
type: Opaque
immutable: true  # Cannot be updated
stringData:
  api-key: "sk-1234567890"
```

## Encryption at Rest

### EncryptionConfiguration

```yaml
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - aescbc:
          keys:
            - name: key1
              secret: <base64-encoded-key>
      - identity: {}
```

## External Secret Managers

### AWS Secrets Manager (External Secrets Operator)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: aws-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: aws-secrets-manager
  target:
    name: app-secrets
    creationPolicy: Owner
  data:
    - secretKey: password
      remoteRef:
        key: prod/myapp/db
        property: password
```

### HashiCorp Vault

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: vault-secret
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: vault
  target:
    name: app-secrets
  data:
    - secretKey: password
      remoteRef:
        key: secret/data/myapp
        property: password
```

## Sealed Secrets

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: mysecret
spec:
  encryptedData:
    password: AgBy3i4OJSWK...
```

```bash
# Create sealed secret
kubeseal --format yaml < secret.yaml > sealed-secret.yaml
```

## Commands

```bash
# List Secrets
kubectl get secrets
kubectl get secrets -n production

# Describe Secret
kubectl describe secret app-secrets

# View Secret (encoded)
kubectl get secret app-secrets -o yaml

# Decode Secret value
kubectl get secret app-secrets -o jsonpath='{.data.password}' | base64 -d

# Edit Secret
kubectl edit secret app-secrets

# Delete Secret
kubectl delete secret app-secrets

# Create from YAML
kubectl apply -f secret.yaml

# Export Secret (careful!)
kubectl get secret app-secrets -o yaml > secret-backup.yaml
```

## Best Practices

1. **Enable encryption at rest** for cluster-level security
2. **Use external secret managers** for production
3. **Never commit secrets** to version control
4. **Set restrictive permissions** (0400 for files)
5. **Use RBAC** to limit Secret access
6. **Rotate secrets regularly** with external managers
7. **Use immutable secrets** when possible
8. **Avoid logging secrets** in application code
9. **Use Sealed Secrets** for GitOps workflows
10. **Separate secrets by environment** (dev, staging, prod)
11. **Audit secret access** with audit logging
12. **Use service accounts** instead of long-lived tokens
