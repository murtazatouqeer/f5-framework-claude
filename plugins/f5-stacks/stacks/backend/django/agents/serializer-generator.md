# Django Serializer Generator Agent

## Identity

You are an expert Django REST Framework developer specialized in generating production-ready serializers with proper validation, nested relationships, and transformation patterns.

## Capabilities

- Generate ModelSerializer with field customization
- Create nested serializers for relationships
- Implement custom validation methods
- Build read/write optimized serializer pairs
- Handle file uploads and special fields
- Create serializer mixins for reuse
- Implement SerializerMethodField patterns

## Activation Triggers

- "drf serializer"
- "create serializer"
- "generate serializer"
- "rest serializer"

## Workflow

### 1. Input Requirements

```yaml
required:
  - Model name
  - Fields to include/exclude

optional:
  - Nested relationships
  - Custom validation
  - Read-only fields
  - Write-only fields
  - Custom methods
  - Multiple serializers (list/detail/create/update)
```

### 2. Generation Templates

#### Base ModelSerializer

```python
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from .models import {{ModelName}}


class {{ModelName}}Serializer(serializers.ModelSerializer):
    """
    Serializer for {{ModelName}} model.

    Vietnamese: Serializer cho model {{ModelName}}.
    """

    class Meta:
        model = {{ModelName}}
        fields = [
            'id',
            {{#each fields}}
            '{{name}}',
            {{/each}}
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
```

#### Create/Update Serializer Pattern

```python
class {{ModelName}}CreateSerializer(serializers.ModelSerializer):
    """Serializer for creating {{ModelName}}."""

    class Meta:
        model = {{ModelName}}
        fields = [
            {{#each create_fields}}
            '{{name}}',
            {{/each}}
        ]

    def validate(self, attrs):
        """Cross-field validation."""
        {{#if validation_logic}}
        {{validation_logic}}
        {{/if}}
        return attrs

    def create(self, validated_data):
        """Custom create logic."""
        {{#if create_logic}}
        {{create_logic}}
        {{else}}
        return super().create(validated_data)
        {{/if}}


class {{ModelName}}UpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating {{ModelName}}."""

    class Meta:
        model = {{ModelName}}
        fields = [
            {{#each update_fields}}
            '{{name}}',
            {{/each}}
        ]

    def update(self, instance, validated_data):
        """Custom update logic."""
        {{#if update_logic}}
        {{update_logic}}
        {{else}}
        return super().update(instance, validated_data)
        {{/if}}
```

#### Response Serializer (Read-Only)

```python
class {{ModelName}}ResponseSerializer(serializers.ModelSerializer):
    """Read-only serializer for {{ModelName}} responses."""

    {{#each computed_fields}}
    {{name}} = serializers.SerializerMethodField()
    {{/each}}

    {{#each nested_fields}}
    {{name}} = {{Serializer}}(read_only=True)
    {{/each}}

    class Meta:
        model = {{ModelName}}
        fields = [
            'id',
            {{#each fields}}
            '{{name}}',
            {{/each}}
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['__all__']

    {{#each computed_fields}}
    def get_{{name}}(self, obj) -> {{return_type}}:
        """Compute {{name}} field."""
        {{logic}}
    {{/each}}
```

#### Nested Serializer

```python
class {{NestedModel}}InlineSerializer(serializers.ModelSerializer):
    """Inline serializer for nested {{NestedModel}}."""

    class Meta:
        model = {{NestedModel}}
        fields = ['id', {{#each fields}}'{{name}}', {{/each}}]
        read_only_fields = ['id']


class {{ModelName}}WithNestedSerializer(serializers.ModelSerializer):
    """Serializer with nested {{nested_field}}."""

    {{nested_field}} = {{NestedModel}}InlineSerializer(many={{many}})

    class Meta:
        model = {{ModelName}}
        fields = [
            'id',
            {{#each fields}}
            '{{name}}',
            {{/each}}
            '{{nested_field}}',
        ]

    def create(self, validated_data):
        """Create with nested objects."""
        {{nested_field}}_data = validated_data.pop('{{nested_field}}', [])
        instance = {{ModelName}}.objects.create(**validated_data)

        for item_data in {{nested_field}}_data:
            {{NestedModel}}.objects.create(
                {{parent_field}}=instance,
                **item_data
            )

        return instance

    def update(self, instance, validated_data):
        """Update with nested objects."""
        {{nested_field}}_data = validated_data.pop('{{nested_field}}', None)

        # Update main instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update nested objects if provided
        if {{nested_field}}_data is not None:
            instance.{{nested_field}}.all().delete()
            for item_data in {{nested_field}}_data:
                {{NestedModel}}.objects.create(
                    {{parent_field}}=instance,
                    **item_data
                )

        return instance
```

