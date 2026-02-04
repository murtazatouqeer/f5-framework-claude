# apps/products/models.py
"""
Product model with soft delete and custom managers.

REQ-001: Product CRUD API
"""
import uuid
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that filters out soft-deleted records."""

    def delete(self):
        """Soft delete all records in queryset."""
        return self.update(deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently delete all records."""
        return super().delete()

    def alive(self):
        """Return only non-deleted records."""
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        """Return only deleted records."""
        return self.filter(deleted_at__isnull=False)


class SoftDeleteManager(models.Manager):
    """Manager that excludes soft-deleted records by default."""

    def get_queryset(self):
        """Return queryset filtered to alive records."""
        return SoftDeleteQuerySet(self.model, using=self._db).alive()


class ProductStatus(models.TextChoices):
    """Product status choices."""

    DRAFT = 'draft', 'Draft'
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ARCHIVED = 'archived', 'Archived'


class Product(models.Model):
    """
    Product model representing items in catalog.

    Attributes:
        name: Product display name
        sku: Stock keeping unit (unique identifier)
        description: Detailed product description
        price: Current selling price
        cost: Cost price for profit calculation
        stock: Available inventory quantity
        status: Publication status
        category: Product category reference
        tags: Product tags for filtering
        image: Primary product image
        metadata: Additional JSON data
        created_by: User who created the product
        created_at: Creation timestamp
        updated_at: Last update timestamp
        deleted_at: Soft delete timestamp
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    # Basic info
    name = models.CharField(
        max_length=255,
        db_index=True
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True
    )
    description = models.TextField(
        blank=True,
        default=''
    )

    # Pricing
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Inventory
    stock = models.PositiveIntegerField(
        default=0
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=ProductStatus.choices,
        default=ProductStatus.DRAFT,
        db_index=True
    )

    # Relationships
    category = models.ForeignKey(
        'categories.Category',
        on_delete=models.PROTECT,
        related_name='products',
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(
        'tags.Tag',
        related_name='products',
        blank=True
    )

    # Media
    image = models.ImageField(
        upload_to='products/',
        null=True,
        blank=True
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True
    )

    # Audit fields
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_products'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True
    )

    # Managers
    objects = SoftDeleteManager.from_queryset(SoftDeleteQuerySet)()
    all_objects = models.Manager()

    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(
                fields=['status', 'created_at'],
                name='idx_product_status_created'
            ),
            models.Index(
                fields=['category', 'status'],
                name='idx_product_category_status'
            ),
        ]
        verbose_name = 'Product'
        verbose_name_plural = 'Products'

    def __str__(self):
        return self.name

    def delete(self, using=None, keep_parents=False):
        """Soft delete the product."""
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at', 'updated_at'])

    def hard_delete(self, using=None, keep_parents=False):
        """Permanently delete the product."""
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        """Restore a soft-deleted product."""
        self.deleted_at = None
        self.save(update_fields=['deleted_at', 'updated_at'])

    @property
    def is_active(self):
        """Check if product is active and in stock."""
        return self.status == ProductStatus.ACTIVE and self.stock > 0

    @property
    def profit_margin(self):
        """Calculate profit margin percentage."""
        if self.cost and self.cost > 0:
            return ((self.price - self.cost) / self.cost) * 100
        return None
