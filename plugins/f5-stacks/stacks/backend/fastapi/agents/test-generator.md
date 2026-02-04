---
name: fastapi-test-generator
description: Agent for generating test files
applies_to: fastapi
category: agent
inputs:
  - entity_name: Entity name in PascalCase
  - entity_plural: Plural form lowercase
  - test_types: Types of tests to generate
---

# FastAPI Test Generator Agent

## Purpose

Generate comprehensive test files for FastAPI applications including API tests, service tests, and fixtures.

## Activation

- User requests: "create tests for [entity]", "generate [entity] test suite"
- After creating new endpoints or services
- When implementing TDD

## Generation Process

### Step 1: Gather Requirements

Ask for or determine:
1. Entity name (PascalCase): e.g., `Product`
2. Entity plural: e.g., `products`
3. Test types needed: API, service, repository
4. Authentication requirements
5. Special business rules to test

### Step 2: Generate API Tests

```python
# tests/api/test_{entity_plural}.py
"""
Tests for {entity_name} API endpoints.

REQ-XXX: {entity_name} API testing
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient

from tests.helpers.assertions import (
    assert_success_response,
    assert_error_response,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def test_{entity_lower}(db_session, test_user, test_category):
    """Create test {entity_lower} fixture."""
    from app.models.{entity_lower} import {entity_name}

    {entity_lower} = {entity_name}(
        id=uuid4(),
        name="Test {entity_name}",
        slug="test-{entity_lower}",
        description="A test {entity_lower}",
        price=29.99,
        sku=f"TEST-{{uuid4().hex[:8].upper()}}",
        stock=100,
        status="active",
        category_id=test_category.id,
        created_by_id=test_user.id,
    )
    db_session.add({entity_lower})
    await db_session.commit()
    await db_session.refresh({entity_lower})
    return {entity_lower}


@pytest.fixture
async def multiple_{entity_plural}(db_session, test_user, test_category):
    """Create multiple test {entity_plural}."""
    from app.models.{entity_lower} import {entity_name}

    {entity_plural} = []
    for i in range(5):
        {entity_lower} = {entity_name}(
            id=uuid4(),
            name=f"Test {entity_name} {{i}}",
            slug=f"test-{entity_lower}-{{i}}",
            price=10.00 + i * 5,
            sku=f"TEST-{{i:03d}}",
            stock=50 + i * 10,
            status="active",
            category_id=test_category.id,
            created_by_id=test_user.id,
        )
        db_session.add({entity_lower})
        {entity_plural}.append({entity_lower})

    await db_session.commit()
    return {entity_plural}


@pytest.fixture
async def other_user_{entity_lower}(db_session, other_user, test_category):
    """Create {entity_lower} owned by another user."""
    from app.models.{entity_lower} import {entity_name}

    {entity_lower} = {entity_name}(
        id=uuid4(),
        name="Other User {entity_name}",
        slug="other-user-{entity_lower}",
        price=19.99,
        sku=f"OTHER-{{uuid4().hex[:8].upper()}}",
        stock=50,
        status="active",
        category_id=test_category.id,
        created_by_id=other_user.id,
    )
    db_session.add({entity_lower})
    await db_session.commit()
    await db_session.refresh({entity_lower})
    return {entity_lower}


# ============================================================================
# List Tests
# ============================================================================

class TestList{entity_name}s:
    """Tests for GET /{entity_plural}/"""

    @pytest.mark.asyncio
    async def test_list_{entity_plural}_success(
        self,
        authenticated_client: AsyncClient,
        multiple_{entity_plural},
    ):
        """Test listing {entity_plural} returns paginated results."""
        response = await authenticated_client.get("/api/v1/{entity_plural}/")

        data = assert_success_response(response)
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert len(data["data"]["items"]) <= 20

    @pytest.mark.asyncio
    async def test_list_{entity_plural}_with_pagination(
        self,
        authenticated_client: AsyncClient,
        multiple_{entity_plural},
    ):
        """Test pagination parameters."""
        response = await authenticated_client.get(
            "/api/v1/{entity_plural}/",
            params={{"page": 1, "page_size": 2}},
        )

        data = assert_success_response(response)
        assert len(data["data"]["items"]) <= 2
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 2

    @pytest.mark.asyncio
    async def test_list_{entity_plural}_with_search(
        self,
        authenticated_client: AsyncClient,
        test_{entity_lower},
    ):
        """Test search functionality."""
        response = await authenticated_client.get(
            "/api/v1/{entity_plural}/",
            params={{"search": test_{entity_lower}.name[:5]}},
        )

        data = assert_success_response(response)
        assert len(data["data"]["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_{entity_plural}_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test listing without auth returns 401."""
        response = await client.get("/api/v1/{entity_plural}/")
        assert response.status_code == 401


# ============================================================================
# Get Single Tests
# ============================================================================

class TestGet{entity_name}:
    """Tests for GET /{entity_plural}/{{id}}"""

    @pytest.mark.asyncio
    async def test_get_{entity_lower}_success(
        self,
        authenticated_client: AsyncClient,
        test_{entity_lower},
    ):
        """Test getting {entity_lower} by ID."""
        response = await authenticated_client.get(
            f"/api/v1/{entity_plural}/{{test_{entity_lower}.id}}"
        )

        data = assert_success_response(response)
        assert data["data"]["id"] == str(test_{entity_lower}.id)
        assert data["data"]["name"] == test_{entity_lower}.name

    @pytest.mark.asyncio
    async def test_get_{entity_lower}_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting non-existent {entity_lower} returns 404."""
        fake_id = uuid4()
        response = await authenticated_client.get(
            f"/api/v1/{entity_plural}/{{fake_id}}"
        )

        assert_error_response(response, 404, "NOT_FOUND")


# ============================================================================
# Create Tests
# ============================================================================

class TestCreate{entity_name}:
    """Tests for POST /{entity_plural}/"""

    @pytest.mark.asyncio
    async def test_create_{entity_lower}_success(
        self,
        authenticated_client: AsyncClient,
        test_category,
    ):
        """Test creating {entity_lower} with valid data."""
        payload = {{
            "name": "New {entity_name}",
            "description": "A new {entity_lower}",
            "price": 29.99,
            "sku": f"NEW-{{uuid4().hex[:8].upper()}}",
            "category_id": str(test_category.id),
        }}

        response = await authenticated_client.post(
            "/api/v1/{entity_plural}/",
            json=payload,
        )

        data = assert_success_response(response, 201)
        assert data["data"]["name"] == payload["name"]
        assert "id" in data["data"]
        assert "slug" in data["data"]

    @pytest.mark.asyncio
    async def test_create_{entity_lower}_validation_error(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating with invalid data returns 422."""
        payload = {{
            "name": "",  # Invalid
            "price": -10,  # Invalid
        }}

        response = await authenticated_client.post(
            "/api/v1/{entity_plural}/",
            json=payload,
        )

        assert_error_response(response, 422, "VALIDATION_ERROR")

    @pytest.mark.asyncio
    async def test_create_{entity_lower}_duplicate_sku(
        self,
        authenticated_client: AsyncClient,
        test_{entity_lower},
        test_category,
    ):
        """Test creating with duplicate SKU returns 409."""
        payload = {{
            "name": "Another {entity_name}",
            "price": 19.99,
            "sku": test_{entity_lower}.sku,
            "category_id": str(test_category.id),
        }}

        response = await authenticated_client.post(
            "/api/v1/{entity_plural}/",
            json=payload,
        )

        assert_error_response(response, 409, "CONFLICT")


# ============================================================================
# Update Tests
# ============================================================================

class TestUpdate{entity_name}:
    """Tests for PUT /{entity_plural}/{{id}}"""

    @pytest.mark.asyncio
    async def test_update_{entity_lower}_success(
        self,
        authenticated_client: AsyncClient,
        test_{entity_lower},
    ):
        """Test updating with valid data."""
        payload = {{
            "name": "Updated {entity_name}",
            "price": 39.99,
        }}

        response = await authenticated_client.put(
            f"/api/v1/{entity_plural}/{{test_{entity_lower}.id}}",
            json=payload,
        )

        data = assert_success_response(response)
        assert data["data"]["name"] == payload["name"]

    @pytest.mark.asyncio
    async def test_update_{entity_lower}_forbidden(
        self,
        authenticated_client: AsyncClient,
        other_user_{entity_lower},
    ):
        """Test updating another user's {entity_lower} returns 403."""
        payload = {{"name": "Hacked"}}

        response = await authenticated_client.put(
            f"/api/v1/{entity_plural}/{{other_user_{entity_lower}.id}}",
            json=payload,
        )

        assert_error_response(response, 403, "FORBIDDEN")


# ============================================================================
# Delete Tests
# ============================================================================

class TestDelete{entity_name}:
    """Tests for DELETE /{entity_plural}/{{id}}"""

    @pytest.mark.asyncio
    async def test_delete_{entity_lower}_success(
        self,
        authenticated_client: AsyncClient,
        test_{entity_lower},
    ):
        """Test deleting returns 204."""
        response = await authenticated_client.delete(
            f"/api/v1/{entity_plural}/{{test_{entity_lower}.id}}"
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await authenticated_client.get(
            f"/api/v1/{entity_plural}/{{test_{entity_lower}.id}}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_{entity_lower}_forbidden(
        self,
        authenticated_client: AsyncClient,
        other_user_{entity_lower},
    ):
        """Test deleting another user's {entity_lower} returns 403."""
        response = await authenticated_client.delete(
            f"/api/v1/{entity_plural}/{{other_user_{entity_lower}.id}}"
        )

        assert_error_response(response, 403, "FORBIDDEN")
```

