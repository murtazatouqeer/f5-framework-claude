---
name: fastapi-clean-architecture
description: Clean Architecture implementation in FastAPI
applies_to: fastapi
category: skill
---

# Clean Architecture in FastAPI

## Overview

Clean Architecture separates concerns into layers with dependencies pointing inward.
The core business logic is independent of frameworks, databases, and external services.

## Layer Structure

```
app/
├── domain/                    # Enterprise Business Rules
│   ├── entities/             # Business entities
│   ├── value_objects/        # Value objects
│   ├── exceptions/           # Domain exceptions
│   └── interfaces/           # Abstract repositories
│
├── application/              # Application Business Rules
│   ├── use_cases/           # Use case implementations
│   ├── dto/                 # Data transfer objects
│   └── interfaces/          # Service interfaces
│
├── infrastructure/           # Frameworks & Drivers
│   ├── database/            # Database implementation
│   ├── repositories/        # Repository implementations
│   ├── external/            # External service clients
│   └── cache/               # Caching implementation
│
└── presentation/            # Interface Adapters
    ├── api/                 # FastAPI routes
    ├── schemas/             # API schemas (Pydantic)
    └── dependencies/        # FastAPI dependencies
```

## Domain Layer

### Entity

```python
# app/domain/entities/user.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

from app.domain.value_objects.email import Email
from app.domain.value_objects.password import HashedPassword
from app.domain.exceptions import DomainError


@dataclass
class User:
    """User domain entity."""

    id: UUID = field(default_factory=uuid4)
    email: Email = field(default=None)
    password: HashedPassword = field(default=None)
    name: str = ""
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self._touch()

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self._touch()

    def verify(self) -> None:
        """Mark email as verified."""
        if self.is_verified:
            raise DomainError("User already verified")
        self.is_verified = True
        self._touch()

    def update_email(self, new_email: Email) -> None:
        """Update email address."""
        self.email = new_email
        self.is_verified = False  # Require re-verification
        self._touch()

    def _touch(self) -> None:
        """Update timestamp."""
        self.updated_at = datetime.utcnow()
```

### Value Object

```python
# app/domain/value_objects/email.py
from dataclasses import dataclass
import re

from app.domain.exceptions import InvalidEmailError


@dataclass(frozen=True)
class Email:
    """Email value object with validation."""

    value: str

    def __post_init__(self):
        if not self._is_valid(self.value):
            raise InvalidEmailError(f"Invalid email: {self.value}")

    @staticmethod
    def _is_valid(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def __str__(self) -> str:
        return self.value


# app/domain/value_objects/password.py
from dataclasses import dataclass
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(frozen=True)
class HashedPassword:
    """Hashed password value object."""

    value: str

    @classmethod
    def from_plain(cls, plain_password: str) -> "HashedPassword":
        """Create hashed password from plain text."""
        if len(plain_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        hashed = pwd_context.hash(plain_password)
        return cls(value=hashed)

    def verify(self, plain_password: str) -> bool:
        """Verify plain password against hash."""
        return pwd_context.verify(plain_password, self.value)
```

### Domain Exceptions

```python
# app/domain/exceptions.py
class DomainError(Exception):
    """Base domain exception."""
    pass


class InvalidEmailError(DomainError):
    """Invalid email format."""
    pass


class EntityNotFoundError(DomainError):
    """Entity not found."""
    pass


class BusinessRuleViolationError(DomainError):
    """Business rule violation."""
    pass
```

### Repository Interface

```python
# app/domain/interfaces/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, Sequence
from uuid import UUID

from app.domain.entities.user import User
from app.domain.value_objects.email import Email


class IUserRepository(ABC):
    """User repository interface."""

    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        pass

    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        """Save user (create or update)."""
        pass

    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """Delete user."""
        pass

    @abstractmethod
    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[User]:
        """List users with pagination."""
        pass
```

## Application Layer

### Use Case

