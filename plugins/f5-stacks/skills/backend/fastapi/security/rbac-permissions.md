---
name: fastapi-rbac-permissions
description: Role-Based Access Control for FastAPI
applies_to: fastapi
category: skill
---

# Role-Based Access Control (RBAC)

## Overview

RBAC provides fine-grained access control based on user roles and permissions.
This implementation supports both role-based and permission-based authorization.

## Models

```python
# app/models/rbac.py
from typing import List, Optional
from uuid import UUID
from sqlalchemy import String, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, Base


# Association tables
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
    Column("permission_id", ForeignKey("permissions.id"), primary_key=True),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True),
)


class Permission(BaseModel):
    """Permission model."""

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))

    # Resource:action format (e.g., "products:create", "users:read")
    resource: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50))

    roles: Mapped[List["Role"]] = relationship(
        secondary=role_permissions,
        back_populates="permissions",
    )


class Role(BaseModel):
    """Role model."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    is_default: Mapped[bool] = mapped_column(default=False)

    permissions: Mapped[List[Permission]] = relationship(
        secondary=role_permissions,
        back_populates="roles",
    )
    users: Mapped[List["User"]] = relationship(
        secondary=user_roles,
        back_populates="roles",
    )


# Update User model
class User(BaseModel):
    """User model with RBAC."""

    __tablename__ = "users"

    # ... other fields ...

    roles: Mapped[List[Role]] = relationship(
        secondary=user_roles,
        back_populates="users",
    )

    @property
    def permissions(self) -> set[str]:
        """Get all permissions from user's roles."""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(perm.name)
        return perms

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        return permission in self.permissions

    def has_role(self, role_name: str) -> bool:
        """Check if user has specific role."""
        return any(role.name == role_name for role in self.roles)

    def has_any_role(self, role_names: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(self.has_role(name) for name in role_names)
```

## Permission Definitions

```python
# app/core/permissions.py
from enum import Enum


class Resource(str, Enum):
    """Resource types."""
    USERS = "users"
    PRODUCTS = "products"
    ORDERS = "orders"
    CATEGORIES = "categories"
    SETTINGS = "settings"


class Action(str, Enum):
    """Permission actions."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    MANAGE = "manage"  # Full access


def permission(resource: Resource, action: Action) -> str:
    """Create permission string."""
    return f"{resource.value}:{action.value}"


# Pre-defined permissions
class Permissions:
    # Users
    USERS_CREATE = permission(Resource.USERS, Action.CREATE)
    USERS_READ = permission(Resource.USERS, Action.READ)
    USERS_UPDATE = permission(Resource.USERS, Action.UPDATE)
    USERS_DELETE = permission(Resource.USERS, Action.DELETE)
    USERS_MANAGE = permission(Resource.USERS, Action.MANAGE)

    # Products
    PRODUCTS_CREATE = permission(Resource.PRODUCTS, Action.CREATE)
    PRODUCTS_READ = permission(Resource.PRODUCTS, Action.READ)
    PRODUCTS_UPDATE = permission(Resource.PRODUCTS, Action.UPDATE)
    PRODUCTS_DELETE = permission(Resource.PRODUCTS, Action.DELETE)
    PRODUCTS_MANAGE = permission(Resource.PRODUCTS, Action.MANAGE)

    # Orders
    ORDERS_CREATE = permission(Resource.ORDERS, Action.CREATE)
    ORDERS_READ = permission(Resource.ORDERS, Action.READ)
    ORDERS_UPDATE = permission(Resource.ORDERS, Action.UPDATE)
    ORDERS_DELETE = permission(Resource.ORDERS, Action.DELETE)
    ORDERS_MANAGE = permission(Resource.ORDERS, Action.MANAGE)


# Role definitions
ROLE_PERMISSIONS = {
    "admin": [
        Permissions.USERS_MANAGE,
        Permissions.PRODUCTS_MANAGE,
        Permissions.ORDERS_MANAGE,
    ],
    "manager": [
        Permissions.PRODUCTS_MANAGE,
        Permissions.ORDERS_MANAGE,
        Permissions.USERS_READ,
    ],
    "seller": [
        Permissions.PRODUCTS_CREATE,
        Permissions.PRODUCTS_READ,
        Permissions.PRODUCTS_UPDATE,
        Permissions.ORDERS_READ,
    ],
    "customer": [
        Permissions.PRODUCTS_READ,
        Permissions.ORDERS_CREATE,
        Permissions.ORDERS_READ,
    ],
}
```

## RBAC Dependencies

