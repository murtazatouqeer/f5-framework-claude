---
name: compose-environment
description: Docker Compose environment and secrets management
applies_to: docker
---

# Docker Compose Environment Configuration

## Environment Variables

### Inline Definition

```yaml
services:
  api:
    environment:
      # Key=value format
      - NODE_ENV=production
      - PORT=3000
      - DEBUG=false

      # Map format
      NODE_ENV: production
      PORT: 3000
      DEBUG: "false"
```

### From .env File

```yaml
services:
  api:
    env_file:
      - .env
      - .env.local  # Overrides .env
```

```env
# .env
NODE_ENV=development
PORT=3000
DATABASE_URL=postgres://localhost:5432/app
JWT_SECRET=development-secret
```

### Variable Substitution

```yaml
services:
  api:
    image: myapp:${VERSION:-latest}
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - LOG_LEVEL=${LOG_LEVEL:-info}
```

### Substitution Syntax

```yaml
# ${VAR}          - Value of VAR
# ${VAR:-default} - default if VAR is unset or empty
# ${VAR-default}  - default if VAR is unset
# ${VAR:?error}   - Error if VAR is unset or empty
# ${VAR?error}    - Error if VAR is unset
# ${VAR:+value}   - value if VAR is set, otherwise empty

services:
  api:
    environment:
      # Use default if not set
      - LOG_LEVEL=${LOG_LEVEL:-info}

      # Required variable (error if missing)
      - SECRET_KEY=${SECRET_KEY:?SECRET_KEY is required}

      # Only set if other var is set
      - DEBUG_HOST=${DEBUG:-}${DEBUG:+localhost}
```

## Environment Files

### File Structure

```
project/
├── .env                  # Default values (committed)
├── .env.local            # Local overrides (not committed)
├── .env.development      # Development values
├── .env.production       # Production values
└── docker-compose.yml
```

### .env Files Priority

```bash
# Loaded automatically (in order)
1. Shell environment
2. .env file
3. env_file directive
4. environment directive
```

### Environment Per Service

```yaml
services:
  api:
    env_file:
      - .env
      - ./api/.env

  worker:
    env_file:
      - .env
      - ./worker/.env
```

## Secrets Management

### Docker Secrets (Swarm Mode)

```yaml
services:
  api:
    secrets:
      - db_password
      - api_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true
```

```bash
# Create external secret
echo "my-secret-password" | docker secret create db_password -

# Secrets available at /run/secrets/<secret_name>
```

### File-Based Secrets

```yaml
services:
  api:
    volumes:
      - ./secrets:/run/secrets:ro
    environment:
      - DB_PASSWORD_FILE=/run/secrets/db_password
```

```javascript
// Read secret from file
const password = fs.readFileSync(process.env.DB_PASSWORD_FILE, 'utf8').trim();
```

### Environment Variable Secrets

```yaml
services:
  api:
    environment:
      - DB_PASSWORD=${DB_PASSWORD}
```

```bash
# Pass at runtime
DB_PASSWORD=secret docker compose up

# Or export
export DB_PASSWORD=secret
docker compose up
```

## Environment Patterns

### Development vs Production

```yaml
# docker-compose.yml (base)
services:
  api:
    environment:
      - PORT=3000

# docker-compose.override.yml (development, auto-loaded)
services:
  api:
    environment:
      - NODE_ENV=development
      - DEBUG=app:*
      - LOG_LEVEL=debug

# docker-compose.prod.yml (production)
services:
  api:
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=warn
```

```bash
# Development (auto-loads override)
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Database Configuration

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD required}
      POSTGRES_DB: ${DB_NAME:-app}

  api:
    environment:
      DATABASE_URL: postgres://${DB_USER:-postgres}:${DB_PASSWORD}@db:5432/${DB_NAME:-app}
```

### Service URLs

```yaml
services:
  frontend:
    environment:
      - NEXT_PUBLIC_API_URL=${API_URL:-http://localhost:4000}
      - NEXT_PUBLIC_WS_URL=${WS_URL:-ws://localhost:4000}

  api:
    environment:
      - DATABASE_URL=postgres://db:5432/app
      - REDIS_URL=redis://redis:6379
      - RABBITMQ_URL=amqp://rabbit:rabbit@rabbitmq:5672
```

### Feature Flags

```yaml
services:
  api:
    environment:
      - FEATURE_NEW_UI=${FEATURE_NEW_UI:-false}
      - FEATURE_BETA=${FEATURE_BETA:-false}
      - FEATURE_EXPERIMENTAL=${FEATURE_EXPERIMENTAL:-false}
```

## Complete Example

### .env (default values)

```env
# Application
NODE_ENV=development
LOG_LEVEL=debug

# Ports
API_PORT=4000
FRONTEND_PORT=3000

# Database
DB_USER=postgres
DB_NAME=myapp

# Redis
REDIS_MAXMEMORY=256mb

# Feature Flags
FEATURE_NEW_UI=false
```

### .env.production

```env
# Application
NODE_ENV=production
LOG_LEVEL=warn

# Feature Flags
FEATURE_NEW_UI=true
```

### docker-compose.yml

```yaml
services:
  frontend:
    build:
      context: ./frontend
      args:
        - NEXT_PUBLIC_API_URL=${API_URL:-http://localhost:${API_PORT:-4000}}
    ports:
      - "${FRONTEND_PORT:-3000}:3000"
    environment:
      - NODE_ENV=${NODE_ENV:-development}
    depends_on:
      - api

  api:
    build:
      context: ./api
    ports:
      - "${API_PORT:-4000}:4000"
    env_file:
      - .env
    environment:
      - NODE_ENV=${NODE_ENV:-development}
      - PORT=4000
      - DATABASE_URL=postgres://${DB_USER:-postgres}:${DB_PASSWORD:?DB_PASSWORD required}@db:5432/${DB_NAME:-app}
      - REDIS_URL=redis://redis:6379
      - JWT_SECRET=${JWT_SECRET:?JWT_SECRET required}
      - LOG_LEVEL=${LOG_LEVEL:-info}
      - FEATURE_NEW_UI=${FEATURE_NEW_UI:-false}
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    ports:
      - "${DB_PORT:-5432}:5432"
    environment:
      POSTGRES_USER: ${DB_USER:-postgres}
      POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD required}
      POSTGRES_DB: ${DB_NAME:-app}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --appendonly yes
      --maxmemory ${REDIS_MAXMEMORY:-256mb}
      --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
```

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use .env.example** for documentation
3. **Require critical variables** with `${VAR:?error}`
4. **Use secrets** for sensitive data in Swarm
5. **Separate env files** for different environments
6. **Use external secret managers** for production
7. **Rotate secrets** regularly

### .gitignore

```gitignore
.env
.env.local
.env.*.local
secrets/
*.pem
*.key
```

### .env.example

```env
# Copy to .env and fill in values

# Required
DB_PASSWORD=
JWT_SECRET=

# Optional (defaults shown)
NODE_ENV=development
LOG_LEVEL=debug
API_PORT=4000
```

## Related Skills
- compose/compose-basics
- security/secrets-management
