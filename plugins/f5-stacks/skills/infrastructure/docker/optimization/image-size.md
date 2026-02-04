---
name: docker-image-size
description: Techniques for reducing Docker image size
applies_to: docker
---

# Docker Image Size Optimization

## Why Size Matters

- **Faster pulls/pushes** - Reduced transfer time
- **Faster deployments** - Quicker scaling
- **Lower storage costs** - Registry and runtime
- **Smaller attack surface** - Fewer packages = fewer vulnerabilities
- **Better caching** - More efficient layer reuse

## Size Analysis

### Check Image Size

```bash
# List images with sizes
docker images

# Detailed size breakdown
docker image inspect myimage --format '{{.Size}}'

# Human-readable
docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}"
```

### Analyze Layers

```bash
# Using docker history
docker history myimage

# Using dive (recommended)
dive myimage

# Install dive
brew install dive  # macOS
# or
docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  wagoodman/dive myimage
```

### Compare Images

```bash
# Before and after
docker images | grep myimage

# Output:
# myimage-old    latest    abc123    500MB
# myimage-new    latest    def456    150MB
```

## Base Image Selection

### Size Comparison

| Base Image | Size | Use Case |
|------------|------|----------|
| Ubuntu | ~77MB | Full compatibility |
| Debian slim | ~80MB | Good compatibility |
| Alpine | ~5MB | Minimal (musl libc) |
| Distroless | ~2MB | Ultra-minimal |
| scratch | 0MB | Static binaries |

### Node.js

```dockerfile
# Full (largest)
FROM node:20                    # ~1GB

# Slim
FROM node:20-slim               # ~200MB

# Alpine (smallest)
FROM node:20-alpine             # ~130MB

# Distroless (production only)
FROM gcr.io/distroless/nodejs20 # ~120MB
```

### Python

```dockerfile
# Full
FROM python:3.12                # ~1GB

# Slim
FROM python:3.12-slim           # ~150MB

# Alpine
FROM python:3.12-alpine         # ~50MB
```

### Go

```dockerfile
# Build stage
FROM golang:1.22-alpine         # ~250MB

# Runtime (scratch - no OS)
FROM scratch                    # 0MB (only binary)
```

## Multi-Stage Builds

### Basic Pattern

```dockerfile
# Build stage - full tools
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage - minimal
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/server.js"]
```

### Go - Scratch Image

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o /app/server

FROM scratch
COPY --from=builder /app/server /server
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
ENTRYPOINT ["/server"]
```

### Python - Slim Runtime

```dockerfile
FROM python:3.12 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY . .
CMD ["python", "app.py"]
```

## Layer Optimization

### Combine RUN Commands

```dockerfile
# Bad - multiple layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y git
RUN apt-get clean

# Good - single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Clean Up in Same Layer

```dockerfile
# Bad - cleanup in separate layer (doesn't reduce size)
RUN apt-get update && apt-get install -y build-essential
RUN apt-get clean

# Good - cleanup in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
```

### Order by Change Frequency

```dockerfile
# Least frequently changed first (better caching)
FROM node:20-alpine

# System dependencies (rarely change)
RUN apk add --no-cache curl

# Dependencies (change occasionally)
COPY package*.json ./
RUN npm ci --only=production

# Source code (changes frequently)
COPY . .

CMD ["node", "server.js"]
```

## Package Management

### APT (Debian/Ubuntu)

```dockerfile
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      package1 \
      package2 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
```

### APK (Alpine)

```dockerfile
RUN apk add --no-cache \
      package1 \
      package2

# With virtual packages for build deps
RUN apk add --no-cache --virtual .build-deps \
      build-base \
      python3-dev && \
    pip install some-package && \
    apk del .build-deps
```

### NPM

```dockerfile
# Production only
RUN npm ci --only=production

# Clean cache
RUN npm ci && npm cache clean --force

# Prune dev dependencies
RUN npm prune --production
```

### Pip

```dockerfile
# No cache
RUN pip install --no-cache-dir -r requirements.txt

# Compile to bytecode
RUN python -m compileall .
```

## Remove Unnecessary Files

### Common Cleanup

