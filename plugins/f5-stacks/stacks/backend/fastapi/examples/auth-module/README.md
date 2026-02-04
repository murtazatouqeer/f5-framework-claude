# FastAPI Authentication Module Example

Complete authentication module with JWT tokens, user management, and role-based access control.

## Directory Structure

```
auth-module/
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings with JWT config
│   │   ├── database.py         # Database connection
│   │   ├── security.py         # Password hashing, JWT
│   │   └── exceptions.py       # Auth exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base model
│   │   ├── user.py             # User model
│   │   └── role.py             # Role model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py             # Auth schemas
│   │   ├── user.py             # User schemas
│   │   └── token.py            # Token schemas
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── user.py             # User repository
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py             # Auth service
│   │   └── user.py             # User service
│   └── api/
│       ├── __init__.py
│       ├── deps.py             # Auth dependencies
│       └── v1/
│           ├── __init__.py
│           ├── router.py
│           └── endpoints/
│               ├── __init__.py
│               ├── auth.py     # Auth endpoints
│               └── users.py    # User endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── api/
│       ├── __init__.py
│       ├── test_auth.py
│       └── test_users.py
├── alembic/
├── pyproject.toml
└── .env.example
```

## Implementation

### 1. Security Configuration (`app/core/config.py`)

```python
"""Application configuration with JWT settings."""
from datetime import timedelta
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API
    app_name: str = "Auth Module Example"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/db"

    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Password
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_digit: bool = True

    @property
    def access_token_expire(self) -> timedelta:
        return timedelta(minutes=self.access_token_expire_minutes)

    @property
    def refresh_token_expire(self) -> timedelta:
        return timedelta(days=self.refresh_token_expire_days)

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

### 2. Security Utilities (`app/core/security.py`)

```python
"""Security utilities: password hashing and JWT."""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[dict[str, Any]] = None,
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + settings.access_token_expire

    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }

    if extra_data:
        to_encode.update(extra_data)

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def create_refresh_token(subject: str) -> str:
    """Create JWT refresh token."""
    expire = datetime.now(timezone.utc) + settings.refresh_token_expire

    to_encode = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
    }

    return jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except JWTError:
        return None
```

### 3. User Model (`app/models/user.py`)

```python
"""User database model."""
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, Base

if TYPE_CHECKING:
    from app.models.role import Role

