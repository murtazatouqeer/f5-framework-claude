# FastAPI CRUD API Example

Complete CRUD API example demonstrating the FastAPI stack patterns with Product entity.

## Directory Structure

```
crud-api/
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py           # Settings management
│   │   ├── database.py         # Database connection
│   │   └── exceptions.py       # Custom exceptions
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py             # Base model with mixins
│   │   └── product.py          # Product model
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── response.py         # API response wrapper
│   │   └── product.py          # Product schemas
│   ├── repositories/
│   │   ├── __init__.py
│   │   └── product.py          # Product repository
│   ├── services/
│   │   ├── __init__.py
│   │   └── product.py          # Product service
│   └── api/
│       ├── __init__.py
│       ├── deps.py             # Dependencies
│       └── v1/
│           ├── __init__.py
│           ├── router.py       # API router
│           └── endpoints/
│               ├── __init__.py
│               └── products.py # Product endpoints
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Test fixtures
│   └── api/
│       ├── __init__.py
│       └── test_products.py    # Product API tests
├── alembic/
│   ├── env.py
│   └── versions/
├── alembic.ini
├── pyproject.toml
└── .env.example
```

## Implementation

### 1. Configuration (`app/core/config.py`)

```python
"""Application configuration."""
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # API
    app_name: str = "CRUD API Example"
    debug: bool = False
    api_prefix: str = "/api/v1"

    # Database
    database_url: str = "postgresql+asyncpg://user:pass@localhost/db"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
```

### 2. Database (`app/core/database.py`)

```python
"""Database connection and session management."""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    echo=settings.debug,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Provide database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

### 3. Base Model (`app/models/base.py`)

```python
"""Base model with common mixins."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarative class."""
    pass


class TimestampMixin:
    """Adds created_at and updated_at timestamps."""

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
    """Adds soft delete capability."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None


class BaseModel(Base, TimestampMixin, SoftDeleteMixin):
    """Base model with UUID primary key and mixins."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )
