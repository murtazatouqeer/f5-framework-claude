---
name: docker-runtime-security
description: Docker container runtime security configuration
applies_to: docker
---

# Docker Runtime Security

## Security Principles

1. **Least privilege** - Minimum required permissions
2. **Isolation** - Container boundaries
3. **Resource limits** - Prevent DoS
4. **Read-only** - Immutable containers
5. **Network segmentation** - Limit connectivity

## User Configuration

### Run as Non-Root

```bash
# Specify user at runtime
docker run --user 1000:1000 myimage

# Use username
docker run --user appuser myimage
```

### Docker Compose

```yaml
services:
  app:
    user: "1000:1000"
    # Or
    user: appuser
```

### Block Root

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
```

## Capabilities

### Drop All, Add Required

```bash
# Drop all capabilities
docker run --cap-drop ALL myimage

# Add specific capability
docker run --cap-drop ALL --cap-add NET_BIND_SERVICE myimage
```

### Docker Compose

```yaml
services:
  app:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Bind to ports < 1024
```

### Common Capabilities

| Capability | Purpose | When Needed |
|------------|---------|-------------|
| NET_BIND_SERVICE | Bind to ports < 1024 | Web servers on port 80/443 |
| CHOWN | Change file ownership | Rarely |
| SETUID/SETGID | Change user/group | Process managers |
| SYS_PTRACE | Debug processes | Debugging only |
| NET_RAW | Raw sockets | Network tools |

### Minimal Capability Set

```yaml
services:
  web:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

  worker:
    cap_drop:
      - ALL
    # No additional capabilities needed
```

## Read-Only Container

### Basic Read-Only

```bash
docker run --read-only myimage
```

### With Writable Areas

```bash
docker run \
  --read-only \
  --tmpfs /tmp \
  --tmpfs /var/run \
  myimage
```

### Docker Compose

```yaml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp:size=100M
      - /var/run:size=10M
      - /app/cache:size=50M
```

## Resource Limits

### Memory

```bash
# Hard memory limit
docker run --memory 512m myimage

# Memory + swap
docker run --memory 512m --memory-swap 1g myimage

# Disable swap
docker run --memory 512m --memory-swap 512m myimage
```

### CPU

```bash
# CPU shares (relative weight)
docker run --cpu-shares 1024 myimage

# CPU quota (hard limit)
docker run --cpus 1.5 myimage

# Pin to specific CPUs
docker run --cpuset-cpus "0,1" myimage
```

### Docker Compose

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M
```

### Prevent Fork Bombs

```bash
# Limit number of processes
docker run --pids-limit 100 myimage
```

```yaml
services:
  app:
    pids_limit: 100
```

## Network Security

### No Network

```bash
docker run --network none myimage
```

### Internal Networks

```yaml
services:
  db:
    networks:
      - backend

networks:
  backend:
    internal: true  # No external access
```

### Disable Inter-Container Communication

```bash
# At daemon level
# /etc/docker/daemon.json
{
  "icc": false
}
```

### Localhost Binding

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"  # Only accessible from host
```

## Security Options

### No New Privileges

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
```

### Seccomp Profile

```bash
# Use default seccomp profile
docker run --security-opt seccomp=default myimage

# Use custom profile
docker run --security-opt seccomp=custom-profile.json myimage
```

```yaml
services:
  app:
    security_opt:
      - seccomp:custom-profile.json
```

### AppArmor Profile

```bash
# Use specific AppArmor profile
docker run --security-opt apparmor=docker-default myimage
```

```yaml
services:
  app:
    security_opt:
      - apparmor:docker-default
```

### SELinux

```bash
# SELinux label
docker run --security-opt label=level:s0:c100,c200 myimage
```

## Privileged Mode (Avoid)

### Never Use Privileged

```bash
# AVOID - full host access
docker run --privileged myimage

# AVOID in production
docker run --privileged -v /:/host myimage
```

### Alternatives to Privileged

```yaml
# Instead of privileged, use specific capabilities
services:
  app:
    cap_add:
      - SYS_PTRACE  # For debugging
    # NOT: privileged: true
```

## Host Namespaces (Avoid)

### Avoid Host Namespaces

```bash
# AVOID - shared host network
docker run --network host myimage

# AVOID - shared host PID namespace
docker run --pid host myimage

# AVOID - shared host IPC namespace
docker run --ipc host myimage
```

## Device Access

### Limit Device Access

```bash
# Don't expose unnecessary devices
# AVOID
docker run --device /dev/sda myimage

# If needed, use specific device
docker run --device /dev/video0 myimage
```

### Device Cgroup Rules

```yaml
services:
  app:
    device_cgroup_rules:
      - 'c 1:3 mr'  # /dev/null read
      - 'c 1:5 mr'  # /dev/zero read
```

## Syscall Filtering

### Default Seccomp Profile

Docker's default seccomp profile blocks dangerous syscalls:
- `kexec_load` - Load new kernel
- `ptrace` - Debug processes
- `reboot` - Reboot system
- `mount` - Mount filesystems

### Custom Seccomp Profile

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64"],
  "syscalls": [
    {
      "names": ["read", "write", "exit", "exit_group"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

## Complete Secure Runtime

```yaml
services:
  app:
    image: myapp:latest

    # User configuration
    user: "1000:1000"

    # Read-only filesystem
    read_only: true
    tmpfs:
      - /tmp:size=50M
      - /var/run:size=10M

    # Capabilities
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE

    # Security options
    security_opt:
      - no-new-privileges:true
      - seccomp:seccomp-profile.json

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

    # Process limit
    pids_limit: 100

    # Network isolation
    networks:
      - internal

    # Health check
    healthcheck:
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine

    # Non-root user
    user: postgres

    # Read-only with data volume
    read_only: true
    tmpfs:
      - /tmp:size=50M
      - /var/run/postgresql:size=10M
    volumes:
      - postgres_data:/var/lib/postgresql/data

    # Minimal capabilities
    cap_drop:
      - ALL

    # Security options
    security_opt:
      - no-new-privileges:true

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G

    # Internal network only
    networks:
      - internal
    # No exposed ports

networks:
  internal:
    internal: true

volumes:
  postgres_data:
```

## Runtime Security Checklist

### Container Configuration

- [ ] Run as non-root user
- [ ] Drop all capabilities, add only needed
- [ ] Enable no-new-privileges
- [ ] Use read-only filesystem
- [ ] Set resource limits (CPU, memory, PIDs)
- [ ] Use tmpfs for writable areas

### Network Security

- [ ] Use internal networks for databases
- [ ] Don't expose unnecessary ports
- [ ] Bind to localhost for development
- [ ] Avoid host network mode

### Security Options

- [ ] Enable seccomp (default profile minimum)
- [ ] Consider AppArmor/SELinux profiles
- [ ] Never use privileged mode in production
- [ ] Avoid host namespace sharing

### Monitoring

- [ ] Enable health checks
- [ ] Configure logging
- [ ] Monitor resource usage
- [ ] Audit container events

## Related Skills
- security/image-security
- security/secrets-management
- networking/network-types
- compose/networks
