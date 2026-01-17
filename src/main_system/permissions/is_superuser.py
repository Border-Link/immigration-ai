from rest_framework import permissions
from main_system.permissions.role_checker import RoleChecker


class IsSuperUser(permissions.BasePermission):
    """
    Custom permission to only allow superusers to access the view.
    """

    def has_permission(self, request, view):
        """Check if the user is authenticated and is a superuser."""
        user = getattr(request, 'user', None)
        return RoleChecker.is_superadmin(user)