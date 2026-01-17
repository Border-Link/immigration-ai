from rest_framework import permissions
from main_system.permissions.role_checker import RoleChecker


class IsAdminOrStaff(permissions.BasePermission):
    """
    Custom permission to only allow admin (superuser) or staff users to access the view.
    """

    def has_permission(self, request, view):
        """Check if the user is authenticated and is either superuser or staff."""
        user = getattr(request, 'user', None)
        return RoleChecker.is_staff(user)

