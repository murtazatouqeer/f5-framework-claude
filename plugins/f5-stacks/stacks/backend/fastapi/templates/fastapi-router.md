---
name: fastapi-router
description: FastAPI router template with full CRUD operations
applies_to: fastapi
category: template
variables:
  - name: entity_name
    description: Entity name in PascalCase (e.g., Product)
  - name: entity_plural
    description: Plural form (e.g., products)
  - name: entity_lower
    description: Lowercase entity name (e.g., product)
---

# FastAPI Router Template

## Template

```python
# app/api/v1/endpoints/{{entity_plural}}.py
"""
{{entity_name}} API endpoints.

REQ-XXX: {{entity_name}} management
"""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import CurrentUser, get_{{entity_lower}}_service
from app.core.openapi import error_responses
from app.schemas.{{entity_lower}} import (
    {{entity_name}}Create,
    {{entity_name}}Update,
    {{entity_name}}Response,
    {{entity_name}}ListResponse,
)
from app.schemas.response import APIResponse
from app.services.{{entity_lower}} import {{entity_name}}Service

router = APIRouter(prefix="/{{entity_plural}}", tags=["{{entity_plural}}"])

# Type alias for dependency injection
{{entity_name}}ServiceDep = Annotated[{{entity_name}}Service, Depends(get_{{entity_lower}}_service)]


@router.get(
    "/",
    response_model=APIResponse[{{entity_name}}ListResponse],
    responses=error_responses(401),
)
async def list_{{entity_plural}}(
    service: {{entity_name}}ServiceDep,
    current_user: CurrentUser,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
    search: Annotated[str | None, Query(max_length=100)] = None,
    sort_by: Annotated[str, Query()] = "created_at",
    sort_order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
):
    """
    List all {{entity_plural}} with pagination.

    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **search**: Search term for filtering
    - **sort_by**: Field to sort by
    - **sort_order**: Sort direction (asc/desc)
    """
    result = await service.list(
        page=page,
        page_size=page_size,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return APIResponse(success=True, data=result)


@router.get(
    "/{id}",
    response_model=APIResponse[{{entity_name}}Response],
    responses=error_responses(401, 404),
)
async def get_{{entity_lower}}(
    id: UUID,
    service: {{entity_name}}ServiceDep,
    current_user: CurrentUser,
):
    """
    Get {{entity_lower}} by ID.

    - **id**: {{entity_name}} UUID
    """
    {{entity_lower}} = await service.get_by_id(id)
    return APIResponse(success=True, data={{entity_name}}Response.model_validate({{entity_lower}}))


@router.post(
    "/",
    response_model=APIResponse[{{entity_name}}Response],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401, 409, 422),
)
async def create_{{entity_lower}}(
    data: {{entity_name}}Create,
    service: {{entity_name}}ServiceDep,
    current_user: CurrentUser,
):
    """
    Create a new {{entity_lower}}.

    Returns the created {{entity_lower}}.
    """
    {{entity_lower}} = await service.create(data, current_user)
    return APIResponse(success=True, data={{entity_name}}Response.model_validate({{entity_lower}}))


@router.put(
    "/{id}",
    response_model=APIResponse[{{entity_name}}Response],
    responses=error_responses(401, 403, 404, 422),
)
async def update_{{entity_lower}}(
    id: UUID,
    data: {{entity_name}}Update,
    service: {{entity_name}}ServiceDep,
    current_user: CurrentUser,
):
    """
    Update {{entity_lower}} by ID.

    - **id**: {{entity_name}} UUID

    Only the owner or admin can update.
    """
    {{entity_lower}} = await service.update(id, data, current_user)
    return APIResponse(success=True, data={{entity_name}}Response.model_validate({{entity_lower}}))


@router.patch(
    "/{id}",
    response_model=APIResponse[{{entity_name}}Response],
    responses=error_responses(401, 403, 404, 422),
)
async def partial_update_{{entity_lower}}(
    id: UUID,
    data: {{entity_name}}Update,
    service: {{entity_name}}ServiceDep,
    current_user: CurrentUser,
):
    """
    Partially update {{entity_lower}} by ID.

    Only provided fields will be updated.
    """
    {{entity_lower}} = await service.update(id, data, current_user, partial=True)
    return APIResponse(success=True, data={{entity_name}}Response.model_validate({{entity_lower}}))


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=error_responses(401, 403, 404),
)
async def delete_{{entity_lower}}(
    id: UUID,
    service: {{entity_name}}ServiceDep,
    current_user: CurrentUser,
):
    """
    Delete {{entity_lower}} by ID.

    Only the owner or admin can delete.
    """
    await service.delete(id, current_user)
    return None
```

## Usage

Replace placeholders:
- `{{entity_name}}`: PascalCase entity name (e.g., `Product`)
- `{{entity_plural}}`: Plural lowercase (e.g., `products`)
- `{{entity_lower}}`: Lowercase singular (e.g., `product`)

### Example: Product Router

```python
# app/api/v1/endpoints/products.py
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])
ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]

@router.get("/", response_model=APIResponse[ProductListResponse])
async def list_products(...):
    ...
```

### Router Registration

```python
# app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.endpoints import products, categories, orders

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(products.router)
api_router.include_router(categories.router)
api_router.include_router(orders.router)
```
