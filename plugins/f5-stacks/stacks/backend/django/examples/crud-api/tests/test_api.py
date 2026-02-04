# tests/products/test_api.py
"""
API tests for Product endpoints.

REQ-001: Product CRUD API
"""
import pytest
from django.urls import reverse
from rest_framework import status

from apps.products.models import Product
from tests.factories import ProductFactory


@pytest.mark.django_db
class TestProductListAPI:
    """Tests for product list endpoint."""

    @pytest.fixture
    def url(self):
        return reverse('products:product-list')

    def test_list_unauthenticated(self, api_client, url):
        """Test list requires authentication."""
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_empty(self, authenticated_client, url):
        """Test list returns empty when no products."""
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 0
        assert response.data['results'] == []

    def test_list_with_products(self, authenticated_client, url, user):
        """Test list returns products."""
        ProductFactory.create_batch(5, created_by=user)

        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5
        assert len(response.data['results']) == 5

    def test_list_pagination(self, authenticated_client, url, user):
        """Test list pagination."""
        ProductFactory.create_batch(30, created_by=user)

        response = authenticated_client.get(url, {'page_size': 10})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 10
        assert response.data['count'] == 30
        assert response.data['next'] is not None

    def test_list_search(self, authenticated_client, url, user):
        """Test list search."""
        target = ProductFactory(name='Unique Widget', created_by=user)
        ProductFactory(name='Other Item', created_by=user)

        response = authenticated_client.get(url, {'search': 'Widget'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['id'] == str(target.id)

    def test_list_filter_status(self, authenticated_client, url, user):
        """Test filter by status."""
        ProductFactory(status='active', created_by=user)
        ProductFactory(status='draft', created_by=user)

        response = authenticated_client.get(url, {'status': 'active'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['status'] == 'active'

    def test_list_filter_price_range(self, authenticated_client, url, user):
        """Test filter by price range."""
        ProductFactory(price='50.00', created_by=user)
        ProductFactory(price='150.00', created_by=user)
        ProductFactory(price='250.00', created_by=user)

        response = authenticated_client.get(url, {'price_min': 100, 'price_max': 200})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_list_ordering(self, authenticated_client, url, user):
        """Test list ordering."""
        ProductFactory(price='100.00', created_by=user)
        ProductFactory(price='50.00', created_by=user)
        ProductFactory(price='150.00', created_by=user)

        response = authenticated_client.get(url, {'ordering': 'price'})

        assert response.status_code == status.HTTP_200_OK
        prices = [r['price'] for r in response.data['results']]
        assert prices == sorted(prices)


@pytest.mark.django_db
class TestProductCreateAPI:
    """Tests for product create endpoint."""

    @pytest.fixture
    def url(self):
        return reverse('products:product-list')

    @pytest.fixture
    def valid_data(self):
        return {
            'name': 'New Product',
            'sku': 'SKU-NEW-001',
            'description': 'A new product description',
            'price': '99.99',
            'stock': 50,
            'status': 'draft',
        }

    def test_create_success(self, authenticated_client, url, valid_data):
        """Test successful product creation."""
        response = authenticated_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Product'
        assert response.data['sku'] == 'SKU-NEW-001'
        assert 'id' in response.data

    def test_create_sets_created_by(self, authenticated_client, url, valid_data, user):
        """Test created_by is set to current user."""
        response = authenticated_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        product = Product.objects.get(pk=response.data['id'])
        assert product.created_by == user

    def test_create_validation_error(self, authenticated_client, url):
        """Test create with missing required fields."""
        response = authenticated_client.post(url, {}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_duplicate_sku(self, authenticated_client, url, valid_data, user):
        """Test create with duplicate SKU."""
        ProductFactory(sku='SKU-NEW-001', created_by=user)

        response = authenticated_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'sku' in str(response.data).lower()

    def test_create_invalid_price(self, authenticated_client, url, valid_data):
        """Test create with invalid price."""
        valid_data['price'] = '-10.00'

        response = authenticated_client.post(url, valid_data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestProductDetailAPI:
    """Tests for product detail endpoint."""

    def url(self, pk):
        return reverse('products:product-detail', kwargs={'pk': pk})

    @pytest.fixture
    def product(self, user):
        return ProductFactory(created_by=user)

    def test_retrieve_success(self, authenticated_client, product):
        """Test retrieve product."""
        response = authenticated_client.get(self.url(product.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == str(product.id)
        assert response.data['name'] == product.name

    def test_retrieve_not_found(self, authenticated_client):
        """Test retrieve non-existent product."""
        response = authenticated_client.get(
            self.url('00000000-0000-0000-0000-000000000000')
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_full(self, authenticated_client, product):
        """Test full update."""
        data = {
            'name': 'Updated Name',
            'description': 'Updated description',
            'price': '199.99',
            'stock': 100,
        }

        response = authenticated_client.put(
            self.url(product.id), data, format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Updated Name'

    def test_update_partial(self, authenticated_client, product):
        """Test partial update."""
        response = authenticated_client.patch(
            self.url(product.id),
            {'name': 'Patched Name'},
            format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Patched Name'

    def test_delete_soft(self, authenticated_client, product):
        """Test soft delete."""
        response = authenticated_client.delete(self.url(product.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Product still exists but is soft-deleted
        product.refresh_from_db()
        assert product.deleted_at is not None


@pytest.mark.django_db
class TestProductCustomActionsAPI:
    """Tests for product custom actions."""

    @pytest.fixture
    def product(self, user):
        return ProductFactory(status='draft', stock=50, created_by=user)

    def test_activate_success(self, authenticated_client, product):
        """Test activate action."""
        url = reverse('products:product-activate', kwargs={'pk': product.id})

        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.status == 'active'

    def test_activate_no_stock(self, authenticated_client, user):
        """Test activate fails with no stock."""
        product = ProductFactory(status='draft', stock=0, created_by=user)
        url = reverse('products:product-activate', kwargs={'pk': product.id})

        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_deactivate(self, authenticated_client, user):
        """Test deactivate action."""
        product = ProductFactory(status='active', created_by=user)
        url = reverse('products:product-deactivate', kwargs={'pk': product.id})

        response = authenticated_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.status == 'inactive'

    def test_bulk_delete(self, authenticated_client, user):
        """Test bulk delete action."""
        products = ProductFactory.create_batch(5, created_by=user)
        ids = [str(p.id) for p in products[:3]]

        url = reverse('products:product-bulk-delete')
        response = authenticated_client.post(url, {'ids': ids}, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['deleted_count'] == 3

    def test_stats(self, authenticated_client, user):
        """Test stats action."""
        ProductFactory.create_batch(3, status='active', created_by=user)
        ProductFactory.create_batch(2, status='draft', created_by=user)

        url = reverse('products:product-stats')
        response = authenticated_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['by_status']['active'] == 3
        assert response.data['by_status']['draft'] == 2
        assert response.data['inventory']['total_products'] == 5
