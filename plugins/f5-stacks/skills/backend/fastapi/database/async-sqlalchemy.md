---
name: fastapi-async-sqlalchemy
description: Async SQLAlchemy patterns for FastAPI
applies_to: fastapi
category: skill
---

# Async SQLAlchemy in FastAPI

## Setup

```python
# app/database.py
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    """Base class for all models."""
    pass


def create_engine() -> AsyncEngine:
    """Create async database engine."""
    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_pre_ping=True,  # Enable connection health checks
        pool_recycle=3600,   # Recycle connections after 1 hour
    )


# For testing, use NullPool to avoid connection issues
def create_test_engine() -> AsyncEngine:
    """Create test database engine."""
    return create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=True,
        poolclass=NullPool,
    )


engine = create_engine()

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## Connection Pooling Configuration

```python
# Production configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    # Pool settings
    pool_size=5,              # Number of connections to keep open
    max_overflow=10,          # Additional connections when pool is exhausted
    pool_timeout=30,          # Seconds to wait for available connection
    pool_recycle=1800,        # Recycle connections after 30 minutes
    pool_pre_ping=True,       # Check connection validity before use

    # Performance settings
    echo=False,               # Disable SQL logging in production
    echo_pool=False,          # Disable pool logging

    # PostgreSQL specific
    connect_args={
        "server_settings": {
            "application_name": "fastapi_app",
            "jit": "off",     # Disable JIT for short queries
        }
    },
)
```

## Async Repository Pattern

```python
# app/repositories/base.py
from typing import TypeVar, Generic, Type, Sequence, Any
from uuid import UUID
from sqlalchemy import select, func, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    """Base repository with common async CRUD operations."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Get single record by ID."""
        stmt = select(self.model).where(
            self.model.id == id,
            self.model.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[UUID]) -> Sequence[ModelType]:
        """Get multiple records by IDs."""
        stmt = select(self.model).where(
            self.model.id.in_(ids),
            self.model.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Get all records with pagination."""
        stmt = (
            select(self.model)
            .where(self.model.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(self.model.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, **filters) -> int:
        """Count all records."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(self.model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def exists(self, **filters) -> bool:
        """Check if record exists."""
        stmt = (
            select(func.count())
            .select_from(self.model)
            .filter_by(**filters)
            .where(self.model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one() > 0

    async def create(self, **data) -> ModelType:
        """Create new record."""
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def create_many(self, items: list[dict]) -> Sequence[ModelType]:
        """Create multiple records."""
        instances = [self.model(**item) for item in items]
        self.session.add_all(instances)
        await self.session.flush()
        for instance in instances:
            await self.session.refresh(instance)
        return instances

    async def update(self, id: UUID, **data) -> ModelType | None:
        """Update record by ID."""
        instance = await self.get_by_id(id)
        if not instance:
            return None

        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update_many(self, ids: list[UUID], **data) -> int:
        """Update multiple records."""
        stmt = (
            update(self.model)
            .where(self.model.id.in_(ids))
            .values(**data)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def delete(self, id: UUID) -> bool:
        """Soft delete record."""
        from datetime import datetime, timezone

        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(deleted_at=datetime.now(timezone.utc))
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    async def hard_delete(self, id: UUID) -> bool:
        """Permanently delete record."""
        stmt = delete(self.model).where(self.model.id == id)
        result = await self.session.execute(stmt)
        return result.rowcount > 0
```

## Specific Repository Implementation

```python
# app/repositories/product.py
from typing import Sequence
from uuid import UUID
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.models.product import Product, ProductStatus
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """Repository for Product model."""

    def __init__(self, session):
        super().__init__(Product, session)

    async def get_by_slug(self, slug: str) -> Product | None:
        """Get product by slug."""
        stmt = select(Product).where(
            Product.slug == slug,
            Product.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Product | None:
        """Get product by SKU."""
        stmt = select(Product).where(
            Product.sku == sku,
            Product.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_relations(self, id: UUID) -> Product | None:
        """Get product with all relations loaded."""
        stmt = (
            select(Product)
            .options(
                selectinload(Product.category),
                selectinload(Product.created_by),
            )
            .where(Product.id == id, Product.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_category(
        self,
        category_id: UUID,
        *,
        skip: int = 0,
        limit: int = 100,
        status: ProductStatus = ProductStatus.ACTIVE,
    ) -> Sequence[Product]:
        """Get products by category."""
        stmt = (
            select(Product)
            .where(
                Product.category_id == category_id,
                Product.status == status,
                Product.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
            .order_by(Product.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search(
        self,
        *,
        query: str | None = None,
        category_id: UUID | None = None,
        status: ProductStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[Sequence[Product], int]:
        """Search products with filters."""
        base = select(Product).where(Product.deleted_at.is_(None))

        if query:
            base = base.where(
                or_(
                    Product.name.ilike(f"%{query}%"),
                    Product.description.ilike(f"%{query}%"),
                )
            )
        if category_id:
            base = base.where(Product.category_id == category_id)
        if status:
            base = base.where(Product.status == status)

        # Count
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(base.subquery())
        count_result = await self.session.execute(count_stmt)
        total = count_result.scalar_one()

        # Data
        data_stmt = base.offset(skip).limit(limit).order_by(Product.created_at.desc())
        result = await self.session.execute(data_stmt)
        items = result.scalars().all()

        return items, total

    async def update_stock(self, id: UUID, quantity: int) -> bool:
        """Update product stock."""
        from sqlalchemy import update as sql_update

        stmt = (
            sql_update(Product)
            .where(Product.id == id)
            .values(stock=Product.stock + quantity)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0
```

## Transaction Management

```python
# Manual transaction control
async def transfer_stock(
    session: AsyncSession,
    source_id: UUID,
    target_id: UUID,
    quantity: int,
) -> bool:
    """Transfer stock between products with transaction."""
    try:
        # Start explicit transaction
        async with session.begin():
            # Decrease source stock
            source = await session.get(Product, source_id)
            if not source or source.stock < quantity:
                raise ValueError("Insufficient stock")

            source.stock -= quantity

            # Increase target stock
            target = await session.get(Product, target_id)
            if not target:
                raise ValueError("Target product not found")

            target.stock += quantity

            # Commit happens automatically on context exit
        return True
    except Exception:
        # Rollback happens automatically on exception
        raise


# Using savepoints for nested transactions
async def complex_operation(session: AsyncSession):
    """Complex operation with savepoints."""
    async with session.begin_nested():  # Savepoint
        # This can be rolled back independently
        ...

    # Continue with main transaction
    ...
```

## Concurrent Operations

```python
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession


async def fetch_product_details(
    session: AsyncSession,
    product_id: UUID,
) -> dict:
    """Fetch product with concurrent related data."""
    # Run queries concurrently
    product_task = asyncio.create_task(
        get_product(session, product_id)
    )
    reviews_task = asyncio.create_task(
        get_product_reviews(session, product_id)
    )
    stats_task = asyncio.create_task(
        get_product_stats(session, product_id)
    )

    product, reviews, stats = await asyncio.gather(
        product_task,
        reviews_task,
        stats_task,
    )

    return {
        "product": product,
        "reviews": reviews,
        "stats": stats,
    }
```

## Best Practices

1. **Always use async context** for database operations
2. **Use `selectinload`** for eager loading relationships
3. **Flush instead of commit** in repositories (let dependency handle commit)
4. **Use `expire_on_commit=False`** to avoid detached instance errors
5. **Implement soft delete** for important data
6. **Use connection pooling** appropriately for production
7. **Enable `pool_pre_ping`** to handle stale connections
