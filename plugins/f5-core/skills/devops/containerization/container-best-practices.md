---
name: container-best-practices
description: Best practices for container development and deployment
category: devops/containerization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Container Best Practices

## Overview

Following container best practices ensures secure, efficient, and
maintainable containerized applications.

## Image Best Practices

### 1. Use Minimal Base Images

```dockerfile
# ❌ Bad - Full OS image (1GB+)
FROM ubuntu:22.04
RUN apt-get update && apt-get install -y nodejs npm

# ✅ Good - Minimal alpine image (~50MB)
FROM node:20-alpine

# ✅ Better - Distroless for production (~20MB)
FROM gcr.io/distroless/nodejs20-debian12
```

### 2. Use Specific Tags

```dockerfile
# ❌ Bad - Unpredictable
FROM node:latest
FROM node

# ✅ Good - Specific version
FROM node:20.10.0-alpine3.18

# ✅ Also good - Minor version pinning
FROM node:20-alpine
```

### 3. Minimize Layers

```dockerfile
# ❌ Bad - Multiple layers
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y git
RUN rm -rf /var/lib/apt/lists/*

# ✅ Good - Single layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        git && \
    rm -rf /var/lib/apt/lists/*
```

### 4. Order Instructions by Change Frequency

```dockerfile
# ✅ Correct order (least to most frequently changed)

# 1. Base image (rarely changes)
FROM node:20-alpine

# 2. System dependencies (rarely changes)
RUN apk add --no-cache tini

# 3. Create user (rarely changes)
RUN addgroup -S app && adduser -S app -G app

# 4. Working directory (rarely changes)
WORKDIR /app

# 5. Package files (changes when deps change)
COPY package*.json ./

# 6. Install dependencies (changes when deps change)
RUN npm ci --only=production

# 7. Application code (changes frequently)
COPY --chown=app:app . .

# 8. Build (changes frequently)
RUN npm run build

# 9. Runtime configuration (rarely changes)
USER app
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

## Security Best Practices

### 1. Run as Non-Root User

```dockerfile
# Create non-root user
FROM node:20-alpine

# Create app user and group
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Set ownership
WORKDIR /app
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

CMD ["node", "server.js"]
```

### 2. Don't Store Secrets in Images

```dockerfile
# ❌ Bad - Secret in image
ENV API_KEY=secret123
COPY .env /app/.env

# ✅ Good - Use runtime secrets
# Pass at runtime: docker run -e API_KEY=secret123 myapp
# Or use Docker secrets / Kubernetes secrets
```

### 3. Scan Images for Vulnerabilities

```bash
# Trivy scan
trivy image myapp:latest

# Snyk scan
snyk container test myapp:latest

# Docker Scout
docker scout cves myapp:latest

# Grype
grype myapp:latest
```

### 4. Use Read-Only Filesystem

```dockerfile
# Enable read-only root filesystem
# docker run --read-only myapp

# Handle writable paths
VOLUME ["/tmp", "/app/logs"]

# Or use tmpfs for temp files
# docker run --read-only --tmpfs /tmp myapp
```

### 5. Drop Capabilities

```yaml
# docker-compose.yml
services:
  api:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    security_opt:
      - no-new-privileges:true
```

## Performance Best Practices

### 1. Use .dockerignore

```plaintext
# .dockerignore
.git
.gitignore
node_modules
npm-debug.log
Dockerfile*
docker-compose*
.dockerignore
.env*
*.md
!README.md
coverage
.nyc_output
dist
*.log
.DS_Store
__tests__
tests
*.test.js
*.spec.js
.github
.vscode
```

### 2. Leverage Build Cache

```dockerfile
# Copy package files first for better caching
COPY package*.json ./
RUN npm ci

# Then copy source code
COPY . .
RUN npm run build
```

### 3. Use BuildKit Features

```dockerfile
# syntax=docker/dockerfile:1.4

# Cache mounts for package managers
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Secret mounts (not stored in image)
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci

# Bind mounts for build context
RUN --mount=type=bind,source=package.json,target=package.json \
    npm install
```

```bash
# Enable BuildKit
DOCKER_BUILDKIT=1 docker build .
```

### 4. Optimize Image Size

```dockerfile
# Multi-stage build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/main.js"]
```

## Health and Observability

### Health Checks

```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# TCP health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD nc -z localhost 3000 || exit 1

