---
name: fastapi-project-structure
description: FastAPI project organization and structure patterns
applies_to: fastapi
category: skill
---

# FastAPI Project Structure

## Recommended Structure

```
project/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Application factory
│   ├── config.py                  # Settings with pydantic
│   ├── database.py                # Database connection
│   ├── dependencies.py            # Shared dependencies
│   │
│   ├── core/                      # Core functionality
│   │   ├── __init__.py
│   │   ├── security.py           # Auth utilities
│   │   ├── exceptions.py         # Custom exceptions
│   │   ├── pagination.py         # Pagination helpers
│   │   └── logging.py            # Logging config
│   │
│   ├── models/                    # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py               # Base model class
│   │   ├── user.py
│   │   └── {entity}.py
│   │
│   ├── schemas/                   # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── base.py               # Base schemas
│   │   ├── user.py
│   │   └── {entity}.py
│   │
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py               # Base repository
│   │   └── {entity}.py
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   └── {entity}.py
│   │
│   └── api/
│       ├── __init__.py
│       ├── deps.py               # API dependencies
│       └── v1/
│           ├── __init__.py
│           ├── router.py         # Main router
│           └── endpoints/
│               ├── __init__.py
│               ├── auth.py
│               ├── users.py
│               └── {entity}.py
│
├── alembic/                       # Migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py               # Fixtures
│   ├── api/
│   │   └── v1/
│   │       └── test_{entity}.py
│   └── services/
│       └── test_{entity}.py
│
├── alembic.ini
├── pyproject.toml
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   └── prod.txt
└── docker-compose.yml
```

## Main Application

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.api.v1.router import api_router
from app.core.exceptions import setup_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handlers
    setup_exception_handlers(app)

    # Routers
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
```

## Configuration

```python
# app/config.py
from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # App
    PROJECT_NAME: str = "FastAPI App"
    PROJECT_DESCRIPTION: str = "FastAPI application"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

## Database Setup

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## API Router

```python
# app/api/v1/router.py
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, products, orders

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(products.router, prefix="/products", tags=["Products"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders"])
```

## Environment Files

```bash
# .env.example
PROJECT_NAME=MyApp
DEBUG=true

# Security
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/dbname

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:8080"]
```

## Best Practices

1. **Use application factory pattern** for testing and flexibility
2. **Separate configuration** using pydantic-settings
3. **Use lifespan** for startup/shutdown events (replaces on_event)
4. **Organize by feature** not by type when project grows
5. **Keep API versioned** from the start (/api/v1/)
6. **Use type hints** everywhere for better IDE support
