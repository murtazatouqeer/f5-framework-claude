---
name: images-containers
description: Understanding Docker images and containers
applies_to: docker
---

# Docker Images and Containers

## Images vs Containers

### Images
- **Read-only template** for creating containers
- **Layered filesystem** - each instruction creates a layer
- **Immutable** - once built, cannot be changed
- **Stored in registry** (Docker Hub, private registry)

### Containers
- **Runnable instance** of an image
- **Writable layer** on top of image layers
- **Ephemeral** by default (data lost when removed)
- **Isolated process** with own filesystem, networking

```
┌─────────────────────────────────────┐
│           Container Layer           │  ← Writable (changes here)
│            (Read/Write)             │
├─────────────────────────────────────┤
│           Image Layer 4             │  ← Read-only
│          (CMD, EXPOSE)              │
├─────────────────────────────────────┤
│           Image Layer 3             │  ← Read-only
│        (COPY application)           │
├─────────────────────────────────────┤
│           Image Layer 2             │  ← Read-only
│       (RUN npm install)             │
├─────────────────────────────────────┤
│           Image Layer 1             │  ← Read-only
│         (FROM node:20)              │
└─────────────────────────────────────┘
```

## Image Layers

### How Layers Work

Each Dockerfile instruction creates a layer:

```dockerfile
FROM node:20-alpine       # Layer 1: Base image
WORKDIR /app              # Layer 2: Set working directory
COPY package*.json ./     # Layer 3: Copy package files
RUN npm ci                # Layer 4: Install dependencies
COPY . .                  # Layer 5: Copy source code
RUN npm run build         # Layer 6: Build application
CMD ["node", "dist/main"] # Layer 7: Set command
```

### Viewing Layers

```bash
# View image layers
docker history myapp:latest

# Detailed layer info
docker history --no-trunc myapp:latest

# Image inspect
docker inspect myapp:latest | jq '.[0].RootFS.Layers'
```

### Layer Caching

Docker caches layers to speed up builds:

```dockerfile
# BAD: Any code change invalidates npm cache
COPY . .
RUN npm ci

# GOOD: Dependencies cached until package.json changes
COPY package*.json ./
RUN npm ci
COPY . .
```

## Image Tags and Digests

### Tags
Human-readable identifiers for images:

```bash
# Tag format
repository:tag
# Examples
nginx:latest
nginx:1.25
nginx:1.25-alpine
myregistry.com/myapp:v1.0.0
```

### Best Practices for Tags

```bash
# Development
myapp:dev
myapp:latest

# Staging
myapp:staging
myapp:rc-1.0.0

# Production (use specific versions)
myapp:1.0.0
myapp:1.0.0-alpine

# Git-based
myapp:abc1234    # Short commit hash
myapp:main-abc1234
```

### Digests
Immutable content-addressable identifiers:

```bash
# Pull by digest (guaranteed same image)
docker pull nginx@sha256:abc123...

# View image digest
docker images --digests

# Inspect shows digest
docker inspect nginx:latest | jq '.[0].RepoDigests'
```

## Working with Images

### Listing Images

```bash
# List all images
docker images

# Filter images
docker images nginx
docker images --filter "dangling=true"

# Format output
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
```

### Pulling Images

```bash
# Pull latest tag
docker pull nginx

# Pull specific tag
docker pull nginx:1.25-alpine

# Pull from private registry
docker pull myregistry.com/myapp:v1.0

# Pull all tags
docker pull -a nginx
```

### Building Images

```bash
# Build from Dockerfile
docker build -t myapp:latest .

# Build with different Dockerfile
docker build -f Dockerfile.prod -t myapp:prod .

# Build with build args
docker build --build-arg NODE_VERSION=20 -t myapp .

# Build specific stage
docker build --target builder -t myapp:builder .

# Build for different platform
docker build --platform linux/amd64 -t myapp .
```

### Pushing Images

```bash
# Login to registry
docker login
docker login myregistry.com

# Tag for registry
docker tag myapp:latest myregistry.com/myapp:v1.0

# Push image
docker push myregistry.com/myapp:v1.0
```

### Saving and Loading

```bash
# Save image to tar file
docker save -o myapp.tar myapp:latest

# Load image from tar file
docker load -i myapp.tar

# Export container filesystem
docker export container_name > filesystem.tar

# Import as image
docker import filesystem.tar myimage:latest
```

## Working with Containers

### Creating vs Running

```bash
# Create container (doesn't start)
docker create --name mycontainer nginx

# Start created container
docker start mycontainer

# Run = create + start
docker run --name mycontainer nginx
```

### Container Data

#### View Changes
```bash
# See what files changed in container
docker diff container_name
# A = Added, C = Changed, D = Deleted
```

#### Copy Files
```bash
# Copy from container to host
docker cp container_name:/app/logs ./logs

# Copy from host to container
docker cp ./config.json container_name:/app/config.json
```

#### Commit Changes
```bash
# Create new image from container changes
docker commit container_name new_image:tag

# With message and author
docker commit -m "Added config" -a "Author" container_name new_image:tag
```

### Container Limits

```bash
# Memory limit
docker run -m 512m myapp

# CPU limit
docker run --cpus 0.5 myapp

# Combine limits
docker run -m 512m --cpus 0.5 myapp

# View resource usage
docker stats
```

## Image Optimization

### Size Comparison

```bash
# Compare base image sizes
docker images --format "{{.Repository}}:{{.Tag}} {{.Size}}" | sort -k2 -h

# Typical sizes:
# node:20          ~1GB
# node:20-slim     ~250MB
# node:20-alpine   ~180MB
# gcr.io/distroless/nodejs20  ~150MB
```

### Analyzing Image Size

```bash
# View layer sizes
docker history myapp:latest

# Use dive for detailed analysis
dive myapp:latest
```

### Cleanup

```bash
# Remove unused images
docker image prune

# Remove all unused images
docker image prune -a

# Remove everything unused
docker system prune -a

# Check disk usage
docker system df
```

## Related Skills
- fundamentals/dockerfile-syntax
- dockerfile/layer-optimization
- optimization/image-size
