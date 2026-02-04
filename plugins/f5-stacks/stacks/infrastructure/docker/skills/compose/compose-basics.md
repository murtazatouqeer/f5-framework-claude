---
name: compose-basics
description: Docker Compose fundamentals and configuration
applies_to: docker
---

# Docker Compose Basics

## What is Docker Compose?

Docker Compose is a tool for defining and running multi-container Docker applications using a YAML file.

## File Format

```yaml
# docker-compose.yml (or compose.yml)
name: my-app  # Optional project name

services:
  web:
    image: nginx
    ports:
      - "80:80"

  api:
    build: ./api
    ports:
      - "3000:3000"

networks:
  default:
    driver: bridge

volumes:
  data:
```

## Essential Commands

### Lifecycle

```bash
# Start services
docker compose up              # Foreground
docker compose up -d           # Detached (background)

# Stop services
docker compose stop            # Stop containers
docker compose down            # Stop and remove containers
docker compose down -v         # Also remove volumes
docker compose down --rmi all  # Also remove images

# Restart
docker compose restart
docker compose restart api     # Specific service
```

### Build

```bash
# Build images
docker compose build
docker compose build --no-cache
docker compose build api       # Specific service

# Build and start
docker compose up --build
```

### Status and Logs

```bash
# List services
docker compose ps
docker compose ps -a           # Include stopped

# View logs
docker compose logs
docker compose logs -f         # Follow
docker compose logs api        # Specific service
docker compose logs --tail 100 # Last 100 lines
```

### Execution

```bash
# Run command in running container
docker compose exec api /bin/sh
docker compose exec api npm test

# Run command in new container
docker compose run api npm test
docker compose run --rm api npm test  # Remove after

# Scale services
docker compose up -d --scale worker=3
```

## Service Configuration

### Basic Service

```yaml
services:
  api:
    # Image to use
    image: node:20-alpine

    # OR build from Dockerfile
    build:
      context: ./api
      dockerfile: Dockerfile
      target: production
      args:
        - NODE_VERSION=20

    # Container name (optional)
    container_name: my-api

    # Command override
    command: npm start

    # Entrypoint override
    entrypoint: ["./docker-entrypoint.sh"]

    # Working directory
    working_dir: /app
```

### Ports

```yaml
services:
  web:
    ports:
      # HOST:CONTAINER
      - "80:80"           # Map host 80 to container 80
      - "443:443"         # HTTPS
      - "3000-3005:3000-3005"  # Range

      # Only container port (random host port)
      - "80"

      # Specific interface
      - "127.0.0.1:3000:3000"

      # UDP
      - "53:53/udp"
```

### Environment Variables

```yaml
services:
  api:
    # List format
    environment:
      - NODE_ENV=production
      - PORT=3000
      - DATABASE_URL=postgres://db:5432/app

    # Map format
    environment:
      NODE_ENV: production
      PORT: 3000

    # From file
    env_file:
      - .env
      - .env.local

    # Required variable (error if not set)
    environment:
      - SECRET_KEY=${SECRET_KEY:?SECRET_KEY is required}

    # Default value
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-info}
```

### Dependencies

```yaml
services:
  api:
    depends_on:
      - db
      - redis

  # With health condition (recommended)
  api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
```

### Health Check

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
```

### Restart Policy

```yaml
services:
  api:
    restart: "no"              # Default, don't restart
    restart: always            # Always restart
    restart: on-failure        # Only on failure
    restart: unless-stopped    # Unless manually stopped
```

### Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Multiple Compose Files

### Override Pattern

```bash
# Base configuration
docker-compose.yml

# Development overrides (auto-loaded)
docker-compose.override.yml

# Production configuration
docker-compose.prod.yml

# Test configuration
docker-compose.test.yml
```

### Using Multiple Files

```bash
# Default: docker-compose.yml + docker-compose.override.yml
docker compose up

# Explicit files
docker compose -f docker-compose.yml -f docker-compose.prod.yml up

# Production (skip override)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Base File

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: ./api
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Development Override

```yaml
# docker-compose.override.yml
services:
  api:
    build:
      target: development
    volumes:
      - ./api:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
    command: npm run dev

  db:
    ports:
      - "5432:5432"
    environment:
      - POSTGRES_PASSWORD=devpassword
```

### Production Override

```yaml
# docker-compose.prod.yml
services:
  api:
    build:
      target: production
    environment:
      - NODE_ENV=production
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G

  db:
    # No exposed ports in production
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
```

## Variable Substitution

### Environment Variables

```yaml
services:
  api:
    image: myapp:${VERSION:-latest}
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

```bash
# .env file (auto-loaded)
VERSION=1.0.0
DATABASE_URL=postgres://localhost:5432/app
```

### Default Values

```yaml
# ${VAR:-default} - Use default if not set or empty
# ${VAR-default}  - Use default only if not set
# ${VAR:?error}   - Error if not set or empty
# ${VAR?error}    - Error only if not set

services:
  api:
    environment:
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - SECRET=${SECRET:?SECRET is required}
```

## Profiles

```yaml
services:
  api:
    # Always runs
    image: myapp

  debug:
    # Only runs with --profile debug
    profiles:
      - debug
    image: debug-tools

  monitoring:
    # Only runs with --profile monitoring
    profiles:
      - monitoring
    image: prometheus
```

```bash
# Run with profiles
docker compose --profile debug up
docker compose --profile debug --profile monitoring up
```

## Best Practices

1. **Use depends_on with conditions** for proper startup order
2. **Define health checks** for all services
3. **Use override files** for environment-specific config
4. **Use .env files** for sensitive data (not in version control)
5. **Pin image versions** (not :latest)
6. **Use networks** for service isolation
7. **Use named volumes** for data persistence

## Related Skills
- compose/services
- compose/networks
- compose/volumes
- compose/environment
