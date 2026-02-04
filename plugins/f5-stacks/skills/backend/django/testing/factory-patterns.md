# Factory Boy Patterns Skill

## Overview

Factory Boy patterns for creating test data in Django applications.

## Basic Factory

```python
# tests/factories/user.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = User
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: f'user{n}@example.com')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password after creation."""
        password = extracted or 'testpass123'
        self.set_password(password)
        if create:
            self.save()

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        """Override create to use create_user."""
        manager = cls._get_manager(model_class)
        return manager.create_user(*args, **kwargs)
```

## Complex Factory with Relationships

```python
# tests/factories/order.py
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from decimal import Decimal

from apps.orders.models import Order, OrderItem
from apps.products.models import Product
from .user import UserFactory


class ProductFactory(DjangoModelFactory):
    """Factory for Product model."""

    class Meta:
        model = Product

    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('paragraph')
    sku = factory.Sequence(lambda n: f'SKU-{n:06d}')
    price = fuzzy.FuzzyDecimal(10.00, 500.00, precision=2)
    stock = fuzzy.FuzzyInteger(0, 100)
    status = 'active'


class OrderFactory(DjangoModelFactory):
    """Factory for Order model."""

    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = 'pending'
    subtotal = Decimal('0.00')
    tax = Decimal('0.00')
    shipping_cost = Decimal('10.00')
    total = Decimal('0.00')

    @factory.lazy_attribute
    def shipping_address(self):
        """Generate shipping address."""
        fake = factory.Faker._get_faker()
        return {
            'street': fake.street_address(),
            'city': fake.city(),
            'state': fake.state(),
            'postal_code': fake.postcode(),
            'country': 'US',
        }

    @factory.post_generation
    def items(self, create, extracted, **kwargs):
        """Add order items after creation."""
        if not create:
            return

        if extracted:
            # Items were passed explicitly
            for item in extracted:
                OrderItemFactory(order=self, **item)
        else:
            # Create default items
            count = kwargs.get('count', 2)
            for _ in range(count):
                OrderItemFactory(order=self)

        # Recalculate totals
        self.recalculate_totals()


class OrderItemFactory(DjangoModelFactory):
    """Factory for OrderItem model."""

    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = fuzzy.FuzzyInteger(1, 5)

    @factory.lazy_attribute
    def unit_price(self):
        """Use product price as unit price."""
        return self.product.price
```

## Traits for Variations

```python
class OrderFactory(DjangoModelFactory):
    """Factory with traits for different order states."""

    class Meta:
        model = Order

    user = factory.SubFactory(UserFactory)
    status = 'pending'
    total = fuzzy.FuzzyDecimal(50.00, 500.00, precision=2)

    class Params:
        # Traits for different states
        completed = factory.Trait(
            status='completed',
            completed_at=factory.Faker('date_time_this_month'),
        )
        cancelled = factory.Trait(
            status='cancelled',
            cancelled_at=factory.Faker('date_time_this_month'),
            cancellation_reason='Customer request',
        )
        paid = factory.Trait(
            status='paid',
            payment_id=factory.Sequence(lambda n: f'pay_{n}'),
            paid_at=factory.Faker('date_time_this_month'),
        )
        high_value = factory.Trait(
            total=fuzzy.FuzzyDecimal(1000.00, 5000.00, precision=2),
        )
        with_discount = factory.Trait(
            discount_percent=fuzzy.FuzzyInteger(10, 30),
        )


# Usage
pending_order = OrderFactory()
completed_order = OrderFactory(completed=True)
high_value_paid = OrderFactory(high_value=True, paid=True)
```

## Lazy Attributes

