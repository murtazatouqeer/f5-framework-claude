---
name: docker-image-tagging
description: Docker image tagging strategies and best practices
applies_to: docker
---

# Docker Image Tagging

## Tagging Basics

### Tag Format

```
[registry/][repository/]name[:tag][@digest]

Examples:
nginx                                    # Default: docker.io/library/nginx:latest
nginx:alpine                            # With tag
nginx:1.25.3-alpine                     # Specific version
nginx@sha256:abc123...                  # With digest
myregistry.com/myapp:v1.0.0            # Full path
ghcr.io/username/myapp:latest          # GitHub Container Registry
```

### Tagging Commands

```bash
# Tag an image
docker tag source:tag target:tag

# Examples
docker tag myapp:latest myapp:v1.0.0
docker tag myapp:latest username/myapp:v1.0.0
docker tag myapp:latest registry.com/myapp:v1.0.0

# Tag with multiple tags
docker tag myapp:latest myapp:v1.0.0
docker tag myapp:latest myapp:v1.0
docker tag myapp:latest myapp:v1
```

## Tagging Strategies

### Semantic Versioning

```bash
# Full semver
v1.0.0
v1.0.1
v1.1.0
v2.0.0

# Major.minor
v1.0
v1.1
v2.0

# Major only
v1
v2

# Complete tagging
docker tag myapp:latest myapp:v1.2.3
docker tag myapp:latest myapp:v1.2
docker tag myapp:latest myapp:v1
docker tag myapp:latest myapp:latest
```

### Git-Based Tags

```bash
# Commit SHA (short)
docker tag myapp:latest myapp:abc1234

# Commit SHA (full)
docker tag myapp:latest myapp:abc1234567890

# Branch name
docker tag myapp:latest myapp:main
docker tag myapp:latest myapp:develop
docker tag myapp:latest myapp:feature-auth

# Git tag
docker tag myapp:latest myapp:v1.0.0
```

### Environment Tags

```bash
# Environment-based
docker tag myapp:latest myapp:production
docker tag myapp:latest myapp:staging
docker tag myapp:latest myapp:development

# Combined with version
docker tag myapp:latest myapp:v1.0.0-production
docker tag myapp:latest myapp:v1.0.0-staging
```

### Date-Based Tags

```bash
# Date format
docker tag myapp:latest myapp:20240115
docker tag myapp:latest myapp:2024-01-15

# Date + build number
docker tag myapp:latest myapp:20240115.1
docker tag myapp:latest myapp:20240115.2

# Timestamp
docker tag myapp:latest myapp:20240115-143022
```

### Build Number Tags

```bash
# CI build number
docker tag myapp:latest myapp:build-123
docker tag myapp:latest myapp:b123

# Combined
docker tag myapp:latest myapp:v1.0.0-b123
```

## Image Digest

### Why Use Digests

```bash
# Tags are mutable - same tag can point to different images
docker pull nginx:latest  # Today's latest
docker pull nginx:latest  # Tomorrow might be different

# Digests are immutable
docker pull nginx@sha256:abc123...  # Always same image
```

### Get Digest

```bash
# After pull
docker images --digests nginx

# From registry
docker manifest inspect nginx:alpine

# From build
docker build -t myapp:latest .
docker inspect myapp:latest --format '{{.RepoDigests}}'
```

### Use Digest

```dockerfile
# Pin to specific digest
FROM node:20-alpine@sha256:abc123def456...

# Combining tag and digest (digest takes precedence)
FROM node:20-alpine@sha256:abc123def456...
```

## Tagging in CI/CD

### GitHub Actions

```yaml
name: Build and Push

on:
  push:
    branches: [main]
    tags:
      - 'v*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: username/myapp
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=semver,pattern={{major}}
            type=sha

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

### GitLab CI

```yaml
variables:
  IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG

build:
  script:
    - docker build -t $IMAGE_TAG .
    - docker push $IMAGE_TAG

    # Also tag with commit SHA
    - docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA

    # Tag as latest for main branch
    - |
      if [ "$CI_COMMIT_BRANCH" == "main" ]; then
        docker tag $IMAGE_TAG $CI_REGISTRY_IMAGE:latest
        docker push $CI_REGISTRY_IMAGE:latest
      fi
```

### Shell Script

```bash
#!/bin/bash
# build-and-tag.sh

VERSION=${1:-$(git describe --tags --always)}
COMMIT=$(git rev-parse --short HEAD)
DATE=$(date +%Y%m%d)

IMAGE=myregistry/myapp

# Build
docker build -t $IMAGE:$VERSION .

# Apply tags
docker tag $IMAGE:$VERSION $IMAGE:$COMMIT
docker tag $IMAGE:$VERSION $IMAGE:$DATE
docker tag $IMAGE:$VERSION $IMAGE:latest

# Push all
docker push $IMAGE:$VERSION
docker push $IMAGE:$COMMIT
docker push $IMAGE:$DATE
docker push $IMAGE:latest
```

## Docker Compose Tagging

### With Environment Variables

```yaml
services:
  api:
    image: myregistry/api:${VERSION:-latest}
    build:
      context: ./api

  web:
    image: myregistry/web:${VERSION:-latest}
    build:
      context: ./web
