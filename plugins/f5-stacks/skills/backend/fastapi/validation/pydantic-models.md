---
name: fastapi-pydantic-models
description: Pydantic models and validation for FastAPI
applies_to: fastapi
category: skill
---

# Pydantic Models for FastAPI

## Basic Model Patterns

### Base Schema

```python
# app/schemas/base.py
from datetime import datetime
from typing import Generic, TypeVar, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode
        populate_by_name=True,  # Allow population by field name or alias
        str_strip_whitespace=True,  # Strip whitespace from strings
        validate_assignment=True,  # Validate on assignment
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""
    created_at: datetime
    updated_at: datetime


class IDSchema(BaseSchema):
    """Schema with ID field."""
    id: UUID


# Generic pagination response
T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response wrapper."""
    items: list[T]
    total: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1
```

### CRUD Schemas

```python
# app/schemas/product.py
from __future__ import annotations
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class ProductBase(BaseModel):
    """Base product schema with common fields."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    compare_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    sku: str = Field(..., min_length=1, max_length=100)


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    category_id: UUID
    tags: List[str] = Field(default_factory=list, max_length=10)
    stock: int = Field(default=0, ge=0)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: List[str]) -> List[str]:
        # Remove duplicates and empty strings
        return list(set(tag.strip().lower() for tag in v if tag.strip()))

    @model_validator(mode="after")
    def validate_prices(self) -> "ProductCreate":
        if self.compare_price and self.compare_price <= self.price:
            raise ValueError("compare_price must be greater than price")
        return self


class ProductUpdate(BaseModel):
    """Schema for updating a product. All fields optional."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    compare_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    status: str
    stock: int
    category_id: UUID
    created_by_id: Optional[UUID] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    # Computed fields
    @property
    def is_on_sale(self) -> bool:
        return self.compare_price is not None and self.compare_price > self.price


class ProductListResponse(BaseModel):
    """Paginated product list response."""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
```

## Field Validation

### Common Validators

```python
# app/schemas/validators.py
from typing import Any
from pydantic import field_validator, model_validator
import re


class EmailValidatorMixin:
    """Mixin for email validation."""

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.lower().strip()
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            raise ValueError("Invalid email format")
        return v


class PhoneValidatorMixin:
    """Mixin for phone validation."""

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        # Remove non-digits
        cleaned = re.sub(r"\D", "", v)
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError("Phone number must be 10-15 digits")
        return cleaned


class PasswordValidatorMixin:
    """Mixin for password validation."""

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        return v


class SlugValidatorMixin:
    """Mixin for slug validation."""

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        v = v.lower().strip()
        if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
            raise ValueError("Invalid slug format")
        return v
```

### Using Validators

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from app.schemas.validators import PasswordValidatorMixin, PhoneValidatorMixin


class UserCreate(BaseModel, PasswordValidatorMixin, PhoneValidatorMixin):
    """User creation schema with validation."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    name: str = Field(..., min_length=1, max_length=100)
    phone: str | None = None


class UserUpdate(BaseModel, PhoneValidatorMixin):
    """User update schema."""
    name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = None
```

## Advanced Patterns

### Nested Models

```python
# app/schemas/order.py
from decimal import Decimal
from typing import List
from uuid import UUID
from pydantic import BaseModel, Field, computed_field


class OrderItemCreate(BaseModel):
    """Order item creation schema."""
    product_id: UUID
    quantity: int = Field(..., gt=0, le=100)
    price: Decimal = Field(..., gt=0)


class OrderCreate(BaseModel):
    """Order creation schema."""
    items: List[OrderItemCreate] = Field(..., min_length=1)
    shipping_address_id: UUID
    notes: str | None = None

    @computed_field
    @property
    def total(self) -> Decimal:
        return sum(item.price * item.quantity for item in self.items)


class OrderItemResponse(BaseModel):
    """Order item response schema."""
    model_config = {"from_attributes": True}

    id: UUID
    product_id: UUID
    quantity: int
    price: Decimal
    product_name: str | None = None


class OrderResponse(BaseModel):
    """Order response schema."""
    model_config = {"from_attributes": True}

    id: UUID
    status: str
    items: List[OrderItemResponse]
    total: Decimal
    created_at: datetime
```

### Discriminated Unions

```python
# app/schemas/notifications.py
from typing import Literal, Union
from pydantic import BaseModel, Field


class EmailNotification(BaseModel):
    """Email notification schema."""
    type: Literal["email"] = "email"
    to: str
    subject: str
    body: str


class SMSNotification(BaseModel):
    """SMS notification schema."""
    type: Literal["sms"] = "sms"
    phone: str
    message: str = Field(..., max_length=160)


class PushNotification(BaseModel):
    """Push notification schema."""
    type: Literal["push"] = "push"
    device_token: str
    title: str
    body: str
    data: dict = Field(default_factory=dict)


# Discriminated union
Notification = Union[
    EmailNotification,
    SMSNotification,
    PushNotification,
]


class NotificationRequest(BaseModel):
    """Notification request with discriminated union."""
    notification: Notification = Field(..., discriminator="type")
```

### Partial Updates

```python
# app/schemas/utils.py
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def create_partial_model(model: Type[T], name: str | None = None) -> Type[T]:
    """Create a partial version of a model where all fields are optional."""
    fields = {}
    for field_name, field_info in model.model_fields.items():
        fields[field_name] = (field_info.annotation | None, None)

    return type(
        name or f"Partial{model.__name__}",
        (BaseModel,),
        {"__annotations__": {k: v[0] for k, v in fields.items()}},
    )


# Usage
PartialProductUpdate = create_partial_model(ProductBase, "ProductUpdate")
```

### Query Parameters Schema

```python
# app/schemas/query.py
from typing import Optional, Literal
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Pagination query parameters."""
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class SortParams(BaseModel):
    """Sorting query parameters."""
    sort_by: str = "created_at"
    sort_order: Literal["asc", "desc"] = "desc"


class SearchParams(BaseModel):
    """Search query parameters."""
    search: Optional[str] = Field(None, min_length=1, max_length=100)


class ProductQueryParams(PaginationParams, SortParams, SearchParams):
    """Product query parameters."""
    category_id: Optional[str] = None
    status: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
```

## Response Models

### Standard API Response

```python
# app/schemas/response.py
from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    message: str
    code: str
    details: Optional[dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response."""
    success: bool = False
    message: str = "Validation error"
    code: str = "VALIDATION_ERROR"
    errors: list[dict[str, Any]]
```

## Best Practices

1. **Use Field()** for validation constraints
2. **Separate Create/Update/Response** schemas
3. **Use model_config** for common settings
4. **Create base schemas** for shared fields
5. **Use computed_field** for derived values
6. **Implement custom validators** as mixins
7. **Use discriminated unions** for polymorphic data
8. **Document schemas** with descriptions
