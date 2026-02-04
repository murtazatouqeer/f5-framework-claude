# Django Logging Skill

## Overview

Logging configuration and patterns for Django applications.

## Logging Configuration

```python
# settings/base.py
import os

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {module}:{lineno} - {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },

    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'request_id': {
            '()': 'apps.core.logging.RequestIDFilter',
        },
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'app.log'),
            'maxBytes': 10 * 1024 * 1024,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'errors.log'),
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'include_html': True,
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console', 'error_file', 'mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',  # DEBUG to see SQL queries
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },

    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
}
```

## Request ID Filter

```python
# apps/core/logging.py
import logging
import threading

_thread_locals = threading.local()


def get_request_id():
    """Get current request ID from thread local."""
    return getattr(_thread_locals, 'request_id', '-')


def set_request_id(request_id):
    """Set request ID in thread local."""
    _thread_locals.request_id = request_id


class RequestIDFilter(logging.Filter):
    """Add request ID to log records."""

    def filter(self, record):
        record.request_id = get_request_id()
        return True


class RequestIDMiddleware:
    """Middleware to set request ID."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import uuid
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4())[:8])
        set_request_id(request_id)
        request.id = request_id

        response = self.get_response(request)
        response['X-Request-ID'] = request_id

        return response
```

## Structured Logging

```python
# apps/core/logging.py
import logging
import json
from datetime import datetime


class StructuredLogger:
    """Logger wrapper for structured logging."""

    def __init__(self, name):
        self.logger = logging.getLogger(name)

    def _log(self, level, message, **kwargs):
        """Log with structured context."""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'context': kwargs,
        }
        getattr(self.logger, level)(message, extra={'structured': extra})

    def info(self, message, **kwargs):
        self._log('info', message, **kwargs)

    def warning(self, message, **kwargs):
        self._log('warning', message, **kwargs)

    def error(self, message, **kwargs):
        self._log('error', message, **kwargs)

    def debug(self, message, **kwargs):
        self._log('debug', message, **kwargs)


# Usage
logger = StructuredLogger(__name__)

logger.info(
    'Order created',
    order_id=str(order.id),
    user_id=str(user.id),
    total=str(order.total),
    items_count=order.items.count()
)
```

## Logging in Views

```python
import logging

logger = logging.getLogger(__name__)


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet with logging."""

    def create(self, request, *args, **kwargs):
        logger.info(
            f'Creating order for user {request.user.id}',
            extra={
                'user_id': str(request.user.id),
                'data': request.data,
            }
        )

        try:
            response = super().create(request, *args, **kwargs)
            logger.info(
                f'Order created: {response.data.get("id")}',
                extra={'order_id': response.data.get('id')}
            )
            return response

        except Exception as e:
            logger.exception(
                f'Failed to create order: {str(e)}',
                extra={
                    'user_id': str(request.user.id),
                    'error': str(e),
                }
            )
            raise
```

## Logging in Services

```python
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)


def log_execution(func):
    """Decorator to log function execution."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        func_name = f'{func.__module__}.{func.__name__}'
        logger.debug(f'Starting {func_name}')
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f'Completed {func_name}',
                extra={'duration_ms': round(duration * 1000, 2)}
            )
            return result

        except Exception as e:
            duration = time.time() - start_time
            logger.exception(
                f'Failed {func_name}: {str(e)}',
                extra={
                    'duration_ms': round(duration * 1000, 2),
                    'error': str(e),
                }
            )
            raise

    return wrapper


class PaymentService:
    """Service with logging."""

    @log_execution
    def process_payment(self, user, amount):
        logger.info(
            f'Processing payment',
            extra={
                'user_id': str(user.id),
                'amount': str(amount),
            }
        )

        # Process payment
        result = self._charge(user, amount)

        logger.info(
            f'Payment successful',
            extra={
                'transaction_id': result.id,
                'amount': str(amount),
            }
        )

        return result
```

## Audit Logging

```python
# apps/core/audit.py
import logging
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

audit_logger = logging.getLogger('audit')


class AuditLog:
    """Audit log for tracking user actions."""

    @staticmethod
    def log(action, user, obj=None, details=None):
        """Log an audit event."""
        log_data = {
            'timestamp': timezone.now().isoformat(),
            'action': action,
            'user_id': str(user.id) if user else None,
            'user_email': user.email if user else None,
        }

        if obj:
            log_data.update({
                'object_type': ContentType.objects.get_for_model(obj).model,
                'object_id': str(obj.pk),
            })

        if details:
            log_data['details'] = details

        audit_logger.info(
            f'{action}: {log_data.get("object_type", "N/A")}',
            extra={'audit': log_data}
        )


# Usage
AuditLog.log(
    action='order.created',
    user=request.user,
    obj=order,
    details={'total': str(order.total)}
)
```

## Best Practices

1. **Use logger hierarchy** - `apps.orders.views`, not generic names
2. **Include context** - User ID, request ID, relevant IDs
3. **Log at appropriate levels** - DEBUG for dev, INFO for ops
4. **Rotate log files** - Prevent disk fill
5. **Structured logging** - JSON format for aggregation
6. **Audit trail** - Track user actions separately
7. **Don't log sensitive data** - Passwords, tokens, PII
