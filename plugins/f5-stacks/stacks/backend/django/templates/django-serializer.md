# Django REST Framework Serializer Template

## Overview

Template for generating DRF serializers with validation and nested relationships.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `SERIALIZER_NAME` | Serializer class name | `ProductSerializer` |
| `MODEL_NAME` | Associated model | `Product` |
| `FIELDS` | Fields to include | `['id', 'name']` |
| `READ_ONLY_FIELDS` | Read-only fields | `['id', 'created_at']` |
| `NESTED_SERIALIZERS` | Nested relationships | See below |
| `VALIDATORS` | Custom validators | See below |

## Base Template

```python
# apps/{{APP_NAME}}/serializers/{{MODEL_NAME_SNAKE}}.py
from rest_framework import serializers
{% if NESTED_SERIALIZERS %}
{% for nested in NESTED_SERIALIZERS %}
from apps.{{nested.app}}.serializers import {{nested.serializer}}
{% endfor %}
{% endif %}

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}


class {{SERIALIZER_NAME}}(serializers.ModelSerializer):
    """
    Serializer for {{MODEL_NAME}}.

    {% if DESCRIPTION %}{{DESCRIPTION}}{% endif %}
    """

    {% for nested in NESTED_SERIALIZERS %}
    {{nested.field}} = {{nested.serializer}}({% if nested.many %}many=True, {% endif %}read_only={{nested.read_only}})
    {% endfor %}

    {% for computed in COMPUTED_FIELDS %}
    {{computed.name}} = serializers.{{computed.type}}({% if computed.source %}source='{{computed.source}}'{% endif %})
    {% endfor %}

    class Meta:
        model = {{MODEL_NAME}}
        fields = {{FIELDS}}
        read_only_fields = {{READ_ONLY_FIELDS}}
        {% if EXTRA_KWARGS %}
        extra_kwargs = {
            {% for field, kwargs in EXTRA_KWARGS.items() %}
            '{{field}}': {{kwargs}},
            {% endfor %}
        }
        {% endif %}

    {% for validator in VALIDATORS %}
    def validate_{{validator.field}}(self, value):
        """{{validator.description}}"""
        {{validator.implementation}}
        return value

    {% endfor %}
    {% if OBJECT_VALIDATORS %}
    def validate(self, attrs):
        """Object-level validation."""
        {% for obj_validator in OBJECT_VALIDATORS %}
        # {{obj_validator.description}}
        {{obj_validator.implementation}}
        {% endfor %}
        return attrs
    {% endif %}

    {% if CUSTOM_CREATE %}
    def create(self, validated_data):
        """Custom create logic."""
        {{CUSTOM_CREATE}}
    {% endif %}

    {% if CUSTOM_UPDATE %}
    def update(self, instance, validated_data):
        """Custom update logic."""
        {{CUSTOM_UPDATE}}
    {% endif %}
```

## Serializer Variants

### List Serializer (Minimal Fields)

```python
class {{MODEL_NAME}}ListSerializer(serializers.ModelSerializer):
    """Minimal serializer for list views."""

    class Meta:
        model = {{MODEL_NAME}}
        fields = ['id', 'name', '{{DISPLAY_FIELD}}', 'created_at']
        read_only_fields = fields
```

### Detail Serializer (All Fields)

```python
class {{MODEL_NAME}}DetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""

    {% for nested in NESTED_SERIALIZERS %}
    {{nested.field}} = {{nested.serializer}}({% if nested.many %}many=True{% endif %})
    {% endfor %}

    class Meta:
        model = {{MODEL_NAME}}
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
```

### Create Serializer (Write Fields)

```python
class {{MODEL_NAME}}CreateSerializer(serializers.ModelSerializer):
    """Serializer for creating {{MODEL_NAME}}."""

    class Meta:
        model = {{MODEL_NAME}}
        fields = {{CREATE_FIELDS}}
        extra_kwargs = {
            {% for field in REQUIRED_FIELDS %}
            '{{field}}': {'required': True},
            {% endfor %}
        }

    def create(self, validated_data):
        """Create with current user."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
```

### Update Serializer (Partial Updates)

```python
class {{MODEL_NAME}}UpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating {{MODEL_NAME}}."""

    class Meta:
        model = {{MODEL_NAME}}
        fields = {{UPDATE_FIELDS}}
        extra_kwargs = {
            {% for field in UPDATE_FIELDS %}
            '{{field}}': {'required': False},
            {% endfor %}
        }
```

