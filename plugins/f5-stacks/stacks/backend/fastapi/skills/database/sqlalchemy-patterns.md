---
name: fastapi-sqlalchemy-patterns
description: SQLAlchemy patterns for FastAPI applications
applies_to: fastapi
category: skill
---

# SQLAlchemy Patterns for FastAPI

## Model Definition (SQLAlchemy 2.0 Style)

### Base Model

```python
# app/models/base.py
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class TimestampMixin:
    """Mixin for timestamp fields."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin for soft delete."""
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class UUIDMixin:
    """Mixin for UUID primary key."""
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class BaseModel(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """Base model with common fields."""
    __abstract__ = True
```

### Entity Model

```python
# app/models/product.py
from __future__ import annotations
import uuid
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import String, Text, Numeric, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category
    from app.models.order import OrderItem


class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        Index("idx_products_status_created", "status", "created_at"),
        Index("idx_products_category", "category_id"),
    )

    # Basic fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    sku: Mapped[str] = mapped_column(String(100), unique=True)

    # Pricing
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    compare_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))

    # Inventory
    stock: Mapped[int] = mapped_column(default=0)
    low_stock_threshold: Mapped[int] = mapped_column(default=10)

    # Status
    status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus),
        default=ProductStatus.DRAFT,
    )

    # Metadata (PostgreSQL specific)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    metadata: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Foreign keys
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
    )

    # Relationships
    category: Mapped[Category] = relationship(back_populates="products")
    created_by: Mapped[Optional[User]] = relationship(back_populates="created_products")
    order_items: Mapped[List[OrderItem]] = relationship(back_populates="product")

    # Computed properties
    @property
    def is_on_sale(self) -> bool:
        return self.compare_price is not None and self.compare_price > self.price

    @property
    def is_low_stock(self) -> bool:
        return self.stock <= self.low_stock_threshold

    @property
    def discount_percentage(self) -> float:
        if not self.is_on_sale:
            return 0.0
        return round((1 - float(self.price / self.compare_price)) * 100, 1)
```

### Relationships

```python
# app/models/user.py
from __future__ import annotations
from typing import TYPE_CHECKING, List
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.order import Order


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

    # One-to-Many relationships
    created_products: Mapped[List[Product]] = relationship(
        back_populates="created_by",
        cascade="all, delete-orphan",
    )
    orders: Mapped[List[Order]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


# Many-to-Many relationship
# app/models/tag.py
from sqlalchemy import Table, Column, ForeignKey

product_tags = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)


class Tag(BaseModel):
    __tablename__ = "tags"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True)

    products: Mapped[List[Product]] = relationship(
        secondary=product_tags,
        back_populates="tags",
    )
```

## Query Patterns

### Basic Queries

```python
# Using select() - SQLAlchemy 2.0 style
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload

async def get_product_by_id(session: AsyncSession, product_id: UUID) -> Product | None:
    """Get single product by ID."""
    stmt = select(Product).where(
        Product.id == product_id,
        Product.deleted_at.is_(None),
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_products_by_category(
    session: AsyncSession,
    category_id: UUID,
    status: ProductStatus = ProductStatus.ACTIVE,
) -> list[Product]:
    """Get products by category."""
    stmt = (
        select(Product)
        .where(
            Product.category_id == category_id,
            Product.status == status,
            Product.deleted_at.is_(None),
        )
        .order_by(Product.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
```

### Eager Loading

```python
async def get_product_with_relations(
    session: AsyncSession,
    product_id: UUID,
) -> Product | None:
    """Get product with eager loaded relationships."""
    stmt = (
        select(Product)
        .options(
            selectinload(Product.category),
            selectinload(Product.created_by),
            selectinload(Product.order_items),
        )
        .where(Product.id == product_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# For nested relationships
async def get_order_with_details(
    session: AsyncSession,
    order_id: UUID,
) -> Order | None:
    stmt = (
        select(Order)
        .options(
            selectinload(Order.items).selectinload(OrderItem.product),
            selectinload(Order.user),
        )
        .where(Order.id == order_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
```

### Pagination and Search

```python
async def search_products(
    session: AsyncSession,
    *,
    search: str | None = None,
    category_id: UUID | None = None,
    status: ProductStatus | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Product], int]:
    """Search products with filters and pagination."""

    # Base query
    base_stmt = select(Product).where(Product.deleted_at.is_(None))

    # Apply filters
    filters = []
    if search:
        filters.append(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
            )
        )
    if category_id:
        filters.append(Product.category_id == category_id)
    if status:
        filters.append(Product.status == status)
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)

    if filters:
        base_stmt = base_stmt.where(and_(*filters))

    # Count query
    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Data query with pagination
    data_stmt = (
        base_stmt
        .options(selectinload(Product.category))
        .order_by(Product.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.execute(data_stmt)
    items = list(result.scalars().all())

    return items, total
```

### Aggregations

```python
async def get_category_stats(session: AsyncSession) -> list[dict]:
    """Get product statistics per category."""
    stmt = (
        select(
            Category.id,
            Category.name,
            func.count(Product.id).label("product_count"),
            func.avg(Product.price).label("avg_price"),
            func.sum(Product.stock).label("total_stock"),
        )
        .join(Product, Category.id == Product.category_id, isouter=True)
        .where(Product.deleted_at.is_(None))
        .group_by(Category.id, Category.name)
    )
    result = await session.execute(stmt)
    return [dict(row._mapping) for row in result.all()]
```

## CRUD Operations

```python
async def create_product(
    session: AsyncSession,
    data: dict,
) -> Product:
    """Create new product."""
    product = Product(**data)
    session.add(product)
    await session.flush()
    await session.refresh(product)
    return product


async def update_product(
    session: AsyncSession,
    product_id: UUID,
    data: dict,
) -> Product | None:
    """Update product."""
    product = await get_product_by_id(session, product_id)
    if not product:
        return None

    for key, value in data.items():
        if hasattr(product, key):
            setattr(product, key, value)

    await session.flush()
    await session.refresh(product)
    return product


async def soft_delete_product(
    session: AsyncSession,
    product_id: UUID,
) -> bool:
    """Soft delete product."""
    from datetime import datetime, timezone

    stmt = (
        update(Product)
        .where(Product.id == product_id)
        .values(deleted_at=datetime.now(timezone.utc))
    )
    result = await session.execute(stmt)
    return result.rowcount > 0
```

## Best Practices

1. **Use SQLAlchemy 2.0 style** with `select()` and `Mapped` type hints
2. **Use selectinload** for collections, `joinedload` for single relations
3. **Implement soft delete** for important data
4. **Use indexes** for frequently queried columns
5. **Flush instead of commit** in repositories - let the session dependency handle commit
6. **Use TYPE_CHECKING** imports to avoid circular imports