```dockerfile
RUN rm -rf \
    /var/lib/apt/lists/* \
    /var/cache/apk/* \
    /root/.cache \
    /tmp/* \
    /var/tmp/* \
    *.log \
    *.md \
    *.txt
```

### Node.js Cleanup

```dockerfile
# Remove unnecessary files
RUN npm ci --only=production && \
    npm cache clean --force && \
    rm -rf \
      /root/.npm \
      /tmp/* \
      node_modules/*/.git \
      node_modules/*/test \
      node_modules/*/tests \
      node_modules/*/*.md
```

### Python Cleanup

```dockerfile
# Remove bytecode and cache
RUN find /usr/local -type d -name __pycache__ -exec rm -rf {} + && \
    find /usr/local -type f -name '*.pyc' -delete && \
    rm -rf /root/.cache/pip
```

## .dockerignore

### Essential .dockerignore

```dockerignore
# Git
.git
.gitignore

# Dependencies (will be installed in container)
node_modules
__pycache__
*.pyc
.venv
vendor

# Build artifacts
dist
build
*.egg-info

# Development
.env
.env.local
*.log
.DS_Store
Thumbs.db

# IDE
.idea
.vscode
*.swp

# Tests
tests
test
__tests__
*.test.js
*.spec.js
coverage
.pytest_cache

# Documentation
docs
*.md
!README.md

# Docker
Dockerfile*
docker-compose*
.docker

# CI/CD
.github
.gitlab-ci.yml
.travis.yml
```

## Advanced Techniques

### Strip Binaries

```dockerfile
# Go - strip debug info
RUN go build -ldflags="-s -w" -o /app/server

# C/C++ - strip binary
RUN strip /app/binary
```

### UPX Compression

```dockerfile
FROM golang:1.22-alpine AS builder
RUN apk add --no-cache upx
WORKDIR /app
COPY . .
RUN go build -ldflags="-s -w" -o server && \
    upx --best server

FROM scratch
COPY --from=builder /app/server /server
ENTRYPOINT ["/server"]
```

### Squash Layers

```bash
# Experimental - squash all layers
docker build --squash -t myimage .
```

### Use Specific Tags

```dockerfile
# Avoid - pulls latest (might change)
FROM node

# Better - specific version
FROM node:20

# Best - specific digest (immutable)
FROM node:20-alpine@sha256:abc123...
```

## Size Optimization Checklist

### Base Image

- [ ] Use smallest suitable base (alpine/distroless/scratch)
- [ ] Use specific version tags
- [ ] Compare image sizes before selecting

### Multi-Stage Build

- [ ] Use multi-stage builds
- [ ] Only copy necessary artifacts
- [ ] Use appropriate runtime image

### Layer Optimization

- [ ] Combine RUN commands
- [ ] Clean up in same layer
- [ ] Order by change frequency

### Dependencies

- [ ] Install production deps only
- [ ] Remove package manager cache
- [ ] Remove build dependencies

### Files

- [ ] Use comprehensive .dockerignore
- [ ] Remove docs, tests, examples
- [ ] Remove unnecessary files

### Advanced

- [ ] Strip binaries
- [ ] Consider UPX for Go binaries
- [ ] Analyze with dive

## Complete Example

```dockerfile
# ===== Build Stage =====
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (cache optimization)
COPY package*.json ./
RUN npm ci

# Build application
COPY . .
RUN npm run build

# Prune dev dependencies
RUN npm prune --production && \
    npm cache clean --force

# ===== Production Stage =====
FROM node:20-alpine

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D appuser

WORKDIR /app

# Copy only production artifacts
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json ./

# Remove unnecessary files from node_modules
RUN find node_modules -type f -name '*.md' -delete && \
    find node_modules -type f -name '*.txt' -delete && \
    find node_modules -type d -name 'test' -exec rm -rf {} + 2>/dev/null || true && \
    find node_modules -type d -name 'tests' -exec rm -rf {} + 2>/dev/null || true && \
    find node_modules -type d -name '.git' -exec rm -rf {} + 2>/dev/null || true && \
    rm -rf /tmp/* /root/.npm

USER appuser

EXPOSE 3000

CMD ["node", "dist/server.js"]
```

## Related Skills
- optimization/build-performance
- dockerfile/multi-stage-builds
- dockerfile/layer-optimization
