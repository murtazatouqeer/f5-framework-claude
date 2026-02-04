# Django QuerySet Patterns Skill

## Overview

Efficient QuerySet patterns, custom managers, and optimization techniques.

## Custom Manager and QuerySet

```python
from django.db import models
from django.db.models import QuerySet, Q, F, Count, Sum, Avg
from django.utils import timezone


class ProductQuerySet(QuerySet):
    """Custom QuerySet for Product model."""

    def active(self):
        """Filter active products only."""
        return self.filter(status='active', deleted_at__isnull=True)

    def in_stock(self):
        """Filter products that are in stock."""
        return self.filter(stock__gt=0)

    def by_category(self, category_id):
        """Filter by category."""
        return self.filter(category_id=category_id)

    def price_range(self, min_price=None, max_price=None):
        """Filter by price range."""
        qs = self
        if min_price is not None:
            qs = qs.filter(price__gte=min_price)
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        return qs

    def with_discount(self):
        """Filter products with active discount."""
        return self.filter(discount_percent__gt=0)

    def popular(self, limit=10):
        """Get most popular products by order count."""
        return self.annotate(
            order_count=Count('order_items')
        ).order_by('-order_count')[:limit]

    def with_category(self):
        """Prefetch category relation."""
        return self.select_related('category')

    def with_tags(self):
        """Prefetch tags relation."""
        return self.prefetch_related('tags')

    def with_reviews(self):
        """Prefetch reviews with stats."""
        return self.prefetch_related('reviews').annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews')
        )

    def search(self, query):
        """Full-text search across name and description."""
        return self.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()


class ProductManager(models.Manager):
    """Custom manager for Product model."""

    def get_queryset(self):
        return ProductQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def in_stock(self):
        return self.get_queryset().in_stock()

    def get_featured(self):
        """Get featured products for homepage."""
        return self.active().in_stock().filter(
            is_featured=True
        ).with_category()[:12]

    def get_by_slug(self, slug):
        """Get product by slug with all relations."""
        return self.get_queryset().with_category().with_tags().get(slug=slug)
```

## Query Optimization

### Select Related (ForeignKey, OneToOne)

```python
# Bad - N+1 queries
orders = Order.objects.all()
for order in orders:
    print(order.user.name)  # Each access hits DB

# Good - 1 query with JOIN
orders = Order.objects.select_related('user').all()
for order in orders:
    print(order.user.name)  # No additional queries

# Multiple relations
orders = Order.objects.select_related(
    'user',
    'user__profile',
    'shipping_address',
    'billing_address'
).all()
```

### Prefetch Related (ManyToMany, Reverse FK)

```python
# Bad - N+1 queries
orders = Order.objects.all()
for order in orders:
    for item in order.items.all():  # Each order hits DB
        print(item.product.name)

# Good - 2 queries total
orders = Order.objects.prefetch_related('items').all()

# With nested prefetch
from django.db.models import Prefetch

orders = Order.objects.prefetch_related(
    Prefetch('items', queryset=OrderItem.objects.select_related('product')),
    'items__product__category'
).all()

# Filtered prefetch
orders = Order.objects.prefetch_related(
    Prefetch(
        'items',
        queryset=OrderItem.objects.filter(quantity__gt=1),
        to_attr='multiple_items'  # Access as order.multiple_items
    )
).all()
```

### Only and Defer

```python
# Only load specific fields
products = Product.objects.only('id', 'name', 'price').all()

# Defer loading of specific fields
products = Product.objects.defer('description', 'metadata').all()

# Combined with relations
products = Product.objects.select_related('category').only(
    'id', 'name', 'price',
    'category__id', 'category__name'
).all()
```

## Aggregation Patterns

