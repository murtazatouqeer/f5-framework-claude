# Django Caching Skill

## Overview

Comprehensive caching strategies for Django applications with Redis.

## Cache Configuration

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
            },
        },
        'KEY_PREFIX': 'myapp',
        'TIMEOUT': 300,  # 5 minutes default
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
        'KEY_PREFIX': 'session',
        'TIMEOUT': 86400,  # 24 hours
    },
}

# Use Redis for sessions
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
```

## Cache Patterns

### Simple Get/Set

```python
from django.core.cache import cache


def get_user_profile(user_id):
    """Get user profile with caching."""
    cache_key = f'user_profile:{user_id}'

    # Try cache first
    profile = cache.get(cache_key)

    if profile is None:
        # Cache miss - fetch from database
        profile = UserProfile.objects.select_related('user').get(user_id=user_id)
        # Store in cache for 15 minutes
        cache.set(cache_key, profile, timeout=900)

    return profile


def update_user_profile(user_id, data):
    """Update profile and invalidate cache."""
    profile = UserProfile.objects.get(user_id=user_id)
    for key, value in data.items():
        setattr(profile, key, value)
    profile.save()

    # Invalidate cache
    cache.delete(f'user_profile:{user_id}')

    return profile
```

### Get or Set Pattern

```python
def get_popular_products():
    """Get popular products using get_or_set."""
    return cache.get_or_set(
        'popular_products',
        lambda: list(
            Product.objects.filter(status='active')
            .order_by('-sales_count')[:20]
            .values('id', 'name', 'price', 'image_url')
        ),
        timeout=600  # 10 minutes
    )
```

### Cache Versioning

```python
class ProductCache:
    """Product cache with versioning."""

    VERSION_KEY = 'product_cache_version'

    @classmethod
    def get_version(cls):
        """Get current cache version."""
        version = cache.get(cls.VERSION_KEY)
        if version is None:
            version = 1
            cache.set(cls.VERSION_KEY, version, timeout=None)
        return version

    @classmethod
    def invalidate_all(cls):
        """Invalidate all product caches by incrementing version."""
        cache.incr(cls.VERSION_KEY)

    @classmethod
    def get_key(cls, product_id):
        """Get versioned cache key."""
        version = cls.get_version()
        return f'product:v{version}:{product_id}'

    @classmethod
    def get(cls, product_id):
        """Get product from cache."""
        return cache.get(cls.get_key(product_id))

    @classmethod
    def set(cls, product_id, data, timeout=300):
        """Set product in cache."""
        cache.set(cls.get_key(product_id), data, timeout)
```

### Cache Tags (using django-redis)

```python
from django_redis import get_redis_connection


class TaggedCache:
    """Cache with tag-based invalidation."""

    @staticmethod
    def set_with_tags(key, value, tags, timeout=300):
        """Set value with tags for group invalidation."""
        cache.set(key, value, timeout)

        # Store key under each tag
        redis = get_redis_connection('default')
        for tag in tags:
            redis.sadd(f'tag:{tag}', key)
            redis.expire(f'tag:{tag}', timeout)

    @staticmethod
    def invalidate_tag(tag):
        """Invalidate all keys with a specific tag."""
        redis = get_redis_connection('default')
        keys = redis.smembers(f'tag:{tag}')

        if keys:
            cache.delete_many([k.decode() for k in keys])
            redis.delete(f'tag:{tag}')


# Usage
TaggedCache.set_with_tags(
    f'product:{product.id}',
    product_data,
    tags=['products', f'category:{product.category_id}']
)

# Invalidate all products in a category
TaggedCache.invalidate_tag(f'category:{category_id}')
```

## View Caching

### Per-View Cache

```python
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


class ProductViewSet(viewsets.ModelViewSet):
    @method_decorator(cache_page(60 * 5))  # 5 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


# For function-based views
@cache_page(60 * 15)
def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/list.html', {'products': products})
```

### Vary Cache by User

```python
from django.views.decorators.vary import vary_on_cookie


@cache_page(60 * 15)
@vary_on_cookie
def user_dashboard(request):
    """Cache varies by user cookie."""
    return render(request, 'dashboard.html')


# Or vary by header
from django.views.decorators.vary import vary_on_headers


@cache_page(60 * 5)
@vary_on_headers('Authorization')
def api_data(request):
    """Cache varies by auth header."""
    pass
```

### Conditional Caching

```python
def should_cache(request, response):
    """Determine if response should be cached."""
    # Don't cache errors
    if response.status_code >= 400:
        return False
    # Don't cache POST responses
    if request.method != 'GET':
        return False
    # Don't cache authenticated users
    if request.user.is_authenticated:
        return False
    return True


from django.views.decorators.cache import cache_page

@cache_page(60 * 15, cache='default', key_prefix='public')
def public_view(request):
    """Only cache for anonymous users."""
    pass
```

## Query Result Caching

```python
from django.core.cache import cache


class CachedQuerySet:
    """Mixin for cached querysets."""

    @classmethod
    def cached_all(cls, timeout=300):
        """Get all records with caching."""
        cache_key = f'{cls.__name__}:all'
        result = cache.get(cache_key)

        if result is None:
            result = list(cls.objects.all())
            cache.set(cache_key, result, timeout)

        return result

    @classmethod
    def cached_get(cls, pk, timeout=300):
        """Get single record with caching."""
        cache_key = f'{cls.__name__}:{pk}'
        result = cache.get(cache_key)

        if result is None:
            result = cls.objects.get(pk=pk)
            cache.set(cache_key, result, timeout)

        return result

    def save(self, *args, **kwargs):
        """Invalidate cache on save."""
        super().save(*args, **kwargs)
        cache.delete(f'{self.__class__.__name__}:{self.pk}')
        cache.delete(f'{self.__class__.__name__}:all')
```

## Signal-Based Invalidation

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache


@receiver([post_save, post_delete], sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalidate product cache on save/delete."""
    # Invalidate specific product
    cache.delete(f'product:{instance.pk}')

    # Invalidate category cache
    cache.delete(f'category_products:{instance.category_id}')

    # Invalidate popular products
    cache.delete('popular_products')

    # Invalidate search cache
    cache.delete_pattern('search:*')  # Requires django-redis


@receiver(post_save, sender=Order)
def invalidate_stats_cache(sender, instance, **kwargs):
    """Invalidate stats cache on new order."""
    cache.delete_pattern('stats:*')
```

## Memoization

```python
from functools import lru_cache


class ProductService:
    """Service with memoization."""

    @staticmethod
    @lru_cache(maxsize=1000)
    def calculate_discount(price, discount_percent):
        """Memoized discount calculation."""
        return price * (1 - discount_percent / 100)

    @staticmethod
    def clear_discount_cache():
        """Clear memoization cache."""
        ProductService.calculate_discount.cache_clear()
```

## Best Practices

1. **Use cache keys wisely** - Include version, type, ID
2. **Set appropriate TTLs** - Balance freshness and performance
3. **Invalidate on write** - Keep cache consistent
4. **Use cache tags** - For group invalidation
5. **Monitor cache hit rate** - Optimize based on metrics
6. **Handle cache failures** - Graceful degradation
7. **Don't cache user-specific data globally** - Use vary decorators
8. **Serialize carefully** - JSON for cross-language, pickle for Python-only
