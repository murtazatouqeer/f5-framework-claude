---
name: container-security
description: Docker and container security best practices
category: security/infrastructure
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Container Security

## Overview

Container security involves securing container images, runtime,
orchestration, and the host system.

## Secure Dockerfile

```dockerfile
# Use specific version, not latest
FROM node:20.10-alpine3.18

# Create non-root user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Set working directory
WORKDIR /app

# Copy package files first (layer caching)
COPY --chown=appuser:appgroup package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY --chown=appuser:appgroup . .

# Build if needed
RUN npm run build

# Remove dev dependencies and build tools
RUN rm -rf node_modules && \
    npm ci --only=production && \
    npm cache clean --force

# Set environment
ENV NODE_ENV=production

# Switch to non-root user
USER appuser

# Expose port (non-privileged)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Use exec form for proper signal handling
CMD ["node", "dist/main.js"]
```

## Multi-Stage Build

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Remove dev dependencies
RUN npm prune --production

# Production stage
FROM node:20-alpine AS production

# Security: Don't run as root
RUN addgroup -g 1001 -S nodejs && \
    adduser -u 1001 -S nodejs -G nodejs

WORKDIR /app

# Copy only necessary files
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

USER nodejs

EXPOSE 3000

CMD ["node", "dist/main.js"]
```

## Distroless Images

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production with distroless
FROM gcr.io/distroless/nodejs20-debian12

WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

# Distroless runs as non-root by default
CMD ["dist/main.js"]
```

## Docker Compose Security

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    # Read-only filesystem
    read_only: true
    # Temporary filesystems for writable directories
    tmpfs:
      - /tmp
      - /var/run
    # Security options
    security_opt:
      - no-new-privileges:true
    # Drop all capabilities, add only needed
    cap_drop:
      - ALL
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    # Non-root user
    user: "1001:1001"
    # Health check
    healthcheck:
      test: ["CMD", "wget", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    # Network isolation
    networks:
      - frontend
      - backend
    # Secrets management
    secrets:
      - db_password
      - jwt_secret
    environment:
      - NODE_ENV=production
      - DB_PASSWORD_FILE=/run/secrets/db_password

  db:
    image: postgres:15-alpine
    read_only: true
    tmpfs:
      - /tmp
      - /var/run/postgresql
    volumes:
      - db_data:/var/lib/postgresql/data
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
    networks:
      - backend
    secrets:
      - db_password
    environment:
      - POSTGRES_PASSWORD_FILE=/run/secrets/db_password

networks:
  frontend:
  backend:
    internal: true  # No external access

volumes:
  db_data:

secrets:
  db_password:
    external: true
  jwt_secret:
    external: true
```

## Image Scanning

```bash
# Trivy - vulnerability scanner
trivy image myapp:latest

# Scan before pushing
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:latest

# Docker Scout
docker scout cves myapp:latest

# Snyk
snyk container test myapp:latest
```

```yaml
# GitHub Actions - scan on build
name: Build and Scan

on: push

jobs:
  build-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .

      - name: Scan image
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: myapp:${{ github.sha }}
          format: 'table'
          exit-code: '1'
          ignore-unfixed: true
          vuln-type: 'os,library'
          severity: 'CRITICAL,HIGH'
```

## Runtime Security

```yaml
# Kubernetes Pod Security
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
    seccompProfile:
      type: RuntimeDefault

  containers:
    - name: app
      image: myapp:latest
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
      resources:
        limits:
          cpu: "1"
          memory: "512Mi"
        requests:
          cpu: "250m"
          memory: "256Mi"
      volumeMounts:
        - name: tmp
          mountPath: /tmp
        - name: cache
          mountPath: /app/.cache

  volumes:
    - name: tmp
      emptyDir: {}
    - name: cache
      emptyDir: {}
```

## Network Policies

```yaml
# Kubernetes Network Policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: app-network-policy
spec:
  podSelector:
    matchLabels:
      app: myapp
  policyTypes:
    - Ingress
    - Egress
  ingress:
    # Allow from ingress controller
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - port: 3000
  egress:
    # Allow to database
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - port: 5432
    # Allow DNS
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
```

## Secrets in Containers

```typescript
// Read secrets from files (Docker secrets)
import fs from 'fs';

function readSecret(name: string): string {
  const secretPath = `/run/secrets/${name}`;

  try {
    return fs.readFileSync(secretPath, 'utf8').trim();
  } catch (error) {
    // Fallback to environment variable
    return process.env[name.toUpperCase()] || '';
  }
}

const dbPassword = readSecret('db_password');
const jwtSecret = readSecret('jwt_secret');
```

## Container Hardening Checklist

```bash
#!/bin/bash
# container-audit.sh

IMAGE=$1

echo "Auditing container image: $IMAGE"

# Check for root user
echo "Checking for non-root user..."
docker run --rm $IMAGE whoami | grep -v root || echo "WARNING: Running as root"

# Check for vulnerabilities
echo "Scanning for vulnerabilities..."
trivy image --severity HIGH,CRITICAL $IMAGE

# Check for secrets in image
echo "Checking for embedded secrets..."
docker history --no-trunc $IMAGE | grep -iE "(password|secret|key|token)" && echo "WARNING: Possible secrets in image history"

# Check exposed ports
echo "Checking exposed ports..."
docker inspect $IMAGE | jq '.[0].Config.ExposedPorts'

# Check environment variables
echo "Checking environment variables..."
docker inspect $IMAGE | jq '.[0].Config.Env'

echo "Audit complete"
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Non-root user | Never run as root |
| Minimal base | Use alpine or distroless |
| Multi-stage builds | Reduce image size and attack surface |
| Pin versions | Use specific image tags |
| Scan images | Regular vulnerability scanning |
| Read-only filesystem | Use tmpfs for writable needs |
