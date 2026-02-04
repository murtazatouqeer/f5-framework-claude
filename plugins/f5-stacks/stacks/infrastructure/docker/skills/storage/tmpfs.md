---
name: docker-tmpfs
description: Docker tmpfs mounts for in-memory temporary storage
applies_to: docker
---

# Docker tmpfs Mounts

## tmpfs Overview

tmpfs mounts are stored in host memory (RAM) and never written to the host filesystem.

### Characteristics

| Feature | tmpfs |
|---------|-------|
| Storage location | Host memory (RAM) |
| Persistence | None (lost on restart) |
| Performance | Fastest |
| Security | Data not on disk |
| Size limit | Configurable |

### When to Use tmpfs

- **Sensitive data**: Credentials, tokens, temporary secrets
- **Cache**: Application cache that can be rebuilt
- **Temp files**: Build artifacts, session data
- **Performance**: Fastest possible I/O
- **Security**: Data must not persist

## Basic Syntax

### CLI

```bash
# Simple tmpfs mount
docker run --tmpfs /tmp nginx

# With options
docker run --tmpfs /tmp:size=100m,mode=1777 nginx

# Using --mount
docker run \
  --mount type=tmpfs,destination=/tmp,tmpfs-size=100m,tmpfs-mode=1777 \
  nginx
```

### Docker Compose

```yaml
services:
  app:
    tmpfs:
      - /tmp
      - /app/cache

    # Or with options
    tmpfs:
      - /tmp:size=100M,mode=1777
```

### Long Syntax (Compose)

```yaml
services:
  app:
    volumes:
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 104857600  # 100MB in bytes
          mode: 1777
```

## tmpfs Options

### Size Limit

```bash
# CLI
docker run --tmpfs /tmp:size=100m nginx

# Compose
services:
  app:
    tmpfs:
      - /tmp:size=100M
```

```yaml
# Long syntax
volumes:
  - type: tmpfs
    target: /tmp
    tmpfs:
      size: 104857600  # bytes
```

### Mode (Permissions)

```bash
# CLI - set permissions
docker run --tmpfs /tmp:mode=1777 nginx

# Common modes:
# 1777 - sticky bit, world writable (like /tmp)
# 0755 - owner rwx, others rx
# 0700 - owner only
```

```yaml
services:
  app:
    tmpfs:
      - /tmp:mode=1777
      - /app/private:mode=0700
```

### Combined Options

```bash
# Size and mode
docker run --tmpfs /tmp:size=50m,mode=1777 nginx
```

```yaml
services:
  app:
    tmpfs:
      - /tmp:size=100M,mode=1777
      - /app/cache:size=50M,mode=0755
```

## Common Patterns

### Application Cache

```yaml
services:
  api:
    build: ./api
    tmpfs:
      - /app/cache:size=100M
    environment:
      - CACHE_DIR=/app/cache
```

### Session Storage

```yaml
services:
  web:
    image: php:8-apache
    tmpfs:
      - /tmp:size=50M
      - /var/lib/php/sessions:size=10M,mode=0700
```

### Build Artifacts

```yaml
services:
  builder:
    build: .
    tmpfs:
      - /tmp:size=500M
      - /app/dist:size=200M
    command: npm run build
```

### Sensitive Data

```yaml
services:
  app:
    tmpfs:
      # Credentials loaded at runtime - never on disk
      - /app/secrets:size=10M,mode=0700
    environment:
      - SECRETS_DIR=/app/secrets
```

### Test Environment

```yaml
services:
  test:
    build:
      target: test
    tmpfs:
      - /tmp:size=100M
      - /app/coverage:size=50M
      - /app/.cache:size=100M
    command: npm test
```

## tmpfs vs Named Volume vs Bind Mount

### Performance Comparison

```yaml
services:
  benchmark:
    volumes:
      # Slowest - network/disk
      - nfs_data:/data/nfs

      # Medium - host disk
      - ./data:/data/bind

      # Fast - Docker managed
      - named_data:/data/volume

    tmpfs:
      # Fastest - RAM
      - /data/tmpfs:size=100M
```

### Use Case Decision

```yaml
services:
  app:
    volumes:
      # Persistent database → Named volume
      - postgres_data:/var/lib/postgresql/data

      # Development source → Bind mount
      - ./src:/app/src

    tmpfs:
      # Temporary cache → tmpfs
      - /app/cache

      # Sensitive temp data → tmpfs
      - /tmp/secrets
```

## Security Considerations

### Sensitive Data

```yaml
services:
  app:
    tmpfs:
      # Sensitive data never touches disk
      - /app/credentials:size=10M,mode=0600
      - /tmp/tokens:size=5M,mode=0600
```

### Secure Defaults

