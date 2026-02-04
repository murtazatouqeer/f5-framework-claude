# Django REST Framework ViewSet Template

## Overview

Template for generating DRF ViewSets with filtering, pagination, and custom actions.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `VIEWSET_NAME` | ViewSet class name | `ProductViewSet` |
| `MODEL_NAME` | Associated model | `Product` |
| `SERIALIZER_CLASS` | Default serializer | `ProductSerializer` |
| `QUERYSET` | Base queryset | `Product.objects.all()` |
| `PERMISSION_CLASSES` | Permissions | `[IsAuthenticated]` |
| `FILTER_FIELDS` | Filterable fields | `['status', 'category']` |
| `SEARCH_FIELDS` | Searchable fields | `['name', 'description']` |
| `ORDERING_FIELDS` | Orderable fields | `['created_at', 'price']` |

## Base Template

```python
# apps/{{APP_NAME}}/views/{{MODEL_NAME_SNAKE}}.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}
from apps.{{APP_NAME}}.serializers import (
    {{MODEL_NAME}}Serializer,
    {{MODEL_NAME}}ListSerializer,
    {{MODEL_NAME}}CreateSerializer,
    {{MODEL_NAME}}UpdateSerializer,
)
{% if FILTER_CLASS %}
from apps.{{APP_NAME}}.filters import {{MODEL_NAME}}Filter
{% endif %}


class {{VIEWSET_NAME}}(viewsets.ModelViewSet):
    """
    ViewSet for {{MODEL_NAME}} CRUD operations.

    Endpoints:
        GET    /{{URL_PREFIX}}/           - List all
        POST   /{{URL_PREFIX}}/           - Create new
        GET    /{{URL_PREFIX}}/{id}/      - Retrieve one
        PUT    /{{URL_PREFIX}}/{id}/      - Full update
        PATCH  /{{URL_PREFIX}}/{id}/      - Partial update
        DELETE /{{URL_PREFIX}}/{id}/      - Delete

    Query Parameters:
        search: Search in {{SEARCH_FIELDS}}
        ordering: Sort by {{ORDERING_FIELDS}}
        {% for field in FILTER_FIELDS %}
        {{field}}: Filter by {{field}}
        {% endfor %}
    """

    queryset = {{MODEL_NAME}}.objects.all()
    serializer_class = {{MODEL_NAME}}Serializer
    permission_classes = [IsAuthenticated]

    # Filtering
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    {% if FILTER_CLASS %}
    filterset_class = {{MODEL_NAME}}Filter
    {% else %}
    filterset_fields = {{FILTER_FIELDS}}
    {% endif %}
    search_fields = {{SEARCH_FIELDS}}
    ordering_fields = {{ORDERING_FIELDS}}
    ordering = ['-created_at']

    def get_queryset(self):
        """
        Optimize queryset with select_related/prefetch_related.
        Filter by user if needed.
        """
        queryset = super().get_queryset()

        {% if SELECT_RELATED %}
        queryset = queryset.select_related({{SELECT_RELATED}})
        {% endif %}
        {% if PREFETCH_RELATED %}
        queryset = queryset.prefetch_related({{PREFETCH_RELATED}})
        {% endif %}

        {% if USER_FILTERED %}
        # Filter to user's own records
        if not self.request.user.is_staff:
            queryset = queryset.filter(created_by=self.request.user)
        {% endif %}

        return queryset

    def get_serializer_class(self):
        """Return appropriate serializer for action."""
        serializer_map = {
            'list': {{MODEL_NAME}}ListSerializer,
            'create': {{MODEL_NAME}}CreateSerializer,
            'update': {{MODEL_NAME}}UpdateSerializer,
            'partial_update': {{MODEL_NAME}}UpdateSerializer,
        }
        return serializer_map.get(self.action, self.serializer_class)

    def get_permissions(self):
        """Return permissions based on action."""
        {% if ACTION_PERMISSIONS %}
        permission_map = {
            {% for action, perms in ACTION_PERMISSIONS.items() %}
            '{{action}}': [{{perms}}],
            {% endfor %}
        }
        permissions = permission_map.get(self.action, self.permission_classes)
        return [permission() for permission in permissions]
        {% else %}
        return super().get_permissions()
        {% endif %}

    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)

    {% for custom_action in CUSTOM_ACTIONS %}
    @action(
        detail={{custom_action.detail}},
        methods={{custom_action.methods}},
        {% if custom_action.url_path %}url_path='{{custom_action.url_path}}',{% endif %}
        {% if custom_action.serializer %}serializer_class={{custom_action.serializer}},{% endif %}
    )
    def {{custom_action.name}}(self, request{% if custom_action.detail %}, pk=None{% endif %}):
        """{{custom_action.description}}"""
        {% if custom_action.detail %}
        instance = self.get_object()
        {% endif %}
        {{custom_action.implementation}}

    {% endfor %}
```

