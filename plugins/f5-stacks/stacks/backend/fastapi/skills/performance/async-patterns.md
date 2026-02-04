---
name: fastapi-async-patterns
description: Async programming patterns for FastAPI performance
applies_to: fastapi
category: skill
---

# Async Patterns for FastAPI

## Concurrent Operations

### Gathering Multiple Results

```python
# app/services/dashboard.py
import asyncio
from typing import Any

from app.repositories.user import UserRepository
from app.repositories.order import OrderRepository
from app.repositories.product import ProductRepository


class DashboardService:
    """Service demonstrating concurrent data fetching."""

    def __init__(
        self,
        user_repo: UserRepository,
        order_repo: OrderRepository,
        product_repo: ProductRepository,
    ):
        self._user_repo = user_repo
        self._order_repo = order_repo
        self._product_repo = product_repo

    async def get_dashboard_data(self, user_id: UUID) -> dict[str, Any]:
        """Fetch all dashboard data concurrently."""
        # Run all queries in parallel
        user, orders, products, stats = await asyncio.gather(
            self._user_repo.get_by_id(user_id),
            self._order_repo.get_recent_by_user(user_id, limit=5),
            self._product_repo.get_featured(limit=10),
            self._get_user_stats(user_id),
        )

        return {
            "user": user,
            "recent_orders": orders,
            "featured_products": products,
            "stats": stats,
        }

    async def _get_user_stats(self, user_id: UUID) -> dict[str, int]:
        """Get aggregated user statistics."""
        total_orders, total_spent, total_items = await asyncio.gather(
            self._order_repo.count_by_user(user_id),
            self._order_repo.sum_total_by_user(user_id),
            self._order_repo.count_items_by_user(user_id),
        )

        return {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "total_items": total_items,
        }
```

### Handling Partial Failures

```python
# app/services/notification.py
import asyncio
from typing import Any


async def send_notifications_safe(
    user_ids: list[UUID],
    message: str,
) -> dict[str, list]:
    """Send notifications with graceful error handling."""
    tasks = [
        send_notification_to_user(user_id, message)
        for user_id in user_ids
    ]

    # gather with return_exceptions=True to handle partial failures
    results = await asyncio.gather(*tasks, return_exceptions=True)

    succeeded = []
    failed = []

    for user_id, result in zip(user_ids, results):
        if isinstance(result, Exception):
            failed.append({"user_id": user_id, "error": str(result)})
        else:
            succeeded.append(user_id)

    return {"succeeded": succeeded, "failed": failed}


async def send_notification_to_user(user_id: UUID, message: str) -> bool:
    """Send notification to a single user."""
    # Implementation
    pass
```

### Semaphore for Rate Limiting

```python
# app/services/external.py
import asyncio
from typing import Any

# Limit concurrent external API calls
_external_api_semaphore = asyncio.Semaphore(10)


async def call_external_api(endpoint: str, data: dict) -> Any:
    """Call external API with concurrency limit."""
    async with _external_api_semaphore:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                endpoint,
                json=data,
                timeout=30.0,
            )
            return response.json()


async def process_batch_with_limit(
    items: list[dict],
    max_concurrent: int = 5,
) -> list[Any]:
    """Process items with concurrency limit."""
    semaphore = asyncio.Semaphore(max_concurrent)

    async def process_with_limit(item: dict) -> Any:
        async with semaphore:
            return await process_item(item)

    return await asyncio.gather(
        *[process_with_limit(item) for item in items]
    )
```

## Timeouts and Cancellation

### Timeout Handling

```python
# app/services/search.py
import asyncio
from app.core.exceptions import ExternalServiceError


async def search_with_timeout(
    query: str,
    timeout_seconds: float = 5.0,
) -> list[dict]:
    """Search with timeout protection."""
    try:
        return await asyncio.wait_for(
            perform_search(query),
            timeout=timeout_seconds,
        )
    except asyncio.TimeoutError:
        raise ExternalServiceError(
            service="search",
            message=f"Search timed out after {timeout_seconds}s",
        )


async def search_multiple_sources(
    query: str,
    timeout_seconds: float = 10.0,
) -> dict[str, list]:
    """Search multiple sources with individual timeouts."""
    async def search_source(source: str, query: str) -> tuple[str, list]:
        try:
            results = await asyncio.wait_for(
                search_in_source(source, query),
                timeout=timeout_seconds / 2,  # Per-source timeout
            )
            return source, results
        except asyncio.TimeoutError:
            return source, []  # Return empty on timeout

    tasks = [
        search_source(source, query)
        for source in ["database", "elasticsearch", "external_api"]
    ]

    results = await asyncio.gather(*tasks)
    return dict(results)
```

### Graceful Cancellation

```python
# app/services/long_running.py
import asyncio
from typing import AsyncIterator


async def process_with_cancellation(
    items: list[dict],
) -> AsyncIterator[dict]:
    """Process items with cancellation support."""
    for item in items:
        # Check for cancellation
        if asyncio.current_task().cancelled():
            break

        try:
            result = await process_item(item)
            yield result
        except asyncio.CancelledError:
            # Clean up and re-raise
            await cleanup_resources()
            raise


async def run_with_graceful_shutdown(
    coro,
    shutdown_event: asyncio.Event,
):
    """Run coroutine with graceful shutdown support."""
    task = asyncio.create_task(coro)
    shutdown_task = asyncio.create_task(shutdown_event.wait())

    done, pending = await asyncio.wait(
        [task, shutdown_task],
        return_when=asyncio.FIRST_COMPLETED,
    )

    for t in pending:
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass

    if task in done:
        return task.result()
    else:
        raise asyncio.CancelledError("Shutdown requested")
```

