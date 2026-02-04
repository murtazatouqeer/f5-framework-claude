# Django Form Validation Skill

## Overview

Django model and form validation patterns for data integrity.

## Model Validation

```python
from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import (
    MinValueValidator,
    MaxValueValidator,
    MinLengthValidator,
    RegexValidator,
)
from django.utils.translation import gettext_lazy as _


class Product(models.Model):
    """Product with comprehensive validation."""

    name = models.CharField(
        max_length=255,
        validators=[MinLengthValidator(3)]
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{2,4}-\d{4,8}$',
                message=_('SKU must be in format XX-0000')
            )
        ]
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    discount_percent = models.IntegerField(
        default=0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100)
        ]
    )
    stock = models.PositiveIntegerField(default=0)
    min_order_quantity = models.PositiveIntegerField(default=1)
    max_order_quantity = models.PositiveIntegerField(default=100)

    def clean(self):
        """Model-level validation."""
        super().clean()
        errors = {}

        # Cross-field validation
        if self.min_order_quantity > self.max_order_quantity:
            errors['min_order_quantity'] = _(
                'Minimum order quantity cannot exceed maximum.'
            )

        # Business logic validation
        if self.discount_percent > 0 and self.price < Decimal('10.00'):
            errors['discount_percent'] = _(
                'Discount not available for products under $10.'
            )

        # SKU format based on category
        if hasattr(self, 'category') and self.category:
            expected_prefix = self.category.sku_prefix
            if not self.sku.startswith(expected_prefix):
                errors['sku'] = _(
                    f'SKU must start with {expected_prefix} for this category.'
                )

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Ensure validation runs on save."""
        self.full_clean()
        super().save(*args, **kwargs)
```

## Form Validation

```python
from django import forms
from django.core.exceptions import ValidationError


class OrderForm(forms.ModelForm):
    """Order form with validation."""

    class Meta:
        model = Order
        fields = ['product', 'quantity', 'shipping_address', 'notes']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_quantity(self):
        """Validate quantity against product constraints."""
        quantity = self.cleaned_data['quantity']
        product = self.cleaned_data.get('product')

        if product:
            if quantity < product.min_order_quantity:
                raise ValidationError(
                    _('Minimum order quantity is %(min)s.'),
                    params={'min': product.min_order_quantity}
                )

            if quantity > product.max_order_quantity:
                raise ValidationError(
                    _('Maximum order quantity is %(max)s.'),
                    params={'max': product.max_order_quantity}
                )

            if quantity > product.stock:
                raise ValidationError(
                    _('Only %(stock)s items available in stock.'),
                    params={'stock': product.stock}
                )

        return quantity

    def clean(self):
        """Cross-field validation."""
        cleaned_data = super().clean()

        # Check user's order limit
        if self.user:
            pending_orders = Order.objects.filter(
                user=self.user,
                status='pending'
            ).count()

            if pending_orders >= 5:
                raise ValidationError(
                    _('You have too many pending orders. '
                      'Please complete existing orders first.')
                )

        return cleaned_data


class RegistrationForm(forms.Form):
    """User registration form."""

    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    terms_accepted = forms.BooleanField()

    def clean_email(self):
        """Check email uniqueness."""
        email = self.cleaned_data['email'].lower()

        if User.objects.filter(email=email).exists():
            raise ValidationError(
                _('This email is already registered.')
            )

        return email

    def clean(self):
        """Validate password match."""
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError({
                'password2': _('Passwords do not match.')
            })

        return cleaned_data
```

## Custom Validators

```python
from django.core.validators import BaseValidator
from django.utils.deconstruct import deconstructible


@deconstructible
class FileSizeValidator(BaseValidator):
    """Validate file size."""

    message = _('File size must be under %(limit_value)s MB.')
    code = 'file_too_large'

    def __init__(self, max_size_mb):
        self.max_size_mb = max_size_mb
        super().__init__(max_size_mb)

    def compare(self, file_size, max_size_mb):
        return file_size > max_size_mb * 1024 * 1024

    def clean(self, x):
        return x.size if hasattr(x, 'size') else 0


@deconstructible
class ImageDimensionValidator:
    """Validate image dimensions."""

    def __init__(self, min_width=None, min_height=None,
                 max_width=None, max_height=None):
        self.min_width = min_width
        self.min_height = min_height
        self.max_width = max_width
        self.max_height = max_height

    def __call__(self, image):
        from PIL import Image

        img = Image.open(image)
        width, height = img.size

        errors = []

        if self.min_width and width < self.min_width:
            errors.append(f'Image width must be at least {self.min_width}px.')

        if self.min_height and height < self.min_height:
            errors.append(f'Image height must be at least {self.min_height}px.')

        if self.max_width and width > self.max_width:
            errors.append(f'Image width must not exceed {self.max_width}px.')

        if self.max_height and height > self.max_height:
            errors.append(f'Image height must not exceed {self.max_height}px.')

        if errors:
            raise ValidationError(errors)


# Usage
class ProductImage(models.Model):
    image = models.ImageField(
        upload_to='products/',
        validators=[
            FileSizeValidator(5),  # 5MB max
            ImageDimensionValidator(
                min_width=200,
                min_height=200,
                max_width=4000,
                max_height=4000
            )
        ]
    )
```

## Async Validation

```python
# For validation requiring external services

class AsyncValidationMixin:
    """Mixin for async validation results."""

    def clean(self):
        cleaned_data = super().clean()

        # Queue async validation (e.g., address verification)
        validation_task = validate_address_async.delay(
            cleaned_data.get('address')
        )

        # Store task ID for later checking
        cleaned_data['_validation_task_id'] = validation_task.id

        return cleaned_data


# Check result before processing
def process_order(form):
    if form.is_valid():
        task_id = form.cleaned_data.get('_validation_task_id')
        if task_id:
            result = AsyncResult(task_id)
            if not result.ready():
                result.wait(timeout=5)

            if not result.successful():
                raise ValidationError('Address validation failed.')
```

## Best Practices

1. **Validate in model** - Data integrity at database level
2. **Use clean() for cross-field** - Related field validation
3. **Custom validators** - Reusable validation logic
4. **Meaningful messages** - User-friendly error messages
5. **Call full_clean()** - Ensure validation on save
6. **Handle None values** - Check before validation
7. **Use deconstructible** - For migration-safe validators
