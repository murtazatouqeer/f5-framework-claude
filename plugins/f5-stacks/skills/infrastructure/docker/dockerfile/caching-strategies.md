---
name: caching-strategies
description: Docker build caching strategies for faster builds
applies_to: docker
---

# Docker Build Caching Strategies

## How Docker Caching Works

Docker caches each layer during build. A layer is reused if:
1. The instruction hasn't changed
2. All parent layers are cached
3. For COPY/ADD: source files haven't changed

```
Layer 5: RUN npm run build     ← Cache invalidated
Layer 4: COPY . .              ← Cache invalidated (source changed)
Layer 3: RUN npm ci            ← Cache HIT
Layer 2: COPY package*.json ./ ← Cache HIT
Layer 1: FROM node:20-alpine   ← Cache HIT
```

## Cache Invalidation Rules

### Instruction Changes
```dockerfile
# Original
RUN npm install

# Modified (cache invalidated)
RUN npm ci
```

### Parent Layer Changes
```dockerfile
# If Layer 2 changes, Layer 3+ rebuild
Layer 1: FROM node:20
Layer 2: COPY package.json ./  # Changed → invalidates below
Layer 3: RUN npm install       # Must rebuild
Layer 4: COPY . .              # Must rebuild
```

### File Changes (COPY/ADD)
```dockerfile
# Cache invalidated if any copied file changes
COPY . .  # Any source change invalidates
```

## Optimal Caching Patterns

### Pattern 1: Dependencies First

```dockerfile
# Dependencies cached until package.json changes
COPY package.json package-lock.json ./
RUN npm ci

# Source code (frequently changes)
COPY . .
RUN npm run build
```

### Pattern 2: Separate Runtime Dependencies

```dockerfile
# Stage 1: All dependencies
FROM node:20-alpine AS deps
COPY package*.json ./
RUN npm ci

# Stage 2: Build
FROM node:20-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Production deps only
FROM node:20-alpine AS prod-deps
COPY package*.json ./
RUN npm ci --only=production

# Stage 4: Runtime
FROM node:20-alpine
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
```

### Pattern 3: System Dependencies Layer

```dockerfile
FROM python:3.12-slim

# System deps rarely change (cached)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python deps (cached until requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source (frequently changes)
COPY . .
```

## BuildKit Cache Mounts

Enable BuildKit for advanced caching:

```bash
export DOCKER_BUILDKIT=1
# Or in Docker Desktop, enable BuildKit in settings
```

### Package Manager Caches

```dockerfile
# syntax=docker/dockerfile:1.4

# npm cache
FROM node:20-alpine
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# pip cache
FROM python:3.12-slim
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# apt cache
FROM ubuntu:22.04
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y python3

# go mod cache
FROM golang:1.22
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

# cargo cache
FROM rust:1.75
RUN --mount=type=cache,target=/usr/local/cargo/registry \
    cargo build --release
```

### Build Artifact Caches

```dockerfile
# syntax=docker/dockerfile:1.4

# Cache Next.js build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN --mount=type=cache,target=/app/.next/cache \
    npm run build

# Cache Gradle build
FROM gradle:8-jdk21 AS builder
WORKDIR /app
COPY . .
RUN --mount=type=cache,target=/home/gradle/.gradle \
    gradle build --no-daemon
```

## CI/CD Caching

### GitHub Actions

```yaml
# .github/workflows/build.yml
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: myapp:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### GitLab CI

```yaml
# .gitlab-ci.yml
build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: 1
  script:
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:cache
        --build-arg BUILDKIT_INLINE_CACHE=1
        -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Registry Cache

```bash
# Build with inline cache
docker build \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  -t myregistry/myapp:latest \
  .

# Push (includes cache metadata)
docker push myregistry/myapp:latest

# Build using registry cache
docker build \
  --cache-from myregistry/myapp:latest \
  -t myregistry/myapp:new \
  .
```

## Cache Debugging

### Inspect Cache Usage

```bash
# Build with progress output
docker build --progress=plain -t myapp .

# Look for:
# CACHED [stage 2/5] COPY package*.json ./
# => [stage 3/5] RUN npm ci

# List build cache
docker buildx du

# Prune build cache
docker buildx prune
```

### Force Cache Invalidation

```bash
# Rebuild without cache
docker build --no-cache -t myapp .

# Invalidate from specific stage
docker build --no-cache-filter builder -t myapp .
```

### Cache Busting with ARG

```dockerfile
# Force rebuild of specific layer
ARG CACHE_BUST=1
RUN echo "Cache bust: $CACHE_BUST" && npm run build

# Use: docker build --build-arg CACHE_BUST=$(date +%s) .
```

## Common Caching Mistakes

### Mistake 1: COPY . . Before Dependencies

```dockerfile
# BAD: Any source change invalidates npm install
COPY . .
RUN npm ci

# GOOD: Dependencies cached
COPY package*.json ./
RUN npm ci
COPY . .
```

### Mistake 2: Changing ENV Unnecessarily

```dockerfile
# BAD: Timestamp changes every build
ENV BUILD_TIME=$(date)

# GOOD: Use ARG for build-time values
ARG BUILD_TIME
```

### Mistake 3: Not Using .dockerignore

```dockerfile
# Without .dockerignore, changes to README.md
# or tests invalidate the COPY layer
COPY . .
```

### Mistake 4: apt-get update Separate

```dockerfile
# BAD: update cached, may get stale packages
RUN apt-get update
RUN apt-get install -y curl  # Uses stale cache

# GOOD: update and install together
RUN apt-get update && apt-get install -y curl
```

## Caching Reference

| Package Manager | Cache Location |
|-----------------|----------------|
| npm | `/root/.npm` |
| yarn | `/root/.yarn/cache` |
| pnpm | `/root/.local/share/pnpm/store` |
| pip | `/root/.cache/pip` |
| go | `/go/pkg/mod` |
| cargo | `/usr/local/cargo/registry` |
| gradle | `/home/gradle/.gradle` |
| maven | `/root/.m2` |

## Related Skills
- dockerfile/layer-optimization
- dockerfile/multi-stage-builds
- optimization/build-performance