```yaml
services:
  secure-app:
    tmpfs:
      # Restrict permissions
      - /tmp:size=50M,mode=0700
      # No world-readable
      - /app/secrets:size=10M,mode=0600
```

### Container Security

```yaml
services:
  app:
    read_only: true  # Root filesystem read-only
    tmpfs:
      # Writable areas only via tmpfs
      - /tmp:size=50M
      - /var/run:size=10M
      - /app/cache:size=100M
```

## Memory Considerations

### Size Planning

```yaml
# Consider total container memory
services:
  app:
    deploy:
      resources:
        limits:
          memory: 512M  # Total container memory
    tmpfs:
      # tmpfs comes from container's memory limit
      - /tmp:size=50M        # 10% for tmp
      - /app/cache:size=100M # 20% for cache
      # Leaves 362M for app
```

### Monitoring

```bash
# Check tmpfs usage
docker exec container df -h /tmp

# Output:
# Filesystem      Size  Used Avail Use% Mounted on
# tmpfs           100M   5M   95M   5% /tmp
```

### OOM Prevention

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          memory: 1G
    tmpfs:
      # Don't over-allocate tmpfs
      - /tmp:size=100M      # Reasonable limit
      - /app/cache:size=200M
    # Leave enough memory for application
```

## Development vs Production

### Development

```yaml
# docker-compose.override.yml
services:
  app:
    tmpfs:
      # Larger tmpfs for development
      - /tmp:size=200M
      - /app/cache:size=500M
```

### Production

```yaml
# docker-compose.prod.yml
services:
  app:
    tmpfs:
      # Minimal tmpfs in production
      - /tmp:size=50M
      - /app/cache:size=100M
```

## Combining with Other Mounts

```yaml
services:
  app:
    volumes:
      # Persistent data
      - app_data:/app/data

      # Config from host
      - ./config:/app/config:ro

    tmpfs:
      # Temporary files
      - /tmp:size=100M

      # Cache (recreatable)
      - /app/cache:size=200M

      # Secrets (security)
      - /app/secrets:size=10M,mode=0700

volumes:
  app_data:
```

## Troubleshooting

### Check tmpfs Mounts

```bash
# List mounts in container
docker exec container mount | grep tmpfs

# Check specific tmpfs
docker exec container df -h /tmp

# Inspect container mounts
docker inspect container --format '{{json .Mounts}}'
```

### Out of Memory

```bash
# tmpfs full
# Error: No space left on device

# Check usage
docker exec container df -h /tmp

# Solutions:
# 1. Increase size limit
# 2. Clean up files
# 3. Use disk-based volume instead
```

### Permission Denied

```bash
# Check tmpfs mode
docker exec container ls -la /tmp

# Fix: Specify correct mode
tmpfs:
  - /tmp:size=100M,mode=1777
```

## Complete Example

```yaml
services:
  # Web application
  app:
    build: ./app
    read_only: true  # Secure: read-only root filesystem
    volumes:
      # Persistent uploads
      - uploads:/app/uploads
      # Read-only config
      - ./config/app.yaml:/app/config/app.yaml:ro
    tmpfs:
      # General temp files
      - /tmp:size=50M,mode=1777
      # Application cache (can be rebuilt)
      - /app/cache:size=200M,mode=0755
      # Session data
      - /app/sessions:size=100M,mode=0700
      # Runtime secrets
      - /app/secrets:size=10M,mode=0600

  # Background worker
  worker:
    build: ./worker
    read_only: true
    tmpfs:
      - /tmp:size=100M
      # Processing workspace
      - /app/workspace:size=500M

  # Redis (ephemeral mode)
  redis:
    image: redis:7-alpine
    tmpfs:
      # All data in memory only
      - /data:size=256M
    command: redis-server --save ""  # Disable persistence

  # Database
  db:
    image: postgres:16-alpine
    volumes:
      # Persistent data on disk
      - postgres_data:/var/lib/postgresql/data
    tmpfs:
      # Temp space for queries
      - /tmp:size=100M
      - /var/run/postgresql:size=10M

  # Build/test service
  test:
    build:
      target: test
    tmpfs:
      # All test artifacts in memory
      - /tmp:size=200M
      - /app/coverage:size=100M
      - /app/.cache:size=200M
      - /app/dist:size=100M
    profiles:
      - test

volumes:
  uploads:
  postgres_data:
```

## Best Practices

1. **Set size limits** - Prevent memory exhaustion
2. **Use appropriate modes** - Restrict permissions for security
3. **Don't over-allocate** - Leave memory for application
4. **Use for sensitive data** - Secrets never touch disk
5. **Combine with read-only** - Maximum security
6. **Monitor usage** - Track tmpfs consumption
7. **Plan for restart** - Data will be lost

## Related Skills
- storage/volumes
- storage/bind-mounts
- security/secrets-management
