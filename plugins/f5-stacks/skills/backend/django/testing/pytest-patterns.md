# Pytest Django Patterns Skill

## Overview

Testing patterns and best practices for Django with pytest-django.

## Configuration

```python
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
python_files = tests.py test_*.py *_test.py
addopts = -v --tb=short --strict-markers
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: integration tests requiring external services
    unit: unit tests

# conftest.py
import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture(scope='session')
def django_db_setup():
    """Configure database for test session."""
    pass


@pytest.fixture
def api_client():
    """Return fresh API client."""
    return APIClient()


@pytest.fixture
def user(db):
    """Create test user."""
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user(db):
    """Create admin user."""
    return User.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123'
    )


@pytest.fixture
def authenticated_client(api_client, user):
    """Return authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    """Return admin API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client
```

## Test Organization

```
tests/
├── conftest.py              # Shared fixtures
├── factories/
│   ├── __init__.py
│   ├── user.py
│   └── order.py
├── unit/
│   ├── test_models.py
│   ├── test_serializers.py
│   └── test_services.py
├── integration/
│   ├── test_views.py
│   └── test_workflows.py
└── e2e/
    └── test_user_journey.py
```

## Unit Test Patterns

```python
# tests/unit/test_models.py
import pytest
from django.core.exceptions import ValidationError
from apps.orders.models import Order


class TestOrderModel:
    """Unit tests for Order model."""

    def test_create_order(self, db, user):
        """Test order creation."""
        order = Order.objects.create(
            user=user,
            total=100.00
        )

        assert order.pk is not None
        assert order.status == 'pending'
        assert order.created_at is not None

    def test_order_str(self, db, user):
        """Test string representation."""
        order = Order.objects.create(user=user, total=100.00)

        assert str(order) == f'Order {order.id}'

    def test_order_total_validation(self, db, user):
        """Test total must be positive."""
        with pytest.raises(ValidationError):
            order = Order(user=user, total=-10.00)
            order.full_clean()

    @pytest.mark.parametrize('status,expected', [
        ('pending', False),
        ('processing', False),
        ('shipped', False),
        ('delivered', True),
        ('cancelled', True),
    ])
    def test_is_completed(self, db, user, status, expected):
        """Test is_completed property for various statuses."""
        order = Order.objects.create(user=user, total=100.00, status=status)

        assert order.is_completed == expected
```

## Serializer Tests

```python
# tests/unit/test_serializers.py
import pytest
from apps.orders.serializers import OrderCreateSerializer


class TestOrderCreateSerializer:
    """Tests for OrderCreateSerializer."""

    def test_valid_data(self):
        """Test serializer with valid data."""
        data = {
            'items': [
                {'product_id': 'uuid', 'quantity': 2}
            ],
            'shipping_address': {
                'street': '123 Main St',
                'city': 'City',
                'postal_code': '12345',
            }
        }
        serializer = OrderCreateSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_empty_items(self):
        """Test validation rejects empty items."""
        data = {'items': []}
        serializer = OrderCreateSerializer(data=data)

        assert not serializer.is_valid()
        assert 'items' in serializer.errors

    def test_invalid_quantity(self):
        """Test validation rejects invalid quantity."""
        data = {
            'items': [
                {'product_id': 'uuid', 'quantity': 0}
            ]
        }
        serializer = OrderCreateSerializer(data=data)

        assert not serializer.is_valid()
```

## View Tests

```python
# tests/integration/test_views.py
import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import OrderFactory, ProductFactory


@pytest.mark.django_db
class TestOrderViewSet:
    """Integration tests for OrderViewSet."""

    @pytest.fixture
    def url_list(self):
        return reverse('orders:order-list')

    @pytest.fixture
    def order(self, user):
        return OrderFactory(user=user)

    # List tests

    def test_list_unauthenticated(self, api_client, url_list):
        """Test list requires authentication."""
        response = api_client.get(url_list)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_success(self, authenticated_client, url_list, order):
        """Test list returns user's orders."""
        response = authenticated_client.get(url_list)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(order.id)

    def test_list_only_own_orders(self, authenticated_client, url_list, admin_user):
        """Test users only see their own orders."""
        # Create order for different user
        OrderFactory(user=admin_user)

        response = authenticated_client.get(url_list)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0

    # Create tests

    def test_create_success(self, authenticated_client, url_list):
        """Test successful order creation."""
        product = ProductFactory()
        data = {
            'items': [
                {'product_id': str(product.id), 'quantity': 2}
            ],
            'shipping_address': {
                'street': '123 Main St',
                'city': 'City',
                'postal_code': '12345',
            }
        }

        response = authenticated_client.post(url_list, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data

    def test_create_validation_error(self, authenticated_client, url_list):
        """Test create with invalid data."""
        response = authenticated_client.post(url_list, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Retrieve tests

    def test_retrieve_success(self, authenticated_client, order):
        """Test retrieve order."""
        url = reverse('orders:order-detail', kwargs={'pk': order.id})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(order.id)

    def test_retrieve_not_found(self, authenticated_client):
        """Test retrieve non-existent order."""
        url = reverse('orders:order-detail', kwargs={'pk': 'non-existent-uuid'})

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
```

## Mocking External Services

```python
# tests/unit/test_services.py
import pytest
from unittest.mock import Mock, patch

from apps.payments.services import PaymentService


class TestPaymentService:
    """Tests for PaymentService."""

    @pytest.fixture
    def payment_service(self):
        return PaymentService()

    @patch('apps.payments.services.stripe')
    def test_create_payment_intent(self, mock_stripe, payment_service):
        """Test payment intent creation."""
        mock_stripe.PaymentIntent.create.return_value = Mock(
            id='pi_123',
            client_secret='secret_123'
        )

        result = payment_service.create_payment_intent(
            amount=1000,
            currency='usd'
        )

        assert result.id == 'pi_123'
        mock_stripe.PaymentIntent.create.assert_called_once_with(
            amount=1000,
            currency='usd'
        )

    @patch('apps.payments.services.stripe')
    def test_create_payment_intent_failure(self, mock_stripe, payment_service):
        """Test payment intent failure handling."""
        mock_stripe.PaymentIntent.create.side_effect = Exception('API Error')

        with pytest.raises(PaymentError):
            payment_service.create_payment_intent(amount=1000, currency='usd')
```

## Database Query Assertions

```python
import pytest
from django.test.utils import CaptureQueriesContext
from django.db import connection


class TestQueryOptimization:
    """Test query optimization."""

    def test_list_queries(self, authenticated_client, url_list):
        """Test list endpoint query count."""
        # Create test data
        OrderFactory.create_batch(10)

        with CaptureQueriesContext(connection) as context:
            response = authenticated_client.get(url_list)

        assert response.status_code == 200
        # Should be <= 3 queries regardless of result count
        assert len(context) <= 3, f"Too many queries: {len(context)}"


@pytest.mark.django_db(transaction=True)
class TestTransactions:
    """Test transactional behavior."""

    def test_atomic_operation(self, user):
        """Test atomic operation rolls back on error."""
        initial_balance = user.balance

        with pytest.raises(InsufficientFundsError):
            OrderService().create_order(user, amount=99999)

        user.refresh_from_db()
        assert user.balance == initial_balance
```

## Best Practices

1. **Use fixtures** - Reusable test setup
2. **Isolate tests** - No test dependencies
3. **Test one thing** - Single assertion focus
4. **Mock external services** - Fast, reliable tests
5. **Use parametrize** - Test multiple scenarios
6. **Check query count** - Prevent N+1
7. **Test error cases** - Not just happy path