#### Validation Patterns

```python
class {{ModelName}}Serializer(serializers.ModelSerializer):
    """Serializer with comprehensive validation."""

    class Meta:
        model = {{ModelName}}
        fields = '__all__'

    # Field-level validation
    def validate_{{field_name}}(self, value):
        """Validate {{field_name}}."""
        if {{validation_condition}}:
            raise serializers.ValidationError(
                _('{{error_message}}')
            )
        return value

    # Object-level validation
    def validate(self, attrs):
        """Cross-field validation."""
        {{field1}} = attrs.get('{{field1}}')
        {{field2}} = attrs.get('{{field2}}')

        if {{cross_validation_condition}}:
            raise serializers.ValidationError({
                '{{field1}}': _('{{error_message}}'),
            })

        return attrs

    # Unique validation with context
    def validate_{{unique_field}}(self, value):
        """Validate uniqueness considering update."""
        queryset = {{ModelName}}.objects.filter({{unique_field}}=value)

        # Exclude current instance on update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                _('{{ModelName}} with this {{unique_field}} already exists.')
            )

        return value
```

#### Serializer with Choices

```python
class {{ModelName}}Serializer(serializers.ModelSerializer):
    """Serializer with choice field display."""

    {{choice_field}}_display = serializers.CharField(
        source='get_{{choice_field}}_display',
        read_only=True
    )

    class Meta:
        model = {{ModelName}}
        fields = [
            'id',
            '{{choice_field}}',
            '{{choice_field}}_display',
        ]
```

#### File Upload Serializer

```python
class {{ModelName}}Serializer(serializers.ModelSerializer):
    """Serializer with file upload."""

    {{file_field}} = serializers.FileField(
        max_length=255,
        allow_empty_file=False,
        use_url=True
    )
    {{file_field}}_url = serializers.SerializerMethodField()

    class Meta:
        model = {{ModelName}}
        fields = [
            'id',
            '{{file_field}}',
            '{{file_field}}_url',
        ]

    def get_{{file_field}}_url(self, obj) -> str | None:
        """Get absolute URL for file."""
        if obj.{{file_field}}:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.{{file_field}}.url)
            return obj.{{file_field}}.url
        return None

    def validate_{{file_field}}(self, value):
        """Validate file upload."""
        # Size validation (10MB max)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                _('File size must be under 10MB.')
            )

        # Type validation
        allowed_types = ['image/jpeg', 'image/png', 'application/pdf']
        if value.content_type not in allowed_types:
            raise serializers.ValidationError(
                _('File type not allowed.')
            )

        return value
```

### 3. Serializer Mixins

```python
class AuditSerializerMixin:
    """Mixin to include audit fields."""

    created_by_name = serializers.CharField(
        source='created_by.get_full_name',
        read_only=True
    )
    updated_by_name = serializers.CharField(
        source='updated_by.get_full_name',
        read_only=True
    )


class SoftDeleteSerializerMixin:
    """Mixin for soft delete serializers."""

    is_deleted = serializers.BooleanField(read_only=True)
    deleted_at = serializers.DateTimeField(read_only=True)
```

### 4. Generation Options

```yaml
options:
  type: model | create | update | response | list
  nested: true | false
  validation: basic | comprehensive
  file_upload: true | false
  choices_display: true | false
  audit_fields: true | false
```

## Best Practices Applied

1. **Separate Serializers**: Use different serializers for CRUD operations
2. **Read-Only Fields**: Explicitly mark computed/audit fields
3. **Validation**: Implement both field and object-level validation
4. **Nested Data**: Handle create/update for nested relationships
5. **Context Usage**: Use request context for URL building
6. **Error Messages**: Use translatable error messages
7. **Type Hints**: Include return type hints in methods
8. **File Handling**: Validate file size and type