## Validation Patterns

### Field-Level Validation

```python
def validate_email(self, value):
    """Validate email is unique."""
    if User.objects.filter(email=value).exists():
        raise serializers.ValidationError("Email already exists.")
    return value.lower()

def validate_price(self, value):
    """Validate price is positive."""
    if value <= 0:
        raise serializers.ValidationError("Price must be positive.")
    return value

def validate_status(self, value):
    """Validate status transition."""
    if self.instance and self.instance.status == 'completed':
        raise serializers.ValidationError("Cannot change completed status.")
    return value
```

### Object-Level Validation

```python
def validate(self, attrs):
    """Validate related fields."""
    start_date = attrs.get('start_date')
    end_date = attrs.get('end_date')

    if start_date and end_date and start_date > end_date:
        raise serializers.ValidationError({
            'end_date': 'End date must be after start date.'
        })

    return attrs
```

### Conditional Validation

```python
def validate(self, attrs):
    """Conditional validation based on type."""
    item_type = attrs.get('type')

    if item_type == 'physical':
        if not attrs.get('weight'):
            raise serializers.ValidationError({
                'weight': 'Weight required for physical items.'
            })
    elif item_type == 'digital':
        if not attrs.get('download_url'):
            raise serializers.ValidationError({
                'download_url': 'Download URL required for digital items.'
            })

    return attrs
```

## Nested Serializer Patterns

### Read-Only Nested

```python
class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'items', 'total', 'status']
```

### Writable Nested

```python
class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True)

    class Meta:
        model = Order
        fields = ['items', 'shipping_address']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)

        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        order.calculate_total()
        return order
```

### PrimaryKeyRelatedField

```python
class OrderCreateSerializer(serializers.ModelSerializer):
    product_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.filter(status='active'),
        write_only=True
    )

    class Meta:
        model = Order
        fields = ['product_ids', 'quantity']
```

## Usage Examples

### Product Serializer

```yaml
input:
  SERIALIZER_NAME: ProductSerializer
  MODEL_NAME: Product
  APP_NAME: products
  FIELDS: "['id', 'name', 'sku', 'price', 'status', 'category', 'created_at']"
  READ_ONLY_FIELDS: "['id', 'created_at']"
  NESTED_SERIALIZERS:
    - field: category
      serializer: CategorySerializer
      app: categories
      read_only: true
  VALIDATORS:
    - field: sku
      description: "Validate SKU format"
      implementation: |
        if not value.startswith('SKU-'):
            raise serializers.ValidationError("SKU must start with 'SKU-'")
```

## Generated Output Example

```python
# apps/products/serializers/product.py
from rest_framework import serializers

from apps.categories.serializers import CategorySerializer
from apps.products.models import Product


class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product.

    Handles product CRUD with category relationship.
    """

    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'price', 'status',
            'category', 'category_id', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
        extra_kwargs = {
            'name': {'required': True, 'min_length': 2},
            'price': {'required': True, 'min_value': 0},
        }

    def validate_sku(self, value):
        """Validate SKU format and uniqueness."""
        if not value.startswith('SKU-'):
            raise serializers.ValidationError("SKU must start with 'SKU-'")

        # Check uniqueness excluding current instance
        qs = Product.objects.filter(sku=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("SKU already exists.")

        return value.upper()

    def validate_price(self, value):
        """Validate price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class ProductListSerializer(serializers.ModelSerializer):
    """Minimal serializer for list views."""

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'sku', 'price', 'status', 'category_name']
        read_only_fields = fields


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating products."""

    class Meta:
        model = Product
        fields = ['name', 'sku', 'description', 'price', 'category', 'status']
        extra_kwargs = {
            'name': {'required': True},
            'sku': {'required': True},
            'price': {'required': True},
            'category': {'required': True},
        }

    def create(self, validated_data):
        """Create product with audit trail."""
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
```

## Best Practices

1. **Separate serializers** for list/detail/create/update
2. **Use read_only_fields** for computed properties
3. **Validate at field level** when possible
4. **Use source** for renamed fields
5. **Handle nested writes** explicitly in create/update
6. **Add extra_kwargs** for validation rules
7. **Document serializers** with docstrings
