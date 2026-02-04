---
name: fastapi-custom-validators
description: Custom validators and validation patterns for FastAPI
applies_to: fastapi
category: skill
---

# Custom Validators in FastAPI

## Pydantic Field Validators

### Field Validator

```python
# app/schemas/validators.py
from typing import Any
from pydantic import BaseModel, Field, field_validator
import re


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format."""
        v = v.strip().lower()
        if not re.match(r"^[a-z][a-z0-9_]*$", v):
            raise ValueError(
                "Username must start with letter and contain only "
                "lowercase letters, numbers, and underscores"
            )
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email."""
        v = v.lower().strip()
        if "@" not in v:
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        errors = []
        if len(v) < 8:
            errors.append("at least 8 characters")
        if not re.search(r"[A-Z]", v):
            errors.append("one uppercase letter")
        if not re.search(r"[a-z]", v):
            errors.append("one lowercase letter")
        if not re.search(r"\d", v):
            errors.append("one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("one special character")

        if errors:
            raise ValueError(f"Password must contain: {', '.join(errors)}")
        return v
```

### Model Validator

```python
from pydantic import BaseModel, Field, model_validator
from datetime import date


class DateRangeFilter(BaseModel):
    """Filter with date range validation."""
    start_date: date | None = None
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self) -> "DateRangeFilter":
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must be before end_date")
        return self


class PasswordChange(BaseModel):
    """Password change with confirmation."""
    current_password: str
    new_password: str
    confirm_password: str

    @model_validator(mode="after")
    def validate_passwords(self) -> "PasswordChange":
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")
        if self.new_password == self.current_password:
            raise ValueError("New password must be different")
        return self


class PriceRange(BaseModel):
    """Price with compare price validation."""
    price: float = Field(..., gt=0)
    compare_price: float | None = Field(None, gt=0)
    cost: float | None = Field(None, gt=0)

    @model_validator(mode="after")
    def validate_prices(self) -> "PriceRange":
        if self.compare_price and self.compare_price <= self.price:
            raise ValueError("compare_price must be greater than price")
        if self.cost and self.cost >= self.price:
            raise ValueError("cost must be less than price")
        return self
```

### Before/After Validators

```python
from pydantic import BaseModel, field_validator
from typing import Any


class ProductCreate(BaseModel):
    name: str
    tags: list[str] = []

    @field_validator("name", mode="before")
    @classmethod
    def preprocess_name(cls, v: Any) -> str:
        """Preprocess name before validation."""
        if isinstance(v, str):
            return v.strip()
        return v

    @field_validator("tags", mode="after")
    @classmethod
    def process_tags(cls, v: list[str]) -> list[str]:
        """Process tags after validation."""
        # Remove duplicates, lowercase, and filter empty
        return list(set(tag.lower().strip() for tag in v if tag.strip()))
```

## Custom Types

### Annotated Types

```python
# app/schemas/types.py
from typing import Annotated
from pydantic import AfterValidator, BeforeValidator, PlainSerializer
import re


def validate_phone(v: str) -> str:
    """Validate phone number."""
    cleaned = re.sub(r"\D", "", v)
    if not (10 <= len(cleaned) <= 15):
        raise ValueError("Phone must be 10-15 digits")
    return cleaned


def validate_slug(v: str) -> str:
    """Validate URL slug."""
    v = v.lower().strip()
    if not re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)*$", v):
        raise ValueError("Invalid slug format")
    return v


def validate_currency_code(v: str) -> str:
    """Validate currency code."""
    v = v.upper()
    if not re.match(r"^[A-Z]{3}$", v):
        raise ValueError("Currency code must be 3 letters")
    return v


# Custom types
PhoneNumber = Annotated[str, AfterValidator(validate_phone)]
Slug = Annotated[str, AfterValidator(validate_slug)]
CurrencyCode = Annotated[str, AfterValidator(validate_currency_code)]


# Usage
from pydantic import BaseModel

class Contact(BaseModel):
    phone: PhoneNumber
    currency: CurrencyCode


class Product(BaseModel):
    slug: Slug
    name: str
```

### Custom Field Types

```python
# app/schemas/fields.py
from typing import Any
from pydantic import GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
import re


class Email(str):
    """Custom Email type with validation."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(
            cls._validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def _validate(cls, v: str) -> "Email":
        v = v.lower().strip()
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", v):
            raise ValueError("Invalid email format")
        return cls(v)

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        _core_schema: CoreSchema,
        handler: GetJsonSchemaHandler,
    ) -> JsonSchemaValue:
        return {"type": "string", "format": "email"}


class Money:
    """Custom Money type for currency handling."""

    def __init__(self, amount: int, currency: str = "USD"):
        self.amount = amount  # Store in cents
        self.currency = currency.upper()

    @classmethod
    def from_decimal(cls, amount: float, currency: str = "USD") -> "Money":
        return cls(int(amount * 100), currency)

    def to_decimal(self) -> float:
        return self.amount / 100

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_plain_validator_function(cls._validate)

    @classmethod
    def _validate(cls, v: Any) -> "Money":
        if isinstance(v, cls):
            return v
        if isinstance(v, dict):
            return cls(v["amount"], v.get("currency", "USD"))
        if isinstance(v, (int, float)):
            return cls.from_decimal(float(v))
        raise ValueError(f"Cannot convert {type(v)} to Money")
```

