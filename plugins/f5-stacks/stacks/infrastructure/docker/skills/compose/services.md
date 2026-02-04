---
name: compose-services
description: Docker Compose service configuration
applies_to: docker
---

# Docker Compose Services

## Service Types

### Application Services

```yaml
services:
  # Frontend (React/Next.js)
  frontend:
    build:
      context: ./frontend
      target: ${BUILD_TARGET:-production}
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api:4000
    depends_on:
      api:
        condition: service_healthy

  # Backend API
  api:
    build:
      context: ./api
      target: ${BUILD_TARGET:-production}
    ports:
      - "4000:4000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Background Worker
  worker:
    build:
      context: ./api
    command: ["node", "dist/worker.js"]
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    deploy:
      replicas: 2
```

### Database Services

```yaml
services:
  # PostgreSQL
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
      POSTGRES_DB: ${DB_NAME:-app}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    ports:
      - "${DB_PORT:-5432}:5432"

  # MySQL
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-app}
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      timeout: 5s
      retries: 5

  # MongoDB
  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: ${MONGO_USER:-root}
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD:-password}
      MONGO_INITDB_DATABASE: ${MONGO_DB:-app}
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5
```

### Cache Services

```yaml
services:
  # Redis
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Memcached
  memcached:
    image: memcached:1.6-alpine
    command: memcached -m 256
```

### Message Queue Services

```yaml
services:
  # RabbitMQ
  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-rabbit}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-rabbit}
    ports:
      - "5672:5672"    # AMQP
      - "15672:15672"  # Management UI
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 30s
      timeout: 10s
      retries: 5

  # Apache Kafka
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
```

### Reverse Proxy Services

```yaml
services:
  # Nginx
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - frontend
      - api

  # Traefik
  traefik:
    image: traefik:v3.0
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
```

### Monitoring Services

```yaml
services:
  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "9090:9090"

  # Grafana
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
    ports:
      - "3001:3000"
    depends_on:
      - prometheus
```

## Build Configuration

### Build Options

```yaml
services:
  api:
    build:
      # Build context
      context: ./api

      # Dockerfile location
      dockerfile: Dockerfile.prod

      # Target stage (multi-stage)
      target: production

      # Build arguments
      args:
        - NODE_VERSION=20
        - BUILD_DATE=${BUILD_DATE}

      # Labels
      labels:
        - "com.example.version=1.0"

      # Cache from
      cache_from:
        - myregistry/myapp:cache

      # Platform
      platform: linux/amd64

      # Network mode
      network: host

      # Additional build context
      additional_contexts:
        - shared=../shared
```

### Development Build

```yaml
services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api:/app
      - /app/node_modules  # Preserve node_modules
    command: npm run dev
    environment:
      - NODE_ENV=development
```

## Deploy Configuration

### Replicas and Resources

```yaml
services:
  api:
    deploy:
      # Number of instances
      replicas: 3

      # Resource limits
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M

      # Update configuration
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        order: start-first

      # Rollback configuration
      rollback_config:
        parallelism: 1
        delay: 10s

      # Restart policy
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s

      # Placement constraints
      placement:
        constraints:
          - node.role == worker
          - node.labels.type == compute
```

## Service Dependencies

### Basic Dependencies

```yaml
services:
  api:
    depends_on:
      - db
      - redis
```

### With Conditions (Recommended)

```yaml
services:
  api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      migrations:
        condition: service_completed_successfully
```

### Startup Order

```
1. db starts (waits for healthy)
2. redis starts (waits for healthy)
3. migrations runs (waits for completion)
4. api starts
```

## Service Profiles

```yaml
services:
  api:
    # No profile - always runs

  debug:
    profiles:
      - debug
    image: busybox
    command: ["sleep", "infinity"]

  admin:
    profiles:
      - admin
    build: ./admin

  test:
    profiles:
      - test
    build:
      context: ./api
      target: test
    command: npm test
```

```bash
# Run default services
docker compose up

# Run with debug
docker compose --profile debug up

# Run multiple profiles
docker compose --profile debug --profile admin up
```

## Service Labels (Traefik Example)

```yaml
services:
  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.example.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls=true"
      - "traefik.http.services.api.loadbalancer.server.port=4000"
```

## Related Skills
- compose/compose-basics
- compose/networks
- compose/volumes
- compose/environment
