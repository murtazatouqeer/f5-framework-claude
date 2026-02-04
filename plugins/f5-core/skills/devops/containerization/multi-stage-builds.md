---
name: multi-stage-builds
description: Multi-stage Docker builds for optimized images
category: devops/containerization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Multi-Stage Builds

## Overview

Multi-stage builds allow you to create optimized production images by using
multiple FROM statements in a single Dockerfile, copying only necessary
artifacts between stages.

## Multi-Stage Build Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   Multi-Stage Build Flow                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Stage 1: Builder                  Stage 2: Runner               │
│  ┌─────────────────────┐          ┌─────────────────────┐       │
│  │ Full Node.js        │          │ Minimal Node.js     │       │
│  │ Dev Dependencies    │    →     │ Production deps     │       │
│  │ Build Tools         │  copy    │ Compiled output     │       │
│  │ Source Code         │  only    │                     │       │
│  │ Tests               │  needed  │ Size: ~100MB        │       │
│  │                     │          │                     │       │
│  │ Size: ~1GB          │          │                     │       │
│  └─────────────────────┘          └─────────────────────┘       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Multi-Stage Build

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Production
FROM node:20-alpine AS runner

WORKDIR /app

# Copy only production dependencies
COPY package*.json ./
RUN npm ci --only=production && npm cache clean --force

# Copy built artifacts from builder
COPY --from=builder /app/dist ./dist

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

EXPOSE 3000
CMD ["node", "dist/main.js"]
```

## Node.js TypeScript Application

```dockerfile
# syntax=docker/dockerfile:1.4

# =============================================================================
# Stage 1: Dependencies
# =============================================================================
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY prisma ./prisma/

# Install all dependencies
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Generate Prisma client
RUN npx prisma generate

# =============================================================================
# Stage 2: Builder
# =============================================================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/package*.json ./

# Copy source code
COPY . .

# Build application
RUN npm run build

# Prune dev dependencies
RUN npm prune --production

# =============================================================================
# Stage 3: Runner (Production)
# =============================================================================
FROM node:20-alpine AS runner

# Install security updates
RUN apk update && apk upgrade && rm -rf /var/cache/apk/*

# Add tini for proper signal handling
RUN apk add --no-cache tini

# Create non-root user
RUN addgroup -S nodejs && adduser -S nodejs -G nodejs

WORKDIR /app

# Copy production dependencies
COPY --from=builder --chown=nodejs:nodejs /app/node_modules ./node_modules

# Copy built application
COPY --from=builder --chown=nodejs:nodejs /app/dist ./dist
COPY --from=builder --chown=nodejs:nodejs /app/package.json ./

# Copy Prisma schema and generated client
COPY --from=builder --chown=nodejs:nodejs /app/prisma ./prisma

# Set environment
ENV NODE_ENV=production
ENV PORT=3000

# Switch to non-root user
USER nodejs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Use tini as entrypoint
ENTRYPOINT ["/sbin/tini", "--"]

# Start application
CMD ["node", "dist/main.js"]
```

## Next.js Application

```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app

COPY package*.json ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build Next.js
RUN npm run build

# Stage 3: Runner
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup -S nodejs && adduser -S nextjs -G nodejs

# Copy public assets
COPY --from=builder /app/public ./public

# Copy Next.js build output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

## Go Application

```dockerfile
# Stage 1: Build
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-w -s" -o main .

# Stage 2: Run
FROM scratch

# Copy CA certificates for HTTPS
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy binary
COPY --from=builder /app/main /main

EXPOSE 8080

ENTRYPOINT ["/main"]
```

## Python Application

```dockerfile
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runner
FROM python:3.12-slim AS runner

WORKDIR /app

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Targeting Specific Stages

```dockerfile
# Multi-target Dockerfile
FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./

# Development stage
FROM base AS development
RUN npm install
COPY . .
CMD ["npm", "run", "dev"]

# Test stage
FROM base AS test
RUN npm ci
COPY . .
CMD ["npm", "test"]

# Production build
FROM base AS builder
RUN npm ci
COPY . .
RUN npm run build

# Production runner
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/main.js"]
```

```bash
# Build specific stage
docker build --target development -t myapp:dev .
docker build --target test -t myapp:test .
docker build --target production -t myapp:prod .

# Run tests in CI
docker build --target test -t myapp:test .
docker run --rm myapp:test
```

## Cache Optimization

```dockerfile
# syntax=docker/dockerfile:1.4

FROM node:20-alpine AS deps

WORKDIR /app

# Use cache mount for npm
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci

FROM node:20-alpine AS builder

WORKDIR /app

# Copy cached dependencies
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Use cache for build artifacts
RUN --mount=type=cache,target=/app/.next/cache \
    npm run build
```

## Build Arguments

```dockerfile
FROM node:20-alpine AS builder

# Build arguments
ARG NODE_ENV=production
ARG API_URL
ARG BUILD_VERSION

# Use in environment
ENV NODE_ENV=$NODE_ENV
ENV NEXT_PUBLIC_API_URL=$API_URL

# Build with version info
RUN npm run build

# Label with build info
LABEL version=$BUILD_VERSION
LABEL build_date=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
```

```bash
# Pass build arguments
docker build \
  --build-arg NODE_ENV=production \
  --build-arg API_URL=https://api.example.com \
  --build-arg BUILD_VERSION=1.0.0 \
  -t myapp:1.0.0 .
```

## Copying from External Images

```dockerfile
FROM node:20-alpine AS runner

# Copy from external image
COPY --from=nginx:alpine /etc/nginx/nginx.conf /nginx.conf
COPY --from=busybox:latest /bin/wget /usr/bin/wget

# Copy binaries from other images
COPY --from=docker:latest /usr/local/bin/docker /usr/local/bin/docker
```

## Security-Focused Multi-Stage

```dockerfile
# Stage 1: Build
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Security scan
FROM aquasec/trivy:latest AS security
COPY --from=builder /app /app
RUN trivy filesystem --exit-code 1 --severity HIGH,CRITICAL /app

# Stage 3: Production (only if security passes)
FROM gcr.io/distroless/nodejs20-debian12 AS runner
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["dist/main.js"]
```

## Image Size Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                   Image Size Comparison                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Approach                           │ Size                       │
│  ───────────────────────────────────┼───────────────────────    │
│  Single-stage (node:20)             │ ~1.2 GB                   │
│  Single-stage (node:20-alpine)      │ ~400 MB                   │
│  Multi-stage (node:20-alpine)       │ ~150 MB                   │
│  Multi-stage (distroless)           │ ~100 MB                   │
│  Multi-stage (scratch) - Go         │ ~10 MB                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Stage Build Best Practices                    │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Name stages for clarity (AS builder, AS runner)              │
│ ☐ Copy only necessary files between stages                      │
│ ☐ Use minimal base images for final stage                       │
│ ☐ Leverage build cache effectively                              │
│ ☐ Use --target for development/test/production                  │
│ ☐ Install production dependencies only in final stage           │
│ ☐ Remove unnecessary files before copying                       │
│ ☐ Use BuildKit cache mounts                                     │
│ ☐ Add security scanning stage                                   │
│ ☐ Document build arguments                                      │
│ ☐ Test each stage independently                                 │
│ ☐ Monitor final image size                                      │
└─────────────────────────────────────────────────────────────────┘
```
