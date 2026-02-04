---
name: compose-microservices
description: Microservices architecture Docker Compose templates
applies_to: docker
variables:
  - gateway_port: API Gateway port
  - services: List of microservices
---

# Microservices Docker Compose Templates

## Basic Microservices Architecture

```yaml
name: microservices

services:
  # API Gateway
  gateway:
    build: ./gateway
    ports:
      - "${GATEWAY_PORT:-8080}:8080"
    environment:
      - USER_SERVICE_URL=http://user-service:3001
      - PRODUCT_SERVICE_URL=http://product-service:3002
      - ORDER_SERVICE_URL=http://order-service:3003
      - JWT_SECRET=${JWT_SECRET}
    depends_on:
      - user-service
      - product-service
      - order-service
    networks:
      - public
      - services
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # User Service
  user-service:
    build: ./services/user
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@user-db:5432/users
      - REDIS_URL=redis://cache:6379
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672
    depends_on:
      user-db:
        condition: service_healthy
    networks:
      - services
      - user-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3001/health"]
      interval: 30s
      timeout: 10s

  user-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: users
    volumes:
      - user_db_data:/var/lib/postgresql/data
    networks:
      - user-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Product Service
  product-service:
    build: ./services/product
    environment:
      - MONGODB_URL=mongodb://product-db:27017/products
      - REDIS_URL=redis://cache:6379
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672
    depends_on:
      product-db:
        condition: service_healthy
    networks:
      - services
      - product-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3002/health"]
      interval: 30s
      timeout: 10s

  product-db:
    image: mongo:7
    volumes:
      - product_db_data:/data/db
    networks:
      - product-network
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Order Service
  order-service:
    build: ./services/order
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@order-db:5432/orders
      - USER_SERVICE_URL=http://user-service:3001
      - PRODUCT_SERVICE_URL=http://product-service:3002
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672
    depends_on:
      order-db:
        condition: service_healthy
      rabbitmq:
        condition: service_healthy
    networks:
      - services
      - order-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3003/health"]
      interval: 30s
      timeout: 10s

  order-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: orders
    volumes:
      - order_db_data:/var/lib/postgresql/data
    networks:
      - order-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Shared Infrastructure
  cache:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    networks:
      - services
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
      - "15672:15672"
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    networks:
      - services
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 30s
      timeout: 10s
      retries: 5

networks:
  public:
    # External access
  services:
    # Inter-service communication
    internal: true
  user-network:
    internal: true
  product-network:
    internal: true
  order-network:
    internal: true

volumes:
  user_db_data:
  product_db_data:
  order_db_data:
  redis_data:
  rabbitmq_data:
```

## With Traefik Gateway

```yaml
name: microservices-traefik

services:
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
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - public

  user-service:
    build: ./services/user
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@user-db:5432/users
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.user.rule=PathPrefix(`/api/users`)"
      - "traefik.http.services.user.loadbalancer.server.port=3001"
    networks:
      - public
      - user-network
    deploy:
      replicas: 2

  user-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: users
    volumes:
      - user_db_data:/var/lib/postgresql/data
    networks:
      - user-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s

  product-service:
    build: ./services/product
    environment:
      - MONGODB_URL=mongodb://product-db:27017/products
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.product.rule=PathPrefix(`/api/products`)"
      - "traefik.http.services.product.loadbalancer.server.port=3002"
    networks:
      - public
      - product-network
    deploy:
      replicas: 2

  product-db:
    image: mongo:7
    volumes:
      - product_db_data:/data/db
    networks:
      - product-network

  order-service:
    build: ./services/order
    environment:
      - DATABASE_URL=postgres://postgres:${DB_PASSWORD}@order-db:5432/orders
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.order.rule=PathPrefix(`/api/orders`)"
      - "traefik.http.services.order.loadbalancer.server.port=3003"
    networks:
      - public
      - order-network
    deploy:
      replicas: 2

  order-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: orders
    volumes:
      - order_db_data:/var/lib/postgresql/data
    networks:
      - order-network

networks:
  public:
  user-network:
    internal: true
  product-network:
    internal: true
  order-network:
    internal: true

volumes:
  user_db_data:
  product_db_data:
  order_db_data:
```

## With Service Discovery (Consul)

```yaml
name: microservices-consul

services:
  consul:
    image: consul:1.15
    ports:
      - "8500:8500"
    command: agent -server -bootstrap -ui -client=0.0.0.0
    volumes:
      - consul_data:/consul/data
    networks:
      - infrastructure

  user-service:
    build: ./services/user
    environment:
      - CONSUL_HTTP_ADDR=consul:8500
      - SERVICE_NAME=user-service
      - SERVICE_PORT=3001
    depends_on:
      - consul
    networks:
      - infrastructure
      - services

  product-service:
    build: ./services/product
    environment:
      - CONSUL_HTTP_ADDR=consul:8500
      - SERVICE_NAME=product-service
      - SERVICE_PORT=3002
    depends_on:
      - consul
    networks:
      - infrastructure
      - services

  order-service:
    build: ./services/order
    environment:
      - CONSUL_HTTP_ADDR=consul:8500
      - SERVICE_NAME=order-service
      - SERVICE_PORT=3003
    depends_on:
      - consul
    networks:
      - infrastructure
      - services

networks:
  infrastructure:
  services:
    internal: true

volumes:
  consul_data:
```

## With Observability Stack

```yaml
name: microservices-observability

services:
  # ... (previous service definitions) ...

  # Jaeger for Distributed Tracing
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"  # UI
      - "6831:6831/udp"  # Jaeger thrift
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    networks:
      - monitoring

  # Prometheus for Metrics
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

  # Grafana for Dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - monitoring
    depends_on:
      - prometheus

  # Loki for Logs
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml:ro
      - loki_data:/loki
    networks:
      - monitoring
    command: -config.file=/etc/loki/local-config.yaml

  # Promtail for Log Collection
  promtail:
    image: grafana/promtail:latest
    volumes:
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - monitoring
    command: -config.file=/etc/promtail/config.yml

networks:
  monitoring:
    internal: true

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

## Event-Driven Architecture

```yaml
name: microservices-events

services:
  # Kafka
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
    networks:
      - messaging

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    networks:
      - messaging
      - services

  # Services communicate via Kafka events
  user-service:
    build: ./services/user
    environment:
      - KAFKA_BROKERS=kafka:9092
      - KAFKA_GROUP_ID=user-service
    depends_on:
      - kafka
    networks:
      - services
      - messaging

  notification-service:
    build: ./services/notification
    environment:
      - KAFKA_BROKERS=kafka:9092
      - KAFKA_GROUP_ID=notification-service
      - KAFKA_TOPICS=user.created,order.completed
    depends_on:
      - kafka
    networks:
      - services
      - messaging

  analytics-service:
    build: ./services/analytics
    environment:
      - KAFKA_BROKERS=kafka:9092
      - KAFKA_GROUP_ID=analytics-service
    depends_on:
      - kafka
    networks:
      - services
      - messaging

networks:
  messaging:
    internal: true
  services:
    internal: true
```

## .env Template

```bash
# .env.example

# Gateway
GATEWAY_PORT=8080

# Database
DB_PASSWORD=

# Security
JWT_SECRET=

# Monitoring
GRAFANA_PASSWORD=admin

# Kafka
KAFKA_BROKERS=kafka:9092
```

## Usage

```bash
# Start all services
docker compose up -d

# Scale specific service
docker compose up -d --scale user-service=3

# View service logs
docker compose logs -f user-service

# Check service health
docker compose ps

# Stop all services
docker compose down

# Stop and remove volumes
docker compose down -v
```
