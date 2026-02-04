---
name: fastapi-background-tasks
description: Background task patterns for FastAPI
applies_to: fastapi
category: skill
---

# Background Tasks in FastAPI

## FastAPI BackgroundTasks

### Basic Usage

```python
# app/api/v1/endpoints/users.py
from fastapi import APIRouter, BackgroundTasks, status

from app.schemas.user import UserCreate, UserResponse
from app.services.user import UserService
from app.services.email import send_welcome_email

router = APIRouter()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    background_tasks: BackgroundTasks,
    service: UserServiceDep,
):
    """Create user and send welcome email in background."""
    user = await service.create(data)

    # Add background task
    background_tasks.add_task(
        send_welcome_email,
        user.email,
        user.name,
    )

    return user


async def send_welcome_email(email: str, name: str) -> None:
    """Send welcome email (runs in background)."""
    await email_service.send(
        to=email,
        subject="Welcome!",
        template="welcome",
        context={"name": name},
    )
```

### Multiple Background Tasks

```python
# app/api/v1/endpoints/orders.py
from fastapi import BackgroundTasks


@router.post("/orders/", response_model=OrderResponse)
async def create_order(
    data: OrderCreate,
    background_tasks: BackgroundTasks,
    service: OrderServiceDep,
    current_user: CurrentUser,
):
    """Create order with multiple background tasks."""
    order = await service.create(data, current_user)

    # Queue multiple background tasks
    background_tasks.add_task(
        send_order_confirmation,
        order.id,
        current_user.email,
    )
    background_tasks.add_task(
        notify_warehouse,
        order.id,
    )
    background_tasks.add_task(
        update_inventory,
        order.items,
    )
    background_tasks.add_task(
        log_order_analytics,
        order.id,
        current_user.id,
    )

    return order
```

### Dependency Injection in Background Tasks

```python
# app/api/v1/endpoints/reports.py
from fastapi import BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db


async def generate_report_task(
    report_id: UUID,
    db_url: str,
) -> None:
    """Generate report in background with own DB connection."""
    # Create new session for background task
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine)

    async with async_session() as session:
        report_service = ReportService(session)
        await report_service.generate(report_id)

    await engine.dispose()


@router.post("/reports/")
async def create_report(
    data: ReportCreate,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
):
    """Create report generation job."""
    report = await report_service.create_pending(data)

    # Pass database URL, not session
    background_tasks.add_task(
        generate_report_task,
        report.id,
        str(settings.DATABASE_URL),
    )

    return {"report_id": report.id, "status": "processing"}
```

## Task Queues with Celery

### Celery Configuration

```python
# app/worker/celery_app.py
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Task routes
celery_app.conf.task_routes = {
    "app.worker.tasks.email.*": {"queue": "email"},
    "app.worker.tasks.reports.*": {"queue": "reports"},
    "app.worker.tasks.notifications.*": {"queue": "notifications"},
}
```

### Celery Tasks

```python
# app/worker/tasks/email.py
from celery import shared_task
from app.services.email import EmailService


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def send_email_task(
    self,
    to: str,
    subject: str,
    template: str,
    context: dict,
):
    """Send email task with retry logic."""
    try:
        email_service = EmailService()
        email_service.send_sync(
            to=to,
            subject=subject,
            template=template,
            context=context,
        )
    except Exception as exc:
        self.retry(exc=exc)


@shared_task(
    bind=True,
    max_retries=3,
)
def send_bulk_emails_task(
    self,
    recipients: list[dict],
    template: str,
):
    """Send bulk emails."""
    email_service = EmailService()

    for recipient in recipients:
        try:
            email_service.send_sync(
                to=recipient["email"],
                subject=recipient["subject"],
                template=template,
                context=recipient.get("context", {}),
            )
        except Exception as e:
            # Log error but continue with others
            logger.error(f"Failed to send email to {recipient['email']}: {e}")


# app/worker/tasks/reports.py
@shared_task(
    bind=True,
    max_retries=2,
    time_limit=3600,
)
def generate_report_task(
    self,
    report_id: str,
    report_type: str,
    params: dict,
):
    """Generate report task."""
    from app.services.reports import ReportService

    service = ReportService()

    try:
        # Update status
        service.update_status_sync(report_id, "processing")

        # Generate report
        result = service.generate_sync(report_type, params)

        # Save result
        service.save_result_sync(report_id, result)
        service.update_status_sync(report_id, "completed")

        return {"report_id": report_id, "status": "completed"}

    except Exception as exc:
        service.update_status_sync(report_id, "failed", error=str(exc))
        self.retry(exc=exc)
```

