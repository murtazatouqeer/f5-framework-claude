# DRF Serializer Patterns Skill

## Overview

Comprehensive validation and transformation patterns for Django REST Framework serializers.

## Field-Level Validation

```python
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
import re


class UserSerializer(serializers.ModelSerializer):
    """Serializer with field-level validation."""

    class Meta:
        model = User
        fields = ['email', 'username', 'phone', 'age']

    def validate_email(self, value):
        """Validate email format and uniqueness."""
        # Normalize email
        value = value.lower().strip()

        # Check domain blacklist
        domain = value.split('@')[1]
        if domain in ['tempmail.com', 'throwaway.com']:
            raise serializers.ValidationError(
                _('Disposable email addresses are not allowed.')
            )

        return value

    def validate_username(self, value):
        """Validate username format."""
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError(
                _('Username can only contain letters, numbers, and underscores.')
            )

        if len(value) < 3:
            raise serializers.ValidationError(
                _('Username must be at least 3 characters.')
            )

        return value.lower()

    def validate_phone(self, value):
        """Validate phone number format."""
        # Remove non-numeric characters
        cleaned = re.sub(r'\D', '', value)

        if len(cleaned) not in [10, 11]:
            raise serializers.ValidationError(
                _('Invalid phone number format.')
            )

        return cleaned

    def validate_age(self, value):
        """Validate age range."""
        if value < 13:
            raise serializers.ValidationError(
                _('Must be at least 13 years old.')
            )
        if value > 120:
            raise serializers.ValidationError(
                _('Please enter a valid age.')
            )
        return value
```

## Object-Level Validation

```python
class OrderSerializer(serializers.ModelSerializer):
    """Serializer with cross-field validation."""

    class Meta:
        model = Order
        fields = ['start_date', 'end_date', 'quantity', 'unit_price', 'discount']

    def validate(self, attrs):
        """Cross-field validation."""
        # Date range validation
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': _('End date must be after start date.')
            })

        # Business logic validation
        quantity = attrs.get('quantity', 0)
        discount = attrs.get('discount', 0)

        if discount > 0 and quantity < 10:
            raise serializers.ValidationError({
                'discount': _('Discount only available for orders of 10+ items.')
            })

        # Maximum discount validation
        unit_price = attrs.get('unit_price', 0)
        max_discount = unit_price * quantity * 0.3  # 30% max

        if discount > max_discount:
            raise serializers.ValidationError({
                'discount': _('Maximum discount is 30% of order total.')
            })

        return attrs
```

## Unique Validation with Context

```python
class ProductSerializer(serializers.ModelSerializer):
    """Handle unique validation during updates."""

    class Meta:
        model = Product
        fields = ['sku', 'name', 'category']

    def validate_sku(self, value):
        """Validate SKU uniqueness, excluding current instance."""
        queryset = Product.objects.filter(sku=value)

        # Exclude current instance during update
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                _('Product with this SKU already exists.')
            )

        return value.upper()

    def validate(self, attrs):
        """Validate unique together constraint."""
        name = attrs.get('name')
        category = attrs.get('category')

        if name and category:
            queryset = Product.objects.filter(name=name, category=category)

            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                raise serializers.ValidationError(
                    _('Product with this name already exists in this category.')
                )

        return attrs
```

## Conditional Validation

