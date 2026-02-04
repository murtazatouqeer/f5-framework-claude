# Django Signal Template

## Overview

Template for generating Django signals for model lifecycle events.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MODEL_NAME` | Model to observe | `Order` |
| `SIGNAL_TYPE` | Signal to connect | `post_save`, `pre_delete` |
| `HANDLER_NAME` | Handler function name | `on_order_created` |
| `ACTIONS` | Actions to perform | See below |

## Base Template

```python
# apps/{{APP_NAME}}/signals.py
from django.db.models.signals import (
    pre_save, post_save, pre_delete, post_delete, m2m_changed
)
from django.dispatch import receiver
from django.utils import timezone
import logging

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}
{% for task in CELERY_TASKS %}
from apps.{{task.app}}.tasks import {{task.name}}
{% endfor %}

logger = logging.getLogger(__name__)


{% for handler in HANDLERS %}
@receiver({{handler.signal}}, sender={{handler.model}})
def {{handler.name}}(sender, instance, **kwargs):
    """
    {{handler.description}}

    Args:
        sender: The model class
        instance: The model instance
        **kwargs: Additional signal arguments
    """
    {% if handler.signal == 'post_save' %}
    created = kwargs.get('created', False)

    if created:
        # Handle creation
        {{handler.on_create}}
    else:
        # Handle update
        {{handler.on_update}}
    {% elif handler.signal == 'pre_save' %}
    if instance.pk:
        # Update - get original
        try:
            original = sender.objects.get(pk=instance.pk)
            {{handler.implementation}}
        except sender.DoesNotExist:
            pass
    else:
        # Create
        {{handler.on_create}}
    {% elif handler.signal == 'post_delete' %}
    {{handler.implementation}}
    {% elif handler.signal == 'm2m_changed' %}
    action = kwargs.get('action')
    pk_set = kwargs.get('pk_set')

    if action == 'post_add':
        {{handler.on_add}}
    elif action == 'post_remove':
        {{handler.on_remove}}
    elif action == 'post_clear':
        {{handler.on_clear}}
    {% endif %}


{% endfor %}
```

## Signal Registration (apps.py)

```python
# apps/{{APP_NAME}}/apps.py
from django.apps import AppConfig


class {{APP_NAME_PASCAL}}Config(AppConfig):
    name = 'apps.{{APP_NAME}}'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Import signals when app is ready."""
        import apps.{{APP_NAME}}.signals  # noqa
```

## Common Signal Patterns

### Post-Save: Audit Logging

```python
@receiver(post_save, sender=Order)
def log_order_changes(sender, instance, created, **kwargs):
    """Log order creation and updates."""
    if created:
        logger.info(
            f"Order created: {instance.id} by user {instance.user_id}",
            extra={
                'order_id': str(instance.id),
                'user_id': str(instance.user_id),
                'total': str(instance.total),
            }
        )
    else:
        logger.info(
            f"Order updated: {instance.id}",
            extra={
                'order_id': str(instance.id),
                'status': instance.status,
            }
        )
```

### Post-Save: Send Notification

```python
@receiver(post_save, sender=Order)
def send_order_notification(sender, instance, created, **kwargs):
    """Send notification on order creation."""
    if created:
        # Async task for email
        send_order_confirmation_email.delay(str(instance.id))

        # Real-time notification
        send_push_notification.delay(
            user_id=str(instance.user_id),
            title='Order Placed',
            body=f'Your order #{instance.order_number} has been placed.'
        )
```

### Post-Save: Update Related Records

```python
@receiver(post_save, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Recalculate order total when item changes."""
    order = instance.order
    order.subtotal = order.items.aggregate(
        total=Sum(F('quantity') * F('unit_price'))
    )['total'] or 0
    order.total = order.subtotal + order.shipping_cost - order.discount
    order.save(update_fields=['subtotal', 'total', 'updated_at'])
```

### Pre-Save: Auto-populate Fields

```python
@receiver(pre_save, sender=Product)
def auto_generate_slug(sender, instance, **kwargs):
    """Generate slug from name if not provided."""
    if not instance.slug:
        from django.utils.text import slugify
        base_slug = slugify(instance.name)
        slug = base_slug
        counter = 1
        while Product.objects.filter(slug=slug).exclude(pk=instance.pk).exists():
            slug = f'{base_slug}-{counter}'
            counter += 1
        instance.slug = slug
