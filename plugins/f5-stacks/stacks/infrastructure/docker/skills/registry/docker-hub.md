---
name: docker-hub
description: Working with Docker Hub public registry
applies_to: docker
---

# Docker Hub

## Overview

Docker Hub is the default public registry for Docker images.
- URL: https://hub.docker.com
- Default registry (no prefix needed)
- Public and private repositories

## Authentication

### Login

```bash
# Interactive login
docker login

# With credentials
docker login -u username -p password

# With token (recommended)
docker login -u username --password-stdin < token.txt

# Environment variable
echo $DOCKER_TOKEN | docker login -u username --password-stdin
```

### Logout

```bash
docker logout
```

### Credential Storage

```bash
# Check current credentials
cat ~/.docker/config.json

# Configure credential helper
# macOS
brew install docker-credential-helper

# In ~/.docker/config.json
{
  "credsStore": "osxkeychain"
}
```

## Pulling Images

### Basic Pull

```bash
# Pull from Docker Hub (default)
docker pull nginx
docker pull nginx:alpine

# Equivalent to
docker pull docker.io/library/nginx:alpine
```

### Pull Official Images

```bash
# Official images (library/)
docker pull python:3.12-slim
docker pull postgres:16-alpine
docker pull redis:7-alpine
docker pull node:20-alpine
```

### Pull Verified Publisher Images

```bash
# Verified publishers
docker pull bitnami/postgresql
docker pull grafana/grafana
docker pull prom/prometheus
```

### Pull with Digest

```bash
# Pin to specific digest (immutable)
docker pull nginx@sha256:abc123...

# In Dockerfile
FROM nginx:alpine@sha256:abc123...
```

## Pushing Images

### Tag for Push

```bash
# Tag with Docker Hub username
docker tag myapp:latest username/myapp:latest

# Tag with version
docker tag myapp:latest username/myapp:v1.0.0
```

### Push Image

```bash
# Login first
docker login

# Push
docker push username/myapp:latest
docker push username/myapp:v1.0.0

# Push all tags
docker push username/myapp --all-tags
```

### Push to Organization

```bash
# Tag for organization
docker tag myapp:latest myorg/myapp:latest

# Push
docker push myorg/myapp:latest
```

## Repository Management

### Create Repository

```bash
# Via web interface: hub.docker.com → Create Repository
# Or push to create automatically
docker push username/new-repo:latest
```

### Repository Settings (Web UI)

- **Visibility**: Public/Private
- **Description**: Repository info
- **Build Settings**: Automated builds
- **Collaborators**: Team access
- **Webhooks**: CI/CD integration

## Automated Builds

### Link to GitHub/GitLab

1. Go to repository settings on Docker Hub
2. Configure Build Rules
3. Set source branch and tag patterns

### Build Rules Example

```yaml
# Source: GitHub branch main
# Docker Tag: latest
# Dockerfile location: /Dockerfile
# Build Context: /

# Source: GitHub tag /^v[0-9.]+$/
# Docker Tag: {sourceref}
# Dockerfile location: /Dockerfile
```

## Docker Hub API

### Get Token

```bash
# Get authentication token
TOKEN=$(curl -s -H "Content-Type: application/json" \
  -X POST -d '{"username": "user", "password": "pass"}' \
  https://hub.docker.com/v2/users/login/ | jq -r .token)
```

### List Repositories

```bash
# List user repositories
curl -s -H "Authorization: JWT ${TOKEN}" \
  https://hub.docker.com/v2/repositories/username/?page_size=100
```

### List Tags

```bash
# List tags for repository
curl -s \
  https://hub.docker.com/v2/repositories/library/nginx/tags/?page_size=100
```

### Delete Tag

```bash
# Delete specific tag
curl -X DELETE -H "Authorization: JWT ${TOKEN}" \
  https://hub.docker.com/v2/repositories/username/repo/tags/v1.0.0/
```

## Rate Limits

### Current Limits

| User Type | Pulls per 6 hours |
|-----------|-------------------|
| Anonymous | 100 |
| Authenticated | 200 |
| Pro/Team | Unlimited |

### Check Remaining

```bash
# Check rate limit
TOKEN=$(curl -s "https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/nginx:pull" | jq -r .token)

curl -s -I -H "Authorization: Bearer $TOKEN" \
  https://registry-1.docker.io/v2/library/nginx/manifests/latest \
  | grep -i ratelimit

# Output:
# ratelimit-limit: 100;w=21600
# ratelimit-remaining: 95;w=21600
```

### Avoid Rate Limits

```dockerfile
# 1. Always authenticate
docker login

# 2. Use local cache
docker pull nginx:alpine  # Cache locally

# 3. Use mirror/proxy
# Configure daemon.json
{
  "registry-mirrors": ["https://mirror.example.com"]
}
```

## Docker Compose with Docker Hub

```yaml
services:
  web:
    # Official image
    image: nginx:alpine

  api:
    # User repository
    image: username/myapi:v1.0.0

  db:
    # Verified publisher
    image: bitnami/postgresql:16

  custom:
    # Build and push
    build: ./app
    image: username/myapp:${VERSION:-latest}
```

### Build and Push

```bash
# Build
docker compose build

# Push
docker compose push

# Or combined
docker compose build --push
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Push to Docker Hub

on:
  push:
    tags:
      - 'v*'

jobs:
  push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            username/myapp:latest
            username/myapp:${{ github.ref_name }}
```

### GitLab CI

```yaml
push:
  stage: deploy
  image: docker:24
  services:
    - docker:dind
  before_script:
    - docker login -u $DOCKERHUB_USERNAME -p $DOCKERHUB_TOKEN
  script:
    - docker build -t $DOCKERHUB_USERNAME/myapp:$CI_COMMIT_TAG .
    - docker push $DOCKERHUB_USERNAME/myapp:$CI_COMMIT_TAG
  only:
    - tags
```

## Best Practices

### Repository Naming

```
# Format: username/repository:tag
mycompany/api:v1.0.0
mycompany/web:latest
mycompany/worker:staging
```

### Tag Conventions

```bash
# Version tags
v1.0.0, v1.0.1, v1.1.0

# Environment tags
production, staging, development

# Branch tags
main, develop, feature-x

# Commit tags
abc1234 (short SHA)
```

### Security

```bash
# Use access tokens, not passwords
# hub.docker.com → Account Settings → Security → Access Tokens

# Read/Write tokens for CI/CD
# Read-only tokens for pulls

# Never commit credentials
# Use CI/CD secrets
```

### Documentation

```yaml
# Include in repository:
# - README.md (displayed on Docker Hub)
# - Usage examples
# - Environment variables
# - Volume mounts
# - Port mappings
```

## Complete Example

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: ./api
      target: production
    image: mycompany/api:${VERSION:-latest}
    environment:
      - NODE_ENV=production

# Build, tag, and push
# VERSION=v1.0.0 docker compose build
# VERSION=v1.0.0 docker compose push
```

```bash
#!/bin/bash
# release.sh

VERSION=$1

# Build
docker compose build

# Tag
docker tag mycompany/api:latest mycompany/api:$VERSION

# Push
docker push mycompany/api:latest
docker push mycompany/api:$VERSION

echo "Released mycompany/api:$VERSION"
```

## Related Skills
- registry/private-registry
- registry/image-tagging
- security/image-security
