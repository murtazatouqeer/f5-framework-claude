# apps/users/permissions.py
"""
Custom permission classes.

REQ-002: User Authentication
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsEmailVerified(BasePermission):
    """
    Permission that requires email verification.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, IsEmailVerified]
    """

    message = 'Email verification required.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.email_verified
        )


class IsOwner(BasePermission):
    """
    Permission that checks object ownership.

    Expects object to have `created_by` or `user` attribute.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, IsOwner]
    """

    def has_object_permission(self, request, view, obj):
        # Check various ownership attributes
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsOwnerOrReadOnly(BasePermission):
    """
    Permission that allows read access to anyone but write only to owner.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in SAFE_METHODS:
            return True

        # Write permissions only for owner
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsAdminOrReadOnly(BasePermission):
    """
    Permission that allows read access to authenticated users but write only to admins.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_staff


class HasRole(BasePermission):
    """
    Permission that checks for specific role.

    Usage:
        class MyView(APIView):
            permission_classes = [IsAuthenticated, HasRole]
            required_role = 'manager'
    """

    def has_permission(self, request, view):
        required_role = getattr(view, 'required_role', None)

        if not required_role:
            return True

        if not request.user or not request.user.is_authenticated:
            return False

        # Check if user has role (assumes User has `roles` relation or `role` field)
        if hasattr(request.user, 'roles'):
            return request.user.roles.filter(name=required_role).exists()
        if hasattr(request.user, 'role'):
            return request.user.role == required_role

        return False


class IsNotAuthenticated(BasePermission):
    """
    Permission that only allows unauthenticated users.

    Useful for registration and login endpoints.

    Usage:
        class RegisterView(APIView):
            permission_classes = [IsNotAuthenticated]
    """

    message = 'You are already authenticated.'

    def has_permission(self, request, view):
        return not request.user or not request.user.is_authenticated


class CanDeleteObject(BasePermission):
    """
    Permission for delete operations.

    Allows owner or staff to delete.
    """

    def has_object_permission(self, request, view, obj):
        if request.method != 'DELETE':
            return True

        # Staff can delete anything
        if request.user.is_staff:
            return True

        # Owner can delete their objects
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user

        return False
