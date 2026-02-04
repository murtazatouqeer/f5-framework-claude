---
name: fastapi-caching
description: Caching strategies and patterns for FastAPI
applies_to: fastapi
category: skill
---

# Caching in FastAPI

## Redis Setup

### Connection Configuration

```python
# app/core/redis.py
from redis import asyncio as aioredis
from app.core.config import settings


class RedisClient:
    """Redis client singleton."""

    _pool: aioredis.Redis | None = None

    @classmethod
    async def get_client(cls) -> aioredis.Redis:
        """Get or create Redis client."""
        if cls._pool is None:
            cls._pool = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,
            )
        return cls._pool

    @classmethod
    async def close(cls) -> None:
        """Close Redis connection."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None


# Dependency
async def get_redis() -> aioredis.Redis:
    """FastAPI dependency for Redis."""
    return await RedisClient.get_client()


Redis = Annotated[aioredis.Redis, Depends(get_redis)]
```

### Lifespan Integration

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.redis import RedisClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await RedisClient.get_client()
    yield
    # Shutdown
    await RedisClient.close()


app = FastAPI(lifespan=lifespan)
```

## Caching Patterns

### Simple Cache Decorator

```python
# app/core/cache.py
import json
import functools
from typing import Callable, Any, Optional
from datetime import timedelta

from app.core.redis import RedisClient


