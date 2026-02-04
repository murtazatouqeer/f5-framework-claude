---
name: docker-basics
description: Docker fundamentals and essential commands
category: devops/containerization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Docker Basics

## Overview

Docker is a platform for developing, shipping, and running applications
in containers - lightweight, portable, self-sufficient environments.

## Container Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Container Architecture                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                       │
│  │Container │  │Container │  │Container │                       │
│  │   App    │  │   App    │  │   App    │                       │
│  │  Node.js │  │  Python  │  │  Nginx   │                       │
│  └──────────┘  └──────────┘  └──────────┘                       │
│  ├──────────────────────────────────────────┤                   │
│  │           Docker Engine                   │                   │
│  ├──────────────────────────────────────────┤                   │
│  │           Host Operating System           │                   │
│  ├──────────────────────────────────────────┤                   │
│  │           Infrastructure                  │                   │
│  └──────────────────────────────────────────┘                   │
│                                                                  │
│  Containers share the host OS kernel but are isolated           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Basic Dockerfile

```dockerfile
# Dockerfile for Node.js application
FROM node:20-alpine

# Create app directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application source
COPY . .

# Build application
RUN npm run build

# Expose port
EXPOSE 3000

# Set environment
ENV NODE_ENV=production

# Run application
CMD ["node", "dist/main.js"]
```

## Essential Commands

### Image Commands

```bash
# Build image
docker build -t myapp:latest .
docker build -t myapp:v1.0 -f Dockerfile.prod .

# List images
docker images
docker image ls

# Remove image
docker rmi myapp:latest
docker image rm myapp:latest

# Tag image
docker tag myapp:latest myapp:v1.0
docker tag myapp:latest registry.example.com/myapp:v1.0

# Push image
docker push registry.example.com/myapp:v1.0

# Pull image
docker pull node:20-alpine

# Image history
docker history myapp:latest

# Inspect image
docker inspect myapp:latest
```

### Container Commands

```bash
# Run container
docker run -d --name api -p 3000:3000 myapp:latest
docker run -it --rm node:20-alpine sh

# List containers
docker ps           # Running containers
docker ps -a        # All containers

# Stop/Start containers
docker stop api
docker start api
docker restart api

# Remove container
docker rm api
docker rm -f api    # Force remove running container

# View logs
docker logs api
docker logs -f api  # Follow logs
docker logs --tail 100 api

# Execute in container
docker exec -it api sh
docker exec api ls -la /app

# Copy files
docker cp api:/app/logs ./logs
docker cp ./config.json api:/app/config.json

# Container stats
docker stats
docker stats api
```

### Volume Commands

```bash
# Create volume
docker volume create app-data

# List volumes
docker volume ls

# Inspect volume
docker volume inspect app-data

# Remove volume
docker volume rm app-data

# Mount volume
docker run -v app-data:/data myapp
docker run -v $(pwd)/logs:/app/logs myapp  # Bind mount

# Named volumes vs bind mounts
docker run -v mydata:/app/data myapp      # Named volume
docker run -v /host/path:/container/path myapp  # Bind mount
```

### Network Commands

```bash
# Create network
docker network create app-network

# List networks
docker network ls

# Connect container to network
docker network connect app-network api

# Disconnect container
docker network disconnect app-network api

# Run with network
docker run --network app-network myapp

# Inspect network
docker network inspect app-network
```

## Dockerfile Instructions

### FROM

```dockerfile
# Base image
FROM node:20-alpine

# Multi-platform
FROM --platform=linux/amd64 node:20-alpine

# Multiple stages
FROM node:20 AS builder
FROM node:20-alpine AS runner
```

### WORKDIR

```dockerfile
# Set working directory
WORKDIR /app

# Subsequent commands run from this directory
RUN pwd  # /app
```

### COPY vs ADD

```dockerfile
# COPY - preferred for most cases
COPY package*.json ./
COPY src/ ./src/

# ADD - has extra features (tar extraction, URLs)
ADD https://example.com/file.tar.gz /tmp/
ADD archive.tar.gz /app/
```

