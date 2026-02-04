---
name: docker-build-performance
description: Optimizing Docker build speed and efficiency
applies_to: docker
---

# Docker Build Performance

## BuildKit

### Enable BuildKit

```bash
# Environment variable
export DOCKER_BUILDKIT=1
docker build .

# Docker daemon config
# /etc/docker/daemon.json
{
  "features": {
    "buildkit": true
  }
}

# Docker Compose
COMPOSE_DOCKER_CLI_BUILD=1 DOCKER_BUILDKIT=1 docker compose build
```

### BuildKit Syntax

```dockerfile
# Enable BuildKit features
# syntax=docker/dockerfile:1
FROM node:20-alpine
...
```

## Caching Strategies

### Layer Caching

```dockerfile
# Order by change frequency (least → most)

# 1. Base image (rarely changes)
FROM node:20-alpine

# 2. System dependencies (rarely change)
RUN apk add --no-cache curl

# 3. Package dependencies (change occasionally)
COPY package*.json ./
RUN npm ci

# 4. Source code (changes frequently)
COPY . .
RUN npm run build
```

### Dependency Cache

```dockerfile
# Node.js - cache node_modules
COPY package*.json ./
RUN npm ci
COPY . .

# Python - cache pip
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . .

# Go - cache go modules
COPY go.mod go.sum ./
RUN go mod download
COPY . .
```

### BuildKit Cache Mounts

```dockerfile
# syntax=docker/dockerfile:1

# NPM cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Pip cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# APT cache mount
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y package

# Go module cache
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go build -o /app/server
```

### External Cache

```bash
# Use registry as cache source
docker build \
  --cache-from myregistry/myapp:cache \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t myapp:latest .

# Push cache to registry
docker push myregistry/myapp:cache
```

## Parallel Builds

### Parallel Stage Execution

```dockerfile
# syntax=docker/dockerfile:1

# These stages build in parallel
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM node:20-alpine AS backend-builder
WORKDIR /app/backend
COPY backend/package*.json ./
RUN npm ci
COPY backend/ .
RUN npm run build

# Final stage combines results
FROM node:20-alpine
COPY --from=frontend-builder /app/frontend/dist /app/public
COPY --from=backend-builder /app/backend/dist /app
CMD ["node", "/app/server.js"]
```

### Parallel Dependencies

```dockerfile
# syntax=docker/dockerfile:1

FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build
```

## Build Arguments

### Conditional Building

```dockerfile
ARG BUILD_ENV=production

# Different commands based on environment
RUN if [ "$BUILD_ENV" = "development" ]; then \
      npm install; \
    else \
      npm ci --only=production; \
    fi
```

### Skip Unnecessary Steps

```dockerfile
ARG SKIP_TESTS=false

RUN if [ "$SKIP_TESTS" = "false" ]; then \
      npm test; \
    fi
```

## .dockerignore Optimization

### Comprehensive .dockerignore

```dockerignore
# Reduce build context size
.git
.gitignore
node_modules
__pycache__
*.pyc
.venv
dist
build
coverage
.pytest_cache
*.log
.DS_Store
*.md
!README.md
.env*
docker-compose*.yml
Dockerfile*
.docker
.github
.gitlab-ci.yml
tests
__tests__
*.test.js
*.spec.js
docs
.idea
.vscode
```

### Check Context Size

```bash
# Check what's being sent
tar -cvf - . | wc -c

# With .dockerignore
docker build . 2>&1 | grep "Sending build context"
```

## Multi-Stage Optimization

### Minimal Copy

```dockerfile
# Only copy what's needed
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
# NOT: COPY --from=builder /app .
```

### Named Stages

```dockerfile
FROM node:20-alpine AS base
WORKDIR /app

FROM base AS deps
COPY package*.json ./
RUN npm ci

FROM base AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS runner
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/server.js"]
```

## Network Optimization

### Use BuildKit's Network Mode

```dockerfile
# syntax=docker/dockerfile:1

# Network access only when needed
RUN --network=default npm ci
```

### Parallel Downloads

```dockerfile
# Use concurrent downloads
RUN npm ci --prefer-offline --no-audit

# Go parallel downloads
RUN go mod download -x
```

## CI/CD Optimization

### GitHub Actions Cache

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### GitLab CI Cache

```yaml
build:
  script:
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:cache
        --build-arg BUILDKIT_INLINE_CACHE=1
        -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Local Registry Cache

```bash
# Run local registry
docker run -d -p 5000:5000 registry:2

# Use as cache
docker build \
  --cache-from localhost:5000/myapp:cache \
  -t myapp:latest .
```

## Build Metrics

### Measure Build Time

```bash
# Time the build
time docker build .

# With BuildKit progress
docker build --progress=plain .

# Detailed timing
DOCKER_BUILDKIT=1 docker build --progress=plain . 2>&1 | tee build.log
```

### Profile Builds

```bash
# BuildKit debug
BUILDKIT_PROGRESS=plain docker build .

# Show cache usage
docker build --progress=plain . 2>&1 | grep -E "(CACHED|RUN)"
```

## Common Pitfalls

### Invalidating Cache

```dockerfile
# BAD - cache invalidated by any file change
COPY . .
RUN npm ci

# GOOD - only invalidated by package.json changes
COPY package*.json ./
RUN npm ci
COPY . .
```

### Large Context

```dockerfile
# BAD - sends entire repo as context
# (if .dockerignore missing node_modules)
docker build .

# GOOD - use .dockerignore
# .dockerignore: node_modules, .git, etc.
```

### Unnecessary Layers

```dockerfile
# BAD - multiple layers
RUN apt-get update
RUN apt-get install curl
RUN apt-get clean

# GOOD - single layer
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

## Complete Optimized Build

```dockerfile
# syntax=docker/dockerfile:1

# ===== Dependencies Stage =====
FROM node:20-alpine AS deps
WORKDIR /app

# Copy only package files
COPY package*.json ./

# Install with cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline

# ===== Builder Stage =====
FROM node:20-alpine AS builder
WORKDIR /app

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy source
COPY . .

# Build with cache
RUN --mount=type=cache,target=/app/.next/cache \
    npm run build

# Prune dev dependencies
RUN npm prune --production

# ===== Runner Stage =====
FROM node:20-alpine AS runner
WORKDIR /app

# Create non-root user
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs nextjs

# Copy only production files
COPY --from=builder --chown=nextjs:nodejs /app/dist ./dist
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./

USER nextjs
EXPOSE 3000

CMD ["node", "dist/server.js"]
```

## Performance Checklist

### Build Setup

- [ ] Enable BuildKit
- [ ] Use BuildKit syntax directive
- [ ] Create comprehensive .dockerignore

### Caching

- [ ] Order Dockerfile by change frequency
- [ ] Use cache mounts for package managers
- [ ] Configure CI/CD cache
- [ ] Use registry cache for remote builds

### Parallelization

- [ ] Use multi-stage builds
- [ ] Enable parallel stage execution
- [ ] Use parallel download flags

### Optimization

- [ ] Minimize build context
- [ ] Combine RUN commands
- [ ] Copy only necessary files
- [ ] Use specific base image tags

### Monitoring

- [ ] Measure build times
- [ ] Monitor cache hit rates
- [ ] Profile slow builds

## Related Skills
- optimization/image-size
- dockerfile/caching-strategies
- dockerfile/multi-stage-builds
