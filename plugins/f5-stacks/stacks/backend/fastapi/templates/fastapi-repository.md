---
name: fastapi-repository
description: Repository pattern template for FastAPI
applies_to: fastapi
category: template
variables:
  - name: entity_name
    description: Entity name in PascalCase (e.g., Product)
  - name: entity_lower
    description: Lowercase entity name (e.g., product)
---

# Repository Pattern Template

## Template

```python
# app/repositories/{{entity_lower}}.py
"""
{{entity_name}} repository for data access.

REQ-XXX: {{entity_name}} data persistence
"""
from datetime import datetime
from typing import Optional, List, Any
from uuid import UUID

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.{{entity_lower}} import {{entity_name}}
from app.repositories.base import BaseRepository


class {{entity_name}}Repository(BaseRepository[{{entity_name}}]):
    """Repository for {{entity_name}} data access."""

    model = {{entity_name}}

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    # ========================================================================
    # Read Operations
    # ========================================================================

    async def get_by_id(
        self,
        id: UUID,
        include_deleted: bool = False,
    ) -> Optional[{{entity_name}}]:
        """Get {{entity_lower}} by ID with relationships."""
        query = (
            select(self.model)
            .options(
                selectinload(self.model.category),
                selectinload(self.model.created_by),
            )
            .where(self.model.id == id)
        )

        if not include_deleted:
            query = query.where(self.model.deleted_at.is_(None))

        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[{{entity_name}}]:
        """Get {{entity_lower}} by slug."""
        query = (
            select(self.model)
            .where(self.model.slug == slug)
            .where(self.model.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_sku(self, sku: str) -> Optional[{{entity_name}}]:
        """Get {{entity_lower}} by SKU."""
        query = (
            select(self.model)
            .where(self.model.sku == sku)
            .where(self.model.deleted_at.is_(None))
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list(
        self,
        offset: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        status: Optional[str] = None,
        category_id: Optional[UUID] = None,
        created_by_id: Optional[UUID] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
    ) -> List[{{entity_name}}]:
        """List {{entity_plural}} with filtering and pagination."""
        query = select(self.model).where(self.model.deleted_at.is_(None))

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.description.ilike(search_term),
                    self.model.sku.ilike(search_term),
                )
            )

        if status:
            query = query.where(self.model.status == status)

        if category_id:
            query = query.where(self.model.category_id == category_id)

        if created_by_id:
            query = query.where(self.model.created_by_id == created_by_id)

        if min_price is not None:
            query = query.where(self.model.price >= min_price)

        if max_price is not None:
            query = query.where(self.model.price <= max_price)

        # Apply sorting
        sort_column = getattr(self.model, sort_by, self.model.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count(
        self,
        search: Optional[str] = None,
        status: Optional[str] = None,
        category_id: Optional[UUID] = None,
        **kwargs,
    ) -> int:
        """Count {{entity_plural}} matching filters."""
        query = (
            select(func.count(self.model.id))
            .where(self.model.deleted_at.is_(None))
        )

        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    self.model.name.ilike(search_term),
                    self.model.description.ilike(search_term),
                )
            )

        if status:
            query = query.where(self.model.status == status)

        if category_id:
            query = query.where(self.model.category_id == category_id)

        result = await self.session.execute(query)
        return result.scalar() or 0

    # ========================================================================
    # Write Operations
    # ========================================================================

    async def create(self, data: dict[str, Any]) -> {{entity_name}}:
        """Create a new {{entity_lower}}."""
        {{entity_lower}} = self.model(**data)
        self.session.add({{entity_lower}})
        await self.session.commit()
        await self.session.refresh({{entity_lower}})
        return {{entity_lower}}

    async def update(
        self,
        id: UUID,
        data: dict[str, Any],
    ) -> Optional[{{entity_name}}]:
        """Update {{entity_lower}} by ID."""
        {{entity_lower}} = await self.get_by_id(id)
        if not {{entity_lower}}:
            return None

        for key, value in data.items():
            if hasattr({{entity_lower}}, key):
                setattr({{entity_lower}}, key, value)

        await self.session.commit()
        await self.session.refresh({{entity_lower}})
        return {{entity_lower}}

    async def delete(self, id: UUID) -> bool:
        """Hard delete {{entity_lower}} by ID."""
        {{entity_lower}} = await self.get_by_id(id, include_deleted=True)
        if not {{entity_lower}}:
            return False

        await self.session.delete({{entity_lower}})
        await self.session.commit()
        return True

    async def soft_delete(self, id: UUID) -> bool:
        """Soft delete {{entity_lower}} by ID."""
        {{entity_lower}} = await self.get_by_id(id)
        if not {{entity_lower}}:
            return False

        {{entity_lower}}.deleted_at = datetime.utcnow()
        await self.session.commit()
        return True

    async def restore(self, id: UUID) -> Optional[{{entity_name}}]:
        """Restore soft-deleted {{entity_lower}}."""
        {{entity_lower}} = await self.get_by_id(id, include_deleted=True)
        if not {{entity_lower}}:
            return None

        {{entity_lower}}.deleted_at = None
        await self.session.commit()
        await self.session.refresh({{entity_lower}})
        return {{entity_lower}}

    # ========================================================================
    # Custom Queries
    # ========================================================================

    async def get_featured(self, limit: int = 10) -> List[{{entity_name}}]:
        """Get featured {{entity_plural}}."""
        query = (
            select(self.model)
            .where(self.model.is_featured == True)
            .where(self.model.status == "active")
            .where(self.model.deleted_at.is_(None))
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_category(
        self,
        category_id: UUID,
        limit: int = 20,
    ) -> List[{{entity_name}}]:
        """Get {{entity_plural}} by category."""
        query = (
            select(self.model)
            .where(self.model.category_id == category_id)
            .where(self.model.status == "active")
            .where(self.model.deleted_at.is_(None))
            .order_by(self.model.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_low_stock(self, threshold: int = 10) -> List[{{entity_name}}]:
        """Get {{entity_plural}} with low stock."""
        query = (
            select(self.model)
            .where(self.model.stock <= threshold)
            .where(self.model.status == "active")
            .where(self.model.deleted_at.is_(None))
            .order_by(self.model.stock.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def bulk_update_status(
        self,
        ids: List[UUID],
        status: str,
    ) -> int:
        """Bulk update status for multiple {{entity_plural}}."""
        from sqlalchemy import update

        stmt = (
            update(self.model)
            .where(self.model.id.in_(ids))
            .values(status=status)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
```

## Base Repository

```python
# app/repositories/base.py
from typing import TypeVar, Generic, Optional, List, Any
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    model: type[T]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: UUID) -> Optional[T]:
        query = select(self.model).where(self.model.id == id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100) -> List[T]:
        query = select(self.model).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> T:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: UUID, data: dict[str, Any]) -> Optional[T]:
        instance = await self.get_by_id(id)
        if not instance:
            return None
        for key, value in data.items():
            setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, id: UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False
        await self.session.delete(instance)
        await self.session.commit()
        return True
```

## Usage

Replace placeholders:
- `{{entity_name}}`: PascalCase entity name (e.g., `Product`)
- `{{entity_lower}}`: Lowercase singular (e.g., `product`)
- `{{entity_plural}}`: Plural lowercase (e.g., `products`)
