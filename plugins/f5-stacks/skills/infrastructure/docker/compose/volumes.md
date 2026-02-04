---
name: compose-volumes
description: Docker Compose volume configuration
applies_to: docker
---

# Docker Compose Volumes

## Volume Types

### Named Volumes

Managed by Docker, best for persistent data:

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:  # Defined at top level
```

### Bind Mounts

Map host directory to container:

```yaml
services:
  api:
    volumes:
      # HOST_PATH:CONTAINER_PATH
      - ./src:/app/src
      - ./config.json:/app/config.json:ro
```

### Anonymous Volumes

Temporary, managed by Docker:

```yaml
services:
  api:
    volumes:
      - /app/node_modules  # Preserves node_modules
```

### tmpfs Mounts

In-memory, not persisted:

```yaml
services:
  api:
    tmpfs:
      - /tmp
      - /app/cache:size=100M
```

## Volume Configuration

### Named Volume Options

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      device: /data/postgres
      o: bind

  # External volume (pre-existing)
  existing_data:
    external: true
    name: my-existing-volume

  # With labels
  app_data:
    labels:
      - "com.example.description=Application data"
      - "com.example.department=IT"
```

### Bind Mount Options

```yaml
services:
  api:
    volumes:
      # Read-write (default)
      - ./data:/app/data

      # Read-only
      - ./config:/app/config:ro

      # Consistent mode (macOS)
      - ./src:/app/src:cached

      # Delegated mode (better performance on macOS)
      - ./logs:/app/logs:delegated

      # Long syntax
      - type: bind
        source: ./src
        target: /app/src
        read_only: false
```

### Long Syntax

```yaml
services:
  api:
    volumes:
      # Named volume
      - type: volume
        source: app_data
        target: /app/data
        volume:
          nocopy: true

      # Bind mount
      - type: bind
        source: ./src
        target: /app/src
        read_only: false
        bind:
          create_host_path: true

      # tmpfs
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 100000000  # 100MB
          mode: 1777
```

## Common Patterns

### Development Hot Reload

```yaml
services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      # Mount source for hot reload
      - ./api/src:/app/src
      # Preserve container's node_modules
      - /app/node_modules
    command: npm run dev
```

### Database Persistence

```yaml
services:
  postgres:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    environment:
      POSTGRES_PASSWORD: secret

  mysql:
    image: mysql:8.0
    volumes:
      - mysql_data:/var/lib/mysql
      - ./db/init:/docker-entrypoint-initdb.d:ro

  mongodb:
    image: mongo:7
    volumes:
      - mongo_data:/data/db

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  mysql_data:
  mongo_data:
  redis_data:
```

### Configuration Files

```yaml
services:
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro

  app:
    build: .
    volumes:
      - ./config/app.json:/app/config/app.json:ro
```

### Logs and Data Separation

```yaml
services:
  api:
    volumes:
      # Persistent data
      - app_data:/app/data

      # Logs (bind mount for easy access)
      - ./logs:/app/logs

      # Cache (tmpfs, not persisted)
    tmpfs:
      - /app/cache

volumes:
  app_data:
```

### Shared Volume Between Services

```yaml
services:
  uploader:
    volumes:
      - uploads:/app/uploads

  processor:
    volumes:
      - uploads:/app/uploads:ro  # Read-only access

  cdn:
    volumes:
      - uploads:/usr/share/nginx/html/uploads:ro

volumes:
  uploads:
```

## Development vs Production

### Development

```yaml
# docker-compose.override.yml
services:
  api:
    volumes:
      # Hot reload
      - ./api/src:/app/src
      - ./api/package.json:/app/package.json
      # Keep node_modules from image
      - /app/node_modules
```

### Production

```yaml
# docker-compose.prod.yml
services:
  api:
    # No source mounts in production
    volumes:
      - app_logs:/app/logs
      - app_uploads:/app/uploads
```

## Volume Management

### Commands

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect myapp_postgres_data

# Create volume
docker volume create my-volume

# Remove volume
docker volume rm my-volume

# Remove unused volumes
docker volume prune

# Remove all project volumes
docker compose down -v
```

### Backup and Restore

```bash
# Backup volume
docker run --rm \
  -v myapp_postgres_data:/source:ro \
  -v $(pwd):/backup \
  alpine tar cvf /backup/postgres_backup.tar /source

# Restore volume
docker run --rm \
  -v myapp_postgres_data:/target \
  -v $(pwd):/backup \
  alpine tar xvf /backup/postgres_backup.tar -C /target --strip-components=1
```

### Database Backup Pattern

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backup:
    image: postgres:16-alpine
    volumes:
      - ./backups:/backups
      - postgres_data:/var/lib/postgresql/data:ro
    command: >
      sh -c "pg_dump -h db -U postgres mydb > /backups/backup_$$(date +%Y%m%d).sql"
    profiles:
      - backup

volumes:
  postgres_data:
```

## Troubleshooting

### Permission Issues

```yaml
services:
  api:
    volumes:
      - ./data:/app/data
    # Fix: Run as same UID as host user
    user: "${UID}:${GID}"

# Or in Dockerfile:
# RUN chown -R 1000:1000 /app/data
```

### Performance on macOS/Windows

```yaml
services:
  api:
    volumes:
      # Use cached for better read performance
      - ./src:/app/src:cached

      # Use delegated for better write performance
      - ./logs:/app/logs:delegated

      # Or use named volume for node_modules
      - node_modules:/app/node_modules

volumes:
  node_modules:
```

### Volume Not Updating

```bash
# Check if volume exists
docker volume ls | grep myapp

# Inspect volume
docker volume inspect myapp_postgres_data

# Force recreate containers with fresh volumes
docker compose down -v
docker compose up -d
```

## Best Practices

1. **Use named volumes** for database data
2. **Use bind mounts** for development source code
3. **Use :ro** for read-only configuration files
4. **Don't mount secrets** - use Docker secrets or env vars
5. **Separate data from logs** - different retention policies
6. **Backup regularly** - named volumes can be backed up
7. **Use .dockerignore** - exclude node_modules etc from context
8. **Document volumes** - add labels and comments

## Complete Example

```yaml
services:
  api:
    build: ./api
    volumes:
      # Application data (persistent)
      - api_data:/app/data
      # Uploads (shared with cdn)
      - uploads:/app/uploads
      # Configuration (read-only)
      - ./config/api.json:/app/config/api.json:ro
    tmpfs:
      # Cache (not persisted)
      - /app/cache:size=100M

  cdn:
    image: nginx:alpine
    volumes:
      # Shared uploads (read-only)
      - uploads:/usr/share/nginx/html/uploads:ro
      # Nginx config
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro

  db:
    image: postgres:16-alpine
    volumes:
      # Database data (persistent)
      - postgres_data:/var/lib/postgresql/data
      # Init scripts (read-only)
      - ./db/init:/docker-entrypoint-initdb.d:ro

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

volumes:
  api_data:
    labels:
      - "backup=daily"
  uploads:
    labels:
      - "backup=daily"
  postgres_data:
    labels:
      - "backup=hourly"
  redis_data:
    labels:
      - "backup=none"
```

## Related Skills
- compose/compose-basics
- storage/volumes
- storage/bind-mounts