### Calling Celery Tasks from FastAPI

```python
# app/api/v1/endpoints/emails.py
from fastapi import APIRouter

from app.worker.tasks.email import send_email_task, send_bulk_emails_task

router = APIRouter()


@router.post("/send-email")
async def send_email(data: EmailRequest):
    """Queue email for sending."""
    task = send_email_task.delay(
        to=data.to,
        subject=data.subject,
        template=data.template,
        context=data.context,
    )

    return {"task_id": task.id, "status": "queued"}


@router.post("/send-bulk")
async def send_bulk(data: BulkEmailRequest):
    """Queue bulk email sending."""
    task = send_bulk_emails_task.delay(
        recipients=data.recipients,
        template=data.template,
    )

    return {"task_id": task.id, "status": "queued"}


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status."""
    from app.worker.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
    }
```

## ARQ (Async Task Queue)

### ARQ Configuration

```python
# app/worker/arq_worker.py
from arq import cron
from arq.connections import RedisSettings

from app.core.config import settings


async def startup(ctx):
    """Worker startup."""
    ctx["db"] = await create_db_pool()
    ctx["redis"] = await create_redis_pool()


async def shutdown(ctx):
    """Worker shutdown."""
    await ctx["db"].close()
    await ctx["redis"].close()


class WorkerSettings:
    """ARQ worker settings."""

    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)

    functions = [
        send_email,
        generate_report,
        process_webhook,
        cleanup_old_files,
    ]

    cron_jobs = [
        cron(cleanup_expired_sessions, hour=0, minute=0),
        cron(generate_daily_report, hour=6, minute=0),
        cron(sync_external_data, minute={0, 30}),
    ]

    on_startup = startup
    on_shutdown = shutdown

    max_jobs = 10
    job_timeout = 300
    keep_result = 3600
```

### ARQ Tasks

```python
# app/worker/tasks.py
import asyncio
from arq import ArqRedis


async def send_email(
    ctx: dict,
    to: str,
    subject: str,
    template: str,
    context: dict,
) -> dict:
    """Send email task."""
    email_service = EmailService()
    await email_service.send(
        to=to,
        subject=subject,
        template=template,
        context=context,
    )
    return {"sent": True, "to": to}


async def generate_report(
    ctx: dict,
    report_id: str,
    report_type: str,
    params: dict,
) -> dict:
    """Generate report task."""
    db = ctx["db"]
    report_service = ReportService(db)

    await report_service.update_status(report_id, "processing")

    try:
        result = await report_service.generate(report_type, params)
        await report_service.save_result(report_id, result)
        await report_service.update_status(report_id, "completed")

        return {"report_id": report_id, "status": "completed"}

    except Exception as e:
        await report_service.update_status(report_id, "failed", error=str(e))
        raise


async def cleanup_expired_sessions(ctx: dict) -> int:
    """Cron job: cleanup expired sessions."""
    db = ctx["db"]
    deleted = await db.execute(
        "DELETE FROM sessions WHERE expires_at < NOW()"
    )
    return deleted.rowcount


# Enqueue tasks from FastAPI
async def enqueue_email(redis: ArqRedis, **kwargs):
    """Enqueue email task."""
    job = await redis.enqueue_job("send_email", **kwargs)
    return job.job_id


# Usage in endpoint
@router.post("/send-email")
async def send_email_endpoint(
    data: EmailRequest,
    redis: Redis,
):
    """Queue email for sending."""
    arq_redis = ArqRedis(redis)
    job_id = await arq_redis.enqueue_job(
        "send_email",
        to=data.to,
        subject=data.subject,
        template=data.template,
        context=data.context,
    )
    return {"job_id": job_id}
```

## Scheduled Tasks

### APScheduler Integration

