---
name: fastapi-router-generator
description: Agent for generating FastAPI routers
applies_to: fastapi
category: agent
inputs:
  - entity_name: Entity name in PascalCase
  - entity_plural: Plural form lowercase
  - operations: CRUD operations to include
  - auth_required: Whether authentication is required
---

# FastAPI Router Generator Agent

## Purpose

Generate complete FastAPI router files with CRUD endpoints, proper typing, dependency injection, and OpenAPI documentation.

## Activation

- User requests: "create router for [entity]", "generate [entity] endpoints"
- When creating new API resources
- When scaffolding REST endpoints

## Generation Process

### Step 1: Gather Requirements

Ask for or determine:
1. Entity name (PascalCase): e.g., `Product`
2. Plural form: e.g., `products`
3. Operations needed: `list`, `get`, `create`, `update`, `delete`
4. Authentication: required for all, some, or none
5. Additional query parameters
6. Custom endpoints needed

### Step 2: Generate Router

```python
# app/api/v1/endpoints/{entity_plural}.py
"""
{entity_name} API endpoints.

REQ-XXX: {entity_name} management API
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, get_{entity_lower}_service
from app.core.openapi import error_responses
from app.schemas.{entity_lower} import (
    {entity_name}Create,
    {entity_name}Update,
    {entity_name}Response,
    {entity_name}ListResponse,
)
from app.schemas.response import APIResponse
from app.services.{entity_lower} import {entity_name}Service

router = APIRouter(prefix="/{entity_plural}", tags=["{entity_plural}"])

{entity_name}ServiceDep = Annotated[{entity_name}Service, Depends(get_{entity_lower}_service)]


@router.get(
    "/",
    response_model=APIResponse[{entity_name}ListResponse],
    responses=error_responses(401),
)
async def list_{entity_plural}(
    service: {entity_name}ServiceDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
):
    """List all {entity_plural} with pagination."""
    result = await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return APIResponse(success=True, data=result)


@router.get(
    "/{{id}}",
    response_model=APIResponse[{entity_name}Response],
    responses=error_responses(401, 404),
)
async def get_{entity_lower}(
    id: UUID,
    service: {entity_name}ServiceDep,
    current_user: CurrentUser,
):
    """Get {entity_lower} by ID."""
    {entity_lower} = await service.get_by_id(id)
    return APIResponse(success=True, data={entity_name}Response.model_validate({entity_lower}))


@router.post(
    "/",
    response_model=APIResponse[{entity_name}Response],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 409, 422),
)
async def create_{entity_lower}(
    data: {entity_name}Create,
    service: {entity_name}ServiceDep,
    current_user: CurrentUser,
):
    """Create a new {entity_lower}."""
    {entity_lower} = await service.create(data, current_user)
    return APIResponse(success=True, data={entity_name}Response.model_validate({entity_lower}))


@router.put(
    "/{{id}}",
    response_model=APIResponse[{entity_name}Response],
    responses=error_responses(401, 403, 404, 422),
)
async def update_{entity_lower}(
    id: UUID,
    data: {entity_name}Update,
    service: {entity_name}ServiceDep,
    current_user: CurrentUser,
):
    """Update {entity_lower} by ID."""
    {entity_lower} = await service.update(id, data, current_user)
    return APIResponse(success=True, data={entity_name}Response.model_validate({entity_lower}))


@router.delete(
    "/{{id}}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404),
)
async def delete_{entity_lower}(
    id: UUID,
    service: {entity_name}ServiceDep,
    current_user: CurrentUser,
):
    """Delete {entity_lower} by ID."""
    await service.delete(id, current_user)
    return None
```

### Step 3: Register Router

Add to `app/api/v1/router.py`:

```python
from app.api.v1.endpoints import {entity_plural}

api_router.include_router({entity_plural}.router)
```

## Customization Options

### Public Endpoints (No Auth)

```python
@router.get("/public", response_model=APIResponse[{entity_name}ListResponse])
async def list_public_{entity_plural}(
    service: {entity_name}ServiceDep,
    page: int = 1,
    page_size: int = 20,
):
    """List public {entity_plural} without authentication."""
    result = await service.list_public(page=page, page_size=page_size)
    return APIResponse(success=True, data=result)
```

### Additional Query Filters

```python
@router.get("/")
async def list_{entity_plural}(
    # ... existing params ...
    status: Annotated[str | None, Query(pattern="^(draft|active|archived)$")] = None,
    category_id: Annotated[UUID | None, Query()] = None,
    min_price: Annotated[float | None, Query(ge=0)] = None,
    max_price: Annotated[float | None, Query(ge=0)] = None,
):
    result = await service.list(
        # ... all params ...
        status=status,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
    )
```

### Nested Resources

```python
@router.get("/{{id}}/items", response_model=APIResponse[ItemListResponse])
async def list_{entity_lower}_items(
    id: UUID,
    service: {entity_name}ServiceDep,
    current_user: CurrentUser,
):
    """List items for a specific {entity_lower}."""
    items = await service.get_items(id)
    return APIResponse(success=True, data=items)
```

## Output Files

1. `app/api/v1/endpoints/{entity_plural}.py` - Router file
2. Update `app/api/v1/router.py` - Router registration

## Validation Checklist

- [ ] Router prefix and tags set correctly
- [ ] Service dependency injected
- [ ] Authentication applied where needed
- [ ] OpenAPI responses documented
- [ ] Query parameters validated
- [ ] Proper HTTP status codes
- [ ] REQ-XXX traceability comment