# Custom script
HEALTHCHECK --interval=30s --timeout=10s \
    CMD /app/healthcheck.sh
```

```typescript
// healthcheck.sh or health endpoint
app.get('/health', async (req, res) => {
  const checks = {
    uptime: process.uptime(),
    database: await checkDatabase(),
    cache: await checkCache(),
    memory: process.memoryUsage(),
  };

  const healthy = checks.database && checks.cache;
  res.status(healthy ? 200 : 503).json(checks);
});
```

### Logging

```dockerfile
# Log to stdout/stderr (Docker captures these)
CMD ["node", "server.js"]

# Don't log to files inside container
# ❌ Bad
# RUN npm start > /var/log/app.log

# ✅ Good - Use logging driver
# docker run --log-driver=json-file --log-opt max-size=10m myapp
```

```typescript
// Application logging to stdout
import pino from 'pino';

const logger = pino({
  transport: {
    target: 'pino-pretty',
    options: { destination: 1 }, // stdout
  },
});
```

## Graceful Shutdown

```dockerfile
# Use init system (tini)
FROM node:20-alpine
RUN apk add --no-cache tini
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "server.js"]
```

```typescript
// Handle shutdown signals
process.on('SIGTERM', async () => {
  console.log('SIGTERM received, shutting down gracefully');

  // Stop accepting new requests
  server.close(async () => {
    // Close database connections
    await prisma.$disconnect();

    // Close Redis connections
    await redis.quit();

    console.log('Graceful shutdown completed');
    process.exit(0);
  });

  // Force shutdown after timeout
  setTimeout(() => {
    console.error('Forced shutdown after timeout');
    process.exit(1);
  }, 30000);
});

process.on('SIGINT', () => {
  console.log('SIGINT received');
  process.exit(0);
});
```

## Resource Management

### Memory Limits

```yaml
# docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

```typescript
// Node.js memory configuration
// Set in Dockerfile or docker run
// --max-old-space-size=460 (80-90% of container limit)

// Monitor memory usage
setInterval(() => {
  const usage = process.memoryUsage();
  console.log({
    heapUsed: Math.round(usage.heapUsed / 1024 / 1024) + 'MB',
    heapTotal: Math.round(usage.heapTotal / 1024 / 1024) + 'MB',
    rss: Math.round(usage.rss / 1024 / 1024) + 'MB',
  });
}, 30000);
```

### CPU Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1.0'
        reservations:
          cpus: '0.5'
```

## Image Tagging Strategy

```bash
# Semantic versioning
myapp:1.0.0
myapp:1.0
myapp:1

# Git-based tagging
myapp:main-abc1234
myapp:feature-xyz-def5678

# Environment-based
myapp:staging
myapp:production

# Combined strategy
myapp:1.0.0-abc1234
myapp:latest  # Only for development
```

## Security Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│              Container Security Checklist                        │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use minimal base images (alpine/distroless)                   │
│ ☐ Run as non-root user                                          │
│ ☐ Don't store secrets in images                                 │
│ ☐ Scan images for vulnerabilities                               │
│ ☐ Use specific image tags                                       │
│ ☐ Sign and verify images                                        │
│ ☐ Use read-only filesystem when possible                        │
│ ☐ Drop all capabilities, add only needed                        │
│ ☐ Set resource limits                                           │
│ ☐ Use security contexts (seccomp, AppArmor)                     │
│ ☐ Keep base images updated                                      │
│ ☐ Use multi-stage builds                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Checklist

```
┌─────────────────────────────────────────────────────────────────┐
│              Container Performance Checklist                     │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use .dockerignore to exclude unnecessary files                │
│ ☐ Order Dockerfile instructions by change frequency             │
│ ☐ Minimize number of layers                                     │
│ ☐ Use multi-stage builds                                        │
│ ☐ Enable BuildKit for faster builds                             │
│ ☐ Use cache mounts for package managers                         │
│ ☐ Implement health checks                                       │
│ ☐ Handle graceful shutdown                                      │
│ ☐ Set appropriate resource limits                               │
│ ☐ Monitor container metrics                                     │
│ ☐ Use init system (tini) for signal handling                    │
│ ☐ Log to stdout/stderr                                          │
└─────────────────────────────────────────────────────────────────┘
```
