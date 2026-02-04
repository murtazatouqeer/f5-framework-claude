---
name: fastapi-pytest-asyncio
description: Async testing patterns with pytest-asyncio for FastAPI
applies_to: fastapi
category: skill
---

# Pytest Asyncio for FastAPI

## Configuration

### pyproject.toml Setup

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["app"]
omit = ["*/tests/*", "*/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "raise NotImplementedError",
]
```

### conftest.py Base Configuration

```python
# tests/conftest.py
import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database override."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
```

## Basic Test Patterns

### Simple Async Test

```python
# tests/test_basic.py
import pytest


@pytest.mark.asyncio
async def test_simple_async():
    """Basic async test."""
    result = await some_async_function()
    assert result == expected_value


@pytest.mark.asyncio
async def test_with_fixture(db_session):
    """Test with database fixture."""
    # db_session is automatically injected
    result = await db_session.execute(select(User))
    assert result is not None
```

### API Endpoint Tests

```python
# tests/api/test_endpoints.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_read_root(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


@pytest.mark.asyncio
async def test_create_item(client: AsyncClient):
    """Test item creation."""
    response = await client.post(
        "/api/v1/items/",
        json={"name": "Test Item", "price": 9.99},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Item"


@pytest.mark.asyncio
async def test_get_item(client: AsyncClient):
    """Test item retrieval."""
    # Create item first
    create_response = await client.post(
        "/api/v1/items/",
        json={"name": "Test Item", "price": 9.99},
    )
    item_id = create_response.json()["data"]["id"]

    # Get item
    response = await client.get(f"/api/v1/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["data"]["id"] == item_id


@pytest.mark.asyncio
async def test_item_not_found(client: AsyncClient):
    """Test 404 response."""
    response = await client.get("/api/v1/items/nonexistent-id")
    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["error"]["code"] == "NOT_FOUND"
```

## Authentication Tests

### Testing Protected Endpoints

```python
# tests/api/test_auth.py
import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Get authentication headers."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "TestPass123!",
            "name": "Test User",
        },
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "TestPass123!",
        },
    )
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_protected_endpoint(client: AsyncClient, auth_headers: dict):
    """Test protected endpoint with auth."""
    response = await client.get(
        "/api/v1/users/me",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_protected_endpoint_unauthorized(client: AsyncClient):
    """Test protected endpoint without auth."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient):
    """Test login with invalid credentials."""
    response = await client.post(
        "/api/v1/auth/login",
        data={
            "username": "wrong@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"
```

## Database Tests

### Repository Tests

```python
# tests/repositories/test_user_repository.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


@pytest.fixture
def user_repo(db_session: AsyncSession) -> UserRepository:
    """Create user repository fixture."""
    return UserRepository(db_session)


@pytest.mark.asyncio
async def test_create_user(user_repo: UserRepository):
    """Test user creation."""
    user_data = UserCreate(
        email="test@example.com",
        password="hashedpassword",
        name="Test User",
    )

    user = await user_repo.create(user_data)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.name == "Test User"


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo: UserRepository):
    """Test user retrieval by email."""
    # Create user
    user_data = UserCreate(
        email="find@example.com",
        password="hashedpassword",
        name="Find User",
    )
    created = await user_repo.create(user_data)

    # Find user
    found = await user_repo.get_by_email("find@example.com")

    assert found is not None
    assert found.id == created.id


@pytest.mark.asyncio
async def test_get_user_not_found(user_repo: UserRepository):
    """Test user not found."""
    found = await user_repo.get_by_email("notfound@example.com")
    assert found is None
```

### Service Tests

```python
# tests/services/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.services.user import UserService
from app.schemas.user import UserCreate


@pytest.fixture
def mock_user_repo():
    """Create mock user repository."""
    return AsyncMock()


@pytest.fixture
def user_service(mock_user_repo) -> UserService:
    """Create user service with mock repository."""
    return UserService(mock_user_repo)


@pytest.mark.asyncio
async def test_create_user_success(user_service: UserService, mock_user_repo):
    """Test successful user creation."""
    user_data = UserCreate(
        email="test@example.com",
        password="TestPass123!",
        name="Test User",
    )

    mock_user = MagicMock()
    mock_user.id = "user-id"
    mock_user.email = "test@example.com"
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.create.return_value = mock_user

    result = await user_service.create(user_data)

    assert result.id == "user-id"
    mock_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(user_service: UserService, mock_user_repo):
    """Test user creation with duplicate email."""
    from app.core.exceptions import ConflictError

    user_data = UserCreate(
        email="existing@example.com",
        password="TestPass123!",
        name="Test User",
    )

    mock_user_repo.get_by_email.return_value = MagicMock()  # User exists

    with pytest.raises(ConflictError):
        await user_service.create(user_data)
```

## Parameterized Tests

```python
# tests/test_validation.py
import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate


@pytest.mark.parametrize("email,valid", [
    ("valid@example.com", True),
    ("user@domain.org", True),
    ("invalid-email", False),
    ("@nodomain.com", False),
    ("", False),
])
def test_email_validation(email: str, valid: bool):
    """Test email validation with various inputs."""
    if valid:
        user = UserCreate(email=email, password="ValidPass123!", name="Test")
        assert user.email == email.lower()
    else:
        with pytest.raises(ValidationError):
            UserCreate(email=email, password="ValidPass123!", name="Test")


@pytest.mark.parametrize("password,valid", [
    ("ValidPass123!", True),
    ("AnotherGood1@", True),
    ("short1A!", False),  # Too short
    ("nouppercasepass1!", False),  # No uppercase
    ("NOLOWERCASE1!", False),  # No lowercase
    ("NoDigitsHere!", False),  # No digits
    ("NoSpecialChar1", False),  # No special char
])
def test_password_validation(password: str, valid: bool):
    """Test password validation with various inputs."""
    if valid:
        user = UserCreate(
            email="test@example.com",
            password=password,
            name="Test",
        )
        assert user.password == password
    else:
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password=password,
                name="Test",
            )
```

## Async Context Managers

```python
# tests/test_transactions.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_transaction_rollback(db_session: AsyncSession):
    """Test transaction rollback on error."""
    from app.models.user import User

    try:
        async with db_session.begin_nested():
            user = User(email="rollback@test.com", name="Test")
            db_session.add(user)
            # Simulate error
            raise ValueError("Simulated error")
    except ValueError:
        pass

    # User should not be persisted
    result = await db_session.execute(
        select(User).where(User.email == "rollback@test.com")
    )
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_concurrent_operations(db_session: AsyncSession):
    """Test concurrent async operations."""
    import asyncio
    from app.repositories.user import UserRepository

    repo = UserRepository(db_session)

    # Create multiple users concurrently
    tasks = [
        repo.create(UserCreate(
            email=f"user{i}@test.com",
            password="hash",
            name=f"User {i}",
        ))
        for i in range(5)
    ]

    users = await asyncio.gather(*tasks)

    assert len(users) == 5
    assert all(u.id is not None for u in users)
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/api/test_endpoints.py

# Run specific test
pytest tests/api/test_endpoints.py::test_create_item

# Run with verbose output
pytest -v

# Run async tests only
pytest -m asyncio

# Run in parallel
pytest -n auto
```

## Best Practices

1. **Use `asyncio_mode = "auto"`** to avoid manual `@pytest.mark.asyncio`
2. **Create fresh database sessions** for each test
3. **Use dependency overrides** for mocking services
4. **Clean up after tests** with proper rollback
5. **Test both success and error cases**
6. **Use parameterized tests** for validation
7. **Mock external services** in unit tests
8. **Use transactions** for test isolation
