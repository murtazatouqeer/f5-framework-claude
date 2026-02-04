---
name: fastapi-service
description: Service layer template for FastAPI
applies_to: fastapi
category: template
variables:
  - name: entity_name
    description: Entity name in PascalCase (e.g., Product)
  - name: entity_lower
    description: Lowercase entity name (e.g., product)
---

# Service Layer Template

## Template

```python
# app/services/{{entity_lower}}.py
"""
{{entity_name}} service layer.

REQ-XXX: {{entity_name}} business logic
"""
from typing import Optional
from uuid import UUID

from slugify import slugify

from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError
from app.models.{{entity_lower}} import {{entity_name}}
from app.models.user import User
from app.repositories.{{entity_lower}} import {{entity_name}}Repository
from app.schemas.{{entity_lower}} import (
    {{entity_name}}Create,
    {{entity_name}}Update,
    {{entity_name}}ListResponse,
    {{entity_name}}ListItem,
)


class {{entity_name}}Service:
    """Service for {{entity_name}} business logic."""

    def __init__(self, repository: {{entity_name}}Repository):
        self._repo = repository

    # ========================================================================
    # Read Operations
    # ========================================================================

    async def get_by_id(self, id: UUID) -> {{entity_name}}:
        """
        Get {{entity_lower}} by ID.

        Raises:
            NotFoundError: If {{entity_lower}} not found.
        """
        {{entity_lower}} = await self._repo.get_by_id(id)
        if not {{entity_lower}}:
            raise NotFoundError(
                message=f"{{entity_name}} with ID {id} not found",
                resource="{{entity_lower}}",
            )
        return {{entity_lower}}

    async def get_by_slug(self, slug: str) -> {{entity_name}}:
        """
        Get {{entity_lower}} by slug.

        Raises:
            NotFoundError: If {{entity_lower}} not found.
        """
        {{entity_lower}} = await self._repo.get_by_slug(slug)
        if not {{entity_lower}}:
            raise NotFoundError(
                message=f"{{entity_name}} with slug '{slug}' not found",
                resource="{{entity_lower}}",
            )
        return {{entity_lower}}

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        **filters,
    ) -> {{entity_name}}ListResponse:
        """List {{entity_plural}} with pagination and filtering."""
        offset = (page - 1) * page_size

        items = await self._repo.list(
            offset=offset,
            limit=page_size,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            **filters,
        )

        total = await self._repo.count(search=search, **filters)
        total_pages = (total + page_size - 1) // page_size

        return {{entity_name}}ListResponse(
            items=[{{entity_name}}ListItem.model_validate(item) for item in items],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    # ========================================================================
    # Write Operations
    # ========================================================================

    async def create(
        self,
        data: {{entity_name}}Create,
        current_user: User,
    ) -> {{entity_name}}:
        """
        Create a new {{entity_lower}}.

        Raises:
            ConflictError: If {{entity_lower}} with same slug/sku exists.
        """
        # Generate slug from name
        slug = slugify(data.name)

        # Check for duplicate slug
        existing = await self._repo.get_by_slug(slug)
        if existing:
            raise ConflictError(
                message="{{entity_name}} with this name already exists",
                field="name",
            )

        # Check for duplicate SKU
        existing_sku = await self._repo.get_by_sku(data.sku)
        if existing_sku:
            raise ConflictError(
                message="{{entity_name}} with this SKU already exists",
                field="sku",
            )

        # Create {{entity_lower}}
        {{entity_lower}} = await self._repo.create({
            **data.model_dump(),
            "slug": slug,
            "created_by_id": current_user.id,
        })

        return {{entity_lower}}

    async def update(
        self,
        id: UUID,
        data: {{entity_name}}Update,
        current_user: User,
        partial: bool = False,
    ) -> {{entity_name}}:
        """
        Update {{entity_lower}} by ID.

        Raises:
            NotFoundError: If {{entity_lower}} not found.
            ForbiddenError: If user lacks permission.
            ConflictError: If update causes conflict.
        """
        {{entity_lower}} = await self.get_by_id(id)

        # Check ownership
        self._check_ownership({{entity_lower}}, current_user)

        # Prepare update data
        if partial:
            update_data = data.model_dump(exclude_unset=True)
        else:
            update_data = data.model_dump()

        # Update slug if name changed
        if "name" in update_data and update_data["name"]:
            new_slug = slugify(update_data["name"])
            if new_slug != {{entity_lower}}.slug:
                existing = await self._repo.get_by_slug(new_slug)
                if existing and existing.id != id:
                    raise ConflictError(
                        message="{{entity_name}} with this name already exists",
                        field="name",
                    )
                update_data["slug"] = new_slug

        # Check SKU uniqueness if changed
        if "sku" in update_data and update_data["sku"] != {{entity_lower}}.sku:
            existing_sku = await self._repo.get_by_sku(update_data["sku"])
            if existing_sku and existing_sku.id != id:
                raise ConflictError(
                    message="{{entity_name}} with this SKU already exists",
                    field="sku",
                )

        # Perform update
        updated = await self._repo.update(id, update_data)
        return updated

    async def delete(self, id: UUID, current_user: User) -> None:
        """
        Delete {{entity_lower}} by ID.

        Raises:
            NotFoundError: If {{entity_lower}} not found.
            ForbiddenError: If user lacks permission.
        """
        {{entity_lower}} = await self.get_by_id(id)

        # Check ownership
        self._check_ownership({{entity_lower}}, current_user)

        # Soft delete
        await self._repo.soft_delete(id)

    # ========================================================================
    # Business Logic
    # ========================================================================

    async def update_stock(self, id: UUID, quantity: int) -> {{entity_name}}:
        """
        Update {{entity_lower}} stock.

        Raises:
            NotFoundError: If {{entity_lower}} not found.
            ValueError: If stock would become negative.
        """
        {{entity_lower}} = await self.get_by_id(id)

        new_stock = {{entity_lower}}.stock + quantity
        if new_stock < 0:
            raise ValueError("Insufficient stock")

        return await self._repo.update(id, {"stock": new_stock})

    async def publish(self, id: UUID, current_user: User) -> {{entity_name}}:
        """Publish a draft {{entity_lower}}."""
        {{entity_lower}} = await self.get_by_id(id)
        self._check_ownership({{entity_lower}}, current_user)

        if {{entity_lower}}.status != "draft":
            raise ValueError("Only draft {{entity_plural}} can be published")

        return await self._repo.update(id, {"status": "active"})

    async def archive(self, id: UUID, current_user: User) -> {{entity_name}}:
        """Archive a {{entity_lower}}."""
        {{entity_lower}} = await self.get_by_id(id)
        self._check_ownership({{entity_lower}}, current_user)

        return await self._repo.update(id, {"status": "archived"})

    # ========================================================================
    # Helpers
    # ========================================================================

    def _check_ownership(self, {{entity_lower}}: {{entity_name}}, user: User) -> None:
        """
        Check if user owns the {{entity_lower}} or is admin.

        Raises:
            ForbiddenError: If user lacks permission.
        """
        if {{entity_lower}}.created_by_id != user.id and not user.is_admin:
            raise ForbiddenError(
                "You don't have permission to modify this {{entity_lower}}"
            )
```

## Usage

Replace placeholders:
- `{{entity_name}}`: PascalCase entity name (e.g., `Product`)
- `{{entity_lower}}`: Lowercase singular (e.g., `product`)
- `{{entity_plural}}`: Plural lowercase (e.g., `products`)

### Example: Product Service

```python
# app/services/product.py
class ProductService:
    def __init__(self, repository: ProductRepository):
        self._repo = repository

    async def get_by_id(self, id: UUID) -> Product:
        product = await self._repo.get_by_id(id)
        if not product:
            raise NotFoundError("Product not found", resource="product")
        return product
```

### Dependency Registration

```python
# app/api/deps.py
async def get_product_service(
    db: AsyncSession = Depends(get_db),
) -> ProductService:
    repository = ProductRepository(db)
    return ProductService(repository)
```
