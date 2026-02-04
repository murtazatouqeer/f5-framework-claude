# Django App Patterns Skill

## Overview

Design patterns and best practices for Django application architecture.

## App Organization Patterns

### 1. Single-File vs Directory Structure

**Simple App (single files)**
```
simple_app/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py
├── views.py
├── urls.py
└── tests.py
```

**Complex App (directory structure)**
```
complex_app/
├── __init__.py
├── apps.py
├── admin/
│   ├── __init__.py
│   └── {{model}}.py
├── models/
│   ├── __init__.py
│   ├── base.py
│   └── {{model}}.py
├── serializers/
│   ├── __init__.py
│   └── {{model}}.py
├── views/
│   ├── __init__.py
│   └── {{model}}.py
├── filters/
│   ├── __init__.py
│   └── {{model}}.py
├── services/
│   ├── __init__.py
│   └── {{domain}}.py
├── tasks.py
├── signals.py
├── permissions.py
├── urls.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── factories.py
    ├── test_models.py
    ├── test_views.py
    └── test_services.py
```

## Service Layer Pattern

### When to Use

- Complex business logic spanning multiple models
- Operations requiring transactions
- External service integrations
- Reusable business operations

### Implementation

```python
# services/order_service.py
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Optional

from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from apps.payments.services import PaymentService


class OrderService:
    """
    Service for order-related business logic.
    """

    def __init__(self):
        self.payment_service = PaymentService()

    @transaction.atomic
    def create_order(
        self,
        user,
        items: list[dict],
        shipping_address: dict,
    ) -> Order:
        """
        Create a new order with items.

        Args:
            user: User placing the order
            items: List of {product_id, quantity}
            shipping_address: Shipping address dict

        Returns:
            Created Order instance

        Raises:
            ValidationError: If validation fails
        """
        # Validate stock
        self._validate_stock(items)

        # Calculate totals
        subtotal = self._calculate_subtotal(items)
        shipping = self._calculate_shipping(shipping_address)
        tax = self._calculate_tax(subtotal, shipping_address)
        total = subtotal + shipping + tax

        # Create order
        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            shipping_cost=shipping,
            tax=tax,
            total=total,
            shipping_address=shipping_address,
        )

        # Create order items
        self._create_order_items(order, items)

        # Reserve inventory
        self._reserve_inventory(items)

        return order

    @transaction.atomic
    def process_payment(
        self,
        order: Order,
        payment_method_id: str,
    ) -> Order:
        """Process payment for an order."""
        if order.status != 'pending':
            raise ValidationError('Order is not in pending status')

        # Process payment
        payment = self.payment_service.charge(
            amount=order.total,
            payment_method_id=payment_method_id,
            metadata={'order_id': str(order.id)},
        )

        # Update order
        order.payment_id = payment.id
        order.status = 'paid'
        order.save(update_fields=['payment_id', 'status'])

        return order

    def _validate_stock(self, items: list[dict]) -> None:
        """Validate all items are in stock."""
        for item in items:
            product = Product.objects.get(pk=item['product_id'])
            if product.stock < item['quantity']:
                raise ValidationError(
                    f'Insufficient stock for {product.name}'
                )

    def _calculate_subtotal(self, items: list[dict]) -> Decimal:
        """Calculate order subtotal."""
        subtotal = Decimal('0')
        for item in items:
            product = Product.objects.get(pk=item['product_id'])
            subtotal += product.price * item['quantity']
        return subtotal

    def _create_order_items(self, order: Order, items: list[dict]) -> None:
        """Create order items."""
        order_items = []
        for item in items:
            product = Product.objects.get(pk=item['product_id'])
            order_items.append(OrderItem(
                order=order,
                product=product,
                quantity=item['quantity'],
                unit_price=product.price,
            ))
        OrderItem.objects.bulk_create(order_items)
```

### Using Services in Views

```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.orders.services import OrderService
from apps.orders.serializers import OrderCreateSerializer, OrderResponseSerializer


class OrderCreateView(APIView):
    """Create a new order."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.order_service = OrderService()

    def post(self, request):
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = self.order_service.create_order(
            user=request.user,
            items=serializer.validated_data['items'],
            shipping_address=serializer.validated_data['shipping_address'],
        )

        return Response(
            OrderResponseSerializer(order).data,
            status=status.HTTP_201_CREATED
        )
```

## Repository Pattern (Optional)

```python
# repositories/order_repository.py
from typing import Optional
from django.db.models import QuerySet

from apps.orders.models import Order


class OrderRepository:
    """
    Repository for Order data access.
    """

    def get_by_id(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        try:
            return Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return None

    def get_user_orders(self, user_id: str) -> QuerySet[Order]:
        """Get all orders for a user."""
        return Order.objects.filter(
            user_id=user_id
        ).select_related(
            'user'
        ).prefetch_related(
            'items', 'items__product'
        ).order_by('-created_at')

    def get_pending_orders(self) -> QuerySet[Order]:
        """Get all pending orders."""
        return Order.objects.filter(
            status='pending'
        ).select_related('user')

    def save(self, order: Order) -> Order:
        """Save order."""
        order.save()
        return order
```

## Mixin Patterns

### Model Mixins

```python
# core/models/mixins.py
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedMixin(models.Model):
    """Add created_at and updated_at fields."""

    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Add soft delete capability."""

    deleted_at = models.DateTimeField(_('deleted at'), null=True, blank=True)

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        from django.utils import timezone
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)


class AuditMixin(models.Model):
    """Add audit fields."""

    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='+',
    )

    class Meta:
        abstract = True
```

### Serializer Mixins

```python
# core/serializers/mixins.py
from rest_framework import serializers


class AuditSerializerMixin:
    """Include audit information in response."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if hasattr(instance, 'created_by') and instance.created_by:
            data['created_by'] = {
                'id': str(instance.created_by.id),
                'name': instance.created_by.get_full_name(),
            }
        return data


class DynamicFieldsMixin:
    """Allow dynamic field selection via query params."""

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
```

## Best Practices

1. **Keep apps focused** - Single responsibility per app
2. **Use services for business logic** - Keep views thin
3. **Prefer composition over inheritance** - Use mixins
4. **Explicit is better than implicit** - Clear dependencies
5. **Test at the right level** - Unit for services, integration for views
