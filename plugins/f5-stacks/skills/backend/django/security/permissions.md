# DRF Permissions Skill

## Overview

Permission patterns for Django REST Framework including custom permissions and object-level access control.

## Built-in Permissions

```python
from rest_framework.permissions import (
    AllowAny,              # No restrictions
    IsAuthenticated,       # Must be logged in
    IsAdminUser,           # Must be staff
    IsAuthenticatedOrReadOnly,  # Read: anyone, Write: authenticated
    DjangoModelPermissions,     # Based on model permissions
    DjangoObjectPermissions,    # Object-level model permissions
)

# Usage in views
class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
```

## Custom Permission Classes

### Basic Custom Permission

```python
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission: only owner can access.
    """

    def has_object_permission(self, request, view, obj):
        # Check if object has owner attribute
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: owner can modify, others read-only.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        return obj.owner == request.user
```

### Action-Based Permission

```python
class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Owner or admin can access.
    """

    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Admin has full access
        if request.user.is_staff:
            return True

        # Owner has access
        return obj.owner == request.user


class CanManageOrganization(permissions.BasePermission):
    """
    Check if user has organization management permissions.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Check for specific permission
        return request.user.has_perm('organizations.manage_organization')

    def has_object_permission(self, request, view, obj):
        # Check organization membership
        return obj.members.filter(
            user=request.user,
            role__in=['admin', 'owner']
        ).exists()
```

### Role-Based Permission

```python
class RoleBasedPermission(permissions.BasePermission):
    """
    Permission based on user roles within an organization.
    """

    # Define required roles per action
    action_roles = {
        'list': ['viewer', 'editor', 'admin', 'owner'],
        'retrieve': ['viewer', 'editor', 'admin', 'owner'],
        'create': ['editor', 'admin', 'owner'],
        'update': ['editor', 'admin', 'owner'],
        'partial_update': ['editor', 'admin', 'owner'],
        'destroy': ['admin', 'owner'],
    }

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        action = getattr(view, 'action', None)
        if action is None:
            return True

        required_roles = self.action_roles.get(action, [])
        if not required_roles:
            return True

        # Get user's role (implement based on your model)
        user_role = self.get_user_role(request.user, view)
        return user_role in required_roles

    def get_user_role(self, user, view):
        """Override to implement role lookup."""
        # Example: get from organization membership
        org_id = view.kwargs.get('organization_pk')
        if org_id:
            membership = user.memberships.filter(
                organization_id=org_id
            ).first()
            if membership:
                return membership.role
        return None
```

### Permission with Custom Error Message

```python
class IsVerifiedUser(permissions.BasePermission):
    """
    Only verified users can access.
    """

    message = 'Your account must be verified to perform this action.'

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return getattr(request.user, 'is_verified', False)
```

## ViewSet Permission Mapping

```python
class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet with per-action permission configuration.
    """

    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_permissions(self):
        """Return permissions based on action."""
        if self.action == 'create':
            permission_classes = [IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
        elif self.action == 'cancel':
            permission_classes = [IsAuthenticated, IsOwner]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminUser]

        return [permission() for permission in permission_classes]

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order - only owner can cancel."""
        order = self.get_object()
        order.status = 'cancelled'
        order.save()
        return Response({'status': 'cancelled'})
```

## Object-Level Permission Filtering

```python
class ProjectViewSet(viewsets.ModelViewSet):
    """
    Filter queryset based on user permissions.
    """

    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated, IsProjectMember]

    def get_queryset(self):
        """Return only projects user has access to."""
        user = self.request.user

        if user.is_staff:
            return Project.objects.all()

        # Return projects where user is a member
        return Project.objects.filter(
            Q(owner=user) |
            Q(members__user=user)
        ).distinct()
```

## Permission Combinations

```python
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAuthenticatedAndVerified(BasePermission):
    """Combine multiple permission checks."""

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            getattr(request.user, 'is_verified', False) and
            not getattr(request.user, 'is_banned', False)
        )


# Using AND/OR combinations in views
class MyView(APIView):
    # All permissions must pass (AND)
    permission_classes = [IsAuthenticated, IsVerified, IsOwner]


# Custom OR logic
class IsOwnerOrStaff(BasePermission):
    """Owner OR staff can access."""

    def has_object_permission(self, request, view, obj):
        return (
            request.user.is_staff or
            obj.owner == request.user
        )
```

## Throttling with Permissions

```python
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class BurstRateThrottle(UserRateThrottle):
    rate = '60/min'


class SustainedRateThrottle(UserRateThrottle):
    rate = '1000/day'


class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [BurstRateThrottle, SustainedRateThrottle]
```

## Best Practices

1. **Least privilege** - Start restrictive, add permissions as needed
2. **Object-level permissions** - Always check has_object_permission
3. **Filter querysets** - Don't rely on permission alone
4. **Custom error messages** - Clear, actionable messages
5. **Test permissions** - Unit test all permission paths
6. **Document permissions** - In API documentation
7. **Combine with throttling** - Prevent abuse
