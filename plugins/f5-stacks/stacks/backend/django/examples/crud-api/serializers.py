# apps/products/serializers.py
"""
Product serializers with action-specific variants.

REQ-001: Product CRUD API
"""
from rest_framework import serializers

from apps.products.models import Product, ProductStatus


class ProductListSerializer(serializers.ModelSerializer):
    """Minimal serializer for list views."""

    category_name = serializers.CharField(
        source='category.name',
        read_only=True,
        default=None
    )

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'price',
            'stock',
            'status',
            'category_name',
            'image',
            'created_at',
        ]
        read_only_fields = fields


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""

    category_name = serializers.CharField(
        source='category.name',
        read_only=True,
        default=None
    )
    tags = serializers.SlugRelatedField(
        slug_field='name',
        many=True,
        read_only=True
    )
    is_active = serializers.BooleanField(read_only=True)
    profit_margin = serializers.FloatField(read_only=True)

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'description',
            'price',
            'cost',
            'stock',
            'status',
            'category',
            'category_name',
            'tags',
            'image',
            'metadata',
            'is_active',
            'profit_margin',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_by',
            'created_at',
            'updated_at',
        ]


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products."""

    class Meta:
        model = Product
        fields = [
            'name',
            'sku',
            'description',
            'price',
            'cost',
            'stock',
            'status',
            'category',
            'tags',
            'image',
            'metadata',
        ]
        extra_kwargs = {
            'name': {'required': True, 'min_length': 2, 'max_length': 255},
            'sku': {'required': True},
            'price': {'required': True, 'min_value': 0},
            'stock': {'min_value': 0},
        }

    def validate_sku(self, value):
        """Validate SKU format and uniqueness."""
        # Ensure uppercase
        value = value.upper()

        # Check format
        if not value.replace('-', '').replace('_', '').isalnum():
            raise serializers.ValidationError(
                "SKU must contain only alphanumeric characters, hyphens, and underscores."
            )

        # Check uniqueness
        if Product.objects.filter(sku=value).exists():
            raise serializers.ValidationError("Product with this SKU already exists.")

        return value

    def validate_price(self, value):
        """Validate price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate(self, attrs):
        """Object-level validation."""
        cost = attrs.get('cost')
        price = attrs.get('price')

        if cost and price and cost > price:
            raise serializers.ValidationError({
                'cost': 'Cost cannot be greater than selling price.'
            })

        return attrs


class ProductUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating products."""

    class Meta:
        model = Product
        fields = [
            'name',
            'description',
            'price',
            'cost',
            'stock',
            'status',
            'category',
            'tags',
            'image',
            'metadata',
        ]
        extra_kwargs = {
            'name': {'required': False, 'min_length': 2},
            'price': {'required': False, 'min_value': 0},
        }

    def validate_price(self, value):
        """Validate price is positive."""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value

    def validate(self, attrs):
        """Object-level validation."""
        cost = attrs.get('cost', self.instance.cost if self.instance else None)
        price = attrs.get('price', self.instance.price if self.instance else None)

        if cost and price and cost > price:
            raise serializers.ValidationError({
                'cost': 'Cost cannot be greater than selling price.'
            })

        return attrs


class BulkDeleteSerializer(serializers.Serializer):
    """Serializer for bulk delete action."""

    ids = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1,
        max_length=100
    )

    def validate_ids(self, value):
        """Validate IDs exist."""
        existing = set(
            Product.objects.filter(id__in=value).values_list('id', flat=True)
        )
        missing = set(value) - existing

        if missing:
            raise serializers.ValidationError(
                f"Products not found: {list(missing)}"
            )

        return value