```

### 4. Product Model (`app/models/product.py`)

```python
"""Product database model."""
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Product(BaseModel):
    """Product model."""

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    sku: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )
    stock: Mapped[int] = mapped_column(default=0)
    status: Mapped[str] = mapped_column(
        String(50),
        default="draft",
        index=True,
    )

    __table_args__ = (
        Index("ix_products_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Product {self.name}>"
```

### 5. Product Schemas (`app/schemas/product.py`)

```python
"""Product Pydantic schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductBase(BaseModel):
    """Base product schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Decimal = Field(..., gt=0, decimal_places=2)
    sku: str = Field(..., min_length=1, max_length=100)


class ProductCreate(ProductBase):
    """Schema for creating a product."""

    stock: int = Field(default=0, ge=0)
    status: str = Field(default="draft", pattern="^(draft|active|archived)$")

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip()


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=2000)
    price: Optional[Decimal] = Field(None, gt=0)
    sku: Optional[str] = Field(None, min_length=1, max_length=100)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[str] = Field(None, pattern="^(draft|active|archived)$")

    model_config = ConfigDict(extra="ignore")


class ProductResponse(ProductBase):
    """Schema for product response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    stock: int
    status: str
    created_at: datetime
    updated_at: datetime


class ProductListItem(BaseModel):
    """Simplified schema for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    price: Decimal
    status: str
    stock: int
    created_at: datetime


class ProductListResponse(BaseModel):
    """Paginated list response."""

    items: list[ProductListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
```

### 6. Product Repository (`app/repositories/product.py`)

```python
"""Product repository for data access."""
from typing import Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from slugify import slugify

from app.models.product import Product


class ProductRepository:
    """Repository for Product data access."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, id: UUID) -> Optional[Product]:
        """Get product by ID."""
        result = await self._session.execute(
            select(Product).where(
                Product.id == id,
                Product.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Product]:
        """Get product by slug."""
        result = await self._session.execute(
            select(Product).where(
                Product.slug == slug,
                Product.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        result = await self._session.execute(
            select(Product).where(
                Product.sku == sku,
                Product.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[Product]:
        """List products with filtering."""
        query = select(Product).where(Product.deleted_at.is_(None))

        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))

        if status:
            query = query.where(Product.status == status)

        # Apply sorting
        sort_column = getattr(Product, sort_by, Product.created_at)
        if sort_order == "desc":
            sort_column = sort_column.desc()
        query = query.order_by(sort_column)

        query = query.offset(offset).limit(limit)

        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
    ) -> int:
        """Count products with filtering."""
        query = select(func.count(Product.id)).where(
            Product.deleted_at.is_(None)
        )

        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))

        if status:
            query = query.where(Product.status == status)

        result = await self._session.execute(query)
        return result.scalar_one()

    async def create(self, data: dict) -> Product:
        """Create a new product."""
        # Generate slug from name
        data["slug"] = slugify(data["name"])

        product = Product(**data)
        self._session.add(product)
        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def update(self, id: UUID, data: dict) -> Product:
        """Update a product."""
        product = await self.get_by_id(id)

        for key, value in data.items():
            if hasattr(product, key):
                setattr(product, key, value)

        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def soft_delete(self, id: UUID) -> None:
        """Soft delete a product."""
        from datetime import datetime, timezone

        product = await self.get_by_id(id)
        product.deleted_at = datetime.now(timezone.utc)
        await self._session.flush()
```

### 7. Product Service (`app/services/product.py`)

```python
"""Product service layer."""
from typing import Optional
from uuid import UUID

from slugify import slugify

from app.core.exceptions import ConflictError, NotFoundError
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.schemas.product import (
    ProductCreate,
    ProductListItem,
    ProductListResponse,
    ProductUpdate,
)


class ProductService:
    """Service for Product business logic."""

    def __init__(self, repository: ProductRepository):
        self._repo = repository

    async def get_by_id(self, id: UUID) -> Product:
        """Get product by ID."""
        product = await self._repo.get_by_id(id)
        if not product:
            raise NotFoundError(f"Product with ID {id} not found")
        return product

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> ProductListResponse:
        """List products with pagination."""
        offset = (page - 1) * page_size

        items = await self._repo.list(
            offset=offset,
            limit=page_size,
            search=search,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        total = await self._repo.count(search=search, status=status)
        total_pages = (total + page_size - 1) // page_size

        return ProductListResponse(
            items=[ProductListItem.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def create(self, data: ProductCreate) -> Product:
        """Create a new product."""
        # Check for duplicate slug
        slug = slugify(data.name)
        existing = await self._repo.get_by_slug(slug)
        if existing:
            raise ConflictError("Product with this name already exists")

        # Check for duplicate SKU
        existing_sku = await self._repo.get_by_sku(data.sku)
        if existing_sku:
            raise ConflictError("Product with this SKU already exists")

        return await self._repo.create(data.model_dump())

    async def update(self, id: UUID, data: ProductUpdate) -> Product:
        """Update a product."""
        product = await self.get_by_id(id)

        update_data = data.model_dump(exclude_unset=True)

        # Check slug uniqueness if name changed
        if "name" in update_data:
            new_slug = slugify(update_data["name"])
            if new_slug != product.slug:
                existing = await self._repo.get_by_slug(new_slug)
                if existing and existing.id != id:
                    raise ConflictError("Product with this name already exists")
                update_data["slug"] = new_slug

        # Check SKU uniqueness if changed
        if "sku" in update_data and update_data["sku"] != product.sku:
            existing = await self._repo.get_by_sku(update_data["sku"])
            if existing and existing.id != id:
                raise ConflictError("Product with this SKU already exists")

        return await self._repo.update(id, update_data)

    async def delete(self, id: UUID) -> None:
        """Delete a product."""
        await self.get_by_id(id)  # Verify exists
        await self._repo.soft_delete(id)
```

### 8. Dependencies (`app/api/deps.py`)

```python
"""API dependencies."""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.product import ProductRepository
from app.services.product import ProductService

DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_product_service(db: DBSession) -> ProductService:
    """Provide ProductService dependency."""
    repository = ProductRepository(db)
    return ProductService(repository)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
```

### 9. Product Endpoints (`app/api/v1/endpoints/products.py`)

```python
"""Product API endpoints."""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.api.deps import ProductServiceDep
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.schemas.response import APIResponse

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=APIResponse[ProductListResponse])
async def list_products(
    service: ProductServiceDep,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[Optional[str], Query(max_length=100)] = None,
    status: Annotated[Optional[str], Query(pattern="^(draft|active|archived)$")] = None,
    sort_by: str = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
):
    """List all products with pagination."""
    result = await service.list(
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return APIResponse(success=True, data=result)


@router.get("/{id}", response_model=APIResponse[ProductResponse])
async def get_product(id: UUID, service: ProductServiceDep):
    """Get product by ID."""
    product = await service.get_by_id(id)
    return APIResponse(success=True, data=ProductResponse.model_validate(product))


@router.post(
    "/",
    response_model=APIResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_product(data: ProductCreate, service: ProductServiceDep):
    """Create a new product."""
    product = await service.create(data)
    return APIResponse(success=True, data=ProductResponse.model_validate(product))


@router.put("/{id}", response_model=APIResponse[ProductResponse])
async def update_product(id: UUID, data: ProductUpdate, service: ProductServiceDep):
    """Update product by ID."""
    product = await service.update(id, data)
    return APIResponse(success=True, data=ProductResponse.model_validate(product))


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(id: UUID, service: ProductServiceDep):
    """Delete product by ID."""
    await service.delete(id)
    return None
```

### 10. Main Application (`app/main.py`)

```python
"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
```

## Testing

### Test Configuration (`tests/conftest.py`)

```python
"""Test fixtures."""
import asyncio
from typing import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.base import Base

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide test client."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_product(db_session: AsyncSession):
    """Create test product."""
    from app.models.product import Product

    product = Product(
        id=uuid4(),
        name="Test Product",
        slug="test-product",
        description="A test product",
        price=29.99,
        sku=f"TEST-{uuid4().hex[:8].upper()}",
        stock=100,
        status="active",
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product
```

### Product API Tests (`tests/api/test_products.py`)

```python
"""Product API tests."""
import pytest
from httpx import AsyncClient


class TestListProducts:
    """Tests for GET /products/"""

    @pytest.mark.asyncio
    async def test_list_products_empty(self, client: AsyncClient):
        """Test listing products when empty."""
        response = await client.get("/api/v1/products/")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["items"] == []
        assert data["data"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_products_with_data(self, client: AsyncClient, test_product):
        """Test listing products with data."""
        response = await client.get("/api/v1/products/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]["items"]) == 1
        assert data["data"]["items"][0]["name"] == "Test Product"


class TestCreateProduct:
    """Tests for POST /products/"""

    @pytest.mark.asyncio
    async def test_create_product_success(self, client: AsyncClient):
        """Test creating a product."""
        payload = {
            "name": "New Product",
            "description": "A new product",
            "price": 19.99,
            "sku": "NEW-001",
        }

        response = await client.post("/api/v1/products/", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "New Product"
        assert "id" in data["data"]
        assert data["data"]["slug"] == "new-product"

    @pytest.mark.asyncio
    async def test_create_product_validation_error(self, client: AsyncClient):
        """Test creating with invalid data."""
        payload = {
            "name": "",
            "price": -10,
            "sku": "BAD",
        }

        response = await client.post("/api/v1/products/", json=payload)

        assert response.status_code == 422


class TestGetProduct:
    """Tests for GET /products/{id}"""

    @pytest.mark.asyncio
    async def test_get_product_success(self, client: AsyncClient, test_product):
        """Test getting a product by ID."""
        response = await client.get(f"/api/v1/products/{test_product.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == str(test_product.id)

    @pytest.mark.asyncio
    async def test_get_product_not_found(self, client: AsyncClient):
        """Test getting non-existent product."""
        from uuid import uuid4

        response = await client.get(f"/api/v1/products/{uuid4()}")

        assert response.status_code == 404


class TestUpdateProduct:
    """Tests for PUT /products/{id}"""

    @pytest.mark.asyncio
    async def test_update_product_success(self, client: AsyncClient, test_product):
        """Test updating a product."""
        payload = {"name": "Updated Product", "price": 39.99}

        response = await client.put(
            f"/api/v1/products/{test_product.id}",
            json=payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"]["name"] == "Updated Product"


class TestDeleteProduct:
    """Tests for DELETE /products/{id}"""

    @pytest.mark.asyncio
    async def test_delete_product_success(self, client: AsyncClient, test_product):
        """Test deleting a product."""
        response = await client.delete(f"/api/v1/products/{test_product.id}")

        assert response.status_code == 204

        # Verify deletion
        get_response = await client.get(f"/api/v1/products/{test_product.id}")
        assert get_response.status_code == 404
```

## Running the Example

```bash
# Install dependencies
pip install -e ".[dev]"

# Set up database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload

# Run tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## Key Patterns Demonstrated

1. **Clean Architecture**: Separation of concerns with layers
2. **Repository Pattern**: Data access abstraction
3. **Service Layer**: Business logic isolation
4. **Dependency Injection**: FastAPI Depends system
5. **Pydantic v2**: Modern validation with ConfigDict
6. **SQLAlchemy 2.0**: Async with Mapped types
7. **Soft Delete**: Non-destructive data removal
8. **Pagination**: Cursor-free page-based pagination
9. **Testing**: Async fixtures and client
