---
name: fastapi-schema
description: Pydantic schema template for FastAPI
applies_to: fastapi
category: template
variables:
  - name: entity_name
    description: Entity name in PascalCase (e.g., Product)
---

# Pydantic Schema Template

## Template

```python
# app/schemas/{{entity_lower}}.py
"""
{{entity_name}} Pydantic schemas.

REQ-XXX: {{entity_name}} data validation
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ============================================================================
# Base Schema
# ============================================================================

class {{entity_name}}Base(BaseModel):
    """Base schema with shared fields."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    compare_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    sku: str = Field(..., min_length=1, max_length=100)


# ============================================================================
# Create Schema
# ============================================================================

class {{entity_name}}Create({{entity_name}}Base):
    """Schema for creating a {{entity_lower}}."""

    category_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list, max_length=10)
    stock: int = Field(default=0, ge=0)
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and normalize name."""
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        """Remove duplicates and normalize tags."""
        return list(set(tag.strip().lower() for tag in v if tag.strip()))

    @model_validator(mode="after")
    def validate_prices(self) -> "{{entity_name}}Create":
        """Validate compare_price > price if set."""
        if self.compare_price and self.compare_price <= self.price:
            raise ValueError("compare_price must be greater than price")
        return self


# ============================================================================
# Update Schema
# ============================================================================

class {{entity_name}}Update(BaseModel):
    """Schema for updating a {{entity_lower}}. All fields optional."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    compare_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")

    model_config = ConfigDict(extra="ignore")


# ============================================================================
# Response Schema
# ============================================================================

class {{entity_name}}Response({{entity_name}}Base):
    """Schema for {{entity_lower}} response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    status: str
    stock: int
    category_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    # Computed fields
    @property
    def is_on_sale(self) -> bool:
        """Check if item is on sale."""
        return self.compare_price is not None and self.compare_price > self.price


# ============================================================================
# List Response Schema
# ============================================================================

class {{entity_name}}ListItem(BaseModel):
    """Simplified schema for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    price: Decimal
    compare_price: Optional[Decimal] = None
    status: str
    stock: int
    created_at: datetime


class {{entity_name}}ListResponse(BaseModel):
    """Paginated list response."""

    items: List[{{entity_name}}ListItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1


# ============================================================================
# Query Parameters Schema
# ============================================================================

class {{entity_name}}QueryParams(BaseModel):
    """Query parameters for listing {{entity_plural}}."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    search: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")
    category_id: Optional[UUID] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    sort_by: str = Field("created_at")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size
```

## Usage

Replace placeholders:
- `{{entity_name}}`: PascalCase entity name (e.g., `Product`)
- `{{entity_lower}}`: Lowercase singular (e.g., `product`)
- `{{entity_plural}}`: Plural lowercase (e.g., `products`)

### Example: Product Schema

```python
# app/schemas/product.py
class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    price: Decimal = Field(..., gt=0)

class ProductCreate(ProductBase):
    category_id: Optional[UUID] = None

class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
```

### Schema Registration

```python
# app/schemas/__init__.py
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse

__all__ = [
    "UserCreate", "UserUpdate", "UserResponse",
    "ProductCreate", "ProductUpdate", "ProductResponse",
]
```
