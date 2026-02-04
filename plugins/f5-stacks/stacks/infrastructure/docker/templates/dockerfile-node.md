---
name: dockerfile-node
description: Production-ready Node.js Dockerfile templates
applies_to: docker
variables:
  - node_version: Node.js version (18, 20, 22)
  - package_manager: npm, yarn, pnpm
  - app_port: Application port
---

# Node.js Dockerfile Templates

## Basic Production Template

```dockerfile
# syntax=docker/dockerfile:1

# ===== Build Stage =====
FROM node:{{node_version}}-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build application
RUN npm run build

# Prune dev dependencies
RUN npm prune --production

# ===== Production Stage =====
FROM node:{{node_version}}-alpine

# Security: Non-root user
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser

WORKDIR /app

# Copy production files
COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser

EXPOSE {{app_port}}

CMD ["node", "dist/server.js"]
```

## With Yarn

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine AS builder
WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build
RUN yarn install --production --frozen-lockfile

FROM node:{{node_version}}-alpine
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser
WORKDIR /app

COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser
EXPOSE {{app_port}}
CMD ["node", "dist/server.js"]
```

## With pnpm

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build
RUN pnpm prune --prod

FROM node:{{node_version}}-alpine
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser
WORKDIR /app

COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser
EXPOSE {{app_port}}
CMD ["node", "dist/server.js"]
```

## Next.js (Standalone)

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:{{node_version}}-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

FROM node:{{node_version}}-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
```

## NestJS

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

RUN npm prune --production

FROM node:{{node_version}}-alpine
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser
WORKDIR /app

COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser
EXPOSE {{app_port}}
CMD ["node", "dist/main.js"]
```

## Express API

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM node:{{node_version}}-alpine
RUN apk add --no-cache dumb-init && \
    addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser
WORKDIR /app

COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser
EXPOSE {{app_port}}

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:{{app_port}}/health || exit 1

ENTRYPOINT ["dumb-init", "--"]
CMD ["node", "dist/server.js"]
```

## Development Template

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine

WORKDIR /app

# Install dependencies first (cache layer)
COPY package*.json ./
RUN npm install

# Copy source
COPY . .

EXPOSE {{app_port}}

# Development command with hot reload
CMD ["npm", "run", "dev"]
```

## With BuildKit Cache

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine AS builder
WORKDIR /app

COPY package*.json ./

# Use BuildKit cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci

COPY . .

RUN --mount=type=cache,target=/app/.next/cache \
    npm run build

RUN npm prune --production

FROM node:{{node_version}}-alpine
RUN addgroup -g 1001 nodejs && \
    adduser -S -u 1001 -G nodejs appuser
WORKDIR /app

COPY --from=builder --chown=appuser:nodejs /app/dist ./dist
COPY --from=builder --chown=appuser:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:nodejs /app/package.json ./

USER appuser
EXPOSE {{app_port}}
CMD ["node", "dist/server.js"]
```

## Distroless (Maximum Security)

```dockerfile
# syntax=docker/dockerfile:1

FROM node:{{node_version}}-alpine AS builder
WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build
RUN npm prune --production

FROM gcr.io/distroless/nodejs{{node_version}}-debian12

WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./

USER nonroot
EXPOSE {{app_port}}
CMD ["dist/server.js"]
```

## .dockerignore

```dockerignore
# Dependencies
node_modules
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Build outputs
dist
build
.next
out

# Environment
.env
.env.*
!.env.example

# Development
.git
.gitignore
.dockerignore
Dockerfile*
docker-compose*

# IDE
.idea
.vscode
*.swp

# Tests
coverage
.nyc_output
__tests__
*.test.js
*.spec.js

# Documentation
docs
*.md
!README.md

# OS
.DS_Store
Thumbs.db
```

## Build Commands

```bash
# Development
docker build --target builder -t myapp:dev .

# Production
docker build -t myapp:latest .

# With build args
docker build \
  --build-arg NODE_VERSION=20 \
  --build-arg APP_PORT=3000 \
  -t myapp:v1.0.0 .

# Multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:latest \
  --push .
```