## Filter Class Template

```python
# apps/{{APP_NAME}}/filters.py
import django_filters
from apps.{{APP_NAME}}.models import {{MODEL_NAME}}


class {{MODEL_NAME}}Filter(django_filters.FilterSet):
    """Filter for {{MODEL_NAME}}."""

    # Range filters
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')

    # Date range filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte'
    )

    # Choice filter
    status = django_filters.ChoiceFilter(choices={{MODEL_NAME}}.Status.choices)

    # Related filter
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.all()
    )

    class Meta:
        model = {{MODEL_NAME}}
        fields = ['status', 'category', 'is_active']
```

## Custom Actions

### Detail Actions (Single Object)

```python
@action(detail=True, methods=['post'])
def activate(self, request, pk=None):
    """Activate this item."""
    instance = self.get_object()
    instance.status = 'active'
    instance.save(update_fields=['status', 'updated_at'])
    serializer = self.get_serializer(instance)
    return Response(serializer.data)

@action(detail=True, methods=['post'])
def archive(self, request, pk=None):
    """Archive this item."""
    instance = self.get_object()
    instance.archived_at = timezone.now()
    instance.save(update_fields=['archived_at', 'updated_at'])
    return Response({'status': 'archived'})

@action(detail=True, methods=['post'], url_path='add-tag')
def add_tag(self, request, pk=None):
    """Add tag to item."""
    instance = self.get_object()
    tag_id = request.data.get('tag_id')
    instance.tags.add(tag_id)
    serializer = self.get_serializer(instance)
    return Response(serializer.data)
```

### List Actions (Collection)

```python
@action(detail=False, methods=['post'], url_path='bulk-delete')
def bulk_delete(self, request):
    """Delete multiple items."""
    ids = request.data.get('ids', [])
    if not ids:
        return Response(
            {'error': 'No IDs provided'},
            status=status.HTTP_400_BAD_REQUEST
        )

    deleted_count, _ = self.get_queryset().filter(id__in=ids).delete()
    return Response({'deleted_count': deleted_count})

@action(detail=False, methods=['post'], url_path='bulk-update')
def bulk_update(self, request):
    """Update multiple items."""
    ids = request.data.get('ids', [])
    update_data = request.data.get('data', {})

    updated_count = self.get_queryset().filter(id__in=ids).update(**update_data)
    return Response({'updated_count': updated_count})

@action(detail=False, methods=['get'])
def export(self, request):
    """Export items to CSV."""
    import csv
    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Status', 'Created'])

    for item in self.get_queryset():
        writer.writerow([item.id, item.name, item.status, item.created_at])

    return response

@action(detail=False, methods=['get'])
def stats(self, request):
    """Get statistics."""
    queryset = self.get_queryset()
    return Response({
        'total': queryset.count(),
        'active': queryset.filter(status='active').count(),
        'inactive': queryset.filter(status='inactive').count(),
    })
```

