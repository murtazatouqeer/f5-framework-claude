---
name: docker-runtime-performance
description: Optimizing Docker container runtime performance
applies_to: docker
---

# Docker Runtime Performance

## Resource Allocation

### Memory

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M      # Hard limit
        reservations:
          memory: 256M      # Guaranteed minimum
```

```bash
# CLI
docker run --memory 512m --memory-reservation 256m myapp
```

### CPU

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1.5'       # Max 1.5 CPUs
        reservations:
          cpus: '0.5'       # Guaranteed 0.5 CPU
```

```bash
# CLI
docker run --cpus 1.5 --cpu-shares 1024 myapp

# Pin to specific CPUs
docker run --cpuset-cpus "0,1" myapp
```

### Memory + CPU Together

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  worker:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M

  db:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 1G
```

## Storage Performance

### Volume Drivers

```yaml
services:
  db:
    volumes:
      - type: volume
        source: postgres_data
        target: /var/lib/postgresql/data
        volume:
          nocopy: true

volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: /fast-ssd/postgres
      o: bind
```

### tmpfs for Speed

```yaml
services:
  app:
    tmpfs:
      # Cache in RAM
      - /app/cache:size=200M
      # Temp files
      - /tmp:size=100M
```

### Bind Mount Performance (macOS/Windows)

```yaml
services:
  app:
    volumes:
      # Read-heavy: use cached
      - ./src:/app/src:cached

      # Write-heavy: use delegated
      - ./logs:/app/logs:delegated

      # Heavy I/O: use named volume
      - node_modules:/app/node_modules

volumes:
  node_modules:
```

## Network Performance

### Host Network

```yaml
services:
  high-perf-api:
    network_mode: host  # Best network performance
```

### Optimize Bridge Network

```yaml
networks:
  fast:
    driver: bridge
    driver_opts:
      com.docker.network.driver.mtu: 9000  # Jumbo frames
```

### Reduce DNS Lookups

```yaml
services:
  app:
    extra_hosts:
      - "db:172.18.0.2"        # Static IP
      - "redis:172.18.0.3"
```

## Application Configuration

### Node.js

```dockerfile
# Increase memory limit
ENV NODE_OPTIONS="--max-old-space-size=4096"

# Enable production optimizations
ENV NODE_ENV=production
```

```yaml
services:
  node-app:
    environment:
      - NODE_ENV=production
      - NODE_OPTIONS=--max-old-space-size=4096
      - UV_THREADPOOL_SIZE=16
```

### Python

```dockerfile
# Disable bytecode writing
ENV PYTHONDONTWRITEBYTECODE=1

# Unbuffered output
ENV PYTHONUNBUFFERED=1

# Optimize
ENV PYTHONOPTIMIZE=1
```

```yaml
services:
  python-app:
    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
```

### Java

```dockerfile
# JVM memory settings
ENV JAVA_OPTS="-Xms512m -Xmx2g -XX:+UseG1GC"
```

```yaml
services:
  java-app:
    environment:
      - JAVA_OPTS=-Xms512m -Xmx2g -XX:+UseG1GC -XX:MaxGCPauseMillis=200
    deploy:
      resources:
        limits:
          memory: 3G  # More than Xmx for native memory
```

### Go

```yaml
services:
  go-app:
    environment:
      - GOMAXPROCS=4
      - GOGC=100
```

## Database Performance

### PostgreSQL

```yaml
services:
  postgres:
    image: postgres:16-alpine
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=1GB
      -c work_mem=16MB
      -c maintenance_work_mem=128MB
      -c max_connections=100
    deploy:
      resources:
        limits:
          memory: 2G
    volumes:
      - postgres_data:/var/lib/postgresql/data
    tmpfs:
      - /tmp:size=100M
```

### MySQL

```yaml
services:
  mysql:
    image: mysql:8.0
    command: >
      --innodb-buffer-pool-size=512M
      --innodb-log-file-size=128M
      --max-connections=100
    deploy:
      resources:
        limits:
          memory: 1G
```

### Redis

```yaml
services:
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
      --appendfsync everysec
    deploy:
      resources:
        limits:
          memory: 300M
```

### MongoDB

```yaml
services:
  mongodb:
    image: mongo:7
    command: >
      mongod
      --wiredTigerCacheSizeGB 1
      --setParameter diagnosticDataCollectionEnabled=false
    deploy:
      resources:
        limits:
          memory: 2G
```

## Container Startup

### Health Checks

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s  # Grace period for startup
```

### Dependency Ordering

```yaml
services:
  api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

### Fast Startup

```dockerfile
# Use lightweight process manager
RUN apk add --no-cache dumb-init

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "server.js"]
```

## Logging Performance

### JSON Logging

```yaml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

### Disable Logging

```yaml
services:
  noisy-service:
    logging:
      driver: none
```

### External Logging

```yaml
services:
  app:
    logging:
      driver: fluentd
      options:
        fluentd-address: localhost:24224
        tag: myapp
```

## Scaling

### Horizontal Scaling

```yaml
services:
  api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
```

```bash
# Scale dynamically
docker compose up -d --scale api=5
```

### Load Balancing

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    depends_on:
      - api

  api:
    deploy:
      replicas: 3
    # Nginx automatically load balances to "api" hostname
```

## Monitoring

### Resource Usage

```bash
# Real-time stats
docker stats

# Specific container
docker stats mycontainer

# Formatted output
docker stats --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Events

```bash
# Watch container events
docker events

# Filter events
docker events --filter 'event=start'
```

### Health Status

```bash
# Check health
docker inspect --format='{{.State.Health.Status}}' container

# Health logs
docker inspect --format='{{json .State.Health}}' container | jq
```

## Complete Performance Configuration

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    healthcheck:
      test: ["CMD", "nginx", "-t"]
      interval: 30s
      timeout: 10s

  api:
    build: ./api
    environment:
      - NODE_ENV=production
      - NODE_OPTIONS=--max-old-space-size=384
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    tmpfs:
      - /tmp:size=50M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=768MB
      -c work_mem=16MB
      -c maintenance_work_mem=64MB
    volumes:
      - postgres_data:/var/lib/postgresql/data
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --maxmemory 128mb
      --maxmemory-policy allkeys-lru
      --appendonly yes
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 192M
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s

volumes:
  postgres_data:
  redis_data:
```

## Performance Checklist

### Resources

- [ ] Set memory limits for all containers
- [ ] Set CPU limits for all containers
- [ ] Configure reservations for critical services
- [ ] Monitor resource usage

### Storage

- [ ] Use named volumes for databases
- [ ] Use tmpfs for cache/temp files
- [ ] Optimize bind mount options (macOS/Windows)

### Network

- [ ] Use internal networks where possible
- [ ] Consider host network for high-perf services
- [ ] Reduce DNS lookups with extra_hosts

### Application

- [ ] Configure language-specific optimizations
- [ ] Tune database parameters
- [ ] Configure appropriate logging

### Scaling

- [ ] Configure replicas for stateless services
- [ ] Implement health checks
- [ ] Set up load balancing

### Monitoring

- [ ] Monitor container stats
- [ ] Set up alerting
- [ ] Track health status

## Related Skills
- optimization/image-size
- optimization/build-performance
- compose/services
