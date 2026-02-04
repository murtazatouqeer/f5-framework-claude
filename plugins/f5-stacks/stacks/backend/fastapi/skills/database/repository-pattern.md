---
name: fastapi-repository-pattern
description: Repository pattern implementation for FastAPI
applies_to: fastapi
category: skill
---

# Repository Pattern in FastAPI

## Overview

The Repository pattern abstracts data access logic, providing a clean separation
between business logic and data access. This enables easier testing and flexibility
to change data sources.

## Abstract Repository Interface

```python
# app/repositories/interfaces.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Sequence, Optional, Any
from uuid import UUID

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Abstract repository interface."""

    @abstractmethod
    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        **filters,
    ) -> Sequence[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create new entity."""
        pass

    @abstractmethod
    async def update(self, id: UUID, data: dict[str, Any]) -> Optional[T]:
        """Update entity by ID."""
        pass

    @abstractmethod
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID."""
        pass

    @abstractmethod
    async def count(self, **filters) -> int:
        """Count entities."""
        pass

    @abstractmethod
    async def exists(self, **filters) -> bool:
        """Check if entity exists."""
        pass
```

## Base Repository Implementation

```python
# app/repositories/base.py
from typing import TypeVar, Generic, Type, Sequence, Optional, Any
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy import select, func, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.base import BaseModel
from app.repositories.interfaces import IRepository

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType], IRepository[ModelType]):
    """Base SQLAlchemy repository implementation."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self._model = model
        self._session = session

    @property
    def model(self) -> Type[ModelType]:
        return self._model

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get entity by ID (excludes soft-deleted)."""
        stmt = select(self._model).where(
            self._model.id == id,
            self._model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_with_deleted(self, id: UUID) -> Optional[ModelType]:
        """Get entity by ID (includes soft-deleted)."""
        stmt = select(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[UUID]) -> Sequence[ModelType]:
        """Get multiple entities by IDs."""
        if not ids:
            return []
        stmt = select(self._model).where(
            self._model.id.in_(ids),
            self._model.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        order_desc: bool = True,
        **filters,
    ) -> Sequence[ModelType]:
        """Get all entities with pagination and filters."""
        stmt = self._build_query(**filters)

        # Ordering
        order_column = getattr(self._model, order_by, self._model.created_at)
        if order_desc:
            stmt = stmt.order_by(order_column.desc())
        else:
            stmt = stmt.order_by(order_column.asc())

        # Pagination
        stmt = stmt.offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def create(self, entity: ModelType) -> ModelType:
        """Create new entity."""
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def create_from_dict(self, data: dict[str, Any]) -> ModelType:
        """Create entity from dictionary."""
        entity = self._model(**data)
        return await self.create(entity)

    async def create_many(self, entities: list[ModelType]) -> Sequence[ModelType]:
        """Create multiple entities."""
        self._session.add_all(entities)
        await self._session.flush()
        for entity in entities:
            await self._session.refresh(entity)
        return entities

    async def update(self, id: UUID, data: dict[str, Any]) -> Optional[ModelType]:
        """Update entity by ID."""
        entity = await self.get_by_id(id)
        if not entity:
            return None

        for key, value in data.items():
            if hasattr(entity, key) and key not in ("id", "created_at"):
                setattr(entity, key, value)

        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update_many(
        self,
        ids: list[UUID],
        data: dict[str, Any],
    ) -> int:
        """Update multiple entities."""
        stmt = (
            update(self._model)
            .where(self._model.id.in_(ids))
            .values(**data)
        )
        result = await self._session.execute(stmt)
        return result.rowcount

    async def delete(self, id: UUID) -> bool:
        """Soft delete entity."""
        stmt = (
            update(self._model)
            .where(self._model.id == id, self._model.deleted_at.is_(None))
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def hard_delete(self, id: UUID) -> bool:
        """Permanently delete entity."""
        stmt = delete(self._model).where(self._model.id == id)
        result = await self._session.execute(stmt)
        return result.rowcount > 0

    async def restore(self, id: UUID) -> Optional[ModelType]:
        """Restore soft-deleted entity."""
        stmt = (
            update(self._model)
            .where(self._model.id == id, self._model.deleted_at.is_not(None))
            .values(deleted_at=None)
        )
        result = await self._session.execute(stmt)
        if result.rowcount > 0:
            return await self.get_by_id(id)
        return None

    async def count(self, **filters) -> int:
        """Count entities matching filters."""
        stmt = self._build_query(**filters)
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self._session.execute(count_stmt)
        return result.scalar_one()

    async def exists(self, **filters) -> bool:
        """Check if entity exists."""
        return await self.count(**filters) > 0

    def _build_query(self, **filters):
        """Build base query with filters."""
        stmt = select(self._model).where(self._model.deleted_at.is_(None))

        conditions = []
        for key, value in filters.items():
            if value is not None and hasattr(self._model, key):
                conditions.append(getattr(self._model, key) == value)

        if conditions:
            stmt = stmt.where(and_(*conditions))

        return stmt
```

