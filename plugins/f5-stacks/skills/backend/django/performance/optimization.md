# Django Performance Optimization Skill

## Overview

Performance optimization techniques for Django applications.

## Database Optimization

### N+1 Query Prevention

```python
# Bad: N+1 queries
orders = Order.objects.all()
for order in orders:
    print(order.user.name)  # Query per order

# Good: Single query with JOIN
orders = Order.objects.select_related('user').all()

# Good: Prefetch for reverse relations
orders = Order.objects.prefetch_related('items').all()

# Good: Complex prefetch
from django.db.models import Prefetch

orders = Order.objects.prefetch_related(
    Prefetch(
        'items',
        queryset=OrderItem.objects.select_related('product')
    )
).all()
```

### QuerySet Optimization

```python
# Use only() for specific fields
products = Product.objects.only('id', 'name', 'price')

# Use defer() to exclude heavy fields
products = Product.objects.defer('description', 'metadata')

# Use values() for dict output
product_names = Product.objects.values('id', 'name')

# Use values_list() for tuples
product_ids = Product.objects.values_list('id', flat=True)

# Use exists() instead of count() for boolean check
if Product.objects.filter(status='active').exists():
    pass

# Use update() for bulk updates
Product.objects.filter(category='electronics').update(
    discount_percent=F('discount_percent') + 10
)

# Use iterator() for large querysets
for product in Product.objects.iterator(chunk_size=1000):
    process(product)
```

### Indexing

```python
class Product(models.Model):
    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=50, unique=True)  # Creates index
    status = models.CharField(max_length=20, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            # Composite index
            models.Index(
                fields=['status', 'created_at'],
                name='idx_status_created'
            ),
            # Partial index (PostgreSQL)
            models.Index(
                fields=['price'],
                name='idx_active_price',
                condition=Q(status='active')
            ),
        ]
```

## View Optimization

### Pagination

```python
from rest_framework.pagination import CursorPagination


class OptimizedPagination(CursorPagination):
    """Cursor pagination for large datasets."""

    page_size = 50
    ordering = '-created_at'
    cursor_query_param = 'cursor'

    # More efficient than offset pagination
    # Doesn't require COUNT(*)
```

### Throttling

```python
from rest_framework.throttling import UserRateThrottle


class BurstThrottle(UserRateThrottle):
    rate = '60/min'


class SustainedThrottle(UserRateThrottle):
    rate = '1000/day'


class ProductViewSet(viewsets.ModelViewSet):
    throttle_classes = [BurstThrottle, SustainedThrottle]
```

### Conditional Requests

```python
from django.utils.decorators import method_decorator
from django.views.decorators.http import condition
from django.utils import timezone


def get_last_modified(request, pk):
    """Get last modified time for conditional GET."""
    try:
        return Product.objects.get(pk=pk).updated_at
    except Product.DoesNotExist:
        return None


def get_etag(request, pk):
    """Generate ETag for caching."""
    try:
        product = Product.objects.get(pk=pk)
        return f'"{product.pk}-{product.updated_at.timestamp()}"'
    except Product.DoesNotExist:
        return None


@method_decorator(condition(etag_func=get_etag, last_modified_func=get_last_modified), name='retrieve')
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
```

## Caching

### View Caching

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


class ProductViewSet(viewsets.ModelViewSet):
    @method_decorator(cache_page(60 * 15))  # 15 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

### Low-Level Caching

```python
from django.core.cache import cache


class ProductService:
    """Service with caching."""

    CACHE_TTL = 60 * 15  # 15 minutes

    def get_product(self, product_id):
        """Get product with caching."""
        cache_key = f'product:{product_id}'

        product = cache.get(cache_key)
        if product is None:
            product = Product.objects.get(pk=product_id)
            cache.set(cache_key, product, self.CACHE_TTL)

        return product

    def get_popular_products(self):
        """Get popular products with caching."""
        cache_key = 'popular_products'

        products = cache.get(cache_key)
        if products is None:
            products = list(
                Product.objects.filter(status='active')
                .order_by('-sales_count')[:10]
            )
            cache.set(cache_key, products, self.CACHE_TTL)

        return products

    def invalidate_product(self, product_id):
        """Invalidate product cache."""
        cache.delete(f'product:{product_id}')
        cache.delete('popular_products')
```

### Cache Decorators

```python
from functools import wraps
from django.core.cache import cache


def cached(ttl=300, key_prefix=''):
    """Decorator for caching function results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f'{k}={v}' for k, v in sorted(kwargs.items()))
            cache_key = ':'.join(key_parts)

            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# Usage
@cached(ttl=600, key_prefix='stats')
def get_sales_stats(category_id):
    """Get sales stats (cached for 10 minutes)."""
    return Order.objects.filter(
        items__product__category_id=category_id
    ).aggregate(
        total=Sum('total'),
        count=Count('id')
    )
```

## Async Operations

### Celery Tasks

```python
from celery import shared_task


@shared_task
def send_order_confirmation(order_id):
    """Send confirmation email asynchronously."""
    order = Order.objects.get(pk=order_id)
    send_email(order.user.email, 'Order Confirmation', ...)


# In view
class OrderViewSet(viewsets.ModelViewSet):
    def perform_create(self, serializer):
        order = serializer.save()
        # Non-blocking email send
        send_order_confirmation.delay(str(order.id))
```

### Database Connection Pooling

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'mydb',
        'CONN_MAX_AGE': 60,  # Connection pooling
        'CONN_HEALTH_CHECKS': True,  # Django 4.1+
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}
```

## Monitoring

### Query Logging

```python
# settings/development.py
LOGGING = {
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Shows all SQL queries
        },
    },
}
```

### Debug Toolbar

```python
# settings/development.py
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
INTERNAL_IPS = ['127.0.0.1']
```

### Query Count Assertion

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection


def test_list_query_count(self, client):
    """Ensure list doesn't have N+1."""
    ProductFactory.create_batch(50)

    with CaptureQueriesContext(connection) as context:
        response = client.get('/api/products/')

    assert response.status_code == 200
    assert len(context) <= 3, f"Too many queries: {len(context)}"
```

## Best Practices

1. **Profile before optimizing** - Measure first
2. **Use select_related/prefetch_related** - Prevent N+1
3. **Index frequently queried fields** - Check query plans
4. **Use pagination** - Cursor for large datasets
5. **Cache expensive queries** - With invalidation strategy
6. **Async heavy operations** - Use Celery for emails, reports
7. **Monitor in production** - APM tools, slow query logs
8. **Connection pooling** - CONN_MAX_AGE setting
