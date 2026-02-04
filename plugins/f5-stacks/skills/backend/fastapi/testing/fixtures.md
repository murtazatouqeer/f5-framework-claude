---
name: fastapi-fixtures
description: Test fixtures and factories for FastAPI testing
applies_to: fastapi
category: skill
---

# Test Fixtures for FastAPI

## Database Fixtures

### Session Fixtures

```python
# tests/conftest.py
import pytest
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.database import Base


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine (session-scoped)."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create fresh database session for each test."""
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def db_session_with_transaction(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Session with outer transaction for isolation."""
    async with test_engine.connect() as connection:
        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with session_factory() as session:
            yield session

        await transaction.rollback()
```

### PostgreSQL Test Database

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
import asyncpg

from app.database import Base

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/test_db"


@pytest.fixture(scope="session")
async def test_engine():
    """Create PostgreSQL test engine."""
    # Create test database
    conn = await asyncpg.connect(
        "postgresql://test:test@localhost:5432/postgres"
    )
    try:
        await conn.execute("DROP DATABASE IF EXISTS test_db")
        await conn.execute("CREATE DATABASE test_db")
    finally:
        await conn.close()

    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()

    # Drop test database
    conn = await asyncpg.connect(
        "postgresql://test:test@localhost:5432/postgres"
    )
    try:
        await conn.execute("DROP DATABASE IF EXISTS test_db")
    finally:
        await conn.close()
```

## Model Fixtures

### User Fixtures

```python
# tests/fixtures/users.py
import pytest
from uuid import uuid4
from datetime import datetime

from app.models.user import User
from app.core.security import hash_password