## Specific Repository Implementation

```python
# app/repositories/product.py
from typing import Sequence, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy import select, or_, and_, func
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductStatus
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for Product model with specific methods."""

    def __init__(self, session):
        super().__init__(Product, session)

    # Custom finder methods
    async def get_by_slug(self, slug: str) -> Optional[Product]:
        """Get product by slug."""
        stmt = select(Product).where(
            Product.slug == slug,
            Product.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Optional[Product]:
        """Get product by SKU."""
        stmt = select(Product).where(
            Product.sku == sku,
            Product.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # Eager loading
    async def get_with_relations(self, id: UUID) -> Optional[Product]:
        """Get product with all relationships loaded."""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.created_by),
                selectinload(Product.tags),
            )
            .where(Product.id == id, Product.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # Category filtering
    async def get_by_category(
        self,
        category_id: UUID,
        *,
        status: ProductStatus = ProductStatus.ACTIVE,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Product]:
        """Get products by category."""
        stmt = (
            select(Product)
            .where(
                Product.category_id == category_id,
                Product.status == status,
                Product.deleted_at.is_(None),
            )
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    # Search with pagination
    async def search(
        self,
        *,
        query: Optional[str] = None,
        category_id: Optional[UUID] = None,
        status: Optional[ProductStatus] = None,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        in_stock: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Product], int]:
        """Search products with multiple filters."""
        base_stmt = select(Product).where(Product.deleted_at.is_(None))

        # Build filters
        filters = []

        if query:
            filters.append(
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%"),
                    Product.sku.ilike(f"%{query}%"),
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

        if in_stock is not None:
            if in_stock:
                filters.append(Product.stock > 0)
            else:
                filters.append(Product.stock == 0)

        if filters:
            base_stmt = base_stmt.where(and_(*filters))

        # Count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        count_result = await self._session.execute(count_stmt)
        total = count_result.scalar_one()

        # Data with pagination
        data_stmt = (
            base_stmt
            .options(selectinload(Product.category))
            .order_by(Product.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(data_stmt)
        items = result.scalars().all()

        return items, total

    # Inventory operations
    async def update_stock(
        self,
        id: UUID,
        quantity_change: int,
    ) -> Optional[Product]:
        """Update product stock (positive to add, negative to subtract)."""
        product = await self.get_by_id(id)
        if not product:
            return None

        new_stock = product.stock + quantity_change
        if new_stock < 0:
            raise ValueError("Insufficient stock")

        product.stock = new_stock
        await self._session.flush()
        await self._session.refresh(product)
        return product

    async def get_low_stock(
        self,
        threshold: int = 10,
    ) -> Sequence[Product]:
        """Get products with low stock."""
        stmt = (
            select(Product)
            .where(
                Product.stock <= threshold,
                Product.status == ProductStatus.ACTIVE,
                Product.deleted_at.is_(None),
            )
            .order_by(Product.stock.asc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    # Aggregations
    async def get_stats_by_category(self) -> list[dict]:
        """Get product statistics grouped by category."""
        stmt = (
            select(
                Product.category_id,
                func.count(Product.id).label("product_count"),
                func.avg(Product.price).label("avg_price"),
                func.sum(Product.stock).label("total_stock"),
            )
            .where(Product.deleted_at.is_(None))
            .group_by(Product.category_id)
        )
        result = await self._session.execute(stmt)
        return [dict(row._mapping) for row in result.all()]
```

