---
name: fastapi-service-generator
description: Agent for generating service layer classes
applies_to: fastapi
category: agent
inputs:
  - entity_name: Entity name in PascalCase
  - business_rules: List of business rules
  - operations: Required operations
---

# FastAPI Service Generator Agent

## Purpose

Generate service layer classes implementing business logic with proper error handling, validation, and repository integration.

## Activation

- User requests: "create service for [entity]", "generate [entity] business logic"
- When implementing business rules
- When adding service layer to an entity

## Generation Process

### Step 1: Gather Requirements

Ask for or determine:
1. Entity name (PascalCase): e.g., `Product`
2. Repository dependency
3. Business rules and validations
4. Related entities and services
5. Ownership/permission rules
6. Custom business operations

### Step 2: Analyze Business Rules

Identify:
- Uniqueness constraints (slug, email, SKU)
- Ownership rules (who can modify)
- State transitions (draft → active → archived)
- Related entity validations
- Custom business operations

### Step 3: Generate Service

```python
# app/services/{entity_lower}.py
"""
{entity_name} service layer.

REQ-XXX: {entity_name} business logic
"""
from typing import Optional
from uuid import UUID

from slugify import slugify

from app.core.exceptions import NotFoundError, ConflictError, ForbiddenError
from app.models.{entity_lower} import {entity_name}
from app.models.user import User
from app.repositories.{entity_lower} import {entity_name}Repository
from app.schemas.{entity_lower} import (
    {entity_name}Create,
    {entity_name}Update,
    {entity_name}ListResponse,
    {entity_name}ListItem,
)


class {entity_name}Service:
    """
    Service for {entity_name} business logic.

    Handles:
    - CRUD operations with validation
    - Ownership verification
    - Business rule enforcement
    - State transitions
    """

    def __init__(self, repository: {entity_name}Repository):
        """Initialize with repository dependency."""
        self._repo = repository

    # ========================================================================
    # Read Operations
    # ========================================================================

    async def get_by_id(self, id: UUID) -> {entity_name}:
        """
        Get {entity_lower} by ID.

        Args:
            id: {entity_name} UUID

        Returns:
            {entity_name} instance

        Raises:
            NotFoundError: If {entity_lower} not found
        """
        {entity_lower} = await self._repo.get_by_id(id)
        if not {entity_lower}:
            raise NotFoundError(
                message=f"{entity_name} with ID {{id}} not found",
                resource="{entity_lower}",
            )
        return {entity_lower}

    async def get_by_slug(self, slug: str) -> {entity_name}:
        """
        Get {entity_lower} by slug.

        Args:
            slug: URL-friendly identifier

        Returns:
            {entity_name} instance

        Raises:
            NotFoundError: If {entity_lower} not found
        """
        {entity_lower} = await self._repo.get_by_slug(slug)
        if not {entity_lower}:
            raise NotFoundError(
                message=f"{entity_name} with slug '{{slug}}' not found",
                resource="{entity_lower}",
            )
        return {entity_lower}

    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        **filters,
    ) -> {entity_name}ListResponse:
        """
        List {entity_plural} with pagination and filtering.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            search: Search term
            sort_by: Field to sort by
            sort_order: Sort direction (asc/desc)
            **filters: Additional filters

        Returns:
            Paginated response with items and metadata
        """
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

        return {entity_name}ListResponse(
            items=[{entity_name}ListItem.model_validate(item) for item in items],
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
        data: {entity_name}Create,
        current_user: User,
    ) -> {entity_name}:
        """
        Create a new {entity_lower}.

        Args:
            data: Creation data
            current_user: Authenticated user

        Returns:
            Created {entity_name} instance

        Raises:
            ConflictError: If {entity_lower} with same slug/sku exists
        """
        # Generate slug from name
        slug = slugify(data.name)

        # Check for duplicate slug
        existing = await self._repo.get_by_slug(slug)
        if existing:
            raise ConflictError(
                message="{entity_name} with this name already exists",
                field="name",
            )

        # Check for duplicate SKU (if applicable)
        if hasattr(data, 'sku'):
            existing_sku = await self._repo.get_by_sku(data.sku)
            if existing_sku:
                raise ConflictError(
                    message="{entity_name} with this SKU already exists",
                    field="sku",
                )

        # Create {entity_lower}
        {entity_lower} = await self._repo.create({{
            **data.model_dump(),
            "slug": slug,
            "created_by_id": current_user.id,
        }})

        return {entity_lower}

    async def update(
        self,
        id: UUID,
        data: {entity_name}Update,
        current_user: User,
        partial: bool = False,
    ) -> {entity_name}:
        """
        Update {entity_lower} by ID.

        Args:
            id: {entity_name} UUID
            data: Update data
            current_user: Authenticated user
            partial: Whether this is a partial update

        Returns:
            Updated {entity_name} instance

        Raises:
            NotFoundError: If {entity_lower} not found
            ForbiddenError: If user lacks permission
            ConflictError: If update causes conflict
        """
        {entity_lower} = await self.get_by_id(id)

        # Check ownership
        self._check_ownership({entity_lower}, current_user)

        # Prepare update data
        if partial:
            update_data = data.model_dump(exclude_unset=True)
        else:
            update_data = data.model_dump()

        # Update slug if name changed
        if "name" in update_data and update_data["name"]:
            new_slug = slugify(update_data["name"])
            if new_slug != {entity_lower}.slug:
                existing = await self._repo.get_by_slug(new_slug)
                if existing and existing.id != id:
                    raise ConflictError(
                        message="{entity_name} with this name already exists",
                        field="name",
                    )
                update_data["slug"] = new_slug

        # Perform update
        updated = await self._repo.update(id, update_data)
        return updated

    async def delete(self, id: UUID, current_user: User) -> None:
        """
        Delete {entity_lower} by ID (soft delete).

        Args:
            id: {entity_name} UUID
            current_user: Authenticated user

        Raises:
            NotFoundError: If {entity_lower} not found
            ForbiddenError: If user lacks permission
        """
        {entity_lower} = await self.get_by_id(id)

        # Check ownership
        self._check_ownership({entity_lower}, current_user)

        # Soft delete
        await self._repo.soft_delete(id)

    # ========================================================================
    # Business Operations
    # ========================================================================

    async def publish(self, id: UUID, current_user: User) -> {entity_name}:
        """
        Publish a draft {entity_lower}.

        Args:
            id: {entity_name} UUID
            current_user: Authenticated user

        Returns:
            Updated {entity_name} instance

        Raises:
            ValueError: If {entity_lower} is not in draft status
        """
        {entity_lower} = await self.get_by_id(id)
        self._check_ownership({entity_lower}, current_user)

        if {entity_lower}.status != "draft":
            raise ValueError("Only draft {entity_plural} can be published")

        return await self._repo.update(id, {{"status": "active"}})

    async def archive(self, id: UUID, current_user: User) -> {entity_name}:
        """
        Archive a {entity_lower}.

        Args:
            id: {entity_name} UUID
            current_user: Authenticated user

        Returns:
            Updated {entity_name} instance
        """
        {entity_lower} = await self.get_by_id(id)
        self._check_ownership({entity_lower}, current_user)

        return await self._repo.update(id, {{"status": "archived"}})

    # ========================================================================
    # Helpers
    # ========================================================================

    def _check_ownership(
        self,
        {entity_lower}: {entity_name},
        user: User,
    ) -> None:
        """
        Check if user owns the {entity_lower} or is admin.

        Args:
            {entity_lower}: {entity_name} instance
            user: User to check

        Raises:
            ForbiddenError: If user lacks permission
        """
        if {entity_lower}.created_by_id != user.id and not user.is_admin:
            raise ForbiddenError(
                "You don't have permission to modify this {entity_lower}"
            )
```