def cache(
    prefix: str,
    expire: timedelta = timedelta(minutes=5),
    key_builder: Optional[Callable[..., str]] = None,
):
    """Cache decorator for async functions."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            redis = await RedisClient.get_client()

            # Build cache key
            if key_builder:
                cache_key = f"{prefix}:{key_builder(*args, **kwargs)}"
            else:
                # Default key from args
                key_parts = [str(a) for a in args[1:]]  # Skip self
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{prefix}:{':'.join(key_parts)}"

            # Try to get from cache
            cached = await redis.get(cache_key)
            if cached is not None:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await redis.set(
                cache_key,
                json.dumps(result, default=str),
                ex=int(expire.total_seconds()),
            )

            return result

        return wrapper

    return decorator


# Usage
class ProductService:
    @cache(prefix="product", expire=timedelta(minutes=10))
    async def get_by_id(self, product_id: UUID) -> dict:
        product = await self._repo.get_by_id(product_id)
        return product.model_dump() if product else None

    @cache(
        prefix="products:featured",
        expire=timedelta(hours=1),
        key_builder=lambda self, limit: f"limit:{limit}",
    )
    async def get_featured(self, limit: int = 10) -> list[dict]:
        products = await self._repo.get_featured(limit)
        return [p.model_dump() for p in products]
```

### Cache Aside Pattern

```python
# app/services/product.py
from typing import Optional
from uuid import UUID

from app.core.redis import RedisClient
from app.repositories.product import ProductRepository
from app.schemas.product import ProductResponse


class ProductService:
    """Service with cache-aside pattern."""

    CACHE_PREFIX = "product"
    CACHE_TTL = 3600  # 1 hour

    def __init__(self, repository: ProductRepository):
        self._repo = repository

    async def get_by_id(self, product_id: UUID) -> Optional[ProductResponse]:
        """Get product with cache-aside."""
        redis = await RedisClient.get_client()
        cache_key = f"{self.CACHE_PREFIX}:{product_id}"

        # 1. Try cache first
        cached = await redis.get(cache_key)
        if cached:
            return ProductResponse.model_validate_json(cached)

        # 2. Fetch from database
        product = await self._repo.get_by_id(product_id)
        if not product:
            return None

        # 3. Update cache
        response = ProductResponse.model_validate(product)
        await redis.set(
            cache_key,
            response.model_dump_json(),
            ex=self.CACHE_TTL,
        )

        return response

    async def update(self, product_id: UUID, data: dict) -> ProductResponse:
        """Update product and invalidate cache."""
        redis = await RedisClient.get_client()

        # Update in database
        product = await self._repo.update(product_id, data)

        # Invalidate cache
        cache_key = f"{self.CACHE_PREFIX}:{product_id}"
        await redis.delete(cache_key)

        return ProductResponse.model_validate(product)

    async def delete(self, product_id: UUID) -> None:
        """Delete product and invalidate cache."""
        redis = await RedisClient.get_client()

        await self._repo.delete(product_id)

        # Invalidate cache
        cache_key = f"{self.CACHE_PREFIX}:{product_id}"
        await redis.delete(cache_key)
```

### Cache Stampede Prevention

```python
# app/core/cache.py
import asyncio
import hashlib
from typing import Callable, Any, TypeVar
from datetime import timedelta

from app.core.redis import RedisClient

T = TypeVar("T")


async def get_with_lock(
    cache_key: str,
    fetch_func: Callable[[], Any],
    expire: timedelta = timedelta(minutes=5),
    lock_timeout: float = 10.0,
) -> T:
    """Get value with distributed lock to prevent stampede."""
    redis = await RedisClient.get_client()

    # Try to get from cache
    cached = await redis.get(cache_key)
    if cached is not None:
        return json.loads(cached)

    # Try to acquire lock
    lock_key = f"{cache_key}:lock"
    lock_acquired = await redis.set(
        lock_key,
        "1",
        ex=int(lock_timeout),
        nx=True,
    )

    if lock_acquired:
        try:
            # Fetch fresh data
            result = await fetch_func()

            # Store in cache
            await redis.set(
                cache_key,
                json.dumps(result, default=str),
                ex=int(expire.total_seconds()),
            )

            return result
        finally:
            # Release lock
            await redis.delete(lock_key)
    else:
        # Wait for other process to populate cache
        for _ in range(int(lock_timeout * 10)):
            await asyncio.sleep(0.1)
            cached = await redis.get(cache_key)
            if cached is not None:
                return json.loads(cached)

        # Fallback: fetch ourselves
        return await fetch_func()


# Usage
async def get_popular_products():
    return await get_with_lock(
        cache_key="products:popular",
        fetch_func=lambda: repo.get_popular_products(),
        expire=timedelta(hours=1),
    )
```

### Write-Through Cache

```python
# app/services/user_settings.py
from typing import Any


class UserSettingsService:
    """Service with write-through cache pattern."""

    CACHE_PREFIX = "user:settings"
    CACHE_TTL = 86400  # 24 hours

    async def get_settings(self, user_id: UUID) -> dict:
        """Get user settings (cache-aside)."""
        redis = await RedisClient.get_client()
        cache_key = f"{self.CACHE_PREFIX}:{user_id}"

        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        settings = await self._repo.get_settings(user_id)
        if settings:
            await redis.set(cache_key, json.dumps(settings), ex=self.CACHE_TTL)

        return settings or {}

    async def update_settings(self, user_id: UUID, data: dict) -> dict:
        """Update settings with write-through."""
        redis = await RedisClient.get_client()
        cache_key = f"{self.CACHE_PREFIX}:{user_id}"

        # Write to database
        settings = await self._repo.update_settings(user_id, data)

        # Write to cache (write-through)
        await redis.set(
            cache_key,
            json.dumps(settings),
            ex=self.CACHE_TTL,
        )

        return settings
```

## Response Caching

### ETag and Conditional Requests

```python
# app/api/deps.py
import hashlib
from fastapi import Request, Response, HTTPException, status


def generate_etag(content: str) -> str:
    """Generate ETag from content."""
    return hashlib.md5(content.encode()).hexdigest()


async def check_etag(
    request: Request,
    response: Response,
    content: str,
) -> str:
    """Check ETag and set response headers."""
    etag = generate_etag(content)
    response.headers["ETag"] = f'"{etag}"'

    # Check If-None-Match header
    if_none_match = request.headers.get("If-None-Match")
    if if_none_match and if_none_match.strip('"') == etag:
        raise HTTPException(status_code=status.HTTP_304_NOT_MODIFIED)

    return content


# Usage in endpoint
@router.get("/products/{id}")
async def get_product(
    id: UUID,
    request: Request,
    response: Response,
    service: ProductServiceDep,
):
    product = await service.get_by_id(id)
    content = product.model_dump_json()

    await check_etag(request, response, content)

    return product
```

### Cache-Control Headers

```python
# app/middleware/cache.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Add Cache-Control headers based on route."""

    CACHE_RULES = {
        "/api/v1/products": "public, max-age=300",  # 5 min
        "/api/v1/categories": "public, max-age=3600",  # 1 hour
        "/api/v1/users/me": "private, no-store",
        "/static": "public, max-age=86400",  # 1 day
    }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Set cache control based on path
        for path, cache_control in self.CACHE_RULES.items():
            if request.url.path.startswith(path):
                response.headers["Cache-Control"] = cache_control
                break
        else:
            # Default: no caching
            response.headers["Cache-Control"] = "no-cache"

        return response
```

## List Caching

### Paginated Results Cache

```python
# app/services/product.py
from typing import Any