## Using Repositories in Services

```python
# app/services/product.py
from typing import Sequence, Optional
from uuid import UUID
from slugify import slugify

from app.models.product import Product, ProductStatus
from app.models.user import User
from app.repositories.product import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate
from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError


class ProductService:
    """Product business logic service."""

    def __init__(self, repository: ProductRepository):
        self._repo = repository

    async def create(
        self,
        data: ProductCreate,
        user: User,
    ) -> Product:
        """Create new product."""
        # Check for duplicate slug
        slug = slugify(data.name)
        existing = await self._repo.get_by_slug(slug)
        if existing:
            raise ConflictError("Product with this name already exists")

        # Check for duplicate SKU
        if await self._repo.get_by_sku(data.sku):
            raise ConflictError("Product with this SKU already exists")

        return await self._repo.create_from_dict({
            **data.model_dump(),
            "slug": slug,
            "created_by_id": user.id,
            "status": ProductStatus.DRAFT,
        })

    async def get_by_id(self, id: UUID) -> Product:
        """Get product by ID."""
        product = await self._repo.get_with_relations(id)
        if not product:
            raise NotFoundError("Product not found")
        return product

    async def list(
        self,
        *,
        query: Optional[str] = None,
        category_id: Optional[UUID] = None,
        status: Optional[ProductStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Product], int]:
        """List products with filters."""
        return await self._repo.search(
            query=query,
            category_id=category_id,
            status=status,
            skip=skip,
            limit=limit,
        )

    async def update(
        self,
        id: UUID,
        data: ProductUpdate,
        user: User,
    ) -> Product:
        """Update product."""
        product = await self._repo.get_by_id(id)
        if not product:
            raise NotFoundError("Product not found")

        # Check ownership
        if product.created_by_id != user.id and not user.is_admin:
            raise ForbiddenError("Not authorized to update this product")

        update_data = data.model_dump(exclude_unset=True)

        # Update slug if name changed
        if "name" in update_data:
            update_data["slug"] = slugify(update_data["name"])

        updated = await self._repo.update(id, update_data)
        return updated

    async def delete(self, id: UUID, user: User) -> bool:
        """Delete product."""
        product = await self._repo.get_by_id(id)
        if not product:
            raise NotFoundError("Product not found")

        if product.created_by_id != user.id and not user.is_admin:
            raise ForbiddenError("Not authorized to delete this product")

        return await self._repo.delete(id)
```

## Dependency Injection

```python
# app/api/deps.py
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.product import ProductRepository
from app.services.product import ProductService


def get_product_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ProductRepository:
    return ProductRepository(db)


def get_product_service(
    repo: Annotated[ProductRepository, Depends(get_product_repository)],
) -> ProductService:
    return ProductService(repo)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
```

## Testing with Mock Repository

```python
# tests/services/test_product.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.product import ProductService
from app.schemas.product import ProductCreate


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    return ProductService(mock_repo)


@pytest.mark.asyncio
async def test_create_product(service, mock_repo):
    """Test product creation."""
    mock_repo.get_by_slug.return_value = None
    mock_repo.get_by_sku.return_value = None
    mock_repo.create_from_dict.return_value = MagicMock(id=uuid4())

    user = MagicMock(id=uuid4())
    data = ProductCreate(
        name="Test Product",
        sku="TEST-001",
        price=99.99,
        category_id=uuid4(),
    )

    result = await service.create(data, user)

    mock_repo.create_from_dict.assert_called_once()
    assert result is not None
```

## Benefits

1. **Testability**: Easy to mock repositories for unit testing
2. **Abstraction**: Business logic doesn't know about SQLAlchemy
3. **Reusability**: Common CRUD operations in base repository
4. **Flexibility**: Can swap data sources without changing services
5. **Clean code**: Clear separation of concerns