```python
# app/application/use_cases/register_user.py
from dataclasses import dataclass
from uuid import UUID

from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import HashedPassword
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.exceptions import BusinessRuleViolationError
from app.application.interfaces.email_service import IEmailService


@dataclass
class RegisterUserInput:
    """Input DTO for user registration."""
    email: str
    password: str
    name: str


@dataclass
class RegisterUserOutput:
    """Output DTO for user registration."""
    id: UUID
    email: str
    name: str


class RegisterUserUseCase:
    """Use case for user registration."""

    def __init__(
        self,
        user_repository: IUserRepository,
        email_service: IEmailService,
    ):
        self._user_repo = user_repository
        self._email_service = email_service

    async def execute(self, input_data: RegisterUserInput) -> RegisterUserOutput:
        """Execute user registration."""
        # Validate email format
        email = Email(input_data.email)

        # Check if user exists
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise BusinessRuleViolationError("Email already registered")

        # Create user entity
        user = User(
            email=email,
            password=HashedPassword.from_plain(input_data.password),
            name=input_data.name,
        )

        # Persist user
        saved_user = await self._user_repo.save(user)

        # Send verification email
        await self._email_service.send_verification_email(
            to=str(saved_user.email),
            user_id=saved_user.id,
        )

        return RegisterUserOutput(
            id=saved_user.id,
            email=str(saved_user.email),
            name=saved_user.name,
        )
```

### Service Interface

```python
# app/application/interfaces/email_service.py
from abc import ABC, abstractmethod
from uuid import UUID


class IEmailService(ABC):
    """Email service interface."""

    @abstractmethod
    async def send_verification_email(self, to: str, user_id: UUID) -> None:
        """Send email verification."""
        pass

    @abstractmethod
    async def send_password_reset_email(self, to: str, token: str) -> None:
        """Send password reset email."""
        pass
```

## Infrastructure Layer

### Repository Implementation

```python
# app/infrastructure/repositories/user_repository.py
from typing import Optional, Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.user import User
from app.domain.value_objects.email import Email
from app.domain.value_objects.password import HashedPassword
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.database.models import UserModel


class UserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.email == str(email))
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, user: User) -> User:
        model = self._to_model(user)
        merged = await self._session.merge(model)
        await self._session.flush()
        await self._session.refresh(merged)
        return self._to_entity(merged)

    async def delete(self, user_id: UUID) -> bool:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            return True
        return False

    async def list(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        stmt = select(UserModel).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars().all()]

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        """Convert database model to domain entity."""
        return User(
            id=model.id,
            email=Email(model.email),
            password=HashedPassword(model.hashed_password),
            name=model.name,
            is_active=model.is_active,
            is_verified=model.is_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        """Convert domain entity to database model."""
        return UserModel(
            id=entity.id,
            email=str(entity.email),
            hashed_password=entity.password.value,
            name=entity.name,
            is_active=entity.is_active,
            is_verified=entity.is_verified,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
```

### Database Model

```python
# app/infrastructure/database/models.py
from datetime import datetime
from uuid import UUID
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class UserModel(Base):
    """User database model."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    updated_at: Mapped[datetime] = mapped_column(DateTime)
```

## Presentation Layer

### API Schema

```python
# app/presentation/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID


class UserRegisterRequest(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)


class UserResponse(BaseModel):
    """User response schema."""
    id: UUID
    email: str
    name: str

    model_config = {"from_attributes": True}
```

### API Endpoint

```python
# app/presentation/api/v1/endpoints/users.py
from fastapi import APIRouter, Depends, status
from typing import Annotated

from app.presentation.schemas.user import UserRegisterRequest, UserResponse
from app.presentation.dependencies import get_register_user_use_case
from app.application.use_cases.register_user import (
    RegisterUserUseCase,
    RegisterUserInput,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: UserRegisterRequest,
    use_case: Annotated[RegisterUserUseCase, Depends(get_register_user_use_case)],
):
    """Register a new user."""
    input_data = RegisterUserInput(
        email=request.email,
        password=request.password,
        name=request.name,
    )
    result = await use_case.execute(input_data)
    return UserResponse(
        id=result.id,
        email=result.email,
        name=result.name,
    )
```

### Dependencies

```python
# app/presentation/dependencies.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.session import get_db
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.external.email_service import EmailService
from app.application.use_cases.register_user import RegisterUserUseCase


def get_register_user_use_case(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RegisterUserUseCase:
    """Dependency for RegisterUserUseCase."""
    user_repo = UserRepository(db)
    email_service = EmailService()
    return RegisterUserUseCase(user_repo, email_service)
```

## Benefits

1. **Testability**: Business logic can be tested without infrastructure
2. **Flexibility**: Easy to swap implementations (e.g., different database)
3. **Maintainability**: Clear separation of concerns
4. **Independence**: Domain logic is framework-agnostic

## Best Practices

1. **Keep domain entities pure** - no framework dependencies
2. **Use interfaces** for infrastructure dependencies
3. **Implement use cases** as single-purpose classes
4. **Map between layers** using DTOs and schema transformations
5. **Test use cases** with mock repositories
