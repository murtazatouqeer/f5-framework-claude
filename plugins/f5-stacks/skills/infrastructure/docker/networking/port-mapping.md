---
name: docker-port-mapping
description: Container port exposure and mapping configuration
applies_to: docker
---

# Docker Port Mapping

## Port Mapping Basics

### Syntax

```bash
# HOST_PORT:CONTAINER_PORT
docker run -p 8080:80 nginx

# Multiple ports
docker run -p 8080:80 -p 8443:443 nginx

# Publish all exposed ports (random host ports)
docker run -P nginx
```

### Port Format

```
[HOST_IP:]HOST_PORT:CONTAINER_PORT[/PROTOCOL]

Examples:
  80:80           # Map host 80 to container 80
  8080:80         # Map host 8080 to container 80
  127.0.0.1:80:80 # Only localhost
  80:80/tcp       # TCP only (default)
  53:53/udp       # UDP only
  53:53/tcp       # TCP
```

## Mapping Patterns

### Single Port

```bash
# Basic mapping
docker run -p 3000:3000 myapp

# Different host port
docker run -p 8080:3000 myapp

# Localhost only (secure)
docker run -p 127.0.0.1:3000:3000 myapp
```

### Port Range

```bash
# Map port range
docker run -p 8000-8010:8000-8010 myapp

# Must be same range size
docker run -p 9000-9005:8000-8005 myapp
```

### Random Host Port

```bash
# Let Docker choose host port
docker run -p 80 nginx

# Publish all EXPOSE ports with random ports
docker run -P nginx

# Check assigned port
docker port <container>
```

### Protocol Specification

```bash
# TCP (default)
docker run -p 80:80/tcp nginx

# UDP
docker run -p 53:53/udp dns-server

# Both TCP and UDP
docker run -p 53:53/tcp -p 53:53/udp dns-server
```

## Interface Binding

### All Interfaces (Default)

```bash
# Binds to 0.0.0.0 (all interfaces)
docker run -p 80:80 nginx

# Equivalent to
docker run -p 0.0.0.0:80:80 nginx
```

### Localhost Only

```bash
# Only accessible from host
docker run -p 127.0.0.1:80:80 nginx

# More secure for development
docker run -p 127.0.0.1:5432:5432 postgres
```

### Specific Interface

```bash
# Bind to specific IP
docker run -p 192.168.1.100:80:80 nginx

# Useful for multi-homed servers
```

### IPv6

```bash
# IPv6 localhost
docker run -p [::1]:80:80 nginx

# All IPv6 interfaces
docker run -p [::]:80:80 nginx
```

## Docker Compose Port Mapping

### Basic Syntax

```yaml
services:
  web:
    image: nginx
    ports:
      # Short syntax
      - "80:80"
      - "443:443"

      # Container port only (random host)
      - "3000"

      # Range
      - "8000-8010:8000-8010"
```

### Long Syntax

```yaml
services:
  web:
    image: nginx
    ports:
      - target: 80        # Container port
        published: 8080   # Host port
        protocol: tcp     # tcp or udp
        mode: host        # host or ingress (Swarm)

      - target: 443
        published: 8443
        protocol: tcp
```

### Interface Binding in Compose

```yaml
services:
  web:
    ports:
      # All interfaces
      - "80:80"

      # Localhost only
      - "127.0.0.1:3000:3000"

      # Specific IP
      - "192.168.1.100:8080:80"
```

### Environment Variable Ports

```yaml
services:
  api:
    ports:
      - "${API_PORT:-3000}:3000"

  db:
    ports:
      - "${DB_PORT:-5432}:5432"
```

## EXPOSE vs Port Mapping

### EXPOSE Instruction

```dockerfile
# Documentation only - doesn't publish ports
EXPOSE 80
EXPOSE 443
EXPOSE 3000/tcp
EXPOSE 53/udp
```

### EXPOSE Purpose

1. **Documentation**: Shows which ports the container uses
2. **Inter-container**: Allows communication between containers
3. **-P flag**: `docker run -P` publishes all EXPOSE ports

### Runtime Publishing

```bash
# EXPOSE doesn't publish ports
# Must use -p to actually map ports
docker run -p 80:80 myapp

# Publish all EXPOSE ports with random host ports
docker run -P myapp
```

## Security Considerations

### Binding to Localhost

```yaml
# Development - bind to localhost only
services:
  db:
    image: postgres
    ports:
      - "127.0.0.1:5432:5432"  # Not exposed externally
```

### Don't Expose Databases

```yaml
services:
  api:
    ports:
      - "3000:3000"  # OK to expose
    networks:
      - backend

  db:
    # NO PORTS - only accessible via network
    networks:
      - backend

networks:
  backend:
    internal: true
```

### Firewall Considerations