## URL Configuration

```python
# apps/{{APP_NAME}}/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.{{APP_NAME}}.views import {{VIEWSET_NAME}}

router = DefaultRouter()
router.register('{{URL_PREFIX}}', {{VIEWSET_NAME}}, basename='{{MODEL_NAME_SNAKE}}')

urlpatterns = [
    path('', include(router.urls)),
]
```

## Pagination Configuration

```python
# apps/core/pagination.py
from rest_framework.pagination import PageNumberPagination, CursorPagination


class StandardPagination(PageNumberPagination):
    """Standard page number pagination."""

    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


class CursorPagination(CursorPagination):
    """Cursor pagination for large datasets."""

    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'
```

## Usage Example

```yaml
input:
  APP_NAME: products
  VIEWSET_NAME: ProductViewSet
  MODEL_NAME: Product
  MODEL_NAME_SNAKE: product
  URL_PREFIX: products
  FILTER_FIELDS: "['status', 'category', 'is_featured']"
  SEARCH_FIELDS: "['name', 'description', 'sku']"
  ORDERING_FIELDS: "['created_at', 'price', 'name']"
  SELECT_RELATED: "'category'"
  PREFETCH_RELATED: "'tags'"
  USER_FILTERED: false
  CUSTOM_ACTIONS:
    - name: activate
      detail: true
      methods: "['post']"
      description: "Activate this product"
      implementation: |
        instance.status = 'active'
        instance.save()
        return Response({'status': 'activated'})
    - name: bulk_delete
      detail: false
      methods: "['post']"
      url_path: bulk-delete
      description: "Delete multiple products"
      implementation: |
        ids = request.data.get('ids', [])
        count, _ = self.get_queryset().filter(id__in=ids).delete()
        return Response({'deleted': count})
```

## Generated Output Example

```python
# apps/products/views/product.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.products.models import Product
from apps.products.serializers import (
    ProductSerializer,
    ProductListSerializer,
    ProductCreateSerializer,
    ProductUpdateSerializer,
)
from apps.products.filters import ProductFilter


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations.

    Endpoints:
        GET    /products/           - List all products
        POST   /products/           - Create new product
        GET    /products/{id}/      - Retrieve product
        PUT    /products/{id}/      - Full update
        PATCH  /products/{id}/      - Partial update
        DELETE /products/{id}/      - Delete product
        POST   /products/{id}/activate/    - Activate product
        POST   /products/bulk-delete/      - Bulk delete
    """

    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['created_at', 'price', 'name']
    ordering = ['-created_at']

    def get_queryset(self):
        """Optimize queryset."""
        return super().get_queryset().select_related(
            'category'
        ).prefetch_related(
            'tags'
        )

    def get_serializer_class(self):
        """Return appropriate serializer."""
        serializer_map = {
            'list': ProductListSerializer,
            'create': ProductCreateSerializer,
            'update': ProductUpdateSerializer,
            'partial_update': ProductUpdateSerializer,
        }
        return serializer_map.get(self.action, self.serializer_class)

    def perform_create(self, serializer):
        """Set created_by on creation."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate this product."""
        instance = self.get_object()
        instance.status = 'active'
        instance.save(update_fields=['status', 'updated_at'])
        return Response({'status': 'activated'})

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        """Delete multiple products."""
        ids = request.data.get('ids', [])
        count, _ = self.get_queryset().filter(id__in=ids).delete()
        return Response({'deleted': count})
```

## Best Practices

1. **Use action-specific serializers** - different fields for list/create/update
2. **Optimize querysets** - select_related/prefetch_related in get_queryset
3. **Consistent filtering** - use django-filters for complex filtering
4. **Document endpoints** - clear docstrings with examples
5. **Handle permissions per action** - override get_permissions
6. **Use URL conventions** - kebab-case for url_path
7. **Return appropriate status codes** - 200, 201, 204, 400, 404
