---
name: layer-optimization
description: Optimizing Docker image layers for size and build speed
applies_to: docker
---

# Docker Layer Optimization

## Understanding Layers

Each Dockerfile instruction creates a layer. Layers are:
- **Cached**: Reused if instruction hasn't changed
- **Stacked**: Each layer adds to the previous
- **Union**: Combined into single filesystem view
- **Immutable**: Can't be modified after creation

## Layer Size Analysis

```bash
# View layer sizes
docker history myapp:latest

# Detailed analysis with dive
docker pull wagoodman/dive
docker run --rm -it -v /var/run/docker.sock:/var/run/docker.sock wagoodman/dive myapp:latest
```

## Optimization Techniques

### 1. Combine RUN Commands

```dockerfile
# BAD: 4 separate layers (~300MB total)
RUN apt-get update
RUN apt-get install -y curl
RUN apt-get install -y git
RUN rm -rf /var/lib/apt/lists/*

# GOOD: 1 layer (~150MB), cleanup in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean
```

### 2. Order Instructions by Change Frequency

```dockerfile
# BAD: Any code change invalidates npm install cache
COPY . .
RUN npm install

# GOOD: Dependencies cached until package.json changes
# Least frequently changed first
COPY package.json package-lock.json ./
RUN npm ci

# Most frequently changed last
COPY . .
RUN npm run build
```

### 3. Use Specific COPY

```dockerfile
# BAD: Copies everything, including unnecessary files
COPY . .

# GOOD: Copy only what's needed
COPY package.json package-lock.json ./
COPY src/ ./src/
COPY tsconfig.json ./
```

### 4. Clean Up in Same Layer

```dockerfile
# BAD: Files deleted in later layer still in image
RUN curl -LO https://example.com/large-file.tar.gz
RUN tar -xzf large-file.tar.gz
RUN rm large-file.tar.gz

# GOOD: Clean up in same RUN command
RUN curl -LO https://example.com/large-file.tar.gz && \
    tar -xzf large-file.tar.gz && \
    rm large-file.tar.gz
```

### 5. Use --no-install-recommends

```dockerfile
# BAD: Installs recommended packages (larger)
RUN apt-get install -y python3

# GOOD: Only install required packages
RUN apt-get install -y --no-install-recommends python3
```

### 6. Multi-Stage for Build Dependencies

```dockerfile
# Build stage has all dependencies
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci  # Includes devDependencies
COPY . .
RUN npm run build

# Production only has runtime dependencies
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
RUN npm ci --only=production  # No devDependencies
CMD ["node", "dist/main.js"]
```

## Layer Caching Strategies

### Optimal Layer Order

```dockerfile
# 1. Base image (rarely changes)
FROM node:20-alpine

# 2. System dependencies (rarely changes)
RUN apk add --no-cache dumb-init

# 3. Working directory
WORKDIR /app

# 4. Package manager files (changes with dependencies)
COPY package.json package-lock.json ./

# 5. Install dependencies (cached until package.json changes)
RUN npm ci

# 6. Application source (changes frequently)
COPY . .

# 7. Build (only runs when source changes)
RUN npm run build

# 8. Runtime configuration
ENV NODE_ENV=production
EXPOSE 3000
CMD ["dumb-init", "node", "dist/main.js"]
```

### Separating Dev and Prod Dependencies

```dockerfile
# Stage 1: All dependencies for building
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Production dependencies only
FROM node:20-alpine AS prod-deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Stage 4: Production image
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=prod-deps /app/node_modules ./node_modules
COPY --from=builder /app/dist ./dist
CMD ["node", "dist/main.js"]
```

## Common Patterns

### Node.js Optimization

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app

# Copy lockfile first for cache
COPY package.json package-lock.json ./

# Use npm ci for reproducible builds
RUN npm ci

# Copy source
COPY . .

# Build
RUN npm run build

# Prune dev dependencies
RUN npm prune --production

FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production

# Copy only necessary files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

CMD ["node", "dist/main.js"]
```

### Python Optimization

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app

# Create venv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
COPY . .

CMD ["python", "app.py"]
```

### Go Optimization

```dockerfile
FROM golang:1.22-alpine AS builder
WORKDIR /app

# Download dependencies first
COPY go.mod go.sum ./
RUN go mod download

# Copy source and build
COPY . .
RUN CGO_ENABLED=0 go build -ldflags='-w -s' -o /server

# Minimal runtime
FROM scratch
COPY --from=builder /server /server
CMD ["/server"]
```

## Measuring Optimization

### Before/After Comparison

```bash
# Check image size
docker images myapp

# Compare layers
docker history myapp:before
docker history myapp:after

# Detailed size analysis
docker inspect myapp:latest | jq '.[0].Size'
```

### Optimization Checklist

- [ ] Combined RUN commands where possible
- [ ] Cleaned up in same layer as install
- [ ] Used --no-install-recommends for apt
- [ ] Ordered COPY by change frequency
- [ ] Used multi-stage build
- [ ] Separated build and runtime dependencies
- [ ] Used specific COPY instead of COPY . .
- [ ] Used minimal base image

## Size Impact Reference

| Optimization | Typical Savings |
|--------------|-----------------|
| Alpine base | 600-800MB |
| Multi-stage | 200-500MB |
| Combine RUN | 50-100MB |
| Clean apt cache | 50-100MB |
| No dev deps | 100-300MB |
| --no-install-recommends | 50-200MB |

## Related Skills
- dockerfile/caching-strategies
- dockerfile/multi-stage-builds
- optimization/image-size