## FastAPI Dependencies for Validation

### Path Parameter Validation

```python
# app/api/deps.py
from typing import Annotated
from uuid import UUID
from fastapi import Path, HTTPException, status


def valid_uuid(
    id: Annotated[str, Path(description="Resource ID")]
) -> UUID:
    """Validate and convert UUID path parameter."""
    try:
        return UUID(id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID format"
        )


# Usage
@router.get("/{id}")
async def get_item(id: Annotated[UUID, Depends(valid_uuid)]):
    ...
```

### Query Parameter Validation

```python
# app/api/deps.py
from typing import Annotated
from fastapi import Query, HTTPException


class DateRangeParams:
    """Date range query parameters with validation."""

    def __init__(
        self,
        start_date: Annotated[str | None, Query(description="Start date (YYYY-MM-DD)")] = None,
        end_date: Annotated[str | None, Query(description="End date (YYYY-MM-DD)")] = None,
    ):
        from datetime import datetime

        self.start_date = None
        self.end_date = None

        if start_date:
            try:
                self.start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(400, "Invalid start_date format (use YYYY-MM-DD)")

        if end_date:
            try:
                self.end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(400, "Invalid end_date format (use YYYY-MM-DD)")

        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise HTTPException(400, "start_date must be before end_date")


# Usage
@router.get("/")
async def list_items(
    date_range: Annotated[DateRangeParams, Depends()],
):
    # date_range.start_date, date_range.end_date
    ...
```

### Request Body Validation

```python
# app/api/deps.py
from typing import Annotated, TypeVar
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel, ValidationError


T = TypeVar("T", bound=BaseModel)


def validate_unique_items(field_name: str, get_items: callable):
    """Factory for unique item validation."""

    async def validator(data: T, db: AsyncSession = Depends(get_db)) -> T:
        value = getattr(data, field_name)
        existing = await get_items(db, value)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"{field_name} already exists"
            )
        return data

    return validator


# Usage
@router.post("/")
async def create_user(
    data: Annotated[
        UserCreate,
        Depends(validate_unique_items("email", get_user_by_email))
    ],
):
    ...
```

## File Upload Validation

```python
# app/api/deps.py
from typing import Annotated
from fastapi import UploadFile, HTTPException, status


class FileValidator:
    """Validate uploaded files."""

    def __init__(
        self,
        max_size_mb: float = 5.0,
        allowed_types: list[str] | None = None,
        allowed_extensions: list[str] | None = None,
    ):
        self.max_size = int(max_size_mb * 1024 * 1024)
        self.allowed_types = allowed_types or []
        self.allowed_extensions = allowed_extensions or []

    async def __call__(self, file: UploadFile) -> UploadFile:
        # Check content type
        if self.allowed_types and file.content_type not in self.allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: {self.allowed_types}"
            )

        # Check extension
        if self.allowed_extensions:
            ext = file.filename.rsplit(".", 1)[-1].lower() if file.filename else ""
            if ext not in self.allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File extension not allowed. Allowed: {self.allowed_extensions}"
                )

        # Check file size
        contents = await file.read()
        if len(contents) > self.max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Max size: {self.max_size / 1024 / 1024}MB"
            )

        # Reset file position
        await file.seek(0)
        return file


# Validators for specific file types
validate_image = FileValidator(
    max_size_mb=5.0,
    allowed_types=["image/jpeg", "image/png", "image/gif", "image/webp"],
    allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"],
)

validate_document = FileValidator(
    max_size_mb=10.0,
    allowed_types=["application/pdf", "application/msword"],
    allowed_extensions=["pdf", "doc", "docx"],
)


# Usage
@router.post("/upload-avatar")
async def upload_avatar(
    file: Annotated[UploadFile, Depends(validate_image)],
):
    ...
```

## JSON Schema Customization

```python
# app/schemas/custom.py
from pydantic import BaseModel, Field
from typing import Any


class ProductCreate(BaseModel):
    """Product creation with custom JSON schema."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Product name",
        json_schema_extra={"example": "Premium Widget"},
    )
    price: float = Field(
        ...,
        gt=0,
        description="Product price in dollars",
        json_schema_extra={"example": 29.99},
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Product tags",
        json_schema_extra={"example": ["electronics", "gadgets"]},
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Premium Widget",
                    "price": 29.99,
                    "tags": ["electronics", "gadgets"],
                }
            ]
        }
    }
```

## Best Practices

1. **Use field_validator** for single field validation
2. **Use model_validator** for cross-field validation
3. **Create reusable validators** as functions or classes
4. **Use Annotated types** for reusable custom types
5. **Validate early** - at API boundary
6. **Return clear error messages** with field context
7. **Use dependencies** for async validation
8. **Document validation rules** in schema descriptions
