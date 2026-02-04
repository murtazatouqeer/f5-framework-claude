# Django Migrations Skill

## Overview

Best practices for Django database migrations, data migrations, and deployment strategies.

## Migration Commands

```bash
# Create migrations
python manage.py makemigrations
python manage.py makemigrations app_name

# Apply migrations
python manage.py migrate
python manage.py migrate app_name

# Show migration status
python manage.py showmigrations
python manage.py showmigrations app_name

# SQL preview
python manage.py sqlmigrate app_name 0001

# Rollback to specific migration
python manage.py migrate app_name 0001

# Rollback all migrations for app
python manage.py migrate app_name zero
```

## Data Migrations

```python
# migrations/0002_populate_defaults.py
from django.db import migrations


def populate_defaults(apps, schema_editor):
    """Forward migration: populate default data."""
    Category = apps.get_model('products', 'Category')

    defaults = [
        {'name': 'Electronics', 'slug': 'electronics'},
        {'name': 'Clothing', 'slug': 'clothing'},
        {'name': 'Books', 'slug': 'books'},
    ]

    for data in defaults:
        Category.objects.get_or_create(
            slug=data['slug'],
            defaults={'name': data['name']}
        )


def remove_defaults(apps, schema_editor):
    """Reverse migration: remove default data."""
    Category = apps.get_model('products', 'Category')
    Category.objects.filter(
        slug__in=['electronics', 'clothing', 'books']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            populate_defaults,
            remove_defaults
        ),
    ]
```

## Complex Schema Changes

### Add Non-Nullable Field

```python
# Step 1: Add nullable field
# migrations/0002_add_field_nullable.py
class Migration(migrations.Migration):
    dependencies = [('app', '0001_initial')]
    operations = [
        migrations.AddField(
            model_name='product',
            name='sku',
            field=models.CharField(max_length=50, null=True),
        ),
    ]


# Step 2: Populate data
# migrations/0003_populate_sku.py
def populate_sku(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.filter(sku__isnull=True):
        product.sku = f'SKU-{product.id}'
        product.save(update_fields=['sku'])


class Migration(migrations.Migration):
    dependencies = [('app', '0002_add_field_nullable')]
    operations = [
        migrations.RunPython(populate_sku, migrations.RunPython.noop),
    ]


# Step 3: Make non-nullable
# migrations/0004_make_sku_required.py
class Migration(migrations.Migration):
    dependencies = [('app', '0003_populate_sku')]
    operations = [
        migrations.AlterField(
            model_name='product',
            name='sku',
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
```

### Rename Field Safely

```python
# migrations/0002_rename_field.py
class Migration(migrations.Migration):
    dependencies = [('app', '0001_initial')]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='title',
            new_name='name',
        ),
    ]
```

### Change Field Type

```python
# For compatible types (e.g., CharField -> TextField)
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(),
        ),
    ]


# For incompatible types (create new, migrate, remove old)
# Step 1: Add new field
# Step 2: Data migration to copy/transform
# Step 3: Remove old field
# Step 4: Rename new field (optional)
```

## Index Migrations

```python
# Add index
class Migration(migrations.Migration):
    operations = [
        migrations.AddIndex(
            model_name='product',
            index=models.Index(
                fields=['category', 'status'],
                name='idx_product_cat_status'
            ),
        ),
    ]


# Concurrent index (PostgreSQL, large tables)
from django.contrib.postgres.operations import AddIndexConcurrently

class Migration(migrations.Migration):
    atomic = False  # Required for concurrent operations

    operations = [
        AddIndexConcurrently(
            model_name='product',
            index=models.Index(
                fields=['created_at'],
                name='idx_product_created'
            ),
        ),
    ]
```

## Zero-Downtime Migrations

### Safe Operations

```python
# These are generally safe:
- AddField (nullable or with default)
- AddIndex (CONCURRENTLY on PostgreSQL)
- CreateModel
- RunPython (read-only or idempotent)
```

### Dangerous Operations

```python
# These require care:
- RemoveField (ensure app doesn't reference)
- AlterField (may lock table)
- RenameField (may break app)
- RemoveIndex (may slow queries)
- DeleteModel (ensure no references)
```

### Multi-Step Deployment

```python
# For renaming a field:

# Deploy 1: Add new field, keep old
# migrations/0002_add_new_field.py
AddField(name='new_name', null=True)

# migrations/0003_copy_data.py
RunPython(copy_old_to_new)

# Update app code to use both fields (write both, read new)
# Deploy 2: Update app code

# migrations/0004_make_required.py
AlterField(name='new_name', null=False)

# migrations/0005_remove_old.py (after confirming new field works)
RemoveField(name='old_name')
```

## Migration Testing

```python
# tests/test_migrations.py
import pytest
from django.core.management import call_command
from django_test_migrations.contrib.unittest_case import MigratorTestCase


class TestMigrations(MigratorTestCase):
    """Test migration correctness."""

    migrate_from = ('products', '0001_initial')
    migrate_to = ('products', '0002_add_sku')

    def prepare(self):
        """Set up test data before migration."""
        Product = self.old_state.apps.get_model('products', 'Product')
        Product.objects.create(name='Test Product', price=10.00)

    def test_migration_forward(self):
        """Test forward migration."""
        Product = self.new_state.apps.get_model('products', 'Product')
        product = Product.objects.get(name='Test Product')

        # SKU should be populated
        assert product.sku is not None
        assert product.sku.startswith('SKU-')


# Test migration reversibility
def test_migration_reversible():
    """Ensure migrations can be reversed."""
    call_command('migrate', 'products', '0001')
    call_command('migrate', 'products')
```

## Squashing Migrations

```bash
# Squash migrations 0001-0010
python manage.py squashmigrations app_name 0001 0010

# After verifying squashed migration works:
# 1. Remove old migrations
# 2. Update replaces = [...] in squashed migration
# 3. Run makemigrations --check to verify
```

## Best Practices

1. **One change per migration** - Easier to debug and rollback
2. **Always test migrations** - Both forward and backward
3. **Use atomic=False for concurrent ops** - PostgreSQL only
4. **Data migrations should be idempotent** - Safe to run multiple times
5. **Check migration SQL** - sqlmigrate before applying
6. **Version control migrations** - Never modify committed migrations
7. **Squash periodically** - Keep migration count manageable
8. **Plan zero-downtime** - Multi-step for breaking changes