```python
class PaymentSerializer(serializers.Serializer):
    """Validation based on payment type."""

    payment_type = serializers.ChoiceField(choices=['card', 'bank', 'wallet'])
    card_number = serializers.CharField(required=False)
    card_expiry = serializers.CharField(required=False)
    card_cvv = serializers.CharField(required=False)
    bank_account = serializers.CharField(required=False)
    wallet_id = serializers.CharField(required=False)

    def validate(self, attrs):
        payment_type = attrs.get('payment_type')

        if payment_type == 'card':
            required_fields = ['card_number', 'card_expiry', 'card_cvv']
            for field in required_fields:
                if not attrs.get(field):
                    raise serializers.ValidationError({
                        field: _('This field is required for card payments.')
                    })

            # Validate card number (Luhn algorithm)
            if not self._validate_luhn(attrs['card_number']):
                raise serializers.ValidationError({
                    'card_number': _('Invalid card number.')
                })

        elif payment_type == 'bank':
            if not attrs.get('bank_account'):
                raise serializers.ValidationError({
                    'bank_account': _('Bank account is required.')
                })

        elif payment_type == 'wallet':
            if not attrs.get('wallet_id'):
                raise serializers.ValidationError({
                    'wallet_id': _('Wallet ID is required.')
                })

        return attrs

    def _validate_luhn(self, number):
        """Luhn algorithm for card validation."""
        digits = [int(d) for d in str(number) if d.isdigit()]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]

        total = sum(odd_digits)
        for d in even_digits:
            total += sum(divmod(d * 2, 10))

        return total % 10 == 0
```

## Custom Validators

```python
from rest_framework.validators import UniqueValidator, UniqueTogetherValidator
from django.core.validators import RegexValidator


# Reusable validators
class PhoneValidator:
    """Validate phone number format."""

    def __call__(self, value):
        pattern = r'^\+?[1-9]\d{9,14}$'
        if not re.match(pattern, value):
            raise serializers.ValidationError(
                _('Enter a valid phone number.')
            )


class PasswordStrengthValidator:
    """Validate password strength."""

    def __init__(self, min_length=8):
        self.min_length = min_length

    def __call__(self, value):
        errors = []

        if len(value) < self.min_length:
            errors.append(f'Password must be at least {self.min_length} characters.')

        if not re.search(r'[A-Z]', value):
            errors.append('Password must contain at least one uppercase letter.')

        if not re.search(r'[a-z]', value):
            errors.append('Password must contain at least one lowercase letter.')

        if not re.search(r'\d', value):
            errors.append('Password must contain at least one number.')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
            errors.append('Password must contain at least one special character.')

        if errors:
            raise serializers.ValidationError(errors)


# Usage
class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(validators=[
        UniqueValidator(queryset=User.objects.all())
    ])
    phone = serializers.CharField(validators=[PhoneValidator()])
    password = serializers.CharField(validators=[PasswordStrengthValidator()])
```

## Nested Validation

```python
class AddressSerializer(serializers.Serializer):
    """Nested address serializer with validation."""

    street = serializers.CharField(max_length=255)
    city = serializers.CharField(max_length=100)
    state = serializers.CharField(max_length=100)
    postal_code = serializers.CharField(max_length=20)
    country = serializers.CharField(max_length=2)

    def validate_postal_code(self, value):
        country = self.initial_data.get('country', '')

        if country == 'US':
            if not re.match(r'^\d{5}(-\d{4})?$', value):
                raise serializers.ValidationError(
                    _('Invalid US postal code format.')
                )
        elif country == 'VN':
            if not re.match(r'^\d{6}$', value):
                raise serializers.ValidationError(
                    _('Invalid Vietnam postal code format.')
                )

        return value


class OrderCreateSerializer(serializers.Serializer):
    """Order with nested address validation."""

    items = ItemSerializer(many=True, min_length=1)
    shipping_address = AddressSerializer()
    billing_address = AddressSerializer(required=False)
    same_as_shipping = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if not attrs.get('same_as_shipping') and not attrs.get('billing_address'):
            raise serializers.ValidationError({
                'billing_address': _('Billing address is required.')
            })

        return attrs
```

## Best Practices

1. **Validate early** - Catch errors before processing
2. **Return meaningful errors** - Include field name and message
3. **Normalize data** - Lowercase emails, strip whitespace
4. **Use custom validators** - Reusable validation logic
5. **Cross-field validation** - Use validate() method
6. **Context awareness** - Handle create vs update differently
7. **Internationalize** - Use gettext for messages
