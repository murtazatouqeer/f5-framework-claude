# Django Test Template

## Overview

Template for generating pytest-django tests with factories and fixtures.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TEST_CLASS` | Test class name | `TestProductAPI` |
| `MODEL_NAME` | Model being tested | `Product` |
| `VIEWSET_NAME` | ViewSet being tested | `ProductViewSet` |
| `FACTORY_NAME` | Factory for test data | `ProductFactory` |
| `URL_PREFIX` | API URL prefix | `products` |

## Base Template

```python
# tests/{{APP_NAME}}/test_{{MODEL_NAME_SNAKE}}.py
import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import {{FACTORY_NAME}}, UserFactory


@pytest.mark.django_db
class {{TEST_CLASS}}:
    """Tests for {{MODEL_NAME}} API."""

    @pytest.fixture
    def user(self):
        """Create test user."""
        return UserFactory()

    @pytest.fixture
    def authenticated_client(self, api_client, user):
        """Return authenticated API client."""
        api_client.force_authenticate(user=user)
        return api_client

    @pytest.fixture
    def {{MODEL_NAME_SNAKE}}(self, user):
        """Create test {{MODEL_NAME}}."""
        return {{FACTORY_NAME}}(created_by=user)

    @pytest.fixture
    def url_list(self):
        """Return list URL."""
        return reverse('{{URL_PREFIX}}:{{MODEL_NAME_SNAKE}}-list')

    def url_detail(self, pk):
        """Return detail URL for given pk."""
        return reverse('{{URL_PREFIX}}:{{MODEL_NAME_SNAKE}}-detail', kwargs={'pk': pk})

    # === LIST TESTS ===

    def test_list_unauthenticated(self, api_client, url_list):
        """Test list requires authentication."""
        response = api_client.get(url_list)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_empty(self, authenticated_client, url_list):
        """Test list returns empty when no {{MODEL_NAME_SNAKE}}s."""
        response = authenticated_client.get(url_list)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_list_with_data(self, authenticated_client, url_list, user):
        """Test list returns {{MODEL_NAME_SNAKE}}s."""
        {{FACTORY_NAME}}.create_batch(5, created_by=user)

        response = authenticated_client.get(url_list)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

    def test_list_pagination(self, authenticated_client, url_list, user):
        """Test list pagination."""
        {{FACTORY_NAME}}.create_batch(30, created_by=user)

        response = authenticated_client.get(url_list, {'page_size': 10})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
        assert response.data['count'] == 30
        assert response.data['next'] is not None

    {% if FILTER_FIELDS %}
    @pytest.mark.parametrize('filter_field,filter_value', [
        {% for field in FILTER_FIELDS %}
        ('{{field.name}}', '{{field.value}}'),
        {% endfor %}
    ])
    def test_list_filtering(self, authenticated_client, url_list, user, filter_field, filter_value):
        """Test list filtering by various fields."""
        # Create matching and non-matching items
        {{FACTORY_NAME}}(**{filter_field: filter_value}, created_by=user)
        {{FACTORY_NAME}}(created_by=user)  # Non-matching

        response = authenticated_client.get(url_list, {filter_field: filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] >= 1
    {% endif %}

    {% if SEARCH_FIELDS %}
    def test_list_search(self, authenticated_client, url_list, user):
        """Test list search."""
        target = {{FACTORY_NAME}}(name='Unique Search Term', created_by=user)
        {{FACTORY_NAME}}(name='Other Item', created_by=user)

        response = authenticated_client.get(url_list, {'search': 'Unique'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(target.id)
    {% endif %}

    # === CREATE TESTS ===

    def test_create_success(self, authenticated_client, url_list):
        """Test successful creation."""
        data = {
            {% for field in CREATE_FIELDS %}
            '{{field.name}}': {{field.value}},
            {% endfor %}
        }

        response = authenticated_client.post(url_list, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert 'id' in response.data
        {% for field in CREATE_FIELDS %}
        assert response.data['{{field.name}}'] == {{field.expected}}
        {% endfor %}

    def test_create_validation_error(self, authenticated_client, url_list):
        """Test create with invalid data."""
        data = {}  # Missing required fields

        response = authenticated_client.post(url_list, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data or 'details' in response.data

    {% for validation in VALIDATIONS %}
    def test_create_{{validation.name}}(self, authenticated_client, url_list):
        """Test {{validation.description}}."""
        data = {
            {% for field in CREATE_FIELDS %}
            '{{field.name}}': {{field.value}},
            {% endfor %}
            '{{validation.field}}': {{validation.invalid_value}},
        }

        response = authenticated_client.post(url_list, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert '{{validation.field}}' in str(response.data)
    {% endfor %}

    # === RETRIEVE TESTS ===

    def test_retrieve_success(self, authenticated_client, {{MODEL_NAME_SNAKE}}):
        """Test retrieve {{MODEL_NAME_SNAKE}}."""
        url = self.url_detail({{MODEL_NAME_SNAKE}}.id)

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str({{MODEL_NAME_SNAKE}}.id)

    def test_retrieve_not_found(self, authenticated_client):
        """Test retrieve non-existent {{MODEL_NAME_SNAKE}}."""
        url = self.url_detail('00000000-0000-0000-0000-000000000000')

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # === UPDATE TESTS ===

    def test_update_full(self, authenticated_client, {{MODEL_NAME_SNAKE}}):
        """Test full update (PUT)."""
        url = self.url_detail({{MODEL_NAME_SNAKE}}.id)
        data = {
            {% for field in UPDATE_FIELDS %}
            '{{field.name}}': {{field.value}},
            {% endfor %}
        }

        response = authenticated_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        {% for field in UPDATE_FIELDS %}
        assert response.data['{{field.name}}'] == {{field.expected}}
        {% endfor %}

    def test_update_partial(self, authenticated_client, {{MODEL_NAME_SNAKE}}):
        """Test partial update (PATCH)."""
        url = self.url_detail({{MODEL_NAME_SNAKE}}.id)
        data = {'{{PATCH_FIELD}}': {{PATCH_VALUE}}}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['{{PATCH_FIELD}}'] == {{PATCH_VALUE}}

    # === DELETE TESTS ===

    def test_delete_success(self, authenticated_client, {{MODEL_NAME_SNAKE}}):
        """Test delete {{MODEL_NAME_SNAKE}}."""
        url = self.url_detail({{MODEL_NAME_SNAKE}}.id)

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_not_found(self, authenticated_client):
        """Test delete non-existent {{MODEL_NAME_SNAKE}}."""
        url = self.url_detail('00000000-0000-0000-0000-000000000000')

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    {% for action in CUSTOM_ACTIONS %}
    # === {{action.name|upper}} ACTION TESTS ===

    def test_{{action.name}}_success(self, authenticated_client, {{MODEL_NAME_SNAKE}}):
        """Test {{action.description}}."""
        url = reverse('{{URL_PREFIX}}:{{MODEL_NAME_SNAKE}}-{{action.url_name}}', kwargs={'pk': {{MODEL_NAME_SNAKE}}.id})

        response = authenticated_client.{{action.method}}(url{% if action.data %}, {{action.data}}, format='json'{% endif %})

        assert response.status_code == status.{{action.expected_status}}
        {{action.assertions}}
    {% endfor %}
```

## Factory Template

```python
# tests/factories/{{MODEL_NAME_SNAKE}}.py
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}
from tests.factories.user import UserFactory


class {{FACTORY_NAME}}(DjangoModelFactory):
    """Factory for {{MODEL_NAME}}."""

    class Meta:
        model = {{MODEL_NAME}}

    {% for field in FACTORY_FIELDS %}
    {{field.name}} = {{field.generator}}
    {% endfor %}

    created_by = factory.SubFactory(UserFactory)

    class Params:
        {% for trait in TRAITS %}
        {{trait.name}} = factory.Trait(
            {% for field, value in trait.fields.items() %}
            {{field}}={{value}},
            {% endfor %}
        )
        {% endfor %}
```

## Conftest Template

```python
# tests/conftest.py
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
    """Return admin API client."""
    api_client.force_authenticate(user=admin_user)
    return api_client
```

## Service Test Template

```python
# tests/{{APP_NAME}}/test_{{SERVICE_NAME_SNAKE}}.py
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

from apps.{{APP_NAME}}.services import {{SERVICE_NAME}}
from tests.factories import {{FACTORY_NAME}}


@pytest.mark.django_db
class Test{{SERVICE_NAME}}:
    """Tests for {{SERVICE_NAME}}."""

    @pytest.fixture
    def service(self):
        """Return service instance."""
        return {{SERVICE_NAME}}()

    def test_{{METHOD_NAME}}_success(self, service):
        """Test successful {{METHOD_NAME}}."""
        # Arrange
        {{ARRANGE}}

        # Act
        result = service.{{METHOD_NAME}}({{PARAMS}})

        # Assert
        {{ASSERTIONS}}

    def test_{{METHOD_NAME}}_failure(self, service):
        """Test {{METHOD_NAME}} failure case."""
        # Arrange
        {{FAILURE_ARRANGE}}

        # Act & Assert
        with pytest.raises({{EXCEPTION}}):
            service.{{METHOD_NAME}}({{FAILURE_PARAMS}})

    @patch('apps.{{APP_NAME}}.services.external_api')
    def test_{{METHOD_NAME}}_with_mock(self, mock_api, service):
        """Test {{METHOD_NAME}} with mocked external service."""
        # Arrange
        mock_api.call.return_value = Mock(success=True, data={'id': '123'})

        # Act
        result = service.{{METHOD_NAME}}({{PARAMS}})

        # Assert
        mock_api.call.assert_called_once()
        assert result is not None
```

## Model Test Template

```python
# tests/{{APP_NAME}}/test_models.py
import pytest
from django.core.exceptions import ValidationError

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}
from tests.factories import {{FACTORY_NAME}}


@pytest.mark.django_db
class Test{{MODEL_NAME}}Model:
    """Tests for {{MODEL_NAME}} model."""

    def test_create(self):
        """Test model creation."""
        instance = {{FACTORY_NAME}}()

        assert instance.pk is not None
        assert instance.created_at is not None

    def test_str(self):
        """Test string representation."""
        instance = {{FACTORY_NAME}}(name='Test Name')

        assert str(instance) == 'Test Name'

    @pytest.mark.parametrize('status,expected', [
        ('pending', False),
        ('active', True),
        ('completed', True),
    ])
    def test_is_active_property(self, status, expected):
        """Test is_active property for various statuses."""
        instance = {{FACTORY_NAME}}(status=status)

        assert instance.is_active == expected

    def test_validation(self):
        """Test model validation."""
        instance = {{FACTORY_NAME}}.build({{INVALID_FIELD}}={{INVALID_VALUE}})

        with pytest.raises(ValidationError):
            instance.full_clean()
```

## Usage Example

```yaml
input:
  APP_NAME: products
  MODEL_NAME: Product
  MODEL_NAME_SNAKE: product
  TEST_CLASS: TestProductAPI
  FACTORY_NAME: ProductFactory
  URL_PREFIX: products
  CREATE_FIELDS:
    - name: name
      value: "'Test Product'"
      expected: "'Test Product'"
    - name: sku
      value: "'SKU-001'"
      expected: "'SKU-001'"
    - name: price
      value: "'99.99'"
      expected: "'99.99'"
  UPDATE_FIELDS:
    - name: name
      value: "'Updated Product'"
      expected: "'Updated Product'"
  PATCH_FIELD: name
  PATCH_VALUE: "'Patched Name'"
  SEARCH_FIELDS: ['name', 'description']
  FILTER_FIELDS:
    - name: status
      value: active
    - name: category
      value: electronics
  CUSTOM_ACTIONS:
    - name: activate
      url_name: activate
      method: post
      description: "Activate product"
      expected_status: HTTP_200_OK
      assertions: |
        product.refresh_from_db()
        assert product.status == 'active'
```

## Best Practices

1. **Use fixtures** - reusable test setup
2. **Use factories** - consistent test data generation
3. **Test edge cases** - empty, null, boundary values
4. **Use parametrize** - test multiple scenarios efficiently
5. **Mock external services** - isolate unit tests
6. **Check query count** - prevent N+1 queries
7. **Group tests by feature** - organize test classes logically
8. **Use meaningful names** - test_METHOD_SCENARIO
