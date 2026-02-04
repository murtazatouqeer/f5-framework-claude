---
name: fastapi-api-key-auth
description: API Key authentication for FastAPI
applies_to: fastapi
category: skill
---

# API Key Authentication

## Overview

API Key authentication is useful for machine-to-machine communication,
third-party integrations, and webhook endpoints.

## API Key Model

```python
# app/models/api_key.py
import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY

from app.models.base import BaseModel


class APIKey(BaseModel):
    """API Key model."""

    __tablename__ = "api_keys"

    # Key identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(String(8), nullable=False)  # For display
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

    # Ownership
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped["User"] = relationship(back_populates="api_keys")

    # Permissions
    scopes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)

    @staticmethod
    def generate_key() -> tuple[str, str, str]:
        """Generate API key, prefix, and hash.

        Returns:
            Tuple of (full_key, prefix, hash)
        """
        # Generate random key
        key = secrets.token_urlsafe(32)
        prefix = key[:8]

        # Hash the key for storage
        import hashlib
        key_hash = hashlib.sha256(key.encode()).hexdigest()

        return key, prefix, key_hash

    @staticmethod
    def hash_key(key: str) -> str:
        """Hash an API key."""
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()

    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if self.expires_at is None:
            return False
        return datetime.now(self.expires_at.tzinfo) > self.expires_at

    @property
    def is_valid(self) -> bool:
        """Check if key is valid for use."""
        return self.is_active and not self.is_expired
```

## API Key Schemas

```python
# app/schemas/api_key.py
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: str = Field(..., min_length=1, max_length=100)
    scopes: list[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    description: Optional[str] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response (without actual key)."""
    id: UUID
    name: str
    key_prefix: str
    scopes: list[str]
    is_active: bool
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyResponse):
    """Schema for newly created API key (includes actual key)."""
    key: str  # Full key - only shown once on creation
```

## API Key Security Scheme

```python
# app/core/api_key.py
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, APIKeyQuery

from app.models.api_key import APIKey

# Support API key in header or query parameter
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_key_query = APIKeyQuery(name="api_key", auto_error=False)


async def get_api_key(
    header_key: Optional[str] = Security(api_key_header),
    query_key: Optional[str] = Security(api_key_query),
) -> str:
    """Extract API key from header or query parameter."""
    api_key = header_key or query_key

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )

    return api_key
```

## API Key Dependencies

```python
# app/api/deps.py
from typing import Annotated
from datetime import datetime, timezone
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.api_key import APIKey
from app.models.user import User
from app.core.api_key import get_api_key


async def validate_api_key(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[str, Depends(get_api_key)],
) -> APIKey:
    """Validate API key and return the key object."""
    key_hash = APIKey.hash_key(api_key)

    stmt = select(APIKey).where(
        APIKey.key_hash == key_hash,
        APIKey.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    key_obj = result.scalar_one_or_none()

    if not key_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not key_obj.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is disabled",
        )

    if key_obj.is_expired:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired",
        )

    # Update last used timestamp
    key_obj.last_used_at = datetime.now(timezone.utc)
    await db.flush()

    return key_obj


async def get_api_key_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    api_key: Annotated[APIKey, Depends(validate_api_key)],
) -> User:
    """Get the user associated with the API key."""
    stmt = select(User).where(User.id == api_key.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


# Type aliases
ValidAPIKey = Annotated[APIKey, Depends(validate_api_key)]
APIKeyUser = Annotated[User, Depends(get_api_key_user)]


# Scope checking dependency
class RequireScopes:
    """Dependency to require specific API key scopes."""

    def __init__(self, required_scopes: list[str]):
        self.required_scopes = required_scopes

    async def __call__(
        self,
        api_key: ValidAPIKey,
    ) -> APIKey:
        if not api_key.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key has no scopes",
            )

        # Check if all required scopes are present
        missing_scopes = set(self.required_scopes) - set(api_key.scopes)
        if missing_scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scopes: {', '.join(missing_scopes)}",
            )

        return api_key
```

## API Key Service