```python
class ProductFactory(DjangoModelFactory):
    """Factory with lazy attributes."""

    class Meta:
        model = Product

    name = factory.Faker('sentence', nb_words=3)
    price = fuzzy.FuzzyDecimal(10.00, 500.00, precision=2)
    discount_percent = 0

    @factory.lazy_attribute
    def slug(self):
        """Generate slug from name."""
        from django.utils.text import slugify
        return slugify(self.name)

    @factory.lazy_attribute
    def discounted_price(self):
        """Calculate discounted price."""
        if self.discount_percent > 0:
            discount = self.price * self.discount_percent / 100
            return self.price - discount
        return self.price

    @factory.lazy_attribute
    def sku(self):
        """Generate SKU based on category."""
        category_prefix = getattr(self, 'category', None)
        if category_prefix and hasattr(category_prefix, 'code'):
            return f'{category_prefix.code}-{factory.Sequence(lambda n: n)}'
        return f'GEN-{factory.Sequence(lambda n: n)}'
```

## Batch Creation

```python
# Create multiple instances
users = UserFactory.create_batch(10)
orders = OrderFactory.create_batch(5, user=users[0])

# Create with variations
products = [
    ProductFactory(status='active'),
    ProductFactory(status='inactive'),
    ProductFactory(status='draft'),
]

# Create related batch
def create_order_with_items(user, item_count=3):
    """Create order with specified number of items."""
    order = OrderFactory(user=user)
    OrderItemFactory.create_batch(item_count, order=order)
    order.recalculate_totals()
    return order
```

## Factory Inheritance

```python
class BaseProductFactory(DjangoModelFactory):
    """Base factory for products."""

    class Meta:
        model = Product
        abstract = True

    name = factory.Faker('sentence', nb_words=3)
    price = fuzzy.FuzzyDecimal(10.00, 100.00, precision=2)
    status = 'active'


class ElectronicsFactory(BaseProductFactory):
    """Factory for electronics products."""

    category = factory.LazyAttribute(lambda _: Category.objects.get(slug='electronics'))
    warranty_months = fuzzy.FuzzyInteger(12, 36)


class ClothingFactory(BaseProductFactory):
    """Factory for clothing products."""

    category = factory.LazyAttribute(lambda _: Category.objects.get(slug='clothing'))
    sizes = factory.LazyAttribute(lambda _: ['S', 'M', 'L', 'XL'])
    colors = factory.LazyAttribute(lambda _: ['Black', 'White', 'Blue'])
```

## Using Factories in Tests

```python
import pytest
from tests.factories import UserFactory, OrderFactory, ProductFactory


@pytest.fixture
def user():
    """Create test user."""
    return UserFactory()


@pytest.fixture
def order(user):
    """Create order for user."""
    return OrderFactory(user=user, items__count=3)


@pytest.fixture
def products():
    """Create multiple products."""
    return ProductFactory.create_batch(10)


class TestOrderService:
    """Test order service with factories."""

    def test_create_order(self, user, products):
        """Test order creation."""
        items = [
            {'product_id': str(products[0].id), 'quantity': 2},
            {'product_id': str(products[1].id), 'quantity': 1},
        ]

        order = OrderService().create_order(user=user, items=items)

        assert order.items.count() == 2
        assert order.total > 0

    def test_cancel_order(self, order):
        """Test order cancellation."""
        OrderService().cancel_order(order)

        order.refresh_from_db()
        assert order.status == 'cancelled'

    @pytest.mark.parametrize('status,can_cancel', [
        ('pending', True),
        ('processing', True),
        ('shipped', False),
        ('delivered', False),
    ])
    def test_can_cancel_by_status(self, user, status, can_cancel):
        """Test cancellation rules by status."""
        order = OrderFactory(user=user, status=status)

        assert order.can_cancel == can_cancel
```

## Best Practices

1. **Use sequences** - Unique values per instance
2. **Use SubFactory** - Related objects
3. **Use traits** - Common variations
4. **Use lazy_attribute** - Computed values
5. **Post-generation hooks** - After-creation setup
6. **Don't over-create** - Only what's needed
7. **Use build() for unit tests** - Skip database
