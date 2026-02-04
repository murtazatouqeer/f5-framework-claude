# Django Model Patterns Skill

## Overview

Comprehensive patterns for Django ORM models including field types, relationships, and best practices.

## Base Model Pattern

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class BaseModel(models.Model):
    """
    Abstract base model with common fields.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
```

## Field Type Patterns

### String Fields

```python
# Short text (max 255 chars)
name = models.CharField(
    _('name'),
    max_length=255,
    db_index=True
)

# Long text
description = models.TextField(
    _('description'),
    blank=True,
    default=''
)

# Email
email = models.EmailField(
    _('email'),
    unique=True,
    db_index=True
)

# URL
website = models.URLField(
    _('website'),
    blank=True,
    default=''
)

# Slug (URL-friendly)
slug = models.SlugField(
    _('slug'),
    max_length=100,
    unique=True
)
```

### Numeric Fields

```python
# Integer
quantity = models.IntegerField(
    _('quantity'),
    default=0,
    validators=[MinValueValidator(0)]
)

# Positive Integer
stock = models.PositiveIntegerField(
    _('stock'),
    default=0
)

# Decimal (for money)
price = models.DecimalField(
    _('price'),
    max_digits=12,
    decimal_places=2,
    validators=[MinValueValidator(Decimal('0.00'))]
)

# Float (avoid for money)
weight = models.FloatField(
    _('weight'),
    null=True,
    blank=True
)
```

### Date/Time Fields

```python
# Date only
birth_date = models.DateField(
    _('birth date'),
    null=True,
    blank=True
)

# DateTime
scheduled_at = models.DateTimeField(
    _('scheduled at'),
    null=True,
    blank=True,
    db_index=True
)

# Time only
start_time = models.TimeField(
    _('start time'),
    null=True,
    blank=True
)

# Duration
duration = models.DurationField(
    _('duration'),
    null=True,
    blank=True
)
```

### Choice Fields

```python
class Status(models.TextChoices):
    DRAFT = 'draft', _('Draft')
    PENDING = 'pending', _('Pending')
    ACTIVE = 'active', _('Active')
    COMPLETED = 'completed', _('Completed')
    CANCELLED = 'cancelled', _('Cancelled')


status = models.CharField(
    _('status'),
    max_length=20,
    choices=Status.choices,
    default=Status.DRAFT,
    db_index=True
)
```

### JSON Field

```python
# Structured metadata
metadata = models.JSONField(
    _('metadata'),
    default=dict,
    blank=True
)

# With validation
from django.core.validators import validate_json

settings = models.JSONField(
    _('settings'),
    default=dict,
    validators=[validate_json],
    help_text=_('JSON object with configuration')
)
```

## Relationship Patterns

### ForeignKey (Many-to-One)

```python
# Standard FK
category = models.ForeignKey(
    'categories.Category',
    on_delete=models.PROTECT,  # Prevent deletion if referenced
    related_name='products',
    verbose_name=_('category')
)

# Nullable FK
assigned_to = models.ForeignKey(
    'users.User',
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='assigned_tasks',
    verbose_name=_('assigned to')
)

# Self-referential
parent = models.ForeignKey(
    'self',
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='children',
    verbose_name=_('parent')
)
```

### ManyToMany

```python
# Simple M2M
tags = models.ManyToManyField(
    'tags.Tag',
    related_name='products',
    blank=True,
    verbose_name=_('tags')
)

# M2M with through model
members = models.ManyToManyField(
    'users.User',
    through='TeamMembership',
    related_name='teams',
    verbose_name=_('members')
)


class TeamMembership(models.Model):
    """Through model for team membership."""

    team = models.ForeignKey(
        'Team',
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=50,
        choices=[
            ('member', 'Member'),
            ('admin', 'Admin'),
        ],
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['team', 'user']
```

### OneToOne

```python
# Profile pattern
profile = models.OneToOneField(
    'users.User',
    on_delete=models.CASCADE,
    related_name='profile',
    verbose_name=_('profile')
)
```

## Model Methods

```python
class Product(BaseModel):
    """Product model with computed properties and methods."""

    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = models.IntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = 'products'
        verbose_name = _('product')
        verbose_name_plural = _('products')
        indexes = [
            models.Index(fields=['name'], name='idx_product_name'),
            models.Index(fields=['created_at'], name='idx_product_created'),
        ]

    def __str__(self) -> str:
        return self.name

    # Computed property
    @property
    def discounted_price(self) -> Decimal:
        """Calculate price after discount."""
        if self.discount_percent > 0:
            discount = self.price * self.discount_percent / 100
            return self.price - discount
        return self.price

    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        return self.stock > 0

    # Instance method
    def reduce_stock(self, quantity: int) -> None:
        """Reduce stock by quantity."""
        if quantity > self.stock:
            raise ValueError('Insufficient stock')
        self.stock -= quantity
        self.save(update_fields=['stock'])

    # Clean method for validation
    def clean(self):
        """Validate model data."""
        if self.discount_percent < 0 or self.discount_percent > 100:
            raise ValidationError({
                'discount_percent': _('Discount must be between 0 and 100')
            })

    def save(self, *args, **kwargs):
        """Override save for additional logic."""
        self.full_clean()
        super().save(*args, **kwargs)
```

## Constraints and Indexes

```python
class Order(BaseModel):
    """Order with database constraints."""

    order_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=20)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'orders'
        indexes = [
            # Single field index
            models.Index(fields=['order_number']),

            # Composite index
            models.Index(
                fields=['status', 'created_at'],
                name='idx_order_status_date'
            ),

            # Partial index (PostgreSQL)
            models.Index(
                fields=['status'],
                name='idx_active_orders',
                condition=Q(status='active')
            ),
        ]
        constraints = [
            # Unique constraint
            models.UniqueConstraint(
                fields=['order_number'],
                name='unique_order_number'
            ),

            # Check constraint
            models.CheckConstraint(
                check=Q(total__gte=0),
                name='positive_total'
            ),

            # Unique together (composite)
            models.UniqueConstraint(
                fields=['user', 'external_id'],
                name='unique_user_external'
            ),
        ]
```

## Best Practices

1. **Use UUID for primary keys** - Better for distributed systems
2. **Always add verbose_name** - For admin and translations
3. **Index frequently queried fields** - Especially FKs and filters
4. **Use TextChoices for choices** - Type-safe and self-documenting
5. **Add db_index to FK fields** - Django doesn't auto-index FK
6. **Use PROTECT for critical FKs** - Prevent accidental deletion
7. **Validate in clean()** - Before saving to database
8. **Use update_fields** - When updating specific fields