```python
# app/services/api_key.py
from typing import Sequence, Optional
from uuid import UUID
from datetime import datetime

from app.models.api_key import APIKey
from app.models.user import User
from app.repositories.api_key import APIKeyRepository
from app.schemas.api_key import APIKeyCreate, APIKeyCreated


class APIKeyService:
    """API Key management service."""

    def __init__(self, repository: APIKeyRepository):
        self._repo = repository

    async def create(
        self,
        data: APIKeyCreate,
        user: User,
    ) -> APIKeyCreated:
        """Create new API key for user."""
        # Generate key
        full_key, prefix, key_hash = APIKey.generate_key()

        # Create key record
        api_key = await self._repo.create_from_dict({
            "name": data.name,
            "key_prefix": prefix,
            "key_hash": key_hash,
            "user_id": user.id,
            "scopes": data.scopes,
            "expires_at": data.expires_at,
            "description": data.description,
        })

        # Return response with full key (only time it's shown)
        return APIKeyCreated(
            id=api_key.id,
            name=api_key.name,
            key_prefix=api_key.key_prefix,
            key=full_key,  # Include full key only on creation
            scopes=api_key.scopes or [],
            is_active=api_key.is_active,
            expires_at=api_key.expires_at,
            last_used_at=api_key.last_used_at,
            created_at=api_key.created_at,
        )

    async def list_user_keys(
        self,
        user: User,
    ) -> Sequence[APIKey]:
        """List all API keys for a user."""
        return await self._repo.get_by_user(user.id)

    async def revoke(
        self,
        key_id: UUID,
        user: User,
    ) -> bool:
        """Revoke (deactivate) an API key."""
        api_key = await self._repo.get_by_id(key_id)

        if not api_key or api_key.user_id != user.id:
            return False

        await self._repo.update(key_id, is_active=False)
        return True

    async def delete(
        self,
        key_id: UUID,
        user: User,
    ) -> bool:
        """Delete an API key."""
        api_key = await self._repo.get_by_id(key_id)

        if not api_key or api_key.user_id != user.id:
            return False

        return await self._repo.delete(key_id)
```

## API Key Endpoints

```python
# app/api/v1/endpoints/api_keys.py
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, get_api_key_service
from app.services.api_key import APIKeyService
from app.schemas.api_key import APIKeyCreate, APIKeyResponse, APIKeyCreated

router = APIRouter()


@router.post("/", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    current_user: CurrentUser,
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
):
    """Create new API key.

    **Important**: The full API key is only returned once on creation.
    Store it securely as it cannot be retrieved again.
    """
    return await service.create(data, current_user)


@router.get("/", response_model=list[APIKeyResponse])
async def list_api_keys(
    current_user: CurrentUser,
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
):
    """List all API keys for current user."""
    return await service.list_user_keys(current_user)


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
):
    """Delete an API key."""
    success = await service.delete(key_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    return {"message": "API key deleted"}


@router.post("/{key_id}/revoke")
async def revoke_api_key(
    key_id: UUID,
    current_user: CurrentUser,
    service: Annotated[APIKeyService, Depends(get_api_key_service)],
):
    """Revoke an API key (deactivate without deleting)."""
    success = await service.revoke(key_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    return {"message": "API key revoked"}
```

## Using API Key Auth in Endpoints

```python
# app/api/v1/endpoints/webhooks.py
from typing import Annotated
from fastapi import APIRouter, Depends

from app.api.deps import ValidAPIKey, APIKeyUser, RequireScopes
from app.models.api_key import APIKey
from app.models.user import User

router = APIRouter()


@router.post("/webhook/orders")
async def receive_order_webhook(
    api_key: ValidAPIKey,
    payload: dict,
):
    """Receive order webhook (requires any valid API key)."""
    # api_key.scopes contains the key's permissions
    return {"status": "received"}


@router.post("/webhook/inventory")
async def receive_inventory_webhook(
    api_key: Annotated[APIKey, Depends(RequireScopes(["inventory:write"]))],
    payload: dict,
):
    """Receive inventory webhook (requires specific scope)."""
    return {"status": "received"}


@router.get("/external/products")
async def external_get_products(
    user: APIKeyUser,  # Get the user associated with the API key
):
    """External API endpoint authenticated via API key."""
    return {"user_id": str(user.id), "products": []}
```

## Best Practices

1. **Hash API keys** before storing (use SHA-256)
2. **Show key only once** on creation
3. **Use prefixes** for key identification in logs
4. **Implement scopes** for fine-grained permissions
5. **Set expiration dates** for temporary keys
6. **Track last used** timestamp for auditing
7. **Rate limit** API key endpoints
8. **Log API key usage** for security monitoring
