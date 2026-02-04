# Containerization Reference

## Multi-Stage Dockerfile

```dockerfile
# Build stage
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# Copy only production files
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "dist/main.js"]
```

## Docker Compose

### Development Stack

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - .:/app
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started

  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=app
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Production Stack

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    image: ${REGISTRY}/api:${TAG}
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - NODE_ENV=production
    secrets:
      - db_password
      - redis_password
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

secrets:
  db_password:
    external: true
  redis_password:
    external: true
```

## Container Best Practices

### .dockerignore

```plaintext
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
.idea
.vscode
```

### Layer Optimization

```dockerfile
# ❌ Bad: Invalidates cache on any file change
COPY . .
RUN npm ci

# ✅ Good: Dependencies cached separately
COPY package*.json ./
RUN npm ci
COPY . .
```

### Security Scanning

```bash
# Trivy scan
docker run --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image myapp:latest

# Snyk scan
snyk container test myapp:latest

# Docker Scout
docker scout cves myapp:latest
```

## Container Commands

### Image Management

```bash
# Build with context
docker build -t app:latest .
docker build -t app:v1.0 -f Dockerfile.prod .
docker build --no-cache -t app:latest .

# Tag and push
docker tag app:latest registry.example.com/app:latest
docker push registry.example.com/app:latest

# Image info
docker images
docker history app:latest
docker inspect app:latest
```

### Container Operations

```bash
# Run with options
docker run -d \
  --name api \
  -p 3000:3000 \
  -e NODE_ENV=production \
  -v logs:/app/logs \
  --restart unless-stopped \
  app:latest

# Exec and debug
docker exec -it api sh
docker logs -f --tail 100 api
docker stats api
docker top api

# Cleanup
docker rm -f api
docker system prune -af --volumes
```

### Networking

```bash
# Create network
docker network create app-network

# Run with network
docker run -d --network app-network --name api app:latest
docker run -d --network app-network --name db postgres:16

# Containers on same network can communicate by name
# api can connect to db:5432
```

### Volumes

```bash
# Named volume
docker volume create app-data
docker run -v app-data:/data app:latest

# Bind mount
docker run -v $(pwd)/config:/app/config:ro app:latest

# tmpfs (memory only)
docker run --tmpfs /tmp app:latest
```

## Resource Limits

```bash
# Memory
docker run -m 512m app:latest
docker run --memory 1g --memory-swap 2g app:latest

# CPU
docker run --cpus 0.5 app:latest
docker run --cpu-shares 512 app:latest

# Both
docker run -m 512m --cpus 0.5 app:latest
```

## Health Checks

```dockerfile
# HTTP check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/health || exit 1

# TCP check
HEALTHCHECK CMD nc -z localhost 3000 || exit 1

# Custom script
HEALTHCHECK CMD /app/healthcheck.sh
```
