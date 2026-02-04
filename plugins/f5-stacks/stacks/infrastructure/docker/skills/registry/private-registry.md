---
name: docker-private-registry
description: Setting up and using private Docker registries
applies_to: docker
---

# Private Docker Registry

## Registry Options

| Registry | Type | Features |
|----------|------|----------|
| Docker Registry | Self-hosted | Basic, open-source |
| Harbor | Self-hosted | Enterprise, RBAC, scanning |
| AWS ECR | Cloud | AWS integration |
| GCP Artifact Registry | Cloud | GCP integration |
| Azure ACR | Cloud | Azure integration |
| GitHub Container Registry | Cloud | GitHub integration |
| GitLab Container Registry | Cloud | GitLab integration |

## Self-Hosted Docker Registry

### Basic Setup

```yaml
# docker-compose.yml
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - registry_data:/var/lib/registry
    environment:
      REGISTRY_STORAGE_DELETE_ENABLED: "true"

volumes:
  registry_data:
```

```bash
# Start registry
docker compose up -d

# Push to local registry
docker tag myapp:latest localhost:5000/myapp:latest
docker push localhost:5000/myapp:latest

# Pull from local registry
docker pull localhost:5000/myapp:latest
```

### With TLS

```yaml
services:
  registry:
    image: registry:2
    ports:
      - "443:443"
    volumes:
      - registry_data:/var/lib/registry
      - ./certs:/certs:ro
    environment:
      REGISTRY_HTTP_ADDR: 0.0.0.0:443
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
      REGISTRY_HTTP_TLS_KEY: /certs/domain.key
```

```bash
# Generate self-signed cert
openssl req -newkey rsa:4096 -nodes -sha256 \
  -keyout domain.key -x509 -days 365 -out domain.crt
```

### With Authentication

```yaml
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - registry_data:/var/lib/registry
      - ./auth:/auth:ro
    environment:
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_REALM: Registry Realm
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
```

```bash
# Create htpasswd file
docker run --rm --entrypoint htpasswd registry:2 \
  -Bbn admin secretpassword > auth/htpasswd

# Login
docker login localhost:5000
```

### Production Configuration

```yaml
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - registry_data:/var/lib/registry
      - ./certs:/certs:ro
      - ./auth:/auth:ro
      - ./config.yml:/etc/docker/registry/config.yml:ro
    restart: unless-stopped

volumes:
  registry_data:
```

```yaml
# config.yml
version: 0.1
log:
  level: info
storage:
  filesystem:
    rootdirectory: /var/lib/registry
  delete:
    enabled: true
http:
  addr: 0.0.0.0:5000
  tls:
    certificate: /certs/domain.crt
    key: /certs/domain.key
auth:
  htpasswd:
    realm: Registry Realm
    path: /auth/htpasswd
```

## Harbor (Enterprise)

### Install with Helm

```bash
# Add Harbor helm repo
helm repo add harbor https://helm.goharbor.io

# Install
helm install harbor harbor/harbor \
  --set expose.type=ingress \
  --set expose.ingress.hosts.core=registry.example.com \
  --set persistence.enabled=true \
  --namespace harbor
```

### Docker Compose Install

```bash
# Download Harbor installer
wget https://github.com/goharbor/harbor/releases/download/v2.10.0/harbor-offline-installer-v2.10.0.tgz
tar xvf harbor-offline-installer-v2.10.0.tgz
cd harbor

# Configure
cp harbor.yml.tmpl harbor.yml
# Edit harbor.yml with your settings

# Install
./install.sh
```

## Cloud Registries

### AWS ECR

```bash
# Create repository
aws ecr create-repository --repository-name myapp

# Login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Tag and push
docker tag myapp:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
```

```yaml
# Docker Compose with ECR
services:
  api:
    image: 123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:latest
```

### GCP Artifact Registry

```bash
# Configure authentication
gcloud auth configure-docker us-docker.pkg.dev

# Create repository
gcloud artifacts repositories create myrepo \
  --repository-format=docker \
  --location=us

# Tag and push
docker tag myapp:latest us-docker.pkg.dev/myproject/myrepo/myapp:latest
docker push us-docker.pkg.dev/myproject/myrepo/myapp:latest
```

### Azure ACR

```bash
# Create registry
az acr create --resource-group mygroup --name myregistry --sku Basic

# Login
az acr login --name myregistry

# Tag and push
docker tag myapp:latest myregistry.azurecr.io/myapp:latest
docker push myregistry.azurecr.io/myapp:latest
```

### GitHub Container Registry

