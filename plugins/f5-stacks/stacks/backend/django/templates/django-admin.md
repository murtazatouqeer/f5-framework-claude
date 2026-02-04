# Django Admin Template

## Overview

Template for generating Django admin configurations with customizations.

## Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MODEL_NAME` | Model to configure | `Product` |
| `LIST_DISPLAY` | Fields in list view | `['name', 'status']` |
| `LIST_FILTER` | Filter sidebar | `['status', 'created_at']` |
| `SEARCH_FIELDS` | Searchable fields | `['name', 'sku']` |
| `INLINES` | Inline related models | See below |
| `FIELDSETS` | Form field grouping | See below |

## Base Template

```python
# apps/{{APP_NAME}}/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum

from apps.{{APP_NAME}}.models import {{MODEL_NAME}}
{% for inline in INLINES %}
from apps.{{inline.app}}.models import {{inline.model}}
{% endfor %}


{% for inline in INLINES %}
class {{inline.model}}Inline(admin.{{inline.type}}):
    """Inline for {{inline.model}}."""

    model = {{inline.model}}
    extra = {{inline.extra|default:0}}
    {% if inline.fields %}
    fields = {{inline.fields}}
    {% endif %}
    {% if inline.readonly_fields %}
    readonly_fields = {{inline.readonly_fields}}
    {% endif %}
    {% if inline.show_change_link %}
    show_change_link = True
    {% endif %}


{% endfor %}
@admin.register({{MODEL_NAME}})
class {{MODEL_NAME}}Admin(admin.ModelAdmin):
    """Admin configuration for {{MODEL_NAME}}."""

    # List view
    list_display = {{LIST_DISPLAY}}
    list_display_links = {{LIST_DISPLAY_LINKS|default:"['id', 'name']"}}
    list_filter = {{LIST_FILTER}}
    list_per_page = {{LIST_PER_PAGE|default:25}}
    list_editable = {{LIST_EDITABLE|default:"[]"}}

    # Search
    search_fields = {{SEARCH_FIELDS}}
    search_help_text = 'Search by {{SEARCH_FIELDS|join:", "}}'

    # Ordering
    ordering = {{ORDERING|default:"['-created_at']"}}

    # Detail view
    {% if FIELDSETS %}
    fieldsets = (
        {% for fieldset in FIELDSETS %}
        ('{{fieldset.title}}', {
            'fields': {{fieldset.fields}},
            {% if fieldset.classes %}'classes': {{fieldset.classes}},{% endif %}
            {% if fieldset.description %}'description': '{{fieldset.description}}',{% endif %}
        }),
        {% endfor %}
    )
    {% else %}
    fields = {{FIELDS}}
    {% endif %}

    readonly_fields = {{READONLY_FIELDS|default:"['id', 'created_at', 'updated_at']"}}

    # Relationships
    {% if AUTOCOMPLETE_FIELDS %}
    autocomplete_fields = {{AUTOCOMPLETE_FIELDS}}
    {% endif %}
    {% if RAW_ID_FIELDS %}
    raw_id_fields = {{RAW_ID_FIELDS}}
    {% endif %}
    {% if FILTER_HORIZONTAL %}
    filter_horizontal = {{FILTER_HORIZONTAL}}
    {% endif %}

    # Inlines
    {% if INLINES %}
    inlines = [{% for inline in INLINES %}{{inline.model}}Inline, {% endfor %}]
    {% endif %}

    # Actions
    actions = ['{{ACTIONS|join:"', '"}}']

    # Dates
    date_hierarchy = '{{DATE_HIERARCHY|default:"created_at"}}'

    {% for custom_display in CUSTOM_DISPLAYS %}
    @admin.display(description='{{custom_display.description}}')
    def {{custom_display.name}}(self, obj):
        """{{custom_display.help_text}}"""
        {{custom_display.implementation}}

    {% endfor %}
    {% for custom_action in CUSTOM_ACTIONS %}
    @admin.action(description='{{custom_action.description}}')
    def {{custom_action.name}}(self, request, queryset):
        """{{custom_action.help_text}}"""
        {{custom_action.implementation}}

    {% endfor %}
    def get_queryset(self, request):
        """Optimize queryset."""
        qs = super().get_queryset(request)
        {% if SELECT_RELATED %}
        qs = qs.select_related({{SELECT_RELATED}})
        {% endif %}
        {% if PREFETCH_RELATED %}
        qs = qs.prefetch_related({{PREFETCH_RELATED}})
        {% endif %}
        {% if ANNOTATIONS %}
        qs = qs.annotate(
            {% for annotation in ANNOTATIONS %}
            {{annotation.name}}={{annotation.expression}},
            {% endfor %}
        )
        {% endif %}
        return qs

    {% if SAVE_MODEL %}
    def save_model(self, request, obj, form, change):
        """Custom save logic."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    {% endif %}

    {% if HAS_CHANGE_PERMISSION %}
    def has_change_permission(self, request, obj=None):
        """Custom change permission."""
        if obj and obj.status == 'locked':
            return False
        return super().has_change_permission(request, obj)
    {% endif %}
```

## Custom Display Fields

### Status with Color Badge

```python
@admin.display(description='Status')
def colored_status(self, obj):
    """Display status with color."""
    colors = {
        'active': 'green',
        'pending': 'orange',
        'inactive': 'red',
    }
    color = colors.get(obj.status, 'gray')
    return format_html(
        '<span style="background-color: {}; color: white; padding: 3px 10px; '
        'border-radius: 3px;">{}</span>',
        color,
        obj.get_status_display()
    )
```

### Link to Related Object

```python
@admin.display(description='User')
def user_link(self, obj):
    """Link to related user."""
    if obj.user:
        url = reverse('admin:users_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    return '-'
```