## Async Iterators and Generators

### Streaming Responses

```python
# app/api/v1/endpoints/export.py
from typing import AsyncIterator
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()


async def generate_csv_rows(
    query_params: dict,
) -> AsyncIterator[str]:
    """Generate CSV rows asynchronously."""
    # Header
    yield "id,name,email,created_at\n"

    # Stream data in batches
    offset = 0
    batch_size = 1000

    while True:
        users = await get_users_batch(offset, batch_size, query_params)
        if not users:
            break

        for user in users:
            yield f"{user.id},{user.name},{user.email},{user.created_at}\n"

        offset += batch_size

        # Yield control to event loop
        await asyncio.sleep(0)


@router.get("/export/users")
async def export_users():
    """Export users as streaming CSV."""
    return StreamingResponse(
        generate_csv_rows({}),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=users.csv"
        },
    )
```

### Async Context Manager Pattern

```python
# app/core/locks.py
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator


class DistributedLock:
    """Async distributed lock using Redis."""

    def __init__(self, redis, name: str, timeout: float = 10.0):
        self.redis = redis
        self.name = f"lock:{name}"
        self.timeout = timeout

    async def acquire(self) -> bool:
        """Try to acquire lock."""
        return await self.redis.set(
            self.name,
            "1",
            ex=int(self.timeout),
            nx=True,
        )

    async def release(self) -> None:
        """Release lock."""
        await self.redis.delete(self.name)

    async def __aenter__(self) -> "DistributedLock":
        if not await self.acquire():
            raise RuntimeError(f"Could not acquire lock: {self.name}")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.release()


@asynccontextmanager
async def timed_operation(name: str) -> AsyncIterator[None]:
    """Context manager for timing operations."""
    import time
    import logging

    logger = logging.getLogger(__name__)
    start = time.perf_counter()

    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info(f"{name} completed in {elapsed:.3f}s")


# Usage
async def process_order(order_id: UUID):
    async with timed_operation("process_order"):
        async with DistributedLock(redis, f"order:{order_id}"):
            await do_processing(order_id)
```

## Async Middleware

```python
# app/middleware/timing.py
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TimingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request timing."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()

        response = await call_next(request)

        process_time = time.perf_counter() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}"

        logger.info(
            f"{request.method} {request.url.path} "
            f"completed in {process_time:.4f}s"
        )

        return response


class AsyncResourceMiddleware(BaseHTTPMiddleware):
    """Middleware for async resource management."""

    async def dispatch(self, request: Request, call_next):
        # Acquire resources
        request.state.db = await get_db_session()
        request.state.cache = await get_cache_client()

        try:
            response = await call_next(request)
            return response
        finally:
            # Release resources
            await request.state.db.close()
            await request.state.cache.close()
```

## Connection Pooling

### Database Connection Pool

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings


def create_engine():
    """Create engine with optimized connection pooling."""
    return create_async_engine(
        settings.DATABASE_URL,
        poolclass=AsyncAdaptedQueuePool,
        pool_size=20,  # Base connections
        max_overflow=10,  # Extra connections under load
        pool_timeout=30,  # Wait time for connection
        pool_recycle=1800,  # Recycle connections every 30 min
        pool_pre_ping=True,  # Check connections before use
        echo=settings.DEBUG,
    )


engine = create_engine()
async_session = async_sessionmaker(
    engine,
    expire_on_commit=False,
    autoflush=False,
)
```

### HTTP Client Pool

```python
# app/core/http_client.py
import httpx
from contextlib import asynccontextmanager
from typing import AsyncIterator


class HTTPClientPool:
    """Managed HTTP client pool."""

    _client: httpx.AsyncClient | None = None

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if cls._client is None:
            cls._client = httpx.AsyncClient(
                timeout=30.0,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=100,
                    keepalive_expiry=30.0,
                ),
            )
        return cls._client

    @classmethod
    async def close(cls) -> None:
        """Close HTTP client."""
        if cls._client is not None:
            await cls._client.aclose()
            cls._client = None


# Lifespan management
@asynccontextmanager
async def lifespan(app) -> AsyncIterator[None]:
    # Startup
    yield
    # Shutdown
    await HTTPClientPool.close()
```

## Event-Driven Patterns

### Async Event Bus

```python
# app/core/events.py
import asyncio
from typing import Callable, Any
from collections import defaultdict


class AsyncEventBus:
    """Simple async event bus."""

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event."""
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from an event."""
        self._handlers[event_type].remove(handler)

    async def publish(self, event_type: str, data: Any) -> None:
        """Publish event to all handlers."""
        handlers = self._handlers.get(event_type, [])
        if handlers:
            await asyncio.gather(
                *[handler(data) for handler in handlers],
                return_exceptions=True,
            )


# Global event bus
event_bus = AsyncEventBus()


# Usage
async def on_user_created(user_data: dict):
    await send_welcome_email(user_data["email"])
    await create_default_settings(user_data["id"])


event_bus.subscribe("user.created", on_user_created)


# In service
async def create_user(data: UserCreate) -> User:
    user = await user_repo.create(data)
    await event_bus.publish("user.created", user.model_dump())
    return user
```

## Best Practices

1. **Use `asyncio.gather`** for concurrent independent operations
2. **Handle partial failures** with `return_exceptions=True`
3. **Limit concurrency** with semaphores for external APIs
4. **Always set timeouts** on external calls
5. **Support cancellation** in long-running operations
6. **Use connection pools** for databases and HTTP clients
7. **Stream large responses** instead of loading into memory
8. **Avoid blocking calls** - use `run_in_executor` for CPU-bound tasks