```python
from django.db.models import Count, Sum, Avg, Max, Min, F, Value
from django.db.models.functions import Coalesce, TruncMonth


# Basic aggregations
stats = Order.objects.aggregate(
    total_orders=Count('id'),
    total_revenue=Sum('total'),
    avg_order_value=Avg('total'),
    max_order=Max('total'),
    min_order=Min('total')
)

# Annotation (per-object aggregation)
customers = User.objects.annotate(
    order_count=Count('orders'),
    total_spent=Coalesce(Sum('orders__total'), Value(0)),
    avg_order=Avg('orders__total')
).filter(order_count__gt=0).order_by('-total_spent')

# Group by with values
monthly_revenue = Order.objects.filter(
    status='completed'
).annotate(
    month=TruncMonth('created_at')
).values('month').annotate(
    revenue=Sum('total'),
    order_count=Count('id')
).order_by('month')

# Conditional aggregation
from django.db.models import Case, When, IntegerField

orders = Order.objects.aggregate(
    pending=Count(Case(When(status='pending', then=1))),
    completed=Count(Case(When(status='completed', then=1))),
    cancelled=Count(Case(When(status='cancelled', then=1))),
)
```

## Complex Queries

### Subqueries

```python
from django.db.models import Subquery, OuterRef

# Latest order per customer
latest_orders = Order.objects.filter(
    user=OuterRef('pk')
).order_by('-created_at')

customers = User.objects.annotate(
    latest_order_date=Subquery(latest_orders.values('created_at')[:1]),
    latest_order_total=Subquery(latest_orders.values('total')[:1])
)

# Exists subquery
from django.db.models import Exists

active_orders = Order.objects.filter(
    user=OuterRef('pk'),
    status='active'
)

customers_with_active = User.objects.annotate(
    has_active_order=Exists(active_orders)
).filter(has_active_order=True)
```

### Window Functions

```python
from django.db.models import Window
from django.db.models.functions import Rank, RowNumber, DenseRank

# Rank products by sales within category
products = Product.objects.annotate(
    sales_rank=Window(
        expression=Rank(),
        partition_by=[F('category')],
        order_by=F('total_sales').desc()
    )
)

# Running total
orders = Order.objects.annotate(
    running_total=Window(
        expression=Sum('total'),
        order_by=F('created_at').asc()
    )
)
```

### Raw Queries (when needed)

```python
# Raw SQL for complex queries
products = Product.objects.raw('''
    SELECT p.*,
           COALESCE(SUM(oi.quantity), 0) as total_sold
    FROM products p
    LEFT JOIN order_items oi ON p.id = oi.product_id
    GROUP BY p.id
    ORDER BY total_sold DESC
    LIMIT 10
''')

# Execute raw SQL
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute('''
        UPDATE products
        SET stock = stock - %s
        WHERE id = %s AND stock >= %s
    ''', [quantity, product_id, quantity])

    if cursor.rowcount == 0:
        raise InsufficientStockError()
```

## Bulk Operations

```python
# Bulk create
products = [
    Product(name=f'Product {i}', price=10.00)
    for i in range(1000)
]
Product.objects.bulk_create(products, batch_size=100)

# Bulk update
Product.objects.filter(category='electronics').update(
    discount_percent=F('discount_percent') + 10
)

# Bulk update with different values
from django.db.models import Case, When

Product.objects.filter(id__in=product_ids).update(
    status=Case(
        When(stock=0, then=Value('out_of_stock')),
        When(stock__lt=10, then=Value('low_stock')),
        default=Value('in_stock')
    )
)

# Bulk update with list of objects (Django 4.0+)
products = Product.objects.filter(category='electronics')
for product in products:
    product.price = product.price * 1.1

Product.objects.bulk_update(products, ['price'], batch_size=100)
```

## Best Practices

1. **Always use select_related/prefetch_related** - Avoid N+1
2. **Use only() for large models** - Reduce memory usage
3. **Index filtered fields** - Check query plans
4. **Use exists() over count()** - For boolean checks
5. **Use update() for bulk updates** - Avoid loading objects
6. **Iterator for large querysets** - Reduce memory
7. **Explain queries in development** - queryset.explain()