# Association table for user-role many-to-many
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class User(BaseModel):
    """User model."""

    __tablename__ = "users"

    # Identity
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    roles: Mapped[List["Role"]] = relationship(
        secondary=user_roles,
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True
        return any(
            permission in role.permissions
            for role in self.roles
        )
```

### 4. Role Model (`app/models/role.py`)

```python
"""Role database model."""
from typing import TYPE_CHECKING, List

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.user import user_roles

if TYPE_CHECKING:
    from app.models.user import User


class Role(BaseModel):
    """Role model for RBAC."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(255))
    permissions: Mapped[list] = mapped_column(JSON, default=list)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )

    def __repr__(self) -> str:
        return f"<Role {self.name}>"
```

### 5. Auth Schemas (`app/schemas/auth.py`)

```python
"""Authentication schemas."""
import re
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.config import settings


class LoginRequest(BaseModel):
    """Schema for login request."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RegisterRequest(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=settings.password_min_length)
    full_name: Optional[str] = Field(None, max_length=255)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscores, and hyphens")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if settings.password_require_uppercase and not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if settings.password_require_digit and not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""

    refresh_token: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""

    token: str
    new_password: str = Field(..., min_length=settings.password_min_length)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if settings.password_require_uppercase and not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if settings.password_require_digit and not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v


class ChangePasswordRequest(BaseModel):
    """Schema for changing password."""

    current_password: str
    new_password: str = Field(..., min_length=settings.password_min_length)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if settings.password_require_uppercase and not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if settings.password_require_digit and not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one digit")
        return v
```

### 6. Token Schemas (`app/schemas/token.py`)

```python
"""Token schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime


class TokenPayload(BaseModel):
    """Token payload schema."""

    sub: str
    exp: datetime
    type: str
    roles: Optional[list[str]] = None
    permissions: Optional[list[str]] = None
```

### 7. User Schemas (`app/schemas/user.py`)

```python
"""User schemas."""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user."""

    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: Optional[str] = Field(None, max_length=255)
    avatar_url: Optional[str] = Field(None, max_length=500)

    model_config = ConfigDict(extra="ignore")


class UserResponse(UserBase):
    """Schema for user response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    is_active: bool
    is_verified: bool
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None


class UserWithRoles(UserResponse):
    """User response with roles."""

    roles: list[str] = []

    @classmethod
    def from_user(cls, user) -> "UserWithRoles":
        return cls(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_verified=user.is_verified,
            avatar_url=user.avatar_url,
            created_at=user.created_at,
            last_login=user.last_login,
            roles=[role.name for role in user.roles],
        )
```

### 8. Auth Service (`app/services/auth.py`)

```python
"""Authentication service."""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    UserNotFoundError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.token import Token


class AuthService:
    """Authentication service."""

    def __init__(self, user_repository: UserRepository):
        self._user_repo = user_repository

    async def register(self, data: RegisterRequest) -> User:
        """Register a new user."""
        # Check email uniqueness
        existing = await self._user_repo.get_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        # Check username uniqueness
        existing = await self._user_repo.get_by_username(data.username)
        if existing:
            raise ValueError("Username already taken")

        # Create user
        user = await self._user_repo.create({
            "email": data.email,
            "username": data.username,
            "full_name": data.full_name,
            "hashed_password": get_password_hash(data.password),
        })

        return user

    async def login(self, data: LoginRequest) -> Token:
        """Authenticate user and return tokens."""
        user = await self._user_repo.get_by_email(data.email)

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(data.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        # Update last login
        await self._user_repo.update(
            user.id,
            {"last_login": datetime.now(timezone.utc)},
        )

        # Generate tokens
        return self._create_tokens(user)

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)

        if not payload:
            raise InvalidTokenError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")

        user_id = payload.get("sub")
        user = await self._user_repo.get_by_id(UUID(user_id))

        if not user:
            raise UserNotFoundError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        return self._create_tokens(user)

    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user password."""
        user = await self._user_repo.get_by_id(user_id)

        if not user:
            raise UserNotFoundError("User not found")

        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        await self._user_repo.update(
            user_id,
            {"hashed_password": get_password_hash(new_password)},
        )

    async def get_current_user(self, token: str) -> User:
        """Get current user from access token."""
        payload = decode_token(token)

        if not payload:
            raise InvalidTokenError("Invalid access token")

        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")

        user_id = payload.get("sub")
        user = await self._user_repo.get_by_id(UUID(user_id))

        if not user:
            raise UserNotFoundError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        return user

    def _create_tokens(self, user: User) -> Token:
        """Create access and refresh tokens for user."""
        from datetime import datetime, timezone
        from app.core.config import settings

        # Collect roles and permissions
        roles = [role.name for role in user.roles]
        permissions = []
        for role in user.roles:
            permissions.extend(role.permissions)

        access_token = create_access_token(
            subject=str(user.id),
            extra_data={
                "roles": roles,
                "permissions": list(set(permissions)),
            },
        )

        refresh_token = create_refresh_token(subject=str(user.id))

        expires_at = datetime.now(timezone.utc) + settings.access_token_expire

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
```

### 9. Auth Dependencies (`app/api/deps.py`)

```python
"""API dependencies for authentication."""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.auth import AuthService

security = HTTPBearer()

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_auth_service(db: DBSession) -> AuthService:
    """Provide AuthService dependency."""
    repository = UserRepository(db)
    return AuthService(repository)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: AuthServiceDep,
) -> User:
    """Get current authenticated user."""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_active_user(current_user: CurrentUser) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


ActiveUser = Annotated[User, Depends(get_current_active_user)]


