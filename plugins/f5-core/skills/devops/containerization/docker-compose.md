---
name: docker-compose
description: Docker Compose for multi-container applications
category: devops/containerization
applies_to: all
allowed-tools: Read, Write, Glob, Grep, Bash
user-invocable: false
context: inject
---

# Docker Compose

## Overview

Docker Compose is a tool for defining and running multi-container Docker
applications using a YAML file to configure services.

## Complete Application Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ==========================================================================
  # API Service
  # ==========================================================================
  api:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        NODE_ENV: production
    image: myapp-api:${VERSION:-latest}
    container_name: myapp-api
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - backend
      - frontend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  # ==========================================================================
  # Database Service
  # ==========================================================================
  db:
    image: postgres:16-alpine
    container_name: myapp-db
    restart: unless-stopped
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
      POSTGRES_DB: myapp
      PGDATA: /var/lib/postgresql/data/pgdata
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d:ro
    ports:
      - "5432:5432"
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d myapp"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  # ==========================================================================
  # Redis Cache
  # ==========================================================================
  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD:-redispass}
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ==========================================================================
  # Nginx Reverse Proxy
  # ==========================================================================
  nginx:
    image: nginx:alpine
    container_name: myapp-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static-files:/var/www/static:ro
    depends_on:
      - api
    networks:
      - frontend
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ==========================================================================
  # Worker Service
  # ==========================================================================
  worker:
    build:
      context: .
      dockerfile: Dockerfile.worker
    image: myapp-worker:${VERSION:-latest}
    container_name: myapp-worker
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    networks:
      - backend
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 256M

# ==========================================================================
# Networks
# ==========================================================================
networks:
  frontend:
    driver: bridge
    name: myapp-frontend
  backend:
    driver: bridge
    name: myapp-backend
    internal: true  # No external access

# ==========================================================================
# Volumes
# ==========================================================================
volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  static-files:
    driver: local
```

## Essential Commands

```bash
# Start services
docker-compose up
docker-compose up -d              # Detached mode
docker-compose up --build         # Rebuild images
docker-compose up -d --scale worker=3  # Scale workers

# Stop services
docker-compose stop               # Stop services
docker-compose down               # Stop and remove containers
docker-compose down -v            # Also remove volumes
docker-compose down --rmi all     # Also remove images

# View status
docker-compose ps
docker-compose logs
docker-compose logs -f api        # Follow specific service

# Execute commands
docker-compose exec api sh
docker-compose exec db psql -U postgres

# Build images
docker-compose build
docker-compose build --no-cache api

# Pull images
docker-compose pull

# Restart services
docker-compose restart
docker-compose restart api
```

## Environment Variables

### Using .env File

```bash
# .env
VERSION=1.0.0
DB_PASSWORD=securepassword
JWT_SECRET=mysupersecretkey
REDIS_PASSWORD=redispass
```

```yaml
# docker-compose.yml
services:
  api:
    image: myapp:${VERSION}
    environment:
      - DB_PASSWORD=${DB_PASSWORD}
```

### Multiple Environment Files

```bash
# Development
docker-compose --env-file .env.development up

# Production
docker-compose --env-file .env.production up

# Override with local
docker-compose -f docker-compose.yml -f docker-compose.local.yml up
```

## Override Files

```yaml
# docker-compose.yml (base)
services:
  api:
    image: myapp:latest
    environment:
      - NODE_ENV=production

# docker-compose.override.yml (dev, auto-loaded)
services:
  api:
    build: .
    volumes:
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DEBUG=*
    ports:
      - "9229:9229"  # Debug port

# docker-compose.prod.yml
services:
  api:
    image: registry.example.com/myapp:${VERSION}
    deploy:
      replicas: 3
```

```bash
# Development (uses override automatically)
docker-compose up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Development Configuration

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      # Hot reload
      - .:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    ports:
      - "3000:3000"
      - "9229:9229"  # Debugger
    command: npm run dev

  # Development database with seed data
  db:
    volumes:
      - ./dev-data:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"

  # Development tools
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    depends_on:
      - db

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"
      - "8025:8025"
```

## Health Checks

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  # Using wget (no curl in image)
  api-light:
    healthcheck:
      test: ["CMD", "wget", "--spider", "-q", "http://localhost:3000/health"]
```

## Dependencies and Startup Order

```yaml
services:
  api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
      migrations:
        condition: service_completed_successfully

  migrations:
    image: myapp:latest
    command: npm run db:migrate
    depends_on:
      db:
        condition: service_healthy
```

## Networking

```yaml
services:
  api:
    networks:
      - frontend
      - backend
    # Custom network aliases
    networks:
      backend:
        aliases:
          - api-internal

  nginx:
    networks:
      - frontend

  db:
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

## Volume Management

```yaml
services:
  api:
    volumes:
      # Named volume
      - app-data:/app/data
      # Bind mount
      - ./config:/app/config:ro
      # Anonymous volume
      - /app/temp
      # tmpfs (in-memory)
      - type: tmpfs
        target: /app/cache
        tmpfs:
          size: 100000000  # 100MB

volumes:
  app-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /data/app
```

## Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
    # Docker Compose v2 alternative
    mem_limit: 512m
    cpus: 1
```

## Logging Configuration

```yaml
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "production_status"
        env: "NODE_ENV"

  # Syslog driver
  api-syslog:
    logging:
      driver: syslog
      options:
        syslog-address: "tcp://logs.example.com:514"
        tag: "myapp-api"

  # Disable logging
  api-silent:
    logging:
      driver: none
```

## Profiles

```yaml
services:
  api:
    profiles: ["default"]

  debug-tools:
    image: busybox
    profiles: ["debug"]
    command: sleep infinity

  monitoring:
    image: prometheus
    profiles: ["monitoring"]
```

```bash
# Run specific profiles
docker-compose --profile debug up
docker-compose --profile monitoring --profile debug up
```

## Best Practices

```
┌─────────────────────────────────────────────────────────────────┐
│             Docker Compose Best Practices                        │
├─────────────────────────────────────────────────────────────────┤
│ ☐ Use .env files for configuration                              │
│ ☐ Use override files for environments                           │
│ ☐ Define health checks for services                             │
│ ☐ Set resource limits                                           │
│ ☐ Use named volumes for persistence                             │
│ ☐ Use internal networks for backend services                    │
│ ☐ Configure logging drivers                                     │
│ ☐ Use depends_on with conditions                                │
│ ☐ Keep services small and focused                               │
│ ☐ Version your compose files                                    │
│ ☐ Use profiles for optional services                            │
│ ☐ Document service dependencies                                 │
└─────────────────────────────────────────────────────────────────┘
```
