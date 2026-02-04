---
name: docker-dns-discovery
description: Docker DNS-based service discovery and resolution
applies_to: docker
---

# Docker DNS & Service Discovery

## DNS Overview

Docker provides automatic DNS resolution for containers on user-defined networks.

### Default Bridge vs User-Defined Network

```bash
# Default bridge - NO DNS resolution
docker run -d --name web1 nginx
docker run -d --name web2 nginx
docker exec web1 ping web2  # FAILS - no DNS

# User-defined network - DNS works
docker network create mynet
docker run -d --name api --network mynet nginx
docker run -d --name db --network mynet postgres
docker exec api ping db  # WORKS - DNS resolves
```

## DNS Resolution

### Container Names

```bash
# Containers can reach each other by name
docker exec api ping db
docker exec api nslookup db
docker exec api getent hosts db
```

### Service Names (Compose)

```yaml
services:
  api:
    # Accessible as "api"

  database:
    # Accessible as "database"

  cache:
    # Accessible as "cache"
```

```bash
# From any container on same network
ping api
ping database
ping cache
```

### Network Aliases

```yaml
services:
  db-primary:
    networks:
      backend:
        aliases:
          - database
          - postgres
          - db

# Accessible as: db-primary, database, postgres, db
```

### Multiple Aliases

```bash
# Runtime alias
docker run -d \
  --name postgres \
  --network mynet \
  --network-alias db \
  --network-alias database \
  postgres
```

## DNS Configuration

### Custom DNS Servers

```bash
# Use custom DNS
docker run --dns 8.8.8.8 --dns 8.8.4.4 nginx

# DNS search domains
docker run --dns-search example.com nginx

# DNS options
docker run --dns-opt timeout:2 nginx
```

### Compose DNS Configuration

```yaml
services:
  api:
    dns:
      - 8.8.8.8
      - 8.8.4.4
    dns_search:
      - example.com
      - internal.local
    dns_opt:
      - timeout:2
      - attempts:3
```

### Daemon-Level DNS

```json
// /etc/docker/daemon.json
{
  "dns": ["8.8.8.8", "8.8.4.4"],
  "dns-search": ["example.com"],
  "dns-opts": ["ndots:1"]
}
```

## Service Discovery Patterns

### Basic Service Discovery

```yaml
services:
  api:
    environment:
      - DATABASE_HOST=db
      - REDIS_HOST=redis

  db:
    image: postgres

  redis:
    image: redis
```

### Load Balancing with Replicas

```yaml
services:
  api:
    deploy:
      replicas: 3

  worker:
    environment:
      # "api" resolves to all replicas round-robin
      - API_URL=http://api:3000
```

### Health-Aware Discovery

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    # DNS only returns healthy containers (Swarm mode)

  client:
    depends_on:
      api:
        condition: service_healthy
