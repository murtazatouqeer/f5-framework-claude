# DRF API Testing Skill

## Overview

Comprehensive API testing patterns for Django REST Framework.

## APIClient Setup

```python
# conftest.py
import pytest
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """Return fresh API client."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    """Return authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def jwt_client(api_client, user):
    """Return client with JWT token."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client
```

## CRUD Testing Pattern

```python
import pytest
from django.urls import reverse
from rest_framework import status

from tests.factories import ProductFactory


@pytest.mark.django_db
class TestProductAPI:
    """Complete CRUD tests for Product API."""

    @pytest.fixture
    def url_list(self):
        return reverse('products:product-list')

    def url_detail(self, pk):
        return reverse('products:product-detail', kwargs={'pk': pk})

    @pytest.fixture
    def product(self):
        return ProductFactory()

    # === LIST ===

    def test_list_unauthenticated(self, api_client, url_list):
        """Test list requires auth."""
        response = api_client.get(url_list)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_empty(self, authenticated_client, url_list):
        """Test list returns empty when no products."""
        response = authenticated_client.get(url_list)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_list_with_data(self, authenticated_client, url_list):
        """Test list returns products."""
        ProductFactory.create_batch(5)

        response = authenticated_client.get(url_list)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

    def test_list_pagination(self, authenticated_client, url_list):
        """Test list pagination."""
        ProductFactory.create_batch(30)

        response = authenticated_client.get(url_list, {'page_size': 10})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
        assert response.data['count'] == 30
        assert response.data['next'] is not None

    def test_list_filtering(self, authenticated_client, url_list):
        """Test list filtering."""
        active = ProductFactory(status='active')
        ProductFactory(status='inactive')

        response = authenticated_client.get(url_list, {'status': 'active'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(active.id)

    def test_list_search(self, authenticated_client, url_list):
        """Test list search."""
        target = ProductFactory(name='Special Widget')
        ProductFactory(name='Regular Item')

        response = authenticated_client.get(url_list, {'search': 'Widget'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_list_ordering(self, authenticated_client, url_list):
        """Test list ordering."""
        ProductFactory(price=100)
        ProductFactory(price=50)
        ProductFactory(price=150)

        response = authenticated_client.get(url_list, {'ordering': 'price'})

        assert response.status_code == status.HTTP_200_OK
        prices = [r['price'] for r in response.data['results']]
        assert prices == sorted(prices)

    # === CREATE ===

    def test_create_success(self, authenticated_client, url_list):
        """Test create product."""
        data = {
            'name': 'New Product',
            'price': '99.99',
            'sku': 'SKU-001',
            'stock': 100,
        }

        response = authenticated_client.post(url_list, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Product'
        assert 'id' in response.data

    def test_create_validation_error(self, authenticated_client, url_list):
        """Test create with invalid data."""
        data = {'name': ''}  # Missing required fields

        response = authenticated_client.post(url_list, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data['details']

    def test_create_duplicate_sku(self, authenticated_client, url_list, product):
        """Test create with duplicate SKU."""
        data = {
            'name': 'Another Product',
            'sku': product.sku,  # Duplicate
            'price': '50.00',
        }

        response = authenticated_client.post(url_list, data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    # === RETRIEVE ===

    def test_retrieve_success(self, authenticated_client, product):
        """Test retrieve product."""
        url = self.url_detail(product.id)

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(product.id)
        assert response.data['name'] == product.name

    def test_retrieve_not_found(self, authenticated_client):
        """Test retrieve non-existent product."""
        url = self.url_detail('00000000-0000-0000-0000-000000000000')

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    # === UPDATE ===

    def test_update_full(self, authenticated_client, product):
        """Test full update (PUT)."""
        url = self.url_detail(product.id)
        data = {
            'name': 'Updated Name',
            'price': '199.99',
            'sku': product.sku,
            'stock': 50,
        }

        response = authenticated_client.put(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_update_partial(self, authenticated_client, product):
        """Test partial update (PATCH)."""
        url = self.url_detail(product.id)
        data = {'name': 'Partially Updated'}

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Partially Updated'
        # Other fields unchanged
        assert response.data['price'] == str(product.price)

    # === DELETE ===

    def test_delete_success(self, authenticated_client, product):
        """Test delete product."""
        url = self.url_detail(product.id)

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_not_found(self, authenticated_client):
        """Test delete non-existent."""
        url = self.url_detail('00000000-0000-0000-0000-000000000000')

        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
```

## Custom Action Testing

```python
@pytest.mark.django_db
class TestProductCustomActions:
    """Test custom ViewSet actions."""

    def test_activate(self, authenticated_client, product):
        """Test activate action."""
        product.status = 'inactive'
        product.save()

        url = reverse('products:product-activate', kwargs={'pk': product.id})
        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.status == 'active'

    def test_bulk_delete(self, authenticated_client):
        """Test bulk delete action."""
        products = ProductFactory.create_batch(5)
        ids = [str(p.id) for p in products[:3]]

        url = reverse('products:product-bulk-delete')
        response = authenticated_client.post(url, {'ids': ids}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['deleted_count'] == 3

    def test_export(self, authenticated_client):
        """Test export action."""
        ProductFactory.create_batch(10)

        url = reverse('products:product-export')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'text/csv'
```

## File Upload Testing

```python
import io
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.mark.django_db
class TestProductImageUpload:
    """Test image upload functionality."""

    @pytest.fixture
    def image_file(self):
        """Create test image file."""
        file = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='red')
        image.save(file, 'JPEG')
        file.seek(0)
        return SimpleUploadedFile(
            'test.jpg',
            file.read(),
            content_type='image/jpeg'
        )

    def test_upload_image(self, authenticated_client, product, image_file):
        """Test image upload."""
        url = reverse('products:product-upload-image', kwargs={'pk': product.id})

        response = authenticated_client.post(
            url,
            {'image': image_file},
            format='multipart'
        )

        assert response.status_code == status.HTTP_200_OK
        assert 'image_url' in response.data

    def test_upload_invalid_file(self, authenticated_client, product):
        """Test upload invalid file type."""
        url = reverse('products:product-upload-image', kwargs={'pk': product.id})
        file = SimpleUploadedFile('test.txt', b'not an image', content_type='text/plain')

        response = authenticated_client.post(url, {'image': file}, format='multipart')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
```

## Error Response Testing

```python
@pytest.mark.django_db
class TestErrorResponses:
    """Test API error responses."""

    def test_validation_error_format(self, authenticated_client):
        """Test validation error response format."""
        url = reverse('products:product-list')
        response = authenticated_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'message' in response.data
        assert 'details' in response.data

    def test_authentication_error_format(self, api_client):
        """Test authentication error format."""
        url = reverse('products:product-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data['error'] == 'not_authenticated'

    def test_permission_error_format(self, authenticated_client, admin_product):
        """Test permission error format."""
        url = reverse('products:product-detail', kwargs={'pk': admin_product.id})
        response = authenticated_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error'] == 'permission_denied'
```

## Best Practices

1. **Test all HTTP methods** - GET, POST, PUT, PATCH, DELETE
2. **Test authentication** - Both authenticated and unauthenticated
3. **Test validation** - Valid and invalid data
4. **Test edge cases** - Empty, null, boundary values
5. **Test permissions** - Object-level and action-level
6. **Test pagination** - With large datasets
7. **Use factories** - Consistent test data
8. **Check response format** - Status code, content type, structure