class ProductService:
    """Service with list caching."""

    LIST_CACHE_PREFIX = "products:list"
    LIST_CACHE_TTL = 300  # 5 minutes

    async def list_products(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: dict | None = None,
    ) -> dict[str, Any]:
        """List products with cached results."""
        redis = await RedisClient.get_client()

        # Build cache key from parameters
        filter_hash = hashlib.md5(
            json.dumps(filters or {}, sort_keys=True).encode()
        ).hexdigest()[:8]
        cache_key = f"{self.LIST_CACHE_PREFIX}:{page}:{page_size}:{filter_hash}"

        # Try cache
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)

        # Fetch from database
        products = await self._repo.list(
            offset=(page - 1) * page_size,
            limit=page_size,
            filters=filters,
        )
        total = await self._repo.count(filters=filters)

        result = {
            "items": [p.model_dump() for p in products],
            "total": total,
            "page": page,
            "page_size": page_size,
        }

        # Cache result
        await redis.set(cache_key, json.dumps(result), ex=self.LIST_CACHE_TTL)

        return result

    async def invalidate_list_cache(self) -> None:
        """Invalidate all list caches."""
        redis = await RedisClient.get_client()

        # Delete all list cache keys
        cursor = 0
        while True:
            cursor, keys = await redis.scan(
                cursor,
                match=f"{self.LIST_CACHE_PREFIX}:*",
                count=100,
            )
            if keys:
                await redis.delete(*keys)
            if cursor == 0:
                break
```

## In-Memory Caching

### LRU Cache for Expensive Computations

```python
# app/core/local_cache.py
from functools import lru_cache
from cachetools import TTLCache
import asyncio


# Sync LRU cache for config/constants
@lru_cache(maxsize=100)
def get_tax_rate(country_code: str) -> float:
    """Get tax rate for country (cached in memory)."""
    TAX_RATES = {
        "US": 0.0,
        "UK": 0.20,
        "DE": 0.19,
        "JP": 0.10,
    }
    return TAX_RATES.get(country_code, 0.0)


# Async-compatible TTL cache
class AsyncTTLCache:
    """TTL cache for async functions."""

    def __init__(self, maxsize: int = 100, ttl: float = 300):
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._cache[key] = value

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._cache.pop(key, None)


# Usage
_exchange_rate_cache = AsyncTTLCache(maxsize=50, ttl=3600)


async def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate with local caching."""
    cache_key = f"{from_currency}:{to_currency}"

    # Check local cache
    cached = await _exchange_rate_cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch from external API
    rate = await fetch_exchange_rate(from_currency, to_currency)

    # Store in local cache
    await _exchange_rate_cache.set(cache_key, rate)

    return rate
```

## Cache Invalidation Strategies

### Event-Based Invalidation

```python
# app/core/cache_invalidation.py
from enum import Enum
from typing import Callable


class CacheEvent(str, Enum):
    PRODUCT_CREATED = "product.created"
    PRODUCT_UPDATED = "product.updated"
    PRODUCT_DELETED = "product.deleted"
    CATEGORY_UPDATED = "category.updated"


class CacheInvalidator:
    """Centralized cache invalidation."""

    def __init__(self):
        self._handlers: dict[CacheEvent, list[Callable]] = {}

    def register(self, event: CacheEvent, handler: Callable) -> None:
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    async def trigger(self, event: CacheEvent, data: dict) -> None:
        handlers = self._handlers.get(event, [])
        for handler in handlers:
            await handler(data)


# Initialize
cache_invalidator = CacheInvalidator()


# Register handlers
async def invalidate_product_cache(data: dict):
    redis = await RedisClient.get_client()
    product_id = data.get("product_id")

    # Invalidate specific product
    await redis.delete(f"product:{product_id}")

    # Invalidate product lists
    cursor = 0
    while True:
        cursor, keys = await redis.scan(cursor, match="products:list:*")
        if keys:
            await redis.delete(*keys)
        if cursor == 0:
            break


cache_invalidator.register(CacheEvent.PRODUCT_UPDATED, invalidate_product_cache)
cache_invalidator.register(CacheEvent.PRODUCT_DELETED, invalidate_product_cache)


# Usage in service
async def update_product(product_id: UUID, data: dict):
    product = await repo.update(product_id, data)

    await cache_invalidator.trigger(
        CacheEvent.PRODUCT_UPDATED,
        {"product_id": product_id},
    )

    return product
```

## Best Practices

1. **Choose appropriate TTL** based on data freshness requirements
2. **Use cache-aside** for read-heavy workloads
3. **Implement cache stampede prevention** for expensive operations
4. **Invalidate caches explicitly** when data changes
5. **Use local cache** for frequently accessed, rarely changing data
6. **Monitor cache hit rates** and adjust strategies
7. **Set appropriate max memory** for Redis
8. **Use consistent key naming** conventions
