# DRF Exception Handling Skill

## Overview

Comprehensive exception handling patterns for Django REST Framework APIs.

## Custom Exception Handler

```python
# core/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Custom exception handler for consistent API error responses.
    """
    # Call DRF's default exception handler first
    response = exception_handler(exc, context)

    # Handle Django validation errors
    if isinstance(exc, DjangoValidationError):
        if hasattr(exc, 'message_dict'):
            data = {
                'error': 'validation_error',
                'message': 'Validation failed',
                'details': exc.message_dict
            }
        else:
            data = {
                'error': 'validation_error',
                'message': str(exc),
                'details': {}
            }
        return Response(data, status=status.HTTP_400_BAD_REQUEST)

    # If DRF handled it, format consistently
    if response is not None:
        # Restructure error response
        error_data = {
            'error': get_error_code(exc),
            'message': get_error_message(exc, response),
            'details': get_error_details(response.data),
        }

        # Add request ID for tracking
        request = context.get('request')
        if request:
            error_data['request_id'] = getattr(request, 'id', None)

        response.data = error_data

        # Log server errors
        if response.status_code >= 500:
            logger.error(
                f"Server error: {error_data}",
                exc_info=True,
                extra={
                    'request': request,
                    'status_code': response.status_code,
                }
            )

    return response


def get_error_code(exc):
    """Get error code from exception."""
    error_codes = {
        'AuthenticationFailed': 'authentication_failed',
        'NotAuthenticated': 'not_authenticated',
        'PermissionDenied': 'permission_denied',
        'NotFound': 'not_found',
        'MethodNotAllowed': 'method_not_allowed',
        'ValidationError': 'validation_error',
        'ParseError': 'parse_error',
        'Throttled': 'rate_limited',
    }
    return error_codes.get(exc.__class__.__name__, 'error')


def get_error_message(exc, response):
    """Get user-friendly error message."""
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, str):
            return exc.detail
        if isinstance(exc.detail, list):
            return exc.detail[0] if exc.detail else 'An error occurred'
    return 'An error occurred'


def get_error_details(data):
    """Extract error details from response data."""
    if isinstance(data, dict):
        # Remove 'detail' key if message is already extracted
        details = {k: v for k, v in data.items() if k != 'detail'}
        return details if details else {}
    if isinstance(data, list):
        return {'errors': data}
    return {}
```

## Custom Exceptions

```python
# core/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status


class BusinessLogicError(APIException):
    """Base exception for business logic errors."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'A business logic error occurred.'
    default_code = 'business_error'


class InsufficientFundsError(BusinessLogicError):
    """Raised when account has insufficient funds."""

    default_detail = 'Insufficient funds for this transaction.'
    default_code = 'insufficient_funds'


class ResourceLockError(BusinessLogicError):
    """Raised when resource is locked by another process."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = 'Resource is currently locked. Please try again later.'
    default_code = 'resource_locked'


class RateLimitExceededError(APIException):
    """Raised when rate limit is exceeded."""

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = 'Rate limit exceeded. Please try again later.'
    default_code = 'rate_limited'

    def __init__(self, detail=None, retry_after=None):
        super().__init__(detail)
        self.retry_after = retry_after


class ExternalServiceError(APIException):
    """Raised when external service fails."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = 'External service unavailable.'
    default_code = 'external_service_error'


class MaintenanceModeError(APIException):
    """Raised during maintenance mode."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = 'Service temporarily unavailable for maintenance.'
    default_code = 'maintenance_mode'
```

## Using Custom Exceptions

```python
# services/payment.py
from core.exceptions import InsufficientFundsError, ExternalServiceError


class PaymentService:
    """Payment service with proper exception handling."""

    def process_payment(self, user, amount):
        # Check balance
        if user.balance < amount:
            raise InsufficientFundsError(
                detail=f'Available balance: {user.balance}. Required: {amount}.'
            )

        try:
            # Call external payment provider
            result = self.payment_provider.charge(user, amount)
        except PaymentProviderTimeout:
            raise ExternalServiceError(
                detail='Payment provider is not responding. Please try again.'
            )
        except PaymentProviderError as e:
            raise ExternalServiceError(detail=str(e))

        return result


# views/payment.py
class PaymentView(APIView):
    """Payment endpoint with exception handling."""

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Exceptions will be caught by custom_exception_handler
        result = PaymentService().process_payment(
            user=request.user,
            amount=serializer.validated_data['amount']
        )

        return Response({'transaction_id': result.id})
```

## Error Response Format

```json
{
    "error": "validation_error",
    "message": "Validation failed",
    "details": {
        "email": ["Enter a valid email address."],
        "password": ["This field is required."]
    },
    "request_id": "req_abc123"
}
```

```json
{
    "error": "insufficient_funds",
    "message": "Available balance: 100.00. Required: 150.00.",
    "details": {},
    "request_id": "req_def456"
}
```

## Middleware for Request ID

```python
# core/middleware.py
import uuid


class RequestIDMiddleware:
    """Add unique ID to each request for tracking."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.id = str(uuid.uuid4())[:8]
        response = self.get_response(request)
        response['X-Request-ID'] = request.id
        return response
```

## Exception Logging

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {request_id} {message}',
            'style': '{',
        },
    },
    'filters': {
        'request_id': {
            '()': 'core.logging.RequestIDFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'filters': ['request_id'],
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/errors.log',
            'formatter': 'verbose',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'api': {
            'handlers': ['console', 'error_file'],
            'level': 'DEBUG',
        },
    },
}
```

## Best Practices

1. **Consistent format** - Same structure for all errors
2. **Request ID** - Track errors across systems
3. **Log server errors** - For debugging
4. **User-friendly messages** - Don't expose internals
5. **Appropriate status codes** - Use correct HTTP status
6. **Custom exceptions** - For business logic errors
7. **Handle external errors** - Wrap provider exceptions
