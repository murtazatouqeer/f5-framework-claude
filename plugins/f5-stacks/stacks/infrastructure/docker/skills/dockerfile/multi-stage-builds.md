---
name: multi-stage-builds
description: Multi-stage Docker builds for optimized images
applies_to: docker
---

# Multi-Stage Docker Builds

## Overview

Multi-stage builds separate build-time dependencies from runtime, resulting in smaller, more secure production images.

## Benefits

1. **Smaller Images**: No build tools in final image
2. **Better Security**: Reduced attack surface
3. **Cleaner Builds**: Build and runtime concerns separated
4. **Cache Efficiency**: Build stages cached independently

## Basic Pattern

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/main.js"]
```

## Language-Specific Examples

### Node.js (TypeScript)

```dockerfile
# =============================================================================
# Stage 1: Dependencies
# =============================================================================
FROM node:20-alpine AS deps
WORKDIR /app

# Install dependencies for native modules (if needed)
RUN apk add --no-cache libc6-compat

COPY package.json package-lock.json* ./
RUN npm ci && npm cache clean --force

# =============================================================================
# Stage 2: Builder
# =============================================================================
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build TypeScript
RUN npm run build

# Remove dev dependencies
RUN npm prune --production

# =============================================================================
# Stage 3: Production
# =============================================================================
FROM node:20-alpine AS production
WORKDIR /app

ENV NODE_ENV=production

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 appuser

# Copy built application
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/main.js"]
```

### Python (FastAPI/Django)

```dockerfile
# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.12-slim AS builder
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.12-slim AS production
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid appgroup --shell /bin/bash appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup . .

USER appuser
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "app.main:app"]
```

### Go (Minimal Binary)

```dockerfile
# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM golang:1.22-alpine AS builder
WORKDIR /app

# Install CA certificates for HTTPS
RUN apk --no-cache add ca-certificates tzdata

# Download dependencies
COPY go.mod go.sum ./
RUN go mod download && go mod verify

# Copy source code
COPY . .

# Build static binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -ldflags='-w -s -extldflags "-static"' \
    -o /app/server ./cmd/server

# =============================================================================
# Stage 2: Production (Scratch - ~10MB total)
# =============================================================================
FROM scratch AS production

# Copy certificates and timezone data
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy binary
COPY --from=builder /app/server /server

EXPOSE 8080

ENTRYPOINT ["/server"]
```

### Go (Distroless - More Practical)

```dockerfile
# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM golang:1.22-alpine AS builder
WORKDIR /app

RUN apk --no-cache add ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags='-w -s' \
    -o /app/server ./cmd/server

# =============================================================================
# Stage 2: Production (Distroless - ~20MB, includes shell debugging)
# =============================================================================
FROM gcr.io/distroless/static-debian12 AS production
WORKDIR /app

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/server /app/server

USER nonroot:nonroot
EXPOSE 8080

ENTRYPOINT ["/app/server"]
```

### Java (Spring Boot with Layered JARs)

```dockerfile
# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app

# Copy Maven wrapper and pom
COPY mvnw pom.xml ./
COPY .mvn .mvn

# Download dependencies (cached layer)
RUN ./mvnw dependency:go-offline -B

# Copy source and build
COPY src src
RUN ./mvnw package -DskipTests -B

# Extract layers for better caching
RUN java -Djarmode=layertools -jar target/*.jar extract --destination extracted

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM eclipse-temurin:21-jre-alpine AS production
WORKDIR /app

# Create non-root user
RUN addgroup --system --gid 1001 javauser && \
    adduser --system --uid 1001 javauser

# Copy extracted layers (in order of change frequency)
COPY --from=builder --chown=javauser:javauser /app/extracted/dependencies/ ./
COPY --from=builder --chown=javauser:javauser /app/extracted/spring-boot-loader/ ./
COPY --from=builder --chown=javauser:javauser /app/extracted/snapshot-dependencies/ ./
COPY --from=builder --chown=javauser:javauser /app/extracted/application/ ./

USER javauser
EXPOSE 8080

# JVM options for containers
ENV JAVA_OPTS="-XX:+UseContainerSupport -XX:MaxRAMPercentage=75.0 -XX:+UseG1GC"

HEALTHCHECK --interval=30s --timeout=3s --start-period=30s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS org.springframework.boot.loader.launch.JarLauncher"]
```

### Rust (Minimal Binary)

```dockerfile
# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM rust:1.75-alpine AS builder
WORKDIR /app

# Install musl for static linking
RUN apk add --no-cache musl-dev

# Create new project and copy dependencies first (for caching)
COPY Cargo.toml Cargo.lock ./
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release --target x86_64-unknown-linux-musl
RUN rm -rf src

# Copy actual source and build
COPY src ./src
RUN touch src/main.rs && \
    cargo build --release --target x86_64-unknown-linux-musl

# =============================================================================
# Stage 2: Production (Distroless)
# =============================================================================
FROM gcr.io/distroless/static-debian12 AS production

COPY --from=builder /app/target/x86_64-unknown-linux-musl/release/app /app

USER nonroot:nonroot
EXPOSE 8080

ENTRYPOINT ["/app"]
```

## Advanced Patterns

### Copying from External Images

```dockerfile
# Copy from official image
COPY --from=nginx:alpine /etc/nginx/nginx.conf /etc/nginx/

# Copy binaries from tool images
COPY --from=docker:cli /usr/local/bin/docker /usr/local/bin/
```

### Parallel Builds (BuildKit)

```dockerfile
# syntax=docker/dockerfile:1.4

# These stages build in parallel
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM golang:1.22-alpine AS backend-builder
WORKDIR /app/backend
COPY backend/go.* ./
RUN go mod download
COPY backend/ ./
RUN go build -o /server

# Final stage combines both
FROM alpine:3.19 AS production
COPY --from=frontend-builder /app/frontend/dist /var/www/static
COPY --from=backend-builder /server /server
CMD ["/server"]
```

### Development Stage

```dockerfile
FROM node:20-alpine AS deps
COPY package*.json ./
RUN npm ci

# Development with hot reload
FROM node:20-alpine AS development
WORKDIR /app
COPY --from=deps /node_modules ./node_modules
COPY . .
CMD ["npm", "run", "dev"]

# Production
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=deps /node_modules ./node_modules
COPY . .
RUN npm run build
CMD ["node", "dist/main.js"]
```

## Building Specific Stages

```bash
# Build only the builder stage
docker build --target builder -t myapp:builder .

# Build development image
docker build --target development -t myapp:dev .

# Build production (default last stage)
docker build -t myapp:prod .
```

## Image Size Comparison

| Approach | Node.js | Python | Go | Java |
|----------|---------|--------|-----|------|
| Single stage | ~1GB | ~1.2GB | ~800MB | ~700MB |
| Multi-stage | ~200MB | ~300MB | ~20MB | ~300MB |
| Distroless | ~150MB | ~250MB | ~10MB | ~250MB |

## Related Skills
- dockerfile/layer-optimization
- dockerfile/caching-strategies
- optimization/image-size
