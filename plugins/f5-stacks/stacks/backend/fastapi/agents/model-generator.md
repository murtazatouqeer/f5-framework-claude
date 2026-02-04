---
name: fastapi-model-generator
description: Agent for generating SQLAlchemy models
applies_to: fastapi
category: agent
inputs:
  - entity_name: Entity name in PascalCase
  - table_name: Database table name
  - fields: List of field definitions
  - relationships: Related models
---

# FastAPI Model Generator Agent

## Purpose

Generate SQLAlchemy 2.0 async models with proper type hints, relationships, indexes, and mixins.

## Activation

- User requests: "create model for [entity]", "generate [entity] table"
- When designing database schema
- When adding new entities to the system

## Generation Process

### Step 1: Gather Requirements

Ask for or determine:
1. Entity name (PascalCase): e.g., `Product`
2. Table name: e.g., `products`
3. Fields and their types
4. Relationships to other models
5. Required indexes
6. Soft delete needed?
7. Custom methods/properties

### Step 2: Analyze Field Types

Map business requirements to SQLAlchemy types:

| Business Type | SQLAlchemy Type | Python Type |
|--------------|-----------------|-------------|
| Short text | `String(n)` | `str` |
| Long text | `Text` | `str` |
| Integer | `Integer` | `int` |
| Decimal/Money | `Numeric(10,2)` | `Decimal` |
| Boolean | `Boolean` | `bool` |
| Date | `Date` | `date` |
| DateTime | `DateTime(timezone=True)` | `datetime` |
| UUID | `UUID` | `UUID` |
| JSON | `JSON` | `dict` |
| Enum | `Enum(MyEnum)` | `MyEnum` |

### Step 3: Generate Model

```python
# app/models/{entity_lower}.py
"""
{entity_name} database model.

REQ-XXX: {entity_name} data persistence
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


class {entity_name}(BaseModel, TimestampMixin, SoftDeleteMixin):
    """
    {entity_name} model.

    Attributes:
        name: Display name
        slug: URL-friendly identifier
        description: Detailed description
        price: Current price
        status: Current status (draft/active/archived)
    """

    __tablename__ = "{table_name}"

    # Primary fields
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Business fields
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    compare_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    stock: Mapped[int] = mapped_column(Integer, default=0)

    # Status and flags
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
        back_populates="{entity_plural}",
        lazy="selectin",
    )
    created_by: Mapped[Optional["User"]] = relationship(
        back_populates="{entity_plural}",
        lazy="selectin",
    )

    # Composite indexes
    __table_args__ = (
        Index("ix_{table_name}_status_created", "status", "created_at"),
        Index("ix_{table_name}_category_status", "category_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<{entity_name} {{self.name}}>"

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

### Step 4: Create Alembic Migration

```python
# alembic/versions/xxx_create_{table_name}.py
"""Create {table_name} table.

Revision ID: {revision_id}
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '{revision_id}'
down_revision = '{previous_revision}'


def upgrade() -> None:
    op.create_table(
        '{table_name}',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('slug', sa.String(255), unique=True, nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('compare_price', sa.Numeric(10, 2)),
        sa.Column('sku', sa.String(100), unique=True, nullable=False),
        sa.Column('stock', sa.Integer, default=0),
        sa.Column('status', sa.String(50), default='draft'),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('category_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('categories.id', ondelete='SET NULL')),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
    )

    op.create_index('ix_{table_name}_slug', '{table_name}', ['slug'])
    op.create_index('ix_{table_name}_status', '{table_name}', ['status'])
    op.create_index('ix_{table_name}_category_id', '{table_name}', ['category_id'])


def downgrade() -> None:
    op.drop_table('{table_name}')
```

### Step 5: Register Model

Add to `app/models/__init__.py`:

```python
from app.models.{entity_lower} import {entity_name}

__all__ = [..., "{entity_name}"]
```

## Relationship Patterns

### One-to-Many

```python
# Parent model
children: Mapped[List["Child"]] = relationship(
    back_populates="parent",
    lazy="selectin",
)

# Child model
parent_id: Mapped[UUID] = mapped_column(ForeignKey("parents.id"))
parent: Mapped["Parent"] = relationship(back_populates="children")
```

### Many-to-Many

```python
# Association table
product_tags = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", ForeignKey("products.id"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id"), primary_key=True),
)

# Product model
tags: Mapped[List["Tag"]] = relationship(
    secondary=product_tags,
    back_populates="products",
)
```

## Output Files

1. `app/models/{entity_lower}.py` - Model file
2. `alembic/versions/xxx_create_{table_name}.py` - Migration
3. Update `app/models/__init__.py` - Model registration

## Validation Checklist

- [ ] All fields have proper types
- [ ] Nullable fields use `Optional`
- [ ] Foreign keys have appropriate ondelete
- [ ] Indexes created for query patterns
- [ ] Relationships configured correctly
- [ ] Migration matches model
- [ ] REQ-XXX traceability comment
