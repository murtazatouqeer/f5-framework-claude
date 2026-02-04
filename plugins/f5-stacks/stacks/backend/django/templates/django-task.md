# Django Celery Task Template

## Overview

Template for generating Celery tasks for async operations.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `TASK_NAME` | Task function name | `send_order_email` |
| `QUEUE` | Celery queue | `default`, `high_priority` |
| `RETRY_CONFIG` | Retry settings | See below |
| `RATE_LIMIT` | Rate limiting | `10/m` |

## Base Template

```python
# apps/{{APP_NAME}}/tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
import time

logger = get_task_logger(__name__)


@shared_task(
    name='{{APP_NAME}}.{{TASK_NAME}}',
    bind=True,
    {% if QUEUE %}queue='{{QUEUE}}',{% endif %}
    {% if RETRY_CONFIG %}
    autoretry_for=({{RETRY_CONFIG.exceptions}}),
    retry_backoff={{RETRY_CONFIG.backoff|default:True}},
    retry_backoff_max={{RETRY_CONFIG.max_backoff|default:600}},
    retry_kwargs={'max_retries': {{RETRY_CONFIG.max_retries|default:3}}},
    {% endif %}
    {% if RATE_LIMIT %}rate_limit='{{RATE_LIMIT}}',{% endif %}
    {% if SOFT_TIME_LIMIT %}soft_time_limit={{SOFT_TIME_LIMIT}},{% endif %}
    {% if TIME_LIMIT %}time_limit={{TIME_LIMIT}},{% endif %}
    {% if ACKS_LATE %}acks_late=True,{% endif %}
)
def {{TASK_NAME}}(self, {{PARAMS}}):
    """
    {{DESCRIPTION}}

    Args:
        {{PARAMS_DOC}}

    Returns:
        {{RETURN_DOC}}
    """
    task_id = self.request.id
    logger.info(f'Task {task_id} started: {{TASK_NAME}}')

    try:
        {{IMPLEMENTATION}}

        logger.info(f'Task {task_id} completed successfully')
        return {{RETURN_VALUE}}

    except Exception as exc:
        logger.error(f'Task {task_id} failed: {exc}', exc_info=True)
        raise self.retry(exc=exc)
```

## Celery Configuration

```python
# config/celery.py
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('{{PROJECT_NAME}}')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# Task routing
app.conf.task_routes = {
    '*.send_*': {'queue': 'email'},
    '*.process_*': {'queue': 'processing'},
    '*.generate_*': {'queue': 'reports'},
    '*.sync_*': {'queue': 'sync'},
}

# Task time limits
app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 25 * 60  # 25 minutes

# Result backend
app.conf.result_backend = 'django-db'
app.conf.result_extended = True
app.conf.result_expires = 60 * 60 * 24 * 7  # 7 days


# Periodic tasks (Celery Beat)
app.conf.beat_schedule = {
    'cleanup-expired-sessions': {
        'task': 'users.cleanup_expired_sessions',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
    'generate-daily-report': {
        'task': 'reports.generate_daily_report',
        'schedule': crontab(hour=6, minute=0),
    },
    'sync-inventory': {
        'task': 'products.sync_inventory',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
    'send-reminder-emails': {
        'task': 'notifications.send_reminder_emails',
        'schedule': crontab(hour=9, minute=0, day_of_week='1-5'),  # Weekdays 9 AM
    },
}
```

## Settings Configuration

```python
# config/settings/base.py
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
```

## Task Patterns

### Email Task

```python
@shared_task(
    bind=True,
    queue='email',
    rate_limit='30/m',
    autoretry_for=(SMTPException,),
    retry_backoff=True,
    max_retries=3,
)
def send_order_confirmation_email(self, order_id: str):
    """Send order confirmation email."""
    from apps.orders.models import Order

    order = Order.objects.select_related('user').get(pk=order_id)

    send_mail(
        subject=f'Order Confirmation #{order.order_number}',
        message=render_to_string('emails/order_confirmation.txt', {'order': order}),
        html_message=render_to_string('emails/order_confirmation.html', {'order': order}),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
    )

    logger.info(f'Sent order confirmation for {order_id}')
    return {'order_id': order_id, 'email': order.user.email}
```

### Data Processing Task

```python
@shared_task(
    bind=True,
    queue='processing',
    soft_time_limit=300,
    time_limit=360,
    acks_late=True,
)
def process_order(self, order_id: str):
    """Process order: validate, reserve inventory, calculate shipping."""
    from apps.orders.models import Order
    from apps.orders.services import OrderProcessor

    order = Order.objects.get(pk=order_id)
    processor = OrderProcessor(order)

    try:
        # Update progress
        self.update_state(state='PROGRESS', meta={'step': 'validating'})
        processor.validate()

        self.update_state(state='PROGRESS', meta={'step': 'reserving_inventory'})
        processor.reserve_inventory()

        self.update_state(state='PROGRESS', meta={'step': 'calculating_shipping'})
        processor.calculate_shipping()

        order.status = 'processing'
        order.save()

        return {'order_id': order_id, 'status': 'processed'}

    except InventoryError as exc:
        order.status = 'failed'
        order.error_message = str(exc)
        order.save()
        raise
```

