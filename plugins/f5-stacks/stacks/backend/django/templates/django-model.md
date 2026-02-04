# Django Model Template

## Overview

Template for generating Django ORM models with best practices.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MODEL_NAME` | Model class name (PascalCase) | `Product` |
| `TABLE_NAME` | Database table name | `products` |
| `FIELDS` | List of field definitions | See below |
| `SOFT_DELETE` | Enable soft delete pattern | `true` |
| `TIMESTAMPS` | Add created_at/updated_at | `true` |
| `UUID_PK` | Use UUID primary key | `true` |

## Base Template

```python
# apps/{{APP_NAME}}/models/{{MODEL_NAME_SNAKE}}.py
import uuid
from django.db import models
from django.utils import timezone
{% if SOFT_DELETE %}

from apps.core.models import SoftDeleteManager, SoftDeleteQuerySet
{% endif %}


{% if BASE_MODEL %}
class {{MODEL_NAME}}({{BASE_MODEL}}):
{% else %}
class {{MODEL_NAME}}(models.Model):
{% endif %}
    """
    {{MODEL_DESCRIPTION}}

    Attributes:
    {% for field in FIELDS %}
        {{field.name}}: {{field.description}}
    {% endfor %}
    """

    {% if UUID_PK %}
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    {% endif %}

    {% for field in FIELDS %}
    {{field.name}} = models.{{field.type}}(
        {% if field.verbose_name %}'{{field.verbose_name}}',{% endif %}
        {% for opt, val in field.options.items() %}
        {{opt}}={{val}},
        {% endfor %}
    )
    {% endfor %}

    {% if TIMESTAMPS %}
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    {% endif %}

    {% if SOFT_DELETE %}
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager.from_queryset(SoftDeleteQuerySet)()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        """Soft delete the instance."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the instance."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted instance."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])
    {% endif %}

    class Meta:
        db_table = '{{TABLE_NAME}}'
        {% if ORDERING %}
        ordering = {{ORDERING}}
        {% endif %}
        {% if INDEXES %}
        indexes = [
            {% for index in INDEXES %}
            models.Index(fields={{index.fields}}, name='{{index.name}}'),
            {% endfor %}
        ]
        {% endif %}
        {% if CONSTRAINTS %}
        constraints = [
            {% for constraint in CONSTRAINTS %}
            {{constraint}},
            {% endfor %}
        ]
        {% endif %}
        verbose_name = '{{VERBOSE_NAME}}'
        verbose_name_plural = '{{VERBOSE_NAME_PLURAL}}'

    def __str__(self):
        return {% if STR_FIELD %}self.{{STR_FIELD}}{% else %}f"{{MODEL_NAME}} {self.id}"{% endif %}

    {% if PROPERTIES %}
    {% for prop in PROPERTIES %}
    @property
    def {{prop.name}}(self):
        """{{prop.description}}"""
        {{prop.implementation}}

    {% endfor %}
    {% endif %}
```

## Field Type Reference

### Common Fields

```python
# String fields
name = models.CharField(max_length=255)
description = models.TextField(blank=True)
slug = models.SlugField(max_length=100, unique=True)

# Numeric fields
price = models.DecimalField(max_digits=10, decimal_places=2)
quantity = models.IntegerField(default=0)
rating = models.FloatField(null=True, blank=True)

# Boolean fields
is_active = models.BooleanField(default=True)
is_featured = models.BooleanField(default=False)

# Date/Time fields
published_at = models.DateTimeField(null=True, blank=True)
birth_date = models.DateField(null=True, blank=True)
duration = models.DurationField(null=True, blank=True)

# JSON fields
metadata = models.JSONField(default=dict, blank=True)
settings = models.JSONField(default=dict)

# File fields
image = models.ImageField(upload_to='images/', null=True, blank=True)
document = models.FileField(upload_to='documents/')

# Email/URL fields
email = models.EmailField(unique=True)
website = models.URLField(blank=True)
```

### Relationship Fields

```python
# ForeignKey (Many-to-One)
category = models.ForeignKey(
    'categories.Category',
    on_delete=models.PROTECT,
    related_name='products'
)

# OneToOneField
profile = models.OneToOneField(
    'users.User',
    on_delete=models.CASCADE,
    related_name='profile'
)

# ManyToManyField
tags = models.ManyToManyField(
    'tags.Tag',
    related_name='products',
    blank=True
)

# Self-referential
parent = models.ForeignKey(
    'self',
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='children'
)
```

## Usage Examples

### Basic Model

```yaml
input:
  MODEL_NAME: Product
  TABLE_NAME: products
  MODEL_DESCRIPTION: "Product in the catalog"
  UUID_PK: true
  TIMESTAMPS: true
  SOFT_DELETE: true
  STR_FIELD: name
  FIELDS:
    - name: name
      type: CharField
      options:
        max_length: 255
    - name: sku
      type: CharField
      options:
        max_length: 50
        unique: true
    - name: price
      type: DecimalField
      options:
        max_digits: 10
        decimal_places: 2
    - name: status
      type: CharField
      options:
        max_length: 20
        choices: "ProductStatus.choices"
        default: "'draft'"
```

### Model with Relationships

```yaml
input:
  MODEL_NAME: OrderItem
  TABLE_NAME: order_items
  UUID_PK: true
  TIMESTAMPS: true
  FIELDS:
    - name: order
      type: ForeignKey
      options:
        to: "'orders.Order'"
        on_delete: models.CASCADE
        related_name: "'items'"
    - name: product
      type: ForeignKey
      options:
        to: "'products.Product'"
        on_delete: models.PROTECT
    - name: quantity
      type: PositiveIntegerField
      options:
        default: 1
    - name: unit_price
      type: DecimalField
      options:
        max_digits: 10
        decimal_places: 2
  INDEXES:
    - fields: "['order', 'product']"
      name: idx_order_product
  CONSTRAINTS:
    - "models.UniqueConstraint(fields=['order', 'product'], name='unique_order_product')"
```

## Generated Output Example

```python
# apps/products/models/product.py
import uuid
from django.db import models
from django.utils import timezone

from apps.core.models import SoftDeleteManager, SoftDeleteQuerySet


class ProductStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'


class Product(models.Model):
    """
    Product in the catalog.

    Attributes:
        name: Product display name
        sku: Stock keeping unit (unique identifier)
        price: Product price
        status: Publication status
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)

    objects = SoftDeleteManager.from_queryset(SoftDeleteQuerySet)()
    all_objects = models.Manager()

    def delete(self, using=None, keep_parents=False):
        """Soft delete the instance."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the instance."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted instance."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='idx_status_created'),
        ]
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name
```

## Best Practices

1. **Always use UUID primary keys** for API-facing models
2. **Add indexes** for frequently queried fields
3. **Use soft delete** for audit-sensitive data
4. **Define `__str__`** for admin display
5. **Add `related_name`** to all relationships
6. **Use `PROTECT`** for critical references
7. **Add `db_index=True`** for filter/ordering fields
