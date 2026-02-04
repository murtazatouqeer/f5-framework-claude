---
name: fastapi-model
description: SQLAlchemy model template for FastAPI
applies_to: fastapi
category: template
variables:
  - name: entity_name
    description: Entity name in PascalCase (e.g., Product)
  - name: table_name
    description: Database table name (e.g., products)
---

# SQLAlchemy Model Template

## Template

```python
# app/models/{{entity_lower}}.py
"""
{{entity_name}} database model.

REQ-XXX: {{entity_name}} data persistence
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import String, Text, Numeric, Integer, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category


class {{entity_name}}(BaseModel, TimestampMixin, SoftDeleteMixin):
    """{{entity_name}} database model."""

    __tablename__ = "{{table_name}}"

    # Primary fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Business fields - customize as needed
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    compare_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        nullable=False,
        index=True,
    )
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Foreign keys
    category_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
    )
    created_by_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
    )

    # Relationships
    category: Mapped[Optional["Category"]] = relationship(
        back_populates="{{entity_plural}}",
        lazy="selectin",
    )
    created_by: Mapped[Optional["User"]] = relationship(
        back_populates="{{entity_plural}}",
        lazy="selectin",
    )

    # Composite indexes for common queries
    __table_args__ = (
        Index("ix_{{table_name}}_status_created", "status", "created_at"),
        Index("ix_{{table_name}}_category_status", "category_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<{{entity_name}} {self.name}>"

    @property
    def is_on_sale(self) -> bool:
        """Check if item is on sale."""
        return self.compare_price is not None and self.compare_price > self.price

    @property
    def discount_percentage(self) -> int:
        """Calculate discount percentage."""
        if not self.is_on_sale:
            return 0
        return int((1 - self.price / self.compare_price) * 100)
```

## Base Model

```python
# app/models/base.py
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


class BaseModel(Base):
    """Base model with UUID primary key."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )


class TimestampMixin:
    """Mixin for created_at and updated_at fields."""

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
    """Mixin for soft delete functionality."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        self.deleted_at = datetime.utcnow()

    def restore(self) -> None:
        self.deleted_at = None
```

## Usage

Replace placeholders:
- `{{entity_name}}`: PascalCase entity name (e.g., `Product`)
- `{{entity_lower}}`: Lowercase singular (e.g., `product`)
- `{{entity_plural}}`: Plural lowercase (e.g., `products`)
- `{{table_name}}`: Database table name (e.g., `products`)

### Example: Product Model

```python
# app/models/product.py
class Product(BaseModel, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    category_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("categories.id"))

    category: Mapped[Optional["Category"]] = relationship(back_populates="products")
```

### Model Registration

```python
# app/models/__init__.py
from app.models.base import Base
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.order import Order

__all__ = ["Base", "User", "Product", "Category", "Order"]
```
