---
name: fastapi-oauth2-jwt
description: OAuth2 with JWT authentication for FastAPI
applies_to: fastapi
category: skill
---

# OAuth2 with JWT Authentication

## Dependencies

```bash
pip install python-jose[cryptography] passlib[bcrypt] python-multipart
```

## Security Configuration

```python
# app/core/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Password Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True


settings = Settings()
```

## Password Hashing

```python
# app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)
```

## JWT Token Creation

```python
# app/core/security.py (continued)
from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError

from app.config import settings


def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    extra_claims: dict | None = None,
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }

    if extra_claims:
        to_encode.update(extra_claims)

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
) -> str:
    """Create JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
```

## Token Schemas

```python
# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    sub: str
    type: str
    exp: int


class LoginRequest(BaseModel):
    """Login request schema."""
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request schema."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    new_password: str = Field(..., min_length=8)
```

## OAuth2 Dependencies

```python
# app/api/deps.py
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.core.security import decode_token
from app.models.user import User
from app.repositories.user import UserRepository

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login"
)

# Optional auth - returns None if no token
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    # Check token type
    if payload.get("type") != "access":
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return user


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    token: Annotated[str | None, Depends(oauth2_scheme_optional)],
) -> User | None:
    """Get current user if authenticated, None otherwise."""
    if not token:
        return None

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    user_repo = UserRepository(db)
    return await user_repo.get_by_id(user_id)


# Type aliases
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_current_user_optional)]
```

## Auth Service

```python
# app/services/auth.py
from datetime import timedelta
from typing import Optional

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.config import settings
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.auth import Token
from app.core.exceptions import AuthenticationError, NotFoundError


class AuthService:
    """Authentication service."""

    def __init__(self, user_repository: UserRepository):
        self._user_repo = user_repository

    async def authenticate(
        self,
        email: str,
        password: str,
    ) -> User:
        """Authenticate user with email and password."""
        user = await self._user_repo.get_by_email(email)

        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is disabled")

        return user

    async def login(self, email: str, password: str) -> Token:
        """Login and return tokens."""
        user = await self.authenticate(email, password)

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email},
        )
        refresh_token = create_refresh_token(subject=str(user.id))

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
        )

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """Refresh access token using refresh token."""
        payload = decode_token(refresh_token)

        if not payload:
            raise AuthenticationError("Invalid refresh token")

        if payload.get("type") != "refresh":
            raise AuthenticationError("Invalid token type")

        user_id = payload.get("sub")
        user = await self._user_repo.get_by_id(user_id)

        if not user or not user.is_active:
            raise AuthenticationError("User not found or inactive")

        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email},
        )
        new_refresh_token = create_refresh_token(subject=str(user.id))

        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
        )

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> bool:
        """Change user password."""
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        hashed = get_password_hash(new_password)
        await self._user_repo.update(user.id, hashed_password=hashed)
        return True
```

## Auth Endpoints

```python
# app/api/v1/endpoints/auth.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_db, get_auth_service, CurrentUser
from app.services.auth import AuthService
from app.schemas.auth import (
    Token,
    RefreshTokenRequest,
    PasswordChangeRequest,
)
from app.core.exceptions import AuthenticationError

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Login with email and password.

    Returns access and refresh tokens.
    """
    try:
        return await auth_service.login(
            email=form_data.username,  # OAuth2 spec uses 'username'
            password=form_data.password,
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Refresh access token using refresh token."""
    try:
        return await auth_service.refresh_tokens(request.refresh_token)
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: CurrentUser,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Change current user's password."""
    try:
        await auth_service.change_password(
            user=current_user,
            current_password=request.current_password,
            new_password=request.new_password,
        )
        return {"message": "Password changed successfully"}
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/me")
async def get_current_user_info(current_user: CurrentUser):
    """Get current authenticated user info."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "is_active": current_user.is_active,
    }
```

## Best Practices

1. **Use bcrypt** for password hashing (included in passlib)
2. **Short-lived access tokens** (15-30 minutes)
3. **Long-lived refresh tokens** (7-30 days)
4. **Include token type** in payload to prevent misuse
5. **Validate token type** in dependencies
6. **Store refresh tokens** in database for revocation
7. **Use HTTPS** in production
8. **Implement rate limiting** on auth endpoints
