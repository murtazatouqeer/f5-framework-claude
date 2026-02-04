# apps/products/admin.py
"""
Product admin configuration with custom displays and actions.

REQ-001: Product CRUD API
"""
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count

from apps.products.models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin configuration for Product model."""

    # List view configuration
    list_display = [
        'id',
        'name',
        'sku',
        'colored_status',
        'formatted_price',
        'stock_display',
        'category',
        'created_at',
    ]
    list_display_links = ['id', 'name']
    list_filter = [
        'status',
        'category',
        ('created_at', admin.DateFieldListFilter),
        ('stock', admin.EmptyFieldListFilter),
    ]
    list_per_page = 25
    list_editable = ['status']

    # Search configuration
    search_fields = ['name', 'sku', 'description']
    search_help_text = 'Search by name, SKU, or description'

    # Ordering
    ordering = ['-created_at']

    # Detail view configuration
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description'),
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'cost', 'stock'),
        }),
        ('Classification', {
            'fields': ('status', 'category', 'tags'),
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',),
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
        ('Audit Information', {
            'fields': ('id', 'created_by', 'created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['id', 'created_by', 'created_at', 'updated_at', 'deleted_at']

    # Relationships
    autocomplete_fields = ['category']
    filter_horizontal = ['tags']
    raw_id_fields = ['created_by']

    # Actions
    actions = ['make_active', 'make_inactive', 'mark_as_draft']

    # Date hierarchy
    date_hierarchy = 'created_at'

    @admin.display(description='Status')
    def colored_status(self, obj):
        """Display status with color badge."""
        colors = {
            'draft': '#6c757d',      # Gray
            'active': '#28a745',     # Green
            'inactive': '#dc3545',   # Red
            'archived': '#17a2b8',   # Cyan
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )

    @admin.display(description='Price')
    def formatted_price(self, obj):
        """Display formatted price."""
        return format_html(
            '<span style="font-family: monospace;">${:,.2f}</span>',
            obj.price
        )

    @admin.display(description='Stock')
    def stock_display(self, obj):
        """Display stock with color indicator."""
        if obj.stock == 0:
            color = '#dc3545'  # Red
            label = 'Out of Stock'
        elif obj.stock < 10:
            color = '#ffc107'  # Yellow
            label = f'{obj.stock} (Low)'
        else:
            color = '#28a745'  # Green
            label = str(obj.stock)

        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            label
        )

    @admin.action(description='Mark selected as Active')
    def make_active(self, request, queryset):
        """Activate selected products."""
        updated = queryset.filter(stock__gt=0).update(status='active')
        self.message_user(
            request,
            f'{updated} products activated. Products with 0 stock were skipped.'
        )

    @admin.action(description='Mark selected as Inactive')
    def make_inactive(self, request, queryset):
        """Deactivate selected products."""
        updated = queryset.update(status='inactive')
        self.message_user(request, f'{updated} products deactivated.')

    @admin.action(description='Mark selected as Draft')
    def mark_as_draft(self, request, queryset):
        """Set selected products to draft."""
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} products set to draft.')

    def get_queryset(self, request):
        """Optimize queryset with annotations."""
        return super().get_queryset(request).select_related(
            'category',
            'created_by'
        )

    def save_model(self, request, obj, form, change):
        """Set created_by on creation."""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