### Step 3: Generate Service Tests

```python
# tests/services/test_{entity_lower}_service.py
"""
Tests for {entity_name}Service.

REQ-XXX: {entity_name} business logic testing
"""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from app.services.{entity_lower} import {entity_name}Service
from app.schemas.{entity_lower} import {entity_name}Create
from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError


@pytest.fixture
def mock_repository():
    return AsyncMock()


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = uuid4()
    user.is_admin = False
    return user


@pytest.fixture
def service(mock_repository):
    return {entity_name}Service(mock_repository)


class TestGet{entity_name}:
    """Tests for get operations."""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, service, mock_repository):
        mock_{entity_lower} = MagicMock()
        mock_{entity_lower}.id = uuid4()
        mock_repository.get_by_id.return_value = mock_{entity_lower}

        result = await service.get_by_id(mock_{entity_lower}.id)

        assert result == mock_{entity_lower}
        mock_repository.get_by_id.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, service, mock_repository):
        mock_repository.get_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id(uuid4())


class TestCreate{entity_name}:
    """Tests for create operations."""

    @pytest.mark.asyncio
    async def test_create_success(
        self,
        service,
        mock_repository,
        mock_user,
    ):
        data = {entity_name}Create(
            name="Test {entity_name}",
            price=29.99,
            sku="TEST-001",
        )

        mock_repository.get_by_slug.return_value = None
        mock_repository.get_by_sku.return_value = None
        mock_repository.create.return_value = MagicMock(id=uuid4())

        result = await service.create(data, mock_user)

        assert result is not None
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_duplicate_slug(
        self,
        service,
        mock_repository,
        mock_user,
    ):
        data = {entity_name}Create(
            name="Existing Name",
            price=29.99,
            sku="TEST-002",
        )

        mock_repository.get_by_slug.return_value = MagicMock()

        with pytest.raises(ConflictError):
            await service.create(data, mock_user)


class TestUpdate{entity_name}:
    """Tests for update operations."""

    @pytest.mark.asyncio
    async def test_update_forbidden_for_non_owner(
        self,
        service,
        mock_repository,
        mock_user,
    ):
        mock_{entity_lower} = MagicMock()
        mock_{entity_lower}.created_by_id = uuid4()  # Different user
        mock_repository.get_by_id.return_value = mock_{entity_lower}

        from app.schemas.{entity_lower} import {entity_name}Update
        data = {entity_name}Update(name="Updated")

        with pytest.raises(ForbiddenError):
            await service.update(mock_{entity_lower}.id, data, mock_user)
```

### Step 4: Generate Test Helpers

```python
# tests/helpers/assertions.py
from typing import Any
from httpx import Response


def assert_success_response(
    response: Response,
    status_code: int = 200,
) -> dict[str, Any]:
    """Assert successful API response."""
    assert response.status_code == status_code, (
        f"Expected {{status_code}}, got {{response.status_code}}: {{response.text}}"
    )
    data = response.json()
    assert data["success"] is True
    return data


def assert_error_response(
    response: Response,
    status_code: int,
    error_code: str,
) -> dict[str, Any]:
    """Assert error API response."""
    assert response.status_code == status_code
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == error_code
    return data
```

## Output Files

1. `tests/api/test_{entity_plural}.py` - API endpoint tests
2. `tests/services/test_{entity_lower}_service.py` - Service tests
3. `tests/helpers/assertions.py` - Test helpers (if not exists)

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/api/test_{entity_plural}.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## Validation Checklist

- [ ] All CRUD endpoints tested
- [ ] Authentication tested
- [ ] Authorization (ownership) tested
- [ ] Validation errors tested
- [ ] Not found errors tested
- [ ] Conflict errors tested
- [ ] Service unit tests included
- [ ] REQ-XXX traceability comment
