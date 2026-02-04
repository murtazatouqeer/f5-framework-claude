---
name: dockerfile-go
description: Production-ready Go Dockerfile templates
applies_to: docker
variables:
  - go_version: Go version (1.21, 1.22)
  - app_name: Application binary name
  - app_port: Application port
---

# Go Dockerfile Templates

## Basic Production Template

```dockerfile
# syntax=docker/dockerfile:1

# ===== Build Stage =====
FROM golang:{{go_version}}-alpine AS builder

WORKDIR /app

# Install CA certificates for HTTPS
RUN apk add --no-cache ca-certificates tzdata

# Copy go.mod and go.sum
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build binary
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -o /app/{{app_name}} .

# ===== Production Stage =====
FROM scratch

# Copy CA certificates
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy binary
COPY --from=builder /app/{{app_name}} /{{app_name}}

# Run as non-root
USER 65534:65534

EXPOSE {{app_port}}

ENTRYPOINT ["/{{app_name}}"]
```

## With Alpine Runtime

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

WORKDIR /app

RUN apk add --no-cache ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux \
    go build -ldflags="-s -w" -o /app/server .

FROM alpine:3.19

RUN apk add --no-cache ca-certificates tzdata && \
    adduser -D -u 1000 appuser

WORKDIR /app

COPY --from=builder /app/server .

USER appuser

EXPOSE {{app_port}}

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:{{app_port}}/health || exit 1

CMD ["./server"]
```

## Distroless (Recommended)

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

WORKDIR /app

RUN apk add --no-cache ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build -ldflags="-s -w" -o /app/server .

FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

USER nonroot:nonroot

EXPOSE {{app_port}}

ENTRYPOINT ["/server"]
```

## With CGO Enabled

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

WORKDIR /app

RUN apk add --no-cache \
    ca-certificates \
    gcc \
    musl-dev

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# CGO enabled for C dependencies
RUN CGO_ENABLED=1 GOOS=linux \
    go build -ldflags="-s -w" -o /app/server .

FROM alpine:3.19

RUN apk add --no-cache ca-certificates && \
    adduser -D -u 1000 appuser

WORKDIR /app

COPY --from=builder /app/server .

USER appuser

EXPOSE {{app_port}}

CMD ["./server"]
```

## Multi-Platform Build

```dockerfile
# syntax=docker/dockerfile:1

FROM --platform=$BUILDPLATFORM golang:{{go_version}}-alpine AS builder

ARG TARGETPLATFORM
ARG TARGETOS
ARG TARGETARCH

WORKDIR /app

RUN apk add --no-cache ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=${TARGETOS} GOARCH=${TARGETARCH} \
    go build -ldflags="-s -w" -o /app/server .

FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

USER nonroot:nonroot

EXPOSE {{app_port}}

ENTRYPOINT ["/server"]
```

## With Private Modules

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

ARG GITHUB_TOKEN

WORKDIR /app

RUN apk add --no-cache ca-certificates git && \
    git config --global url."https://${GITHUB_TOKEN}:x-oauth-basic@github.com/".insteadOf "https://github.com/"

ENV GOPRIVATE=github.com/myorg/*

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux \
    go build -ldflags="-s -w" -o /app/server .

FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

USER nonroot:nonroot

EXPOSE {{app_port}}

ENTRYPOINT ["/server"]
```

## With BuildKit Cache

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

WORKDIR /app

RUN apk add --no-cache ca-certificates

COPY go.mod go.sum ./

# Use cache mount for Go modules
RUN --mount=type=cache,target=/go/pkg/mod \
    go mod download

COPY . .

# Use cache mount for build cache
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 GOOS=linux \
    go build -ldflags="-s -w" -o /app/server .

FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

USER nonroot:nonroot

EXPOSE {{app_port}}

ENTRYPOINT ["/server"]
```

## With UPX Compression

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

WORKDIR /app

RUN apk add --no-cache ca-certificates upx

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux \
    go build -ldflags="-s -w" -o /app/server . && \
    upx --best /app/server

FROM scratch

COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /app/server /server

USER 65534:65534

EXPOSE {{app_port}}

ENTRYPOINT ["/server"]
```

## With Version Info

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

ARG VERSION=dev
ARG COMMIT=unknown
ARG BUILD_DATE=unknown

WORKDIR /app

RUN apk add --no-cache ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux \
    go build -ldflags="-s -w \
      -X main.version=${VERSION} \
      -X main.commit=${COMMIT} \
      -X main.buildDate=${BUILD_DATE}" \
    -o /app/server .

FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

USER nonroot:nonroot

EXPOSE {{app_port}}

ENTRYPOINT ["/server"]
```

## Development Template

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine

WORKDIR /app

# Install air for hot reload
RUN go install github.com/cosmtrek/air@latest

COPY go.mod go.sum ./
RUN go mod download

COPY . .

EXPOSE {{app_port}}

# Use air for development
CMD ["air", "-c", ".air.toml"]
```

## Gin Framework

```dockerfile
# syntax=docker/dockerfile:1

FROM golang:{{go_version}}-alpine AS builder

WORKDIR /app

RUN apk add --no-cache ca-certificates

COPY go.mod go.sum ./
RUN go mod download

COPY . .

RUN CGO_ENABLED=0 GOOS=linux \
    go build -ldflags="-s -w" -o /app/server ./cmd/server

FROM gcr.io/distroless/static-debian12

COPY --from=builder /app/server /server

# Copy static files if needed
# COPY --from=builder /app/static /static

USER nonroot:nonroot

ENV GIN_MODE=release

EXPOSE {{app_port}}

ENTRYPOINT ["/server"]
```

## .dockerignore

```dockerignore
# Git
.git
.gitignore

# IDE
.idea
.vscode
*.swp

# Build outputs
/bin
/dist
*.exe

# Test files
*_test.go
/testdata

# Vendor (if using modules)
# vendor

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Environment
.env
.env.*

# Documentation
docs
*.md
!README.md

# OS
.DS_Store
Thumbs.db

# Development
.air.toml
tmp
```

## Build Commands

```bash
# Basic build
docker build -t myapp:latest .

# With version info
docker build \
  --build-arg VERSION=v1.0.0 \
  --build-arg COMMIT=$(git rev-parse --short HEAD) \
  --build-arg BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ") \
  -t myapp:v1.0.0 .

# Multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:latest \
  --push .

# With private modules
docker build \
  --build-arg GITHUB_TOKEN=$GITHUB_TOKEN \
  -t myapp:latest .
```
