---
name: docker-basics
description: Docker fundamentals and core concepts
applies_to: docker
---

# Docker Basics

## What is Docker?

Docker is a platform for developing, shipping, and running applications in containers. Containers package an application with all its dependencies into a standardized unit.

## Core Components

### Docker Engine
The runtime that builds and runs containers.

```bash
# Check Docker version
docker version

# View system info
docker info

# Check Docker status
docker system df
```

### Docker CLI
Command-line interface for interacting with Docker.

```bash
# Basic command structure
docker [OPTIONS] COMMAND [ARG...]

# Get help
docker --help
docker COMMAND --help
```

## Container Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Created   │ ──► │   Running   │ ──► │   Stopped   │
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                   │
      │                    ▼                   │
      │             ┌─────────────┐            │
      └──────────── │   Removed   │ ◄──────────┘
                    └─────────────┘
```

### Container States
- **Created**: Container created but not started
- **Running**: Container is executing
- **Paused**: Container processes paused
- **Stopped**: Container exited (can be restarted)
- **Removed**: Container deleted

## Essential Commands

### Running Containers

```bash
# Run a container
docker run nginx

# Run in detached mode (background)
docker run -d nginx

# Run with port mapping
docker run -d -p 8080:80 nginx

# Run with name
docker run -d --name my-nginx nginx

# Run with environment variables
docker run -d -e MYSQL_ROOT_PASSWORD=secret mysql

# Run with volume
docker run -d -v mydata:/data nginx

# Run interactively
docker run -it ubuntu /bin/bash

# Run and remove after exit
docker run --rm -it python:3.12 python
```

### Managing Containers

```bash
# List running containers
docker ps

# List all containers (including stopped)
docker ps -a

# Stop a container
docker stop my-nginx

# Start a stopped container
docker start my-nginx

# Restart a container
docker restart my-nginx

# Remove a container
docker rm my-nginx

# Force remove running container
docker rm -f my-nginx

# Remove all stopped containers
docker container prune
```

### Container Inspection

```bash
# View container logs
docker logs my-nginx
docker logs -f my-nginx      # Follow logs
docker logs --tail 100 my-nginx  # Last 100 lines

# Execute command in running container
docker exec -it my-nginx /bin/bash
docker exec my-nginx cat /etc/nginx/nginx.conf

# View container details
docker inspect my-nginx

# View container resource usage
docker stats
docker stats my-nginx

# View processes in container
docker top my-nginx
```

### Managing Images

```bash
# List images
docker images

# Pull an image
docker pull nginx:latest
docker pull nginx:1.25-alpine

# Remove an image
docker rmi nginx:latest

# Remove unused images
docker image prune

# Remove all unused images
docker image prune -a

# Build an image
docker build -t myapp:latest .

# Tag an image
docker tag myapp:latest myregistry/myapp:v1.0

# Push an image
docker push myregistry/myapp:v1.0
```

## Flags Reference

### Common `docker run` Flags

| Flag | Description | Example |
|------|-------------|---------|
| `-d` | Detached mode (background) | `docker run -d nginx` |
| `-p` | Port mapping | `docker run -p 8080:80 nginx` |
| `-v` | Volume mount | `docker run -v data:/app/data nginx` |
| `-e` | Environment variable | `docker run -e NODE_ENV=prod app` |
| `--name` | Container name | `docker run --name web nginx` |
| `--rm` | Remove after exit | `docker run --rm -it python` |
| `-it` | Interactive with TTY | `docker run -it ubuntu bash` |
| `--network` | Network to connect | `docker run --network mynet nginx` |
| `-m` | Memory limit | `docker run -m 512m nginx` |
| `--cpus` | CPU limit | `docker run --cpus 0.5 nginx` |

## Docker Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Client                        │
│                    (docker CLI)                          │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                     Docker Host                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  Container  │  │  Container  │  │  Container  │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Image     │  │   Image     │  │   Image     │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                                                         │
│                   Docker Daemon                         │
└─────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Docker Registry                       │
│              (Docker Hub, Private Registry)              │
└─────────────────────────────────────────────────────────┘
```

## Best Practices

1. **Use Specific Tags**: Don't use `latest`, pin to specific versions
2. **Clean Up Resources**: Regularly prune unused containers and images
3. **Use Volumes for Data**: Don't store data in containers
4. **One Process Per Container**: Follow single responsibility principle
5. **Use .dockerignore**: Exclude unnecessary files from build context

## Related Skills
- fundamentals/images-containers
- fundamentals/dockerfile-syntax
- fundamentals/build-context
