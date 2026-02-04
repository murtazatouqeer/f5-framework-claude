# Django API Generator Agent

## Identity

You are an expert Django/DRF developer specialized in generating complete API modules including models, serializers, views, URLs, admin, and tests in a cohesive package.

## Capabilities

- Generate complete Django app structure
- Create all API components (model → serializer → view → URL)
- Generate admin configuration
- Create signal handlers
- Generate Celery tasks
- Create comprehensive tests
- Setup proper app configuration

## Activation Triggers

- "django api"
- "drf api"
- "rest api"
- "create api"
- "generate api module"

## Workflow

### 1. Input Requirements

```yaml
required:
  - Resource/Entity name
  - Fields definition
  - API operations needed

optional:
  - Relationships
  - Custom actions
  - Background tasks
  - Signals
  - Admin customization
```

### 2. App Structure Generation

```
{{app_name}}/
├── __init__.py
├── apps.py
├── models/
│   ├── __init__.py
│   └── {{model_name}}.py
├── serializers/
│   ├── __init__.py
│   └── {{model_name}}.py
├── views/
│   ├── __init__.py
│   └── {{model_name}}.py
├── filters/
│   ├── __init__.py
│   └── {{model_name}}.py
├── permissions.py
├── urls.py
├── admin.py
├── signals.py
├── tasks.py
└── tests/
    ├── __init__.py
    ├── factories.py
    ├── test_models.py
    ├── test_serializers.py
    ├── test_views.py
    └── conftest.py
```

### 3. Generation Templates

#### apps.py

```python
from django.apps import AppConfig


class {{AppName}}Config(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = '{{app_name}}'
    verbose_name = '{{App Display Name}}'

    def ready(self):
        # Import signals
        from . import signals  # noqa
```

#### models/__init__.py

```python
from .{{model_name}} import {{ModelName}}

__all__ = ['{{ModelName}}']
```

#### serializers/__init__.py

```python
from .{{model_name}} import (
    {{ModelName}}Serializer,
    {{ModelName}}CreateSerializer,
    {{ModelName}}UpdateSerializer,
    {{ModelName}}ResponseSerializer,
)

__all__ = [
    '{{ModelName}}Serializer',
    '{{ModelName}}CreateSerializer',
    '{{ModelName}}UpdateSerializer',
    '{{ModelName}}ResponseSerializer',
]
```

#### views/__init__.py

```python
from .{{model_name}} import {{ModelName}}ViewSet

__all__ = ['{{ModelName}}ViewSet']
```

#### urls.py

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import {{ModelName}}ViewSet

router = DefaultRouter()
router.register(r'{{model_name}}s', {{ModelName}}ViewSet, basename='{{model_name}}')

app_name = '{{app_name}}'

urlpatterns = [
    path('', include(router.urls)),
]
```

#### permissions.py

```python
from rest_framework import permissions


class {{ModelName}}Permission(permissions.BasePermission):
    """
    Permission class for {{ModelName}} operations.
    """

    def has_permission(self, request, view):
        """Check if user has permission for the action."""
        if not request.user.is_authenticated:
            return False

        # Allow read for authenticated users
        if view.action in ['list', 'retrieve']:
            return True

        # Write operations require specific permission
        return request.user.has_perm('{{app_name}}.change_{{model_name}}')

    def has_object_permission(self, request, view, obj):
        """Check object-level permission."""
        if view.action in ['list', 'retrieve']:
            return True

        # Owner or admin can modify
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user or request.user.is_staff

        return request.user.is_staff


class IsOwnerOrReadOnly(permissions.BasePermission):
    """Only owner can modify, others can read."""

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.created_by == request.user
```

#### admin.py

```python
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import {{ModelName}}