```python
# app/core/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger


scheduler = AsyncIOScheduler()


def setup_scheduler():
    """Configure scheduled tasks."""

    # Daily cleanup at midnight
    scheduler.add_job(
        cleanup_expired_data,
        CronTrigger(hour=0, minute=0),
        id="cleanup_expired_data",
        replace_existing=True,
    )

    # Hourly stats aggregation
    scheduler.add_job(
        aggregate_hourly_stats,
        CronTrigger(minute=0),
        id="aggregate_hourly_stats",
        replace_existing=True,
    )

    # Every 5 minutes health check
    scheduler.add_job(
        check_external_services,
        IntervalTrigger(minutes=5),
        id="check_external_services",
        replace_existing=True,
    )

    scheduler.start()


async def cleanup_expired_data():
    """Clean up expired data."""
    async with async_session() as session:
        # Delete expired sessions
        await session.execute(
            delete(Session).where(Session.expires_at < datetime.utcnow())
        )
        # Delete old notifications
        await session.execute(
            delete(Notification).where(
                Notification.created_at < datetime.utcnow() - timedelta(days=30)
            )
        )
        await session.commit()


async def aggregate_hourly_stats():
    """Aggregate statistics hourly."""
    async with async_session() as session:
        stats_service = StatsService(session)
        await stats_service.aggregate_hour()


# Lifespan integration
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_scheduler()
    yield
    scheduler.shutdown()
```

## Task Patterns

### Fire and Forget

```python
# app/services/analytics.py
import asyncio


async def track_event(event_type: str, data: dict) -> None:
    """Track analytics event (fire and forget)."""
    # Don't await - fire and forget
    asyncio.create_task(_send_analytics(event_type, data))


async def _send_analytics(event_type: str, data: dict) -> None:
    """Send analytics data."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                settings.ANALYTICS_URL,
                json={"event": event_type, "data": data},
                timeout=5.0,
            )
    except Exception as e:
        logger.warning(f"Failed to send analytics: {e}")


# Usage
@router.post("/products/{id}/view")
async def view_product(id: UUID):
    product = await service.get_by_id(id)

    # Track view in background
    await track_event("product_viewed", {"product_id": str(id)})

    return product
```

### Batch Processing

```python
# app/services/batch.py
import asyncio
from typing import Any


class BatchProcessor:
    """Process items in batches."""

    def __init__(
        self,
        batch_size: int = 100,
        max_concurrent: int = 5,
    ):
        self.batch_size = batch_size
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def process_all(
        self,
        items: list[Any],
        processor: callable,
    ) -> list[Any]:
        """Process all items in batches."""
        results = []

        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_results = await self.process_batch(batch, processor)
            results.extend(batch_results)

        return results

    async def process_batch(
        self,
        batch: list[Any],
        processor: callable,
    ) -> list[Any]:
        """Process a single batch concurrently."""

        async def process_with_semaphore(item):
            async with self.semaphore:
                return await processor(item)

        return await asyncio.gather(
            *[process_with_semaphore(item) for item in batch],
            return_exceptions=True,
        )


# Usage
async def import_products(products: list[dict]) -> dict:
    processor = BatchProcessor(batch_size=50, max_concurrent=10)

    results = await processor.process_all(
        products,
        process_product_import,
    )

    succeeded = [r for r in results if not isinstance(r, Exception)]
    failed = [r for r in results if isinstance(r, Exception)]

    return {
        "total": len(products),
        "succeeded": len(succeeded),
        "failed": len(failed),
    }
```

### Retry with Exponential Backoff

```python
# app/core/retry.py
import asyncio
from typing import TypeVar, Callable
from functools import wraps

T = TypeVar("T")


def retry_async(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    exceptions: tuple = (Exception,),
):
    """Decorator for async retry with exponential backoff."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay,
                        )
                        logger.warning(
                            f"Attempt {attempt + 1} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)

            raise last_exception

        return wrapper

    return decorator


# Usage
@retry_async(max_retries=3, base_delay=1.0)
async def call_external_api(data: dict) -> dict:
    """Call external API with retry."""
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, json=data, timeout=10.0)
        response.raise_for_status()
        return response.json()
```

## Best Practices

1. **Use BackgroundTasks** for simple, quick operations
2. **Use Celery/ARQ** for long-running or distributed tasks
3. **Don't pass ORM objects** to background tasks (pass IDs)
4. **Handle errors gracefully** with proper logging
5. **Implement retry logic** for unreliable operations
6. **Use batch processing** for large datasets
7. **Monitor task queues** and set alerts
8. **Set appropriate timeouts** for all tasks
