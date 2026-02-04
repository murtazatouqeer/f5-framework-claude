---
name: docker-bind-mounts
description: Docker bind mounts for host filesystem access
applies_to: docker
---

# Docker Bind Mounts

## Bind Mount Overview

Bind mounts allow you to mount a file or directory from the host machine into a container.

### When to Use Bind Mounts

| Use Case | Bind Mount | Named Volume |
|----------|------------|--------------|
| Development hot reload | ✅ | ❌ |
| Config files | ✅ | ❌ |
| Share host files | ✅ | ❌ |
| Database persistence | ❌ | ✅ |
| Production data | ❌ | ✅ |
| Cross-platform | ❌ | ✅ |

## Basic Syntax

### CLI

```bash
# Short syntax
docker run -v /host/path:/container/path nginx

# Long syntax (recommended)
docker run \
  --mount type=bind,source=/host/path,target=/container/path \
  nginx

# Read-only
docker run -v /host/path:/container/path:ro nginx

# Or with --mount
docker run \
  --mount type=bind,source=/host/path,target=/container/path,readonly \
  nginx
```

### Docker Compose

```yaml
services:
  app:
    volumes:
      # Short syntax
      - ./src:/app/src
      - ./config.json:/app/config.json:ro

      # Long syntax
      - type: bind
        source: ./src
        target: /app/src
        read_only: false
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
      # Mount source code for hot reload
      - ./api/src:/app/src
      # Preserve container's node_modules
      - /app/node_modules
    command: npm run dev
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
    volumes:
      - ./config/app.yaml:/app/config/app.yaml:ro
      - ./config/secrets.json:/app/config/secrets.json:ro
```

### Log Access

```yaml
services:
  app:
    volumes:
      # Logs accessible from host
      - ./logs:/app/logs

  nginx:
    volumes:
      - ./nginx/logs:/var/log/nginx
```

### Static Files

```yaml
services:
  web:
    image: nginx:alpine
    volumes:
      - ./public:/usr/share/nginx/html:ro
      - ./uploads:/usr/share/nginx/html/uploads
```

### Init Scripts

```yaml
services:
  db:
    image: postgres:16-alpine
    volumes:
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
      - ./db/seed.sql:/docker-entrypoint-initdb.d/seed.sql:ro
```

## Mount Options

### Read-Only

```yaml
services:
  app:
    volumes:
      # Read-only - container cannot modify
      - ./config:/app/config:ro

      # Long syntax
      - type: bind
        source: ./config
        target: /app/config
        read_only: true
```

### Consistency Modes (macOS)

```yaml
services:
  app:
    volumes:
      # Cached - host authoritative (better read performance)
      - ./src:/app/src:cached

      # Delegated - container authoritative (better write performance)
      - ./logs:/app/logs:delegated

      # Consistent - full consistency (default, slowest)
      - ./data:/app/data:consistent
```

### Bind Propagation

```yaml
services:
  app:
    volumes:
      - type: bind
        source: ./data
        target: /app/data
        bind:
          propagation: rprivate  # default
          # Options: shared, slave, private, rshared, rslave, rprivate
```

### SELinux Options

```yaml
services:
  app:
    volumes:
      # :z - shared between containers
      - ./data:/app/data:z

      # :Z - private to this container
      - ./private:/app/private:Z
```

## Development vs Production

### Development

```yaml
# docker-compose.override.yml (auto-loaded in development)
services:
  frontend:
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
    command: npm run dev

  api:
    volumes:
      - ./api/src:/app/src
      - ./api/tests:/app/tests
    command: npm run dev

  db:
    volumes:
      # Expose for local tools
      - ./db/data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
```

### Production

```yaml
# docker-compose.prod.yml
services:
  frontend:
    # No source mounts - use built image

  api:
    volumes:
      # Only config and logs, no source code
      - ./config/production.yaml:/app/config/production.yaml:ro
      - api_logs:/app/logs

  db:
    volumes:
      # Named volume, not bind mount
      - postgres_data:/var/lib/postgresql/data
    # No exposed ports

volumes:
  api_logs:
  postgres_data:
```

## Handling node_modules

### Problem

```yaml
# BAD - overwrites container's node_modules
services:
  app:
    volumes:
      - ./:/app  # Includes empty/different node_modules
```

### Solutions

#### Anonymous Volume

```yaml
services:
  app:
    volumes:
      - ./:/app
      - /app/node_modules  # Preserved from image
```

#### Named Volume

