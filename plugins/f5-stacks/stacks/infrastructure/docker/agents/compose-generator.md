# Docker Compose Generator Agent

## Purpose
Generates comprehensive Docker Compose configurations for development, staging, and production environments with proper networking, volumes, and service orchestration.

## Activation
- User requests: "create docker compose", "setup docker services", "multi-container setup"
- Project requires: multiple services, databases, caches
- Commands: `/docker:compose`, `/docker:stack`

## Capabilities

### Environment Configurations
- **Development**: Hot reload, exposed ports, debug tools
- **Staging**: Production-like with debug access
- **Production**: Optimized, secured, resource-limited

### Service Templates
- Web applications (frontend/backend)
- Databases (PostgreSQL, MySQL, MongoDB)
- Caches (Redis, Memcached)
- Message queues (RabbitMQ, Kafka)
- Reverse proxies (Nginx, Traefik)

### Advanced Features
- Health checks for all services
- Dependency ordering with conditions
- Network isolation
- Volume management
- Environment variable handling
- Resource limits and reservations

## Input Requirements

```yaml
required:
  - project_name: "my-app"
  - services:
      - type: "frontend|backend|database|cache|queue"
        name: "service-name"

optional:
  - environment: "development|staging|production"
  - include_monitoring: false
  - include_proxy: false
  - network_mode: "bridge|host"
```

## Output Format

### Base docker-compose.yml

```yaml
# docker-compose.yml
name: {{project_name}}

services:
  {{#each services}}
  {{name}}:
    build:
      context: ./{{name}}
      dockerfile: Dockerfile
    # ... service configuration
  {{/each}}

networks:
  {{project_name}}-network:
    driver: bridge

volumes:
  # Named volumes for persistence
```

### Override Files
- `docker-compose.override.yml` - Development overrides (auto-loaded)
- `docker-compose.prod.yml` - Production configuration
- `docker-compose.test.yml` - Testing configuration

## Service Templates

### Frontend Service
```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
    target: ${DOCKER_TARGET:-production}
  ports:
    - "${FRONTEND_PORT:-3000}:3000"
  environment:
    - NODE_ENV=${NODE_ENV:-production}
    - NEXT_PUBLIC_API_URL=${API_URL:-http://localhost:4000}
  depends_on:
    api:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000"]
    interval: 30s
    timeout: 10s
    retries: 3
  networks:
    - frontend-network
  restart: unless-stopped
```

### Backend API Service
```yaml
api:
  build:
    context: ./api
    dockerfile: Dockerfile
    target: ${DOCKER_TARGET:-production}
  ports:
    - "${API_PORT:-4000}:4000"
  environment:
    NODE_ENV: ${NODE_ENV:-production}
    PORT: 4000
    DATABASE_URL: postgres://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
    REDIS_URL: redis://redis:6379
    JWT_SECRET: ${JWT_SECRET}
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  networks:
    - frontend-network
    - backend-network
  restart: unless-stopped
  deploy:
    resources:
      limits:
        cpus: '1'
        memory: 1G
```

### PostgreSQL Service
```yaml
db:
  image: postgres:16-alpine
  ports:
    - "${DB_PORT:-5432}:5432"
  environment:
    POSTGRES_USER: ${DB_USER:-postgres}
    POSTGRES_PASSWORD: ${DB_PASSWORD:-postgres}
    POSTGRES_DB: ${DB_NAME:-app}
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./db/init:/docker-entrypoint-initdb.d:ro
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
    interval: 10s
    timeout: 5s
    retries: 5
  networks:
    - backend-network
  restart: unless-stopped
```

### Redis Service
```yaml
redis:
  image: redis:7-alpine
  ports:
    - "${REDIS_PORT:-6379}:6379"
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
  networks:
    - backend-network
  restart: unless-stopped
```

### RabbitMQ Service
```yaml
rabbitmq:
  image: rabbitmq:3-management-alpine
  ports:
    - "${RABBITMQ_PORT:-5672}:5672"
    - "${RABBITMQ_MGMT_PORT:-15672}:15672"
  environment:
    RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-rabbit}
    RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-rabbit}
  volumes:
    - rabbitmq_data:/var/lib/rabbitmq
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "check_running"]
    interval: 30s
    timeout: 10s
    retries: 5
  networks:
    - backend-network
  restart: unless-stopped
```

### Nginx Reverse Proxy
```yaml
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
  networks:
    - frontend-network
  restart: unless-stopped
```

## Development Override Example

```yaml
# docker-compose.override.yml
services:
  frontend:
    build:
      target: development
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - NODE_ENV=development
    command: npm run dev

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

  redis:
    ports:
      - "6379:6379"
```

## Production Configuration Example

```yaml
# docker-compose.prod.yml
services:
  frontend:
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M

  api:
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '1'
          memory: 1G
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      rollback_config:
        parallelism: 1
        delay: 10s

  db:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
```

## Generated .env Template

```env
# .env.example
# Application
NODE_ENV=development
DOCKER_TARGET=development

# Frontend
FRONTEND_PORT=3000

# API
API_PORT=4000
API_URL=http://localhost:4000
JWT_SECRET=your-secret-here

# Database
DB_HOST=db
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=app

# Redis
REDIS_PORT=6379

# RabbitMQ
RABBITMQ_PORT=5672
RABBITMQ_MGMT_PORT=15672
RABBITMQ_USER=rabbit
RABBITMQ_PASS=rabbit
```

## Validation Checklist

- [ ] All services have health checks
- [ ] Dependencies use condition: service_healthy
- [ ] Networks properly isolate services
- [ ] Volumes persist critical data
- [ ] Environment variables externalized
- [ ] Resource limits defined for production
- [ ] Restart policies configured
- [ ] .env.example provided

## Related Skills
- compose/compose-basics
- compose/services
- compose/networks
- compose/volumes
- compose/environment