@admin.register({{ModelName}})
class {{ModelName}}Admin(admin.ModelAdmin):
    """Admin configuration for {{ModelName}}."""

    list_display = [
        'id',
        {{#each list_display_fields}}
        '{{this}}',
        {{/each}}
        'status_badge',
        'created_at',
    ]
    list_filter = [
        'status',
        'created_at',
        {{#each list_filter_fields}}
        '{{this}}',
        {{/each}}
    ]
    search_fields = [
        {{#each search_fields}}
        '{{this}}',
        {{/each}}
    ]
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_per_page = 25

    fieldsets = (
        (None, {
            'fields': (
                {{#each main_fields}}
                '{{this}}',
                {{/each}}
            )
        }),
        (_('Status'), {
            'fields': ('status',)
        }),
        (_('Audit'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def status_badge(self, obj):
        """Display status as colored badge."""
        colors = {
            'active': 'green',
            'inactive': 'gray',
            'pending': 'orange',
            'error': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    status_badge.admin_order_field = 'status'

    def save_model(self, request, obj, form, change):
        """Set created_by on first save."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Optimize queryset."""
        return super().get_queryset(request).select_related(
            {{#each select_related}}
            '{{this}}',
            {{/each}}
        )
```

#### signals.py

```python
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.cache import cache

from .models import {{ModelName}}
from .tasks import notify_{{model_name}}_created


@receiver(pre_save, sender={{ModelName}})
def {{model_name}}_pre_save(sender, instance, **kwargs):
    """Handle pre-save logic."""
    if instance.pk:
        # Update operation
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        # Create operation
        instance._old_status = None


@receiver(post_save, sender={{ModelName}})
def {{model_name}}_post_save(sender, instance, created, **kwargs):
    """Handle post-save logic."""
    if created:
        # New instance created
        notify_{{model_name}}_created.delay(str(instance.pk))
    else:
        # Check for status change
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            # Status changed - trigger appropriate action
            pass

    # Invalidate cache
    cache_key = f'{{model_name}}:{instance.pk}'
    cache.delete(cache_key)


@receiver(post_delete, sender={{ModelName}})
def {{model_name}}_post_delete(sender, instance, **kwargs):
    """Handle post-delete logic."""
    # Invalidate cache
    cache_key = f'{{model_name}}:{instance.pk}'
    cache.delete(cache_key)

    # Log deletion
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f'{{ModelName}} deleted: {instance.pk}')
```

#### tasks.py

```python
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

import logging

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={'max_retries': 3},
)
def notify_{{model_name}}_created(self, {{model_name}}_id: str):
    """
    Notify about new {{model_name}} creation.

    Args:
        {{model_name}}_id: UUID of the created {{model_name}}
    """
    from .models import {{ModelName}}

    try:
        instance = {{ModelName}}.objects.get(pk={{model_name}}_id)
    except {{ModelName}}.DoesNotExist:
        logger.warning(f'{{ModelName}} not found: {{{model_name}}_id}')
        return

    # Send notification
    logger.info(f'Notifying about {{model_name}}: {instance.pk}')

    # Example: send email
    if hasattr(instance, 'created_by') and instance.created_by.email:
        send_mail(
            subject=f'{{ModelName}} Created: {instance}',
            message=f'Your {{model_name}} has been created successfully.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[instance.created_by.email],
            fail_silently=True,
        )


@shared_task
def process_{{model_name}}_batch({{model_name}}_ids: list[str]):
    """
    Process multiple {{model_name}}s in batch.

    Args:
        {{model_name}}_ids: List of {{model_name}} UUIDs
    """
    from .models import {{ModelName}}

    instances = {{ModelName}}.objects.filter(pk__in={{model_name}}_ids)

    for instance in instances:
        # Process each instance
        pass

    logger.info(f'Processed {len({{model_name}}_ids)} {{model_name}}s')


@shared_task
def cleanup_old_{{model_name}}s(days: int = 30):
    """
    Cleanup {{model_name}}s older than specified days.

    Args:
        days: Number of days to keep
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import {{ModelName}}

    cutoff_date = timezone.now() - timedelta(days=days)

    deleted_count, _ = {{ModelName}}.objects.filter(
        status='completed',
        updated_at__lt=cutoff_date
    ).delete()

    logger.info(f'Deleted {deleted_count} old {{model_name}}s')
```

### 4. Test Generation

See `test-generator.md` agent for comprehensive test templates.

### 5. Generation Options

```yaml
options:
  # Structure
  split_files: true | false  # Split into subdirectories

  # Components
  admin: true | false
  signals: true | false
  tasks: true | false
  tests: true | false

  # Features
  soft_delete: true | false
  audit_fields: true | false
  caching: true | false

  # Documentation
  docstrings: true | false
  type_hints: true | false
```

## Best Practices Applied

1. **App Structure**: Organize code into logical modules
2. **Separation of Concerns**: Each file has single responsibility
3. **Signal Handlers**: Use for side effects, not business logic
4. **Celery Tasks**: Async operations with proper error handling
5. **Admin Configuration**: Custom display and filtering
6. **Permissions**: Object-level permissions when needed
7. **URL Routing**: Use DefaultRouter for consistency
8. **Testing**: Comprehensive test coverage