### RUN

```dockerfile
# Shell form
RUN npm install

# Exec form
RUN ["npm", "install"]

# Chain commands to reduce layers
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*
```

### ENV

```dockerfile
# Set environment variables
ENV NODE_ENV=production
ENV PORT=3000 HOST=0.0.0.0

# Use in subsequent instructions
RUN echo $NODE_ENV
```

### ARG

```dockerfile
# Build-time arguments
ARG NODE_VERSION=20
FROM node:${NODE_VERSION}-alpine

ARG BUILD_DATE
ARG GIT_COMMIT
LABEL build_date=$BUILD_DATE
LABEL git_commit=$GIT_COMMIT

# Usage: docker build --build-arg GIT_COMMIT=$(git rev-parse HEAD) .
```

### EXPOSE

```dockerfile
# Document exposed ports
EXPOSE 3000
EXPOSE 3000/tcp 3001/udp
```

### CMD vs ENTRYPOINT

```dockerfile
# CMD - default command, can be overridden
CMD ["node", "server.js"]

# ENTRYPOINT - always runs, CMD as arguments
ENTRYPOINT ["node"]
CMD ["server.js"]

# Combined usage
ENTRYPOINT ["npm"]
CMD ["start"]  # docker run myapp test -> npm test
```

### USER

```dockerfile
# Run as non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

# Or use existing user
USER node
```

### HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1
```

## .dockerignore

```plaintext
# .dockerignore
node_modules
npm-debug.log
Dockerfile*
docker-compose*
.dockerignore
.git
.gitignore
.env*
*.md
!README.md
coverage
.nyc_output
dist
*.log
.DS_Store
```

## Environment Variables

```dockerfile
# Dockerfile
ENV NODE_ENV=production
ENV PORT=3000
```

```bash
# Runtime override
docker run -e NODE_ENV=development myapp
docker run --env-file .env myapp

# Multiple variables
docker run \
  -e DATABASE_URL=postgres://... \
  -e REDIS_URL=redis://... \
  myapp
```

## Port Mapping

```bash
# Map container port to host port
docker run -p 3000:3000 myapp           # localhost:3000 -> container:3000
docker run -p 8080:3000 myapp           # localhost:8080 -> container:3000
docker run -p 127.0.0.1:3000:3000 myapp # Bind to localhost only
docker run -P myapp                      # Map all exposed ports to random ports
```

## Resource Limits

```bash
# Memory limits
docker run -m 512m myapp           # 512 MB limit
docker run --memory=1g myapp       # 1 GB limit
docker run --memory-swap=2g myapp  # 2 GB swap

# CPU limits
docker run --cpus=0.5 myapp        # 50% of one CPU
docker run --cpus=2 myapp          # 2 CPUs
docker run --cpu-shares=512 myapp  # Relative weight
```

## Debugging Containers

```bash
# View container details
docker inspect api
docker inspect --format='{{.State.Status}}' api

# View logs
docker logs api
docker logs -f --since 5m api

# Execute shell
docker exec -it api sh
docker exec -it api /bin/bash

# View processes
docker top api

# View resource usage
docker stats api

# Export container filesystem
docker export api > api.tar
```

## Best Practices Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                  Docker Best Practices                           │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use official base images                                      │
│ ☐ Use specific version tags (not :latest)                       │
│ ☐ Use alpine images when possible                               │
│ ☐ Run as non-root user                                          │
│ ☐ Minimize number of layers                                     │
│ ☐ Use .dockerignore                                             │
│ ☐ Order instructions from least to most changing                │
│ ☐ Use multi-stage builds                                        │
│ ☐ Don't store secrets in images                                 │
│ ☐ Implement health checks                                       │
│ ☐ Set resource limits                                           │
│ ☐ Scan images for vulnerabilities                               │
└─────────────────────────────────────────────────────────────────┘
```
