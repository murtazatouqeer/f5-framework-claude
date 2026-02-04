---
name: docker-network-types
description: Docker network drivers and their use cases
applies_to: docker
---

# Docker Network Types

## Network Drivers Overview

| Driver | Use Case | Isolation | Performance |
|--------|----------|-----------|-------------|
| bridge | Default, container communication | Container-level | Good |
| host | Maximum performance | None | Best |
| none | Complete isolation | Complete | N/A |
| overlay | Multi-host (Swarm) | Container-level | Good |
| macvlan | Legacy integration | Network-level | Good |
| ipvlan | IP-based routing | Network-level | Good |

## Bridge Network (Default)

### Default Bridge

```bash
# Containers use default bridge by default
docker run -d --name web nginx

# Inspect default bridge
docker network inspect bridge

# Containers on default bridge use IP addresses (no DNS)
docker exec web ping 172.17.0.3
```

### User-Defined Bridge (Recommended)

```bash
# Create custom bridge network
docker network create my-network

# Run containers on custom network
docker run -d --name api --network my-network myapi
docker run -d --name db --network my-network postgres

# Containers can use DNS names
docker exec api ping db
```

### Bridge Network Options

```bash
# Create with specific subnet
docker network create \
  --driver bridge \
  --subnet 172.28.0.0/16 \
  --ip-range 172.28.5.0/24 \
  --gateway 172.28.0.1 \
  my-network

# With additional options
docker network create \
  --driver bridge \
  --opt com.docker.network.bridge.name=my-bridge \
  --opt com.docker.network.bridge.enable_ip_masquerade=true \
  --opt com.docker.network.bridge.enable_icc=true \
  my-network
```

### Compose Bridge Network

```yaml
services:
  api:
    networks:
      - backend

  db:
    networks:
      - backend

networks:
  backend:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

## Host Network

Direct access to host's network stack:

```bash
# Use host network
docker run -d --network host nginx

# No port mapping needed - uses host ports directly
# Container sees host's network interfaces
```

### Use Cases

- Maximum network performance
- Applications that need to see all network traffic
- Services that bind to many ports
- Legacy applications expecting host networking

### Limitations

- No network isolation
- Port conflicts possible
- Not available on Docker Desktop (macOS/Windows)

```yaml
# Compose host network
services:
  app:
    network_mode: host
```

## None Network

Complete network isolation:

```bash
# No networking
docker run -d --network none alpine sleep infinity

# Container has only loopback interface
docker exec <container> ip addr
# Only shows: lo (127.0.0.1)
```

### Use Cases

- Security-sensitive batch jobs
- Containers that don't need networking
- Testing without network dependencies

```yaml
# Compose none network
services:
  processor:
    network_mode: none
```

## Overlay Network (Swarm Mode)

Multi-host networking for Docker Swarm:

```bash
# Initialize swarm
docker swarm init

# Create overlay network
docker network create \
  --driver overlay \
  --attachable \
  my-overlay

# Services can communicate across hosts
docker service create \
  --name api \
  --network my-overlay \
  myapi
```

### Overlay Options

```bash
# Encrypted overlay network
docker network create \
  --driver overlay \
  --opt encrypted \
  --attachable \
  secure-overlay

# With specific subnet
docker network create \
  --driver overlay \
  --subnet 10.0.9.0/24 \
  --attachable \
  my-overlay
```

## Macvlan Network

Assign MAC addresses to containers:

```bash
# Create macvlan network
docker network create \
  --driver macvlan \
  --subnet 192.168.1.0/24 \
  --gateway 192.168.1.1 \
  -o parent=eth0 \
  my-macvlan

# Container gets IP on physical network
docker run -d \
  --network my-macvlan \
  --ip 192.168.1.100 \
  nginx
```

### Use Cases

- Legacy applications expecting physical network
- Applications requiring unique MAC addresses
- Integration with existing VLANs

### Macvlan Modes

```bash
# Bridge mode (default)
docker network create \
  --driver macvlan \
  -o macvlan_mode=bridge \
  -o parent=eth0 \
  --subnet 192.168.1.0/24 \
  my-macvlan