async def get_current_superuser(current_user: CurrentUser) -> User:
    """Get current superuser."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser required",
        )
    return current_user


SuperUser = Annotated[User, Depends(get_current_superuser)]


class RequirePermission:
    """Dependency for requiring specific permission."""

    def __init__(self, permission: str):
        self.permission = permission

    async def __call__(self, current_user: CurrentUser) -> User:
        if not current_user.has_permission(self.permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {self.permission}",
            )
        return current_user


class RequireRole:
    """Dependency for requiring specific role."""

    def __init__(self, role: str):
        self.role = role

    async def __call__(self, current_user: CurrentUser) -> User:
        if not current_user.has_role(self.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {self.role}",
            )
        return current_user


# Usage examples:
# @router.get("/admin", dependencies=[Depends(RequireRole("admin"))])
# @router.delete("/users/{id}", dependencies=[Depends(RequirePermission("users:delete"))])
```

### 10. Auth Endpoints (`app/api/v1/endpoints/auth.py`)

```python
"""Authentication API endpoints."""
from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep, CurrentUser
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
)
from app.schemas.response import APIResponse
from app.schemas.token import Token
from app.schemas.user import UserResponse, UserWithRoles

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
)
async def register(data: RegisterRequest, auth_service: AuthServiceDep):
    """Register a new user."""
    user = await auth_service.register(data)
    return APIResponse(success=True, data=UserResponse.model_validate(user))


@router.post("/login", response_model=APIResponse[Token])
async def login(data: LoginRequest, auth_service: AuthServiceDep):
    """Authenticate user and return tokens."""
    token = await auth_service.login(data)
    return APIResponse(success=True, data=token)


@router.post("/refresh", response_model=APIResponse[Token])
async def refresh_token(data: RefreshTokenRequest, auth_service: AuthServiceDep):
    """Refresh access token."""
    token = await auth_service.refresh_tokens(data.refresh_token)
    return APIResponse(success=True, data=token)


@router.get("/me", response_model=APIResponse[UserWithRoles])
async def get_current_user_info(current_user: CurrentUser):
    """Get current user information."""
    return APIResponse(
        success=True,
        data=UserWithRoles.from_user(current_user),
    )


@router.post("/change-password", response_model=APIResponse[dict])
async def change_password(
    data: ChangePasswordRequest,
    current_user: CurrentUser,
    auth_service: AuthServiceDep,
):
    """Change current user's password."""
    await auth_service.change_password(
        current_user.id,
        data.current_password,
        data.new_password,
    )
    return APIResponse(success=True, data={"message": "Password changed successfully"})


@router.post("/logout", response_model=APIResponse[dict])
async def logout(current_user: CurrentUser):
    """Logout current user (client should discard tokens)."""
    # In a real implementation, you might want to:
    # - Add the token to a blacklist
    # - Invalidate refresh tokens in database
    return APIResponse(success=True, data={"message": "Logged out successfully"})
```

### 11. User Endpoints (`app/api/v1/endpoints/users.py`)

```python
"""User management API endpoints."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import (
    ActiveUser,
    CurrentUser,
    RequirePermission,
    SuperUser,
)
from app.schemas.response import APIResponse
from app.schemas.user import UserResponse, UserUpdate, UserWithRoles
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=APIResponse[list[UserResponse]],
    dependencies=[Depends(RequirePermission("users:read"))],
)
async def list_users(
    user_service: UserService,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List all users (requires users:read permission)."""
    users = await user_service.list(page=page, page_size=page_size)
    return APIResponse(
        success=True,
        data=[UserResponse.model_validate(u) for u in users],
    )


@router.get("/{id}", response_model=APIResponse[UserWithRoles])
async def get_user(
    id: UUID,
    current_user: CurrentUser,
    user_service: UserService,
):
    """Get user by ID."""
    # Users can view their own profile, admins can view any
    if id != current_user.id and not current_user.is_superuser:
        if not current_user.has_permission("users:read"):
            raise HTTPException(status_code=403, detail="Permission denied")

    user = await user_service.get_by_id(id)
    return APIResponse(success=True, data=UserWithRoles.from_user(user))


