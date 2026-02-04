# apps/products/filters.py
"""
Product filters using django-filter.

REQ-001: Product CRUD API
"""
import django_filters
from django.db.models import Q

from apps.products.models import Product, ProductStatus


class ProductFilter(django_filters.FilterSet):
    """
    Filter for Product queryset.

    Supported filters:
        status: Exact match on status
        category: Filter by category ID
        price_min: Minimum price (inclusive)
        price_max: Maximum price (inclusive)
        in_stock: Products with stock > 0
        created_after: Created on or after date
        created_before: Created on or before date
        has_image: Products with/without images
        tags: Filter by tag IDs (multiple allowed)
    """

    # Status filter
    status = django_filters.ChoiceFilter(
        choices=ProductStatus.choices
    )

    # Category filter
    category = django_filters.UUIDFilter(
        field_name='category_id'
    )

    # Price range filters
    price_min = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='gte',
        label='Minimum price'
    )
    price_max = django_filters.NumberFilter(
        field_name='price',
        lookup_expr='lte',
        label='Maximum price'
    )

    # Stock filter
    in_stock = django_filters.BooleanFilter(
        method='filter_in_stock',
        label='In stock'
    )

    # Date range filters
    created_after = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='gte',
        label='Created after'
    )
    created_before = django_filters.DateTimeFilter(
        field_name='created_at',
        lookup_expr='lte',
        label='Created before'
    )

    # Image filter
    has_image = django_filters.BooleanFilter(
        method='filter_has_image',
        label='Has image'
    )

    # Tags filter (multiple)
    tags = django_filters.BaseInFilter(
        field_name='tags__id',
        label='Tag IDs'
    )

    # Full-text search (alternative to SearchFilter)
    q = django_filters.CharFilter(
        method='filter_search',
        label='Search'
    )

    class Meta:
        model = Product
        fields = [
            'status',
            'category',
            'price_min',
            'price_max',
            'in_stock',
            'created_after',
            'created_before',
            'has_image',
            'tags',
            'q',
        ]

    def filter_in_stock(self, queryset, name, value):
        """Filter products by stock availability."""
        if value is True:
            return queryset.filter(stock__gt=0)
        elif value is False:
            return queryset.filter(stock=0)
        return queryset

    def filter_has_image(self, queryset, name, value):
        """Filter products by image presence."""
        if value is True:
            return queryset.exclude(image='').exclude(image__isnull=True)
        elif value is False:
            return queryset.filter(Q(image='') | Q(image__isnull=True))
        return queryset

    def filter_search(self, queryset, name, value):
        """Full-text search across multiple fields."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(sku__icontains=value) |
                Q(description__icontains=value)
            )
        return queryset


class ProductOrderingFilter(django_filters.OrderingFilter):
    """Custom ordering filter with additional options."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('fields', [
            ('name', 'name'),
            ('price', 'price'),
            ('stock', 'stock'),
            ('created_at', 'created'),
            ('updated_at', 'updated'),
        ])
        super().__init__(*args, **kwargs)