```bash
# Docker modifies iptables by default
# UFW rules may be bypassed

# Disable Docker's iptables management (if needed)
# /etc/docker/daemon.json
{
  "iptables": false
}
```

### Production Best Practices

```yaml
services:
  # Reverse proxy handles external traffic
  nginx:
    ports:
      - "80:80"
      - "443:443"
    networks:
      - frontend
      - backend

  # Internal services - no port exposure
  api:
    # No ports section
    networks:
      - backend

  db:
    # No ports section
    networks:
      - backend

networks:
  frontend:
  backend:
    internal: true
```

## Common Patterns

### Development Setup

```yaml
services:
  frontend:
    ports:
      - "3000:3000"

  api:
    ports:
      - "4000:4000"

  # Expose for debugging tools
  db:
    ports:
      - "127.0.0.1:5432:5432"

  redis:
    ports:
      - "127.0.0.1:6379:6379"
```

### Production Setup

```yaml
services:
  nginx:
    ports:
      - "80:80"
      - "443:443"

  # No other services expose ports
  frontend:
    networks:
      - proxy

  api:
    networks:
      - proxy
      - backend

  db:
    networks:
      - backend

networks:
  proxy:
  backend:
    internal: true
```

### Multiple Environments

```yaml
# docker-compose.yml (base)
services:
  api:
    build: ./api

# docker-compose.override.yml (development)
services:
  api:
    ports:
      - "3000:3000"
  db:
    ports:
      - "127.0.0.1:5432:5432"

# docker-compose.prod.yml (production)
services:
  api:
    # No ports - behind reverse proxy
  db:
    # No ports - internal only
```

## Port Conflicts

### Handling Conflicts

```bash
# Check what's using a port
lsof -i :3000
netstat -tulpn | grep 3000

# Use different host port
docker run -p 3001:3000 myapp

# Or stop conflicting service
```

### Dynamic Port Assignment

```bash
# Let Docker assign port
docker run -p 3000 myapp

# Get assigned port
docker port <container> 3000

# Output: 0.0.0.0:49153
```

### Using Port Variables

```yaml
services:
  api:
    ports:
      - "${API_HOST_PORT:-3000}:3000"
```

```bash
# Override port
API_HOST_PORT=4000 docker compose up
```

## Port Inspection

### Check Container Ports

```bash
# List port mappings
docker port <container>

# Specific port
docker port <container> 80

# In container details
docker inspect <container> --format '{{json .NetworkSettings.Ports}}'
```

### Check Listening Ports

```bash
# From host
docker exec <container> netstat -tlnp
docker exec <container> ss -tlnp

# Check if port is open
docker exec <container> nc -zv localhost 80
```

## Troubleshooting

### Port Not Accessible

```bash
# 1. Check container is running
docker ps

# 2. Check port mapping
docker port <container>

# 3. Check process is listening inside container
docker exec <container> netstat -tlnp

# 4. Check firewall
sudo iptables -L -n

# 5. Test from container
docker exec <container> curl localhost:80
```

### Connection Refused

```bash
# Common causes:
# 1. App binding to localhost instead of 0.0.0.0
# Fix: App must bind to 0.0.0.0 or "::"

# 2. Wrong port in mapping
# Fix: Verify container port matches app port

# 3. Firewall blocking
# Fix: Check iptables/firewalld rules
```

### Port Already in Use

```bash
# Error: bind: address already in use

# Find process using port
sudo lsof -i :3000
sudo fuser 3000/tcp

# Kill process or use different port
docker run -p 3001:3000 myapp
```

## Best Practices

1. **Use localhost binding** for sensitive services (databases, admin panels)
2. **Don't expose databases** in production - use internal networks
3. **Use reverse proxy** (nginx, traefik) as single entry point
4. **Document ports** in docker-compose.yml with comments
5. **Use environment variables** for flexible port configuration
6. **Avoid port conflicts** by planning port allocation
7. **Use internal networks** for service-to-service communication

## Complete Example

```yaml
services:
  # Single entry point - only service with external ports
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    networks:
      - frontend
    depends_on:
      - api
      - frontend

  # Frontend app - no external ports
  frontend:
    build: ./frontend
    # No ports - proxied through nginx
    networks:
      - frontend

  # API - no external ports
  api:
    build: ./api
    # No ports - proxied through nginx
    networks:
      - frontend
      - backend
    environment:
      - DATABASE_URL=postgres://db:5432/app

  # Database - no external ports, internal network only
  db:
    image: postgres:16-alpine
    # No ports in production
    networks:
      - backend
    volumes:
      - postgres_data:/var/lib/postgresql/data

  # Redis - no external ports
  redis:
    image: redis:7-alpine
    networks:
      - backend

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
- networking/network-types
- networking/dns-discovery
- compose/networks