```bash
# Login with PAT
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag and push
docker tag myapp:latest ghcr.io/username/myapp:latest
docker push ghcr.io/username/myapp:latest
```

### GitLab Container Registry

```bash
# Login
docker login registry.gitlab.com

# Tag and push
docker tag myapp:latest registry.gitlab.com/username/project/myapp:latest
docker push registry.gitlab.com/username/project/myapp:latest
```

## Configure Docker Client

### Insecure Registries

```json
// /etc/docker/daemon.json
{
  "insecure-registries": ["registry.internal:5000"]
}
```

```bash
# Restart Docker
sudo systemctl restart docker
```

### Registry Mirrors

```json
// /etc/docker/daemon.json
{
  "registry-mirrors": [
    "https://mirror.gcr.io",
    "https://registry.internal:5000"
  ]
}
```

### Multiple Registries

```bash
# Login to multiple registries
docker login docker.io
docker login ghcr.io
docker login 123456789.dkr.ecr.us-east-1.amazonaws.com

# Credentials stored in ~/.docker/config.json
```

## Docker Compose with Private Registry

```yaml
services:
  api:
    image: registry.internal:5000/myapp:${VERSION:-latest}
    build:
      context: ./api

  db:
    image: registry.internal:5000/postgres-custom:16
```

### Build and Push

```bash
# Login first
docker login registry.internal:5000

# Build
docker compose build

# Push
docker compose push
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Private Registry
        uses: docker/login-action@v3
        with:
          registry: registry.internal:5000
          username: ${{ secrets.REGISTRY_USERNAME }}
          password: ${{ secrets.REGISTRY_PASSWORD }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: registry.internal:5000/myapp:${{ github.sha }}
```

### GitLab CI

```yaml
build:
  stage: build
  image: docker:24
  services:
    - docker:dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

## Registry API

### List Repositories

```bash
# List all repositories
curl -X GET https://registry.internal:5000/v2/_catalog

# With auth
curl -u user:pass https://registry.internal:5000/v2/_catalog
```

### List Tags

```bash
# List tags for repository
curl -X GET https://registry.internal:5000/v2/myapp/tags/list
```

### Delete Image

```bash
# Get digest
DIGEST=$(curl -s -I -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  https://registry.internal:5000/v2/myapp/manifests/v1.0.0 \
  | grep -i docker-content-digest | cut -d' ' -f2 | tr -d '\r')

# Delete by digest
curl -X DELETE https://registry.internal:5000/v2/myapp/manifests/$DIGEST
```

### Garbage Collection

```bash
# Run garbage collection on self-hosted registry
docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml

# Dry run
docker exec registry bin/registry garbage-collect --dry-run /etc/docker/registry/config.yml
```

## Security Best Practices

### Authentication

```yaml
# Always use authentication
services:
  registry:
    environment:
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
```

### TLS Encryption

```yaml
# Always use TLS
services:
  registry:
    environment:
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/cert.pem
      REGISTRY_HTTP_TLS_KEY: /certs/key.pem
```

### Image Scanning

```yaml
# Harbor with vulnerability scanning
# Configure Trivy scanner in Harbor UI
```

### Access Control

```yaml
# Use RBAC (Harbor)
# Project-level permissions
# Repository-level permissions
```

## Complete Self-Hosted Setup

```yaml
# docker-compose.yml
services:
  registry:
    image: registry:2
    ports:
      - "5000:5000"
    volumes:
      - registry_data:/var/lib/registry
      - ./certs:/certs:ro
      - ./auth:/auth:ro
    environment:
      REGISTRY_HTTP_TLS_CERTIFICATE: /certs/domain.crt
      REGISTRY_HTTP_TLS_KEY: /certs/domain.key
      REGISTRY_AUTH: htpasswd
      REGISTRY_AUTH_HTPASSWD_REALM: Private Registry
      REGISTRY_AUTH_HTPASSWD_PATH: /auth/htpasswd
      REGISTRY_STORAGE_DELETE_ENABLED: "true"
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "https://localhost:5000/v2/"]
      interval: 30s
      timeout: 10s
      retries: 3

  registry-ui:
    image: joxit/docker-registry-ui:latest
    ports:
      - "8080:80"
    environment:
      REGISTRY_TITLE: Private Registry
      REGISTRY_URL: https://registry:5000
      SINGLE_REGISTRY: "true"
    depends_on:
      - registry

volumes:
  registry_data:
```

## Related Skills
- registry/docker-hub
- registry/image-tagging
- security/image-security