@pytest.fixture
async def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password=hash_password("TestPass123!"),
        name="Test User",
        is_active=True,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def admin_user(db_session) -> User:
    """Create an admin user."""
    user = User(
        id=uuid4(),
        email="admin@example.com",
        hashed_password=hash_password("AdminPass123!"),
        name="Admin User",
        is_active=True,
        is_verified=True,
        is_admin=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(db_session) -> User:
    """Create an inactive user."""
    user = User(
        id=uuid4(),
        email="inactive@example.com",
        hashed_password=hash_password("TestPass123!"),
        name="Inactive User",
        is_active=False,
        is_verified=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def multiple_users(db_session) -> list[User]:
    """Create multiple test users."""
    users = []
    for i in range(5):
        user = User(
            id=uuid4(),
            email=f"user{i}@example.com",
            hashed_password=hash_password("TestPass123!"),
            name=f"User {i}",
            is_active=True,
            is_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(user)
        users.append(user)

    await db_session.commit()
    for user in users:
        await db_session.refresh(user)

    return users
```

### Domain Model Fixtures

```python
# tests/fixtures/products.py
import pytest
from uuid import uuid4
from decimal import Decimal
from datetime import datetime

from app.models.product import Product
from app.models.category import Category


@pytest.fixture
async def test_category(db_session) -> Category:
    """Create a test category."""
    category = Category(
        id=uuid4(),
        name="Test Category",
        slug="test-category",
        description="A test category",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)
    return category


@pytest.fixture
async def test_product(db_session, test_category, test_user) -> Product:
    """Create a test product."""
    product = Product(
        id=uuid4(),
        name="Test Product",
        slug="test-product",
        description="A test product description",
        price=Decimal("29.99"),
        compare_price=Decimal("39.99"),
        sku="TEST-001",
        stock=100,
        status="active",
        category_id=test_category.id,
        created_by_id=test_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


@pytest.fixture
async def multiple_products(
    db_session,
    test_category,
    test_user,
) -> list[Product]:
    """Create multiple test products."""
    products = []
    for i in range(10):
        product = Product(
            id=uuid4(),
            name=f"Product {i}",
            slug=f"product-{i}",
            description=f"Description for product {i}",
            price=Decimal(f"{10 + i}.99"),
            sku=f"PROD-{i:03d}",
            stock=50 + i * 10,
            status="active",
            category_id=test_category.id,
            created_by_id=test_user.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db_session.add(product)
        products.append(product)

    await db_session.commit()
    for product in products:
        await db_session.refresh(product)

    return products
```

## Factory Pattern

### Base Factory

```python
# tests/factories/base.py
from typing import TypeVar, Generic, Type, Any
from uuid import uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base

T = TypeVar("T", bound=Base)


class BaseFactory(Generic[T]):
    """Base factory for creating test models."""

    model_class: Type[T]

    def __init__(self, session: AsyncSession):
        self.session = session

    def get_defaults(self) -> dict[str, Any]:
        """Override to provide default values."""
        return {
            "id": uuid4(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

    async def create(self, **overrides) -> T:
        """Create and persist a model instance."""
        data = {**self.get_defaults(), **overrides}
        instance = self.model_class(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def create_batch(self, count: int, **overrides) -> list[T]:
        """Create multiple instances."""
        instances = []
        for i in range(count):
            # Allow overrides to be functions for dynamic values
            resolved_overrides = {}
            for key, value in overrides.items():
                if callable(value):
                    resolved_overrides[key] = value(i)
                else:
                    resolved_overrides[key] = value

            instance = await self.create(**resolved_overrides)
            instances.append(instance)

        return instances

    def build(self, **overrides) -> T:
        """Build instance without persisting."""
        data = {**self.get_defaults(), **overrides}
        return self.model_class(**data)
```

### Model Factories

```python
# tests/factories/user.py
from app.models.user import User
from app.core.security import hash_password
from tests.factories.base import BaseFactory


class UserFactory(BaseFactory[User]):
    """Factory for User model."""

    model_class = User
    _counter = 0

    def get_defaults(self) -> dict:
        UserFactory._counter += 1
        return {
            **super().get_defaults(),
            "email": f"user{self._counter}@example.com",
            "hashed_password": hash_password("TestPass123!"),
            "name": f"Test User {self._counter}",
            "is_active": True,
            "is_verified": True,
            "is_admin": False,
        }


# tests/factories/product.py
from decimal import Decimal
from app.models.product import Product
from tests.factories.base import BaseFactory


class ProductFactory(BaseFactory[Product]):
    """Factory for Product model."""

    model_class = Product
    _counter = 0

    def get_defaults(self) -> dict:
        ProductFactory._counter += 1
        return {
            **super().get_defaults(),
            "name": f"Product {self._counter}",
            "slug": f"product-{self._counter}",
            "description": f"Description for product {self._counter}",
            "price": Decimal("29.99"),
            "sku": f"PROD-{self._counter:03d}",
            "stock": 100,
            "status": "active",
        }


# Usage in tests
@pytest.fixture
def user_factory(db_session) -> UserFactory:
    return UserFactory(db_session)


@pytest.fixture
def product_factory(db_session) -> ProductFactory:
    return ProductFactory(db_session)


@pytest.mark.asyncio
async def test_with_factory(user_factory: UserFactory):
    user = await user_factory.create(name="Custom Name")
    assert user.name == "Custom Name"


@pytest.mark.asyncio
async def test_batch_create(product_factory: ProductFactory, test_category, test_user):
    products = await product_factory.create_batch(
        5,
        category_id=test_category.id,
        created_by_id=test_user.id,
        name=lambda i: f"Batch Product {i}",
    )
    assert len(products) == 5
```

## Authentication Fixtures

```python
# tests/fixtures/auth.py
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token
from app.models.user import User


@pytest.fixture
def access_token(test_user: User) -> str:
    """Generate access token for test user."""
    return create_access_token(data={"sub": test_user.email})


@pytest.fixture
def refresh_token(test_user: User) -> str:
    """Generate refresh token for test user."""
    return create_refresh_token(data={"sub": test_user.email})


@pytest.fixture
def auth_headers(access_token: str) -> dict[str, str]:
    """Generate auth headers."""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_user: User) -> dict[str, str]:
    """Generate admin auth headers."""
    token = create_access_token(
        data={"sub": admin_user.email, "roles": ["admin"]}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    auth_headers: dict,
) -> AsyncClient:
    """Create authenticated client."""
    client.headers.update(auth_headers)
    yield client
    # Clean up headers
    if "Authorization" in client.headers:
        del client.headers["Authorization"]
```

## API Key Fixtures

```python
# tests/fixtures/api_keys.py
import pytest
from uuid import uuid4
import secrets
from datetime import datetime, timedelta

from app.models.api_key import APIKey
from app.core.security import hash_api_key


@pytest.fixture
async def test_api_key(db_session, test_user) -> tuple[APIKey, str]:
    """Create test API key and return model and raw key."""
    raw_key = secrets.token_urlsafe(32)
    hashed_key = hash_api_key(raw_key)

    api_key = APIKey(
        id=uuid4(),
        key_hash=hashed_key,
        name="Test API Key",
        user_id=test_user.id,
        scopes=["read", "write"],
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=30),
        created_at=datetime.utcnow(),
    )
    db_session.add(api_key)
    await db_session.commit()
    await db_session.refresh(api_key)

    return api_key, raw_key


@pytest.fixture
async def expired_api_key(db_session, test_user) -> tuple[APIKey, str]:
    """Create expired API key."""
    raw_key = secrets.token_urlsafe(32)
    hashed_key = hash_api_key(raw_key)

    api_key = APIKey(
        id=uuid4(),
        key_hash=hashed_key,
        name="Expired API Key",
        user_id=test_user.id,
        scopes=["read"],
        is_active=True,
        expires_at=datetime.utcnow() - timedelta(days=1),  # Expired
        created_at=datetime.utcnow(),
    )
    db_session.add(api_key)
    await db_session.commit()

    return api_key, raw_key
```

## Service and Repository Fixtures

```python
# tests/fixtures/services.py
import pytest
from unittest.mock import AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.repositories.product import ProductRepository
from app.services.user import UserService
from app.services.product import ProductService


# Real repositories
@pytest.fixture
def user_repository(db_session: AsyncSession) -> UserRepository:
    """Create real user repository."""
    return UserRepository(db_session)


@pytest.fixture
def product_repository(db_session: AsyncSession) -> ProductRepository:
    """Create real product repository."""
    return ProductRepository(db_session)


# Real services
@pytest.fixture
def user_service(user_repository: UserRepository) -> UserService:
    """Create real user service."""
    return UserService(user_repository)


@pytest.fixture
def product_service(product_repository: ProductRepository) -> ProductService:
    """Create real product service."""
    return ProductService(product_repository)


# Mock repositories for unit tests
@pytest.fixture
def mock_user_repository() -> AsyncMock:
    """Create mock user repository."""
    mock = AsyncMock(spec=UserRepository)
    return mock


@pytest.fixture
def mock_product_repository() -> AsyncMock:
    """Create mock product repository."""
    mock = AsyncMock(spec=ProductRepository)
    return mock


# Services with mocked dependencies
@pytest.fixture
def user_service_mocked(mock_user_repository: AsyncMock) -> UserService:
    """Create user service with mock repository."""
    return UserService(mock_user_repository)
```

## Test Data Cleanup

```python
# tests/fixtures/cleanup.py
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture(autouse=True)
async def cleanup_database(db_session: AsyncSession):
    """Clean up database after each test."""
    yield

    # Rollback any uncommitted changes
    await db_session.rollback()


@pytest.fixture
async def clean_tables(db_session: AsyncSession):
    """Truncate all tables before test."""
    tables = ["order_items", "orders", "products", "categories", "users"]

    for table in tables:
        await db_session.execute(text(f"DELETE FROM {table}"))

    await db_session.commit()
    yield
```

## Configuration Fixtures

```python
# tests/fixtures/config.py
import pytest
from unittest.mock import patch

from app.core.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        SECRET_KEY="test-secret-key-for-testing-only",
        ACCESS_TOKEN_EXPIRE_MINUTES=30,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
        DEBUG=True,
        ENVIRONMENT="test",
    )


@pytest.fixture
def mock_settings(test_settings):
    """Patch settings for tests."""
    with patch("app.core.config.settings", test_settings):
        yield test_settings
```

## Organizing Fixtures

```python
# tests/conftest.py
# Import all fixtures from fixture modules

from tests.fixtures.database import (
    test_engine,
    db_session,
)
from tests.fixtures.users import (
    test_user,
    admin_user,
    multiple_users,
)
from tests.fixtures.products import (
    test_category,
    test_product,
    multiple_products,
)
from tests.fixtures.auth import (
    access_token,
    auth_headers,
    authenticated_client,
)
from tests.fixtures.services import (
    user_repository,
    user_service,
    mock_user_repository,
)
from tests.fixtures.factories import (
    user_factory,
    product_factory,
)


# Re-export all fixtures
__all__ = [
    "test_engine",
    "db_session",
    "test_user",
    "admin_user",
    "multiple_users",
    "test_category",
    "test_product",
    "multiple_products",
    "access_token",
    "auth_headers",
    "authenticated_client",
    "user_repository",
    "user_service",
    "mock_user_repository",
    "user_factory",
    "product_factory",
]
```

## Best Practices

1. **Scope fixtures appropriately** - session for expensive setup, function for isolation
2. **Use factories** for complex object creation with variations
3. **Separate fixtures** by domain (users, products, auth)
4. **Provide both real and mock** versions for flexibility
5. **Clean up after tests** with autouse fixtures
6. **Document fixture purpose** with docstrings
7. **Avoid fixture dependencies** when possible
8. **Use fixture inheritance** for shared behavior