# VLAN trunk mode
docker network create \
  --driver macvlan \
  -o parent=eth0.100 \
  --subnet 192.168.100.0/24 \
  vlan100
```

## IPvlan Network

Similar to macvlan but uses same MAC:

```bash
# L2 mode (like macvlan)
docker network create \
  --driver ipvlan \
  --subnet 192.168.1.0/24 \
  -o parent=eth0 \
  my-ipvlan-l2

# L3 mode (routing mode)
docker network create \
  --driver ipvlan \
  --subnet 192.168.1.0/24 \
  -o parent=eth0 \
  -o ipvlan_mode=l3 \
  my-ipvlan-l3
```

### IPvlan vs Macvlan

| Feature | Macvlan | IPvlan |
|---------|---------|--------|
| MAC addresses | Unique per container | Shared (parent's MAC) |
| Host communication | Requires bridge | Works in L3 mode |
| VLAN support | Yes | Yes |
| Switch compatibility | May need promiscuous | Better compatibility |

## Internal Networks

Networks without external access:

```bash
# Create internal network
docker network create \
  --driver bridge \
  --internal \
  isolated-network
```

```yaml
# Compose internal network
services:
  db:
    networks:
      - internal

networks:
  internal:
    driver: bridge
    internal: true  # No external access
```

### Use Case: Database Isolation

```yaml
services:
  api:
    networks:
      - frontend
      - backend

  db:
    networks:
      - backend  # Only API can reach

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true
```

## Network Comparison

### When to Use Each Driver

```
Bridge (User-Defined):
├─ Default choice for most applications
├─ Container-to-container communication
├─ DNS-based service discovery
└─ Good isolation with connectivity

Host:
├─ Maximum network performance needed
├─ Legacy applications
├─ Many ports to expose
└─ Development/debugging

None:
├─ Security-sensitive workloads
├─ Batch processing without network
└─ Testing isolation

Overlay:
├─ Multi-host deployments
├─ Docker Swarm services
├─ Cross-datacenter communication
└─ Service mesh architectures

Macvlan/IPvlan:
├─ Integration with existing networks
├─ Legacy application requirements
├─ VLAN integration
└─ Unique IP per container needed
```

## Network Management

### Commands

```bash
# List networks
docker network ls

# Inspect network
docker network inspect my-network

# Connect container to network
docker network connect my-network container1

# Disconnect container
docker network disconnect my-network container1

# Remove network
docker network rm my-network

# Prune unused networks
docker network prune
```

### Troubleshooting

```bash
# Check container's networks
docker inspect container1 --format '{{json .NetworkSettings.Networks}}'

# Check network's containers
docker network inspect my-network --format '{{range .Containers}}{{.Name}} {{end}}'

# Test connectivity
docker exec container1 ping container2
docker exec container1 nslookup container2
```

## Best Practices

1. **Always use user-defined bridge networks** over default bridge
2. **Use internal networks** for databases and sensitive services
3. **Separate concerns** with multiple networks (frontend, backend, monitoring)
4. **Use overlay networks** for multi-host deployments
5. **Avoid host network** unless performance is critical
6. **Document network topology** in docker-compose.yml comments

## Complete Example

```yaml
services:
  # Public-facing load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    networks:
      - frontend

  # Application servers
  api:
    build: ./api
    networks:
      - frontend   # Reached by nginx
      - backend    # Reaches database
      - monitoring # Metrics collection

  # Database (isolated)
  postgres:
    image: postgres:16-alpine
    networks:
      - backend    # Only API can reach

  # Cache (isolated)
  redis:
    image: redis:7-alpine
    networks:
      - backend

  # Monitoring (separate network)
  prometheus:
    image: prom/prometheus
    networks:
      - monitoring

networks:
  frontend:
    driver: bridge
    # Public-facing network

  backend:
    driver: bridge
    internal: true  # No external access

  monitoring:
    driver: bridge
    internal: true  # Internal metrics only
```

## Related Skills
- networking/port-mapping
- networking/dns-discovery
- compose/networks
