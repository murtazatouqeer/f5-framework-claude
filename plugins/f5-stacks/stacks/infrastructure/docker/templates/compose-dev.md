---
name: compose-dev
description: Development environment Docker Compose templates
applies_to: docker
variables:
  - project_type: fullstack, backend, frontend
  - language: node, python, go, java
---

# Development Docker Compose Templates

## Node.js Development

```yaml
name: dev-nodejs

services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api/src:/app/src
      - ./api/package.json:/app/package.json
      - /app/node_modules
    ports:
      - "4000:4000"
      - "9229:9229"  # Debug port
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgres://postgres:postgres@db:5432/dev
      - REDIS_URL=redis://redis:6379
      - DEBUG=app:*
    command: npm run dev
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql:ro

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Database admin
  adminer:
    image: adminer
    ports:
      - "8080:8080"
    depends_on:
      - db

volumes:
  postgres_data:
```

## Full-Stack Development

```yaml
name: dev-fullstack

services:
  frontend:
    build:
      context: ./frontend
      target: development
    volumes:
      - ./frontend/src:/app/src
      - ./frontend/public:/app/public
      - /app/node_modules
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:4000
      - WATCHPACK_POLLING=true
    command: npm run dev
    depends_on:
      - api

  api:
    build:
      context: ./backend
      target: development
    volumes:
      - ./backend/src:/app/src
      - /app/node_modules
    ports:
      - "4000:4000"
      - "9229:9229"
    environment:
      - NODE_ENV=development
      - DATABASE_URL=postgres://postgres:postgres@db:5432/dev
      - REDIS_URL=redis://redis:6379
    command: npm run dev
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: dev
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Tools
  pgadmin:
    image: dpage/pgadmin4
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@admin.com
      PGADMIN_DEFAULT_PASSWORD: admin
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    profiles:
      - tools

  mailhog:
    image: mailhog/mailhog
    ports:
      - "1025:1025"  # SMTP
      - "8025:8025"  # Web UI
    profiles:
      - tools

volumes:
  postgres_data:
  pgadmin_data:
```

## Python Development

```yaml
name: dev-python

services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api:/app
    ports:
      - "8000:8000"
      - "5678:5678"  # Debug port
    environment:
      - PYTHONDONTWRITEBYTECODE=1
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=postgres://postgres:postgres@db:5432/dev
      - REDIS_URL=redis://redis:6379
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: dev
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Worker for background tasks
  worker:
    build:
      context: ./api
      target: development
    volumes:
      - ./api:/app
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/dev
      - REDIS_URL=redis://redis:6379
    command: celery -A tasks worker --loglevel=info
    depends_on:
      - db
      - redis
    profiles:
      - worker

volumes:
  postgres_data:
```

## Go Development

```yaml
name: dev-go

services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api:/app
      - go-mod-cache:/go/pkg/mod
    ports:
      - "8080:8080"
      - "2345:2345"  # Delve debug port
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/dev?sslmode=disable
      - REDIS_URL=redis://redis:6379
    command: air -c .air.toml
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: dev
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  go-mod-cache:
```

## Java/Spring Development

```yaml
name: dev-java

services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api/src:/app/src
      - maven-cache:/root/.m2
    ports:
      - "8080:8080"
      - "5005:5005"  # Debug port
    environment:
      - SPRING_PROFILES_ACTIVE=dev
      - SPRING_DATASOURCE_URL=jdbc:postgresql://db:5432/dev
      - SPRING_DATASOURCE_PASSWORD=postgres
      - SPRING_REDIS_HOST=redis
    command: ./mvnw spring-boot:run -Dspring-boot.run.jvmArguments="-agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=*:5005"
    depends_on:
      - db
      - redis

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: dev
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
  maven-cache:
```

## With Testing Services

```yaml
name: dev-testing

services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api:/app
      - /app/node_modules
    ports:
      - "4000:4000"
    environment:
      - NODE_ENV=test
      - DATABASE_URL=postgres://postgres:postgres@db-test:5432/test
      - REDIS_URL=redis://redis:6379

  # Test database (separate from dev)
  db-test:
    image: postgres:16-alpine
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: test
    tmpfs:
      - /var/lib/postgresql/data  # In-memory for speed

  redis:
    image: redis:7-alpine

  # Test runner
  test:
    build:
      context: ./api
      target: test
    volumes:
      - ./api:/app
      - /app/node_modules
      - ./coverage:/app/coverage
    environment:
      - NODE_ENV=test
      - DATABASE_URL=postgres://postgres:postgres@db-test:5432/test
    command: npm run test:watch
    depends_on:
      - db-test
    profiles:
      - test

  # E2E tests
  e2e:
    build:
      context: ./e2e
    volumes:
      - ./e2e:/app
      - /app/node_modules
    environment:
      - BASE_URL=http://api:4000
    command: npm run test:e2e
    depends_on:
      - api
    profiles:
      - e2e
```

## Debug Configuration

```yaml
# docker-compose.debug.yml
services:
  api:
    build:
      context: ./api
      target: development
    volumes:
      - ./api:/app
      - /app/node_modules
    ports:
      - "4000:4000"
      - "9229:9229"  # Node.js debugger
    environment:
      - NODE_OPTIONS=--inspect=0.0.0.0:9229
    command: node --inspect=0.0.0.0:9229 dist/server.js
```

### VS Code launch.json

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Docker: Attach to Node",
      "type": "node",
      "request": "attach",
      "remoteRoot": "/app",
      "localRoot": "${workspaceFolder}/api",
      "port": 9229,
      "address": "localhost"
    }
  ]
}
```

## Override Files

```yaml
# docker-compose.override.yml (auto-loaded in development)
services:
  api:
    volumes:
      - ./api/src:/app/src
    environment:
      - DEBUG=*
    command: npm run dev

  db:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"
```

## Makefile for Development

```makefile
# Makefile

.PHONY: up down logs shell db-shell test lint

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec api /bin/sh

db-shell:
	docker compose exec db psql -U postgres -d dev

test:
	docker compose --profile test run --rm test

lint:
	docker compose exec api npm run lint

build:
	docker compose build --no-cache

clean:
	docker compose down -v --remove-orphans
	docker system prune -f
```

## Usage

```bash
# Start development environment
docker compose up -d

# View logs
docker compose logs -f api

# Run with tools profile
docker compose --profile tools up -d

# Shell into container
docker compose exec api /bin/sh

# Run tests
docker compose --profile test up

# Stop everything
docker compose down

# Clean restart
docker compose down -v
docker compose up -d --build
```
