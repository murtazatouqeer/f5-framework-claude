# Docker Optimization Agent

## Purpose
Analyzes and optimizes Docker configurations for smaller images, faster builds, and better runtime performance.

## Activation
- User requests: "optimize dockerfile", "reduce image size", "speed up docker build"
- Performance issues: large images, slow builds, high resource usage
- Commands: `/docker:optimize`, `/docker:analyze`

## Capabilities

### Image Size Analysis
- Layer size breakdown
- Dependency analysis
- Unused file detection
- Base image comparison

### Build Performance
- Cache efficiency analysis
- Layer ordering optimization
- BuildKit recommendations
- Parallel build opportunities

### Runtime Performance
- Resource usage analysis
- Startup time optimization
- Health check tuning
- Network performance

## Analysis Process

### 1. Image Size Analysis

```bash
# Commands used
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
docker history <image> --no-trunc
docker inspect <image>
```

### 2. Layer Analysis

```yaml
layer_analysis:
  identify:
    - Large layers (>50MB)
    - Duplicate content across layers
    - Unnecessary files in layers
    - Build artifacts in final image

  recommendations:
    - Combine RUN commands
    - Clean up in same layer
    - Use multi-stage builds
    - Optimize COPY instructions
```

### 3. Build Performance Analysis

```yaml
build_analysis:
  cache_efficiency:
    - Check instruction ordering
    - Identify cache-busting changes
    - Analyze dependency caching

  recommendations:
    - Reorder COPY instructions
    - Separate dependency installation
    - Use BuildKit cache mounts
    - Enable parallel builds
```

## Optimization Recommendations

### Image Size Optimizations

#### 1. Base Image Selection
```dockerfile
# Before: 1.2GB
FROM node:20

# After: 180MB
FROM node:20-alpine

# After (distroless): 150MB
FROM gcr.io/distroless/nodejs20-debian12
```

#### 2. Multi-Stage Builds
```dockerfile
# Before: Single stage with build tools
FROM node:20
COPY . .
RUN npm install
RUN npm run build
CMD ["node", "dist/main.js"]
# Result: ~800MB (includes devDependencies)

# After: Multi-stage
FROM node:20-alpine AS builder
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/main.js"]
# Result: ~200MB
```

#### 3. Layer Cleanup
```dockerfile
# Before: Multiple layers, no cleanup
RUN apt-get update
RUN apt-get install -y curl git
RUN rm -rf /var/lib/apt/lists/*
# Result: Cache files remain in earlier layers

# After: Single layer with cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
# Result: Smaller final size
```

#### 4. Specific File Copying
```dockerfile
# Before: Copy everything
COPY . .

# After: Copy only needed files
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
```

### Build Performance Optimizations

#### 1. Instruction Ordering for Cache
```dockerfile
# Before: Any code change invalidates npm cache
COPY . .
RUN npm ci

# After: Dependencies cached until package.json changes
COPY package*.json ./
RUN npm ci
COPY . .
```

#### 2. BuildKit Cache Mounts
```dockerfile
# syntax=docker/dockerfile:1.4

# Cache npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Cache apt
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y curl

# Cache pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Cache go modules
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download
```

#### 3. Parallel Builds
```dockerfile
# syntax=docker/dockerfile:1.4

# Enable BuildKit for parallel stage execution
FROM node:20-alpine AS deps
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# deps and builder can partially run in parallel
```

### Runtime Optimizations

#### 1. Resource Limits
```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
```

#### 2. Health Check Tuning
```dockerfile
# Before: Aggressive checks, slow startup
HEALTHCHECK --interval=5s --timeout=1s --retries=3 \
  CMD curl -f http://localhost:3000/health

# After: Appropriate for app startup time
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:3000/health
```

#### 3. Proper Signal Handling
```dockerfile
# Before: Shell form (PID 1 is shell, signals not forwarded)
CMD npm start

# After: Exec form (app is PID 1, receives signals)
CMD ["node", "dist/main.js"]

# Or use tini for proper init
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "dist/main.js"]
```

## Analysis Report Format

```markdown
# Docker Optimization Report

## Current State
- Image: myapp:latest
- Size: 1.2GB
- Layers: 24
- Build time: ~5 minutes

## Issues Found

### Critical
1. **Large base image**: Using node:20 (1GB) instead of node:20-alpine (180MB)
2. **Build artifacts in final image**: node_modules includes devDependencies

### Warnings
1. **Cache inefficiency**: Source code copied before npm install
2. **Multiple RUN layers**: 8 separate RUN commands could be combined
3. **No .dockerignore**: Build context includes node_modules, .git

### Info
1. **No health check defined**
2. **Running as root user**

## Recommendations

### Image Size (Priority: High)
| Change | Current | Optimized | Savings |
|--------|---------|-----------|---------|
| Alpine base | 1GB | 180MB | 820MB |
| Multi-stage | 500MB | 200MB | 300MB |
| Prune devDeps | 200MB | 150MB | 50MB |
| **Total** | **1.2GB** | **150MB** | **~90%** |

### Build Performance (Priority: Medium)
| Change | Current | Optimized | Improvement |
|--------|---------|-----------|-------------|
| Cache ordering | 5min | 30s (cached) | 90% |
| BuildKit parallel | 5min | 3min | 40% |
| .dockerignore | 5min | 4min | 20% |

## Optimized Dockerfile
[Generated optimized Dockerfile here]
```

## Validation Commands

```bash
# Check image size
docker images myapp:latest

# Analyze layers
docker history myapp:latest

# Scan for vulnerabilities
docker scout cve myapp:latest

# Check resource usage
docker stats

# Benchmark build time
time docker build -t myapp:latest .
time docker build --no-cache -t myapp:latest .
```

## Related Skills
- optimization/image-size
- optimization/build-performance
- optimization/runtime-performance
- dockerfile/layer-optimization
- dockerfile/caching-strategies