```

```bash
# Build with specific version
VERSION=v1.0.0 docker compose build

# Push
VERSION=v1.0.0 docker compose push
```

### Multi-Tag Build

```yaml
# docker-compose.build.yml
services:
  api:
    build:
      context: ./api
    image: myregistry/api

  web:
    build:
      context: ./web
    image: myregistry/web
```

```bash
#!/bin/bash
# Build and tag with multiple tags

VERSION=$1
COMMIT=$(git rev-parse --short HEAD)

# Build
docker compose -f docker-compose.build.yml build

# Tag each service
for SERVICE in api web; do
  docker tag myregistry/$SERVICE:latest myregistry/$SERVICE:$VERSION
  docker tag myregistry/$SERVICE:latest myregistry/$SERVICE:$COMMIT
done

# Push all tags
docker push myregistry/api:latest
docker push myregistry/api:$VERSION
docker push myregistry/api:$COMMIT
docker push myregistry/web:latest
docker push myregistry/web:$VERSION
docker push myregistry/web:$COMMIT
```

## Tag Management

### List Tags

```bash
# Local images
docker images myapp

# From Docker Hub
curl -s https://hub.docker.com/v2/repositories/library/nginx/tags/?page_size=100 | jq '.results[].name'

# From private registry
curl -s https://registry.internal:5000/v2/myapp/tags/list
```

### Delete Tags

```bash
# Local
docker rmi myapp:old-tag

# From registry (if enabled)
# Get digest first
DIGEST=$(curl -sI -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
  https://registry:5000/v2/myapp/manifests/v1.0.0 \
  | grep docker-content-digest | cut -d' ' -f2)

# Delete
curl -X DELETE https://registry:5000/v2/myapp/manifests/$DIGEST
```

### Cleanup Old Tags

```bash
#!/bin/bash
# cleanup-old-tags.sh
# Keep last N tags

REPO="myregistry/myapp"
KEEP=10

# List tags sorted by date
TAGS=$(docker image ls --format "{{.Tag}}" $REPO | tail -n +$((KEEP+1)))

for TAG in $TAGS; do
  echo "Removing $REPO:$TAG"
  docker rmi $REPO:$TAG
done
```

## Best Practices

### Do

```bash
# Use specific versions
FROM node:20.10.0-alpine

# Use semantic versioning
v1.0.0, v1.0.1, v1.1.0

# Include both version and latest
docker push myapp:v1.0.0
docker push myapp:latest

# Use digests for security-critical images
FROM node:20-alpine@sha256:abc123...

# Tag with commit SHA for traceability
docker tag myapp:latest myapp:abc1234
```

### Don't

```bash
# Don't rely only on :latest
FROM nginx:latest  # Changes over time

# Don't use mutable tags in production
FROM myapp:development

# Don't overwrite tags without versioning
docker push myapp:release  # Loses history
```

### Production Recommendations

```bash
# Immutable deployment tags
v1.0.0-abc1234       # Version + commit
v1.0.0-20240115.1    # Version + date + build

# Development tags
develop              # Latest develop branch
feature-auth         # Feature branch
pr-123              # Pull request

# Environment promotion
staging-v1.0.0       # Staged for testing
production-v1.0.0    # Production release
```

## Complete Tagging Workflow

```bash
#!/bin/bash
# release.sh - Complete tagging workflow

set -e

# Get version from argument or git tag
VERSION=${1:-$(git describe --tags --always)}
COMMIT=$(git rev-parse --short HEAD)
BRANCH=$(git rev-parse --abbrev-ref HEAD)
DATE=$(date +%Y%m%d)
REGISTRY="myregistry.com"
IMAGE="$REGISTRY/myapp"

echo "Building $IMAGE version $VERSION"

# Build
docker build \
  --build-arg VERSION=$VERSION \
  --build-arg COMMIT=$COMMIT \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t $IMAGE:$VERSION .

# Apply standard tags
docker tag $IMAGE:$VERSION $IMAGE:$COMMIT
docker tag $IMAGE:$VERSION $IMAGE:$DATE

# Branch-specific tags
if [ "$BRANCH" == "main" ]; then
  docker tag $IMAGE:$VERSION $IMAGE:latest
fi

if [ "$BRANCH" == "develop" ]; then
  docker tag $IMAGE:$VERSION $IMAGE:develop
fi

# Semantic version tags (if semver)
if [[ $VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  MAJOR=$(echo $VERSION | cut -d. -f1)
  MINOR=$(echo $VERSION | cut -d. -f1-2)
  docker tag $IMAGE:$VERSION $IMAGE:$MAJOR
  docker tag $IMAGE:$VERSION $IMAGE:$MINOR
fi

# Push all tags
echo "Pushing tags..."
docker push $IMAGE --all-tags

echo "Done! Tags pushed:"
docker images $IMAGE --format "{{.Tag}}"
```

## Related Skills
- registry/docker-hub
- registry/private-registry
- dockerfile/best-practices
