---
name: compose-networks
description: Docker Compose networking configuration
applies_to: docker
---

# Docker Compose Networks

## Default Network

Docker Compose creates a default network for all services:

```yaml
# All services automatically connected to default network
services:
  api:
    image: myapi
  db:
    image: postgres

# api can reach db at hostname "db"
```

## Custom Networks

### Basic Network Definition

```yaml
services:
  api:
    networks:
      - frontend
      - backend

  db:
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
```

### Network Isolation

```yaml
services:
  # Public-facing
  nginx:
    networks:
      - frontend

  # API server
  api:
    networks:
      - frontend  # Can be reached by nginx
      - backend   # Can reach database

  # Database (isolated)
  db:
    networks:
      - backend   # Only API can reach it

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

## Network Drivers

### Bridge (Default)

```yaml
networks:
  my-network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: my-bridge
```

### Host

```yaml
services:
  api:
    network_mode: host  # Use host network directly
```

### None

```yaml
services:
  isolated:
    network_mode: none  # No networking
```

### External Network

```yaml
networks:
  existing-network:
    external: true
    name: my-existing-network

services:
  api:
    networks:
      - existing-network
```

## Network Configuration

### IP Address Management

```yaml
networks:
  app-network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.28.0.0/16
          ip_range: 172.28.5.0/24
          gateway: 172.28.0.1
```

### Static IP Assignment

```yaml
services:
  api:
    networks:
      app-network:
        ipv4_address: 172.28.5.10

networks:
  app-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
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

  db-replica:
    networks:
      backend:
        aliases:
          - database-replica

# Both can be reached at their aliases
# Primary: database, postgres, db-primary
# Replica: database-replica, db-replica
```

## Service Discovery

### DNS Resolution

```yaml
services:
  api:
    networks:
      - backend
    # Can reach other services by name:
    # - db:5432
    # - redis:6379
    # - cache:11211

  db:
    networks:
      - backend

  redis:
    networks:
      - backend
```

### Custom DNS

```yaml
services:
  api:
    dns:
      - 8.8.8.8
      - 8.8.4.4
    dns_search:
      - example.com
```

## Network Patterns

### Frontend/Backend Isolation

```yaml
services:
  nginx:
    image: nginx
    ports:
      - "80:80"
    networks:
      - frontend
    depends_on:
      - api

  api:
    build: ./api
    networks:
      - frontend
      - backend
    depends_on:
      - db

  db:
    image: postgres
    networks:
      - backend
    # Not exposed to frontend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

### Microservices Pattern

```yaml
services:
  gateway:
    networks:
      - public
      - services

  user-service:
    networks:
      - services
      - user-db

  order-service:
    networks:
      - services
      - order-db

  user-db:
    networks:
      - user-db

  order-db:
    networks:
      - order-db

networks:
  public:
    # External access
  services:
    # Inter-service communication
    internal: true
  user-db:
    internal: true
  order-db:
    internal: true
```

### Shared Database Network

```yaml
services:
  api-1:
    networks:
      - api-network
      - shared-db

  api-2:
    networks:
      - api-network
      - shared-db

  database:
    networks:
      - shared-db

networks:
  api-network:
  shared-db:
    internal: true
```

## Port Exposure vs Networks

### Internal Communication (Use Networks)

```yaml
services:
  api:
    # No ports needed for internal communication
    networks:
      - backend

  db:
    # No ports exposed
    networks:
      - backend

# api connects to db:5432 via network
```

### External Access (Use Ports)

```yaml
services:
  api:
    ports:
      - "4000:4000"  # Expose to host
    networks:
      - backend

  db:
    # ports:
    #   - "5432:5432"  # Don't expose database!
    networks:
      - backend
```

### Development (Expose for Tools)

```yaml
# docker-compose.override.yml
services:
  db:
    ports:
      - "5432:5432"  # Expose for local dev tools
```

## Network Debugging

### Inspect Network

```bash
# List networks
docker network ls

# Inspect network
docker network inspect myapp_backend

# Check connected containers
docker network inspect myapp_backend --format '{{range .Containers}}{{.Name}}{{end}}'
```

### Test Connectivity

```bash
# Exec into container
docker compose exec api /bin/sh

# Test connection
ping db
nslookup db
wget -O- http://db:5432
nc -zv db 5432
```

### Debug DNS

```bash
# Check DNS configuration
docker compose exec api cat /etc/resolv.conf

# Test DNS resolution
docker compose exec api nslookup db
```

## Best Practices

1. **Use internal networks** for databases and caches
2. **Don't expose ports** unless needed externally
3. **Use network aliases** for flexible service names
4. **Separate frontend/backend** networks
5. **Use health checks** before connecting services
6. **Document network topology** in comments

## Complete Example

```yaml
# docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    networks:
      - frontend
    depends_on:
      - api

  api:
    build: ./api
    networks:
      - frontend
      - backend
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

  worker:
    build: ./api
    command: ["node", "worker.js"]
    networks:
      - backend
    depends_on:
      - redis

  db:
    image: postgres:16-alpine
    networks:
      backend:
        aliases:
          - database
          - postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    networks:
      - backend
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access

volumes:
  postgres_data:
```

## Related Skills
- compose/compose-basics
- networking/network-types
- networking/dns-discovery
