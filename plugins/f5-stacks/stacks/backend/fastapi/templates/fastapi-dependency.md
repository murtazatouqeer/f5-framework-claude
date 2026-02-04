---
name: fastapi-dependency
description: FastAPI dependency injection template
applies_to: fastapi
category: template
variables:
  - name: entity_name
    description: Entity name in PascalCase (e.g., Product)
  - name: entity_lower
    description: Lowercase entity name (e.g., product)
---

# FastAPI Dependency Template

## Template

```python
# app/api/deps.py
"""
FastAPI dependencies for dependency injection.

REQ-XXX: Dependency injection setup
"""
from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database import async_session
from app.models.user import User
from app.repositories.user import UserRepository
from app.repositories.{{entity_lower}} import {{entity_name}}Repository
from app.services.user import UserService
from app.services.{{entity_lower}} import {{entity_name}}Service


# ============================================================================
# Database Session
# ============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session dependency."""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


DBSession = Annotated[AsyncSession, Depends(get_db)]


# ============================================================================
# Authentication
# ============================================================================

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    db: DBSession,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(UUID(user_id))

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Verify user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_admin_user(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """Verify user is admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


# Type aliases for cleaner signatures
CurrentUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


# ============================================================================
# Optional Authentication
# ============================================================================

async def get_optional_user(
    db: DBSession,
    token: Annotated[str | None, Depends(OAuth2PasswordBearer(
        tokenUrl="/api/v1/auth/token",
        auto_error=False,
    ))] = None,
) -> User | None:
    """Get current user if authenticated, None otherwise."""
    if token is None:
        return None

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None

    user_repo = UserRepository(db)
    return await user_repo.get_by_id(UUID(user_id))


OptionalUser = Annotated[User | None, Depends(get_optional_user)]


# ============================================================================
# Repository Dependencies
# ============================================================================

async def get_user_repository(db: DBSession) -> UserRepository:
    """Provide UserRepository dependency."""
    return UserRepository(db)


async def get_{{entity_lower}}_repository(db: DBSession) -> {{entity_name}}Repository:
    """Provide {{entity_name}}Repository dependency."""
    return {{entity_name}}Repository(db)


# Type aliases
UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
{{entity_name}}RepoDep = Annotated[{{entity_name}}Repository, Depends(get_{{entity_lower}}_repository)]


# ============================================================================
# Service Dependencies
# ============================================================================

async def get_user_service(
    repository: UserRepoDep,
) -> UserService:
    """Provide UserService dependency."""
    return UserService(repository)


async def get_{{entity_lower}}_service(
    repository: {{entity_name}}RepoDep,
) -> {{entity_name}}Service:
    """Provide {{entity_name}}Service dependency."""
    return {{entity_name}}Service(repository)


# Type aliases
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
{{entity_name}}ServiceDep = Annotated[{{entity_name}}Service, Depends(get_{{entity_lower}}_service)]


# ============================================================================
# Pagination
# ============================================================================

class PaginationParams:
    """Pagination query parameters."""

    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
    ):
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 1
        if page_size > 100:
            page_size = 100

        self.page = page
        self.page_size = page_size

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


Pagination = Annotated[PaginationParams, Depends()]


# ============================================================================
# Resource Ownership
# ============================================================================

class RequireOwnership:
    """Dependency to verify resource ownership."""

    def __init__(
        self,
        get_resource,
        owner_field: str = "created_by_id",
        admin_bypass: bool = True,
    ):
        self.get_resource = get_resource
        self.owner_field = owner_field
        self.admin_bypass = admin_bypass

    async def __call__(
        self,
        resource_id: UUID,
        current_user: CurrentUser,
        db: DBSession,
    ) -> bool:
        # Admin bypass
        if self.admin_bypass and current_user.is_admin:
            return True

        # Get resource
        resource = await self.get_resource(db, resource_id)
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",
            )

        # Check ownership
        owner_id = getattr(resource, self.owner_field, None)
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource",
            )

        return True


# ============================================================================
# Rate Limiting
# ============================================================================

from fastapi import Request
from app.core.redis import RedisClient


class RateLimiter:
    """Rate limiting dependency."""

    def __init__(
        self,
        times: int = 100,
        seconds: int = 60,
    ):
        self.times = times
        self.seconds = seconds

    async def __call__(self, request: Request) -> None:
        redis = await RedisClient.get_client()

        # Use IP or user ID as key
        client_ip = request.client.host
        key = f"ratelimit:{client_ip}"

        # Check current count
        current = await redis.get(key)
        if current and int(current) >= self.times:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": str(self.seconds)},
            )

        # Increment counter
        pipe = redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, self.seconds)
        await pipe.execute()


# Pre-configured rate limiters
rate_limit_default = RateLimiter(times=100, seconds=60)
rate_limit_strict = RateLimiter(times=10, seconds=60)
```

## Usage

Replace placeholders:
- `{{entity_name}}`: PascalCase entity name (e.g., `Product`)
- `{{entity_lower}}`: Lowercase singular (e.g., `product`)

### Example Usage in Endpoint

```python
# app/api/v1/endpoints/products.py
from app.api.deps import (
    CurrentUser,
    ProductServiceDep,
    Pagination,
    rate_limit_default,
)

@router.get("/")
async def list_products(
    service: ProductServiceDep,
    current_user: CurrentUser,
    pagination: Pagination,
    _: Annotated[None, Depends(rate_limit_default)],
):
    return await service.list(
        page=pagination.page,
        page_size=pagination.page_size,
    )
```
