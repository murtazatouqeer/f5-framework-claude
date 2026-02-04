---
name: compose-fullstack
description: Full-stack application Docker Compose templates
applies_to: docker
variables:
  - frontend_port: Frontend application port
  - backend_port: Backend API port
  - db_type: postgresql, mysql, mongodb
---

# Full-Stack Docker Compose Templates

## Basic Full-Stack (React + Node.js + PostgreSQL)

```yaml
# docker-compose.yml
name: fullstack-app

services:
  # Frontend (React/Next.js)
  frontend:
    build:
      context: ./frontend
      target: production
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:${BACKEND_PORT:-4000}
    depends_on:
      - api
    networks:
      - frontend

  # Backend API (Node.js)
  api:
    build:
      context: ./backend
      target: production
    ports:
      - "${BACKEND_PORT:-4000}:4000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://${DB_USER:-postgres}:${DB_PASSWORD}@db:5432/${DB_NAME:-app}
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Database
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD required}
      POSTGRES_DB: ${DB_NAME:-app}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Cache
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
  backend:
    internal: true

volumes:
  postgres_data:
  redis_data:
```

## With Nginx Reverse Proxy

```yaml
name: fullstack-nginx

services:
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
      - frontend
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      target: production
    networks:
      - frontend
    restart: unless-stopped

  api:
    build:
      context: ./backend
      target: production
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@db:5432/app
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - frontend
      - backend
    restart: unless-stopped

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend
    restart: unless-stopped

networks:
  frontend:
  backend:
    internal: true

volumes:
  postgres_data:
  redis_data:
```

## With Background Worker

```yaml
name: fullstack-worker

services:
  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - api
    networks:
      - frontend

  api:
    build:
      context: ./backend
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@db:5432/app
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    networks:
      - frontend
      - backend

  worker:
    build:
      context: ./backend
    command: ["node", "dist/worker.js"]
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@db:5432/app
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672
    depends_on:
      - db
      - redis
      - rabbitmq
    networks:
      - backend
    deploy:
      replicas: 2

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s

  rabbitmq:
    image: rabbitmq:3-management-alpine
    environment:
      RABBITMQ_DEFAULT_USER: rabbit
      RABBITMQ_DEFAULT_PASS: rabbit
    ports:
      - "15672:15672"  # Management UI
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - backend
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  frontend:
  backend:
    internal: true

volumes:
  postgres_data:
  redis_data:
  rabbitmq_data:
```

## With Monitoring

```yaml
name: fullstack-monitored

services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    networks:
      - frontend
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=3000"

  api:
    build: ./backend
    ports:
      - "4000:4000"
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@db:5432/app
    networks:
      - frontend
      - backend
      - monitoring
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=4000"

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: app
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    networks:
      - monitoring
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - monitoring
    depends_on:
      - prometheus

networks:
  frontend:
  backend:
    internal: true
  monitoring:
    internal: true

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

## Python + Vue + MongoDB

```yaml
name: python-vue-mongo

services:
  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - api
    networks:
      - frontend

  api:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://root:${MONGO_PASSWORD}@mongodb:27017/app?authSource=admin
      - REDIS_URL=redis://redis:6379
    depends_on:
      mongodb:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: ${MONGO_PASSWORD}
      MONGO_INITDB_DATABASE: app
    volumes:
      - mongo_data:/data/db
      - ./db/init-mongo.js:/docker-entrypoint-initdb.d/init-mongo.js:ro
    networks:
      - backend
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s

networks:
  frontend:
  backend:
    internal: true

volumes:
  mongo_data:
  redis_data:
```

## .env Template

```bash
# .env.example

# Application
NODE_ENV=production
FRONTEND_PORT=3000
BACKEND_PORT=4000

# Database
DB_USER=postgres
DB_PASSWORD=
DB_NAME=app

# MongoDB (if using)
MONGO_PASSWORD=

# Security
JWT_SECRET=

# Monitoring
GRAFANA_PASSWORD=admin
```

## nginx.conf Example

```nginx
# nginx/nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream frontend {
        server frontend:3000;
    }

    upstream api {
        server api:4000;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # API
        location /api/ {
            proxy_pass http://api/;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket support
        location /ws/ {
            proxy_pass http://api/ws/;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
    }
}
```

## Usage

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Scale workers
docker compose up -d --scale worker=3

# Production deployment
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Stop and clean
docker compose down -v
```