### Report Generation Task

```python
@shared_task(
    bind=True,
    queue='reports',
    soft_time_limit=1800,  # 30 minutes
    time_limit=2100,  # 35 minutes
)
def generate_sales_report(self, start_date: str, end_date: str, user_id: str):
    """Generate sales report for date range."""
    from apps.reports.services import ReportGenerator
    from apps.users.models import User

    user = User.objects.get(pk=user_id)
    generator = ReportGenerator()

    # Generate report
    report_data = generator.generate_sales_report(
        start_date=start_date,
        end_date=end_date,
    )

    # Save report file
    report_path = generator.save_report(report_data, format='xlsx')

    # Send email with report
    send_report_email.delay(
        user_id=user_id,
        report_path=report_path,
        report_type='sales',
    )

    return {'report_path': report_path}
```

### Periodic Cleanup Task

```python
@shared_task(name='orders.cleanup_stale_orders')
def cleanup_stale_orders():
    """Clean up orders stuck in pending state."""
    from apps.orders.models import Order

    stale_cutoff = timezone.now() - timedelta(hours=24)

    stale_orders = Order.objects.filter(
        status='pending',
        created_at__lt=stale_cutoff,
    )

    cancelled_count = 0
    for order in stale_orders:
        order.status = 'cancelled'
        order.cancellation_reason = 'Timed out - no payment received'
        order.save()
        cancelled_count += 1

        # Restore inventory
        for item in order.items.all():
            item.product.stock += item.quantity
            item.product.save()

    logger.info(f'Cancelled {cancelled_count} stale orders')
    return {'cancelled': cancelled_count}
```

### Webhook Task with Retry

```python
@shared_task(
    bind=True,
    queue='webhooks',
    autoretry_for=(RequestException,),
    retry_backoff=True,
    retry_backoff_max=3600,  # Max 1 hour backoff
    max_retries=10,
)
def send_webhook(self, webhook_id: str, event_type: str, payload: dict):
    """Send webhook to external service."""
    from apps.integrations.models import Webhook
    import requests

    webhook = Webhook.objects.get(pk=webhook_id)

    response = requests.post(
        webhook.url,
        json={
            'event': event_type,
            'data': payload,
            'timestamp': timezone.now().isoformat(),
        },
        headers={
            'Content-Type': 'application/json',
            'X-Webhook-Secret': webhook.secret,
        },
        timeout=30,
    )

    response.raise_for_status()

    # Log delivery
    WebhookDelivery.objects.create(
        webhook=webhook,
        event_type=event_type,
        status_code=response.status_code,
        response_body=response.text[:1000],
    )

    return {'status_code': response.status_code}
```

### Chained Tasks

```python
from celery import chain, group

def process_large_order(order_id: str):
    """Chain of tasks for large order processing."""
    return chain(
        validate_order.s(order_id),
        reserve_inventory.s(),
        calculate_shipping.s(),
        process_payment.s(),
        send_confirmation.s(),
    ).apply_async()


def parallel_notifications(user_id: str, message: str):
    """Send notifications in parallel."""
    return group(
        send_email_notification.s(user_id, message),
        send_push_notification.s(user_id, message),
        send_sms_notification.s(user_id, message),
    ).apply_async()
```

## Usage Example

```yaml
input:
  APP_NAME: orders
  TASK_NAME: process_order_payment
  QUEUE: payments
  DESCRIPTION: "Process payment for order"
  PARAMS: "order_id: str, payment_method: str"
  RETRY_CONFIG:
    exceptions: "(PaymentError, ConnectionError)"
    max_retries: 5
    backoff: true
    max_backoff: 300
  RATE_LIMIT: "100/m"
  SOFT_TIME_LIMIT: 60
  TIME_LIMIT: 90
  IMPLEMENTATION: |
    from apps.orders.models import Order
    from apps.payments.services import PaymentService

    order = Order.objects.get(pk=order_id)
    payment_service = PaymentService()

    result = payment_service.process_payment(
        order=order,
        method=payment_method,
    )

    if result.success:
        order.status = 'paid'
        order.payment_id = result.transaction_id
        order.save()

        # Trigger fulfillment
        create_fulfillment.delay(order_id)

    return {'success': result.success, 'transaction_id': result.transaction_id}
  RETURN_VALUE: "result"
```

## Best Practices

1. **Use bind=True** - access task instance for retries
2. **Set time limits** - prevent runaway tasks
3. **Use acks_late** - for critical tasks that shouldn't be lost
4. **Implement idempotency** - tasks may run multiple times
5. **Log task progress** - for debugging and monitoring
6. **Use appropriate queues** - separate by priority/type
7. **Handle failures gracefully** - retry with backoff
8. **Monitor task results** - use Flower or similar