@router.put("/{id}", response_model=APIResponse[UserResponse])
async def update_user(
    id: UUID,
    data: UserUpdate,
    current_user: CurrentUser,
    user_service: UserService,
):
    """Update user by ID."""
    # Users can update their own profile, admins can update any
    if id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Permission denied")

    user = await user_service.update(id, data)
    return APIResponse(success=True, data=UserResponse.model_validate(user))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequirePermission("users:delete"))],
)
async def delete_user(
    id: UUID,
    current_user: SuperUser,
    user_service: UserService,
):
    """Delete user by ID (superuser only)."""
    if id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    await user_service.delete(id)
    return None


@router.post(
    "/{id}/roles/{role_name}",
    response_model=APIResponse[UserWithRoles],
    dependencies=[Depends(RequirePermission("users:manage_roles"))],
)
async def assign_role(
    id: UUID,
    role_name: str,
    user_service: UserService,
):
    """Assign role to user."""
    user = await user_service.assign_role(id, role_name)
    return APIResponse(success=True, data=UserWithRoles.from_user(user))


@router.delete(
    "/{id}/roles/{role_name}",
    response_model=APIResponse[UserWithRoles],
    dependencies=[Depends(RequirePermission("users:manage_roles"))],
)
async def remove_role(
    id: UUID,
    role_name: str,
    user_service: UserService,
):
    """Remove role from user."""
    user = await user_service.remove_role(id, role_name)
    return APIResponse(success=True, data=UserWithRoles.from_user(user))
```

## Testing

### Auth Tests (`tests/api/test_auth.py`)

```python
"""Authentication API tests."""
import pytest
from httpx import AsyncClient


class TestRegister:
    """Tests for POST /auth/register"""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful registration."""
        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "Password123",
            "full_name": "Test User",
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration with weak password."""
        payload = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422


class TestLogin:
    """Tests for POST /auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        payload = {
            "email": test_user.email,
            "password": "Password123",
        }

        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, client: AsyncClient, test_user):
        """Test login with invalid password."""
        payload = {
            "email": test_user.email,
            "password": "wrongpassword",
        }

        response = await client.post("/api/v1/auth/login", json=payload)

        assert response.status_code == 401


class TestRefreshToken:
    """Tests for POST /auth/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_success(self, client: AsyncClient, auth_tokens):
        """Test successful token refresh."""
        payload = {"refresh_token": auth_tokens["refresh_token"]}

        response = await client.post("/api/v1/auth/refresh", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]


class TestGetCurrentUser:
    """Tests for GET /auth/me"""

    @pytest.mark.asyncio
    async def test_get_current_user(self, authenticated_client: AsyncClient):
        """Test getting current user info."""
        response = await authenticated_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "email" in data["data"]

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without auth."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
```

## Running the Example

```bash
# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export SECRET_KEY="your-secret-key"
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db"

# Set up database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest -v
```

## API Endpoints Summary

### Authentication

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | /auth/register | Register new user | No |
| POST | /auth/login | Login and get tokens | No |
| POST | /auth/refresh | Refresh access token | No |
| GET | /auth/me | Get current user | Yes |
| POST | /auth/change-password | Change password | Yes |
| POST | /auth/logout | Logout | Yes |

### Users

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | /users/ | List users | users:read |
| GET | /users/{id} | Get user | Owner/Admin |
| PUT | /users/{id} | Update user | Owner/Admin |
| DELETE | /users/{id} | Delete user | users:delete |
| POST | /users/{id}/roles/{role} | Assign role | users:manage_roles |
| DELETE | /users/{id}/roles/{role} | Remove role | users:manage_roles |

## Key Patterns Demonstrated

1. **JWT Authentication**: Access and refresh token flow
2. **Password Security**: Bcrypt hashing with strength validation
3. **RBAC**: Role-based access control with permissions
4. **Dependency Injection**: Auth dependencies for endpoints
5. **Token Refresh**: Secure token rotation
6. **Permission Guards**: RequirePermission and RequireRole
7. **User Management**: Self-service and admin operations
8. **Secure Defaults**: Strong password requirements, token expiry
