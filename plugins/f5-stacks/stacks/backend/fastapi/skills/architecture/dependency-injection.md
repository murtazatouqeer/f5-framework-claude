---
name: fastapi-dependency-injection
description: FastAPI dependency injection patterns
applies_to: fastapi
category: skill
---

# FastAPI Dependency Injection

## Overview

FastAPI's dependency injection system allows for clean, testable code
with automatic resolution of dependencies.

## Basic Dependencies

```python
# app/api/deps.py
from typing import Annotated, AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from app.database import AsyncSessionLocal
from app.config import settings
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.user import UserService


# Database Session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Type alias for cleaner annotations
DBSession = Annotated[AsyncSession, Depends(get_db)]


# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


# Current user dependency
async def get_current_user(
    db: DBSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


# Type alias
CurrentUser = Annotated[User, Depends(get_current_user)]


# Active user (verified)
async def get_current_active_user(
    current_user: CurrentUser,
) -> User:
    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="Email not verified")
    return current_user


ActiveUser = Annotated[User, Depends(get_current_active_user)]


# Admin user
async def get_current_admin_user(
    current_user: CurrentUser,
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


AdminUser = Annotated[User, Depends(get_current_admin_user)]
```

## Service Dependencies

```python
# app/api/deps.py (continued)
from app.repositories.product import ProductRepository
from app.services.product import ProductService

# Repository dependencies
def get_user_repository(db: DBSession) -> UserRepository:
    return UserRepository(db)


def get_product_repository(db: DBSession) -> ProductRepository:
    return ProductRepository(db)


# Service dependencies
def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


def get_product_service(
    product_repo: Annotated[ProductRepository, Depends(get_product_repository)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> ProductService:
    return ProductService(product_repo, user_service)


# Type aliases
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
```

## Using Dependencies in Endpoints

```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.api.deps import (
    DBSession,
    CurrentUser,
    AdminUser,
    UserServiceDep,
)
from app.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: CurrentUser,
):
    """Get current user profile."""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    update_data: UserUpdate,
    current_user: CurrentUser,
    user_service: UserServiceDep,
):
    """Update current user profile."""
    return await user_service.update(current_user.id, update_data)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    admin_user: AdminUser,  # Only admins can list all users
    user_service: UserServiceDep,
    skip: int = 0,
    limit: int = 100,
):
    """List all users (admin only)."""
    return await user_service.list(skip=skip, limit=limit)
```

## Class-based Dependencies

```python
# app/api/deps.py

class Pagination:
    """Pagination dependency."""

    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100,
    ):
        self.page = max(1, page)
        self.page_size = min(max(1, page_size), max_page_size)
        self.offset = (self.page - 1) * self.page_size
        self.limit = self.page_size


class QueryParams:
    """Common query parameters."""

    def __init__(
        self,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ):
        self.search = search
        self.sort_by = sort_by
        self.sort_order = sort_order


class DateRangeFilter:
    """Date range filter dependency."""

    def __init__(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        self.start_date = start_date
        self.end_date = end_date

        if start_date and end_date and start_date > end_date:
            raise HTTPException(
                status_code=400,
                detail="start_date must be before end_date"
            )


# Usage
@router.get("/")
async def list_items(
    pagination: Annotated[Pagination, Depends()],
    query: Annotated[QueryParams, Depends()],
    date_range: Annotated[DateRangeFilter, Depends()],
):
    # pagination.offset, pagination.limit
    # query.search, query.sort_by
    # date_range.start_date, date_range.end_date
    ...
```

## Resource Access Control

```python
# app/api/deps.py
from sqlalchemy import text

class ResourceOwnerCheck:
    """Check if current user owns the resource."""

    def __init__(self, resource_type: str):
        self.resource_type = resource_type

    async def __call__(
        self,
        resource_id: str,
        current_user: CurrentUser,
        db: DBSession,
    ) -> bool:
        # Generic ownership check
        query = text(f"SELECT user_id FROM {self.resource_type} WHERE id = :id")
        result = await db.execute(query, {"id": resource_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Resource not found")

        if row.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="Not authorized")

        return True


# Usage
check_product_owner = ResourceOwnerCheck("products")

@router.put("/{product_id}")
async def update_product(
    product_id: str,
    data: ProductUpdate,
    _: Annotated[bool, Depends(check_product_owner)],
    product_service: ProductServiceDep,
):
    return await product_service.update(product_id, data)
```

## Dependency with Yield (Cleanup)

```python
# app/api/deps.py
from redis import asyncio as aioredis

async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Redis connection with cleanup."""
    redis = await aioredis.from_url(settings.REDIS_URL)
    try:
        yield redis
    finally:
        await redis.close()


RedisDep = Annotated[aioredis.Redis, Depends(get_redis)]
```

## Caching Dependencies

```python
# app/api/deps.py
from functools import lru_cache

@lru_cache
def get_settings():
    """Cached settings."""
    return Settings()


# For async dependencies that should be cached per-request
# use a custom solution or starlette-context
```

## Best Practices

1. **Use Annotated type aliases** for cleaner code
2. **Create service/repository dependencies** for business logic
3. **Use class-based dependencies** for complex parameter validation
4. **Implement resource ownership checks** as reusable dependencies
5. **Use yield dependencies** for cleanup (connections, files)
6. **Cache expensive dependencies** when appropriate
7. **Keep dependencies focused** - single responsibility