```

## DNS Resolution Details

### Resolution Order

```
1. /etc/hosts (container's hosts file)
2. Docker's embedded DNS (127.0.0.11)
3. External DNS servers
```

### View Container DNS

```bash
# Check DNS configuration
docker exec container cat /etc/resolv.conf

# Output:
# nameserver 127.0.0.11
# options ndots:0

# Check hosts file
docker exec container cat /etc/hosts
```

### DNS Response

```bash
# Query DNS
docker exec api nslookup db

# Returns:
# Server:    127.0.0.11
# Address:   127.0.0.11#53
# Non-authoritative answer:
# Name: db
# Address: 172.18.0.3
```

## Multi-Network Discovery

### Container on Multiple Networks

```yaml
services:
  api:
    networks:
      - frontend
      - backend
    # Can resolve containers on both networks

  web:
    networks:
      - frontend
    # Can only resolve api (both on frontend)

  db:
    networks:
      - backend
    # Can only resolve api (both on backend)

networks:
  frontend:
  backend:
```

### Network-Specific Aliases

```yaml
services:
  api:
    networks:
      frontend:
        aliases:
          - api-frontend
      backend:
        aliases:
          - api-backend
```

## Extra Hosts

### Static Host Entries

```bash
# Add host entry
docker run --add-host myhost:192.168.1.100 nginx
```

```yaml
services:
  api:
    extra_hosts:
      - "myhost:192.168.1.100"
      - "otherhost:192.168.1.101"
      - "host.docker.internal:host-gateway"  # Access host
```

### Host Access

```yaml
services:
  api:
    extra_hosts:
      # Access host machine from container
      - "host.docker.internal:host-gateway"
    environment:
      - HOST_SERVICE_URL=http://host.docker.internal:8080
```

## Service Discovery Examples

### Database Connection

```yaml
services:
  api:
    environment:
      # Use service name as host
      - DATABASE_URL=postgres://user:pass@postgres:5432/mydb
      - REDIS_URL=redis://redis:6379

  postgres:
    image: postgres:16-alpine

  redis:
    image: redis:7-alpine
```

### Microservices Communication

```yaml
services:
  gateway:
    environment:
      - USER_SERVICE_URL=http://user-service:3001
      - ORDER_SERVICE_URL=http://order-service:3002
      - PRODUCT_SERVICE_URL=http://product-service:3003

  user-service:
    # Accessible as "user-service"

  order-service:
    # Accessible as "order-service"

  product-service:
    # Accessible as "product-service"
```

### Queue Workers

```yaml
services:
  api:
    environment:
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672

  worker:
    environment:
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672

  rabbitmq:
    image: rabbitmq:3-management
```

## Round-Robin DNS

### Scaled Services

```yaml
services:
  api:
    deploy:
      replicas: 3
    # DNS returns all 3 IPs in round-robin
```

```bash
# Multiple queries return different IPs
docker exec client nslookup api
# Returns: 172.18.0.3, 172.18.0.4, 172.18.0.5

# Requests are distributed
for i in {1..10}; do
  docker exec client curl -s http://api:3000/hostname
done
```

### Task Slot Discovery (Swarm)

```bash
# Specific replica
api.1.xxx  # First replica
api.2.xxx  # Second replica
api.3.xxx  # Third replica

# VIP (Virtual IP) - load balanced
api        # Resolves to VIP
```

## Debugging DNS

### DNS Lookup Commands

```bash
# Using nslookup
docker exec container nslookup service-name

# Using dig
docker exec container dig service-name

# Using getent
docker exec container getent hosts service-name

# Using host
docker exec container host service-name
```

### Check DNS Resolution

```bash
# Test from container
docker exec api ping db
docker exec api curl http://db:5432

# Check embedded DNS
docker exec api cat /etc/resolv.conf

# Verify network connectivity
docker exec api nc -zv db 5432
```

### Common Issues

```bash
# DNS not resolving
# 1. Check if on same network
docker inspect container --format '{{json .NetworkSettings.Networks}}'

# 2. Check if using user-defined network (not default bridge)
docker network ls
docker network inspect <network>

# 3. Check service name spelling
docker compose ps

# 4. Check if target container is running
docker ps
```

## Network Troubleshooting Container

```yaml
services:
  debug:
    image: nicolaka/netshoot
    command: sleep infinity
    networks:
      - frontend
      - backend
    profiles:
      - debug
```

```bash
# Start debug container
docker compose --profile debug up -d

# Use debugging tools
docker exec debug ping api
docker exec debug nslookup api
docker exec debug dig api
docker exec debug nc -zv api 3000
docker exec debug tcpdump -i eth0
```

## Best Practices

1. **Always use user-defined networks** - default bridge has no DNS
2. **Use meaningful service names** - they become DNS names
3. **Use aliases for flexibility** - multiple names for same service
4. **Configure health checks** - ensure DNS returns healthy hosts
5. **Use environment variables** - centralize service URLs
6. **Document service dependencies** - track who talks to whom

## Complete Example

```yaml
services:
  # API Gateway - entry point
  gateway:
    build: ./gateway
    ports:
      - "80:80"
    environment:
      - USER_SERVICE=http://user-service:3001
      - PRODUCT_SERVICE=http://product-service:3002
      - ORDER_SERVICE=http://order-service:3003
    networks:
      - frontend
      - services
    depends_on:
      - user-service
      - product-service
      - order-service

  # User Service
  user-service:
    build: ./services/user
    environment:
      - DATABASE_URL=postgres://postgres:secret@user-db:5432/users
      - REDIS_URL=redis://cache:6379
    networks:
      services:
        aliases:
          - users
      user-data:
    depends_on:
      - user-db

  # User Database
  user-db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=users
      - POSTGRES_PASSWORD=secret
    networks:
      - user-data

  # Product Service
  product-service:
    build: ./services/product
    environment:
      - MONGODB_URL=mongodb://product-db:27017/products
    networks:
      services:
        aliases:
          - products
      product-data:

  # Product Database
  product-db:
    image: mongo:7
    networks:
      - product-data

  # Order Service
  order-service:
    build: ./services/order
    environment:
      - DATABASE_URL=postgres://postgres:secret@order-db:5432/orders
      - USER_SERVICE=http://user-service:3001
      - PRODUCT_SERVICE=http://product-service:3002
      - RABBITMQ_URL=amqp://rabbit:rabbit@queue:5672
    networks:
      services:
        aliases:
          - orders
      order-data:
      messaging:

  # Order Database
  order-db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=orders
      - POSTGRES_PASSWORD=secret
    networks:
      - order-data

  # Message Queue
  queue:
    image: rabbitmq:3-management
    networks:
      messaging:
        aliases:
          - rabbitmq
          - mq

  # Shared Cache
  cache:
    image: redis:7-alpine
    networks:
      - services

networks:
  frontend:
    # Public-facing
  services:
    # Inter-service communication
    internal: true
  user-data:
    # User service + DB
    internal: true
  product-data:
    # Product service + DB
    internal: true
  order-data:
    # Order service + DB
    internal: true
  messaging:
    # Message queue network
    internal: true
```

## Related Skills
- networking/network-types
- networking/port-mapping
- compose/networks
