---
name: dockerfile-syntax
description: Dockerfile instructions and syntax reference
applies_to: docker
---

# Dockerfile Syntax

## Dockerfile Overview

A Dockerfile is a text file containing instructions to build a Docker image.

```dockerfile
# Comment
INSTRUCTION arguments
```

## Instructions Reference

### FROM
Sets the base image for subsequent instructions.

```dockerfile
# Basic usage
FROM ubuntu:22.04

# With platform
FROM --platform=linux/amd64 node:20-alpine

# Named stage (for multi-stage builds)
FROM node:20-alpine AS builder

# Scratch (empty base image)
FROM scratch
```

### WORKDIR
Sets the working directory for subsequent instructions.

```dockerfile
# Set working directory
WORKDIR /app

# Creates directory if it doesn't exist
WORKDIR /app/src

# Can use environment variables
WORKDIR $HOME/app
```

### COPY
Copies files from build context into the image.

```dockerfile
# Copy single file
COPY package.json .

# Copy multiple files
COPY package.json package-lock.json ./

# Copy directory
COPY src/ ./src/

# Copy with glob pattern
COPY *.json ./

# Copy with ownership
COPY --chown=user:group files/ /app/

# Copy from another stage
COPY --from=builder /app/dist ./dist
```

### ADD
Similar to COPY, but with extra features (use COPY unless you need these).

```dockerfile
# Auto-extract tar archives
ADD archive.tar.gz /app/

# Download from URL (not recommended)
ADD https://example.com/file.txt /app/
```

### RUN
Executes commands in a new layer.

```dockerfile
# Shell form (runs in /bin/sh -c)
RUN apt-get update && apt-get install -y curl

# Exec form (no shell processing)
RUN ["apt-get", "update"]

# Multi-line (use backslash)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      git \
    && rm -rf /var/lib/apt/lists/*

# With BuildKit cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci
```

### ENV
Sets environment variables.

```dockerfile
# Single variable
ENV NODE_ENV=production

# Multiple variables (legacy)
ENV NODE_ENV=production PORT=3000

# Multiple with new syntax
ENV NODE_ENV=production
ENV PORT=3000

# Use in subsequent instructions
ENV APP_HOME=/app
WORKDIR $APP_HOME
```

### ARG
Defines build-time variables.

```dockerfile
# Define argument with default
ARG NODE_VERSION=20

# Use in FROM
FROM node:${NODE_VERSION}-alpine

# Define without default
ARG BUILD_DATE

# Use in RUN
RUN echo "Build date: $BUILD_DATE"
```

```bash
# Pass at build time
docker build --build-arg NODE_VERSION=18 --build-arg BUILD_DATE=$(date -I) .
```

### EXPOSE
Documents which ports the container listens on.

```dockerfile
# Single port
EXPOSE 3000

# Multiple ports
EXPOSE 80 443

# With protocol
EXPOSE 80/tcp
EXPOSE 53/udp
```

**Note**: EXPOSE doesn't actually publish the port. Use `-p` when running.

### CMD
Sets the default command to run when container starts.

```dockerfile
# Exec form (recommended)
CMD ["node", "dist/main.js"]

# Shell form
CMD node dist/main.js

# As parameters to ENTRYPOINT
ENTRYPOINT ["python"]
CMD ["app.py"]
```

### ENTRYPOINT
Configures the container to run as an executable.

```dockerfile
# Exec form
ENTRYPOINT ["python", "app.py"]

# Combined with CMD for defaults
ENTRYPOINT ["python"]
CMD ["--help"]

# Can be overridden with --entrypoint
docker run --entrypoint /bin/sh myimage
```

#### CMD vs ENTRYPOINT

| Scenario | ENTRYPOINT | CMD |
|----------|------------|-----|
| Default command | - | `CMD ["node", "app.js"]` |
| Fixed executable | `ENTRYPOINT ["python"]` | `CMD ["app.py"]` |
| Wrapper script | `ENTRYPOINT ["./entrypoint.sh"]` | `CMD ["start"]` |

### USER
Sets the user for subsequent instructions and container runtime.

```dockerfile
# Create user and switch
RUN addgroup -g 1001 -S appgroup && \
    adduser -S -u 1001 -G appgroup appuser

USER appuser

# Or use UID
USER 1001

# User:group
USER appuser:appgroup
```

### VOLUME
Creates a mount point for external volumes.

```dockerfile
# Single volume
VOLUME /data

# Multiple volumes
VOLUME ["/data", "/logs"]
```

### LABEL
Adds metadata to the image.

```dockerfile
# OCI standard labels
LABEL org.opencontainers.image.title="My App"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.description="My application"
LABEL org.opencontainers.image.vendor="My Company"
LABEL org.opencontainers.image.source="https://github.com/myorg/myapp"

# Multiple labels
LABEL version="1.0" maintainer="dev@example.com"
```

### HEALTHCHECK
Defines how to check if container is healthy.

```dockerfile
# Basic health check
HEALTHCHECK CMD curl -f http://localhost:3000/health || exit 1

# With options
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

# Disable health check (if base image has one)
HEALTHCHECK NONE
```

### SHELL
Changes the default shell for shell form commands.

```dockerfile
# Use PowerShell on Windows
SHELL ["powershell", "-Command"]

# Use bash
SHELL ["/bin/bash", "-c"]
```

### STOPSIGNAL
Sets the system call signal to stop the container.

```dockerfile
# Default is SIGTERM
STOPSIGNAL SIGTERM

# Use SIGQUIT for graceful shutdown
STOPSIGNAL SIGQUIT
```

## Multi-Stage Builds

```dockerfile
# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/main.js"]
```

## BuildKit Features

Enable BuildKit for advanced features:

```bash
export DOCKER_BUILDKIT=1
```

### Cache Mounts

```dockerfile
# syntax=docker/dockerfile:1.4

# Cache npm
RUN --mount=type=cache,target=/root/.npm \
    npm ci

# Cache pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Secret Mounts

```dockerfile
# syntax=docker/dockerfile:1.4

# Mount secret at build time
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

```bash
docker build --secret id=npmrc,src=.npmrc .
```

### SSH Mounts

```dockerfile
# syntax=docker/dockerfile:1.4

# Forward SSH agent for private repos
RUN --mount=type=ssh \
    git clone git@github.com:private/repo.git
```

```bash
docker build --ssh default .
```

## Best Practices

1. **Use specific base image tags**
2. **Order instructions for cache efficiency**
3. **Combine RUN commands**
4. **Clean up in the same layer**
5. **Use multi-stage builds**
6. **Run as non-root user**
7. **Use .dockerignore**

## Related Skills
- fundamentals/build-context
- dockerfile/multi-stage-builds
- dockerfile/best-practices