### Thumbnail Image

```python
@admin.display(description='Image')
def thumbnail(self, obj):
    """Display thumbnail image."""
    if obj.image:
        return format_html(
            '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
            obj.image.url
        )
    return '-'
```

### Computed Value

```python
@admin.display(description='Total Items', ordering='item_count')
def total_items(self, obj):
    """Display computed item count."""
    return obj.item_count  # From annotation
```

### Boolean Icon

```python
@admin.display(description='Active', boolean=True)
def is_active_display(self, obj):
    """Display boolean as icon."""
    return obj.is_active
```

## Custom Actions

### Bulk Status Change

```python
@admin.action(description='Mark selected as active')
def make_active(self, request, queryset):
    """Activate selected items."""
    updated = queryset.update(status='active')
    self.message_user(request, f'{updated} items activated.')

@admin.action(description='Mark selected as inactive')
def make_inactive(self, request, queryset):
    """Deactivate selected items."""
    updated = queryset.update(status='inactive')
    self.message_user(request, f'{updated} items deactivated.')
```

### Export Action

```python
import csv
from django.http import HttpResponse

@admin.action(description='Export to CSV')
def export_csv(self, request, queryset):
    """Export selected to CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="export.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'Name', 'Status', 'Created'])

    for obj in queryset:
        writer.writerow([obj.id, obj.name, obj.status, obj.created_at])

    return response
```

### Send Notification

```python
@admin.action(description='Send notification')
def send_notification(self, request, queryset):
    """Send notification to related users."""
    for obj in queryset:
        send_notification_task.delay(obj.user_id, 'Your item was selected.')
    self.message_user(request, f'Notifications sent to {queryset.count()} users.')
```

## Inline Patterns

### Tabular Inline

```python
class OrderItemInline(admin.TabularInline):
    """Inline for order items."""

    model = OrderItem
    extra = 0
    fields = ['product', 'quantity', 'unit_price', 'line_total']
    readonly_fields = ['line_total']
    autocomplete_fields = ['product']

    def line_total(self, obj):
        return obj.quantity * obj.unit_price
```

### Stacked Inline

```python
class AddressInline(admin.StackedInline):
    """Inline for addresses."""

    model = Address
    extra = 0
    max_num = 5
    fieldsets = (
        (None, {
            'fields': ('type', 'is_default')
        }),
        ('Address', {
            'fields': ('street', 'city', 'state', 'postal_code', 'country')
        }),
    )
```

## Usage Example

```yaml
input:
  APP_NAME: products
  MODEL_NAME: Product
  LIST_DISPLAY: "['id', 'name', 'colored_status', 'price', 'category', 'created_at']"
  LIST_FILTER: "['status', 'category', 'created_at']"
  SEARCH_FIELDS: "['name', 'sku', 'description']"
  FIELDSETS:
    - title: Basic Info
      fields: "['name', 'sku', 'description']"
    - title: Pricing
      fields: "['price', 'discount_price', 'cost']"
    - title: Classification
      fields: "['category', 'tags', 'status']"
    - title: Metadata
      fields: "['created_at', 'updated_at', 'created_by']"
      classes: "['collapse']"
  AUTOCOMPLETE_FIELDS: "['category']"
  FILTER_HORIZONTAL: "['tags']"
  INLINES:
    - model: ProductImage
      type: TabularInline
      app: products
      fields: "['image', 'alt_text', 'order']"
      extra: 1
  CUSTOM_ACTIONS:
    - name: make_active
      description: "Mark as active"
      implementation: "queryset.update(status='active')"
```

## Generated Output Example

```python
# apps/products/admin.py
from django.contrib import admin
from django.utils.html import format_html

from apps.products.models import Product, ProductImage


class ProductImageInline(admin.TabularInline):
    """Inline for product images."""

    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'order']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product."""

    # List view
    list_display = ['id', 'name', 'colored_status', 'price', 'category', 'created_at']
    list_display_links = ['id', 'name']
    list_filter = ['status', 'category', 'created_at']
    list_per_page = 25

    # Search
    search_fields = ['name', 'sku', 'description']

    # Ordering
    ordering = ['-created_at']

    # Detail view
    fieldsets = (
        ('Basic Info', {
            'fields': ['name', 'sku', 'description'],
        }),
        ('Pricing', {
            'fields': ['price', 'discount_price', 'cost'],
        }),
        ('Classification', {
            'fields': ['category', 'tags', 'status'],
        }),
        ('Metadata', {
            'fields': ['created_at', 'updated_at', 'created_by'],
            'classes': ['collapse'],
        }),
    )

    readonly_fields = ['id', 'created_at', 'updated_at']
    autocomplete_fields = ['category']
    filter_horizontal = ['tags']

    inlines = [ProductImageInline]
    actions = ['make_active', 'make_inactive', 'export_csv']
    date_hierarchy = 'created_at'

    @admin.display(description='Status')
    def colored_status(self, obj):
        """Display colored status badge."""
        colors = {
            'active': 'green',
            'draft': 'orange',
            'inactive': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.action(description='Mark as active')
    def make_active(self, request, queryset):
        queryset.update(status='active')

    @admin.action(description='Mark as inactive')
    def make_inactive(self, request, queryset):
        queryset.update(status='inactive')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
```

## Best Practices

1. **Optimize queries** - use select_related/prefetch_related
2. **Add search fields** - improve findability
3. **Use date_hierarchy** - for time-based models
4. **Group with fieldsets** - organize complex forms
5. **Custom displays** - make status visual
6. **Bulk actions** - common operations
7. **Autocomplete** - for related fields with many options
