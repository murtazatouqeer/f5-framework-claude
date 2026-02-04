---
name: fastapi-test
description: Test file template for FastAPI
applies_to: fastapi
category: template
variables:
  - name: entity_name
    description: Entity name in PascalCase (e.g., Product)
  - name: entity_lower
    description: Lowercase entity name (e.g., product)
  - name: entity_plural
    description: Plural form (e.g., products)
---

# FastAPI Test Template

## Template

```python
# tests/api/test_{{entity_plural}}.py
"""
Tests for {{entity_name}} API endpoints.

REQ-XXX: {{entity_name}} API testing
"""
import pytest
from uuid import uuid4
from httpx import AsyncClient

from tests.helpers.assertions import (
    assert_success_response,
    assert_error_response,
    assert_paginated_response,
)


# ============================================================================
# List Tests
# ============================================================================

class TestList{{entity_name}}s:
    """Tests for GET /{{entity_plural}}/"""

    @pytest.mark.asyncio
    async def test_list_{{entity_plural}}_success(
        self,
        authenticated_client: AsyncClient,
        multiple_{{entity_plural}},
    ):
        """Test listing {{entity_plural}} returns paginated results."""
        response = await authenticated_client.get("/api/v1/{{entity_plural}}/")

        data = assert_success_response(response)
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert len(data["data"]["items"]) <= 20  # Default page size

    @pytest.mark.asyncio
    async def test_list_{{entity_plural}}_with_pagination(
        self,
        authenticated_client: AsyncClient,
        multiple_{{entity_plural}},
    ):
        """Test pagination parameters."""
        response = await authenticated_client.get(
            "/api/v1/{{entity_plural}}/",
            params={"page": 1, "page_size": 5},
        )

        data = assert_success_response(response)
        assert len(data["data"]["items"]) <= 5
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 5

    @pytest.mark.asyncio
    async def test_list_{{entity_plural}}_with_search(
        self,
        authenticated_client: AsyncClient,
        test_{{entity_lower}},
    ):
        """Test search functionality."""
        response = await authenticated_client.get(
            "/api/v1/{{entity_plural}}/",
            params={"search": test_{{entity_lower}}.name[:5]},
        )

        data = assert_success_response(response)
        assert len(data["data"]["items"]) >= 1

    @pytest.mark.asyncio
    async def test_list_{{entity_plural}}_unauthorized(
        self,
        client: AsyncClient,
    ):
        """Test listing without authentication returns 401."""
        response = await client.get("/api/v1/{{entity_plural}}/")
        assert_error_response(response, 401, "AUTHENTICATION_ERROR")


# ============================================================================
# Get Single Tests
# ============================================================================

class TestGet{{entity_name}}:
    """Tests for GET /{{entity_plural}}/{id}"""

    @pytest.mark.asyncio
    async def test_get_{{entity_lower}}_success(
        self,
        authenticated_client: AsyncClient,
        test_{{entity_lower}},
    ):
        """Test getting {{entity_lower}} by ID."""
        response = await authenticated_client.get(
            f"/api/v1/{{entity_plural}}/{test_{{entity_lower}}.id}"
        )

        data = assert_success_response(response)
        assert data["data"]["id"] == str(test_{{entity_lower}}.id)
        assert data["data"]["name"] == test_{{entity_lower}}.name

    @pytest.mark.asyncio
    async def test_get_{{entity_lower}}_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting non-existent {{entity_lower}} returns 404."""
        fake_id = uuid4()
        response = await authenticated_client.get(
            f"/api/v1/{{entity_plural}}/{fake_id}"
        )

        assert_error_response(response, 404, "NOT_FOUND")

    @pytest.mark.asyncio
    async def test_get_{{entity_lower}}_invalid_id(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting with invalid UUID returns 422."""
        response = await authenticated_client.get(
            "/api/v1/{{entity_plural}}/invalid-uuid"
        )

        assert response.status_code == 422


# ============================================================================
# Create Tests
# ============================================================================

class TestCreate{{entity_name}}:
    """Tests for POST /{{entity_plural}}/"""

    @pytest.mark.asyncio
    async def test_create_{{entity_lower}}_success(
        self,
        authenticated_client: AsyncClient,
        test_category,
    ):
        """Test creating {{entity_lower}} with valid data."""
        payload = {
            "name": "Test {{entity_name}}",
            "description": "A test {{entity_lower}}",
            "price": 29.99,
            "sku": f"TEST-{uuid4().hex[:8].upper()}",
            "category_id": str(test_category.id),
        }

        response = await authenticated_client.post(
            "/api/v1/{{entity_plural}}/",
            json=payload,
        )

        data = assert_success_response(response, 201)
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["price"] == payload["price"]
        assert "id" in data["data"]
        assert "slug" in data["data"]

    @pytest.mark.asyncio
    async def test_create_{{entity_lower}}_validation_error(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating {{entity_lower}} with invalid data returns 422."""
        payload = {
            "name": "",  # Invalid: empty
            "price": -10,  # Invalid: negative
        }

        response = await authenticated_client.post(
            "/api/v1/{{entity_plural}}/",
            json=payload,
        )

        assert_error_response(response, 422, "VALIDATION_ERROR")

    @pytest.mark.asyncio
    async def test_create_{{entity_lower}}_duplicate_sku(
        self,
        authenticated_client: AsyncClient,
        test_{{entity_lower}},
        test_category,
    ):
        """Test creating {{entity_lower}} with duplicate SKU returns 409."""
        payload = {
            "name": "Another {{entity_name}}",
            "price": 19.99,
            "sku": test_{{entity_lower}}.sku,  # Duplicate
            "category_id": str(test_category.id),
        }

        response = await authenticated_client.post(
            "/api/v1/{{entity_plural}}/",
            json=payload,
        )

        assert_error_response(response, 409, "CONFLICT")


# ============================================================================
# Update Tests
# ============================================================================

class TestUpdate{{entity_name}}:
    """Tests for PUT /{{entity_plural}}/{id}"""

    @pytest.mark.asyncio
    async def test_update_{{entity_lower}}_success(
        self,
        authenticated_client: AsyncClient,
        test_{{entity_lower}},
    ):
        """Test updating {{entity_lower}} with valid data."""
        payload = {
            "name": "Updated {{entity_name}}",
            "price": 39.99,
        }

        response = await authenticated_client.put(
            f"/api/v1/{{entity_plural}}/{test_{{entity_lower}}.id}",
            json=payload,
        )

        data = assert_success_response(response)
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["price"] == payload["price"]

    @pytest.mark.asyncio
    async def test_update_{{entity_lower}}_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test updating non-existent {{entity_lower}} returns 404."""
        fake_id = uuid4()
        payload = {"name": "Updated"}

        response = await authenticated_client.put(
            f"/api/v1/{{entity_plural}}/{fake_id}",
            json=payload,
        )

        assert_error_response(response, 404, "NOT_FOUND")

    @pytest.mark.asyncio
    async def test_update_{{entity_lower}}_forbidden(
        self,
        authenticated_client: AsyncClient,
        other_user_{{entity_lower}},
    ):
        """Test updating another user's {{entity_lower}} returns 403."""
        payload = {"name": "Hacked"}

        response = await authenticated_client.put(
            f"/api/v1/{{entity_plural}}/{other_user_{{entity_lower}}.id}",
            json=payload,
        )

        assert_error_response(response, 403, "FORBIDDEN")


# ============================================================================
# Partial Update Tests
# ============================================================================

class TestPartialUpdate{{entity_name}}:
    """Tests for PATCH /{{entity_plural}}/{id}"""

    @pytest.mark.asyncio
    async def test_partial_update_{{entity_lower}}_success(
        self,
        authenticated_client: AsyncClient,
        test_{{entity_lower}},
    ):
        """Test partial update only changes specified fields."""
        original_price = float(test_{{entity_lower}}.price)
        payload = {"name": "Partially Updated"}

        response = await authenticated_client.patch(
            f"/api/v1/{{entity_plural}}/{test_{{entity_lower}}.id}",
            json=payload,
        )

        data = assert_success_response(response)
        assert data["data"]["name"] == payload["name"]
        assert data["data"]["price"] == original_price  # Unchanged


# ============================================================================
# Delete Tests
# ============================================================================

class TestDelete{{entity_name}}:
    """Tests for DELETE /{{entity_plural}}/{id}"""

    @pytest.mark.asyncio
    async def test_delete_{{entity_lower}}_success(
        self,
        authenticated_client: AsyncClient,
        test_{{entity_lower}},
    ):
        """Test deleting {{entity_lower}} returns 204."""
        response = await authenticated_client.delete(
            f"/api/v1/{{entity_plural}}/{test_{{entity_lower}}.id}"
        )

        assert response.status_code == 204

        # Verify deletion
        get_response = await authenticated_client.get(
            f"/api/v1/{{entity_plural}}/{test_{{entity_lower}}.id}"
        )
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_{{entity_lower}}_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test deleting non-existent {{entity_lower}} returns 404."""
        fake_id = uuid4()

        response = await authenticated_client.delete(
            f"/api/v1/{{entity_plural}}/{fake_id}"
        )

        assert_error_response(response, 404, "NOT_FOUND")

    @pytest.mark.asyncio
    async def test_delete_{{entity_lower}}_forbidden(
        self,
        authenticated_client: AsyncClient,
        other_user_{{entity_lower}},
    ):
        """Test deleting another user's {{entity_lower}} returns 403."""
        response = await authenticated_client.delete(
            f"/api/v1/{{entity_plural}}/{other_user_{{entity_lower}}.id}"
        )

        assert_error_response(response, 403, "FORBIDDEN")


# ============================================================================
# Admin Tests
# ============================================================================

class TestAdmin{{entity_name}}Operations:
    """Tests for admin operations on {{entity_plural}}."""

    @pytest.mark.asyncio
    async def test_admin_can_update_any_{{entity_lower}}(
        self,
        admin_client: AsyncClient,
        other_user_{{entity_lower}},
    ):
        """Test admin can update any user's {{entity_lower}}."""
        payload = {"name": "Admin Updated"}

        response = await admin_client.put(
            f"/api/v1/{{entity_plural}}/{other_user_{{entity_lower}}.id}",
            json=payload,
        )

        data = assert_success_response(response)
        assert data["data"]["name"] == payload["name"]

    @pytest.mark.asyncio
    async def test_admin_can_delete_any_{{entity_lower}}(
        self,
        admin_client: AsyncClient,
        other_user_{{entity_lower}},
    ):
        """Test admin can delete any user's {{entity_lower}}."""
        response = await admin_client.delete(
            f"/api/v1/{{entity_plural}}/{other_user_{{entity_lower}}.id}"
        )

        assert response.status_code == 204
```

## Test Helpers

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
        f"Expected {status_code}, got {response.status_code}: {response.text}"
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


def assert_paginated_response(
    response: Response,
    expected_page: int = 1,
) -> dict[str, Any]:
    """Assert paginated API response."""
    data = assert_success_response(response)
    assert "items" in data["data"]
    assert "total" in data["data"]
    assert data["data"]["page"] == expected_page
    return data
```

## Usage

Replace placeholders:
- `{{entity_name}}`: PascalCase entity name (e.g., `Product`)
- `{{entity_lower}}`: Lowercase singular (e.g., `product`)
- `{{entity_plural}}`: Plural lowercase (e.g., `products`)

Run tests with:
```bash
pytest tests/api/test_products.py -v
```