### Step 4: Create Dependency

Add to `app/api/deps.py`:

```python
async def get_{entity_lower}_service(
    db: DBSession,
) -> {entity_name}Service:
    """Provide {entity_name}Service dependency."""
    repository = {entity_name}Repository(db)
    return {entity_name}Service(repository)


{entity_name}ServiceDep = Annotated[{entity_name}Service, Depends(get_{entity_lower}_service)]
```

## Business Rule Patterns

### State Machine

```python
VALID_TRANSITIONS = {{
    "draft": ["active", "archived"],
    "active": ["archived"],
    "archived": ["active"],
}}

async def transition_status(
    self,
    id: UUID,
    new_status: str,
    current_user: User,
) -> {entity_name}:
    {entity_lower} = await self.get_by_id(id)
    self._check_ownership({entity_lower}, current_user)

    if new_status not in VALID_TRANSITIONS.get({entity_lower}.status, []):
        raise ValueError(
            f"Cannot transition from {{{entity_lower}.status}} to {{new_status}}"
        )

    return await self._repo.update(id, {{"status": new_status}})
```

### Inventory Management

```python
async def update_stock(
    self,
    id: UUID,
    quantity_change: int,
) -> {entity_name}:
    {entity_lower} = await self.get_by_id(id)

    new_stock = {entity_lower}.stock + quantity_change
    if new_stock < 0:
        raise ValueError("Insufficient stock")

    return await self._repo.update(id, {{"stock": new_stock}})
```

## Output Files

1. `app/services/{entity_lower}.py` - Service file
2. Update `app/api/deps.py` - Dependency registration

## Validation Checklist

- [ ] Repository injected via constructor
- [ ] NotFoundError for missing resources
- [ ] ConflictError for uniqueness violations
- [ ] ForbiddenError for permission failures
- [ ] Ownership checks implemented
- [ ] State transitions validated
- [ ] REQ-XXX traceability comment
