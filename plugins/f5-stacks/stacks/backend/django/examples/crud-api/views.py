# apps/products/views.py
"""
Product ViewSet with filtering and custom actions.

REQ-001: Product CRUD API
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Count, Sum

from apps.products.models import Product
from apps.products.serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
    BulkDeleteSerializer,
)
from apps.products.filters import ProductFilter


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations.

    Endpoints:
        GET    /products/                - List all products
        POST   /products/                - Create new product
        GET    /products/{id}/           - Retrieve product
        PUT    /products/{id}/           - Full update
        PATCH  /products/{id}/           - Partial update
        DELETE /products/{id}/           - Soft delete
        POST   /products/{id}/activate/  - Activate product
        POST   /products/{id}/deactivate/- Deactivate product
        POST   /products/bulk-delete/    - Bulk delete products
        GET    /products/stats/          - Get statistics

    Query Parameters:
        search: Search in name, sku, description
        status: Filter by status
        category: Filter by category ID
        price_min: Minimum price
        price_max: Maximum price
        in_stock: Filter in-stock items (true/false)
        ordering: Sort by field (prefix with - for desc)
        page: Page number
        page_size: Items per page (max 100)
    """

    queryset = Product.objects.all()
    serializer_class = ProductDetailSerializer
    permission_classes = [IsAuthenticated]

    # Filtering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'price', 'stock', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optimize queryset with select_related/prefetch_related.
        """
        queryset = super().get_queryset()

        # Optimize for list view
        if self.action == 'list':
            queryset = queryset.select_related('category')
        # Optimize for detail view
        elif self.action in ['retrieve', 'update', 'partial_update']:
            queryset = queryset.select_related(
                'category',
                'created_by'
            ).prefetch_related('tags')

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer for action."""
        serializer_map = {
            'list': ProductListSerializer,
            'create': ProductCreateSerializer,
            'update': ProductUpdateSerializer,
            'partial_update': ProductUpdateSerializer,
            'bulk_delete': BulkDeleteSerializer,
        }
        return serializer_map.get(self.action, self.serializer_class)

    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        """Soft delete instead of hard delete."""
        instance.delete()  # Uses soft delete

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate a product.

        Sets status to 'active' if product has stock.
        """
        product = self.get_object()

        if product.stock <= 0:
            return Response(
                {'error': 'Cannot activate product with no stock.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.status = 'active'
        product.save(update_fields=['status', 'updated_at'])

        serializer = self.get_serializer(product)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate a product.

        Sets status to 'inactive'.
        """
        product = self.get_object()
        product.status = 'inactive'
        product.save(update_fields=['status', 'updated_at'])

        serializer = self.get_serializer(product)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        """
        Bulk delete multiple products.

        Request body:
            ids: List of product UUIDs to delete
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        ids = serializer.validated_data['ids']
        deleted_count = self.get_queryset().filter(id__in=ids).delete()

        return Response({
            'deleted_count': deleted_count,
            'ids': ids,
        })

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get product statistics.

        Returns counts by status and inventory summary.
        """
        queryset = self.get_queryset()

        # Count by status
        status_counts = queryset.values('status').annotate(
            count=Count('id')
        )

        # Inventory stats
        inventory = queryset.aggregate(
            total_products=Count('id'),
            total_stock=Sum('stock'),
            total_value=Sum('price'),
        )

        return Response({
            'by_status': {
                item['status']: item['count']
                for item in status_counts
            },
            'inventory': {
                'total_products': inventory['total_products'] or 0,
                'total_stock': inventory['total_stock'] or 0,
                'total_value': str(inventory['total_value'] or 0),
            },
        })

    @action(detail=True, methods=['post'])
    def restore(self, request, pk=None):
        """
        Restore a soft-deleted product.

        Only available for admin users.
        """
        # Get from all_objects to include deleted
        product = Product.all_objects.get(pk=pk)

        if product.deleted_at is None:
            return Response(
                {'error': 'Product is not deleted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        product.restore()
        serializer = self.get_serializer(product)
        return Response(serializer.data)
