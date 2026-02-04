# Django API URL Configuration Template

## Overview

Template for generating API URL patterns with DRF routers and nested routes.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `APP_NAME` | Application name | `products` |
| `VIEWSETS` | List of ViewSets to register | See below |
| `NESTED_ROUTES` | Nested router configurations | See below |
| `EXTRA_URLS` | Additional URL patterns | See below |

## Base Template

```python
# apps/{{APP_NAME}}/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
{% if NESTED_ROUTES %}
from rest_framework_nested import routers as nested_routers
{% endif %}

{% for viewset in VIEWSETS %}
from apps.{{APP_NAME}}.views import {{viewset.class_name}}
{% endfor %}

app_name = '{{APP_NAME}}'

# Main router
router = DefaultRouter()
{% for viewset in VIEWSETS %}
router.register('{{viewset.prefix}}', {{viewset.class_name}}, basename='{{viewset.basename}}')
{% endfor %}

{% if NESTED_ROUTES %}
# Nested routers
{% for nested in NESTED_ROUTES %}
{{nested.name}}_router = nested_routers.NestedDefaultRouter(
    router,
    '{{nested.parent_prefix}}',
    lookup='{{nested.lookup}}'
)
{{nested.name}}_router.register(
    '{{nested.prefix}}',
    {{nested.viewset}},
    basename='{{nested.basename}}'
)
{% endfor %}
{% endif %}

urlpatterns = [
    path('', include(router.urls)),
    {% if NESTED_ROUTES %}
    {% for nested in NESTED_ROUTES %}
    path('', include({{nested.name}}_router.urls)),
    {% endfor %}
    {% endif %}
    {% for url in EXTRA_URLS %}
    path('{{url.path}}', {{url.view}}, name='{{url.name}}'),
    {% endfor %}
]
```

## Project-Level URL Configuration

```python
# config/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include([
        # Authentication
        path('auth/', include([
            path('token/', TokenObtainPairView.as_view(), name='token_obtain'),
            path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
            path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
        ])),

        # Apps
        path('users/', include('apps.users.urls')),
        path('products/', include('apps.products.urls')),
        path('orders/', include('apps.orders.urls')),
    ])),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Debug toolbar
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path('__debug__/', include('debug_toolbar.urls'))]
```

## Router Patterns

### Simple Router

```python
from rest_framework.routers import DefaultRouter
from apps.products.views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')

# Generated URLs:
# GET/POST     /products/
# GET/PUT/DELETE /products/{pk}/
# GET/POST     /categories/
# GET/PUT/DELETE /categories/{pk}/
```

### Nested Router (drf-nested-routers)

```python
from rest_framework_nested import routers as nested_routers

# Parent router
router = DefaultRouter()
router.register('orders', OrderViewSet, basename='order')

# Nested router for order items
items_router = nested_routers.NestedDefaultRouter(
    router,
    'orders',
    lookup='order'  # Creates order_pk parameter
)
items_router.register('items', OrderItemViewSet, basename='order-item')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(items_router.urls)),
]

# Generated URLs:
# GET/POST     /orders/
# GET/PUT/DELETE /orders/{pk}/
# GET/POST     /orders/{order_pk}/items/
# GET/PUT/DELETE /orders/{order_pk}/items/{pk}/
```

### Deep Nested Routes

```python
# Three levels: Store -> Product -> Review
store_router = DefaultRouter()
store_router.register('stores', StoreViewSet, basename='store')

product_router = nested_routers.NestedDefaultRouter(
    store_router, 'stores', lookup='store'
)
product_router.register('products', StoreProductViewSet, basename='store-product')

review_router = nested_routers.NestedDefaultRouter(
    product_router, 'products', lookup='product'
)
review_router.register('reviews', ProductReviewViewSet, basename='product-review')

# URLs:
# /stores/{store_pk}/products/{product_pk}/reviews/
# /stores/{store_pk}/products/{product_pk}/reviews/{pk}/
```

## ViewSet with Nested Lookup

```python
class OrderItemViewSet(viewsets.ModelViewSet):
    """ViewSet for order items."""

    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by parent order."""
        return OrderItem.objects.filter(
            order_id=self.kwargs['order_pk'],
            order__user=self.request.user
        )

    def perform_create(self, serializer):
        """Create item for parent order."""
        order = get_object_or_404(
            Order,
            pk=self.kwargs['order_pk'],
            user=self.request.user
        )
        serializer.save(order=order)
```

## Custom Actions in URLs

```python
# ViewSet with custom actions
class ProductViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        pass

    @action(detail=False, methods=['get'])
    def featured(self, request):
        pass

    @action(detail=True, methods=['post'], url_path='add-to-cart')
    def add_to_cart(self, request, pk=None):
        pass

# Auto-generated URLs:
# POST /products/{pk}/activate/
# GET  /products/featured/
# POST /products/{pk}/add-to-cart/
```

## API Versioning

### URL Path Versioning

```python
# config/urls.py
urlpatterns = [
    path('api/v1/', include('config.urls_v1')),
    path('api/v2/', include('config.urls_v2')),
]

# config/urls_v1.py
urlpatterns = [
    path('products/', include('apps.products.urls_v1')),
]

# config/urls_v2.py
urlpatterns = [
    path('products/', include('apps.products.urls_v2')),
]
```

### Namespace Versioning

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.NamespaceVersioning',
}

# urls.py
urlpatterns = [
    path('api/v1/', include('apps.products.urls', namespace='v1')),
    path('api/v2/', include('apps.products.urls', namespace='v2')),
]
```

## Usage Example

```yaml
input:
  APP_NAME: products
  VIEWSETS:
    - class_name: ProductViewSet
      prefix: ''
      basename: product
    - class_name: CategoryViewSet
      prefix: categories
      basename: category
  NESTED_ROUTES:
    - name: product_reviews
      parent_prefix: ''
      lookup: product
      prefix: reviews
      viewset: ProductReviewViewSet
      basename: product-review
  EXTRA_URLS:
    - path: featured/
      view: FeaturedProductsView.as_view()
      name: featured-products
```

## Generated Output Example

```python
# apps/products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from apps.products.views import (
    ProductViewSet,
    CategoryViewSet,
    ProductReviewViewSet,
    FeaturedProductsView,
)

app_name = 'products'

# Main router
router = DefaultRouter()
router.register('', ProductViewSet, basename='product')
router.register('categories', CategoryViewSet, basename='category')

# Nested router for product reviews
product_reviews_router = nested_routers.NestedDefaultRouter(
    router,
    '',
    lookup='product'
)
product_reviews_router.register(
    'reviews',
    ProductReviewViewSet,
    basename='product-review'
)

urlpatterns = [
    path('', include(router.urls)),
    path('', include(product_reviews_router.urls)),
    path('featured/', FeaturedProductsView.as_view(), name='featured-products'),
]

# Generated endpoints:
# GET/POST     /products/
# GET/PUT/DEL  /products/{pk}/
# POST         /products/{pk}/activate/
# GET/POST     /products/{product_pk}/reviews/
# GET/PUT/DEL  /products/{product_pk}/reviews/{pk}/
# GET/POST     /products/categories/
# GET/PUT/DEL  /products/categories/{pk}/
# GET          /products/featured/
```

## Best Practices

1. **Use app_name** for URL namespacing
2. **Consistent basename** - matches model name in lowercase
3. **Use nested routers** for related resources
4. **Keep nesting shallow** - max 2-3 levels
5. **Version your API** - from the start
6. **Document endpoints** - in ViewSet docstrings
7. **Use url_path** for custom action URLs with hyphens