```python
# app/api/deps.py
from typing import Annotated, Callable
from fastapi import Depends, HTTPException, status

from app.api.deps import CurrentUser
from app.models.user import User


class RequireRole:
    """Dependency to require specific role(s)."""

    def __init__(self, *roles: str, require_all: bool = False):
        self.roles = roles
        self.require_all = require_all

    async def __call__(self, user: CurrentUser) -> User:
        if self.require_all:
            # User must have all specified roles
            if not all(user.has_role(role) for role in self.roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required roles: {', '.join(self.roles)}",
                )
        else:
            # User must have at least one of the specified roles
            if not user.has_any_role(list(self.roles)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required one of roles: {', '.join(self.roles)}",
                )
        return user


class RequirePermission:
    """Dependency to require specific permission(s)."""

    def __init__(self, *permissions: str, require_all: bool = True):
        self.permissions = permissions
        self.require_all = require_all

    async def __call__(self, user: CurrentUser) -> User:
        # Check for manage permission (superuser for resource)
        for perm in self.permissions:
            resource = perm.split(":")[0]
            if user.has_permission(f"{resource}:manage"):
                return user

        if self.require_all:
            # User must have all specified permissions
            missing = [p for p in self.permissions if not user.has_permission(p)]
            if missing:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing permissions: {', '.join(missing)}",
                )
        else:
            # User must have at least one of the specified permissions
            if not any(user.has_permission(p) for p in self.permissions):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required one of: {', '.join(self.permissions)}",
                )
        return user


# Type alias factory
def require_roles(*roles: str) -> type:
    """Create type alias for role requirement."""
    return Annotated[User, Depends(RequireRole(*roles))]


def require_permissions(*permissions: str) -> type:
    """Create type alias for permission requirement."""
    return Annotated[User, Depends(RequirePermission(*permissions))]


# Pre-defined type aliases
AdminUser = Annotated[User, Depends(RequireRole("admin"))]
ManagerUser = Annotated[User, Depends(RequireRole("admin", "manager"))]

# Permission-based aliases
CanManageUsers = Annotated[User, Depends(RequirePermission(Permissions.USERS_MANAGE))]
CanManageProducts = Annotated[User, Depends(RequirePermission(Permissions.PRODUCTS_MANAGE))]
CanCreateProducts = Annotated[User, Depends(RequirePermission(Permissions.PRODUCTS_CREATE))]
```

## Using RBAC in Endpoints

```python
# app/api/v1/endpoints/products.py
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends

from app.api.deps import (
    CurrentUser,
    RequireRole,
    RequirePermission,
    AdminUser,
    CanCreateProducts,
    CanManageProducts,
)
from app.core.permissions import Permissions
from app.schemas.product import ProductCreate, ProductResponse

router = APIRouter()


@router.get("/")
async def list_products(
    current_user: CurrentUser,
    # Any authenticated user can read
):
    """List products (any authenticated user)."""
    return []


@router.post("/", response_model=ProductResponse)
async def create_product(
    data: ProductCreate,
    user: CanCreateProducts,  # Requires products:create permission
):
    """Create product (requires create permission)."""
    return {"id": "...", "name": data.name}


@router.put("/{product_id}")
async def update_product(
    product_id: UUID,
    data: ProductCreate,
    user: Annotated[User, Depends(RequirePermission(Permissions.PRODUCTS_UPDATE))],
):
    """Update product (requires update permission)."""
    return {"id": str(product_id)}


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    user: CanManageProducts,  # Requires manage permission
):
    """Delete product (requires manage permission)."""
    return {"deleted": True}


# Role-based endpoint
@router.get("/admin/stats")
async def get_admin_stats(
    user: AdminUser,  # Requires admin role
):
    """Admin-only statistics."""
    return {"total_products": 100}


# Multiple roles
@router.get("/reports")
async def get_reports(
    user: Annotated[User, Depends(RequireRole("admin", "manager"))],
):
    """Reports for admin or manager."""
    return []
```

## Resource-Based Authorization

```python
# app/api/deps.py
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


class ResourceOwner:
    """Check if user owns or can access the resource."""

    def __init__(
        self,
        repository_getter: Callable,
        owner_field: str = "user_id",
        admin_bypass: bool = True,
    ):
        self.repository_getter = repository_getter
        self.owner_field = owner_field
        self.admin_bypass = admin_bypass

    async def __call__(
        self,
        resource_id: UUID,
        current_user: CurrentUser,
        db: Annotated[AsyncSession, Depends(get_db)],
    ) -> bool:
        # Admin bypass
        if self.admin_bypass and current_user.has_role("admin"):
            return True

        repository = self.repository_getter(db)
        resource = await repository.get_by_id(resource_id)

        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource not found",
            )

        owner_id = getattr(resource, self.owner_field)
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this resource",
            )

        return True


# Usage
from app.repositories.product import ProductRepository

check_product_owner = ResourceOwner(
    repository_getter=lambda db: ProductRepository(db),
    owner_field="created_by_id",
)


@router.put("/{product_id}")
async def update_own_product(
    product_id: UUID,
    data: ProductUpdate,
    _: Annotated[bool, Depends(check_product_owner)],
    current_user: CurrentUser,
):
    """Update product (owner or admin only)."""
    ...
```

## Permission Seeding

```python
# scripts/seed_permissions.py
import asyncio
from app.database import AsyncSessionLocal
from app.models.rbac import Role, Permission
from app.core.permissions import ROLE_PERMISSIONS


async def seed_permissions():
    """Seed permissions and roles."""
    async with AsyncSessionLocal() as session:
        # Create permissions
        all_permissions = set()
        for perms in ROLE_PERMISSIONS.values():
            all_permissions.update(perms)

        permission_objects = {}
        for perm_name in all_permissions:
            resource, action = perm_name.split(":")
            permission = Permission(
                name=perm_name,
                resource=resource,
                action=action,
            )
            session.add(permission)
            permission_objects[perm_name] = permission

        await session.flush()

        # Create roles with permissions
        for role_name, perm_names in ROLE_PERMISSIONS.items():
            role = Role(
                name=role_name,
                is_default=(role_name == "customer"),
            )
            role.permissions = [permission_objects[p] for p in perm_names]
            session.add(role)

        await session.commit()
        print("Permissions and roles seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_permissions())
```

## Best Practices

1. **Use permission strings** in format "resource:action"
2. **Create manage permission** as superuser for each resource
3. **Cache user permissions** for performance
4. **Implement role hierarchy** if needed
5. **Separate role and permission checks** for flexibility
6. **Use resource ownership** for fine-grained control
7. **Seed permissions** on deployment
8. **Log authorization failures** for security auditing
