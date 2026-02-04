---
name: docker-image-security
description: Docker image security best practices and hardening
applies_to: docker
---

# Docker Image Security

## Security Principles

1. **Minimal base images** - Reduce attack surface
2. **Non-root users** - Limit privilege escalation
3. **No secrets in images** - Keep credentials separate
4. **Verified sources** - Use trusted base images
5. **Regular updates** - Patch vulnerabilities

## Base Image Selection

### Image Comparison

| Base Image | Size | Attack Surface | Security |
|------------|------|----------------|----------|
| Alpine | ~5MB | Minimal | High |
| Distroless | ~2MB | Ultra-minimal | Highest |
| Slim | ~80MB | Reduced | Medium |
| Full | ~900MB | Large | Low |

### Recommended Base Images

```dockerfile
# Node.js
FROM node:20-alpine           # Best balance
FROM gcr.io/distroless/nodejs20-debian12  # Maximum security

# Python
FROM python:3.12-alpine       # Minimal
FROM python:3.12-slim         # More compatible
FROM gcr.io/distroless/python3  # Maximum security

# Go
FROM golang:1.22-alpine       # Build
FROM gcr.io/distroless/static  # Runtime (scratch alternative)

# Java
FROM eclipse-temurin:21-jre-alpine  # Minimal
FROM gcr.io/distroless/java21  # Maximum security
```

### Verify Image Source

```dockerfile
# Use official images
FROM node:20-alpine

# Pin to specific digest (immutable)
FROM node:20-alpine@sha256:abc123...

# Use verified publisher images
FROM bitnami/postgresql:16
```

## Non-Root User

### Create User in Dockerfile

```dockerfile
FROM node:20-alpine

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D appuser

# Set ownership
WORKDIR /app
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

CMD ["node", "server.js"]
```

### Python Example

```dockerfile
FROM python:3.12-slim

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /home/appuser/app
COPY --chown=appuser:appuser . .

USER appuser

CMD ["python", "app.py"]
```

### Multi-Stage with User

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D appuser
WORKDIR /app
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
USER appuser
CMD ["node", "dist/server.js"]
```

## Minimal Images

### Remove Unnecessary Components

```dockerfile
FROM node:20-alpine

# Remove package manager after use
RUN npm ci --only=production && \
    npm cache clean --force && \
    rm -rf /var/cache/apk/*

# Don't install dev dependencies
RUN npm ci --omit=dev
```

### Multi-Stage Build

```dockerfile
# Build stage with full tools
FROM node:20 AS builder
WORKDIR /app
COPY . .
RUN npm ci && npm run build

# Minimal production stage
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/server.js"]
```

### Distroless Images

```dockerfile
# Build stage
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /app/server

# Distroless runtime
FROM gcr.io/distroless/static-debian12
COPY --from=builder /app/server /server
USER nonroot:nonroot
CMD ["/server"]
```

## No Secrets in Images

### Bad Practices (Never Do)

```dockerfile
# NEVER - Secret in ENV
ENV API_KEY=secret123

# NEVER - Secret in COPY
COPY .env /app/.env

# NEVER - Secret in RUN
RUN echo "password" > /app/secrets.txt
```

### Good Practices

```dockerfile
# Reference at runtime
ENV API_KEY=""

# Use build args for non-sensitive config
ARG BUILD_ENV=production

# Mount secrets at runtime
# docker run -v /secrets:/app/secrets:ro myapp
```

### BuildKit Secrets

```dockerfile
# syntax=docker/dockerfile:1

FROM node:20-alpine

# Secret never stored in layer
RUN --mount=type=secret,id=npmrc,dst=/app/.npmrc \
    npm ci
```

```bash
# Build with secret
docker build --secret id=npmrc,src=.npmrc .
```

## Image Signing

### Docker Content Trust

```bash
# Enable content trust
export DOCKER_CONTENT_TRUST=1

# Sign on push
docker push myregistry/myimage:latest

# Verify on pull
docker pull myregistry/myimage:latest
```

### Cosign (Sigstore)

```bash
# Sign image
cosign sign myregistry/myimage:latest

# Verify signature
cosign verify myregistry/myimage:latest

# Sign with key
cosign sign --key cosign.key myregistry/myimage:latest
```

## Read-Only Filesystem

### Dockerfile

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY . .
# Ensure app can run with read-only root
CMD ["node", "server.js"]
```

### Runtime

```bash
# Run with read-only root filesystem
docker run --read-only myimage

# Add tmpfs for writable areas
docker run --read-only --tmpfs /tmp --tmpfs /app/cache myimage
```

### Docker Compose

```yaml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
      - /app/cache
```

## Security Labels

```dockerfile
# Add security-related labels
LABEL org.opencontainers.image.source="https://github.com/org/repo"
LABEL org.opencontainers.image.vendor="MyCompany"
LABEL org.opencontainers.image.licenses="MIT"
LABEL security.scan.date="2024-01-15"
LABEL security.compliance="SOC2"
```

## Health Checks

```dockerfile
# Add health check for monitoring
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1
```

## Complete Secure Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependency files first (cache optimization)
COPY package*.json ./

# Install dependencies with audit
RUN npm ci --audit && \
    npm audit fix || true

COPY . .

# Build application
RUN npm run build

# Production stage
FROM node:20-alpine

# Security labels
LABEL maintainer="security@company.com"
LABEL org.opencontainers.image.source="https://github.com/company/app"

# Create non-root user
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D -s /sbin/nologin appuser

# Set secure working directory
WORKDIR /app

# Copy only necessary files with proper ownership
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/package.json ./

# Remove unnecessary tools
RUN apk --no-cache add dumb-init && \
    rm -rf /var/cache/apk/* /tmp/* /root/.npm

# Set secure environment
ENV NODE_ENV=production
ENV NODE_OPTIONS="--max-old-space-size=512"

# Switch to non-root user
USER appuser

# Expose application port (documentation)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/server.js"]
```

## Security Checklist

### Image Build

- [ ] Use official/verified base images
- [ ] Pin image versions with SHA256 digest
- [ ] Use minimal base (alpine/distroless)
- [ ] Create and use non-root user
- [ ] Remove unnecessary packages
- [ ] Don't store secrets in image
- [ ] Use multi-stage builds
- [ ] Add health checks
- [ ] Add security labels

### Image Content

- [ ] No hardcoded credentials
- [ ] No development tools in production
- [ ] No unnecessary SUID/SGID binaries
- [ ] Minimal file permissions
- [ ] No sensitive data in layers

### Build Process

- [ ] Enable BuildKit
- [ ] Use secret mounts for sensitive build data
- [ ] Scan images for vulnerabilities
- [ ] Sign images
- [ ] Use .dockerignore

## Related Skills
- security/runtime-security
- security/secrets-management
- security/vulnerability-scanning
- dockerfile/best-practices
