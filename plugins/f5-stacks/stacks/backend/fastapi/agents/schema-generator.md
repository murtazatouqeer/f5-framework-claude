---
name: fastapi-schema-generator
description: Agent for generating Pydantic schemas
applies_to: fastapi
category: agent
inputs:
  - entity_name: Entity name in PascalCase
  - fields: List of field definitions
  - validations: Custom validation rules
---

# FastAPI Schema Generator Agent

## Purpose

Generate Pydantic v2 schemas for request/response validation with proper typing, validators, and OpenAPI documentation.

## Activation

- User requests: "create schema for [entity]", "generate [entity] validation"
- When defining API data structures
- When adding validation rules

## Generation Process

### Step 1: Gather Requirements

Ask for or determine:
1. Entity name (PascalCase): e.g., `Product`
2. Fields and their types
3. Required vs optional fields
4. Validation rules
5. Nested schemas needed
6. Computed fields

### Step 2: Analyze Field Types

Map business requirements to Pydantic types:

| Business Type | Pydantic Type | Field Options |
|--------------|---------------|---------------|
| Short text | `str` | `min_length`, `max_length` |
| Email | `EmailStr` | Built-in validation |
| URL | `HttpUrl` | Built-in validation |
| Integer | `int` | `ge`, `le`, `gt`, `lt` |
| Decimal | `Decimal` | `decimal_places` |
| Boolean | `bool` | - |
| Date | `date` | - |
| DateTime | `datetime` | - |
| UUID | `UUID` | - |
| List | `List[T]` | `min_length`, `max_length` |
| Enum | `Literal[...]` | Pattern validation |

### Step 3: Generate Schemas

```python
# app/schemas/{entity_lower}.py
"""
{entity_name} Pydantic schemas.

REQ-XXX: {entity_name} data validation
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    field_validator,
    model_validator,
)


# ============================================================================
# Base Schema
# ============================================================================

class {entity_name}Base(BaseModel):
    """Base schema with shared fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name",
        json_schema_extra={{"example": "Premium Widget"}},
    )
    description: Optional[str] = Field(
        None,
        max_length=2000,
        description="Detailed description",
    )
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Price in dollars",
        json_schema_extra={{"example": 29.99}},
    )
    compare_price: Optional[Decimal] = Field(
        None,
        gt=0,
        decimal_places=2,
        description="Original price for sale display",
    )
    sku: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Stock keeping unit",
        json_schema_extra={{"example": "PROD-001"}},
    )


# ============================================================================
# Create Schema
# ============================================================================

class {entity_name}Create({entity_name}Base):
    """Schema for creating a {entity_lower}."""

    category_id: Optional[UUID] = Field(
        None,
        description="Category UUID",
    )
    tags: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Product tags",
    )
    stock: int = Field(
        default=0,
        ge=0,
        description="Initial stock quantity",
    )
    status: str = Field(
        default="draft",
        pattern="^(draft|active|archived)$",
        description="Initial status",
    )

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
    def validate_prices(self) -> "{entity_name}Create":
        """Validate compare_price > price if set."""
        if self.compare_price and self.compare_price <= self.price:
            raise ValueError("compare_price must be greater than price")
        return self

    model_config = ConfigDict(
        json_schema_extra={{
            "examples": [
                {{
                    "name": "Premium Widget",
                    "description": "High-quality widget",
                    "price": 29.99,
                    "sku": "PROD-001",
                    "tags": ["electronics", "gadgets"],
                }}
            ]
        }}
    )


# ============================================================================
# Update Schema
# ============================================================================

class {entity_name}Update(BaseModel):
    """Schema for updating a {entity_lower}. All fields optional."""

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

class {entity_name}Response({entity_name}Base):
    """Schema for {entity_lower} response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    status: str
    stock: int
    is_featured: bool = False
    category_id: Optional[UUID] = None
    created_by_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ============================================================================
# List Response Schema
# ============================================================================

class {entity_name}ListItem(BaseModel):
    """Simplified schema for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    price: Decimal
    compare_price: Optional[Decimal] = None
    status: str
    stock: int
    is_featured: bool = False
    created_at: datetime


class {entity_name}ListResponse(BaseModel):
    """Paginated list response."""

    items: List[{entity_name}ListItem]
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
# Query Parameters
# ============================================================================

class {entity_name}QueryParams(BaseModel):
    """Query parameters for listing."""

    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    search: Optional[str] = Field(None, max_length=100)
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")
    category_id: Optional[UUID] = None
    min_price: Optional[Decimal] = Field(None, ge=0)
    max_price: Optional[Decimal] = Field(None, ge=0)
    sort_by: str = Field("created_at")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
```

### Step 4: Register Schemas

Add to `app/schemas/__init__.py`:

```python
from app.schemas.{entity_lower} import (
    {entity_name}Create,
    {entity_name}Update,
    {entity_name}Response,
    {entity_name}ListResponse,
)

__all__ = [
    ...,
    "{entity_name}Create",
    "{entity_name}Update",
    "{entity_name}Response",
    "{entity_name}ListResponse",
]
```

## Common Validators

### Email Normalization

```python
@field_validator("email")
@classmethod
def normalize_email(cls, v: str) -> str:
    return v.lower().strip()
```

### Password Strength

```python
@field_validator("password")
@classmethod
def validate_password(cls, v: str) -> str:
    if len(v) < 8:
        raise ValueError("Password must be at least 8 characters")
    if not re.search(r"[A-Z]", v):
        raise ValueError("Password must contain uppercase")
    if not re.search(r"[0-9]", v):
        raise ValueError("Password must contain digit")
    return v
```

### Cross-Field Validation

```python
@model_validator(mode="after")
def validate_date_range(self) -> "DateRange":
    if self.start_date and self.end_date:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before end_date")
    return self
```

## Output Files

1. `app/schemas/{entity_lower}.py` - Schema file
2. Update `app/schemas/__init__.py` - Schema registration

## Validation Checklist

- [ ] Base schema has shared fields
- [ ] Create schema has required fields
- [ ] Update schema has all optional fields
- [ ] Response schema has `from_attributes=True`
- [ ] Field validators normalize input
- [ ] Model validators check cross-field rules
- [ ] OpenAPI examples provided
- [ ] REQ-XXX traceability comment