```yaml
services:
  app:
    volumes:
      - ./:/app
      - node_modules:/app/node_modules

volumes:
  node_modules:
```

#### Selective Mounts

```yaml
services:
  app:
    volumes:
      - ./src:/app/src
      - ./package.json:/app/package.json
      # Don't mount node_modules directory
```

## Permission Issues

### Common Problem

```bash
# Error: Permission denied
# Container runs as different user than host files
```

### Solutions

#### Match User IDs

```yaml
services:
  app:
    user: "${UID}:${GID}"
    volumes:
      - ./data:/app/data
```

```bash
# Run with host user
UID=$(id -u) GID=$(id -g) docker compose up
```

#### Fix Permissions in Dockerfile

```dockerfile
FROM node:20-alpine

# Create app directory with proper permissions
RUN mkdir -p /app && chown -R node:node /app

USER node
WORKDIR /app

COPY --chown=node:node package*.json ./
RUN npm ci

COPY --chown=node:node . .
```

#### Use Named Group

```dockerfile
# Add container user to a group with known GID
RUN addgroup -g 1000 hostgroup && \
    adduser appuser hostgroup
```

### Docker Desktop (macOS/Windows)

```yaml
services:
  app:
    volumes:
      # Docker Desktop handles permissions automatically
      - ./src:/app/src
```

## Performance Optimization

### macOS/Windows Performance

```yaml
services:
  app:
    volumes:
      # Use cached for read-heavy directories
      - ./src:/app/src:cached

      # Use delegated for write-heavy directories
      - ./logs:/app/logs:delegated

      # Use named volumes for heavy I/O
      - node_modules:/app/node_modules

volumes:
  node_modules:
```

### Minimize Mount Scope

```yaml
# BAD - mounting entire project
services:
  app:
    volumes:
      - ./:/app

# GOOD - mount only needed directories
services:
  app:
    volumes:
      - ./src:/app/src
      - ./config:/app/config:ro
```

### Use .dockerignore

```dockerignore
# Don't include in build context
node_modules
.git
*.log
.env.local
```

## File vs Directory

### Single File Mount

```yaml
services:
  app:
    volumes:
      # Mount single file
      - ./config.json:/app/config.json:ro
      - ./secrets.env:/app/.env:ro
```

### Gotcha: Non-Existent File

```bash
# If host file doesn't exist, Docker creates a DIRECTORY
docker run -v ./missing.conf:/app/config.conf nginx
# Creates /app/config.conf as a directory!
```

### Solution

```bash
# Ensure file exists first
touch config.conf
docker run -v ./config.conf:/app/config.conf nginx
```

## Troubleshooting

### Check Mount

```bash
# Verify mount in container
docker inspect container --format '{{json .Mounts}}'

# List mounts
docker inspect container --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{println}}{{end}}'
```

### Permission Denied

```bash
# Check host permissions
ls -la ./data

# Check container user
docker exec container id

# Fix: Match user or change permissions
sudo chown -R 1000:1000 ./data
# Or
docker run --user $(id -u):$(id -g) ...
```

### File Not Updated

```bash
# macOS/Windows - sync delay
# Use :cached or :delegated options

# Or force sync
docker compose restart app
```

### Path Issues

```bash
# Use absolute paths or $(pwd)
docker run -v $(pwd)/src:/app/src nginx

# Windows PowerShell
docker run -v ${PWD}/src:/app/src nginx

# Windows CMD
docker run -v %cd%/src:/app/src nginx
```

## Complete Example

```yaml
services:
  # Development frontend with hot reload
  frontend:
    build:
      context: ./frontend
      target: development
    volumes:
      - ./frontend/src:/app/src:cached
      - ./frontend/public:/app/public:cached
      - /app/node_modules  # Preserve from image
    ports:
      - "3000:3000"
    command: npm run dev

  # Development API with hot reload
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api/src:/app/src:cached
      - ./api/tests:/app/tests:cached
      - /app/node_modules
    ports:
      - "4000:4000"
    command: npm run dev
    environment:
      - NODE_ENV=development

  # Nginx with custom config
  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx:delegated
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - frontend
      - api

  # Database with init scripts
  db:
    image: postgres:16-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Named volume for data
      - ./db/init:/docker-entrypoint-initdb.d:ro  # Init scripts
    ports:
      - "127.0.0.1:5432:5432"  # Localhost only
    environment:
      POSTGRES_PASSWORD: devpassword

volumes:
  postgres_data:
```

## Related Skills
- storage/volumes
- storage/tmpfs
- compose/volumes
