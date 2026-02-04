---
name: dockerfile-python
description: Production-ready Python Dockerfile templates
applies_to: docker
variables:
  - python_version: Python version (3.11, 3.12)
  - framework: Django, FastAPI, Flask
  - app_port: Application port
---

# Python Dockerfile Templates

## Basic Production Template

```dockerfile
# syntax=docker/dockerfile:1

# ===== Build Stage =====
FROM python:{{python_version}}-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc && \
    rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== Production Stage =====
FROM python:{{python_version}}-slim

WORKDIR /app

# Security: Non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE {{app_port}}

CMD ["python", "app.py"]
```

## FastAPI

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:{{python_version}}-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE {{app_port}}

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:{{app_port}}/health')" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{{app_port}}"]
```

## FastAPI with Poetry

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim AS builder

WORKDIR /app

RUN pip install poetry && \
    poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock ./
RUN poetry install --only main --no-interaction --no-ansi

COPY . .

FROM python:{{python_version}}-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER appuser

EXPOSE {{app_port}}

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{{app_port}}"]
```

## Django

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:{{python_version}}-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 && \
    rm -rf /var/lib/apt/lists/* && \
    useradd --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser . .

# Collect static files
RUN python manage.py collectstatic --noinput

USER appuser

EXPOSE {{app_port}}

CMD ["gunicorn", "--bind", "0.0.0.0:{{app_port}}", "--workers", "4", "config.wsgi:application"]
```

## Flask

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:{{python_version}}-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE {{app_port}}

CMD ["gunicorn", "--bind", "0.0.0.0:{{app_port}}", "--workers", "4", "app:app"]
```

## With uv (Fast Package Manager)

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Create virtual environment and install deps
COPY requirements.txt .
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install -r requirements.txt

FROM python:{{python_version}}-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE {{app_port}}

CMD ["python", "main.py"]
```

## Alpine (Smaller)

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-alpine AS builder

WORKDIR /app

RUN apk add --no-cache \
      gcc \
      musl-dev \
      libffi-dev

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:{{python_version}}-alpine

WORKDIR /app

RUN adduser -D -u 1000 appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE {{app_port}}

CMD ["python", "main.py"]
```

## Development Template

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim

WORKDIR /app

# Development tools
RUN pip install --no-cache-dir \
      pytest \
      black \
      flake8 \
      mypy

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{app_port}}

# Hot reload with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{{app_port}}", "--reload"]
```

## With BuildKit Cache

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

FROM python:{{python_version}}-slim

WORKDIR /app

RUN useradd --create-home appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE {{app_port}}

CMD ["python", "main.py"]
```

## Distroless (Maximum Security)

```dockerfile
# syntax=docker/dockerfile:1

FROM python:{{python_version}}-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM gcr.io/distroless/python3-debian12

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app .

ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

USER nonroot

EXPOSE {{app_port}}

CMD ["main.py"]
```

## .dockerignore

```dockerignore
# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.venv
venv
ENV
env.bak
venv.bak

# Packaging
.eggs
*.egg-info
*.egg
dist
build
*.whl

# Testing
.tox
.coverage
.pytest_cache
htmlcov

# IDE
.idea
.vscode
*.swp

# Environment
.env
.env.*
!.env.example

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Git
.git
.gitignore

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
  --build-arg PYTHON_VERSION=3.12 \
  -t myapp:v1.0.0 .

# Multi-platform
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t myapp:latest \
  --push .
```
