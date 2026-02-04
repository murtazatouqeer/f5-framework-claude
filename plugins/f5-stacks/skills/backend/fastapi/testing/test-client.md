---
name: fastapi-test-client
description: Test client patterns for FastAPI testing
applies_to: fastapi
category: skill
---

# FastAPI Test Client

## HTTPX AsyncClient Setup

### Basic Configuration

```python
# tests/conftest.py
import pytest
from httpx import AsyncClient, ASGITransport
from typing import AsyncGenerator

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0,
    ) as ac:
        yield ac
```

### Client with Authentication

```python
# tests/conftest.py
from typing import AsyncGenerator
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.security import create_access_token


@pytest.fixture
async def authenticated_client(
    client: AsyncClient,
    test_user,
) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated test client."""
    token = create_access_token(data={"sub": test_user.email})
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    del client.headers["Authorization"]


@pytest.fixture
async def admin_client(
    client: AsyncClient,
    admin_user,
) -> AsyncClient:
    """Create admin authenticated client."""
    token = create_access_token(
        data={"sub": admin_user.email, "roles": ["admin"]}
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

## Request Patterns

### GET Requests

```python
# tests/api/test_get.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_list(client: AsyncClient):
    """Test GET list endpoint."""
    response = await client.get("/api/v1/items/")

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_with_query_params(client: AsyncClient):
    """Test GET with query parameters."""
    response = await client.get(
        "/api/v1/items/",
        params={
            "page": 1,
            "page_size": 10,
            "sort_by": "created_at",
            "sort_order": "desc",
            "search": "test",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert data["meta"]["page"] == 1
    assert data["meta"]["page_size"] == 10


@pytest.mark.asyncio
async def test_get_by_id(client: AsyncClient, created_item):
    """Test GET by ID."""
    response = await client.get(f"/api/v1/items/{created_item.id}")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(created_item.id)


@pytest.mark.asyncio
async def test_get_not_found(client: AsyncClient):
    """Test GET non-existent resource."""
    response = await client.get("/api/v1/items/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
```

### POST Requests

```python
# tests/api/test_post.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_item(authenticated_client: AsyncClient):
    """Test POST create."""
    response = await authenticated_client.post(
        "/api/v1/items/",
        json={
            "name": "New Item",
            "description": "A test item",
            "price": 29.99,
            "category_id": "category-uuid",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "New Item"
    assert "id" in data["data"]


@pytest.mark.asyncio
async def test_create_validation_error(authenticated_client: AsyncClient):
    """Test POST with validation error."""
    response = await authenticated_client.post(
        "/api/v1/items/",
        json={
            "name": "",  # Invalid: empty name
            "price": -10,  # Invalid: negative price
        },
    )

    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "errors" in data["error"]["details"]


@pytest.mark.asyncio
async def test_create_unauthorized(client: AsyncClient):
    """Test POST without authentication."""
    response = await client.post(
        "/api/v1/items/",
        json={"name": "Test", "price": 9.99},
    )

    assert response.status_code == 401
```

### PUT/PATCH Requests

```python
# tests/api/test_update.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_update_full(authenticated_client: AsyncClient, created_item):
    """Test PUT full update."""
    response = await authenticated_client.put(
        f"/api/v1/items/{created_item.id}",
        json={
            "name": "Updated Name",
            "description": "Updated description",
            "price": 39.99,
            "category_id": str(created_item.category_id),
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_partial_update(authenticated_client: AsyncClient, created_item):
    """Test PATCH partial update."""
    response = await authenticated_client.patch(
        f"/api/v1/items/{created_item.id}",
        json={"name": "Partially Updated"},
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Partially Updated"
    # Other fields unchanged
    assert data["price"] == float(created_item.price)


@pytest.mark.asyncio
async def test_update_not_found(authenticated_client: AsyncClient):
    """Test update non-existent resource."""
    response = await authenticated_client.put(
        "/api/v1/items/00000000-0000-0000-0000-000000000000",
        json={"name": "Test", "price": 9.99},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_forbidden(authenticated_client: AsyncClient, other_user_item):
    """Test update resource owned by another user."""
    response = await authenticated_client.put(
        f"/api/v1/items/{other_user_item.id}",
        json={"name": "Hacked"},
    )

    assert response.status_code == 403
```

### DELETE Requests

```python
# tests/api/test_delete.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_delete_item(authenticated_client: AsyncClient, created_item):
    """Test DELETE."""
    response = await authenticated_client.delete(
        f"/api/v1/items/{created_item.id}"
    )

    assert response.status_code == 204

    # Verify deletion
    get_response = await authenticated_client.get(
        f"/api/v1/items/{created_item.id}"
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_not_found(authenticated_client: AsyncClient):
    """Test DELETE non-existent resource."""
    response = await authenticated_client.delete(
        "/api/v1/items/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_forbidden(authenticated_client: AsyncClient, other_user_item):
    """Test DELETE resource owned by another user."""
    response = await authenticated_client.delete(
        f"/api/v1/items/{other_user_item.id}"
    )

    assert response.status_code == 403
```

## File Uploads

```python
# tests/api/test_uploads.py
import pytest
from httpx import AsyncClient
from io import BytesIO


@pytest.mark.asyncio
async def test_upload_file(authenticated_client: AsyncClient):
    """Test file upload."""
    file_content = b"test file content"

    response = await authenticated_client.post(
        "/api/v1/files/upload",
        files={"file": ("test.txt", BytesIO(file_content), "text/plain")},
    )

    assert response.status_code == 201
    assert "file_id" in response.json()["data"]


@pytest.mark.asyncio
async def test_upload_image(authenticated_client: AsyncClient):
    """Test image upload."""
    # Create minimal PNG
    png_content = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00'
        b'\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00'
        b'\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    response = await authenticated_client.post(
        "/api/v1/files/upload-image",
        files={"file": ("test.png", BytesIO(png_content), "image/png")},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_invalid_type(authenticated_client: AsyncClient):
    """Test upload with invalid file type."""
    response = await authenticated_client.post(
        "/api/v1/files/upload-image",
        files={"file": ("test.exe", BytesIO(b"content"), "application/octet-stream")},
    )

    assert response.status_code == 400
    assert "File type not allowed" in response.json()["error"]["message"]


@pytest.mark.asyncio
async def test_upload_too_large(authenticated_client: AsyncClient):
    """Test upload file size limit."""
    large_content = b"x" * (10 * 1024 * 1024 + 1)  # 10MB + 1 byte

    response = await authenticated_client.post(
        "/api/v1/files/upload",
        files={"file": ("large.txt", BytesIO(large_content), "text/plain")},
    )

    assert response.status_code == 400
    assert "too large" in response.json()["error"]["message"].lower()
```

## Form Data

```python
# tests/api/test_forms.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_oauth_login(client: AsyncClient, test_user):
    """Test OAuth2 password flow."""
    response = await client.post(
        "/api/v1/auth/token",
        data={
            "username": test_user.email,
            "password": "testpassword",
            "grant_type": "password",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_form_submission(client: AsyncClient):
    """Test form data submission."""
    response = await client.post(
        "/api/v1/contact",
        data={
            "name": "John Doe",
            "email": "john@example.com",
            "message": "Hello, this is a test message.",
        },
    )

    assert response.status_code == 200
```

## Response Assertions

### Custom Assertion Helpers

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
    assert data["success"] is True, f"Response not successful: {data}"
    return data


def assert_error_response(
    response: Response,
    status_code: int,
    error_code: str,
) -> dict[str, Any]:
    """Assert error API response."""
    assert response.status_code == status_code, (
        f"Expected {status_code}, got {response.status_code}: {response.text}"
    )
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == error_code
    return data


def assert_paginated_response(
    response: Response,
    expected_page: int = 1,
    expected_page_size: int = 20,
) -> dict[str, Any]:
    """Assert paginated API response."""
    data = assert_success_response(response)
    assert "data" in data
    assert "meta" in data
    assert data["meta"]["page"] == expected_page
    assert data["meta"]["page_size"] == expected_page_size
    assert "total" in data["meta"]
    return data


# Usage in tests
@pytest.mark.asyncio
async def test_with_helpers(client: AsyncClient):
    response = await client.get("/api/v1/items/")
    data = assert_paginated_response(response)
    assert len(data["data"]) <= data["meta"]["page_size"]
```

## Request Headers

```python
# tests/api/test_headers.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_custom_headers(client: AsyncClient):
    """Test custom request headers."""
    response = await client.get(
        "/api/v1/items/",
        headers={
            "X-Request-ID": "test-request-123",
            "Accept-Language": "ja",
        },
    )

    assert response.status_code == 200
    # Check response header
    assert "X-Request-ID" in response.headers


@pytest.mark.asyncio
async def test_api_key_header(client: AsyncClient, test_api_key):
    """Test API key authentication via header."""
    response = await client.get(
        "/api/v1/external/data",
        headers={"X-API-Key": test_api_key},
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_content_negotiation(client: AsyncClient):
    """Test content type negotiation."""
    response = await client.get(
        "/api/v1/items/",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
```

## Cookie Handling

```python
# tests/api/test_cookies.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_session_cookie(client: AsyncClient):
    """Test session cookie handling."""
    # Login to get session cookie
    login_response = await client.post(
        "/api/v1/auth/login-session",
        json={"email": "test@example.com", "password": "password"},
    )

    assert login_response.status_code == 200
    assert "session" in login_response.cookies

    # Use session cookie for authenticated request
    # httpx client automatically handles cookies
    profile_response = await client.get("/api/v1/users/me")
    assert profile_response.status_code == 200
```

## WebSocket Testing

```python
# tests/api/test_websocket.py
import pytest
from httpx import AsyncClient
from starlette.testclient import TestClient

from app.main import app


def test_websocket_connection():
    """Test WebSocket connection."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws/chat") as websocket:
            websocket.send_json({"type": "message", "content": "Hello"})
            data = websocket.receive_json()
            assert data["type"] == "message"


def test_websocket_auth():
    """Test authenticated WebSocket."""
    with TestClient(app) as client:
        with client.websocket_connect(
            "/ws/chat",
            headers={"Authorization": "Bearer valid-token"},
        ) as websocket:
            data = websocket.receive_json()
            assert data["type"] == "connected"
```

## Best Practices

1. **Use `AsyncClient`** with `ASGITransport` for async tests
2. **Create fixtures** for common test data and clients
3. **Use helper functions** for repetitive assertions
4. **Test all HTTP methods** and status codes
5. **Test authentication** and authorization
6. **Test error responses** with proper codes
7. **Clean up test data** after tests
8. **Use meaningful test names** describing the scenario
