---
name: dockerfile-best-practices
description: Dockerfile best practices for production
applies_to: docker
---

# Dockerfile Best Practices

## Security Best Practices

### 1. Use Non-Root User

```dockerfile
# Create and use non-root user
FROM node:20-alpine

# Create user and group
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 --ingroup nodejs appuser

WORKDIR /app

# Change ownership
COPY --chown=appuser:nodejs . .

# Switch to non-root (AFTER installing dependencies)
USER appuser

CMD ["node", "dist/main.js"]
```

### 2. Use Minimal Base Images

```dockerfile
# Prefer alpine or slim variants
FROM node:20-alpine      # ~180MB vs ~1GB for node:20
FROM python:3.12-slim    # ~250MB vs ~1GB for python:3.12
FROM golang:1.22-alpine  # Build only, use scratch/distroless for runtime

# For Go/Rust: Use distroless or scratch
FROM gcr.io/distroless/static-debian12  # ~2MB
FROM scratch  # 0MB (need static binary)
```

### 3. Pin Image Versions

```dockerfile
# BAD: Unpredictable, could break
FROM node:latest
FROM node:20

# GOOD: Specific version
FROM node:20.11.0-alpine3.19
FROM python:3.12.1-slim-bookworm
```

### 4. Don't Store Secrets

```dockerfile
# NEVER DO THIS
ENV API_KEY=sk-1234567890
ARG DATABASE_PASSWORD=secret
COPY .env /app/.env

# DO THIS: Pass at runtime
# docker run -e API_KEY=$API_KEY myapp
# Or use Docker secrets / external secret manager
```

### 5. Scan for Vulnerabilities

```bash
# Use Docker Scout
docker scout cve myapp:latest
docker scout quickview myapp:latest

# Use Trivy
trivy image myapp:latest

# In CI/CD
docker scan myapp:latest --exit-code 1
```

## Image Size Best Practices

### 1. Use Multi-Stage Builds

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage (minimal)
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/main.js"]
```

### 2. Clean Up in Same Layer

```dockerfile
# BAD: Cleanup in separate layer doesn't reduce size
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*

# GOOD: Cleanup in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean
```

### 3. Use .dockerignore

```dockerignore
# .dockerignore
.git
node_modules
dist
*.log
.env*
Dockerfile*
docker-compose*
README.md
.vscode
.idea
coverage
__tests__
```

### 4. Use Specific COPY

```dockerfile
# BAD: Copies everything
COPY . .

# GOOD: Copy only needed files
COPY package.json package-lock.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
```

## Build Performance Best Practices

### 1. Order Instructions for Caching

```dockerfile
# Least frequently changed first
FROM node:20-alpine
WORKDIR /app

# System deps (rarely change)
RUN apk add --no-cache dumb-init

# Package files (change with dependencies)
COPY package*.json ./
RUN npm ci

# Source code (changes frequently)
COPY . .
RUN npm run build
```

### 2. Use BuildKit Features

```dockerfile
# syntax=docker/dockerfile:1.4

# Cache mounts
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Secret mounts (build-time only)
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

### 3. Leverage Parallel Builds

```dockerfile
# These stages can build in parallel with BuildKit
FROM node:20 AS frontend
COPY frontend/ .
RUN npm run build

FROM golang:1.22 AS backend
COPY backend/ .
RUN go build

FROM nginx
COPY --from=frontend /dist /usr/share/nginx/html
COPY --from=backend /server /server
```

## Reliability Best Practices

### 1. Always Use Health Checks

```dockerfile
# HTTP health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# TCP health check (no curl needed)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD nc -z localhost 3000 || exit 1

# wget (available in alpine)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
```

### 2. Handle Signals Properly

```dockerfile
# Use exec form (not shell form)
# BAD: Shell form - signals not forwarded
CMD npm start

# GOOD: Exec form - app receives signals
CMD ["node", "dist/main.js"]

# Or use init process
RUN apk add --no-cache dumb-init
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/main.js"]
```

### 3. Use Proper Labels

```dockerfile
# OCI standard labels
LABEL org.opencontainers.image.title="My App"
LABEL org.opencontainers.image.description="My awesome application"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.vendor="My Company"
LABEL org.opencontainers.image.source="https://github.com/myorg/myapp"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.revision="${VCS_REF}"
```

## Dockerfile Template

```dockerfile
# =============================================================================
# Multi-Stage Dockerfile Template
# =============================================================================

# syntax=docker/dockerfile:1.4

# Build arguments
ARG NODE_VERSION=20
ARG ALPINE_VERSION=3.19

# =============================================================================
# Stage 1: Dependencies
# =============================================================================
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS deps

WORKDIR /app

# Install dependencies for native modules if needed
RUN apk add --no-cache libc6-compat

COPY package.json package-lock.json* ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# =============================================================================
# Stage 2: Builder
# =============================================================================
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

RUN npm run build && \
    npm prune --production

# =============================================================================
# Stage 3: Production
# =============================================================================
FROM node:${NODE_VERSION}-alpine${ALPINE_VERSION} AS production

# Labels
LABEL org.opencontainers.image.title="My App"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

# Install tini for proper signal handling
RUN apk add --no-cache tini

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 appuser

# Environment
ENV NODE_ENV=production
ENV PORT=3000

# Copy built application
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Use tini as init
ENTRYPOINT ["/sbin/tini", "--"]

# Start application
CMD ["node", "dist/main.js"]
```

## Checklist

### Security
- [ ] Non-root user created and used
- [ ] Specific base image version pinned
- [ ] No secrets in Dockerfile
- [ ] Minimal base image used
- [ ] Vulnerability scan passed

### Size
- [ ] Multi-stage build used
- [ ] .dockerignore configured
- [ ] Cleanup in same layer
- [ ] Production dependencies only
- [ ] Specific COPY (not COPY . .)

### Performance
- [ ] Instructions ordered for caching
- [ ] BuildKit features used
- [ ] Dependencies cached before source

### Reliability
- [ ] HEALTHCHECK defined
- [ ] Proper signal handling (exec form CMD)
- [ ] Labels added
- [ ] Appropriate start_period for health check

## Related Skills
- dockerfile/multi-stage-builds
- dockerfile/layer-optimization
- security/image-security
