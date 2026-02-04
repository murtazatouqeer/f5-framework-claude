# tests/products/conftest.py
"""
Pytest fixtures for product tests.

REQ-001: Product CRUD API
"""
import pytest
from rest_framework.test import APIClient

from tests.factories import UserFactory


@pytest.fixture
def api_client():
    """Return fresh API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create test user."""
    return UserFactory()


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return UserFactory(is_staff=True, is_superuser=True)


@pytest.fixture
def authenticated_client(api_client, user):
    """Return authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return admin authenticated client."""
    api_client.force_authenticate(user=admin_user)
    return api_client
