# tests/factories/product.py
"""
Factory Boy factories for Product tests.

REQ-001: Product CRUD API
"""
import factory
from factory import fuzzy
from factory.django import DjangoModelFactory
from decimal import Decimal

from apps.products.models import Product, ProductStatus
from tests.factories.user import UserFactory


class ProductFactory(DjangoModelFactory):
    """Factory for Product model."""

    class Meta:
        model = Product

    name = factory.Faker('sentence', nb_words=3)
    sku = factory.Sequence(lambda n: f'SKU-{n:06d}')
    description = factory.Faker('paragraph')
    price = fuzzy.FuzzyDecimal(10.00, 500.00, precision=2)
    cost = factory.LazyAttribute(lambda o: o.price * Decimal('0.6'))
    stock = fuzzy.FuzzyInteger(0, 100)
    status = ProductStatus.DRAFT
    created_by = factory.SubFactory(UserFactory)

    class Params:
        """Factory traits for common variations."""

        # Active product with stock
        active = factory.Trait(
            status=ProductStatus.ACTIVE,
            stock=fuzzy.FuzzyInteger(10, 100),
        )

        # Inactive product
        inactive = factory.Trait(
            status=ProductStatus.INACTIVE,
        )

        # Out of stock
        out_of_stock = factory.Trait(
            stock=0,
        )

        # High value product
        high_value = factory.Trait(
            price=fuzzy.FuzzyDecimal(500.00, 2000.00, precision=2),
        )

        # Low stock product
        low_stock = factory.Trait(
            stock=fuzzy.FuzzyInteger(1, 5),
        )

        # Archived product
        archived = factory.Trait(
            status=ProductStatus.ARCHIVED,
        )

    @factory.lazy_attribute
    def metadata(self):
        """Generate random metadata."""
        fake = factory.Faker._get_faker()
        return {
            'brand': fake.company(),
            'weight': f'{fake.random_int(100, 5000)}g',
        }


class CategoryFactory(DjangoModelFactory):
    """Factory for Category model."""

    class Meta:
        model = 'categories.Category'

    name = factory.Faker('word')
    slug = factory.LazyAttribute(
        lambda o: o.name.lower().replace(' ', '-')
    )


class TagFactory(DjangoModelFactory):
    """Factory for Tag model."""

    class Meta:
        model = 'tags.Tag'

    name = factory.Faker('word')