```

### Pre-Save: Track Field Changes

```python
@receiver(pre_save, sender=Order)
def track_status_change(sender, instance, **kwargs):
    """Track when status changes."""
    if instance.pk:
        try:
            original = Order.objects.get(pk=instance.pk)
            if original.status != instance.status:
                # Status changed
                instance.status_changed_at = timezone.now()

                # Log transition
                StatusHistory.objects.create(
                    order=instance,
                    from_status=original.status,
                    to_status=instance.status,
                )
        except Order.DoesNotExist:
            pass
```

### Post-Delete: Cleanup Related Data

```python
@receiver(post_delete, sender=Product)
def cleanup_product_files(sender, instance, **kwargs):
    """Delete associated files when product is deleted."""
    # Delete product images from storage
    if instance.image:
        instance.image.delete(save=False)

    # Delete related media files
    for image in instance.images.all():
        image.file.delete(save=False)
```

### Post-Delete: Invalidate Cache

```python
@receiver(post_delete, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Clear product caches on delete."""
    from django.core.cache import cache

    cache.delete(f'product:{instance.pk}')
    cache.delete(f'category_products:{instance.category_id}')
    cache.delete('featured_products')
```

### M2M Changed: Sync Data

```python
@receiver(m2m_changed, sender=Product.tags.through)
def sync_tag_count(sender, instance, action, pk_set, **kwargs):
    """Update tag counts when products change."""
    if action in ('post_add', 'post_remove', 'post_clear'):
        # Update affected tags
        from apps.tags.models import Tag

        if pk_set:
            tags = Tag.objects.filter(pk__in=pk_set)
        else:
            tags = instance.tags.all()

        for tag in tags:
            tag.product_count = tag.products.count()
            tag.save(update_fields=['product_count'])
```

## Signal with Transaction Handling

```python
from django.db import transaction

@receiver(post_save, sender=Order)
def process_order_creation(sender, instance, created, **kwargs):
    """Process order with transaction safety."""
    if created:
        # Execute after transaction commits
        transaction.on_commit(
            lambda: send_order_confirmation_email.delay(str(instance.id))
        )

        # Immediate database operations
        instance.user.update_order_stats()
```

## Custom Signal Definition

```python
# apps/{{APP_NAME}}/signals.py
from django.dispatch import Signal

# Define custom signals
order_paid = Signal()  # Provides: ['order', 'payment']
order_shipped = Signal()  # Provides: ['order', 'tracking']
order_delivered = Signal()  # Provides: ['order']


# Emit signal
def process_payment(order, payment_result):
    if payment_result.success:
        order.status = 'paid'
        order.save()

        # Emit custom signal
        order_paid.send(
            sender=order.__class__,
            order=order,
            payment=payment_result
        )


# Handle signal
@receiver(order_paid)
def on_order_paid(sender, order, payment, **kwargs):
    """Handle successful payment."""
    # Update inventory
    for item in order.items.all():
        item.product.stock -= item.quantity
        item.product.save(update_fields=['stock'])

    # Notify warehouse
    create_fulfillment_request.delay(str(order.id))
```

## Usage Example

```yaml
input:
  APP_NAME: orders
  MODEL_NAME: Order
  HANDLERS:
    - name: on_order_created
      signal: post_save
      model: Order
      description: "Handle new order creation"
      on_create: |
        # Send confirmation email
        send_order_confirmation_email.delay(str(instance.id))

        # Create audit log
        AuditLog.objects.create(
            action='order_created',
            object_id=str(instance.id),
            user=instance.user,
            data={'total': str(instance.total)}
        )
      on_update: |
        # Check for status change
        if instance.tracker.has_changed('status'):
            send_order_status_update.delay(str(instance.id))
    - name: cleanup_order_data
      signal: post_delete
      model: Order
      description: "Clean up order-related data"
      implementation: |
        # Clear related caches
        cache.delete(f'user_orders:{instance.user_id}')

        # Log deletion
        logger.info(f'Order {instance.id} deleted')
```

## Best Practices

1. **Keep signals lightweight** - offload heavy work to Celery tasks
2. **Use transaction.on_commit** - for post-commit actions like emails
3. **Handle exceptions** - don't break saves with signal errors
4. **Avoid signal cascades** - watch for infinite loops
5. **Log signal execution** - for debugging
6. **Test signals** - verify they fire correctly
7. **Document signal dependencies** - for maintenance
